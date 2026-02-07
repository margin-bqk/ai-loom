"""
数据导出命令

支持会话数据、规则、配置等导出功能
"""

import typer
import asyncio
from pathlib import Path
from typing import Optional, List
import json
import yaml
import csv
from datetime import datetime

from ...core.session_manager import SessionManager
from ...core.config_manager import ConfigManager
from ...core.persistence_engine import SQLitePersistence
from ...rules.rule_loader import RuleLoader
from ...utils.logging_config import setup_logging

app = typer.Typer(
    name="export",
    help="数据导出",
    no_args_is_help=True,
)


@app.command("session")
def export_session(
    session_id: str = typer.Argument(..., help="会话ID"),
    output: str = typer.Option(
        None, "--output", "-o", help="输出文件路径（默认：session_{id}.json）"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="输出格式 (json, yaml, csv)"
    ),
    include_memory: bool = typer.Option(
        False, "--include-memory", "-m", help="包含记忆数据"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """导出会话数据"""
    typer.echo(f"导出会话: {session_id}")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_export_session_async(session_id, output, format, include_memory))


async def _export_session_async(
    session_id: str,
    output_path: Optional[str],
    output_format: str,
    include_memory: bool,
):
    """异步导出会话"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # 初始化持久化引擎
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()

        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)

        # 加载会话
        session = await session_manager.load_session(session_id)
        if not session:
            typer.echo(f"会话 {session_id} 不存在", err=True)
            return

        # 构建导出数据
        export_data = session.to_dict()

        # 包含记忆数据
        if include_memory:
            # 获取记忆数据（需要实现记忆查询）
            memory_data = await _get_session_memory(session_id, persistence)
            export_data["memory"] = memory_data

        # 确定输出路径
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"session_{session_id}_{timestamp}.{output_format}"

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            if output_format == "json":
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            elif output_format == "yaml":
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)
            elif output_format == "csv":
                # 简化CSV导出（仅基本信息）
                writer = csv.writer(f)
                writer.writerow(["字段", "值"])
                writer.writerow(["session_id", session_id])
                writer.writerow(["name", session.name])
                writer.writerow(["status", session.status.value])
                writer.writerow(["current_turn", session.current_turn])
                writer.writerow(["total_turns", session.total_turns])
                writer.writerow(["created_at", session.created_at.isoformat()])
                writer.writerow(["llm_provider", session.config.llm_provider])
            else:
                typer.echo(f"不支持的格式: {output_format}", err=True)
                return

        typer.echo(f"会话已导出到: {output_path}")
        typer.echo(f"格式: {output_format}")
        typer.echo(f"包含记忆: {'是' if include_memory else '否'}")

    except Exception as e:
        typer.echo(f"导出会话失败: {e}", err=True)


async def _get_session_memory(session_id: str, persistence) -> dict:
    """获取会话记忆数据"""
    # 这是一个简化实现，实际需要根据持久化引擎实现
    try:
        # 尝试从持久化引擎获取记忆
        if hasattr(persistence, "get_session_memory"):
            return await persistence.get_session_memory(session_id)
    except:
        pass

    return {"note": "记忆数据获取功能待实现"}


@app.command("sessions")
def export_sessions(
    output: str = typer.Option(
        "sessions_export.json", "--output", "-o", help="输出文件路径"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="输出格式 (json, yaml, csv)"
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="按状态过滤(active, paused, completed, archived, error)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """导出所有会话"""
    typer.echo("导出所有会话...")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_export_sessions_async(output, format, status))


async def _export_sessions_async(
    output_path: str,
    output_format: str,
    status_filter: Optional[str],
):
    """异步导出所有会话"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # 初始化持久化引擎
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()

        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)

        # 获取所有会话
        sessions = await session_manager.list_sessions(include_inactive=True)

        # 应用状态过滤
        if status_filter:
            from ...core.session_manager import SessionStatus

            try:
                filter_status = SessionStatus(status_filter)
                sessions = {
                    sid: sess
                    for sid, sess in sessions.items()
                    if sess.status == filter_status
                }
            except ValueError:
                typer.echo(f"无效的状态值: {status_filter}", err=True)
                return

        # 构建导出数据
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "sessions": {},
        }

        for session_id, session in sessions.items():
            export_data["sessions"][session_id] = session.to_dict()

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            if output_format == "json":
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            elif output_format == "yaml":
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)
            elif output_format == "csv":
                # 简化CSV导出
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "session_id",
                        "name",
                        "status",
                        "current_turn",
                        "total_turns",
                        "created_at",
                        "llm_provider",
                    ]
                )
                for session_id, session in sessions.items():
                    writer.writerow(
                        [
                            session_id,
                            session.name,
                            session.status.value,
                            session.current_turn,
                            session.total_turns,
                            session.created_at.isoformat(),
                            session.config.llm_provider,
                        ]
                    )
            else:
                typer.echo(f"不支持的格式: {output_format}", err=True)
                return

        typer.echo(f"会话已导出到: {output_path}")
        typer.echo(f"格式: {output_format}")
        typer.echo(f"会话数量: {len(sessions)}")
        if status_filter:
            typer.echo(f"状态过滤: {status_filter}")

    except Exception as e:
        typer.echo(f"导出会话失败: {e}", err=True)
