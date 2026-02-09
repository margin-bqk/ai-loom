"""
第二阶段LLM Provider增强组件单元测试

测试EnhancedProviderManager、CostOptimizer和LocalModelProvider。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
import json

from src.loom.interpretation.llm_provider import LLMProvider, LLMResponse
from src.loom.interpretation.enhanced_provider_manager import (
    EnhancedProviderManager,
    ProviderHealthMonitor,
    ProviderLoadBalancer,
    FallbackStrategy,
    ProviderPriority,
    ProviderHealth,
    ProviderMetrics,
)
from src.loom.interpretation.cost_optimizer import (
    CostOptimizer,
    BudgetAlertLevel,
    CostRecord,
    BudgetLimit,
    ProviderPricing,
)
from src.loom.interpretation.local_model_provider import (
    LocalModelProvider,
    LocalModelManager,
    LocalModelInfo,
    LocalModelType,
    ModelPerformanceMetrics,
)


class MockLLMProvider(LLMProvider):
    """模拟LLM Provider用于测试"""

    def __init__(self, name="test_provider", success=True, latency=0.1):
        config = {
            "name": name,
            "type": "mock",
            "model": "test-model",
            "enabled": True,
            "fallback_enabled": False,
        }
        super().__init__(config)
        self._success = success
        self._latency = latency
        self._response_content = f"Mock response from {name}"

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """模拟生成实现"""
        await asyncio.sleep(self._latency)  # 模拟延迟

        if not self._success:
            raise Exception(f"Mock error from {self.name}")

        return LLMResponse(
            content=self._response_content,
            model=kwargs.get("model", self.model),
            usage={
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": 50,
                "total_tokens": len(prompt) // 4 + 50,
            },
            metadata={"provider": self.name},
        )

    async def generate_stream(self, prompt: str, **kwargs):
        """模拟流式生成"""
        if not self._success:
            raise Exception(f"Mock stream error from {self.name}")

        yield "Stream "
        yield "response "
        yield "from "
        yield self.name

    async def health_check(self):
        """模拟健康检查"""
        return {
            "healthy": self._success,
            "latency": self._latency,
            "timestamp": datetime.now().isoformat(),
        }

    def get_stats(self):
        """获取统计信息"""
        return {
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "error_count": self.error_count,
        }


class TestEnhancedProviderManager:
    """EnhancedProviderManager测试"""

    @pytest.fixture
    def mock_providers(self):
        """创建模拟Provider"""
        return {
            "provider1": MockLLMProvider("provider1", success=True, latency=0.1),
            "provider2": MockLLMProvider("provider2", success=True, latency=0.2),
            "provider3": MockLLMProvider(
                "provider3", success=False, latency=0.1
            ),  # 会失败的Provider
        }

    @pytest.fixture
    def manager(self):
        """创建EnhancedProviderManager实例"""
        config = {
            "health_check_interval": 1,
            "selection_strategy": "weighted_round_robin",
            "fallback_order": ["provider2", "provider1"],
            "max_fallback_attempts": 3,
            "fallback_delay": 0.01,
        }
        return EnhancedProviderManager(config)

    @pytest.mark.asyncio
    async def test_register_provider(self, manager, mock_providers):
        """测试注册Provider"""
        provider = mock_providers["provider1"]

        await manager.register_provider("test_provider", provider)

        assert "test_provider" in manager.providers
        assert manager.providers["test_provider"] == provider
        assert "test_provider" in manager.load_balancer.providers

    @pytest.mark.asyncio
    async def test_generate_with_intelligent_fallback_success(
        self, manager, mock_providers
    ):
        """测试智能故障转移生成（成功情况）"""
        # 注册两个Provider
        await manager.register_provider("fast", mock_providers["provider1"])
        await manager.register_provider("slow", mock_providers["provider2"])

        # 设置默认Provider
        manager.set_default("fast")

        # 测试生成
        response = await manager.generate_with_intelligent_fallback(
            "Test prompt", priority=ProviderPriority.BALANCED
        )

        # 负载均衡器可能选择任一provider，两者都是有效的
        assert response.content in [
            "Mock response from provider1",
            "Mock response from provider2",
        ]
        assert response.model == "test-model"

    @pytest.mark.asyncio
    async def test_generate_with_intelligent_fallback_failure(
        self, manager, mock_providers
    ):
        """测试智能故障转移生成（失败情况）"""
        # 注册一个会失败的Provider和一个正常的Provider
        await manager.register_provider("failing", mock_providers["provider3"])
        await manager.register_provider("working", mock_providers["provider1"])

        # 设置回退顺序
        manager.set_fallback_order(["working"])

        # 测试生成（应该会回退到working provider）
        response = await manager.generate_with_intelligent_fallback(
            "Test prompt", priority=ProviderPriority.BALANCED
        )

        # 由于第一个Provider失败，应该回退到第二个Provider
        assert response.content == "Mock response from provider1"

    @pytest.mark.asyncio
    async def test_provider_health_monitoring(self, manager, mock_providers):
        """测试Provider健康监控"""
        provider = mock_providers["provider1"]
        await manager.register_provider("monitored", provider)

        # 获取健康状态
        health = await manager.health_monitor.get_provider_health("monitored")

        assert "healthy" in health
        assert "metrics" in health
        assert health["metrics"]["request_count"] == 0  # 还没有请求

    @pytest.mark.asyncio
    async def test_get_provider_stats(self, manager, mock_providers):
        """测试获取Provider统计信息"""
        # 注册多个Provider
        for name, provider in mock_providers.items():
            await manager.register_provider(name, provider)

        # 生成一些请求
        await manager.generate_with_intelligent_fallback("Test 1")
        await manager.generate_with_intelligent_fallback("Test 2")

        # 获取统计
        stats = await manager.get_provider_stats()

        assert "providers" in stats
        assert "overall" in stats
        assert stats["overall"]["total_requests"] > 0

    @pytest.mark.asyncio
    async def test_disable_enable_provider(self, manager, mock_providers):
        """测试禁用和启用Provider"""
        provider = mock_providers["provider1"]
        await manager.register_provider("toggle", provider)

        # 禁用Provider
        await manager.disable_provider("toggle", "testing")
        assert not provider.enabled

        # 启用Provider
        await manager.enable_provider("toggle")
        assert provider.enabled


class TestCostOptimizer:
    """CostOptimizer测试"""

    @pytest.fixture
    def cost_optimizer(self):
        """创建CostOptimizer实例"""
        config = {
            "budget": {
                "total_budget": 100.0,
                "daily_limit": 10.0,
                "monthly_limit": 50.0,
                "per_request_limit": 1.0,
            },
            "pricing": {
                "test_provider": {
                    "model_pricing": {"test-model": {"input": 0.001, "output": 0.002}}
                }
            },
            "optimization_enabled": True,
            "alert_cooldown": 60,
        }
        return CostOptimizer(config)

    @pytest.fixture
    def mock_response(self):
        """创建模拟响应"""
        return LLMResponse(
            content="Test response content",
            model="test-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            metadata={"provider": "test_provider"},
        )

    def test_record_usage(self, cost_optimizer, mock_response):
        """测试记录使用成本"""
        initial_count = len(cost_optimizer.cost_history)

        cost = cost_optimizer.record_usage("test_provider", mock_response)

        assert len(cost_optimizer.cost_history) == initial_count + 1
        assert cost > 0
        assert "test_provider" in cost_optimizer.provider_costs
        assert "test-model" in cost_optimizer.model_costs

    def test_calculate_cost(self, cost_optimizer, mock_response):
        """测试成本计算"""
        cost = cost_optimizer._calculate_cost("test_provider", mock_response)

        # 验证成本计算：100输入令牌 * 0.001 + 50输出令牌 * 0.002
        expected_cost = (100 / 1000 * 0.001) + (50 / 1000 * 0.002)
        assert abs(cost - expected_cost) < 0.0001

    def test_check_budget_limits(self, cost_optimizer):
        """测试预算限制检查"""
        budget_check = cost_optimizer._check_budget_limits()

        assert "alert_level" in budget_check
        assert "costs" in budget_check
        assert "usage_rates" in budget_check
        assert budget_check["alert_level"] == BudgetAlertLevel.INFO  # 初始状态应为INFO

    def test_get_provider_cost(self, cost_optimizer, mock_response):
        """测试获取Provider成本统计"""
        # 记录一些使用
        cost_optimizer.record_usage("provider1", mock_response)
        cost_optimizer.record_usage("provider1", mock_response)

        stats = cost_optimizer.get_provider_cost("provider1")

        assert stats["total_cost"] > 0
        assert stats["request_count"] == 2
        assert "test-model" in stats["models"]

    def test_get_cost_summary(self, cost_optimizer, mock_response):
        """测试获取成本摘要"""
        # 记录一些使用
        cost_optimizer.record_usage("provider1", mock_response)
        cost_optimizer.record_usage("provider2", mock_response)

        summary = cost_optimizer.get_cost_summary()

        assert summary["total_cost"] > 0
        assert summary["request_count"] == 2
        assert "provider1" in summary["providers"]
        assert "provider2" in summary["providers"]

    def test_can_make_request(self, cost_optimizer):
        """测试是否可以发起请求"""
        can_make, reason = cost_optimizer.can_make_request(estimated_cost=0.5)

        assert can_make is True
        assert "预算检查通过" in reason

    def test_estimate_cost(self, cost_optimizer):
        """测试成本预估"""
        estimated = cost_optimizer.estimate_cost(
            provider_name="test_provider",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
        )

        expected = (100 / 1000 * 0.001) + (50 / 1000 * 0.002)
        assert abs(estimated - expected) < 0.0001

    def test_get_optimization_suggestions(self, cost_optimizer, mock_response):
        """测试获取优化建议"""
        # 记录足够的使用以生成建议
        for i in range(20):
            cost_optimizer.record_usage(f"provider{i%3}", mock_response)

        suggestions = cost_optimizer.get_optimization_suggestions()

        assert isinstance(suggestions, list)
        # 可能有建议，也可能没有，取决于成本分布


class TestLocalModelProvider:
    """LocalModelProvider测试"""

    @pytest.fixture
    def local_provider_config(self):
        """本地Provider配置"""
        return {
            "name": "test_local",
            "type": "local",
            "model": "test-model",
            "base_url": "http://localhost:11434/api",
            "auto_discovery": False,  # 测试中禁用自动发现
            "performance_monitoring": True,
            "auto_model_selection": True,
        }

    @pytest.fixture
    async def local_provider(self, local_provider_config):
        """创建LocalModelProvider实例"""
        provider = LocalModelProvider(local_provider_config)
        await provider.start()
        return provider

    @pytest.fixture
    def mock_model_info(self):
        """模拟模型信息"""
        return LocalModelInfo(
            name="test-model-7b",
            model_type=LocalModelType.OLLAMA,
            size="7B",
            format="gguf",
            context_length=4096,
            parameters=7_000_000_000,
            performance_score=0.8,
        )

    @pytest.mark.asyncio
    async def test_model_discovery(self, local_provider):
        """测试模型发现"""
        # 由于自动发现已禁用，初始应为空
        models = await local_provider.get_available_models()
        assert isinstance(models, list)

    @pytest.mark.asyncio
    async def test_model_performance_recording(self, local_provider):
        """测试模型性能记录"""
        # 模拟性能记录
        await local_provider.model_manager.record_performance(
            model_name="test-model", success=True, tokens=100, latency=0.5
        )

        # 获取性能数据
        performance = await local_provider.get_model_performance("test-model")

        assert performance is not None
        assert performance["request_count"] == 1
        assert performance["success_count"] == 1
        assert performance["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_recommended_model(self, local_provider, mock_model_info):
        """测试获取推荐模型"""
        # 添加模拟模型
        local_provider.model_manager.models["model1"] = mock_model_info

        recommended = await local_provider.model_manager.get_recommended_model()

        assert recommended == "model1"

    def test_extract_model_size(self, local_provider):
        """测试提取模型大小"""
        test_cases = [
            ("llama2-7b", "7B"),
            ("mistral-7b-instruct", "7B"),
            ("codellama-13b", "13B"),
            ("mixtral-8x7b", "7B"),  # 注意：这可能会匹配到7b
            ("tiny-model-500M", "500M"),
            ("large-model-1.5B", "1.5B"),
            ("no-size-model", None),
        ]

        for model_name, expected_size in test_cases:
            size = local_provider.model_manager._extract_model_size(model_name)
            assert (
                size == expected_size
            ), f"Failed for {model_name}: expected {expected_size}, got {size}"

    def test_estimate_parameters(self, local_provider):
        """测试估算参数量"""
        test_cases = [
            ("7B", 7_000_000_000),
            ("13B", 13_000_000_000),
            ("1.5B", 1_500_000_000),
            ("500M", 500_000_000),
            ("unknown", None),
        ]

        for size_str, expected_params in test_cases:
            # 创建一个包含该大小的模型名
            model_name = f"test-model-{size_str}"
            params = local_provider.model_manager._estimate_parameters(model_name)
            assert (
                params == expected_params
            ), f"Failed for {size_str}: expected {expected_params}, got {params}"


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_enhanced_provider_with_cost_optimizer(self):
        """测试EnhancedProviderManager与CostOptimizer集成"""
        # 创建组件
        provider_config = {
            "health_check_interval": 1,
            "selection_strategy": "weighted_round_robin",
        }
        manager = EnhancedProviderManager(provider_config)

        cost_config = {"budget": {"total_budget": 100.0, "daily_limit": 10.0}}
        cost_optimizer = CostOptimizer(cost_config)

        # 设置成本优化器
        manager.cost_tracker = cost_optimizer

        # 注册Provider
        provider = MockLLMProvider("test_integration")
        await manager.register_provider("integrated", provider)

        # 生成请求
        response = await manager.generate_with_intelligent_fallback("Integration test")

        # 验证响应
        assert response.content == "Mock response from test_integration"

        # 验证成本记录
        assert len(cost_optimizer.cost_history) == 1
        # 使用注册的provider名称 "integrated"
        assert cost_optimizer.provider_costs["integrated"] > 0

    @pytest.mark.asyncio
    async def test_local_provider_with_model_manager(self):
        """测试LocalModelProvider与ModelManager集成"""
        config = {
            "name": "integration_test",
            "type": "local",
            "auto_discovery": False,
            "performance_monitoring": True,
        }

        provider = LocalModelProvider(config)

        # 验证组件已初始化
        assert provider.model_manager is not None
        assert provider.performance_monitoring is True

        # 清理
        await provider.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
