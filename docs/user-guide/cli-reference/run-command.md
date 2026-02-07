# run 命令

## 概述

`run` 命令用于运行 LOOM 世界会话。它支持交互式运行、批处理运行、从文件加载会话等多种运行模式。

## 命令语法

```bash
loom run [OPTIONS] COMMAND [ARGS]...
```

## 子命令

### 1. `interactive` - 交互式运行

启动交互式会话，与 AI 进行实时对话。

**语法**:
```bash
loom run interactive [OPTIONS]
```

**选项**:
- `--canon, -c PATH`: 规则文件路径 [默认: "./canon/default.md"]
- `--name, -n TEXT`: 会话名称 [默认: "New Session"]
- `--provider, -p TEXT`: LLM 提供商
- `--max-turns, -m INTEGER`: 最大回合数
- `--output, -o PATH`: 输出文件路径
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 基础交互式会话
loom run interactive --canon templates/rules/fantasy_basic.md

# 指定会话名称和提供商
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --name "奇幻冒险" \
  --provider openai

# 限制回合数并保存输出
loom run interactive \
  --canon my_rules.md \
  --max-turns 10 \
  --output session_log.txt

# 详细模式
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --verbose
```

**交互模式命令**:
在交互式会话中，您可以输入以下特殊命令：

- `help` - 显示可用命令
- `quit` - 退出会话
- `save` - 手动保存会话
- `status` - 查看会话状态

### 2. `batch` - 批处理运行

从文件加载输入，批量运行会话。

**语法**:
```bash
loom run batch INPUT_FILE [OPTIONS]
```

**参数**:
- `INPUT_FILE`: 输入文件路径（JSON或文本格式）

**选项**:
- `--canon, -c PATH`: 规则文件路径 [默认: "./canon/default.md"]
- `--name, -n TEXT`: 会话名称
- `--output, -o PATH`: 输出文件路径
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 基础批处理运行
loom run batch actions.txt --canon templates/rules/fantasy_basic.md

# 指定会话名称和输出文件
loom run batch prompts.txt \
  --canon templates/rules/fantasy_basic.md \
  --name "批处理测试" \
  --output results.json

# 详细模式
loom run batch data.json \
  --canon my_rules.md \
  --verbose
```

**输入文件格式**:

1. **文本格式**: 每行一个输入
   ```
   第一行输入
   第二行输入
   第三行输入
   ```

2. **JSON 格式**: JSON数组格式
   ```json
   [
     "第一行输入",
     "第二行输入",
     "第三行输入"
   ]
   ```

**输出格式**:
- 如果指定 `--output` 选项，结果将保存到指定文件
- 支持文本格式（.txt）和JSON格式（.json）
- 如果不指定输出文件，结果将显示在控制台

## 通用选项

以下选项适用于所有 `run` 子命令：

- `--config PATH`: 使用特定配置文件
- `--env-file PATH`: 从文件加载环境变量
- `--log-level TEXT`: 日志级别 (DEBUG, INFO, WARNING, ERROR) [默认: INFO]
- `--log-file PATH`: 日志文件路径
- `--cache-dir PATH`: 缓存目录
- `--temp-dir PATH`: 临时目录
- `--no-color`: 禁用彩色输出
- `--version`: 显示版本信息

## 运行模式详解

### 交互式模式工作流程

1. **初始化**:
   - 加载规则文件
   - 创建会话管理器
   - 初始化 LLM 提供商
   - 设置记忆系统

2. **会话循环**:
   ```
   显示提示 → 用户输入 → 处理输入 → 生成响应 → 更新记忆 → 显示响应
   ```

3. **结束处理**:
   - 保存会话状态
   - 生成摘要
   - 清理资源

### 批处理模式工作流程

1. **准备阶段**:
   - 加载所有输入
   - 初始化会话
   - 准备输出格式

2. **处理阶段**:
   - 对每个输入执行会话
   - 收集响应
   - 更新进度

3. **完成阶段**:
   - 保存所有结果
   - 生成统计信息
   - 清理资源

## 使用示例

### 示例 1：完整的奇幻冒险

