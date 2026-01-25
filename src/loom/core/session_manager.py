"""
Session管理模块

负责会话生命周期：创建、加载、保存、删除。
支持会话元数据管理、状态跟踪、与ConfigManager集成。
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"


@dataclass
class SessionConfig:
    """会话配置"""
    name: str
    canon_path: str  # 规则文件路径
    memory_backend: str = "sqlite"
    llm_provider: str = "openai"
    max_turns: Optional[int] = None
    auto_save: bool = True
    auto_save_interval: int = 5  # 每5回合自动保存
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        """从字典创建配置"""
        return cls(
            name=data.get("name", "Unnamed Session"),
            canon_path=data.get("canon_path", "./canon"),
            memory_backend=data.get("memory_backend", "sqlite"),
            llm_provider=data.get("llm_provider", "openai"),
            max_turns=data.get("max_turns"),
            auto_save=data.get("auto_save", True),
            auto_save_interval=data.get("auto_save_interval", 5),
            metadata=data.get("metadata", {})
        )


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
    last_activity: datetime = field(default_factory=datetime.now)
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
    
    def increment_turn(self):
        """增加回合计数"""
        self.current_turn += 1
        self.total_turns += 1
        self.update_activity()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "config": {
                "name": self.config.name,
                "canon_path": self.config.canon_path,
                "memory_backend": self.config.memory_backend,
                "llm_provider": self.config.llm_provider,
                "max_turns": self.config.max_turns,
                "auto_save": self.config.auto_save,
                "auto_save_interval": self.config.auto_save_interval,
                "metadata": self.config.metadata
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "current_turn": self.current_turn,
            "total_turns": self.total_turns,
            "last_activity": self.last_activity.isoformat(),
            "state": self.state,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建会话"""
        config = SessionConfig.from_dict(data["config"])
        
        return cls(
            id=data["id"],
            name=data["name"],
            config=config,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            status=SessionStatus(data["status"]),
            current_turn=data["current_turn"],
            total_turns=data["total_turns"],
            last_activity=datetime.fromisoformat(data["last_activity"]),
            state=data["state"],
            metadata=data["metadata"]
        )


