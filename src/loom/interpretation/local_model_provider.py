"""
本地模型提供者增强版

支持Ollama、LM Studio、vLLM等本地模型，提供模型管理、性能监控和自动发现功能。
"""

import asyncio
import time
import json
import subprocess
import platform
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
from aiohttp import ClientSession, ClientTimeout

from ..utils.logging_config import get_logger
from .llm_provider import LLMProvider, LLMResponse, LocalProvider

logger = get_logger(__name__)


class LocalModelType(Enum):
    """本地模型类型"""

    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    VLLM = "vllm"
    TEXT_GENERATION_WEBUI = "text_generation_webui"
    UNKNOWN = "unknown"


@dataclass
class LocalModelInfo:
    """本地模型信息"""

    name: str
    model_type: LocalModelType
    size: Optional[str] = None  # 模型大小（如 "7B", "13B"）
    format: Optional[str] = None  # 模型格式（如 "gguf", "safetensors"）
    context_length: Optional[int] = None  # 上下文长度
    parameters: Optional[int] = None  # 参数量
    last_used: Optional[datetime] = None
    performance_score: float = 0.0  # 性能评分（0-1）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "model_type": self.model_type.value,
            "size": self.size,
            "format": self.format,
            "context_length": self.context_length,
            "parameters": self.parameters,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "performance_score": self.performance_score,
        }


@dataclass
class ModelPerformanceMetrics:
    """模型性能指标"""

    model_name: str
    request_count: int = 0
    success_count: int = 0
    total_tokens: int = 0
    avg_latency: float = 0.0
    latency_history: List[float] = field(default_factory=list)
    error_history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count

    @property
    def tokens_per_second(self) -> float:
        """计算每秒令牌数"""
        if self.avg_latency == 0 or self.total_tokens == 0:
            return 0.0
        avg_tokens_per_request = self.total_tokens / max(self.request_count, 1)
        return (
            avg_tokens_per_request / self.avg_latency if self.avg_latency > 0 else 0.0
        )


