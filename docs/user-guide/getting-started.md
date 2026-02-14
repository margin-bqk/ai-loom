# LOOM 用户指南

## 目录

1. [简介](#简介)
2. [安装指南](#安装指南)
   - [系统要求](#系统要求)
   - [安装步骤](#安装步骤)
   - [验证安装](#验证安装)
3. [快速开始](#快速开始)
   - [创建第一个世界](#创建第一个世界)
   - [运行第一个会话](#运行第一个会话)
   - [基本交互](#基本交互)
4. [核心概念](#核心概念)
   - [非承载式架构](#非承载式架构)
   - [叙事失明](#叙事失明)
   - [五层架构](#五层架构)
5. [CLI 工具使用](#cli-工具使用)
   - [常用命令](#常用命令)
   - [会话管理](#会话管理)
   - [规则管理](#规则管理)
   - [玩家干预](#玩家干预)
6. [Web 界面使用](#web-界面使用)
   - [启动 Web 服务器](#启动-web-服务器)
   - [界面功能](#界面功能)
   - [实时监控](#实时监控)
7. [规则编写指南](#规则编写指南)
   - [规则文件结构](#规则文件结构)
   - [规则语法](#规则语法)
   - [最佳实践](#最佳实践)
8. [世界构建教程](#世界构建教程)
   - [奇幻世界构建](#奇幻世界构建)
   - [科幻世界构建](#科幻世界构建)
   - [现实世界构建](#现实世界构建)
9. [高级功能](#高级功能)
   - [多 LLM 提供商](#多-llm-提供商)
   - [插件系统](#插件系统)
   - [性能优化](#性能优化)
10. [故障排除](#故障排除)
    - [常见问题](#常见问题)
    - [错误代码](#错误代码)
    - [获取帮助](#获取帮助)

## 简介

LOOM（Language-Oriented Open Mythos）是一个基于 Markdown 规则的非承载式叙事引擎，专为 AI 驱动的角色扮演和互动叙事设计。本指南将帮助您从零开始使用 LOOM，创建和管理您的叙事世界。

## 安装指南

### 系统要求

- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.10 或更高版本
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 500MB 可用空间
- **网络**: 用于访问 LLM API（可选本地模型）

### 安装步骤

#### 方法一：从源码安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/your-org/loom.git
cd loom

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

#### 方法二：使用 pip 安装（如果已发布到 PyPI）

```bash
# 从 PyPI 安装（如果已发布）
# pip install loom

# 注意：当前版本建议从源码安装以获得最新功能
```

#### 方法三：使用 Docker

```bash
# 拉取镜像
docker pull loom/loom:latest

# 运行容器
docker run -p 8000:8000 -v ./data:/app/data loom/loom:latest
```

### 验证安装

```bash
# 检查版本
loom --version

# 查看帮助
loom --help

# 运行测试
loom dev test
```

## 快速开始

### 创建第一个世界

1. **初始化项目**

```bash
# 创建新世界
loom init my_first_world --type fantasy

# 进入项目目录
cd my_first_world
```

2. **查看生成的文件**

```
my_first_world/
├── canon/
│   ├── world.md          # 世界观定义
│   ├── tone.md           # 叙事基调
│   ├── conflict.md       # 冲突解决
│   ├── permissions.md    # 权限边界
│   └── causality.md      # 因果关系
├── config/
│   └── world_config.yaml # 世界配置
└── sessions/             # 会话存储
```

3. **编辑规则文件**

编辑 `canon/world.md`：

```markdown
# 世界观

## 地理环境
- 大陆名称：艾瑟兰
- 主要地形：森林、山脉、河流
- 气候：温带海洋性气候

## 社会结构
- 主要种族：人类、精灵、矮人
- 政治体制：封建王国制
- 经济体系：农业和手工业为主

## 魔法系统
- 魔法类型：元素魔法、神圣魔法、自然魔法
- 魔法限制：需要魔力，有反噬风险
- 魔法学习：通过学习和实践掌握
```

### 运行第一个会话

1. **启动会话**

```bash
# 使用默认规则运行
loom run

# 使用特定角色
loom run --character "冒险者"

# 使用自定义规则
loom run --canon canon/custom_rules.md
```

2. **交互示例**

```
LOOM> 欢迎来到艾瑟兰大陆！你是一名年轻的冒险者，站在森林边缘。
你> 我观察周围环境
LOOM> 你看到茂密的森林，远处有山脉轮廓，一条小路通向森林深处。
你> 我沿着小路前进
LOOM> 你沿着小路前进，听到鸟鸣声，阳光透过树叶洒在地上。
```

3. **保存和加载会话**

```bash
# 查看所有会话
loom session list

# 保存当前会话
loom session save --name "森林冒险"

# 加载会话
loom session load --id "session_123"
```

### 基本交互

#### 玩家输入格式

- **普通叙事**: `我打开门`
- **OOC 注释**: `(OOC: 我想检查门后是否有陷阱)`
- **世界编辑**: `[EDIT: 门后有一个宝箱]`
- **Retcon**: `[RETCON: 修正时间线，门应该是锁着的]`
- **意图声明**: `[INTENT: 探索地下城]`

#### 常用快捷键

- `Ctrl+C`: 暂停会话
- `Ctrl+D`: 退出会话
- `Ctrl+R`: 重新加载规则
- `Ctrl+S`: 快速保存

## 核心概念

### 非承载式架构

LOOM 采用非承载式架构，意味着：

1. **规则与代码分离**: 游戏规则完全存储在 Markdown 文件中
2. **框架中立**: 引擎不包含任何硬编码的游戏逻辑
3. **可移植性**: 规则文件可以在不同版本的 LOOM 中使用
4. **可读性**: 规则是人类可读的，不需要编程知识

### 叙事失明

叙事失明是 LOOM 的核心设计原则：

1. **不解析内容**: 引擎不解析规则的具体内容
2. **仅传递文本**: 将规则文本传递给 LLM 进行解释
3. **无状态设计**: 核心层不存储叙事状态
4. **一致性优先**: 通过 LLM 确保叙事一致性

### 五层架构

LOOM 采用五层架构设计：

| 层级 | 职责 | 关键组件 |
|------|------|----------|
| 运行时核心层 | 生命周期管理、调度、持久化 | SessionManager, TurnScheduler |
| 规则层 | Markdown 规则解析和加载 | RuleLoader, MarkdownCanon |
| 解释层 | LLM 推理和规则解释 | RuleInterpreter, LLMProvider |
| 世界记忆层 | 结构化状态存储 | WorldMemory, MemorySummarizer |
| 玩家干预层 | 玩家输入解析和处理 | PlayerIntervention, WorldEditor |

## CLI 工具使用

### 常用命令

#### 项目管理

```bash
# 创建新项目
loom init <project_name> [--type <world_type>]

# 列出所有项目
loom project list

# 删除项目
loom project delete <project_name>
```

#### 会话管理

```bash
# 启动新会话
loom run [--canon <rules_file>] [--character <character_name>]

# 列出所有会话
loom session list [--project <project_name>]

# 加载会话
loom session load --id <session_id>

# 导出会话
loom session export --id <session_id> --format <json|markdown|pdf>

# 删除会话
loom session delete --id <session_id>
```

#### 规则管理

```bash
# 验证规则
loom rules validate --file <rules_file>

# 比较规则版本
loom rules diff <file1> <file2>

# 创建规则模板
loom rules template --type <fantasy|scifi|modern>

# 检查规则一致性
loom rules check --all
```

#### 玩家干预

```bash
# 应用干预
loom intervention apply --type <ooc|edit|retcon> --content "<content>"

# 查看干预历史
loom intervention history [--session <session_id>]

# 撤销干预
loom intervention undo [--id <intervention_id>]
```

#### 开发工具

```bash
# 启动开发服务器
loom dev [--reload] [--port <port>]

# 运行测试
loom dev test [--coverage]

# 生成文档
loom dev docs [--format <html|pdf>]

# 性能分析
loom dev profile [--duration <seconds>]
```

### 会话管理详细指南

#### 创建和配置会话

```bash
# 创建带配置的会话
loom run \
  --canon canon/fantasy_world.md \
  --character "艾莉亚" \
  --llm-provider openai \
  --model gpt-4 \
  --temperature 0.7 \
  --max-tokens 1000

# 使用配置文件
loom run --config config/session_config.yaml
```

#### 会话状态管理

```bash
# 查看会话详情
loom session info --id <session_id>

# 查看会话统计
loom session stats --id <session_id>

# 备份会话
loom session backup --id <session_id> --output backup/

# 恢复会话
loom session restore --file <backup_file>
```

#### 批量操作

```bash
# 批量导出会话
loom session export-all --project <project_name> --format json

# 批量删除旧会话
loom session cleanup --days 30

# 批量运行测试场景
loom session batch-run --scenarios scenarios/
```

### 规则管理详细指南

#### 规则验证

```bash
# 基本验证
loom rules validate --file canon/world.md

# 详细验证报告
loom rules validate --file canon/world.md --verbose --output report.json

# 验证所有规则文件
loom rules validate --all --project <project_name>
```

#### 规则版本控制

```bash
# 初始化 Git 仓库
loom rules git-init

# 提交更改
loom rules git-commit --message "更新世界观"

# 查看历史
loom rules git-log

# 回滚到特定版本
loom rules git-rollback --commit <commit_hash>
```

#### 规则模板系统

```bash
# 列出可用模板
loom rules template-list

# 从模板创建规则
loom rules template-create --type fantasy --output canon/fantasy_world.md

# 自定义模板
loom rules template-custom --file my_template.md --name "我的模板"
```

## Web 界面使用

### 启动 Web 服务器

```bash
# 基本启动
loom web

# 自定义配置
loom web \
  --port 8080 \
  --host 0.0.0.0 \
  --debug \
  --reload

# 使用 SSL
loom web \
  --ssl-cert cert.pem \
  --ssl-key key.key \
  --port 443
```

### 界面功能

#### 仪表板

- **会话概览**: 显示所有活跃和历史的会话
- **性能指标**: 实时显示系统性能数据
- **成本跟踪**: 跟踪 LLM API 使用成本
- **系统状态**: 显示服务器健康状态

#### 规则编辑器

- **实时编辑**: 在线编辑规则文件
- **语法高亮**: Markdown 语法高亮
- **实时预览**: 规则效果预览
- **版本对比**: 不同版本规则对比

#### 会话管理器

- **会话创建**: 创建新会话
- **实时交互**: 与 AI 实时对话
- **记忆浏览**: 查看和编辑记忆
- **干预管理**: 应用和管理玩家干预

#### 记忆浏览器

- **实体查看**: 查看所有记忆实体
- **关系图**: 可视化实体关系
- **搜索功能**: 全文搜索记忆
- **导出功能**: 导出记忆数据

### 实时监控

#### 性能监控

```bash
# 查看性能指标
curl http://localhost:8000/metrics

# 监控 API
curl http://localhost:8000/api/v1/monitoring/health
```

#### 日志查看

```bash
# 实时查看日志
loom web --log-level DEBUG --log-file logs/app.log

# 日志分析
loom dev logs --analyze --file logs/app.log
```

## 规则编写指南

### 规则文件结构

#### 标准章节

```markdown
# 世界观
<!-- 世界的基本设定 -->

# 叙事基调
<!-- 故事的风格和情感基调 -->

# 冲突解决
<!-- 如何处理冲突和挑战 -->

# 权限边界
<!-- 玩家可以/不可以做什么 -->

# 因果关系
<!-- 世界的物理和逻辑规则 -->

# 元信息
<!-- 规则的元数据 -->
```

#### 扩展章节

```markdown
# 角色指南
<!-- 角色创建和发展指南 -->

# 物品系统
<!-- 物品和装备规则 -->

# 魔法/科技系统
<!-- 特殊能力系统 -->

# 经济系统
<!-- 货币和交易规则 -->

# 时间系统
<!-- 时间和季节规则 -->
```

### 规则语法

#### 基本语法

```markdown
# 标题
## 子标题
### 小标题

- 列表项
- 另一个列表项

1. 有序列表
2. 第二项

**粗体** *斜体* ~~删除线~~

> 引用块

`行内代码`

```代码块
def function():
    pass
```

#### LOOM 扩展语法

```markdown
::: rule
类型: permission
内容: 玩家可以施放魔法
优先级: 3
:::

::: constraint
类型: causality
内容: 时间只能向前流动
不可违反: true
:::

::: entity
类型: character
名称: 艾莉亚
描述: 年轻的法师学徒
属性:
  力量: 8
  智力: 16
  魅力: 12
:::
```

#### 条件规则

```markdown
::: conditional
条件: 当玩家在战斗中时
规则:
  - 每回合只能进行一次攻击
  - 防御动作消耗额外行动点
:::
```

### 最佳实践

#### 规则编写原则

1. **清晰明确**: 使用简单直接的语言
2. **一致性**: 保持术语和概念一致
3. **模块化**: 将相关规则分组
4. **可扩展**: 为未来扩展留出空间
5. **可测试**: 编写可验证的规则

#### 示例规则文件

```markdown
# 世界观

## 世界设定
- 世界名称：艾瑟兰大陆
- 时代：中世纪奇幻
- 主要种族：人类、精灵、矮人、兽人

## 地理环境
- 大陆被分为五个王国
- 中央山脉分隔东西大陆
- 北方寒冷，南方温暖

# 叙事基调

## 整体风格
- 黑暗奇幻，带有希望元素
- 强调角色成长和选择
- 道德灰色地带

## 情感基调
- 紧张刺激的战斗场景
- 温馨的角色互动时刻
- 史诗般的冒险旅程

# 冲突解决

## 战斗规则
- 回合制战斗系统
- 基于属性的成功率计算
- 环境因素影响战斗

## 社交冲突
- 基于魅力的说服系统
- 派系关系影响对话
- 长期关系发展

# 权限边界

## 玩家权限
- 可以探索任何已发现区域
- 可以与任何 NPC 对话
- 可以学习任何可用的技能

## 玩家限制
- 不能无故杀死重要 NPC
- 不能违反世界物理规则
- 不能进行时间旅行

# 因果关系

## 物理规则
- 重力与地球相似
- 魔法需要消耗魔力
- 死亡通常是永久的

## 逻辑规则
- 时间线性流动
- 因果必须合理
- 记忆连续性保持

# 元信息

版本: 1.0.0
作者: 你的名字
创建日期: 2025-12-31
最后更新: 2025-12-31
兼容性: LOOM v1.0+
```

## 世界构建教程

### 奇幻世界构建

#### 步骤 1：基础设定

```markdown
# 世界观

## 核心概念
- 魔法是世界的自然力量
- 多种智慧种族共存
- 古老的神祇影响世界

## 历史背景
- 创世神话：元素之神创造世界
- 古代文明：魔法帝国兴衰
- 现代时代：王国争霸时期
```

#### 步骤 2：种族设计

```markdown
## 主要种族

### 人类
- 适应性最强
- 短寿但繁殖快
- 擅长技术和贸易

### 精灵
- 长寿优雅
- 与自然和谐共生
- 擅长魔法和弓箭

### 矮人
- 坚韧强壮
- 居住在山脉中
- 擅长锻造和采矿
```

#### 步骤 3：魔法系统

```markdown
## 魔法体系

### 魔法类型
1. **元素魔法**: 控制火、水、土、风
2. **神圣魔法**: 治疗、祝福、驱邪
3. **自然魔法**: 植物、动物、天气
4. **黑暗魔法**: 诅咒
