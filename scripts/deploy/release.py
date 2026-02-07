#!/usr/bin/env python3
"""
LOOM 版本管理和发布脚本

功能：
1. 版本号管理
2. 发布前检查
3. 自动构建和上传
4. 创建 Git 标签

用法：
    python scripts/release.py --help
"""

import argparse
import subprocess
import sys
import re
import toml
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
CHANGELOG_PATH = PROJECT_ROOT / "CHANGELOG.md"
INIT_PATH = PROJECT_ROOT / "src" / "loom" / "__init__.py"


def get_current_version() -> str:
    """从 pyproject.toml 读取当前版本号"""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)
    return data["project"]["version"]


def update_version(new_version: str) -> None:
    """更新所有文件中的版本号"""
    print(f"更新版本号到 {new_version}")
    
    # 1. 更新 pyproject.toml
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)
    data["project"]["version"] = new_version
    with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
        toml.dump(data, f)
    
    # 2. 更新 __init__.py
    if INIT_PATH.exists():
        with open(INIT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        # 查找 __version__ = "x.y.z"
        pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
        if re.search(pattern, content):
            content = re.sub(pattern, f'__version__ = "{new_version}"', content)
            with open(INIT_PATH, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            # 如果不存在，则添加
            with open(INIT_PATH, "a", encoding="utf-8") as f:
                f.write(f'\n__version__ = "{new_version}"\n')
    
    print("版本号更新完成")


def run_command(cmd: str, cwd: Optional[Path] = None) -> bool:
    """运行命令并检查结果"""
    print(f"执行: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"输出: {e.stdout}")
        print(f"错误: {e.stderr}")
        return False


def pre_release_checks() -> bool:
    """运行发布前检查"""
    print("运行发布前检查...")
    
    checks = [
        ("运行测试", "pytest"),
        ("代码格式化检查", "black --check src/ tests/"),
        ("类型检查", "mypy src/"),
        ("代码风格检查", "flake8 src/"),
        ("安全检查", "bandit -r src/ -q"),
    ]
    
    all_passed = True
    for name, cmd in checks:
        print(f"\n--- {name} ---")
        if not run_command(cmd):
            all_passed = False
            print(f"{name} 失败")
    
    return all_passed


def build_packages() -> bool:
    """构建发布包"""
    print("构建发布包...")
    
    # 清理旧的构建文件
    run_command("rm -rf dist/ build/ *.egg-info/")
    
    # 安装构建工具
    run_command("pip install build twine")
    
    # 构建
    if not run_command("python -m build"):
        return False
    
    # 检查包
    if not run_command("twine check dist/*"):
        return False
    
    return True


def create_git_tag(version: str, message: Optional[str] = None) -> bool:
    """创建 Git 标签"""
    tag = f"v{version}"
    if message is None:
        message = f"Release {tag}"
    
    print(f"创建 Git 标签 {tag}")
    
    # 检查是否有未提交的更改
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    if result.stdout.strip():
        print("警告：有未提交的更改")
        response = input("是否继续？(y/N): ")
        if response.lower() != "y":
            return False
    
    # 创建标签
    commands = [
        f'git tag -a {tag} -m "{message}"',
        f'git push origin {tag}',
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            return False
    
    return True


def update_changelog(version: str, changes: str) -> bool:
    """更新变更日志"""
    print(f"更新变更日志 {version}")
    
    if not CHANGELOG_PATH.exists():
        print("警告：CHANGELOG.md 不存在")
        return True
    
    with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 查找未发布部分
    unreleased_pattern = r"## \[未发布\](.*?)## \["
    match = re.search(unreleased_pattern, content, re.DOTALL)
    if not match:
        print("未找到 [未发布] 部分")
        return False
    
    unreleased_content = match.group(1).strip()
    if not unreleased_content:
        print("警告：[未发布] 部分为空")
    
    # 替换为版本号
    today = subprocess.run(
        "date +%Y-%m-%d",
        shell=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    
    new_section = f"## [{version}] - {today}\n\n{unreleased_content}\n\n"
    new_content = content.replace(
        f"## [未发布]\n\n{unreleased_content}",
        f"## [未发布]\n\n### 新增\n- 待添加\n\n### 变更\n- 待添加\n\n### 修复\n- 待添加\n\n{new_section}",
    )
    
    with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("变更日志已更新")
    return True


def main():
    parser = argparse.ArgumentParser(description="LOOM 版本管理和发布脚本")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # version 子命令
    version_parser = subparsers.add_parser("version", help="版本管理")
    version_parser.add_argument("action", choices=["get", "set", "bump"],
                               help="操作类型")
    version_parser.add_argument("value", nargs="?", help="版本号或 bump 类型")
    
    # check 子命令
    subparsers.add_parser("check", help="运行发布前检查")
    
    # build 子命令
    subparsers.add_parser("build", help="构建发布包")
    
    # tag 子命令
    tag_parser = subparsers.add_parser("tag", help="创建 Git 标签")
    tag_parser.add_argument("--message", "-m", help="标签消息")
    
    # release 子命令
    release_parser = subparsers.add_parser("release", help="完整发布流程")
    release_parser.add_argument("--dry-run", action="store_true",
                               help="干运行，不实际执行")
    
    args = parser.parse_args()
    
    if args.command == "version":
        if args.action == "get":
            print(get_current_version())
        elif args.action == "set":
            if not args.value:
                print("错误：需要提供版本号")
                sys.exit(1)
            update_version(args.value)
        elif args.action == "bump":
            current = get_current_version()
            parts = list(map(int, current.split(".")))
            if args.value == "major":
                parts[0] += 1
                parts[1] = 0
                parts[2] = 0
            elif args.value == "minor":
                parts[1] += 1
                parts[2] = 0
            elif args.value == "patch":
                parts[2] += 1
            else:
                print(f"错误：未知的 bump 类型 {args.value}")
                sys.exit(1)
            new_version = ".".join(map(str, parts))
            update_version(new_version)
    
    elif args.command == "check":
        if pre_release_checks():
            print("所有检查通过")
            sys.exit(0)
        else:
            print("检查失败")
            sys.exit(1)
    
    elif args.command == "build":
        if build_packages():
            print("构建成功")
            sys.exit(0)
        else:
            print("构建失败")
            sys.exit(1)
    
    elif args.command == "tag":
        version = get_current_version()
        if create_git_tag(version, args.message):
            print("标签创建成功")
            sys.exit(0)
        else:
            print("标签创建失败")
            sys.exit(1)
    
    elif args.command == "release":
        print("开始完整发布流程")
        version = get_current_version()
        
        steps = [
            ("运行发布前检查", lambda: pre_release_checks()),
            ("构建发布包", lambda: build_packages()),
            ("更新变更日志", lambda: update_changelog(version, "自动发布")),
            ("创建 Git 标签", lambda: create_git_tag(version, f"Release v{version}")),
        ]
        
        for name, step in steps:
            print(f"\n=== {name} ===")
            if args.dry_run:
                print(f"[干运行] 跳过 {name}")
                continue
            if not step():
                print(f"失败: {name}")
                sys.exit(1)
        
        print("\n发布流程完成！")
        print("下一步：")
        print("1. 上传到 PyPI: twine upload dist/*")
        print("2. 创建 GitHub Release")
        print("3. 更新 Docker 镜像")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()