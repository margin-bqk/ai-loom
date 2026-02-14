"""
性能优化管理器

提供连接池管理、请求批处理、响应缓存、令牌统计等性能优化功能。
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
import backoff
from aiohttp import ClientSession, ClientTimeout

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 1
    ttl: int = 300  # 默认5分钟

    def is_expired(self) -> bool:
        """检查是否过期"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl

    def update_access(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class BatchRequest:
    """批处理请求"""

    request_id: str
    prompt: str
    callback: Any  # 回调函数
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionPool:
    """连接池"""

    def __init__(self, max_size: int = 10, timeout: int = 30):
        self.max_size = max_size
        self.timeout = timeout
        self._pool: List[ClientSession] = []
        self._lock = asyncio.Lock()
        self._created_count = 0

        logger.info(
            f"ConnectionPool initialized with max_size={max_size}, timeout={timeout}"
        )

    async def get_session(self) -> ClientSession:
        """获取会话"""
        async with self._lock:
            if self._pool:
                session = self._pool.pop()
                logger.debug(
                    f"Reusing session from pool (pool size: {len(self._pool)})"
                )
                return session

            # 创建新会话
            self._created_count += 1
            timeout = ClientTimeout(total=self.timeout)
            session = ClientSession(timeout=timeout)
            logger.debug(f"Created new session (total created: {self._created_count})")
            return session

    async def release_session(self, session: ClientSession):
        """释放会话"""
        async with self._lock:
            if len(self._pool) < self.max_size:
                self._pool.append(session)
                logger.debug(f"Returned session to pool (pool size: {len(self._pool)})")
            else:
                await session.close()
                logger.debug(f"Closed session (pool full, size: {len(self._pool)})")

    async def close_all(self):
        """关闭所有连接"""
        async with self._lock:
            for session in self._pool:
                await session.close()
            self._pool.clear()
            logger.info(f"Closed all sessions in pool")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "pool_size": len(self._pool),
            "max_size": self.max_size,
            "created_count": self._created_count,
            "timeout": self.timeout,
        }


