# 验证安装

## 概述

本文档提供了一系列验证步骤，确保 LOOM 已正确安装并可以正常工作。建议在完成安装后按照本文档的顺序进行验证。

## 验证步骤概览

1. **基础验证** - 检查 Python 环境和基本依赖
2. **CLI 验证** - 测试命令行工具
3. **配置验证** - 检查配置系统
4. **LLM 提供商验证** - 测试 API 连接
5. **功能验证** - 运行测试和示例
6. **性能验证** - 检查系统性能

## 1. 基础验证

### 1.1 检查 Python 版本

```bash
# 检查 Python 版本
python --version

# 预期输出：Python 3.10.x 或更高
# 如果版本不符，需要升级 Python
```

### 1.2 检查虚拟环境

```bash
# 检查是否在虚拟环境中
which python
# 或
where python  # Windows

# 预期输出应包含 "venv" 路径
# 例如：/path/to/loom/venv/bin/python
```

### 1.3 检查核心依赖

```bash
# 检查关键依赖包
python -c "import typer; print(f'Typer版本: {typer.__version__}')"
python -c "import sqlite3; print(f'SQLite版本: {sqlite3.sqlite_version}')"
python -c "import yaml; print('PyYAML 已安装')"
python -c "import aiohttp; print('aiohttp 已安装')"
```

### 1.4 检查项目结构

```bash
# 检查关键目录和文件
ls -la src/loom/
ls -la config/
ls -la templates/rules/

# 预期应看到：
# src/loom/ - 源代码目录
# config/ - 配置文件目录
# templates/rules/ - 规则模板目录
```

## 2. CLI 验证

### 2.1 检查 LOOM 命令

```bash
# 检查 loom 命令是否可用
loom --help

# 预期输出应显示所有可用命令：
# Usage: loom [OPTIONS] COMMAND [ARGS]...
#
# Options:
#   --version  Show version
#   --help     Show this message and exit.
#
# Commands:
#   config   配置管理
#   export   导出会话
#   import   导入会话
#   init     初始化项目
#   run      运行世界会话
#   session  会话管理
#   rules    规则管理
```

### 2.2 检查版本信息

```bash
# 检查 LOOM 版本
loom --version

# 预期输出：loom 0.10.0
```

### 2.3 测试各子命令

```bash
# 测试 config 命令
loom config --help

# 测试 run 命令
loom run --help

# 测试 session 命令
loom session --help

# 测试 rules 命令
loom rules --help
```

## 3. 配置验证

### 3.1 检查默认配置

```bash
# 查看默认配置
loom config show --section llm --format table

# 预期输出应显示 LLM 提供商配置表格
```

### 3.2 测试配置验证

```bash
# 验证配置语法
loom config validate

# 预期输出：Configuration is valid.
```

### 3.3 测试环境变量

```bash
# 检查环境变量加载
export TEST_VAR="hello"
loom config set test.value "${TEST_VAR}"
loom config show --section test

# 预期输出应显示 test.value: hello
```

## 4. LLM 提供商验证

### 4.1 测试 OpenAI 连接

```bash
# 测试 OpenAI 连接（需要配置 API 密钥）
loom config test --provider openai

# 预期输出：
# Testing OpenAI provider...
# ✓ Connection successful
# ✓ Model available: gpt-3.5-turbo
# ✓ Authentication valid
```

### 4.2 测试备用提供商

```bash
# 测试 Anthropic（如果配置了）
loom config test --provider anthropic

# 测试 Ollama（本地模型）
loom config test --provider ollama
```

### 4.3 测试故障转移

```bash
# 测试多个提供商
loom config test --all

# 预期输出应显示所有已配置提供商的测试结果
```

## 5. 功能验证

### 5.1 运行测试脚本

```bash
# 运行基础组件测试
python scripts/test_utils/test_component_imports_fixed.py

# 运行规则解释测试
python scripts/test_utils/test_rules_interpretation_simple.py

# 运行运行时集成测试
python scripts/test_utils/test_runtime_integration.py

# 运行内存集成测试
python scripts/test_utils/test_memory_integration.py
```

### 5.2 运行验证脚本

```bash
# 运行验证脚本检查组件
python scripts/verification/verify_components_ascii.py

# 运行增强组件验证
python scripts/verification/verify_enhanced_components_simple.py

# 运行规则验证
python scripts/verification/verify_rule_simple.py

# 运行运行时验证
python scripts/verification/verify_runtime.py
```

