"""
一致性检查器

检查LLM输出与规则/记忆的一致性。
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .rule_interpreter import RuleConstraint
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ConsistencyIssue:
    """一致性问题"""

    type: str  # "rule_violation", "memory_conflict", "tone_mismatch", "logic_error"
    severity: str  # "low", "medium", "high"
    description: str
    evidence: str
    suggestion: Optional[str] = None


@dataclass
class ConsistencyReport:
    """一致性报告"""

    passed: bool
    score: float  # 0-1
    issues: List[ConsistencyIssue]
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsistencyChecker:
    """一致性检查器"""

    def __init__(self):
        self.rules_cache = {}
        logger.info("ConsistencyChecker initialized")

    def check(
        self, response: str, rules_text: str, constraints: List[RuleConstraint]
    ) -> Dict[str, Any]:
        """检查一致性"""
        issues = []

        # 检查规则违反
        rule_issues = self._check_rule_violations(response, constraints)
        issues.extend(rule_issues)

        # 检查逻辑一致性
        logic_issues = self._check_logic_consistency(response)
        issues.extend(logic_issues)

        # 检查基调一致性
        tone_issues = self._check_tone_consistency(response, rules_text)
        issues.extend(tone_issues)

        # 计算分数
        score = self._calculate_consistency_score(issues)

        # 生成报告
        report = ConsistencyReport(
            passed=len(issues) == 0,
            score=score,
            issues=issues,
            summary=self._generate_summary(issues, score),
        )

        logger.debug(f"Consistency check: {len(issues)} issues, score={score:.2f}")

        return report.__dict__

    def _check_rule_violations(
        self, response: str, constraints: List[RuleConstraint]
    ) -> List[ConsistencyIssue]:
        """检查规则违反"""
        issues = []

        for constraint in constraints:
            if constraint.type == "permission":
                # 检查禁止性规则
                if constraint.metadata.get("is_prohibition", False):
                    # 简单关键词匹配
                    violation = self._check_prohibition_violation(
                        response, constraint.content
                    )
                    if violation:
                        issues.append(
                            ConsistencyIssue(
                                type="rule_violation",
                                severity="high",
                                description=f"违反禁止性规则",
                                evidence=f"规则: {constraint.content}",
                                suggestion="修改响应以避免违反此规则",
                            )
                        )

            elif constraint.type == "causality":
                # 检查因果关系违反
                violation = self._check_causality_violation(
                    response, constraint.content
                )
                if violation:
                    issues.append(
                        ConsistencyIssue(
                            type="rule_violation",
                            severity="medium",
                            description=f"违反因果关系规则",
                            evidence=f"规则: {constraint.content}",
                            suggestion="确保响应符合世界因果关系",
                        )
                    )

        return issues

    def _check_prohibition_violation(self, response: str, prohibition: str) -> bool:
        """检查禁止性规则违反"""
        # 简化实现：提取禁止内容并检查
        prohibition_lower = prohibition.lower()
        response_lower = response.lower()

        # 查找禁止关键词
        prohibition_keywords = ["不能", "禁止", "不允许", "不可以", "禁止"]
        for keyword in prohibition_keywords:
            if keyword in prohibition_lower:
                # 提取禁止的对象
                # 简化：直接检查整个句子
                if any(word in response_lower for word in ["违反", "打破", "无视"]):
                    return True

        return False

    def _check_causality_violation(self, response: str, causality_rule: str) -> bool:
        """检查因果关系违反"""
        # 简化实现
        causality_keywords = ["时间倒流", "死而复生", "因果颠倒", "违反物理"]
        response_lower = response.lower()

        for keyword in causality_keywords:
            if keyword in causality_rule and keyword in response_lower:
                # 检查是否在描述违反
                context_words = ["但是", "然而", "突然", "奇迹般地", "违反"]
                for context in context_words:
                    if context in response_lower:
                        return True

        return False

    def _check_logic_consistency(self, response: str) -> List[ConsistencyIssue]:
        """检查逻辑一致性"""
        issues = []

        # 检查自相矛盾
        contradictions = self._find_contradictions(response)
        for contradiction in contradictions:
            issues.append(
                ConsistencyIssue(
                    type="logic_error",
                    severity="medium",
                    description="响应中存在自相矛盾",
                    evidence=contradiction,
                    suggestion="确保叙事逻辑一致",
                )
            )

        # 检查时间顺序
        time_issues = self._check_temporal_consistency(response)
        issues.extend(time_issues)

        return issues

    def _find_contradictions(self, text: str) -> List[str]:
        """查找自相矛盾"""
        contradictions = []

        # 简单模式匹配
        patterns = [
            (r"是.*但是.*不是", "是/不是矛盾"),
            (r"有.*但是.*没有", "有/没有矛盾"),
            (r"能.*但是.*不能", "能/不能矛盾"),
        ]

        for pattern, description in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                contradictions.append(f"{description}: {match.group(0)}")

        return contradictions

    def _check_temporal_consistency(self, response: str) -> List[ConsistencyIssue]:
        """检查时间顺序一致性"""
        issues = []

        # 查找时间相关词汇
        time_words = ["之前", "之后", "然后", "接着", "同时", "与此同时"]
        time_mentions = []

        for word in time_words:
            if word in response:
                time_mentions.append(word)

        # 如果有多个时间词，检查顺序
        if len(time_mentions) > 1:
            # 简化检查：确保"之前"在"之后"前面
            if "之后" in response and "之前" in response:
                after_idx = response.find("之后")
                before_idx = response.find("之前")
                if after_idx < before_idx:
                    issues.append(
                        ConsistencyIssue(
                            type="logic_error",
                            severity="low",
                            description="时间顺序可能混乱",
                            evidence="'之后'出现在'之前'前面",
                            suggestion="检查时间顺序逻辑",
                        )
                    )

        return issues

    def _check_tone_consistency(
        self, response: str, rules_text: str
    ) -> List[ConsistencyIssue]:
        """检查基调一致性"""
        issues = []

        # 从规则中提取基调
        tone_keywords = self._extract_tone_keywords(rules_text)
        if not tone_keywords:
            return issues

        # 检查响应中的基调
        response_tone = self._analyze_response_tone(response)

        # 比较基调
        mismatches = []
        for rule_tone in tone_keywords:
            if rule_tone not in response_tone:
                mismatches.append(rule_tone)

        if mismatches:
            issues.append(
                ConsistencyIssue(
                    type="tone_mismatch",
                    severity="low",
                    description="响应基调与规则基调不匹配",
                    evidence=f"规则基调: {', '.join(tone_keywords)}，响应基调: {', '.join(response_tone)}",
                    suggestion="调整叙事基调以匹配规则",
                )
            )

        return issues

    def _extract_tone_keywords(self, rules_text: str) -> List[str]:
        """从规则中提取基调关键词"""
        tone_keywords = ["黑暗", "光明", "喜剧", "悲剧", "严肃", "轻松", "史诗", "日常"]
        found = []

        for keyword in tone_keywords:
            if keyword in rules_text:
                found.append(keyword)

        return found

    def _analyze_response_tone(self, response: str) -> List[str]:
        """分析响应基调"""
        tone_indicators = {
            "黑暗": ["黑暗", "恐怖", "死亡", "阴影", "邪恶"],
            "光明": ["光明", "希望", "正义", "善良", "治愈"],
            "喜剧": ["幽默", "搞笑", "滑稽", "玩笑", "欢乐"],
            "悲剧": ["悲伤", "痛苦", "失去", "死亡", "绝望"],
            "严肃": ["严肃", "认真", "正式", "庄重", "重要"],
            "轻松": ["轻松", "愉快", "休闲", "随意", "有趣"],
        }

        found_tones = []
        response_lower = response.lower()

        for tone, indicators in tone_indicators.items():
            for indicator in indicators:
                if indicator in response_lower:
                    found_tones.append(tone)
                    break

        return found_tones

    def _calculate_consistency_score(self, issues: List[ConsistencyIssue]) -> float:
        """计算一致性分数"""
        if not issues:
            return 1.0

        # 根据问题严重性扣分
        penalty = 0.0
        for issue in issues:
            if issue.severity == "high":
                penalty += 0.3
            elif issue.severity == "medium":
                penalty += 0.15
            elif issue.severity == "low":
                penalty += 0.05

        score = max(0.0, 1.0 - penalty)
        return score

    def _generate_summary(self, issues: List[ConsistencyIssue], score: float) -> str:
        """生成摘要"""
        if not issues:
            return f"一致性检查通过，分数：{score:.2f}"

        issue_counts = {}
        for issue in issues:
            issue_counts[issue.type] = issue_counts.get(issue.type, 0) + 1

        counts_str = ", ".join([f"{k}: {v}" for k, v in issue_counts.items()])
        return f"发现{len(issues)}个问题 ({counts_str})，一致性分数：{score:.2f}"

    def check_with_llm(
        self, response: str, rules_text: str, llm_provider
    ) -> Dict[str, Any]:
        """使用LLM进行更深入的一致性检查"""
        # 此方法可以使用LLM进行更复杂的检查
        # 简化实现
        logger.info("Using LLM for enhanced consistency check")

        # 返回基本检查结果
        return self.check(response, rules_text, [])

    def check_with_memories(
        self,
        response: str,
        memories: List[Dict[str, Any]],
        constraints: List[RuleConstraint] = None,
    ) -> Dict[str, Any]:
        """检查与历史记忆的一致性"""
        issues = []

        # 检查与记忆的一致性
        memory_issues = self._check_memory_consistency(response, memories)
        issues.extend(memory_issues)

        # 检查规则违反（如果提供了约束）
        if constraints:
            rule_issues = self._check_rule_violations(response, constraints)
            issues.extend(rule_issues)

        # 计算分数
        score = self._calculate_consistency_score(issues)

        # 生成报告
        report = ConsistencyReport(
            passed=len(issues) == 0,
            score=score,
            issues=issues,
            summary=self._generate_memory_summary(issues, score, len(memories)),
        )

        logger.debug(
            f"Memory consistency check: {len(issues)} issues, score={score:.2f}, memories={len(memories)}"
        )

        return report.__dict__

    def _check_memory_consistency(
        self, response: str, memories: List[Dict[str, Any]]
    ) -> List[ConsistencyIssue]:
        """检查记忆一致性"""
        issues = []

        for memory in memories:
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})

            # 根据记忆类型检查一致性
            if mem_type == "fact":
                fact_issues = self._check_fact_consistency(response, content)
                issues.extend(fact_issues)
            elif mem_type == "character":
                character_issues = self._check_character_consistency(response, content)
                issues.extend(character_issues)
            elif mem_type == "event":
                event_issues = self._check_event_consistency(response, content)
                issues.extend(event_issues)

        return issues

    def _check_fact_consistency(
        self, response: str, fact: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查事实一致性"""
        issues = []

        # 提取事实内容
        fact_text = fact.get("description", "") or str(fact)
        fact_keywords = self._extract_keywords(fact_text)

        # 检查响应是否与事实矛盾
        response_lower = response.lower()

        # 简单实现：检查否定性关键词
        negation_patterns = [
            (r"不是" + r"[^。]*?" + kw, f"否定事实: {kw}") for kw in fact_keywords[:3]
        ]

        for pattern, description in negation_patterns:
            if re.search(pattern, response_lower):
                issues.append(
                    ConsistencyIssue(
                        type="memory_conflict",
                        severity="medium",
                        description=f"响应与已知事实矛盾",
                        evidence=f"事实: {fact_text[:100]}...",
                        suggestion="检查事实一致性",
                    )
                )
                break

        return issues

    def _check_character_consistency(
        self, response: str, character: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查角色一致性"""
        issues = []

        # 提取角色信息
        char_name = character.get("name", "")
        char_traits = character.get("traits", [])
        char_relationships = character.get("relationships", {})

        if not char_name:
            return issues

        # 检查角色名称是否出现在响应中
        if char_name.lower() in response.lower():
            # 检查角色特征一致性
            for trait in char_traits[:5]:  # 限制检查数量
                trait_lower = trait.lower()
                response_lower = response.lower()

                # 检查是否有矛盾描述
                contradiction_patterns = [
                    f"{char_name}.*不.*{trait_lower}",
                    f"{char_name}.*没有.*{trait_lower}",
                    f"虽然.*{char_name}.*{trait_lower}.*但是",
                ]

                for pattern in contradiction_patterns:
                    if re.search(pattern, response_lower):
                        issues.append(
                            ConsistencyIssue(
                                type="character_inconsistency",
                                severity="low",
                                description=f"角色特征不一致",
                                evidence=f"角色: {char_name}, 特征: {trait}",
                                suggestion=f"保持角色'{char_name}'的特征'{trait}'一致性",
                            )
                        )
                        break

        return issues

    def _check_event_consistency(
        self, response: str, event: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查事件一致性"""
        issues = []

        # 提取事件信息
        event_desc = event.get("description", "")
        event_time = event.get("time", "")
        event_location = event.get("location", "")

        if not event_desc:
            return issues

        # 检查时间顺序一致性
        if event_time and "之前" in response or "之后" in response:
            # 简单检查：如果提到事件时间，确保时间顺序合理
            time_keywords = ["之前", "之后", "然后", "接着"]
            time_mentions = [kw for kw in time_keywords if kw in response]

            if len(time_mentions) > 1:
                # 这里可以添加更复杂的时间逻辑检查
                pass

        return issues

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词"""
        # 简单实现：提取名词性词汇
        import jieba
        import jieba.posseg as pseg

        try:
            words = pseg.cut(text)
            keywords = []

            for word, flag in words:
                if flag.startswith("n") and len(word) > 1:  # 名词且长度大于1
                    keywords.append(word)
                    if len(keywords) >= max_keywords:
                        break

            return keywords
        except:
            # 如果jieba不可用，使用简单分词
            return [word for word in text.split() if len(word) > 1][:max_keywords]

    def _generate_memory_summary(
        self, issues: List[ConsistencyIssue], score: float, memory_count: int
    ) -> str:
        """生成记忆一致性摘要"""
        if not issues:
            return (
                f"记忆一致性检查通过（检查了{memory_count}条记忆），分数：{score:.2f}"
            )

        memory_issues = [
            i
            for i in issues
            if i.type in ["memory_conflict", "character_inconsistency"]
        ]
        other_issues = [
            i
            for i in issues
            if i.type not in ["memory_conflict", "character_inconsistency"]
        ]

        summary_parts = []

        if memory_issues:
            summary_parts.append(f"发现{len(memory_issues)}个记忆相关问题")

        if other_issues:
            summary_parts.append(f"发现{len(other_issues)}个其他一致性问题")

        summary = "，".join(summary_parts)
        return f"{summary}，一致性分数：{score:.2f}（检查了{memory_count}条记忆）"

    def generate_correction_suggestions(
        self, issues: List[ConsistencyIssue], response: str
    ) -> List[Dict[str, str]]:
        """生成修正建议"""
        suggestions = []

        for issue in issues:
            suggestion = {
                "issue_type": issue.type,
                "severity": issue.severity,
                "description": issue.description,
                "suggestion": issue.suggestion
                or self._get_default_suggestion(issue.type),
                "evidence": issue.evidence[:200],  # 限制长度
            }

            # 添加具体的修正建议
            if issue.type == "rule_violation":
                suggestion["specific_advice"] = (
                    "考虑修改响应以避免直接违反规则，或添加解释说明为什么这个例外是合理的。"
                )
            elif issue.type == "memory_conflict":
                suggestion["specific_advice"] = (
                    "检查历史记忆，确保新响应不与已建立的事实矛盾。"
                )
            elif issue.type == "character_inconsistency":
                suggestion["specific_advice"] = (
                    "保持角色特征的一致性，如果需要改变，请提供合理的角色发展解释。"
                )
            elif issue.type == "tone_mismatch":
                suggestion["specific_advice"] = (
                    "调整语言风格以匹配故事基调，使用更符合基调的词汇和句式。"
                )
            elif issue.type == "logic_error":
                suggestion["specific_advice"] = (
                    "检查逻辑矛盾，确保叙事前后一致，时间顺序合理。"
                )

            suggestions.append(suggestion)

        return suggestions

    def _get_default_suggestion(self, issue_type: str) -> str:
        """获取默认建议"""
        suggestions = {
            "rule_violation": "修改响应以符合规则约束",
            "memory_conflict": "检查并修正与历史记忆的矛盾",
            "character_inconsistency": "保持角色特征的一致性",
            "tone_mismatch": "调整叙事基调以匹配规则",
            "logic_error": "修正逻辑矛盾，确保叙事连贯",
        }

        return suggestions.get(issue_type, "检查并修正不一致之处")
