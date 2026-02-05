"""
增强一致性检查器

实现深度一致性检查，支持叙事一致性、逻辑一致性、时间线一致性检查。
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from .consistency_checker import ConsistencyChecker, ConsistencyIssue, ConsistencyReport
from .rule_interpreter import InterpretationResult, RuleConstraint
from .reasoning_pipeline import ReasoningContext
from .llm_provider import LLMProvider, LLMResponse
from ..utils.logging_config import get_logger
from ..memory.interfaces import MemoryEntity

logger = get_logger(__name__)


class ConsistencyCategory(Enum):
    """一致性分类"""

    RULE_SEMANTIC = "rule_semantic"  # 规则语义一致性
    MEMORY_SEMANTIC = "memory_semantic"  # 记忆语义一致性
    NARRATIVE_LOGIC = "narrative_logic"  # 叙事逻辑一致性
    STYLE_TONE = "style_tone"  # 风格基调一致性
    TEMPORAL = "temporal"  # 时间线一致性
    CHARACTER = "character"  # 角色一致性
    CAUSALITY = "causality"  # 因果关系一致性


@dataclass
class DeepConsistencyIssue(ConsistencyIssue):
    """深度一致性问题"""

    category: ConsistencyCategory = ConsistencyCategory.RULE_SEMANTIC
    confidence: float = 0.5  # 0-1，问题置信度
    evidence_context: str = ""  # 证据上下文
    impact_level: str = "medium"  # "low", "medium", "high", "critical"


@dataclass
class DeepConsistencyReport:
    """深度一致性报告"""

    passed: bool
    overall_score: float  # 0-1
    category_scores: Dict[ConsistencyCategory, float]  # 各分类分数
    issues: List[DeepConsistencyIssue]
    suggestions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedConsistencyChecker(ConsistencyChecker):
    """增强一致性检查器"""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        初始化增强一致性检查器

        Args:
            llm_provider: 用于深度语义检查的LLM提供者
        """
        super().__init__()
        self.llm_provider = llm_provider
        self.semantic_cache = {}
        self.patterns = self._initialize_patterns()

        logger.info(
            f"EnhancedConsistencyChecker initialized with LLM provider: {llm_provider is not None}"
        )

    async def deep_check(
        self,
        response: Union[LLMResponse, str],
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> DeepConsistencyReport:
        """深度一致性检查"""
        logger.info(
            f"Performing deep consistency check for session {context.session_id}"
        )

        issues = []

        # 1. 规则语义一致性检查
        rule_issues = await self._check_semantic_rule_violations(
            response, interpretation, context
        )
        issues.extend(rule_issues)

        # 2. 记忆语义一致性检查
        memory_issues = await self._check_semantic_memory_consistency(
            response, memories, context
        )
        issues.extend(memory_issues)

        # 3. 叙事逻辑一致性检查
        narrative_issues = await self._check_narrative_logic(
            response, context, memories
        )
        issues.extend(narrative_issues)

        # 4. 风格基调一致性检查
        style_issues = await self._check_style_consistency(response, context.rules_text)
        issues.extend(style_issues)

        # 5. 时间线一致性检查
        temporal_issues = await self._check_temporal_consistency(
            response, memories, context
        )
        issues.extend(temporal_issues)

        # 6. 角色一致性检查
        character_issues = await self._check_character_consistency(
            response, memories, context
        )
        issues.extend(character_issues)

        # 7. 因果关系一致性检查
        causality_issues = await self._check_causality_consistency(
            response, interpretation, context
        )
        issues.extend(causality_issues)

        # 8. 使用LLM进行深度语义检查（如果可用）
        if self.llm_provider:
            llm_issues = await self._check_with_llm(
                response, context, interpretation, memories
            )
            issues.extend(llm_issues)

        # 计算分数和生成报告
        report = self._generate_deep_report(issues, context)

        logger.info(
            f"Deep consistency check completed: {len(issues)} issues, "
            f"overall score: {report.overall_score:.2f}"
        )

        return report

    async def _check_semantic_rule_violations(
        self,
        response: Union[LLMResponse, str],
        interpretation: InterpretationResult,
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查规则语义一致性"""
        issues = []
        response_text = (
            response.content if isinstance(response, LLMResponse) else response
        )

        if not hasattr(interpretation, "constraints"):
            return issues

        for constraint in interpretation.constraints:
            constraint_type = getattr(constraint, "type", "")
            constraint_content = getattr(constraint, "content", "")

            if not constraint_content:
                continue

            # 根据约束类型进行不同检查
            if constraint_type == "prohibition":
                violation = await self._check_semantic_prohibition_violation(
                    response_text, constraint_content, context
                )
                if violation["found"]:
                    issues.append(
                        DeepConsistencyIssue(
                            type="rule_semantic_violation",
                            severity="high",
                            description=f"语义违反禁止性规则",
                            evidence=violation["evidence"],
                            suggestion="重新表述以避免违反此规则",
                            category=ConsistencyCategory.RULE_SEMANTIC,
                            confidence=violation["confidence"],
                            evidence_context=constraint_content,
                            impact_level="high",
                        )
                    )

            elif constraint_type == "permission":
                misuse = await self._check_permission_misuse(
                    response_text, constraint_content, context
                )
                if misuse["found"]:
                    issues.append(
                        DeepConsistencyIssue(
                            type="permission_misuse",
                            severity="medium",
                            description=f"可能滥用权限性规则",
                            evidence=misuse["evidence"],
                            suggestion="确保权限使用符合规则意图",
                            category=ConsistencyCategory.RULE_SEMANTIC,
                            confidence=misuse["confidence"],
                            evidence_context=constraint_content,
                            impact_level="medium",
                        )
                    )

            elif constraint_type == "causality":
                violation = await self._check_causality_violation_semantic(
                    response_text, constraint_content, context
                )
                if violation["found"]:
                    issues.append(
                        DeepConsistencyIssue(
                            type="causality_violation",
                            severity="medium",
                            description=f"违反因果关系规则",
                            evidence=violation["evidence"],
                            suggestion="调整叙事以符合因果关系",
                            category=ConsistencyCategory.CAUSALITY,
                            confidence=violation["confidence"],
                            evidence_context=constraint_content,
                            impact_level="medium",
                        )
                    )

        return issues

    async def _check_semantic_prohibition_violation(
        self, response_text: str, prohibition: str, context: ReasoningContext
    ) -> Dict[str, Any]:
        """检查语义禁止性规则违反"""
        # 简化实现：使用关键词和上下文分析
        response_lower = response_text.lower()
        prohibition_lower = prohibition.lower()

        # 提取禁止的关键概念
        prohibition_concepts = self._extract_concepts(prohibition_lower)

        # 检查响应中是否包含这些概念
        found_concepts = []
        for concept in prohibition_concepts:
            if concept in response_lower:
                found_concepts.append(concept)

        if not found_concepts:
            return {"found": False, "confidence": 0.0, "evidence": ""}

        # 检查上下文是否表明违反
        context_words = ["违反", "打破", "无视", "不顾", "虽然", "但是"]
        has_context = any(word in response_lower for word in context_words)

        evidence = f"响应中包含禁止概念: {', '.join(found_concepts)}"
        if has_context:
            evidence += "，且上下文表明可能违反"

        confidence = 0.7 if has_context else 0.4

        return {"found": True, "confidence": confidence, "evidence": evidence}

    async def _check_permission_misuse(
        self, response_text: str, permission: str, context: ReasoningContext
    ) -> Dict[str, Any]:
        """检查权限滥用"""
        # 简化实现
        permission_lower = permission.lower()
        response_lower = response_text.lower()

        # 提取权限范围
        if "只能" in permission_lower or "仅限于" in permission_lower:
            # 有限权限，检查是否超出范围
            scope_keywords = ["只能", "仅限于", "只在", "只有在"]
            scope_found = any(kw in permission_lower for kw in scope_keywords)

            if scope_found:
                # 检查响应中是否有超出范围的描述
                excess_keywords = ["也", "还", "同时", "另外", "除此之外"]
                excess_found = any(kw in response_lower for kw in excess_keywords)

                if excess_found:
                    return {
                        "found": True,
                        "confidence": 0.5,
                        "evidence": "响应可能超出权限范围",
                    }

        return {"found": False, "confidence": 0.0, "evidence": ""}

    async def _check_causality_violation_semantic(
        self, response_text: str, causality_rule: str, context: ReasoningContext
    ) -> Dict[str, Any]:
        """检查语义因果关系违反"""
        # 简化实现
        causality_patterns = [
            (r"时间倒流", "时间倒流违反因果关系"),
            (r"死而复生[^，。]*没有解释", "无解释的复活违反因果关系"),
            (r"因果颠倒", "因果颠倒违反逻辑"),
            (r"违反物理定律", "违反物理定律"),
        ]

        for pattern, description in causality_patterns:
            if re.search(pattern, response_text):
                # 检查是否有合理解释
                explanation_indicators = ["因为", "由于", "原因是", "解释为"]
                has_explanation = any(
                    indicator in response_text for indicator in explanation_indicators
                )

                if not has_explanation:
                    return {"found": True, "confidence": 0.8, "evidence": description}

        return {"found": False, "confidence": 0.0, "evidence": ""}

    async def _check_semantic_memory_consistency(
        self,
        response: Union[LLMResponse, str],
        memories: List[Dict[str, Any]],
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查记忆语义一致性"""
        issues = []
        response_text = (
            response.content if isinstance(response, LLMResponse) else response
        )

        for memory in memories:
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})

            if mem_type == "fact":
                fact_issues = await self._check_fact_semantic_consistency(
                    response_text, content, memory, context
                )
                issues.extend(fact_issues)

            elif mem_type == "character":
                character_issues = await self._check_character_semantic_consistency(
                    response_text, content, memory, context
                )
                issues.extend(character_issues)

            elif mem_type == "event":
                event_issues = await self._check_event_semantic_consistency(
                    response_text, content, memory, context
                )
                issues.extend(event_issues)

        return issues

    async def _check_fact_semantic_consistency(
        self,
        response_text: str,
        fact_content: Dict[str, Any],
        memory: Dict[str, Any],
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查事实语义一致性"""
        issues = []

        fact_description = fact_content.get("description", "") or str(fact_content)
        if not fact_description:
            return issues

        # 提取事实的关键元素
        fact_elements = self._extract_fact_elements(fact_description)

        for element in fact_elements:
            # 检查响应中是否有矛盾描述
            contradiction_patterns = [
                f"不是{element}",
                f"没有{element}",
                f"{element}不存在",
                f"从未有{element}",
            ]

            for pattern in contradiction_patterns:
                if re.search(pattern, response_text):
                    issues.append(
                        DeepConsistencyIssue(
                            type="fact_semantic_conflict",
                            severity="medium",
                            description=f"响应与已知事实矛盾",
                            evidence=f"事实: {fact_description[:100]}...，矛盾: {pattern}",
                            suggestion="调整响应以符合已知事实",
                            category=ConsistencyCategory.MEMORY_SEMANTIC,
                            confidence=0.6,
                            evidence_context=fact_description[:200],
                            impact_level="medium",
                        )
                    )
                    break

        return issues

    async def _check_character_semantic_consistency(
        self,
        response_text: str,
        character_content: Dict[str, Any],
        memory: Dict[str, Any],
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查角色语义一致性"""
        issues = []

        char_name = character_content.get("name", "")
        char_traits = character_content.get("traits", [])
        char_relationships = character_content.get("relationships", {})

        if not char_name:
            return issues

        # 检查角色名称是否出现在响应中
        if char_name not in response_text:
            return issues

        # 检查角色特征一致性
        for trait in char_traits[:5]:  # 限制检查数量
            # 查找可能矛盾的模式
            contradiction_patterns = [
                f"{char_name}[^，。]*不{trait}",
                f"{char_name}[^，。]*没有{trait}",
                f"虽然[^，。]*{char_name}[^，。]*{trait}[^，。]*但是",
            ]

            for pattern in contradiction_patterns:
                if re.search(pattern, response_text):
                    issues.append(
                        DeepConsistencyIssue(
                            type="character_trait_inconsistency",
                            severity="low",
                            description=f"角色特征不一致",
                            evidence=f"角色: {char_name}, 特征: {trait}，响应模式: {pattern}",
                            suggestion=f"保持角色'{char_name}'的特征'{trait}'一致性",
                            category=ConsistencyCategory.CHARACTER,
                            confidence=0.5,
                            evidence_context=f"角色{char_name}的特征{trait}",
                            impact_level="low",
                        )
                    )
                    break

        return issues

    async def _check_event_semantic_consistency(
        self,
        response_text: str,
        event_content: Dict[str, Any],
        memory: Dict[str, Any],
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查事件语义一致性"""
        issues = []

        event_description = event_content.get("description", "")
        event_time = event_content.get("time", "")
        event_location = event_content.get("location", "")

        if not event_description:
            return issues

        # 提取事件关键信息
        event_keywords = self._extract_keywords(event_description)

        # 检查时间线一致性
        if event_time:
            time_issues = await self._check_event_temporal_consistency(
                response_text, event_time, event_description, context
            )
            issues.extend(time_issues)

        return issues

    async def _check_narrative_logic(
        self,
        response: Union[LLMResponse, str],
        context: ReasoningContext,
        memories: List[Dict[str, Any]],
    ) -> List[DeepConsistencyIssue]:
        """检查叙事逻辑一致性"""
        issues = []
        response_text = (
            response.content if isinstance(response, LLMResponse) else response
        )

        # 1. 检查自相矛盾
        contradictions = self._find_semantic_contradictions(response_text)
        for contradiction in contradictions:
            issues.append(
                DeepConsistencyIssue(
                    type="narrative_contradiction",
                    severity="medium",
                    description="叙事中存在自相矛盾",
                    evidence=contradiction["evidence"],
                    suggestion="消除叙事中的矛盾",
                    category=ConsistencyCategory.NARRATIVE_LOGIC,
                    confidence=contradiction["confidence"],
                    evidence_context=contradiction["context"],
                    impact_level="medium",
                )
            )

        # 2. 检查逻辑连贯性
        coherence_issues = self._check_narrative_coherence(response_text)
        issues.extend(coherence_issues)

        # 3. 检查动机合理性
        motivation_issues = await self._check_character_motivations(
            response_text, memories, context
        )
        issues.extend(motivation_issues)

        return issues

    def _find_semantic_contradictions(self, text: str) -> List[Dict[str, Any]]:
        """查找语义矛盾"""
        contradictions = []

        # 定义矛盾模式
        contradiction_patterns = [
            {
                "pattern": r"是([^，。]+)但是[^，。]*不是\1",
                "description": "是/不是矛盾",
                "confidence": 0.8,
            },
            {
                "pattern": r"有([^，。]+)但是[^，。]*没有\1",
                "description": "有/没有矛盾",
                "confidence": 0.7,
            },
            {
                "pattern": r"能([^，。]+)但是[^，。]*不能\1",
                "description": "能/不能矛盾",
                "confidence": 0.7,
            },
            {
                "pattern": r"应该([^，。]+)但是[^，。]*不应该\1",
                "description": "应该/不应该矛盾",
                "confidence": 0.6,
            },
        ]

        for pattern_info in contradiction_patterns:
            matches = re.finditer(pattern_info["pattern"], text)
            for match in matches:
                contradictions.append(
                    {
                        "evidence": f"{pattern_info['description']}: {match.group(0)}",
                        "confidence": pattern_info["confidence"],
                        "context": text[
                            max(0, match.start() - 50) : min(
                                len(text), match.end() + 50
                            )
                        ],
                    }
                )

        return contradictions

    def _check_narrative_coherence(self, text: str) -> List[DeepConsistencyIssue]:
        """检查叙事连贯性"""
        issues = []

        # 检查段落过渡
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1:
            for i in range(len(paragraphs) - 1):
                para1 = paragraphs[i].strip()
                para2 = paragraphs[i + 1].strip()

                if para1 and para2:
                    # 检查过渡是否突兀
                    transition_score = self._evaluate_paragraph_transition(para1, para2)
                    if transition_score < 0.3:
                        issues.append(
                            DeepConsistencyIssue(
                                type="narrative_transition_abrupt",
                                severity="low",
                                description="段落过渡可能突兀",
                                evidence=f"段落{i+1}到段落{i+2}的过渡不自然",
                                suggestion="添加过渡语句或调整段落顺序",
                                category=ConsistencyCategory.NARRATIVE_LOGIC,
                                confidence=0.5,
                                evidence_context=f"{para1[-50:]}... → ...{para2[:50]}",
                                impact_level="low",
                            )
                        )

        # 检查主题一致性
        theme_issues = self._check_theme_consistency(text)
        issues.extend(theme_issues)

        return issues

    def _evaluate_paragraph_transition(self, para1: str, para2: str) -> float:
        """评估段落过渡质量"""
        score = 0.5

        # 检查时间连续性
        time_words = ["然后", "接着", "之后", "随后", "同时", "与此同时"]
        para1_end = para1[-20:] if len(para1) > 20 else para1
        para2_start = para2[:20] if len(para2) > 20 else para2

        # 如果前一段以时间词结束或后一段以时间词开始，过渡较好
        if any(word in para1_end for word in time_words) or any(
            word in para2_start for word in time_words
        ):
            score += 0.3

        # 检查主题连续性
        para1_keywords = set(
            re.findall(
                r"[\u4e00-\u9fff]{2,}", para1[-50:] if len(para1) > 50 else para1
            )
        )
        para2_keywords = set(
            re.findall(r"[\u4e00-\u9fff]{2,}", para2[:50] if len(para2) > 50 else para2)
        )

        common_keywords = para1_keywords & para2_keywords
        if common_keywords:
            score += min(len(common_keywords) * 0.1, 0.2)

        return min(score, 1.0)

    def _check_theme_consistency(self, text: str) -> List[DeepConsistencyIssue]:
        """检查主题一致性"""
        issues = []

        # 提取主要主题
        sentences = re.split(r"[。！？]", text)
        themes_by_sentence = []

        for sentence in sentences:
            if len(sentence.strip()) > 5:
                themes = self._extract_sentence_themes(sentence)
                themes_by_sentence.append(themes)

        # 检查主题变化是否合理
        if len(themes_by_sentence) > 2:
            for i in range(len(themes_by_sentence) - 1):
                current_themes = themes_by_sentence[i]
                next_themes = themes_by_sentence[i + 1]

                if current_themes and next_themes:
                    overlap = (
                        len(current_themes & next_themes)
                        / len(current_themes | next_themes)
                        if (current_themes | next_themes)
                        else 0
                    )

                    if overlap < 0.1 and i > 0:  # 主题变化很大且不是开头
                        issues.append(
                            DeepConsistencyIssue(
                                type="theme_inconsistency",
                                severity="low",
                                description="主题变化可能过于突兀",
                                evidence=f"句子{i+1}到句子{i+2}的主题变化较大",
                                suggestion="添加过渡或解释主题变化",
                                category=ConsistencyCategory.NARRATIVE_LOGIC,
                                confidence=0.4,
                                evidence_context=f"主题变化: {current_themes} → {next_themes}",
                                impact_level="low",
                            )
                        )

        return issues

    async def _check_character_motivations(
        self,
        response_text: str,
        memories: List[Dict[str, Any]],
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查角色动机合理性"""
        issues = []

        # 从记忆中提取角色信息
        character_memories = [m for m in memories if m.get("type") == "character"]

        for char_memory in character_memories:
            char_content = char_memory.get("content", {})
            char_name = char_content.get("name", "")

            if not char_name or char_name not in response_text:
                continue

            # 检查角色行为是否符合其性格
            char_traits = char_content.get("traits", [])
            char_motivations = char_content.get("motivations", [])

            # 查找角色在响应中的行为描述
            char_pattern = (
                f"{char_name}[^，。]*[做|行动|决定|选择|想要|试图][^，。]*[。！？]"
            )
            char_actions = re.findall(char_pattern, response_text)

            for action in char_actions:
                # 检查行为是否符合角色特征
                trait_match_score = self._evaluate_action_trait_match(
                    action, char_traits
                )
                if trait_match_score < 0.3:
                    issues.append(
                        DeepConsistencyIssue(
                            type="character_motivation_inconsistency",
                            severity="medium",
                            description="角色行为可能不符合其性格",
                            evidence=f"角色{char_name}的行为'{action[:50]}...'可能不符合其性格特征",
                            suggestion="调整角色行为以符合其性格设定",
                            category=ConsistencyCategory.CHARACTER,
                            confidence=0.6,
                            evidence_context=action,
                            impact_level="medium",
                        )
                    )

        return issues

    async def _check_style_consistency(
        self, response: Union[LLMResponse, str], rules_text: str
    ) -> List[DeepConsistencyIssue]:
        """检查风格基调一致性"""
        issues = []
        response_text = (
            response.content if isinstance(response, LLMResponse) else response
        )

        # 从规则中提取风格基调
        rule_style = self._extract_style_from_rules(rules_text)

        # 分析响应风格
        response_style = self._analyze_response_style(response_text)

        # 比较风格
        mismatches = []
        for style_category in rule_style:
            if style_category not in response_style:
                mismatches.append(style_category)

        if mismatches:
            issues.append(
                DeepConsistencyIssue(
                    type="style_tone_mismatch",
                    severity="low",
                    description="响应风格与规则基调不匹配",
                    evidence=f"规则基调: {', '.join(rule_style)}，响应基调: {', '.join(response_style)}",
                    suggestion="调整叙事风格以匹配规则基调",
                    category=ConsistencyCategory.STYLE_TONE,
                    confidence=0.7,
                    evidence_context=f"规则风格: {rule_style}，响应风格: {response_style}",
                    impact_level="low",
                )
            )

        # 检查语言风格一致性
        language_issues = self._check_language_style_consistency(response_text)
        issues.extend(language_issues)

        return issues

    async def _check_temporal_consistency(
        self,
        response: Union[LLMResponse, str],
        memories: List[Dict[str, Any]],
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查时间线一致性"""
        issues = []
        response_text = (
            response.content if isinstance(response, LLMResponse) else response
        )

        # 提取响应中的时间信息
        time_expressions = self._extract_time_expressions(response_text)

        # 检查时间顺序
        if len(time_expressions) > 1:
            order_issues = self._check_time_order_consistency(time_expressions)
            issues.extend(order_issues)

        # 检查与记忆的时间一致性
        memory_time_issues = await self._check_memory_temporal_consistency(
            response_text, memories, context
        )
        issues.extend(memory_time_issues)

        return issues

    async def _check_character_consistency(
        self,
        response: Union[LLMResponse, str],
        memories: List[Dict[str, Any]],
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查角色一致性"""
        issues = []
        response_text = (
            response.content if isinstance(response, LLMResponse) else response
        )

        # 从记忆中提取角色信息
        character_memories = [m for m in memories if m.get("type") == "character"]

        for char_memory in character_memories:
            char_content = char_memory.get("content", {})
            char_name = char_content.get("name", "")

            if not char_name:
                continue

            # 检查角色在响应中的表现是否一致
            char_appearances = self._find_character_appearances(
                response_text, char_name
            )

            for appearance in char_appearances:
                # 检查对话风格一致性
                if "说" in appearance or "道" in appearance:
                    dialogue_style = self._analyze_dialogue_style(appearance)
                    char_dialogue_style = char_content.get("dialogue_style", "")

                    if char_dialogue_style and dialogue_style != char_dialogue_style:
                        issues.append(
                            DeepConsistencyIssue(
                                type="character_dialogue_inconsistency",
                                severity="low",
                                description="角色对话风格不一致",
                                evidence=f"角色{char_name}的对话风格与设定不符",
                                suggestion="调整对话风格以符合角色设定",
                                category=ConsistencyCategory.CHARACTER,
                                confidence=0.5,
                                evidence_context=appearance,
                                impact_level="low",
                            )
                        )

        return issues

    async def _check_causality_consistency(
        self,
        response: Union[LLMResponse, str],
        interpretation: InterpretationResult,
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查因果关系一致性"""
        issues = []
        response_text = (
            response.content if isinstance(response, LLMResponse) else response
        )

        # 查找因果关系描述
        causality_patterns = [
            r"因为([^，。]+)所以[^，。]*",
            r"由于([^，。]+)因此[^，。]*",
            r"既然([^，。]+)那么[^，。]*",
        ]

        for pattern in causality_patterns:
            matches = re.finditer(pattern, response_text)
            for match in matches:
                causality_statement = match.group(0)

                # 检查因果关系是否合理
                is_plausible = self._evaluate_causality_plausibility(
                    causality_statement
                )
                if not is_plausible:
                    issues.append(
                        DeepConsistencyIssue(
                            type="causality_implausible",
                            severity="medium",
                            description="因果关系可能不合理",
                            evidence=f"因果关系陈述: {causality_statement}",
                            suggestion="提供更合理的因果关系解释",
                            category=ConsistencyCategory.CAUSALITY,
                            confidence=0.6,
                            evidence_context=causality_statement,
                            impact_level="medium",
                        )
                    )

        return issues

    async def _check_with_llm(
        self,
        response: Union[LLMResponse, str],
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> List[DeepConsistencyIssue]:
        """使用LLM进行深度语义检查"""
        if not self.llm_provider:
            return []

        issues = []
        response_text = (
            response.content if isinstance(response, LLMResponse) else response
        )

        try:
            # 构建LLM检查提示
            prompt = self._build_llm_consistency_prompt(
                response_text, context, interpretation, memories
            )

            # 调用LLM
            llm_response = await self.llm_provider.generate(
                prompt, temperature=0.3, max_tokens=500
            )

            # 解析LLM响应
            llm_issues = self._parse_llm_consistency_response(llm_response.content)
            issues.extend(llm_issues)

        except Exception as e:
            logger.error(f"LLM consistency check failed: {e}")

        return issues

    def _generate_deep_report(
        self, issues: List[DeepConsistencyIssue], context: ReasoningContext
    ) -> DeepConsistencyReport:
        """生成深度报告"""
        # 按分类统计
        category_counts = {}
        category_scores = {}

        for category in ConsistencyCategory:
            category_issues = [issue for issue in issues if issue.category == category]
            category_counts[category] = len(category_issues)

            # 计算分类分数（问题越少分数越高）
            if category_issues:
                avg_severity = self._calculate_avg_severity(category_issues)
                category_scores[category] = max(
                    0.0, 1.0 - (len(category_issues) * 0.1 + avg_severity * 0.3)
                )
            else:
                category_scores[category] = 1.0

        # 计算总体分数
        overall_score = self._calculate_overall_score(category_scores)

        # 生成修正建议
        suggestions = self._generate_correction_suggestions(issues)

        # 确定是否通过
        passed = (
            overall_score >= 0.7
            and len([i for i in issues if i.severity in ["high", "critical"]]) == 0
        )

        return DeepConsistencyReport(
            passed=passed,
            overall_score=overall_score,
            category_scores=category_scores,
            issues=issues,
            suggestions=suggestions,
            metadata={
                "session_id": context.session_id,
                "turn_number": context.turn_number,
                "issue_count": len(issues),
                "category_counts": {k.value: v for k, v in category_counts.items()},
                "critical_issues": len(
                    [i for i in issues if i.severity in ["high", "critical"]]
                ),
            },
        )

    # ========== 辅助方法 ==========

    def _extract_concepts(self, text: str) -> List[str]:
        """提取概念"""
        # 简化实现：提取名词性词汇
        import jieba
        import jieba.posseg as pseg

        try:
            words = pseg.cut(text)
            concepts = []

            for word, flag in words:
                if flag.startswith("n") and len(word) > 1:  # 名词且长度大于1
                    concepts.append(word)

            return concepts[:10]  # 限制数量
        except:
            # 如果jieba不可用，使用简单分词
            return [word for word in text.split() if len(word) > 1][:10]

    def _extract_fact_elements(self, fact_description: str) -> List[str]:
        """提取事实元素"""
        # 简化实现
        elements = []

        # 提取名词短语
        noun_patterns = [
            r"([\u4e00-\u9fff]{2,}的[\u4e00-\u9fff]{2,})",  # XX的XX
            r"([\u4e00-\u9fff]{3,})",  # 三字及以上词汇
        ]

        for pattern in noun_patterns:
            matches = re.findall(pattern, fact_description)
            elements.extend(matches)

        return list(set(elements))[:5]  # 去重并限制数量

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 使用简单分词
        words = re.findall(r"[\u4e00-\u9fff]{2,}", text)

        # 过滤常见虚词
        stop_words = {
            "的",
            "了",
            "在",
            "是",
            "有",
            "和",
            "与",
            "及",
            "或",
            "但",
            "而",
            "且",
            "虽然",
            "但是",
            "然而",
        }
        filtered = [word for word in words if word not in stop_words]

        # 按频率排序
        from collections import Counter

        word_counts = Counter(filtered)
        top_keywords = [word for word, _ in word_counts.most_common(10)]

        return top_keywords

    def _extract_sentence_themes(self, sentence: str) -> set:
        """提取句子主题"""
        themes = set()

        # 提取名词性短语作为主题
        noun_phrases = re.findall(r"[\u4e00-\u9fff]{2,}的[\u4e00-\u9fff]{2,}", sentence)
        themes.update(noun_phrases)

        # 提取主要名词
        nouns = re.findall(r"[\u4e00-\u9fff]{2,}", sentence)
        themes.update(nouns[:3])  # 取前3个名词

        return themes

    def _evaluate_action_trait_match(self, action: str, traits: List[str]) -> float:
        """评估行为与特征匹配度"""
        if not traits:
            return 0.5

        action_lower = action.lower()
        match_count = 0

        for trait in traits:
            trait_lower = trait.lower()

            # 检查行为是否体现特征
            if trait_lower in action_lower:
                match_count += 1
            else:
                # 检查是否有矛盾
                contradiction_patterns = [
                    f"不{trait_lower}",
                    f"没有{trait_lower}",
                    f"缺乏{trait_lower}",
                ]
                if any(pattern in action_lower for pattern in contradiction_patterns):
                    match_count -= 1

        return max(0.0, match_count / len(traits))

    def _extract_style_from_rules(self, rules_text: str) -> List[str]:
        """从规则中提取风格基调"""
        style_keywords = {
            "黑暗": ["黑暗", "恐怖", "死亡", "阴影", "邪恶", "绝望"],
            "光明": ["光明", "希望", "正义", "善良", "治愈", "和平"],
            "喜剧": ["幽默", "搞笑", "滑稽", "玩笑", "欢乐", "轻松"],
            "悲剧": ["悲伤", "痛苦", "失去", "死亡", "绝望", "牺牲"],
            "史诗": ["宏大", "壮丽", "传奇", "英雄", "命运", "历史"],
            "日常": ["平凡", "普通", "日常", "生活", "琐事", "现实"],
            "严肃": ["严肃", "认真", "正式", "庄重", "重要", "沉重"],
            "轻松": ["轻松", "愉快", "休闲", "随意", "有趣", "活泼"],
        }

        found_styles = []
        rules_lower = rules_text.lower()

        for style, keywords in style_keywords.items():
            for keyword in keywords:
                if keyword in rules_lower:
                    found_styles.append(style)
                    break

        return found_styles if found_styles else ["一般"]

    def _analyze_response_style(self, response_text: str) -> List[str]:
        """分析响应风格"""
        style_indicators = {
            "黑暗": ["黑暗", "恐怖", "死亡", "阴影", "邪恶", "绝望", "血腥", "恐怖"],
            "光明": ["光明", "希望", "正义", "善良", "治愈", "和平", "温暖", "阳光"],
            "喜剧": ["幽默", "搞笑", "滑稽", "玩笑", "欢乐", "轻松", "笑话", "有趣"],
            "悲剧": ["悲伤", "痛苦", "失去", "死亡", "绝望", "牺牲", "哭泣", "哀伤"],
            "史诗": ["宏大", "壮丽", "传奇", "英雄", "命运", "历史", "伟大", "不朽"],
            "日常": ["平凡", "普通", "日常", "生活", "琐事", "现实", "平常", "简单"],
            "严肃": ["严肃", "认真", "正式", "庄重", "重要", "沉重", "严峻", "紧张"],
            "轻松": ["轻松", "愉快", "休闲", "随意", "有趣", "活泼", "欢快", "舒适"],
        }

        found_styles = []
        response_lower = response_text.lower()

        for style, indicators in style_indicators.items():
            indicator_count = sum(
                1 for indicator in indicators if indicator in response_lower
            )
            if indicator_count >= 2:  # 至少出现2个相关词汇
                found_styles.append(style)

        return found_styles if found_styles else ["一般"]

    def _check_language_style_consistency(
        self, text: str
    ) -> List[DeepConsistencyIssue]:
        """检查语言风格一致性"""
        issues = []

        # 检查正式程度变化
        formal_words = ["阁下", "陛下", "臣", "卑职", "谨", "奉", "遵"]
        informal_words = ["哥们", "伙计", "喂", "嘿", "靠", "特么"]

        formal_count = sum(1 for word in formal_words if word in text)
        informal_count = sum(1 for word in informal_words if word in text)

        if formal_count > 0 and informal_count > 0:
            issues.append(
                DeepConsistencyIssue(
                    type="language_style_mixed",
                    severity="low",
                    description="语言风格混合（正式与非正式）",
                    evidence=f"包含{formal_count}个正式词汇和{informal_count}个非正式词汇",
                    suggestion="统一语言风格（选择正式或非正式）",
                    category=ConsistencyCategory.STYLE_TONE,
                    confidence=0.6,
                    evidence_context="语言风格不一致",
                    impact_level="low",
                )
            )

        return issues

    def _extract_time_expressions(self, text: str) -> List[Dict[str, Any]]:
        """提取时间表达式"""
        time_expressions = []

        # 时间词模式
        time_patterns = [
            (r"(\d+)年前", "relative_before"),
            (r"(\d+)年后", "relative_after"),
            (r"之前", "relative_before"),
            (r"之后", "relative_after"),
            (r"然后", "sequence"),
            (r"接着", "sequence"),
            (r"同时", "simultaneous"),
            (r"与此同时", "simultaneous"),
            (r"清晨", "absolute"),
            (r"中午", "absolute"),
            (r"傍晚", "absolute"),
            (r"夜晚", "absolute"),
        ]

        for pattern, time_type in time_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                time_expressions.append(
                    {
                        "text": match.group(0),
                        "type": time_type,
                        "position": match.start(),
                        "value": match.group(1) if match.groups() else None,
                    }
                )

        # 按位置排序
        time_expressions.sort(key=lambda x: x["position"])

        return time_expressions

    def _check_time_order_consistency(
        self, time_expressions: List[Dict[str, Any]]
    ) -> List[DeepConsistencyIssue]:
        """检查时间顺序一致性"""
        issues = []

        for i in range(len(time_expressions) - 1):
            current = time_expressions[i]
            next_expr = time_expressions[i + 1]

            # 检查相对时间顺序
            if (
                current["type"] == "relative_after"
                and next_expr["type"] == "relative_before"
            ):
                # "之后"后面不应该直接跟"之前"
                issues.append(
                    DeepConsistencyIssue(
                        type="temporal_order_inconsistent",
                        severity="low",
                        description="时间顺序可能混乱",
                        evidence=f"'{current['text']}'出现在'{next_expr['text']}'前面",
                        suggestion="检查时间顺序逻辑",
                        category=ConsistencyCategory.TEMPORAL,
                        confidence=0.5,
                        evidence_context=f"时间表达式: {current['text']} → {next_expr['text']}",
                        impact_level="low",
                    )
                )

        return issues

    async def _check_memory_temporal_consistency(
        self,
        response_text: str,
        memories: List[Dict[str, Any]],
        context: ReasoningContext,
    ) -> List[DeepConsistencyIssue]:
        """检查与记忆的时间一致性"""
        issues = []

        # 提取响应中的时间参考
        response_time_refs = self._extract_time_references(response_text)

        for memory in memories:
            if memory.get("type") == "event":
                event_time = memory.get("content", {}).get("time", "")
                if event_time and response_time_refs:
                    # 简化检查：如果提到事件时间，确保不矛盾
                    time_consistency = self._check_time_reference_consistency(
                        event_time, response_time_refs
                    )
                    if not time_consistency["consistent"]:
                        issues.append(
                            DeepConsistencyIssue(
                                type="memory_temporal_inconsistency",
                                severity="medium",
                                description="响应时间与事件记忆时间不一致",
                                evidence=time_consistency["evidence"],
                                suggestion="调整时间描述以符合历史事件时间",
                                category=ConsistencyCategory.TEMPORAL,
                                confidence=time_consistency["confidence"],
                                evidence_context=f"事件时间: {event_time}，响应时间: {response_time_refs}",
                                impact_level="medium",
                            )
                        )

        return issues

    def _extract_time_references(self, text: str) -> List[str]:
        """提取时间参考"""
        time_refs = []

        # 简单模式匹配
        patterns = [
            r"(\d+)年",
            r"(\d+)月",
            r"(\d+)日",
            r"(\d+)世纪",
            r"古代",
            r"现代",
            r"未来",
            r"过去",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            time_refs.extend(matches)

        return time_refs

    def _check_time_reference_consistency(
        self, event_time: str, response_times: List[str]
    ) -> Dict[str, Any]:
        """检查时间参考一致性"""
        # 简化实现
        if not event_time or not response_times:
            return {"consistent": True, "confidence": 0.0, "evidence": ""}

        # 检查是否有明显矛盾
        contradictions = []

        if "古代" in event_time and "现代" in response_times:
            contradictions.append("事件发生在古代但响应提到现代")
        elif "现代" in event_time and "古代" in response_times:
            contradictions.append("事件发生在现代但响应提到古代")
        elif "未来" in event_time and "过去" in response_times:
            contradictions.append("事件发生在未来但响应提到过去")

        if contradictions:
            return {
                "consistent": False,
                "confidence": 0.7,
                "evidence": "; ".join(contradictions),
            }

        return {"consistent": True, "confidence": 0.0, "evidence": ""}

    def _find_character_appearances(self, text: str, character_name: str) -> List[str]:
        """查找角色出现"""
        appearances = []

        # 查找包含角色名的句子
        sentences = re.split(r"[。！？]", text)

        for sentence in sentences:
            if character_name in sentence:
                appearances.append(sentence.strip())

        return appearances

    def _analyze_dialogue_style(self, dialogue: str) -> str:
        """分析对话风格"""
        # 简化实现
        if "：" in dialogue or "道：" in dialogue or "说：" in dialogue:
            return "formal"
        elif "：" not in dialogue and ("说" in dialogue or "问" in dialogue):
            return "informal"
        else:
            return "neutral"

    def _evaluate_causality_plausibility(self, causality_statement: str) -> bool:
        """评估因果关系合理性"""
        # 简化实现：检查常见不合理因果关系
        implausible_patterns = [
            r"因为下雨所以太阳出来了",
            r"因为饿了所以饱了",
            r"因为死了所以活了",
            r"因为年轻所以年老",
            r"因为成功所以失败",
        ]

        for pattern in implausible_patterns:
            if re.search(pattern, causality_statement):
                return False

        return True

    def _build_llm_consistency_prompt(
        self,
        response_text: str,
        context: ReasoningContext,
        interpretation: InterpretationResult,
        memories: List[Dict[str, Any]],
    ) -> str:
        """构建LLM一致性检查提示"""
        # 简化记忆格式化
        memory_summaries = []
        for memory in memories[:3]:  # 限制数量
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})
            if isinstance(content, dict):
                summary = content.get("summary", str(content)[:50])
            else:
                summary = str(content)[:50]
            memory_summaries.append(f"- [{mem_type}] {summary}")

        memories_text = (
            "\n".join(memory_summaries) if memory_summaries else "无相关记忆"
        )

        prompt = f"""请分析以下叙事响应的一致性问题：

# 世界观规则（摘要）
{context.rules_text[:500]}...

# 关键约束
{getattr(interpretation, 'narrative_output', '无解释结果')[:300]}

# 相关记忆
{memories_text}

# 玩家输入
{context.player_input}

# 待检查的叙事响应
{response_text}

请分析以上叙事响应是否存在以下一致性问题：
1. 规则违反：是否违反世界观规则或约束？
2. 记忆矛盾：是否与历史记忆矛盾？
3. 逻辑问题：是否存在逻辑矛盾或不合理之处？
4. 风格不一致：是否与世界观基调风格不一致？
5. 时间线问题：是否存在时间线矛盾？

请以JSON格式回答，包含以下字段：
- "issues": 问题列表，每个问题包含"type"（问题类型）、"description"（描述）、"evidence"（证据）、"severity"（严重程度：low/medium/high）、"suggestion"（修正建议）
- "overall_assessment": 总体评估（"consistent"/"minor_issues"/"major_issues"）
- "confidence": 分析置信度（0-1）

请确保分析具体、有证据支持。"""

        return prompt

    def _parse_llm_consistency_response(
        self, llm_response: str
    ) -> List[DeepConsistencyIssue]:
        """解析LLM一致性响应"""
        issues = []

        try:
            # 尝试解析JSON
            import json

            data = json.loads(llm_response)

            if "issues" in data:
                for issue_data in data["issues"]:
                    # 映射到DeepConsistencyIssue
                    category_map = {
                        "rule_violation": ConsistencyCategory.RULE_SEMANTIC,
                        "memory_contradiction": ConsistencyCategory.MEMORY_SEMANTIC,
                        "logic_problem": ConsistencyCategory.NARRATIVE_LOGIC,
                        "style_inconsistency": ConsistencyCategory.STYLE_TONE,
                        "timeline_issue": ConsistencyCategory.TEMPORAL,
                    }

                    issue_type = issue_data.get("type", "unknown")
                    category = category_map.get(
                        issue_type, ConsistencyCategory.NARRATIVE_LOGIC
                    )

                    issues.append(
                        DeepConsistencyIssue(
                            type=f"llm_{issue_type}",
                            severity=issue_data.get("severity", "medium"),
                            description=issue_data.get(
                                "description", "LLM检测到一致性问题"
                            ),
                            evidence=issue_data.get("evidence", "无具体证据"),
                            suggestion=issue_data.get("suggestion", "请检查一致性"),
                            category=category,
                            confidence=float(issue_data.get("confidence", 0.7)),
                            evidence_context="LLM分析结果",
                            impact_level=issue_data.get("severity", "medium"),
                        )
                    )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse LLM consistency response: {e}")
            # 尝试从文本中提取问题
            text_issues = self._extract_issues_from_text(llm_response)
            issues.extend(text_issues)

        return issues

    def _extract_issues_from_text(self, text: str) -> List[DeepConsistencyIssue]:
        """从文本中提取问题"""
        issues = []

        # 简单模式匹配
        issue_patterns = [
            (r"规则违反[：:]\s*(.+)", "rule_violation"),
            (r"记忆矛盾[：:]\s*(.+)", "memory_contradiction"),
            (r"逻辑问题[：:]\s*(.+)", "logic_problem"),
            (r"风格不一致[：:]\s*(.+)", "style_inconsistency"),
            (r"时间线问题[：:]\s*(.+)", "timeline_issue"),
        ]

        for pattern, issue_type in issue_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                description = match.group(1).strip()
                if len(description) > 10:  # 确保有实质内容
                    issues.append(
                        DeepConsistencyIssue(
                            type=f"llm_{issue_type}",
                            severity="medium",
                            description=description[:100],
                            evidence="从LLM分析中提取",
                            suggestion="根据LLM分析进行修正",
                            category=ConsistencyCategory.NARRATIVE_LOGIC,
                            confidence=0.6,
                            evidence_context=description[:200],
                            impact_level="medium",
                        )
                    )

        return issues

    def _calculate_avg_severity(self, issues: List[DeepConsistencyIssue]) -> float:
        """计算平均严重程度"""
        if not issues:
            return 0.0

        severity_values = {"low": 0.3, "medium": 0.6, "high": 0.9, "critical": 1.0}

        total = sum(severity_values.get(issue.severity, 0.5) for issue in issues)
        return total / len(issues)

    def _calculate_overall_score(
        self, category_scores: Dict[ConsistencyCategory, float]
    ) -> float:
        """计算总体分数"""
        if not category_scores:
            return 1.0

        # 加权平均，重要类别权重更高
        weights = {
            ConsistencyCategory.RULE_SEMANTIC: 0.25,
            ConsistencyCategory.MEMORY_SEMANTIC: 0.20,
            ConsistencyCategory.NARRATIVE_LOGIC: 0.15,
            ConsistencyCategory.CAUSALITY: 0.15,
            ConsistencyCategory.CHARACTER: 0.10,
            ConsistencyCategory.TEMPORAL: 0.08,
            ConsistencyCategory.STYLE_TONE: 0.07,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for category, score in category_scores.items():
            weight = weights.get(category, 0.05)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return sum(category_scores.values()) / len(category_scores)

    def _generate_correction_suggestions(
        self, issues: List[DeepConsistencyIssue]
    ) -> List[str]:
        """生成修正建议"""
        suggestions = []

        # 按问题类型分组
        issue_types = {}
        for issue in issues:
            issue_type = issue.type
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        # 为每种问题类型生成建议
        for issue_type, type_issues in issue_types.items():
            if issue_type.startswith("rule_"):
                suggestions.append("检查并修正规则违反")
            elif issue_type.startswith("memory_"):
                suggestions.append("调整响应以符合历史记忆")
            elif issue_type.startswith("character_"):
                suggestions.append("确保角色行为符合性格设定")
            elif issue_type.startswith("temporal_"):
                suggestions.append("检查并修正时间线问题")
            elif issue_type.startswith("style_"):
                suggestions.append("统一叙事风格和基调")
            elif issue_type.startswith("causality_"):
                suggestions.append("确保因果关系合理")
            elif issue_type.startswith("narrative_"):
                suggestions.append("消除叙事逻辑矛盾")

        # 去重并限制数量
        unique_suggestions = list(set(suggestions))
        return unique_suggestions[:5]

    def _initialize_patterns(self) -> Dict[str, Any]:
        """初始化模式"""
        return {
            "contradiction_patterns": [
                r"是([^，。]+)但是[^，。]*不是\1",
                r"有([^，。]+)但是[^，。]*没有\1",
                r"能([^，。]+)但是[^，。]*不能\1",
            ],
            "causality_patterns": [
                r"因为([^，。]+)所以[^，。]*",
                r"由于([^，。]+)因此[^，。]*",
                r"既然([^，。]+)那么[^，。]*",
            ],
            "time_patterns": [
                r"(\d+)年前",
                r"(\d+)年后",
                r"之前",
                r"之后",
                r"然后",
                r"接着",
            ],
        }

    # ========== 批量处理和高级功能 ==========

    async def batch_deep_check(
        self,
        responses: List[Union[LLMResponse, str]],
        contexts: List[ReasoningContext],
        interpretations: List[InterpretationResult],
        memories_list: List[List[Dict[str, Any]]],
    ) -> List[DeepConsistencyReport]:
        """批量深度检查"""
        if (
            len(responses) != len(contexts)
            or len(responses) != len(interpretations)
            or len(responses) != len(memories_list)
        ):
            raise ValueError("All input lists must have the same length")

        tasks = []
        for i in range(len(responses)):
            task = self.deep_check(
                responses[i], contexts[i], interpretations[i], memories_list[i]
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch deep check failed for item {i}: {result}")
                # 创建降级报告
                fallback_report = DeepConsistencyReport(
                    passed=False,
                    overall_score=0.0,
                    category_scores={},
                    issues=[],
                    suggestions=["检查过程出错"],
                    metadata={"error": str(result)},
                )
                final_results.append(fallback_report)
            else:
                final_results.append(result)

        return final_results

    def generate_comparative_report(
        self, reports: List[DeepConsistencyReport]
    ) -> Dict[str, Any]:
        """生成比较报告"""
        if not reports:
            return {"error": "No reports"}

        total = len(reports)

        # 统计指标
        avg_overall_score = sum(r.overall_score for r in reports) / total
        pass_count = sum(1 for r in reports if r.passed)
        pass_rate = pass_count / total * 100

        # 分类分数统计
        category_stats = {}
        for report in reports:
            for category, score in report.category_scores.items():
                if category not in category_stats:
                    category_stats[category] = []
                category_stats[category].append(score)

        avg_category_scores = {}
        for category, scores in category_stats.items():
            avg_category_scores[category.value] = sum(scores) / len(scores)

        # 问题类型分布
        issue_types = {}
        for report in reports:
            for issue in report.issues:
                issue_type = issue.type
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        # 严重程度分布
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for report in reports:
            for issue in report.issues:
                severity_counts[issue.severity] = (
                    severity_counts.get(issue.severity, 0) + 1
                )

        return {
            "total_checked": total,
            "pass_rate": pass_rate,
            "average_overall_score": avg_overall_score,
            "average_category_scores": avg_category_scores,
            "issue_type_distribution": issue_types,
            "severity_distribution": severity_counts,
            "recommendations": self._generate_batch_recommendations(reports),
        }

    def _generate_batch_recommendations(
        self, reports: List[DeepConsistencyReport]
    ) -> List[str]:
        """生成批量建议"""
        recommendations = []

        # 收集常见问题
        common_issues = {}
        for report in reports:
            for issue in report.issues:
                issue_type = issue.type
                common_issues[issue_type] = common_issues.get(issue_type, 0) + 1

        # 找出最常见的问题类型
        if common_issues:
            sorted_issues = sorted(
                common_issues.items(), key=lambda x: x[1], reverse=True
            )
            top_issues = sorted_issues[:3]

            for issue_type, count in top_issues:
                if issue_type.startswith("rule_"):
                    recommendations.append(
                        f"常见问题：规则违反（出现{count}次），建议加强规则理解"
                    )
                elif issue_type.startswith("memory_"):
                    recommendations.append(
                        f"常见问题：记忆矛盾（出现{count}次），建议改进记忆整合"
                    )
                elif issue_type.startswith("character_"):
                    recommendations.append(
                        f"常见问题：角色不一致（出现{count}次），建议统一角色设定"
                    )

        # 总体建议
        pass_rate = sum(1 for r in reports if r.passed) / len(reports) * 100
        if pass_rate < 70:
            recommendations.append(
                f"整体通过率较低（{pass_rate:.1f}%），建议全面检查一致性流程"
            )

        return recommendations[:5]
