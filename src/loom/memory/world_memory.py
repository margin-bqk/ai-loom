"""
世界记忆管理

管理结构化叙事状态存储，包括实体和关系。
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MemoryEntityType(Enum):
    """记忆实体类型"""

    CHARACTER = "character"  # 角色
    LOCATION = "location"  # 地点
    FACT = "fact"  # 事实
    PLOTLINE = "plotline"  # 剧情线
    STYLE = "style"  # 风格
    EVENT = "event"  # 事件
    OBJECT = "object"  # 物体
    CONCEPT = "concept"  # 概念


class MemoryRelationType(Enum):
    """记忆关系类型"""

    PART_OF = "part_of"  # 属于
    CAUSED_BY = "caused_by"  # 由...引起
    LOCATED_AT = "located_at"  # 位于
    RELATED_TO = "related_to"  # 相关
    OWNS = "owns"  # 拥有
    KNOWS = "knows"  # 认识
    INVOLVES = "involves"  # 涉及
    PRECEDES = "precedes"  # 先于


@dataclass
class MemoryEntity:
    """记忆实体"""

    id: str
    session_id: str
    type: MemoryEntityType
    content: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "type": self.type.value,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntity":
        """从字典创建"""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            type=MemoryEntityType(data["type"]),
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemoryRelation:
    """记忆关系"""

    source_id: str
    target_id: str
    relation_type: MemoryRelationType
    strength: float = 1.0  # 关系强度 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "strength": self.strength,
            "metadata": self.metadata,
        }


class WorldMemory:
    """世界记忆管理器"""

    def __init__(
        self,
        session_id: str,
        structured_store=None,
        vector_store=None,
        enable_cache: bool = True,
        cache_size: int = 1000,
    ):
        self.session_id = session_id
        self.structured_store = structured_store
        self.vector_store = vector_store
        self.enable_cache = enable_cache
        self.cache_size = cache_size

        # 内存缓存
        self.entities: Dict[str, MemoryEntity] = {}
        self.relations: List[MemoryRelation] = []

        # LRU缓存实现
        self.entity_cache_order = []  # 最近使用的实体ID列表
        self.entity_cache_hits = {}  # 缓存命中统计
        self.entity_cache_misses = {}  # 缓存未命中统计

        # 缓存统计
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}

        logger.info(
            f"WorldMemory initialized for session {session_id}, cache={'enabled' if enable_cache else 'disabled'}"
        )

    async def store_entity(self, entity: MemoryEntity) -> bool:
        """存储实体"""
        # 更新时间戳
        entity.updated_at = datetime.now()

        # 存储到内存缓存
        self.entities[entity.id] = entity
        self._update_cache_order(entity.id)

        # 存储到结构化存储
        if self.structured_store:
            success = await self.structured_store.store_entity(entity)
            if not success:
                logger.warning(
                    f"Failed to store entity {entity.id} in structured store"
                )

        # 存储到向量存储
        if self.vector_store and entity.type in [
            MemoryEntityType.FACT,
            MemoryEntityType.EVENT,
        ]:
            success = await self.vector_store.store_entity(entity)
            if not success:
                logger.debug(
                    f"Entity {entity.id} not stored in vector store (type: {entity.type})"
                )

        logger.debug(f"Stored entity {entity.id} ({entity.type.value})")
        return True

    async def warmup_cache(
        self, entity_types: Optional[List[MemoryEntityType]] = None, limit: int = 100
    ):
        """预热缓存"""
        if not self.structured_store:
            logger.warning("Cannot warmup cache: no structured store available")
            return

        try:
            # 获取所有实体类型
            if entity_types is None:
                entity_types = list(MemoryEntityType)

            total_loaded = 0
            for entity_type in entity_types:
                entities = await self.structured_store.retrieve_entities_by_type(
                    self.session_id, entity_type, limit
                )

                for entity in entities:
                    if entity.id not in self.entities:
                        self.entities[entity.id] = entity
                        self._update_cache_order(entity.id)
                        total_loaded += 1

            logger.info(f"Cache warmup completed: loaded {total_loaded} entities")

        except Exception as e:
            logger.error(f"Failed to warmup cache: {e}")

    def _update_cache_order(self, entity_id: str):
        """更新缓存顺序（LRU）"""
        if entity_id in self.entity_cache_order:
            self.entity_cache_order.remove(entity_id)
        self.entity_cache_order.append(entity_id)

        # 如果超过缓存大小，移除最旧的
        if len(self.entity_cache_order) > self.cache_size:
            evicted_id = self.entity_cache_order.pop(0)
            if evicted_id in self.entities:
                del self.entities[evicted_id]
            self.cache_stats["evictions"] += 1

    def _record_cache_hit(self, entity_id: str):
        """记录缓存命中"""
        self.cache_stats["hits"] += 1
        self.entity_cache_hits[entity_id] = self.entity_cache_hits.get(entity_id, 0) + 1
        self._update_cache_order(entity_id)

    def _record_cache_miss(self, entity_id: str):
        """记录缓存未命中"""
        self.cache_stats["misses"] += 1
        self.entity_cache_misses[entity_id] = (
            self.entity_cache_misses.get(entity_id, 0) + 1
        )

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total if total > 0 else 0

        return {
            **self.cache_stats,
            "total_requests": total,
            "hit_rate": hit_rate,
            "cache_size": len(self.entities),
            "max_cache_size": self.cache_size,
            "top_hits": dict(
                sorted(
                    self.entity_cache_hits.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ),
            "top_misses": dict(
                sorted(
                    self.entity_cache_misses.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ),
        }

    def clear_cache(self):
        """清空缓存"""
        self.entities.clear()
        self.entity_cache_order.clear()
        self.entity_cache_hits.clear()
        self.entity_cache_misses.clear()
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        logger.info("WorldMemory cache cleared")

    async def retrieve_entity(self, entity_id: str) -> Optional[MemoryEntity]:
        """检索实体"""
        # 检查内存缓存
        if entity_id in self.entities:
            self._record_cache_hit(entity_id)
            return self.entities[entity_id]

        self._record_cache_miss(entity_id)

        # 从结构化存储检索
        if self.structured_store:
            entity = await self.structured_store.retrieve_entity(entity_id)
            if entity:
                # 添加到缓存
                self.entities[entity_id] = entity
                self._update_cache_order(entity_id)
                return entity

        return None

    async def retrieve_entities_by_type(
        self, entity_type: MemoryEntityType, limit: int = 100
    ) -> List[MemoryEntity]:
        """按类型检索实体"""
        # 首先检查内存
        entities = [e for e in self.entities.values() if e.type == entity_type]

        if len(entities) >= limit:
            return entities[:limit]

        # 从结构化存储获取更多
        if self.structured_store:
            more_entities = await self.structured_store.retrieve_entities_by_type(
                self.session_id, entity_type, limit - len(entities)
            )
            for entity in more_entities:
                if entity.id not in self.entities:
                    self.entities[entity.id] = entity
                    entities.append(entity)

        return entities[:limit]

    async def search_entities(
        self, query: str, filters: Optional[Dict] = None, limit: int = 10
    ) -> List[MemoryEntity]:
        """搜索实体"""
        results = []

        # 使用向量存储进行语义搜索
        if self.vector_store:
            vector_results = await self.vector_store.search(query, limit)
            for entity_id, score in vector_results:
                entity = await self.retrieve_entity(entity_id)
                if entity:
                    results.append((entity, score))

        # 如果没有向量存储或结果不足，使用关键词搜索
        if not results and self.structured_store:
            keyword_results = await self.structured_store.search_entities(
                query, filters, limit
            )
            for entity in keyword_results:
                results.append((entity, 0.5))  # 默认分数

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)

        # 返回实体列表
        return [entity for entity, score in results[:limit]]

    async def add_relation(self, relation: MemoryRelation) -> bool:
        """添加关系"""
        # 验证实体存在
        source_exists = await self.retrieve_entity(relation.source_id)
        target_exists = await self.retrieve_entity(relation.target_id)

        if not source_exists or not target_exists:
            logger.warning(
                f"Cannot add relation: entities not found ({relation.source_id} -> {relation.target_id})"
            )
            return False

        # 添加关系
        self.relations.append(relation)

        # 存储到结构化存储
        if self.structured_store:
            success = await self.structured_store.store_relation(relation)
            if not success:
                logger.warning(f"Failed to store relation in structured store")

        logger.debug(
            f"Added relation {relation.source_id} -[{relation.relation_type.value}]-> {relation.target_id}"
        )
        return True

    async def get_related_entities(
        self, entity_id: str, relation_type: Optional[MemoryRelationType] = None
    ) -> List[MemoryEntity]:
        """获取相关实体"""
        related_ids = []

        for relation in self.relations:
            if relation.source_id == entity_id:
                if relation_type is None or relation.relation_type == relation_type:
                    related_ids.append(relation.target_id)
            elif relation.target_id == entity_id:
                if relation_type is None or relation.relation_type == relation_type:
                    related_ids.append(relation.source_id)

        # 检索实体
        entities = []
        for related_id in related_ids:
            entity = await self.retrieve_entity(related_id)
            if entity:
                entities.append(entity)

        return entities

    async def update_entity(
        self, entity_id: str, updates: Dict[str, Any]
    ) -> Optional[MemoryEntity]:
        """更新实体"""
        entity = await self.retrieve_entity(entity_id)
        if not entity:
            return None

        # 创建新版本
        new_entity = MemoryEntity(
            id=entity.id,
            session_id=entity.session_id,
            type=entity.type,
            content={**entity.content, **updates},
            created_at=entity.created_at,
            updated_at=datetime.now(),
            version=entity.version + 1,
            metadata=entity.metadata,
        )

        # 存储更新
        await self.store_entity(new_entity)

        logger.info(f"Updated entity {entity_id} to version {new_entity.version}")
        return new_entity

    async def delete_entity(self, entity_id: str) -> bool:
        """删除实体"""
        if entity_id in self.entities:
            del self.entities[entity_id]

        # 删除相关关系
        self.relations = [
            r
            for r in self.relations
            if r.source_id != entity_id and r.target_id != entity_id
        ]

        # 从存储中删除
        if self.structured_store:
            success = await self.structured_store.delete_entity(entity_id)
            if not success:
                logger.warning(
                    f"Failed to delete entity {entity_id} from structured store"
                )

        if self.vector_store:
            success = await self.vector_store.delete_entity(entity_id)
            if not success:
                logger.debug(f"Failed to delete entity {entity_id} from vector store")

        logger.info(f"Deleted entity {entity_id}")
        return True

    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        stats = {
            "session_id": self.session_id,
            "entities_in_memory": len(self.entities),
            "relations_in_memory": len(self.relations),
            "entity_types": {},
            "relation_types": {},
            "cache_enabled": self.enable_cache,
            "cache_size": len(self.entities),
            "max_cache_size": self.cache_size,
        }

        # 添加缓存统计
        if self.enable_cache:
            cache_stats = self.get_cache_stats()
            stats["cache_stats"] = {
                "hits": cache_stats["hits"],
                "misses": cache_stats["misses"],
                "hit_rate": cache_stats["hit_rate"],
                "evictions": cache_stats["evictions"],
            }

        # 统计实体类型
        for entity in self.entities.values():
            entity_type = entity.type.value
            stats["entity_types"][entity_type] = (
                stats["entity_types"].get(entity_type, 0) + 1
            )

        # 统计关系类型
        for relation in self.relations:
            rel_type = relation.relation_type.value
            stats["relation_types"][rel_type] = (
                stats["relation_types"].get(rel_type, 0) + 1
            )

        return stats

    async def export_memory(self) -> Dict[str, Any]:
        """导出记忆"""
        entities_data = [entity.to_dict() for entity in self.entities.values()]
        relations_data = [relation.to_dict() for relation in self.relations]

        return {
            "session_id": self.session_id,
            "exported_at": datetime.now().isoformat(),
            "entities": entities_data,
            "relations": relations_data,
            "stats": await self.get_memory_stats(),
        }

    async def import_memory(self, data: Dict[str, Any]) -> bool:
        """导入记忆"""
        try:
            # 导入实体
            for entity_data in data.get("entities", []):
                entity = MemoryEntity.from_dict(entity_data)
                await self.store_entity(entity)

            # 导入关系
            for relation_data in data.get("relations", []):
                relation = MemoryRelation(
                    source_id=relation_data["source_id"],
                    target_id=relation_data["target_id"],
                    relation_type=MemoryRelationType(relation_data["relation_type"]),
                    strength=relation_data.get("strength", 1.0),
                    metadata=relation_data.get("metadata", {}),
                )
                await self.add_relation(relation)

            logger.info(
                f"Imported memory with {len(data.get('entities', []))} entities and {len(data.get('relations', []))} relations"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to import memory: {e}")
            return False

    async def store_entities_batch(self, entities: List[MemoryEntity]) -> List[bool]:
        """批量存储实体"""
        results = []
        for entity in entities:
            success = await self.store_entity(entity)
            results.append(success)

        logger.info(f"Batch stored {len(entities)} entities, {sum(results)} successful")
        return results

    async def retrieve_entities_batch(
        self, entity_ids: List[str]
    ) -> Dict[str, Optional[MemoryEntity]]:
        """批量检索实体"""
        results = {}
        for entity_id in entity_ids:
            entity = await self.retrieve_entity(entity_id)
            results[entity_id] = entity

        logger.debug(
            f"Batch retrieved {len(entity_ids)} entities, {sum(1 for e in results.values() if e is not None)} found"
        )
        return results

    async def update_entities_batch(
        self, updates: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Optional[MemoryEntity]]:
        """批量更新实体"""
        results = {}
        for entity_id, entity_updates in updates.items():
            updated_entity = await self.update_entity(entity_id, entity_updates)
            results[entity_id] = updated_entity

        logger.info(f"Batch updated {len(updates)} entities")
        return results

    async def delete_entities_batch(self, entity_ids: List[str]) -> List[bool]:
        """批量删除实体"""
        results = []
        for entity_id in entity_ids:
            success = await self.delete_entity(entity_id)
            results.append(success)

        logger.info(
            f"Batch deleted {len(entity_ids)} entities, {sum(results)} successful"
        )
        return results

    async def add_relations_batch(self, relations: List[MemoryRelation]) -> List[bool]:
        """批量添加关系"""
        results = []
        for relation in relations:
            success = await self.add_relation(relation)
            results.append(success)

        logger.info(
            f"Batch added {len(relations)} relations, {sum(results)} successful"
        )
        return results

    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务操作"""
        # 简化的事务实现：按顺序执行操作，失败时回滚
        executed_operations = []

        try:
            for op in operations:
                op_type = op.get("type")

                if op_type == "store_entity":
                    entity = op["entity"]
                    success = await self.store_entity(entity)
                    if not success:
                        raise Exception(f"Failed to store entity {entity.id}")
                    executed_operations.append(("store_entity", entity.id))

                elif op_type == "update_entity":
                    entity_id = op["entity_id"]
                    updates = op["updates"]
                    entity = await self.update_entity(entity_id, updates)
                    if not entity:
                        raise Exception(f"Failed to update entity {entity_id}")
                    executed_operations.append(("update_entity", entity_id))

                elif op_type == "delete_entity":
                    entity_id = op["entity_id"]
                    success = await self.delete_entity(entity_id)
                    if not success:
                        raise Exception(f"Failed to delete entity {entity_id}")
                    executed_operations.append(("delete_entity", entity_id))

                elif op_type == "add_relation":
                    relation = op["relation"]
                    success = await self.add_relation(relation)
                    if not success:
                        raise Exception(
                            f"Failed to add relation {relation.source_id}->{relation.target_id}"
                        )
                    executed_operations.append(
                        ("add_relation", f"{relation.source_id}->{relation.target_id}")
                    )

                else:
                    raise Exception(f"Unknown operation type: {op_type}")

            logger.info(
                f"Transaction completed successfully with {len(operations)} operations"
            )
            return True

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            # 简化回滚：记录错误但不实际回滚
            # 在实际实现中，这里应该回滚已执行的操作
            logger.warning(
                f"Transaction rollback would be needed for {len(executed_operations)} operations"
            )
            return False

    async def get_contextual_memories(
        self, query: str, context_entities: List[str] = None, limit: int = 10
    ) -> List[MemoryEntity]:
        """获取上下文相关记忆"""
        results = []

        # 使用向量存储进行语义搜索
        if self.vector_store:
            vector_results = await self.vector_store.search(query, limit * 2)
            for entity_id, score in vector_results:
                entity = await self.retrieve_entity(entity_id)
                if entity:
                    results.append((entity, score))

        # 如果没有向量存储或结果不足，使用关键词搜索
        if len(results) < limit and self.structured_store:
            keyword_results = await self.structured_store.search_entities(
                query, None, limit * 2
            )
            for entity in keyword_results:
                results.append((entity, 0.3))  # 较低的基础分数

        # 如果有上下文实体，提升相关实体的分数
        if context_entities:
            for i, (entity, score) in enumerate(results):
                if entity.id in context_entities:
                    # 提升上下文相关实体的分数
                    results[i] = (entity, score * 1.5)

        # 按分数排序并返回
        results.sort(key=lambda x: x[1], reverse=True)
        return [entity for entity, score in results[:limit]]

    async def create_fact(self, fact_data: Dict[str, Any]) -> str:
        """创建事实"""
        if not self.structured_store:
            logger.error("Structured store required for fact creation")
            return None

        try:
            fact_id = await self.structured_store.store_fact(fact_data)
            logger.info(f"Created fact {fact_id}")
            return fact_id
        except Exception as e:
            logger.error(f"Failed to create fact: {e}")
            return None

    async def get_facts(
        self, filters: Optional[Dict] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取事实"""
        if not self.structured_store:
            return []

        try:
            facts = await self.structured_store.retrieve_facts(
                self.session_id, filters, limit
            )
            return facts
        except Exception as e:
            logger.error(f"Failed to get facts: {e}")
            return []

    async def create_plotline(self, plotline_data: Dict[str, Any]) -> str:
        """创建剧情线"""
        if not self.structured_store:
            logger.error("Structured store required for plotline creation")
            return None

        try:
            plotline_id = await self.structured_store.create_plotline(plotline_data)
            logger.info(f"Created plotline {plotline_id}")
            return plotline_id
        except Exception as e:
            logger.error(f"Failed to create plotline: {e}")
            return None

    async def get_plotlines(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取剧情线"""
        if not self.structured_store:
            return []

        try:
            plotlines = await self.structured_store.get_plotlines(
                self.session_id, status
            )
            return plotlines
        except Exception as e:
            logger.error(f"Failed to get plotlines: {e}")
            return []

    async def update_plotline(self, plotline_id: str, updates: Dict[str, Any]) -> bool:
        """更新剧情线"""
        if not self.structured_store:
            return False

        try:
            success = await self.structured_store.update_plotline(plotline_id, updates)
            if success:
                logger.info(f"Updated plotline {plotline_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update plotline: {e}")
            return False

    async def sync_with_persistence(self, persistence_engine):
        """与持久化引擎同步"""
        try:
            # 导出当前记忆
            memory_data = await self.export_memory()

            # 存储到持久化引擎
            success = await persistence_engine.save_memory(self.session_id, memory_data)

            if success:
                logger.info(
                    f"Synced memory to persistence engine for session {self.session_id}"
                )
            else:
                logger.warning(f"Failed to sync memory to persistence engine")

            return success

        except Exception as e:
            logger.error(f"Failed to sync with persistence engine: {e}")
            return False

    async def load_from_persistence(self, persistence_engine):
        """从持久化引擎加载"""
        try:
            # 从持久化引擎加载记忆
            memory_data = await persistence_engine.load_memory(self.session_id)

            if memory_data:
                success = await self.import_memory(memory_data)
                if success:
                    logger.info(
                        f"Loaded memory from persistence engine for session {self.session_id}"
                    )
                return success
            else:
                logger.info(
                    f"No memory found in persistence engine for session {self.session_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to load from persistence engine: {e}")
            return False
