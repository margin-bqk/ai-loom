"""
运行时核心层接口定义

定义运行时核心层的抽象接口，确保各层解耦和可替换性。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SessionStatus(Enum):
    """会话状态枚举"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"


@dataclass(frozen=True)
class SessionConfig:
    """会话配置数据类"""

    name: str
    canon_path: str
    llm_provider: str = "openai"
    max_turns: Optional[int] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "canon_path": self.canon_path,
            "llm_provider": self.llm_provider,
            "max_turns": self.max_turns,
            "metadata": self.metadata or {},
        }


@dataclass
class Session:
    """会话实体"""

    id: str
    name: str
    config: SessionConfig
    created_at: datetime
    updated_at: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    current_turn: int = 0
    total_turns: int = 0
    last_activity: datetime = None
    state: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.state is None:
            self.state = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Turn:
    """回合实体"""

    id: str
    session_id: str
    turn_number: int
    player_input: str
    llm_response: str
    memories_used: List[str]
    interventions: List[Dict[str, Any]]
    timestamp: datetime
    duration_ms: int


@dataclass
class TurnResult:
    """回合结果"""

    turn: Turn
    success: bool
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None


@dataclass
class PromptContext:
    """Prompt组装上下文"""

    session: Session
    rules_text: str
    memories_summary: str
    player_input: str
    interventions: List[Dict[str, Any]]
    turn_number: int


class RuntimeCore(ABC):
    """运行时核心层接口"""

    @abstractmethod
    async def create_session(self, config: SessionConfig) -> str:
        """创建新会话

        Args:
            config: 会话配置

        Returns:
            会话ID

        Raises:
            ConfigurationError: 配置无效时
        """
        pass

    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[Session]:
        """加载会话

        Args:
            session_id: 会话ID

        Returns:
            会话对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def save_session(self, session: Session) -> bool:
        """保存会话

        Args:
            session: 会话对象

        Returns:
            是否成功保存
        """
        pass

    @abstractmethod
    async def schedule_turn(self, session_id: str, player_input: str) -> TurnResult:
        """调度回合

        Args:
            session_id: 会话ID
            player_input: 玩家输入

        Returns:
            回合结果

        Raises:
            SessionNotFoundError: 会话不存在时
            TurnProcessingError: 回合处理失败时
        """
        pass

    @abstractmethod
    async def assemble_prompt(self, context: PromptContext) -> str:
        """组装Prompt

        Args:
            context: Prompt上下文

        Returns:
            组装好的Prompt文本
        """
        pass


class SessionManager(ABC):
    """会话管理器接口"""

    @abstractmethod
    async def create_session(self, config: SessionConfig) -> Session:
        """创建新会话"""
        pass

    @abstractmethod
    async def load_session(
        self, session_id: str, force_reload: bool = False
    ) -> Optional[Session]:
        """加载会话"""
        pass

    @abstractmethod
    async def save_session(self, session: Session, force: bool = False) -> bool:
        """保存会话"""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str, permanent: bool = True) -> bool:
        """删除会话"""
        pass

    @abstractmethod
    async def list_sessions(self, include_inactive: bool = False) -> Dict[str, Session]:
        """列出所有会话"""
        pass


class TurnScheduler(ABC):
    """回合调度器接口"""

    @abstractmethod
    async def schedule_turn(self, session_id: str, player_input: str) -> TurnResult:
        """调度回合"""
        pass

    @abstractmethod
    async def get_turn_history(self, session_id: str, limit: int = 100) -> List[Turn]:
        """获取回合历史"""
        pass


class PersistenceEngine(ABC):
    """持久化引擎接口"""

    @abstractmethod
    async def save_session(self, session: Session) -> bool:
        """保存会话"""
        pass

    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据"""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass

    @abstractmethod
    async def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """列出所有会话"""
        pass

    @abstractmethod
    async def save_turn(self, turn: Turn) -> bool:
        """保存回合"""
        pass

    @abstractmethod
    async def load_turns(
        self, session_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """加载回合列表"""
        pass


class PromptAssembler(ABC):
    """Prompt组装器接口"""

    @abstractmethod
    async def assemble(self, context: PromptContext) -> str:
        """组装Prompt"""
        pass

    @abstractmethod
    def get_token_count(self, prompt: str) -> int:
        """获取Prompt的令牌数量"""
        pass


# 叙事解释器相关数据类
@dataclass
class NarrativeContext:
    """叙事上下文"""

    session: Session
    current_scene: str
    characters_present: List[str]
    plot_points: List[str]
    narrative_tone: str = "neutral"
    narrative_pace: str = "normal"
    consistency_checks: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NarrativeInterpretation:
    """叙事解释结果"""

    interpretation: str
    consistency_score: float  # 0.0-1.0
    continuity_issues: List[str]
    suggested_improvements: List[str]
    narrative_arcs: List[Dict[str, Any]]


@dataclass
class NarrativeArchive:
    """叙事档案"""

    id: str
    session_id: str
    title: str
    summary: str
    narrative_timeline: List[Dict[str, Any]]
    key_characters: List[Dict[str, Any]]
    plot_arcs: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


# 叙事解释器接口
class NarrativeInterpreter(ABC):
    """叙事解释器接口 - 扩展SessionManager，添加叙事解释功能"""

    @abstractmethod
    async def create_session(self, config: SessionConfig) -> Session:
        """创建新会话"""
        pass

    @abstractmethod
    async def load_session(
        self, session_id: str, force_reload: bool = False
    ) -> Optional[Session]:
        """加载会话"""
        pass

    @abstractmethod
    async def save_session(self, session: Session, force: bool = False) -> bool:
        """保存会话"""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str, permanent: bool = True) -> bool:
        """删除会话"""
        pass

    @abstractmethod
    async def list_sessions(self, include_inactive: bool = False) -> Dict[str, Session]:
        """列出所有会话"""
        pass

    # 新增叙事解释方法
    @abstractmethod
    async def interpret_narrative(
        self, session_id: str, context: NarrativeContext
    ) -> NarrativeInterpretation:
        """解释叙事上下文，分析一致性和连续性"""
        pass

    @abstractmethod
    async def check_consistency(
        self, session_id: str, new_content: str
    ) -> Tuple[bool, List[str]]:
        """检查新内容与现有叙事的一致性"""
        pass

    @abstractmethod
    async def generate_narrative_summary(self, session_id: str) -> str:
        """生成叙事摘要"""
        pass

    @abstractmethod
    async def track_narrative_arcs(self, session_id: str) -> List[Dict[str, Any]]:
        """跟踪叙事弧线"""
        pass


