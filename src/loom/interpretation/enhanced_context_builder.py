"""
增强上下文构建器

实现智能上下文构建，支持动态上下文构建，包括历史对话、记忆片段、规则约束等。
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..memory.interfaces import MemoryEntity
from ..utils.logging_config import get_logger
from .reasoning_pipeline import ReasoningContext
from .rule_interpreter import InterpretationResult

logger = get_logger(__name__)


class ContextOptimizationStrategy(Enum):
    """上下文优化策略"""

    BALANCED = "balanced"  # 平衡策略
    MEMORY_FOCUSED = "memory_focused"  # 记忆重点
    CONSTRAINT_FOCUSED = "constraint_focused"  # 约束重点
    CONCISE = "concise"  # 简洁策略
    DETAILED = "detailed"  # 详细策略


@dataclass
class ContextQualityMetrics:
    """上下文质量指标"""

    total_tokens: int
    memory_coverage: float  # 0-1
    constraint_coverage: float  # 0-1
    relevance_score: float  # 0-1
    coherence_score: float  # 0-1
    optimization_level: float  # 0-1


class EnhancedContextBuilder:
    """增强上下文构建器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化增强上下文构建器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.template_registry = self._initialize_templates()
        self.optimization_strategies = self._initialize_strategies()

        logger.info(f"EnhancedContextBuilder initialized with config: {self.config}")

    async def build_optimized(
        self,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> str:
        """构建优化提示"""
        logger.info(f"Building optimized context for session {context.session_id}")

        # 1. 选择最相关的记忆
        relevant_memories = await self._select_relevant_memories(
            context, memories, limit=self.config.get("max_memories", 5)
        )

        # 2. 提取关键约束
        key_constraints = self._extract_key_constraints(interpretation)

        # 3. 选择最佳模板
        template = self._select_best_template(
            context, interpretation, relevant_memories
        )

        # 4. 组装提示
        prompt = self._render_template(
            template,
            rules=context.rules_text,
            constraints=key_constraints,
            memories=relevant_memories,
            player_input=context.player_input,
            interventions=context.interventions,
            interpretation=interpretation,
        )

        # 5. 优化提示
        optimized_prompt = await self._optimize_prompt(prompt, context)

        # 6. 评估质量
        quality_metrics = self._evaluate_context_quality(
            optimized_prompt, context, interpretation, relevant_memories
        )

        logger.info(
            f"Context built: {len(optimized_prompt)} chars, "
            f"quality: {quality_metrics.relevance_score:.2f}"
        )

        return optimized_prompt

    async def build_with_strategy(
        self,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
        strategy: ContextOptimizationStrategy,
    ) -> str:
        """使用指定策略构建上下文"""
        logger.info(f"Building context with strategy: {strategy.value}")

        # 根据策略调整参数
        strategy_config = self._get_strategy_config(strategy)

        # 选择记忆
        memory_limit = strategy_config.get("memory_limit", 5)
        relevant_memories = await self._select_relevant_memories(
            context,
            memories,
            limit=memory_limit,
            relevance_threshold=strategy_config.get("relevance_threshold", 0.3),
        )

        # 提取约束
        constraint_limit = strategy_config.get("constraint_limit", 10)
        key_constraints = self._extract_key_constraints(
            interpretation, limit=constraint_limit
        )

        # 选择模板
        template_type = strategy_config.get("template_type", "balanced")
        template = self._get_template_by_type(template_type)

        # 渲染
        prompt = self._render_template(
            template,
            rules=context.rules_text,
            constraints=key_constraints,
            memories=relevant_memories,
            player_input=context.player_input,
            interventions=context.interventions,
            interpretation=interpretation,
            strategy=strategy.value,
        )

        # 策略特定优化
        optimized_prompt = await self._apply_strategy_optimization(
            prompt, strategy, context
        )

        return optimized_prompt

    async def _select_relevant_memories(
        self,
        context: ReasoningContext,
        memories: List[Dict[str, Any]],
        limit: int = 5,
        relevance_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """选择最相关的记忆"""
        if not memories:
            return []

        # 计算每个记忆的相关性分数
        scored_memories = []
        for memory in memories:
            score = self._calculate_memory_relevance(memory, context)
            if score >= relevance_threshold:
                scored_memories.append(
                    {
                        "memory": memory,
                        "score": score,
                        "type": memory.get("type", "unknown"),
                    }
                )

        # 按分数排序
        scored_memories.sort(key=lambda x: x["score"], reverse=True)

        # 选择前N个
        selected = scored_memories[:limit]

        # 确保类型多样性
        diversified = self._diversify_memory_types(selected)

        logger.debug(
            f"Selected {len(diversified)} memories from {len(memories)} "
            f"(threshold: {relevance_threshold})"
        )

        return [item["memory"] for item in diversified]

    def _calculate_memory_relevance(
        self, memory: Dict[str, Any], context: ReasoningContext
    ) -> float:
        """计算记忆相关性"""
        score = 0.0

        # 基于记忆类型的基础分数
        mem_type = memory.get("type", "unknown")
        type_weights = {
            "fact": 0.3,
            "character": 0.4,
            "event": 0.5,
            "relationship": 0.4,
            "location": 0.3,
        }
        score += type_weights.get(mem_type, 0.2)

        # 基于内容匹配
        memory_content = str(memory.get("content", "")).lower()
        player_input = context.player_input.lower()

        # 关键词匹配
        common_words = set(memory_content.split()) & set(player_input.split())
        if common_words:
            score += min(len(common_words) * 0.1, 0.3)

        # 时间相关性（如果记忆有时间戳）
        memory_time = memory.get("timestamp")
        if memory_time and context.turn_number:
            # 简单时间衰减：越近的记忆越相关
            time_diff = context.turn_number - memory_time
            if isinstance(time_diff, (int, float)) and time_diff >= 0:
                decay = max(0.1, 1.0 - (time_diff * 0.1))
                score += decay * 0.2

        # 会话相关性
        session_id = memory.get("session_id")
        if session_id == context.session_id:
            score += 0.2

        return min(score, 1.0)

    def _diversify_memory_types(
        self, scored_memories: List[Dict[str, Any]], max_per_type: int = 2
    ) -> List[Dict[str, Any]]:
        """确保记忆类型多样性"""
        if not scored_memories:
            return []

        # 按类型分组
        type_groups = {}
        for item in scored_memories:
            mem_type = item["type"]
            if mem_type not in type_groups:
                type_groups[mem_type] = []
            type_groups[mem_type].append(item)

        # 从每个类型中选择最多max_per_type个
        diversified = []
        for mem_type, items in type_groups.items():
            diversified.extend(items[:max_per_type])

        # 重新按分数排序
        diversified.sort(key=lambda x: x["score"], reverse=True)

        return diversified

    def _extract_key_constraints(
        self, interpretation: InterpretationResult, limit: int = 10
    ) -> List[Any]:
        """提取关键约束"""
        if not hasattr(interpretation, "constraints"):
            return []

        constraints = interpretation.constraints

        # 按重要性排序
        # 1. 禁止性规则（最重要）
        # 2. 权限性规则
        # 3. 因果关系
        # 4. 其他

        sorted_constraints = sorted(
            constraints,
            key=lambda c: (
                (
                    0
                    if getattr(c, "type", "") == "prohibition"
                    else (
                        1
                        if getattr(c, "type", "") == "permission"
                        else 2 if getattr(c, "type", "") == "causality" else 3
                    )
                ),
                -len(getattr(c, "content", "")),  # 内容越长可能越重要
            ),
        )

        # 提取关键信息
        key_constraints = []
        for constraint in sorted_constraints[:limit]:
            constraint_type = getattr(constraint, "type", "unknown")
            constraint_content = getattr(constraint, "content", "")
            constraint_importance = getattr(constraint, "importance", "medium")

            key_constraints.append(
                {
                    "type": constraint_type,
                    "content": constraint_content,
                    "importance": constraint_importance,
                    "summary": self._summarize_constraint(constraint_content),
                }
            )

        return key_constraints

    def _summarize_constraint(self, constraint_content: str) -> str:
        """总结约束"""
        # 简化实现：提取前50个字符
        if len(constraint_content) <= 50:
            return constraint_content

        # 尝试在句子边界截断
        sentences = re.split(r"[。！？]", constraint_content)
        if sentences and sentences[0]:
            return sentences[0][:50] + "..."

        return constraint_content[:50] + "..."

    def _select_best_template(
        self,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """选择最佳模板"""
        # 根据上下文特征选择模板
        context_features = self._analyze_context_features(
            context, interpretation, memories
        )

        # 选择最匹配的模板
        best_template = None
        best_score = 0.0

        for template_name, template in self.template_registry.items():
            score = self._calculate_template_match_score(template, context_features)
            if score > best_score:
                best_score = score
                best_template = template

        if not best_template:
            # 使用默认模板
            best_template = self.template_registry.get("balanced")

        logger.debug(f"Selected template with score: {best_score:.2f}")
        return best_template

    def _analyze_context_features(
        self,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """分析上下文特征"""
        features = {
            "memory_count": len(memories),
            "constraint_count": len(getattr(interpretation, "constraints", [])),
            "player_input_length": len(context.player_input),
            "rules_length": len(context.rules_text),
            "intervention_count": len(context.interventions),
            "turn_number": context.turn_number,
        }

        # 计算复杂度
        features["complexity"] = (
            features["memory_count"] * 0.2
            + features["constraint_count"] * 0.3
            + min(features["player_input_length"] / 100, 1.0) * 0.2
            + min(features["rules_length"] / 1000, 1.0) * 0.3
        )

        return features

    def _calculate_template_match_score(
        self, template: Dict[str, Any], context_features: Dict[str, Any]
    ) -> float:
        """计算模板匹配分数"""
        score = 0.0

        # 基于复杂度匹配
        template_complexity = template.get("complexity", "medium")
        context_complexity = context_features.get("complexity", 0.5)

        if template_complexity == "low" and context_complexity < 0.3:
            score += 0.4
        elif template_complexity == "medium" and 0.3 <= context_complexity <= 0.7:
            score += 0.4
        elif template_complexity == "high" and context_complexity > 0.7:
            score += 0.4

        # 基于记忆数量匹配
        memory_support = template.get("memory_support", "medium")
        memory_count = context_features.get("memory_count", 0)

        if memory_support == "low" and memory_count <= 2:
            score += 0.3
        elif memory_support == "medium" and 3 <= memory_count <= 6:
            score += 0.3
        elif memory_support == "high" and memory_count > 6:
            score += 0.3

        # 基于约束数量匹配
        constraint_support = template.get("constraint_support", "medium")
        constraint_count = context_features.get("constraint_count", 0)

        if constraint_support == "low" and constraint_count <= 3:
            score += 0.3
        elif constraint_support == "medium" and 4 <= constraint_count <= 8:
            score += 0.3
        elif constraint_support == "high" and constraint_count > 8:
            score += 0.3

        return score

    def _get_template_by_type(self, template_type: str) -> Dict[str, Any]:
        """根据类型获取模板"""
        return self.template_registry.get(
            template_type, self.template_registry["balanced"]
        )

    def _render_template(
        self,
        template: Dict[str, Any],
        rules: str,
        constraints: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        player_input: str,
        interventions: List[Dict[str, Any]],
        interpretation: InterpretationResult,
        **kwargs,
    ) -> str:
        """渲染模板"""
        template_format = template.get("format", "default")

        if template_format == "detailed":
            return self._render_detailed_template(
                rules,
                constraints,
                memories,
                player_input,
                interventions,
                interpretation,
                **kwargs,
            )
        elif template_format == "concise":
            return self._render_concise_template(
                rules, constraints, memories, player_input, interventions, **kwargs
            )
        elif template_format == "memory_focused":
            return self._render_memory_focused_template(
                rules, constraints, memories, player_input, interventions, **kwargs
            )
        else:  # balanced/default
            return self._render_balanced_template(
                rules,
                constraints,
                memories,
                player_input,
                interventions,
                interpretation,
                **kwargs,
            )

    def _render_balanced_template(
        self,
        rules: str,
        constraints: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        player_input: str,
        interventions: List[Dict[str, Any]],
        interpretation: InterpretationResult,
        **kwargs,
    ) -> str:
        """渲染平衡模板"""
        strategy = kwargs.get("strategy", "balanced")

        prompt = f"""你是一个叙事引擎，负责根据给定的世界观规则和上下文推进故事。

# 世界观规则
{rules}

# 关键约束（必须严格遵守）
{self._format_constraints_for_prompt(constraints)}

# 相关记忆（按相关性排序）
{self._format_memories_for_prompt(memories)}

# 玩家输入
{player_input}

# 干预信息
{self._format_interventions_for_prompt(interventions)}

# 推理指导
1. 严格遵守所有约束条件，特别是禁止性规则
2. 保持与历史记忆的一致性
3. 维持叙事基调和风格
4. 自然地推进故事发展
5. 考虑角色的动机和性格
6. 确保逻辑和因果关系合理

请生成符合以上所有要求的叙事响应。保持响应长度适中，内容丰富且有深度。"""

        return prompt

    def _render_detailed_template(
        self,
        rules: str,
        constraints: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        player_input: str,
        interventions: List[Dict[str, Any]],
        interpretation: InterpretationResult,
        **kwargs,
    ) -> str:
        """渲染详细模板"""
        prompt = f"""你是一个高级叙事引擎，需要生成详细、丰富的叙事响应。

# 详细世界观规则
{rules}

# 深度规则分析
{getattr(interpretation, 'narrative_output', '无深度分析')}

# 完整约束列表（按重要性排序）
{self._format_constraints_detailed(constraints)}

# 完整记忆上下文
{self._format_memories_detailed(memories)}

# 玩家输入分析
玩家输入：{player_input}

输入分析：{self._analyze_player_input(player_input)}

# 干预处理要求
{self._format_interventions_detailed(interventions)}

# 详细生成要求
1. 严格遵守所有约束，特别是标记为"高重要性"的约束
2. 深度整合历史记忆，引用具体记忆内容
3. 保持角色性格和关系的一致性
4. 确保时间线和事件的逻辑连贯
5. 维持世界观设定的基调和风格
6. 生成丰富、详细的叙事，包含环境描写、角色互动和情节推进
7. 响应长度应在300-800字之间，确保内容充实

请生成符合以上所有要求的详细叙事响应。"""

        return prompt

    def _render_concise_template(
        self,
        rules: str,
        constraints: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        player_input: str,
        interventions: List[Dict[str, Any]],
        **kwargs,
    ) -> str:
        """渲染简洁模板"""
        # 总结规则
        rules_summary = self._summarize_rules(rules, max_length=200)

        # 只保留最重要的约束
        key_constraints = constraints[:3] if constraints else []

        prompt = f"""叙事引擎：根据规则和记忆推进故事。

规则：{rules_summary}

关键约束：{self._format_constraints_concise(key_constraints)}

相关记忆：{self._format_memories_concise(memories[:2])}

玩家：{player_input}

干预：{self._format_interventions_concise(interventions)}

要求：遵守约束，保持一致性，自然推进。

响应："""

        return prompt

    def _render_memory_focused_template(
        self,
        rules: str,
        constraints: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        player_input: str,
        interventions: List[Dict[str, Any]],
        **kwargs,
    ) -> str:
        """渲染记忆重点模板"""
        prompt = f"""你是一个注重历史连续性的叙事引擎。

# 世界观规则（摘要）
{self._summarize_rules(rules, max_length=300)}

# 必须遵守的约束
{self._format_constraints_for_prompt(constraints[:5])}

# 历史记忆上下文（这是重点）
{self._format_memories_as_context(memories)}

# 当前情况
玩家输入：{player_input}

干预：{self._format_interventions_for_prompt(interventions)}

# 核心要求
你的响应必须深度整合上述历史记忆，保持严格的时间线、角色发展和事件连续性。引用具体记忆来增强叙事的真实感和连贯性。

生成与历史深度整合的叙事响应："""

        return prompt

    def _format_constraints_for_prompt(self, constraints: List[Dict[str, Any]]) -> str:
        """为提示格式化约束"""
        if not constraints:
            return "（无明确约束）"

        formatted = []
        for i, constraint in enumerate(constraints):
            importance = constraint.get("importance", "medium")
            importance_marker = "⚠️" if importance == "high" else "•"

            formatted.append(
                f"{importance_marker} [{constraint.get('type', 'constraint')}] "
                f"{constraint.get('summary', constraint.get('content', ''))}"
            )

        return "\n".join(formatted)

    def _format_constraints_detailed(self, constraints: List[Dict[str, Any]]) -> str:
        """详细格式化约束"""
        if not constraints:
            return "无约束条件"

        formatted = []
        for i, constraint in enumerate(constraints):
            formatted.append(f"{i+1}. 类型：{constraint.get('type', 'unknown')}")
            formatted.append(f"   内容：{constraint.get('content', '')}")
            formatted.append(f"   重要性：{constraint.get('importance', 'medium')}")
            formatted.append("")

        return "\n".join(formatted)

    def _format_constraints_concise(self, constraints: List[Dict[str, Any]]) -> str:
        """简洁格式化约束"""
        if not constraints:
            return "无"

        return "，".join(
            [c.get("summary", c.get("content", ""))[:30] for c in constraints]
        )

    def _format_memories_for_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """为提示格式化记忆"""
        if not memories:
            return "（无相关记忆）"

        formatted = []
        for i, memory in enumerate(memories):
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})

            if isinstance(content, dict):
                summary = content.get("summary", str(content)[:80])
            else:
                summary = str(content)[:80]

            formatted.append(f"{i+1}. [{mem_type}] {summary}")

        return "\n".join(formatted)

    def _format_memories_detailed(self, memories: List[Dict[str, Any]]) -> str:
        """详细格式化记忆"""
        if not memories:
            return "无相关记忆"

        formatted = []
        for i, memory in enumerate(memories):
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})
            timestamp = memory.get("timestamp", "未知时间")
            relevance = memory.get("relevance_score", 0.0)

            formatted.append(f"记忆 #{i+1}:")
            formatted.append(f"  类型：{mem_type}")
            formatted.append(f"  时间：{timestamp}")
            formatted.append(f"  相关性：{relevance:.2f}")

            if isinstance(content, dict):
                for key, value in list(content.items())[:3]:
                    formatted.append(f"  {key}: {str(value)[:50]}")
            else:
                formatted.append(f"  内容：{str(content)[:100]}")

            formatted.append("")

        return "\n".join(formatted)

    def _format_memories_concise(self, memories: List[Dict[str, Any]]) -> str:
        """简洁格式化记忆"""
        if not memories:
            return "无"

        summaries = []
        for memory in memories:
            content = memory.get("content", {})
            if isinstance(content, dict):
                summary = content.get("summary", "")
            else:
                summary = str(content)

            if summary:
                summaries.append(summary[:30])

        return "；".join(summaries[:2])

    def _format_memories_as_context(self, memories: List[Dict[str, Any]]) -> str:
        """将记忆格式化为上下文"""
        if not memories:
            return "无历史记忆可用。"

        # 按类型分组
        type_groups = {}
        for memory in memories:
            mem_type = memory.get("type", "unknown")
            if mem_type not in type_groups:
                type_groups[mem_type] = []
            type_groups[mem_type].append(memory)

        formatted = []
        for mem_type, mem_list in type_groups.items():
            formatted.append(f"## {mem_type.capitalize()}记忆")
            for i, memory in enumerate(mem_list[:3]):  # 每个类型最多3个
                content = memory.get("content", {})
                if isinstance(content, dict):
                    summary = content.get("summary", str(content)[:60])
                else:
                    summary = str(content)[:60]

                formatted.append(f"{i+1}. {summary}")
            formatted.append("")

        return "\n".join(formatted)

    def _format_interventions_for_prompt(
        self, interventions: List[Dict[str, Any]]
    ) -> str:
        """为提示格式化干预信息"""
        if not interventions:
            return "（无干预）"

        formatted = []
        for interv in interventions:
            interv_type = interv.get("type", "unknown")
            content = interv.get("content", "")
            priority = interv.get("priority", "normal")

            priority_marker = (
                "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
            )
            formatted.append(f"{priority_marker} [{interv_type}] {content}")

        return "\n".join(formatted)

    def _format_interventions_detailed(
        self, interventions: List[Dict[str, Any]]
    ) -> str:
        """详细格式化干预信息"""
        if not interventions:
            return "无干预信息"

        formatted = []
        for i, interv in enumerate(interventions):
            formatted.append(f"干预 #{i+1}:")
            formatted.append(f"  类型：{interv.get('type', 'unknown')}")
            formatted.append(f"  内容：{interv.get('content', '')}")
            formatted.append(f"  优先级：{interv.get('priority', 'normal')}")
            formatted.append(f"  来源：{interv.get('source', 'unknown')}")
            formatted.append("")

        return "\n".join(formatted)

    def _format_interventions_concise(self, interventions: List[Dict[str, Any]]) -> str:
        """简洁格式化干预信息"""
        if not interventions:
            return "无"

        types = [interv.get("type", "unknown") for interv in interventions]
        return f"{len(interventions)}个干预（{', '.join(types[:2])}）"

    def _summarize_rules(self, rules: str, max_length: int = 200) -> str:
        """总结规则"""
        if len(rules) <= max_length:
            return rules

        # 尝试在段落边界截断
        paragraphs = rules.split("\n\n")
        summary = []
        total_length = 0

        for para in paragraphs:
            if total_length + len(para) + 2 <= max_length:
                summary.append(para)
                total_length += len(para) + 2
            else:
                # 当前段落太长，截断
                remaining = max_length - total_length - 3  # 留出"..."
                if remaining > 20:
                    summary.append(para[:remaining] + "...")
                break

        return "\n\n".join(summary)

    def _analyze_player_input(self, player_input: str) -> str:
        """分析玩家输入"""
        if not player_input:
            return "无玩家输入"

        length = len(player_input)
        sentences = len(re.split(r"[。！？]", player_input)) - 1

        analysis = []
        analysis.append(f"长度：{length}字符")
        analysis.append(f"句子数：{sentences}")

        # 简单意图分析
        if any(word in player_input for word in ["做什么", "怎么办", "如何"]):
            analysis.append("意图：寻求指导/建议")
        elif any(word in player_input for word in ["去", "前往", "进入"]):
            analysis.append("意图：移动/探索")
        elif any(word in player_input for word in ["攻击", "战斗", "使用"]):
            analysis.append("意图：战斗/行动")
        elif any(word in player_input for word in ["说", "告诉", "问"]):
            analysis.append("意图：对话/交流")
        else:
            analysis.append("意图：一般叙事推进")

        return "；".join(analysis)

    async def _optimize_prompt(self, prompt: str, context: ReasoningContext) -> str:
        """优化提示"""
        # 1. 令牌优化（简化实现）
        optimized = self._optimize_tokens(prompt)

        # 2. 结构优化
        optimized = self._optimize_structure(optimized)

        # 3. 清晰度优化
        optimized = self._optimize_clarity(optimized)

        return optimized

    def _optimize_tokens(self, prompt: str) -> str:
        """优化令牌使用"""
        # 简化实现：移除多余的空行和空格
        lines = prompt.split("\n")
        optimized_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped:  # 非空行
                # 压缩多个空格
                compressed = re.sub(r"\s+", " ", stripped)
                optimized_lines.append(compressed)

        return "\n".join(optimized_lines)

    def _optimize_structure(self, prompt: str) -> str:
        """优化结构"""
        # 确保有清晰的章节分隔
        sections = [
            "世界观规则",
            "关键约束",
            "相关记忆",
            "玩家输入",
            "干预信息",
            "推理指导",
            "生成要求",
        ]

        # 检查是否包含主要章节
        for section in sections:
            if f"# {section}" not in prompt and f"## {section}" not in prompt:
                # 没有明确标记，但可能在其他形式中
                pass

        return prompt

    def _optimize_clarity(self, prompt: str) -> str:
        """优化清晰度"""
        # 简化实现：确保指令清晰
        clarity_improvements = [
            ("必须严格遵守", "必须严格遵守"),
            ("确保", "确保"),
            ("保持", "保持"),
        ]

        optimized = prompt
        for old, new in clarity_improvements:
            optimized = optimized.replace(old, new)

        return optimized

    async def _apply_strategy_optimization(
        self,
        prompt: str,
        strategy: ContextOptimizationStrategy,
        context: ReasoningContext,
    ) -> str:
        """应用策略特定优化"""
        if strategy == ContextOptimizationStrategy.CONCISE:
            return self._make_concise(prompt)
        elif strategy == ContextOptimizationStrategy.DETAILED:
            return self._add_detail(prompt, context)
        elif strategy == ContextOptimizationStrategy.MEMORY_FOCUSED:
            return self._emphasize_memories(prompt)
        elif strategy == ContextOptimizationStrategy.CONSTRAINT_FOCUSED:
            return self._emphasize_constraints(prompt)
        else:  # BALANCED
            return prompt

    def _make_concise(self, prompt: str) -> str:
        """使提示更简洁"""
        # 移除多余的空行
        lines = [line for line in prompt.split("\n") if line.strip()]

        # 合并短行
        concise_lines = []
        buffer = ""

        for line in lines:
            if len(line) < 50 and not line.startswith("#") and not line.startswith("•"):
                buffer += " " + line if buffer else line
            else:
                if buffer:
                    concise_lines.append(buffer)
                    buffer = ""
                concise_lines.append(line)

        if buffer:
            concise_lines.append(buffer)

        return "\n".join(concise_lines)

    def _add_detail(self, prompt: str, context: ReasoningContext) -> str:
        """添加细节"""
        # 添加更多上下文信息
        detail_sections = []

        # 添加会话上下文
        detail_sections.append(f"# 会话上下文")
        detail_sections.append(f"会话ID：{context.session_id}")
        detail_sections.append(f"回合数：{context.turn_number}")

        # 添加生成参数建议
        detail_sections.append(f"# 生成参数建议")
        detail_sections.append("建议使用较低温度（0.6-0.8）以确保一致性")
        detail_sections.append("建议生成长度：400-800字")

        # 将新部分插入到合适位置
        prompt_parts = prompt.split("\n\n")
        if len(prompt_parts) > 2:
            # 在规则部分后插入
            prompt_parts.insert(2, "\n".join(detail_sections))

        return "\n\n".join(prompt_parts)

    def _emphasize_memories(self, prompt: str) -> str:
        """强调记忆部分"""
        # 在记忆部分添加强调说明
        memory_section = "# 相关记忆（重点：必须深度整合）"

        # 替换原有的记忆标题
        prompt = prompt.replace("# 相关记忆", memory_section)
        prompt = prompt.replace("## 相关记忆", memory_section)

        # 添加记忆整合说明
        integration_note = (
            "\n\n**记忆整合要求**：你的响应必须明确引用上述记忆，展示历史连续性。"
        )
        if "请生成" in prompt:
            # 在生成指令前插入
            parts = prompt.split("请生成")
            prompt = parts[0] + integration_note + "\n\n请生成" + parts[1]

        return prompt

    def _emphasize_constraints(self, prompt: str) -> str:
        """强调约束部分"""
        # 在约束部分添加警告
        constraint_section = "# 关键约束（⚠️ 必须严格遵守，违反将导致叙事不一致）"

        # 替换原有的约束标题
        prompt = prompt.replace("# 关键约束", constraint_section)
        prompt = prompt.replace("## 关键约束", constraint_section)

        # 添加约束检查说明
        check_note = "\n\n**约束检查清单**：生成后请自行检查是否：1) 遵守所有禁止性规则 2) 符合所有因果关系 3) 不违反任何权限限制"
        if "请生成" in prompt:
            # 在生成指令前插入
            parts = prompt.split("请生成")
            prompt = parts[0] + check_note + "\n\n请生成" + parts[1]

        return prompt

    def _evaluate_context_quality(
        self,
        prompt: str,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> ContextQualityMetrics:
        """评估上下文质量"""
        total_tokens = len(prompt) // 4  # 近似估计

        # 记忆覆盖率
        memory_coverage = self._calculate_memory_coverage(prompt, memories)

        # 约束覆盖率
        constraint_coverage = self._calculate_constraint_coverage(
            prompt, interpretation
        )

        # 相关性分数
        relevance_score = self._calculate_relevance_score(prompt, context)

        # 连贯性分数
        coherence_score = self._calculate_coherence_score(prompt)

        # 优化级别
        optimization_level = self._calculate_optimization_level(
            memory_coverage, constraint_coverage, relevance_score, coherence_score
        )

        return ContextQualityMetrics(
            total_tokens=total_tokens,
            memory_coverage=memory_coverage,
            constraint_coverage=constraint_coverage,
            relevance_score=relevance_score,
            coherence_score=coherence_score,
            optimization_level=optimization_level,
        )

    def _calculate_memory_coverage(
        self, prompt: str, memories: List[Dict[str, Any]]
    ) -> float:
        """计算记忆覆盖率"""
        if not memories:
            return 0.0

        # 检查提示中是否提到了记忆内容
        coverage = 0.0

        for memory in memories:
            content = str(memory.get("content", ""))
            if content and len(content) > 10:
                # 检查关键词是否出现在提示中
                keywords = content.split()[:5]
                keyword_count = sum(1 for kw in keywords if kw in prompt)
                coverage += keyword_count / len(keywords) * 0.2

        return min(coverage, 1.0)

    def _calculate_constraint_coverage(
        self, prompt: str, interpretation: InterpretationResult
    ) -> float:
        """计算约束覆盖率"""
        if not hasattr(interpretation, "constraints") or not interpretation.constraints:
            return 0.0

        coverage = 0.0

        for constraint in interpretation.constraints[:5]:  # 检查前5个约束
            constraint_content = getattr(constraint, "content", "")
            if constraint_content and constraint_content in prompt:
                coverage += 0.2

        return min(coverage, 1.0)

    def _calculate_relevance_score(
        self, prompt: str, context: ReasoningContext
    ) -> float:
        """计算相关性分数"""
        score = 0.5  # 基础分数

        # 检查是否包含关键部分
        required_sections = ["世界观规则", "玩家输入"]
        for section in required_sections:
            if section in prompt:
                score += 0.1

        # 检查是否包含上下文信息
        if context.session_id and str(context.session_id) in prompt:
            score += 0.1

        if str(context.turn_number) in prompt:
            score += 0.1

        return min(score, 1.0)

    def _calculate_coherence_score(self, prompt: str) -> float:
        """计算连贯性分数"""
        score = 0.5

        # 检查结构清晰度
        lines = prompt.split("\n")
        section_headers = sum(
            1 for line in lines if line.startswith("#") and len(line.strip()) > 2
        )

        if section_headers >= 3:
            score += 0.2

        # 检查段落长度
        paragraphs = prompt.split("\n\n")
        avg_paragraph_length = (
            sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        )

        if 50 <= avg_paragraph_length <= 500:
            score += 0.2

        # 检查指令清晰度
        if "必须" in prompt or "确保" in prompt or "保持" in prompt:
            score += 0.1

        return min(score, 1.0)

    def _calculate_optimization_level(
        self,
        memory_coverage: float,
        constraint_coverage: float,
        relevance_score: float,
        coherence_score: float,
    ) -> float:
        """计算优化级别"""
        weights = {"memory": 0.3, "constraint": 0.3, "relevance": 0.2, "coherence": 0.2}

        return (
            memory_coverage * weights["memory"]
            + constraint_coverage * weights["constraint"]
            + relevance_score * weights["relevance"]
            + coherence_score * weights["coherence"]
        )

    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """初始化模板"""
        return {
            "balanced": {
                "name": "平衡模板",
                "format": "balanced",
                "complexity": "medium",
                "memory_support": "medium",
                "constraint_support": "medium",
                "description": "平衡考虑记忆和约束的标准模板",
            },
            "detailed": {
                "name": "详细模板",
                "format": "detailed",
                "complexity": "high",
                "memory_support": "high",
                "constraint_support": "high",
                "description": "提供详细上下文和深度分析的模板",
            },
            "concise": {
                "name": "简洁模板",
                "format": "concise",
                "complexity": "low",
                "memory_support": "low",
                "constraint_support": "low",
                "description": "简洁高效的模板，适用于简单场景",
            },
            "memory_focused": {
                "name": "记忆重点模板",
                "format": "memory_focused",
                "complexity": "medium",
                "memory_support": "high",
                "constraint_support": "medium",
                "description": "强调历史记忆和连续性的模板",
            },
            "constraint_focused": {
                "name": "约束重点模板",
                "format": "balanced",  # 使用平衡格式但会特别强调约束
                "complexity": "medium",
                "memory_support": "medium",
                "constraint_support": "high",
                "description": "特别强调规则约束遵守的模板",
            },
        }

    def _initialize_strategies(
        self,
    ) -> Dict[ContextOptimizationStrategy, Dict[str, Any]]:
        """初始化策略"""
        return {
            ContextOptimizationStrategy.BALANCED: {
                "memory_limit": 5,
                "constraint_limit": 8,
                "relevance_threshold": 0.3,
                "template_type": "balanced",
                "description": "平衡策略，兼顾记忆和约束",
            },
            ContextOptimizationStrategy.MEMORY_FOCUSED: {
                "memory_limit": 8,
                "constraint_limit": 5,
                "relevance_threshold": 0.2,
                "template_type": "memory_focused",
                "description": "记忆重点策略，强调历史连续性",
            },
            ContextOptimizationStrategy.CONSTRAINT_FOCUSED: {
                "memory_limit": 3,
                "constraint_limit": 10,
                "relevance_threshold": 0.4,
                "template_type": "constraint_focused",
                "description": "约束重点策略，确保规则遵守",
            },
            ContextOptimizationStrategy.CONCISE: {
                "memory_limit": 2,
                "constraint_limit": 3,
                "relevance_threshold": 0.5,
                "template_type": "concise",
                "description": "简洁策略，生成高效提示",
            },
            ContextOptimizationStrategy.DETAILED: {
                "memory_limit": 6,
                "constraint_limit": 12,
                "relevance_threshold": 0.2,
                "template_type": "detailed",
                "description": "详细策略，提供深度上下文",
            },
        }

    def _get_strategy_config(
        self, strategy: ContextOptimizationStrategy
    ) -> Dict[str, Any]:
        """获取策略配置"""
        return self.optimization_strategies.get(
            strategy, self.optimization_strategies[ContextOptimizationStrategy.BALANCED]
        )

    # ========== 批量处理和高级功能 ==========

    async def batch_build(
        self,
        contexts: List[ReasoningContext],
        interpretations: List[InterpretationResult],
        memories_list: List[List[Dict[str, Any]]],
    ) -> List[str]:
        """批量构建上下文"""
        if len(contexts) != len(interpretations) or len(contexts) != len(memories_list):
            raise ValueError("Input lists must have the same length")

        prompts = []
        for i, (context, interpretation, memories) in enumerate(
            zip(contexts, interpretations, memories_list)
        ):
            try:
                prompt = await self.build_optimized(context, interpretation, memories)
                prompts.append(prompt)
                logger.debug(f"Built context {i+1}/{len(contexts)}")
            except Exception as e:
                logger.error(f"Failed to build context {i+1}: {e}")
                # 使用降级提示
                fallback_prompt = self._create_fallback_prompt(context)
                prompts.append(fallback_prompt)

        return prompts

    def _create_fallback_prompt(self, context: ReasoningContext) -> str:
        """创建降级提示"""
        return f"""叙事引擎：根据以下信息推进故事。

规则：{context.rules_text[:200]}...

玩家输入：{context.player_input}

生成符合规则的叙事响应。"""

    def analyze_prompt_quality(self, prompt: str) -> Dict[str, Any]:
        """分析提示质量"""
        lines = prompt.split("\n")
        paragraphs = prompt.split("\n\n")

        # 基本统计
        stats = {
            "total_length": len(prompt),
            "line_count": len(lines),
            "paragraph_count": len(paragraphs),
            "section_count": sum(1 for line in lines if line.startswith("#")),
            "avg_line_length": (
                sum(len(line) for line in lines) / len(lines) if lines else 0
            ),
            "avg_paragraph_length": (
                sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
            ),
        }

        # 内容分析
        content_analysis = {
            "has_rules": "世界观规则" in prompt or "规则" in prompt,
            "has_constraints": "约束" in prompt or "必须" in prompt,
            "has_memories": "记忆" in prompt or "历史" in prompt,
            "has_instructions": "要求" in prompt or "指导" in prompt,
            "has_player_input": "玩家输入" in prompt or "玩家" in prompt,
            "instruction_clarity": self._evaluate_instruction_clarity(prompt),
        }

        # 质量评分
        quality_score = self._calculate_prompt_quality_score(stats, content_analysis)

        return {
            "statistics": stats,
            "content_analysis": content_analysis,
            "quality_score": quality_score,
            "quality_level": self._get_quality_level(quality_score),
            "suggestions": self._generate_quality_suggestions(stats, content_analysis),
        }

    def _evaluate_instruction_clarity(self, prompt: str) -> str:
        """评估指令清晰度"""
        clarity_indicators = ["必须", "确保", "保持", "要求", "禁止", "允许"]
        indicator_count = sum(
            1 for indicator in clarity_indicators if indicator in prompt
        )

        if indicator_count >= 4:
            return "high"
        elif indicator_count >= 2:
            return "medium"
        else:
            return "low"

    def _calculate_prompt_quality_score(
        self, stats: Dict[str, Any], content_analysis: Dict[str, Any]
    ) -> float:
        """计算提示质量分数"""
        score = 0.0

        # 长度适中（500-3000字符）
        length = stats["total_length"]
        if 500 <= length <= 3000:
            score += 0.3
        elif 300 <= length < 500 or 3000 < length <= 5000:
            score += 0.2
        else:
            score += 0.1

        # 结构良好（有章节）
        if stats["section_count"] >= 3:
            score += 0.2

        # 内容完整
        required_elements = ["has_rules", "has_player_input"]
        element_count = sum(
            1 for elem in required_elements if content_analysis.get(elem, False)
        )
        score += (element_count / len(required_elements)) * 0.3

        # 指令清晰
        if content_analysis["instruction_clarity"] == "high":
            score += 0.2
        elif content_analysis["instruction_clarity"] == "medium":
            score += 0.1

        return min(score, 1.0)

    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 0.8:
            return "优秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "一般"
        else:
            return "较差"

    def _generate_quality_suggestions(
        self, stats: Dict[str, Any], content_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成质量改进建议"""
        suggestions = []

        # 长度建议
        length = stats["total_length"]
        if length < 300:
            suggestions.append("提示可能过短，考虑添加更多上下文")
        elif length > 5000:
            suggestions.append("提示可能过长，考虑精简内容")

        # 结构建议
        if stats["section_count"] < 2:
            suggestions.append("添加更多章节标题以改善结构")

        # 内容建议
        if not content_analysis["has_rules"]:
            suggestions.append("添加世界观规则部分")

        if not content_analysis["has_player_input"]:
            suggestions.append("明确标识玩家输入")

        if content_analysis["instruction_clarity"] == "low":
            suggestions.append("添加更明确的指令和要求")

        return suggestions[:5]  # 最多5条建议
