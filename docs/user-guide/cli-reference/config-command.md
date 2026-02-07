# config 命令

## 概述

`config` 命令用于管理 LOOM 的配置系统。它支持查看、编辑、验证、导入导出配置等操作。

## 命令语法

```bash
loom config [OPTIONS] COMMAND [ARGS]...
```

## 子命令

### 1. `show` - 显示配置

显示当前配置信息。

**语法**:
```bash
loom config show [OPTIONS]
```

**选项**:
- `--section, -s TEXT`: 显示特定配置部分 (llm, memory, session, etc.)
- `--format, -f TEXT`: 输出格式 (table, json, yaml) [默认: table]
- `--verbose, -v`: 详细输出，显示配置来源
- `--show-sources`: 显示每个配置项的来源
- `--help`: 显示帮助信息

**示例**:
```bash
# 显示所有配置（表格格式）
loom config show

# 显示 LLM 配置部分
loom config show --section llm

# 显示 JSON 格式的会话配置
loom config show --section session --format json

# 显示详细配置，包括来源
loom config show --verbose --show-sources
```

**输出示例** (表格格式):
```
┌─────────────────┬─────────────────────────────────────┐
│ Section         │ Value                               │
├─────────────────┼─────────────────────────────────────┤
│ llm.openai      │                                     │
│   enabled       │ true                                │
│   model         │ gpt-3.5-turbo                       │
│   temperature   │ 0.7                                 │
│   max_tokens    │ 1000                                │
│   timeout       │ 30                                  │
└─────────────────┴─────────────────────────────────────┘
```

### 2. `set` - 设置配置值

设置配置项的值。

**语法**:
```bash
loom config set [OPTIONS] KEY VALUE
```

**选项**:
- `--global, -g`: 保存到全局配置文件 (~/.loom/config.yaml)
- `--local, -l`: 保存到项目配置文件 (./config/local.yaml)
- `--env, -e`: 设置为环境变量（仅当前会话）
- `--type TEXT`: 值类型 (string, int, float, bool, json)
- `--help`: 显示帮助信息

**参数**:
- `KEY`: 配置键，使用点号分隔 (如: `llm.openai.model`)
- `VALUE`: 配置值

**示例**:
```bash
# 设置 OpenAI 模型
loom config set llm.openai.model "gpt-4-turbo"

# 设置温度参数（浮点数）
loom config set llm.openai.temperature 0.5 --type float

# 设置最大回合数（整数）
loom config set session.default_max_turns 100 --type int

# 启用缓存（布尔值）
loom config set llm.openai.enable_caching true --type bool

# 设置 JSON 值
loom config set memory.vector_store '{"enabled": true, "provider": "chromadb"}' --type json

# 保存到全局配置
loom config set --global llm.openai.model "gpt-4"

# 保存到本地配置
loom config set --local session.auto_save_interval 10
```

### 3. `get` - 获取配置值

获取特定配置项的值。

**语法**:
```bash
loom config get [OPTIONS] KEY
```

**选项**:
- `--format, -f TEXT`: 输出格式 (raw, json, yaml) [默认: raw]
- `--default TEXT`: 如果键不存在，返回默认值
- `--help`: 显示帮助信息

**示例**:
```bash
# 获取 OpenAI 模型
loom config get llm.openai.model

# 获取 JSON 格式的完整 LLM 配置
loom config get llm --format json

# 获取不存在的键，返回默认值
loom config get nonexistent.key --default "default_value"
```

### 4. `unset` - 删除配置项

删除配置项，恢复为默认值。

**语法**:
```bash
loom config unset [OPTIONS] KEY
```

**选项**:
- `--global, -g`: 从全局配置中删除
- `--local, -l`: 从本地配置中删除
- `--all`: 从所有配置源中删除
- `--help`: 显示帮助信息

**示例**:
```bash
# 删除特定配置项
loom config unset llm.openai.temperature

# 从全局配置中删除
loom config unset --global llm.openai.model

# 从本地配置中删除
loom config unset --local session.auto_save_interval

# 从所有配置源中删除
loom config unset --all llm.openai.api_key
```

