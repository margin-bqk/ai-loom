"""
MarkdownCanon单元测试
"""

import pytest
from pathlib import Path
from src.loom.rules.markdown_canon import MarkdownCanon, CanonSection, CanonSectionType


class TestMarkdownCanon:
    """MarkdownCanon测试类"""

    def test_parse_basic_markdown(self):
        """测试基本Markdown解析"""
        content = """# 世界观
这是一个奇幻世界。

# 叙事基调
黑暗奇幻风格。

# 冲突解决
现实主义。
"""

        canon = MarkdownCanon(path=Path("test.md"), raw_content=content)

        assert len(canon.sections) == 3
        assert "世界观" in canon.sections
        assert "叙事基调" in canon.sections
        assert "冲突解决" in canon.sections

        world_section = canon.sections["世界观"]
        assert world_section.section_type == CanonSectionType.WORLD
        assert "奇幻世界" in world_section.content

    def test_parse_with_frontmatter(self):
        """测试带YAML frontmatter的解析"""
        content = """---
version: 1.0.0
author: Test Author
created: 2025-01-01
---

# 世界观
测试世界。
"""

        canon = MarkdownCanon(path=Path("test_frontmatter.md"), raw_content=content)

        assert canon.metadata["version"] == "1.0.0"
        assert canon.metadata["author"] == "Test Author"
        assert len(canon.sections) == 1
        assert "世界观" in canon.sections

    def test_section_type_inference(self):
        """测试章节类型推断"""
        test_cases = [
            ("世界观", CanonSectionType.WORLD),
            ("世界设定", CanonSectionType.WORLD),
            ("叙事基调", CanonSectionType.TONE),
            ("风格", CanonSectionType.TONE),
            ("冲突解决", CanonSectionType.CONFLICT),
            ("权限边界", CanonSectionType.PERMISSIONS),
            ("因果关系", CanonSectionType.CAUSALITY),
            ("元信息", CanonSectionType.META),
            ("自定义章节", CanonSectionType.CUSTOM),
        ]

        for section_name, expected_type in test_cases:
            content = f"# {section_name}\n测试内容。"
            canon = MarkdownCanon(path=Path("test_inference.md"), raw_content=content)

            section = canon.sections[section_name]
            assert section.section_type == expected_type

    def test_search_content(self):
        """测试内容搜索"""
        content = """# 世界观
这是一个有魔法和龙的世界。
魔法分为元素魔法和神圣魔法。

# 角色
主角是一名魔法师。
"""

        canon = MarkdownCanon(path=Path("test_search.md"), raw_content=content)

        # 搜索"魔法"
        results = canon.search_content("魔法")
        assert len(results) >= 2  # 应该找到至少2处

        # 按类型搜索
        world_results = canon.search_content("魔法", CanonSectionType.WORLD)
        assert len(world_results) >= 1

    def test_extract_entities(self):
        """测试实体提取"""
        content = """# 世界观
主要角色：艾伦、莉莉丝。
重要地点：魔法学院、黑暗森林。
关键物品：魔法杖、龙之心。
"""

        canon = MarkdownCanon(path=Path("test_entities.md"), raw_content=content)

        entities = canon.extract_entities()

        # 检查是否提取到角色
        assert len(entities["characters"]) >= 2
        assert any("艾伦" in char for char in entities["characters"])
        assert any("莉莉丝" in char for char in entities["characters"])

        # 检查是否提取到地点
        assert len(entities["locations"]) >= 1

    def test_combine_fragments(self):
        """测试规则片段组合"""
        content = """# 世界观
奇幻世界。

# 叙事基调
黑暗风格。

# 冲突解决
现实主义。
"""

        canon = MarkdownCanon(path=Path("test_combine.md"), raw_content=content)

        # 组合特定章节
        combined = canon.combine_fragments(["世界观", "叙事基调"])

        assert "# 世界观" in combined
        assert "奇幻世界" in combined
        assert "# 叙事基调" in combined
        assert "黑暗风格" in combined
        assert "# 冲突解决" not in combined

    def test_validation(self):
        """测试规则验证"""
        # 缺少必需章节
        content = """# 自定义章节
测试内容。
"""

        canon = MarkdownCanon(path=Path("test_validation.md"), raw_content=content)

        errors = canon.validate()
        assert len(errors) >= 1  # 应该缺少必需章节

        # 完整规则
        complete_content = """# 世界观
测试世界。

# 叙事基调
测试基调。

# 元信息
version: 1.0.0
"""

        complete_canon = MarkdownCanon(
            path=Path("test_complete.md"), raw_content=complete_content
        )

        complete_errors = complete_canon.validate()
        assert len(complete_errors) == 0  # 应该通过验证

    def test_to_dict(self):
        """测试转换为字典"""
        content = """# 世界观
测试内容。
"""

        canon = MarkdownCanon(path=Path("test_dict.md"), raw_content=content)

        data = canon.to_dict()

        assert "path" in data
        assert "metadata" in data
        assert "sections" in data
        assert "entities" in data
        assert "世界观" in data["sections"]

        # 检查序列化
        import json

        json_str = json.dumps(data, ensure_ascii=False)
        assert "测试内容" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