class ResponseCache:
    """响应缓存"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

        logger.info(
            f"ResponseCache initialized with max_size={max_size}, default_ttl={default_ttl}s"
        )

    def _generate_key(self, provider: str, prompt: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        content = f"{provider}:{prompt}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    async def get(
        self, provider: str, prompt: str, params: Dict[str, Any]
    ) -> Optional[Any]:
        """获取缓存响应"""
        key = self._generate_key(provider, prompt, params)

        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                if entry.is_expired():
                    # 删除过期条目
                    del self._cache[key]
                    logger.debug(f"Cache entry expired for key: {key[:8]}...")
                    return None

                # 更新访问时间
                entry.update_access()
                logger.debug(
                    f"Cache hit for key: {key[:8]}... (access count: {entry.access_count})"
                )
                return entry.value

        return None

    async def set(
        self,
        provider: str,
        prompt: str,
        params: Dict[str, Any],
        value: Any,
        ttl: Optional[int] = None,
    ):
        """设置缓存响应"""
        key = self._generate_key(provider, prompt, params)

        async with self._lock:
            # 检查缓存大小
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            # 创建缓存条目
            entry = CacheEntry(key=key, value=value, ttl=ttl or self.default_ttl)

            self._cache[key] = entry
            logger.debug(
                f"Cached response for key: {key[:8]}... (cache size: {len(self._cache)})"
            )

    def _evict_oldest(self):
        """驱逐最旧的缓存条目"""
        if not self._cache:
            return

        # 找到最久未访问的条目
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)

        del self._cache[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key[:8]}...")

    async def clear(self):
        """清除缓存"""
        async with self._lock:
            self._cache.clear()
            logger.info("Response cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_size = len(self._cache)
        total_accesses = sum(entry.access_count for entry in self._cache.values())

        # 计算命中率（如果有访问记录）
        hit_rate = 0.0
        if total_accesses > 0:
            hit_rate = total_accesses / (total_accesses + total_size)  # 简化计算

        return {
            "cache_size": total_size,
            "max_size": self.max_size,
            "total_accesses": total_accesses,
            "estimated_hit_rate": hit_rate,
            "default_ttl": self.default_ttl,
        }


class BatchProcessor:
    """批处理器"""

    def __init__(self, max_batch_size: int = 10, max_wait_time: float = 0.1):
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time  # 最大等待时间（秒）
        self._batches: Dict[str, List[BatchRequest]] = defaultdict(list)
        self._batch_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._batch_timers: Dict[str, asyncio.Task] = {}

        logger.info(
            f"BatchProcessor initialized with max_batch_size={max_batch_size}, max_wait_time={max_wait_time}s"
        )

    async def add_request(
        self,
        batch_key: str,
        prompt: str,
        callback: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """添加请求到批处理队列"""
        request_id = hashlib.md5(
            f"{batch_key}:{prompt}:{time.time()}".encode()
        ).hexdigest()[:16]

        request = BatchRequest(
            request_id=request_id,
            prompt=prompt,
            callback=callback,
            metadata=metadata or {},
        )

        async with self._batch_locks[batch_key]:
            self._batches[batch_key].append(request)

            # 如果达到最大批处理大小，立即处理
            if len(self._batches[batch_key]) >= self.max_batch_size:
                await self._process_batch(batch_key)
            else:
                # 启动或重置计时器
                await self._start_batch_timer(batch_key)

        logger.debug(
            f"Added request {request_id} to batch {batch_key} (size: {len(self._batches[batch_key])})"
        )
        return request_id

    async def _start_batch_timer(self, batch_key: str):
        """启动批处理计时器"""
        # 取消现有计时器
        if batch_key in self._batch_timers:
            self._batch_timers[batch_key].cancel()

        # 创建新计时器
        self._batch_timers[batch_key] = asyncio.create_task(
            self._batch_timer(batch_key)
        )

    async def _batch_timer(self, batch_key: str):
        """批处理计时器"""
        try:
            await asyncio.sleep(self.max_wait_time)
            async with self._batch_locks[batch_key]:
                if self._batches[batch_key]:
                    await self._process_batch(batch_key)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Batch timer error for {batch_key}: {e}")

    async def _process_batch(self, batch_key: str):
        """处理批处理请求"""
        if batch_key not in self._batches or not self._batches[batch_key]:
            return

        # 获取当前批次的请求
        requests = self._batches[batch_key].copy()
        self._batches[batch_key].clear()

        # 取消计时器
        if batch_key in self._batch_timers:
            self._batch_timers[batch_key].cancel()
            del self._batch_timers[batch_key]

        logger.info(f"Processing batch {batch_key} with {len(requests)} requests")

        # 这里应该实现实际的批处理逻辑
        # 目前只是简单地为每个请求调用回调
        for request in requests:
            try:
                # 模拟批处理响应
                response = (
                    f"[批处理响应] 请求ID: {request.request_id}, 提示长度: {len(request.prompt)}"
                )
                await request.callback(response)
            except Exception as e:
                logger.error(f"Error processing request {request.request_id}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_pending = sum(len(batch) for batch in self._batches.values())
        active_batches = len(self._batches)

        return {
            "max_batch_size": self.max_batch_size,
            "max_wait_time": self.max_wait_time,
            "total_pending_requests": total_pending,
            "active_batches": active_batches,
            "batch_keys": list(self._batches.keys()),
        }


class TokenCounter:
    """令牌计数器"""

    def __init__(self):
        self._counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._costs: Dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

        # 令牌定价（美元/千令牌）
        self._pricing = {
            "openai": {
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            },
            "anthropic": {
                "claude-3-opus": {"input": 0.015, "output": 0.075},
                "claude-3-sonnet": {"input": 0.003, "output": 0.015},
                "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            },
            "google": {"gemini-pro": {"input": 0.0005, "output": 0.0015}},
        }

        logger.info("TokenCounter initialized")

    async def add_usage(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ):
        """添加令牌使用量"""
        async with self._lock:
            self._counts[provider][f"{model}_input"] += input_tokens
            self._counts[provider][f"{model}_output"] += output_tokens

            # 计算成本
            cost = self._calculate_cost(provider, model, input_tokens, output_tokens)
            self._costs[provider] += cost

            logger.debug(
                f"Added token usage: {provider}/{model} - input: {input_tokens}, output: {output_tokens}, cost: ${cost:.6f}"
            )

    def _calculate_cost(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """计算成本"""
        if provider not in self._pricing:
            return 0.0

        provider_pricing = self._pricing[provider]

        # 查找模型定价
        model_key = None
        for key in provider_pricing.keys():
            if key in model:
                model_key = key
                break

        if not model_key:
            # 使用默认定价
            return (input_tokens + output_tokens) / 1000 * 0.002

        pricing = provider_pricing[model_key]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    def get_usage(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """获取使用量统计"""
        if provider:
            if provider not in self._counts:
                return {"provider": provider, "total_tokens": 0, "total_cost": 0.0}

            total_tokens = sum(self._counts[provider].values())
            total_cost = self._costs.get(provider, 0.0)

            return {
                "provider": provider,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "breakdown": dict(self._counts[provider]),
            }
        else:
            # 所有Provider的统计
            all_stats = {}
            total_tokens_all = 0
            total_cost_all = 0.0

            for prov in self._counts.keys():
                prov_tokens = sum(self._counts[prov].values())
                prov_cost = self._costs.get(prov, 0.0)

                all_stats[prov] = {
                    "total_tokens": prov_tokens,
                    "total_cost": prov_cost,
                    "breakdown": dict(self._counts[prov]),
                }

                total_tokens_all += prov_tokens
                total_cost_all += prov_cost

            return {
                "total_tokens": total_tokens_all,
                "total_cost": total_cost_all,
                "providers": all_stats,
            }

    def reset(self, provider: Optional[str] = None):
        """重置计数器"""
        if provider:
            if provider in self._counts:
                self._counts[provider].clear()
            if provider in self._costs:
                self._costs[provider] = 0.0
            logger.info(f"Reset token counter for provider: {provider}")
        else:
            self._counts.clear()
            self._costs.clear()
            logger.info("Reset all token counters")


class PerformanceOptimizer:
    """性能优化管理器"""

    def __init__(self):
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.response_cache = ResponseCache()
        self.batch_processor = BatchProcessor()
        self.token_counter = TokenCounter()

        logger.info("PerformanceOptimizer initialized")

    def get_connection_pool(
        self, provider: str, max_size: int = 10, timeout: int = 30
    ) -> ConnectionPool:
        """获取连接池"""
        if provider not in self.connection_pools:
            self.connection_pools[provider] = ConnectionPool(
                max_size=max_size, timeout=timeout
            )

        return self.connection_pools[provider]

    async def close_all_connections(self):
        """关闭所有连接"""
        for pool in self.connection_pools.values():
            await pool.close_all()

        logger.info("Closed all connection pools")

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        connection_stats = {}
        for provider, pool in self.connection_pools.items():
            connection_stats[provider] = pool.get_stats()

        return {
            "connection_pools": connection_stats,
            "response_cache": self.response_cache.get_stats(),
            "batch_processor": self.batch_processor.get_stats(),
            "token_counter": self.token_counter.get_usage(),
        }


# 全局PerformanceOptimizer实例
_global_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取全局PerformanceOptimizer实例"""
    global _global_performance_optimizer
    if _global_performance_optimizer is None:
        _global_performance_optimizer = PerformanceOptimizer()
    return _global_performance_optimizer
