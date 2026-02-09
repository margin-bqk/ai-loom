"""
增强LLM Provider管理器

提供智能故障转移、健康监控、负载均衡和成本优化的Provider管理功能。
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
from enum import Enum

from ..utils.logging_config import get_logger
from .llm_provider import LLMProvider, LLMResponse, ProviderManager

logger = get_logger(__name__)


class ProviderPriority(Enum):
    """Provider优先级策略"""

    COST = "cost"  # 成本优先
    SPEED = "speed"  # 速度优先
    QUALITY = "quality"  # 质量优先
    BALANCED = "balanced"  # 平衡策略


@dataclass
class ProviderHealth:
    """Provider健康状态"""

    healthy: bool = True
    last_check: datetime = field(default_factory=datetime.now)
    success_rate: float = 1.0
    avg_latency: float = 0.0
    error_count: int = 0
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    last_success: Optional[datetime] = None


@dataclass
class ProviderMetrics:
    """Provider性能指标"""

    request_count: int = 0
    success_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    latency_history: List[float] = field(default_factory=list)
    error_history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count

    @property
    def avg_latency(self) -> float:
        """计算平均延迟"""
        if not self.latency_history:
            return 0.0
        return statistics.mean(self.latency_history)

    @property
    def p95_latency(self) -> float:
        """计算95百分位延迟"""
        if not self.latency_history:
            return 0.0
        return statistics.quantiles(self.latency_history, n=20)[18]  # 95th percentile


class ProviderHealthMonitor:
    """Provider健康监控器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_checks: Dict[str, ProviderHealth] = {}
        self.metrics: Dict[str, ProviderMetrics] = {}
        self.check_interval = config.get("health_check_interval", 60)  # 秒
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}

    async def monitor_provider(self, name: str, provider: LLMProvider):
        """开始监控Provider"""
        self.health_checks[name] = ProviderHealth()
        self.metrics[name] = ProviderMetrics()

        # 启动健康检查任务
        task = asyncio.create_task(self._monitor_loop(name, provider))
        self._monitoring_tasks[name] = task

    async def _monitor_loop(self, name: str, provider: LLMProvider):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self._perform_health_check(name, provider)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {name}: {e}")

    async def _perform_health_check(self, name: str, provider: LLMProvider):
        """执行健康检查"""
        try:
            start_time = time.time()
            # 简单的ping检查（使用小提示）
            test_prompt = "Hello, are you working?"
            response = await provider.generate(test_prompt, max_tokens=10)
            latency = time.time() - start_time

            health = self.health_checks[name]
            health.healthy = True
            health.last_check = datetime.now()
            health.last_success = datetime.now()
            health.success_rate = self.metrics[name].success_rate
            health.avg_latency = self.metrics[name].avg_latency
            health.consecutive_failures = 0

            logger.debug(f"Health check passed for {name}, latency: {latency:.2f}s")

        except Exception as e:
            health = self.health_checks[name]
            health.healthy = False
            health.last_check = datetime.now()
            health.last_error = str(e)
            health.error_count += 1
            health.consecutive_failures += 1

            logger.warning(f"Health check failed for {name}: {e}")

    async def record_success(self, name: str, response: LLMResponse, latency: float):
        """记录成功请求"""
        if name not in self.metrics:
            self.metrics[name] = ProviderMetrics()

        metrics = self.metrics[name]
        metrics.request_count += 1
        metrics.success_count += 1
        metrics.latency_history.append(latency)

        # 限制历史记录大小
        if len(metrics.latency_history) > 100:
            metrics.latency_history = metrics.latency_history[-100:]

        # 更新健康状态
        if name in self.health_checks:
            health = self.health_checks[name]
            health.last_success = datetime.now()
            health.consecutive_failures = 0
            health.success_rate = metrics.success_rate
            health.avg_latency = metrics.avg_latency

    async def record_failure(self, name: str, error: str):
        """记录失败请求"""
        if name not in self.metrics:
            self.metrics[name] = ProviderMetrics()

        metrics = self.metrics[name]
        metrics.request_count += 1
        metrics.error_history.append(
            {"timestamp": datetime.now().isoformat(), "error": error}
        )

        # 限制错误历史大小
        if len(metrics.error_history) > 50:
            metrics.error_history = metrics.error_history[-50:]

        # 更新健康状态
        if name in self.health_checks:
            health = self.health_checks[name]
            health.last_error = error
            health.error_count += 1
            health.consecutive_failures += 1

            # 如果连续失败超过阈值，标记为不健康
            if health.consecutive_failures >= 3:
                health.healthy = False

    async def get_provider_health(self, name: str) -> Dict[str, Any]:
        """获取Provider健康状态"""
        if name not in self.health_checks:
            return {"healthy": False, "error": "Provider not monitored"}

        health = self.health_checks[name]
        metrics = self.metrics.get(name, ProviderMetrics())

        return {
            "healthy": health.healthy,
            "last_check": health.last_check.isoformat() if health.last_check else None,
            "success_rate": health.success_rate,
            "avg_latency": health.avg_latency,
            "error_count": health.error_count,
            "consecutive_failures": health.consecutive_failures,
            "last_error": health.last_error,
            "last_success": (
                health.last_success.isoformat() if health.last_success else None
            ),
            "metrics": {
                "request_count": metrics.request_count,
                "success_count": metrics.success_count,
                "success_rate": metrics.success_rate,
                "avg_latency": metrics.avg_latency,
                "p95_latency": metrics.p95_latency,
                "total_tokens": metrics.total_tokens,
            },
        }

    async def stop_monitoring(self, name: str):
        """停止监控Provider"""
        if name in self._monitoring_tasks:
            task = self._monitoring_tasks[name]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._monitoring_tasks[name]

        if name in self.health_checks:
            del self.health_checks[name]

        if name in self.metrics:
            del self.metrics[name]


