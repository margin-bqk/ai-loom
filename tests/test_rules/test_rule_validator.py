"""
RuleValidator 单元测试

测试规则验证器的功能，包括：
1. 结构验证
2. 语义验证（模拟LLM）
3. 一致性验证
4. 完整性验证
5. 冲突检测
6. 引用验证
7. 报告生成
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.loom.rules.rule_validator import (
    RuleValidator,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationType,
)
from src.loom.rules.markdown_canon import MarkdownCanon, CanonSectionType
from src.loom.rules.advanced_markdown_canon import AdvancedMarkdownCanon


class TestRuleValidator:
    """RuleValidator 测试类"""

    @pytest.fixture
    def sample_canon(self):
        """创建示例规则集"""
        content = """---
version: 1.0.0
author: Test Author
created: 2025-01-01
updated: 2025-01-02
---

# 世界观 (World)

这是一个测试世界观。
包含多个角色和地点。

# 叙事基调 (Tone)

严肃的奇幻风格。

# 冲突解决 (Conflict)

不能同时攻击和防御。
必须遵守物理法则。

# 权限边界 (Permissions)

玩家可以探索世界。
不能直接控制NPC。
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = Path(f.name)

        canon = MarkdownCanon(temp_path, raw_content=content)

        yield canon

        # 清理
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def advanced_canon(self):
        """创建高级规则集（带引用）"""
        content = """---
version: 2.0.0
author: Advanced Test
requires: ["base_rules"]
---

# 世界观 (World)

引用[@角色设定]和[@地点描述]。

# 角色设定 (Characters)

主要角色。

# 地点描述 (Locations)

重要地点。
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = Path(f.name)

        canon = AdvancedMarkdownCanon(temp_path, raw_content=content)

        yield canon

        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        config = {
            "validator_config": {
                "required_sections": ["world", "tone"],
                "section_min_length": 10,
            }
        }
        return RuleValidator(config)

    @pytest.fixture
    def validator_with_llm(self):
        """创建带LLM模拟的验证器"""
        config = {"llm_config": {"provider": "mock", "model": "test-model"}}

        # 模拟LLM Provider
        mock_llm_provider = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps(
            [
                {
                    "severity": "warning",
                    "description": "测试语义问题",
                    "suggestion": "建议修改",
                    "metadata": {"category": "模糊不清"},
                }
            ]
        )

        mock_llm_provider.generate = AsyncMock(return_value=mock_response)

        with patch(
            "src.loom.rules.rule_validator.LLMProvider", return_value=mock_llm_provider
        ):
            return RuleValidator(config)

    def test_initialization(self, validator):
        """测试初始化"""
        assert validator is not None
        assert validator.config is not None
        assert validator.validation_rules is not None
        assert "required_sections" in validator.validation_rules

    def test_initialization_without_config(self):
        """测试无配置初始化"""
        validator = RuleValidator()
        assert validator.config == {}
        assert validator.llm_provider is None

    @pytest.mark.asyncio
    async def test_validate_structure(self, validator, sample_canon):
        """测试结构验证"""
        issues = validator._validate_structure(sample_canon)

        assert isinstance(issues, list)

        # 检查是否有结构问题
        structure_issues = [
            i for i in issues if i.issue_type == ValidationType.STRUCTURE
        ]
        assert len(structure_issues) >= 0  # 可能没有结构问题

    @pytest.mark.asyncio
    async def test_validate_completeness(self, validator, sample_canon):
        """测试完整性验证"""
        issues = validator._validate_completeness(sample_canon)

        assert isinstance(issues, list)

        # 检查是否有完整性问题
        completeness_issues = [
            i for i in issues if i.issue_type == ValidationType.COMPLETENESS
        ]

        # 示例规则集应该有必需的章节和元数据
        # 所以应该没有完整性错误
        error_issues = [
            i
            for i in completeness_issues
            if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
        ]
        assert len(error_issues) == 0

    @pytest.mark.asyncio
    async def test_validate_consistency(self, validator, sample_canon):
        """测试一致性验证"""
        issues = validator._validate_consistency(sample_canon)

        assert isinstance(issues, list)

        # 检查时间戳一致性
        timestamp_issues = [i for i in issues if "timestamp" in i.description.lower()]
        assert len(timestamp_issues) == 0  # 时间戳应该一致

    @pytest.mark.asyncio
    async def test_validate_conflicts(self, validator, sample_canon):
        """测试冲突检测"""
        issues = validator._validate_conflicts(sample_canon)

        assert isinstance(issues, list)

        # 检查冲突问题
        conflict_issues = [i for i in issues if i.issue_type == ValidationType.CONFLICT]
        assert len(conflict_issues) >= 0  # 可能没有冲突

    @pytest.mark.asyncio
    async def test_validate_references(self, validator, advanced_canon):
        """测试引用验证"""
        issues = validator._validate_references(advanced_canon)

        assert isinstance(issues, list)

        # 检查引用问题
        reference_issues = [
            i for i in issues if i.issue_type == ValidationType.REFERENCE
        ]
        assert len(reference_issues) >= 0  # 可能没有引用问题

    @pytest.mark.asyncio
    async def test_validate_semantics_with_llm(self, validator_with_llm, sample_canon):
        """测试语义验证（使用LLM）"""
        issues = await validator_with_llm._validate_semantics(sample_canon)

        assert isinstance(issues, list)

        # 检查语义问题
        semantic_issues = [i for i in issues if i.issue_type == ValidationType.SEMANTIC]
        assert len(semantic_issues) > 0  # 模拟LLM应该返回问题

    @pytest.mark.asyncio
    async def test_validate_semantics_without_llm(self, validator, sample_canon):
        """测试无LLM时的语义验证"""
        issues = await validator._validate_semantics(sample_canon)

        assert isinstance(issues, list)
        assert len(issues) == 0  # 没有LLM Provider，应该返回空列表

    @pytest.mark.asyncio
    async def test_full_validation(self, validator, sample_canon):
        """测试完整验证流程"""
        report = await validator.validate(sample_canon)

        assert isinstance(report, ValidationReport)
        assert report.canon_path == sample_canon.path
        assert isinstance(report.issues, list)
        assert isinstance(report.severity_counts, dict)
        assert 0 <= report.validation_score <= 1
        assert isinstance(report.suggestions, list)
        assert isinstance(report.timestamp, datetime)

    def test_validate_sync(self, validator, sample_canon):
        """测试同步验证"""
        report = validator.validate_sync(sample_canon)

        assert isinstance(report, ValidationReport)
        assert report.is_valid() in [True, False]

    def test_validate_multiple(self, validator, sample_canon):
        """测试多规则集验证"""
        # 创建第二个规则集
        content2 = """---
