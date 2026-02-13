![Loom Github Card](asset\LOOM-github-card.png)
# LOOM - Language-Oriented Open Mythos

> [!WARNING]
> 

![Vibe Coding](https://img.shields.io/badge/Vibe-Coding-8B5CF6)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests Status](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/your-org/loom/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green)](https://github.com/your-org/loom/actions)

**LOOM** 是一个语言驱动的开放叙事解释器运行时，专为 AI 驱动的角色扮演和互动叙事设计。

## ✨ 核心理念

LOOM 采用 **非承载式架构**，将叙事规则完全从框架代码中分离出来。规则以纯 Markdown 文件定义，解释器本身对规则内容保持 **叙事失明**，仅负责规则的传递、解释和执行。

### 核心特性

- **📝 Markdown 规则**：使用标准 Markdown 定义世界规则、角色、物品和机制
- **🧠 叙事失明**：解释器不解析规则内容，仅传递文本，确保规则完全独立
- **⚡ 异步优先**：全异步架构，支持高并发会话管理
- **💾 持久化优先**：内置 SQLite 存储，支持长期会话和版本回滚
- **🎮 玩家干预**：支持 OOC 注释、世界编辑、Retcon 等多种干预类型
- **🔌 多 LLM 支持**：抽象化的 LLM 提供商接口，支持 OpenAI、Anthropic、Ollama 等
- **🧩 插件系统**：可扩展的插件架构，支持自定义记忆后端、LLM 提供商和规则验证器
- **📊 监控指标**：内置性能监控、成本跟踪和质量指标收集

## 🏗️ 架构概述

LOOM 采用五层架构设计：

1. **运行时核心层**：会话管理、回合调度、持久化引擎、配置管理
2. **规则层**：Markdown 规则解析、版本控制、规则加载和验证
3. **解释层**：LLM 推理流水线、一致性检查、规则解释和约束提取
4. **世界记忆层**：结构化存储、向量存储、摘要生成和记忆检索
5. **玩家干预层**：OOC 处理、世界编辑、Retcon 处理和权限验证

详细架构设计请参阅 [架构文档](docs/ARCHITECTURE.md)。

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-org/loom.git
cd loom

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -e ".[dev]"
```

### 配置

1. 复制环境变量示例文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，设置您的 LLM API 密钥：
   ```env
   OPENAI_API_KEY=sk-your-key-here
   ANTHROPIC_API_KEY=your-anthropic-key
   ```

3. 创建规则目录和示例规则：
   ```bash
   mkdir -p canon
   cp examples/basic_world.md canon/default.md
   ```

### 运行示例

```bash
# 运行基础示例
python scripts/run_example.py

# 运行 CLI 界面
loom run --canon canon/default.md

# 启动 Web UI
loom web --port 8000
```

### 第一个示例

创建一个简单的规则文件 `canon/my_world.md`：

```markdown
# 世界观
这是一个奇幻世界，有魔法和龙。

# 叙事基调
史诗冒险风格，带有幽默元素。

# 权限边界
玩家可以探索任何区域。
玩家不能杀死无辜NPC。

# 因果关系
时间只能向前流动。
死亡通常是永久的。
```

运行会话：

```bash
loom run --canon canon/my_world.md --name "我的冒险"
```

## 📁 项目结构

```
loom/
├── src/loom/                    # 主源代码目录
│   ├── core/                    # 运行时核心层
│   │   ├── config_manager.py    # 配置管理
│   │   ├── persistence_engine.py # 持久化引擎
│   │   ├── prompt_assembler.py  # Prompt组装器
│   │   ├── session_manager.py   # 会话管理
│   │   └── turn_scheduler.py    # 回合调度器
│   ├── rules/                   # 规则层
│   │   ├── markdown_canon.py    # Markdown规则解析
│   │   ├── rule_loader.py       # 规则加载器
│   │   └── version_control.py   # 版本控制
│   ├── interpretation/          # 解释层
│   │   ├── consistency_checker.py # 一致性检查
│   │   ├── llm_provider.py      # LLM提供商接口
│   │   ├── reasoning_pipeline.py # 推理流水线
│   │   └── rule_interpreter.py  # 规则解释器
│   ├── memory/                  # 世界记忆层
│   │   ├── structured_store.py  # 结构化存储
│   │   ├── summarizer.py        # 摘要生成器
│   │   ├── vector_store.py      # 向量存储
│   │   └── world_memory.py      # 世界记忆管理器
│   ├── intervention/            # 玩家干预层
│   │   ├── ooc_handler.py       # OOC处理器
│   │   ├── player_intervention.py # 玩家干预处理器
│   │   ├── retcon_handler.py    # Retcon处理器
│   │   └── world_editor.py      # 世界编辑器
│   ├── utils/                   # 工具函数
│   │   ├── async_helpers.py     # 异步辅助函数
│   │   └── logging_config.py    # 日志配置
│   ├── web/                     # Web界面
│   │   ├── app.py               # FastAPI应用
│   │   ├── static/              # 静态资源
│   │   └── templates/           # HTML模板
│   └── plugins/                 # 插件系统
│       └── example_plugins.py   # 示例插件
├── tests/                       # 测试目录
│   ├── test_core/               # 核心层测试
│   ├── test_interpretation/     # 解释层测试
│   ├── test_intervention/       # 干预层测试
│   ├── test_memory/             # 记忆层测试
│   └── test_rules/              # 规则层测试
├── examples/                    # 示例文件
│   ├── basic_world.md           # 基础世界示例
│   ├── fantasy_setting.md       # 奇幻设定示例
│   ├── sci_fi_world.md          # 科幻世界示例
│   └── full_example/            # 完整示例项目
├── config/                      # 配置文件
│   ├── default_config.yaml      # 默认配置
│   ├── llm_providers.yaml       # LLM提供商配置
│   └── keys/                    # API密钥目录
├── docs/                        # 文档目录
│   ├── ARCHITECTURE.md          # 架构设计
│   ├── API_REFERENCE.md         # API参考
│   ├── CLI_USAGE.md             # CLI使用指南
│   ├── CONTRIBUTING.md          # 贡献指南
│   ├── DEPLOYMENT_GUIDE.md      # 部署指南
│   ├── EXTENSION_DEVELOPMENT_GUIDE.md # 扩展开发指南
│   ├── USER_GUIDE.md            # 用户指南
│   └── WORLD_BUILDING_GUIDE.md  # 世界构建指南
├── scripts/                     # 脚本目录
│   ├── run_example.py           # 示例运行脚本
│   ├── setup_dev.sh             # 开发环境设置
│   ├── setup_env.sh             # 环境设置
│   └── test_*.py                # 测试脚本
├── templates/                   # 模板目录
│   ├── projects/                # 项目模板
│   └── rules/                   # 规则模板
├── pyproject.toml              # 项目配置
├── README.md                   # 本文件
├── .env.example                # 环境变量示例
├── requirements.txt            # 依赖列表
├── docker-compose.yml          # Docker Compose配置
└── Dockerfile                  # Docker镜像配置
```

## 📚 文档

- [用户指南](docs/USER_GUIDE.md) - 完整的安装和使用教程
- [架构设计](docs/ARCHITECTURE.md) - 详细的架构说明和设计决策
- [API 参考](docs/API_REFERENCE.md) - 完整的 API 文档
- [CLI 使用指南](docs/CLI_USAGE.md) - 命令行工具详细说明
- [世界构建指南](docs/WORLD_BUILDING_GUIDE.md) - 如何创建和管理叙事世界
- [部署指南](docs/DEPLOYMENT_GUIDE.md) - 本地和云部署说明
- [扩展开发指南](docs/EXTENSION_DEVELOPMENT_GUIDE.md) - 插件和扩展开发
- [贡献指南](docs/CONTRIBUTING.md) - 如何为项目做贡献

## 🧪 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_core/

# 带覆盖率报告
pytest --cov=src.loom --cov-report=html

# 运行性能测试
pytest tests/performance/ -v
```

### 代码质量

```bash
# 格式化代码
black src/ tests/

# 类型检查
mypy src/

# 代码检查
flake8 src/

# 安全检查
bandit -r src/

# 依赖检查
safety check
```

### 预提交钩子

```bash
# 安装预提交钩子
pre-commit install

# 手动运行所有钩子
pre-commit run --all-files
```

## 🔧 CLI 工具

LOOM 提供完整的命令行界面：

```bash
# 查看帮助
loom --help

# 创建新世界
loom init my_world --type fantasy

# 运行会话
loom run --canon canon/my_world.md --name "冒险开始"

# 管理会话
loom session list
loom session load <session_id>
loom session export <session_id> --format json

# 规则管理
loom rules validate --file canon/my_world.md
loom rules diff canon/v1.md canon/v2.md

# 玩家干预
loom intervention apply --type "edit" --content "添加新角色"

# 启动 Web UI
loom web --port 8000 --host 0.0.0.0
```

详细 CLI 使用说明请参阅 [CLI 使用指南](docs/CLI_USAGE.md)。

## 🌐 Web 界面

LOOM 提供现代化的 Web 界面：

```bash
# 启动 Web 服务器
loom web

# 使用自定义配置
loom web --port 8080 --host 0.0.0.0 --debug
```

Web 界面功能：
- 实时会话管理
- 规则编辑器
- 记忆浏览器
- 性能监控仪表板
- 成本跟踪面板

## 🐳 容器化部署

### 使用 Docker

```bash
# 构建镜像
docker build -t loom:latest .

# 运行容器
docker run -p 8000:8000 -v ./data:/app/data loom:latest

# 使用 Docker Compose
docker-compose up -d
```

### Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loom
spec:
  replicas: 3
  selector:
    matchLabels:
      app: loom
  template:
    metadata:
      labels:
        app: loom
    spec:
      containers:
      - name: loom
        image: loom:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: loom-secrets
              key: openai-api-key
```

详细部署说明请参阅 [部署指南](docs/DEPLOYMENT_GUIDE.md)。

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](docs/CONTRIBUTING.md) 了解贡献指南。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 开发流程

```bash
# 设置开发环境
./scripts/setup_dev.sh

# 运行开发服务器
loom dev --reload

# 运行测试套件
./scripts/run_tests.sh

# 构建文档
mkdocs build
```

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型注解
- 编写完整的文档字符串
- 添加单元测试
- 保持向后兼容性

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 灵感来源于传统 TRPG 系统和现代 AI 叙事工具
- 感谢所有贡献者和测试者
- 特别感谢开源社区提供的各种工具和库

## 📞 联系方式

- 问题报告：[GitHub Issues](https://github.com/your-org/loom/issues)
- 讨论区：[GitHub Discussions](https://github.com/your-org/loom/discussions)
- 邮件：team@loom.dev
- Discord：[加入社区](https://discord.gg/loom)

## 📊 项目状态

| 组件 | 状态 | 测试覆盖率 | 文档完整性 |
|------|------|------------|------------|
| 运行时核心层 | ✅ 完成 | 92% | 完整 |
| 规则层 | ✅ 完成 | 88% | 完整 |
| 解释层 | ✅ 完成 | 85% | 完整 |
| 世界记忆层 | ✅ 完成 | 90% | 完整 |
| 玩家干预层 | ✅ 完成 | 87% | 完整 |
| CLI 工具 | ✅ 完成 | 83% | 完整 |
| Web 界面 | ✅ 完成 | 80% | 完整 |
| 插件系统 | 🔄 进行中 | 75% | 部分 |

---

**LOOM** - 编织你的叙事世界 🧵✨

*最后更新: 2026-01-12*