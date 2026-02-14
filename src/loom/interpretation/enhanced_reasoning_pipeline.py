"""
增强推理管道

实现多步骤推理管道，支持规则解释→记忆检索→上下文构建→LLM生成→一致性检查→记忆更新的完整流程。
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..memory.interfaces import MemoryEntity
from ..memory.world_memory import WorldMemory
from ..utils.logging_config import get_logger
from .consistency_checker import ConsistencyChecker, ConsistencyReport
from .llm_provider import LLMProvider, LLMResponse, ProviderManager
from .reasoning_pipeline import ReasoningContext, ReasoningResult
from .rule_interpreter import InterpretationResult, RuleConstraint, RuleInterpreter

logger = get_logger(__name__)


class ReasoningStep(Enum):
    """推理步骤枚举"""

    RULE_INTERPRETATION = "rule_interpretation"
    MEMORY_RETRIEVAL = "memory_retrieval"
    CONTEXT_BUILDING = "context_building"
    LLM_GENERATION = "llm_generation"
    CONSISTENCY_CHECK = "consistency_check"
    MEMORY_UPDATE = "memory_update"
    EXPLAINABILITY = "explainability"


@dataclass
class EnhancedReasoningResult(ReasoningResult):
    """增强推理结果"""

    reasoning_steps_detailed: List[Dict[str, Any]] = field(default_factory=list)
    consistency_report: Optional[Dict[str, Any]] = None
    explainability_report: Optional[Dict[str, Any]] = None
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    metadata_enhanced: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeepConsistencyReport:
    """深度一致性报告"""

    passed: bool
    overall_score: float  # 0-1
    category_scores: Dict[str, float]  # 各分类分数
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedReasoningPipeline:
    """增强推理管道"""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        provider_manager: Optional[ProviderManager] = None,
        world_memory: Optional[WorldMemory] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化增强推理管道

        Args:
            llm_provider: 单个LLM提供者（向后兼容）
            provider_manager: Provider管理器（支持多Provider）
            world_memory: 世界记忆系统
            config: 配置参数
        """
        self.config = config or {}

        # 初始化基础组件
        if provider_manager:
            self.provider_manager = provider_manager
            self.llm_provider = None
        elif llm_provider:
            self.llm_provider = llm_provider
            self.provider_manager = ProviderManager()
            self.provider_manager.register_provider(llm_provider.name, llm_provider)
            self.provider_manager.set_default(llm_provider.name)
        else:
            raise ValueError("Either llm_provider or provider_manager must be provided")

        self.rule_interpreter = RuleInterpreter()
        self.consistency_checker = ConsistencyChecker()
        self.world_memory = world_memory

        # 推理跟踪
        self.reasoning_steps = []
        self.step_metrics = {}

        # 缓存
        self.cache = {}

        logger.info(f"EnhancedReasoningPipeline initialized with config: {self.config}")

    async def process(self, context: ReasoningContext) -> EnhancedReasoningResult:
        """处理增强推理流程"""
        start_time = time.time()
        detailed_steps = []

        try:
            # 步骤1：深度规则解释
            logger.info(
                f"Step 1: Deep rule interpretation for session {context.session_id}"
            )
            interpretation_result = await self._deep_interpret_rules(context)
            context.interpretation_result = interpretation_result

            step1_metrics = {
                "step": ReasoningStep.RULE_INTERPRETATION.value,
                "duration": time.time() - start_time,
                "constraints_found": len(interpretation_result.constraints),
                "interpretation_depth": self._calculate_interpretation_depth(
                    interpretation_result
                ),
            }
            detailed_steps.append(step1_metrics)

            # 步骤2：智能记忆检索
            logger.info(
                f"Step 2: Intelligent memory retrieval for turn {context.turn_number}"
            )
            memories = await self._intelligent_memory_retrieval(context)
            context.memories = memories

            step2_metrics = {
                "step": ReasoningStep.MEMORY_RETRIEVAL.value,
                "duration": time.time() - start_time - step1_metrics["duration"],
                "memories_retrieved": len(memories),
                "relevance_score": self._calculate_memory_relevance(memories, context),
            }
            detailed_steps.append(step2_metrics)

            # 步骤3：优化上下文构建
            logger.info(f"Step 3: Optimized context building")
            prompt = await self._build_optimized_context(
                context, interpretation_result, memories
            )

            step3_metrics = {
                "step": ReasoningStep.CONTEXT_BUILDING.value,
                "duration": time.time()
                - start_time
                - sum(s["duration"] for s in detailed_steps),
                "prompt_length": len(prompt),
                "context_optimization": self._evaluate_context_quality(prompt),
            }
            detailed_steps.append(step3_metrics)

            # 步骤4：策略性LLM生成
            logger.info(f"Step 4: Strategic LLM generation")
            llm_response = await self._strategic_llm_generation(prompt, context)
            context.llm_response = llm_response

            step4_metrics = {
                "step": ReasoningStep.LLM_GENERATION.value,
                "duration": time.time()
                - start_time
                - sum(s["duration"] for s in detailed_steps),
                "model": llm_response.model,
                "response_length": len(llm_response.content),
                "tokens_used": (
                    llm_response.usage.get("total_tokens", 0)
                    if hasattr(llm_response, "usage")
                    else 0
                ),
            }
            detailed_steps.append(step4_metrics)

            # 步骤5：深度一致性检查
            logger.info(f"Step 5: Deep consistency check")
            consistency_report = await self._deep_consistency_check(
                llm_response, context, interpretation_result, memories
            )
            context.consistency_report = consistency_report

            step5_metrics = {
                "step": ReasoningStep.CONSISTENCY_CHECK.value,
                "duration": time.time()
                - start_time
                - sum(s["duration"] for s in detailed_steps),
                "consistency_score": consistency_report.get("overall_score", 0.0),
                "issues_found": len(consistency_report.get("issues", [])),
            }
            detailed_steps.append(step5_metrics)

            # 步骤6：智能记忆更新
            logger.info(f"Step 6: Intelligent memory update")
            memory_update_result = await self._intelligent_memory_update(
                context, llm_response, consistency_report
            )

            step6_metrics = {
                "step": ReasoningStep.MEMORY_UPDATE.value,
                "duration": time.time()
                - start_time
                - sum(s["duration"] for s in detailed_steps),
                "memories_updated": memory_update_result.get("updated_count", 0),
                "new_memories": memory_update_result.get("created_count", 0),
            }
            detailed_steps.append(step6_metrics)

            # 步骤7：生成可解释性报告
            logger.info(f"Step 7: Explainability report generation")
            explainability_report = self._generate_explainability_report(
                detailed_steps, context, consistency_report
            )

            step7_metrics = {
                "step": ReasoningStep.EXPLAINABILITY.value,
                "duration": time.time()
                - start_time
                - sum(s["duration"] for s in detailed_steps),
                "explainability_score": explainability_report.get("score", 0.0),
            }
            detailed_steps.append(step7_metrics)

            # 生成最终结果
            total_duration = time.time() - start_time
            result = self._generate_enhanced_result(
                context,
                detailed_steps,
                consistency_report,
                explainability_report,
                total_duration,
            )

            logger.info(
                f"Enhanced reasoning pipeline completed in {total_duration:.2f}s"
            )
            logger.info(f"  Response length: {len(result.narrative_response)}")
            logger.info(f"  Overall confidence: {result.confidence:.2f}")
            logger.info(
                f"  Consistency score: {consistency_report.get('overall_score', 0.0):.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Enhanced reasoning pipeline failed: {e}")
            return self._generate_fallback_result(context, str(e))

    async def _deep_interpret_rules(
        self, context: ReasoningContext
    ) -> InterpretationResult:
        """深度规则解释"""
        from pathlib import Path

        from ..rules.markdown_canon import MarkdownCanon

        # 创建Canon对象
        canon = MarkdownCanon(
            path=Path(f"session_{context.session_id}"), raw_content=context.rules_text
        )

        # 使用规则解释器
        interpretation = self.rule_interpreter.interpret(canon)

        # 增强解释：提取更多语义信息
        # 注意：InterpretationResult来自rule_interpreter，有不同的字段
        # 我们需要创建一个新的EnhancedInterpretationResult或使用metadata
        enhanced_interpretation = InterpretationResult(
            constraints=interpretation.constraints,
            key_themes=interpretation.key_themes,
            narrative_guidelines=interpretation.narrative_guidelines,
            summary=interpretation.summary,
            metadata={
                **interpretation.metadata,
                "enhanced_analysis": True,
                "semantic_constraints": self._extract_semantic_constraints(
                    interpretation
                ),
                "rule_categories": self._categorize_rules(context.rules_text),
                # 添加缺少的字段到metadata
                "narrative_output": interpretation.summary,  # 使用summary作为narrative_output
                "reasoning_steps": [],
                "confidence": 0.8,
                "consistency_level": "medium",
            },
        )

        return enhanced_interpretation

    async def _intelligent_memory_retrieval(
        self, context: ReasoningContext
    ) -> List[Dict[str, Any]]:
        """智能记忆检索"""
        if not self.world_memory:
            logger.warning("No world memory available, using provided memories")
            return context.memories or []

        try:
            # 使用世界记忆系统检索相关记忆
            query = f"{context.player_input} {context.rules_text[:100]}"

            # 检索不同类型的内存
            memories = []

            # 检索事实记忆
            fact_memories = await self.world_memory.retrieve_facts(
                query=query, limit=5, session_id=context.session_id
            )
            memories.extend(fact_memories)

            # 检索角色记忆
            character_memories = await self.world_memory.retrieve_characters(
                query=query, limit=3, session_id=context.session_id
            )
            memories.extend(character_memories)

            # 检索事件记忆
            event_memories = await self.world_memory.retrieve_events(
                query=query, limit=3, session_id=context.session_id
            )
            memories.extend(event_memories)

            # 按相关性排序
            memories.sort(key=lambda m: m.get("relevance_score", 0), reverse=True)

            logger.info(f"Retrieved {len(memories)} memories from world memory")
            return memories

        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}, using fallback")
            return context.memories or []

    async def _build_optimized_context(
        self,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> str:
        """构建优化上下文"""
        # 提取关键约束
        key_constraints = self._extract_key_constraints(interpretation)

        # 选择最相关的记忆
        relevant_memories = self._select_relevant_memories(memories, context, limit=5)

        # 构建系统提示
        system_prompt = f"""你是一个高级叙事引擎，负责根据给定的世界观规则、记忆和约束来推进故事。

# 世界观规则
{context.rules_text}

# 规则深度解释
{interpretation.summary if hasattr(interpretation, 'summary') else '规则解释不可用'}

# 关键约束（必须遵守）
{self._format_constraints_detailed(key_constraints)}

# 相关记忆（按相关性排序）
{self._format_memories_detailed(relevant_memories)}

# 玩家输入
{context.player_input}

# 干预信息
{self._format_interventions_detailed(context.interventions)}

# 推理指导
1. 严格遵守所有约束条件
2. 保持与历史记忆的一致性
3. 维持叙事基调和风格
4. 自然地推进故事发展
5. 考虑角色的动机和性格
6. 确保逻辑和因果关系合理

请生成符合以上所有要求的叙事响应。"""

        return system_prompt

    async def _strategic_llm_generation(
        self, prompt: str, context: ReasoningContext
    ) -> LLMResponse:
        """策略性LLM生成"""
        try:
            # 根据上下文选择策略
            strategy = self._select_generation_strategy(context)

            # 调整生成参数
            generation_params = self._get_generation_params(context, strategy)

            # 使用Provider管理器进行生成
            if hasattr(self, "provider_manager") and self.provider_manager:
                # 根据策略选择Provider
                provider_name = self._select_provider_by_strategy(strategy)

                response = await self.provider_manager.generate_with_fallback(
                    prompt, provider=provider_name, **generation_params
                )
            else:
                # 使用单个Provider
                response = await self.llm_provider.generate(prompt, **generation_params)

            # 记录生成策略
            response.metadata["generation_strategy"] = strategy
            response.metadata["generation_params"] = generation_params

            return response

        except Exception as e:
            logger.error(f"Strategic LLM generation failed: {e}")
            # 降级到基础生成
            return await self._fallback_llm_generation(prompt, context)

    async def _deep_consistency_check(
        self,
        response: LLMResponse,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """深度一致性检查"""
        # 基础一致性检查
        base_report = self.consistency_checker.check(
            response=response.content,
            rules_text=context.rules_text,
            constraints=(
                interpretation.constraints
                if hasattr(interpretation, "constraints")
                else []
            ),
        )

        # 记忆一致性检查
        memory_report = self.consistency_checker.check_with_memories(
            response=response.content,
            memories=memories,
            constraints=(
                interpretation.constraints
                if hasattr(interpretation, "constraints")
                else []
            ),
        )

        # 语义一致性检查（简化实现）
        semantic_issues = await self._check_semantic_consistency(
            response.content, context, interpretation, memories
        )

        # 合并报告
        all_issues = []
        all_issues.extend(base_report.get("issues", []))
        all_issues.extend(memory_report.get("issues", []))
        all_issues.extend(semantic_issues)

        # 计算综合分数
        overall_score = self._calculate_deep_consistency_score(
            base_report.get("score", 0.0),
            memory_report.get("score", 0.0),
            semantic_issues,
        )

        # 生成深度报告
        deep_report = {
            "passed": len(all_issues) == 0,
            "overall_score": overall_score,
            "category_scores": {
                "rule_consistency": base_report.get("score", 0.0),
                "memory_consistency": memory_report.get("score", 0.0),
                "semantic_consistency": 1.0 - (len(semantic_issues) * 0.1),
            },
            "issues": all_issues,
            "suggestions": self._generate_consistency_suggestions(all_issues),
            "metadata": {
                "base_check": base_report,
                "memory_check": memory_report,
                "semantic_check": {"issues": semantic_issues},
            },
        }

        return deep_report

    async def _intelligent_memory_update(
        self,
        context: ReasoningContext,
        response: LLMResponse,
        consistency_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """智能记忆更新"""
        if not self.world_memory:
            return {"updated_count": 0, "created_count": 0, "reason": "no_world_memory"}

        try:
            update_result = {"updated_count": 0, "created_count": 0, "details": []}

            # 提取响应中的关键信息
            key_entities = self._extract_key_entities(response.content)

            # 更新事实记忆
            for entity in key_entities.get("facts", []):
                memory_id = await self.world_memory.store_fact(
                    content=entity,
                    session_id=context.session_id,
                    turn_number=context.turn_number,
                )
                if memory_id:
                    update_result["created_count"] += 1
                    update_result["details"].append(
                        {"type": "fact", "entity": entity[:50], "memory_id": memory_id}
                    )

            # 更新事件记忆
            events = self._extract_events(response.content)
            for event in events:
                memory_id = await self.world_memory.store_event(
                    description=event,
                    session_id=context.session_id,
                    turn_number=context.turn_number,
                )
                if memory_id:
                    update_result["created_count"] += 1
                    update_result["details"].append(
                        {
                            "type": "event",
                            "description": event[:100],
                            "memory_id": memory_id,
                        }
                    )

            return update_result

        except Exception as e:
            logger.error(f"Memory update failed: {e}")
            return {"updated_count": 0, "created_count": 0, "error": str(e)}

    def _generate_explainability_report(
        self,
        detailed_steps: List[Dict[str, Any]],
        context: ReasoningContext,
        consistency_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """生成可解释性报告"""
        # 计算可解释性分数
        explainability_score = self._calculate_explainability_score(
            detailed_steps, consistency_report
        )

        # 提取关键决策点
        key_decisions = self._extract_key_decisions(detailed_steps, context)

        # 生成推理链
        reasoning_chain = self._generate_reasoning_chain(detailed_steps)

        return {
            "score": explainability_score,
            "key_decisions": key_decisions,
            "reasoning_chain": reasoning_chain,
            "step_breakdown": detailed_steps,
            "confidence_factors": self._extract_confidence_factors(
                detailed_steps, consistency_report
            ),
            "metadata": {
                "session_id": context.session_id,
                "turn_number": context.turn_number,
                "generated_at": time.time(),
            },
        }

    def _generate_enhanced_result(
        self,
        context: ReasoningContext,
        detailed_steps: List[Dict[str, Any]],
        consistency_report: Dict[str, Any],
        explainability_report: Dict[str, Any],
        total_duration: float,
    ) -> EnhancedReasoningResult:
        """生成增强结果"""
        narrative_response = (
            context.llm_response.content if context.llm_response else ""
        )

        # 计算综合置信度
        confidence = self._calculate_enhanced_confidence(
            consistency_report, explainability_report, detailed_steps
        )

        # 提取应用的约束
        constraints_applied = []
        if context.interpretation_result and hasattr(
            context.interpretation_result, "constraints"
        ):
            constraints_applied = [
                f"{c.type}: {c.content[:50]}..."
                for c in context.interpretation_result.constraints[:5]
            ]

        # 生成基础推理步骤
        reasoning_steps = [
            {
                "step": step["step"],
                "duration": step["duration"],
                "metrics": {
                    k: v for k, v in step.items() if k not in ["step", "duration"]
                },
            }
            for step in detailed_steps
        ]

        return EnhancedReasoningResult(
            narrative_response=narrative_response,
            reasoning_steps=reasoning_steps,
            constraints_applied=constraints_applied,
            confidence=confidence,
            reasoning_steps_detailed=detailed_steps,
            consistency_report=consistency_report,
            explainability_report=explainability_report,
            confidence_breakdown={
                "consistency": consistency_report.get("overall_score", 0.0),
                "explainability": explainability_report.get("score", 0.0),
                "step_quality": self._calculate_step_quality(detailed_steps),
                "response_quality": self._evaluate_response_quality(narrative_response),
            },
            metadata_enhanced={
                "session_id": context.session_id,
                "turn_number": context.turn_number,
                "total_duration": total_duration,
                "llm_model": (
                    context.llm_response.model if context.llm_response else "unknown"
                ),
                "generation_strategy": (
                    context.llm_response.metadata.get("generation_strategy", "default")
                    if context.llm_response
                    else "unknown"
                ),
                "consistency_passed": consistency_report.get("passed", False),
            },
        )

    def _generate_fallback_result(
        self, context: ReasoningContext, error: str
    ) -> EnhancedReasoningResult:
        """生成降级结果"""
        return EnhancedReasoningResult(
            narrative_response=f"[错误] 增强推理失败: {error}",
            reasoning_steps=[],
            constraints_applied=[],
            confidence=0.0,
            reasoning_steps_detailed=[],
            consistency_report={"passed": False, "error": error},
            explainability_report={"score": 0.0, "error": error},
            confidence_breakdown={"error": 1.0},
            metadata_enhanced={
                "session_id": context.session_id,
                "turn_number": context.turn_number,
                "error": error,
                "fallback": True,
            },
        )

    # ========== 辅助方法 ==========

    def _calculate_interpretation_depth(
        self, interpretation: InterpretationResult
    ) -> float:
        """计算解释深度"""
        # 基于约束数量、推理步骤长度等
        depth = 0.5  # 基础深度

        if hasattr(interpretation, "constraints"):
            depth += min(len(interpretation.constraints) * 0.05, 0.3)

        if hasattr(interpretation, "reasoning_steps"):
            depth += min(len(interpretation.reasoning_steps) * 0.02, 0.2)

        return min(depth, 1.0)

    def _calculate_memory_relevance(
        self, memories: List[Dict[str, Any]], context: ReasoningContext
    ) -> float:
        """计算记忆相关性"""
        if not memories:
            return 0.0

        # 简单实现：基于记忆数量和质量
        relevance = min(len(memories) * 0.1, 0.5)

        # 检查记忆是否包含关键词
        player_input_lower = context.player_input.lower()
        relevant_count = sum(
            1 for mem in memories if player_input_lower in str(mem).lower()
        )
        relevance += min(relevant_count * 0.1, 0.3)

        return min(relevance, 1.0)

    def _evaluate_context_quality(self, prompt: str) -> float:
        """评估上下文质量"""
        # 基于提示长度、结构等
        quality = 0.5

        # 长度适中
        if 500 < len(prompt) < 3000:
            quality += 0.2

        # 包含关键部分
        key_sections = ["世界观规则", "关键约束", "相关记忆", "玩家输入"]
        section_count = sum(1 for section in key_sections if section in prompt)
        quality += section_count * 0.05

        return min(quality, 1.0)

    def _extract_semantic_constraints(
        self, interpretation: InterpretationResult
    ) -> List[Dict[str, Any]]:
        """提取语义约束"""
        # 简化实现
        return [
            {"type": "semantic", "content": "保持叙事一致性"},
            {"type": "semantic", "content": "维持角色性格"},
        ]

    def _categorize_rules(self, rules_text: str) -> Dict[str, List[str]]:
        """分类规则"""
        # 简化实现
        categories = {
            "permissions": ["允许", "可以", "能够"],
            "prohibitions": ["禁止", "不能", "不可以"],
            "characteristics": ["性格", "特征", "属性"],
            "events": ["事件", "发生", "历史"],
        }

        result = {}
        for category, keywords in categories.items():
            found = [kw for kw in keywords if kw in rules_text]
            if found:
                result[category] = found

        return result

    def _extract_key_constraints(
        self, interpretation: InterpretationResult
    ) -> List[Any]:
        """提取关键约束"""
        if not hasattr(interpretation, "constraints"):
            return []

        # 按类型和重要性排序
        constraints = interpretation.constraints
        constraints.sort(
            key=lambda c: (
                0
                if c.type == "permission"
                else 1
                if c.type == "prohibition"
                else 2
                if c.type == "causality"
                else 3
            )
        )

        return constraints[:10]  # 限制数量

    def _select_relevant_memories(
        self, memories: List[Dict[str, Any]], context: ReasoningContext, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """选择相关记忆"""
        if not memories:
            return []

        # 简单实现：按类型和相关性排序
        sorted_memories = sorted(
            memories,
            key=lambda m: (
                (
                    0
                    if m.get("type") == "fact"
                    else (
                        1
                        if m.get("type") == "character"
                        else 2
                        if m.get("type") == "event"
                        else 3
                    )
                ),
                m.get("relevance_score", 0),
            ),
            reverse=True,
        )

        return sorted_memories[:limit]

    def _format_constraints_detailed(self, constraints: List[Any]) -> str:
        """格式化约束（详细）"""
        if not constraints:
            return "（无明确约束）"

        formatted = []
        for i, constraint in enumerate(constraints):
            constraint_type = getattr(constraint, "type", "unknown")
            constraint_content = getattr(constraint, "content", str(constraint))

            formatted.append(f"{i+1}. [{constraint_type}] {constraint_content}")

        return "\n".join(formatted)

    def _format_memories_detailed(self, memories: List[Dict[str, Any]]) -> str:
        """格式化记忆（详细）"""
        if not memories:
            return "（无相关记忆）"

        formatted = []
        for i, memory in enumerate(memories):
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})

            if isinstance(content, dict):
                summary = content.get("summary", str(content)[:100])
            else:
                summary = str(content)[:100]

            relevance = memory.get("relevance_score", 0)
            formatted.append(f"{i+1}. [{mem_type}] {summary} (相关性: {relevance:.2f})")

        return "\n".join(formatted)

    def _format_interventions_detailed(
        self, interventions: List[Dict[str, Any]]
    ) -> str:
        """格式化干预信息（详细）"""
        if not interventions:
            return "（无干预）"

        formatted = []
        for i, interv in enumerate(interventions):
            interv_type = interv.get("type", "unknown")
            content = interv.get("content", "")
            priority = interv.get("priority", "normal")

            formatted.append(f"{i+1}. [{interv_type}] {content} (优先级: {priority})")

        return "\n".join(formatted)

    def _select_generation_strategy(self, context: ReasoningContext) -> str:
        """选择生成策略"""
        # 基于上下文选择策略
        if len(context.player_input) > 100:
            return "detailed"  # 详细生成
        elif context.turn_number == 1:
            return "world_building"  # 世界构建
        elif context.interventions:
            return "intervention_handling"  # 干预处理
        else:
            return "standard"  # 标准生成

    def _get_generation_params(
        self, context: ReasoningContext, strategy: str
    ) -> Dict[str, Any]:
        """获取生成参数"""
        base_params = {"temperature": 0.7, "max_tokens": 1000, "top_p": 0.9}

        strategy_params = {
            "detailed": {"temperature": 0.8, "max_tokens": 1500},
            "world_building": {"temperature": 0.9, "max_tokens": 2000},
            "intervention_handling": {"temperature": 0.6, "max_tokens": 1200},
            "standard": {"temperature": 0.7, "max_tokens": 1000},
        }

        return {**base_params, **strategy_params.get(strategy, {})}

    def _select_provider_by_strategy(self, strategy: str) -> str:
        """根据策略选择Provider"""
        # 简化实现：返回默认Provider
        return "default"

    async def _fallback_llm_generation(
        self, prompt: str, context: ReasoningContext
    ) -> LLMResponse:
        """降级LLM生成"""
        try:
            if hasattr(self, "provider_manager") and self.provider_manager:
                return await self.provider_manager.generate_with_fallback(prompt)
            elif self.llm_provider:
                return await self.llm_provider.generate(prompt)
            else:
                raise ValueError("No LLM provider available")
        except Exception as e:
            logger.error(f"Fallback LLM generation also failed: {e}")
            return LLMResponse(
                content=f"[降级响应] 由于技术问题，无法生成完整叙事。玩家输入：{context.player_input}",
                model="fallback",
                usage={},
                metadata={"error": str(e), "fallback": True},
            )

    async def _check_semantic_consistency(
        self,
        response: str,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """检查语义一致性"""
        # 简化实现
        issues = []

        # 检查响应是否包含关键约束
        if hasattr(interpretation, "constraints"):
            for constraint in interpretation.constraints[:3]:
                if constraint.type == "prohibition":
                    # 检查是否违反了禁止性规则
                    if constraint.content in response:
                        issues.append(
                            {
                                "type": "semantic_violation",
                                "severity": "high",
                                "description": f"可能违反禁止性规则: {constraint.content}",
                                "evidence": f"响应中包含: {constraint.content}",
                            }
                        )

        return issues

    def _calculate_deep_consistency_score(
        self,
        base_score: float,
        memory_score: float,
        semantic_issues: List[Dict[str, Any]],
    ) -> float:
        """计算深度一致性分数"""
        # 加权平均
        weights = {"base": 0.4, "memory": 0.4, "semantic": 0.2}

        semantic_penalty = len(semantic_issues) * 0.1
        semantic_score = max(0.0, 1.0 - semantic_penalty)

        overall_score = (
            base_score * weights["base"]
            + memory_score * weights["memory"]
            + semantic_score * weights["semantic"]
        )

        return overall_score

    def _generate_consistency_suggestions(
        self, issues: List[Dict[str, Any]]
    ) -> List[str]:
        """生成一致性建议"""
        suggestions = []

        for issue in issues:
            if issue.get("type") == "rule_violation":
                suggestions.append("检查并修正规则违反")
            elif issue.get("type") == "memory_conflict":
                suggestions.append("调整响应以符合历史记忆")
            elif issue.get("type") == "semantic_violation":
                suggestions.append("重新考虑语义一致性")

        return list(set(suggestions))[:5]  # 去重并限制数量

    def _extract_key_entities(self, text: str) -> Dict[str, List[str]]:
        """提取关键实体"""
        # 简化实现
        return {
            "facts": [text[:50]] if len(text) > 20 else [],
            "characters": [],
            "events": [text[:100]] if len(text) > 50 else [],
        }

    def _extract_events(self, text: str) -> List[str]:
        """提取事件"""
        # 简化实现：按句子分割
        import re

        sentences = re.split(r"[。！？]", text)
        return [s.strip() for s in sentences if len(s.strip()) > 10][:3]

    def _calculate_explainability_score(
        self, detailed_steps: List[Dict[str, Any]], consistency_report: Dict[str, Any]
    ) -> float:
        """计算可解释性分数"""
        score = 0.5

        # 基于步骤详细程度
        if detailed_steps:
            step_detail_score = min(len(detailed_steps) * 0.1, 0.3)
            score += step_detail_score

        # 基于一致性报告质量
        if consistency_report.get("issues"):
            issue_detail_score = min(len(consistency_report["issues"]) * 0.05, 0.2)
            score += issue_detail_score

        return min(score, 1.0)

    def _extract_key_decisions(
        self, detailed_steps: List[Dict[str, Any]], context: ReasoningContext
    ) -> List[Dict[str, Any]]:
        """提取关键决策点"""
        decisions = []

        for step in detailed_steps:
            if step.get("step") in ["llm_generation", "consistency_check"]:
                decisions.append(
                    {
                        "step": step["step"],
                        "decision": f"在{step['step']}步骤中做出的关键决策",
                        "impact": (
                            "high" if step.get("step") == "llm_generation" else "medium"
                        ),
                        "reasoning": (
                            "基于上下文和约束生成叙事"
                            if step.get("step") == "llm_generation"
                            else "基于一致性检查调整响应"
                        ),
                    }
                )

        return decisions

    def _generate_reasoning_chain(
        self, detailed_steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成推理链"""
        chain = []

        for i, step in enumerate(detailed_steps):
            chain.append(
                {
                    "step_number": i + 1,
                    "step_name": step["step"],
                    "input": f"步骤{i}的输出" if i > 0 else "初始上下文",
                    "output": f"步骤{i+1}的输入",
                    "transformation": self._describe_step_transformation(step),
                }
            )

        return chain

    def _extract_confidence_factors(
        self, detailed_steps: List[Dict[str, Any]], consistency_report: Dict[str, Any]
    ) -> Dict[str, float]:
        """提取置信度因子"""
        factors = {
            "step_completion": len(detailed_steps) / 7.0,  # 7个步骤的完成度
            "consistency_score": consistency_report.get("overall_score", 0.0),
            "response_quality": 0.7,  # 简化
            "memory_relevance": 0.8,  # 简化
        }

        return factors

    def _calculate_enhanced_confidence(
        self,
        consistency_report: Dict[str, Any],
        explainability_report: Dict[str, Any],
        detailed_steps: List[Dict[str, Any]],
    ) -> float:
        """计算增强置信度"""
        weights = {
            "consistency": 0.4,
            "explainability": 0.3,
            "step_quality": 0.2,
            "response_quality": 0.1,
        }

        consistency_score = consistency_report.get("overall_score", 0.0)
        explainability_score = explainability_report.get("score", 0.0)
        step_quality = self._calculate_step_quality(detailed_steps)
        response_quality = 0.7  # 简化

        confidence = (
            consistency_score * weights["consistency"]
            + explainability_score * weights["explainability"]
            + step_quality * weights["step_quality"]
            + response_quality * weights["response_quality"]
        )

        return min(confidence, 1.0)

    def _calculate_step_quality(self, detailed_steps: List[Dict[str, Any]]) -> float:
        """计算步骤质量"""
        if not detailed_steps:
            return 0.0

        # 检查每个步骤是否有合理的持续时间
        valid_steps = 0
        for step in detailed_steps:
            duration = step.get("duration", 0)
            if 0.1 <= duration <= 30.0:  # 合理的时间范围
                valid_steps += 1

        return valid_steps / len(detailed_steps)

    def _evaluate_response_quality(self, response: str) -> float:
        """评估响应质量"""
        quality = 0.5

        # 长度适中
        if 100 <= len(response) <= 2000:
            quality += 0.2

        # 包含完整句子
        import re

        sentences = re.split(r"[。！？]", response)
        if len(sentences) >= 2:
            quality += 0.1

        # 没有错误标记
        if "[错误]" not in response and "[降级响应]" not in response:
            quality += 0.2

        return min(quality, 1.0)

    def _describe_step_transformation(self, step: Dict[str, Any]) -> str:
        """描述步骤转换"""
        step_name = step.get("step", "")

        transformations = {
            "rule_interpretation": "将规则文本转换为结构化约束",
            "memory_retrieval": "从记忆系统中检索相关信息",
            "context_building": "构建优化的提示上下文",
            "llm_generation": "使用LLM生成叙事响应",
            "consistency_check": "检查响应的一致性和质量",
            "memory_update": "将新信息存储到记忆系统",
            "explainability": "生成推理过程和决策解释",
        }

        return transformations.get(step_name, "未知转换")

    # ========== 批量处理和高级功能 ==========

    async def batch_process(
        self, contexts: List[ReasoningContext]
    ) -> List[EnhancedReasoningResult]:
        """批量处理"""
        tasks = [self.process(context) for context in contexts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch processing failed for context {i}: {result}")
                final_results.append(
                    self._generate_fallback_result(contexts[i], str(result))
                )
            else:
                final_results.append(result)

        return final_results

    async def process_with_adaptive_strategy(
        self,
        context: ReasoningContext,
        max_iterations: int = 3,
        quality_threshold: float = 0.8,
    ) -> EnhancedReasoningResult:
        """使用自适应策略处理"""
        best_result = None
        best_quality = 0.0

        for iteration in range(max_iterations):
            logger.info(f"Adaptive strategy iteration {iteration + 1}")

            # 调整上下文以尝试不同的方法
            adjusted_context = self._adjust_context_for_iteration(context, iteration)

            result = await self.process(adjusted_context)
            quality = result.confidence

            if quality > best_quality:
                best_result = result
                best_quality = quality

            # 如果质量足够好，提前返回
            if quality >= quality_threshold:
                logger.info(
                    f"Iteration {iteration + 1}: Quality sufficient ({quality:.2f}), returning"
                )
                return result

            logger.info(
                f"Iteration {iteration + 1}: Quality {quality:.2f}, continuing..."
            )

        return best_result if best_result else await self.process(context)

    def _adjust_context_for_iteration(
        self, context: ReasoningContext, iteration: int
    ) -> ReasoningContext:
        """为迭代调整上下文"""
        # 创建上下文的副本
        adjusted_context = ReasoningContext(
            session_id=context.session_id,
            turn_number=context.turn_number,
            player_input=context.player_input,
            rules_text=context.rules_text,
            memories=context.memories.copy() if context.memories else [],
            interventions=context.interventions.copy() if context.interventions else [],
            interpretation_result=context.interpretation_result,
            llm_response=context.llm_response,
            consistency_report=context.consistency_report,
            metadata={**context.metadata, "iteration": iteration},
        )

        # 根据迭代调整参数
        if iteration == 1:
            # 尝试更详细的生成
            adjusted_context.metadata["generation_strategy"] = "detailed"
        elif iteration == 2:
            # 尝试更保守的生成
            adjusted_context.metadata["generation_strategy"] = "conservative"

        return adjusted_context

    def generate_comprehensive_report(
        self, results: List[EnhancedReasoningResult]
    ) -> Dict[str, Any]:
        """生成综合报告"""
        if not results:
            return {"error": "No results"}

        total = len(results)

        # 计算各种指标
        avg_confidence = sum(r.confidence for r in results) / total
        avg_consistency = (
            sum(
                r.consistency_report.get("overall_score", 0.0)
                for r in results
                if r.consistency_report
            )
            / total
        )
        avg_explainability = (
            sum(
                r.explainability_report.get("score", 0.0)
                for r in results
                if r.explainability_report
            )
            / total
        )

        # 质量分布
        quality_levels = {"优秀": 0, "良好": 0, "一般": 0, "较差": 0}
        for result in results:
            if result.confidence >= 0.9:
                quality_levels["优秀"] += 1
            elif result.confidence >= 0.7:
                quality_levels["良好"] += 1
            elif result.confidence >= 0.5:
                quality_levels["一般"] += 1
            else:
                quality_levels["较差"] += 1

        # 步骤性能分析
        step_performance = {}
        for result in results:
            for step in result.reasoning_steps_detailed:
                step_name = step.get("step")
                if step_name not in step_performance:
                    step_performance[step_name] = {"count": 0, "total_duration": 0.0}

                step_performance[step_name]["count"] += 1
                step_performance[step_name]["total_duration"] += step.get(
                    "duration", 0.0
                )

        # 计算平均持续时间
        for step_name, data in step_performance.items():
            if data["count"] > 0:
                data["avg_duration"] = data["total_duration"] / data["count"]

        return {
            "total_processed": total,
            "average_confidence": avg_confidence,
            "average_consistency_score": avg_consistency,
            "average_explainability_score": avg_explainability,
            "quality_distribution": quality_levels,
            "step_performance": step_performance,
            "success_rate": sum(1 for r in results if r.confidence >= 0.5)
            / total
            * 100,
            "timestamp": time.time(),
            "metadata": {
                "pipeline_version": "enhanced_v1.0",
                "report_generated_by": "EnhancedReasoningPipeline",
            },
        }
