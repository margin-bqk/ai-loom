#!/bin/bash
# LOOM 开发环境设置脚本

set -e

echo "🚀 设置 LOOM 开发环境..."

# 检查 Python 版本
echo "检查 Python 版本..."
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$python_version" < "3.10" ]]; then
    echo "❌ 需要 Python 3.10+，当前版本: $python_version"
    exit 1
fi
echo "✅ Python $python_version 符合要求"

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装开发依赖
echo "安装开发依赖..."
pip install -e .[dev,api,cli,vector]

# 安装 pre-commit
echo "安装 pre-commit..."
pip install pre-commit
pre-commit install

# 创建配置文件
echo "创建配置文件..."
if [ ! -f ".env" ]; then
    echo "复制 .env.example 到 .env..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置 API 密钥"
fi

# 创建目录结构
echo "创建目录结构..."
mkdir -p data logs canon config

# 检查配置文件
if [ ! -f "config/default_config.yaml" ]; then
    echo "创建默认配置文件..."
    cp config/default_config.yaml.example config/default_config.yaml 2>/dev/null || echo "使用默认配置"
fi

# 运行检查
echo "运行系统检查..."
python -c "import sys; sys.path.insert(0, 'src'); import loom; print('✅ LOOM 导入成功')"

# 运行测试
echo "运行测试..."
pytest tests/ -xvs -k "not slow"

echo ""
echo "🎉 开发环境设置完成!"
echo ""
echo "下一步:"
echo "1. 编辑 .env 文件配置 API 密钥"
echo "2. 运行 'loom dev check' 检查系统状态"
echo "3. 运行 'loom init' 初始化项目"
echo "4. 运行 'loom run interactive' 启动交互式会话"
echo ""
echo "常用命令:"
echo "  loom dev lint     - 代码质量检查"
echo "  loom dev test     - 运行测试"
echo "  loom dev docs     - 构建文档"
echo "  pre-commit run --all-files - 运行所有代码检查"
