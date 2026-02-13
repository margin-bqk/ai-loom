"""
玩家干预处理

解析和处理玩家干预，包括OOC注释、世界编辑、Retcon等。
"""

import re
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class InterventionType(Enum):
    """干预类型"""

    OOC = "ooc"  # OOC注释
    WORLD_EDIT = "world_edit"  # 世界编辑
    RETCON = "retcon"  # Retcon
    TONE_ADJUST = "tone_adjust"  # 基调调整
    INTENT_DECLARE = "intent_declare"  # 意图声明
    META_COMMENT = "meta_comment"  # 元注释
    UNKNOWN = "unknown"  # 未知类型


class InterventionPriority(IntEnum):
    """干预优先级"""

    CRITICAL = 100  # 紧急干预（如安全相关）
    HIGH = 80  # 高优先级（如Retcon、世界编辑）
    MEDIUM = 50  # 中优先级（如基调调整）
    LOW = 20  # 低优先级（如意图声明）
    BACKGROUND = 1  # 后台优先级（如OOC、元注释）


@dataclass
class Intervention:
    """干预"""

    type: InterventionType
    content: str
    raw_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    position: Optional[int] = None  # 在原始文本中的位置
    priority: InterventionPriority = InterventionPriority.MEDIUM  # 干预优先级
    urgency: int = 0  # 紧急程度（0-100）
    scope: str = "local"  # 影响范围：local, session, global