class LocalModelManager:
    """本地模型管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models: Dict[str, LocalModelInfo] = {}
        self.performance_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.auto_discovery_enabled = config.get("auto_discovery", True)
        self.discovery_interval = config.get("discovery_interval", 300)  # 秒
        self._discovery_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动模型管理器"""
        if self.auto_discovery_enabled:
            self._discovery_task = asyncio.create_task(self._discovery_loop())
            logger.info("Started local model auto-discovery")

        # 初始发现
        await self.discover_models()

    async def stop(self):
        """停止模型管理器"""
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
            self._discovery_task = None
            logger.info("Stopped local model auto-discovery")

    async def _discovery_loop(self):
        """自动发现循环"""
        while True:
            try:
                await asyncio.sleep(self.discovery_interval)
                await self.discover_models()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in model discovery loop: {e}")

    async def discover_models(self) -> List[LocalModelInfo]:
        """发现可用的本地模型"""
        discovered_models = []

        # 尝试发现Ollama模型
        ollama_models = await self._discover_ollama_models()
        discovered_models.extend(ollama_models)

        # 尝试发现LM Studio模型
        lm_studio_models = await self._discover_lm_studio_models()
        discovered_models.extend(lm_studio_models)

        # 尝试发现vLLM模型
        vllm_models = await self._discover_vllm_models()
        discovered_models.extend(vllm_models)

        # 更新模型列表
        for model_info in discovered_models:
            self.models[model_info.name] = model_info

        logger.info(f"Discovered {len(discovered_models)} local models")
        return discovered_models

    async def _discover_ollama_models(self) -> List[LocalModelInfo]:
        """发现Ollama模型"""
        models = []

        # 检查Ollama是否运行
        ollama_url = self.config.get("ollama_url", "http://localhost:11434")

        try:
            timeout = ClientTimeout(total=5)
            async with ClientSession(timeout=timeout) as session:
                # 检查Ollama服务是否可用
                try:
                    async with session.get(f"{ollama_url}/api/tags") as response:
                        if response.status == 200:
                            data = await response.json()
                            for model_data in data.get("models", []):
                                model_info = LocalModelInfo(
                                    name=model_data.get("name", "unknown"),
                                    model_type=LocalModelType.OLLAMA,
                                    size=self._extract_model_size(
                                        model_data.get("name", "")
                                    ),
                                    format="gguf",  # Ollama通常使用GGUF格式
                                    parameters=self._estimate_parameters(
                                        model_data.get("name", "")
                                    ),
                                    last_used=(
                                        datetime.fromisoformat(
                                            model_data.get("modified_at", "")
                                        )
                                        if model_data.get("modified_at")
                                        else None
                                    ),
                                )
                                models.append(model_info)
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass

        except Exception as e:
            logger.debug(f"Ollama discovery failed: {e}")

        return models

    async def _discover_lm_studio_models(self) -> List[LocalModelInfo]:
        """发现LM Studio模型"""
        models = []

        # LM Studio通常运行在http://localhost:1234
        lm_studio_url = self.config.get("lm_studio_url", "http://localhost:1234")

        try:
            timeout = ClientTimeout(total=5)
            async with ClientSession(timeout=timeout) as session:
                # 尝试获取模型列表
                try:
                    async with session.get(f"{lm_studio_url}/v1/models") as response:
                        if response.status == 200:
                            data = await response.json()
                            for model_data in data.get("data", []):
                                model_info = LocalModelInfo(
                                    name=model_data.get("id", "unknown"),
                                    model_type=LocalModelType.LM_STUDIO,
                                    size=self._extract_model_size(
                                        model_data.get("id", "")
                                    ),
                                    parameters=self._estimate_parameters(
                                        model_data.get("id", "")
                                    ),
                                )
                                models.append(model_info)
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass

        except Exception as e:
            logger.debug(f"LM Studio discovery failed: {e}")

        return models

    async def _discover_vllm_models(self) -> List[LocalModelInfo]:
        """发现vLLM模型"""
        models = []

        vllm_url = self.config.get("vllm_url", "http://localhost:8000")

        try:
            timeout = ClientTimeout(total=5)
            async with ClientSession(timeout=timeout) as session:
                # 尝试获取模型列表
                try:
                    async with session.get(f"{vllm_url}/v1/models") as response:
                        if response.status == 200:
                            data = await response.json()
                            for model_data in data.get("data", []):
                                model_info = LocalModelInfo(
                                    name=model_data.get("id", "unknown"),
                                    model_type=LocalModelType.VLLM,
                                    size=self._extract_model_size(
                                        model_data.get("id", "")
                                    ),
                                    parameters=self._estimate_parameters(
                                        model_data.get("id", "")
                                    ),
                                )
                                models.append(model_info)
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass

        except Exception as e:
            logger.debug(f"vLLM discovery failed: {e}")

        return models

    def _extract_model_size(self, model_name: str) -> Optional[str]:
        """从模型名提取大小信息"""
        import re

        # 匹配常见的模型大小模式
        patterns = [
            r"(\d+B)",  # 7B, 13B, 70B
            r"(\d+\.\d+B)",  # 1.5B, 3.5B
            r"(\d+[Mm])",  # 500M, 1.5M
            r"(\d+[Gg])",  # 1.5G
        ]

        for pattern in patterns:
            match = re.search(pattern, model_name)
            if match:
                return match.group(1)

        return None

    def _estimate_parameters(self, model_name: str) -> Optional[int]:
        """估算模型参数量"""
        size_str = self._extract_model_size(model_name)
        if not size_str:
            return None

        try:
            if size_str.endswith("B"):
                # 如 7B, 13B
                value = float(size_str[:-1])
                return int(value * 1_000_000_000)
            elif size_str.endswith("M"):
                # 如 500M
                value = float(size_str[:-1])
                return int(value * 1_000_000)
            elif size_str.endswith("G"):
                # 如 1.5G
                value = float(size_str[:-1])
                return int(value * 1_000_000_000)
        except (ValueError, AttributeError):
            pass

        return None

    async def get_model_info(self, model_name: str) -> Optional[LocalModelInfo]:
        """获取模型信息"""
        return self.models.get(model_name)

    async def record_performance(
        self,
        model_name: str,
        success: bool,
        tokens: int,
        latency: float,
        error: Optional[str] = None,
    ):
        """记录模型性能"""
        if model_name not in self.performance_metrics:
            self.performance_metrics[model_name] = ModelPerformanceMetrics(
                model_name=model_name
            )

        metrics = self.performance_metrics[model_name]
        metrics.request_count += 1

        if success:
            metrics.success_count += 1
            metrics.total_tokens += tokens
            metrics.latency_history.append(latency)

            # 更新平均延迟
            if metrics.latency_history:
                metrics.avg_latency = sum(metrics.latency_history) / len(
                    metrics.latency_history
                )

            # 限制历史记录大小
            if len(metrics.latency_history) > 100:
                metrics.latency_history = metrics.latency_history[-100:]
        else:
            if error:
                metrics.error_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "error": error,
                        "latency": latency,
                    }
                )
                # 限制错误历史大小
                if len(metrics.error_history) > 50:
                    metrics.error_history = metrics.error_history[-50:]

    async def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report = {
            "models": {},
            "overall": {
                "total_models": len(self.models),
                "total_requests": 0,
                "total_tokens": 0,
                "avg_success_rate": 0.0,
                "avg_tokens_per_second": 0.0,
            },
        }

        total_success_rate = 0.0
        total_tokens_per_second = 0.0
        model_count = 0

        for model_name, metrics in self.performance_metrics.items():
            report["models"][model_name] = {
                "request_count": metrics.request_count,
                "success_count": metrics.success_count,
                "success_rate": metrics.success_rate,
                "total_tokens": metrics.total_tokens,
                "avg_latency": metrics.avg_latency,
                "tokens_per_second": metrics.tokens_per_second,
                "error_count": len(metrics.error_history),
            }

            report["overall"]["total_requests"] += metrics.request_count
            report["overall"]["total_tokens"] += metrics.total_tokens

            if metrics.request_count > 0:
                total_success_rate += metrics.success_rate
                total_tokens_per_second += metrics.tokens_per_second
                model_count += 1

        if model_count > 0:
            report["overall"]["avg_success_rate"] = total_success_rate / model_count
            report["overall"]["avg_tokens_per_second"] = (
                total_tokens_per_second / model_count
            )

        return report

    async def get_recommended_model(
        self, criteria: Dict[str, Any] = None
    ) -> Optional[str]:
        """获取推荐模型"""
        if not self.models:
            return None

        criteria = criteria or {}
        priority = criteria.get(
            "priority", "balanced"
        )  # balanced, speed, quality, size

        # 根据优先级选择模型
        if priority == "speed":
            # 选择性能评分最高的模型
            return max(
                self.models.items(),
                key=lambda x: x[1].performance_score,
                default=(None, None),
            )[0]
        elif priority == "quality":
            # 选择参数量最大的模型（通常质量更好）
            return max(
                self.models.items(),
                key=lambda x: x[1].parameters or 0,
                default=(None, None),
            )[0]
        elif priority == "size":
            # 选择大小最小的模型
            return min(
                self.models.items(),
                key=lambda x: self._parse_size_to_bytes(x[1].size or "0B"),
                default=(None, None),
            )[0]
        else:  # balanced
            # 平衡考虑性能评分和最近使用时间
            scored_models = []
            for name, info in self.models.items():
                score = info.performance_score * 0.7
                if info.last_used:
                    # 最近使用过的模型有加分
                    hours_since_use = (
                        datetime.now() - info.last_used
                    ).total_seconds() / 3600
                    if hours_since_use < 24:
                        score += 0.3 * (1 - hours_since_use / 24)
                scored_models.append((name, score))

            if scored_models:
                return max(scored_models, key=lambda x: x[1])[0]

        return list(self.models.keys())[0] if self.models else None

    def _parse_size_to_bytes(self, size_str: str) -> int:
        """将大小字符串解析为字节数"""
        if not size_str:
            return 0

        try:
            if size_str.endswith("B"):
                value = float(size_str[:-1])
                return int(value * 1_000_000_000)
            elif size_str.endswith("M"):
                value = float(size_str[:-1])
                return int(value * 1_000_000)
            elif size_str.endswith("G"):
                value = float(size_str[:-1])
                return int(value * 1_000_000_000)
            else:
                return int(size_str)
        except (ValueError, AttributeError):
            return 0


