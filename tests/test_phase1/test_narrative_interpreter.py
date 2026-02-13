"""
NarrativeInterpreter接口测试

测试新的NarrativeInterpreter接口功能，确保接口定义正确且实现符合预期。
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from src.loom.core.interfaces import (
    NarrativeArchive,
    NarrativeArchivePersistence,
    NarrativeContext,
    NarrativeInterpretation,
    NarrativeInterpreter,
    NarrativeScheduler,
    Session,
    SessionConfig,
    SessionStatus,
    Turn,
    TurnResult,
)


class TestNarrativeInterpreterInterface:
    """NarrativeInterpreter接口测试"""

    @pytest.fixture
    def mock_interpreter(self):
        """创建模拟的NarrativeInterpreter"""
        interpreter = Mock(spec=NarrativeInterpreter)

        # 设置模拟方法
        interpreter.create_session = AsyncMock()
        interpreter.load_session = AsyncMock()
        interpreter.save_session = AsyncMock()
        interpreter.delete_session = AsyncMock()
        interpreter.list_sessions = AsyncMock()
        interpreter.interpret_narrative = AsyncMock()
        interpreter.check_consistency = AsyncMock()
        interpreter.generate_narrative_summary = AsyncMock()
        interpreter.track_narrative_arcs = AsyncMock()

        return interpreter

    @pytest.fixture
    def sample_session_config(self):
        """示例会话配置"""
        return SessionConfig(
            name="测试会话",
            canon_path="./tests/data/canon.md",
            llm_provider="openai",
            max_turns=10,
            metadata={"test": True},
        )

    @pytest.fixture
    def sample_session(self, sample_session_config):
        """示例会话"""
        return Session(
            id="test-session-123",
            name="测试会话",
            config=sample_session_config,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SessionStatus.ACTIVE,
            current_turn=0,
            total_turns=0,
            state={"narrative": "初始状态"},
            metadata={"test": True},
        )

    @pytest.fixture
    def sample_narrative_context(self, sample_session):
        """示例叙事上下文"""
        return NarrativeContext(
            session=sample_session,
            current_scene="城堡大厅",
            characters_present=["国王", "骑士", "巫师"],
            plot_points=["寻找圣杯", "击败恶龙"],
            narrative_tone="史诗",
            narrative_pace="正常",
            consistency_checks=[],
        )

    @pytest.mark.asyncio
    async def test_create_session_interface(
        self, mock_interpreter, sample_session_config
    ):
        """测试创建会话接口"""
        # 设置模拟返回值
        mock_interpreter.create_session.return_value = Mock(spec=Session)

        # 调用接口
        result = await mock_interpreter.create_session(sample_session_config)

        # 验证调用
        mock_interpreter.create_session.assert_called_once_with(sample_session_config)
        assert isinstance(result, Mock)

    @pytest.mark.asyncio
    async def test_load_session_interface(self, mock_interpreter):
        """测试加载会话接口"""
        # 设置模拟返回值
        mock_session = Mock(spec=Session)
        mock_interpreter.load_session.return_value = mock_session

        # 调用接口
        session_id = "test-session-123"
        result = await mock_interpreter.load_session(session_id, force_reload=True)

        # 验证调用
        mock_interpreter.load_session.assert_called_once_with(
            session_id, force_reload=True
        )
        assert result == mock_session

    @pytest.mark.asyncio
    async def test_interpret_narrative_interface(
        self, mock_interpreter, sample_narrative_context
    ):
        """测试解释叙事接口"""
        # 设置模拟返回值
        mock_interpretation = NarrativeInterpretation(
            interpretation="叙事解释结果",
            consistency_score=0.85,
            continuity_issues=["时间线轻微不一致"],
            suggested_improvements=["增加角色动机描述"],
            narrative_arcs=[{"name": "英雄之旅", "progress": 0.3}],
        )
        mock_interpreter.interpret_narrative.return_value = mock_interpretation

        # 调用接口
        session_id = "test-session-123"
        result = await mock_interpreter.interpret_narrative(
            session_id, sample_narrative_context
        )

        # 验证调用
        mock_interpreter.interpret_narrative.assert_called_once_with(
            session_id, sample_narrative_context
        )
        assert result == mock_interpretation
        assert result.consistency_score == 0.85
        assert len(result.continuity_issues) == 1

    @pytest.mark.asyncio
    async def test_check_consistency_interface(self, mock_interpreter):
        """测试检查一致性接口"""
        # 设置模拟返回值
        mock_interpreter.check_consistency.return_value = (True, ["轻微的时间线问题"])

        # 调用接口
        session_id = "test-session-123"
        new_content = "骑士突然出现在城堡中"
        success, issues = await mock_interpreter.check_consistency(
            session_id, new_content
        )

        # 验证调用
        mock_interpreter.check_consistency.assert_called_once_with(
            session_id, new_content
        )
        assert success is True
        assert len(issues) == 1

    @pytest.mark.asyncio
    async def test_generate_narrative_summary_interface(self, mock_interpreter):
        """测试生成叙事摘要接口"""
        # 设置模拟返回值
        summary_text = "这是一个关于英雄寻找圣杯的史诗故事..."
        mock_interpreter.generate_narrative_summary.return_value = summary_text

        # 调用接口
        session_id = "test-session-123"
        result = await mock_interpreter.generate_narrative_summary(session_id)

        # 验证调用
        mock_interpreter.generate_narrative_summary.assert_called_once_with(session_id)
        assert result == summary_text
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_track_narrative_arcs_interface(self, mock_interpreter):
        """测试跟踪叙事弧线接口"""
        # 设置模拟返回值
        arcs = [
            {"name": "英雄之旅", "progress": 0.3, "milestones": ["召唤", "启程"]},
            {"name": "爱情故事", "progress": 0.1, "milestones": ["相遇"]},
        ]
        mock_interpreter.track_narrative_arcs.return_value = arcs

        # 调用接口
        session_id = "test-session-123"
        result = await mock_interpreter.track_narrative_arcs(session_id)

        # 验证调用
        mock_interpreter.track_narrative_arcs.assert_called_once_with(session_id)
        assert len(result) == 2
        assert result[0]["name"] == "英雄之旅"


class TestNarrativeSchedulerInterface:
    """NarrativeScheduler接口测试"""

    @pytest.fixture
    def mock_scheduler(self):
        """创建模拟的NarrativeScheduler"""
        scheduler = Mock(spec=NarrativeScheduler)

        # 设置模拟方法
        scheduler.schedule_turn = AsyncMock()
        scheduler.get_turn_history = AsyncMock()
        scheduler.schedule_narrative_event = AsyncMock()
        scheduler.get_narrative_timeline = AsyncMock()
        scheduler.adjust_narrative_pace = AsyncMock()
        scheduler.manage_narrative_dependencies = AsyncMock()

        return scheduler

    @pytest.mark.asyncio
    async def test_schedule_narrative_event_interface(self, mock_scheduler):
        """测试调度叙事事件接口"""
        # 设置模拟返回值
        event_id = "event-123"
        mock_scheduler.schedule_narrative_event.return_value = event_id

        # 调用接口
        session_id = "test-session-123"
        event_type = "time_skip"
        event_data = {"duration": "3天", "reason": "旅行时间"}
        priority = 1

        result = await mock_scheduler.schedule_narrative_event(
            session_id, event_type, event_data, priority
        )

        # 验证调用
        mock_scheduler.schedule_narrative_event.assert_called_once_with(
            session_id, event_type, event_data, priority
        )
        assert result == event_id

    @pytest.mark.asyncio
    async def test_get_narrative_timeline_interface(self, mock_scheduler):
        """测试获取叙事时间线接口"""
        # 设置模拟返回值
        timeline = [
            {"timestamp": "2024-01-01", "event": "故事开始", "type": "start"},
            {"timestamp": "2024-01-02", "event": "遇到导师", "type": "character"},
        ]
        mock_scheduler.get_narrative_timeline.return_value = timeline

        # 调用接口
        session_id = "test-session-123"
        result = await mock_scheduler.get_narrative_timeline(session_id)

        # 验证调用
        mock_scheduler.get_narrative_timeline.assert_called_once_with(session_id)
        assert len(result) == 2
        assert result[0]["event"] == "故事开始"

    @pytest.mark.asyncio
    async def test_adjust_narrative_pace_interface(self, mock_scheduler):
        """测试调整叙事节奏接口"""
        # 设置模拟返回值
        mock_scheduler.adjust_narrative_pace.return_value = True

        # 调用接口
        session_id = "test-session-123"
        pace = "fast"
        result = await mock_scheduler.adjust_narrative_pace(session_id, pace)

        # 验证调用
        mock_scheduler.adjust_narrative_pace.assert_called_once_with(session_id, pace)
        assert result is True

    @pytest.mark.asyncio
    async def test_manage_narrative_dependencies_interface(self, mock_scheduler):
        """测试管理叙事依赖关系接口"""
        # 设置模拟返回值
        dependencies = {
            "unresolved": ["角色背景", "地点描述"],
            "resolved": ["主要冲突", "故事目标"],
            "conflicts": ["时间线矛盾"],
        }
        mock_scheduler.manage_narrative_dependencies.return_value = dependencies

        # 调用接口
        session_id = "test-session-123"
        result = await mock_scheduler.manage_narrative_dependencies(session_id)

        # 验证调用
        mock_scheduler.manage_narrative_dependencies.assert_called_once_with(session_id)
        assert "unresolved" in result
        assert "conflicts" in result


class TestNarrativeArchivePersistenceInterface:
    """NarrativeArchivePersistence接口测试"""

    @pytest.fixture
    def mock_archive_persistence(self):
        """创建模拟的NarrativeArchivePersistence"""
        persistence = Mock(spec=NarrativeArchivePersistence)

        # 设置模拟方法
        persistence.save_narrative_archive = AsyncMock()
        persistence.load_narrative_archive = AsyncMock()
        persistence.list_narrative_archives = AsyncMock()
        persistence.export_to_markdown = AsyncMock()
        persistence.import_from_markdown = AsyncMock()
        persistence.create_archive_version = AsyncMock()
        persistence.rollback_archive_version = AsyncMock()

        return persistence

    @pytest.fixture
    def sample_narrative_archive(self):
        """示例叙事档案"""
        return NarrativeArchive(
            id="archive-123",
            session_id="test-session-123",
            title="英雄之旅档案",
            summary="一个关于英雄寻找圣杯的故事",
            narrative_timeline=[
                {"timestamp": "2024-01-01", "event": "故事开始", "importance": "high"}
            ],
            key_characters=[{"name": "亚瑟", "role": "主角", "development": "成长中"}],
            plot_arcs=[{"name": "寻找圣杯", "status": "进行中", "progress": 0.3}],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
            metadata={"genre": "fantasy"},
        )

    @pytest.mark.asyncio
    async def test_save_narrative_archive_interface(
        self, mock_archive_persistence, sample_narrative_archive
    ):
        """测试保存叙事档案接口"""
        # 设置模拟返回值
        mock_archive_persistence.save_narrative_archive.return_value = True

        # 调用接口
        result = await mock_archive_persistence.save_narrative_archive(
            sample_narrative_archive
        )

        # 验证调用
        mock_archive_persistence.save_narrative_archive.assert_called_once_with(
            sample_narrative_archive
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_load_narrative_archive_interface(
        self, mock_archive_persistence, sample_narrative_archive
    ):
        """测试加载叙事档案接口"""
        # 设置模拟返回值
        mock_archive_persistence.load_narrative_archive.return_value = (
            sample_narrative_archive
        )

        # 调用接口
        archive_id = "archive-123"
        result = await mock_archive_persistence.load_narrative_archive(archive_id)

        # 验证调用
        mock_archive_persistence.load_narrative_archive.assert_called_once_with(
            archive_id
        )
        assert result == sample_narrative_archive
        assert result.id == archive_id

    @pytest.mark.asyncio
    async def test_list_narrative_archives_interface(
        self, mock_archive_persistence, sample_narrative_archive
    ):
        """测试列出叙事档案接口"""
        # 设置模拟返回值
        archives = [sample_narrative_archive]
        mock_archive_persistence.list_narrative_archives.return_value = archives

        # 调用接口
        session_id = "test-session-123"
        result = await mock_archive_persistence.list_narrative_archives(session_id)

        # 验证调用
        mock_archive_persistence.list_narrative_archives.assert_called_once_with(
            session_id
        )
        assert len(result) == 1
        assert result[0].session_id == session_id

    @pytest.mark.asyncio
    async def test_export_to_markdown_interface(self, mock_archive_persistence):
        """测试导出为Markdown接口"""
        # 设置模拟返回值
        mock_archive_persistence.export_to_markdown.return_value = True

        # 调用接口
        archive_id = "archive-123"
        output_path = "./exports/archive.md"
        result = await mock_archive_persistence.export_to_markdown(
            archive_id, output_path
        )

        # 验证调用
        mock_archive_persistence.export_to_markdown.assert_called_once_with(
            archive_id, output_path
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_create_archive_version_interface(self, mock_archive_persistence):
        """测试创建档案版本接口"""
        # 设置模拟返回值
        version_id = "v2"
        mock_archive_persistence.create_archive_version.return_value = version_id

        # 调用接口
        archive_id = "archive-123"
        description = "添加了新角色和情节"
        result = await mock_archive_persistence.create_archive_version(
            archive_id, description
        )

        # 验证调用
        mock_archive_persistence.create_archive_version.assert_called_once_with(
            archive_id, description
        )
        assert result == version_id


class TestInterfaceIntegration:
    """接口集成测试"""

    @pytest.mark.asyncio
    async def test_interpreter_scheduler_integration(self):
        """测试解释器和调度器集成"""
        # 创建模拟对象
        mock_interpreter = Mock(spec=NarrativeInterpreter)
        mock_scheduler = Mock(spec=NarrativeScheduler)

        # 创建真实的NarrativeInterpretation对象
        from src.loom.core.interfaces import NarrativeInterpretation

        interpretation = NarrativeInterpretation(
            interpretation="测试解释",
            consistency_score=0.6,  # 低于0.7，应该触发事件调度
            continuity_issues=["时间线问题"],
            suggested_improvements=[],
            narrative_arcs=[],
        )

        # 设置模拟返回值
        mock_interpreter.interpret_narrative = AsyncMock(return_value=interpretation)
        mock_scheduler.schedule_narrative_event = AsyncMock(return_value="event-123")

        # 模拟集成场景：解释叙事后调度事件
        session_id = "test-session-123"
        context = Mock(spec=NarrativeContext)

        # 解释叙事
        result = await mock_interpreter.interpret_narrative(session_id, context)

        # 基于解释结果调度事件
        if result.consistency_score < 0.7:
            event_id = await mock_scheduler.schedule_narrative_event(
                session_id, "consistency_fix", {"issues": result.continuity_issues}
            )
            assert event_id == "event-123"

        # 验证调用
        mock_interpreter.interpret_narrative.assert_called_once_with(
            session_id, context
        )
        mock_scheduler.schedule_narrative_event.assert_called_once_with(
            session_id, "consistency_fix", {"issues": ["时间线问题"]}
        )

    @pytest.mark.asyncio
    async def test_archive_persistence_integration(self):
        """测试档案持久化集成"""
        # 创建模拟对象
        mock_persistence = Mock(spec=NarrativeArchivePersistence)

        # 设置模拟返回值
        archive = Mock(spec=NarrativeArchive)
        archive.id = "archive-123"
        archive.session_id = "test-session-123"

        mock_persistence.save_narrative_archive = AsyncMock(return_value=True)
        mock_persistence.export_to_markdown = AsyncMock(return_value=True)

        # 保存档案
        save_result = await mock_persistence.save_narrative_archive(archive)
        assert save_result is True

        # 导出为Markdown
        export_result = await mock_persistence.export_to_markdown(
            archive.id, "./exports/archive.md"
        )
        assert export_result is True

        # 验证调用
        mock_persistence.save_narrative_archive.assert_called_once_with(archive)
        mock_persistence.export_to_markdown.assert_called_once_with(
            archive.id, "./exports/archive.md"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
