"""
SessionManager单元测试
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.loom.core.session_manager import (
    Session,
    SessionConfig,
    SessionManager,
    SessionStatus,
)


class TestSessionManager:
    """SessionManager测试类"""

    @pytest.fixture
    def session_manager(self):
        """创建SessionManager实例"""
        persistence_mock = AsyncMock()
        config_manager_mock = MagicMock()

        # 模拟配置
        app_config = MagicMock()
        app_config.llm_providers = {"openai": MagicMock()}
        app_config.session_defaults.default_llm_provider = "openai"
        config_manager_mock.get_config.return_value = app_config

        manager = SessionManager(
            persistence_engine=persistence_mock, config_manager=config_manager_mock
        )
        return manager

    @pytest.fixture
    def sample_session_config(self):
        """创建示例会话配置"""
        return SessionConfig(
            name="测试会话",
            canon_path="./test_canon",
            memory_backend="sqlite",
            llm_provider="openai",
            max_turns=100,
            metadata={"test": True},
        )

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, sample_session_config):
        """测试创建会话"""
        # 模拟持久化引擎
        session_manager.persistence.save_session = AsyncMock(return_value=True)

        # 创建会话
        session = await session_manager.create_session(sample_session_config)

        assert session is not None
        assert session.id is not None
        assert session.name == "测试会话"
        assert session.config == sample_session_config
        assert session.status == SessionStatus.ACTIVE
        assert session.current_turn == 0
        assert session.total_turns == 0
        assert "created_by" in session.metadata

        # 验证会话被添加到活跃会话
        assert session.id in session_manager.active_sessions
        assert session_manager.active_sessions[session.id] == session

        # 验证保存被调用
        session_manager.persistence.save_session.assert_called_once_with(session)

    @pytest.mark.asyncio
    async def test_load_session_from_memory(
        self, session_manager, sample_session_config
    ):
        """测试从内存加载会话"""
        # 先创建会话
        session_manager.persistence.save_session = AsyncMock(return_value=True)
        session = await session_manager.create_session(sample_session_config)

        # 从内存加载
        loaded_session = await session_manager.load_session(session.id)

        assert loaded_session is not None
        assert loaded_session.id == session.id
        assert loaded_session.name == session.name

        # 持久化引擎不应该被调用
        session_manager.persistence.load_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_session_from_persistence(self, session_manager):
        """测试从持久化存储加载会话"""
        # 模拟持久化引擎返回会话
        mock_session_data = {
            "id": "test-session-id",
            "name": "持久化会话",
            "config": {
                "name": "持久化会话",
                "canon_path": "./test",
                "memory_backend": "sqlite",
                "llm_provider": "openai",
                "max_turns": 50,
                "auto_save": True,
                "auto_save_interval": 5,
                "metadata": {},
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "current_turn": 10,
            "total_turns": 10,
            "last_activity": datetime.now().isoformat(),
            "state": {"turns": []},
            "metadata": {"loaded_from": "persistence"},
        }

        session_manager.persistence.load_session = AsyncMock(
            return_value=mock_session_data
        )

        # 加载会话
        loaded_session = await session_manager.load_session("test-session-id")

        assert loaded_session is not None
        assert loaded_session.id == "test-session-id"
        assert loaded_session.name == "持久化会话"
        assert loaded_session.current_turn == 10
        assert loaded_session.metadata["loaded_from"] == "persistence"

        # 验证会话被添加到活跃会话
        assert "test-session-id" in session_manager.active_sessions

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self, session_manager):
        """测试加载不存在的会话"""
        session_manager.persistence.load_session = AsyncMock(return_value=None)

        loaded_session = await session_manager.load_session("nonexistent-id")

        assert loaded_session is None

    @pytest.mark.asyncio
    async def test_save_session(self, session_manager, sample_session_config):
        """测试保存会话"""
        # 创建会话
        session_manager.persistence.save_session = AsyncMock(return_value=True)
        session = await session_manager.create_session(sample_session_config)

        # 修改会话
        original_updated_at = session.updated_at
        session.current_turn = 5

        # 保存会话
        success = await session_manager.save_session(session)

        assert success is True
        assert session.updated_at > original_updated_at  # 更新时间应该更新

        # 验证保存被调用
        session_manager.persistence.save_session.assert_called_with(session)

        # 验证会话在活跃会话中
        assert session.id in session_manager.active_sessions

    @pytest.mark.asyncio
    async def test_save_session_without_persistence(self):
        """测试没有持久化引擎时保存会话"""
        manager = SessionManager(persistence_engine=None)

        session_config = SessionConfig(name="测试", canon_path="./test")
        session = await manager.create_session(session_config)

        # 应该成功（即使没有持久化引擎）
        success = await manager.save_session(session)
        assert success is True

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager, sample_session_config):
        """测试删除会话"""
        # 创建会话
        session = await session_manager.create_session(sample_session_config)

        # 模拟持久化删除
        session_manager.persistence.delete_session = AsyncMock(return_value=True)

        # 删除会话
        success = await session_manager.delete_session(session.id, permanent=True)

        assert success is True
        assert session.id not in session_manager.active_sessions

        # 验证删除被调用
        session_manager.persistence.delete_session.assert_called_with(session.id)

    @pytest.mark.asyncio
    async def test_archive_session(self, session_manager, sample_session_config):
        """测试归档会话（非永久删除）"""
        # 创建会话
        session = await session_manager.create_session(sample_session_config)

        # 模拟保存
        session_manager.persistence.save_session = AsyncMock(return_value=True)

        # 归档会话
        success = await session_manager.delete_session(session.id, permanent=False)

        assert success is True
        assert session.id in session_manager.active_sessions  # 仍然在活跃会话中
        assert session.status == SessionStatus.ARCHIVED

        # 验证保存被调用（状态更新）
        session_manager.persistence.save_session.assert_called_with(session)

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_manager, sample_session_config):
        """测试列出会话"""
        # 创建多个会话
        sessions = []
        for i in range(3):
            config = SessionConfig(
                name=f"测试会话{i}", canon_path=f"./test{i}", metadata={"index": i}
            )
            session = await session_manager.create_session(config)
            sessions.append(session)

        # 列出活跃会话
        active_sessions = await session_manager.list_sessions(include_inactive=False)

        assert len(active_sessions) == 3
        for session in sessions:
            assert session.id in active_sessions

        # 归档一个会话
        await session_manager.update_session_status(
            sessions[0].id, SessionStatus.ARCHIVED
        )

        # 再次列出活跃会话（应该只有2个）
        active_sessions = await session_manager.list_sessions(include_inactive=False)
        assert len(active_sessions) == 2

        # 列出所有会话（包括非活跃）
        all_sessions = await session_manager.list_sessions(include_inactive=True)
        assert len(all_sessions) == 3

    @pytest.mark.asyncio
    async def test_update_session_status(self, session_manager, sample_session_config):
        """测试更新会话状态"""
        session = await session_manager.create_session(sample_session_config)

        # 模拟保存
        session_manager.persistence.save_session = AsyncMock(return_value=True)

        # 更新状态
        success = await session_manager.update_session_status(
            session.id, SessionStatus.PAUSED
        )

        assert success is True
        assert session.status == SessionStatus.PAUSED

        # 验证保存被调用
        session_manager.persistence.save_session.assert_called_with(session)

    @pytest.mark.asyncio
    async def test_get_session_stats(self, session_manager, sample_session_config):
        """测试获取会话统计信息"""
        session = await session_manager.create_session(sample_session_config)

        # 获取统计信息
        stats = await session_manager.get_session_stats(session.id)

        assert stats is not None
        assert stats["session_id"] == session.id
        assert stats["name"] == session.name
        assert stats["status"] == SessionStatus.ACTIVE.value
        assert stats["current_turn"] == 0
        assert stats["total_turns"] == 0
        assert "uptime_hours" in stats
        assert "turns_per_hour" in stats
        assert "config" in stats

    @pytest.mark.asyncio
    async def test_get_session_stats_nonexistent(self, session_manager):
        """测试获取不存在的会话统计信息"""
        # 确保load_session返回None
        session_manager.persistence.load_session = AsyncMock(return_value=None)

        stats = await session_manager.get_session_stats("nonexistent-id")

        assert stats is None

    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions(
        self, session_manager, sample_session_config
    ):
        """测试清理不活跃会话"""
        # 创建会话
        session = await session_manager.create_session(sample_session_config)

        # 将会话标记为不活跃（设置最后活动时间为很久以前）
        session.last_activity = datetime.now() - timedelta(hours=48)

        # 模拟保存
        session_manager.persistence.save_session = AsyncMock(return_value=True)

        # 清理不活跃会话（24小时阈值）
        cleaned_count = await session_manager.cleanup_inactive_sessions(
            max_inactive_hours=24
        )

        assert cleaned_count == 1
        assert session.status == SessionStatus.ARCHIVED

        # 验证保存被调用
        session_manager.persistence.save_session.assert_called_with(session)

    @pytest.mark.asyncio
    async def test_search_sessions(self, session_manager):
        """测试搜索会话"""
        # 创建多个不同特征的会话
        sessions_data = [
            ("奇幻世界", SessionStatus.ACTIVE, datetime.now() - timedelta(hours=1)),
            ("科幻冒险", SessionStatus.PAUSED, datetime.now() - timedelta(hours=2)),
            ("历史剧", SessionStatus.ACTIVE, datetime.now() - timedelta(hours=3)),
        ]

        sessions = []
        for name, status, created_at in sessions_data:
            config = SessionConfig(name=name, canon_path=f"./{name}")
            session = await session_manager.create_session(config)
            session.status = status
            session.created_at = created_at
            sessions.append(session)

        # 按名称搜索
        results = await session_manager.search_sessions({"name": "奇幻"})
        assert len(results) == 1
        assert results[0].name == "奇幻世界"

        # 按状态搜索
        results = await session_manager.search_sessions(
            {"status": SessionStatus.ACTIVE.value}
        )
        assert len(results) == 2

        # 按创建时间搜索
        cutoff = datetime.now() - timedelta(hours=1.5)
        results = await session_manager.search_sessions({"created_after": cutoff})
        assert len(results) == 1  # 只有"奇幻世界"在cutoff之后创建

        # 组合搜索
        results = await session_manager.search_sessions(
            {"name": "世界", "status": SessionStatus.ACTIVE.value}
        )
        assert len(results) == 1
        assert results[0].name == "奇幻世界"

    @pytest.mark.asyncio
    async def test_session_increment_turn(self, sample_session_config):
        """测试会话回合递增"""
        session = Session(
            id="test-id",
            name="测试",
            config=sample_session_config,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SessionStatus.ACTIVE,
        )

        original_turn = session.current_turn
        original_total = session.total_turns
        original_activity = session.last_activity

        # 递增回合
        session.increment_turn()

        assert session.current_turn == original_turn + 1
        assert session.total_turns == original_total + 1
        assert session.last_activity >= original_activity
        assert session.updated_at >= original_activity

    def test_session_to_dict_and_from_dict(self, sample_session_config):
        """测试会话序列化和反序列化"""
        # 创建原始会话
        original_session = Session(
            id="test-id",
            name="测试会话",
            config=sample_session_config,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SessionStatus.ACTIVE,
            current_turn=5,
            total_turns=10,
            last_activity=datetime.now(),
            state={"turns": [1, 2, 3]},
            metadata={"test": True},
        )

        # 转换为字典
        session_dict = original_session.to_dict()

        assert session_dict["id"] == "test-id"
        assert session_dict["name"] == "测试会话"
        assert session_dict["status"] == SessionStatus.ACTIVE.value
        assert session_dict["current_turn"] == 5
        assert session_dict["total_turns"] == 10
        assert "config" in session_dict
        assert "state" in session_dict
        assert "metadata" in session_dict

        # 从字典恢复
        restored_session = Session.from_dict(session_dict)

        assert restored_session.id == original_session.id
        assert restored_session.name == original_session.name
        assert restored_session.status == original_session.status
        assert restored_session.current_turn == original_session.current_turn
        assert restored_session.total_turns == original_session.total_turns
        assert restored_session.state == original_session.state
        assert restored_session.metadata == original_session.metadata
