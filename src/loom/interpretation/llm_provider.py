"""
LLM提供者接口

抽象LLM提供商接口，支持多种LLM后端。
支持BYOK（Bring Your Own Key）、异步请求处理、错误重试和降级。
增强版：支持多Provider、连接池、批处理、缓存等高级功能。
"""

import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
import backoff
from aiohttp import ClientSession, ClientTimeout

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """LLM响应"""

    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "metadata": self.metadata,
        }


@dataclass
class LLMRequest:
    """LLM请求"""

    prompt: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def get_hash(self) -> str:
        """获取请求哈希（用于缓存）"""
        content = f"{self.prompt}:{self.model}:{self.temperature}:{self.max_tokens}"
        return hashlib.md5(content.encode()).hexdigest()


class LLMProvider(ABC):
    """LLM提供者抽象基类（增强版）"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")
        self.provider_type = config.get("type", "unknown")
        self.model = config.get("model", "default")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        self.fallback_enabled = config.get("fallback_enabled", True)
        self.enabled = config.get("enabled", True)

        # 性能优化配置
        self.connection_pool_size = config.get("connection_pool_size", 5)
        self.enable_batching = config.get("enable_batching", False)
        self.enable_caching = config.get("enable_caching", True)
        self.cache_ttl = config.get("cache_ttl", 300)  # 5分钟

        # 统计信息
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.error_count = 0
        self.last_used = None

        # 连接池
        self._session_pool = []
        self._session_lock = asyncio.Lock()

        # 缓存
        self._response_cache = {}

        logger.info(f"Initialized LLM provider: {self.name} ({self.provider_type})")

    @abstractmethod
    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现"""
        pass

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本（带重试机制）"""
        # 创建请求对象
        request = LLMRequest(
            prompt=prompt,
            model=kwargs.get("model", self.model),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens"),
            stream=False,
            extra_params=kwargs,
        )

        # 检查缓存
        if self.enable_caching:
            cached_response = self._get_cached_response(request)
            if cached_response:
                logger.debug(f"Using cached response for {self.name}")
                return cached_response

        # 带退避的重试机制
        @backoff.on_exception(
            backoff.expo,
            (aiohttp.ClientError, asyncio.TimeoutError),
            max_tries=self.max_retries,
            max_time=self.timeout,
        )
        async def _generate_with_retry():
            self.request_count += 1
            self.last_used = datetime.now()

            try:
                response = await self._generate_impl(prompt, **kwargs)

                # 更新统计
                if response.usage:
                    self.total_tokens += sum(response.usage.values())
                    self.total_cost += self._calculate_cost(response)

                # 缓存响应
                if self.enable_caching:
                    self._cache_response(request, response)

                return response

            except Exception as e:
                self.error_count += 1
                logger.error(f"Provider {self.name} error: {e}")
                raise

        try:
            return await _generate_with_retry()
        except Exception as e:
            logger.error(f"All retries failed for {self.name}: {e}")

            # 尝试降级
            if self.fallback_enabled:
                return await self._generate_fallback(prompt, **kwargs)
            else:
                raise

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """批量生成文本"""
        if not self.enable_batching:
            # 如果不支持批处理，则顺序处理
            results = []
            for prompt in prompts:
                results.append(await self.generate(prompt, **kwargs))
            return results

        # 创建批量请求
        requests = [
            LLMRequest(
                prompt=prompt,
                model=kwargs.get("model", self.model),
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens"),
                stream=False,
                extra_params=kwargs,
            )
            for prompt in prompts
        ]

        try:
            return await self._generate_batch_impl(requests)
        except Exception as e:
            logger.error(f"Batch generation failed for {self.name}: {e}")
            # 降级为顺序处理
            results = []
            for request in requests:
                try:
                    response = await self.generate(
                        request.prompt, **request.extra_params
                    )
                    results.append(response)
                except Exception as inner_e:
                    logger.error(f"Individual request failed: {inner_e}")
                    results.append(
                        await self._generate_fallback(
                            request.prompt, **request.extra_params
                        )
                    )
            return results

    async def _generate_batch_impl(
        self, requests: List[LLMRequest]
    ) -> List[LLMResponse]:
        """批量生成的具体实现（默认顺序处理）"""
        results = []
        for request in requests:
            results.append(
                await self._generate_impl(request.prompt, **request.extra_params)
            )
        return results

    async def _generate_fallback(self, prompt: str, **kwargs) -> LLMResponse:
        """降级生成（默认实现）"""
        logger.warning(f"Using fallback response for {self.name}")
        return LLMResponse(
            content=f"[降级响应] 由于技术问题，{self.name} 无法生成完整响应。原始提示长度：{len(prompt)}字符。",
            model=f"{self.model}-fallback",
            usage={"input_tokens": len(prompt) // 4, "output_tokens": 50},
            metadata={
                "fallback": True,
                "provider": self.name,
                "error": "All retries failed",
                "timestamp": datetime.now().isoformat(),
            },
        )

    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        pass

    def _get_cached_response(self, request: LLMRequest) -> Optional[LLMResponse]:
        """获取缓存的响应"""
        if not self.enable_caching:
            return None

        cache_key = request.get_hash()
        if cache_key in self._response_cache:
            cached_item = self._response_cache[cache_key]
            # 检查TTL
            if datetime.now() - cached_item["timestamp"] < timedelta(
                seconds=self.cache_ttl
            ):
                logger.debug(f"Cache hit for {self.name}")
                return cached_item["response"]
            else:
                # 缓存过期
                del self._response_cache[cache_key]

        return None

    def _cache_response(self, request: LLMRequest, response: LLMResponse):
        """缓存响应"""
        if not self.enable_caching:
            return

        cache_key = request.get_hash()
        self._response_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now(),
        }

        # 限制缓存大小
        if len(self._response_cache) > 100:
            # 删除最旧的缓存项
            oldest_key = min(
                self._response_cache.keys(),
                key=lambda k: self._response_cache[k]["timestamp"],
            )
            del self._response_cache[oldest_key]

    async def get_session(self) -> ClientSession:
        """获取连接池中的会话"""
        async with self._session_lock:
            if self._session_pool:
                return self._session_pool.pop()

        # 创建新会话
        timeout = ClientTimeout(total=self.timeout)
        return ClientSession(timeout=timeout)

    async def release_session(self, session: ClientSession):
        """释放会话到连接池"""
        async with self._session_lock:
            if len(self._session_pool) < self.connection_pool_size:
                self._session_pool.append(session)
            else:
                await session.close()

    async def close(self):
        """关闭所有连接"""
        async with self._session_lock:
            for session in self._session_pool:
                await session.close()
            self._session_pool.clear()

    def _calculate_cost(self, response: LLMResponse) -> float:
        """计算成本（子类可以覆盖）"""
        # 默认实现：按字符数估算
        total_chars = len(response.content)
        return total_chars / 1000 * 0.001  # 假设每千字符0.001美元

    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []

        # 检查必需字段（子类可以覆盖）
        if "api_key" not in self.config and self.provider_type not in [
            "ollama",
            "local",
        ]:
            errors.append("Missing required field: api_key")

        # 检查连接池大小
        if self.connection_pool_size < 1:
            errors.append("connection_pool_size must be >= 1")

        return errors

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = time.time()
            # 发送一个简单的测试提示
            test_prompt = "Hello, please respond with 'OK' if you're working."
            response = await self.generate(test_prompt, max_tokens=10)
            elapsed = time.time() - start_time

            return {
                "healthy": True,
                "response_time": elapsed,
                "model": response.model,
                "provider": self.name,
                "type": self.provider_type,
                "request_count": self.request_count,
                "error_count": self.error_count,
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "provider": self.name,
                "type": self.provider_type,
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "type": self.provider_type,
            "model": self.model,
            "enabled": self.enabled,
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "error_count": self.error_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "performance": {
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "connection_pool_size": self.connection_pool_size,
                "enable_batching": self.enable_batching,
                "enable_caching": self.enable_caching,
                "cache_ttl": self.cache_ttl,
            },
        }


class OpenAIProvider(LLMProvider):
    """OpenAI提供者"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.organization = config.get("organization")

        # OpenAI特定配置
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现"""
        session = await self.get_session()
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            if self.organization:
                headers["OpenAI-Organization"] = self.organization

            payload = {
                "model": kwargs.get("model", self.model),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["model", "temperature", "max_tokens"]
                },
            }

            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error: {response.status} - {error_text}")
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data["model"],
                    usage=data.get("usage", {}),
                    metadata={
                        "id": data.get("id"),
                        "finish_reason": data["choices"][0].get("finish_reason"),
                        "provider": "openai",
                    },
                )
        finally:
            await self.release_session(session)

    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        # 简化实现：先使用非流式
        response = await self.generate(prompt, **kwargs)
        yield response.content

    def _calculate_cost(self, response: LLMResponse) -> float:
        """计算OpenAI成本"""
        # 基于实际使用量计算
        if not response.usage:
            return super()._calculate_cost(response)

        # 根据模型定价计算
        model = response.model
        input_tokens = response.usage.get("prompt_tokens", 0)
        output_tokens = response.usage.get("completion_tokens", 0)

        # 简化定价模型
        if "gpt-4" in model:
            cost = (input_tokens / 1000 * 0.03) + (output_tokens / 1000 * 0.06)
        elif "gpt-3.5-turbo" in model:
            cost = (input_tokens / 1000 * 0.0015) + (output_tokens / 1000 * 0.002)
        else:
            cost = (input_tokens + output_tokens) / 1000 * 0.002

        return cost


class AnthropicProvider(LLMProvider):
    """Anthropic提供者"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.anthropic.com/v1")
        self.version = config.get("version", "2023-06-01")

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现"""
        session = await self.get_session()
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.version,
                "Content-Type": "application/json",
            }

            payload = {
                "model": kwargs.get("model", self.model),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["model", "temperature", "max_tokens"]
                },
            }

            async with session.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Anthropic API error: {response.status} - {error_text}"
                    )
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                return LLMResponse(
                    content=data["content"][0]["text"],
                    model=data["model"],
                    usage={
                        "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                    },
                    metadata={
                        "id": data.get("id"),
                        "stop_reason": data.get("stop_reason"),
                        "provider": "anthropic",
                    },
                )
        finally:
            await self.release_session(session)

    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        response = await self.generate(prompt, **kwargs)
        yield response.content


class GoogleProvider(LLMProvider):
    """Google Gemini提供者"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get(
            "base_url", "https://generativelanguage.googleapis.com/v1beta"
        )

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现"""
        session = await self.get_session()
        try:
            headers = {"Content-Type": "application/json"}

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "maxOutputTokens": kwargs.get("max_tokens", 1000),
                    **{
                        k: v
                        for k, v in kwargs.items()
                        if k not in ["temperature", "max_tokens"]
                    },
                },
            }

            url = f"{self.base_url}/models/{kwargs.get('model', self.model)}:generateContent"
            if self.api_key:
                url += f"?key={self.api_key}"

            async with session.post(
                url, json=payload, headers=headers, timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Google API error: {response.status} - {error_text}")
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                return LLMResponse(
                    content=data["candidates"][0]["content"]["parts"][0]["text"],
                    model=data.get("model", kwargs.get("model", self.model)),
                    usage={
                        "input_tokens": data.get("usageMetadata", {}).get(
                            "promptTokenCount", 0
                        ),
                        "output_tokens": data.get("usageMetadata", {}).get(
                            "candidatesTokenCount", 0
                        ),
                    },
                    metadata={
                        "provider": "google",
                        "safety_ratings": data["candidates"][0].get(
                            "safetyRatings", []
                        ),
                    },
                )
        finally:
            await self.release_session(session)

    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        response = await self.generate(prompt, **kwargs)
        yield response.content


class AzureProvider(LLMProvider):
    """Azure OpenAI提供者"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.api_version = config.get("api_version", "2023-12-01-preview")
        self.deployment = config.get("deployment")

        if not self.base_url:
            raise ValueError("Azure provider requires base_url")
        if not self.deployment:
            raise ValueError("Azure provider requires deployment name")

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现"""
        session = await self.get_session()
        try:
            headers = {"api-key": self.api_key, "Content-Type": "application/json"}

            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["temperature", "max_tokens"]
                },
            }

            url = (
                f"{self.base_url}/openai/deployments/{self.deployment}/chat/completions"
            )
            url += f"?api-version={self.api_version}"

            async with session.post(
                url, json=payload, headers=headers, timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Azure API error: {response.status} - {error_text}")
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data["model"],
                    usage=data.get("usage", {}),
                    metadata={
                        "id": data.get("id"),
                        "provider": "azure",
                        "deployment": self.deployment,
                    },
                )
        finally:
            await self.release_session(session)

    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        response = await self.generate(prompt, **kwargs)
        yield response.content


class LocalProvider(LLMProvider):
    """本地模型提供者（Ollama/LM Studio等）"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434/api")
        self.model = config.get("model", "llama2")

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现"""
        session = await self.get_session()
        try:
            payload = {
                "model": kwargs.get("model", self.model),
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "stream": False,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["model", "temperature", "max_tokens"]
                },
            }

            async with session.post(
                f"{self.base_url}/generate", json=payload, timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Local API error: {response.status} - {error_text}")
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                return LLMResponse(
                    content=data["response"],
                    model=data.get("model", kwargs.get("model", self.model)),
                    usage={
                        "input_tokens": data.get("prompt_eval_count", 0),
                        "output_tokens": data.get("eval_count", 0),
                    },
                    metadata={"provider": "local", "done": data.get("done", True)},
                )
        finally:
            await self.release_session(session)

    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        session = await self.get_session()
        try:
            payload = {
                "model": kwargs.get("model", self.model),
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "stream": True,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["model", "temperature", "max_tokens"]
                },
            }

            async with session.post(
                f"{self.base_url}/generate", json=payload, timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Local API error: {response.status} - {error_text}")
                    raise Exception(f"API error: {response.status}")

                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode())
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
        finally:
            await self.release_session(session)


class DeepSeekProvider(LLMProvider):
    """DeepSeek API提供者"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.deepseek.com")
        self.thinking_enabled = config.get("thinking_enabled", False)

        # DeepSeek特定配置
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 1.0)

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现"""
        session = await self.get_session()
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # 构建请求体
            payload = {
                "model": kwargs.get("model", self.model),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False,
            }

            # 处理推理模式
            if self.thinking_enabled:
                payload["thinking"] = {"type": "enabled"}
            else:
                payload["thinking"] = {"type": "disabled"}

            # 添加其他参数
            for key in ["frequency_penalty", "presence_penalty", "top_p", "stop"]:
                if key in kwargs:
                    payload[key] = kwargs[key]

            # 处理异步上下文管理器
            post_result = session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            # 检查是否是协程（模拟对象可能返回协程）
            if asyncio.iscoroutine(post_result):
                post_result = await post_result

            # 现在 post_result 应该是异步上下文管理器
            async with post_result as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"DeepSeek API error: {response.status} - {error_text}"
                    )
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data["model"],
                    usage=data.get("usage", {}),
                    metadata={
                        "id": data.get("id"),
                        "finish_reason": data["choices"][0].get("finish_reason"),
                        "provider": "deepseek",
                        "thinking_enabled": self.thinking_enabled,
                    },
                )
        finally:
            await self.release_session(session)

    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        # 简化实现：先使用非流式
        response = await self.generate(prompt, **kwargs)
        yield response.content

    def _calculate_cost(self, response: LLMResponse) -> float:
        """计算DeepSeek成本"""
        if not response.usage:
            return super()._calculate_cost(response)

        # DeepSeek定价模型
        input_tokens = response.usage.get("prompt_tokens", 0)
        output_tokens = response.usage.get("completion_tokens", 0)

        # 定价：$0.28/1M输入token，$0.42/1M输出token
        input_cost = (input_tokens / 1_000_000) * 0.28
        output_cost = (output_tokens / 1_000_000) * 0.42

        return input_cost + output_cost

    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []
        if not self.api_key:
            errors.append("API key is required for DeepSeek provider")
        if not self.model:
            errors.append("Model is required for DeepSeek provider")
        return errors


class ProviderManager:
    """Provider管理器"""

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider: Optional[str] = None
        self.fallback_order: List[str] = []
        self._lock = asyncio.Lock()

    def register_provider(self, name: str, provider: LLMProvider):
        """注册Provider"""
        self.providers[name] = provider
        logger.info(f"Registered provider: {name} ({provider.provider_type})")

    def set_default(self, name: str):
        """设置默认Provider"""
        if name not in self.providers:
            raise ValueError(f"Provider {name} not registered")
        self.default_provider = name
        logger.info(f"Set default provider to: {name}")

    def set_fallback_order(self, order: List[str]):
        """设置回退顺序"""
        self.fallback_order = order
        logger.info(f"Set fallback order: {order}")

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """获取Provider"""
        if name is None:
            if self.default_provider is None:
                raise ValueError("No default provider set")
            name = self.default_provider

        if name not in self.providers:
            raise ValueError(f"Provider {name} not found")

        return self.providers[name]

    async def generate_with_fallback(self, prompt: str, **kwargs) -> LLMResponse:
        """使用回退机制生成文本"""
        providers_to_try = []

        # 确定要尝试的Provider顺序
        if "provider" in kwargs:
            providers_to_try.append(kwargs.pop("provider"))
        elif self.default_provider:
            providers_to_try.append(self.default_provider)

        # 添加回退顺序，但避免重复添加已经在列表中的provider
        for provider_name in self.fallback_order:
            if provider_name not in providers_to_try:
                providers_to_try.append(provider_name)

        last_error = None
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]
            if not provider.enabled:
                logger.debug(f"Provider {provider_name} is disabled, skipping")
                continue

            try:
                logger.info(f"Trying provider: {provider_name}")
                return await provider.generate(prompt, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue

        # 所有Provider都失败
        if last_error:
            raise last_error
        else:
            raise Exception("No available providers")

    async def health_check_all(self) -> Dict[str, Any]:
        """检查所有Provider的健康状态"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e), "provider": name}
        return results

    def get_stats_all(self) -> Dict[str, Any]:
        """获取所有Provider的统计信息"""
        stats = {}
        total_requests = 0
        total_tokens = 0
        total_cost = 0.0

        for name, provider in self.providers.items():
            stats[name] = provider.get_stats()
            total_requests += provider.request_count
            total_tokens += provider.total_tokens
            total_cost += provider.total_cost

        return {
            "providers": stats,
            "totals": {
                "requests": total_requests,
                "tokens": total_tokens,
                "cost": total_cost,
                "provider_count": len(self.providers),
            },
            "default_provider": self.default_provider,
            "fallback_order": self.fallback_order,
        }

    async def close_all(self):
        """关闭所有Provider"""
        for provider in self.providers.values():
            try:
                await provider.close()
            except Exception as e:
                logger.error(f"Error closing provider {provider.name}: {e}")


