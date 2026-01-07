"""
运行世界会话命令

支持交互式运行、批处理运行、从文件加载会话等
"""

import typer
import asyncio
from pathlib import Path
from typing import Optional, List
import sys

from ...core.session_manager import SessionManager, SessionConfig
from ...core.config_manager import ConfigManager
from ...rules.rule_loader import RuleLoader
from ...utils.logging_config import setup_logging

app = typer.Typer(
    name="run",
    help="运行世界会话",
    no_args_is_help=True,
)

@app.command("interactive")
def run_interactive(
    canon: str = typer.Option(
        "./canon/default.md", "--canon", "-c", help="规则文件路径"
    ),
    name: str = typer.Option(
        "New Session", "--name", "-n", help="会话名称"
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="LLM提供商"
    ),
    max_turns: Optional[int] = typer.Option(
        None, "--max-turns", "-m", help="最大回合数"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="输出文件路径"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """交互式运行会话"""
    typer.echo(f"启动交互式会话: {name}")
    typer.echo(f"规则文件: {canon}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_run_interactive_async(
        canon, name, provider, max_turns, output
    ))

async def _run_interactive_async(
    canon_path: str,
    session_name: str,
    provider: Optional[str],
    max_turns: Optional[int],
    output: Optional[str],
):
    """异步交互式运行"""
    from ...core.persistence_engine import SQLitePersistence
    from ...interpretation.reasoning_pipeline import ReasoningPipeline
    
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
            name=session_name,
            canon_path=canon_path,
            llm_provider=provider or config.session_defaults.default_llm_provider,
            max_turns=max_turns,
            metadata={
                "run_mode": "interactive",
                "cli": True,
            }
        )
        
        # 创建会话
        session = await session_manager.create_session(session_config)
        typer.echo(f"会话创建成功: {session.id}")
        
        # 初始化推理管道
        pipeline = ReasoningPipeline(
            session_manager=session_manager,
            config_manager=config_manager,
            persistence=persistence
        )
        
        # 启动交互式循环
        typer.echo("\n=== 交互式会话开始 ===")
        typer.echo("输入 'quit' 退出，'help' 查看帮助")
        
        while True:
            try:
                # 显示提示
                user_input = typer.prompt(f"[Turn {session.current_turn}] > ")
                
                if user_input.lower() == 'quit':
                    typer.echo("退出会话")
                    break
                elif user_input.lower() == 'help':
                    typer.echo("可用命令:")
                    typer.echo("  quit - 退出会话")
                    typer.echo("  help - 显示此帮助")
                    typer.echo("  status - 显示会话状态")
                    typer.echo("  save - 保存会话")
                    typer.echo("  其他输入将作为叙事输入处理")
                    continue
                elif user_input.lower() == 'status':
                    stats = await session_manager.get_session_stats(session.id)
                    if stats:
                        typer.echo(f"会话状态: {stats['status']}")
                        typer.echo(f"当前回合: {stats['current_turn']}")
                        typer.echo(f"总回合数: {stats['total_turns']}")
                    continue
                elif user_input.lower() == 'save':
                    await session_manager.save_session(session, force=True)
                    typer.echo("会话已保存")
                    continue
                
                # 处理叙事输入
                typer.echo("处理中...")
                result = await pipeline.process_turn(
                    session_id=session.id,
                    user_input=user_input,
                    intervention_type="player_input"
                )
                
                if result and result.get("success"):
                    typer.echo(f"结果: {result.get('response', '无响应')}")
                else:
                    typer.echo(f"错误: {result.get('error', '未知错误')}")
                
                # 检查是否达到最大回合数
                if max_turns and session.current_turn >= max_turns:
                    typer.echo(f"达到最大回合数 {max_turns}，会话结束")
                    break
                    
            except KeyboardInterrupt:
                typer.echo("\n中断会话")
                break
            except Exception as e:
                typer.echo(f"错误: {e}")
                continue
        
        # 保存最终状态
        await session_manager.save_session(session, force=True)
        typer.echo(f"会话已保存到: {config.data_dir}/sessions/{session.id}.json")
        
        # 如果有输出文件，导出会话
        if output:
            await _export_session(session.id, output, persistence)
        
    except Exception as e:
        typer.echo(f"启动会话失败: {e}", err=True)
        sys.exit(1)

async def _export_session(session_id: str, output_path: str, persistence):
    """导出会话"""
    try:
        session_data = await persistence.load_session(session_id)
        if session_data:
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            typer.echo(f"会话已导出到: {output_path}")
    except Exception as e:
        typer.echo(f"导出会话失败: {e}")

@app.command("batch")
def run_batch(
    input_file: str = typer.Argument(..., help="输入文件路径（JSON或文本）"),
    canon: str = typer.Option(
        "./canon/default.md", "--canon", "-c", help="规则文件路径"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="会话名称"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="输出文件路径"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """批处理运行会话"""
    typer.echo(f"批处理运行: {input_file}")
    # 实现批处理逻辑
    typer.echo("批处理功能待实现")

@app.command("resume")
def resume_session(
    session_id: str = typer.Argument(..., help="会话ID"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="输出文件路径"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """恢复现有会话"""
    typer.echo(f"恢复会话: {session_id}")
    # 实现恢复逻辑
    typer.echo("恢复功能待实现")

@app.command("list")
def list_sessions(
    all: bool = typer.Option(
        False, "--all", "-a", help="显示所有会话（包括非活跃）"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """列出所有会话"""
    typer.echo("列出会话:")
    # 实现列表逻辑
    typer.echo("列表功能待实现")

if __name__ == "__main__":
    app()