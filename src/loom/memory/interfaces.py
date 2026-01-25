"""
世界记忆层接口定义

定义世界记忆层的抽象接口，确保记忆存储、检索和管理的解耦。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid


class MemoryEntityType(Enum):
    """记忆实体类型"""
    CHARACTER = "character"
    LOCATION = "location"
    FACT = "fact"
    PLOTLINE = "plotline"
    STYLE = "style"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    OBJECT = "object"


class MemoryRelationType(Enum):
    """记忆关系类型"""
    PART_OF = "part_of"
    CAUSED_BY = "caused_by"
    LOCATED_AT = "located_at"
    RELATED_TO = "related_to"
    KNOWS = "knows"
    OWNS = "owns"
    BELONGS_TO = "belongs_to"
    PRECEDES = "precedes"
    FOLLOWS = "follows"


@dataclass
class MemoryEntity:
    """记忆实体"""
    id: str
    type: MemoryEntityType
    content: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MemoryRelation:
    """记忆关系"""
    source_id: str
    target_id: str
    relation_type: MemoryRelationType
    strength: float = 1.0  # 关系强度 0.0-1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MemoryQuery:
    """记忆查询"""
    entity_types: Optional[List[MemoryEntityType]] = None
    session_id: Optional[str] = None
    keywords: Optional[List[str]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    limit: int = 10
    offset: int = 0
    
    def __post_init__(self):
        if self.entity_types is None:
            self.entity_types = []


@dataclass
class MemorySummary:
    """记忆摘要"""
    entities_count: int
    relations_count: int
    by_type: Dict[MemoryEntityType, int]
    recent_entities: List[MemoryEntity]
    key_facts: List[str]
    generated_at: datetime


class WorldMemory(ABC):
    """世界记忆层接口"""
    
    @abstractmethod
    async def store_entity(self, entity: MemoryEntity) -> str:
        """存储记忆实体
        
        Args:
            entity: 记忆实体
            
        Returns:
            实体ID
            
        Raises:
            StorageError: 存储失败时
        """
        pass
    
    @abstractmethod
    async def retrieve_entity(self, entity_id: str) -> Optional[MemoryEntity]:
        """检索记忆实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            记忆实体，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def query_entities(self, query: MemoryQuery) -> List[MemoryEntity]:
        """查询记忆实体
        
        Args:
            query: 查询条件
            
        Returns:
            记忆实体列表
        """
        pass
    
    @abstractmethod
    async def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆实体
        
        Args:
            entity_id: 实体ID
            updates: 更新内容
            
        Returns:
            是否成功更新
        """
        pass
    
    @abstractmethod
    async def delete_entity(self, entity_id: str) -> bool:
        """删除记忆实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    async def add_relation(self, relation: MemoryRelation) -> bool:
        """添加记忆关系
        
        Args:
            relation: 记忆关系
            
        Returns:
            是否成功添加
        """
        pass
    
    @abstractmethod
    async def remove_relation(self, source_id: str, target_id: str, relation_type: MemoryRelationType) -> bool:
        """移除记忆关系
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            
        Returns:
            是否成功移除
        """
        pass
    
    @abstractmethod
    async def get_related_entities(self, entity_id: str, relation_type: Optional[MemoryRelationType] = None) -> List[MemoryEntity]:
        """获取相关实体
        
        Args:
            entity_id: 实体ID
            relation_type: 关系类型（如未指定则返回所有关系）
            
        Returns:
            相关实体列表
        """
        pass
    
    @abstractmethod
    async def summarize(self, session_id: str, time_range: Optional[Tuple[datetime, datetime]] = None) -> MemorySummary:
        """生成记忆摘要
        
        Args:
            session_id: 会话ID
            time_range: 时间范围
            
        Returns:
            记忆摘要
        """
        pass
    
    @abstractmethod
    async def rollback(self, session_id: str, to_version: int) -> bool:
        """回滚到指定版本
        
        Args:
            session_id: 会话ID
            to_version: 目标版本
            
        Returns:
            是否成功回滚
        """
        pass
    
    @abstractmethod
    async def cleanup(self, session_id: str, max_age_hours: int = 24) -> int:
        """清理旧记忆
        
        Args:
            session_id: 会话ID
            max_age_hours: 最大年龄（小时）
            
        Returns:
            清理的实体数量
        """
        pass


class MemoryStorage(ABC):
    """记忆存储接口"""
    
    @abstractmethod
    async def save_entity(self, entity: MemoryEntity) -> bool:
        """保存实体"""
        pass
    
    @abstractmethod
    async def load_entity(self, entity_id: str) -> Optional[MemoryEntity]:
        """加载实体"""
        pass
    
    @abstractmethod
    async def query_entities(self, query: MemoryQuery) -> List[MemoryEntity]:
        """查询实体"""
        pass
    
    @abstractmethod
    async def delete_entity(self, entity_id: str) -> bool:
        """删除实体"""
        pass


class MemoryRetrieval(ABC):
    """记忆检索接口"""
    
    @abstractmethod
    async def retrieve_relevant(self, context: str, limit: int = 10) -> List[MemoryEntity]:
        """检索相关记忆
        
        Args:
            context: 上下文文本
            limit: 返回数量限制
            
        Returns:
            相关记忆实体列表
        """
        pass
    
    @abstractmethod
    async def semantic_search(self, query: str, entity_types: Optional[List[MemoryEntityType]] = None) -> List[MemoryEntity]:
        """语义搜索
        
        Args:
            query: 搜索查询
            entity_types: 实体类型过滤
            
        Returns:
            搜索结果
        """
        pass


class MemorySummarizer(ABC):
    """记忆摘要器接口"""
    
    @abstractmethod
    async def summarize_entities(self, entities: List[MemoryEntity]) -> str:
        """生成实体摘要
        
        Args:
            entities: 实体列表
            
        Returns:
            摘要文本
        """
        pass
    
    @abstractmethod
    async def generate_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """生成时间线
        
        Args:
            session_id: 会话ID
            
        Returns:
            时间线事件列表
        """
        pass


# 异常定义
class StorageError(Exception):
    """存储错误"""
    pass


class RetrievalError(Exception):
    """检索错误"""
    pass


class ConsistencyError(Exception):
    """一致性错误（记忆冲突）"""
    pass