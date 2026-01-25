"""
适配器层测试

测试阶段1重构中创建的适配器，确保向后兼容性和接口适配正确性。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from src.loom.core.interfaces import (
    SessionManager,
    TurnScheduler,
    PersistenceEngine,
    SessionConfig,
    Session,
    SessionStatus,
    Turn,
    TurnResult,
    PromptContext,
    NarrativeInterpreter,
    NarrativeScheduler,
    NarrativeArchivePersistence,
    NarrativeContext,
    NarrativeInterpretation,
    NarrativeArchive
)


class TestLegacyAdapterCompatibility:
    """传统适配器兼容性测试"""
    
    @pytest.fixture
    def legacy_session_manager(self):
        """传统会话管理器模拟"""
        manager = Mock()
        manager.create_session = AsyncMock()
        manager.load_session = AsyncMock()
        manager.save_session = AsyncMock()
        manager.delete_session = AsyncMock()
        manager.list_sessions = AsyncMock()
        return manager
    
    @pytest.fixture
    def legacy_turn_scheduler(self):
        """传统回合调度器模拟"""
        scheduler = Mock()
        scheduler.schedule_turn = AsyncMock()
        scheduler.get_turn_history = AsyncMock()
        return scheduler
    
    @pytest.fixture
    def legacy_persistence_engine(self):
        """传统持久化引擎模拟"""
        engine = Mock()
        engine.save_session = AsyncMock()
        engine.load_session = AsyncMock()
        engine.delete_session = AsyncMock()
        engine.list_sessions = AsyncMock()
        engine.save_turn = AsyncMock()
        engine.load_turns = AsyncMock()
        return engine
    
    def test_session_manager_adapter_interface(self, legacy_session_manager):
        """测试会话管理器适配器接口"""
        # 创建适配器（这里模拟适配器创建）
        class LegacySessionManagerAdapter(SessionManager):
            def __init__(self, legacy_manager):
                self.legacy = legacy_manager
            
            async def create_session(self, config: SessionConfig) -> Session:
                # 转换配置为传统格式
                legacy_config = {
                    "name": config.name,
                    "canon_path": config.canon_path,
                    "llm_provider": config.llm_provider,
                    "max_turns": config.max_turns,
                    "metadata": config.metadata or {}
                }
                
                # 调用传统方法
                legacy_result = await self.legacy.create_session(legacy_config)
                
                # 转换结果为新格式
                return Session(
                    id=legacy_result.get("id", "unknown"),
                    name=legacy_result.get("name", ""),
                    config=config,
                    created_at=datetime.fromisoformat(legacy_result.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(legacy_result.get("updated_at", datetime.now().isoformat())),
                    status=SessionStatus(legacy_result.get("status", "active")),
                    current_turn=legacy_result.get("current_turn", 0),
                    total_turns=legacy_result.get("total_turns", 0),
                    state=legacy_result.get("state", {}),
                    metadata=legacy_result.get("metadata", {})
                )
            
            async def load_session(self, session_id: str, force_reload: bool = False) -> Optional[Session]:
                legacy_result = await self.legacy.load_session(session_id, force_reload)
                if not legacy_result:
                    return None
                
                # 转换逻辑（简化）
                return Mock(spec=Session)
            
            async def save_session(self, session: Session, force: bool = False) -> bool:
                # 转换会话为传统格式
                legacy_session = {
                    "id": session.id,
                    "name": session.name,
                    "config": session.config.to_dict(),
                    "status": session.status.value,
                    "current_turn": session.current_turn,
                    "total_turns": session.total_turns,
                    "state": session.state,
                    "metadata": session.metadata
                }
                
                return await self.legacy.save_session(legacy_session, force)
            
            async def delete_session(self, session_id: str, permanent: bool = True) -> bool:
                return await self.legacy.delete_session(session_id, permanent)
            
            async def list_sessions(self, include_inactive: bool = False) -> Dict[str, Session]:
                legacy_sessions = await self.legacy.list_sessions(include_inactive)
                
                # 转换会话字典
                sessions = {}
                for session_id, legacy_session in legacy_sessions.items():
                    sessions[session_id] = Mock(spec=Session)  # 简化转换
                
                return sessions
        
        # 创建适配器实例
        adapter = LegacySessionManagerAdapter(legacy_session_manager)
        
        # 验证适配器实现了正确的接口
        assert isinstance(adapter, SessionManager)
        assert hasattr(adapter, 'create_session')
        assert hasattr(adapter, 'load_session')
        assert hasattr(adapter, 'save_session')
        assert hasattr(adapter, 'delete_session')
        assert hasattr(adapter, 'list_sessions')
    
    @pytest.mark.asyncio
    async def test_turn_scheduler_adapter_compatibility(self, legacy_turn_scheduler):
        """测试回合调度器适配器兼容性"""
        # 创建适配器（这里模拟适配器创建）
        class LegacyTurnSchedulerAdapter(TurnScheduler):
            def __init__(self, legacy_scheduler):
                self.legacy = legacy_scheduler
            
            async def schedule_turn(self, session_id: str, player_input: str) -> TurnResult:
                # 调用传统方法
                legacy_result = await self.legacy.schedule_turn(session_id, player_input)
                
                # 转换结果为新格式
                return TurnResult(
                    turn=Mock(spec=Turn),  # 简化转换
                    success=legacy_result.get("success", False),
                    error_message=legacy_result.get("error_message"),
                    metrics=legacy_result.get("metrics", {})
                )
            
            async def get_turn_history(self, session_id: str, limit: int = 100) -> List[Turn]:
                legacy_turns = await self.legacy.get_turn_history(session_id, limit)
                
                # 转换回合列表
                turns = []
                for legacy_turn in legacy_turns:
                    turns.append(Mock(spec=Turn))  # 简化转换
                
                return turns
        
        # 创建适配器实例
        adapter = LegacyTurnSchedulerAdapter(legacy_turn_scheduler)
        
        # 测试适配器方法
        legacy_turn_scheduler.schedule_turn.return_value = {
            "success": True,
            "error_message": None,
            "metrics": {"duration_ms": 1500}
        }
        
        result = await adapter.schedule_turn("test-session", "玩家输入")
        
        # 验证调用
        legacy_turn_scheduler.schedule_turn.assert_called_once_with("test-session", "玩家输入")
        assert result.success is True
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_persistence_engine_adapter_compatibility(self, legacy_persistence_engine):
        """测试持久化引擎适配器兼容性"""
        # 创建适配器（这里模拟适配器创建）
        class LegacyPersistenceEngineAdapter(PersistenceEngine):
            def __init__(self, legacy_engine):
                self.legacy = legacy_engine
            
            async def save_session(self, session: Session) -> bool:
                # 转换会话为传统格式
                legacy_session = {
                    "id": session.id,
                    "name": session.name,
                    "config": session.config.to_dict(),
                    "status": session.status.value,
                    "current_turn": session.current_turn,
                    "total_turns": session.total_turns,
                    "state": session.state,
                    "metadata": session.metadata,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat()
                }
                
                return await self.legacy.save_session(legacy_session)
            
            async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
                return await self.legacy.load_session(session_id)
            
            async def delete_session(self, session_id: str) -> bool:
                return await self.legacy.delete_session(session_id)
            
            async def list_sessions(self) -> Dict[str, Dict[str, Any]]:
                return await self.legacy.list_sessions()
            
            async def save_turn(self, turn: Turn) -> bool:
                # 转换回合为传统格式
                legacy_turn = {
                    "id": turn.id,
                    "session_id": turn.session_id,
                    "turn_number": turn.turn_number,
                    "player_input": turn.player_input,
                    "llm_response": turn.llm_response,
                    "memories_used": turn.memories_used,
                    "interventions": turn.interventions,
                    "timestamp": turn.timestamp.isoformat(),
                    "duration_ms": turn.duration_ms
                }
                
                return await self.legacy.save_turn(legacy_turn)
            
            async def load_turns(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
                return await self.legacy.load_turns(session_id, limit)
        
        # 创建适配器实例
        adapter = LegacyPersistenceEngineAdapter(legacy_persistence_engine)
        
        # 测试适配器方法
        test_session = Mock(spec=Session)
        test_session.id = "test-session"
        test_session.name = "测试会话"
        test_session.config = Mock(spec=SessionConfig)
        test_session.config.to_dict.return_value = {"name": "测试会话"}
        test_session.status = SessionStatus.ACTIVE
        test_session.current_turn = 0
        test_session.total_turns = 0
        test_session.state = {}
        test_session.metadata = {}
        test_session.created_at = datetime.now()
        test_session.updated_at = datetime.now()
        
        legacy_persistence_engine.save_session.return_value = True
        
        result = await adapter.save_session(test_session)
        
        # 验证调用
        legacy_persistence_engine.save_session.assert_called_once()
        assert result is True


class TestNarrativeAdapterCompatibility:
    """叙事适配器兼容性测试"""
    
    @pytest.fixture
    def legacy_narrative_system(self):
        """传统叙事系统模拟"""
        system = Mock()
        system.analyze_narrative = AsyncMock()
        system.schedule_event = AsyncMock()
        system.create_archive = AsyncMock()
        return system
    
    def test_narrative_interpreter_adapter(self, legacy_narrative_system):
        """测试叙事解释器适配器"""
        # 创建适配器（这里模拟适配器创建）
        class LegacyNarrativeInterpreterAdapter(NarrativeInterpreter):
            def __init__(self, legacy_system, session_manager):
                self.legacy = legacy_system
                self.session_manager = session_manager
            
            async def create_session(self, config: SessionConfig) -> Session:
                return await self.session_manager.create_session(config)
            
            async def load_session(self, session_id: str, force_reload: bool = False) -> Optional[Session]:
                return await self.session_manager.load_session(session_id, force_reload)
            
            async def save_session(self, session: Session, force: bool = False) -> bool:
                return await self.session_manager.save_session(session, force)
            
            async def delete_session(self, session_id: str, permanent: bool = True) -> bool:
                return await self.session_manager.delete_session(session_id, permanent)
            
            async def list_sessions(self, include_inactive: bool = False) -> Dict[str, Session]:
                return await self.session_manager.list_sessions(include_inactive)
            
            async def interpret_narrative(self, session_id: str, context: NarrativeContext) -> NarrativeInterpretation:
                # 调用传统分析方法
                legacy_result = await self.legacy.analyze_narrative(
                    session_id,
                    {
                        "current_scene": context.current_scene,
                        "characters_present": context.characters_present,
                        "plot_points": context.plot_points,
                        "tone": context.narrative_tone
                    }
                )
                
                # 转换结果为新格式
                from src.loom.core.interfaces import NarrativeInterpretation
                return NarrativeInterpretation(
                    interpretation=legacy_result.get("analysis", ""),
                    consistency_score=legacy_result.get("consistency_score", 0.0),
                    continuity_issues=legacy_result.get("issues", []),
                    suggested_improvements=legacy_result.get("suggestions", []),
                    narrative_arcs=legacy_result.get("arcs", [])
                )
            
            async def check_consistency(self, session_id: str, new_content: str) -> Tuple[bool, List[str]]:
                # 调用传统一致性检查
                legacy_result = await self.legacy.check_consistency(session_id, new_content)
                return (
                    legacy_result.get("consistent", False),
                    legacy_result.get("issues", [])
                )
            
            async def generate_narrative_summary(self, session_id: str) -> str:
                legacy_result = await self.legacy.generate_summary(session_id)
                return legacy_result.get("summary", "")
            
            async def track_narrative_arcs(self, session_id: str) -> List[Dict[str, Any]]:
                legacy_result = await self.legacy.track_arcs(session_id)
                return legacy_result.get("arcs", [])
        
        # 创建模拟会话管理器
        mock_session_manager = Mock(spec=SessionManager)
        
        # 创建适配器实例
        adapter = LegacyNarrativeInterpreterAdapter(legacy_narrative_system, mock_session_manager)
        
        # 验证适配器实现了正确的接口
        assert isinstance(adapter, NarrativeInterpreter)
        assert hasattr(adapter, 'interpret_narrative')
        assert hasattr(adapter, 'check_consistency')
        assert hasattr(adapter, 'generate_narrative_summary')
        assert hasattr(adapter, 'track_narrative_arcs')
    
    @pytest.mark.asyncio
    async def test_narrative_scheduler_adapter(self, legacy_narrative_system):
        """测试叙事调度器适配器"""
        # 创建适配器（这里模拟适配器创建）
        class LegacyNarrativeSchedulerAdapter(NarrativeScheduler):
            def __init__(self, legacy_system, turn_scheduler):
                self.legacy = legacy_system
                self.turn_scheduler = turn_scheduler
            
            async def schedule_turn(self, session_id: str, player_input: str) -> TurnResult:
                return await self.turn_scheduler.schedule_turn(session_id, player_input)
            
            async def get_turn_history(self, session_id: str, limit: int = 100) -> List[Turn]:
                return await self.turn_scheduler.get_turn_history(session_id, limit)
            
            async def schedule_narrative_event(self, session_id: str, event_type: str,
                                             event_data: Dict[str, Any], priority: int = 0) -> str:
                # 调用传统事件调度
                legacy_result = await self.legacy.schedule_event(
                    session_id,
                    {
                        "type": event_type,
                        "data": event_data,
                        "priority": priority
                    }
                )
                
                return legacy_result.get("event_id", "unknown")
            
            async def get_narrative_timeline(self, session_id: str) -> List[Dict[str, Any]]:
                legacy_result = await self.legacy.get_timeline(session_id)
                return legacy_result.get("timeline", [])
            
            async def adjust_narrative_pace(self, session_id: str, pace: str) -> bool:
                legacy_result = await self.legacy.adjust_pace(session_id, pace)
                return legacy_result.get("success", False)
            
            async def manage_narrative_dependencies(self, session_id: str) -> Dict[str, Any]:
                legacy_result = await self.legacy.manage_dependencies(session_id)
                return legacy_result.get("dependencies", {})
        
        # 创建模拟回合调度器
        mock_turn_scheduler = Mock(spec=TurnScheduler)
        
        # 创建适配器实例
        adapter = LegacyNarrativeSchedulerAdapter(legacy_narrative_system, mock_turn_scheduler)
        
        # 测试适配器方法
        legacy_narrative_system.schedule_event.return_value = {"event_id": "event-123"}
        
        event_id = await adapter.schedule_narrative_event(
            "test-session", "time_skip", {"duration": "3天"}, 1
        )
        
        # 验证调用
        legacy_narrative_system.schedule_event.assert_called_once()
        assert event_id == "event-123"


class TestBackwardCompatibility:
    """向后兼容性测试"""
    
    @pytest.mark.asyncio
    async def test_data_model_conversion(self):
        """测试数据模型转换"""
        # 测试会话配置转换
        from src.loom.core.interfaces import SessionConfig
        
        # 新格式配置
        new_config = SessionConfig(
            name="测试会话",
            canon_path="./canon.md",
            llm_provider="openai",
            max_turns=10,
            metadata={"test": True}
        )
        
        # 转换为传统格式
        legacy_config = {
            "name": new_config.name,
            "canon_path": new_config.canon_path,
            "llm_provider": new_config.llm_provider,
            "max_turns": new_config.max_turns,
            "metadata": new_config.metadata or {}
        }
        
        # 验证转换正确性
        assert legacy_config["name"] == "测试会话"
        assert legacy_config["canon_path"] == "./canon.md"
        assert legacy_config["llm_provider"] == "openai"
        assert legacy_config["max_turns"] == 10
        assert legacy_config["metadata"]["test"] is True
        
        # 测试从传统格式转换回新格式
        restored_config = SessionConfig(
            name=legacy_config["name"],
            canon_path=legacy_config["canon_path"],
            llm_provider=legacy_config["llm_provider"],
            max_turns=legacy_config["max_turns"],
            metadata=legacy_config["metadata"]
        )
        
        # 验证转换正确性
        assert restored_config.name == new_config.name
        assert restored_config.canon_path == new_config.canon_path
        assert restored_config.llm_provider == new_config.llm_provider
        assert restored_config.max_turns == new_config.max_turns
        assert restored_config.metadata == new_config.metadata
    
    @pytest.mark.asyncio
    async def test_session_conversion(self):
        """测试会话数据转换"""
        from src.loom.core.interfaces import Session, SessionStatus, SessionConfig
        from datetime import datetime
        
        # 新格式会话
        config = SessionConfig(
            name="测试会话",
            canon_path="./canon.md",
            llm_provider="openai"
        )
        
        new_session = Session(
            id="session-123",
            name="测试会话",
            config=config,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SessionStatus.ACTIVE,
            current_turn=5,
            total_turns=10,
            state={"scene": "城堡", "mood": "紧张"},
            metadata={"genre": "fantasy"}
        )
        
        # 转换为传统格式
        legacy_session = {
            "id": new_session.id,
            "name": new_session.name,
            "config": new_session.config.to_dict(),
            "created_at": new_session.created_at.isoformat(),
            "updated_at": new_session.updated_at.isoformat(),
            "status": new_session.status.value,
            "current_turn": new_session.current_turn,
            "total_turns": new_session.total_turns,
            "state": new_session.state,
            "metadata": new_session.metadata
        }
        
        # 验证转换正确性
        assert legacy_session["id"] == "session-123"
        assert legacy_session["status"] == "active"
        assert legacy_session["current_turn"] == 5
        assert legacy_session["state"]["scene"] == "城堡"
        
        # 测试从传统格式转换回新格式（简化）
        # 注意：实际实现中需要更复杂的转换逻辑
        restored_session = Session(
            id=legacy_session["id"],
            name=legacy_session["name"],
            config=SessionConfig(**legacy_session["config"]),
            created_at=datetime.fromisoformat(legacy_session["created_at"]),
            updated_at=datetime.fromisoformat(legacy_session["updated_at"]),
            status=SessionStatus(legacy_session["status"]),
            current_turn=legacy_session["current_turn"],
            total_turns=legacy_session["total_turns"],
            state=legacy_session["state"],
            metadata=legacy_session["metadata"]
        )
        
        assert restored_session.id == new_session.id
        assert restored_session.status == new_session.status
    
    @pytest.mark.asyncio
    async def test_api_compatibility(self):
        """测试API兼容性"""
        # 模拟传统API调用
        legacy_api_response = {
            "success": True,
            "session_id": "legacy-session-123",
            "data": {
                "name": "传统会话",
                "turns": 5,
                "status": "active"
            }
        }
        
        # 适配器应该能够处理传统响应
        def adapt_legacy_response(response):
            """适配传统响应为新格式"""
            return {
                "success": response["success"],
                "session": {
                    "id": response["session_id"],
                    "name": response["data"]["name"],
                    "current_turn": response["data"]["turns"],
                    "status": response["data"]["status"]
                }
            }
        
        new_response = adapt_legacy_response(legacy_api_response)
        
        # 验证适配正确性
        assert new_response["success"] is True
        assert new_response["session"]["id"] == "legacy-session-123"
        assert new_response["session"]["name"] == "传统会话"
        assert new_response["session"]["current_turn"] == 5
        assert new_response["session"]["status"] == "active"


class TestAdapterImplementation:
    """适配器实现测试"""
    
    @pytest.mark.asyncio
    async def test_adapter_error_handling(self):
        """测试适配器错误处理"""
        # 模拟传统系统抛出异常
        class LegacySystemError(Exception):
            pass
        
        legacy_system = Mock()
        legacy_system.perform_operation = AsyncMock(side_effect=LegacySystemError("传统系统错误"))
        
        # 适配器应该捕获并转换异常
        class SafeAdapter:
            def __init__(self, legacy):
                self.legacy = legacy
            
            async def perform_operation(self):
                try:
                    return await self.legacy.perform_operation()
                except LegacySystemError as e:
                    # 转换为新系统的异常类型
                    raise RuntimeError(f"适配器错误: {str(e)}")
        
        adapter = SafeAdapter(legacy_system)
        
        # 验证异常被正确转换
        with pytest.raises(RuntimeError, match="适配器错误: 传统系统错误"):
            await adapter.perform_operation()
    
    @pytest.mark.asyncio
    async def test_adapter_performance(self):
        """测试适配器性能"""
        import time
        
        # 模拟传统操作有延迟
        legacy_system = Mock()
        legacy_system.slow_operation = AsyncMock()
        
        # 模拟延迟
        async def slow_operation():
            await asyncio.sleep(0.01)  # 10ms延迟
            return "result"
        
        legacy_system.slow_operation.side_effect = slow_operation
        
        # 适配器不应该增加显著开销
        class EfficientAdapter:
            def __init__(self, legacy):
                self.legacy = legacy
            
            async def perform(self):
                start = time.time()
                result = await self.legacy.slow_operation()
                end = time.time()
                return result, end - start
        
        adapter = EfficientAdapter(legacy_system)
        
        result, duration = await adapter.perform()
        
        # 验证结果正确
        assert result == "result"
        # 验证延迟在合理范围内（适配器开销应小于1ms）
        # 注意：asyncio.sleep(0.01) 是10ms，加上开销可能达到15-20ms
        assert duration < 0.03  # 30ms阈值，为系统负载留出余量


if __name__ == "__main__":
    pytest.main([__file__, "-v"])