#!/usr/bin/env python3
"""
LLM Provider增强组件集成验证脚本

验证EnhancedProviderManager、CostOptimizer和LocalModelProvider与现有系统的兼容性。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loom.interpretation.llm_provider import (
    LLMProvider,
    ProviderManager,
    LLMProviderFactory,
)
from src.loom.interpretation.enhanced_provider_manager import (
    EnhancedProviderManager,
    ProviderPriority,
)
from src.loom.interpretation.cost_optimizer import CostOptimizer, BudgetLimit
from src.loom.interpretation.local_model_provider import LocalModelProvider


class MockProvider(LLMProvider):
    """模拟Provider用于测试"""

    def __init__(self, name="mock", success_rate=1.0):
        config = {"name": name, "type": "mock", "model": "mock-model", "enabled": True}
        super().__init__(config)
        self.success_rate = success_rate
        self.call_count = 0

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """模拟生成实现"""
        self.call_count += 1

        # 模拟失败
        if self.call_count == 1 and self.success_rate < 1.0:
            raise Exception("Simulated failure for testing")

        from src.loom.interpretation.llm_provider import LLMResponse

        return LLMResponse(
            content=f"Mock response from {self.name} for: {prompt[:50]}...",
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            metadata={"provider": self.name, "mock": True},
        )

    async def generate_stream(self, prompt: str, **kwargs):
        """模拟流式生成"""
        yield f"Stream from {self.name}: "
        yield prompt[:20]

    async def health_check(self):
        """健康检查"""
        return {"healthy": True, "latency": 0.1}


async def test_backward_compatibility():
    """测试向后兼容性"""
    print("=" * 60)
    print("测试向后兼容性")
    print("=" * 60)

    # 1. 测试现有的ProviderManager仍然工作
    print("\n1. 测试现有的ProviderManager...")
    manager = ProviderManager()

    mock_provider = MockProvider("legacy_provider")
    manager.register_provider("legacy", mock_provider)
    manager.set_default("legacy")

    assert "legacy" in manager.providers
    print("  ✓ 现有ProviderManager注册Provider成功")

    # 2. 测试EnhancedProviderManager继承自ProviderManager
    print("\n2. 测试EnhancedProviderManager继承关系...")
    enhanced_config = {
        "health_check_interval": 5,
        "selection_strategy": "weighted_round_robin",
    }
    enhanced_manager = EnhancedProviderManager(enhanced_config)

    # 验证EnhancedProviderManager是ProviderManager的子类
    assert isinstance(enhanced_manager, ProviderManager)
    print("  ✓ EnhancedProviderManager是ProviderManager的子类")

    # 3. 测试EnhancedProviderManager支持现有接口
    print("\n3. 测试EnhancedProviderManager支持现有接口...")
    await enhanced_manager.register_provider("enhanced_test", mock_provider)
    enhanced_manager.set_default("enhanced_test")

    # 测试现有的generate_with_fallback方法
    try:
        response = await enhanced_manager.generate_with_fallback("Test prompt")
        print(f"  ✓ 现有generate_with_fallback方法工作正常")
        print(f"    响应: {response.content[:50]}...")
    except Exception as e:
        print(f"  ✗ generate_with_fallback失败: {e}")
        return False

    # 4. 测试新的智能故障转移方法
    print("\n4. 测试新的智能故障转移方法...")
    try:
        response = await enhanced_manager.generate_with_intelligent_fallback(
            "Test intelligent fallback", priority=ProviderPriority.BALANCED
        )
        print(f"  ✓ 智能故障转移方法工作正常")
        print(f"    响应: {response.content[:50]}...")
    except Exception as e:
        print(f"  ✗ 智能故障转移失败: {e}")
        return False

    return True


async def test_cost_optimizer_integration():
    """测试CostOptimizer集成"""
    print("\n" + "=" * 60)
    print("测试CostOptimizer集成")
    print("=" * 60)

    # 1. 创建CostOptimizer
    print("\n1. 创建CostOptimizer...")
    cost_config = {
        "budget": {
            "total_budget": 100.0,
            "daily_limit": 10.0,
            "monthly_limit": 50.0,
            "per_request_limit": 1.0,
        },
        "pricing": {
            "mock": {"model_pricing": {"mock-model": {"input": 0.001, "output": 0.002}}}
        },
    }

    cost_optimizer = CostOptimizer(cost_config)
    print("  ✓ CostOptimizer创建成功")

    # 2. 测试成本记录
    print("\n2. 测试成本记录...")
    from src.loom.interpretation.llm_provider import LLMResponse

    mock_response = LLMResponse(
        content="Test response",
        model="mock-model",
        usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        metadata={"provider": "mock"},
    )

    cost = cost_optimizer.record_usage("mock", mock_response)
    print(f"  ✓ 成本记录成功: ${cost:.6f}")
    print(f"    总记录数: {len(cost_optimizer.cost_history)}")

    # 3. 测试预算检查
    print("\n3. 测试预算检查...")
    can_make, reason = cost_optimizer.can_make_request(estimated_cost=0.5)
    print(f"  ✓ 预算检查: {can_make} - {reason}")

    # 4. 测试成本摘要
    print("\n4. 测试成本摘要...")
    summary = cost_optimizer.get_cost_summary()
    print(f"  ✓ 成本摘要生成成功")
    print(f"    总成本: ${summary['total_cost']:.4f}")
    print(f"    请求数: {summary['request_count']}")

    return True


async def test_local_model_provider_compatibility():
    """测试LocalModelProvider兼容性"""
    print("\n" + "=" * 60)
    print("测试LocalModelProvider兼容性")
    print("=" * 60)

    # 1. 测试LocalModelProvider继承关系
    print("\n1. 测试LocalModelProvider继承关系...")
    from src.loom.interpretation.llm_provider import LocalProvider

    local_config = {
        "name": "test_local",
        "type": "local",
        "model": "test-model",
        "base_url": "http://localhost:11434/api",
        "auto_discovery": False,  # 测试中禁用自动发现
    }

    local_provider = LocalModelProvider(local_config)

    # 验证LocalModelProvider是LocalProvider的子类
    assert isinstance(local_provider, LocalProvider)
    print("  ✓ LocalModelProvider是LocalProvider的子类")

    # 2. 测试模型管理器功能
    print("\n2. 测试模型管理器功能...")
    assert local_provider.model_manager is not None
    print("  ✓ 模型管理器初始化成功")

    # 3. 测试性能监控
    print("\n3. 测试性能监控...")
    assert local_provider.performance_monitoring is True
    print("  ✓ 性能监控已启用")

    # 4. 测试可用模型获取
    print("\n4. 测试可用模型获取...")
    models = await local_provider.get_available_models()
    print(f"  ✓ 获取到 {len(models)} 个模型")

    await local_provider.close()
    print("  ✓ LocalModelProvider关闭成功")

    return True


async def test_integration_scenario():
    """测试集成场景"""
    print("\n" + "=" * 60)
    print("测试完整集成场景")
    print("=" * 60)

    # 创建完整的工作流
    print("\n1. 创建集成工作流...")

    # 创建EnhancedProviderManager
    manager_config = {
        "health_check_interval": 2,
        "selection_strategy": "weighted_round_robin",
        "fallback_order": ["provider2", "provider3"],
        "fallback_delay": 0.1,
    }

    manager = EnhancedProviderManager(manager_config)

    # 创建CostOptimizer
    cost_config = {
        "budget": {"total_budget": 50.0, "daily_limit": 5.0},
        "optimization_enabled": True,
    }
    cost_optimizer = CostOptimizer(cost_config)
    manager.cost_tracker = cost_optimizer

    # 注册多个Provider
    providers = [
        MockProvider("provider1", success_rate=0.8),
        MockProvider("provider2", success_rate=1.0),
        MockProvider("provider3", success_rate=0.9),
    ]

    for i, provider in enumerate(providers, 1):
        await manager.register_provider(f"provider{i}", provider)

    manager.set_default("provider1")
    manager.set_fallback_order(["provider2", "provider3"])

    print("  ✓ 工作流组件创建完成")
    print(f"    注册了 {len(providers)} 个Provider")
    print(f"    成本优化器: {'已集成' if manager.cost_tracker else '未集成'}")

    # 测试多个请求
    print("\n2. 测试多个请求...")
    test_prompts = [
        "First test prompt",
        "Second test prompt with longer text",
        "Third prompt for fallback testing",
    ]

    successful_requests = 0
    for i, prompt in enumerate(test_prompts, 1):
        try:
            response = await manager.generate_with_intelligent_fallback(
                prompt, priority=ProviderPriority.BALANCED
            )
            print(f"  ✓ 请求 {i} 成功: {response.content[:40]}...")
            successful_requests += 1
        except Exception as e:
            print(f"  ✗ 请求 {i} 失败: {e}")

    print(f"\n  成功率: {successful_requests}/{len(test_prompts)}")

    # 检查成本记录
    print("\n3. 检查成本记录...")
    cost_summary = cost_optimizer.get_cost_summary()
    print(f"  总成本: ${cost_summary['total_cost']:.4f}")
    print(f"  总请求数: {cost_summary['request_count']}")

    # 检查Provider统计
    print("\n4. 检查Provider统计...")
    stats = await manager.get_provider_stats()
    print(f"  健康Provider数: {stats['overall']['healthy_providers']}/{len(providers)}")
    print(f"  总体成功率: {stats['overall']['success_rate']:.1%}")

    # 清理
    await manager.close_all()
    print("\n5. 清理资源...")
    print("  ✓ 所有资源已清理")

    return successful_requests > 0


async def main():
    """主函数"""
    print("LLM Provider增强组件集成验证")
    print("=" * 60)

    tests = [
        ("向后兼容性测试", test_backward_compatibility),
        ("CostOptimizer集成测试", test_cost_optimizer_integration),
        ("LocalModelProvider兼容性测试", test_local_model_provider_compatibility),
        ("完整集成场景测试", test_integration_scenario),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n开始 {test_name}...")
            success = await test_func()
            results.append((test_name, success))

            if success:
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")

        except Exception as e:
            print(f"✗ {test_name} 异常: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("\n🎉 所有集成验证测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    # 设置事件循环策略（Windows需要）
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
