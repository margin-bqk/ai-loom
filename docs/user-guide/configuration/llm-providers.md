# LLM 提供商配置

## 概述

LOOM 支持多种 LLM（大语言模型）提供商，包括 OpenAI、Anthropic、DeepSeek、Google Gemini 和本地模型（Ollama）。本文档详细介绍每个提供商的配置方法、功能特性和使用建议。

## 配置结构

LOOM 使用两种配置文件来管理 LLM 提供商配置：

### 1. 主配置文件 (`default_config.yaml`)
包含运行时配置，使用扁平结构：

```yaml
llm_providers:
  openai:
    type: openai
    api_key: ${OPENAI_API_KEY:}
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 1000
    timeout: 30
    # ... 其他配置选项
```

### 2. 详细配置文件 (`llm_providers.yaml`)
包含详细的提供商信息，使用嵌套结构：

```yaml
providers:
  openai:
    display_name: "OpenAI GPT"
    models:
      - name: "gpt-4"
        description: "GPT-4 最新版本"
        max_tokens: 8192
        cost_per_1k_input: 0.03
        cost_per_1k_output: 0.06
    capabilities:
      - "function_calling"
      - "json_mode"
      - "streaming"
    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 90000

# 提供商选择策略
selection_strategy:
  default: "openai"
  fallback_order:
    - "openai"
    - "anthropic"
    - "deepseek"
    - "gemini"
    - "ollama"
```

## 支持的提供商

### 1. OpenAI GPT 系列

**显示名称**: OpenAI GPT  
**提供商类型**: `openai`

#### 可用模型
- **gpt-4**: GPT-4 最新版本，最大令牌数 8192
- **gpt-4-turbo**: GPT-4 Turbo，最大令牌数 4096
- **gpt-3.5-turbo**: GPT-3.5 Turbo（默认），最大令牌数 4096

#### 功能特性
- 函数调用（Function Calling）
- JSON 模式输出
- 流式响应
- 多轮对话

#### 主配置文件示例
```yaml
llm_providers:
  openai:
    type: openai
    enabled: true
    api_key: ${OPENAI_API_KEY:}
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 1000
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
    fallback_enabled: true
    connection_pool_size: 5
    enable_caching: true
    cache_ttl: 300
```

#### 详细配置文件示例
```yaml
providers:
  openai:
    display_name: "OpenAI GPT"
    models:
      - name: "gpt-4"
        description: "GPT-4 最新版本"
        max_tokens: 8192
        cost_per_1k_input: 0.03
        cost_per_1k_output: 0.06
        
      - name: "gpt-4-turbo"
        description: "GPT-4 Turbo"
        max_tokens: 4096
        cost_per_1k_input: 0.01
        cost_per_1k_output: 0.03
        
      - name: "gpt-3.5-turbo"
        description: "GPT-3.5 Turbo (默认)"
        max_tokens: 4096
        cost_per_1k_input: 0.0015
        cost_per_1k_output: 0.002

    capabilities:
      - "function_calling"
      - "json_mode"
      - "streaming"

    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 90000
```

#### 环境变量
```bash
export OPENAI_API_KEY="sk-your-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export OPENAI_MODEL="gpt-4-turbo-preview"  # 可选
```

### 2. Anthropic Claude 系列

**显示名称**: Anthropic Claude  
**提供商类型**: `anthropic`

#### 可用模型
- **claude-3-opus-20240229**: Claude 3 Opus（最强），最大令牌数 4096
- **claude-3-sonnet-20240229**: Claude 3 Sonnet（平衡），最大令牌数 4096
- **claude-3-haiku-20240307**: Claude 3 Haiku（快速），最大令牌数 4096

#### 功能特性
- 工具使用（Tool Use）
- 视觉能力（Vision）
- 长上下文支持
- 结构化输出

#### 主配置文件示例
```yaml
llm_providers:
  anthropic:
    type: anthropic
    enabled: true
    api_key: ${ANTHROPIC_API_KEY:}
    model: claude-3-haiku-20240307
    temperature: 1.0
    max_tokens: 4096
    timeout: 30
```

#### 详细配置文件示例
```yaml
providers:
  anthropic:
    display_name: "Anthropic Claude"
    models:
      - name: "claude-3-opus-20240229"
        description: "Claude 3 Opus (最强)"
        max_tokens: 4096
        cost_per_1k_input: 0.015
        cost_per_1k_output: 0.075
        
      - name: "claude-3-sonnet-20240229"
        description: "Claude 3 Sonnet (平衡)"
        max_tokens: 4096
        cost_per_1k_input: 0.003
        cost_per_1k_output: 0.015
        
      - name: "claude-3-haiku-20240307"
        description: "Claude 3 Haiku (快速)"
        max_tokens: 4096
        cost_per_1k_input: 0.00025
        cost_per_1k_output: 0.00125

    capabilities:
      - "tool_use"
      - "vision"

    rate_limits:
      requests_per_minute: 100
      tokens_per_minute: 100000
```

