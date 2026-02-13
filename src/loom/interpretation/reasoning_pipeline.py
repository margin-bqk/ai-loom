"""
推理流水线

实现完整的推理流程：理解→分析→推导→输出。
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..utils.logging_config import get_logger
from .consistency_checker import ConsistencyChecker
from .llm_provider import LLMProvider, LLMProviderFactory, LLMResponse, ProviderManager
from .rule_interpreter import InterpretationResult, RuleInterpreter

logger = get_logger(__name__)


@dataclass
class ReasoningContext:
    """推理上下文"""

    session_id: str
    turn_number: int
    player_input: str
    rules_text: str
    memories: List[Dict[str, Any]]
    interventions: List[Dict[str, Any]]
    interpretation_result: Optional[InterpretationResult] = None
    llm_response: Optional[LLMResponse] = None
    consistency_report: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningResult:
    """推理结果"""

    narrative_response: str
    reasoning_steps: List[Dict[str, Any]]
    constraints_applied: List[str]
    confidence: float  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReasoningPipeline:
    """推理流水线"""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        provider_manager: Optional[ProviderManager] = None,
    ):
        """
        初始化推理流水线

        Args:
            llm_provider: 单个LLM提供者（向后兼容）
            provider_manager: Provider管理器（支持多Provider）
        """
        if provider_manager:
            self.provider_manager = provider_manager
            self.llm_provider = None
            logger.info(f"ReasoningPipeline initialized with provider manager")
        elif llm_provider:
            # 向后兼容：创建简单的Provider管理器
            self.llm_provider = llm_provider
            self.provider_manager = ProviderManager()
            self.provider_manager.register_provider(llm_provider.name, llm_provider)
            self.provider_manager.set_default(llm_provider.name)
            logger.info(
                f"ReasoningPipeline initialized with single provider: {llm_provider.name}"
            )
        else:
            raise ValueError("Either llm_provider or provider_manager must be provided")

        self.rule_interpreter = RuleInterpreter()
        self.consistency_checker = ConsistencyChecker()
        self.cache = {}

    async def process(self, context: ReasoningContext) -> ReasoningResult:
        """处理推理流程"""
        reasoning_steps = []

        # 步骤1：解释规则
        logger.info(f"Step 1: Interpreting rules for session {context.session_id}")
        interpretation_result = await self._interpret_rules(context)
        context.interpretation_result = interpretation_result
        reasoning_steps.append(
            {
                "step": "rule_interpretation",
                "result": interpretation_result.summary,
                "constraints_found": len(interpretation_result.constraints),
            }
        )

        # 步骤2：组装Prompt
        logger.info(f"Step 2: Assembling prompt for turn {context.turn_number}")
        prompt = self._assemble_prompt(context)
        reasoning_steps.append(
            {
                "step": "prompt_assembly",
                "prompt_length": len(prompt),
                "memories_used": len(context.memories),
            }
        )

        # 步骤3：调用LLM
        provider_name = "unknown"
        if self.llm_provider:
            provider_name = self.llm_provider.name
        elif (
            hasattr(self, "provider_manager")
            and self.provider_manager
            and self.provider_manager.default_provider
        ):
            provider_name = self.provider_manager.default_provider

        logger.info(f"Step 3: Calling LLM (provider: {provider_name})")
        llm_response = await self._call_llm(prompt, context)
        context.llm_response = llm_response
        reasoning_steps.append(
            {
                "step": "llm_generation",
                "model": llm_response.model,
                "response_length": len(llm_response.content),
                "usage": llm_response.usage,
            }
        )

        # 步骤4：一致性检查
        logger.info(f"Step 4: Checking consistency")
        consistency_report = await self._check_consistency(context)
        context.consistency_report = consistency_report
        reasoning_steps.append(
            {
                "step": "consistency_check",
                "passed": consistency_report.get("passed", False),
                "issues": len(consistency_report.get("issues", [])),
            }
        )

        # 步骤5：生成最终结果
        logger.info(f"Step 5: Generating final result")
        result = self._generate_result(context, reasoning_steps)

        # 添加最终结果步骤到推理步骤中
        reasoning_steps.append(
            {
                "step": "final_result_generation",
                "response_length": len(result.narrative_response),
                "confidence": result.confidence,
                "constraints_applied": len(result.constraints_applied),
            }
        )

        logger.info(
            f"Reasoning pipeline completed for session {context.session_id}, turn {context.turn_number}"
        )
        logger.info(f"  Response length: {len(result.narrative_response)}")
        logger.info(f"  Confidence: {result.confidence:.2f}")

        return result

    async def _interpret_rules(self, context: ReasoningContext) -> InterpretationResult:
        """解释规则"""
        # 这里需要从rules_text创建Canon对象
        # 简化实现：直接使用规则文本
        from pathlib import Path

        from ..rules.markdown_canon import MarkdownCanon

        # 创建临时Canon对象
        canon = MarkdownCanon(
            path=Path(f"session_{context.session_id}"), raw_content=context.rules_text
        )

        # 解释规则
        return self.rule_interpreter.interpret(canon)

    def _assemble_prompt(self, context: ReasoningContext) -> str:
        """组装Prompt"""
        interpretation = context.interpretation_result

        # 构建系统提示
        system_prompt = f"""你是一个叙事引擎，负责根据给定的世界观规则和记忆来推进故事。