class SessionManager:
    """会话管理器"""
    
    def __init__(self, persistence_engine=None, config_manager=None):
        self.persistence = persistence_engine
        self.config_manager = config_manager
        self.active_sessions: Dict[str, Session] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        logger.info("SessionManager initialized")
    
    def _get_session_lock(self, session_id: str) -> asyncio.Lock:
        """获取会话锁（用于并发控制）"""
        if session_id not in self._session_locks:
            self._session_locks[session_id] = asyncio.Lock()
        return self._session_locks[session_id]
    
    async def create_session(self, config: SessionConfig) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        # 应用配置管理器中的默认值
        if self.config_manager:
            app_config = self.config_manager.get_config()
            
            # 如果未指定Provider，根据会话类型选择
            if not config.llm_provider or config.llm_provider not in app_config.llm_providers:
                # 尝试根据会话类型选择Provider
                session_type = config.metadata.get("session_type", "default")
                provider_selection = app_config.provider_selection
                
                # 检查会话类型映射
                if session_type in provider_selection.session_type_mapping:
                    mapping = provider_selection.session_type_mapping[session_type]
                    preferred_provider = mapping.get("preferred_provider")
                    if preferred_provider and preferred_provider in app_config.llm_providers:
                        config.llm_provider = preferred_provider
                        config.metadata["preferred_model"] = mapping.get("preferred_model")
                        logger.info(f"Selected provider {preferred_provider} for session type {session_type}")
                
                # 如果仍未设置，使用默认Provider
                if not config.llm_provider:
                    config.llm_provider = provider_selection.default_provider
                    logger.info(f"Using default provider {config.llm_provider}")
        
        session = Session(
            id=session_id,
            name=config.name,
            config=config,
            created_at=now,
            updated_at=now,
            last_activity=now,
            state={
                "turns": [],
                "characters": {},
                "locations": {},
                "plotlines": []
            },
            metadata={
                **config.metadata,
                "created_by": "system",
                "version": "1.0"
            }
        )
        
        async with self._get_session_lock(session_id):
            self.active_sessions[session_id] = session
            
            if self.persistence:
                await self.persistence.save_session(session)
        
        logger.info(f"Created session {session_id} ({config.name})")
        return session
    
    async def load_session(self, session_id: str, force_reload: bool = False) -> Optional[Session]:
        """加载会话"""
        # 首先检查活跃会话（除非强制重新加载）
        if not force_reload and session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # 从持久化存储加载
        if self.persistence:
            session_data = await self.persistence.load_session(session_id)
            if session_data:
                try:
                    if isinstance(session_data, dict):
                        session = Session.from_dict(session_data)
                    else:
                        # 假设已经是Session对象
                        session = session_data
                    
                    async with self._get_session_lock(session_id):
                        self.active_sessions[session_id] = session
                    
                    logger.info(f"Loaded session {session_id} from persistence")
                    return session
                except Exception as e:
                    logger.error(f"Failed to parse session data for {session_id}: {e}")
        
        logger.warning(f"Session {session_id} not found")
        return None
    
    async def save_session(self, session: Session, force: bool = False) -> bool:
        """保存会话"""
        # 检查是否需要自动保存
        if not force and not session.config.auto_save:
            return True
        
        # 检查自动保存间隔
        if not force and session.config.auto_save_interval > 0:
            if session.current_turn % session.config.auto_save_interval != 0:
                return True
        
        session.update_activity()
        
        async with self._get_session_lock(session.id):
            self.active_sessions[session.id] = session
            
            if self.persistence:
                success = await self.persistence.save_session(session)
                if success:
                    logger.debug(f"Saved session {session.id}")
                    return True
                else:
                    logger.error(f"Failed to save session {session.id} to persistence")
                    return False
        
        return True
    
    async def delete_session(self, session_id: str, permanent: bool = True) -> bool:
        """删除会话"""
        async with self._get_session_lock(session_id):
            if session_id in self.active_sessions:
                # 更新状态为已归档（如果非永久删除）
                if not permanent:
                    session = self.active_sessions[session_id]
                    session.status = SessionStatus.ARCHIVED
                    session.update_activity()
                    # 先释放锁，然后保存会话（save_session会重新获取锁）
                    # 避免死锁
                    pass
                else:
                    del self.active_sessions[session_id]
            
            # 从持久化存储删除
            if self.persistence and permanent:
                success = await self.persistence.delete_session(session_id)
                if success:
                    logger.info(f"Deleted session {session_id} from persistence")
                    return True
        
        # 在锁外部保存会话
        if not permanent and session_id in self.active_sessions:
            await self.save_session(self.active_sessions[session_id], force=True)
            logger.info(f"Archived session {session_id}")
            return True
        
        logger.info(f"Removed session {session_id} from memory")
        return True
    
    async def list_sessions(self, include_inactive: bool = False) -> Dict[str, Session]:
        """列出所有会话"""
        if self.persistence and include_inactive:
            # 从持久化存储获取所有会话
            try:
                all_sessions = await self.persistence.list_sessions()
                # 合并活跃会话
                for session_id, session in all_sessions.items():
                    if session_id not in self.active_sessions:
                        self.active_sessions[session_id] = session
            except Exception as e:
                logger.error(f"Failed to list sessions from persistence: {e}")
        
        if include_inactive:
            return self.active_sessions.copy()
        else:
            return {sid: sess for sid, sess in self.active_sessions.items()
                   if sess.status == SessionStatus.ACTIVE}
    
    async def update_session_status(self, session_id: str, status: SessionStatus) -> bool:
        """更新会话状态"""
        session = await self.load_session(session_id)
        if not session:
            return False
        
        async with self._get_session_lock(session_id):
            session.status = status
            session.update_activity()
            # 不在此处调用save_session，避免死锁
        
        # 在锁外部保存会话
        await self.save_session(session, force=True)
        logger.info(f"Updated session {session_id} status to {status.value}")
        return True
    
    async def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话统计信息"""
        session = await self.load_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "name": session.name,
            "status": session.status.value,
            "current_turn": session.current_turn,
            "total_turns": session.total_turns,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "uptime_hours": (datetime.now() - session.created_at).total_seconds() / 3600,
            "turns_per_hour": session.total_turns / max(1, (datetime.now() - session.created_at).total_seconds() / 3600),
            "config": {
                "llm_provider": session.config.llm_provider,
                "canon_path": session.config.canon_path,
                "max_turns": session.config.max_turns
            }
        }
    
    async def cleanup_inactive_sessions(self, max_inactive_hours: int = 24):
        """清理不活跃的会话"""
        cutoff_time = datetime.now().timestamp() - (max_inactive_hours * 3600)
        sessions_to_cleanup = []
        
        for session_id, session in self.active_sessions.items():
            if session.last_activity.timestamp() < cutoff_time:
                sessions_to_cleanup.append(session_id)
        
        for session_id in sessions_to_cleanup:
            await self.update_session_status(session_id, SessionStatus.ARCHIVED)
            logger.info(f"Archived inactive session {session_id}")
        
        return len(sessions_to_cleanup)
    
    async def search_sessions(self, query: Dict[str, Any]) -> List[Session]:
        """搜索会话"""
        results = []
        
        for session in self.active_sessions.values():
            match = True
            
            # 按名称搜索
            if "name" in query and query["name"].lower() not in session.name.lower():
                match = False
            
            # 按状态搜索
            if "status" in query and session.status.value != query["status"]:
                match = False
            
            # 按创建时间范围搜索
            if "created_after" in query:
                created_after = datetime.fromisoformat(query["created_after"]) if isinstance(query["created_after"], str) else query["created_after"]
                if session.created_at < created_after:
                    match = False
            
            if "created_before" in query:
                created_before = datetime.fromisoformat(query["created_before"]) if isinstance(query["created_before"], str) else query["created_before"]
                if session.created_at > created_before:
                    match = False
            
            if match:
                results.append(session)
        
        return results