### 5.3 测试示例项目

```bash
# 运行完整示例
cd examples/full_example
python run_example.py

# 预期输出应显示示例运行成功
```

## 6. 性能验证

### 6.1 测试启动时间

```bash
# 测试冷启动时间
time loom --version

# 预期应在 1-2 秒内完成
```

### 6.2 测试会话创建

```bash
# 测试会话创建性能
time loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --name "性能测试" \
  --max-turns 1 \
  --no-input <<< "exit"

# 预期应在 3-5 秒内完成（包括 LLM 调用）
```

### 6.3 测试内存使用

```bash
# 运行内存测试脚本
python scripts/test_memory_integration.py

# 或使用系统工具监控
# Linux/Mac:
# /usr/bin/time -v loom --version
```

## 详细验证脚本

### 完整验证脚本

创建 `verify_installation.py`：

```python
#!/usr/bin/env python3
"""
LOOM 安装验证脚本
运行此脚本验证 LOOM 是否已正确安装
"""

import sys
import subprocess
import platform
import sqlite3
import yaml
import json
from pathlib import Path

def run_command(cmd, check=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_python_version():
    """检查 Python 版本"""
    print("1. 检查 Python 版本...")
    version = platform.python_version()
    major, minor, _ = map(int, version.split('.'))

    if major == 3 and minor >= 10:
        print(f"  ✓ Python {version} (符合要求)")
        return True
    else:
        print(f"  ✗ Python {version} (需要 3.10+)")
        return False

def check_virtual_env():
    """检查虚拟环境"""
    print("2. 检查虚拟环境...")
    success, stdout, _ = run_command("which python", check=False)

    if "venv" in stdout or "VIRTUAL_ENV" in os.environ:
        print("  ✓ 在虚拟环境中")
        return True
    else:
        print("  ⚠ 不在虚拟环境中（建议使用虚拟环境）")
        return True  # 不强制要求

def check_dependencies():
    """检查依赖包"""
    print("3. 检查核心依赖...")
    dependencies = [
        ("typer", "import typer"),
        ("sqlite3", "import sqlite3"),
        ("yaml", "import yaml"),
        ("aiohttp", "import aiohttp"),
        ("pydantic", "import pydantic"),
    ]

    all_ok = True
    for name, import_stmt in dependencies:
        try:
            exec(import_stmt)
            print(f"  ✓ {name} 已安装")
        except ImportError:
            print(f"  ✗ {name} 未安装")
            all_ok = False

    return all_ok

def check_loom_cli():
    """检查 LOOM CLI"""
    print("4. 检查 LOOM CLI...")

    # 检查版本
    success, stdout, stderr = run_command("loom --version", check=False)
    if success and "loom" in stdout:
        version = stdout.strip()
        print(f"  ✓ {version}")

        # 检查帮助
        success, stdout, stderr = run_command("loom --help", check=False)
        if success and "Commands:" in stdout:
            print("  ✓ CLI 命令可用")
            return True
        else:
            print("  ✗ CLI 命令不可用")
            return False
    else:
        print("  ✗ LOOM 未安装或不可用")
        return False

def check_configuration():
    """检查配置"""
    print("5. 检查配置...")

    config_path = Path("config/default_config.yaml")
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            print(f"  ✓ 配置文件存在 ({len(config)} 个配置项)")

            # 检查必要配置
            required_sections = ["llm_providers", "session", "memory"]
            missing = [s for s in required_sections if s not in config]

            if not missing:
                print("  ✓ 必要配置部分完整")
                return True
            else:
                print(f"  ✗ 缺少配置部分: {missing}")
                return False
        except Exception as e:
            print(f"  ✗ 配置文件错误: {e}")
            return False
    else:
        print("  ✗ 配置文件不存在")
        return False

def check_llm_providers():
    """检查 LLM 提供商"""
    print("6. 检查 LLM 提供商...")

    # 检查环境变量
    env_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    configured = [var for var in env_vars if var in os.environ]

    if configured:
        print(f"  ⚠ 已配置的 API 密钥: {len(configured)} 个")
        print(f"    建议至少配置一个 LLM 提供商")
        return True
    else:
        print("  ⚠ 未配置 LLM API 密钥")
        print("    需要配置至少一个 LLM 提供商才能运行会话")
        return True  # 不强制要求，但会限制功能

def run_smoke_test():
    """运行冒烟测试"""
    print("7. 运行冒烟测试...")

    # 创建测试规则文件
    test_rules = Path("test_smoke_rules.md")
    test_rules.write_text("# 测试规则\n\n这是一个简单的测试规则文件。\n")

    try:
        # 尝试启动会话（不实际运行）
        cmd = 'loom run interactive --canon test_smoke_rules.md --name "冒烟测试" --max-turns 0 --dry-run'
        success, stdout, stderr = run_command(cmd, check=False)

        if success or "dry run" in stdout.lower():
            print("  ✓ 冒烟测试通过")
            return True
        else:
            print(f"  ✗ 冒烟测试失败: {stderr[:100]}")
            return False
    finally:
        # 清理
        if test_rules.exists():
            test_rules.unlink()

def main():
    """主验证函数"""
    print("=" * 60)
    print("LOOM 安装验证")
    print("=" * 60)

    checks = [
        ("Python 版本", check_python_version),
        ("虚拟环境", check_virtual_env),
        ("核心依赖", check_dependencies),
        ("LOOM CLI", check_loom_cli),
        ("配置", check_configuration),
        ("LLM 提供商", check_llm_providers),
        ("冒烟测试", run_smoke_test),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ 检查失败: {e}")
            results.append((name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 项检查通过")

    if passed == total:
        print("\n🎉 所有检查通过！LOOM 已正确安装。")
        return 0
    elif passed >= total * 0.7:
        print("\n⚠ 大部分检查通过，但有一些问题需要解决。")
        print("建议查看上面的失败项并进行修复。")
        return 1
    else:
        print("\n❌ 安装存在严重问题。")
        print("请重新安装或查看文档获取帮助。")
        return 2

if __name__ == "__main__":
    import os
    sys.exit(main())
```