@dataclass
class InterventionResult:
    """干预处理结果"""

    success: bool
    intervention: Intervention
    narrative_impact: str  # 对叙事的影响描述
    actions_taken: List[Dict[str, Any]]
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class PlayerIntervention:
    """玩家干预处理器"""

    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.priority_map = self._initialize_priority_map()
        self.conflict_rules = self._initialize_conflict_rules()
        logger.info("PlayerIntervention initialized")

    def _initialize_patterns(self) -> Dict[InterventionType, re.Pattern]:
        """初始化干预模式"""
        return {
            InterventionType.OOC: re.compile(
                r"\(OOC:\s*(.*?)\)", re.IGNORECASE | re.DOTALL
            ),
            InterventionType.WORLD_EDIT: re.compile(
                r"\[EDIT:\s*(.*?)\]", re.IGNORECASE | re.DOTALL
            ),
            InterventionType.RETCON: re.compile(
                r"\[RETCON:\s*(.*?)\]", re.IGNORECASE | re.DOTALL
            ),
            InterventionType.TONE_ADJUST: re.compile(
                r"\[TONE:\s*(.*?)\]", re.IGNORECASE | re.DOTALL
            ),
            InterventionType.INTENT_DECLARE: re.compile(
                r"\[INTENT:\s*(.*?)\]", re.IGNORECASE | re.DOTALL
            ),
            InterventionType.META_COMMENT: re.compile(
                r"\[META:\s*(.*?)\]", re.IGNORECASE | re.DOTALL
            ),
        }

    def _initialize_priority_map(self) -> Dict[InterventionType, InterventionPriority]:
        """初始化干预类型优先级映射"""
        return {
            InterventionType.RETCON: InterventionPriority.HIGH,
            InterventionType.WORLD_EDIT: InterventionPriority.HIGH,
            InterventionType.TONE_ADJUST: InterventionPriority.MEDIUM,
            InterventionType.INTENT_DECLARE: InterventionPriority.LOW,
            InterventionType.OOC: InterventionPriority.BACKGROUND,
            InterventionType.META_COMMENT: InterventionPriority.BACKGROUND,
            InterventionType.UNKNOWN: InterventionPriority.LOW,
        }

    def _initialize_conflict_rules(
        self,
    ) -> List[Tuple[InterventionType, InterventionType, str]]:
        """初始化冲突规则"""
        return [
            (
                InterventionType.RETCON,
                InterventionType.WORLD_EDIT,
                "Retcon和世界编辑可能冲突",
            ),
            (
                InterventionType.WORLD_EDIT,
                InterventionType.RETCON,
                "世界编辑和Retcon可能冲突",
            ),
            (
                InterventionType.TONE_ADJUST,
                InterventionType.INTENT_DECLARE,
                "基调调整和意图声明可能冲突",
            ),
        ]

    def parse_input(self, player_input: str) -> Dict[str, Any]:
        """解析玩家输入，提取干预"""
        result = {
            "clean_input": player_input,
            "interventions": [],
            "has_interventions": False,
            "conflicts": [],
        }

        interventions = []
        clean_input = player_input

        # 查找所有干预
        for interv_type, pattern in self.patterns.items():
            matches = list(pattern.finditer(player_input))
            for match in matches:
                content = match.group(1).strip()

                # 设置优先级
                priority = self.priority_map.get(
                    interv_type, InterventionPriority.MEDIUM
                )

                intervention = Intervention(
                    type=interv_type,
                    content=content,
                    raw_text=match.group(0),
                    position=match.start(),
                    priority=priority,
                    urgency=self._detect_urgency(content),
                    scope=self._detect_scope(content, interv_type),
                )

                interventions.append(intervention)

                # 从clean_input中移除干预文本
                clean_input = clean_input.replace(match.group(0), "")

        # 按位置排序
        interventions.sort(key=lambda x: x.position if x.position is not None else 0)

        # 检测冲突
        conflicts = self._detect_conflicts(interventions)

        result["interventions"] = interventions
        result["has_interventions"] = len(interventions) > 0
        result["clean_input"] = clean_input.strip()
        result["conflicts"] = conflicts

        logger.debug(
            f"Parsed input: found {len(interventions)} interventions, {len(conflicts)} conflicts"
        )
        for interv in interventions:
            logger.debug(
                f"  - {interv.type.value} (priority={interv.priority.name}): {interv.content[:50]}..."
            )

        return result

    def _detect_urgency(self, content: str) -> int:
        """检测紧急程度"""
        urgency_keywords = {
            "紧急": 90,
            "立刻": 80,
            "马上": 70,
            "立即": 70,
            "尽快": 60,
            "重要": 50,
            "请": 30,
        }

        content_lower = content.lower()
        max_urgency = 0
        for keyword, score in urgency_keywords.items():
            if keyword in content_lower:
                max_urgency = max(max_urgency, score)

        return max_urgency

    def _detect_scope(self, content: str, interv_type: InterventionType) -> str:
        """检测影响范围"""
        if interv_type in [InterventionType.RETCON, InterventionType.WORLD_EDIT]:
            # 检查是否影响全局
            global_keywords = ["全局", "所有", "整个", "世界", "全部"]
            content_lower = content.lower()
            if any(keyword in content_lower for keyword in global_keywords):
                return "global"
            return "session"
        return "local"

    def _detect_conflicts(
        self, interventions: List[Intervention]
    ) -> List[Dict[str, Any]]:
        """检测干预之间的冲突"""
        conflicts = []

        if len(interventions) < 2:
            return conflicts

        for i, interv1 in enumerate(interventions):
            for j, interv2 in enumerate(interventions[i + 1 :], i + 1):
                # 检查冲突规则
                for rule in self.conflict_rules:
                    type1, type2, reason = rule
                    if (interv1.type == type1 and interv2.type == type2) or (
                        interv1.type == type2 and interv2.type == type1
                    ):
                        conflicts.append(
                            {
                                "intervention1": interv1.type.value,
                                "intervention2": interv2.type.value,
                                "reason": reason,
                                "positions": (interv1.position, interv2.position),
                            }
                        )

        return conflicts

    def prioritize_interventions(
        self, interventions: List[Intervention]
    ) -> List[Intervention]:
        """按优先级排序干预"""

        # 计算综合优先级分数：基础优先级 + 紧急程度
        def priority_score(interv: Intervention) -> int:
            base_score = interv.priority.value * 10
            urgency_bonus = interv.urgency
            return base_score + urgency_bonus

        return sorted(interventions, key=priority_score, reverse=True)

    async def process_interventions(
        self, interventions: List[Intervention], session_context: Dict[str, Any]
    ) -> List[InterventionResult]:
        """处理干预列表"""
        results = []

        # 按优先级排序
        prioritized = self.prioritize_interventions(interventions)

        for intervention in prioritized:
            result = await self._process_single_intervention(
                intervention, session_context
            )
            results.append(result)

            logger.info(
                f"Processed {intervention.type.value} intervention (priority={intervention.priority.name}): {result.success}"
            )
            if not result.success:
                logger.warning(f"Intervention failed: {result.errors}")

        return results

    async def _process_single_intervention(
        self, intervention: Intervention, session_context: Dict[str, Any]
    ) -> InterventionResult:
        """处理单个干预"""
        try:
            handler_method = getattr(self, f"_handle_{intervention.type.value}", None)
            if not handler_method:
                return InterventionResult(
                    success=False,
                    intervention=intervention,
                    narrative_impact="不支持此干预类型",
                    actions_taken=[],
                    errors=[
                        f"Unsupported intervention type: {intervention.type.value}"
                    ],
                )

            return await handler_method(intervention, session_context)

        except Exception as e:
            logger.error(f"Error processing intervention: {e}")
            return InterventionResult(
                success=False,
                intervention=intervention,
                narrative_impact="处理干预时发生错误",
                actions_taken=[],
                errors=[str(e)],
            )

    async def _handle_ooc(
        self, intervention: Intervention, session_context: Dict[str, Any]
    ) -> InterventionResult:
        """处理OOC注释"""
        # OOC注释不影响叙事，仅记录
        return InterventionResult(
            success=True,
            intervention=intervention,
            narrative_impact="OOC注释不影响叙事",
            actions_taken=[{"action": "log_ooc", "content": intervention.content}],
            warnings=["OOC注释将被记录但不影响叙事"],
        )

    async def _handle_world_edit(
        self, intervention: Intervention, session_context: Dict[str, Any]
    ) -> InterventionResult:
        """处理世界编辑"""
        # 解析编辑指令
        edit_parts = intervention.content.split(":", 1)
        if len(edit_parts) < 2:
            return InterventionResult(
                success=False,
                intervention=intervention,
                narrative_impact="世界编辑格式错误",
                actions_taken=[],
                errors=["世界编辑格式应为: [EDIT: 目标: 修改内容]"],
            )

        target = edit_parts[0].strip()
        change = edit_parts[1].strip()

        return InterventionResult(
            success=True,
            intervention=intervention,
            narrative_impact=f"世界编辑: {target} -> {change}",
            actions_taken=[
                {"action": "world_edit", "target": target, "change": change}
            ],
        )

    async def _handle_retcon(
        self, intervention: Intervention, session_context: Dict[str, Any]
    ) -> InterventionResult:
        """处理Retcon"""
        # Retcon需要更复杂的处理
        return InterventionResult(
            success=True,
            intervention=intervention,
            narrative_impact=f"Retcon: {intervention.content}",
            actions_taken=[{"action": "retcon", "content": intervention.content}],
            warnings=["Retcon可能影响叙事一致性，请谨慎使用"],
        )

    async def _handle_tone_adjust(
        self, intervention: Intervention, session_context: Dict[str, Any]
    ) -> InterventionResult:
        """处理基调调整"""
        tone_change = intervention.content

        return InterventionResult(
            success=True,
            intervention=intervention,
            narrative_impact=f"叙事基调调整为: {tone_change}",
            actions_taken=[{"action": "tone_adjust", "new_tone": tone_change}],
        )

    async def _handle_intent_declare(
        self, intervention: Intervention, session_context: Dict[str, Any]
    ) -> InterventionResult:
        """处理意图声明"""
        intent = intervention.content

        return InterventionResult(
            success=True,
            intervention=intervention,
            narrative_impact=f"玩家意图: {intent}",
            actions_taken=[{"action": "intent_declare", "intent": intent}],
        )

    async def _handle_meta_comment(
        self, intervention: Intervention, session_context: Dict[str, Any]
    ) -> InterventionResult:
        """处理元注释"""
        return InterventionResult(
            success=True,
            intervention=intervention,
            narrative_impact="元注释不影响叙事",
            actions_taken=[{"action": "log_meta", "content": intervention.content}],
        )

    async def validate_permission(
        self, intervention: Intervention, rules_text: str
    ) -> bool:
        """验证干预权限"""
        # 简化实现：检查规则中是否有权限限制
        if (
            "禁止编辑" in rules_text
            and intervention.type == InterventionType.WORLD_EDIT
        ):
            return False

        if "禁止Retcon" in rules_text and intervention.type == InterventionType.RETCON:
            return False

        return True

    def merge_interventions_into_prompt(
        self, clean_input: str, intervention_results: List[InterventionResult]
    ) -> str:
        """将干预合并到Prompt中"""
        if not intervention_results:
            return clean_input

        intervention_texts = []

        for result in intervention_results:
            if not result.success:
                continue

            interv = result.intervention
            if interv.type == InterventionType.OOC:
                # OOC注释通常不合并到Prompt
                continue

            intervention_texts.append(
                f"[{interv.type.value.upper()}: {interv.content}]"
            )

        if not intervention_texts:
            return clean_input

        interventions_str = "\n".join(intervention_texts)
        return f"{clean_input}\n\n玩家干预:\n{interventions_str}"

    async def audit_intervention(
        self,
        intervention: Intervention,
        result: InterventionResult,
        user_id: str = "unknown",
    ) -> Dict[str, Any]:
        """审计干预"""
        audit_record = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "user_id": user_id,
            "intervention_type": intervention.type.value,
            "intervention_content": intervention.content,
            "success": result.success,
            "narrative_impact": result.narrative_impact,
            "actions_taken": result.actions_taken,
            "warnings": result.warnings,
            "errors": result.errors,
        }

        logger.info(
            f"Audit: {intervention.type.value} intervention by {user_id} - Success: {result.success}"
        )

        return audit_record

    # 与SessionManager和TurnScheduler集成的方法

    async def integrate_with_session(
        self, session_manager, session_id: str, interventions: List[Intervention]
    ) -> Dict[str, Any]:
        """与SessionManager集成，更新会话状态"""
        if not session_manager:
            return {"success": False, "error": "SessionManager not provided"}

        session = await session_manager.load_session(session_id)
        if not session:
            return {"success": False, "error": f"Session {session_id} not found"}

        # 更新会话状态
        session.state.setdefault("interventions", []).extend(
            [
                {
                    "type": interv.type.value,
                    "content": interv.content,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                    "priority": interv.priority.value,
                    "scope": interv.scope,
                }
                for interv in interventions
            ]
        )

        # 更新会话元数据
        session.metadata["last_intervention_time"] = (
            __import__("datetime").datetime.now().isoformat()
        )
        session.metadata["total_interventions"] = session.metadata.get(
            "total_interventions", 0
        ) + len(interventions)

        # 保存会话
        success = await session_manager.save_session(session, force=True)

        return {
            "success": success,
            "session_updated": success,
            "interventions_added": len(interventions),
            "session_stats": {
                "total_interventions": session.metadata.get("total_interventions", 0),
                "last_intervention_time": session.metadata.get(
                    "last_intervention_time"
                ),
            },
        }

    async def integrate_with_turn_scheduler(
        self,
        turn_scheduler,
        turn_id: str,
        intervention_results: List[InterventionResult],
    ) -> Dict[str, Any]:
        """与TurnScheduler集成，更新回合干预信息"""
        if not turn_scheduler:
            return {"success": False, "error": "TurnScheduler not provided"}

        turn = await turn_scheduler.get_turn(turn_id)
        if not turn:
            return {"success": False, "error": f"Turn {turn_id} not found"}

        # 添加干预信息到回合
        for result in intervention_results:
            turn.interventions.append(
                {
                    "type": result.intervention.type.value,
                    "content": result.intervention.content,
                    "success": result.success,
                    "narrative_impact": result.narrative_impact,
                    "actions_taken": result.actions_taken,
                    "warnings": result.warnings,
                    "errors": result.errors,
                    "processed_at": __import__("datetime").datetime.now().isoformat(),
                }
            )

        # 更新回合优先级（如果有高优先级干预）
        max_priority = max(
            [result.intervention.priority.value for result in intervention_results],
            default=0,
        )
        if max_priority > turn.priority:
            turn.priority = max_priority
            logger.info(
                f"Updated turn {turn_id} priority to {turn.priority} based on interventions"
            )

        # 保存回合
        if turn_scheduler.persistence:
            await turn_scheduler.persistence.save_turn(turn)

        return {
            "success": True,
            "turn_updated": True,
            "interventions_added": len(intervention_results),
            "new_priority": turn.priority,
        }

    async def process_player_input_with_integration(
        self,
        player_input: str,
        session_manager,
        session_id: str,
        turn_scheduler,
        turn_id: str,
    ) -> Dict[str, Any]:
        """完整处理玩家输入，包括干预解析和集成"""
        # 解析输入
        parsed = self.parse_input(player_input)

        if not parsed["has_interventions"]:
            return {
                "success": True,
                "has_interventions": False,
                "clean_input": parsed["clean_input"],
                "message": "No interventions found",
            }

        # 处理干预
        session_context = {"session_id": session_id, "turn_id": turn_id}
        intervention_results = await self.process_interventions(
            parsed["interventions"], session_context
        )

        # 与SessionManager集成
        session_integration = await self.integrate_with_session(
            session_manager, session_id, parsed["interventions"]
        )

        # 与TurnScheduler集成
        turn_integration = await self.integrate_with_turn_scheduler(
            turn_scheduler, turn_id, intervention_results
        )

        # 合并干预到Prompt
        final_prompt = self.merge_interventions_into_prompt(
            parsed["clean_input"], intervention_results
        )

        return {
            "success": True,
            "has_interventions": True,
            "clean_input": parsed["clean_input"],
            "final_prompt": final_prompt,
            "interventions_parsed": len(parsed["interventions"]),
            "interventions_processed": len(intervention_results),
            "conflicts": parsed["conflicts"],
            "session_integration": session_integration,
            "turn_integration": turn_integration,
            "intervention_results": [
                {
                    "type": r.intervention.type.value,
                    "success": r.success,
                    "narrative_impact": r.narrative_impact,
                    "warnings": r.warnings,
                    "errors": r.errors,
                }
                for r in intervention_results
            ],
        }