class LocalModelProvider(LocalProvider):
    """增强版本地模型提供者"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_manager = LocalModelManager(config)
        self.performance_monitoring = config.get("performance_monitoring", True)
        self.auto_model_selection = config.get("auto_model_selection", True)

        # 启动模型管理器
        asyncio.create_task(self.model_manager.start())

        logger.info(
            f"Initialized enhanced local model provider with auto-discovery: {self.auto_discovery_enabled}"
        )

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现（增强版）"""
        start_time = time.time()

        # 自动选择模型（如果启用）
        if self.auto_model_selection and "model" not in kwargs:
            recommended_model = await self.model_manager.get_recommended_model(
                criteria=kwargs.get("model_selection_criteria", {})
            )
            if recommended_model:
                kwargs["model"] = recommended_model
                logger.debug(f"Auto-selected model: {recommended_model}")

        try:
            # 调用父类实现
            response = await super()._generate_impl(prompt, **kwargs)

            # 记录性能
            if self.performance_monitoring:
                latency = time.time() - start_time
                tokens = response.usage.get("total_tokens", 0) if response.usage else 0
                model_name = kwargs.get("model", self.model)

                await self.model_manager.record_performance(
                    model_name=model_name, success=True, tokens=tokens, latency=latency
                )

            return response

        except Exception as e:
            # 记录失败
            if self.performance_monitoring:
                latency = time.time() - start_time
                model_name = kwargs.get("model", self.model)

                await self.model_manager.record_performance(
                    model_name=model_name,
                    success=False,
                    tokens=0,
                    latency=latency,
                    error=str(e),
                )

            raise

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本（增强版）"""
        start_time = time.time()

        # 自动选择模型（如果启用）
        if self.auto_model_selection and "model" not in kwargs:
            recommended_model = await self.model_manager.get_recommended_model(
                criteria=kwargs.get("model_selection_criteria", {})
            )
            if recommended_model:
                kwargs["model"] = recommended_model

        try:
            async for chunk in super().generate_stream(prompt, **kwargs):
                yield chunk

            # 记录成功（流式生成难以准确统计令牌数）
            if self.performance_monitoring:
                latency = time.time() - start_time
                model_name = kwargs.get("model", self.model)

                await self.model_manager.record_performance(
                    model_name=model_name,
                    success=True,
                    tokens=0,  # 流式生成难以统计
                    latency=latency,
                )

        except Exception as e:
            # 记录失败
            if self.performance_monitoring:
                latency = time.time() - start_time
                model_name = kwargs.get("model", self.model)

                await self.model_manager.record_performance(
                    model_name=model_name,
                    success=False,
                    tokens=0,
                    latency=latency,
                    error=str(e),
                )

            raise

    async def get_available_models(self) -> List[LocalModelInfo]:
        """获取可用模型列表"""
        return list(self.model_manager.models.values())

    async def get_model_performance(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型性能数据"""
        metrics = self.model_manager.performance_metrics.get(model_name)
        if not metrics:
            return None

        return {
            "request_count": metrics.request_count,
            "success_count": metrics.success_count,
            "success_rate": metrics.success_rate,
            "total_tokens": metrics.total_tokens,
            "avg_latency": metrics.avg_latency,
            "tokens_per_second": metrics.tokens_per_second,
            "error_count": len(metrics.error_history),
            "recent_errors": (
                metrics.error_history[-5:] if metrics.error_history else []
            ),
        }

    async def test_model(
        self, model_name: str, test_prompt: str = "Hello, how are you?"
    ) -> Dict[str, Any]:
        """测试模型"""
        start_time = time.time()

        try:
            response = await self._generate_impl(
                test_prompt, model=model_name, max_tokens=50
            )

            latency = time.time() - start_time
            tokens = response.usage.get("total_tokens", 0) if response.usage else 0

            return {
                "success": True,
                "latency": latency,
                "tokens": tokens,
                "tokens_per_second": tokens / latency if latency > 0 else 0,
                "response_preview": (
                    response.content[:100] + "..."
                    if len(response.content) > 100
                    else response.content
                ),
                "model": response.model,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency": time.time() - start_time,
            }

    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """拉取模型（Ollama专用）"""
        if not self.base_url.startswith("http://localhost:11434"):
            return {
                "success": False,
                "error": "Model pulling only supported for Ollama",
            }

        session = await self.get_session()
        try:
            async with session.post(
                f"{self.base_url}/pull",
                json={"name": model_name},
                timeout=300,  # 5分钟超时
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "status": data.get("status", "unknown"),
                        "message": f"Model {model_name} pull initiated",
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API error: {response.status} - {error_text}",
                    }
        finally:
            await self.release_session(session)

    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "local_providers": [],
        }

        # 检查各种本地服务
        providers_to_check = [
            ("Ollama", "http://localhost:11434/api/tags"),
            ("LM Studio", "http://localhost:1234/v1/models"),
            ("vLLM", "http://localhost:8000/v1/models"),
            ("Text Generation WebUI", "http://localhost:5000/api/v1/model"),
        ]

        for provider_name, url in providers_to_check:
            try:
                timeout = ClientTimeout(total=3)
                async with ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            system_info["local_providers"].append(
                                {"name": provider_name, "available": True, "url": url}
                            )
                        else:
                            system_info["local_providers"].append(
                                {
                                    "name": provider_name,
                                    "available": False,
                                    "url": url,
                                    "status": response.status,
                                }
                            )
            except Exception as e:
                system_info["local_providers"].append(
                    {
                        "name": provider_name,
                        "available": False,
                        "url": url,
                        "error": str(e),
                    }
                )

        return system_info

    async def close(self):
        """关闭Provider"""
        await self.model_manager.stop()
        await super().close()

        logger.info("Enhanced local model provider closed")