#### 环境变量
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-3-opus-20240229"
```

### 3. DeepSeek 系列

**显示名称**: DeepSeek  
**提供商类型**: `deepseek`

#### 可用模型
- **deepseek-chat**: DeepSeek Chat（非推理模式），最大令牌数 4096，上下文长度 128K
- **deepseek-reasoner**: DeepSeek Reasoner（推理模式），最大令牌数 32000，上下文长度 128K

#### 功能特性
- **推理模式**：支持链式思考和推理过程
- **JSON 输出**：支持结构化 JSON 响应
- **工具调用**：支持函数调用和工具使用
- **128K 上下文**：超长上下文支持
- **中文优化**：对中文内容有更好的理解和生成能力

#### 主配置文件示例
```yaml
llm_providers:
  deepseek:
    type: deepseek
    enabled: true
    api_key: ${DEEPSEEK_API_KEY:}
    base_url: https://api.deepseek.com
    model: deepseek-chat
    thinking_enabled: false  # 是否启用推理模式
    temperature: 1.0
    max_tokens: 4096
    timeout: 60  # DeepSeek可能需要更长的超时时间
```

#### 详细配置文件示例
```yaml
providers:
  deepseek:
    display_name: "DeepSeek"
    models:
      - name: "deepseek-chat"
        description: "DeepSeek Chat (非推理模式)"
        max_tokens: 4096
        context_length: 128000
        cost_per_1k_input: 0.00028
        cost_per_1k_output: 0.00042
        
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

#### 环境变量
```bash
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"  # 可选
export DEEPSEEK_MODEL="deepseek-chat"  # 可选
```

#### 使用场景
- **中文内容生成**：DeepSeek 对中文有优秀的理解和生成能力
- **推理任务**：使用 `deepseek-reasoner` 模型进行复杂推理
- **长文档处理**：128K 上下文适合处理长文档和复杂对话
- **成本敏感场景**：相比 OpenAI 和 Anthropic，DeepSeek 具有更好的性价比

#### 推理模式配置
要启用推理模式，需要设置 `thinking_enabled: true` 并使用 `deepseek-reasoner` 模型：
```yaml
deepseek:
  type: deepseek
  model: deepseek-reasoner
  thinking_enabled: true
  max_tokens: 32000  # 推理模式支持更多令牌
```

### 4. Google Gemini 系列

**显示名称**: Google Gemini  
**提供商类型**: `gemini`

#### 可用模型
- **gemini-pro**: Gemini Pro，最大令牌数 32768

#### 功能特性
- 多模态能力
- 函数调用
- 长上下文支持

#### 主配置文件示例
```yaml
llm_providers:
  gemini:
    type: gemini
    enabled: false  # 默认禁用
    api_key: ${GOOGLE_API_KEY:}
    model: gemini-pro
    timeout: 30
```

#### 详细配置文件示例
```yaml
providers:
  gemini:
    display_name: "Google Gemini"
    models:
      - name: "gemini-pro"
        description: "Gemini Pro"
        max_tokens: 32768
        cost_per_1k_input: 0.0005
        cost_per_1k_output: 0.0015

    capabilities:
      - "multimodal"
      - "function_calling"

    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 60000
```

#### 环境变量
```bash
export GOOGLE_API_KEY="your-google-key"
export GOOGLE_MODEL="gemini-pro"
```

### 5. 本地模型 (Ollama)

**显示名称**: 本地模型 (Ollama)  
**提供商类型**: `ollama`

#### 可用模型
- **llama2**: Llama 2 7B，最大令牌数 4096
- **mistral**: Mistral 7B，最大令牌数 8192
- **codellama**: CodeLlama 7B，最大令牌数 4096

#### 功能特性
- 本地推理，无需互联网
- 零成本（无 API 费用）
- 完全隐私保护

#### 主配置文件示例
```yaml
llm_providers:
  ollama:
    type: ollama
    enabled: false  # 默认禁用
    base_url: http://localhost:11434
    model: llama2
    timeout: 120  # 本地模型可能需要更长时间
```

