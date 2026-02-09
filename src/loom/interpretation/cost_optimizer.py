"""
成本优化器

跟踪LLM使用成本，提供预算控制、成本分析和优化建议。
支持实时成本监控、预算告警和成本优化策略。
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics

from ..utils.logging_config import get_logger
from .llm_provider import LLMResponse

logger = get_logger(__name__)


class BudgetAlertLevel(Enum):
    """预算告警级别"""

    INFO = "info"  # 信息级别
    WARNING = "warning"  # 警告级别
    CRITICAL = "critical"  # 严重级别
    EXCEEDED = "exceeded"  # 已超出


@dataclass
class CostRecord:
    """成本记录"""

    timestamp: datetime
    provider: str
    model: str
    cost: float
    tokens: int
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetLimit:
    """预算限制"""

    total_budget: float = 100.0  # 总预算（美元）
    daily_limit: float = 10.0  # 每日限制（美元）
    monthly_limit: float = 100.0  # 每月限制（美元）
    per_request_limit: float = 1.0  # 单次请求限制（美元）

    def validate(self) -> List[str]:
        """验证预算限制"""
        errors = []
        if self.total_budget <= 0:
            errors.append("总预算必须大于0")
        if self.daily_limit <= 0:
            errors.append("每日限制必须大于0")
        if self.monthly_limit <= 0:
            errors.append("每月限制必须大于0")
        if self.per_request_limit <= 0:
            errors.append("单次请求限制必须大于0")

        if self.daily_limit > self.total_budget:
            errors.append("每日限制不能超过总预算")
        if self.monthly_limit > self.total_budget:
            errors.append("每月限制不能超过总预算")

        return errors


@dataclass
class ProviderPricing:
    """Provider定价配置"""

    provider_name: str
    model_pricing: Dict[
        str, Dict[str, float]
    ]  # 模型名 -> {"input": 价格, "output": 价格}
    default_input_price: float = 0.0015  # 默认输入价格（美元/千令牌）
    default_output_price: float = 0.0020  # 默认输出价格（美元/千令牌）

    def get_price(self, model: str, token_type: str = "output") -> float:
        """获取指定模型和令牌类型的价格"""
        if model in self.model_pricing:
            model_prices = self.model_pricing[model]
            if token_type in model_prices:
                return model_prices[token_type]

        # 使用默认价格
        if token_type == "input":
            return self.default_input_price
        else:
            return self.default_output_price


class CostOptimizer:
    """成本优化器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.budget_limit = BudgetLimit(**config.get("budget", {}))

        # 成本记录
        self.cost_history: List[CostRecord] = []
        self.provider_costs: Dict[str, float] = {}
        self.model_costs: Dict[str, float] = {}

        # 定价配置
        self.pricing_configs: Dict[str, ProviderPricing] = self._load_pricing_configs(
            config.get("pricing", {})
        )

        # 告警系统
        self.alerts_sent: Dict[str, datetime] = {}
        self.alert_cooldown = config.get("alert_cooldown", 300)  # 告警冷却时间（秒）

        # 优化策略
        self.optimization_enabled = config.get("optimization_enabled", True)
        self.auto_switch_threshold = config.get(
            "auto_switch_threshold", 0.8
        )  # 预算使用率阈值

        logger.info(
            f"Initialized cost optimizer with budget: ${self.budget_limit.total_budget}"
        )

    def _load_pricing_configs(
        self, pricing_config: Dict[str, Any]
    ) -> Dict[str, ProviderPricing]:
        """加载定价配置"""
        configs = {}

        # 默认定价配置
        default_pricing = {
            "openai": ProviderPricing(
                provider_name="openai",
                model_pricing={
                    "gpt-4": {"input": 0.03, "output": 0.06},
                    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
                    "gpt-3.5-turbo-instruct": {"input": 0.0015, "output": 0.002},
                },
            ),
            "anthropic": ProviderPricing(
                provider_name="anthropic",
                model_pricing={
                    "claude-3-opus": {"input": 0.015, "output": 0.075},
                    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
                    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
                },
            ),
            "google": ProviderPricing(
                provider_name="google",
                model_pricing={
                    "gemini-pro": {"input": 0.000125, "output": 0.000375},
                    "gemini-ultra": {"input": 0.00125, "output": 0.00375},
                },
            ),
            "local": ProviderPricing(
                provider_name="local",
                model_pricing={},
                default_input_price=0.0,
                default_output_price=0.0,
            ),
        }

        # 合并用户配置
        for provider_name, provider_config in pricing_config.items():
            if provider_name in default_pricing:
                # 更新现有配置
                default_config = default_pricing[provider_name]
                if "model_pricing" in provider_config:
                    default_config.model_pricing.update(
                        provider_config["model_pricing"]
                    )
                if "default_input_price" in provider_config:
                    default_config.default_input_price = provider_config[
                        "default_input_price"
                    ]
                if "default_output_price" in provider_config:
                    default_config.default_output_price = provider_config[
                        "default_output_price"
                    ]
            else:
                # 创建新配置
                configs[provider_name] = ProviderPricing(
                    provider_name=provider_name,
                    model_pricing=provider_config.get("model_pricing", {}),
                    default_input_price=provider_config.get(
                        "default_input_price", 0.0015
                    ),
                    default_output_price=provider_config.get(
                        "default_output_price", 0.0020
                    ),
                )

        # 添加默认配置
        configs.update(default_pricing)
        return configs

    def record_usage(self, provider_name: str, response: LLMResponse) -> float:
        """记录使用成本"""
        # 计算成本
        cost = self._calculate_cost(provider_name, response)

        # 创建成本记录
        record = CostRecord(
            timestamp=datetime.now(),
            provider=provider_name,
            model=response.model,
            cost=cost,
            tokens=response.usage.get("total_tokens", 0) if response.usage else 0,
            request_id=response.metadata.get("request_id"),
            metadata={
                "usage": response.usage,
                "model": response.model,
                "provider": provider_name,
            },
        )

        # 添加到历史记录
        self.cost_history.append(record)

        # 更新统计
        self.provider_costs[provider_name] = (
            self.provider_costs.get(provider_name, 0.0) + cost
        )
        self.model_costs[response.model] = (
            self.model_costs.get(response.model, 0.0) + cost
        )

        # 检查预算限制
        budget_check = self._check_budget_limits()
        if budget_check["alert_level"] != BudgetAlertLevel.INFO:
            self._send_budget_alert(budget_check)

        # 清理旧记录（保留最近1000条）
        if len(self.cost_history) > 1000:
            self.cost_history = self.cost_history[-1000:]

        logger.debug(f"Recorded cost: ${cost:.6f} for {provider_name}/{response.model}")
        return cost

    def _calculate_cost(self, provider_name: str, response: LLMResponse) -> float:
        """计算成本"""
        # 获取定价配置
        pricing = self.pricing_configs.get(provider_name)
        if not pricing:
            # 使用默认定价
            pricing = ProviderPricing(
                provider_name="default",
                model_pricing={"default": {"input": 0.0015, "output": 0.0020}},
            )

        # 获取使用量
        usage = response.usage or {}
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

        # 如果没有令牌数，估算
        if total_tokens == 0:
            # 简单估算：每字符约0.25个令牌
            total_chars = len(response.content)
            total_tokens = total_chars // 4
            input_tokens = total_tokens // 2
            output_tokens = total_tokens // 2

        # 计算成本
        input_cost = (input_tokens / 1000) * pricing.get_price(response.model, "input")
        output_cost = (output_tokens / 1000) * pricing.get_price(
            response.model, "output"
        )
        total_cost = input_cost + output_cost

        return total_cost

    def _check_budget_limits(self) -> Dict[str, Any]:
        """检查预算限制"""
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        month_start = datetime(now.year, now.month, 1)

        # 计算各种时间范围的成本
        total_cost = sum(record.cost for record in self.cost_history)
        daily_cost = sum(
            record.cost
            for record in self.cost_history
            if record.timestamp >= today_start
        )
        monthly_cost = sum(
            record.cost
            for record in self.cost_history
            if record.timestamp >= month_start
        )

        # 计算使用率
        total_usage = (
            total_cost / self.budget_limit.total_budget
            if self.budget_limit.total_budget > 0
            else 0
        )
        daily_usage = (
            daily_cost / self.budget_limit.daily_limit
            if self.budget_limit.daily_limit > 0
            else 0
        )
        monthly_usage = (
            monthly_cost / self.budget_limit.monthly_limit
            if self.budget_limit.monthly_limit > 0
            else 0
        )

        # 确定告警级别
        alert_level = BudgetAlertLevel.INFO
        exceeded_limits = []

        if total_cost >= self.budget_limit.total_budget:
            alert_level = BudgetAlertLevel.EXCEEDED
            exceeded_limits.append("总预算")
        elif total_usage >= 0.9:
            alert_level = BudgetAlertLevel.CRITICAL
        elif total_usage >= 0.8:
            alert_level = BudgetAlertLevel.WARNING

        if daily_cost >= self.budget_limit.daily_limit:
            if alert_level.value < BudgetAlertLevel.EXCEEDED.value:
                alert_level = BudgetAlertLevel.EXCEEDED
            exceeded_limits.append("每日限制")
        elif daily_usage >= 0.9:
            if alert_level.value < BudgetAlertLevel.CRITICAL.value:
                alert_level = BudgetAlertLevel.CRITICAL
        elif daily_usage >= 0.8:
            if alert_level.value < BudgetAlertLevel.WARNING.value:
                alert_level = BudgetAlertLevel.WARNING

        if monthly_cost >= self.budget_limit.monthly_limit:
            if alert_level.value < BudgetAlertLevel.EXCEEDED.value:
                alert_level = BudgetAlertLevel.EXCEEDED
            exceeded_limits.append("每月限制")
        elif monthly_usage >= 0.9:
            if alert_level.value < BudgetAlertLevel.CRITICAL.value:
                alert_level = BudgetAlertLevel.CRITICAL
        elif monthly_usage >= 0.8:
            if alert_level.value < BudgetAlertLevel.WARNING.value:
                alert_level = BudgetAlertLevel.WARNING

        return {
            "alert_level": alert_level,
            "exceeded_limits": exceeded_limits,
            "costs": {
                "total": total_cost,
                "daily": daily_cost,
                "monthly": monthly_cost,
            },
            "usage_rates": {
                "total": total_usage,
                "daily": daily_usage,
                "monthly": monthly_usage,
            },
            "limits": {
                "total": self.budget_limit.total_budget,
                "daily": self.budget_limit.daily_limit,
                "monthly": self.budget_limit.monthly_limit,
            },
        }

    def _send_budget_alert(self, budget_check: Dict[str, Any]):
        """发送预算告警"""
        alert_key = (
            f"{budget_check['alert_level'].value}_{datetime.now().strftime('%Y%m%d%H')}"
        )

        # 检查冷却时间
        if alert_key in self.alerts_sent:
            last_sent = self.alerts_sent[alert_key]
            if (datetime.now() - last_sent).total_seconds() < self.alert_cooldown:
                return

        # 发送告警
        alert_level = budget_check["alert_level"]
        costs = budget_check["costs"]
        usage_rates = budget_check["usage_rates"]
        exceeded_limits = budget_check["exceeded_limits"]

        if alert_level == BudgetAlertLevel.EXCEEDED:
            logger.error(
                f"BUDGET EXCEEDED! Limits exceeded: {exceeded_limits}. "
                f"Total cost: ${costs['total']:.2f}, Daily: ${costs['daily']:.2f}, "
                f"Monthly: ${costs['monthly']:.2f}"
            )
        elif alert_level == BudgetAlertLevel.CRITICAL:
            logger.warning(
                f"BUDGET CRITICAL! Usage rates - Total: {usage_rates['total']:.1%}, "
                f"Daily: {usage_rates['daily']:.1%}, Monthly: {usage_rates['monthly']:.1%}"
            )
        elif alert_level == BudgetAlertLevel.WARNING:
            logger.warning(
                f"BUDGET WARNING! Usage rates - Total: {usage_rates['total']:.1%}, "
                f"Daily: {usage_rates['daily']:.1%}, Monthly: {usage_rates['monthly']:.1%}"
            )

        # 记录告警发送时间
        self.alerts_sent[alert_key] = datetime.now()

    def get_provider_cost(self, provider_name: str) -> Dict[str, Any]:
        """获取Provider成本统计"""
        provider_records = [r for r in self.cost_history if r.provider == provider_name]

        if not provider_records:
            return {
                "total_cost": 0.0,
                "request_count": 0,
                "avg_cost_per_request": 0.0,
                "models": {},
            }

        total_cost = sum(r.cost for r in provider_records)
        models = {}

        for record in provider_records:
            if record.model not in models:
                models[record.model] = {"total_cost": 0.0, "request_count": 0}
            models[record.model]["total_cost"] += record.cost
            models[record.model]["request_count"] += 1

        # 计算每个模型的平均成本
        for model_data in models.values():
            if model_data["request_count"] > 0:
                model_data["avg_cost"] = (
                    model_data["total_cost"] / model_data["request_count"]
                )

        return {
            "total_cost": total_cost,
            "request_count": len(provider_records),
            "avg_cost_per_request": (
                total_cost / len(provider_records) if provider_records else 0.0
            ),
            "models": models,
        }

    def get_cost_summary(
        self, time_range: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """获取成本摘要"""
        if time_range:
            cutoff = datetime.now() - time_range
            records = [r for r in self.cost_history if r.timestamp >= cutoff]
        else:
            records = self.cost_history

        if not records:
            return {
                "total_cost": 0.0,
                "request_count": 0,
                "providers": {},
                "models": {},
                "time_range": str(time_range) if time_range else "all",
            }

        total_cost = sum(r.cost for r in records)

        # Provider统计
        providers = {}
        for record in records:
            if record.provider not in providers:
                providers[record.provider] = {
                    "total_cost": 0.0,
                    "request_count": 0,
                    "models": {},
                }
            providers[record.provider]["total_cost"] += record.cost
            providers[record.provider]["request_count"] += 1

            # 模型统计
            if record.model not in providers[record.provider]["models"]:
                providers[record.provider]["models"][record.model] = {
                    "total_cost": 0.0,
                    "request_count": 0,
                }
            providers[record.provider]["models"][record.model][
                "total_cost"
            ] += record.cost
            providers[record.provider]["models"][record.model]["request_count"] += 1

        # 总体模型统计
        models = {}
        for record in records:
            if record.model not in models:
                models[record.model] = {
                    "total_cost": 0.0,
                    "request_count": 0,
                    "providers": {},
                }
            models[record.model]["total_cost"] += record.cost
            models[record.model]["request_count"] += 1

            # Provider统计
            if record.provider not in models[record.model]["providers"]:
                models[record.model]["providers"][record.provider] = {
                    "total_cost": 0.0,
                    "request_count": 0,
                }
            models[record.model]["providers"][record.provider][
                "total_cost"
            ] += record.cost
            models[record.model]["providers"][record.provider]["request_count"] += 1

        # 计算平均值
        for model_data in models.values():
            if model_data["request_count"] > 0:
                model_data["avg_cost_per_request"] = (
                    model_data["total_cost"] / model_data["request_count"]
                )

        for provider_data in providers.values():
            if provider_data["request_count"] > 0:
                provider_data["avg_cost_per_request"] = (
                    provider_data["total_cost"] / provider_data["request_count"]
                )

            # 计算每个模型的平均成本
            for model_data in provider_data["models"].values():
                if model_data["request_count"] > 0:
                    model_data["avg_cost"] = (
                        model_data["total_cost"] / model_data["request_count"]
                    )

        return {
            "total_cost": total_cost,
            "request_count": len(records),
            "avg_cost_per_request": total_cost / len(records) if records else 0.0,
            "providers": providers,
            "models": models,
            "time_range": str(time_range) if time_range else "all",
        }

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        suggestions = []

        # 获取最近一周的成本数据
        week_ago = datetime.now() - timedelta(days=7)
        recent_records = [r for r in self.cost_history if r.timestamp >= week_ago]

        if not recent_records:
            return suggestions

        # 分析成本分布
        provider_costs = {}
        model_costs = {}

        for record in recent_records:
            provider_costs[record.provider] = (
                provider_costs.get(record.provider, 0.0) + record.cost
            )
            model_costs[record.model] = model_costs.get(record.model, 0.0) + record.cost

        total_cost = sum(provider_costs.values())

        # 建议1：高成本Provider
        for provider, cost in provider_costs.items():
            if cost / total_cost > 0.5:  # 超过50%的成本
                suggestions.append(
                    {
                        "type": "high_cost_provider",
                        "provider": provider,
                        "cost_percentage": cost / total_cost,
                        "suggestion": f"考虑将部分请求切换到其他Provider，{provider}占总成本的{cost/total_cost:.1%}",
                        "priority": "high",
                    }
                )

        # 建议2：高成本模型
        for model, cost in model_costs.items():
            if cost / total_cost > 0.3:  # 超过30%的成本
                suggestions.append(
                    {
                        "type": "high_cost_model",
                        "model": model,
                        "cost_percentage": cost / total_cost,
                        "suggestion": f"考虑使用成本更低的模型替代{model}",
                        "priority": "medium",
                    }
                )

        # 建议3：预算使用情况
        budget_check = self._check_budget_limits()
        if budget_check["alert_level"] in [
            BudgetAlertLevel.WARNING,
            BudgetAlertLevel.CRITICAL,
        ]:
            suggestions.append(
                {
                    "type": "budget_warning",
                    "alert_level": budget_check["alert_level"].value,
                    "usage_rates": budget_check["usage_rates"],
                    "suggestion": "预算使用率较高，建议启用成本优化策略或增加预算",
                    "priority": "high",
                }
            )

        # 建议4：成本效率分析
        if len(recent_records) > 10:
            # 计算每个Provider的平均成本
            provider_stats = {}
            for provider in set(r.provider for r in recent_records):
                provider_records = [r for r in recent_records if r.provider == provider]
                if provider_records:
                    total_cost = sum(r.cost for r in provider_records)
                    avg_cost = total_cost / len(provider_records)
                    provider_stats[provider] = avg_cost

            # 找出成本最高的Provider
            if provider_stats:
                max_provider = max(provider_stats.items(), key=lambda x: x[1])
                min_provider = min(provider_stats.items(), key=lambda x: x[1])

                if max_provider[1] > min_provider[1] * 2:  # 成本相差2倍以上
                    suggestions.append(
                        {
                            "type": "cost_efficiency",
                            "high_cost_provider": max_provider[0],
                            "low_cost_provider": min_provider[0],
                            "cost_ratio": max_provider[1] / min_provider[1],
                            "suggestion": f"{max_provider[0]}的平均成本是{min_provider[0]}的{max_provider[1]/min_provider[1]:.1f}倍，考虑更多使用{min_provider[0]}",
                            "priority": "medium",
                        }
                    )

        return suggestions

    def can_make_request(self, estimated_cost: float = 0.0) -> Tuple[bool, str]:
        """检查是否可以发起新请求（预算检查）"""
        budget_check = self._check_budget_limits()

        # 检查是否已超出任何限制
        if budget_check["exceeded_limits"]:
            return (
                False,
                f"预算限制已超出: {', '.join(budget_check['exceeded_limits'])}",
            )

        # 检查单次请求限制
        if estimated_cost > self.budget_limit.per_request_limit:
            return (
                False,
                f"预估成本${estimated_cost:.4f}超过单次请求限制${self.budget_limit.per_request_limit:.2f}",
            )

        # 检查总预算
        total_cost = budget_check["costs"]["total"]
        if total_cost + estimated_cost > self.budget_limit.total_budget:
            return False, f"预估成本将超出总预算"

        # 检查每日限制
        daily_cost = budget_check["costs"]["daily"]
        if daily_cost + estimated_cost > self.budget_limit.daily_limit:
            return False, f"预估成本将超出每日限制"

        # 检查每月限制
        monthly_cost = budget_check["costs"]["monthly"]
        if monthly_cost + estimated_cost > self.budget_limit.monthly_limit:
            return False, f"预估成本将超出每月限制"

        return True, "预算检查通过"

    def estimate_cost(
        self, provider_name: str, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """预估成本"""
        pricing = self.pricing_configs.get(provider_name)
        if not pricing:
            pricing = ProviderPricing(provider_name="default")

        input_cost = (input_tokens / 1000) * pricing.get_price(model, "input")
        output_cost = (output_tokens / 1000) * pricing.get_price(model, "output")

        return input_cost + output_cost

    def reset_budget(self, new_budget: Optional[BudgetLimit] = None):
        """重置预算"""
        if new_budget:
            self.budget_limit = new_budget

        # 清空成本历史（可选）
        # self.cost_history = []
        # self.provider_costs = {}
        # self.model_costs = {}

        logger.info(
            f"Budget reset to: total=${self.budget_limit.total_budget}, "
            f"daily=${self.budget_limit.daily_limit}"
        )

    def export_cost_data(self, format: str = "json") -> str:
        """导出成本数据"""
        if format == "json":
            data = {
                "budget_limit": {
                    "total_budget": self.budget_limit.total_budget,
                    "daily_limit": self.budget_limit.daily_limit,
                    "monthly_limit": self.budget_limit.monthly_limit,
                    "per_request_limit": self.budget_limit.per_request_limit,
                },
                "cost_summary": self.get_cost_summary(),
                "optimization_suggestions": self.get_optimization_suggestions(),
                "export_timestamp": datetime.now().isoformat(),
            }
            return json.dumps(data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def periodic_report(self, interval: int = 3600):
        """定期生成成本报告"""
        while True:
            await asyncio.sleep(interval)

            try:
                report = self.get_cost_summary(timedelta(hours=24))  # 最近24小时
                budget_check = self._check_budget_limits()

                logger.info(
                    f"Cost Report - Last 24h: ${report['total_cost']:.2f}, "
                    f"Total: ${budget_check['costs']['total']:.2f}/"
                    f"${self.budget_limit.total_budget:.2f} "
                    f"({budget_check['usage_rates']['total']:.1%})"
                )

                # 如果有警告或严重告警，记录详细信息
                if budget_check["alert_level"] != BudgetAlertLevel.INFO:
                    logger.warning(
                        f"Budget Alert: {budget_check['alert_level'].value}, "
                        f"Exceeded: {budget_check['exceeded_limits']}"
                    )

            except Exception as e:
                logger.error(f"Error generating periodic cost report: {e}")
