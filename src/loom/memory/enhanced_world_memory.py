"""
增强世界记忆 (EnhancedWorldMemory)

增强版世界记忆接口，统一结构化存储和向量存储，支持复杂查询、
语义搜索、时间线分析和关系网络查询。

设计目标：
1. 统一结构化存储（SQLite）和向量存储接口
2. 支持复杂查询（语义、时间范围、关系网络）
3. 集成记忆摘要生成
4. 提供高级记忆管理功能
5. 保持向后兼容性
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from ..utils.async_helpers import async_retry
from ..utils.logging_config import get_logger
from .interfaces import (
    ConsistencyError,
    MemoryQuery,
    MemorySummary,
    RetrievalError,
    StorageError,
)
from .memory_summarizer import EnhancedMemorySummary, MemorySummarizer, SummaryConfig
from .structured_store import StructuredStore
from .vector_memory_store import VectorMemoryStore, VectorSearchResult
from .world_memory import (
    MemoryEntity,
    MemoryEntityType,
    MemoryRelation,
    MemoryRelationType,
    WorldMemory,
)

logger = get_logger(__name__)


@dataclass
class EnhancedMemoryConfig:
    """增强记忆配置"""

    # 结构化存储配置
    structured_store_enabled: bool = True
    db_path: str = "./loom_memory.db"

    # 向量存储配置
    vector_store_enabled: bool = True
    vector_store_config: Optional[Dict[str, Any]] = None

    # 摘要生成配置
    summarizer_enabled: bool = True
    summarizer_config: Optional[Dict[str, Any]] = None

    # 高级功能配置
    enable_semantic_search: bool = True
    enable_timeline_analysis: bool = True
    enable_relationship_network: bool = True
    enable_consistency_checking: bool = True

    # 性能配置
    cache_ttl_seconds: int = 300
    batch_size: int = 50
    max_relationships_depth: int = 3


@dataclass
class TimelineEvent:
    """时间线事件"""

    timestamp: datetime
    entity_id: str
    entity_type: MemoryEntityType
    content_summary: str
    importance: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipNetwork:
    """关系网络"""

    central_entity_id: str
    nodes: Dict[str, Dict[str, Any]]  # entity_id -> node_data
    edges: List[Dict[str, Any]]  # 边数据
    depth: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedWorldMemory(WorldMemory):
    """增强世界记忆

    提供完整的世界记忆功能，包括：
    1. 结构化存储管理
    2. 向量存储集成
    3. 语义搜索和复杂查询
    4. 时间线分析和关系网络
    5. 记忆摘要生成
    """

    def __init__(self, session_id: str, config: Optional[Dict[str, Any]] = None):
        """初始化增强世界记忆

        Args:
            session_id: 会话ID
            config: 配置字典
        """
        super().__init__(session_id)
        self.session_id = session_id
        self.config = (
            EnhancedMemoryConfig(**config) if config else EnhancedMemoryConfig()
        )

        # 初始化存储组件
        self.structured_store = None
        self.vector_store = None
        self.summarizer = None

        self._initialize_components()

        # 缓存
        self.entity_cache: Dict[str, Tuple[MemoryEntity, datetime]] = {}
        self.query_cache: Dict[str, Tuple[List[MemoryEntity], datetime]] = {}

        logger.info(f"EnhancedWorldMemory initialized for session: {session_id}")

    def _initialize_components(self):
        """初始化组件"""
        # 结构化存储
        if self.config.structured_store_enabled:
            try:
                from .structured_store import StructuredStore

                self.structured_store = StructuredStore(self.config.db_path)
                logger.info("StructuredStore initialized")
            except ImportError as e:
                logger.error(f"Failed to initialize StructuredStore: {e}")
                self.config.structured_store_enabled = False

        # 向量存储
        if self.config.vector_store_enabled:
            try:
                vector_config = self.config.vector_store_config or {}
                self.vector_store = VectorMemoryStore(vector_config)
                logger.info("VectorMemoryStore initialized")
            except Exception as e:
                logger.error(f"Failed to initialize VectorMemoryStore: {e}")
                self.config.vector_store_enabled = False

        # 摘要生成器
        if self.config.summarizer_enabled:
            try:
                from ..interpretation.llm_provider import LLMProvider

                llm_provider = LLMProvider()  # 使用默认配置
                summarizer_config = self.config.summarizer_config or {}
                self.summarizer = MemorySummarizer(llm_provider, summarizer_config)
                logger.info("MemorySummarizer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize MemorySummarizer: {e}")
                self.config.summarizer_enabled = False

    async def store_entity(self, entity: MemoryEntity) -> str:
        """存储记忆实体

        Args:
            entity: 记忆实体

        Returns:
            实体ID

        Raises:
            StorageError: 存储失败
        """
        try:
            # 确保实体有会话ID
            if not entity.session_id:
                entity.session_id = self.session_id

            # 存储到结构化存储
            if self.config.structured_store_enabled and self.structured_store:
                entity_id = await self.structured_store.store_entity(entity)
            else:
                # 生成实体ID
                import uuid

                entity_id = str(uuid.uuid4())
                entity.id = entity_id

            # 存储到向量存储
            if (
                self.config.vector_store_enabled
                and self.vector_store
                and self.config.enable_semantic_search
            ):
                try:
                    await self.vector_store.store_entity_with_embedding(entity)
                except Exception as e:
                    logger.warning(f"Failed to store entity in vector store: {e}")

            # 更新缓存
            self._cache_entity(entity)

            logger.debug(f"Stored entity {entity_id} of type {entity.type.value}")
            return entity_id

        except Exception as e:
            logger.error(f"Failed to store entity: {e}")
            raise StorageError(f"Failed to store entity: {e}")

    async def retrieve_entity(self, entity_id: str) -> Optional[MemoryEntity]:
        """检索记忆实体

        Args:
            entity_id: 实体ID

        Returns:
            记忆实体，如果不存在则返回None
        """
        # 检查缓存
        cached_entity = self._get_cached_entity(entity_id)
        if cached_entity:
            return cached_entity

        try:
            # 从结构化存储检索
            if self.config.structured_store_enabled and self.structured_store:
                entity = await self.structured_store.retrieve_entity(entity_id)
                if entity:
                    self._cache_entity(entity)
                    return entity

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve entity {entity_id}: {e}")
            return None

    async def query_entities(self, query: MemoryQuery) -> List[MemoryEntity]:
        """查询记忆实体

        Args:
            query: 查询条件

        Returns:
            记忆实体列表
        """
        # 检查缓存
        cache_key = self._generate_query_cache_key(query)
        cached_result = self._get_cached_query(cache_key)
        if cached_result:
            return cached_result

        try:
            entities = []

            # 从结构化存储查询
            if self.config.structured_store_enabled and self.structured_store:
                entities = await self.structured_store.query_entities(query)

            # 缓存结果
            self._cache_query(cache_key, entities)

            return entities

        except Exception as e:
            logger.error(f"Failed to query entities: {e}")
            return []

    async def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆实体

        Args:
            entity_id: 实体ID
            updates: 更新内容

        Returns:
            是否成功更新
        """
        try:
            # 从存储中获取实体
            entity = await self.retrieve_entity(entity_id)
            if not entity:
                return False

            # 应用更新
            for key, value in updates.items():
                if key == "content" and isinstance(entity.content, dict):
                    entity.content.update(value)
                elif hasattr(entity, key):
                    setattr(entity, key, value)

            entity.updated_at = datetime.now()
            entity.version += 1

            # 更新结构化存储
            if self.config.structured_store_enabled and self.structured_store:
                success = await self.structured_store.update_entity(entity_id, updates)
                if not success:
                    return False

            # 更新向量存储
            if (
                self.config.vector_store_enabled
                and self.vector_store
                and self.config.enable_semantic_search
            ):
                try:
                    await self.vector_store.update_entity_embedding(entity)
                except Exception as e:
                    logger.warning(f"Failed to update entity in vector store: {e}")

            # 更新缓存
            self._cache_entity(entity)

            logger.debug(f"Updated entity {entity_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update entity {entity_id}: {e}")
            return False

    async def delete_entity(self, entity_id: str) -> bool:
        """删除记忆实体

        Args:
            entity_id: 实体ID

        Returns:
            是否成功删除
        """
        try:
            # 从结构化存储删除
            if self.config.structured_store_enabled and self.structured_store:
                success = await self.structured_store.delete_entity(entity_id)
                if not success:
                    return False

            # 从向量存储删除
            if self.config.vector_store_enabled and self.vector_store:
                try:
                    await self.vector_store.delete_entity(entity_id)
                except Exception as e:
                    logger.warning(f"Failed to delete entity from vector store: {e}")

            # 清除缓存
            self._remove_cached_entity(entity_id)

            logger.debug(f"Deleted entity {entity_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {e}")
            return False

    async def add_relation(self, relation: MemoryRelation) -> bool:
        """添加记忆关系

        Args:
            relation: 记忆关系

        Returns:
            是否成功添加
        """
        try:
            if self.config.structured_store_enabled and self.structured_store:
                return await self.structured_store.add_relation(relation)
            return False

        except Exception as e:
            logger.error(f"Failed to add relation: {e}")
            return False

    async def remove_relation(
        self, source_id: str, target_id: str, relation_type: MemoryRelationType
    ) -> bool:
        """移除记忆关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型

        Returns:
            是否成功移除
        """
        try:
            if self.config.structured_store_enabled and self.structured_store:
                return await self.structured_store.remove_relation(
                    source_id, target_id, relation_type
                )
            return False

        except Exception as e:
            logger.error(f"Failed to remove relation: {e}")
            return False

    async def get_related_entities(
        self, entity_id: str, relation_type: Optional[MemoryRelationType] = None
    ) -> List[MemoryEntity]:
        """获取相关实体

        Args:
            entity_id: 实体ID
            relation_type: 关系类型（如未指定则返回所有关系）

        Returns:
            相关实体列表
        """
        try:
            if self.config.structured_store_enabled and self.structured_store:
                return await self.structured_store.get_related_entities(
                    entity_id, relation_type
                )
            return []

        except Exception as e:
            logger.error(f"Failed to get related entities: {e}")
            return []

    async def summarize(
        self, session_id: str, time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> MemorySummary:
        """生成记忆摘要

        Args:
            session_id: 会话ID
            time_range: 时间范围

        Returns:
            记忆摘要
        """
        try:
            # 查询实体
            query = MemoryQuery(session_id=session_id, time_range=time_range)
            entities = await self.query_entities(query)

            if not entities:
                return MemorySummary(
                    entities_count=0,
                    relations_count=0,
                    by_type={},
                    recent_entities=[],
                    key_facts=[],
                    generated_at=datetime.now(),
                )

            # 使用摘要生成器
            if self.config.summarizer_enabled and self.summarizer:
                enhanced_summary = await self.summarizer.generate_summary(entities)
                if enhanced_summary:
                    # 转换为标准MemorySummary
                    return MemorySummary(
                        entities_count=len(entities),
                        relations_count=0,  # 需要从存储获取
                        by_type=self._count_entity_types(entities),
                        recent_entities=entities[-10:],  # 最近10个实体
                        key_facts=self._extract_key_facts(
                            enhanced_summary.summary_text
                        ),
                        generated_at=datetime.now(),
                    )

            # 回退到简单摘要
            return self._generate_simple_summary(entities)

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return MemorySummary(
                entities_count=0,
                relations_count=0,
                by_type={},
                recent_entities=[],
                key_facts=[],
                generated_at=datetime.now(),
            )

    async def rollback(self, session_id: str, to_version: int) -> bool:
        """回滚到指定版本

        Args:
            session_id: 会话ID
            to_version: 目标版本

        Returns:
            是否成功回滚
        """
        # 需要版本控制支持
        logger.warning("Rollback not implemented in EnhancedWorldMemory")
        return False

    async def cleanup(self, session_id: str, max_age_hours: int = 24) -> int:
        """清理旧记忆

        Args:
            session_id: 会话ID
            max_age_hours: 最大年龄（小时）

        Returns:
            清理的实体数量
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            # 查询旧实体
            query = MemoryQuery(
                session_id=session_id, time_range=(datetime.min, cutoff_time)
            )
            old_entities = await self.query_entities(query)

            # 删除旧实体
            deleted_count = 0
            for entity in old_entities:
                success = await self.delete_entity(entity.id)
                if success:
                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old entities")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old memories: {e}")
            return 0

    # 增强功能

    async def semantic_search(
        self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10
    ) -> List[MemoryEntity]:
        """语义搜索

        Args:
            query: 查询文本
            filters: 过滤条件
            limit: 返回数量限制

        Returns:
            相关实体列表
        """
        if (
            not self.config.enable_semantic_search
            or not self.config.vector_store_enabled
        ):
            logger.warning("Semantic search is disabled")
            return []

        try:
            # 使用向量存储进行语义搜索
            search_results = await self.vector_store.semantic_search(
                query, filters, limit
            )

            # 检索完整实体
            entities = []
            for entity_id, score in search_results:
                entity = await self.retrieve_entity(entity_id)
                if entity:
                    # 添加相似度分数到元数据
                    if not entity.metadata:
                        entity.metadata = {}
                    entity.metadata["similarity_score"] = score
                    entities.append(entity)

            # 按相似度排序
            entities.sort(
                key=lambda e: e.metadata.get("similarity_score", 0), reverse=True
            )

            logger.debug(
                f"Semantic search found {len(entities)} results for query: {query[:50]}..."
            )
            return entities[:limit]

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def get_timeline(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[TimelineEvent]:
        """获取时间线

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            时间线事件列表
        """
        if not self.config.enable_timeline_analysis:
            return []

        try:
            # 查询时间范围内的实体
            query = MemoryQuery(
                session_id=self.session_id,
                time_range=(start_time, end_time) if start_time or end_time else None,
            )
            entities = await self.query_entities(query)

            # 转换为时间线事件
            timeline_events = []
            for entity in entities:
                # 计算重要性（简化）
                importance = self._calculate_entity_importance(entity)

                event = TimelineEvent(
                    timestamp=entity.created_at,
                    entity_id=entity.id,
                    entity_type=entity.type,
                    content_summary=self._summarize_content(entity.content),
                    importance=importance,
                    metadata={"type": entity.type.value, "version": entity.version},
                )
                timeline_events.append(event)

            # 按时间排序
            timeline_events.sort(key=lambda e: e.timestamp)

            logger.debug(f"Generated timeline with {len(timeline_events)} events")
            return timeline_events

        except Exception as e:
            logger.error(f"Failed to generate timeline: {e}")
            return []

    async def get_relationship_network(
        self, entity_id: str, depth: int = 2
    ) -> RelationshipNetwork:
        """获取关系网络

        Args:
            entity_id: 中心实体ID
            depth: 关系深度

        Returns:
            关系网络
        """
        if not self.config.enable_relationship_network:
            return RelationshipNetwork(
                central_entity_id=entity_id, nodes={}, edges=[], depth=depth
            )

        try:
            # 限制深度
            depth = min(depth, self.config.max_relationships_depth)

            # 初始化网络
            network = RelationshipNetwork(
                central_entity_id=entity_id, nodes={}, edges=[], depth=depth
            )

            # 广度优先搜索
            await self._bfs_relationship_search(entity_id, depth, network)

            logger.debug(
                f"Generated relationship network with {len(network.nodes)} nodes and {len(network.edges)} edges"
            )
            return network

        except Exception as e:
            logger.error(f"Failed to generate relationship network: {e}")
            return RelationshipNetwork(
                central_entity_id=entity_id, nodes={}, edges=[], depth=depth
            )

    async def _bfs_relationship_search(
        self, start_entity_id: str, max_depth: int, network: RelationshipNetwork
    ):
        """广度优先搜索关系"""
        from collections import deque

        visited = set()
        queue = deque([(start_entity_id, 0)])  # (entity_id, depth)

        while queue:
            entity_id, current_depth = queue.popleft()

            if entity_id in visited or current_depth > max_depth:
                continue

            visited.add(entity_id)

            # 获取实体
            entity = await self.retrieve_entity(entity_id)
            if not entity:
                continue

            # 添加节点
            network.nodes[entity_id] = {
                "id": entity_id,
                "type": entity.type.value,
                "content_summary": self._summarize_content(entity.content),
                "depth": current_depth,
            }

            # 如果达到最大深度，停止探索
            if current_depth >= max_depth:
                continue

            # 获取相关实体
            related_entities = await self.get_related_entities(entity_id)

            for related_entity in related_entities:
                # 添加边
                edge = {
                    "source": entity_id,
                    "target": related_entity.id,
                    "depth": current_depth,
                    "metadata": {},
                }
                network.edges.append(edge)

                # 添加到队列
                if related_entity.id not in visited:
                    queue.append((related_entity.id, current_depth + 1))

    async def generate_enhanced_summary(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        summary_format: str = "text",
    ) -> Optional[EnhancedMemorySummary]:
        """生成增强摘要

        Args:
            time_range: 时间范围
            summary_format: 摘要格式

        Returns:
            增强记忆摘要
        """
        if not self.config.summarizer_enabled or not self.summarizer:
            logger.warning("Summarizer is disabled")
            return None

        try:
            # 查询实体
            query = MemoryQuery(session_id=self.session_id, time_range=time_range)
            entities = await self.query_entities(query)

            if not entities:
                return None

            # 生成摘要
            summary = await self.summarizer.generate_summary(entities)
            return summary

        except Exception as e:
            logger.error(f"Failed to generate enhanced summary: {e}")
            return None

    async def search_hybrid(
        self,
        query: str,
        keyword_filters: Optional[Dict[str, Any]] = None,
        semantic_limit: int = 5,
        keyword_limit: int = 5,
    ) -> List[MemoryEntity]:
        """混合搜索（语义+关键词）

        Args:
            query: 查询文本
            keyword_filters: 关键词过滤条件
            semantic_limit: 语义搜索结果数量
            keyword_limit: 关键词搜索结果数量

        Returns:
            搜索结果实体列表
        """
        try:
            results = []

            # 语义搜索
            if self.config.enable_semantic_search and self.config.vector_store_enabled:
                semantic_results = await self.semantic_search(
                    query, limit=semantic_limit
                )
                results.extend(semantic_results)

            # 关键词搜索
            if keyword_filters:
                keyword_query = MemoryQuery(
                    session_id=self.session_id,
                    keywords=[query] if query else None,
                    **keyword_filters,
                )
                keyword_results = await self.query_entities(keyword_query)
                results.extend(keyword_results[:keyword_limit])

            # 去重
            unique_results = []
            seen_ids = set()
            for entity in results:
                if entity.id not in seen_ids:
                    seen_ids.add(entity.id)
                    unique_results.append(entity)

            return unique_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def sync_vector_store(self):
        """同步向量存储"""
        if not self.config.vector_store_enabled or not self.vector_store:
            return False

        try:
            # 获取所有实体
            query = MemoryQuery(session_id=self.session_id)
            entities = await self.query_entities(query)

            # 批量存储到向量存储
            success_count = 0
            for entity in entities:
                try:
                    await self.vector_store.store_entity_with_embedding(entity)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to sync entity {entity.id}: {e}")

            logger.info(
                f"Synced {success_count}/{len(entities)} entities to vector store"
            )
            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to sync vector store: {e}")
            return False

    # 辅助方法

    def _cache_entity(self, entity: MemoryEntity):
        """缓存实体"""
        cache_key = f"entity:{entity.id}"
        self.entity_cache[cache_key] = (entity, datetime.now())

        # 清理过期缓存
        self._cleanup_cache()

    def _get_cached_entity(self, entity_id: str) -> Optional[MemoryEntity]:
        """获取缓存的实体"""
        cache_key = f"entity:{entity_id}"
        if cache_key in self.entity_cache:
            entity, timestamp = self.entity_cache[cache_key]
            if datetime.now() - timestamp < timedelta(
                seconds=self.config.cache_ttl_seconds
            ):
                return entity
            else:
                del self.entity_cache[cache_key]
        return None

    def _remove_cached_entity(self, entity_id: str):
        """移除缓存的实体"""
        cache_key = f"entity:{entity_id}"
        if cache_key in self.entity_cache:
            del self.entity_cache[cache_key]

    def _generate_query_cache_key(self, query: MemoryQuery) -> str:
        """生成查询缓存键"""
        import hashlib

        query_dict = {
            "session_id": query.session_id,
            "entity_types": (
                [t.value for t in query.entity_types] if query.entity_types else []
            ),
            "keywords": query.keywords or [],
            "time_range": query.time_range,
            "limit": query.limit,
            "offset": query.offset,
        }
        query_str = json.dumps(query_dict, sort_keys=True, default=str)
        return hashlib.md5(query_str.encode()).hexdigest()

    def _cache_query(self, cache_key: str, entities: List[MemoryEntity]):
        """缓存查询结果"""
        self.query_cache[cache_key] = (entities, datetime.now())

        # 清理过期缓存
        self._cleanup_cache()

    def _get_cached_query(self, cache_key: str) -> Optional[List[MemoryEntity]]:
        """获取缓存的查询结果"""
        if cache_key in self.query_cache:
            entities, timestamp = self.query_cache[cache_key]
            if datetime.now() - timestamp < timedelta(
                seconds=self.config.cache_ttl_seconds
            ):
                return entities
            else:
                del self.query_cache[cache_key]
        return None

    def _cleanup_cache(self):
        """清理过期缓存"""
        now = datetime.now()
        ttl = timedelta(seconds=self.config.cache_ttl_seconds)

        # 清理实体缓存
        expired_entities = [
            key
            for key, (_, timestamp) in self.entity_cache.items()
            if now - timestamp > ttl
        ]
        for key in expired_entities:
            del self.entity_cache[key]

        # 清理查询缓存
        expired_queries = [
            key
            for key, (_, timestamp) in self.query_cache.items()
            if now - timestamp > ttl
        ]
        for key in expired_queries:
            del self.query_cache[key]

        if expired_entities or expired_queries:
            logger.debug(
                f"Cleaned up {len(expired_entities)} entity caches and {len(expired_queries)} query caches"
            )

    def _calculate_entity_importance(self, entity: MemoryEntity) -> float:
        """计算实体重要性（简化）"""
        # 基于类型的重要性
        type_importance = {
            MemoryEntityType.CHARACTER: 0.8,
            MemoryEntityType.EVENT: 0.7,
            MemoryEntityType.FACT: 0.6,
            MemoryEntityType.LOCATION: 0.5,
            MemoryEntityType.PLOTLINE: 0.9,
            MemoryEntityType.OBJECT: 0.4,
            MemoryEntityType.CONCEPT: 0.5,
            MemoryEntityType.STYLE: 0.3,
        }

        importance = type_importance.get(entity.type, 0.5)

        # 基于元数据调整
        if entity.metadata and "importance" in entity.metadata:
            try:
                metadata_importance = float(entity.metadata["importance"])
                importance = (importance + metadata_importance) / 2
            except:
                pass

        return importance

    def _summarize_content(self, content: Any) -> str:
        """摘要内容"""
        if isinstance(content, str):
            if len(content) > 100:
                return content[:100] + "..."
            return content
        elif isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False)[:100] + "..."
        else:
            return str(content)[:100] + "..."

    def _count_entity_types(self, entities: List[MemoryEntity]) -> Dict[str, int]:
        """统计实体类型"""
        type_counts = {}
        for entity in entities:
            entity_type = entity.type.value
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts

    def _extract_key_facts(self, summary_text: str) -> List[str]:
        """提取关键事实（简化）"""
        # 简单实现：按句子分割
        import re

        sentences = re.split(r"[.!?]+", summary_text)
        key_facts = [s.strip() for s in sentences if len(s.strip()) > 10]
        return key_facts[:5]  # 返回前5个关键事实

    def _generate_simple_summary(self, entities: List[MemoryEntity]) -> MemorySummary:
        """生成简单摘要"""
        type_counts = self._count_entity_types(entities)

        return MemorySummary(
            entities_count=len(entities),
            relations_count=0,
            by_type=type_counts,
            recent_entities=entities[-10:] if len(entities) > 10 else entities,
            key_facts=self._extract_key_facts_from_entities(entities),
            generated_at=datetime.now(),
        )

    def _extract_key_facts_from_entities(
        self, entities: List[MemoryEntity]
    ) -> List[str]:
        """从实体中提取关键事实"""
        key_facts = []

        # 提取重要实体
        important_entities = []
        for entity in entities:
            importance = self._calculate_entity_importance(entity)
            if importance > 0.7:  # 重要性阈值
                important_entities.append((entity, importance))

        # 按重要性排序
        important_entities.sort(key=lambda x: x[1], reverse=True)

        # 生成关键事实
        for entity, _ in important_entities[:5]:  # 前5个重要实体
            fact = f"{entity.type.value}: {self._summarize_content(entity.content)}"
            key_facts.append(fact)

        return key_facts

    async def close(self):
        """关闭资源"""
        # 清理缓存
        self.entity_cache.clear()
        self.query_cache.clear()

        logger.info(f"EnhancedWorldMemory closed for session: {self.session_id}")
