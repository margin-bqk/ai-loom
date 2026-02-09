"""
规则解释器

加载并解释Markdown规则，提取关键约束和指导原则。
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..rules.markdown_canon import MarkdownCanon, CanonSection
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RuleConstraint:
    """规则约束"""

    type: str  # "permission", "causality", "tone", "world", "conflict"
    content: str
    priority: int = 1  # 1-5，越高越重要
    source_section: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterpretationResult:
    """解释结果"""

    constraints: List[RuleConstraint]
    key_themes: List[str]
    narrative_guidelines: List[str]
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuleInterpreter:
    """规则解释器"""

    def __init__(self):
        self.cache: Dict[str, InterpretationResult] = {}
        logger.info("RuleInterpreter initialized")

    def interpret(
        self, canon: MarkdownCanon, use_cache: bool = True
    ) -> InterpretationResult:
        """解释规则集"""
        cache_key = f"{canon.path}:{hash(canon.get_full_text())}"

        if use_cache and cache_key in self.cache:
            logger.debug(f"Using cached interpretation for {canon.path}")
            return self.cache[cache_key]

        constraints = []
        key_themes = []
        narrative_guidelines = []

        # 处理每个章节
        for section_name, section in canon.sections.items():
            section_constraints = self._interpret_section(section)
            constraints.extend(section_constraints)

            # 提取关键主题
            themes = self._extract_themes(section)
            key_themes.extend(themes)

            # 提取叙事指南
            guidelines = self._extract_guidelines(section)
            narrative_guidelines.extend(guidelines)

        # 去重
        key_themes = list(set(key_themes))
        narrative_guidelines = list(set(narrative_guidelines))

        # 生成摘要
        summary = self._generate_summary(constraints, key_themes)

        result = InterpretationResult(
            constraints=constraints,
            key_themes=key_themes,
            narrative_guidelines=narrative_guidelines,
            summary=summary,
            metadata={
                "canon_path": str(canon.path),
                "canon_version": canon.metadata.get("version", "unknown"),
                "sections_interpreted": len(canon.sections),
            },
        )

        # 缓存结果
        self.cache[cache_key] = result
        logger.info(
            f"Interpreted canon {canon.path}, found {len(constraints)} constraints"
        )

        return result

    def _interpret_section(self, section: CanonSection) -> List[RuleConstraint]:
        """解释单个章节"""
        constraints = []
        content = section.content

        # 根据章节类型使用不同的解析策略
        if section.section_type.name == "PERMISSIONS":
            constraints.extend(self._parse_permissions(content, section.name))
        elif section.section_type.name == "CAUSALITY":
            constraints.extend(self._parse_causality(content, section.name))
        elif section.section_type.name == "TONE":
            constraints.extend(self._parse_tone(content, section.name))
        elif section.section_type.name == "CONFLICT":
            constraints.extend(self._parse_conflict(content, section.name))
        elif section.section_type.name == "WORLD":
            constraints.extend(self._parse_world(content, section.name))

        # 为所有约束设置来源
        for constraint in constraints:
            constraint.source_section = section.name

        return constraints

    def _parse_permissions(
        self, content: str, section_name: str
    ) -> List[RuleConstraint]:
        """解析权限章节"""
        constraints = []

        # 首先按句子分割（中文句子分隔符：。！？；）
        import re

        sentences = re.split(r"[。！？；]", content)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_lower = sentence.lower()

            if any(
                word in sentence_lower for word in ["不能", "禁止", "不允许", "不可以"]
            ):
                constraints.append(
                    RuleConstraint(
                        type="permission",
                        content=sentence,
                        priority=3,  # 禁止性规则优先级较高
                        metadata={"is_prohibition": True},
                    )
                )
            elif any(word in sentence_lower for word in ["可以", "允许", "能够"]):
                constraints.append(
                    RuleConstraint(
                        type="permission",
                        content=sentence,
                        priority=2,
                        metadata={"is_prohibition": False},
                    )
                )

        return constraints

    def _parse_causality(self, content: str, section_name: str) -> List[RuleConstraint]:
        """解析因果关系章节"""
        constraints = []

        # 查找时间、死亡、因果相关描述
        patterns = [
            (r"(时间|时光|时序).*?(流动|倒流|停止|跳跃)", "time_flow"),
            (r"(死亡|死去|牺牲).*?(可逆|不可逆|永久|暂时)", "death"),
            (r"(因果|原因|结果).*?(必然|偶然|随机)", "causality"),
        ]

        for pattern, constraint_type in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                constraints.append(
                    RuleConstraint(
                        type="causality",
                        content=match.group(0),
                        priority=4,  # 因果关系通常很重要
                        metadata={"subtype": constraint_type},
                    )
                )

        return constraints

    def _parse_tone(self, content: str, section_name: str) -> List[RuleConstraint]:
        """解析叙事基调章节"""
        constraints = []

        # 提取基调描述
        tone_keywords = ["黑暗", "光明", "喜剧", "悲剧", "严肃", "轻松", "史诗", "日常"]

        for keyword in tone_keywords:
            if keyword in content:
                constraints.append(
                    RuleConstraint(
                        type="tone",
                        content=f"叙事基调包含'{keyword}'元素",
                        priority=2,
                        metadata={"tone_keyword": keyword},
                    )
                )

        return constraints

    def _parse_conflict(self, content: str, section_name: str) -> List[RuleConstraint]:
        """解析冲突解决章节"""
        constraints = []

        # 查找冲突解决策略
        strategies = ["现实主义", "戏剧性", "规则化", "玩家决定", "随机"]

        for strategy in strategies:
            if strategy in content:
                constraints.append(
                    RuleConstraint(
                        type="conflict",
                        content=f"冲突解决倾向于{strategy}",
                        priority=3,
                        metadata={"strategy": strategy},
                    )
                )

        return constraints

    def _parse_world(self, content: str, section_name: str) -> List[RuleConstraint]:
        """解析世界观章节"""
        constraints = []

        # 提取重要设定
        important_phrases = self._extract_important_phrases(content)
        for phrase in important_phrases:
            constraints.append(
                RuleConstraint(
                    type="world",
                    content=phrase,
                    priority=2,
                    metadata={"is_setting": True},
                )
            )

        return constraints

    def _extract_important_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """提取重要短语"""
        # 简单实现：提取包含关键名词的句子
        important_nouns = ["世界", "法则", "种族", "文化", "历史", "魔法", "科技"]
        sentences = re.split(r"[。！？]", text)

        phrases = []
        for sentence in sentences:
            if any(noun in sentence for noun in important_nouns):
                phrases.append(sentence.strip())
                if len(phrases) >= max_phrases:
                    break

        return phrases

    def _extract_themes(self, section: CanonSection) -> List[str]:
        """提取关键主题"""
        themes = []
        content = section.content

        # 根据章节类型提取主题
        if section.section_type.name == "WORLD":
            world_themes = [
                "奇幻",
                "科幻",
                "现实",
                "历史",
                "神话",
                "未来",
                "古代",
                "魔法",
                "龙",
                "种族",
            ]
            themes.extend([t for t in world_themes if t in content])

        elif section.section_type.name == "TONE":
            tone_themes = [
                "黑暗",
                "光明",
                "幽默",
                "严肃",
                "浪漫",
                "恐怖",
                "冒险",
                "悲剧",
                "史诗",
            ]
            themes.extend([t for t in tone_themes if t in content])

        # 从所有章节提取通用主题
        generic_themes = ["奇幻", "黑暗", "史诗", "魔法", "龙", "人类", "精灵", "矮人"]
        for theme in generic_themes:
            if theme in content and theme not in themes:
                themes.append(theme)

        return themes

    def _extract_guidelines(self, section: CanonSection) -> List[str]:
        """提取叙事指南"""
        guidelines = []

        # 查找指导性语句
        guidance_indicators = ["应该", "建议", "推荐", "最好", "避免", "注意"]

        lines = section.content.split("\n")
        for line in lines:
            if any(indicator in line for indicator in guidance_indicators):
                guidelines.append(line.strip())

        return guidelines

    def _generate_summary(
        self, constraints: List[RuleConstraint], themes: List[str]
    ) -> str:
        """生成摘要"""
        if not constraints:
            return "规则集未提供具体约束"

        # 按类型分组
        by_type = {}
        for constraint in constraints:
            by_type.setdefault(constraint.type, []).append(constraint)

        summary_parts = []

        # 添加主题
        if themes:
            summary_parts.append(f"关键主题：{', '.join(themes[:5])}")

        # 添加各类型约束统计
        for const_type, const_list in by_type.items():
            summary_parts.append(f"{const_type}约束：{len(const_list)}条")

        # 添加高优先级约束
        high_priority = [c for c in constraints if c.priority >= 4]
        if high_priority:
            summary_parts.append(f"高优先级约束：{len(high_priority)}条")

        return "；".join(summary_parts)

    def format_for_prompt(
        self, result: InterpretationResult, max_constraints: int = 20
    ) -> str:
        """格式化解释结果以供Prompt使用"""
        sections = []

        # 添加摘要
        sections.append(f"## 规则摘要\n{result.summary}")

        # 添加关键主题
        if result.key_themes:
            themes_str = ", ".join(result.key_themes[:10])
            sections.append(f"## 关键主题\n{themes_str}")

        # 添加约束
        if result.constraints:
            # 按优先级排序
            sorted_constraints = sorted(
                result.constraints, key=lambda c: c.priority, reverse=True
            )
            constraints_text = []

            for i, constraint in enumerate(sorted_constraints[:max_constraints]):
                priority_stars = "★" * constraint.priority
                constraints_text.append(
                    f"{i+1}. [{constraint.type}] {constraint.content} {priority_stars}"
                )

            sections.append(f"## 关键约束\n" + "\n".join(constraints_text))

        # 添加叙事指南
        if result.narrative_guidelines:
            guidelines_text = "\n".join(
                [f"- {g}" for g in result.narrative_guidelines[:10]]
            )
            sections.append(f"## 叙事指南\n{guidelines_text}")

        return "\n\n".join(sections)

    def detect_conflicts(
        self, constraints: List[RuleConstraint]
    ) -> List[Dict[str, Any]]:
        """检测约束冲突"""
        conflicts = []

        # 检查权限冲突（允许 vs 禁止）
        permission_constraints = [c for c in constraints if c.type == "permission"]
        allowed = [
            c
            for c in permission_constraints
            if not c.metadata.get("is_prohibition", False)
        ]
        prohibited = [
            c for c in permission_constraints if c.metadata.get("is_prohibition", False)
        ]

        # 简单冲突检测：检查是否有相互矛盾的描述
        for allow in allowed:
            for prohibit in prohibited:
                # 提取关键名词/动词进行冲突检测
                allow_content = allow.content
                prohibit_content = prohibit.content

                # 检查是否有明显的语义冲突
                # 例如："可以时间旅行" vs "禁止时间旅行"
                # 简单的字符串匹配：如果允许的内容包含禁止内容的关键部分
                conflict_detected = False

                # 方法1：检查是否有共同的关键词（排除"可以"、"不能"等）
                keywords_to_check = [
                    "时间旅行",
                    "旅行",
                    "改变历史",
                    "历史",
                    "探索",
                    "杀死",
                    "偷窃",
                    "杀人",
                    "时间",
                    "倒流",
                    "停止",
                    "跳跃",
                ]
                for keyword in keywords_to_check:
                    if keyword in allow_content and keyword in prohibit_content:
                        conflict_detected = True
                        break

                # 方法2：检查语义相似性（简化版）
                if not conflict_detected:
                    # 移除允许/禁止关键词后比较
                    allow_stripped = (
                        allow_content.replace("可以", "")
                        .replace("允许", "")
                        .replace("能够", "")
                        .strip()
                    )
                    prohibit_stripped = (
                        prohibit_content.replace("不能", "")
                        .replace("禁止", "")
                        .replace("不允许", "")
                        .replace("不可以", "")
                        .strip()
                    )

                    # 如果去除关键词后内容相似，则可能冲突
                    if (
                        allow_stripped
                        and prohibit_stripped
                        and (
                            allow_stripped in prohibit_stripped
                            or prohibit_stripped in allow_stripped
                        )
                    ):
                        conflict_detected = True

                if conflict_detected:
                    conflicts.append(
                        {
                            "type": "permission_conflict",
                            "constraint1": allow.content,
                            "constraint2": prohibit.content,
                            "severity": "medium",
                        }
                    )

        # 检查因果关系冲突
        causality_constraints = [c for c in constraints if c.type == "causality"]
        time_flow_constraints = [
            c for c in causality_constraints if c.metadata.get("subtype") == "time_flow"
        ]

        # 检查时间流向冲突（如同时允许和禁止时间倒流）
        time_keywords = [
            "时间倒流",
            "时间停止",
            "时间跳跃",
            "时间旅行",
            "时间向前",
            "时间向后",
        ]
        for keyword in time_keywords:
            related = [c for c in time_flow_constraints if keyword in c.content]
            if len(related) > 1:
                # 检查是否有矛盾描述
                contents = [c.content for c in related]
                if any("可以" in c for c in contents) and any(
                    "不能" in c for c in contents
                ):
                    conflicts.append(
                        {
                            "type": "causality_conflict",
                            "keyword": keyword,
                            "constraints": contents,
                            "severity": "high",
                        }
                    )

        return conflicts

    def resolve_conflicts(
        self, constraints: List[RuleConstraint], conflicts: List[Dict[str, Any]]
    ) -> List[RuleConstraint]:
        """解决约束冲突"""
        if not conflicts:
            return constraints

        resolved = constraints.copy()

        for conflict in conflicts:
            if conflict["type"] == "permission_conflict":
                # 权限冲突：优先考虑禁止性规则（更严格）
                constraint1 = conflict["constraint1"]
                constraint2 = conflict["constraint2"]

                # 找出哪个是禁止性规则
                for constraint in resolved:
                    if constraint.content == constraint1 and constraint.metadata.get(
                        "is_prohibition", False
                    ):
                        # constraint1是禁止性规则，保留它
                        # 可能需要调整另一个规则的优先级
                        pass
                    elif constraint.content == constraint2 and constraint.metadata.get(
                        "is_prohibition", False
                    ):
                        # constraint2是禁止性规则，保留它
                        pass

            elif conflict["type"] == "causality_conflict":
                # 因果关系冲突：提高优先级或添加说明
                for constraint in resolved:
                    if any(c in constraint.content for c in conflict["constraints"]):
                        # 提高这些约束的优先级
                        constraint.priority = min(5, constraint.priority + 1)

        return resolved

    def get_contextual_rules(
        self, context: Dict[str, Any], result: InterpretationResult
    ) -> List[RuleConstraint]:
        """获取上下文相关的规则"""
        contextual = []

        # 根据上下文类型过滤规则
        context_type = context.get("type", "general")
        scene = context.get("scene", "")
        characters = context.get("characters", [])

        for constraint in result.constraints:
            # 检查约束是否与上下文相关
            content_lower = constraint.content.lower()

            # 场景相关
            if scene and scene.lower() in content_lower:
                contextual.append(constraint)
                continue

            # 角色相关
            if characters:
                for character in characters:
                    if character.lower() in content_lower:
                        contextual.append(constraint)
                        break

            # 根据上下文类型选择相关约束
            if context_type == "combat" and constraint.type in [
                "permissions",
                "conflict",
            ]:
                contextual.append(constraint)
            elif context_type == "dialogue" and constraint.type in [
                "tone",
                "permissions",
            ]:
                contextual.append(constraint)
            elif context_type == "world_building" and constraint.type in [
                "world",
                "causality",
            ]:
                contextual.append(constraint)

        # 如果没有找到上下文相关的规则，返回高优先级规则
        if not contextual:
            contextual = [c for c in result.constraints if c.priority >= 4][:5]

        return contextual

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("Interpretation cache cleared")