class ProviderLoadBalancer:
    """Provider负载均衡器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self.weights: Dict[str, float] = {}
        self.selection_strategy = config.get(
            "selection_strategy", "weighted_round_robin"
        )
        self._last_selected: Dict[str, datetime] = {}

    def add_provider(self, name: str, provider: LLMProvider):
        """添加Provider"""
        self.providers[name] = provider
        self.weights[name] = 1.0  # 默认权重
        self._last_selected[name] = datetime.now()

    def update_weight(self, name: str, weight: float):
        """更新Provider权重"""
        if name in self.weights:
            self.weights[name] = max(0.1, min(weight, 10.0))  # 限制在0.1-10之间

    def get_weight(self, name: str) -> float:
        """获取Provider权重"""
        return self.weights.get(name, 1.0)

    async def select_provider(
        self,
        prompt: str,
        model: Optional[str] = None,
        priority: ProviderPriority = ProviderPriority.BALANCED,
        health_monitor: Optional[ProviderHealthMonitor] = None,
    ) -> str:
        """选择最佳Provider"""
        if not self.providers:
            raise ValueError("No providers available")

        # 过滤可用的Provider
        available_providers = []
        for name, provider in self.providers.items():
            if not provider.enabled:
                continue

            # 检查健康状态
            if health_monitor:
                health = await health_monitor.get_provider_health(name)
                if not health.get("healthy", True):
                    continue

            available_providers.append(name)

        if not available_providers:
            raise ValueError("No healthy providers available")

        # 根据优先级策略选择
        if priority == ProviderPriority.COST:
            return self._select_by_cost(available_providers)
        elif priority == ProviderPriority.SPEED:
            return await self._select_by_speed(available_providers, health_monitor)
        elif priority == ProviderPriority.QUALITY:
            return await self._select_by_quality(available_providers, health_monitor)
        else:  # BALANCED
            return await self._select_balanced(available_providers, health_monitor)

    def _select_by_cost(self, providers: List[str]) -> str:
        """成本优先选择"""
        # 简单实现：选择第一个Provider
        # 实际实现应考虑每个Provider的成本模型
        return providers[0]

    async def _select_by_speed(
        self, providers: List[str], health_monitor: Optional[ProviderHealthMonitor]
    ) -> str:
        """速度优先选择"""
        if not health_monitor or len(providers) == 1:
            return providers[0]

        # 选择延迟最低的Provider
        fastest_provider = providers[0]
        fastest_latency = float("inf")

        for name in providers:
            health = await health_monitor.get_provider_health(name)
            latency = health.get("metrics", {}).get("avg_latency", float("inf"))
            if latency < fastest_latency:
                fastest_latency = latency
                fastest_provider = name

        return fastest_provider

    async def _select_by_quality(
        self, providers: List[str], health_monitor: Optional[ProviderHealthMonitor]
    ) -> str:
        """质量优先选择"""
        if not health_monitor or len(providers) == 1:
            return providers[0]

        # 选择成功率最高的Provider
        best_provider = providers[0]
        best_success_rate = 0.0

        for name in providers:
            health = await health_monitor.get_provider_health(name)
            success_rate = health.get("metrics", {}).get("success_rate", 0.0)
            if success_rate > best_success_rate:
                best_success_rate = success_rate
                best_provider = name

        return best_provider

    async def _select_balanced(
        self, providers: List[str], health_monitor: Optional[ProviderHealthMonitor]
    ) -> str:
        """平衡策略选择"""
        # 加权随机选择，考虑权重、延迟和成功率
        if len(providers) == 1:
            return providers[0]

        import random

        # 计算每个Provider的得分
        scores = {}
        for name in providers:
            score = self.weights.get(name, 1.0)

            if health_monitor:
                health = await health_monitor.get_provider_health(name)
                success_rate = health.get("metrics", {}).get("success_rate", 0.5)
                avg_latency = health.get("metrics", {}).get("avg_latency", 1.0)

                # 成功率越高得分越高
                score *= success_rate
                # 延迟越低得分越高
                score *= 1.0 / max(avg_latency, 0.1)

            scores[name] = max(0.1, score)

        # 加权随机选择
        total_score = sum(scores.values())
        if total_score == 0:
            return random.choice(providers)

        rand_val = random.uniform(0, total_score)
        cumulative = 0
        for name, score in scores.items():
            cumulative += score
            if rand_val <= cumulative:
                return name

        return providers[0]


class FallbackStrategy:
    """故障转移策略"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fallback_order: List[str] = config.get("fallback_order", [])
        self.max_fallback_attempts = config.get("max_fallback_attempts", 3)
        self.fallback_delay = config.get("fallback_delay", 0.5)  # 秒

    async def get_fallback(
        self,
        failed_provider: str,
        error: Exception,
        prompt: str,
        kwargs: Dict[str, Any],
        available_providers: List[str],
        health_monitor: Optional[ProviderHealthMonitor] = None,
    ) -> Optional[str]:
        """获取故障转移Provider"""
        # 从回退顺序中排除失败的Provider
        candidates = [
            p
            for p in self.fallback_order
            if p != failed_provider and p in available_providers
        ]

        if not candidates:
            # 如果没有配置回退顺序，使用所有可用的Provider
            candidates = [p for p in available_providers if p != failed_provider]

        # 根据错误类型选择回退策略
        error_str = str(error).lower()

        # 如果是超时错误，优先选择速度快的Provider
        if "timeout" in error_str or "time out" in error_str:
            # 简单实现：选择第一个候选
            return candidates[0] if candidates else None

        # 如果是认证错误，可能需要切换API密钥
        if (
            "auth" in error_str
            or "key" in error_str
            or "401" in error_str
            or "403" in error_str
        ):
            logger.warning(
                f"Authentication error for {failed_provider}, trying fallback"
            )
            return candidates[0] if candidates else None

        # 默认：选择第一个可用的Provider
        return candidates[0] if candidates else None


