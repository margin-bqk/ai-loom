"""
规则验证器

提供全面的规则验证功能，包括：
1. 结构验证 - 语法和格式检查
2. 语义验证 - 使用LLM进行语义合理性检查
3. 一致性验证 - 规则内部和跨规则一致性
4. 完整性验证 - 必需章节和字段检查
5. 冲突检测 - 规则间冲突检测
6. 引用验证 - 交叉引用有效性检查

设计目标：提供详细的验证报告和修复建议。
"""

import re
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .markdown_canon import MarkdownCanon, CanonSectionType
from .advanced_markdown_canon import AdvancedMarkdownCanon
from ..interpretation.llm_provider import LLMProvider
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """验证严重性级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationType(Enum):
    """验证类型"""

    STRUCTURE = "structure"
    SEMANTIC = "semantic"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    CONFLICT = "conflict"
    REFERENCE = "reference"


@dataclass
class ValidationIssue:
    """验证问题"""

    issue_type: ValidationType
    severity: ValidationSeverity
    description: str
    location: str  # section:name, line:number, global, etc.
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """验证报告"""

    canon_path: Path
    issues: List[ValidationIssue]
    severity_counts: Dict[str, int]
    validation_score: float  # 0-1
    suggestions: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "canon_path": str(self.canon_path),
            "issue_count": len(self.issues),
            "severity_counts": {k.value: v for k, v in self.severity_counts.items()},
            "validation_score": self.validation_score,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat(),
            "issues": [
                {
                    "type": issue.issue_type.value,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                    "metadata": issue.metadata,
                }
                for issue in self.issues
            ],
        }

    def is_valid(self) -> bool:
        """检查是否有效（无错误或严重错误）"""
        critical_count = self.severity_counts.get(ValidationSeverity.CRITICAL, 0)
        error_count = self.severity_counts.get(ValidationSeverity.ERROR, 0)
        return critical_count == 0 and error_count == 0

    def get_summary(self) -> str:
        """获取验证摘要"""
        total = len(self.issues)
        critical = self.severity_counts.get(ValidationSeverity.CRITICAL, 0)
        errors = self.severity_counts.get(ValidationSeverity.ERROR, 0)
        warnings = self.severity_counts.get(ValidationSeverity.WARNING, 0)
        infos = self.severity_counts.get(ValidationSeverity.INFO, 0)

        return (
            f"Validation Report for {self.canon_path.name}\n"
            f"  Total Issues: {total}\n"
            f"  Critical: {critical}, Errors: {errors}, Warnings: {warnings}, Info: {infos}\n"
            f"  Validation Score: {self.validation_score:.2%}\n"
            f"  Status: {'VALID' if self.is_valid() else 'INVALID'}"
        )


class RuleValidator:
    """规则验证器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validation_rules = self._load_validation_rules()
        self.llm_provider = None

        # 初始化LLM Provider（如果配置了）
        llm_config = self.config.get("llm_config")
        if llm_config:
            try:
                self.llm_provider = LLMProvider(llm_config)
                logger.info("LLM Provider initialized for semantic validation")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM Provider: {e}")

    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            "required_sections": ["world", "世界观", "World", "tone", "基调", "Tone"],
            "required_metadata": ["version", "author"],
            "section_min_length": 50,  # 章节最小长度（字符）
            "max_section_depth": 4,  # 最大嵌套深度
            "allowed_reference_types": ["cross_reference", "include"],
            "conflict_patterns": [
                r"不能.*同时.*可以",
                r"禁止.*但.*允许",
                r"必须.*但.*不能",
            ],
        }

    async def validate(self, canon: MarkdownCanon) -> ValidationReport:
        """验证规则集"""
        issues = []

        # 1. 结构验证
        structure_issues = self._validate_structure(canon)
        issues.extend(structure_issues)

        # 2. 语义验证（如果启用了LLM）
        semantic_issues = await self._validate_semantics(canon)
        issues.extend(semantic_issues)

        # 3. 一致性验证
        consistency_issues = self._validate_consistency(canon)
        issues.extend(consistency_issues)

        # 4. 完整性验证
        completeness_issues = self._validate_completeness(canon)
        issues.extend(completeness_issues)

        # 5. 冲突检测
        conflict_issues = self._validate_conflicts(canon)
        issues.extend(conflict_issues)

        # 6. 引用验证（如果是AdvancedMarkdownCanon）
        if isinstance(canon, AdvancedMarkdownCanon):
            reference_issues = self._validate_references(canon)
            issues.extend(reference_issues)

        # 生成报告
        return self._generate_report(canon, issues)

    def _validate_structure(self, canon: MarkdownCanon) -> List[ValidationIssue]:
        """验证结构"""
        issues = []

        # 检查章节非空
        for section_name, section in canon.sections.items():
            if not section.content.strip():
                issue = ValidationIssue(
                    issue_type=ValidationType.STRUCTURE,
                    severity=ValidationSeverity.WARNING,
                    description=f"Section '{section_name}' is empty",
                    location=f"section:{section_name}",
                    suggestion="Add content to this section or remove it",
                )
                issues.append(issue)

            # 检查章节长度
            min_length = self.validation_rules["section_min_length"]
            if len(section.content.strip()) < min_length:
                issue = ValidationIssue(
                    issue_type=ValidationType.STRUCTURE,
                    severity=ValidationSeverity.INFO,
                    description=f"Section '{section_name}' is very short ({len(section.content.strip())} chars)",
                    location=f"section:{section_name}",
                    suggestion=f"Consider expanding this section to at least {min_length} characters",
                )
                issues.append(issue)

        # 检查元数据格式
        if "version" in canon.metadata:
            version = canon.metadata["version"]
            if not re.match(r"^\d+\.\d+\.\d+$", str(version)):
                issue = ValidationIssue(
                    issue_type=ValidationType.STRUCTURE,
                    severity=ValidationSeverity.WARNING,
                    description=f"Version format '{version}' is not semantic (should be X.Y.Z)",
                    location="metadata:version",
                    suggestion="Use semantic versioning format (e.g., 1.0.0)",
                )
                issues.append(issue)

        return issues

    async def _validate_semantics(self, canon: MarkdownCanon) -> List[ValidationIssue]:
        """验证语义（使用LLM）"""
        issues = []

        # 如果没有LLM Provider，跳过语义验证
        if not self.llm_provider:
            logger.debug("LLM Provider not available, skipping semantic validation")
            return issues

        try:
            # 对每个章节进行语义验证
            for section_name, section in canon.sections.items():
                # 跳过太短的章节
                if len(section.content) < 100:
                    continue

                prompt = self._build_semantic_validation_prompt(section_name, section)

                try:
                    # 使用LLM进行验证
                    response = await self.llm_provider.generate(prompt)

                    # 解析响应
                    semantic_issues = self._parse_semantic_response(response.content)

                    for semantic_issue in semantic_issues:
                        issue = ValidationIssue(
                            issue_type=ValidationType.SEMANTIC,
                            severity=ValidationSeverity(
                                semantic_issue.get("severity", "info")
                            ),
                            description=semantic_issue.get("description", ""),
                            location=f"section:{section_name}",
                            suggestion=semantic_issue.get("suggestion"),
                            metadata=semantic_issue.get("metadata", {}),
                        )
                        issues.append(issue)

                except Exception as e:
                    logger.warning(
                        f"Failed to validate semantics for section '{section_name}': {e}"
                    )
                    continue

        except Exception as e:
            logger.error(f"Semantic validation failed: {e}")

        return issues

    def _build_semantic_validation_prompt(self, section_name: str, section) -> str:
        """构建语义验证提示"""
        return f"""
请验证以下规则章节的语义合理性：

章节名称：{section_name}
章节类型：{section.section_type.value}
内容：
{section.content[:2000]}

请检查以下问题：
1. 逻辑矛盾 - 内容中是否存在自相矛盾的陈述？
2. 模糊不清 - 是否有过于模糊或不确定的描述？
3. 不合理约束 - 是否有不现实或不合理的限制？
4. 缺失信息 - 是否缺少必要的上下文或定义？
5. 语法问题 - 是否有明显的语法或表达问题？

请以JSON格式返回发现的问题，格式如下：
[
  {{
    "severity": "info|warning|error|critical",
    "description": "问题描述",
    "suggestion": "修复建议（可选）",
    "metadata": {{"category": "逻辑矛盾|模糊不清|..."}}
  }}
]

如果没有问题，返回空列表 []。
"""

    def _parse_semantic_response(self, response_text: str) -> List[Dict[str, Any]]:
        """解析语义验证响应"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)

            # 如果没有找到JSON，尝试直接解析
            if response_text.strip().startswith("["):
                return json.loads(response_text.strip())

            return []

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse semantic validation response: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error parsing semantic response: {e}")
            return []

    def _validate_consistency(self, canon: MarkdownCanon) -> List[ValidationIssue]:
        """验证一致性"""
        issues = []

        # 检查元数据一致性
        if "created" in canon.metadata and "updated" in canon.metadata:
            try:
                created = datetime.fromisoformat(
                    canon.metadata["created"].replace("Z", "+00:00")
                )
                updated = datetime.fromisoformat(
                    canon.metadata["updated"].replace("Z", "+00:00")
                )

                if updated < created:
                    issue = ValidationIssue(
                        issue_type=ValidationType.CONSISTENCY,
                        severity=ValidationSeverity.WARNING,
                        description="Update timestamp is earlier than creation timestamp",
                        location="metadata",
                        suggestion="Check the created and updated timestamps",
                    )
                    issues.append(issue)

            except (ValueError, TypeError):
                pass

        # 检查章节类型一致性
        type_counts = {}
        for section in canon.sections.values():
            type_counts[section.section_type] = (
                type_counts.get(section.section_type, 0) + 1
            )

        # 如果有多个相同类型的章节，检查它们是否应该合并
        for section_type, count in type_counts.items():
            if count > 1 and section_type != CanonSectionType.CUSTOM:
                issue = ValidationIssue(
                    issue_type=ValidationType.CONSISTENCY,
                    severity=ValidationSeverity.INFO,
                    description=f"Multiple sections of type '{section_type.value}' found ({count} sections)",
                    location="global",
                    suggestion=f"Consider merging {section_type.value} sections or renaming them for clarity",
                )
                issues.append(issue)

        return issues

    def _validate_completeness(self, canon: MarkdownCanon) -> List[ValidationIssue]:
        """验证完整性"""
        issues = []

        # 检查必需章节
        required_sections = self.validation_rules["required_sections"]
        found_required = False

        for req_section in required_sections:
            for section_name in canon.sections.keys():
                if req_section.lower() in section_name.lower():
                    found_required = True
                    break

            if not found_required:
                issue = ValidationIssue(
                    issue_type=ValidationType.COMPLETENESS,
                    severity=ValidationSeverity.WARNING,
                    description=f"Missing recommended section matching '{req_section}'",
                    location="global",
                    suggestion=f"Add a section about '{req_section}' to provide essential context",
                )
                issues.append(issue)

            found_required = False

        # 检查必需元数据
        required_metadata = self.validation_rules["required_metadata"]
        for field in required_metadata:
            if field not in canon.metadata:
                issue = ValidationIssue(
                    issue_type=ValidationType.COMPLETENESS,
                    severity=ValidationSeverity.WARNING,
                    description=f"Missing metadata field: '{field}'",
                    location="metadata",
                    suggestion=f"Add '{field}' field to metadata",
                )
                issues.append(issue)

        return issues

    def _validate_conflicts(self, canon: MarkdownCanon) -> List[ValidationIssue]:
        """验证冲突"""
        issues = []

        # 检查冲突模式
        conflict_patterns = self.validation_rules["conflict_patterns"]

        for section_name, section in canon.sections.items():
            content = section.content

            for pattern in conflict_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    issue = ValidationIssue(
                        issue_type=ValidationType.CONFLICT,
                        severity=ValidationSeverity.WARNING,
                        description=f"Potential conflict detected: '{match}'",
                        location=f"section:{section_name}",
                        suggestion="Review this statement for logical consistency",
                    )
                    issues.append(issue)

        # 检查跨章节冲突
        if len(canon.sections) > 1:
            # 简单实现：检查关键词冲突
            keyword_sections = {}

            for section_name, section in canon.sections.items():
                # 提取关键词（简化实现）
                keywords = re.findall(
                    r"[不能|必须|禁止|允许|可以|应当]+[^。]*", section.content
                )
                for keyword in keywords:
                    keyword_sections.setdefault(keyword, []).append(section_name)

            # 检查相同关键词出现在不同章节
            for keyword, sections in keyword_sections.items():
                if len(sections) > 1:
                    issue = ValidationIssue(
                        issue_type=ValidationType.CONFLICT,
                        severity=ValidationSeverity.INFO,
                        description=f"Same rule pattern '{keyword[:50]}...' appears in multiple sections",
                        location=f"sections:{','.join(sections)}",
                        suggestion="Check if these rules are consistent across sections",
                    )
                    issues.append(issue)

        return issues

    def _validate_references(
        self, canon: AdvancedMarkdownCanon
    ) -> List[ValidationIssue]:
        """验证引用（仅适用于AdvancedMarkdownCanon）"""
        issues = []

        # 获取验证报告
        report = canon.get_validation_report()

        # 检查引用错误
        for issue in report.get("issues", []):
            if issue["severity"] in ["error", "warning"]:
                validation_issue = ValidationIssue(
                    issue_type=ValidationType.REFERENCE,
                    severity=ValidationSeverity(issue["severity"]),
                    description=issue["message"],
                    location=issue["location"],
                    suggestion=issue.get("suggestion"),
                )
                issues.append(validation_issue)

        # 检查循环依赖
        if report.get("has_circular_dependencies", False):
            issue = ValidationIssue(
                issue_type=ValidationType.REFERENCE,
                severity=ValidationSeverity.ERROR,
                description="Circular dependencies detected in rule references",
                location="global",
                suggestion="Review and fix circular references between sections",
            )
            issues.append(issue)

        return issues

    def _generate_report(
        self, canon: MarkdownCanon, issues: List[ValidationIssue]
    ) -> ValidationReport:
        """生成验证报告"""
        # 统计严重性
        severity_counts = {
            ValidationSeverity.CRITICAL: 0,
            ValidationSeverity.ERROR: 0,
            ValidationSeverity.WARNING: 0,
            ValidationSeverity.INFO: 0,
        }

        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

        # 计算验证分数
        total_issues = len(issues)
        critical_weight = 1.0
        error_weight = 0.7
        warning_weight = 0.3
        info_weight = 0.1

        weighted_score = (
            severity_counts[ValidationSeverity.CRITICAL] * critical_weight
            + severity_counts[ValidationSeverity.ERROR] * error_weight
            + severity_counts[ValidationSeverity.WARNING] * warning_weight
            + severity_counts[ValidationSeverity.INFO] * info_weight
        )

        # 归一化到0-1范围，问题越多分数越低
        max_weighted_issues = 10  # 假设最多10个加权问题
        normalized_score = max(0, 1 - (weighted_score / max_weighted_issues))

        # 提取建议
        suggestions = []
        for issue in issues:
            if issue.suggestion and issue.severity in [
                ValidationSeverity.ERROR,
                ValidationSeverity.CRITICAL,
            ]:
                suggestions.append(issue.suggestion)

        # 去重
        suggestions = list(set(suggestions))

        return ValidationReport(
            canon_path=canon.path,
            issues=issues,
            severity_counts=severity_counts,
            validation_score=normalized_score,
            suggestions=suggestions,
        )

    def validate_sync(self, canon: MarkdownCanon) -> ValidationReport:
        """同步验证规则集"""
        # 创建事件循环或使用现有循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.validate(canon))

    def validate_multiple(
        self, canons: List[MarkdownCanon]
    ) -> Dict[str, ValidationReport]:
        """验证多个规则集"""
        reports = {}

        for canon in canons:
            try:
                report = self.validate_sync(canon)
                reports[str(canon.path)] = report
            except Exception as e:
                logger.error(f"Failed to validate {canon.path}: {e}")

        return reports

    def compare_versions(
        self, old_canon: MarkdownCanon, new_canon: MarkdownCanon
    ) -> Dict[str, Any]:
        """比较两个版本的规则集"""
        changes = {
            "added_sections": [],
            "removed_sections": [],
            "modified_sections": [],
            "metadata_changes": [],
            "breaking_changes": [],
        }

        # 比较章节
        old_sections = set(old_canon.sections.keys())
        new_sections = set(new_canon.sections.keys())

        changes["added_sections"] = list(new_sections - old_sections)
        changes["removed_sections"] = list(old_sections - new_sections)

        # 检查修改的章节
        common_sections = old_sections & new_sections
        for section in common_sections:
            old_content = old_canon.sections[section].content
            new_content = new_canon.sections[section].content

            if old_content != new_content:
                changes["modified_sections"].append(
                    {
                        "section": section,
                        "change_type": "modified",
                        "old_length": len(old_content),
                        "new_length": len(new_content),
                    }
                )

        # 比较元数据
        for key in set(old_canon.metadata.keys()) | set(new_canon.metadata.keys()):
            old_value = old_canon.metadata.get(key)
            new_value = new_canon.metadata.get(key)

            if old_value != new_value:
                changes["metadata_changes"].append(
                    {"key": key, "old_value": old_value, "new_value": new_value}
                )

                # 检查是否是破坏性变更
                if key in ["version", "requires"]:
                    changes["breaking_changes"].append(f"Metadata '{key}' changed")

        # 检查必需章节的移除
        required_sections = self.validation_rules["required_sections"]
        for removed in changes["removed_sections"]:
            for req in required_sections:
                if req.lower() in removed.lower():
                    changes["breaking_changes"].append(
                        f"Required section '{removed}' was removed"
                    )

        return changes

    def generate_fix_suggestions(
        self, report: ValidationReport
    ) -> List[Dict[str, Any]]:
        """生成修复建议"""
        suggestions = []

        for issue in report.issues:
            if issue.severity in [
                ValidationSeverity.ERROR,
                ValidationSeverity.CRITICAL,
            ]:
                suggestion = {
                    "issue": issue.description,
                    "location": issue.location,
                    "suggestion": issue.suggestion
                    or "No specific suggestion available",
                    "priority": (
                        "high"
                        if issue.severity == ValidationSeverity.CRITICAL
                        else "medium"
                    ),
                    "automated_fix_possible": self._check_automated_fix(issue),
                }
                suggestions.append(suggestion)

        return suggestions

    def _check_automated_fix(self, issue: ValidationIssue) -> bool:
        """检查是否可以自动修复"""
        # 简单实现：检查问题类型
        automatable_types = [ValidationType.STRUCTURE, ValidationType.REFERENCE]

        return issue.issue_type in automatable_types

    def export_validation_results(
        self, reports: Dict[str, ValidationReport], output_format: str = "json"
    ) -> str:
        """导出验证结果"""
        if output_format == "json":
            result = {
                "validation_summary": {
                    "total_reports": len(reports),
                    "valid_reports": sum(1 for r in reports.values() if r.is_valid()),
                    "invalid_reports": sum(
                        1 for r in reports.values() if not r.is_valid()
                    ),
                    "average_score": (
                        sum(r.validation_score for r in reports.values()) / len(reports)
                        if reports
                        else 0
                    ),
                },
                "reports": {path: report.to_dict() for path, report in reports.items()},
            }
            return json.dumps(result, indent=2, ensure_ascii=False)

        elif output_format == "text":
            lines = ["RULE VALIDATION REPORT", "=" * 50]

            for path, report in reports.items():
                lines.append(f"\n{report.get_summary()}")

                # 添加关键问题
                critical_issues = [
                    i
                    for i in report.issues
                    if i.severity
                    in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
                ]

                if critical_issues:
                    lines.append("\nCritical Issues:")
                    for issue in critical_issues[:5]:  # 只显示前5个
                        lines.append(f"  - {issue.description} ({issue.location})")

            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported output format: {output_format}")
