#!/usr/bin/env python3
"""
检查VSCode标签中不存在的文件
用于清理VSCode标签残留
"""

import os
import sys
from pathlib import Path
from datetime import datetime


def check_vscode_tabs(tab_files):
    """检查VSCode标签文件是否存在"""
    missing_files = []
    existing_files = []

    for file_path in tab_files:
        path = Path(file_path)
        if path.exists():
            existing_files.append(str(path))
        else:
            missing_files.append(str(path))

    return existing_files, missing_files


def generate_report(existing_files, missing_files):
    """生成检查报告"""
    report = f"""# VSCode标签文件检查报告

## 检查时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 标签文件统计
- 总标签数: {len(existing_files) + len(missing_files)}
- 存在的文件: {len(existing_files)}
- 不存在的文件: {len(missing_files)}

## 存在的文件 ({len(existing_files)}个)
"""

    if existing_files:
        for file in existing_files:
            report += f"- `{file}`\n"
    else:
        report += "无\n"

    report += f"\n## 不存在的文件（标签残留） ({len(missing_files)}个)\n"

    if missing_files:
        for file in missing_files:
            report += f"- `{file}`\n"

        report += "\n## 清理建议\n"
        report += "这些文件已不存在，但VSCode标签中仍有残留。建议：\n"
        report += "1. 在VSCode中手动关闭这些标签\n"
        report += "2. 或使用VSCode命令：`View: Close All Editors` 关闭所有编辑器\n"
        report += "3. 或使用VSCode命令：`View: Close Editor` 逐个关闭\n"
    else:
        report += "无标签残留，所有文件都存在。\n"

    return report


def main():
    # 从环境变量或参数获取标签文件列表
    # 这里我们硬编码从环境详情中看到的标签
    tab_files = [
        "scripts/organize_docs.py",
        "docs/mkdocs.yml",
        "docs/quick-start/install-and-run.md",
        "docs/quick-start/basic-configuration.md",
        "docs/quick-start/first-example.md",
        "docs/quick-start/verify-installation.md",
        "docs/user-guide/cli-reference/config-command.md",
        "docs/user-guide/cli-reference/session-command.md",
        "docs/development/setup-development.md",
        "docs/development/code-organization.md",
        "docs/deployment/local-deployment.md",
        "docs/reference/architecture-overview.md",
        "src/loom/cli/commands/export.py",
        "src/loom/cli/commands/init.py",
        "src/loom/cli/commands/__init__.py",
        "test_input.txt",
        "test_db.py",
        "test_session_db.py",
        "src/loom/cli/commands/session.py",
        "test_session_db_fixed.py",
    ]

    print("=" * 60)
    print("检查VSCode标签文件状态")
    print("=" * 60)

    existing_files, missing_files = check_vscode_tabs(tab_files)

    print(f"\n检查完成:")
    print(f"  存在的文件: {len(existing_files)} 个")
    print(f"  不存在的文件: {len(missing_files)} 个")

    if missing_files:
        print(f"\n不存在的文件（标签残留）:")
        for file in missing_files:
            print(f"  - {file}")

        print(f"\n建议清理这些VSCode标签残留。")

    # 生成报告
    from datetime import datetime

    report = generate_report(existing_files, missing_files)

    # 保存报告
    report_path = Path("vscode_tabs_check_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已保存到: {report_path}")

    return len(missing_files)


if __name__ == "__main__":
    sys.exit(main())
