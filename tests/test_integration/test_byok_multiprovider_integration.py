"""
BYOK和多Provider集成测试

测试增强版LLMProvider与现有组件的集成。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os
import tempfile
import yaml

from src.loom.core.config_manager import ConfigManager
from src.loom.core.session_manager import SessionManager, SessionConfig
from src.loom.interpretation.reasoning_pipeline import ReasoningPipeline, ReasoningContext
from src.loom.interpretation.llm_provider import (
    LLMProviderFactory,
    ProviderManager,
    OpenAIProvider,
    AnthropicProvider,
    LocalProvider
)
from src.loom.interpretation.key_manager import KeyManager


class TestBYOKMultiProviderIntegration:
    """BYOK和多Provider集成测试"""
    
    def setup_method(self):
        """测试设置"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")
        
        # 创建测试配置
        test_config = {
            "llm_providers": {
                "openai_test": {
                    "type": "openai",
                    "api_key": "test-openai-key",
                    "model": "gpt-3.5-turbo",
                    "enabled": True
                },
                "anthropic_test": {
                    "type": "anthropic",
                    "api_key": "test-anthropic-key",
                    "model": "claude-3-haiku",
                    "enabled": True
                },
                "ollama_test": {
                    "type": "ollama",
                    "base_url": "http://localhost:11434/api",
                    "model": "llama2",
                    "enabled": True
                }
            },
            "provider_selection": {
                "default_provider": "openai_test",
                "fallback_order": ["openai_test", "anthropic_test", "ollama_test"],
                "session_type_mapping": {
                    "creative_writing": {
                        "preferred_provider": "openai_test",
                        "preferred_model": "gpt-3.5-turbo"
                    },
                    "world_building": {
                        "preferred_provider": "anthropic_test",
                        "preferred_model": "claude-3-haiku"
                    }
                }
            },
            "session_defaults": {
                "default_llm_provider": "openai_test"
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f)
        
        # 设置环境变量
        os.environ["OPENAI_API_KEY"] = "test-openai-env-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-env-key"
    
    def teardown_method(self):
        """测试清理"""
        # 清理环境变量
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_manager_with_multiprovider(self):
        """测试ConfigManager支持多Provider配置"""
        config_manager = ConfigManager(config_path=self.config_path)
        config = config_manager.get_config()
        
        # 验证Provider配置
        assert len(config.llm_providers) >= 3
        assert "openai_test" in config.llm_providers
        assert "anthropic_test" in config.llm_providers
        assert "ollama_test" in config.llm_providers
        
        # 验证Provider选择策略
        assert config.provider_selection.default_provider == "openai_test"
        assert len(config.provider_selection.fallback_order) == 3
        assert "creative_writing" in config.provider_selection.session_type_mapping
        
        # 验证环境变量覆盖
        openai_config = config.llm_providers["openai_test"]
        assert openai_config.api_key == "test-openai-key"  # 配置文件优先级高于环境变量
    
    def test_provider_factory_creation(self):
        """测试Provider工厂创建多Provider"""
        configs = {
            "openai_1": {
                "type": "openai",
                "api_key": "test-key-1",
                "model": "gpt-3.5-turbo"
            },
            "anthropic_1": {
                "type": "anthropic",
                "api_key": "test-key-2",
                "model": "claude-3-haiku"
            }
        }
        
        providers = LLMProviderFactory.create_from_configs(configs)
        
        assert len(providers) == 2
        assert "openai_1" in providers
        assert "anthropic_1" in providers
        assert isinstance(providers["openai_1"], OpenAIProvider)
        assert isinstance(providers["anthropic_1"], AnthropicProvider)
    
    def test_provider_manager_with_fallback(self):
        """测试Provider管理器回退机制"""
        # 创建模拟Provider
        mock_provider1 = AsyncMock()
        mock_provider1.name = "provider1"
        mock_provider1.provider_type = "openai"
        mock_provider1.enabled = True
        mock_provider1.generate.side_effect = Exception("Provider 1 failed")
        
        mock_provider2 = AsyncMock()
        mock_provider2.name = "provider2"
        mock_provider2.provider_type = "anthropic"
        mock_provider2.enabled = True
        mock_provider2.generate.return_value = MagicMock(
            content="Success from provider 2",
            model="test-model",
            usage={},
            metadata={}
        )
        
        # 创建Provider管理器
        manager = ProviderManager()
        manager.register_provider("provider1", mock_provider1)
        manager.register_provider("provider2", mock_provider2)
        manager.set_default("provider1")
        manager.set_fallback_order(["provider1", "provider2"])
        
        # 测试回退
        import asyncio
        result = asyncio.run(manager.generate_with_fallback("Test prompt"))
        
        assert result.content == "Success from provider 2"
        mock_provider1.generate.assert_called_once()
        mock_provider2.generate.assert_called_once()
    
    def test_session_manager_provider_selection(self):
        """测试SessionManager根据会话类型选择Provider"""
        # 创建ConfigManager
        config_manager = ConfigManager(config_path=self.config_path)
        
        # 创建SessionManager
        session_manager = SessionManager(config_manager=config_manager)
        
        # 测试创意写作会话
        creative_config = SessionConfig(
            name="Creative Writing Session",
            canon_path="./test_canon",
            memory_backend="sqlite",
            llm_provider="",  # 留空以测试自动选择
            metadata={"session_type": "creative_writing"}
        )
        
        # 创建会话
        import asyncio
        session = asyncio.run(session_manager.create_session(creative_config))
        
        # 验证选择的Provider
        assert session.config.llm_provider == "openai_test"
        assert session.config.metadata.get("preferred_model") == "gpt-3.5-turbo"
        
        # 测试世界构建会话
        world_config = SessionConfig(
            name="World Building Session",
            canon_path="./test_canon",
            memory_backend="sqlite",
            llm_provider="",  # 留空以测试自动选择
            metadata={"session_type": "world_building"}
        )
        
        session = asyncio.run(session_manager.create_session(world_config))
        assert session.config.llm_provider == "anthropic_test"
    
    @pytest.mark.asyncio
    async def test_reasoning_pipeline_with_provider_manager(self):
        """测试ReasoningPipeline与ProviderManager集成"""
        # 创建模拟Provider
        mock_provider = AsyncMock()
        mock_provider.name = "test_provider"
        mock_provider.provider_type = "openai"
        mock_provider.enabled = True
        mock_provider.generate.return_value = MagicMock(
            content="Test narrative response",
            model="gpt-3.5-turbo",
            usage={"input_tokens": 10, "output_tokens": 20},
            metadata={}
        )
        
        # 创建Provider管理器
        provider_manager = ProviderManager()
        provider_manager.register_provider("test_provider", mock_provider)
        provider_manager.set_default("test_provider")
        
        # 创建ReasoningPipeline
        pipeline = ReasoningPipeline(provider_manager=provider_manager)
        
        # 创建测试上下文
        context = ReasoningContext(
            session_id="test_session",
            turn_number=1,
            player_input="What happens next?",
            rules_text="Test rules",
            memories=[],
            interventions=[],
            metadata={"llm_provider": "test_provider"}
        )
        
        # 处理推理
        result = await pipeline.process(context)
        
        # 验证结果
        assert result.narrative_response == "Test narrative response"
        assert result.confidence > 0
        assert len(result.reasoning_steps) == 5  # 5个推理步骤
        
        # 验证Provider被调用
        mock_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_key_manager_integration(self):
        """测试KeyManager与ConfigManager集成"""
        # 创建KeyManager
        key_manager = KeyManager(config_dir=os.path.join(self.temp_dir, "keys"))
        
        # 添加测试密钥
        key_id = key_manager.add_key("openai", "test-api-key-12345")
        assert key_id is not None
        
        # 验证密钥检索
        key_value = key_manager.get_key("openai")
        assert key_value == "test-api-key-12345"
        
        # 测试密钥掩码
        key_info = key_manager._keys["openai"]
        masked = key_info.mask_key()
        assert masked == "test...2345"
    
    def test_config_snapshot_hides_sensitive_info(self):
        """测试配置快照隐藏敏感信息"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # 获取配置快照
        snapshot = config_manager.get_config_snapshot()
        
        # 验证敏感信息被隐藏
        if "llm_providers" in snapshot:
            for provider in snapshot["llm_providers"].values():
                if "api_key" in provider:
                    assert provider["api_key"] == "***REDACTED***"
    
    @pytest.mark.asyncio
    async def test_provider_health_check(self):
        """测试Provider健康检查"""
        # 创建模拟Provider
        mock_provider = AsyncMock()
        mock_provider.name = "test_provider"
        mock_provider.provider_type = "openai"
        mock_provider.enabled = True
        mock_provider.health_check.return_value = {
            "healthy": True,
            "response_time": 0.5,
            "model": "gpt-3.5-turbo",
            "provider": "test_provider",
            "type": "openai"
        }
        
        # 创建Provider管理器
        provider_manager = ProviderManager()
        provider_manager.register_provider("test_provider", mock_provider)
        
        # 执行健康检查
        health_results = await provider_manager.health_check_all()
        
        # 验证结果
        assert "test_provider" in health_results
        assert health_results["test_provider"]["healthy"] is True
        mock_provider.health_check.assert_called_once()
    
    def test_provider_statistics(self):
        """测试Provider统计信息"""
        # 创建Provider管理器
        provider_manager = ProviderManager()
        
        # 创建模拟Provider
        mock_provider1 = MagicMock()
        mock_provider1.name = "provider1"
        mock_provider1.provider_type = "openai"
        mock_provider1.request_count = 10
        mock_provider1.total_tokens = 5000
        mock_provider1.total_cost = 0.05
        mock_provider1.get_stats.return_value = {
            "name": "provider1",
            "type": "openai",
            "model": "gpt-3.5-turbo",
            "request_count": 10,
            "total_tokens": 5000,
            "total_cost": 0.05
        }
        
        mock_provider2 = MagicMock()
        mock_provider2.name = "provider2"
        mock_provider2.provider_type = "anthropic"
        mock_provider2.request_count = 5
        mock_provider2.total_tokens = 3000
        mock_provider2.total_cost = 0.03
        mock_provider2.get_stats.return_value = {
            "name": "provider2",
            "type": "anthropic",
            "model": "claude-3-haiku",
            "request_count": 5,
            "total_tokens": 3000,
            "total_cost": 0.03
        }
        
        provider_manager.register_provider("provider1", mock_provider1)
        provider_manager.register_provider("provider2", mock_provider2)
        
        # 获取统计信息
        stats = provider_manager.get_stats_all()
        
        # 验证统计信息
        assert "providers" in stats
        assert "totals" in stats
        assert stats["totals"]["requests"] == 15
        assert stats["totals"]["tokens"] == 8000
        assert stats["totals"]["cost"] == 0.08
        assert stats["totals"]["provider_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])