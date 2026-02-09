# 配置文件

## 概述

LOOM 使用多层次的配置系统，支持通过配置文件、环境变量和命令行参数进行配置。本文档详细介绍 LOOM 的配置文件系统，包括配置文件的位置、格式、结构以及所有可用的配置选项。

## 配置文件位置

LOOM 按照以下顺序查找和加载配置文件：

1. **命令行参数**：通过 `--config` 参数指定的配置文件
2. **环境变量**：通过 `.env` 文件或系统环境变量设置
3. **用户配置文件**：`~/.loom/config.yaml`（用户主目录）
4. **项目配置文件**：`./config/default_config.yaml`（当前项目目录）
5. **默认配置**：内置的默认配置值

### 配置文件优先级

配置项的优先级从高到低为：
1. 命令行参数
2. 环境变量
3. 用户配置文件
4. 项目配置文件
5. 默认配置

## 配置文件类型

### 1. 主配置文件 (`default_config.yaml`)

主配置文件包含 LOOM 的核心配置，位于 `config/default_config.yaml`。如果文件不存在，LOOM 会使用内置的默认配置。

**示例配置：**

```yaml
# LOOM 主配置文件
# 版本: 1.0.0

# LLM 提供商配置
llm_providers:
  openai:
    type: openai
    api_key: ${OPENAI_API_KEY:}
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 1000
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
    fallback_enabled: true
    enabled: true
    connection_pool_size: 5
    enable_batching: false
    enable_caching: true
    cache_ttl: 300

  deepseek:
    type: deepseek
    api_key: ${DEEPSEEK_API_KEY:}
    base_url: https://api.deepseek.com
    model: deepseek-chat
    temperature: 1.0
    max_tokens: 4096
    timeout: 60
    thinking_enabled: false

# Provider 选择策略
provider_selection:
  default_provider: openai
  fallback_order:
    - openai
    - anthropic
    - deepseek
    - gemini
    - ollama
  
  # 基于会话类型的 Provider 选择
  session_type_mapping:
    creative_writing:
      preferred_provider: openai
      preferred_model: gpt-4
      
    world_building:
      preferred_provider: anthropic
      preferred_model: claude-3-sonnet
      
    code_generation:
      preferred_provider: ollama
      preferred_model: codellama
      
    quick_chat:
      preferred_provider: openai
      preferred_model: gpt-3.5-turbo
      
    chinese_content:
      preferred_provider: deepseek
      preferred_model: deepseek-chat
      fallback_to: openai
      
    reasoning_tasks:
      preferred_provider: deepseek
      preferred_model: deepseek-reasoner
      fallback_to: anthropic
  
  # 成本优化策略
  cost_optimization:
    enabled: true
    monthly_budget: 50.0
    alert_threshold: 0.8
    auto_switch_to_cheaper: true
    token_counting: true

# 记忆配置
memory:
  backend: sqlite
  db_path: ./data/loom_memory.db
  vector_store_enabled: false
  max_memories_per_session: 1000
  auto_summarize: true
  summarization_interval_days: 7

# 会话默认配置
session_defaults:
  default_canon_path: ./canon
  default_llm_provider: openai
  max_turns: null  # 无限制
  auto_save_interval: 5
  intervention_allowed: true
  retcon_allowed: true

# 叙事解释器配置
narrative:
  enabled: true
  consistency_check_enabled: true
  continuity_check_enabled: true
  auto_summarize: true
  summarization_interval_turns: 10
  narrative_arc_tracking: true
  max_narrative_arcs: 5
  default_narrative_tone: neutral
  default_narrative_pace: normal
  consistency_threshold: 0.7
  max_continuity_issues: 5
  auto_archive: true
  archive_interval_turns: 50
  max_archive_versions: 10
  export_format: markdown

# 性能配置
performance:
  max_prompt_length: 8000
  max_memories_per_prompt: 10
  enable_response_caching: true
  cache_size_mb: 100

# 安全配置
security:
  allow_file_system_access: true
  max_session_duration_hours: 24
  intervention_rate_limit: 10
  require_justification_for_retcon: true

# 监控配置
monitoring:
  enable_metrics: true
  metrics_port: 9090
  enable_tracing: false
  log_retention_days: 30

# 运行时配置
max_concurrent_turns: 3
log_level: INFO
data_dir: ./data
cache_enabled: true
cache_ttl_minutes: 60

# 插件配置
plugins: {}
```

