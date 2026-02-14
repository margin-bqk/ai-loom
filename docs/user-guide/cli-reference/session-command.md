# session 命令

## 概述

`session` 命令用于管理 LOOM 会话。它支持查看、搜索、删除、导出、导入会话等操作。

## 命令语法

```bash
loom session [OPTIONS] COMMAND [ARGS]...
```

## 子命令

### 1. `list` - 列出会话

列出所有可用的会话。

**语法**:
```bash
loom session list [OPTIONS]
```

**选项**:
- `--format, -f TEXT`: 输出格式 (table, json, yaml) [默认: table]
- `--limit INTEGER`: 显示数量限制
- `--offset INTEGER`: 偏移量
- `--sort-by TEXT`: 排序字段 (name, created_at, updated_at, turns)
- `--order TEXT`: 排序顺序 (asc, desc) [默认: desc]
- `--filter TEXT`: 过滤条件 (JSON 格式)
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 列出所有会话（表格格式）
loom session list

# 列出前10个会话
loom session list --limit 10

# 按创建时间升序排列
loom session list --sort-by created_at --order asc

# JSON 格式输出
loom session list --format json

# 过滤特定条件的会话
loom session list --filter '{"world": "fantasy", "turns": {"$gt": 5}}'

# 详细输出，包括元数据
loom session list --verbose
```

**输出示例** (表格格式):
```
┌─────────────────┬──────────────────────┬──────────┬────────────┬────────────┐
│ ID              │ Name                 │ Turns    │ Created    │ Updated    │
├─────────────────┼──────────────────────┼──────────┼────────────┼────────────┤
│ abc123-def456   │ 奇幻冒险             │ 15       │ 2024-01-15 │ 2024-01-15 │
│ ghi789-jkl012   │ 科幻探索             │ 8        │ 2024-01-14 │ 2024-01-14 │
│ mno345-pqr678   │ 测试会话             │ 3        │ 2024-01-13 │ 2024-01-13 │
└─────────────────┴──────────────────────┴──────────┴────────────┴────────────┘
```

### 2. `show` - 显示会话详情

显示特定会话的详细信息。

**语法**:
```bash
loom session show [OPTIONS]
```

**选项**:
- `--session-id TEXT`: 会话 ID
- `--session-name TEXT`: 会话名称
- `--format, -f TEXT`: 输出格式 (table, json, yaml, markdown) [默认: table]
- `--include-history`: 包括历史记录
- `--include-memory`: 包括记忆内容
- `--include-config`: 包括会话配置
- `--include-stats`: 包括统计信息
- `--limit-history INTEGER`: 历史记录限制 [默认: 10]
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 通过会话名称显示详情
loom session show --session-name "奇幻冒险"

# 通过会话 ID 显示详情
loom session show --session-id "abc123-def456"

# 包括历史记录
loom session show --session-name "奇幻冒险" --include-history

# 包括记忆内容
loom session show --session-name "奇幻冒险" --include-memory

# JSON 格式输出，包括所有信息
loom session show --session-name "奇幻冒险" \
  --format json \
  --include-history \
  --include-memory \
  --include-config \
  --include-stats

# Markdown 格式导出
loom session show --session-name "奇幻冒险" \
  --format markdown \
  --output session_report.md
```

### 3. `search` - 搜索会话

搜索包含特定内容的会话。

**语法**:
```bash
loom session search [OPTIONS] QUERY
```

**选项**:
- `--field TEXT`: 搜索字段 (all, name, history, memory, metadata) [默认: all]
- `--case-sensitive`: 区分大小写
- `--regex`: 使用正则表达式
- `--limit INTEGER`: 结果数量限制
- `--format, -f TEXT`: 输出格式 (table, json) [默认: table]
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**参数**:
- `QUERY`: 搜索查询

**示例**:
```bash
# 搜索名称包含"冒险"的会话
loom session search "冒险"

# 在历史记录中搜索特定内容
loom session search "龙" --field history

# 使用正则表达式搜索
loom session search "魔法|咒语" --regex

# 搜索元数据
loom session search '{"world": "fantasy"}' --field metadata

# JSON 格式输出
loom session search "宝藏" --format json --limit 5
```

### 4. `delete` - 删除会话

删除一个或多个会话。

**语法**:
```bash
loom session delete [OPTIONS]
```

**选项**:
- `--session-id TEXT`: 会话 ID
- `--session-name TEXT`: 会话名称
- `--all`: 删除所有会话
- `--older-than TEXT`: 删除早于指定时间的会话 (如: "7d", "30d", "2024-01-01")
- `--turns-less-than INTEGER`: 删除回合数少于指定值的会话
- `--dry-run`: 预览删除效果，不实际删除
- `--confirm`: 跳过确认提示
- `--help`: 显示帮助信息

