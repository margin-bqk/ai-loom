"""
世界记忆层 (World Memory)

职责：结构化叙事状态存储（Canon事实、角色、剧情线、地点等）。
"""

from .world_memory import WorldMemory, MemoryEntity, MemoryRelation
from .structured_store import StructuredStore
from .vector_store import VectorStore
from .summarizer import MemorySummarizer

__all__ = [
    "WorldMemory",
    "MemoryEntity",
    "MemoryRelation",
    "StructuredStore",
    "VectorStore",
    "MemorySummarizer",
]