### 2. LLM 提供商详细配置 (`llm_providers.yaml`)

LLM 提供商详细配置文件位于 `config/llm_providers.yaml`，提供更详细的提供商信息，包括模型规格、成本、速率限制等。

**文件位置：** `config/llm_providers.yaml`

**配置结构：**
```yaml
providers:
  # 提供商名称 (如 openai, deepseek, anthropic 等)
  openai:
    display_name: "OpenAI GPT"
    models:
      - name: "gpt-4"
        description: "GPT-4 最新版本"
        max_tokens: 8192
        cost_per_1k_input: 0.03
        cost_per_1k_output: 0.06
      # ... 更多模型
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
  cost_optimization: true
  latency_optimization: false
  
  # 基于会话类型的模型选择
  session_type_mapping:
    creative_writing:
      preferred_provider: "openai"
      preferred_model: "gpt-4"
    # ... 更多会话类型

# 成本控制
cost_control:
  monthly_budget: 50.0
  alert_threshold: 0.8
  auto_switch_to_cheaper: true
  token_counting: true
  
  optimization_strategies:
    - name: "use_cheaper_model_for_long_context"
      enabled: true
      threshold_tokens: 2000
    - name: "cache_frequent_queries"
      enabled: true
      ttl_minutes: 60

# 监控和日志
monitoring:
  log_all_requests: false
  log_errors_only: true
  metrics_collection_interval: 60
  
  track_metrics:
    - "response_time"
    - "token_usage"
    - "cost_per_session"
    - "error_rate"
```

### 3. 环境变量配置 (`.env`)

环境变量配置文件用于存储敏感信息（如 API 密钥）和运行时配置。

**文件位置：** `.env`（基于 `.env.example` 创建）

**创建方法：**
```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件，填入实际的 API 密钥
```

**主要环境变量：**

```bash
# ====================
# LLM 提供商配置
# ====================

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Ollama (本地运行)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Google Gemini
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_MODEL=gemini-pro

# ====================
# 数据库配置
# ====================

# SQLite 数据库路径
DATABASE_URL=sqlite+aiosqlite:///loom.db

# 向量存储配置
VECTOR_STORE_TYPE=chroma
CHROMA_PATH=./chroma_db

# ====================
# 会话配置
# ====================

# 默认会话存储路径
SESSION_STORAGE_PATH=./sessions

# 最大并发会话数
MAX_CONCURRENT_SESSIONS=10

# 会话超时（秒）
SESSION_TIMEOUT=3600

# ====================
# 日志配置
# ====================

# 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# 日志文件路径
LOG_FILE=./logs/loom.log

# 是否启用 JSON 格式日志
LOG_JSON=false

# ====================
# 缓存配置
# ====================

# LLM 响应缓存（秒，0 表示禁用）
LLM_CACHE_TTL=300

# 规则解析缓存（秒）
RULE_CACHE_TTL=60

# ====================
# 性能配置
# ====================

# 最大重试次数
MAX_RETRIES=3

# 请求超时（秒）
REQUEST_TIMEOUT=30

# 批处理大小
BATCH_SIZE=10

# ====================
# 安全配置
# ====================

# API 密钥（用于 Web API）
API_SECRET_KEY=change-this-in-production

# CORS 允许的来源
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# ====================
# 开发配置
# ====================

# 模拟模式（不实际调用 LLM）
SIMULATE_MODE=false

# 调试模式
DEBUG=false

# 测试模式
TESTING=false
```

### 4. 示例世界配置 (`world_config.yaml`)

示例世界配置文件位于 `examples/full_example/config/world_config.yaml`，展示如何配置一个完整的世界设定。

**文件位置：** `examples/full_example/config/world_config.yaml`

**配置结构：**
```yaml
world:
  name: "艾瑟兰大陆"
  description: "一个充满魔法与冒险的奇幻世界"
  genre: "fantasy"
  time_period: "中世纪"
  tone: "史诗、冒险、神秘"

characters:
  - name: "艾莉亚"
    role: "主角"
    description: "年轻的法师学徒，拥有强大的魔法天赋"
    traits: ["好奇", "勇敢", "善良"]
    
  - name: "雷纳德"
    role: "导师"
    description: "经验丰富的老法师，艾莉亚的导师"
    traits: ["智慧", "耐心", "神秘"]

locations:
  - name: "法师塔"
    description: "位于山顶的古老法师塔，雷纳德的居所"
    type: "建筑"
    
  - name: "幽暗森林"
    description: "充满神秘生物和古老魔法的森林"
    type: "自然"

magic_system:
  magic_types:
    - name: "元素魔法"
      description: "操控火、水、土、风等自然元素"
      
    - name: "奥术魔法"
      description: "纯粹的魔法能量，用于创造和破坏"

rules:
  consistency: "高"
  allow_player_intervention: true
  max_retcon_depth: 3
  memory_retention: "7天"
  
llm_settings:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000
```