**示例**:
```bash
# 删除特定会话（需要确认）
loom session delete --session-name "测试会话"

# 通过 ID 删除
loom session delete --session-id "abc123-def456"

# 删除所有会话（危险！）
loom session delete --all --confirm

# 删除7天前的会话
loom session delete --older-than "7d"

# 删除回合数少于3的会话
loom session delete --turns-less-than 3

# 预览删除效果
loom session delete --older-than "30d" --dry-run
```

### 5. `export` - 导出会话

导出会话到文件。

**语法**:
```bash
loom session export [OPTIONS]
```

**选项**:
- `--session-id TEXT`: 会话 ID
- `--session-name TEXT`: 会话名称
- `--output, -o PATH`: 输出文件路径 [必需]
- `--format, -f TEXT`: 导出格式 (json, yaml, markdown, html) [默认: json]
- `--include-history`: 包括历史记录
- `--include-memory`: 包括记忆内容
- `--include-config`: 包括会话配置
- `--compress`: 压缩输出文件
- `--pretty`: 美化输出（JSON/YAML）
- `--help`: 显示帮助信息

**示例**:
```bash
# 导出会话为 JSON
loom session export \
  --session-name "奇幻冒险" \
  --output adventure.json

# 导出为 Markdown，包括历史
loom session export \
  --session-name "奇幻冒险" \
  --output adventure.md \
  --format markdown \
  --include-history

# 导出为 HTML 报告
loom session export \
  --session-name "奇幻冒险" \
  --output report.html \
  --format html \
  --include-history \
  --include-memory \
  --include-config

# 压缩导出
loom session export \
  --session-name "大型会话" \
  --output session.json.gz \
  --compress
```

### 6. `import` - 导入会话

从文件导入会话。

**语法**:
```bash
loom session import [OPTIONS]
```

**选项**:
- `--file, -f PATH`: 导入文件路径 [必需]
- `--name TEXT`: 新会话名称（覆盖原名称）
- `--format TEXT`: 文件格式 (auto, json, yaml) [默认: auto]
- `--merge`: 合并到现有会话（如果存在）
- `--overwrite`: 覆盖现有会话
- `--dry-run`: 预览导入效果
- `--help`: 显示帮助信息

**示例**:
```bash
# 导入 JSON 会话文件
loom session import --file adventure.json

# 导入并重命名
loom session import --file backup.json --name "恢复的冒险"

# 导入 Markdown 文件
loom session import --file session.md --format markdown

# 合并到现有会话
loom session import --file updates.json --merge

# 预览导入
loom session import --file large_session.json --dry-run
```

### 7. `stats` - 会话统计

显示会话统计信息。

**语法**:
```bash
loom session stats [OPTIONS]
```

**选项**:
- `--session-id TEXT`: 会话 ID
- `--session-name TEXT`: 会话名称
- `--all`: 所有会话的统计
- `--time-range TEXT`: 时间范围 (today, week, month, year, all) [默认: all]
- `--format, -f TEXT`: 输出格式 (table, json, chart) [默认: table]
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 特定会话的统计
loom session stats --session-name "奇幻冒险"

# 所有会话的统计
loom session stats --all

# 本周的会话统计
loom session stats --all --time-range week

# JSON 格式输出
loom session stats --all --format json

# 图表输出
loom session stats --all --format chart
```

**统计输出示例**:
```
会话统计 (总计: 15 个会话)
========================================

基本统计:
- 总回合数: 127
- 平均回合数: 8.5
- 最长会话: 25 回合 ("史诗冒险")
- 最短会话: 1 回合 ("快速测试")

时间分布:
- 今天: 2 个会话
- 本周: 8 个会话
- 本月: 15 个会话

世界类型分布:
- 奇幻: 10 个会话 (66.7%)
- 科幻: 3 个会话 (20.0%)
- 现代: 2 个会话 (13.3%)

活跃度:
- 活跃会话: 3 个
- 最近活动: 2 小时前
```

### 8. `cleanup` - 清理会话

清理会话数据，如临时文件、缓存等。

**语法**:
```bash
loom session cleanup [OPTIONS]
```

**选项**:
- `--session-id TEXT`: 会话 ID
- `--session-name TEXT`: 会话名称
- `--all`: 清理所有会话
- `--temp-files`: 清理临时文件
- `--cache`: 清理缓存
- `--orphaned`: 清理孤儿数据
- `--dry-run`: 预览清理效果
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 清理特定会话的临时文件
loom session cleanup --session-name "测试会话" --temp-files

# 清理所有会话的缓存
loom session cleanup --all --cache

# 清理孤儿数据
loom session cleanup --orphaned

# 预览清理效果
loom session cleanup --all --dry-run --verbose
```

### 9. `migrate` - 迁移会话

迁移会话到新格式或新版本。

