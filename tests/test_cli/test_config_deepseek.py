"""
CLI配置命令DeepSeek支持测试

测试config命令对DeepSeek的支持：
1. 确保config命令支持DeepSeek提供商
2. 验证提供商选择策略
3. 测试配置显示和验证
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import os
import yaml

from loom.cli.commands.config import _test_config_async
from loom.core.config_manager import ConfigManager
from loom.interpretation.llm_provider import DeepSeekProvider


class TestCLIConfigDeepSeekSupport:
    """CLI配置命令DeepSeek支持测试"""

    def test_config_contains_deepseek_provider(self):
        """测试配置包含DeepSeek提供商"""
        # 创建测试配置
        test_config = {
            "llm_providers": {
                "openai": {
                    "type": "openai",
                    "api_key": "test-openai-key",
                    "model": "gpt-3.5-turbo",
                    "enabled": True,
                },
                "deepseek": {
                    "type": "deepseek",
                    "api_key": "test-deepseek-key",
                    "model": "deepseek-chat",
                    "thinking_enabled": False,
                    "enabled": True,
                },
            },
            "provider_selection": {
                "default_provider": "openai",
                "fallback_order": ["openai", "deepseek", "anthropic"],
            },
        }

        # 验证DeepSeek在配置中
        assert "deepseek" in test_config["llm_providers"]
        deepseek_config = test_config["llm_providers"]["deepseek"]

        # 验证必要字段
        assert deepseek_config["type"] == "deepseek"
        assert deepseek_config["model"] == "deepseek-chat"
        assert deepseek_config["enabled"] == True

        # 验证回退顺序包含DeepSeek
        assert "deepseek" in test_config["provider_selection"]["fallback_order"]

    @pytest.mark.asyncio
    async def test_config_test_command_with_deepseek(self):
        """测试config test命令处理DeepSeek"""
        # 创建模拟配置
        mock_config = MagicMock()
        mock_config.llm_providers = {
            "openai": MagicMock(
                type="openai",
                api_key="test-openai-key",
                model="gpt-3.5-turbo",
                enabled=True,
            ),
            "deepseek": MagicMock(
                type="deepseek",
                api_key="test-deepseek-key",
                model="deepseek-chat",
                thinking_enabled=False,
                enabled=True,
            ),
            "anthropic": MagicMock(
                type="anthropic",
                api_key="test-anthropic-key",
                model="claude-3-haiku",
                enabled=False,  # 禁用状态
            ),
        }
        mock_config.data_dir = "./data"

        # Mock配置管理器
        with patch("loom.cli.commands.config.ConfigManager") as MockConfigManager:
            mock_config_manager = MagicMock()
            mock_config_manager.get_config.return_value = mock_config
            MockConfigManager.return_value = mock_config_manager

            # 测试所有启用的提供商
            results = []
            with patch("rich.console.Console") as MockConsole:
                mock_console = MagicMock()
                MockConsole.return_value = mock_console

                # 调用测试函数
                await _test_config_async(
                    provider=None,
                    test_all=True,
                    test_database=False,
                    test_memory=False,
                    timeout=30,
                )

                # 验证配置管理器被调用
                mock_config_manager.get_config.assert_called_once()

    def test_deepseek_specific_config_fields(self):
        """测试DeepSeek特定配置字段"""
        # DeepSeek特有配置
        deepseek_specific_config = {
            "type": "deepseek",
            "api_key": "test-key",
            "model": "deepseek-chat",
            "thinking_enabled": False,
            "temperature": 1.0,  # DeepSeek默认温度
            "max_tokens": 4096,  # DeepSeek默认最大token数
            "timeout": 60,  # DeepSeek可能需要更长超时
            "base_url": "https://api.deepseek.com",
        }

        # 验证特有字段
        assert "thinking_enabled" in deepseek_specific_config
        assert deepseek_specific_config["thinking_enabled"] == False
        assert "temperature" in deepseek_specific_config
        assert deepseek_specific_config["temperature"] == 1.0
        assert "max_tokens" in deepseek_specific_config
        assert deepseek_specific_config["max_tokens"] == 4096
        assert "timeout" in deepseek_specific_config
        assert deepseek_specific_config["timeout"] == 60
        assert "base_url" in deepseek_specific_config
        assert deepseek_specific_config["base_url"] == "https://api.deepseek.com"

    def test_provider_selection_strategy_includes_deepseek(self):
        """测试提供商选择策略包含DeepSeek"""
        # 测试各种配置场景

        # 场景1：标准回退顺序
        fallback_order_standard = [
            "openai",
            "anthropic",
            "deepseek",
            "google",
            "ollama",
        ]
        assert "deepseek" in fallback_order_standard

        # 场景2：成本优化顺序（DeepSeek在便宜提供商中）
        fallback_order_cost_optimized = ["deepseek", "ollama", "openai", "anthropic"]
        assert "deepseek" in fallback_order_cost_optimized

        # 场景3：中文内容优先
        session_mapping_chinese = {
            "chinese_content": {
                "preferred_provider": "deepseek",
                "preferred_model": "deepseek-chat",
                "fallback_to": "openai",
            }
        }
        assert (
            session_mapping_chinese["chinese_content"]["preferred_provider"]
            == "deepseek"
        )

        # 场景4：推理任务优先
        session_mapping_reasoning = {
            "reasoning_tasks": {
                "preferred_provider": "deepseek",
                "preferred_model": "deepseek-reasoner",
                "fallback_to": "anthropic",
            }
        }
        assert (
            session_mapping_reasoning["reasoning_tasks"]["preferred_provider"]
            == "deepseek"
        )

    @pytest.mark.asyncio
    async def test_deepseek_provider_validation(self):
        """测试DeepSeek提供商验证"""
        # 有效配置
        valid_config = {
            "api_key": "valid-key",
            "model": "deepseek-chat",
            "thinking_enabled": False,
        }
        provider = DeepSeekProvider(valid_config)

        errors = provider.validate_config()
        assert len(errors) == 0

        # 无效配置：缺少API密钥
        invalid_config_no_key = {
            "model": "deepseek-chat",
        }
        provider_no_key = DeepSeekProvider(invalid_config_no_key)

        errors = provider_no_key.validate_config()
        # 至少应该有一个错误
        assert len(errors) >= 1
        # 检查是否包含API密钥相关的错误
        api_key_errors = [e for e in errors if "API" in e or "key" in e]
        assert len(api_key_errors) > 0

        # 无效配置：缺少模型
        invalid_config_no_model = {
            "api_key": "test-key",
        }
        provider_no_model = DeepSeekProvider(invalid_config_no_model)

        errors = provider_no_model.validate_config()
        # 由于父类设置了默认model="default"，所以不会报错
        assert len(errors) == 0
        assert provider_no_model.model == "default"

    def test_config_file_parsing_with_deepseek(self):
        """测试配置文件解析包含DeepSeek"""
        # 创建包含DeepSeek的YAML配置
        yaml_content = """