### 5. `validate` - 验证配置

验证配置文件的语法和完整性。

**语法**:
```bash
loom config validate [OPTIONS]
```

**选项**:
- `--file, -f PATH`: 验证特定配置文件
- `--check-required`: 检查必需配置项
- `--check-connections`: 检查外部连接（LLM、数据库等）
- `--report PATH`: 生成验证报告文件
- `--fix`: 自动修复可修复的问题
- `--help`: 显示帮助信息

**示例**:
```bash
# 验证当前配置
loom config validate

# 验证特定配置文件
loom config validate --file custom_config.yaml

# 检查必需配置项
loom config validate --check-required

# 检查外部连接
loom config validate --check-connections

# 生成验证报告
loom config validate --report validation_report.json

# 自动修复问题
loom config validate --fix
```

**验证输出示例**:
```
✓ Configuration syntax is valid
✓ All required fields are present
⚠ Missing API key for OpenAI provider
✓ Database connection successful
✗ Invalid timeout value: must be positive integer
```

### 6. `test` - 测试配置

测试配置的实际功能，如 LLM 连接、数据库连接等。

**语法**:
```bash
loom config test [OPTIONS]
```

**选项**:
- `--provider TEXT`: 测试特定 LLM 提供商
- `--all`: 测试所有已启用的提供商
- `--database`: 测试数据库连接
- `--memory`: 测试记忆系统
- `--timeout INTEGER`: 测试超时时间（秒） [默认: 30]
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 测试 OpenAI 连接
loom config test --provider openai

# 测试 DeepSeek 连接
loom config test --provider deepseek

# 测试所有提供商
loom config test --all

# 测试数据库连接
loom config test --database

# 测试记忆系统
loom config test --memory

# 详细测试
loom config test --all --verbose

# 测试 DeepSeek 推理模式
loom config test --provider deepseek --verbose --timeout 60
```

**测试输出示例**:
```
Testing OpenAI provider...
  ✓ Connection successful (200ms)
  ✓ Model available: gpt-3.5-turbo
  ✓ Authentication valid
  ✓ Response time: 1.2s

Testing DeepSeek provider...
  ✓ Connection successful (350ms)
  ✓ Model available: deepseek-chat
  ✓ Authentication valid
  ✓ Response time: 1.5s
  ✓ 128K context supported
  ✓ Reasoning mode available

Testing database connection...
  ✓ SQLite database accessible
  ✓ Schema version: 2.0.0
  ✓ Read/write permissions OK

All tests passed! ✅
```

### 7. `import` - 导入配置

从文件导入配置。

**语法**:
```bash
loom config import [OPTIONS]
```

**选项**:
- `--file, -f PATH`: 要导入的配置文件 [必需]
- `--merge`: 合并到现有配置（而不是替换）
- `--overwrite`: 覆盖现有配置项
- `--dry-run`: 预览导入效果，不实际应用
- `--help`: 显示帮助信息

**示例**:
```bash
# 从文件导入配置
loom config import --file backup_config.yaml

# 合并配置
loom config import --file custom_settings.yaml --merge

# 预览导入效果
loom config import --file new_config.yaml --dry-run
```

### 8. `export` - 导出配置

导出当前配置到文件。

**语法**:
```bash
loom config export [OPTIONS]
```

**选项**:
- `--file, -f PATH`: 导出文件路径 [必需]
- `--format TEXT`: 导出格式 (yaml, json) [默认: yaml]
- `--include-defaults`: 包括默认值
- `--include-sources`: 包括配置来源信息
- `--section TEXT`: 只导出特定部分
- `--help`: 显示帮助信息

**示例**:
```bash
# 导出完整配置
loom config export --file config_backup.yaml

# 导出 JSON 格式
loom config export --file config_backup.json --format json

# 只导出 LLM 配置
loom config export --file llm_config.yaml --section llm

