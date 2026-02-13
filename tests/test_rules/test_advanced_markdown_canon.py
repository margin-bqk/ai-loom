"""
AdvancedMarkdownCanon 单元测试

测试高级Markdown解析器的功能，包括：
1. 嵌套章节解析
2. 交叉引用提取
3. 动态包含支持
4. 条件规则标记
5. 依赖关系分析
6. 验证功能
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from loom.rules.advanced_markdown_canon import (
    AdvancedMarkdownCanon,
    Reference,
    Dependency,
    ValidationError,
    ReferenceType,
)
from loom.rules.markdown_canon import CanonSectionType


class TestAdvancedMarkdownCanon:
    """AdvancedMarkdownCanon 测试类"""

    @pytest.fixture
    def sample_markdown_content(self):
        """示例Markdown内容"""
        return """---
version: 1.0.0
author: Test Author
requires: ["base_rules"]
---

# 世界观 (World)

这是一个测试世界观。

包含对[@角色设定]的引用。

{{include:common_rules.md}}

# 角色设定 (Characters)

主要角色包括：
- 英雄
- 反派

{{macro:power_level}}
力量等级分为1-10级
{{endmacro}}

使用宏：{{use:power_level}}

# 冲突解决 (Conflict)

不能同时攻击和防御。
必须遵守物理法则。

{{if:magic_enabled}}
如果魔法启用，可以使用魔法攻击。
{{endif}}
"""

    @pytest.fixture
    def temp_file(self, sample_markdown_content):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(sample_markdown_content)
            temp_path = Path(f.name)

        yield temp_path

        # 清理
        if temp_path.exists():
            temp_path.unlink()

    def test_initialization(self, temp_file, sample_markdown_content):
        """测试初始化"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        assert canon.path == temp_file
        assert canon.raw_content == sample_markdown_content
        assert len(canon.sections) > 0
        assert "version" in canon.metadata
        assert canon.metadata["version"] == "1.0.0"

    def test_reference_extraction(self, temp_file, sample_markdown_content):
        """测试引用提取"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        # 检查交叉引用
        assert "世界观 (World)" in canon.references
        world_refs = canon.references["世界观 (World)"]
        assert len(world_refs) >= 2  # 应该包含交叉引用和包含

        # 检查引用类型
        ref_types = {ref.reference_type for ref in world_refs}
        assert ReferenceType.CROSS_REFERENCE in ref_types
        assert ReferenceType.INCLUDE in ref_types

    def test_macro_extraction(self, temp_file, sample_markdown_content):
        """测试宏提取"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        assert "power_level" in canon.macros
        assert "力量等级分为1-10级" in canon.macros["power_level"]

    def test_dependency_analysis(self, temp_file, sample_markdown_content):
        """测试依赖分析"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        assert len(canon.dependencies) > 0

        # 检查元数据依赖
        metadata_deps = [
            d for d in canon.dependencies if d.dependency_type == "metadata"
        ]
        assert len(metadata_deps) > 0

        # 检查引用依赖
        reference_deps = [
            d for d in canon.dependencies if d.dependency_type == "reference"
        ]
        assert len(reference_deps) > 0

    def test_validation(self, temp_file, sample_markdown_content):
        """测试验证功能"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        report = canon.get_validation_report()

        assert "canon_path" in report
        assert "total_issues" in report
        assert "is_valid" in report
        assert isinstance(report["is_valid"], bool)

    def test_get_referenced_sections(self, temp_file, sample_markdown_content):
        """测试获取引用的章节"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        referenced = canon.get_referenced_sections("世界观 (World)")
        assert "角色设定 (Characters)" in referenced

    def test_get_dependent_sections(self, temp_file, sample_markdown_content):
        """测试获取依赖的章节"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        # 角色设定应该被世界观依赖
        dependents = canon.get_dependent_sections("角色设定 (Characters)")
        assert "世界观 (World)" in dependents

    def test_get_include_paths(self, temp_file, sample_markdown_content):
        """测试获取包含路径"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        include_paths = canon.get_include_paths()
        assert "common_rules.md" in include_paths

    def test_to_enhanced_dict(self, temp_file, sample_markdown_content):
        """测试转换为增强字典"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        enhanced_dict = canon.to_enhanced_dict()

        assert "advanced_features" in enhanced_dict
        assert "references" in enhanced_dict
        assert "dependencies" in enhanced_dict
        assert "macros" in enhanced_dict
        assert "validation_report" in enhanced_dict

        features = enhanced_dict["advanced_features"]
        assert "has_references" in features
        assert "has_dependencies" in features
        assert "has_macros" in features

    def test_get_section_with_context(self, temp_file, sample_markdown_content):
        """测试获取章节上下文"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        section_info = canon.get_section_with_context(
            "世界观 (World)", include_references=True
        )

        assert "name" in section_info
        assert "content" in section_info
        assert "type" in section_info
        assert "references" in section_info

        references = section_info["references"]
        assert "outgoing" in references
        assert "incoming" in references

    def test_search_with_context(self, temp_file, sample_markdown_content):
        """测试增强搜索"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        results = canon.search_with_context("角色")

        assert len(results) > 0
        for result in results:
            assert "section" in result
            assert "context" in result
            assert "section_info" in result
            assert "relevance_score" in result

    def test_extract_rule_patterns(self, temp_file, sample_markdown_content):
        """测试规则模式提取"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        patterns = canon.extract_rule_patterns()

        assert "constraints" in patterns
        assert "permissions" in patterns
        assert isinstance(patterns["constraints"], list)
        assert isinstance(patterns["permissions"], list)

    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        # 创建有循环引用的内容
        circular_content = """# 章节A
