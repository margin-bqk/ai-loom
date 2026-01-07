"""
异步辅助函数
提供常用的异步编程工具和装饰器
"""

import asyncio
import functools
import inspect
from typing import Any, Callable, TypeVar, Coroutine
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

T = TypeVar("T")


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    异步重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避系数
        exceptions: 触发重试的异常类型
    """
    
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    # 计算下一次延迟
                    wait_time = current_delay * (backoff ** attempt)
                    
                    # 记录重试日志
                    func_name = func.__name__
                    print(f"重试 {func_name}: 第 {attempt + 1} 次尝试失败，{wait_time:.2f} 秒后重试: {e}")
                    
                    await asyncio.sleep(wait_time)
            
            # 所有重试都失败
            raise last_exception
        
        return wrapper
    
    return decorator


def timeout(timeout_seconds: float):
    """
    异步超时装饰器
    
    Args:
        timeout_seconds: 超时时间（秒）
    """
    
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                func_name = func.__name__
                raise TimeoutError(
                    f"函数 {func_name} 执行超时（{timeout_seconds} 秒）"
                )
        
        return wrapper
    
    return decorator


class AsyncRateLimiter:
    """
    异步速率限制器
    基于令牌桶算法
    """
    
    def __init__(self, rate: float, capacity: int = None):
        """
        Args:
            rate: 每秒允许的请求数
            capacity: 桶容量（默认为 rate * 2）
        """
        self.rate = rate
        self.capacity = capacity or int(rate * 2)
        self.tokens = self.capacity
        self.last_update = datetime.now()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        获取指定数量的令牌
        
        Args:
            tokens: 需要的令牌数量
            
        Returns:
            等待的时间（秒）
        """
        async with self._lock:
            now = datetime.now()
            elapsed = (now - self.last_update).total_seconds()
            
            # 补充令牌
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            # 检查是否有足够的令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            
            # 计算需要等待的时间
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate
            
            # 等待并补充令牌
            await asyncio.sleep(wait_time)
            self.tokens = 0
            self.last_update = datetime.now()
            
            return wait_time
    
    @asynccontextmanager
    async def limit(self, tokens: int = 1):
        """
        上下文管理器，用于速率限制
        
        Args:
            tokens: 需要的令牌数量
        """
        wait_time = await self.acquire(tokens)
        if wait_time > 0:
            print(f"速率限制: 等待了 {wait_time:.2f} 秒")
        try:
            yield
        finally:
            pass


async def gather_with_concurrency(
    tasks: list[Coroutine],
    max_concurrent: int = 10
) -> list[Any]:
    """
    带并发限制的 asyncio.gather
    
    Args:
        tasks: 协程列表
        max_concurrent: 最大并发数
        
    Returns:
        结果列表
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def sem_task(task: Coroutine) -> Any:
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[sem_task(task) for task in tasks])


async def run_in_thread(func: Callable, *args, **kwargs) -> Any:
    """
    在线程池中运行同步函数
    
    Args:
        func: 同步函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        函数返回值
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(func, *args, **kwargs)
    )


def sync_to_async(func: Callable) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    将同步函数转换为异步函数
    
    Args:
        func: 同步函数
        
    Returns:
        异步函数
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await run_in_thread(func, *args, **kwargs)
    
    return wrapper


class AsyncCache:
    """
    简单的异步缓存
    """
    
    def __init__(self, ttl: timedelta = timedelta(minutes=5)):
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        if key not in self._cache:
            return default
        
        timestamp = self._timestamps.get(key)
        if timestamp and datetime.now() - timestamp > self.ttl:
            # 缓存过期
            del self._cache[key]
            del self._timestamps[key]
            return default
        
        return self._cache[key]
    
    async def set(self, key: str, value: Any):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    async def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()
    
    async def delete(self, key: str):
        """删除缓存键"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]


# 常用异步工具函数
async def sleep_random(min_seconds: float = 0.1, max_seconds: float = 1.0):
    """
    随机睡眠
    
    Args:
        min_seconds: 最小睡眠时间
        max_seconds: 最大睡眠时间
    """
    import random
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))


async def wait_for_first(*coroutines, timeout: float = None):
    """
    等待第一个完成的协程
    
    Args:
        *coroutines: 协程列表
        timeout: 超时时间
        
    Returns:
        (结果, 索引) 或超时时抛出异常
    """
    tasks = [asyncio.create_task(coro) for coro in coroutines]
    
    try:
        done, pending = await asyncio.wait(
            tasks,
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 取消未完成的任务
        for task in pending:
            task.cancel()
        
        # 获取第一个完成的结果
        if done:
            task = next(iter(done))
            idx = tasks.index(task)
            return task.result(), idx
        else:
            raise asyncio.TimeoutError("等待超时")
    finally:
        # 清理
        for task in tasks:
            if not task.done():
                task.cancel()