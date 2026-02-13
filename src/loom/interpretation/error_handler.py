"""
错误处理和降级机制

提供统一的错误处理、重试策略和降级机制。
支持Provider故障检测、自动切换、请求重试和优雅降级。
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from ..utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 轻微错误，可重试
    MEDIUM = "medium"  # 中等错误，可能需要降级
    HIGH = "high"  # 严重错误，需要切换Provider
    CRITICAL = "critical"  # 致命错误，需要人工干预


class ErrorCategory(Enum):
    """错误类别"""

    NETWORK = "network"  # 网络错误
    TIMEOUT = "timeout"  # 超时错误
    AUTHENTICATION = "auth"  # 认证错误
    RATE_LIMIT = "rate_limit"  # 速率限制
    QUOTA_EXCEEDED = "quota"  # 配额超限
    MODEL_UNAVAILABLE = "model_unavailable"  # 模型不可用
    INVALID_REQUEST = "invalid_request"  # 无效请求
    SERVER_ERROR = "server_error"  # 服务器错误
    UNKNOWN = "unknown"  # 未知错误


@dataclass
class ErrorInfo:
    """错误信息"""

    timestamp: datetime = field(default_factory=datetime.now)
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    provider: str = "unknown"
    error_message: str = ""
    error_code: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "severity": self.severity.value,
            "provider": self.provider,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


@dataclass
class RetryPolicy:
    """重试策略"""

    max_retries: int = 3
    base_delay: float = 1.0  # 基础延迟（秒）
    max_delay: float = 30.0  # 最大延迟（秒）
    jitter: bool = True  # 是否添加随机抖动
    exponential_backoff: bool = True  # 是否使用指数退避

    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.exponential_backoff:
            delay = self.base_delay * (2 ** (attempt - 1))
        else:
            delay = self.base_delay

        # 限制最大延迟
        delay = min(delay, self.max_delay)

        # 添加随机抖动
        if self.jitter:
            delay = delay * (0.5 + random.random())

        return delay


@dataclass
class CircuitBreakerState:
    """熔断器状态"""

    is_open: bool = False
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    opened_at: Optional[datetime] = None

    def should_allow_request(self, reset_timeout: float = 60.0) -> bool:
        """是否允许请求"""
        if not self.is_open:
            return True

        # 检查是否应该重置
        if self.opened_at:
            elapsed = (datetime.now() - self.opened_at).total_seconds()
            if elapsed >= reset_timeout:
                # 尝试半开状态
                self.is_open = False
                logger.info(
                    f"Circuit breaker transitioning to half-open after {elapsed:.1f}s"
                )
                return True

        return False

    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        # 如果失败次数过多，打开熔断器
        if self.failure_count >= 5 and not self.is_open:
            self.is_open = True
            self.opened_at = datetime.now()
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    def record_success(self):
        """记录成功"""
        self.failure_count = 0
        self.last_success_time = datetime.now()

        # 如果熔断器是打开的，关闭它
        if self.is_open:
            self.is_open = False
            self.opened_at = None
            logger.info("Circuit breaker closed after successful request")


class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self.error_history: List[ErrorInfo] = []
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.max_history_size = 1000

        # Provider健康状态
        self.provider_health: Dict[str, Dict[str, Any]] = {}

        logger.info("ErrorHandler initialized")

    def record_error(self, error_info: ErrorInfo):
        """记录错误"""
        self.error_history.append(error_info)

        # 限制历史记录大小
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size :]

        # 更新Provider健康状态
        provider = error_info.provider
        if provider not in self.provider_health:
            self.provider_health[provider] = {
                "total_errors": 0,
                "recent_errors": 0,
                "last_error_time": None,
                "error_categories": {},
            }

        health = self.provider_health[provider]
        health["total_errors"] += 1
        health["recent_errors"] += 1
        health["last_error_time"] = error_info.timestamp

        # 记录错误类别
        category = error_info.category.value
        health["error_categories"][category] = (
            health["error_categories"].get(category, 0) + 1
        )

        # 更新熔断器状态
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreakerState()

        circuit_breaker = self.circuit_breakers[provider]

        # 根据错误严重程度决定是否记录失败
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            circuit_breaker.record_failure()

        logger.warning(f"Recorded error for {provider}: {error_info.error_message}")

    def record_success(self, provider: str):
        """记录成功"""
        if provider in self.circuit_breakers:
            self.circuit_breakers[provider].record_success()

        # 重置最近错误计数
        if provider in self.provider_health:
            self.provider_health[provider]["recent_errors"] = 0

    def can_retry(self, error_info: ErrorInfo, retry_policy: RetryPolicy) -> bool:
        """判断是否可以重试"""
        # 检查错误类别
        non_retryable_categories = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.INVALID_REQUEST,
            ErrorCategory.QUOTA_EXCEEDED,
        ]

        if error_info.category in non_retryable_categories:
            return False

        # 检查重试次数
        if error_info.retry_count >= retry_policy.max_retries:
            return False

        # 检查熔断器
        if error_info.provider in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[error_info.provider]
            if not circuit_breaker.should_allow_request():
                return False

        return True

    def get_retry_delay(
        self, error_info: ErrorInfo, retry_policy: RetryPolicy
    ) -> float:
        """获取重试延迟"""
        return retry_policy.calculate_delay(error_info.retry_count + 1)

    def get_provider_health(self, provider: str) -> Dict[str, Any]:
        """获取Provider健康状态"""
        if provider not in self.provider_health:
            return {
                "healthy": True,
                "total_errors": 0,
                "recent_errors": 0,
                "last_error_time": None,
                "error_rate": 0.0,
            }

        health = self.provider_health[provider].copy()

        # 计算错误率（基于最近100次请求）
        recent_errors = health.get("recent_errors", 0)
        error_rate = min(recent_errors / 100.0, 1.0) if recent_errors > 0 else 0.0

        health["healthy"] = error_rate < 0.5  # 错误率低于50%视为健康
        health["error_rate"] = error_rate

        # 检查熔断器状态
        if provider in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[provider]
            health["circuit_breaker_open"] = circuit_breaker.is_open
            health["failure_count"] = circuit_breaker.failure_count
            if circuit_breaker.opened_at:
                health["circuit_breaker_opened_at"] = (
                    circuit_breaker.opened_at.isoformat()
                )

        return health

    def get_best_provider(
        self, providers: List[str], exclude: Optional[List[str]] = None
    ) -> Optional[str]:
        """获取最佳Provider（基于健康状态）"""
        if exclude is None:
            exclude = []

        available_providers = [p for p in providers if p not in exclude]
        if not available_providers:
            return None

        # 评估每个Provider的健康状态
        provider_scores = {}
        for provider in available_providers:
            health = self.get_provider_health(provider)

            # 计算分数（越高越好）
            score = 100.0

            # 减去错误率
            score -= health.get("error_rate", 0.0) * 50

            # 检查熔断器
            if health.get("circuit_breaker_open", False):
                score -= 30

            # 减去最近错误数
            score -= health.get("recent_errors", 0) * 5

            provider_scores[provider] = score

        # 返回分数最高的Provider
        best_provider = max(provider_scores.items(), key=lambda x: x[1])[0]
        logger.debug(
            f"Selected best provider: {best_provider} with score {provider_scores[best_provider]:.1f}"
        )

        return best_provider

    def classify_error(self, error: Exception, provider: str) -> ErrorInfo:
        """分类错误"""
        error_message = str(error)
        error_category = ErrorCategory.UNKNOWN
        error_severity = ErrorSeverity.MEDIUM

        # 根据错误类型分类
        if isinstance(error, TimeoutError) or "timeout" in error_message.lower():
            error_category = ErrorCategory.TIMEOUT
            error_severity = ErrorSeverity.MEDIUM
        elif (
            isinstance(error, ConnectionError) or "connection" in error_message.lower()
        ):
            error_category = ErrorCategory.NETWORK
            error_severity = ErrorSeverity.MEDIUM
        elif "auth" in error_message.lower() or "unauthorized" in error_message.lower():
            error_category = ErrorCategory.AUTHENTICATION
            error_severity = ErrorSeverity.HIGH
        elif (
            "rate limit" in error_message.lower()
            or "too many requests" in error_message.lower()
        ):
            error_category = ErrorCategory.RATE_LIMIT
            error_severity = ErrorSeverity.MEDIUM
        elif (
            "quota" in error_message.lower()
            or "insufficient credits" in error_message.lower()
        ):
            error_category = ErrorCategory.QUOTA_EXCEEDED
            error_severity = ErrorSeverity.HIGH
        elif (
            "model" in error_message.lower() and "unavailable" in error_message.lower()
        ):
            error_category = ErrorCategory.MODEL_UNAVAILABLE
            error_severity = ErrorSeverity.MEDIUM
        elif (
            "invalid" in error_message.lower() or "bad request" in error_message.lower()
        ):
            error_category = ErrorCategory.INVALID_REQUEST
            error_severity = ErrorSeverity.HIGH
        elif (
            "server error" in error_message.lower()
            or "internal error" in error_message.lower()
        ):
            error_category = ErrorCategory.SERVER_ERROR
            error_severity = ErrorSeverity.HIGH

        return ErrorInfo(
            category=error_category,
            severity=error_severity,
            provider=provider,
            error_message=error_message,
            error_code=getattr(error, "code", None),
        )

    def get_error_stats(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """获取错误统计"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_errors = [e for e in self.error_history if e.timestamp > cutoff_time]

        # 按Provider统计
        provider_stats = {}
        for error in recent_errors:
            provider = error.provider
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "total": 0,
                    "by_category": {},
                    "by_severity": {},
                }

            stats = provider_stats[provider]
            stats["total"] += 1

            # 按类别统计
            category = error.category.value
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # 按严重程度统计
            severity = error.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

        return {
            "total_errors": len(recent_errors),
            "time_window_minutes": time_window_minutes,
            "providers": provider_stats,
            "timestamp": datetime.now().isoformat(),
        }

    def clear_history(self):
        """清除历史记录"""
        self.error_history.clear()
        logger.info("Error history cleared")