引用[@章节B]

# 章节B
引用[@章节C]

# 章节C
引用[@章节A]
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(circular_content)
            temp_path = Path(f.name)

        try:
            canon = AdvancedMarkdownCanon(temp_path, circular_content)
            report = canon.get_validation_report()

            # 应该检测到循环依赖
            issues = report.get("issues", [])
            circular_issues = [
                i for i in issues if "circular" in i.get("message", "").lower()
            ]
            assert len(circular_issues) > 0

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_resolve_include(self, temp_file):
        """测试解析包含文件"""
        canon = AdvancedMarkdownCanon(temp_file, "")

        # 创建包含文件
        include_content = "这是包含的内容"
        include_path = temp_file.parent / "included.md"

        try:
            with open(include_path, "w", encoding="utf-8") as f:
                f.write(include_content)

            resolved = canon.resolve_include("included.md", temp_file.parent)
            assert resolved == include_content

            # 测试缓存
            cached = canon.resolve_include("included.md", temp_file.parent)
            assert cached == include_content

        finally:
            if include_path.exists():
                include_path.unlink()

    def test_merge_with(self, temp_file, sample_markdown_content):
        """测试合并规则集"""
        canon1 = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        # 创建第二个规则集
        additional_content = """# 新增章节
这是新增的内容。
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(additional_content)
            temp_path2 = Path(f.name)

        try:
            canon2 = AdvancedMarkdownCanon(temp_path2, additional_content)
            merged = canon1.merge_with(canon2)

            assert merged is not None
            assert isinstance(merged, AdvancedMarkdownCanon)

            # 检查合并后的内容
            merged_sections = list(merged.sections.keys())
            assert "新增章节" in merged_sections

        finally:
            if temp_path2.exists():
                temp_path2.unlink()

    def test_backward_compatibility(self, temp_file, sample_markdown_content):
        """测试向后兼容性"""
        canon = AdvancedMarkdownCanon(temp_file, sample_markdown_content)

        # 应该继承父类的所有方法
        assert hasattr(canon, "get_section")
        assert hasattr(canon, "validate")
        assert hasattr(canon, "search_content")
        assert hasattr(canon, "to_dict")

        # 父类方法应该正常工作
        section = canon.get_section("世界观 (World)")
        assert section is not None

        errors = canon.validate()
        assert isinstance(errors, list)

        search_results = canon.search_content("角色")
        assert isinstance(search_results, list)

        dict_repr = canon.to_dict()
        assert isinstance(dict_repr, dict)
        assert "path" in dict_repr
        assert "sections" in dict_repr
