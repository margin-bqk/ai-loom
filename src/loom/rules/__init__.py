"""
规则层 (Markdown规则)

职责：纯Markdown编写的世界观、叙事基调、冲突解决哲学等。
提供规则解析、验证、热加载和版本控制功能。
"""

from .advanced_markdown_canon import (
    AdvancedMarkdownCanon,
    Dependency,
    Reference,
    ValidationError,
)
from .interfaces import (
    CanonLoader,
    CanonNotFoundError,
    CanonValidator,
    CanonWatcher,
    ParseError,
    RuleLayer,
)
from .interfaces import ValidationError as InterfacesValidationError
from .markdown_canon import CanonSection, CanonSectionType, MarkdownCanon
from .rule_hot_loader import (
    CanonVersion,
    ChangeType,
    FileChange,
    RuleHotLoader,
    SessionState,
)
from .rule_loader import RuleLoader
from .rule_validator import (
    RuleValidator,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationType,
)
from .version_control import VersionControl

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
