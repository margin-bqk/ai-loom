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
- `--canon, -c PATH`: 规则文件路径 [必需]
- `--name, -n TEXT`: 会话名称 [默认: "New Session"]
- `--provider, -p TEXT`: LLM 提供商 (openai, anthropic, google, ollama)
- `--model TEXT`: 特定模型名称
- `--max-turns, -m INTEGER`: 最大回合数
- `--output, -o PATH`: 输出文件路径
- `--verbose, -v`: 详细输出
- `--debug-reasoning`: 显示推理过程
- `--monitor-performance`: 显示性能监控
- `--no-save`: 不保存会话
- `--dry-run`: 预览运行，不实际执行
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

# 使用特定模型
loom run interactive \
  --canon templates/rules/sci_fi_basic.md \
  --provider openai \
  --model "gpt-4-turbo"

# 限制回合数并保存输出
loom run interactive \
  --canon my_rules.md \
  --max-turns 10 \
  --output session_log.txt

# 详细模式，显示推理过程
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --verbose \
  --debug-reasoning

# 性能监控模式
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --monitor-performance
```

**交互模式命令**:
在交互式会话中，您可以输入以下特殊命令：

- `help` - 显示可用命令
- `exit` 或 `quit` - 退出会话
- `save` - 手动保存会话
- `history` - 查看会话历史
- `status` - 查看会话状态
- `!edit [描述]` - 编辑世界状态
- `!retcon [修正]` - 修正之前的叙述
- `!ooc [注释]` - 添加 OOC 注释
- `!config [键] [值]` - 修改会话配置
- `!export [格式]` - 导出当前会话

### 2. `batch` - 批处理运行

从文件加载输入，批量运行会话。

**语法**:
```bash
loom run batch [OPTIONS]
```

**选项**:
- `--canon, -c PATH`: 规则文件路径 [必需]
- `--input, -i PATH`: 输入文件路径 [必需]
- `--output, -o PATH`: 输出文件路径
- `--name, -n TEXT`: 会话名称 [默认: "Batch Session"]
- `--provider, -p TEXT`: LLM 提供商
- `--max-turns, -m INTEGER`: 每行输入的最大回合数
- `--parallel INTEGER`: 并行处理数 [默认: 1]
- `--format TEXT`: 输入文件格式 (text, json, csv) [默认: text]
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 基础批处理运行
loom run batch \
  --canon templates/rules/fantasy_basic.md \
  --input actions.txt \
  --output results.txt

# 并行处理
loom run batch \
  --canon my_rules.md \
  --input scenarios.csv \
  --output outcomes.json \
  --parallel 4 \
  --format csv

# 限制每行输入的回合数
loom run batch \
  --canon templates/rules/fantasy_basic.md \
  --input prompts.txt \
  --max-turns 3

# JSON 格式输入
loom run batch \
  --canon templates/rules/fantasy_basic.md \
  --input data.json \
  --format json \
  --output responses.json
```

**输入文件格式**:

1. **文本格式** (`--format text`):
   ```
   第一行输入
   第二行输入
   第三行输入
   ```

2. **JSON 格式** (`--format json`):
   ```json
   [
     {"input": "第一行输入", "context": "额外上下文"},
     {"input": "第二行输入", "context": "更多上下文"}
   ]
   ```

3. **CSV 格式** (`--format csv`):
   ```csv
   input,context
   "第一行输入","额外上下文"
   "第二行输入","更多上下文"
   ```

### 3. `continue` - 继续现有会话

继续之前保存的会话。

**语法**:
```bash
loom run continue [OPTIONS]
```

**选项**:
- `--session-id TEXT`: 会话 ID
- `--session-name TEXT`: 会话名称
- `--max-turns, -m INTEGER`: 额外最大回合数
- `--output, -o PATH`: 输出文件路径
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 通过会话 ID 继续
loom run continue --session-id "abc123-def456"

# 通过会话名称继续
loom run continue --session-name "奇幻冒险"

# 继续并限制额外回合数
loom run continue \
  --session-name "奇幻冒险" \
  --max-turns 5 \
  --output continued_session.txt
```

### 4. `script` - 运行脚本

运行预定义的脚本或场景。

**语法**:
```bash
loom run script [OPTIONS] SCRIPT_NAME
```

**选项**:
- `--canon, -c PATH`: 规则文件路径
- `--params TEXT`: 脚本参数 (JSON 格式)
- `--output, -o PATH`: 输出文件路径
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**参数**:
- `SCRIPT_NAME`: 脚本名称或路径

**示例**:
```bash
# 运行内置脚本
loom run script "character_creation"

# 运行自定义脚本
loom run script ./my_script.py

# 带参数的脚本
loom run script "world_building" \
  --params '{"theme": "fantasy", "complexity": "medium"}'