class LLMProviderFactory:
    """LLM提供者工厂"""

    @staticmethod
    def create_provider(config: Dict[str, Any]) -> LLMProvider:
        """创建提供者实例"""
        provider_type = config.get("type", "openai").lower()

        if provider_type == "openai":
            return OpenAIProvider(config)
        elif provider_type == "anthropic":
            return AnthropicProvider(config)
        elif provider_type == "google":
            return GoogleProvider(config)
        elif provider_type == "azure":
            return AzureProvider(config)
        elif provider_type in ["local", "ollama"]:
            return LocalProvider(config)
        elif provider_type == "deepseek":
            return DeepSeekProvider(config)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    @staticmethod
    def create_from_configs(
        configs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, LLMProvider]:
        """从配置字典创建多个提供者"""
        providers = {}

        for name, config in configs.items():
            try:
                config["name"] = name
                provider = LLMProviderFactory.create_provider(config)

                # 验证配置
                errors = provider.validate_config()
                if errors:
                    logger.warning(f"Provider {name} has config errors: {errors}")
                    continue

                providers[name] = provider
                logger.info(f"Created LLM provider: {name} ({config.get('type')})")

            except Exception as e:
                logger.error(f"Failed to create provider {name}: {e}")

        return providers

    @staticmethod
    def create_provider_manager(configs: Dict[str, Dict[str, Any]]) -> ProviderManager:
        """从配置创建Provider管理器"""
        manager = ProviderManager()

        for name, config in configs.items():
            try:
                config["name"] = name
                provider = LLMProviderFactory.create_provider(config)

                # 验证配置
                errors = provider.validate_config()
                if errors:
                    logger.warning(f"Provider {name} has config errors: {errors}")
                    continue

                manager.register_provider(name, provider)

            except Exception as e:
                logger.error(f"Failed to create provider {name}: {e}")

        # 设置默认Provider
        if configs:
            first_provider = next(iter(configs.keys()))
            manager.set_default(first_provider)

        return manager
