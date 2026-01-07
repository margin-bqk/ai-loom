"""
会话管理命令

支持创建、删除、列出、查看会话等操作。
"""

import typer
import asyncio
from typing import Optional, List
import json
from pathlib import Path

from ...core.session_manager import SessionManager, SessionConfig, SessionStatus
from ...core.config_manager import ConfigManager
from ...core.persistence_engine import SQLitePersistence
from ...utils.logging_config import setup_logging

app = typer.Typer(
    name="session",
    help="会话管理",
    no_args_is_help=True,
)

@app.command("create")
def create_session(
    name: str = typer.Option(..., "--name", "-n", help="会话名称"),
    canon: str = typer.Option(
        "./canon/default.md", "--canon", "-c", help="规则文件路径"
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="LLM提供商"
    ),
    max_turns: Optional[int] = typer.Option(
        None, "--max-turns", "-m", help="最大回合数"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="输出会话信息文件"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """创建新会话"""
    typer.echo(f"创建会话: {name}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_create_session_async(
        name, canon, provider, max_turns, output
    ))

async def _create_session_async(
    name: str,
    canon_path: str,
    provider: Optional[str],
    max_turns: Optional[int],
    output: Optional[str],
):
    """异步创建会话"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 初始化持久化引擎
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()
        
        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)
        
        # 创建会话配置
        session_config = SessionConfig(
            name=name,
            canon_path=canon_path,
            llm_provider=provider or config.session_defaults.default_llm_provider,
            max_turns=max_turns,
            metadata={
                "created_via": "cli",
                "canon_path": canon_path,
            }
        )
        
        # 创建会话
        session = await session_manager.create_session(session_config)
        
        # 显示会话信息
        typer.echo(f"会话创建成功!")
        typer.echo(f"  ID: {session.id}")
        typer.echo(f"  名称: {session.name}")
        typer.echo(f"  状态: {session.status.value}")
        typer.echo(f"  创建时间: {session.created_at}")
        typer.echo(f"  LLM提供商: {session.config.llm_provider}")
        typer.echo(f"  规则文件: {session.config.canon_path}")
        
        # 保存会话信息到文件
        if output:
            session_info = session.to_dict()
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, ensure_ascii=False, indent=2)
            typer.echo(f"会话信息已保存到: {output}")
        
        return session
        
    except Exception as e:
        typer.echo(f"创建会话失败: {e}", err=True)
        raise

@app.command("list")
def list_sessions(
    all: bool = typer.Option(
        False, "--all", "-a", help="显示所有会话（包括非活跃）"
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="按状态过滤 (active, paused, completed, archived, error)"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="输出格式 (table, json, csv)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """列出所有会话"""
    typer.echo("列出会话...")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_list_sessions_async(all, status, format))

async def _list_sessions_async(
    all_sessions: bool,
    status_filter: Optional[str],
    output_format: str,
):
    """异步列出会话"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 初始化持久化引擎
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()
        
        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)
        
        # 获取会话列表
        sessions = await session_manager.list_sessions(include_inactive=all_sessions)
        
        # 应用状态过滤
        if status_filter:
            try:
                filter_status = SessionStatus(status_filter)
                sessions = {sid: sess for sid, sess in sessions.items() 
                           if sess.status == filter_status}
            except ValueError:
                typer.echo(f"无效的状态值: {status_filter}", err=True)
                return
        
        if not sessions:
            typer.echo("没有找到会话")
            return
        
        # 按格式输出
        if output_format == "json":
            sessions_dict = {sid: sess.to_dict() for sid, sess in sessions.items()}
            typer.echo(json.dumps(sessions_dict, ensure_ascii=False, indent=2))
        elif output_format == "csv":
            typer.echo("session_id,name,status,current_turn,total_turns,created_at,llm_provider")
            for session_id, session in sessions.items():
                typer.echo(f"{session_id},{session.name},{session.status.value},{session.current_turn},{session.total_turns},{session.created_at},{session.config.llm_provider}")
        else:  # table
            from rich.console import Console
            from rich.table import Table
            
            console = Console()
            table = Table(title="LOOM 会话列表")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("名称", style="white")
            table.add_column("状态", style="green")
            table.add_column("回合", style="yellow")
            table.add_column("创建时间", style="blue")
            table.add_column("LLM提供商", style="magenta")
            
            for session_id, session in sessions.items():
                short_id = session_id[:8] + "..."
                table.add_row(
                    short_id,
                    session.name,
                    session.status.value,
                    f"{session.current_turn}/{session.total_turns}",
                    session.created_at.strftime("%Y-%m-%d %H:%M"),
                    session.config.llm_provider
                )
            
            console.print(table)
        
        typer.echo(f"总计: {len(sessions)} 个会话")
        
    except Exception as e:
        typer.echo(f"列出会话失败: {e}", err=True)