# 叙事调度器接口
class NarrativeScheduler(ABC):
    """叙事调度器接口 - 扩展TurnScheduler，添加叙事调度功能"""

    @abstractmethod
    async def schedule_turn(self, session_id: str, player_input: str) -> TurnResult:
        """调度回合"""
        pass

    @abstractmethod
    async def get_turn_history(self, session_id: str, limit: int = 100) -> List[Turn]:
        """获取回合历史"""
        pass

    # 新增叙事调度方法
    @abstractmethod
    async def schedule_narrative_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """调度叙事事件（如时间跳跃、场景切换等）"""
        pass

    @abstractmethod
    async def get_narrative_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """获取叙事时间线"""
        pass

    @abstractmethod
    async def adjust_narrative_pace(self, session_id: str, pace: str) -> bool:
        """调整叙事节奏（slow/normal/fast）"""
        pass

    @abstractmethod
    async def manage_narrative_dependencies(self, session_id: str) -> Dict[str, Any]:
        """管理叙事依赖关系"""
        pass


# 叙事档案持久化接口
class NarrativeArchivePersistence(ABC):
    """叙事档案持久化接口"""

    @abstractmethod
    async def save_narrative_archive(self, archive: NarrativeArchive) -> bool:
        """保存叙事档案"""
        pass

    @abstractmethod
    async def load_narrative_archive(
        self, archive_id: str
    ) -> Optional[NarrativeArchive]:
        """加载叙事档案"""
        pass

    @abstractmethod
    async def list_narrative_archives(
        self, session_id: Optional[str] = None
    ) -> List[NarrativeArchive]:
        """列出叙事档案"""
        pass

    @abstractmethod
    async def export_to_markdown(self, archive_id: str, output_path: str) -> bool:
        """导出叙事档案为Markdown格式"""
        pass

    @abstractmethod
    async def import_from_markdown(
        self, markdown_path: str, session_id: str
    ) -> Optional[NarrativeArchive]:
        """从Markdown导入叙事档案"""
        pass

    @abstractmethod
    async def create_archive_version(
        self, archive_id: str, description: str
    ) -> Optional[str]:
        """创建档案版本"""
        pass

    @abstractmethod
    async def rollback_archive_version(self, archive_id: str, version: int) -> bool:
        """回滚到指定版本"""
        pass


# 异常定义
class ConfigurationError(Exception):
    """配置错误"""

    pass


class SessionNotFoundError(Exception):
    """会话未找到错误"""

    pass


class TurnProcessingError(Exception):
    """回合处理错误"""

    pass


class NarrativeConsistencyError(Exception):
    """叙事一致性错误"""

    pass


class ArchiveExportError(Exception):
    """档案导出错误"""

    pass