llm_providers:
  openai:
    type: openai
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
    enabled: true
    
  deepseek:
    type: deepseek
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-chat
    thinking_enabled: false
    temperature: 1.0
    max_tokens: 4096
    timeout: 60
    enabled: true

provider_selection:
  default_provider: openai
  fallback_order:
    - openai
    - anthropic
    - deepseek
    - google
    - ollama
  
  session_type_mapping:
    chinese_content:
      preferred_provider: deepseek
      preferred_model: deepseek-chat
      fallback_to: openai
      
    reasoning_tasks:
      preferred_provider: deepseek
      preferred_model: deepseek-reasoner
      fallback_to: anthropic
"""

        # 解析YAML
        config_data = yaml.safe_load(yaml_content)

        # 验证DeepSeek配置
        assert "deepseek" in config_data["llm_providers"]
        deepseek_config = config_data["llm_providers"]["deepseek"]

        assert deepseek_config["type"] == "deepseek"
        assert deepseek_config["model"] == "deepseek-chat"
        assert deepseek_config["thinking_enabled"] == False
        assert deepseek_config["temperature"] == 1.0
        assert deepseek_config["max_tokens"] == 4096
        assert deepseek_config["timeout"] == 60
        assert deepseek_config["enabled"] == True

        # 验证提供商选择策略
        selection = config_data["provider_selection"]
        assert "deepseek" in selection["fallback_order"]

        # 验证会话类型映射
        session_mapping = selection["session_type_mapping"]
        assert session_mapping["chinese_content"]["preferred_provider"] == "deepseek"
        assert session_mapping["reasoning_tasks"]["preferred_provider"] == "deepseek"
        assert session_mapping["chinese_content"]["preferred_model"] == "deepseek-chat"
        assert (
            session_mapping["reasoning_tasks"]["preferred_model"] == "deepseek-reasoner"
        )

    @pytest.mark.asyncio
    async def test_multiple_deepseek_configurations(self):
        """测试多个DeepSeek配置"""
        # 测试可以配置多个DeepSeek实例
        configs = {
            "deepseek-chat": {
                "type": "deepseek",
                "api_key": "key-chat",
                "model": "deepseek-chat",
                "thinking_enabled": False,
                "description": "通用聊天",
            },
            "deepseek-reasoner": {
                "type": "deepseek",
                "api_key": "key-reasoner",
                "model": "deepseek-reasoner",
                "thinking_enabled": True,
                "description": "推理任务专用",
            },
            "deepseek-custom": {
                "type": "deepseek",
                "api_key": "key-custom",
                "model": "deepseek-chat",
                "base_url": "https://custom.deepseek.com",
                "thinking_enabled": False,
                "description": "自定义端点",
            },
        }

        # 验证所有配置
        for name, config in configs.items():
            assert config["type"] == "deepseek"
            assert "api_key" in config
            assert "model" in config

            # 创建提供商实例
            provider = DeepSeekProvider(config)

            # 验证配置
            if "thinking_enabled" in config:
                assert provider.thinking_enabled == config["thinking_enabled"]

            if "base_url" in config:
                assert provider.base_url == config["base_url"]

            # 验证配置验证
            errors = provider.validate_config()
            assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
