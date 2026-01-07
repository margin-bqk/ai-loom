#!/bin/bash

# LOOM 环境设置脚本
# 此脚本用于设置 LOOM 开发环境

set -e  # 遇到错误时退出

echo "=== LOOM 环境设置脚本 ==="
echo "开始设置 LOOM 开发环境..."

# 检查 Python 版本
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "错误: 需要 Python 3.10+，当前版本: $python_version"
    echo "请升级 Python 版本"
    exit 1
fi
echo "✓ Python 版本: $python_version"

# 检查 pip
echo "检查 pip..."
if ! command -v pip3 &> /dev/null; then
    echo "错误: pip3 未安装"
    exit 1
fi
echo "✓ pip 已安装"

# 创建虚拟环境
echo "创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 虚拟环境已创建"
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装基础依赖
echo "安装基础依赖..."
pip install wheel setuptools

# 安装项目依赖
echo "安装项目依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✓ 从 requirements.txt 安装依赖"
elif [ -f "pyproject.toml" ]; then
    pip install -e .
    echo "✓ 从 pyproject.toml 安装依赖"
else
    echo "警告: 未找到依赖文件，安装常用依赖..."
    pip install aiohttp pydantic sqlalchemy markdown-it-py typer
fi

# 安装开发依赖（可选）
if [ "$1" == "--dev" ]; then
    echo "安装开发依赖..."
    pip install pytest pytest-asyncio black mypy flake8
    echo "✓ 开发依赖已安装"
fi

# 创建必要目录
echo "创建必要目录..."
mkdir -p data
mkdir -p canon
mkdir -p config
mkdir -p logs
mkdir -p backups

echo "✓ 目录结构已创建"

# 复制示例配置文件
echo "设置配置文件..."
if [ -f "config/default_config.yaml" ]; then
    echo "✓ 配置文件已存在"
else
    if [ -f "config/default_config.yaml.example" ]; then
        cp config/default_config.yaml.example config/default_config.yaml
        echo "✓ 从示例文件创建配置文件"
    else
        echo "警告: 未找到示例配置文件"
    fi
fi

# 复制示例规则文件
echo "设置示例规则..."
if [ ! -f "canon/default.md" ]; then
    if [ -f "examples/basic_world.md" ]; then
        cp examples/basic_world.md canon/default.md
        echo "✓ 从示例创建默认规则"
    else
        echo "警告: 未找到示例规则文件"
    fi
fi

# 设置环境变量示例
echo "设置环境变量..."
if [ ! -f ".env" ]; then
    cat > .env.example << EOF
# LOOM 环境变量配置
# 复制此文件为 .env 并填写实际值

# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API 配置
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 日志级别
LOOM_LOG_LEVEL=INFO

# 数据目录
LOOM_DATA_DIR=./data

# 其他配置...
EOF
    echo "✓ 环境变量示例文件已创建 (.env.example)"
    echo "  请复制 .env.example 为 .env 并填写实际值"
fi

# 运行基础测试（可选）
if [ "$1" == "--test" ]; then
    echo "运行基础测试..."
    if command -v pytest &> /dev/null; then
        pytest tests/test_core/ -v
    else
        echo "警告: pytest 未安装，跳过测试"
    fi
fi

echo ""
echo "=== 环境设置完成 ==="
echo ""
echo "下一步:"
echo "1. 复制 .env.example 为 .env 并填写 API 密钥"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 运行示例: python scripts/run_example.py"
echo ""
echo "开发命令:"
echo "  - 运行测试: pytest"
echo "  - 代码格式化: black src/"
echo "  - 类型检查: mypy src/"
echo "  - 代码检查: flake8 src/"
echo ""
echo "祝您使用愉快！"