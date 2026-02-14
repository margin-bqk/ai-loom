# DeepSeek API 集成实施计划

## 概述
本计划详细说明了如何在AI-Loom项目中集成DeepSeek API作为新的LLM提供商。DeepSeek提供高性能、低成本的中文优化模型，支持128K上下文长度和推理模式。

## 1. 任务分解

### 1.1 核心实现任务
- [ ] 创建 `DeepSeekProvider` 类实现
- [ ] 更新 `LLMProviderFactory` 工厂类
- [ ] 添加配置文件支持
- [ ] 更新文档和示例
- [ ] 实现测试套件

### 1.2 配置集成任务
- [ ] 更新 `config/llm_providers.yaml`
- [ ] 更新 `config/default_config.yaml.backup`
- [ ] 添加环境变量支持
- [ ] 更新CLI配置命令

### 1.3 测试验证任务
- [ ] 单元测试：DeepSeekProvider基本功能
- [ ] 集成测试：提供商管理器集成
- [ ] 端到端测试：完整会话流程
- [ ] 性能测试：响应时间和成本

## 2. 技术设计

### 2.1 DeepSeekProvider 类设计

```python
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
                "Content-Type": "application/json"
            }

            # 构建请求体
            payload = {
                "model": kwargs.get("model", self.model),
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False
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

            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"DeepSeek API error: {response.status} - {error_text}")
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
                        "thinking_enabled": self.thinking_enabled
                    }
                )
        finally:
            await self.release_session(session)

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
```

### 2.2 提供商工厂更新

```python
# 在 LLMProviderFactory.create_provider 中添加
elif provider_type == "deepseek":
    return DeepSeekProvider(config)
```

### 2.3 流式生成支持（可选）
```python
async def generate_stream(self, prompt: str, **kwargs):
    """流式生成文本"""
    # 实现SSE流式响应处理
    pass
```

## 3. 配置设计

### 3.1 `config/llm_providers.yaml` 更新

```yaml
# DeepSeek 系列
deepseek:
  display_name: "DeepSeek"
  models:
    - name: "deepseek-chat"
      description: "DeepSeek Chat (非推理模式)"
      max_tokens: 4096
      context_length: 128000
      cost_per_1k_input: 0.00028  # $0.28/1M tokens
      cost_per_1k_output: 0.00042 # $0.42/1M tokens

    - name: "deepseek-reasoner"
      description: "DeepSeek Reasoner (推理模式)"
      max_tokens: 32000
      context_length: 128000
      cost_per_1k_input: 0.00028
      cost_per_1k_output: 0.00042
      features: ["reasoning_mode"]

  capabilities:
    - "reasoning_mode"
    - "json_output"
    - "tool_calls"
    - "128k_context"

  rate_limits:
    requests_per_minute: "unlimited"  # DeepSeek不限制速率
    tokens_per_minute: "unlimited"

  requirements:
    - "API key from platform.deepseek.com"
    - "Internet connection"
```

### 3.2 `config/default_config.yaml.backup` 更新

```yaml
deepseek:
  type: deepseek
  api_key: ''
  base_url: https://api.deepseek.com
  model: deepseek-chat
  thinking_enabled: false
  temperature: 1.0
  max_tokens: 4096
  timeout: 60  # DeepSeek可能需要更长的超时时间
  max_retries: 3
  retry_delay: 2.0
  fallback_enabled: true
  enabled: true
  connection_pool_size: 5
  enable_batching: false
  enable_caching: true
  cache_ttl: 300
```

### 3.3 提供商选择策略更新

```yaml
# 在 provider_selection 部分添加
fallback_order:
  - "openai"
  - "anthropic"
  - "deepseek"  # 新增
  - "google"
  - "ollama"
  - "azure"

# 在 session_type_mapping 中添加DeepSeek推荐
session_type_mapping:
  chinese_content:
    preferred_provider: "deepseek"
    preferred_model: "deepseek-chat"
    fallback_to: "openai"

  reasoning_tasks:
    preferred_provider: "deepseek"
    preferred_model: "deepseek-reasoner"
    fallback_to: "anthropic"
```

## 4. 集成点

### 4.1 需要修改的文件

1. **`src/loom/interpretation/llm_provider.py`**
   - 添加 `DeepSeekProvider` 类定义
   - 更新 `LLMProviderFactory.create_provider()` 方法
   - 添加必要的导入

2. **`config/llm_providers.yaml`**
   - 添加DeepSeek提供商配置
   - 更新提供商选择策略

3. **`config/default_config.yaml.backup`**
   - 添加DeepSeek默认配置

4. **`src/loom/core/config_manager.py`**
   - 更新提供商名称列表（如果需要）

5. **`src/loom/cli/commands/config.py`**
   - 更新提供商测试逻辑

6. **文档文件**
   - `docs/user-guide/configuration/llm-providers.md`
   - `docs/quick-start/basic-configuration.md`

### 4.2 新增文件

1. **`tests/test_interpretation/test_deepseek_provider.py`**
   - DeepSeekProvider单元测试

2. **`examples/deepseek_example.py`**
   - 使用示例

## 5. 测试策略

### 5.1 单元测试

