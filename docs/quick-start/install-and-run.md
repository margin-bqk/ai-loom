# 安装与运行

## 概述

本文档将指导您完成 LOOM 的安装和基本运行。LOOM 是一个语言驱动的开放叙事解释器运行时，专为 AI 驱动的角色扮演和互动叙事设计。

## 系统要求

- **Python**: 3.10 或更高版本
- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+, CentOS 8+)
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 500MB 可用空间

## 安装步骤

### 1. 克隆仓库

```bash
# 克隆 LOOM 仓库
git clone https://github.com/your-org/loom.git
cd loom
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装核心依赖
pip install -e .

# 或者安装开发依赖（包含测试工具）
pip install -e ".[dev]"

# 安装向量存储支持（可选）
pip install chromadb
```

### 4. 配置环境变量

创建 `.env` 文件（基于 `.env.example`）：

```bash
# 复制示例环境文件
cp .env.example .env

# 编辑 .env 文件，设置您的 API 密钥
# 需要至少配置一个 LLM 提供商
```

`.env` 文件示例：
```env
# OpenAI API 配置
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic API 配置
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Google Gemini API 配置
GOOGLE_API_KEY=your-google-api-key-here

# 本地模型配置（Ollama）
OLLAMA_BASE_URL=http://localhost:11434
```

## 验证安装

### 1. 检查版本

```bash
# 检查 LOOM 版本
loom --version

# 预期输出类似：
# loom 0.10.0
```

### 2. 运行简单测试

```bash
# 运行内置测试
python -m pytest tests/test_core/test_config_manager.py -v

# 或者运行完整测试套件
python scripts/run_phase1_tests.py
```

### 3. 检查 CLI 命令

```bash
# 查看所有可用命令
loom --help

# 查看特定命令帮助
loom run --help
loom config --help
loom session --help
```

## 快速运行示例

### 1. 使用内置示例

```bash
# 运行基础示例
loom run interactive --canon templates/rules/fantasy_basic.md

# 运行完整示例项目
cd examples/full_example
python run_example.py
```

### 2. 交互式会话

启动交互式会话：

```bash
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --name "我的第一个会话" \
  --provider openai \
  --max-turns 10
```

### 3. 批处理运行

```bash
# 从文件加载输入
loom run batch \
  --canon templates/rules/fantasy_basic.md \
  --input input.txt \
  --output output.txt
```

## 故障排除

### 常见问题

#### 1. 虚拟环境激活失败
- **Windows**: 确保以管理员身份运行 PowerShell，或执行 `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Linux/Mac**: 确保脚本有执行权限 `chmod +x venv/bin/activate`

#### 2. 依赖安装失败
```bash
# 升级 pip
python -m pip install --upgrade pip

# 清除缓存后重试
pip cache purge
pip install -e .
```

#### 3. API 密钥错误
- 确保 `.env` 文件中的 API 密钥正确
- 检查环境变量是否已加载：`echo $OPENAI_API_KEY`
- 尝试重新激活虚拟环境

#### 4. 缺少向量存储支持
```bash
# 安装 ChromaDB
pip install chromadb

# 或者使用 SQLite 内存模式（无需额外安装）
# 在配置中设置 memory.vector_store.enabled = false
```

## 下一步

安装完成后，您可以：

1. **配置基本设置**: 查看 [基本配置指南](basic-configuration.md)
2. **运行第一个示例**: 查看 [第一个示例](first-example.md)
3. **验证安装**: 查看 [验证安装](verify-installation.md)
4. **深入学习**: 查看 [用户指南](../user-guide/getting-started.md)

## 获取帮助

- **文档**: 查看完整文档 [https://loom.dev/docs](https://loom.dev/docs)
- **GitHub Issues**: 报告问题 [https://github.com/your-org/loom/issues](https://github.com/your-org/loom/issues)
- **Discord**: 加入社区讨论 [https://discord.gg/loom](https://discord.gg/loom)

---

> 注意：LOOM 仍在积极开发中，API 和功能可能会有变化。建议定期更新到最新版本。
