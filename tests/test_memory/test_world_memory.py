"""
世界记忆系统单元测试
测试WorldMemory、StructuredStore、VectorStore和Summarizer
"""

import pytest
import asyncio
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from loom.memory.world_memory import (
    WorldMemory,
    MemoryEntity,
    MemoryEntityType,
    MemoryRelation,
    MemoryRelationType,
)
from loom.memory.structured_store import StructuredStore
from loom.memory.vector_store import VectorStore
from loom.memory.summarizer import MemorySummarizer, SummaryConfig


@pytest.fixture
def temp_db_path():
    """创建临时数据库路径"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_memory.db")
    yield db_path
    # 清理
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_entity():
    """创建示例实体"""
    return MemoryEntity(
        id="test-entity-1",
        session_id="test-session",
        type=MemoryEntityType.CHARACTER,
        content={"name": "测试角色", "description": "一个测试角色"},
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_relation(sample_entity):
    """创建示例关系"""
    return MemoryRelation(
        source_id=sample_entity.id,
        target_id="test-entity-2",
        relation_type=MemoryRelationType.KNOWS,
        strength=0.8,
    )


class TestWorldMemory:
    """WorldMemory单元测试"""

    @pytest.mark.asyncio
    async def test_world_memory_initialization(self):
        """测试WorldMemory初始化"""
        memory = WorldMemory(session_id="test-session")
        assert memory.session_id == "test-session"
        assert memory.entities == {}
        assert memory.relations == []

    @pytest.mark.asyncio
    async def test_store_and_retrieve_entity(self, sample_entity):
        """测试存储和检索实体"""
        memory = WorldMemory(session_id="test-session")

        # 存储实体
        success = await memory.store_entity(sample_entity)
        assert success is True

        # 检索实体
        retrieved = await memory.retrieve_entity(sample_entity.id)
        assert retrieved is not None
        assert retrieved.id == sample_entity.id
        assert retrieved.type == sample_entity.type
        assert retrieved.content == sample_entity.content

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_entity(self):
        """测试检索不存在的实体"""
        memory = WorldMemory(session_id="test-session")
        retrieved = await memory.retrieve_entity("nonexistent-id")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_add_and_get_relations(self, sample_entity, sample_relation):
        """测试添加和获取关系"""
        memory = WorldMemory(session_id="test-session")

        # 先存储源实体
        await memory.store_entity(sample_entity)

        # 创建并存储目标实体
        target_entity = MemoryEntity(
            id="test-entity-2",
            session_id="test-session",
            type=MemoryEntityType.CHARACTER,
            content={"name": "目标角色", "description": "关系目标角色"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await memory.store_entity(target_entity)

        # 添加关系
        success = await memory.add_relation(sample_relation)
        assert success is True

        # 获取相关实体
        related = await memory.get_related_entities(sample_entity.id)
        assert len(related) == 1  # 现在应该有一个相关实体
        assert related[0].id == "test-entity-2"

    @pytest.mark.asyncio
    async def test_update_entity(self, sample_entity):
        """测试更新实体"""
        memory = WorldMemory(session_id="test-session")

        # 存储实体
        await memory.store_entity(sample_entity)

        # 更新实体
        updates = {"description": "更新后的描述", "age": 25}
        updated = await memory.update_entity(sample_entity.id, updates)

        assert updated is not None
        assert updated.version == 2
        assert updated.content["description"] == "更新后的描述"
        assert updated.content["age"] == 25
        assert updated.content["name"] == "测试角色"  # 原有字段应保留

    @pytest.mark.asyncio
    async def test_delete_entity(self, sample_entity):
        """测试删除实体"""
        memory = WorldMemory(session_id="test-session")

        # 存储实体
        await memory.store_entity(sample_entity)

        # 确认实体存在
        assert sample_entity.id in memory.entities

        # 删除实体
        success = await memory.delete_entity(sample_entity.id)
        assert success is True

        # 确认实体已删除
        assert sample_entity.id not in memory.entities

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, sample_entity):
        """测试获取记忆统计"""
        memory = WorldMemory(session_id="test-session")

        # 存储一些实体
        await memory.store_entity(sample_entity)

        # 获取统计
        stats = await memory.get_memory_stats()

        assert stats["session_id"] == "test-session"
        assert stats["entities_in_memory"] == 1
        assert stats["relations_in_memory"] == 0
        assert "character" in stats["entity_types"]
        assert stats["entity_types"]["character"] == 1

    @pytest.mark.asyncio
    async def test_export_and_import_memory(self, sample_entity, sample_relation):
        """测试导出和导入记忆"""
        memory1 = WorldMemory(session_id="test-session")

        # 存储源实体
        await memory1.store_entity(sample_entity)

        # 创建并存储目标实体
        target_entity = MemoryEntity(
            id="test-entity-2",
            session_id="test-session",
            type=MemoryEntityType.CHARACTER,
            content={"name": "目标角色", "description": "关系目标角色"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await memory1.store_entity(target_entity)

        # 添加关系
        await memory1.add_relation(sample_relation)

        # 导出记忆
        exported = await memory1.export_memory()

        assert exported["session_id"] == "test-session"
        assert len(exported["entities"]) == 2
        assert len(exported["relations"]) == 1

        # 创建新内存并导入
        memory2 = WorldMemory(session_id="test-session")
        success = await memory2.import_memory(exported)

        assert success is True
        assert len(memory2.entities) == 2
        assert len(memory2.relations) == 1

    @pytest.mark.asyncio
    async def test_batch_operations(self):
        """测试批量操作"""
        memory = WorldMemory(session_id="test-session")

        # 创建多个实体
        entities = []
        for i in range(5):
            entity = MemoryEntity(
                id=f"batch-entity-{i}",
                session_id="test-session",
                type=MemoryEntityType.CHARACTER,
                content={"name": f"角色{i}"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            entities.append(entity)

        # 批量存储
        results = await memory.store_entities_batch(entities)
        assert len(results) == 5
        assert all(results)

        # 批量检索
        entity_ids = [e.id for e in entities]
        retrieved = await memory.retrieve_entities_batch(entity_ids)

        assert len(retrieved) == 5
        for entity_id in entity_ids:
            assert entity_id in retrieved
            assert retrieved[entity_id] is not None

    @pytest.mark.asyncio
    async def test_transaction_operations(self, sample_entity):
        """测试事务操作"""
        memory = WorldMemory(session_id="test-session")

        operations = [
            {"type": "store_entity", "entity": sample_entity},
            {
                "type": "update_entity",
                "entity_id": sample_entity.id,
                "updates": {"description": "在事务中更新"},
            },
        ]

        success = await memory.execute_transaction(operations)
        assert success is True

        # 验证实体已更新
        retrieved = await memory.retrieve_entity(sample_entity.id)
        assert retrieved is not None
        assert retrieved.content["description"] == "在事务中更新"


class TestStructuredStore:
    """StructuredStore单元测试"""

    @pytest.mark.asyncio
    async def test_structured_store_initialization(self, temp_db_path):
        """测试StructuredStore初始化"""
        store = StructuredStore(db_path=temp_db_path)
        # 比较路径字符串（WindowsPath和字符串可能不直接相等）
        assert str(store.db_path) == str(temp_db_path)

        # 等待表创建完成
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_store_and_retrieve_entity(self, temp_db_path, sample_entity):
        """测试存储和检索实体"""
        store = StructuredStore(db_path=temp_db_path)
        await asyncio.sleep(0.1)

        # 存储实体
        success = await store.store_entity(sample_entity)
        assert success is True

        # 检索实体
        retrieved = await store.retrieve_entity(sample_entity.id)
        assert retrieved is not None
        assert retrieved.id == sample_entity.id
        assert retrieved.type == sample_entity.type

    @pytest.mark.asyncio
    async def test_retrieve_entities_by_type(self, temp_db_path):
        """测试按类型检索实体"""
        store = StructuredStore(db_path=temp_db_path)
        await asyncio.sleep(0.1)

        # 创建多个不同类型的实体
        character_entity = MemoryEntity(
            id="char-1",
            session_id="test-session",
            type=MemoryEntityType.CHARACTER,
            content={"name": "角色1"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        location_entity = MemoryEntity(
            id="loc-1",
            session_id="test-session",
            type=MemoryEntityType.LOCATION,
            content={"name": "地点1"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await store.store_entity(character_entity)
        await store.store_entity(location_entity)

        # 按类型检索
        characters = await store.retrieve_entities_by_type(
            "test-session", MemoryEntityType.CHARACTER
        )

        assert len(characters) == 1
        assert characters[0].type == MemoryEntityType.CHARACTER

    @pytest.mark.asyncio
    async def test_store_and_retrieve_facts(self, temp_db_path):
        """测试存储和检索事实"""
        store = StructuredStore(db_path=temp_db_path)
        await asyncio.sleep(0.1)

        fact_data = {
            "session_id": "test-session",
            "fact_type": "event",
            "content": {"description": "测试事件", "importance": "high"},
            "timestamp": datetime.now().isoformat(),
            "source_entity_id": "char-1",
            "target_entity_id": "loc-1",
            "confidence": 0.9,
        }

        # 存储事实
        fact_id = await store.store_fact(fact_data)
        assert fact_id is not None

        # 检索事实
        facts = await store.retrieve_facts("test-session")
        assert len(facts) == 1
        assert facts[0]["id"] == fact_id
        assert facts[0]["fact_type"] == "event"

    @pytest.mark.asyncio
    async def test_create_and_get_plotlines(self, temp_db_path):
        """测试创建和获取剧情线"""
        store = StructuredStore(db_path=temp_db_path)
        await asyncio.sleep(0.1)

        plotline_data = {
            "session_id": "test-session",
            "title": "测试剧情线",
            "description": "这是一个测试剧情线",
            "status": "active",
            "priority": 1,
            "entities": [
                {"entity_id": "char-1", "role": "protagonist"},
                {"entity_id": "loc-1", "role": "location"},
            ],
        }

        # 创建剧情线
        plotline_id = await store.create_plotline(plotline_data)
        assert plotline_id is not None

        # 获取剧情线
        plotlines = await store.get_plotlines("test-session")
        assert len(plotlines) == 1
        assert plotlines[0]["id"] == plotline_id
        assert plotlines[0]["title"] == "测试剧情线"
        assert len(plotlines[0]["entities"]) == 2

    @pytest.mark.asyncio
    async def test_get_session_stats(self, temp_db_path, sample_entity):
        """测试获取会话统计"""
        store = StructuredStore(db_path=temp_db_path)
        await asyncio.sleep(0.1)

        # 存储实体
        await store.store_entity(sample_entity)

        # 获取统计
        stats = await store.get_session_stats("test-session")

        assert stats["session_id"] == "test-session"
        assert stats["entity_count"] == 1
        assert "character" in stats["entity_stats"]
        assert stats["entity_stats"]["character"] == 1


class TestVectorStore:
    """VectorStore单元测试"""

    @pytest.fixture
    def vector_store_config(self):
        """VectorStore配置"""
        return {
            "enabled": False,  # 测试中禁用，避免依赖chromadb
            "embedding_provider": "local",
            "collection_name": "test_memories",
        }

    @pytest.mark.asyncio
    async def test_vector_store_initialization(self, vector_store_config):
        """测试VectorStore初始化"""
        store = VectorStore(config=vector_store_config)
        assert store.enabled == False
        assert store.embedding_provider == "local"

    @pytest.mark.asyncio
    async def test_dummy_vector_store(self):
        """测试虚拟向量存储"""
        from loom.memory.vector_store import DummyVectorStore

        store = DummyVectorStore()
        assert store.enabled == False

        # 测试虚拟方法
        entity = MemoryEntity(
            id="test-entity",
            session_id="test-session",
            type=MemoryEntityType.CHARACTER,
            content={"name": "测试"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        success = await store.store_entity(entity)
        assert success == False

        results = await store.search("测试查询")
        assert results == []

        stats = await store.get_collection_stats()
        assert stats["enabled"] == False


class TestMemorySummarizer:
    """MemorySummarizer单元测试"""

    @pytest.fixture
    def sample_entities(self):
        """创建示例实体列表"""
        entities = []
        base_time = datetime.now() - timedelta(days=10)

        for i in range(8):
            entity = MemoryEntity(
                id=f"summary-entity-{i}",
                session_id="test-session",
                type=(
                    MemoryEntityType.CHARACTER if i % 2 == 0 else MemoryEntityType.EVENT
                ),
                content={
                    "name": f"实体{i}",
                    "description": f"这是第{i}个测试实体",
                    "importance": 0.5 + (i * 0.1),
                },
                created_at=base_time + timedelta(days=i),
                updated_at=base_time + timedelta(days=i),
                metadata={"test": True},
            )
            entities.append(entity)

        return entities

    @pytest.mark.asyncio
    async def test_summarizer_initialization(self):
        """测试Summarizer初始化"""
        summarizer = MemorySummarizer()
        assert summarizer.config is not None
        assert summarizer.config.summary_strategy == "time_based"
        assert summarizer.config.enable_cache == True

    @pytest.mark.asyncio
    async def test_should_summarize(self, sample_entities):
        """测试是否应该生成摘要"""
        summarizer = MemorySummarizer()

        # 实体数量不足
        few_entities = sample_entities[:3]
        should_summarize = await summarizer.should_summarize(few_entities)
        assert should_summarize == False

        # 实体数量足够
        should_summarize = await summarizer.should_summarize(sample_entities)
        assert should_summarize == True

    @pytest.mark.asyncio
    async def test_select_entities_for_summarization(self, sample_entities):
        """测试选择需要摘要的实体"""
        summarizer = MemorySummarizer()

        selected = await summarizer.select_entities_for_summarization(sample_entities)

        # 应该选择最旧的实体
        assert len(selected) > 0
        assert len(selected) <= summarizer.config.max_entities_per_summary

        # 选择的实体应该比保留天数更旧
        cutoff_time = datetime.now() - timedelta(
            days=summarizer.config.preserve_recent_days
        )
        for entity in selected:
            assert entity.created_at < cutoff_time

    @pytest.mark.asyncio
    async def test_generate_summary_without_llm(self, sample_entities):
        """测试无LLM生成摘要"""
        summarizer = MemorySummarizer(llm_provider=None)

        # 选择需要摘要的实体
        selected = await summarizer.select_entities_for_summarization(sample_entities)

        if selected:
            summary = await summarizer.generate_summary(selected)
            assert summary is not None
            assert summary.session_id == "test-session"
            assert len(summary.original_entities) == len(selected)
            assert summary.summary_text is not None

    @pytest.mark.asyncio
    async def test_cache_functionality(self, sample_entities):
        """测试缓存功能"""
        config = SummaryConfig(
            enable_cache=True,
            cache_ttl_hours=1,
            min_entities_to_summarize=3,  # 设置为3以匹配测试中的实体数量
        )
        summarizer = MemorySummarizer(config=config)

        # 生成摘要
        selected = sample_entities[:4]
        summary1 = await summarizer.generate_summary(selected)
        assert summary1 is not None

        # 再次生成相同实体的摘要，应该从缓存获取
        summary2 = await summarizer.generate_summary(selected)
        assert summary2 is not None
        assert summary2.id == summary1.id  # 应该返回相同的摘要（缓存命中）