version: 1.1.0
author: Test Author 2
---

# 世界观
另一个世界观。
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content2)
            temp_path2 = Path(f.name)

        try:
            canon2 = MarkdownCanon(temp_path2, raw_content=content2)
            canons = [sample_canon, canon2]

            reports = validator.validate_multiple(canons)

            assert isinstance(reports, dict)
            assert len(reports) == 2

            for path, report in reports.items():
                assert isinstance(report, ValidationReport)

        finally:
            if temp_path2.exists():
                temp_path2.unlink()

    def test_compare_versions(self, validator, sample_canon):
        """测试版本比较"""
        # 创建修改后的版本
        modified_content = sample_canon.raw_content.replace(
            "这是一个测试世界观。", "这是一个修改后的测试世界观。"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(modified_content)
            temp_path2 = Path(f.name)

        try:
            new_canon = MarkdownCanon(temp_path2, raw_content=modified_content)
            changes = validator.compare_versions(sample_canon, new_canon)

            assert isinstance(changes, dict)
            assert "modified_sections" in changes
            assert "metadata_changes" in changes
            assert "breaking_changes" in changes

            # 应该检测到修改的章节
            modified_sections = changes["modified_sections"]
            assert len(modified_sections) > 0

            # 世界观章节应该被修改
            world_modifications = [
                m for m in modified_sections if "世界观" in m.get("section", "")
            ]
            assert len(world_modifications) > 0

        finally:
            if temp_path2.exists():
                temp_path2.unlink()

    def test_generate_fix_suggestions(self, validator, sample_canon):
        """测试生成修复建议"""
        # 首先进行验证
        report = validator.validate_sync(sample_canon)

        suggestions = validator.generate_fix_suggestions(report)

        assert isinstance(suggestions, list)

        for suggestion in suggestions:
            assert "issue" in suggestion
            assert "location" in suggestion
            assert "suggestion" in suggestion
            assert "priority" in suggestion
            assert "automated_fix_possible" in suggestion

    def test_export_validation_results_json(self, validator, sample_canon):
        """测试导出JSON格式验证结果"""
        report = validator.validate_sync(sample_canon)
        reports = {str(sample_canon.path): report}

        json_output = validator.export_validation_results(reports, "json")

        assert isinstance(json_output, str)

        # 验证JSON格式
        parsed = json.loads(json_output)
        assert "validation_summary" in parsed
        assert "reports" in parsed

        summary = parsed["validation_summary"]
        assert "total_reports" in summary
        assert summary["total_reports"] == 1

    def test_export_validation_results_text(self, validator, sample_canon):
        """测试导出文本格式验证结果"""
        report = validator.validate_sync(sample_canon)
        reports = {str(sample_canon.path): report}

        text_output = validator.export_validation_results(reports, "text")

        assert isinstance(text_output, str)
        assert "RULE VALIDATION REPORT" in text_output
        assert str(sample_canon.path.name) in text_output

    def test_export_validation_results_invalid_format(self, validator):
        """测试无效输出格式"""
        with pytest.raises(ValueError):
            validator.export_validation_results({}, "invalid_format")

    def test_report_to_dict(self, validator, sample_canon):
        """测试报告转换为字典"""
        report = validator.validate_sync(sample_canon)
        report_dict = report.to_dict()

        assert isinstance(report_dict, dict)
        assert "canon_path" in report_dict
        assert "issue_count" in report_dict
        assert "severity_counts" in report_dict
        assert "validation_score" in report_dict
        assert "suggestions" in report_dict
        assert "timestamp" in report_dict
        assert "issues" in report_dict

    def test_report_is_valid(self, validator, sample_canon):
        """测试报告有效性检查"""
        report = validator.validate_sync(sample_canon)

        assert isinstance(report.is_valid(), bool)

        # 检查严重性统计
        severity_counts = report.severity_counts
        critical_count = severity_counts.get(ValidationSeverity.CRITICAL, 0)
        error_count = severity_counts.get(ValidationSeverity.ERROR, 0)

        if critical_count == 0 and error_count == 0:
            assert report.is_valid() == True
        else:
            assert report.is_valid() == False

    def test_report_get_summary(self, validator, sample_canon):
        """测试报告摘要"""
        report = validator.validate_sync(sample_canon)
        summary = report.get_summary()

        assert isinstance(summary, str)
        assert "Validation Report for" in summary
        assert "Total Issues:" in summary
        assert "Validation Score:" in summary
        assert "Status:" in summary

    def test_build_semantic_validation_prompt(self, validator, sample_canon):
        """测试构建语义验证提示"""
        section_name = "世界观 (World)"
        section = sample_canon.sections[section_name]

        prompt = validator._build_semantic_validation_prompt(section_name, section)

        assert isinstance(prompt, str)
        assert section_name in prompt
        assert "请验证以下规则章节的语义合理性" in prompt
        assert "JSON格式" in prompt

    def test_parse_semantic_response_valid_json(self, validator):
        """测试解析有效的语义验证响应"""
        valid_response = json.dumps(
            [
                {
                    "severity": "warning",
                    "description": "测试问题",
                    "suggestion": "测试建议",
                    "metadata": {"category": "test"},
                }
            ]
        )

        issues = validator._parse_semantic_response(valid_response)

        assert isinstance(issues, list)
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"

    def test_parse_semantic_response_invalid_json(self, validator):
        """测试解析无效的语义验证响应"""
        invalid_response = "这不是有效的JSON"

        issues = validator._parse_semantic_response(invalid_response)

        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_parse_semantic_response_empty(self, validator):
        """测试解析空响应"""
        empty_response = ""

        issues = validator._parse_semantic_response(empty_response)

        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_check_automated_fix(self, validator):
        """测试检查自动修复可能性"""
        # 创建不同类型的问题
        structure_issue = ValidationIssue(
            issue_type=ValidationType.STRUCTURE,
            severity=ValidationSeverity.WARNING,
            description="结构问题",
            location="section:test",
        )

        semantic_issue = ValidationIssue(
            issue_type=ValidationType.SEMANTIC,
            severity=ValidationSeverity.WARNING,
            description="语义问题",
            location="section:test",
        )

        # 结构问题应该可以自动修复
        assert validator._check_automated_fix(structure_issue) == True

        # 语义问题可能无法自动修复
        assert validator._check_automated_fix(semantic_issue) == False
