"""
高级Markdown规则解析器

扩展基础MarkdownCanon功能，支持：
1. 嵌套章节解析
2. 交叉引用解析
3. 动态包含支持
4. 条件规则标记
5. 依赖关系分析
6. 高级验证功能

设计目标：保持向后兼容性，同时提供增强功能。
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .markdown_canon import MarkdownCanon, CanonSection, CanonSectionType
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ReferenceType(Enum):
    """引用类型"""

    CROSS_REFERENCE = "cross_reference"  # 交叉引用 [@section]
    INCLUDE = "include"  # 动态包含 {{include:path}}
    CONDITIONAL = "conditional"  # 条件规则 {{if:condition}}
    MACRO = "macro"  # 宏定义 {{macro:name}}


@dataclass
class Reference:
    """引用定义"""

    source_section: str
    target: str
    reference_type: ReferenceType
    line_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dependency:
    """依赖关系"""

    source: str
    target: str
    dependency_type: str  # reference, include, metadata, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationError:
    """验证错误"""

    error_type: str
    severity: str  # info, warning, error, critical
    message: str
    location: str  # section:name, line:number, etc.
    suggestion: Optional[str] = None


class AdvancedMarkdownCanon(MarkdownCanon):
    """高级Markdown规则解析器"""

    def __init__(self, path: Path, raw_content: str = ""):
        # 正确调用父类初始化，传递所有参数
        super().__init__(path=path, raw_content=raw_content)
        self.references: Dict[str, List[Reference]] = {}  # 章节名 -> 引用列表
        self.dependencies: List[Dependency] = []  # 依赖关系
        self.nested_sections: Dict[str, List[str]] = {}  # 父章节 -> 子章节列表
        self.validation_errors: List[ValidationError] = []  # 验证错误
        self.macros: Dict[str, str] = {}  # 宏定义
        self.include_cache: Dict[str, str] = {}  # 包含文件缓存

        # 如果提供了原始内容，进行增强解析
        if raw_content:
            self._enhanced_parse_content()

    def _enhanced_parse_content(self):
        """增强解析内容"""
        # 首先调用父类的基础解析
        super()._parse_content()

        # 提取宏定义
        self._extract_macros()

        # 提取交叉引用和动态包含
        self._extract_references()

        # 分析嵌套章节结构
        self._analyze_nested_sections()

        # 分析依赖关系
        self._analyze_dependencies()

        # 验证规则结构
        self._validate_structure()

        # 展开宏和包含
        self._expand_content()

    def _extract_macros(self):
        """提取宏定义"""
        macro_pattern = r"\{\{macro:([^}]+)\}\}([\s\S]*?)\{\{endmacro\}\}"
        matches = re.findall(macro_pattern, self.raw_content)

        for macro_name, macro_content in matches:
            self.macros[macro_name.strip()] = macro_content.strip()
            logger.debug(f"Extracted macro '{macro_name}'")

    def _extract_references(self):
        """提取所有类型的引用"""
        for section_name, section in self.sections.items():
            section_refs = []

            # 提取交叉引用 [@section_name]
            cross_ref_pattern = r"\[@([^\]]+)\]"
            for match in re.finditer(cross_ref_pattern, section.content):
                target_text = match.group(1)
                # 尝试将引用文本映射到完整的章节名称
                target_section = self._resolve_reference_target(target_text)
                ref = Reference(
                    source_section=section_name,
                    target=target_section,
                    reference_type=ReferenceType.CROSS_REFERENCE,
                    line_number=self._find_line_number(section.content, match.start()),
                )
                section_refs.append(ref)

            # 提取动态包含 {{include:path}}
            include_pattern = r"\{\{include:([^}]+)\}\}"
            for match in re.finditer(include_pattern, section.content):
                target = match.group(1)
                ref = Reference(
                    source_section=section_name,
                    target=target,
                    reference_type=ReferenceType.INCLUDE,
                    line_number=self._find_line_number(section.content, match.start()),
                    metadata={"path": target},
                )
                section_refs.append(ref)

            # 提取条件规则 {{if:condition}}
            conditional_pattern = r"\{\{if:([^}]+)\}\}"
            for match in re.finditer(conditional_pattern, section.content):
                condition = match.group(1)
                ref = Reference(
                    source_section=section_name,
                    target=condition,
                    reference_type=ReferenceType.CONDITIONAL,
                    line_number=self._find_line_number(section.content, match.start()),
                    metadata={"condition": condition},
                )
                section_refs.append(ref)

            if section_refs:
                self.references[section_name] = section_refs
                logger.debug(
                    f"Extracted {len(section_refs)} references from section '{section_name}'"
                )

    def _find_line_number(self, content: str, position: int) -> int:
        """查找字符串位置对应的行号"""
        return content[:position].count("\n") + 1

    def _resolve_reference_target(self, target_text: str) -> str:
        """将引用文本解析为完整的章节名称

        例如：'角色设定' -> '角色设定 (Characters)'
        """
        # 首先检查是否有完全匹配的章节
        if target_text in self.sections:
            return target_text

        # 尝试部分匹配：检查引用文本是否是章节名称的一部分
        for section_name in self.sections.keys():
            if target_text in section_name:
                return section_name

        # 尝试模糊匹配：检查引用文本是否与章节名称的主要部分匹配
        # 例如：移除括号和英文部分后进行比较
        for section_name in self.sections.keys():
            # 提取中文部分（假设括号前的内容）
            chinese_part = (
                section_name.split(" (")[0] if " (" in section_name else section_name
            )
            if target_text == chinese_part:
                return section_name

        # 如果没有找到匹配，返回原始文本
        return target_text

    def _analyze_nested_sections(self):
        """分析嵌套章节结构"""
        # 基于标题级别分析嵌套关系
        section_levels = {}

        for section_name in self.sections.keys():
            # 简单实现：通过标题级别推断嵌套
            # 实际实现可能需要解析原始Markdown的标题级别
            level = self._get_section_level(section_name)
            section_levels[section_name] = level

        # 构建嵌套关系（简化版本）
        # 实际实现需要更复杂的解析
        sorted_sections = sorted(section_levels.items(), key=lambda x: x[1])

        for i, (section_name, level) in enumerate(sorted_sections):
            parent = None
            # 查找最近的上级标题
            for j in range(i - 1, -1, -1):
                prev_name, prev_level = sorted_sections[j]
                if prev_level < level:
                    parent = prev_name
                    break

            if parent:
                self.nested_sections.setdefault(parent, []).append(section_name)

    def _get_section_level(self, section_name: str) -> int:
        """获取章节级别（基于标题深度）"""
        # 简化实现：假设章节名就是标题文本
        # 实际实现需要解析原始Markdown
        return 1  # 基础实现，返回固定级别

    def _analyze_dependencies(self):
        """分析依赖关系"""
        # 分析引用依赖
        for section_name, refs in self.references.items():
            for ref in refs:
                if ref.reference_type == ReferenceType.CROSS_REFERENCE:
                    dep = Dependency(
                        source=section_name,
                        target=ref.target,
                        dependency_type="reference",
                        metadata={"reference_type": ref.reference_type.value},
                    )
                    self.dependencies.append(dep)

        # 分析元数据依赖
        if "requires" in self.metadata:
            requirements = self.metadata["requires"]
            if isinstance(requirements, list):
                for req in requirements:
                    dep = Dependency(
                        source=self.path.name,
                        target=req,
                        dependency_type="metadata",
                        metadata={"field": "requires"},
                    )
                    self.dependencies.append(dep)
            elif isinstance(requirements, str):
                dep = Dependency(
                    source=self.path.name,
                    target=requirements,
                    dependency_type="metadata",
                    metadata={"field": "requires"},
                )
                self.dependencies.append(dep)

        # 分析包含依赖
        for section_name, refs in self.references.items():
            for ref in refs:
                if ref.reference_type == ReferenceType.INCLUDE:
                    dep = Dependency(
                        source=section_name,
                        target=ref.target,
                        dependency_type="include",
                        metadata={"path": ref.metadata.get("path")},
                    )
                    self.dependencies.append(dep)

    def _validate_structure(self):
        """验证规则结构"""
        self.validation_errors = []

        # 检查交叉引用有效性
        for section_name, refs in self.references.items():
            for ref in refs:
                if ref.reference_type == ReferenceType.CROSS_REFERENCE:
                    if ref.target not in self.sections:
                        error = ValidationError(
                            error_type="invalid_reference",
                            severity="warning",
                            message=f"Section '{section_name}' references non-existent section '{ref.target}'",
                            location=f"section:{section_name}",
                            suggestion=f"Check if section '{ref.target}' exists or fix the reference",
                        )
                        self.validation_errors.append(error)

        # 检查循环依赖
        if self._has_circular_dependencies():
            error = ValidationError(
                error_type="circular_dependency",
                severity="error",
                message="Circular dependencies detected in rules",
                location="global",
                suggestion="Review dependency relationships between sections",
            )
            self.validation_errors.append(error)

        # 检查必需章节
        required_sections = ["世界观", "World", "world"]
        for req_section in required_sections:
            if not any(
                req_section.lower() in name.lower() for name in self.sections.keys()
            ):
                error = ValidationError(
                    error_type="missing_required_section",
                    severity="warning",
                    message=f"Missing required world setting section (looking for '{req_section}')",
                    location="global",
                    suggestion="Add a world setting section to define the basic world context",
                )
                self.validation_errors.append(error)

    def _has_circular_dependencies(self) -> bool:
        """检查循环依赖"""
        # 构建邻接表
        graph = {}
        for dep in self.dependencies:
            if dep.dependency_type in ["reference", "include"]:
                graph.setdefault(dep.source, []).append(dep.target)

        # DFS检测循环
        visited = set()
        recursion_stack = set()

        def dfs(node: str) -> bool:
            if node in recursion_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True

            recursion_stack.remove(node)
            return False

        for node in graph:
            if dfs(node):
                return True

        return False

    def _expand_content(self):
        """展开宏和包含内容"""
        # 展开宏
        for section_name, section in self.sections.items():
            expanded_content = section.content

            # 展开宏调用 {{use:macro_name}}
            macro_use_pattern = r"\{\{use:([^}]+)\}\}"
            for match in re.finditer(macro_use_pattern, expanded_content):
                macro_name = match.group(1)
                if macro_name in self.macros:
                    macro_content = self.macros[macro_name]
                    expanded_content = expanded_content.replace(
                        match.group(0), macro_content
                    )

            # 更新章节内容
            section.content = expanded_content

    def get_referenced_sections(self, section_name: str) -> List[str]:
        """获取引用的章节"""
        if section_name not in self.references:
            return []

        return [
            ref.target
            for ref in self.references[section_name]
            if ref.reference_type == ReferenceType.CROSS_REFERENCE
        ]

    def get_dependent_sections(self, section_name: str) -> List[str]:
        """获取依赖的章节"""
        dependents = []
        for dep in self.dependencies:
            if dep.target == section_name and dep.dependency_type == "reference":
                dependents.append(dep.source)
        return dependents

    def get_include_paths(self) -> List[str]:
        """获取所有包含文件路径"""
        include_paths = []
        for refs in self.references.values():
            for ref in refs:
                if ref.reference_type == ReferenceType.INCLUDE:
                    include_paths.append(ref.target)
        return list(set(include_paths))

    def get_validation_report(self) -> Dict[str, Any]:
        """获取验证报告"""
        error_count = sum(1 for e in self.validation_errors if e.severity == "error")
        warning_count = sum(
            1 for e in self.validation_errors if e.severity == "warning"
        )
        info_count = sum(1 for e in self.validation_errors if e.severity == "info")

        return {
            "canon_path": str(self.path),
            "total_issues": len(self.validation_errors),
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "is_valid": error_count == 0,
            "issues": [
                {
                    "type": error.error_type,
                    "severity": error.severity,
                    "message": error.message,
                    "location": error.location,
                    "suggestion": error.suggestion,
                }
                for error in self.validation_errors
            ],
            "dependencies": [
                {
                    "source": dep.source,
                    "target": dep.target,
                    "type": dep.dependency_type,
                }
                for dep in self.dependencies
            ],
            "references": {
                section: [
                    {
                        "target": ref.target,
                        "type": ref.reference_type.value,
                        "line": ref.line_number,
                    }
                    for ref in refs
                ]
                for section, refs in self.references.items()
            },
        }

    def resolve_include(
        self, include_path: str, base_dir: Optional[Path] = None
    ) -> Optional[str]:
        """解析包含文件内容"""
        if include_path in self.include_cache:
            return self.include_cache[include_path]

        try:
            # 确定基础目录
            if base_dir is None:
                base_dir = self.path.parent

            # 解析路径
            target_path = base_dir / include_path

            if not target_path.exists():
                logger.warning(f"Include file not found: {target_path}")
                return None

            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.include_cache[include_path] = content
            return content

        except Exception as e:
            logger.error(f"Failed to resolve include {include_path}: {e}")
            return None

    def to_enhanced_dict(self) -> Dict[str, Any]:
        """转换为增强字典（包含高级信息）"""
        base_dict = super().to_dict()

        enhanced_dict = {
            **base_dict,
            "advanced_features": {
                "has_references": len(self.references) > 0,
                "has_dependencies": len(self.dependencies) > 0,
                "has_macros": len(self.macros) > 0,
                "has_nested_sections": len(self.nested_sections) > 0,
                "validation_status": self.get_validation_report()["is_valid"],
            },
            "references": {
                section: [
                    {
                        "target": ref.target,
                        "type": ref.reference_type.value,
                        "line": ref.line_number,
                    }
                    for ref in refs
                ]
                for section, refs in self.references.items()
            },
            "dependencies": [
                {
                    "source": dep.source,
                    "target": dep.target,
                    "type": dep.dependency_type,
                }
                for dep in self.dependencies
            ],
            "macros": list(self.macros.keys()),
            "nested_sections": self.nested_sections,
            "validation_report": self.get_validation_report(),
        }

        return enhanced_dict

    def get_section_with_context(
        self, section_name: str, include_references: bool = True
    ) -> Dict[str, Any]:
        """获取章节内容及其上下文"""
        section = self.get_section(section_name)
        if not section:
            return {}

        result = {
            "name": section_name,
            "type": section.section_type.value,
            "content": section.content,
            "metadata": section.metadata,
            "line_start": section.line_start,
            "line_end": section.line_end,
        }

        if include_references:
            # 添加引用信息
            referenced = self.get_referenced_sections(section_name)
            dependents = self.get_dependent_sections(section_name)

            result["references"] = {"outgoing": referenced, "incoming": dependents}

            # 添加嵌套章节信息
            if section_name in self.nested_sections:
                result["children"] = self.nested_sections[section_name]

            parent = None
            for parent_name, children in self.nested_sections.items():
                if section_name in children:
                    parent = parent_name
                    break

            if parent:
                result["parent"] = parent

        return result

    def search_with_context(
        self, query: str, section_type: Optional[CanonSectionType] = None
    ) -> List[Dict[str, Any]]:
        """增强搜索功能，返回上下文信息"""
        base_results = super().search_content(query, section_type)

        enhanced_results = []
        for section_name, context in base_results:
            section_info = self.get_section_with_context(section_name)
            enhanced_results.append(
                {
                    "section": section_name,
                    "context": context,
                    "section_info": section_info,
                    "relevance_score": self._calculate_relevance_score(query, context),
                }
            )

        # 按相关性排序
        enhanced_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return enhanced_results

    def _calculate_relevance_score(self, query: str, context: str) -> float:
        """计算查询与上下文的相关性分数"""
        query_lower = query.lower()
        context_lower = context.lower()

        # 简单实现：基于出现次数和位置
        if query_lower not in context_lower:
            return 0.0

        # 计算出现次数
        count = context_lower.count(query_lower)

        # 计算位置权重（越靠前权重越高）
        first_pos = context_lower.find(query_lower)
        position_weight = 1.0 - (first_pos / max(len(context_lower), 1))

        # 综合分数
        score = min(count * 0.3 + position_weight * 0.7, 1.0)
        return score

    def merge_with(
        self, other_canon: "AdvancedMarkdownCanon"
    ) -> "AdvancedMarkdownCanon":
        """合并两个规则集"""
        # 创建新的规则集
        merged_content = self.raw_content + "\n\n---\n\n" + other_canon.raw_content
        merged_canon = AdvancedMarkdownCanon(path=self.path, raw_content=merged_content)

        return merged_canon

    def extract_rule_patterns(self) -> Dict[str, List[str]]:
        """提取规则模式"""
        patterns = {
            "constraints": [],
            "permissions": [],
            "causality_rules": [],
            "character_traits": [],
            "location_features": [],
        }

        # 从冲突解决章节提取约束
        conflict_section = self.get_section_by_type(CanonSectionType.CONFLICT)
        if conflict_section:
            # 提取约束模式（如"不能"、"必须"、"禁止"等）
            constraint_patterns = [
                r"不能([^。]+)",
                r"必须([^。]+)",
                r"禁止([^。]+)",
                r"不允许([^。]+)",
                r"应当([^。]+)",
            ]

            for pattern in constraint_patterns:
                matches = re.findall(pattern, conflict_section.content)
                patterns["constraints"].extend(matches)

        # 从权限边界章节提取权限
        permissions_section = self.get_section_by_type(CanonSectionType.PERMISSIONS)
        if permissions_section:
            permission_patterns = [
                r"可以([^。]+)",
                r"允许([^。]+)",
                r"有权([^。]+)",
                r"能够([^。]+)",
            ]

            for pattern in permission_patterns:
                matches = re.findall(pattern, permissions_section.content)
                patterns["permissions"].extend(matches)

        # 清理结果
        for key in patterns:
            patterns[key] = [p.strip() for p in patterns[key] if p.strip()]
            patterns[key] = list(set(patterns[key]))

        return patterns
