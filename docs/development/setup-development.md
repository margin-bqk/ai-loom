# 开发环境设置

## 概述

本文档指导您设置 LOOM 的开发环境，包括代码获取、依赖安装、开发工具配置等。

## 系统要求

### 基础要求
- **Python**: 3.10 或更高版本
- **Git**: 2.25 或更高版本
- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+, CentOS 8+)
- **内存**: 至少 8GB RAM（推荐 16GB+）
- **磁盘空间**: 至少 2GB 可用空间

### 可选组件
- **Docker**: 20.10+（用于容器化开发）
- **Node.js**: 18+（用于 Web 界面开发）
- **Redis**: 6.0+（用于缓存和队列）
- **PostgreSQL**: 13+（用于生产级数据库）

## 获取代码

### 1. 克隆仓库

```bash
# 克隆主仓库
git clone https://github.com/your-org/loom.git
cd loom

# 或克隆您的 fork
git clone https://github.com/your-username/loom.git
cd loom
```

### 2. 配置 Git

```bash
# 设置用户信息
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 设置上游仓库（如果是 fork）
git remote add upstream https://github.com/your-org/loom.git

# 验证配置
git remote -v
```

## 环境设置

### 1. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat
```

### 2. 安装开发依赖

```bash
# 安装开发版本（可编辑模式）
pip install -e ".[dev]"

# 或分步安装
pip install -e .  # 核心依赖
pip install -r requirements-dev.txt  # 开发工具
```

### 3. 安装预提交钩子

```bash
# 安装预提交
pre-commit install

# 安装所有钩子类型
pre-commit install --hook-type pre-commit
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg

# 运行预提交检查
pre-commit run --all-files
```

## 开发工具配置

### 1. 代码编辑器配置

#### VS Code 配置

创建 `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests",
    "--no-header",
    "--verbose",
    "--tb=short"
  ],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true
  }
}
```

#### PyCharm 配置

1. 设置项目解释器为虚拟环境中的 Python
2. 启用 Black 作为代码格式化工具
3. 配置 pytest 作为测试运行器
4. 启用类型检查（mypy）

### 2. 开发依赖安装

```bash
# 安装代码质量工具
pip install black flake8 isort mypy pylint

# 安装测试工具
pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist

# 安装文档工具
pip install mkdocs mkdocs-material mkdocstrings mkdocs-autorefs

# 安装构建工具
pip install build twine setuptools wheel

# 安装调试工具
pip install ipython ipdb debugpy
```

## 项目结构

### 目录结构说明

```
loom/
├── src/loom/                    # 源代码
│   ├── core/                   # 核心运行时
│   ├── interpretation/         # 解释层
│   ├── memory/                 # 记忆系统
│   ├── rules/                  # 规则层
│   ├── intervention/           # 玩家干预
│   ├── cli/                    # 命令行界面
│   ├── web/                    # Web 界面
│   └── utils/                  # 工具函数
├── tests/                      # 测试代码
├── docs/                       # 文档
├── config/                     # 配置文件
├── examples/                   # 示例代码
├── templates/                  # 模板文件
├── scripts/                    # 工具脚本
└── plans/                      # 项目计划
```

### 关键文件说明

- `pyproject.toml` - 项目配置和依赖管理
- `requirements.txt` - 生产依赖
- `requirements-dev.txt` - 开发依赖
- `.pre-commit-config.yaml` - 预提交钩子配置
- `.flake8` - 代码风格检查配置
- `.env.example` - 环境变量示例
- `docker-compose.yml` - Docker 开发环境

## 开发工作流

### 1. 创建开发分支

```bash
# 从主分支创建特性分支
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name

# 或从 issue 创建分支
git checkout -b fix/issue-123
```

### 2. 编写代码

```bash
# 启动开发服务器（Web 界面）
python -m loom.web.app

# 运行测试
pytest tests/ -v

# 检查代码质量
pre-commit run --all-files
```

### 3. 提交更改

```bash
# 添加更改
git add .

# 提交（预提交钩子会自动运行）
git commit -m "feat: 添加新功能"

# 或使用交互式提交
git commit
```

### 4. 推送到远程

```bash
# 推送到您的 fork
git push origin feature/your-feature-name

# 创建 Pull Request
# 访问 GitHub 仓库创建 PR
```

## 测试环境

### 1. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_core/test_session_manager.py

# 运行特定测试类
pytest tests/test_core/test_session_manager.py::TestSessionManager

# 运行特定测试方法
pytest tests/test_core/test_session_manager.py::TestSessionManager::test_create_session

# 并行运行测试
pytest -n auto

# 生成覆盖率报告
pytest --cov=src/loom --cov-report=html --cov-report=term
```

### 2. 测试配置

创建 `tests/conftest.py` 用于测试配置：

```python
import pytest
import asyncio
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def sample_rules_file(test_data_dir):
    """示例规则文件"""
    return test_data_dir / "sample_rules.md"

@pytest.fixture(scope="session")
def event_loop():
    """为异步测试创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### 3. 集成测试

```bash
# 运行集成测试
pytest tests/test_integration/ -v

# 运行端到端测试
python scripts/test_runtime_integration.py

# 运行性能测试
python scripts/test_performance_benchmark.py
```

## 调试指南

### 1. 使用调试器

```python
# 在代码中插入断点
import ipdb; ipdb.set_trace()