## 配置选项详解

### LLM 提供商配置选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `type` | string | - | 提供商类型 (openai, deepseek, anthropic, gemini, ollama) |
| `api_key` | string | - | API 密钥，支持环境变量插值 `${VAR_NAME:default}` |
| `base_url` | string | 提供商默认 | API 基础 URL |
| `model` | string | 提供商默认 | 使用的模型名称 |
| `temperature` | float | 0.7 | 温度参数 (0.0-2.0) |
| `max_tokens` | int | 1000 | 最大生成令牌数 |
| `timeout` | int | 30 | 请求超时时间（秒） |
| `max_retries` | int | 3 | 最大重试次数 |
| `retry_delay` | float | 1.0 | 重试延迟（秒） |
| `fallback_enabled` | bool | true | 是否启用故障转移 |
| `enabled` | bool | true | 是否启用该提供商 |
| `connection_pool_size` | int | 5 | 连接池大小 |
| `enable_batching` | bool | false | 是否启用批处理 |
| `enable_caching` | bool | true | 是否启用响应缓存 |
| `cache_ttl` | int | 300 | 缓存生存时间（秒） |

### 会话配置选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `default_canon_path` | string | "./canon" | 默认规则文件路径 |
| `default_llm_provider` | string | "openai" | 默认 LLM 提供商 |
| `max_turns` | int | null | 最大回合数，null 表示无限制 |
| `auto_save_interval` | int | 5 | 自动保存间隔（回合数） |
| `intervention_allowed` | bool | true | 是否允许玩家干预 |
| `retcon_allowed` | bool | true | 是否允许 Retcon（历史修改） |

### 记忆配置选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `backend` | string | "sqlite" | 记忆存储后端 (sqlite, duckdb, postgresql) |
| `db_path` | string | "./data/loom_memory.db" | 数据库文件路径 |
| `vector_store_enabled` | bool | false | 是否启用向量存储 |
| `max_memories_per_session` | int | 1000 | 每个会话的最大记忆数 |
| `auto_summarize` | bool | true | 是否自动摘要记忆 |
| `summarization_interval_days` | int | 7 | 摘要间隔（天） |

### 性能配置选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `max_prompt_length` | int | 8000 | 最大提示长度（令牌数） |
| `max_memories_per_prompt` | int | 10 | 每个提示的最大记忆数 |
| `enable_response_caching` | bool | true | 是否启用响应缓存 |
| `cache_size_mb` | int | 100 | 缓存大小（MB） |

## 环境变量插值

LOOM 支持在配置文件中使用环境变量插值，语法为 `${VAR_NAME:default_value}`。

**示例：**
```yaml
openai:
  api_key: ${OPENAI_API_KEY:}  # 必须提供，无默认值
  model: ${OPENAI_MODEL:gpt-3.5-turbo}  # 默认值为 gpt-3.5-turbo
```

**插值规则：**
1. `${VAR_NAME}` - 必须提供环境变量，否则报错
2. `${VAR_NAME:default}` - 如果环境变量不存在，使用默认值
3. `${VAR_NAME:}` - 允许为空，如果环境变量不存在则使用空字符串

## 配置验证

LOOM 提供配置验证功能，确保配置的正确性。

### 验证配置
```bash
# 验证当前配置
loom config validate

# 验证指定配置文件
loom config validate --config /path/to/config.yaml
```

### 验证内容
1. **必填字段检查**：检查所有必填字段是否已设置
2. **类型检查**：验证配置值的类型是否正确
3. **范围检查**：验证数值是否在允许范围内
4. **环境变量检查**：验证引用的环境变量是否存在
5. **提供商连接测试**：测试 LLM 提供商连接是否正常

## 配置管理命令

LOOM CLI 提供完整的配置管理功能：

### 查看配置
```bash
# 查看当前配置（隐藏敏感信息）
loom config show

# 查看完整配置（包含敏感信息）
loom config show --include-secrets

# 查看特定配置项
loom config get llm.openai.model
loom config get provider_selection.default_provider
```