### 使用验证脚本

```bash
# 运行验证脚本
python verify_installation.py

# 或直接运行验证命令
python -c "
import sys
sys.path.insert(0, '.')
from verify_installation import main
sys.exit(main())
"
```

## 常见问题解决

### 问题 1: "command not found: loom"

**解决方案**:
```bash
# 确保在虚拟环境中
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 重新安装
pip install -e .

# 检查安装路径
which loom  # 或 where loom (Windows)
```

### 问题 2: "ModuleNotFoundError"

**解决方案**:
```bash
# 安装缺失的依赖
pip install -r requirements.txt

# 或安装开发依赖
pip install -e ".[dev]"
```

### 问题 3: "Invalid API key"

**解决方案**:
```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 重新设置环境变量
export OPENAI_API_KEY="sk-your-key-here"

# 或编辑 .env 文件
vim .env
```

### 问题 4: 配置文件错误

**解决方案**:
```bash
# 验证配置文件语法
python -c "import yaml; yaml.safe_load(open('config/default_config.yaml'))"

# 重置为默认配置
cp config/default_config.yaml ~/.loom/config.yaml
```

### 问题 5: 性能问题

**解决方案**:
```bash
# 启用缓存
loom config set llm.openai.enable_caching true

# 使用更轻量级的模型
loom config set llm.openai.model "gpt-3.5-turbo"

# 增加超时时间
loom config set llm.openai.timeout 60
```

## 验证报告

完成验证后，您可以生成验证报告：

```bash
# 生成验证报告
loom config validate --report validation_report.json

# 查看报告
cat validation_report.json | python -m json.tool
```

## 下一步

验证通过后，您可以：

1. **开始使用 LOOM**: 查看 [第一个示例](first-example.md)
2. **深入学习**: 查看 [用户指南](../user-guide/getting-started.md)
3. **配置高级功能**: 查看 [配置指南](basic-configuration.md)
4. **开发扩展**: 查看 [开发指南](../development/setup-development.md)

## 获取帮助

如果验证过程中遇到问题：

1. **查看日志**: `tail -f logs/loom.log`
2. **运行调试模式**: `loom --debug --help`
3. **查看 GitHub Issues**: [https://github.com/your-org/loom/issues](https://github.com/your-org/loom/issues)
4. **加入社区**: [Discord](https://discord.gg/loom)

---

> 注意：定期运行验证可以确保 LOOM 始终处于正常工作状态，特别是在更新或环境变更后。