# 包括默认值
loom config export --file full_config.yaml --include-defaults
```

### 9. `reset` - 重置配置

重置配置为默认值。

**语法**:
```bash
loom config reset [OPTIONS]
```

**选项**:
- `--global, -g`: 重置全局配置
- `--local, -l`: 重置本地配置
- `--all`: 重置所有配置
- `--confirm`: 跳过确认提示
- `--help`: 显示帮助信息

**示例**:
```bash
# 重置所有配置（需要确认）
loom config reset

# 重置全局配置
loom config reset --global

# 重置本地配置
loom config reset --local

# 跳过确认提示
loom config reset --all --confirm
```

### 10. `diff` - 比较配置

比较不同配置源之间的差异。

**语法**:
```bash
loom config diff [OPTIONS]
```

**选项**:
- `--source1 TEXT`: 第一个配置源 (current, global, local, default, file:PATH)
- `--source2 TEXT`: 第二个配置源 [默认: current]
- `--format TEXT`: 输出格式 (table, json, unified) [默认: table]
- `--only-different`: 只显示不同的项
- `--help`: 显示帮助信息

**示例**:
```bash
# 比较当前配置与默认配置
loom config diff --source1 current --source2 default

# 比较全局配置与本地配置
loom config diff --source1 global --source2 local

# 比较配置文件
loom config diff --source1 file:config1.yaml --source2 file:config2.yaml

# 只显示不同的项
loom config diff --source1 current --source2 default --only-different
```

## 配置键参考

### LLM 配置键
- `llm.{provider}.enabled` - 是否启用提供商
- `llm.{provider}.api_key` - API 密钥（建议使用环境变量）
- `llm.{provider}.model` - 模型名称
- `llm.{provider}.temperature` - 温度参数 (0.0-2.0)
- `llm.{provider}.max_tokens` - 最大令牌数
- `llm.{provider}.timeout` - 超时时间（秒）
- `llm.{provider}.max_retries` - 最大重试次数
- `llm.{provider}.enable_caching` - 是否启用缓存
- `llm.{provider}.cache_ttl` - 缓存生存时间（秒）

### DeepSeek 特定配置键
- `llm.deepseek.base_url` - API基础URL（默认: https://api.deepseek.com）
- `llm.deepseek.thinking_enabled` - 是否启用推理模式（布尔值）
- `llm.deepseek.connection_pool_size` - 连接池大小
- `llm.deepseek.fallback_enabled` - 是否启用故障转移
- `llm.deepseek.enable_batching` - 是否启用批处理

### 会话配置键
- `session.default_max_turns` - 默认最大回合数
- `session.auto_save_interval` - 自动保存间隔（回合数）
- `session.persistence.enabled` - 是否启用持久化
- `session.persistence.engine` - 持久化引擎 (sqlite, postgresql)
- `session.persistence.database_path` - 数据库路径
- `session.memory.short_term_capacity` - 短期记忆容量
- `session.memory.long_term_capacity` - 长期记忆容量

### 记忆系统配置键
- `memory.vector_store.enabled` - 是否启用向量存储
- `memory.vector_store.provider` - 向量存储提供商 (chromadb, sqlite)
- `memory.vector_store.collection_name` - 集合名称
- `memory.vector_store.embedding_model` - 嵌入模型
- `memory.structured_store.enabled` - 是否启用结构化存储
- `memory.structured_store.provider` - 结构化存储提供商
- `memory.summarizer.enabled` - 是否启用摘要生成器
- `memory.summarizer.max_chunk_size` - 最大块大小
- `memory.summarizer.compression_ratio` - 压缩比例

### 监控配置键
- `monitoring.enabled` - 是否启用监控
- `monitoring.metrics[].name` - 指标名称
- `monitoring.metrics[].enabled` - 是否启用指标
- `monitoring.metrics[].aggregation` - 聚合方式
- `monitoring.alerting.enabled` - 是否启用告警
- `monitoring.alerting.webhook_url` - 告警 Webhook URL

## 使用示例

### 示例 1：配置开发环境

```bash
# 设置开发环境配置
loom config set --local llm.openai.model "gpt-3.5-turbo"
loom config set --local llm.openai.temperature 0.8
loom config set --local session.default_max_turns 20
loom config set --local session.auto_save_interval 5
loom config set --local logging.level "DEBUG"

