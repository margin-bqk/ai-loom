# LOOM CLI 使用指南

LOOM 命令行界面提供了完整的系统管理功能，支持会话管理、规则编辑、世界运行等核心操作。

## 0. 状态说明

> **注意**: 本文档描述了LOOM CLI的完整功能集。部分功能在当前版本(v0.10.1)中尚未实现，已用 `[未实现]` 标记。请使用 `loom --help` 查看实际可用的命令。

**当前已实现的命令**:
- `run` - 运行世界会话
- `session` - 会话管理
- `rules` - 规则管理（部分功能）
- `config` - 配置管理
- `export` - 数据导出（部分功能）
- `dev` - 开发工具
- `init` - 项目初始化
- `status` - 系统状态
- `version` - 版本信息
- `help` - 帮助信息

**计划中的命令** (标记为 `[未实现]`):
- `world` - 世界管理
- `memory` - 记忆管理
- `intervention` - 玩家干预
- `plugins` - 插件管理
- `script` - 脚本模式
- `batch` - 批处理模式
- `remote` - 远程操作

## 1. 安装和配置

### 1.1 安装
```bash
# 从源码安装（推荐用于开发）
pip install -e .

# 或安装开发版本（包含测试工具）
pip install -e ".[dev]"

# 从 PyPI 安装（如果已发布）
# pip install loom
```

### 1.2 配置
```bash
# 查看当前配置
loom config show

# 设置配置项
loom config set llm_providers.openai.api_key "your_api_key_here"
loom config set llm_providers.anthropic.api_key "your_api_key_here"

# 验证配置
loom config validate

# 测试 LLM 提供商连接
loom config test --provider openai
```

## 2. 基本命令

### 2.1 帮助系统
```bash
# 查看所有命令
loom --help

# 查看特定命令帮助
loom run --help
loom session --help
loom rules --help
```

### 2.2 版本信息
```bash
# 查看版本
loom version

# 查看系统信息
loom dev info
```

## 3. 会话管理

### 3.1 创建和运行会话
```bash
# 创建新会话（交互式）
loom run --world fantasy_world --character "艾莉亚"

# 使用特定规则集
loom run --world sci_fi_world --character "船长" --rules rules/space_rules.md

# 批量运行
loom run --batch --scenario "任务开始" --output sessions/batch_results.json
```

### 3.2 会话列表和查看
```bash
# 列出所有会话
loom session list

# 查看会话详情
loom session show session_id_here

# 查看会话历史
loom session history session_id_here --limit 10
```

### 3.3 会话控制
```bash
# 暂停会话
loom session pause session_id_here

# 继续会话
loom session resume session_id_here

# 结束会话
loom session end session_id_here

# 删除会话
loom session delete session_id_here
```

### 3.4 会话导出
```bash
# 导出为 JSON
loom session export session_id_here --format json --output session.json

# 导出为 Markdown
loom session export session_id_here --format markdown --output session.md

# 导出为 YAML
loom session export session_id_here --format yaml --output session.yaml
```

## 4. 规则管理

### 4.1 规则加载和查看
```bash
# 加载规则集
loom rules load --canon fantasy_basic --format table

# 列出所有规则集
loom rules list --recursive --format table

# 查看规则详情
loom rules load --canon fantasy_basic --format json
```

### 4.2 规则验证
```bash
# 验证单个规则集
loom rules validate --canon fantasy_basic

# 验证所有规则集
loom rules validate

# 尝试自动修复问题
loom rules validate --canon fantasy_basic --fix
```

### 4.3 规则创建
```bash
# 创建新规则集
loom rules create --name "奇幻世界基础规则" --template fantasy

# 使用特定模板创建
loom rules create --name "科幻世界规则" --template scifi

# 强制覆盖现有文件
loom rules create --name "我的规则" --template default --force
```

### 4.4 注意事项
- 当前版本仅支持上述命令，更多功能（如规则编辑、应用、移除）计划在后续版本中实现
- 使用 `loom rules --help` 查看完整的参数说明

## 5. 世界管理 [未实现]

### 5.1 世界创建和配置
```bash
# 创建新世界
loom world create --name "艾瑟兰大陆" --type fantasy --config config/world_config.yaml

# 导入世界配置
loom world import --file world_export.json

# 导出世界配置
loom world export fantasy_world --format yaml --output world_config.yaml
```