# 或使用内置断点
breakpoint()
```

### 2. VS Code 调试配置

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: LOOM CLI",
      "type": "python",
      "request": "launch",
      "module": "loom.cli",
      "args": ["run", "interactive", "--canon", "templates/rules/fantasy_basic.md"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### 3. 日志调试

```python
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)

# 在代码中添加日志
logger = logging.getLogger(__name__)
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

## 代码质量

### 1. 代码格式化

```bash
# 使用 Black 格式化代码
black src/ tests/

# 使用 isort 整理导入
isort src/ tests/

# 自动修复所有格式问题
black src/ tests/ && isort src/ tests/
```

### 2. 代码检查

```bash
# 使用 flake8 检查代码风格
flake8 src/ tests/

# 使用 mypy 检查类型
mypy src/

# 使用 pylint 进行更严格的检查
pylint src/loom/
```

### 3. 安全检查

```bash
# 使用 bandit 检查安全漏洞
bandit -r src/

# 使用 safety 检查依赖漏洞
safety check
```

## 文档开发

### 1. 编写文档

```bash
# 启动文档开发服务器
mkdocs serve

# 构建文档
mkdocs build

# 部署文档
mkdocs gh-deploy
```

### 2. 文档标准

- 使用 Markdown 格式
- 遵循 [Google 风格指南](https://google.github.io/styleguide/pyguide.html)
- 为所有公共 API 编写文档字符串
- 包含代码示例和使用说明

### 3. API 文档

```python
def create_session(name: str, canon_path: str) -> Session:
    """
    创建新会话。
    
    Args:
        name: 会话名称
        canon_path: 规则文件路径
        
    Returns:
        Session: 创建的会话对象
        
    Raises:
        FileNotFoundError: 规则文件不存在
        ValidationError: 规则文件无效
        
    Example:
        >>> session = create_session("测试会话", "rules/fantasy.md")
        >>> session.name
        '测试会话'
    """
    # 实现代码
```

## 依赖管理

### 1. 添加新依赖

```bash
# 添加生产依赖
poetry add package-name

# 添加开发依赖
poetry add --dev package-name

# 或直接编辑 pyproject.toml
```

### 2. 更新依赖

```bash
# 更新所有依赖
poetry update

# 更新特定依赖
poetry update package-name

# 生成 requirements.txt
poetry export -f requirements.txt --output requirements.txt
```

### 3. 依赖锁定

```bash
# 锁定依赖版本
poetry lock

# 安装锁定版本
poetry install
```

## 容器化开发

### 1. Docker 开发环境

```bash
# 构建开发镜像
docker build -t loom-dev -f Dockerfile.dev .

# 运行开发容器
docker run -it --rm \
  -v $(pwd):/app \
  -p 8000:8000 \
  loom-dev

# 使用 docker-compose
docker-compose up -d
```

### 2. 开发环境配置

创建 `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  loom:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - loom-venv:/app/venv
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app/src
      - LOOM_ENV=development
    command: python -m loom.web.app

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=loom_dev
      - POSTGRES_USER=loom
      - POSTGRES_PASSWORD=loom123
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  loom-venv:
  postgres-data:
```

## 性能优化

### 1. 性能分析

```bash
# 使用 cProfile 分析性能
python -m cProfile -o profile.stats scripts/run_example.py

# 分析结果
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('time').print_stats(20)"

# 使用 memory_profiler
python -m memory_profiler scripts/run_example.py
```

### 2. 异步性能

```python
import asyncio
import aiohttp

async def fetch_concurrently(urls):
    """并发获取多个 URL"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

## 贡献指南

### 1. 贡献流程

1. Fork 仓库
2. 创建特性分支
3. 编写代码和测试
4. 运行测试和代码检查
5. 提交 Pull Request
6. 等待代码审查

### 2. 代码审查标准

- 代码符合项目风格指南
- 包含适当的测试
- 文档已更新
- 没有引入安全漏洞
- 性能影响可接受

### 3. 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加或修改测试
chore: 构建过程或辅助工具变动
```

## 故障排除

### 常见问题

#### 1. 虚拟环境问题

```bash
# 重新创建虚拟环境
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

#### 2. 依赖冲突

```bash
# 清理并重新安装
pip cache purge
pip uninstall -y -r <(pip freeze)
pip install -e ".[dev]"
```

#### 3. 测试失败

```bash
# 清理测试缓存
rm -rf .pytest_cache
rm -rf .coverage

# 重新运行测试
pytest --tb=short -v
```

#### 4. 预提交钩子失败

```bash
# 跳过预提交检查
git commit --no-verify -m "紧急修复"

# 手动运行检查
pre-commit run --all-files --show-diff-on-failure
```

## 下一步

开发环境设置完成后，您可以：

1. **阅读代码**: 查看 [代码组织](code-organization.md)
2. **编写测试**: 查看 [测试指南](testing-guide.md)
3. **调试代码**: 查看 [调试指南](debugging-guide.md)
4. **贡献代码**: 查看 [贡献指南](../user-guide/contributing.md)

## 获取帮助

- **文档**: [https://loom.dev/docs](https://loom.dev/docs)
- **GitHub Issues**: [https://github.com/your-org/loom/issues](https://github.com/your-org/loom/issues)
- **Discord**: [https://discord.gg/loom](https://discord.gg/loom)
- **开发邮件列表**: dev@loom.dev
