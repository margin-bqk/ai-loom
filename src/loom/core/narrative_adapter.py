"""
叙事适配器层

提供从旧接口到新接口的适配器，确保向后兼容性。
实现NarrativeInterpreter和NarrativeScheduler接口，包装现有的SessionManager和TurnScheduler。
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logging_config import get_logger
from .interfaces import (
    NarrativeArchive,
    NarrativeConsistencyError,
    NarrativeContext,
    NarrativeInterpretation,
    NarrativeInterpreter,
    NarrativeScheduler,
    Session,
    SessionConfig,
    SessionNotFoundError,
    SessionStatus,
)
from .session_manager import SessionManager as LegacySessionManager
from .turn_scheduler import TurnScheduler as LegacyTurnScheduler

logger = get_logger(__name__)


class NarrativeInterpreterAdapter(NarrativeInterpreter):
    """叙事解释器适配器 - 包装现有的SessionManager"""

    def __init__(self, legacy_session_manager: LegacySessionManager):
        self.legacy_manager = legacy_session_manager
        self._narrative_cache: Dict[str, Dict[str, Any]] = {}
        logger.info("NarrativeInterpreterAdapter initialized")

    async def create_session(self, config: SessionConfig) -> Session:
        """创建新会话 - 委托给legacy manager"""
        # 转换SessionConfig为legacy格式
        legacy_config = self._convert_to_legacy_config(config)
        return await self.legacy_manager.create_session(legacy_config)

    async def load_session(
        self, session_id: str, force_reload: bool = False
    ) -> Optional[Session]:
        """加载会话 - 委托给legacy manager"""
        legacy_session = await self.legacy_manager.load_session(
            session_id, force_reload
        )
        if legacy_session:
            return self._convert_to_interface_session(legacy_session)
        return None

    async def save_session(self, session: Session, force: bool = False) -> bool:
        """保存会话 - 委托给legacy manager"""
        legacy_session = self._convert_to_legacy_session(session)
        return await self.legacy_manager.save_session(legacy_session, force)

    async def delete_session(self, session_id: str, permanent: bool = True) -> bool:
        """删除会话 - 委托给legacy manager"""
        return await self.legacy_manager.delete_session(session_id, permanent)

    async def list_sessions(self, include_inactive: bool = False) -> Dict[str, Session]:
        """列出所有会话 - 委托给legacy manager"""
        legacy_sessions = await self.legacy_manager.list_sessions(include_inactive)
        return {
            session_id: self._convert_to_interface_session(session)
            for session_id, session in legacy_sessions.items()
        }

    async def interpret_narrative(
        self, session_id: str, context: NarrativeContext
    ) -> NarrativeInterpretation:
        """解释叙事上下文，分析一致性和连续性"""
        # 获取会话
        session = await self.load_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # 分析叙事上下文
        consistency_score = await self._analyze_consistency(session, context)
        continuity_issues = await self._check_continuity(session, context)

        # 生成解释
        interpretation = await self._generate_interpretation(session, context)

        # 跟踪叙事弧线
        narrative_arcs = await self.track_narrative_arcs(session_id)

        return NarrativeInterpretation(
            interpretation=interpretation,
            consistency_score=consistency_score,
            continuity_issues=continuity_issues,
            suggested_improvements=self._suggest_improvements(
                consistency_score, continuity_issues
            ),
            narrative_arcs=narrative_arcs,
        )

    async def check_consistency(
        self, session_id: str, new_content: str
    ) -> Tuple[bool, List[str]]:
        """检查新内容与现有叙事的一致性"""
        session = await self.load_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # 简单的一致性检查（可扩展为更复杂的逻辑）
        issues = []

        # 检查角色一致性
        if "character" in new_content.lower():
            # 这里可以添加更复杂的角色一致性检查
            pass

        # 检查时间线一致性
        if "yesterday" in new_content.lower() or "tomorrow" in new_content.lower():
            # 检查时间线冲突
            issues.append("时间线引用可能需要与现有叙事对齐")

        # 检查地点一致性
        if "location" in new_content.lower():
            # 检查地点描述是否一致
            pass

        is_consistent = len(issues) == 0
        return is_consistent, issues

    async def generate_narrative_summary(self, session_id: str) -> str:
        """生成叙事摘要"""
        session = await self.load_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # 从会话状态中提取叙事信息
        state = session.state
        turns = state.get("turns", [])

        if not turns:
            return "尚无叙事内容"

        # 生成简单摘要
        summary_parts = []
        summary_parts.append(f"会话: {session.name}")
        summary_parts.append(f"状态: {session.status.value}")
        summary_parts.append(f"总回合数: {session.total_turns}")

        # 添加关键事件
        if "key_events" in state:
            summary_parts.append("\n关键事件:")
            for i, event in enumerate(state.get("key_events", [])[:5]):
                summary_parts.append(f"  {i+1}. {event.get('description', '未知事件')}")

        # 添加角色
        if "characters" in state:
            characters = state.get("characters", {})
            if characters:
                summary_parts.append("\n主要角色:")
                for char_name, char_data in list(characters.items())[:5]:
                    summary_parts.append(
                        f"  - {char_name}: {char_data.get('role', '未知角色')}"
                    )

        return "\n".join(summary_parts)

    async def track_narrative_arcs(self, session_id: str) -> List[Dict[str, Any]]:
        """跟踪叙事弧线"""
        session = await self.load_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        state = session.state
        arcs = []

        # 从状态中提取叙事弧线
        if "plotlines" in state:
            for plotline in state.get("plotlines", []):
                arcs.append(
                    {
                        "id": plotline.get("id", str(uuid.uuid4())),
                        "name": plotline.get("name", "未命名弧线"),
                        "status": plotline.get("status", "active"),
                        "progress": plotline.get("progress", 0.0),
                        "characters_involved": plotline.get("characters", []),
                        "description": plotline.get("description", ""),
                    }
                )

        # 如果没有显式定义的弧线，尝试从回合中推断
        if not arcs and "turns" in state:
            # 简单实现：将每5个回合作为一个叙事单元
            turns = state.get("turns", [])
            for i in range(0, len(turns), 5):
                arc_turns = turns[i : min(i + 5, len(turns))]
                if arc_turns:
                    arcs.append(
                        {
                            "id": f"arc_{i//5 + 1}",
                            "name": f"叙事单元 {i//5 + 1}",
                            "status": "completed" if i + 5 >= len(turns) else "active",
                            "progress": min(
                                1.0, (i + len(arc_turns)) / max(1, len(turns))
                            ),
                            "turns_count": len(arc_turns),
                            "description": f"包含回合 {i+1} 到 {i+len(arc_turns)}",
                        }
                    )

        return arcs

    # 辅助方法
    def _convert_to_legacy_config(self, config: SessionConfig) -> Any:
        """转换SessionConfig为legacy格式"""
        from .session_manager import SessionConfig as LegacySessionConfig

        return LegacySessionConfig(
            name=config.name,
            canon_path=config.canon_path,
            llm_provider=config.llm_provider,
            max_turns=config.max_turns,
            metadata=config.metadata or {},
        )

    def _convert_to_interface_session(self, legacy_session: Any) -> Session:
        """转换legacy session为接口Session"""
        # 这里需要根据实际legacy session结构进行转换
        # 简化实现：假设legacy session有to_dict方法
        session_dict = (
            legacy_session.to_dict()
            if hasattr(legacy_session, "to_dict")
            else legacy_session
        )

        return Session(
            id=session_dict["id"],
            name=session_dict["name"],
            config=SessionConfig(
                name=session_dict["config"]["name"],
                canon_path=session_dict["config"]["canon_path"],
                llm_provider=session_dict["config"]["llm_provider"],
                max_turns=session_dict["config"].get("max_turns"),
                metadata=session_dict["config"].get("metadata", {}),
            ),
            created_at=datetime.fromisoformat(session_dict["created_at"]),
            updated_at=datetime.fromisoformat(session_dict["updated_at"]),
            status=SessionStatus(session_dict["status"]),
            current_turn=session_dict["current_turn"],
            total_turns=session_dict["total_turns"],
            last_activity=datetime.fromisoformat(session_dict["last_activity"]),
            state=session_dict["state"],
            metadata=session_dict["metadata"],
        )

    def _convert_to_legacy_session(self, session: Session) -> Any:
        """转换接口Session为legacy session"""

        # 这里需要根据实际legacy session结构进行转换
        # 简化实现：返回一个具有to_dict方法的对象
        class LegacySessionWrapper:
            def __init__(self, session: Session):
                self.session = session

            def to_dict(self):
                return {
                    "id": self.session.id,
                    "name": self.session.name,
                    "config": {
                        "name": self.session.config.name,
                        "canon_path": self.session.config.canon_path,
                        "llm_provider": self.session.config.llm_provider,
                        "max_turns": self.session.config.max_turns,
                        "metadata": self.session.config.metadata or {},
                    },
                    "created_at": self.session.created_at.isoformat(),
                    "updated_at": self.session.updated_at.isoformat(),
                    "status": self.session.status.value,
                    "current_turn": self.session.current_turn,
                    "total_turns": self.session.total_turns,
                    "last_activity": self.session.last_activity.isoformat(),
                    "state": self.session.state or {},
                    "metadata": self.session.metadata or {},
                }

        return LegacySessionWrapper(session)

    async def _analyze_consistency(
        self, session: Session, context: NarrativeContext
    ) -> float:
        """分析叙事一致性"""
        # 简单实现：基于会话状态和上下文的匹配度
        state = session.state

        # 检查角色一致性
        character_score = 1.0
        if "characters" in state:
            existing_chars = set(state["characters"].keys())
            context_chars = set(context.characters_present)
            if existing_chars:
                overlap = len(existing_chars.intersection(context_chars)) / len(
                    existing_chars
                )
                character_score = overlap

        # 检查场景一致性
        scene_score = 1.0
        if "current_scene" in state:
            if state["current_scene"] != context.current_scene:
                scene_score = 0.5

        # 综合得分
        return (character_score + scene_score) / 2

    async def _check_continuity(
        self, session: Session, context: NarrativeContext
    ) -> List[str]:
        """检查叙事连续性"""
        issues = []
        state = session.state

        # 检查时间线连续性
        if "timeline" in state:
            last_event = state["timeline"][-1] if state["timeline"] else None
            if last_event and "time" in last_event:
                # 这里可以添加时间线连续性检查
                pass

        # 检查角色发展连续性
        if "character_development" in state:
            # 检查角色发展是否连贯
            pass

        return issues

    async def _generate_interpretation(
        self, session: Session, context: NarrativeContext
    ) -> str:
        """生成叙事解释"""
        # 基于会话状态和上下文生成解释
        state = session.state

        interpretation_parts = []
        interpretation_parts.append(f"叙事解释 - 会话: {session.name}")
        interpretation_parts.append(f"当前场景: {context.current_scene}")
        interpretation_parts.append(
            f"在场角色: {', '.join(context.characters_present)}"
        )
        interpretation_parts.append(f"叙事基调: {context.narrative_tone}")
        interpretation_parts.append(f"叙事节奏: {context.narrative_pace}")

        # 添加叙事弧线信息
        arcs = await self.track_narrative_arcs(session.id)
        if arcs:
            interpretation_parts.append("\n活跃叙事弧线:")
            for arc in arcs[:3]:  # 只显示前3个
                interpretation_parts.append(
                    f"  - {arc['name']}: {arc['status']} (进度: {arc['progress']:.0%})"
                )

        return "\n".join(interpretation_parts)

    def _suggest_improvements(
        self, consistency_score: float, continuity_issues: List[str]
    ) -> List[str]:
        """基于一致性和连续性问题提出改进建议"""
        suggestions = []

        if consistency_score < 0.7:
            suggestions.append("叙事一致性较低，建议检查角色和场景的一致性")

        if continuity_issues:
            suggestions.append(
                f"发现{len(continuity_issues)}个连续性问题，建议审查叙事时间线"
            )

        if consistency_score > 0.9 and not continuity_issues:
            suggestions.append("叙事质量良好，继续保持")

        return suggestions


class NarrativeSchedulerAdapter(NarrativeScheduler):
    """叙事调度器适配器 - 包装现有的TurnScheduler"""

    def __init__(self, legacy_scheduler: LegacyTurnScheduler):
        self.legacy_scheduler = legacy_scheduler
        self._narrative_timelines: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("NarrativeSchedulerAdapter initialized")

    async def schedule_turn(self, session_id: str, player_input: str) -> Any:
        """调度回合 - 委托给legacy scheduler"""
        # 创建回合对象
        from .turn_scheduler import Turn as LegacyTurn

        # 获取当前回合号
        turn_number = await self._get_next_turn_number(session_id)

        # 创建legacy turn
        turn = self.legacy_scheduler.create_turn(
            session_id=session_id, turn_number=turn_number, player_input=player_input
        )

        # 提交到调度器
        turn_id = await self.legacy_scheduler.submit_turn(turn)

        # 等待回合完成
        completed_turn = await self.legacy_scheduler.wait_for_turn(turn_id, timeout=30)

        # 转换为接口格式的TurnResult
        from .interfaces import Turn, TurnResult

        if completed_turn:
            interface_turn = Turn(
                id=completed_turn.id,
                session_id=completed_turn.session_id,
                turn_number=completed_turn.turn_number,
                player_input=completed_turn.player_input,
                llm_response=completed_turn.llm_response or "",
                memories_used=completed_turn.memories_used,
                interventions=completed_turn.interventions,
                timestamp=completed_turn.completed_at or completed_turn.created_at,
                duration_ms=completed_turn.duration_ms or 0,
            )

            return TurnResult(
                turn=interface_turn,
                success=completed_turn.status.value == "completed",
                error_message=completed_turn.error,
                metrics={"duration_ms": completed_turn.duration_ms},
            )

        # 如果回合未完成，返回失败结果
        return TurnResult(
            turn=Turn(
                id=turn_id,
                session_id=session_id,
                turn_number=turn_number,
                player_input=player_input,
                llm_response="",
                memories_used=[],
                interventions=[],
                timestamp=datetime.now(),
                duration_ms=0,
            ),
            success=False,
            error_message="Turn processing timeout",
            metrics={},
        )

    async def get_turn_history(self, session_id: str, limit: int = 100) -> List[Any]:
        """获取回合历史 - 委托给legacy scheduler"""
        legacy_turns = await self.legacy_scheduler.get_session_turns(session_id, limit)

        # 转换为接口格式
        from .interfaces import Turn

        return [
            Turn(
                id=turn.id,
                session_id=turn.session_id,
                turn_number=turn.turn_number,
                player_input=turn.player_input,
                llm_response=turn.llm_response or "",
                memories_used=turn.memories_used,
                interventions=turn.interventions,
                timestamp=turn.completed_at or turn.created_at,
                duration_ms=turn.duration_ms or 0,
            )
            for turn in legacy_turns
        ]

    async def schedule_narrative_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """调度叙事事件（如时间跳跃、场景切换等）"""
        event_id = str(uuid.uuid4())

        # 创建事件记录
        event = {
            "id": event_id,
            "session_id": session_id,
            "type": event_type,
            "data": event_data,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }

        # 添加到叙事时间线
        if session_id not in self._narrative_timelines:
            self._narrative_timelines[session_id] = []

        self._narrative_timelines[session_id].append(event)

        # 根据事件类型处理
        if event_type == "time_skip":
            logger.info(
                f"Scheduled time skip event for session {session_id}: {event_data}"
            )
        elif event_type == "scene_change":
            logger.info(
                f"Scheduled scene change event for session {session_id}: {event_data}"
            )
        elif event_type == "character_entrance":
            logger.info(
                f"Scheduled character entrance event for session {session_id}: {event_data}"
            )
        elif event_type == "character_exit":
            logger.info(
                f"Scheduled character exit event for session {session_id}: {event_data}"
            )
        elif event_type == "plot_twist":
            logger.info(
                f"Scheduled plot twist event for session {session_id}: {event_data}"
            )

        return event_id

    async def get_narrative_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """获取叙事时间线"""
        if session_id not in self._narrative_timelines:
            # 尝试从会话状态中恢复时间线
            await self._recover_timeline_from_session(session_id)

        return self._narrative_timelines.get(session_id, [])

    async def adjust_narrative_pace(self, session_id: str, pace: str) -> bool:
        """调整叙事节奏（slow/normal/fast）"""
        valid_paces = ["slow", "normal", "fast"]
        if pace not in valid_paces:
            logger.warning(
                f"Invalid narrative pace: {pace}. Must be one of {valid_paces}"
            )
            return False

        # 更新叙事时间线中的节奏设置
        if session_id not in self._narrative_timelines:
            self._narrative_timelines[session_id] = []

        # 添加节奏调整事件
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "session_id": session_id,
            "type": "pace_adjustment",
            "data": {"old_pace": "normal", "new_pace": pace},
            "created_at": datetime.now().isoformat(),
            "status": "applied",
        }

        self._narrative_timelines[session_id].append(event)
        logger.info(f"Adjusted narrative pace for session {session_id} to {pace}")

        return True

    async def manage_narrative_dependencies(self, session_id: str) -> Dict[str, Any]:
        """管理叙事依赖关系"""
        timeline = await self.get_narrative_timeline(session_id)

        # 分析依赖关系
        dependencies = {}
        event_map = {event["id"]: event for event in timeline}

        for event in timeline:
            deps = []

            # 基于事件类型推断依赖
            if event["type"] == "scene_change":
                # 场景切换可能依赖于之前的场景
                prev_scene_events = [
                    e
                    for e in timeline
                    if e["type"] == "scene_change" and e["id"] != event["id"]
                ]
                if prev_scene_events:
                    deps.append(prev_scene_events[-1]["id"])

            elif event["type"] == "character_entrance":
                # 角色入场可能依赖于场景
                scene_events = [e for e in timeline if e["type"] == "scene_change"]
                if scene_events:
                    deps.append(scene_events[-1]["id"])

            elif event["type"] == "plot_twist":
                # 情节转折可能依赖于之前的叙事弧线
                plot_events = [
                    e
                    for e in timeline
                    if e["type"] in ["plot_twist", "character_development"]
                ]
                if plot_events:
                    deps.extend([e["id"] for e in plot_events[-2:]])

            if deps:
                dependencies[event["id"]] = {
                    "event": event,
                    "dependencies": deps,
                    "dependency_status": self._check_dependency_status(deps, event_map),
                }

        return {
            "session_id": session_id,
            "total_events": len(timeline),
            "events_with_dependencies": len(dependencies),
            "dependency_graph": dependencies,
        }

    # 辅助方法
    async def _get_next_turn_number(self, session_id: str) -> int:
        """获取下一个回合号"""
        # 这里需要从会话或持久化存储中获取当前回合号
        # 简化实现：从legacy scheduler获取
        turns = await self.legacy_scheduler.get_session_turns(session_id, limit=1)
        if turns:
            return turns[0].turn_number + 1
        return 1

    async def _recover_timeline_from_session(self, session_id: str):
        """从会话状态中恢复时间线"""
        # 这里需要从会话状态中提取叙事时间线
        # 简化实现：创建空时间线
        self._narrative_timelines[session_id] = []

        # 可以添加从持久化存储恢复的逻辑
        logger.debug(f"Created empty narrative timeline for session {session_id}")

    def _check_dependency_status(
        self, dependency_ids: List[str], event_map: Dict[str, Dict]
    ) -> Dict[str, str]:
        """检查依赖状态"""
        status = {}
        for dep_id in dependency_ids:
            if dep_id in event_map:
                dep_event = event_map[dep_id]
                status[dep_id] = dep_event.get("status", "unknown")
            else:
                status[dep_id] = "missing"
        return status