# 指定规则文件
loom run script "combat_scenario" \
  --canon templates/rules/fantasy_basic.md \
  --output combat_log.txt
```

### 5. `test` - 测试运行

运行测试场景，验证规则和配置。

**语法**:
```bash
loom run test [OPTIONS]
```

**选项**:
- `--canon, -c PATH`: 规则文件路径 [必需]
- `--scenario TEXT`: 测试场景名称
- `--iterations INTEGER`: 测试迭代次数 [默认: 1]
- `--output, -o PATH`: 输出文件路径
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 基础测试
loom run test --canon templates/rules/fantasy_basic.md

# 特定场景测试
loom run test \
  --canon my_rules.md \
  --scenario "combat_test"

# 多次迭代测试
loom run test \
  --canon templates/rules/fantasy_basic.md \
  --iterations 10 \
  --output test_results.json
```

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
  --model "gpt-4" \
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
loom run batch \
  --canon templates/rules/fantasy_basic.md \
  --input test_inputs.txt \
  --output test_results.txt \
  --name "规则测试" \
  --max-turns 3 \
  --parallel 2

# 查看结果
cat test_results.txt
```

### 示例 3：继续复杂会话

```bash
# 查看现有会话
loom session list

# 继续会话
loom run continue \
  --session-name "龙之谷冒险" \
  --max-turns 10 \
  --output continued_adventure.txt

# 导出会话历史
loom export markdown \
  --session-name "龙之谷冒险" \
  --output adventure_history.md
```

### 示例 4：性能测试

```bash
# 创建性能测试脚本
cat > perf_test.py << 'EOF'
import asyncio
import time
from loom.core.session_manager import SessionManager

async def run_performance_test():
    start_time = time.time()
    
    # 初始化
    session_manager = SessionManager()
    session = await session_manager.create_session(
        name="性能测试",
        canon_path="templates/rules/fantasy_basic.md"
    )
    
    # 执行多个行动
    actions = [
        "测试行动1",
        "测试行动2", 
        "测试行动3"
    ]
    
    for i, action in enumerate(actions, 1):
        print(f"执行行动 {i}...")
        response = await session.execute_action(action)
        print(f"响应长度: {len(response)} 字符")
    
    # 计算性能指标
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n性能统计:")
    print(f"总时间: {total_time:.2f}秒")
    print(f"平均响应时间: {total_time/len(actions):.2f}秒/行动")
    
    await session.save()

asyncio.run(run_performance_test())
EOF

# 运行性能测试
python perf_test.py
```

## 高级功能

### 1. 自定义提示模板

```bash
# 创建自定义提示模板
cat > custom_prompt.txt << 'EOF'
你是一个专业的奇幻叙事者。

当前世界: {{world_name}}
当前场景: {{current_scene}}
玩家角色: {{player_character}}

请根据以上信息，以生动、详细的方式回应玩家的行动。
保持角色一致性，推动故事发展。

玩家行动: {{player_action}}
EOF

# 使用自定义提示运行
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --prompt-template custom_prompt.txt
```

### 2. 记忆系统集成

```bash
# 启用详细记忆日志
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --verbose \
  --debug-memory

# 查看记忆摘要
loom session show --session-name "测试会话" --include-memory
```

### 3. 多提供商故障转移

```bash
# 配置故障转移
loom config set llm.openai.fallback_enabled true
loom config set llm.openai.fallback_provider anthropic

# 运行会话，自动故障转移
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --provider openai \
  --fallback-enabled
```

## 故障排除

### 常见问题

#### 1. 会话启动失败
```bash
# 检查规则文件
loom rules validate --file templates/rules/fantasy_basic.md

# 检查提供商连接
loom config test --provider openai

# 查看详细日志
loom run interactive --verbose --log-level DEBUG
```

#### 2. 响应时间过长
```bash
# 减少最大令牌数
loom config set llm.openai.max_tokens 500

# 启用缓存
loom config set llm.openai.enable_caching true

# 使用更快的模型
loom run interactive --provider openai --model "gpt-3.5-turbo"
```

#### 3. 记忆问题
```bash
# 检查记忆系统
loom config test --memory

# 调整记忆容量
loom config set session.memory.short_term_capacity 50
loom config set session.memory.long_term_capacity 500

# 清理记忆缓存
rm -rf ./data/memory_cache
```

#### 4. 输出格式问题
```bash
# 检查输出编码
loom run batch --input test.txt --output test.out --encoding utf-8

# 验证输出格式
python -c "print(open('test.out', 'r', encoding='utf-8').read()[:100])"
```

## 最佳实践

### 1. 会话管理
- 为每个项目使用唯一的会话名称
- 定期保存重要会话
- 使用有意义的输出文件名

### 2. 性能优化
- 批处理时使用适当的并行度
- 启用缓存减少 API 调用
- 监控资源使用情况

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