#### 详细配置文件示例
```yaml
providers:
  ollama:
    display_name: "本地模型 (Ollama)"
    models:
      - name: "llama2"
        description: "Llama 2 7B"
        max_tokens: 4096
        cost_per_1k_input: 0.0
        cost_per_1k_output: 0.0
        
      - name: "mistral"
        description: "Mistral 7B"
        max_tokens: 8192
        cost_per_1k_input: 0.0
        cost_per_1k_output: 0.0
        
      - name: "codellama"
        description: "CodeLlama 7B"
        max_tokens: 4096
        cost_per_1k_input: 0.0
        cost_per_1k_output: 0.0

    capabilities:
      - "local_inference"
      - "no_internet_required"

    requirements:
      - "ollama installed"
      - "8GB+ RAM"
      - "模型已下载"
```

#### 系统要求
- Ollama 已安装并运行
- 8GB+ 内存
- 模型已下载到本地

## 提供商选择策略

LOOM 支持智能的提供商选择策略，可以根据会话类型、成本、性能等因素自动选择最合适的提供商。

### 默认回退顺序
```yaml
selection_strategy:
  default: "openai"
  fallback_order:
    - "openai"
    - "anthropic"
    - "deepseek"
    - "gemini"
    - "ollama"
```

### 基于会话类型的推荐
```yaml
selection_strategy:
  session_type_mapping:
    creative_writing:
      preferred_provider: "openai"
      preferred_model: "gpt-4"
      
    world_building:
      preferred_provider: "anthropic"
      preferred_model: "claude-3-sonnet"
      
    code_generation:
      preferred_provider: "ollama"
      preferred_model: "codellama"
      
    quick_chat:
      preferred_provider: "openai"
      preferred_model: "gpt-3.5-turbo"
      
    chinese_content:
      preferred_provider: "deepseek"
      preferred_model: "deepseek-chat"
      fallback_to: "openai"
      
    reasoning_tasks:
      preferred_provider: "deepseek"
      preferred_model: "deepseek-reasoner"
      fallback_to: "anthropic"
```

### 成本优化策略
```yaml
cost_control:
  monthly_budget: 50.0  # 美元
  alert_threshold: 0.8  # 预算使用80%时告警
  auto_switch_to_cheaper: true
  token_counting: true
  
  optimization_strategies:
    - name: "use_cheaper_model_for_long_context"
      enabled: true
      threshold_tokens: 2000
      
    - name: "cache_frequent_queries"
      enabled: true
      ttl_minutes: 60
```

## 配置最佳实践

### 1. 安全配置
- 使用环境变量存储 API 密钥，避免硬编码
- 为不同环境（开发、测试、生产）使用不同的配置
- 定期轮换 API 密钥

### 2. 性能优化
- 启用缓存以减少 API 调用：`enable_caching: true`
- 设置合理的超时时间：`timeout: 30`
- 配置连接池：`connection_pool_size: 5`

### 3. 成本控制
- 设置月度预算限制
- 启用自动切换到更便宜的模型
- 监控令牌使用情况

### 4. 故障转移
- 配置多个提供商以实现高可用性
- 设置合理的重试机制：`max_retries: 3`
- 启用故障转移：`fallback_enabled: true`

## 故障排除

### 常见问题

#### 1. API 密钥无效
```bash
# 验证环境变量
echo $DEEPSEEK_API_KEY

# 测试连接
loom config test --provider deepseek
```

#### 2. 连接超时
```yaml
# 增加超时时间
deepseek:
  timeout: 60  # 增加到60秒
  max_retries: 3
  retry_delay: 2.0
```

#### 3. 模型不可用
```bash
# 检查模型名称
loom config get llm.deepseek.model

# 查看可用模型
cat config/llm_providers.yaml | grep -A5 "deepseek:"
```

#### 4. 成本计算异常
```bash
# 检查定价配置
loom config show --section llm.deepseek

# 验证成本计算
loom config test --provider deepseek --verbose
```

## 高级配置

### 自定义提供商
您可以通过实现 `LLMProvider` 接口来添加自定义提供商。参考 `src/loom/interpretation/llm_provider.py` 中的示例。

### 提供商权重
```yaml
provider_weights:
  openai: 0.4
  anthropic: 0.3
  deepseek: 0.2
  gemini: 0.1
```

### 区域选择
对于支持多个区域的提供商（如 Azure OpenAI），可以配置区域端点：
```yaml
azure_openai:
  type: azure_openai
  api_key: ${AZURE_OPENAI_KEY:}
  endpoint: https://your-resource.openai.azure.com/
  deployment_name: gpt-35-turbo
```

## 下一步

配置完成后，您可以：

1. **验证配置**：运行 `loom config validate --check-connections`
2. **测试提供商**：运行 `loom config test --all`
3. **开始使用**：查看 [快速开始指南](../quick-start/basic-configuration.md)
4. **了解 API 使用**：查看 [API 使用示例](../api-usage/quick-api-start.md)
