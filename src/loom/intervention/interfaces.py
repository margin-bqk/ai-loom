"""
玩家干预层接口定义

定义玩家干预层的抽象接口，确保干预解析、验证和处理的解耦。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class InterventionType(Enum):
    """干预类型"""

    OOC = "ooc"  # 场外注释
    EDIT = "edit"  # 世界编辑
    RETCON = "retcon"  # 追溯性修改
    TONE = "tone"  # 基调调整
    INTENT = "intent"  # 意图声明
    META = "meta"  # 元干预
    SUGGESTION = "suggestion"  # 建议


class PermissionLevel(Enum):
    """权限级别"""

    ALLOW = "allow"  # 允许
    WARN = "warn"  # 警告但允许
    DENY = "deny"  # 拒绝
    REQUIRE_APPROVAL = "require_approval"  # 需要批准


@dataclass
class Intervention:
    """干预"""

    type: InterventionType
    content: str
    player_id: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Intent:
    """玩家意图"""

    action: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = None
    confidence: float = 1.0  # 意图识别置信度 0.0-1.0

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ParsedInput:
    """解析后的输入"""

    raw_input: str
    narrative_part: Optional[str] = None
    interventions: List[Intervention] = None
    intents: List[Intent] = None

    def __post_init__(self):
        if self.interventions is None:
            self.interventions = []
        if self.intents is None:
            self.intents = []


@dataclass
class PermissionResult:
    """权限验证结果"""

    allowed: bool
    level: PermissionLevel
    message: str
    required_approval: bool = False
    approval_reason: Optional[str] = None


@dataclass
class ProcessedResult:
    """处理结果"""

    success: bool
    narrative_impact: Optional[str] = None
    state_changes: Dict[str, Any] = None
    messages: List[str] = None
    requires_confirmation: bool = False

    def __post_init__(self):
        if self.state_changes is None:
            self.state_changes = {}
        if self.messages is None:
            self.messages = []


class PlayerIntervention(ABC):
    """玩家干预层接口"""

    @abstractmethod
    def parse_input(self, input_text: str) -> ParsedInput:
        """解析玩家输入

        Args:
            input_text: 玩家输入文本

        Returns:
            解析后的输入

        Raises:
            ParseError: 解析失败时
        """
        pass

    @abstractmethod
    async def process_intervention(
        self, intervention: Intervention, session_state: Dict[str, Any]
    ) -> ProcessedResult:
        """处理干预

        Args:
            intervention: 干预对象
            session_state: 会话状态

        Returns:
            处理结果

        Raises:
            InterventionError: 处理失败时
        """
        pass

    @abstractmethod
    def validate_permission(
        self, intervention: Intervention, rules_text: str
    ) -> PermissionResult:
        """验证权限

        Args:
            intervention: 干预对象
            rules_text: 规则文本

        Returns:
            权限验证结果
        """
        pass

    @abstractmethod
    async def absorb_intervention(
        self, intervention: Intervention, current_narrative: str
    ) -> str:
        """吸收干预到叙事中

        Args:
            intervention: 干预对象
            current_narrative: 当前叙事文本

        Returns:
            吸收后的叙事文本
        """
        pass

    @abstractmethod
    def get_supported_intervention_types(self) -> List[InterventionType]:
        """获取支持的干预类型

        Returns:
            支持的干预类型列表
        """
        pass


class InterventionParser(ABC):
    """干预解析器接口"""

    @abstractmethod
    def parse(self, input_text: str) -> ParsedInput:
        """解析输入"""
        pass

    @abstractmethod
    def extract_interventions(self, input_text: str) -> List[Intervention]:
        """提取干预"""
        pass

    @abstractmethod
    def is_intervention(self, text: str) -> bool:
        """判断是否为干预"""
        pass


class IntentRecognizer(ABC):
    """意图识别器接口"""

    @abstractmethod
    async def recognize(self, input_text: str) -> List[Intent]:
        """识别意图

        Args:
            input_text: 输入文本

        Returns:
            意图列表
        """
        pass

    @abstractmethod
    def get_intent_patterns(self) -> Dict[str, Any]:
        """获取意图模式

        Returns:
            意图模式字典
        """
        pass


class PermissionValidator(ABC):
    """权限验证器接口"""

    @abstractmethod
    def validate(self, intervention: Intervention, rules_text: str) -> PermissionResult:
        """验证权限"""
        pass

    @abstractmethod
    def check_permission_level(
        self, intervention_type: InterventionType, rule_section: str
    ) -> PermissionLevel:
        """检查权限级别"""
        pass


class AbsorptionEngine(ABC):
    """吸收引擎接口"""

    @abstractmethod
    async def absorb(
        self,
        intervention: Intervention,
        current_narrative: str,
        session_state: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """吸收干预

        Args:
            intervention: 干预对象
            current_narrative: 当前叙事文本
            session_state: 会话状态

        Returns:
            (吸收后的叙事文本, 状态变化)
        """
        pass

    @abstractmethod
    def can_absorb(self, intervention: Intervention) -> bool:
        """检查是否可以吸收

        Args:
            intervention: 干预对象

        Returns:
            是否可以吸收
        """
        pass


class AuditLogger(ABC):
    """审计日志器接口"""

    @abstractmethod
    async def log_intervention(
        self, intervention: Intervention, result: ProcessedResult
    ) -> None:
        """记录干预

        Args:
            intervention: 干预对象
            result: 处理结果
        """
        pass

    @abstractmethod
    async def get_intervention_history(
        self, session_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取干预历史

        Args:
            session_id: 会话ID
            limit: 数量限制

        Returns:
            干预历史列表
        """
        pass


# 异常定义
class ParseError(Exception):
    """解析错误"""

    pass


class InterventionError(Exception):
    """干预错误"""

    pass


class PermissionDeniedError(Exception):
    """权限拒绝错误"""

    pass


class AbsorptionError(Exception):
    """吸收错误"""

    pass
