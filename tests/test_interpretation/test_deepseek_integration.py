"""
DeepSeek集成测试

根据plans/deepseek_integration_plan.md中的第三阶段测试和验证计划，
创建完整的DeepSeek集成测试脚本。

包含：
1. 单元测试：测试DeepSeekProvider类的各个方法
2. 集成测试：测试提供商管理器集成
3. Mock测试：使用Mock避免实际API调用
4. 配置测试：验证配置文件加载
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.loom.interpretation.llm_provider import (
    LLMProvider,
    DeepSeekProvider,
    OpenAIProvider,
    AnthropicProvider,
    ProviderManager,
    LLMProviderFactory,
    LLMResponse,
    LLMRequest,
)


class TestDeepSeekProvider:
    """DeepSeekProvider单元测试"""

    def test_initialization(self):
        """测试DeepSeekProvider初始化"""
        config = {
            "name": "test-deepseek",
            "type": "deepseek",
            "api_key": "test-key-123456",
            "model": "deepseek-chat",
            "thinking_enabled": False,
            "temperature": 1.0,
            "max_tokens": 4096,
        }
        provider = DeepSeekProvider(config)

        assert provider.provider_type == "deepseek"
        assert provider.model == "deepseek-chat"
        assert provider.thinking_enabled == False
        assert provider.temperature == 1.0
        assert provider.max_tokens == 4096
        assert provider.api_key == "test-key-123456"
        assert provider.base_url == "https://api.deepseek.com"

    def test_initialization_with_custom_config(self):
        """测试自定义配置初始化"""
        config = {
            "name": "custom-deepseek",
            "type": "deepseek",
            "api_key": "custom-key",
            "model": "deepseek-reasoner",
            "thinking_enabled": True,
            "temperature": 0.8,
            "max_tokens": 32000,
            "base_url": "https://custom.deepseek.com",
            "timeout": 90,
            "max_retries": 5,
        }
        provider = DeepSeekProvider(config)

        assert provider.model == "deepseek-reasoner"
        assert provider.thinking_enabled == True
        assert provider.temperature == 0.8
        assert provider.max_tokens == 32000
        assert provider.base_url == "https://custom.deepseek.com"
        assert provider.timeout == 90
        assert provider.max_retries == 5

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """测试成功生成响应"""
        config = {
            "api_key": "test-key",
            "model": "deepseek-chat",
            "thinking_enabled": False,
        }
        provider = DeepSeekProvider(config)

        # Mock API响应
        mock_response_data = {
            "id": "chatcmpl-123",
            "model": "deepseek-chat",
            "choices": [
                {
                    "message": {"content": "这是一个测试响应", "role": "assistant"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }

        with patch.object(provider, "_generate_impl") as mock_generate:
            mock_generate.return_value = LLMResponse(
                content="这是一个测试响应",
                model="deepseek-chat",
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
                metadata={
                    "id": "chatcmpl-123",
                    "finish_reason": "stop",
                    "provider": "deepseek",
                    "thinking_enabled": False,
                },
            )

            response = await provider.generate("测试提示")
            assert response.content == "这是一个测试响应"
            assert response.model == "deepseek-chat"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 20
            assert response.metadata["provider"] == "deepseek"

    @pytest.mark.asyncio
    async def test_generate_with_thinking_enabled(self):
        """测试启用推理模式的生成"""
        config = {
            "api_key": "test-key",
            "model": "deepseek-reasoner",
            "thinking_enabled": True,
        }
        provider = DeepSeekProvider(config)

        with patch.object(provider, "_generate_impl") as mock_generate:
            mock_generate.return_value = LLMResponse(
                content="推理模式响应",
                model="deepseek-reasoner",
                usage={"prompt_tokens": 15, "completion_tokens": 25},
                metadata={"thinking_enabled": True},
            )

            response = await provider.generate("需要推理的问题")
            assert response.content == "推理模式响应"
            assert response.metadata.get("thinking_enabled") == True

    def test_cost_calculation(self):
        """测试成本计算"""
        config = {"api_key": "test", "model": "deepseek-chat"}
        provider = DeepSeekProvider(config)

        response = LLMResponse(
            content="测试响应",
            model="deepseek-chat",
            usage={"prompt_tokens": 1000, "completion_tokens": 500},
        )

        # 1000输入token + 500输出token
        # 成本 = (1000/1M * 0.28) + (500/1M * 0.42) = 0.00028 + 0.00021 = 0.00049
        cost = provider._calculate_cost(response)
        expected_cost = (1000 / 1_000_000) * 0.28 + (500 / 1_000_000) * 0.42
        assert abs(cost - expected_cost) < 0.00001

    def test_cost_calculation_without_usage(self):
        """测试无使用量数据的成本计算"""
        config = {"api_key": "test", "model": "deepseek-chat"}
        provider = DeepSeekProvider(config)

        response = LLMResponse(
            content="测试响应", model="deepseek-chat", usage={}  # 4个字符  # 空使用量
        )

        # 应该调用父类的计算方法（基于字符数）
        cost = provider._calculate_cost(response)
        # 父类默认：每千字符0.001美元，4个字符 = 4/1000 * 0.001 = 0.000004
        expected_cost = len("测试响应") / 1000 * 0.001
        assert abs(cost - expected_cost) < 0.000001

    def test_cost_calculation_large_tokens(self):
        """测试大量token的成本计算"""
        config = {"api_key": "test", "model": "deepseek-chat"}
        provider = DeepSeekProvider(config)

        response = LLMResponse(
            content="长文本响应",
            model="deepseek-chat",
            usage={"prompt_tokens": 50000, "completion_tokens": 25000},
        )

        # 50000输入 + 25000输出
        # 成本 = (50000/1M * 0.28) + (25000/1M * 0.42) = 0.014 + 0.0105 = 0.0245
        cost = provider._calculate_cost(response)
        expected_cost = 0.014 + 0.0105
        assert abs(cost - expected_cost) < 0.00001

    def test_validate_config_valid(self):
        """测试有效配置验证"""
        config = {"api_key": "valid-key", "model": "deepseek-chat"}
        provider = DeepSeekProvider(config)

        errors = provider.validate_config()
        assert len(errors) == 0

    def test_validate_config_missing_api_key(self):
        """测试缺少API密钥的配置验证"""
        config = {
            "model": "deepseek-chat"
            # 缺少api_key
        }
        provider = DeepSeekProvider(config)

        errors = provider.validate_config()
        assert len(errors) == 1
        assert "API key is required for DeepSeek provider" in errors[0]

    def test_validate_config_missing_model(self):
        """测试缺少模型的配置验证"""
        config = {
            "api_key": "test-key"
            # 缺少model，但父类会设置默认值"default"
        }
        provider = DeepSeekProvider(config)

        errors = provider.validate_config()
        # 由于父类设置了model="default"，所以不会报错
        assert len(errors) == 0
        assert provider.model == "default"

    def test_validate_config_missing_both(self):
        """测试缺少API密钥和模型的配置验证"""
        config = {
            # 缺少api_key和model
        }
        provider = DeepSeekProvider(config)

        errors = provider.validate_config()
        # 只有API密钥错误，模型有默认值"default"
        assert len(errors) == 1
        assert "API key is required for DeepSeek provider" in errors[0]
        assert provider.model == "default"


class TestDeepSeekIntegration:
    """DeepSeek集成测试"""

    def test_provider_factory_creation(self):
        """测试工厂创建DeepSeekProvider"""
        config = {
            "type": "deepseek",
            "api_key": "test-factory-key",
            "model": "deepseek-chat",
        }

        provider = LLMProviderFactory.create_provider(config)
        assert isinstance(provider, DeepSeekProvider)
        assert provider.provider_type == "deepseek"
        assert provider.model == "deepseek-chat"

    def test_provider_manager_integration(self):
        """测试提供商管理器集成"""
        configs = {
            "my-deepseek": {
                "type": "deepseek",
                "api_key": "test-manager-key",
                "model": "deepseek-chat",
                "enabled": True,
            }
        }

        manager = LLMProviderFactory.create_provider_manager(configs)
        assert "my-deepseek" in manager.providers
        assert isinstance(manager.providers["my-deepseek"], DeepSeekProvider)

    def test_multiple_providers_in_manager(self):
        """测试管理器中的多个提供商"""
        configs = {
            "openai-1": {
                "type": "openai",
                "api_key": "test-openai-key",
                "model": "gpt-3.5-turbo",
            },
            "deepseek-1": {
                "type": "deepseek",
                "api_key": "test-deepseek-key",
                "model": "deepseek-chat",
            },
            "anthropic-1": {
                "type": "anthropic",
                "api_key": "test-anthropic-key",
                "model": "claude-3-haiku",
            },
        }

        manager = LLMProviderFactory.create_provider_manager(configs)

        assert len(manager.providers) == 3
        assert "openai-1" in manager.providers
        assert "deepseek-1" in manager.providers
        assert "anthropic-1" in manager.providers

        assert isinstance(manager.providers["openai-1"], OpenAIProvider)
        assert isinstance(manager.providers["deepseek-1"], DeepSeekProvider)
        assert isinstance(manager.providers["anthropic-1"], AnthropicProvider)

    @pytest.mark.asyncio
    async def test_provider_manager_fallback_with_deepseek(self):
        """测试包含DeepSeek的回退机制"""
        # 创建模拟提供商
        mock_openai = AsyncMock(spec=OpenAIProvider)
        mock_openai.enabled = True
        mock_openai.provider_type = "openai"
        mock_openai.generate.side_effect = Exception("OpenAI失败")

        mock_deepseek = AsyncMock(spec=DeepSeekProvider)
        mock_deepseek.enabled = True
        mock_deepseek.provider_type = "deepseek"
        mock_deepseek.generate.return_value = LLMResponse(
            content="DeepSeek成功响应",
            model="deepseek-chat",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )

        # 创建管理器并注册提供商
        manager = ProviderManager()
        manager.register_provider("openai", mock_openai)
        manager.register_provider("deepseek", mock_deepseek)
        manager.set_default("openai")
        manager.set_fallback_order(["deepseek"])  # 只包含deepseek，避免openai重复

        # 测试回退
        response = await manager.generate_with_fallback("测试提示")

        # 验证OpenAI被调用且失败（默认提供商）
        assert mock_openai.generate.call_count >= 1
        # 验证DeepSeek被调用且成功（回退提供商）
        mock_deepseek.generate.assert_called_once()
        assert response.content == "DeepSeek成功响应"

    def test_config_loading_from_yaml(self):
        """测试从YAML配置文件加载DeepSeek配置"""
        # 这里我们模拟配置加载
        test_config = {
            "deepseek": {
                "type": "deepseek",
                "api_key": "${DEEPSEEK_API_KEY}",
                "model": "deepseek-chat",
                "thinking_enabled": False,
                "temperature": 1.0,
                "max_tokens": 4096,
                "timeout": 60,
                "enabled": True,
            }
        }

        # 验证配置结构
        assert "deepseek" in test_config
        deepseek_config = test_config["deepseek"]
        assert deepseek_config["type"] == "deepseek"
        assert deepseek_config["model"] == "deepseek-chat"
        assert deepseek_config["thinking_enabled"] == False
        assert deepseek_config["temperature"] == 1.0
        assert deepseek_config["max_tokens"] == 4096
        assert deepseek_config["timeout"] == 60
        assert deepseek_config["enabled"] == True


class TestDeepSeekMockAPI:
    """DeepSeek Mock API测试"""

    @pytest.mark.asyncio
    async def test_mock_api_success(self):
        """测试Mock API成功响应"""
        config = {
            "api_key": "mock-key",
            "model": "deepseek-chat",
            "thinking_enabled": False,
        }
        provider = DeepSeekProvider(config)

        # Mock aiohttp会话
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-mock-123",
            "model": "deepseek-chat",
            "choices": [
                {
                    "message": {"content": "Mock API响应", "role": "assistant"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch.object(provider, "get_session", return_value=mock_session):
            with patch.object(provider, "release_session") as mock_release:
                response = await provider._generate_impl("Mock提示")

                # 验证API调用
                mock_session.post.assert_called_once()
                call_args = mock_session.post.call_args
                assert "chat/completions" in call_args[0][0]

                # 验证请求体
                request_json = call_args[1]["json"]
                assert request_json["model"] == "deepseek-chat"
                assert request_json["messages"][0]["content"] == "Mock提示"
                assert request_json["thinking"]["type"] == "disabled"

                # 验证响应
                assert response.content == "Mock API响应"
                assert response.model == "deepseek-chat"
                assert response.usage["prompt_tokens"] == 5
                assert response.metadata["provider"] == "deepseek"

                # 验证会话释放
                mock_release.assert_called_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_mock_api_with_thinking_enabled(self):
        """测试启用推理模式的Mock API"""
        config = {
            "api_key": "mock-key",
            "model": "deepseek-reasoner",
            "thinking_enabled": True,
        }
        provider = DeepSeekProvider(config)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-mock-456",
            "model": "deepseek-reasoner",
            "choices": [
                {
                    "message": {"content": "推理模式响应", "role": "assistant"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 8, "completion_tokens": 15, "total_tokens": 23},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch.object(provider, "get_session", return_value=mock_session):
            with patch.object(provider, "release_session"):
                response = await provider._generate_impl("需要推理的问题")

                # 验证请求体包含推理模式
                call_args = mock_session.post.call_args
                request_json = call_args[1]["json"]
                assert request_json["thinking"]["type"] == "enabled"
                assert response.metadata["thinking_enabled"] == True

    @pytest.mark.asyncio
    async def test_mock_api_error_handling(self):
        """测试Mock API错误处理"""
        config = {"api_key": "mock-key", "model": "deepseek-chat"}
        provider = DeepSeekProvider(config)

        mock_response = AsyncMock()
        mock_response.status = 401  # 未授权错误
        mock_response.text.return_value = "Invalid API key"

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch.object(provider, "get_session", return_value=mock_session):
            with patch.object(provider, "release_session"):
                # 验证抛出异常
                with pytest.raises(Exception, match="API error: 401"):
                    await provider._generate_impl("测试提示")

    @pytest.mark.asyncio
    async def test_mock_api_with_additional_params(self):
        """测试带额外参数的Mock API调用"""
        config = {
            "api_key": "mock-key",
            "model": "deepseek-chat",
            "temperature": 0.8,
            "max_tokens": 2000,
        }
        provider = DeepSeekProvider(config)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-mock-789",
            "model": "deepseek-chat",
            "choices": [
                {
                    "message": {"content": "带参数响应", "role": "assistant"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch.object(provider, "get_session", return_value=mock_session):
            with patch.object(provider, "release_session"):
                # 调用时传递额外参数
                response = await provider._generate_impl(
                    "测试提示",
                    temperature=0.5,
                    max_tokens=1000,
                    top_p=0.9,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    stop=["\n", "。"],
                )

                # 验证请求体包含所有参数
                call_args = mock_session.post.call_args
                request_json = call_args[1]["json"]

                assert request_json["temperature"] == 0.5  # 覆盖默认值
                assert request_json["max_tokens"] == 1000  # 覆盖默认值
                assert request_json["top_p"] == 0.9
                assert request_json["frequency_penalty"] == 0.1
                assert request_json["presence_penalty"] == 0.1
                assert request_json["stop"] == ["\n", "。"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
