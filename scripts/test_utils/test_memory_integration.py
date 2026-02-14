#!/usr/bin/env python3
"""
第二阶段世界记忆系统集成测试脚本

验证VectorMemoryStore、MemorySummarizer、EnhancedWorldMemory和MemoryConsistencyChecker的集成兼容性。
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loom.memory.enhanced_world_memory import (
    EnhancedMemoryConfig,
    EnhancedWorldMemory,
)
from src.loom.memory.interfaces import MemoryQuery
from src.loom.memory.memory_consistency_checker import MemoryConsistencyChecker
from src.loom.memory.memory_summarizer import (
    MemorySummarizer,
    SummaryFormat,
    SummaryStrategy,
)
from src.loom.memory.vector_memory_store import VectorMemoryStore, VectorStoreBackend
from src.loom.memory.world_memory import (
    MemoryEntity,
    MemoryEntityType,
    MemoryRelation,
    MemoryRelationType,
)


class MockLLMProvider:
    """模拟LLM提供者用于测试"""

    def __init__(self):
        self.call_count = 0

    async def generate(self, prompt, **kwargs):
        """模拟生成摘要"""
        self.call_count += 1
        return MockLLMResponse(f"这是模拟生成的摘要 #{self.call_count}")


class MockLLMResponse:
    """模拟LLM响应"""

    def __init__(self, content):
        self.content = content


async def test_vector_store_integration():
    """测试向量存储集成"""
    print("=" * 60)
    print("测试向量存储集成")
    print("=" * 60)

    # 创建向量存储
    vector_config = {
        "backend": VectorStoreBackend.MEMORY.value,
        "enabled": True,
        "embedding_dimension": 384,
        "similarity_threshold": 0.7,
    }

    vector_store = VectorMemoryStore(vector_config)

    # 创建测试实体
    test_entities = []
    for i in range(5):
        entity = MemoryEntity(
            id=f"vector_test_{i}",
            session_id="integration_test",
            type=MemoryEntityType.FACT,
            content={"text": f"向量存储测试实体 {i}", "category": "test"},
            created_at=datetime.now() - timedelta(hours=i),
            updated_at=datetime.now() - timedelta(hours=i),
        )
        test_entities.append(entity)

    # 测试存储
    print("1. 测试实体存储...")
    for entity in test_entities:
        success = await vector_store.store_entity_with_embedding(entity)
        print(f"   存储实体 {entity.id}: {'成功' if success else '失败'}")

    # 测试语义搜索
    print("\n2. 测试语义搜索...")
    search_results = await vector_store.semantic_search("向量存储测试", limit=3)
    print(f"   找到 {len(search_results)} 个相关结果")
    for entity_id, similarity in search_results[:3]:
        print(f"   - {entity_id}: 相似度 {similarity:.3f}")

    # 测试批量操作
    print("\n3. 测试批量操作...")
    batch_results = await vector_store.store_entities_batch(test_entities)
    print(f"   批量存储 {len(batch_results)} 个实体")

    # 测试删除
    print("\n4. 测试删除操作...")
    delete_success = await vector_store.delete_entity(test_entities[0].id)
    print(f"   删除实体 {test_entities[0].id}: {'成功' if delete_success else '失败'}")

    print("\n向量存储集成测试完成 ✓")


async def test_memory_summarizer_integration():
    """测试记忆摘要生成器集成"""
    print("\n" + "=" * 60)
    print("测试记忆摘要生成器集成")
    print("=" * 60)

    # 创建模拟LLM
    mock_llm = MockLLMProvider()

    # 创建摘要生成器
    summarizer_config = {
        "summary_strategy": SummaryStrategy.TIME_BASED.value,
        "summary_format": SummaryFormat.TEXT.value,
        "max_entities_per_summary": 3,
        "enable_cache": True,
        "cache_ttl_seconds": 300,
    }

    summarizer = MemorySummarizer(mock_llm, summarizer_config)

    # 创建测试实体
    test_entities = []
    for i in range(10):
        entity = MemoryEntity(
            id=f"summary_test_{i}",
            session_id="integration_test",
            type=MemoryEntityType.FACT,
            content={
                "text": f"摘要测试实体 {i}",
                "timestamp": f"2024-01-{i+1:02d}",
                "importance": 0.1 * i,
            },
            created_at=datetime.now() - timedelta(days=10 - i),
            updated_at=datetime.now() - timedelta(days=10 - i),
        )
        test_entities.append(entity)

    # 测试摘要生成
    print("1. 测试摘要生成...")
    summary = await summarizer.generate_summary(test_entities)
    print(f"   生成摘要 ID: {summary.id}")
    print(f"   摘要文本: {summary.summary_text[:100]}...")
    print(f"   包含实体数: {len(summary.original_entities)}")

    # 测试重要性评分
    print("\n2. 测试重要性评分...")
    for i, entity in enumerate(test_entities[:3]):
        importance = await summarizer.calculate_entity_importance(entity)
        print(f"   实体 {entity.id}: 重要性 {importance.score:.3f}")

    # 测试缓存
    print("\n3. 测试缓存功能...")
    summary2 = await summarizer.generate_summary(test_entities[:3])
    print(f"   缓存命中: {summary2.id == summary.id}")

    print("\n记忆摘要生成器集成测试完成 ✓")


async def test_enhanced_world_memory_integration():
    """测试增强世界记忆集成"""
    print("\n" + "=" * 60)
    print("测试增强世界记忆集成")
    print("=" * 60)

    # 创建增强记忆配置
    memory_config = {
        "structured_store_enabled": True,
        "vector_store_enabled": True,
        "summarizer_enabled": True,
        "enable_consistency_checking": True,
        "cache_enabled": True,
        "max_cache_size": 1000,
    }

    # 创建增强记忆实例
    memory = EnhancedWorldMemory("integration_test", memory_config)

    # 测试实体CRUD
    print("1. 测试实体CRUD操作...")

    # 创建实体
    entity = MemoryEntity(
        id="enhanced_test_1",
        session_id="integration_test",
        type=MemoryEntityType.CHARACTER,
        content={
            "name": "测试角色",
            "description": "这是一个用于集成测试的角色",
            "traits": ["勇敢", "聪明", "忠诚"],
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    entity_id = await memory.store_entity(entity)
    print(f"   存储实体: {entity_id}")

    # 检索实体
    retrieved = await memory.retrieve_entity(entity_id)
    print(f"   检索实体: {'成功' if retrieved else '失败'}")

    # 更新实体
    updates = {"content": {"description": "更新后的角色描述"}}
    update_success = await memory.update_entity(entity_id, updates)
    print(f"   更新实体: {'成功' if update_success else '失败'}")

    # 测试查询
    print("\n2. 测试查询功能...")
    query = MemoryQuery(
        session_id="integration_test", entity_type=MemoryEntityType.CHARACTER, limit=10
    )

    results = await memory.query_entities(query)
    print(f"   查询结果: {len(results)} 个实体")

    # 测试语义搜索
    print("\n3. 测试语义搜索...")
    search_results = await memory.semantic_search("测试角色", limit=5)
    print(f"   语义搜索结果: {len(search_results)} 个相关实体")

    # 测试时间线
    print("\n4. 测试时间线功能...")
    timeline = await memory.get_timeline()
    print(f"   时间线事件数: {len(timeline)}")

    print("\n增强世界记忆集成测试完成 ✓")


async def test_consistency_checker_integration():
    """测试一致性检查器集成"""
    print("\n" + "=" * 60)
    print("测试一致性检查器集成")
    print("=" * 60)

    # 创建一致性检查器
    checker = MemoryConsistencyChecker()

    # 创建有问题的测试实体
    problematic_entities = []

    # 重复实体
    problematic_entities.append(
        MemoryEntity(
            id="consistency_dup_1",
            session_id="integration_test",
            type=MemoryEntityType.FACT,
            content={"text": "重复的事实内容"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )

    problematic_entities.append(
        MemoryEntity(
            id="consistency_dup_2",
            session_id="integration_test",
            type=MemoryEntityType.FACT,
            content={"text": "重复的事实内容"},  # 相同内容
            created_at=datetime.now() + timedelta(minutes=5),
            updated_at=datetime.now() + timedelta(minutes=5),
        )
    )

    # 时间冲突实体
    problematic_entities.append(
        MemoryEntity(
            id="consistency_time_1",
            session_id="integration_test",
            type=MemoryEntityType.EVENT,
            content={"name": "事件A", "location": "地点X"},
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 10, 0, 0),
        )
    )

    problematic_entities.append(
        MemoryEntity(
            id="consistency_time_2",
            session_id="integration_test",
            type=MemoryEntityType.EVENT,
            content={"name": "事件B", "location": "地点X"},  # 相同地点
            created_at=datetime(2024, 1, 1, 10, 15, 0),  # 15分钟后
            updated_at=datetime(2024, 1, 1, 10, 15, 0),
        )
    )

    # 运行一致性检查
    print("1. 运行一致性检查...")
    result = await checker.check_consistency(problematic_entities)

    print(f"   检查完成: {result.issues_found} 个问题")
    print(f"   检查时间: {result.check_time}")

    # 显示问题详情
    print("\n2. 问题详情:")
    for i, issue in enumerate(result.issues[:3], 1):
        print(f"   {i}. {issue.issue_type.value} - {issue.severity.value}")
        print(f"      描述: {issue.description}")
        print(f"      影响实体: {', '.join(issue.affected_entities[:3])}")
        if issue.suggested_fix:
            print(f"      建议修复: {issue.suggested_fix}")
        print()

    # 测试问题解决
    print("3. 测试问题解决...")
    if result.issues:
        issue_id = result.issues[0].issue_id
        await checker.mark_issue_resolved(issue_id)
        print(f"   标记问题 {issue_id} 为已解决")

    # 获取未解决的问题
    unresolved = await checker.get_unresolved_issues()
    print(f"   未解决问题数: {len(unresolved)}")

    print("\n一致性检查器集成测试完成 ✓")


async def test_full_integration():
    """测试完整集成"""
    print("\n" + "=" * 60)
    print("测试完整系统集成")
    print("=" * 60)

    # 创建完整的增强记忆系统
    memory_config = {
        "structured_store_enabled": True,
        "vector_store_enabled": True,
        "summarizer_enabled": True,
        "enable_consistency_checking": True,
        "cache_enabled": True,
        "max_cache_size": 1000,
    }

    memory = EnhancedWorldMemory("full_integration_test", memory_config)

    # 创建多样化的测试数据
    print("1. 创建测试数据...")

    # 角色实体
    character = MemoryEntity(
        id="character_hero",
        session_id="full_integration_test",
        type=MemoryEntityType.CHARACTER,
        content={
            "name": "英雄",
            "description": "故事的主角",
            "traits": ["勇敢", "正义", "强大"],
            "relationships": ["ally_villain"],
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # 地点实体
    location = MemoryEntity(
        id="location_castle",
        session_id="full_integration_test",
        type=MemoryEntityType.LOCATION,
        content={
            "name": "城堡",
            "description": "古老的城堡，充满神秘",
            "features": ["高塔", "地牢", "大厅"],
            "inhabitants": ["character_hero"],
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # 事件实体
    event = MemoryEntity(
        id="event_battle",
        session_id="full_integration_test",
        type=MemoryEntityType.EVENT,
        content={
            "name": "城堡之战",
            "description": "英雄在城堡中与敌人战斗",
            "participants": ["character_hero"],
            "location": "location_castle",
            "timestamp": "2024-01-15T14:30:00",
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # 存储所有实体
    entities = [character, location, event]
    for entity in entities:
        await memory.store_entity(entity)

    print(f"   创建了 {len(entities)} 个测试实体")

    # 测试复杂查询
    print("\n2. 测试复杂查询...")

    # 查询所有角色
    character_query = MemoryQuery(
        session_id="full_integration_test", entity_type=MemoryEntityType.CHARACTER
    )
    characters = await memory.query_entities(character_query)
    print(f"   角色数量: {len(characters)}")

    # 查询所有事件
    event_query = MemoryQuery(
        session_id="full_integration_test", entity_type=MemoryEntityType.EVENT
    )
    events = await memory.query_entities(event_query)
    print(f"   事件数量: {len(events)}")

    # 测试关系网络
    print("\n3. 测试关系网络...")
    network = await memory.get_relationship_network()
    print(f"   关系网络节点数: {len(network.nodes)}")
    print(f"   关系网络边数: {len(network.edges)}")

    # 测试语义搜索
    print("\n4. 测试语义搜索...")
    search_results = await memory.semantic_search("英雄战斗", limit=5)
    print(f"   语义搜索结果数: {len(search_results)}")

    # 测试向后兼容性
    print("\n5. 测试向后兼容性...")
    # 验证EnhancedWorldMemory继承自WorldMemory
    from src.loom.memory.world_memory import WorldMemory

    assert isinstance(memory, WorldMemory), "EnhancedWorldMemory必须继承自WorldMemory"
    print("   向后兼容性验证通过 ✓")

    print("\n完整系统集成测试完成 ✓")


async def main():
    """主测试函数"""
    print("第二阶段世界记忆系统集成测试")
    print("=" * 60)

    try:
        # 运行所有集成测试
        await test_vector_store_integration()
        await test_memory_summarizer_integration()
        await test_enhanced_world_memory_integration()
        await test_consistency_checker_integration()
        await test_full_integration()

        print("\n" + "=" * 60)
        print("所有集成测试完成！ ✓")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行异步测试
    success = asyncio.run(main())

    if success:
        print("\n集成兼容性验证通过！")
        sys.exit(0)
    else:
        print("\n集成兼容性验证失败！")
        sys.exit(1)
