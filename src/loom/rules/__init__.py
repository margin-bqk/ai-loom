"""
规则层 (Markdown Canon)

职责：纯Markdown编写的世界观、叙事基调、冲突解决哲学等。
"""

from .markdown_canon import MarkdownCanon, CanonSection
from .rule_loader import RuleLoader
from .version_control import VersionControl

__all__ = [
    "MarkdownCanon",
    "CanonSection",
    "RuleLoader",
    "VersionControl",
]