class FallbackStrategy:
    """降级策略"""

    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.strategies = {
            "model_downgrade": self._model_downgrade,
            "provider_switch": self._provider_switch,
            "response_caching": self._response_caching,
            "simplified_response": self._simplified_response,
        }

    async def execute_fallback(
        self,
        original_request: Dict[str, Any],
        error: ErrorInfo,
        available_providers: List[str],
    ) -> Dict[str, Any]:
        """执行降级"""
        # 根据错误严重程度选择降级策略
        strategies_to_try = []

        if error.severity == ErrorSeverity.LOW:
            strategies_to_try = ["response_caching", "model_downgrade"]
        elif error.severity == ErrorSeverity.MEDIUM:
            strategies_to_try = [
                "provider_switch",
                "model_downgrade",
                "response_caching",
            ]
        elif error.severity == ErrorSeverity.HIGH:
            strategies_to_try = ["provider_switch", "simplified_response"]
        else:  # CRITICAL
            strategies_to_try = ["simplified_response"]

        # 尝试每个策略
        for strategy_name in strategies_to_try:
            try:
                strategy_func = self.strategies[strategy_name]
                result = await strategy_func(
                    original_request, error, available_providers
                )
                if result:
                    logger.info(f"Fallback strategy '{strategy_name}' succeeded")
                    return result
            except Exception as e:
                logger.warning(f"Fallback strategy '{strategy_name}' failed: {e}")
                continue

        # 所有策略都失败，返回最低限度的响应
        return {
            "success": False,
            "fallback": True,
            "content": "[系统降级] 由于技术问题，无法生成响应。请稍后重试。",
            "strategy": "emergency",
            "error": error.error_message,
        }

    async def _model_downgrade(
        self, request: Dict[str, Any], error: ErrorInfo, available_providers: List[str]
    ) -> Optional[Dict[str, Any]]:
        """模型降级（使用更便宜的模型）"""
        # 这里可以实现模型降级逻辑
        # 例如：从GPT-4降级到GPT-3.5
        return None

    async def _provider_switch(
        self, request: Dict[str, Any], error: ErrorInfo, available_providers: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Provider切换"""
        # 排除当前失败的Provider
        exclude_providers = [error.provider]

        # 获取最佳Provider
        best_provider = self.error_handler.get_best_provider(
            available_providers, exclude_providers
        )
        if not best_provider:
            return None

        # 这里应该调用新的Provider
        # 返回一个占位符响应
        return {
            "success": True,
            "fallback": True,
            "content": f"[Provider切换] 已从 {error.provider} 切换到 {best_provider}。",
            "strategy": "provider_switch",
            "new_provider": best_provider,
        }

    async def _response_caching(
        self, request: Dict[str, Any], error: ErrorInfo, available_providers: List[str]
    ) -> Optional[Dict[str, Any]]:
        """响应缓存"""
        # 这里可以实现缓存查找逻辑
        # 如果找到缓存响应，则返回
        return None

    async def _simplified_response(
        self, request: Dict[str, Any], error: ErrorInfo, available_providers: List[str]
    ) -> Optional[Dict[str, Any]]:
        """简化响应"""
        # 生成一个简化的响应
        prompt = request.get("prompt", "")
        prompt_length = len(prompt)

        return {
            "success": True,
            "fallback": True,
            "content": f"[简化响应] 由于系统问题，无法生成完整回答。您的问题长度为{prompt_length}字符。",
            "strategy": "simplified_response",
            "original_prompt_length": prompt_length,
        }


# 全局ErrorHandler实例
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局ErrorHandler实例"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def get_fallback_strategy() -> FallbackStrategy:
    """获取降级策略"""
    return FallbackStrategy(get_error_handler())


async def retry_with_backoff(
    func: Callable,
    retry_policy: RetryPolicy = RetryPolicy(),
    error_handler: Optional[ErrorHandler] = None,
    provider: str = "unknown",
) -> Any:
    """带退避的重试装饰器"""
    if error_handler is None:
        error_handler = get_error_handler()

    last_error = None

    for attempt in range(retry_policy.max_retries + 1):
        try:
            if attempt > 0:
                # 计算延迟
                delay = retry_policy.calculate_delay(attempt)
                logger.info(
                    f"Retry attempt {attempt}/{retry_policy.max_retries} for {provider}, waiting {delay:.1f}s"
                )
                await asyncio.sleep(delay)

            result = await func()

            # 记录成功
            error_handler.record_success(provider)

            return result

        except Exception as e:
            last_error = e

            # 分类错误
            error_info = error_handler.classify_error(e, provider)
            error_info.retry_count = attempt

            # 记录错误
            error_handler.record_error(error_info)

            # 检查是否可以重试
            if not error_handler.can_retry(error_info, retry_policy):
                logger.error(f"Cannot retry {provider}: {error_info.category.value}")
                break

            logger.warning(f"Attempt {attempt + 1} failed for {provider}: {e}")

    # 所有重试都失败
    if last_error:
        raise last_error
    else:
        raise Exception(f"Failed after {retry_policy.max_retries} retries")