class EnhancedProviderManager(ProviderManager):
    """增强Provider管理器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.health_monitor = ProviderHealthMonitor(config)
        self.load_balancer = ProviderLoadBalancer(config)
        self.fallback_strategy = FallbackStrategy(config)
        self.cost_tracker = None  # 将在集成CostOptimizer时设置

    async def register_provider(self, name: str, provider: LLMProvider):
        """注册Provider"""
        super().register_provider(name, provider)

        # 启动健康监控
        await self.health_monitor.monitor_provider(name, provider)

        # 更新负载均衡器
        self.load_balancer.add_provider(name, provider)

        logger.info(f"Registered enhanced provider: {name}")

    async def unregister_provider(self, name: str):
        """注销Provider"""
        if name in self.providers:
            # 停止健康监控
            await self.health_monitor.stop_monitoring(name)

            # 从负载均衡器移除
            if name in self.load_balancer.providers:
                del self.load_balancer.providers[name]
            if name in self.load_balancer.weights:
                del self.load_balancer.weights[name]

            # 从父类移除
            del self.providers[name]

            logger.info(f"Unregistered enhanced provider: {name}")

    async def generate_with_intelligent_fallback(
        self,
        prompt: str,
        priority: ProviderPriority = ProviderPriority.BALANCED,
        **kwargs,
    ) -> LLMResponse:
        """智能故障转移生成"""
        start_time = time.time()

        try:
            # 1. 选择最佳Provider
            selected_provider = await self.load_balancer.select_provider(
                prompt, kwargs.get("model"), priority, self.health_monitor
            )

            logger.info(
                f"Selected provider: {selected_provider} with priority: {priority.value}"
            )

            # 2. 尝试生成
            provider = self.providers[selected_provider]
            response = await provider.generate(prompt, **kwargs)

            # 3. 记录成功
            latency = time.time() - start_time
            await self.health_monitor.record_success(
                selected_provider, response, latency
            )

            # 4. 记录成本（如果成本跟踪器可用）
            if self.cost_tracker:
                self.cost_tracker.record_usage(selected_provider, response)

            return response

        except Exception as e:
            # 记录失败
            latency = time.time() - start_time
            await self.health_monitor.record_failure(selected_provider, str(e))

            logger.warning(f"Provider {selected_provider} failed: {e}")

            # 执行故障转移
            available_providers = list(self.providers.keys())
            fallback_provider = await self.fallback_strategy.get_fallback(
                selected_provider,
                e,
                prompt,
                kwargs,
                available_providers,
                self.health_monitor,
            )

            if fallback_provider and fallback_provider != selected_provider:
                logger.info(
                    f"Falling back from {selected_provider} to {fallback_provider}"
                )

                # 等待回退延迟
                if self.fallback_strategy.fallback_delay > 0:
                    await asyncio.sleep(self.fallback_strategy.fallback_delay)

                # 尝试回退Provider
                try:
                    provider = self.providers[fallback_provider]
                    response = await provider.generate(prompt, **kwargs)

                    # 记录回退成功
                    total_latency = time.time() - start_time
                    await self.health_monitor.record_success(
                        fallback_provider, response, total_latency
                    )

                    if self.cost_tracker:
                        self.cost_tracker.record_usage(fallback_provider, response)

                    return response

                except Exception as fallback_error:
                    logger.error(
                        f"Fallback provider {fallback_provider} also failed: {fallback_error}"
                    )

            # 如果所有Provider都失败，返回降级响应
            logger.error(f"All providers failed for prompt: {prompt[:100]}...")
            return await self._generate_degraded_response(prompt, **kwargs)

    async def _generate_degraded_response(self, prompt: str, **kwargs) -> LLMResponse:
        """生成降级响应"""
        logger.warning("Generating degraded response due to all provider failures")

        return LLMResponse(
            content=f"[系统降级] 所有LLM Provider均不可用。原始提示长度：{len(prompt)}字符。",
            model="degraded-fallback",
            usage={"input_tokens": len(prompt) // 4, "output_tokens": 50},
            metadata={
                "degraded": True,
                "timestamp": datetime.now().isoformat(),
                "error": "All providers failed",
                "prompt_length": len(prompt),
            },
        )

    async def get_provider_stats(self) -> Dict[str, Any]:
        """获取Provider统计信息"""
        stats = {
            "providers": {},
            "overall": {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "success_rate": 0.0,
                "avg_latency": 0.0,
                "healthy_providers": 0,
            },
        }

        total_latency = 0.0
        latency_count = 0

        for name, provider in self.providers.items():
            # 获取Provider基本统计
            provider_stats = (
                provider.get_stats() if hasattr(provider, "get_stats") else {}
            )

            # 获取健康状态
            health = await self.health_monitor.get_provider_health(name)

            # 获取负载均衡权重
            weight = self.load_balancer.get_weight(name)

            # 获取成本信息
            cost_info = {}
            if self.cost_tracker and hasattr(self.cost_tracker, "get_provider_cost"):
                cost_info = self.cost_tracker.get_provider_cost(name)

            stats["providers"][name] = {
                **provider_stats,
                "health": health,
                "load_balancing_weight": weight,
                "cost": cost_info,
                "enabled": provider.enabled,
                "provider_type": provider.provider_type,
                "model": provider.model,
            }

            # 更新总体统计
            stats["overall"]["total_requests"] += provider_stats.get("request_count", 0)
            stats["overall"]["total_tokens"] += provider_stats.get("total_tokens", 0)
            stats["overall"]["total_cost"] += cost_info.get("total_cost", 0.0)

            if health.get("healthy", False):
                stats["overall"]["healthy_providers"] += 1

            # 累加延迟
            metrics = health.get("metrics", {})
            avg_latency = metrics.get("avg_latency", 0)
            if avg_latency > 0:
                total_latency += avg_latency
                latency_count += 1

        # 计算总体成功率
        total_success = sum(
            1
            for provider_stats in stats["providers"].values()
            if provider_stats["health"].get("healthy", False)
        )
        stats["overall"]["success_rate"] = (
            total_success / len(self.providers) if self.providers else 0
        )

        # 计算平均延迟
        if latency_count > 0:
            stats["overall"]["avg_latency"] = total_latency / latency_count

        return stats

    async def update_provider_weights(self, weights: Dict[str, float]):
        """更新Provider权重"""
        for name, weight in weights.items():
            if name in self.load_balancer.weights:
                self.load_balancer.update_weight(name, weight)
                logger.info(f"Updated weight for {name}: {weight}")

    async def disable_provider(self, name: str, reason: str = ""):
        """禁用Provider"""
        if name in self.providers:
            self.providers[name].enabled = False
            logger.warning(f"Disabled provider {name}: {reason}")

    async def enable_provider(self, name: str):
        """启用Provider"""
        if name in self.providers:
            self.providers[name].enabled = True
            logger.info(f"Enabled provider {name}")

    async def health_check_all(self) -> Dict[str, Any]:
        """检查所有Provider的健康状态"""
        results = {}
        for name, provider in self.providers.items():
            try:
                # 使用健康监控器的检查
                health = await self.health_monitor.get_provider_health(name)
                results[name] = health
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e), "provider": name}
        return results

    async def close_all(self):
        """关闭所有Provider"""
        # 停止所有监控任务
        for name in list(self.health_monitor._monitoring_tasks.keys()):
            await self.health_monitor.stop_monitoring(name)

        # 关闭所有Provider连接
        await super().close_all()

        logger.info("Enhanced provider manager closed")