```bash
# 创建详细的规则文件
cat > my_fantasy_rules.md << 'EOF'
# 龙之谷奇幻世界

## 世界设定
- **世界名称**: 龙之谷
- **时代背景**: 中世纪奇幻
- **魔法系统**: 元素魔法、神圣魔法、黑暗魔法
- **主要种族**: 人类、精灵、矮人、龙族

## 核心规则
1. 魔法需要吟唱和材料
2. 龙族是智慧生物，可以交流
3. 每个角色有独特的背景故事
4. 重大决定影响世界走向
EOF

# 启动交互式会话
loom run interactive \
  --canon my_fantasy_rules.md \
  --name "龙之谷冒险" \
  --provider openai \
  --max-turns 20 \
  --verbose
```

### 示例 2：批量测试规则

```bash
# 创建测试输入
cat > test_inputs.txt << 'EOF'
我来到风语镇，想找一份工作
我去铁匠铺看看
我和镇民交谈了解情况
我发现了一个神秘的地图
我决定按照地图去探险
EOF

# 运行批处理测试
loom run batch test_inputs.txt \
  --canon templates/rules/fantasy_basic.md \
  --name "规则测试" \
  --output test_results.json

# 查看结果
cat test_results.json
```

### 示例 3：使用会话命令管理会话

```bash
# 查看现有会话
loom session list

# 查看会话详情
loom session show --session-name "龙之谷冒险"

# 导出会话历史
loom export markdown \
  --session-name "龙之谷冒险" \
  --output adventure_history.md
```

## 高级功能

### 1. 使用详细日志进行调试

```bash
# 启用详细日志
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --verbose

# 查看会话日志
tail -f logs/loom.log
```

### 2. 配置LLM提供商

```bash
# 设置默认LLM提供商
loom config set session_defaults.default_llm_provider openai

# 设置API密钥
loom config set llm.openai.api_key "your-api-key"

# 测试配置
loom config test
```

### 3. 管理会话数据

```bash
# 查看所有会话
loom session list

# 导出会话数据
loom export markdown --session-name "测试会话" --output session_export.md

# 清理旧会话
loom session delete --older-than 7d
```

## 故障排除

### 常见问题

#### 1. 会话启动失败
```bash
# 检查规则文件
loom rules validate --file templates/rules/fantasy_basic.md

# 检查提供商连接
loom config test

# 查看详细日志
loom run interactive --verbose
```

#### 2. 响应时间过长
```bash
# 减少最大回合数
loom run interactive --max-turns 5

# 使用更简单的规则文件
loom run interactive --canon templates/rules/fantasy_basic.md
```

#### 3. 批处理文件读取失败
```bash
# 检查输入文件格式
cat input.txt

# 使用正确的批处理语法
loom run batch input.txt --canon templates/rules/fantasy_basic.md

# 检查文件编码
file -i input.txt
```

#### 4. 输出文件写入失败
```bash
# 检查输出目录权限
ls -la output/

# 使用绝对路径
loom run batch input.txt --output /tmp/results.json

# 检查磁盘空间
df -h .
```

## 最佳实践

### 1. 会话管理
- 为每个项目使用唯一的会话名称
- 定期保存重要会话
- 使用有意义的输出文件名

### 2. 性能优化
- 批处理时合理控制输入数量
- 使用适当的最大回合数限制
- 监控会话资源使用情况

### 3. 错误处理
- 使用 `--verbose` 模式调试问题
- 检查日志文件了解详细错误
- 测试规则文件后再正式运行

### 4. 资源管理
- 清理不再需要的会话
- 定期备份重要数据
- 监控磁盘空间使用

## 相关命令

- [`session` 命令](session-command.md) - 管理会话
- [`config` 命令](config-command.md) - 管理配置
- [`export` 命令](../export/basic-commands.md) - 导出会话
- [`rules` 命令](../rules/basic-commands.md) - 管理规则

## 获取帮助

```bash
# 查看完整帮助
loom run --help

# 查看特定子命令帮助
loom run interactive --help
loom run batch --help

# 查看示例
loom run examples
