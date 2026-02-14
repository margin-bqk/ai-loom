#!/usr/bin/env python3
"""
本地CI测试流程脚本
运行所有CI检查，确保代码质量
支持多Python版本测试（通过tox）
"""

import os
import platform
import subprocess
import sys


def run_command(cmd, description):
    """运行命令并检查结果"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"命令: {cmd}")

    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print("成功")
        if result.stdout:
            # 只显示前500字符，避免输出过长
            output = result.stdout
            if len(output) > 500:
                output = output[:500] + "..."
            print(f"输出: {output}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"失败: {e}")
        if e.stderr:
            print(f"错误输出: {e.stderr[:500]}...")
        return False


def check_python_version():
    """检查当前Python版本"""
    import sys

    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")

    # 支持的Python版本
    supported_versions = [(3, 10), (3, 11), (3, 12)]
    current = (version.major, version.minor)

    if current in supported_versions:
        print(f"当前版本 {version.major}.{version.minor} 在支持列表中")
        return True
    else:
        print(f"警告: 当前版本 {version.major}.{version.minor} 不在官方支持列表 [3.10, 3.11, 3.12] 中")
        print("建议使用支持的Python版本进行测试")
        return False


def run_tox_multiversion():
    """使用tox运行多版本测试"""
    print("\n" + "=" * 60)
    print("多Python版本测试 (使用tox)")
    print("=" * 60)

    # 检查是否安装了tox
    try:
        subprocess.run(["tox", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("tox未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "tox"], check=True)

    print("运行tox测试多个Python版本 (3.10, 3.11, 3.12)...")
    print("注意: 这可能需要一些时间，并且需要安装多个Python版本")

    return run_command("tox", "多版本测试")


def main():
    """主函数"""
    print("开始本地CI测试流程")
    print("工作目录:", os.getcwd())
    print("操作系统:", platform.system(), platform.release())

    # 检查Python版本
    check_python_version()

    all_passed = True

    # 解析命令行参数
    run_multiversion = "--multiversion" in sys.argv
    skip_multiversion = "--skip-multiversion" in sys.argv

    # 1. 代码格式化检查
    if not run_command("black --check src/ tests/", "1. 代码格式化检查"):
        all_passed = False

    # 2. 导入排序检查
    if not run_command("isort --check-only --diff src/ tests/", "2. 导入排序检查"):
        all_passed = False

    # 3. 代码风格检查
    if not run_command("flake8 src/ tests/", "3. 代码风格检查"):
        all_passed = False

    # 4. 类型检查
    if not run_command("mypy src/loom --ignore-missing-imports", "4. 类型检查"):
        all_passed = False

    # 5. 单元测试 (当前Python版本)
    if not run_command("pytest tests/ -v", "5. 单元测试 (当前Python版本)"):
        all_passed = False

    # 6. 多版本测试 (可选)
    if run_multiversion and not skip_multiversion:
        if not run_tox_multiversion():
            all_passed = False
    elif not skip_multiversion:
        print("\n" + "=" * 60)
        print("多版本测试跳过")
        print("如需测试多个Python版本 (3.10, 3.11, 3.12)，请运行:")
        print("  python scripts/run_ci_local.py --multiversion")
        print("或使用: tox")
        print("=" * 60)

    # 7. 安全扫描
    if not run_command("bandit -r src/ -c pyproject.toml", "7. 安全扫描"):
        all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("所有CI检查通过！可以安全地push代码。")
        print("\n注意: 本地测试仅针对当前Python版本。")
        print("GitHub Actions CI将测试所有支持的Python版本 (3.10, 3.11, 3.12)。")
        return 0
    else:
        print("部分CI检查失败，请修复后再push。")
        print("\n修复建议:")
        print("1. 运行 'python scripts/run_ci_local.py --fix' 自动修复格式问题")
        print("2. 查看具体错误信息并修复")
        return 1


if __name__ == "__main__":
    # 处理命令行参数
    if "--fix" in sys.argv:
        print("运行自动修复...")
        subprocess.run("black src/ tests/", shell=True)
        subprocess.run("isort src/ tests/", shell=True)
        print("自动修复完成")
        sys.exit(0)
    elif "--help" in sys.argv or "-h" in sys.argv:
        print("本地CI测试脚本")
        print("\n用法:")
        print("  python scripts/run_ci_local.py [选项]")
        print("\n选项:")
        print("  --fix             自动修复格式问题")
        print("  --multiversion    运行多Python版本测试 (需要tox)")
        print("  --skip-multiversion 跳过多版本测试")
        print("  --help, -h        显示帮助信息")
        sys.exit(0)

    sys.exit(main())
