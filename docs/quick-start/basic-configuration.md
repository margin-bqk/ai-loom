# 基本配置

## 概述

本文档介绍 LOOM 的基本配置方法。LOOM 采用分层配置系统，支持多种配置源和环境变量覆盖。

## 配置系统架构

LOOM 的配置系统采用以下优先级（从高到低）：

1. **命令行参数** - 最高优先级
2. **环境变量** - 次高优先级
3. **用户配置文件** (`~/.loom/config.yaml`)
4. **项目配置文件** (`./config/default_config.yaml`)
5. **默认配置** - 最低优先级

## 配置文件位置

### 1. 默认配置文件
- 路径: `config/default_config.yaml`
- 用途: 项目级别的默认配置
- 示例: [查看默认配置](https://github.com/your-org/loom/blob/main/config/default_config.yaml)

### 2. 用户配置文件
- 路径: `~/.loom/config.yaml` (Linux/Mac) 或 `%USERPROFILE%\.loom\config.yaml` (Windows)
- 用途: 用户级别的个性化配置
- 创建方法:
```bash
# 创建配置目录
mkdir -p ~/.loom

# 从默认配置复制
cp config/default_config.yaml ~/.loom/config.yaml
```

### 3. 环境特定配置文件
- 路径: `config/production.yaml`, `config/development.yaml`, `config/testing.yaml`
- 用途: 不同环境的特定配置
- 加载方式: 通过 `LOOM_ENV` 环境变量指定

## 核心配置部分

### 1. LLM 提供商配置

```yaml
llm_providers:
  openai:
    type: openai
    enabled: true
    api_key: ${OPENAI_API_KEY:}  # 从环境变量读取
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 1000
    
  anthropic:
    type: anthropic
    enabled: true
    api_key: ${ANTHROPIC_API_KEY:}
    model: claude-3-haiku-20240307
    
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
    
  google:
    type: google
    enabled: false  # 默认禁用
    api_key: ${GOOGLE_API_KEY:}
    
  ollama:
    type: ollama
    enabled: false  # 默认禁用
    base_url: http://localhost:11434
    model: llama2
```

### 2. 会话配置

```yaml
session:
  default_max_turns: 50
  auto_save_interval: 5  # 每5回合自动保存
  persistence:
    enabled: true
    engine: sqlite
    database_path: ./data/sessions.db
  memory:
    short_term_capacity: 100  # 短期记忆容量
    long_term_capacity: 1000  # 长期记忆容量
```

### 3. 记忆系统配置

```yaml
memory:
  vector_store:
    enabled: true
    provider: chromadb  # 或 "sqlite", "memory"
    collection_name: loom_memory
    embedding_model: text-embedding-3-small
    
  structured_store:
    enabled: true
    provider: sqlite
    database_path: ./data/memory.db
    
  summarizer:
    enabled: true
    max_chunk_size: 2000
    compression_ratio: 0.3
```

### 4. 性能监控配置

```yaml
monitoring:
  enabled: true
  metrics:
    - name: llm_latency
      enabled: true
      aggregation: p95
      
    - name: memory_usage
      enabled: true
      
    - name: cost_tracking
      enabled: true
      currency: USD
      
  alerting:
    enabled: false
    webhook_url: ${ALERT_WEBHOOK_URL:}
```

## 环境变量配置

### 常用环境变量

```bash
# LLM API 密钥
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="your-anthropic-key"
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export GOOGLE_API_KEY="your-google-key"

# 数据库配置
export LOOM_DB_PATH="./data/loom.db"
export LOOM_DB_TYPE="sqlite"  # 或 "postgresql", "mysql"

# 性能配置
export LOOM_MAX_WORKERS="4"
export LOOM_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR

# 环境指定
export LOOM_ENV="development"  # development, production, testing
```

### .env 文件示例

创建 `.env` 文件在项目根目录：

```env
# LLM 提供商
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
GOOGLE_API_KEY=your-google-api-key

# 数据库
LOOM_DB_PATH=./data/loom.db
LOOM_DB_TYPE=sqlite

# 性能
LOOM_MAX_WORKERS=4
LOOM_LOG_LEVEL=INFO

# 环境
LOOM_ENV=development
```

## 使用 CLI 管理配置

### 1. 查看配置

```bash
# 查看所有配置
loom config show

# 查看特定部分
loom config show --section llm
loom config show --section session

# 不同格式输出
loom config show --format json
loom config show --format yaml
loom config show --format table
```

### 2. 编辑配置

```bash
# 设置配置值
loom config set llm.openai.model "gpt-4-turbo"
loom config set session.default_max_turns 100

# 从文件导入配置
loom config import --file custom_config.yaml

# 导出当前配置
loom config export --file backup_config.yaml
```

### 3. 验证配置

```bash
# 验证配置语法
loom config validate

# 验证配置完整性
loom config validate --check-required

# 测试 LLM 连接
loom config test --provider openai
loom config test --provider deepseek
```

## 配置最佳实践

### 1. 安全配置

```yaml
# 使用环境变量存储敏感信息
api_key: ${API_KEY_ENV_VAR:}

# 禁用不必要的提供商
enabled: false

# 设置合理的超时和重试
timeout: 30
max_retries: 3
retry_delay: 1.0
```

### 2. 性能优化配置

```yaml
# 启用缓存
enable_caching: true
cache_ttl: 300  # 5分钟

# 连接池
connection_pool_size: 5

# 批处理
enable_batching: true
batch_size: 10
batch_timeout: 0.5
```

### 3. 开发环境配置

```yaml
# development.yaml
llm_providers:
  openai:
    enabled: true
    model: gpt-3.5-turbo  # 使用便宜模型
    
  deepseek:
    enabled: true
    model: deepseek-chat  # 中文优化模型
    
  ollama:
    enabled: true  # 启用本地模型
    
session:
  auto_save_interval: 1  # 频繁保存
  
logging:
  level: DEBUG  # 详细日志
```

### 4. 生产环境配置

```yaml
# production.yaml
llm_providers:
  openai:
    enabled: true
    model: gpt-4-turbo  # 使用高质量模型
    
  anthropic:
    enabled: true  # 启用备用提供商
    
  deepseek:
    enabled: true  # 启用DeepSeek作为成本优化选项
    
session:
  auto_save_interval: 10  # 减少保存频率
  
monitoring:
  enabled: true
  alerting:
    enabled: true
    
logging:
  level: WARNING  # 减少日志量
```

## 故障排除

### 1. 配置加载失败

```bash
# 检查配置文件语法
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 查看加载的配置
loom config show --verbose

# 重置为默认配置
loom config reset
```

### 2. 环境变量未生效

```bash
# 检查环境变量
echo $OPENAI_API_KEY
echo $DEEPSEEK_API_KEY

# 重新加载环境变量
source .env  # Linux/Mac
# 或重新启动终端

# 使用 --env-file 参数
loom run --env-file .env interactive
```

### 3. 配置优先级问题

```bash
# 查看配置来源
loom config show --show-sources

# 强制使用特定配置文件
loom --config custom_config.yaml run interactive
```

## 下一步

配置完成后，您可以：

1. **运行第一个示例**: 查看 [第一个示例](first-example.md)
2. **验证配置**: 查看 [验证安装](verify-installation.md)
3. **深入学习配置**: 查看 [配置指南](../user-guide/configuration/config-files.md)
4. **了解高级配置**: 查看 [高级配置](../user-guide/configuration/advanced-config.md)