# 验证配置
loom config validate --check-required

# 测试连接
loom config test --provider openai
```

### 示例 2：配置生产环境

```bash
# 设置生产环境配置
loom config set --global llm.openai.model "gpt-4-turbo"
loom config set --global llm.openai.temperature 0.7
loom config set --global llm.openai.enable_caching true
loom config set --global session.default_max_turns 100
loom config set --global monitoring.enabled true
loom config set --global logging.level "WARNING"

# 导出配置备份
loom config export --file production_backup.yaml

# 测试所有功能
loom config test --all --timeout 60
```

### 示例 3：配置 DeepSeek 提供商

```bash
# 设置 DeepSeek 配置
loom config set --global llm.deepseek.enabled true
loom config set --global llm.deepseek.api_key "${DEEPSEEK_API_KEY}"
loom config set --global llm.deepseek.model "deepseek-chat"
loom config set --global llm.deepseek.thinking_enabled false
loom config set --global llm.deepseek.temperature 1.0
loom config set --global llm.deepseek.max_tokens 4096
loom config set --global llm.deepseek.timeout 60

# 配置推理模式（使用 deepseek-reasoner 模型）
loom config set --local llm.deepseek.model "deepseek-reasoner"
loom config set --local llm.deepseek.thinking_enabled true
loom config set --local llm.deepseek.max_tokens 32000

# 验证配置
loom config validate --check-required

# 测试 DeepSeek 连接
loom config test --provider deepseek --verbose --timeout 60

# 查看 DeepSeek 配置
loom config show --section llm.deepseek
```

### 示例 5：故障排除配置

```bash
# 查看当前配置
loom config show --verbose

# 检查配置问题
loom config validate --check-connections

# 测试特定功能
loom config test --provider openai --verbose
loom config test --provider deepseek --verbose

# 重置有问题的配置
loom config unset llm.openai.api_key
loom config set llm.openai.api_key "${OPENAI_API_KEY}"

loom config unset llm.deepseek.api_key
loom config set llm.deepseek.api_key "${DEEPSEEK_API_KEY}"

# 比较与默认配置的差异
loom config diff --source1 current --source2 default --only-different
```

## 最佳实践

### 1. 安全实践
- 使用环境变量存储 API 密钥，而不是硬编码在配置文件中
- 定期轮换 API 密钥
- 为不同环境使用不同的配置

### 2. 性能优化
- 启用缓存以减少 API 调用
- 设置合理的超时和重试参数
- 根据使用场景调整记忆容量

### 3. 维护实践
- 定期备份配置
- 使用版本控制管理配置文件
- 为不同团队成员创建配置模板

### 4. 调试技巧
- 使用 `--verbose` 选项查看详细输出
- 使用 `--dry-run` 预览更改效果
- 使用 `diff` 命令比较配置差异

## 故障排除

### 常见问题

#### 1. 配置更改未生效
```bash
# 检查配置优先级
loom config show --show-sources

# 重新加载配置
loom config reset --local
```

#### 2. API 密钥错误
```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 重新设置
loom config unset llm.openai.api_key
loom config set llm.openai.api_key "${OPENAI_API_KEY}"
```

#### 3. 配置文件语法错误
```bash
# 验证语法
loom config validate --file config.yaml

# 查看错误详情
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

#### 4. 配置冲突
```bash
# 查看冲突
loom config diff --source1 global --source2 local

# 解决冲突
loom config unset --global conflicting.key
loom config unset --local conflicting.key
loom config set conflicting.key "correct_value"
```

## 相关命令

- [`run` 命令](run-command.md) - 运行会话
- [`session` 命令](session-command.md) - 管理会话
- [`rules` 命令](../rules/basic-commands.md) - 管理规则

## 获取帮助

```bash
# 查看完整帮助
loom config --help

# 查看特定子命令帮助
loom config show --help
loom config set --help

# 查看配置键文档
loom config docs