@app.command("show")
def show_session(
    session_id: str = typer.Argument(..., help="会话ID"),
    format: str = typer.Option(
        "table", "--format", "-f", help="输出格式 (table, json, yaml)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """显示会话详细信息"""
    typer.echo(f"显示会话: {session_id}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_show_session_async(session_id, format))

async def _show_session_async(session_id: str, output_format: str):
    """异步显示会话详情"""
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
        
        # 获取会话统计
        stats = await session_manager.get_session_stats(session_id)
        
        if output_format == "json":
            result = {
                "session": session.to_dict(),
                "stats": stats
            }
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif output_format == "yaml":
            import yaml
            result = {
                "session": session.to_dict(),
                "stats": stats
            }
            typer.echo(yaml.dump(result, allow_unicode=True, default_flow_style=False))
        else:  # table
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            from rich.text import Text
            
            console = Console()
            
            # 基本信息表
            info_table = Table(title="会话基本信息", show_header=False)
            info_table.add_column("字段", style="cyan")
            info_table.add_column("值", style="white")
            
            info_table.add_row("ID", session.id)
            info_table.add_row("名称", session.name)
            info_table.add_row("状态", session.status.value)
            info_table.add_row("创建时间", session.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            info_table.add_row("最后活动", session.last_activity.strftime("%Y-%m-%d %H:%M:%S"))
            info_table.add_row("当前回合", str(session.current_turn))
            info_table.add_row("总回合数", str(session.total_turns))
            info_table.add_row("LLM提供商", session.config.llm_provider)
            info_table.add_row("规则文件", session.config.canon_path)
            info_table.add_row("最大回合数", str(session.config.max_turns) if session.config.max_turns else "无限制")
            
            console.print(Panel(info_table, title="会话信息"))
            
            # 统计信息表
            if stats:
                stats_table = Table(title="会话统计", show_header=False)
                stats_table.add_column("统计项", style="cyan")
                stats_table.add_column("值", style="white")
                
                stats_table.add_row("运行时间", f"{stats.get('uptime_hours', 0):.2f} 小时")
                stats_table.add_row("回合/小时", f"{stats.get('turns_per_hour', 0):.2f}")
                
                console.print(Panel(stats_table, title="统计信息"))
            
            # 元数据
            if session.metadata:
                meta_text = Text()
                for key, value in session.metadata.items():
                    meta_text.append(f"{key}: {value}\n", style="dim")
                console.print(Panel(meta_text, title="元数据"))
        
    except Exception as e:
        typer.echo(f"显示会话失败: {e}", err=True)

@app.command("delete")
def delete_session(
    session_id: str = typer.Argument(..., help="会话ID"),
    permanent: bool = typer.Option(
        False, "--permanent", "-p", help="永久删除（否则归档）"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="强制删除，不确认"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """删除会话"""
    if not force:
        action = "永久删除" if permanent else "归档"
        confirm = typer.confirm(f"确定要{action}会话 {session_id} 吗？")
        if not confirm:
            typer.echo("操作取消")
            return
    
    typer.echo(f"{'删除' if permanent else '归档'}会话: {session_id}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_delete_session_async(session_id, permanent))

async def _delete_session_async(session_id: str, permanent: bool):
    """异步删除会话"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 初始化持久化引擎
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()
        
        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)
        
        # 删除会话
        success = await session_manager.delete_session(session_id, permanent)
        
        if success:
            action = "永久删除" if permanent else "归档"
            typer.echo(f"会话 {session_id} 已{action}")
        else:
            typer.echo(f"删除会话失败", err=True)
        
    except Exception as e:
        typer.echo(f"删除会话失败: {e}", err=True)

@app.command("update")
def update_session(
    session_id: str = typer.Argument(..., help="会话ID"),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="更新会话名称"
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="更新会话状态 (active, paused, completed, archived, error)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """更新会话属性"""
    typer.echo(f"更新会话: {session_id}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_update_session_async(session_id, name, status))

async def _update_session_async(
    session_id: str,
    new_name: Optional[str],
    new_status: Optional[str],
):
    """异步更新会话"""
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
        
        updated = False
        
        # 更新名称
        if new_name:
            session.name = new_name
            updated = True
            typer.echo(f"更新名称: {new_name}")
        
        # 更新状态
        if new_status:
            try:
                status_enum = SessionStatus(new_status)
                success = await session_manager.update_session_status(session_id, status_enum)
                if success:
                    updated = True
                    typer.echo(f"更新状态: {new_status}")
                else:
                    typer.echo(f"更新状态失败", err=True)
            except ValueError:
                typer.echo(f"无效的状态值: {new_status}", err=True)
        
        # 保存更新
        if updated:
            await session_manager.save_session(session, force=True)
            typer.echo("会话更新成功")
        else:
            typer.echo("没有需要更新的内容")
        
    except Exception as e:
        typer.echo(f"更新会话失败: {e}", err=True)

@app.command("cleanup")
def cleanup_sessions(
    max_hours: int = typer.Option(
        24, "--max-hours", "-h", help="最大不活跃小时数"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="模拟运行，不实际删除"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """清理不活跃的会话"""
    typer.echo(f"清理不活跃会话（超过 {max_hours} 小时）...")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_cleanup_sessions_async(max_hours, dry_run))

async def _cleanup_sessions_async(max_hours: int, dry_run: bool):
    """异步清理会话"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 初始化持久化引擎
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()
        
        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)
        
        # 执行清理
        count = await session_manager.cleanup_inactive_sessions(max_hours)
        
        if dry_run:
            typer.echo(f"模拟清理: 将归档 {count} 个不活跃会话")
        else:
            typer.echo(f"已归档 {count} 个不活跃会话")
        
    except Exception as e:
        typer.echo(f"清理会话失败: {e}", err=True)

if __name__ == "__main__":
    app()