```python
# test_deepseek_provider.py
import pytest
from unittest.mock import AsyncMock, patch
from src.loom.interpretation.llm_provider import DeepSeekProvider

class TestDeepSeekProvider:
    def test_initialization(self):
        """测试DeepSeekProvider初始化"""
        config = {
            "name": "test-deepseek",
            "type": "deepseek",
            "api_key": "test-key",
            "model": "deepseek-chat"
        }
        provider = DeepSeekProvider(config)
        assert provider.provider_type == "deepseek"
        assert provider.model == "deepseek-chat"
        assert provider.thinking_enabled == False

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """测试成功生成响应"""
        config = {"api_key": "test", "model": "deepseek-chat"}
        provider = DeepSeekProvider(config)

        with patch.object(provider, '_generate_impl') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content="测试响应",
                model="deepseek-chat",
                usage={"prompt_tokens": 10, "completion_tokens": 20}
            )

            response = await provider.generate("测试提示")
            assert response.content == "测试响应"
            assert response.model == "deepseek-chat"

    def test_cost_calculation(self):
        """测试成本计算"""
        config = {"api_key": "test", "model": "deepseek-chat"}
        provider = DeepSeekProvider(config)

        response = LLMResponse(
            content="测试",
            model="deepseek-chat",
            usage={"prompt_tokens": 1000, "completion_tokens": 500}
        )

        # 1000输入token + 500输出token
        # 成本 = (1000/1M * 0.28) + (500/1M * 0.42) = 0.00028 + 0.00021 = 0.00049
        cost = provider._calculate_cost(response)
        assert abs(cost - 0.00049) < 0.00001
```

### 5.2 集成测试

```python
# test_deepseek_integration.py
class TestDeepSeekIntegration:
    def test_provider_factory(self):
        """测试工厂创建DeepSeekProvider"""
        config = {
            "type": "deepseek",
            "api_key": "test",
            "model": "deepseek-chat"
        }
        provider = LLMProviderFactory.create_provider(config)
        assert isinstance(provider, DeepSeekProvider)

    def test_provider_manager_integration(self):
        """测试提供商管理器集成"""
        configs = {
            "my-deepseek": {
                "type": "deepseek",
                "api_key": "test",
                "model": "deepseek-chat"
            }
        }
        manager = LLMProviderFactory.create_provider_manager(configs)
        assert "my-deepseek" in manager.providers
```

### 5.3 端到端测试

```python
# test_deepseek_e2e.py
@pytest.mark.integration
class TestDeepSeekEndToEnd:
    @pytest.mark.asyncio
    async def test_complete_session_with_deepseek(self):
        """使用DeepSeek完成完整会话"""
        # 配置DeepSeek为默认提供商
        config = load_config_with_deepseek()

        # 创建会话管理器
        session_manager = SessionManager(config)

        # 创建会话并运行
        session = await session_manager.create_session(
            session_type="chinese_content",
            initial_prompt="用中文写一个科幻故事开头"
        )

        # 验证响应
        assert session.responses
        assert "deepseek" in session.metadata.get("llm_provider", "")
```

## 6. 部署计划

### 6.1 开发阶段
1. **第1周**：实现核心DeepSeekProvider类
   - 完成基础API调用
   - 实现错误处理和重试逻辑
   - 添加成本计算

2. **第2周**：配置和集成
   - 更新配置文件
   - 集成到提供商工厂
   - 更新CLI命令

3. **第3周**：测试和文档
   - 编写单元测试
   - 创建集成测试
   - 更新用户文档

### 6.2 测试阶段
1. **功能测试**：验证所有API功能正常工作
2. **性能测试**：测试响应时间和并发性能
3. **兼容性测试**：确保与现有系统兼容
4. **安全测试**：验证API密钥管理和安全配置

### 6.3 部署阶段
1. **预发布环境**：在测试环境中部署
2. **金丝雀发布**：向小部分用户开放
3. **全面发布**：向所有用户开放
4. **监控和优化**：监控使用情况，优化配置

## 7. 风险缓解

### 7.1 技术风险
- **API变更风险**：DeepSeek API可能变更
  - 缓解：使用版本化的API端点，定期检查API文档
- **性能风险**：DeepSeek响应时间可能不稳定
  - 缓解：实现超时和重试机制，设置合理的超时时间

### 7.2 业务风险
- **成本风险**：定价模型可能变化
  - 缓解：实现成本监控和告警，定期检查定价页面
- **可用性风险**：服务可能不可用
  - 缓解：实现故障转移和回退机制

### 7.3 安全风险
- **API密钥泄露**：密钥管理不当
  - 缓解：使用环境变量和密钥管理器，实现密钥轮换

## 8. 成功指标

### 8.1 技术指标
- ✅ DeepSeekProvider通过所有单元测试
- ✅ 集成测试通过率100%
- ✅ 平均响应时间 < 5秒
- ✅ 错误率 < 1%

### 8.2 业务指标
- ✅ 用户可以使用DeepSeek作为LLM提供商
- ✅ 配置过程简单直观
- ✅ 成本计算准确
- ✅ 文档完整且易于理解

## 9. 附录

### 9.1 DeepSeek API参考
- **基础URL**: `https://api.deepseek.com`
- **认证**: Bearer Token
- **端点**: `/chat/completions`
- **模型**: `deepseek-chat`, `deepseek-reasoner`
- **上下文长度**: 128K tokens
- **定价**: $0.28/1M输入token, $0.42/1M输出token

### 9.2 环境变量
```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com  # 可选
DEEPSEEK_MODEL=deepseek-chat  # 可选
```

### 9.3 故障排除
1. **认证失败**：检查API密钥是否正确
2. **超时错误**：增加超时时间设置
3. **模型不可用**：检查模型名称是否正确
4. **成本计算异常**：验证定价模型配置

---

## 下一步行动

1. **评审本计划**：与团队评审技术设计和实施步骤
2. **开始实现**：按照任务分解开始编码
3. **定期检查**：每周检查进度，调整计划
4. **用户反馈**：收集早期用户反馈，优化实现

**计划创建者**: AI-Loom架构团队
**创建日期**: 2026-02-07
**版本**: 1.0
**状态**: 待评审
