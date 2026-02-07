"""
配置管理器

负责配置加载与环境变量管理，支持多层级配置。
支持环境变量插值、类型安全访问、配置热重载和完整性验证。
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, field_validator, ValidationError
from datetime import datetime
import asyncio
import threading
import time

from ..utils.logging_config import get_logger
from ..interpretation.key_manager import get_key_manager

logger = get_logger(__name__)


class LLMProviderConfig(BaseModel):
    """LLM提供商配置（增强版）"""

    type: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1000, ge=1, le=100000)
    timeout: int = Field(30, ge=1, le=300)
    max_retries: int = Field(3, ge=0, le=10)
    retry_delay: float = Field(1.0, ge=0.1, le=10.0)
    fallback_enabled: bool = True
    enabled: bool = True
    connection_pool_size: int = Field(5, ge=1, le=50)
    enable_batching: bool = False
    enable_caching: bool = True
    cache_ttl: int = Field(300, ge=60, le=86400)  # 5分钟

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class ProviderSelectionConfig(BaseModel):
    """Provider选择策略配置"""

    default_provider: str = "openai"
    fallback_order: List[str] = Field(
        default_factory=lambda: ["openai", "anthropic", "ollama"]
    )

    # 基于会话类型的Provider选择
    session_type_mapping: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # 自动切换策略
    auto_switch: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "health_check_interval": 60,
            "max_failures_before_switch": 3,
            "switch_back_after_success": True,
            "switch_back_delay": 300,
        }
    )

    # 成本优化策略
    cost_optimization: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "monthly_budget": 50.0,
            "alert_threshold": 0.8,
            "auto_switch_to_cheaper": True,
            "token_counting": True,
        }
    )


class MemoryConfig(BaseModel):
    """记忆存储配置"""

    backend: str = Field("sqlite", pattern="^(sqlite|duckdb|postgresql)$")
    db_path: str = "./data/loom_memory.db"
    vector_store_enabled: bool = False
    max_memories_per_session: int = Field(1000, ge=1, le=100000)
    auto_summarize: bool = True
    summarization_interval_days: int = Field(7, ge=1, le=365)


class SessionDefaultsConfig(BaseModel):
    """会话默认配置"""

    default_canon_path: str = "./canon"
    default_llm_provider: str = "openai"
    max_turns: Optional[int] = Field(None, ge=1)
    auto_save_interval: int = Field(5, ge=1, le=100)
    intervention_allowed: bool = True
    retcon_allowed: bool = True


class PerformanceConfig(BaseModel):
    """性能配置"""

    max_prompt_length: int = Field(8000, ge=100, le=100000)
    max_memories_per_prompt: int = Field(10, ge=1, le=100)
    enable_response_caching: bool = True
    cache_size_mb: int = Field(100, ge=1, le=10000)


class SecurityConfig(BaseModel):
    """安全配置"""

    allow_file_system_access: bool = True
    max_session_duration_hours: int = Field(24, ge=1, le=720)
    intervention_rate_limit: int = Field(10, ge=1, le=1000)
    require_justification_for_retcon: bool = True


class NarrativeConfig(BaseModel):
    """叙事解释器配置"""

    enabled: bool = True
    consistency_check_enabled: bool = True
    continuity_check_enabled: bool = True
    auto_summarize: bool = True
    summarization_interval_turns: int = Field(10, ge=1, le=100)
    narrative_arc_tracking: bool = True
    max_narrative_arcs: int = Field(5, ge=1, le=20)
    default_narrative_tone: str = Field(
        "neutral", pattern="^(neutral|serious|humorous|dramatic|mysterious)$"
    )
    default_narrative_pace: str = Field("normal", pattern="^(slow|normal|fast)$")

    # 一致性检查配置
    consistency_threshold: float = Field(0.7, ge=0.0, le=1.0)
    max_continuity_issues: int = Field(5, ge=0, le=50)

    # 档案配置
    auto_archive: bool = True
    archive_interval_turns: int = Field(50, ge=10, le=1000)
    max_archive_versions: int = Field(10, ge=1, le=100)
    export_format: str = Field("markdown", pattern="^(markdown|json|yaml)$")


class MonitoringConfig(BaseModel):
    """监控配置"""

    enable_metrics: bool = True
    metrics_port: int = Field(9090, ge=1024, le=65535)
    enable_tracing: bool = False
    log_retention_days: int = Field(30, ge=1, le=3650)


@dataclass
class AppConfig:
    """应用配置（增强版）"""

    # LLM配置
    llm_providers: Dict[str, LLMProviderConfig] = field(default_factory=dict)

    # Provider选择策略
    provider_selection: ProviderSelectionConfig = field(
        default_factory=ProviderSelectionConfig
    )

    # 记忆配置
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    # 会话默认配置
    session_defaults: SessionDefaultsConfig = field(
        default_factory=SessionDefaultsConfig
    )

    # 叙事解释器配置
    narrative: NarrativeConfig = field(default_factory=NarrativeConfig)

    # 运行时配置
    max_concurrent_turns: int = Field(3, ge=1, le=100)
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    data_dir: str = "./data"
    cache_enabled: bool = True
    cache_ttl_minutes: int = Field(60, ge=1, le=10080)

    # 性能配置
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # 安全配置
    security: SecurityConfig = field(default_factory=SecurityConfig)

    # 监控配置
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # 扩展配置
    plugins: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # 元数据
    loaded_at: datetime = field(default_factory=datetime.now)
    config_path: Optional[str] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], config_path: Optional[str] = None
    ) -> "AppConfig":
        """从字典创建配置，支持环境变量插值"""
        # 处理环境变量插值
        data = cls._interpolate_env_vars(data)

        # 提取基本字段的值，使用Field()的默认值
        max_concurrent_turns = data.get("max_concurrent_turns", 3)
        log_level = data.get("log_level", "INFO")
        data_dir = data.get("data_dir", "./data")
        cache_enabled = data.get("cache_enabled", True)
        cache_ttl_minutes = data.get("cache_ttl_minutes", 60)
        plugins = data.get("plugins", {})

        # 创建配置实例，手动传递所有字段值
        config = cls(
            max_concurrent_turns=max_concurrent_turns,
            log_level=log_level,
            data_dir=data_dir,
            cache_enabled=cache_enabled,
            cache_ttl_minutes=cache_ttl_minutes,
            plugins=plugins,
        )
        config.config_path = config_path

        # 处理LLM提供商
        if "llm_providers" in data:
            for name, provider_data in data["llm_providers"].items():
                try:
                    config.llm_providers[name] = LLMProviderConfig(**provider_data)
                except ValidationError as e:
                    logger.warning(f"Invalid LLM provider config for {name}: {e}")
                    # 使用默认值
                    config.llm_providers[name] = LLMProviderConfig(type=name)

        # 处理Provider选择策略
        if "provider_selection" in data:
            try:
                config.provider_selection = ProviderSelectionConfig(
                    **data["provider_selection"]
                )
            except ValidationError as e:
                logger.warning(f"Invalid provider selection config: {e}")

        # 处理记忆配置
        if "memory" in data:
            try:
                config.memory = MemoryConfig(**data["memory"])
            except ValidationError as e:
                logger.warning(f"Invalid memory config: {e}")

        # 处理会话默认配置
        if "session_defaults" in data:
            try:
                config.session_defaults = SessionDefaultsConfig(
                    **data["session_defaults"]
                )
            except ValidationError as e:
                logger.warning(f"Invalid session defaults config: {e}")

        # 处理性能配置
        if "performance" in data:
            try:
                config.performance = PerformanceConfig(**data["performance"])
            except ValidationError as e:
                logger.warning(f"Invalid performance config: {e}")

        # 处理安全配置
        if "security" in data:
            try:
                config.security = SecurityConfig(**data["security"])
            except ValidationError as e:
                logger.warning(f"Invalid security config: {e}")

        # 处理叙事配置
        if "narrative" in data:
            try:
                config.narrative = NarrativeConfig(**data["narrative"])
            except ValidationError as e:
                logger.warning(f"Invalid narrative config: {e}")

        # 处理监控配置
        if "monitoring" in data:
            try:
                config.monitoring = MonitoringConfig(**data["monitoring"])
            except ValidationError as e:
                logger.warning(f"Invalid monitoring config: {e}")

        return config

    @staticmethod
    def _interpolate_env_vars(data: Any) -> Any:
        """递归处理环境变量插值"""
        if isinstance(data, dict):
            return {k: AppConfig._interpolate_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [AppConfig._interpolate_env_vars(item) for item in data]
        elif isinstance(data, str):
            # 匹配 ${VAR_NAME:default_value} 格式
            pattern = r"\$\{([A-Za-z0-9_]+)(?::([^}]*))?\}"

            def replace(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""
                return os.environ.get(var_name, default_value)

            return re.sub(pattern, replace, data)
        else:
            return data

    def validate(self) -> List[str]:
        """验证配置完整性，返回错误列表"""
        errors = []

        # 检查必需配置
        if not self.llm_providers:
            errors.append("至少需要一个LLM提供商配置")

        # 检查默认LLM提供商是否存在
        default_provider = self.session_defaults.default_llm_provider
        if default_provider not in self.llm_providers:
            errors.append(f"默认LLM提供商 '{default_provider}' 未配置")

        # 检查数据目录是否可写
        try:
            Path(self.data_dir).mkdir(parents=True, exist_ok=True)
            test_file = Path(self.data_dir) / ".test_write"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors.append(f"数据目录不可写: {e}")

        # 检查配置路径是否存在
        if self.config_path and not Path(self.config_path).exists():
            errors.append(f"配置文件不存在: {self.config_path}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        # 构建结果字典
        result = {}

        # 处理LLM提供商
        result["llm_providers"] = {
            name: provider.dict() for name, provider in self.llm_providers.items()
        }

        # 处理其他Pydantic模型
        result["provider_selection"] = self.provider_selection.dict()
        result["memory"] = self.memory.dict()
        result["session_defaults"] = self.session_defaults.dict()
        result["narrative"] = self.narrative.dict()
        result["performance"] = self.performance.dict()
        result["security"] = self.security.dict()
        result["monitoring"] = self.monitoring.dict()

        # 处理基本字段 - 直接获取实际值
        result["max_concurrent_turns"] = self.max_concurrent_turns
        result["log_level"] = self.log_level
        result["data_dir"] = self.data_dir
        result["cache_enabled"] = self.cache_enabled
        result["cache_ttl_minutes"] = self.cache_ttl_minutes

        # 处理其他字段
        result["plugins"] = self.plugins

        return result


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None, enable_watch: bool = False):
        self.config_path = config_path or self._find_config_file()
        self.config: Optional[AppConfig] = None
        self._callbacks: List[callable] = []
        self._watch_enabled = enable_watch
        self._watch_thread: Optional[threading.Thread] = None
        self._last_modified: float = 0

        # 加载配置
        self._load_config()

        # 验证配置
        errors = self.validate()
        if errors:
            logger.warning(f"Configuration validation warnings: {errors}")

        logger.info(f"ConfigManager initialized with config from {self.config_path}")

        # 启动文件监视
        if enable_watch:
            self._start_watch()

    def _find_config_file(self) -> str:
        """查找配置文件"""
        possible_paths = [
            "./config/default_config.yaml",
            "./config/config.yaml",
            "./config.yaml",
            "~/.loom/config.yaml",
            "/etc/loom/config.yaml",
        ]

        for path in possible_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                return expanded

        # 如果找不到，使用默认路径
        default_path = "./config/default_config.yaml"
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        return default_path

    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                self._last_modified = os.path.getmtime(self.config_path)
            else:
                data = {}
                logger.warning(
                    f"Config file not found at {self.config_path}, using defaults"
                )

            # 环境变量插值已经在AppConfig.from_dict中处理
            # 额外合并环境变量覆盖
            self._merge_env_overrides(data)

            self.config = AppConfig.from_dict(data, self.config_path)
            logger.info(f"Configuration loaded from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            # 使用默认配置
            self.config = AppConfig()

    def _merge_env_overrides(self, data: Dict[str, Any]):
        """合并环境变量覆盖"""
        # 初始化KeyManager
        key_manager = get_key_manager()

        # LLM API密钥覆盖（从KeyManager获取）
        provider_names = ["openai", "anthropic", "google", "azure", "ollama", "local"]
        for provider_name in provider_names:
            # 首先尝试从KeyManager获取密钥
            api_key = key_manager.get_key(provider_name)
            if api_key:
                if "llm_providers" not in data:
                    data["llm_providers"] = {}
                if provider_name not in data["llm_providers"]:
                    data["llm_providers"][provider_name] = {"type": provider_name}
                data["llm_providers"][provider_name]["api_key"] = api_key
                logger.debug(f"Using key from KeyManager for provider {provider_name}")

            # 然后检查环境变量（作为备用）
            env_key = f"{provider_name.upper()}_API_KEY"
            if env_key in os.environ:
                if "llm_providers" not in data:
                    data["llm_providers"] = {}
                if provider_name not in data["llm_providers"]:
                    data["llm_providers"][provider_name] = {"type": provider_name}
                data["llm_providers"][provider_name]["api_key"] = os.environ[env_key]
                logger.debug(
                    f"Using key from environment variable for provider {provider_name}"
                )

        # 通用环境变量覆盖
        env_mappings = {
            "LOOM_LOG_LEVEL": "log_level",
            "LOOM_DATA_DIR": "data_dir",
            "LOOM_MAX_CONCURRENT_TURNS": "max_concurrent_turns",
            "LOOM_CACHE_ENABLED": "cache_enabled",
            "LOOM_CACHE_TTL_MINUTES": "cache_ttl_minutes",
            "LOOM_DEFAULT_PROVIDER": "session_defaults.default_llm_provider",
            "LOOM_NARRATIVE_ENABLED": "narrative.enabled",
            "LOOM_CONSISTENCY_CHECK_ENABLED": "narrative.consistency_check_enabled",
            "LOOM_AUTO_ARCHIVE": "narrative.auto_archive",
        }

        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                # 处理嵌套路径
                keys = config_key.split(".")
                current = data
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # 转换类型
                value = os.environ[env_var]
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit() and value.count(".") <= 1:
                    value = float(value)

                current[keys[-1]] = value
                logger.debug(
                    f"Overriding config {config_key} with environment variable {env_var}"
                )

    def get_config(self) -> AppConfig:
        """获取配置"""
        if self.config is None:
            self._load_config()
        return self.config

    def save_config(
        self, config: Optional[AppConfig] = None, path: Optional[str] = None
    ):
        """保存配置到文件"""
        if config is None:
            config = self.config

        if config is None:
            logger.error("No configuration to save")
            return

        save_path = path or self.config_path

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 转换为字典
            data = config.to_dict()

            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            self._last_modified = os.path.getmtime(save_path)
            logger.info(f"Configuration saved to {save_path}")

        except Exception as e:
            logger.error(f"Failed to save config to {save_path}: {e}")

    def get_llm_provider_config(
        self, provider_name: str
    ) -> Optional[LLMProviderConfig]:
        """获取LLM提供商配置"""
        if self.config is None:
            return None
        return self.config.llm_providers.get(provider_name)

    def update_llm_api_key(self, provider_name: str, api_key: str):
        """更新LLM API密钥"""
        if self.config is None:
            return

        if provider_name not in self.config.llm_providers:
            self.config.llm_providers[provider_name] = LLMProviderConfig(
                type=provider_name
            )

        self.config.llm_providers[provider_name].api_key = api_key
        logger.info(f"Updated API key for provider {provider_name}")

    def reload(self) -> bool:
        """重新加载配置"""
        logger.info("Reloading configuration")
        old_config = self.config
        self._load_config()

        # 触发回调
        if old_config != self.config:
            self._notify_callbacks(old_config, self.config)
            return True
        return False

    def validate(self) -> List[str]:
        """验证配置完整性"""
        if self.config is None:
            return ["Configuration not loaded"]
        return self.config.validate()

    def register_callback(self, callback: callable):
        """注册配置变更回调"""
        self._callbacks.append(callback)
        logger.debug(
            f"Registered config change callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}"
        )

    def _notify_callbacks(self, old_config: AppConfig, new_config: AppConfig):
        """通知所有回调"""
        for callback in self._callbacks:
            try:
                callback(old_config, new_config)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")

    def _start_watch(self):
        """启动配置文件监视"""

        def watch_loop():
            while self._watch_enabled:
                try:
                    if os.path.exists(self.config_path):
                        current_modified = os.path.getmtime(self.config_path)
                        if current_modified > self._last_modified:
                            logger.info(f"Config file changed, reloading...")
                            self.reload()
                            self._last_modified = current_modified
                except Exception as e:
                    logger.error(f"Error watching config file: {e}")

                time.sleep(5)  # 每5秒检查一次

        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()
        logger.info("Config file watch started")

    def stop_watch(self):
        """停止配置文件监视"""
        self._watch_enabled = False
        if self._watch_thread:
            self._watch_thread.join(timeout=2)
        logger.info("Config file watch stopped")

    def get_config_snapshot(self) -> Dict[str, Any]:
        """获取配置快照（安全版本，隐藏敏感信息）"""
        if self.config is None:
            return {}

        snapshot = self.config.to_dict()

        # 隐藏敏感信息
        if "llm_providers" in snapshot:
            for provider in snapshot["llm_providers"].values():
                if "api_key" in provider and provider["api_key"]:
                    provider["api_key"] = "***REDACTED***"

        return snapshot

    async def async_reload(self):
        """异步重新加载配置"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.reload)