### 5.2 世界列表和查看
```bash
# 列出所有世界
loom world list

# 查看世界详情
loom world show fantasy_world

# 查看世界统计
loom world stats fantasy_world
```

### 5.3 世界编辑
```bash
# 添加角色
loom world add-character fantasy_world --name "雷纳德" --role "导师"

# 添加地点
loom world add-location fantasy_world --name "法师塔" --type "建筑"

# 更新世界描述
loom world update fantasy_world --description "一个充满魔法与冒险的奇幻世界"
```

## 6. 记忆管理 [未实现]

### 6.1 记忆查询
```bash
# 查询会话记忆
loom memory query session_id_here --query "龙之袭击"

# 查看角色关系
loom memory relationships session_id_here --character "艾莉亚"

# 查看时间线
loom memory timeline session_id_here --limit 20
```

### 6.2 记忆操作
```bash
# 添加记忆
loom memory add session_id_here --content "艾莉亚学会了火球术" --type "技能学习"

# 更新记忆
loom memory update memory_id_here --content "修正后的记忆内容"

# 删除记忆
loom memory delete memory_id_here
```

### 6.3 记忆导出
```bash
# 导出所有记忆
loom memory export session_id_here --format json --output memories.json

# 导出记忆总结
loom memory summarize session_id_here --output summary.md
```

## 7. 玩家干预 [未实现]

### 7.1 干预操作
```bash
# 查看可用的干预类型
loom intervention list-types

# 应用重述干预
loom intervention apply session_id_here --type retcon --description "修正时间线错误"

# 应用编辑干预
loom intervention apply session_id_here --type edit --target "场景描述" --content "新的描述内容"
```

### 7.2 干预历史
```bash
# 查看干预历史
loom intervention history session_id_here

# 撤销干预
loom intervention undo session_id_here --intervention-id intervention_id_here

# 查看干预影响
loom intervention impact session_id_here --intervention-id intervention_id_here
```

## 8. 数据导出

### 8.1 导出单个会话
```bash
# 导出为 JSON（默认）
loom export session session_id_here --format json

# 导出为 YAML
loom export session session_id_here --format yaml

# 导出为 CSV
loom export session session_id_here --format csv

# 包含记忆数据
loom export session session_id_here --format json --include-memory

# 指定输出文件
loom export session session_id_here --output my_session.json
```

### 8.2 导出所有会话
```bash
# 导出所有会话为 JSON
loom export sessions --output sessions_export.json

# 按状态过滤导出
loom export sessions --status active --format yaml

# 导出为 CSV 格式
loom export sessions --format csv --output sessions.csv
```

### 8.3 注意事项
- 当前版本支持 JSON、YAML、CSV 格式
- Markdown 和 PDF 格式计划在后续版本中实现
- 批量导出功能 (`export-batch`, `export-world`) 尚未实现
- 使用 `loom export --help` 查看完整的参数说明

## 9. 开发工具

### 9.1 调试工具
```bash
# 进入调试模式
loom dev debug --session session_id_here

# 查看系统日志
loom dev logs --level DEBUG --lines 100

# 性能分析
loom dev profile --session session_id_here --duration 30
```

### 9.2 测试工具
```bash
# 运行单元测试
loom dev test --unit

# 运行集成测试
loom dev test --integration

# 运行特定测试
loom dev test --file tests/test_core/test_session_manager.py

# 生成测试报告
loom dev test --coverage --report html
```

### 9.3 维护工具
```bash
# 清理临时文件
loom dev cleanup --temp --cache

# 检查数据库完整性
loom dev check-db

# 备份数据
loom dev backup --output backup_$(date +%Y%m%d).zip

# 恢复数据
loom dev restore --file backup_20241230.zip
```

## 10. 插件管理 [未实现]

### 10.1 插件操作
```bash
# 列出所有插件
loom plugins list

# 查看插件详情
loom plugins show plugin_name

# 启用/禁用插件
loom plugins enable plugin_name
loom plugins disable plugin_name

# 重新加载插件
loom plugins reload
```

### 10.2 插件开发
```bash
# 创建新插件模板
loom plugins new --name my_plugin --type rule

# 测试插件
loom plugins test plugin_name

# 打包插件
loom plugins package plugin_name --output my_plugin.zip
```

