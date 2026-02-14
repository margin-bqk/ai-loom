#!/usr/bin/env python3
"""
简化版LLM Provider增强组件验证脚本

直接验证三个核心组件的功能和兼容性，不依赖项目其他部分。
"""

import asyncio
import os
import sys
from pathlib import Path

# 直接导入我们实现的组件
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dataclasses import dataclass, field
from datetime import datetime

# 定义必要的基类和数据结构
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp


# 定义LLMResponse（简化版）
@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# 定义LLMProvider基类（简化版）
class LLMProvider:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")
        self.provider_type = config.get("type", "unknown")
        self.model = config.get("model", "default")
        self.enabled = config.get("enabled", True)
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        self.request_count += 1
        return await self._generate_impl(prompt, **kwargs)

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        raise NotImplementedError

    async def generate_stream(self, prompt: str, **kwargs):
        raise NotImplementedError

    def get_stats(self):
        return {
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
        }


# 定义LocalProvider基类（简化版）
class LocalProvider(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434/api")


# 现在导入我们实现的组件
try:
    from loom.interpretation.cost_optimizer import (
        BudgetAlertLevel,
        BudgetLimit,
        CostOptimizer,
    )
    from loom.interpretation.enhanced_provider_manager import (
        EnhancedProviderManager,
        FallbackStrategy,
        ProviderHealthMonitor,
        ProviderLoadBalancer,
        ProviderPriority,
    )
    from loom.interpretation.local_model_provider import (
        LocalModelInfo,
        LocalModelProvider,
        LocalModelType,
    )

    print("✓ 成功导入所有增强组件")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


class MockEnhancedProvider(LLMProvider):
    """模拟Provider用于测试增强功能"""

    def __init__(self, name="mock", success=True, latency=0.1):
        config = {"name": name, "type": "mock", "model": "test-model", "enabled": True}
        super().__init__(config)
        self.success = success
        self.latency = latency

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        import asyncio

        await asyncio.sleep(self.latency)

        if not self.success:
            raise Exception(f"Mock failure from {self.name}")

        return LLMResponse(
            content=f"Response from {self.name}: {prompt[:20]}...",
            model=self.model,
            usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
            metadata={"provider": self.name},
        )

    async def generate_stream(self, prompt: str, **kwargs):
        if not self.success:
            raise Exception(f"Mock stream failure from {self.name}")

        yield f"Stream from {self.name}: "
        for word in prompt.split()[:3]:
            yield word + " "

    async def health_check(self):
        return {"healthy": self.success, "latency": self.latency}


async def test_enhanced_provider_manager():
    """测试EnhancedProviderManager"""
    print("\n" + "=" * 60)
    print("测试 EnhancedProviderManager")
    print("=" * 60)

    # 创建管理器
    config = {
        "health_check_interval": 1,
        "selection_strategy": "weighted_round_robin",
        "fallback_order": ["provider2", "provider3"],
        "fallback_delay": 0.01,
    }

    manager = EnhancedProviderManager(config)
    print("✓ EnhancedProviderManager 创建成功")

    # 注册多个Provider
    providers = {
        "provider1": MockEnhancedProvider("provider1", success=True, latency=0.1),
        "provider2": MockEnhancedProvider("provider2", success=True, latency=0.2),
        "provider3": MockEnhancedProvider(
            "provider3", success=False, latency=0.1
        ),  # 会失败的
    }

    for name, provider in providers.items():
        await manager.register_provider(name, provider)

    print(f"✓ 注册了 {len(providers)} 个Provider")

    # 测试智能故障转移
    print("\n测试智能故障转移...")
    try:
        response = await manager.generate_with_intelligent_fallback(
            "Test prompt for intelligent fallback", priority=ProviderPriority.BALANCED
        )
        print(f"✓ 智能故障转移成功: {response.content[:50]}...")

        # 验证响应来自可用的Provider（不是provider3）
        assert "provider3" not in response.content
        print("✓ 故障转移逻辑正确（避开了失败的Provider）")

    except Exception as e:
        print(f"✗ 智能故障转移失败: {e}")
        return False

    # 测试Provider统计
    print("\n测试Provider统计...")
    try:
        stats = await manager.get_provider_stats()
        assert "providers" in stats
        assert "overall" in stats
        print(f"✓ 获取统计成功: {stats['overall']['total_requests']} 个请求")
    except Exception as e:
        print(f"✗ 获取统计失败: {e}")
        return False

    # 清理
    await manager.close_all()
    print("✓ 资源清理成功")

    return True


async def test_cost_optimizer():
    """测试CostOptimizer"""
    print("\n" + "=" * 60)
    print("测试 CostOptimizer")
    print("=" * 60)

    # 创建成本优化器
    config = {
        "budget": {
            "total_budget": 100.0,
            "daily_limit": 10.0,
            "monthly_limit": 50.0,
            "per_request_limit": 0.5,
        },
        "pricing": {
            "test_provider": {
                "model_pricing": {"test-model": {"input": 0.001, "output": 0.002}}
            }
        },
        "optimization_enabled": True,
    }

    optimizer = CostOptimizer(config)
    print("✓ CostOptimizer 创建成功")

    # 测试成本记录
    print("\n测试成本记录...")
    response = LLMResponse(
        content="Test response",
        model="test-model",
        usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        metadata={"provider": "test_provider"},
    )

    cost = optimizer.record_usage("test_provider", response)
    print(f"✓ 成本记录成功: ${cost:.6f}")
    print(f"  历史记录数: {len(optimizer.cost_history)}")

    # 测试预算检查
    print("\n测试预算检查...")
    can_make, reason = optimizer.can_make_request(estimated_cost=0.1)
    print(f"✓ 预算检查: {can_make} - {reason}")

    # 测试成本摘要
    print("\n测试成本摘要...")
    summary = optimizer.get_cost_summary()
    print(f"✓ 成本摘要: ${summary['total_cost']:.4f} / {summary['request_count']} 请求")

    # 测试优化建议
    print("\n测试优化建议...")
    suggestions = optimizer.get_optimization_suggestions()
    print(f"✓ 生成 {len(suggestions)} 条优化建议")

    return True


async def test_local_model_provider():
    """测试LocalModelProvider"""
    print("\n" + "=" * 60)
    print("测试 LocalModelProvider")
    print("=" * 60)

    # 创建本地模型Provider
    config = {
        "name": "test_local",
        "type": "local",
        "model": "test-model",
        "base_url": "http://localhost:11434/api",
        "auto_discovery": False,  # 测试中禁用
        "performance_monitoring": True,
        "auto_model_selection": True,
    }

    try:
        provider = LocalModelProvider(config)
        print("✓ LocalModelProvider 创建成功")

        # 验证继承关系
        assert isinstance(provider, LocalProvider)
        print("✓ 正确的继承关系（LocalModelProvider -> LocalProvider -> LLMProvider）")

        # 验证模型管理器
        assert provider.model_manager is not None
        print("✓ 模型管理器初始化成功")

        # 测试模型发现（模拟）
        print("\n测试模型发现...")
        # 添加模拟模型
        test_model = LocalModelInfo(
            name="test-model-7b",
            model_type=LocalModelType.OLLAMA,
            size="7B",
            format="gguf",
            context_length=4096,
            parameters=7_000_000_000,
        )

        provider.model_manager.models["test-model-7b"] = test_model
        models = await provider.get_available_models()
        print(f"✓ 发现 {len(models)} 个模型")

        # 测试模型推荐
        print("\n测试模型推荐...")
        recommended = await provider.model_manager.get_recommended_model()
        print(f"✓ 推荐模型: {recommended}")

        # 清理
        await provider.close()
        print("✓ 资源清理成功")

        return True

    except Exception as e:
        print(f"✗ LocalModelProvider测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_integration():
    """测试集成"""
    print("\n" + "=" * 60)
    print("测试组件集成")
    print("=" * 60)

    # 创建集成的场景
    print("创建集成工作流...")

    # 1. 创建EnhancedProviderManager
    manager_config = {
        "health_check_interval": 1,
        "selection_strategy": "weighted_round_robin",
    }
    manager = EnhancedProviderManager(manager_config)

    # 2. 创建CostOptimizer并集成
    cost_config = {"budget": {"total_budget": 50.0, "daily_limit": 5.0}}
    cost_optimizer = CostOptimizer(cost_config)
    manager.cost_tracker = cost_optimizer

    # 3. 注册Provider
    provider1 = MockEnhancedProvider("integrated1", success=True)
    provider2 = MockEnhancedProvider("integrated2", success=True)

    await manager.register_provider("provider1", provider1)
    await manager.register_provider("provider2", provider2)

    manager.set_default("provider1")
    manager.set_fallback_order(["provider2"])

    print("✓ 集成工作流创建完成")
    print(f"  Provider数: {len(manager.providers)}")
    print(f"  成本优化器: {'已集成' if manager.cost_tracker else '未集成'}")

    # 测试集成功能
    print("\n测试集成功能...")

    # 生成请求
    response = await manager.generate_with_intelligent_fallback(
        "Integration test prompt", priority=ProviderPriority.COST
    )

    print(f"✓ 集成生成成功: {response.content[:40]}...")

    # 验证成本记录
    assert len(cost_optimizer.cost_history) > 0
    print(f"✓ 成本记录成功: {len(cost_optimizer.cost_history)} 条记录")

    # 获取统计
    stats = await manager.get_provider_stats()
    print(f"✓ 统计获取成功: {stats['overall']['total_requests']} 总请求")

    # 清理
    await manager.close_all()
    print("✓ 集成资源清理成功")

    return True


async def main():
    """主函数"""
    print("LLM Provider增强组件验证")
    print("=" * 60)

    tests = [
        ("EnhancedProviderManager", test_enhanced_provider_manager),
        ("CostOptimizer", test_cost_optimizer),
        ("LocalModelProvider", test_local_model_provider),
        ("组件集成", test_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            print(f"\n开始测试: {name}")
            success = await test_func()
            results.append((name, success))

            if success:
                print(f"✓ {name} 测试通过")
            else:
                print(f"✗ {name} 测试失败")

        except Exception as e:
            print(f"✗ {name} 测试异常: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name:30} {status}")

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("\n🎉 所有组件验证通过！")
        print("\n实现总结:")
        print("1. EnhancedProviderManager - 智能故障转移、健康监控、负载均衡")
        print("2. CostOptimizer - 成本跟踪、预算控制、优化建议")
        print("3. LocalModelProvider - 本地模型支持、自动发现、性能监控")
        print("\n所有组件已成功集成并保持向后兼容性。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    # Windows事件循环策略
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
