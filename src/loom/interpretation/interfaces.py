"""
解释层接口定义

定义解释层（LLM推理）的抽象接口，确保规则解释和推理的解耦。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class ConsistencyLevel(Enum):
    """一致性级别"""
    HIGH = "high"      # 高度一致，无矛盾
    MEDIUM = "medium"  # 中等一致，轻微矛盾
    LOW = "low"        # 低一致，明显矛盾
    CONFLICT = "conflict"  # 冲突，无法调和


@dataclass
class InterpretationResult:
    """解释结果"""
    narrative_output: str
    reasoning_steps: List[str]
    confidence: float  # 0.0-1.0
    consistency_level: ConsistencyLevel
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ConsistencyReport:
    """一致性报告"""
    level: ConsistencyLevel
    issues: List[str]
    suggestions: List[str]
    score: float  # 0.0-1.0


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class InterpretationContext:
    """解释上下文"""
    rules_text: str
    memories_summary: str
    player_input: str
    session_state: Dict[str, Any]
    turn_number: int
    interventions: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.interventions is None:
            self.interventions = []


class InterpretationLayer(ABC):
    """解释层接口"""
    
    @abstractmethod
    async def interpret(
        self,
        context: InterpretationContext
    ) -> InterpretationResult:
        """解释规则并生成叙事输出
        
        Args:
            context: 解释上下文
            
        Returns:
            解释结果
            
        Raises:
            InterpretationError: 解释失败时
        """
        pass
    
    @abstractmethod
    async def check_consistency(
        self,
        result: InterpretationResult,
        rules_text: str
    ) -> ConsistencyReport:
        """检查解释结果与规则的一致性
        
        Args:
            result: 解释结果
            rules_text: 规则文本
            
        Returns:
            一致性报告
        """
        pass
    
    @abstractmethod
    async def explain_reasoning(
        self,
        result: InterpretationResult
    ) -> str:
        """解释推理过程
        
        Args:
            result: 解释结果
            
        Returns:
            推理过程的可读描述
        """
        pass


class LLMProvider(ABC):
    """LLM提供商接口"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本
        
        Args:
            prompt: 输入提示
            model: 模型名称（如未指定则使用默认模型）
            temperature: 温度参数
            max_tokens: 最大令牌数
            **kwargs: 其他参数
            
        Returns:
            LLM响应
            
        Raises:
            LLMError: LLM调用失败时
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用模型列表
        
        Returns:
            模型名称列表
        """
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """获取文本的令牌数量
        
        Args:
            text: 文本
            
        Returns:
            令牌数量
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """验证连接
        
        Returns:
            是否连接成功
        """
        pass


class RuleInterpreter(ABC):
    """规则解释器接口"""
    
    @abstractmethod
    async def interpret_rules(
        self,
        rules_text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解释规则
        
        Args:
            rules_text: 规则文本
            context: 解释上下文
            
        Returns:
            解释后的规则结构
        """
        pass
    
    @abstractmethod
    async def extract_constraints(
        self,
        rules_text: str
    ) -> List[Dict[str, Any]]:
        """提取约束条件
        
        Args:
            rules_text: 规则文本
            
        Returns:
            约束条件列表
        """
        pass


class ReasoningPipeline(ABC):
    """推理流水线接口"""
    
    @abstractmethod
    async def process(
        self,
        context: InterpretationContext
    ) -> InterpretationResult:
        """处理推理流水线
        
        Args:
            context: 解释上下文
            
        Returns:
            解释结果
        """
        pass
    
    @abstractmethod
    def add_step(self, step_name: str, step_func: callable) -> None:
        """添加处理步骤
        
        Args:
            step_name: 步骤名称
            step_func: 步骤函数
        """
        pass
    
    @abstractmethod
    def get_steps(self) -> List[str]:
        """获取处理步骤列表
        
        Returns:
            步骤名称列表
        """
        pass


class ConsistencyChecker(ABC):
    """一致性检查器接口"""
    
    @abstractmethod
    async def check(
        self,
        narrative: str,
        rules_text: str,
        memories: List[str]
    ) -> ConsistencyReport:
        """检查一致性
        
        Args:
            narrative: 叙事文本
            rules_text: 规则文本
            memories: 记忆列表
            
        Returns:
            一致性报告
        """
        pass
    
    @abstractmethod
    async def find_conflicts(
        self,
        narrative: str,
        rules_text: str
    ) -> List[Tuple[str, str]]:
        """查找冲突
        
        Args:
            narrative: 叙事文本
            rules_text: 规则文本
            
        Returns:
            冲突列表（冲突描述，建议修复）
        """
        pass


# 异常定义
class InterpretationError(Exception):
    """解释错误"""
    pass


class LLMError(Exception):
    """LLM错误"""
    pass


class ConsistencyError(Exception):
    """一致性错误"""
    pass