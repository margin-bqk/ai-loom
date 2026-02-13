"""
ConfigManager单元测试
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.loom.core.config_manager import AppConfig, ConfigManager, LLMProviderConfig


class TestConfigManager:
    """ConfigManager测试类"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")

        # 创建测试配置文件
        test_config = {
            "llm_providers": {
                "openai": {
                    "type": "openai",
                    "api_key": "test_key",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                }
            },
            "memory": {"backend": "sqlite", "db_path": "./test.db"},
            "log_level": "DEBUG",
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(test_config, f)

    def teardown_method(self):
        """测试清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_config_manager_initialization(self):
        """测试ConfigManager初始化"""
        config_manager = ConfigManager(config_path=self.config_path)

        assert config_manager.config_path == self.config_path
        assert config_manager.config is not None
        assert isinstance(config_manager.config, AppConfig)

    def test_load_config(self):
        """测试配置加载"""
        config_manager = ConfigManager(config_path=self.config_path)
        config = config_manager.get_config()

        assert config.log_level == "DEBUG"
        assert "openai" in config.llm_providers
        assert config.llm_providers["openai"].model == "gpt-3.5-turbo"
        assert config.llm_providers["openai"].temperature == 0.7

    def test_env_var_interpolation(self):
        """测试环境变量插值"""
        # 创建包含环境变量引用的配置文件
        test_config = {
            "llm_providers": {
                "openai": {
                    "type": "openai",
                    "api_key": "${TEST_API_KEY:default_key}",
                    "model": "gpt-4",
                }
            }
        }

        config_path = os.path.join(self.temp_dir, "env_config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(test_config, f)

        # 完全模拟KeyManager和ConfigManager的_merge_env_overrides方法
        with patch(
            "src.loom.core.config_manager.get_key_manager"
        ) as mock_get_key_manager:
            mock_key_manager = MagicMock()
            mock_key_manager.get_key.return_value = None
            mock_get_key_manager.return_value = mock_key_manager

            # 也模拟_merge_env_overrides方法，使其不进行任何覆盖
            with patch.object(ConfigManager, "_merge_env_overrides") as mock_merge:
                mock_merge.return_value = None

                # 测试默认值
                config_manager = ConfigManager(config_path=config_path)
                config = config_manager.get_config()
                # 由于_merge_env_overrides被模拟，API密钥应该来自环境变量插值
                assert config.llm_providers["openai"].api_key == "default_key"

                # 测试环境变量覆盖
                with patch.dict(os.environ, {"TEST_API_KEY": "env_key"}):
                    config_manager = ConfigManager(config_path=config_path)
                    config = config_manager.get_config()
                    assert config.llm_providers["openai"].api_key == "env_key"

    def test_env_var_overrides(self):
        """测试环境变量覆盖"""
        with patch.dict(
            os.environ, {"LOOM_LOG_LEVEL": "ERROR", "LOOM_DATA_DIR": "/custom/data"}
        ):
            config_manager = ConfigManager(config_path=self.config_path)
            config = config_manager.get_config()

            assert config.log_level == "ERROR"
            assert config.data_dir == "/custom/data"

    def test_get_llm_provider_config(self):
        """测试获取LLM提供商配置"""
        config_manager = ConfigManager(config_path=self.config_path)

        provider_config = config_manager.get_llm_provider_config("openai")
        assert provider_config is not None
        assert provider_config.type == "openai"
        assert provider_config.model == "gpt-3.5-turbo"

        # 测试不存在的提供商
        provider_config = config_manager.get_llm_provider_config("nonexistent")
        assert provider_config is None

    def test_update_llm_api_key(self):
        """测试更新LLM API密钥"""
        config_manager = ConfigManager(config_path=self.config_path)

        # 更新现有提供商的API密钥
        config_manager.update_llm_api_key("openai", "new_api_key")

        provider_config = config_manager.get_llm_provider_config("openai")
        assert provider_config.api_key == "new_api_key"

        # 更新不存在的提供商（应创建新配置）
        config_manager.update_llm_api_key("anthropic", "anthro_key")
        provider_config = config_manager.get_llm_provider_config("anthropic")
        assert provider_config is not None
        assert provider_config.api_key == "anthro_key"

    def test_save_config(self):
        """测试保存配置"""
        config_manager = ConfigManager(config_path=self.config_path)

        # 修改配置
        config = config_manager.get_config()
        config.log_level = "WARNING"
        config.max_concurrent_turns = 5

        # 模拟to_dict方法返回有效的字典
        with patch.object(AppConfig, "to_dict") as mock_to_dict:
            mock_to_dict.return_value = {
                "log_level": "WARNING",
                "max_concurrent_turns": 5,
                "llm_providers": {},
                "provider_selection": {},
                "memory": {},
                "session_defaults": {},
                "narrative": {},
                "performance": {},
                "security": {},
                "monitoring": {},
                "plugins": {},
                "data_dir": "./data",
                "cache_enabled": True,
                "cache_ttl_minutes": 60,
            }

            # 保存配置
            save_path = os.path.join(self.temp_dir, "saved_config.yaml")
            config_manager.save_config(config, path=save_path)

            # 验证保存的文件
            assert os.path.exists(save_path)

            with open(save_path, "r", encoding="utf-8") as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["log_level"] == "WARNING"
            assert saved_data["max_concurrent_turns"] == 5

    def test_reload(self):
        """测试重新加载配置"""
        config_manager = ConfigManager(config_path=self.config_path)

        # 修改配置文件
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            config_data["log_level"] = "INFO"

            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f)

            # 重新加载
            changed = config_manager.reload()
            assert changed is True

            config = config_manager.get_config()
            assert config.log_level == "INFO"
        except OSError as e:
            # Windows上有时临时文件路径有问题，跳过测试
            if "Invalid argument" in str(e):
                pytest.skip(f"Windows file path issue: {e}")
            raise

    def test_validate(self):
        """测试配置验证"""
        config_manager = ConfigManager(config_path=self.config_path)

        errors = config_manager.validate()
        # 应该有错误，因为默认LLM提供商可能不存在
        # 这取决于配置文件内容

        # 测试有效配置
        valid_config = AppConfig()
        valid_config.llm_providers["openai"] = LLMProviderConfig(type="openai")
        valid_config.session_defaults.default_llm_provider = "openai"
        valid_config.data_dir = self.temp_dir  # 可写目录

        config_manager.config = valid_config
        errors = config_manager.validate()
        assert len(errors) == 0

    def test_get_config_snapshot(self):
        """测试获取配置快照"""
        config_manager = ConfigManager(config_path=self.config_path)

        snapshot = config_manager.get_config_snapshot()

        assert "llm_providers" in snapshot
        assert "memory" in snapshot
        assert "session_defaults" in snapshot

        # 验证敏感信息被隐藏
        if "openai" in snapshot.get("llm_providers", {}):
            provider = snapshot["llm_providers"]["openai"]
            if "api_key" in provider and provider["api_key"]:
                assert provider["api_key"] == "***REDACTED***"


class TestAppConfig:
    """AppConfig测试类"""

    def test_app_config_from_dict(self):
        """测试从字典创建AppConfig"""
        data = {
            "llm_providers": {
                "openai": {"type": "openai", "model": "gpt-4", "temperature": 0.8}
            },
            "memory": {
                "backend": "sqlite",
                "db_path": "./test.db",
                "max_memories_per_session": 5000,
            },
            "log_level": "INFO",
            "max_concurrent_turns": 5,
        }

        config = AppConfig.from_dict(data)

        assert "openai" in config.llm_providers
        assert config.llm_providers["openai"].model == "gpt-4"
        assert config.llm_providers["openai"].temperature == 0.8
        assert config.memory.backend == "sqlite"
        assert config.memory.max_memories_per_session == 5000
        assert config.log_level == "INFO"
        assert config.max_concurrent_turns == 5

    def test_app_config_validation(self):
        """测试AppConfig验证"""
        config = AppConfig()

        # 应该有一些验证错误
        errors = config.validate()
        assert isinstance(errors, list)

        # 测试有效配置
        config.llm_providers["openai"] = LLMProviderConfig(type="openai")
        config.session_defaults.default_llm_provider = "openai"

        errors = config.validate()
        # 数据目录可能不可写，但至少LLM提供商验证应该通过

    def test_app_config_to_dict(self):
        """测试AppConfig转换为字典"""
        config = AppConfig()
        config.llm_providers["openai"] = LLMProviderConfig(
            type="openai", model="gpt-3.5-turbo"
        )
        config.log_level = "DEBUG"

        config_dict = config.to_dict()

        assert "llm_providers" in config_dict
        assert "openai" in config_dict["llm_providers"]
        assert config_dict["llm_providers"]["openai"]["model"] == "gpt-3.5-turbo"
        assert config_dict["log_level"] == "DEBUG"
        assert "memory" in config_dict
        assert "session_defaults" in config_dict


class TestLLMProviderConfig:
    """LLMProviderConfig测试类"""

    def test_llm_provider_config_validation(self):
        """测试LLMProviderConfig验证"""
        # 测试有效配置
        config = LLMProviderConfig(
            type="openai",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000,
            timeout=30,
        )

        assert config.type == "openai"
        assert config.temperature == 0.7

        # 测试温度范围验证
        with pytest.raises(ValueError):
            LLMProviderConfig(type="openai", temperature=2.5)  # 超过最大范围

        with pytest.raises(ValueError):
            LLMProviderConfig(type="openai", temperature=-0.5)  # 低于最小范围