**语法**:
```bash
loom session migrate [OPTIONS]
```

**选项**:
- `--session-id TEXT`: 会话 ID
- `--session-name TEXT`: 会话名称
- `--all`: 迁移所有会话
- `--from-version TEXT`: 源版本
- `--to-version TEXT`: 目标版本 [默认: current]
- `--backup`: 创建备份
- `--dry-run`: 预览迁移效果
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 迁移特定会话
loom session migrate --session-name "旧会话"

# 迁移所有会话到新版本
loom session migrate --all --to-version "2.0.0"

# 从特定版本迁移
loom session migrate --all --from-version "1.5.0" --to-version "2.0.0"

# 迁移并创建备份
loom session migrate --all --backup

# 预览迁移
loom session migrate --all --dry-run
```

### 10. `analyze` - 分析会话

分析会话内容，提取洞察。

**语法**:
```bash
loom session analyze [OPTIONS]
```

**选项**:
- `--session-id TEXT`: 会话 ID
- `--session-name TEXT`: 会话名称
- `--all`: 分析所有会话
- `--analysis-type TEXT`: 分析类型 (topics, entities, sentiment, structure)
- `--output, -o PATH`: 输出文件路径
- `--format, -f TEXT`: 输出格式 (table, json, report) [默认: table]
- `--verbose, -v`: 详细输出
- `--help`: 显示帮助信息

**示例**:
```bash
# 分析特定会话的主题
loom session analyze --session-name "奇幻冒险" --analysis-type topics

# 分析所有会话的实体
loom session analyze --all --analysis-type entities

# 情感分析
loom session analyze --session-name "对话测试" --analysis-type sentiment

# 生成分析报告
loom session analyze --all --output analysis_report.json --format json
```

## 会话文件格式

### JSON 格式示例

```json
{
  "session": {
    "id": "abc123-def456",
    "name": "奇幻冒险",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:45:00Z",
    "turns": 15,
    "config": {
      "canon": "templates/rules/fantasy_basic.md",
      "provider": "openai",
      "model": "gpt-3.5-turbo"
    }
  },
  "history": [
    {
      "turn": 1,
      "player": "我来到风语镇",
      "response": "欢迎来到风语镇...",
      "timestamp": "2024-01-15T10:31:00Z"
    }
  ],
  "memory": {
    "short_term": ["玩家在风语镇", "寻找工作"],
    "long_term": ["世界背景: 奇幻中世纪"]
  },
  "metadata": {
    "world": "fantasy",
    "characters": ["玩家", "镇长", "铁匠"],
    "locations": ["风语镇", "铁匠铺"]
  }
}
```

### Markdown 格式示例

```markdown
# 会话: 奇幻冒险

**ID**: abc123-def456
**创建时间**: 2024-01-15 10:30:00
**更新时间**: 2024-01-15 11:45:00
**回合数**: 15

## 配置
- **规则文件**: templates/rules/fantasy_basic.md
- **LLM 提供商**: openai (gpt-3.5-turbo)

## 历史记录

### 回合 1
**玩家**: 我来到风语镇
**响应**: 欢迎来到风语镇，这是一个位于...

### 回合 2
**玩家**: 我想找一份工作
**响应**: 风语镇有几个地方可能需要帮手...

## 记忆摘要
- 短期记忆: 玩家在风语镇，寻找工作
- 长期记忆: 世界背景: 奇幻中世纪
```

## 使用示例

### 示例 1：会话管理工作流

```bash
# 1. 查看所有会话
loom session list

# 2. 查看特定会话详情
loom session show --session-name "奇幻冒险" --include-history

# 3. 导出会话备份
loom session export \
  --session-name "奇幻冒险" \
  --output backup_20240115.json \
  --format json \
  --include-history \
  --include-memory

# 4. 清理旧会话
loom session delete --older-than "30d"

# 5. 查看统计
loom session stats --all
```

### 示例 2：批量处理会话

```bash
# 导出所有奇幻世界会话
for session in $(loom session list --filter '{"world": "fantasy"}' --format json | jq -r '.[].id'); do
  loom session export \
    --session-id "$session" \
    --output "fantasy_sessions/session_${session}.json"
done

# 批量导入会话
for file in backup/*.json; do
  loom session import --file "$file" --name "恢复_$(basename "$file" .json)"
done

# 批量分析
loom session analyze --all --output analysis.json --format json
```

### 示例 3：会话恢复和继续

```bash
# 1. 查找中断的会话
loom session list --filter '{"status": "interrupted"}'

# 2. 查看会话状态
loom session show --session-name "中断的冒险" --include-history

# 3. 导出当前状态
loom session export --session-name "中断的冒险" --output checkpoint.json

# 4. 修复问题后继续
loom run continue --session-name "中断的冒险" --max-turns 10

# 5. 验证恢复