### 修改配置
```bash
# 设置配置项
loom config set llm.openai.model gpt-4
loom config set provider_selection.default_provider deepseek

# 从文件导入配置
loom config import /path/to/config.yaml

# 重置为默认配置
loom config reset
```

### 验证配置
```bash
# 验证配置
loom config validate

# 测试 LLM 提供商连接
loom config test --provider openai
loom config test --all
```

### 配置文件操作
```bash
# 创建默认配置文件
loom config init

# 备份配置文件
loom config backup

# 恢复配置文件
loom config restore /path/to/backup.yaml
```

## 配置最佳实践

### 1. 安全配置
- **使用环境变量存储敏感信息**：API 密钥等敏感信息应存储在 `.env` 文件中
- **分环境配置**：为开发、测试、生产环境使用不同的配置文件
- **定期轮换密钥**：定期更新 API 密钥，避免长期使用同一密钥
- **最小权限原则**：只启用必要的功能和权限

### 2. 性能优化
- **启用缓存**：`enable_caching: true` 可显著减少 API 调用
- **合理设置超时**：根据网络状况设置适当的超时时间
- **使用连接池**：`connection_pool_size: 5` 可提高并发性能
- **批处理优化**：对于批量任务启用 `enable_batching: true`

### 3. 成本控制
- **设置预算限制**：`monthly_budget: 50.0` 防止意外费用
- **启用自动切换**：`auto_switch_to_cheaper: true` 自动选择成本更低的模型
- **监控令牌使用**：`token_counting: true` 跟踪令牌消耗
- **使用缓存减少调用**：缓存频繁使用的响应

### 4. 故障转移和高可用
- **配置多个提供商**：确保至少有两个可用的 LLM 提供商
- **设置合理的重试策略**：`max_retries: 3`, `retry_delay: 1.0`
- **启用故障转移**：`fallback_enabled: true`
- **健康检查**：定期检查提供商可用性

## 故障排除

### 常见问题

#### 1. 配置文件无法加载
```bash
# 检查配置文件路径
loom config show --verbose

# 查看日志
tail -f ./logs/loom.log

# 验证配置文件格式
yamllint config/default_config.yaml
```

#### 2. 环境变量未生效
```bash
# 检查环境变量是否设置
echo $OPENAI_API_KEY

# 重新加载环境变量
source .env

# 使用 --env-file 参数指定环境文件
loom run --env-file .env
```

#### 3. LLM 提供商连接失败
```bash
# 测试提供商连接
loom config test --provider openai

# 检查 API 密钥
loom config get llm.openai.api_key

# 查看详细错误信息
loom config test --provider openai --verbose
```

#### 4. 配置验证失败
```bash
# 查看验证错误
loom config validate --verbose

# 修复配置错误
loom config set <key> <value>

# 重置为默认配置
loom config reset
```

## 高级配置

### 自定义配置类
您可以通过继承 `AppConfig` 类来添加自定义配置：

```python
from loom.core.config_manager import AppConfig, ConfigManager

class CustomAppConfig(AppConfig):
    """自定义应用配置"""
    
    custom_field: str = "default_value"
    custom_dict: Dict[str, Any] = field(default_factory=dict)

# 使用自定义配置
config_manager = ConfigManager(config_class=CustomAppConfig)
```

### 动态配置加载
LOOM 支持运行时动态加载配置：

```python
from loom.core.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 动态更新配置
config_manager.update_config({
    "llm": {
        "openai": {
            "model": "gpt-4"
        }
    }
})

# 保存配置
config_manager.save_config()
```

### 配置热重载
启用配置热重载，无需重启应用：

```yaml
# 在配置文件中启用热重载
monitoring:
  enable_config_watcher: true
  config_watch_interval: 5  # 检查间隔（秒）
```

## 下一步

配置完成后，您可以：

1. **验证配置**：运行 `loom config validate --check-connections`
2. **测试提供商**：运行 `loom config test --all`
3. **开始使用**：查看 [快速开始指南](../quick-start/basic-configuration.md)
4. **了解 API 使用**：查看 [API 使用示例](../api-usage/quick-api-start.md)
5. **配置环境变量**：查看 [环境变量配置文档](./environment-vars.md)
6. **了解高级配置**：查看 [高级配置文档](./advanced-config.md)
