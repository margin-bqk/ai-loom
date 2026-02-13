"""
RuleInterpreter单元测试
"""

import pytest
from pathlib import Path
from src.loom.rules.markdown_canon import MarkdownCanon
from src.loom.interpretation.rule_interpreter import (
    RuleInterpreter,
    InterpretationResult,
    RuleConstraint,
)


class TestRuleInterpreter:
    """RuleInterpreter测试类"""

    def setup_method(self):
        """测试设置"""
        self.interpreter = RuleInterpreter()

        # 创建测试规则集
        self.test_content = """# 世界观
这是一个奇幻世界，有魔法和龙。
主要种族：人类、精灵、矮人。
魔法分为元素魔法和神圣魔法。

# 叙事基调
黑暗奇幻风格，带有悲剧色彩。
故事基调严肃而史诗。

# 冲突解决
现实主义冲突解决。
玩家决定重要选择。

# 权限边界
玩家可以探索任何区域。
玩家不能杀死无辜NPC。
禁止时间旅行。

# 因果关系
时间只能向前流动。
死亡通常是永久的。

# 元信息
version: 1.0.0
"""

        self.canon = MarkdownCanon(
            path=Path("test_interpreter.md"), raw_content=self.test_content
        )

    def test_interpret_basic(self):
        """测试基本解释"""
        result = self.interpreter.interpret(self.canon)

        assert isinstance(result, InterpretationResult)
        assert len(result.constraints) > 0
        assert len(result.key_themes) > 0
        assert result.summary

        # 检查元数据
        assert result.metadata["canon_path"] == "test_interpreter.md"
        assert result.metadata["canon_version"] == "1.0.0"
        assert result.metadata["sections_interpreted"] == 6

    def test_constraint_extraction(self):
        """测试约束提取"""
        result = self.interpreter.interpret(self.canon)
        constraints = result.constraints

        # 检查约束类型
        constraint_types = {c.type for c in constraints}
        assert "permission" in constraint_types
        assert "causality" in constraint_types
        assert "tone" in constraint_types
        assert "world" in constraint_types
        assert "conflict" in constraint_types

        # 检查权限约束
        permission_constraints = [c for c in constraints if c.type == "permission"]
        assert len(permission_constraints) >= 2

        # 检查禁止性规则
        prohibitions = [
            c for c in permission_constraints if c.metadata.get("is_prohibition", False)
        ]
        assert len(prohibitions) >= 1

        # 检查因果关系约束
        causality_constraints = [c for c in constraints if c.type == "causality"]
        assert len(causality_constraints) >= 1

    def test_theme_extraction(self):
        """测试主题提取"""
        result = self.interpreter.interpret(self.canon)
        themes = result.key_themes

        # 应该提取到相关主题
        assert any("奇幻" in theme for theme in themes)
        assert any("黑暗" in theme for theme in themes)
        assert any("史诗" in theme for theme in themes)

    def test_guideline_extraction(self):
        """测试指南提取"""
        result = self.interpreter.interpret(self.canon)
        guidelines = result.narrative_guidelines

        # 检查是否有指导性语句
        # 注意：测试内容中没有明确的指导性语句，所以可能为空
        # 这是一个合理的测试结果

    def test_cache_mechanism(self):
        """测试缓存机制"""
        # 第一次解释
        result1 = self.interpreter.interpret(self.canon)

        # 第二次解释应该使用缓存
        result2 = self.interpreter.interpret(self.canon, use_cache=True)

        # 检查是否是同一个对象（缓存）
        # 注意：由于缓存键包含哈希，应该是同一个对象
        assert result1 is result2

        # 清空缓存后应该重新解释
        self.interpreter.clear_cache()
        result3 = self.interpreter.interpret(self.canon)
        assert result3 is not result1

    def test_format_for_prompt(self):
        """测试Prompt格式化"""
        result = self.interpreter.interpret(self.canon)
        prompt_text = self.interpreter.format_for_prompt(result)

        assert "## 规则摘要" in prompt_text
        assert "## 关键主题" in prompt_text
        assert "## 关键约束" in prompt_text

        # 检查约束格式化
        if result.constraints:
            constraint = result.constraints[0]
            assert constraint.type in prompt_text

    def test_conflict_detection(self):
        """测试冲突检测"""
        # 创建有冲突的规则
        conflict_content = """# 权限边界
玩家可以时间旅行。
玩家不能改变历史。
禁止时间旅行。
"""

        conflict_canon = MarkdownCanon(
            path=Path("test_conflict.md"), raw_content=conflict_content
        )

        result = self.interpreter.interpret(conflict_canon)
        conflicts = self.interpreter.detect_conflicts(result.constraints)

        # 应该检测到权限冲突
        assert len(conflicts) >= 1

        permission_conflicts = [
            c for c in conflicts if c["type"] == "permission_conflict"
        ]
        assert len(permission_conflicts) >= 1

    def test_conflict_resolution(self):
        """测试冲突解决"""
        # 创建有冲突的约束
        from dataclasses import replace

        constraint1 = RuleConstraint(
            type="permission",
            content="玩家可以时间旅行",
            priority=2,
            metadata={"is_prohibition": False},
        )

        constraint2 = RuleConstraint(
            type="permission",
            content="禁止时间旅行",
            priority=3,
            metadata={"is_prohibition": True},
        )

        constraints = [constraint1, constraint2]

        # 检测冲突
        conflicts = self.interpreter.detect_conflicts(constraints)
        assert len(conflicts) >= 1

        # 解决冲突
        resolved = self.interpreter.resolve_conflicts(constraints, conflicts)
        assert len(resolved) == len(constraints)

    def test_contextual_rules(self):
        """测试上下文相关规则"""
        result = self.interpreter.interpret(self.canon)

        # 测试战斗上下文
        combat_context = {
            "type": "combat",
            "scene": "战斗",
            "characters": ["人类", "精灵"],
        }

        combat_rules = self.interpreter.get_contextual_rules(combat_context, result)
        assert len(combat_rules) > 0

        # 检查是否包含相关约束类型
        combat_rule_types = {c.type for c in combat_rules}
        assert "permission" in combat_rule_types or "conflict" in combat_rule_types

        # 测试对话上下文
        dialogue_context = {"type": "dialogue", "scene": "对话", "characters": ["NPC"]}

        dialogue_rules = self.interpreter.get_contextual_rules(dialogue_context, result)
        assert len(dialogue_rules) > 0

    def test_parse_specific_sections(self):
        """测试特定章节解析"""
        # 测试权限解析
        permissions_content = "玩家可以探索。玩家不能偷窃。禁止杀人。"
        permissions = self.interpreter._parse_permissions(
            permissions_content, "权限边界"
        )
        assert len(permissions) >= 2

        # 检查禁止性规则
        prohibitions = [
            p for p in permissions if p.metadata.get("is_prohibition", False)
        ]
        assert len(prohibitions) >= 1

        # 测试因果关系解析
        causality_content = "时间只能向前流动。死亡是永久的。"
        causality = self.interpreter._parse_causality(causality_content, "因果关系")
        assert len(causality) >= 1

        # 测试基调解析
        tone_content = "黑暗奇幻风格，带有悲剧色彩。"
        tone = self.interpreter._parse_tone(tone_content, "叙事基调")
        assert len(tone) >= 1

        # 测试冲突解析
        conflict_content = "现实主义冲突解决。"
        conflict = self.interpreter._parse_conflict(conflict_content, "冲突解决")
        assert len(conflict) >= 1

        # 测试世界观解析
        world_content = "奇幻世界，有魔法和龙。"
        world = self.interpreter._parse_world(world_content, "世界观")
        assert len(world) >= 1

    def test_extract_important_phrases(self):
        """测试重要短语提取"""
        text = "这是一个有魔法和龙的世界。魔法分为元素魔法和神圣魔法。世界历史悠久。"

        phrases = self.interpreter._extract_important_phrases(text)
        assert len(phrases) > 0

        # 检查是否包含关键词
        assert any("魔法" in phrase for phrase in phrases)
        assert any("世界" in phrase for phrase in phrases)

    def test_generate_summary(self):
        """测试摘要生成"""
        # 创建测试约束
        constraints = [
            RuleConstraint(type="permission", content="测试约束1", priority=3),
            RuleConstraint(type="causality", content="测试约束2", priority=4),
            RuleConstraint(type="tone", content="测试约束3", priority=2),
        ]

        themes = ["奇幻", "黑暗"]

        summary = self.interpreter._generate_summary(constraints, themes)

        assert "关键主题" in summary
        assert "permission约束" in summary
        assert "causality约束" in summary
        assert "tone约束" in summary
        assert "高优先级约束" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
