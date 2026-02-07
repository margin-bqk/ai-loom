#!/usr/bin/env python3
"""
整理docs文档为mkdocs格式
"""

import os
import shutil
from pathlib import Path

# 文档映射：源文件 -> 目标路径
DOC_MAPPING = {
    # index.md - 文档首页
    "README.md": "index.md",
    # quick-start/ - 快速开始
    # 这些需要从现有文档提取或创建新内容
    # user-guide/ - 用户指南
    "USER_GUIDE.md": "user-guide/getting-started.md",
    "WORLD_BUILDING_GUIDE.md": "reference/world-building-guide.md",
    "CLI_USAGE.md": "user-guide/cli-reference/basic-commands.md",
    "API_REFERENCE.md": "user-guide/api-usage/http-api.md",
    # development/ - 开发指南
    "CONTRIBUTING.md": "development/contributing.md",
    "CODE_QUALITY_STANDARDS.md": "development/code-standards.md",
    "TESTING_GUIDE.md": "development/testing-guide.md",
    "EXTENSION_DEVELOPMENT_GUIDE.md": "development/extension-development.md",
    "PERFORMANCE_BENCHMARKS.md": "development/performance-benchmarks.md",
    # deployment/ - 部署指南
    "DEPLOYMENT_GUIDE.md": "deployment/deployment-guide.md",
    "DEPLOYMENT_TROUBLESHOOTING.md": "deployment/troubleshooting.md",
    "UPGRADE_GUIDE.md": "deployment/upgrade-guide.md",
    "RELEASE_PROCESS.md": "deployment/release-process.md",
    # reference/ - 参考文档
    "TEST_COVERAGE_REPORT.md": "reference/test-coverage.md",
    "TEST_TOOLS.md": "reference/test-tools.md",
    "DOCUMENTATION_VALIDATION.md": "reference/documentation-validation.md",
    "RELEASE_NOTES_v0.10.0.md": "reference/release-notes/v0.10.0.md",
    "TEST_REPORT_PHASE1.md": "reference/test-report-phase1.md",
}


def organize_docs():
    """整理文档"""
    docs_dir = Path("docs")

    # 首先，移动所有映射的文件
    for src_name, dst_path in DOC_MAPPING.items():
        src_file = docs_dir / src_name
        dst_file = docs_dir / dst_path

        if src_file.exists():
            # 确保目标目录存在
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            # 移动文件
            print(f"移动: {src_name} -> {dst_path}")
            shutil.move(str(src_file), str(dst_file))
        else:
            print(f"警告: 源文件不存在: {src_name}")

    # 检查是否有未处理的文件
    print("\n检查未处理的文件:")
    for file in docs_dir.glob("*.md"):
        if file.name not in DOC_MAPPING:
            print(f"  未处理: {file.name}")

    # 创建必要的占位符文件
    create_placeholder_files(docs_dir)

    print("\n文档整理完成!")


def create_placeholder_files(docs_dir):
    """创建必要的占位符文件"""
    placeholders = [
        # quick-start/
        "quick-start/install-and-run.md",
        "quick-start/first-example.md",
        "quick-start/basic-configuration.md",
        "quick-start/verify-installation.md",
        # user-guide/
        "user-guide/cli-reference/run-command.md",
        "user-guide/cli-reference/session-command.md",
        "user-guide/cli-reference/config-command.md",
        "user-guide/cli-reference/examples.md",
        "user-guide/api-usage/quick-api-start.md",
        "user-guide/api-usage/python-client.md",
        "user-guide/api-usage/api-examples.md",
        "user-guide/configuration/config-files.md",
        "user-guide/configuration/environment-vars.md",
        "user-guide/configuration/llm-providers.md",
        "user-guide/configuration/advanced-config.md",
        "user-guide/practical-examples/basic-narrative.md",
        "user-guide/practical-examples/fantasy-example.md",
        "user-guide/practical-examples/sci-fi-example.md",
        "user-guide/practical-examples/interactive-example.md",
        # development/
        "development/setup-development.md",
        "development/code-organization.md",
        "development/debugging-guide.md",
        # deployment/
        "deployment/local-deployment.md",
        "deployment/docker-deployment.md",
        "deployment/cloud-deployment.md",
        "deployment/monitoring.md",
        # reference/
        "reference/architecture-overview.md",
        "reference/performance-tuning.md",
        "reference/security-guide.md",
    ]

    for placeholder in placeholders:
        file_path = docs_dir / placeholder
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {file_path.stem.replace('-', ' ').title()}\n\n")
                f.write("> 此文档正在编写中，敬请期待。\n\n")
                f.write("## 概述\n\n")
                f.write("本文档将详细介绍相关内容。\n")
            print(f"创建占位符: {placeholder}")


if __name__ == "__main__":
    organize_docs()
