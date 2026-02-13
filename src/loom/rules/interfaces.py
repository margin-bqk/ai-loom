"""
规则层接口定义

定义规则层（Markdown规则）的抽象接口，确保规则加载、验证和管理的解耦。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """验证严重性级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """验证问题"""

    severity: ValidationSeverity
    message: str
    section: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None


@dataclass
class ValidationResult:
    """验证结果"""

    valid: bool
    issues: List[ValidationIssue]
    warnings_count: int = 0
    errors_count: int = 0

    def __post_init__(self):
        self.warnings_count = sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING
        )
        self.errors_count = sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )


@dataclass
class CanonMetadata:
    """规则元数据"""

    version: str
    author: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class Canon:
    """规则集"""

    metadata: CanonMetadata
    sections: Dict[str, str]  # 章节名 → Markdown内容
    raw_text: str  # 原始完整文本
    file_path: Optional[str] = None

    def get_section(self, section_name: str) -> Optional[str]:
        """获取指定章节内容"""
        return self.sections.get(section_name)

    def has_section(self, section_name: str) -> bool:
        """检查是否存在指定章节"""
        return section_name in self.sections


@dataclass
class RuleSection:
    """规则章节"""

    name: str
    content: str
    order: int
    required: bool = False
    description: Optional[str] = None


class RuleLayer(ABC):
    """规则层接口"""

    @abstractmethod
    def load_canon(self, path: str) -> Canon:
        """加载规则集

        Args:
            path: 规则文件路径或目录

        Returns:
            规则集对象

        Raises:
            FileNotFoundError: 规则文件不存在时
            ParseError: 解析失败时
        """
        pass

    @abstractmethod
    def get_rule_section(self, canon: Canon, section: str) -> Optional[str]:
        """获取规则章节内容

        Args:
            canon: 规则集对象
            section: 章节名称

        Returns:
            章节内容，如果不存在则返回None
        """
        pass

    @abstractmethod
    def validate_canon(self, canon: Canon) -> ValidationResult:
        """验证规则集

        Args:
            canon: 规则集对象

        Returns:
            验证结果
        """
        pass

    @abstractmethod
    def watch_for_changes(self, path: str, callback: Callable[[Canon], None]) -> None:
        """监视规则文件变化

        Args:
            path: 规则文件路径
            callback: 变化时的回调函数
        """
        pass

    @abstractmethod
    def get_available_sections(self) -> List[str]:
        """获取可用的规则章节列表

        Returns:
            章节名称列表
        """
        pass


class CanonLoader(ABC):
    """规则加载器接口"""

    @abstractmethod
    def load(self, path: str) -> Canon:
        """加载规则"""
        pass

    @abstractmethod
    def reload(self, canon: Canon) -> Canon:
        """重新加载规则"""
        pass


class CanonValidator(ABC):
    """规则验证器接口"""

    @abstractmethod
    def validate(self, canon: Canon) -> ValidationResult:
        """验证规则"""
        pass

    @abstractmethod
    def validate_section(
        self, section_name: str, content: str
    ) -> List[ValidationIssue]:
        """验证单个章节"""
        pass


class CanonWatcher(ABC):
    """规则监视器接口"""

    @abstractmethod
    def start_watching(self, path: str, callback: Callable[[Canon], None]) -> None:
        """开始监视"""
        pass

    @abstractmethod
    def stop_watching(self, path: str) -> None:
        """停止监视"""
        pass

    @abstractmethod
    def is_watching(self, path: str) -> bool:
        """检查是否正在监视"""
        pass


# 异常定义
class ParseError(Exception):
    """解析错误"""

    pass


class ValidationError(Exception):
    """验证错误"""

    pass


class CanonNotFoundError(Exception):
    """规则集未找到错误"""

    pass
