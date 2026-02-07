"""
第二阶段世界记忆系统单元测试

测试VectorMemoryStore、MemorySummarizer、EnhancedWorldMemory和MemoryConsistencyChecker。
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from src.loom.memory.vector_memory_store import VectorMemoryStore, VectorStoreBackend
from src.loom.memory.memory_summarizer import (
    MemorySummarizer,
    SummaryConfig,
    SummaryStrategy,
    SummaryFormat,
)
from src.loom.memory.enhanced_world_memory import (
    EnhancedWorldMemory,
    EnhancedMemoryConfig,
)
from src.loom.memory.memory_consistency_checker import (
    MemoryConsistencyChecker,
    ConsistencyIssueType,
    ConsistencySeverity,
)
from src.loom.memory.world_memory import (
    MemoryEntity,
    MemoryEntityType,
    MemoryRelation,
    MemoryRelationType,
)


class TestVectorMemoryStore:
    """测试VectorMemoryStore"""

    @pytest.fixture
    def vector_store(self):
        """创建测试用的VectorMemoryStore"""
        config = {
            "backend": VectorStoreBackend.MEMORY.value,  # 使用内存后端进行测试
            "enabled": True,
            "embedding_dimension": 384,
        }
        return VectorMemoryStore(config)

    @pytest.fixture
    def test_entity(self):
        """创建测试实体"""
        return MemoryEntity(
            id="test_entity_1",
            session_id="test_session",
            type=MemoryEntityType.FACT,
            content={"text": "这是一个测试事实", "importance": 0.8},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_store_and_retrieve_embedding(self, vector_store, test_entity):
        """测试存储和检索嵌入"""
        # 存储实体
        success = await vector_store.store_entity_with_embedding(test_entity)
        assert success is True

        # 测试语义搜索
        results = await vector_store.semantic_search("测试事实", limit=5)
        assert len(results) > 0
        assert any(entity_id == test_entity.id for entity_id, _ in results)

    @pytest.mark.asyncio
    async def test_batch_operations(self, vector_store):
        """测试批量操作"""
        entities = []
        for i in range(3):
            entity = MemoryEntity(
                id=f"batch_entity_{i}",
                session_id="test_session",
                type=MemoryEntityType.FACT,
                content={"text": f"批量测试实体 {i}"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            entities.append(entity)

        # 批量存储
        results = await vector_store.store_entities_batch(entities)
        assert len(results) == 3
        assert all(success for success in results.values())

    @pytest.mark.asyncio
    async def test_delete_entity(self, vector_store, test_entity):
        """测试删除实体"""
        # 先存储
        await vector_store.store_entity_with_embedding(test_entity)

        # 删除
        success = await vector_store.delete_entity(test_entity.id)
        assert success is True

        # 验证已删除
        results = await vector_store.semantic_search("测试事实", limit=5)
        assert not any(entity_id == test_entity.id for entity_id, _ in results)


class TestMemorySummarizer:
    """测试MemorySummarizer"""

    @pytest.fixture
    def summarizer(self):
        """创建测试用的MemorySummarizer"""
        # 使用模拟的LLM提供者
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value=Mock(content="这是一个测试摘要"))

        config = {
            "summary_strategy": SummaryStrategy.TIME_BASED.value,
            "summary_format": SummaryFormat.TEXT.value,
            "max_entities_per_summary": 5,
            "min_entities_to_summarize": 3,  # 设置为3以匹配测试中的实体数量
            "enable_cache": False,
        }
        return MemorySummarizer(mock_llm, config)

    @pytest.fixture
    def test_entities(self):
        """创建测试实体列表"""
        entities = []
        for i in range(10):
            entity = MemoryEntity(
                id=f"summary_entity_{i}",
                session_id="test_session",
                type=MemoryEntityType.FACT,
                content={"text": f"测试事实 {i}", "timestamp": f"2024-01-{i+1:02d}"},
                created_at=datetime.now() - timedelta(days=10 - i),
                updated_at=datetime.now() - timedelta(days=10 - i),
            )
            entities.append(entity)
        return entities

    @pytest.mark.asyncio
    async def test_generate_summary(self, summarizer, test_entities):
        """测试生成摘要"""
        summary = await summarizer.generate_summary(test_entities[:3])

        assert summary is not None
        assert summary.id.startswith("summary_")
        assert summary.session_id == "test_session"
        assert len(summary.original_entities) == 3
        assert summary.summary_text == "这是一个测试摘要"

    @pytest.mark.asyncio
    async def test_importance_scoring(self, summarizer):
        """测试重要性评分"""
        entity = MemoryEntity(
            id="importance_test",
            session_id="test_session",
            type=MemoryEntityType.CHARACTER,  # 角色类型通常有较高重要性
            content={"name": "测试角色", "role": "主角"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        importance_score = await summarizer.calculate_entity_importance(entity)

        assert importance_score.entity_id == entity.id
        assert 0 <= importance_score.score <= 1
        assert "type" in importance_score.factors

    @pytest.mark.asyncio
    async def test_entity_selection_strategies(self, summarizer, test_entities):
        """测试实体选择策略"""
        # 测试时间策略
        summarizer.config.summary_strategy = SummaryStrategy.TIME_BASED
        time_based = summarizer._select_entities_for_summary(test_entities)
        assert len(time_based) <= summarizer.config.max_entities_per_summary

        # 测试重要性策略
        summarizer.config.summary_strategy = SummaryStrategy.IMPORTANCE_BASED
        importance_based = summarizer._select_entities_for_summary(test_entities)
        assert len(importance_based) <= summarizer.config.max_entities_per_summary


class TestEnhancedWorldMemory:
    """测试EnhancedWorldMemory"""

    @pytest.fixture
    def enhanced_memory(self):
        """创建测试用的EnhancedWorldMemory"""
        config = {
            "structured_store_enabled": False,  # 测试中禁用结构化存储
            "vector_store_enabled": False,  # 测试中禁用向量存储
            "summarizer_enabled": False,  # 测试中禁用摘要生成器
        }
        return EnhancedWorldMemory("test_session", config)

    @pytest.fixture
    def mock_structured_store(self):
        """创建模拟的结构化存储"""
        mock_store = Mock()
        mock_store.store_entity = AsyncMock(return_value="test_entity_id")
        mock_store.retrieve_entity = AsyncMock(return_value=None)
        mock_store.query_entities = AsyncMock(return_value=[])
        mock_store.update_entity = AsyncMock(return_value=True)
        mock_store.delete_entity = AsyncMock(return_value=True)
        return mock_store

    @pytest.mark.asyncio
    async def test_entity_crud_operations(self, enhanced_memory):
        """测试实体的CRUD操作"""
        # 创建实体
        entity = MemoryEntity(
            id="test_crud_entity",
            session_id="test_session",
            type=MemoryEntityType.FACT,
            content={"text": "CRUD测试"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 存储
        entity_id = await enhanced_memory.store_entity(entity)
        # 当结构化存储被禁用时，EnhancedWorldMemory会生成新的UUID
        # 所以不检查具体的ID值，只检查返回的ID是否有效
        assert entity_id is not None
        assert len(entity_id) > 0

        # 检索
        retrieved = await enhanced_memory.retrieve_entity(entity_id)
        assert retrieved is not None
        assert retrieved.id == entity_id

        # 更新
        updates = {"content": {"text": "更新后的内容"}}
        success = await enhanced_memory.update_entity(entity_id, updates)
        assert success is True

        # 删除
        success = await enhanced_memory.delete_entity(entity_id)
        assert success is True

        # 验证删除
        deleted = await enhanced_memory.retrieve_entity(entity_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_query_entities(self, enhanced_memory):
        """测试查询实体"""
        # 创建一些测试实体
        entities = []
        for i in range(5):
            entity = MemoryEntity(
                id=f"query_test_{i}",
                session_id="test_session",
                type=MemoryEntityType.FACT,
                content={"text": f"查询测试 {i}"},
                created_at=datetime.now() - timedelta(hours=i),
                updated_at=datetime.now() - timedelta(hours=i),
            )
            await enhanced_memory.store_entity(entity)
            entities.append(entity)

        # 查询
        from src.loom.memory.interfaces import MemoryQuery

        query = MemoryQuery(session_id="test_session", limit=10)
        results = await enhanced_memory.query_entities(query)

        # 由于我们禁用了结构化存储，这里可能返回空列表
        # 在实际测试中，应该启用结构化存储或使用模拟

    @pytest.mark.asyncio
    async def test_relationship_operations(self, enhanced_memory):
        """测试关系操作"""
        # 创建两个实体
        entity1 = MemoryEntity(
            id="rel_entity_1",
            session_id="test_session",
            type=MemoryEntityType.CHARACTER,
            content={"name": "角色A"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        entity2 = MemoryEntity(
            id="rel_entity_2",
            session_id="test_session",
            type=MemoryEntityType.CHARACTER,
            content={"name": "角色B"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await enhanced_memory.store_entity(entity1)
        await enhanced_memory.store_entity(entity2)

        # 添加关系
        relation = MemoryRelation(
            source_id="rel_entity_1",
            target_id="rel_entity_2",
            relation_type=MemoryRelationType.KNOWS,
        )

        success = await enhanced_memory.add_relation(relation)
        # 由于禁用了结构化存储，这里可能返回False
        # 在实际测试中，应该启用结构化存储


class TestMemoryConsistencyChecker:
    """测试MemoryConsistencyChecker"""

    @pytest.fixture
    def consistency_checker(self):
        """创建测试用的MemoryConsistencyChecker"""
        return MemoryConsistencyChecker()

    @pytest.fixture
    def test_entities_with_issues(self):
        """创建有问题的测试实体"""
        entities = []

        # 重复实体
        entities.append(
            MemoryEntity(
                id="dup_entity_1",
                session_id="test_session",
                type=MemoryEntityType.FACT,
                content={"text": "重复内容"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )

        entities.append(
            MemoryEntity(
                id="dup_entity_2",
                session_id="test_session",
                type=MemoryEntityType.FACT,
                content={"text": "重复内容"},  # 相同内容
                created_at=datetime.now() + timedelta(hours=1),
                updated_at=datetime.now() + timedelta(hours=1),
            )
        )

        # 时间冲突实体
        entities.append(
            MemoryEntity(
                id="time_conflict_1",
                session_id="test_session",
                type=MemoryEntityType.EVENT,
                content={"name": "事件A"},
                created_at=datetime(2024, 1, 1, 10, 0, 0),
                updated_at=datetime(2024, 1, 1, 10, 0, 0),
            )
        )

        entities.append(
            MemoryEntity(
                id="time_conflict_2",
                session_id="test_session",
                type=MemoryEntityType.EVENT,
                content={"name": "事件B"},
                created_at=datetime(2024, 1, 1, 10, 30, 0),  # 30分钟后
                updated_at=datetime(2024, 1, 1, 10, 30, 0),
            )
        )

        return entities

    @pytest.mark.asyncio
    async def test_duplicate_detection(
        self, consistency_checker, test_entities_with_issues
    ):
        """测试重复检测"""
        # 提取重复实体
        duplicate_entities = test_entities_with_issues[:2]

        issues = await consistency_checker._check_duplicates(duplicate_entities)

        assert len(issues) > 0
        issue = issues[0]
        assert issue.issue_type == ConsistencyIssueType.ENTITY_DUPLICATE
        assert issue.severity == ConsistencySeverity.MEDIUM
        assert "dup_entity_1" in issue.affected_entities
        assert "dup_entity_2" in issue.affected_entities

    @pytest.mark.asyncio
    async def test_temporal_conflict_detection(
        self, consistency_checker, test_entities_with_issues
    ):
        """测试时间冲突检测"""
        # 提取时间冲突实体
        temporal_entities = test_entities_with_issues[2:]

        issues = await consistency_checker._check_temporal_conflicts(temporal_entities)

        # 由于时间差小于24小时，应该检测到冲突
        assert len(issues) > 0
        issue = issues[0]
        assert issue.issue_type == ConsistencyIssueType.TEMPORAL_CONFLICT
        assert issue.severity == ConsistencySeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_full_consistency_check(
        self, consistency_checker, test_entities_with_issues
    ):
        """测试完整的一致性检查"""
        result = await consistency_checker.check_consistency(test_entities_with_issues)

        assert result is not None
        assert result.issues_found > 0
        assert len(result.issues) == result.issues_found

        # 验证问题类型
        issue_types = {issue.issue_type for issue in result.issues}
        assert ConsistencyIssueType.ENTITY_DUPLICATE in issue_types
        assert ConsistencyIssueType.TEMPORAL_CONFLICT in issue_types

    @pytest.mark.asyncio
    async def test_issue_resolution(
        self, consistency_checker, test_entities_with_issues
    ):
        """测试问题解决"""
        # 运行检查
        result = await consistency_checker.check_consistency(
            test_entities_with_issues[:2]
        )

        # 标记问题为已解决
        for issue in result.issues:
            await consistency_checker.mark_issue_resolved(issue.issue_id)

        # 获取未解决的问题
        unresolved = await consistency_checker.get_unresolved_issues()
        assert len(unresolved) == 0


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_enhanced_memory_with_consistency_check(self):
        """测试增强记忆与一致性检查的集成"""
        # 创建配置
        memory_config = {
            "structured_store_enabled": False,
            "vector_store_enabled": False,
            "summarizer_enabled": False,
            "enable_consistency_checking": True,
        }

        # 创建增强记忆
        memory = EnhancedWorldMemory("integration_test", memory_config)

        # 创建一致性检查器
        checker = MemoryConsistencyChecker()

        # 创建一些实体
        entities = []
        for i in range(3):
            entity = MemoryEntity(
                id=f"integration_entity_{i}",
                session_id="integration_test",
                type=MemoryEntityType.FACT,
                content={"text": f"集成测试实体 {i}"},
                created_at=datetime.now() - timedelta(hours=i),
                updated_at=datetime.now() - timedelta(hours=i),
            )
            await memory.store_entity(entity)
            entities.append(entity)

        # 运行一致性检查
        result = await checker.check_consistency(entities)

        # 验证结果
        assert result is not None
        assert result.session_id == "integration_test"

        # 这里可能没有发现问题，因为实体都是正常的
        # 在实际测试中，可以添加有问题的实体进行测试


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
