"""
数据导出命令

支持会话数据、规则、配置等导出功能�?"""

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
        None, "--output", "-o", help="输出文件路径（默认：session_{id}.json�?
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="输出格式 (json, yaml, csv)"
    ),
    include_memory: bool = typer.Option(
        False, "--include-memory", "-m", help="包含记忆数据"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
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
            typer.echo(f"会话 {session_id} 不存�?, err=True)
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
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_format == "json":
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            elif output_format == "yaml":
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)
            elif output_format == "csv":
                # 简化CSV导出（仅基本信息�?                writer = csv.writer(f)
                writer.writerow(["字段", "�?])
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
        
        typer.echo(f"�?会话已导出到: {output_path}")
        typer.echo(f"格式: {output_format}")
        typer.echo(f"包含记忆: {'�? if include_memory else '�?}")
        
    except Exception as e:
        typer.echo(f"导出会话失败: {e}", err=True)

async def _get_session_memory(session_id: str, persistence) -> dict:
    """获取会话记忆数据"""
    # 这是一个简化实现，实际需要根据持久化引擎实现
    try:
        # 尝试从持久化引擎获取记忆
        if hasattr(persistence, 'get_session_memory'):
            return await persistence.get_session_memory(session_id)
    except:
        pass
    
    return {"note": "记忆数据获取功能待实�?}

@app.command("sessions")
def export_sessions(
    output: str = typer.Option(
        "sessions_export.json", "--output", "-o", help="输出文件路径"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="输出格式 (json, yaml, csv)"
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="按状态过�?(active, paused, completed, archived, error)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """导出所有会�?""
    typer.echo("导出所有会�?..")
    
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
    """异步导出所有会�?""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 初始化持久化引擎
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()
        
        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)
        
        # 获取所有会�?        sessions = await session_manager.list_sessions(include_inactive=True)
        
        # 应用状态过�?        if status_filter:
            from ...core.session_manager import SessionStatus
            try:
                filter_status = SessionStatus(status_filter)
                sessions = {sid: sess for sid, sess in sessions.items() 
                           if sess.status == filter_status}
            except ValueError:
                typer.echo(f"无效的状态�? {status_filter}", err=True)
                return
        
        # 构建导出数据
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "sessions": {}
        }
        
        for session_id, session in sessions.items():
            export_data["sessions"][session_id] = session.to_dict()
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_format == "json":
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            elif output_format == "yaml":
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)
            elif output_format == "csv":
                # 简化CSV导出
                writer = csv.writer(f)
                writer.writerow(["session_id", "name", "status", "current_turn", "total_turns", "created_at", "llm_provider"])
                for session_id, session in sessions.items():
                    writer.writerow([
                        session_id,
                        session.name,
                        session.status.value,
                        session.current_turn,
                        session.total_turns,
                        session.created_at.isoformat(),
                        session.config.llm_provider
                    ])
            else:
                typer.echo(f"不支持的格式: {output_format}", err=True)
                return
        
        typer.echo(f"�?会话已导出到: {output_path}")
        typer.echo(f"格式: {output_format}")
        typer.echo(f"会话数量: {len(sessions)}")
        if status_filter:
            typer.echo(f"状态过�? {status_filter}")
        
    except Exception as e:
        typer.echo(f"导出会话失败: {e}", err=True)

@app.command("rules")
def export_rules(
    canon: Optional[str] = typer.Option(
        None, "--canon", "-c", help="规则集名称（如未指定则导出所有）"
    ),
    output: str = typer.Option(
        "rules_export.json", "--output", "-o", help="输出文件路径"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="输出格式 (json, yaml, markdown)"
    ),
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="规则目录路径"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """导出规则�?""
    if canon:
        typer.echo(f"导出规则�? {canon}")
    else:
        typer.echo("导出所有规则集...")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_export_rules_async(canon, output, format, path))

async def _export_rules_async(
    canon_name: Optional[str],
    output_path: str,
    output_format: str,
    rules_path: Optional[str],
):
    """异步导出规则"""
    try:
        # 初始化规则加载器
        if rules_path:
            loader = RuleLoader(canon_dir=rules_path, recursive=True)
        else:
            loader = RuleLoader(recursive=True)
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "source_dir": str(loader.canon_dir)
        }
        
        if canon_name:
            # 导出单个规则�?            canon = loader.load_canon(canon_name)
            if not canon:
                typer.echo(f"规则�?{canon_name} 不存�?, err=True)
                return
            
            export_data["canon"] = canon_name
            export_data["metadata"] = canon.metadata
            export_data["sections"] = canon.sections
            
            # 对于markdown格式，直接导出原始内�?            if output_format == "markdown":
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(canon.get_full_text())
                typer.echo(f"�?规则集已导出�? {output_path}")
                typer.echo(f"格式: {output_format}")
                return
        else:
            # 导出所有规则集
            canons = loader.load_all_canons()
            export_data["total_canons"] = len(canons)
            export_data["canons"] = {}
            
            for name, canon in canons.items():
                export_data["canons"][name] = {
                    "metadata": canon.metadata,
                    "sections": canon.sections,
                    "path": str(canon.path)
                }
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_format == "json":
                # 自定义序列化函数处理复杂对象
                def default_serializer(obj):
                    if hasattr(obj, '__dict__'):
                        return obj.__dict__
                    return str(obj)
                
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=default_serializer)
            elif output_format == "yaml":
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)
            else:
                typer.echo(f"不支持的格式: {output_format}", err=True)
                return
        
        typer.echo(f"�?规则已导出到: {output_path}")
        typer.echo(f"格式: {output_format}")
        if canon_name:
            typer.echo(f"规则�? {canon_name}")
        else:
            typer.echo(f"规则集数�? {export_data.get('total_canons', 1)}")
        
    except Exception as e:
        typer.echo(f"导出规则失败: {e}", err=True)

@app.command("config")
def export_config_cmd(
    output: str = typer.Option(
        "config_export.yaml", "--output", "-o", help="输出文件路径"
    ),
    format: str = typer.Option(
        "yaml", "--format", "-f", help="输出格式 (yaml, json)"
    ),
    include_secrets: bool = typer.Option(
        False, "--include-secrets", "-s", help="包含敏感信息（如API密钥�?
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """导出配置（config命令的别名）"""
    # 重用config命令的导出功�?    from .config import _export_config_async
    typer.echo(f"导出配置�? {output}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_export_config_async(output, format, include_secrets))

@app.command("all")
def export_all(
    output_dir: str = typer.Option(
        "loom_export", "--output-dir", "-o", help="输出目录路径"
    ),
    include_secrets: bool = typer.Option(
        False, "--include-secrets", "-s", help="包含敏感信息"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """导出所有数据（会话、规则、配置）"""
    typer.echo(f"导出所有数据到目录: {output_dir}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_export_all_async(output_dir, include_secrets))

async def _export_all_async(output_dir: str, include_secrets: bool):
    """异步导出所有数�?""
    try:
        # 创建输出目录
        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 导出配置
        config_path = export_dir / f"config_{timestamp}.yaml"
        from .config import _export_config_async
        await _export_config_async(str(config_path), "yaml", include_secrets)
        
        # 导出规则
        rules_path = export_dir / f"rules_{timestamp}.json"
        await _export_rules_async(None, str(rules_path), "json", None)
        
        # 导出会话
        sessions_path = export_dir / f"sessions_{timestamp}.json"
        await _export_sessions_async(str(sessions_path), "json", None)
        
        # 创建元数据文�?        metadata = {
            "exported_at": datetime.now().isoformat(),
            "export_version": "1.0",
            "components": ["config", "rules", "sessions"],
            "files": {
                "config": str(config_path.name),
                "rules": str(rules_path.name),
                "sessions": str(sessions_path.name)
            }
        }
        
        metadata_path = export_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        typer.echo("�?所有数据导出完�?)
        typer.echo(f"导出目录: {export_dir}")
        typer.echo(f"包含文件:")
        typer.echo(f"  �?{config_path.name} - 配置")
        typer.echo(f"  �?{rules_path.name} - 规则")
        typer.echo(f"  �?{sessions_path.name} - 会话")
        typer.echo(f"  �?metadata.json - 元数�?)
        
    except Exception as e:
        typer.echo(f"导出所有数据失�? {e}", err=True)

if __name__ == "__main__":
    app()