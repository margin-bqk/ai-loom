"""
规则层 (Markdown规则)

职责：纯Markdown编写的世界观、叙事基调、冲突解决哲学等。
提供规则解析、验证、热加载和版本控制功能。
"""

from .markdown_canon import MarkdownCanon, CanonSection, CanonSectionType
from .advanced_markdown_canon import (
    AdvancedMarkdownCanon,
    Reference,
    Dependency,
    ValidationError,
)
from .rule_loader import RuleLoader
from .rule_validator import (
    RuleValidator,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationType,
)
from .rule_hot_loader import (
    RuleHotLoader,
    FileChange,
    CanonVersion,
    SessionState,
    ChangeType,
)
from .version_control import VersionControl
from .interfaces import (
    RuleLayer,
    CanonLoader,
    CanonValidator,
    CanonWatcher,
    ParseError,
    ValidationError as InterfacesValidationError,
    CanonNotFoundError,
)

__all__ = [
    # 基础组件
    "MarkdownCanon",
    "CanonSection",
    "CanonSectionType",
    "RuleLoader",
    "VersionControl",
    # 第二阶段增强组件
    "AdvancedMarkdownCanon",
    "Reference",
    "Dependency",
    "ValidationError",
    # 规则验证器
    "RuleValidator",
    "ValidationIssue",
    "ValidationReport",
    "ValidationSeverity",
    "ValidationType",
    # 规则热加载器
    "RuleHotLoader",
    "FileChange",
    "CanonVersion",
    "SessionState",
    "ChangeType",
    # 接口
    "RuleLayer",
    "CanonLoader",
    "CanonValidator",
    "CanonWatcher",
    "ParseError",
    "InterfacesValidationError",
    "CanonNotFoundError",
]
