#!/usr/bin/env python3
"""
验证LOOM项目术语一致性
检查是否还有未更新的"游戏引擎"相关术语
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 需要检查的术语模式
TERM_PATTERNS = [
    r"\b游戏引擎\b",
    r"\b叙事引擎\b",
    r"\b引擎\b(?!.*解释器)",  # 匹配"引擎"但不匹配"解释器引擎"中的引擎
    r"\bLanguage-Oriented Ontology Machine\b",
    r"\b非承载式叙事引擎\b",
]

# 需要检查的文件扩展名
TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".html",
    ".css",
    ".js",
}

# 需要检查的目录
TARGET_DIRS = [
    "docs/",
    "examples/",
    "templates/",
    "src/loom/",
    "scripts/",
    "config/",
]

# 排除的文件和目录
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dll",
    "*.exe",
    "*.bin",
    "update_terminology.py",  # 排除术语更新脚本本身
    "verify_terminology.py",  # 排除验证脚本本身
]


def should_check_file(filepath: Path) -> bool:
    """判断是否应该检查该文件"""
    # 检查扩展名
    if filepath.suffix.lower() not in TEXT_EXTENSIONS:
        return False

    # 检查排除模式
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath_str:
            return False

    return True


def check_file_for_terms(filepath: Path) -> List[Tuple[str, int, str]]:
    """检查文件中的术语"""
    issues = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern in TERM_PATTERNS:
                matches = re.findall(pattern, line)
                if matches:
                    for match in matches:
                        issues.append((match, line_num, line.strip()))

    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                content = f.read()

            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                for pattern in TERM_PATTERNS:
                    matches = re.findall(pattern, line)
                    if matches:
                        for match in matches:
                            issues.append((match, line_num, line.strip()))
        except:
            pass
    except Exception as e:
        print(f"  读取文件 {filepath} 时出错: {e}")

    return issues


def check_directory(directory: Path) -> Dict[str, List[Tuple[str, int, str]]]:
    """检查目录中的所有文件"""
    results = {}

    for root, dirs, files in os.walk(directory):
        # 过滤排除的目录
        dirs[:] = [
            d for d in dirs if not any(pattern in d for pattern in EXCLUDE_PATTERNS)
        ]

        for file in files:
            filepath = Path(root) / file
            if should_check_file(filepath):
                issues = check_file_for_terms(filepath)
                if issues:
                    results[str(filepath)] = issues

    return results


def main():
    """主函数"""
    print("LOOM项目术语一致性验证")
    print("=" * 60)

    base_dir = Path.cwd()
    print(f"工作目录: {base_dir}")

    all_issues = {}

    for target_dir in TARGET_DIRS:
        target_path = base_dir / target_dir
        if target_path.exists():
            print(f"\n检查目录: {target_dir}")
            issues = check_directory(target_path)
            if issues:
                all_issues.update(issues)
                print(f"  发现 {len(issues)} 个文件有术语问题")
            else:
                print(f"  ✓ 无术语问题")
        else:
            print(f"\n跳过不存在的目录: {target_dir}")

    # 检查根目录下的文件
    print(f"\n检查根目录文件")
    for file in base_dir.iterdir():
        if file.is_file() and should_check_file(file):
            issues = check_file_for_terms(file)
            if issues:
                all_issues[str(file)] = issues

    print("\n" + "=" * 60)

    if all_issues:
        print(f"发现 {len(all_issues)} 个文件存在术语不一致问题:")
        print("-" * 60)

        total_issues = 0
        for filepath, issues in all_issues.items():
            print(f"\n{filepath}:")
            for term, line_num, line in issues:
                print(f"  第 {line_num} 行: '{term}' -> {line[:80]}...")
                total_issues += 1

        print(f"\n总计: {total_issues} 处术语问题需要修复")
        print("\n建议修复方法:")
        print("1. 运行 scripts/update_terminology.py 脚本")
        print("2. 手动更新上述文件中的术语")
        print("3. 重新运行此验证脚本确认修复")

        return 1
    else:
        print("✓ 所有文件术语一致!")
        print("✓ 项目定位重构 - 文档和术语更新完成")
        return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
