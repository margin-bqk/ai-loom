"""
LOOM CLI 入口点

提供命令行界面，支持会话管理、规则编辑、世界运行等核心功能。
使用 Typer 构建，支持交互式模式和批处理模式。
"""

import typer
from typing import Optional, List
from pathlib import Path
import sys
import asyncio

from . import commands

# 创建 Typer 应用
app = typer.Typer(
    name="loom",
    help="Language-Oriented Ontology Machine - 基于Markdown规则的非承载叙事引擎",
    add_completion=False,
    no_args_is_help=True,
)

# 注册子命令
app.add_typer(commands.run.app, name="run", help="运行世界会话")
app.add_typer(commands.session.app, name="session", help="会话管理")
app.add_typer(commands.rules.app, name="rules", help="规则管理")
app.add_typer(commands.config.app, name="config", help="配置管理")
app.add_typer(commands.export.app, name="export", help="数据导出")
app.add_typer(commands.dev.app, name="dev", help="开发工具")

# 添加版本命令
@app.command("version")
def version():
    """显示 LOOM 版本"""
    from .. import __version__
    typer.echo(f"LOOM v{__version__}")

# 添加初始化命令
@app.command("init")
def init(
    path: Optional[str] = typer.Option(
        ".", "--path", "-p", help="初始化目录路径"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="强制覆盖现有配置"
    )
):
    """初始化 LOOM 项目"""
    from .commands.init import init_project
    init_project(path, force)

# 添加状态命令
@app.command("status")
def status(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="显示详细信息"
    )
):
    """显示系统状态"""
    from .commands.status import show_status
    show_status(verbose)

# 添加帮助命令
@app.command("help")
def help_command():
    """显示帮助信息"""
    typer.echo("LOOM 命令行工具")
    typer.echo("\n可用命令:")
    typer.echo("  loom run        - 运行世界会话")
    typer.echo("  loom session    - 会话管理")
    typer.echo("  loom rules      - 规则管理")
    typer.echo("  loom config     - 配置管理")
    typer.echo("  loom export     - 数据导出")
    typer.echo("  loom dev        - 开发工具")
    typer.echo("  loom init       - 初始化项目")
    typer.echo("  loom status     - 显示系统状态")
    typer.echo("  loom version    - 显示版本")
    typer.echo("  loom help       - 显示此帮助")
    typer.echo("\n使用 'loom <command> --help' 获取命令详细帮助。")

# 主函数
def main():
    """CLI 主入口点"""
    app()

if __name__ == "__main__":
    main()