## 11. 高级功能 [未实现]

### 11.1 脚本模式 [未实现]
```bash
# 运行脚本文件
loom script run scripts/my_script.loom

# 创建脚本模板
loom script new --name adventure_script --template basic

# 调试脚本
loom script debug scripts/my_script.loom --step-by-step
```

### 11.2 批处理模式 [未实现]
```bash
# 从文件读取命令
loom batch --file commands.txt

# 交互式批处理
loom batch --interactive

# 并行处理
loom batch --file jobs.txt --parallel 4
```

### 11.3 远程操作 [未实现]
```bash
# 连接到远程服务器
loom remote connect --url http://remote-server:8000 --api-key your_key

# 执行远程命令
loom remote exec --command "session list"

# 同步数据
loom remote sync --direction both
```

## 12. 配置管理

### 12.1 配置文件
```bash
# 查看配置路径
loom config path

# 编辑配置文件
loom config edit

# 重置配置
loom config reset

# 导入配置
loom config import --file config_backup.yaml
```

### 12.2 环境设置
```bash
# 设置环境变量
loom config set-env OPENAI_API_KEY your_key_here

# 查看环境变量
loom config get-env

# 切换环境
loom config use-environment production
```

## 13. 实用技巧

### 13.1 快捷键
- `Ctrl+C`: 中断当前操作
- `Ctrl+D`: 退出交互模式
- `Tab`: 命令补全
- `↑/↓`: 历史命令导航

### 13.2 输出格式
```bash
# JSON 输出（机器可读）
loom session list --format json

# 表格输出（人类可读）
loom session list --format table

# CSV 输出
loom session list --format csv

# 自定义输出
loom session list --format "{{.ID}} - {{.World}}"
```

### 13.3 日志控制
```bash
# 设置日志级别
loom --log-level DEBUG run --world fantasy_world

# 输出到文件
loom --log-file loom.log run --world fantasy_world

# 彩色输出
loom --color always session list

# 无颜色输出（用于脚本）
loom --color never session list
```

## 14. 故障排除

### 14.1 常见问题
```bash
# 检查连接
loom dev ping

# 查看系统状态
loom dev status

# 诊断问题
loom dev diagnose

# 重置状态
loom dev reset --soft
```

### 14.2 错误处理
```bash
# 详细错误信息
loom --verbose run --world invalid_world

# 调试模式
loom --debug session show invalid_session

# 忽略错误继续执行
loom --continue-on-error batch --file commands.txt
```

## 15. 示例工作流

### 15.1 创建和运行奇幻冒险
```bash
# 1. 创建世界
loom world create --name "龙之国度" --type fantasy

# 2. 添加角色
loom world add-character "龙之国度" --name "勇士" --role "主角"

# 3. 创建规则
loom rules new --name "龙之规则" --template fantasy

# 4. 开始冒险
loom run --world "龙之国度" --character "勇士" --scenario "开始冒险"

# 5. 导出结果
loom export latest --format markdown --output adventure.md
```

### 15.2 批量处理会话
```bash
# 1. 创建批处理文件
echo "run --world sci_fi --character 船长 --scenario 任务开始" > batch.txt
echo "run --world fantasy --character 法师 --scenario 魔法测试" >> batch.txt

# 2. 执行批处理
loom batch --file batch.txt --parallel 2

# 3. 导出所有结果
loom export-batch --all --format json --output-dir results/
```

## 16. 获取帮助

### 16.1 内置帮助
```bash
# 查看所有可用命令
loom help --all

# 搜索命令
loom help search "export"

# 查看示例
loom help examples
```

### 16.2 在线资源
- [完整文档](https://docs.loom.dev)
- [API 参考](https://api.loom.dev)
- [示例仓库](https://github.com/loom-project/examples)
- [社区论坛](https://community.loom.dev)

### 16.3 支持渠道
```bash
# 报告问题
loom dev report-issue --description "详细描述问题"

# 请求功能
loom dev request-feature --description "功能描述"

# 查看已知问题
loom dev known-issues
```

---

*本指南将持续更新。使用 `loom version` 查看当前版本，使用 `loom help` 获取最新命令信息。*
