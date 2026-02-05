"""
世界记忆层 (世界记忆)

职责：结构化叙事状态存储（Canon事实、角色、剧情线、地点等）。
包含第二阶段增强功能：向量存储集成、记忆摘要生成、增强记忆接口、一致性检查。
"""

from .world_memory import WorldMemory, MemoryEntity, MemoryRelation
from .structured_store import StructuredStore
from .vector_store import VectorStore
from .summarizer import MemorySummarizer

# 第二阶段增强组件
from .vector_memory_store import (
    VectorMemoryStore,
    VectorStoreBackend,
    VectorSearchResult,
    VectorSearchQuery,
)
from .memory_summarizer import (
    MemorySummarizer as EnhancedMemorySummarizer,
    SummaryConfig,
    SummaryStrategy,
    SummaryFormat,
    EnhancedMemorySummary,
)
from .enhanced_world_memory import (
    EnhancedWorldMemory,
    EnhancedMemoryConfig,
    TimelineEvent,
    RelationshipNetwork,
)
from .memory_consistency_checker import (
    MemoryConsistencyChecker,
    ConsistencyIssue,
    ConsistencyCheckResult,
    ConsistencyIssueType,
    ConsistencySeverity,
)

__all__ = [
    # 基础组件
    "WorldMemory",
    "MemoryEntity",
    "MemoryRelation",
    "StructuredStore",
    "VectorStore",
    "MemorySummarizer",
    # 第二阶段增强组件
    "VectorMemoryStore",
    "VectorStoreBackend",
    "VectorSearchResult",
    "VectorSearchQuery",
    "EnhancedMemorySummarizer",
    "SummaryConfig",
    "SummaryStrategy",
    "SummaryFormat",
    "EnhancedMemorySummary",
    "EnhancedWorldMemory",
    "EnhancedMemoryConfig",
    "TimelineEvent",
    "RelationshipNetwork",
    "MemoryConsistencyChecker",
    "ConsistencyIssue",
    "ConsistencyCheckResult",
    "ConsistencyIssueType",
    "ConsistencySeverity",
]