# 世界观规则
{context.rules_text}

# 规则解释摘要
{interpretation.summary if interpretation else "无解释结果"}

# 关键约束
{self._format_constraints(interpretation.constraints if interpretation else [])}

# 相关记忆
{self._format_memories(context.memories)}

# 玩家输入
{context.player_input}

# 干预信息
{self._format_interventions(context.interventions)}

请生成符合世界观规则的叙事响应。保持叙事一致性，尊重所有约束，并自然地推进故事发展。"""

        return system_prompt

    def _format_constraints(self, constraints: List) -> str:
        """格式化约束"""
        if not constraints:
            return "（无明确约束）"

        formatted = []
        for i, constraint in enumerate(constraints[:10]):  # 限制数量
            formatted.append(f"{i+1}. [{constraint.type}] {constraint.content}")

        return "\n".join(formatted)

    def _format_memories(self, memories: List[Dict[str, Any]]) -> str:
        """格式化记忆"""
        if not memories:
            return "（无相关记忆）"

        formatted = []
        for i, memory in enumerate(memories[:5]):  # 限制数量
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})
            summary = content.get("summary", str(content)[:100])

            formatted.append(f"{i+1}. [{mem_type}] {summary}")

        return "\n".join(formatted)

    def _format_interventions(self, interventions: List[Dict[str, Any]]) -> str:
        """格式化干预信息"""
        if not interventions:
            return "（无干预）"

        formatted = []
        for interv in interventions:
            interv_type = interv.get("type", "unknown")
            content = interv.get("content", "")
            formatted.append(f"- [{interv_type}] {content}")

        return "\n".join(formatted)

    async def _call_llm(self, prompt: str, context: ReasoningContext) -> LLMResponse:
        """调用LLM（支持多Provider回退）"""
        try:
            # 如果有Provider管理器，使用回退机制
            if hasattr(self, "provider_manager") and self.provider_manager:
                # 从会话配置中获取Provider名称（如果可用）
                provider_name = context.metadata.get("llm_provider")
                if provider_name:
                    return await self.provider_manager.generate_with_fallback(
                        prompt,
                        provider=provider_name,
                        model=context.metadata.get("model"),
                        temperature=context.metadata.get("temperature", 0.7),
                        max_tokens=context.metadata.get("max_tokens", 1000),
                    )
                else:
                    return await self.provider_manager.generate_with_fallback(prompt)
            # 否则使用单个Provider（向后兼容）
            elif self.llm_provider:
                return await self.llm_provider.generate(prompt)
            else:
                raise ValueError("No LLM provider available")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # 返回降级响应
            return LLMResponse(
                content=f"[降级响应] 由于技术问题，无法生成完整叙事。玩家输入：{context.player_input}",
                model="fallback",
                usage={},
                metadata={"error": str(e), "fallback": True},
            )

    async def _check_consistency(self, context: ReasoningContext) -> Dict[str, Any]:
        """检查一致性"""
        if not context.llm_response:
            return {"passed": False, "issues": ["No LLM response"]}

        return self.consistency_checker.check(
            response=context.llm_response.content,
            rules_text=context.rules_text,
            constraints=(
                context.interpretation_result.constraints
                if context.interpretation_result
                else []
            ),
        )

    def _generate_result(
        self, context: ReasoningContext, reasoning_steps: List[Dict]
    ) -> ReasoningResult:
        """生成最终结果"""
        narrative_response = (
            context.llm_response.content if context.llm_response else ""
        )

        # 计算置信度
        confidence = self._calculate_confidence(context)

        # 提取应用的约束
        constraints_applied = []
        if context.interpretation_result:
            constraints_applied = [
                f"{c.type}: {c.content[:50]}..."
                for c in context.interpretation_result.constraints[:3]
            ]

        return ReasoningResult(
            narrative_response=narrative_response,
            reasoning_steps=reasoning_steps,
            constraints_applied=constraints_applied,
            confidence=confidence,
            metadata={
                "session_id": context.session_id,
                "turn_number": context.turn_number,
                "llm_model": (
                    context.llm_response.model if context.llm_response else "unknown"
                ),
                "consistency_passed": (
                    context.consistency_report.get("passed", False)
                    if context.consistency_report
                    else False
                ),
            },
        )

    def _calculate_confidence(self, context: ReasoningContext) -> float:
        """计算置信度"""
        confidence = 0.7  # 基础置信度

        # 基于一致性检查调整
        if context.consistency_report and context.consistency_report.get(
            "passed", False
        ):
            confidence += 0.2

        # 基于响应长度调整
        if context.llm_response and len(context.llm_response.content) > 50:
            confidence += 0.1

        # 基于约束数量调整
        if context.interpretation_result and context.interpretation_result.constraints:
            confidence = min(confidence + 0.05, 0.95)

        return min(confidence, 1.0)

    async def batch_process(
        self, contexts: List[ReasoningContext]
    ) -> List[ReasoningResult]:
        """批量处理"""
        tasks = [self.process(context) for context in contexts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch processing failed for context {i}: {result}")
                # 创建降级结果
                final_results.append(
                    ReasoningResult(
                        narrative_response=f"[错误] 处理失败: {result}",
                        reasoning_steps=[],
                        constraints_applied=[],
                        confidence=0.0,
                        metadata={"error": str(result)},
                    )
                )
            else:
                final_results.append(result)

        return final_results

    def evaluate_quality(self, result: ReasoningResult) -> Dict[str, Any]:
        """评估结果质量"""
        quality_score = result.confidence * 0.6  # 置信度占60%

        # 响应长度评分
        response_length = len(result.narrative_response)
        if response_length < 50:
            length_score = 0.3
        elif response_length < 200:
            length_score = 0.7
        else:
            length_score = 1.0

        quality_score += length_score * 0.2  # 长度占20%

        # 约束应用评分
        constraints_score = min(len(result.constraints_applied) / 5.0, 1.0)
        quality_score += constraints_score * 0.2  # 约束应用占20%

        # 检查是否有错误标记
        if (
            "[错误]" in result.narrative_response
            or "[降级响应]" in result.narrative_response
        ):
            quality_score *= 0.5

        return {
            "overall_score": min(quality_score, 1.0),
            "confidence": result.confidence,
            "response_length": response_length,
            "constraints_applied": len(result.constraints_applied),
            "reasoning_steps": len(result.reasoning_steps),
            "quality_level": self._get_quality_level(quality_score),
        }

    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.7:
            return "良好"
        elif score >= 0.5:
            return "一般"
        else:
            return "较差"

    def filter_results(
        self,
        results: List[ReasoningResult],
        min_confidence: float = 0.5,
        min_quality: float = 0.6,
    ) -> List[ReasoningResult]:
        """过滤结果"""
        filtered = []

        for result in results:
            quality = self.evaluate_quality(result)

            if (
                result.confidence >= min_confidence
                and quality["overall_score"] >= min_quality
            ):
                filtered.append(result)
            else:
                logger.warning(
                    f"Filtered out result with confidence {result.confidence:.2f}, quality {quality['overall_score']:.2f}"
                )

        return filtered

    async def process_with_retry(
        self, context: ReasoningContext, max_retries: int = 2
    ) -> ReasoningResult:
        """带重试的处理"""
        best_result = None
        best_quality = 0.0

        for attempt in range(max_retries + 1):
            try:
                result = await self.process(context)
                quality = self.evaluate_quality(result)

                if quality["overall_score"] > best_quality:
                    best_result = result
                    best_quality = quality["overall_score"]

                # 如果质量足够好，提前返回
                if quality["overall_score"] >= 0.8:
                    logger.info(
                        f"Attempt {attempt + 1}: Quality sufficient ({quality['overall_score']:.2f}), returning"
                    )
                    return result

                logger.info(
                    f"Attempt {attempt + 1}: Quality {quality['overall_score']:.2f}, retrying..."
                )

                # 修改上下文以尝试不同的方法
                if attempt < max_retries:
                    # 可以调整一些参数，比如添加更多上下文
                    context.metadata[f"retry_{attempt}"] = True

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    raise

        return (
            best_result if best_result else await self.process(context)
        )  # 最后一次尝试

    def generate_report(self, results: List[ReasoningResult]) -> Dict[str, Any]:
        """生成处理报告"""
        if not results:
            return {"error": "No results"}

        total = len(results)
        qualities = [self.evaluate_quality(r) for r in results]

        avg_confidence = sum(r.confidence for r in results) / total
        avg_quality = sum(q["overall_score"] for q in qualities) / total
        avg_length = sum(len(r.narrative_response) for r in results) / total

        # 统计质量等级
        quality_levels = {}
        for q in qualities:
            level = q["quality_level"]
            quality_levels[level] = quality_levels.get(level, 0) + 1

        return {
            "total_processed": total,
            "average_confidence": avg_confidence,
            "average_quality": avg_quality,
            "average_response_length": avg_length,
            "quality_distribution": quality_levels,
            "success_rate": sum(1 for r in results if r.confidence >= 0.5)
            / total
            * 100,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
