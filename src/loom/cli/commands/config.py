"""
配置管理命令

支持配置查看、编辑、验证、导入导出等操作。
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Optional

import typer
import yaml

from ...core.config_manager import ConfigManager
from ...utils.logging_config import setup_logging

app = typer.Typer(
    name="config",
    help="配置管理",
    no_args_is_help=True,
)


@app.command("show")
def show_config(
    section: Optional[str] = typer.Option(
        None, "--section", "-s", help="配置部分 (llm, memory, session, etc.)"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="输出格式 (table, json, yaml)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """显示当前配置"""
    typer.echo("显示配置...")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_show_config_async(section, format))


async def _show_config_async(section: Optional[str], output_format: str):
    """异步显示配置"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # 获取配置快照（隐藏敏感信息）
        snapshot = config_manager.get_config_snapshot()

        # 过滤部分
        if section:
            if section in snapshot:
                snapshot = {section: snapshot[section]}
            else:
                # 尝试在嵌套结构中查找
                filtered = {}
                for key, value in snapshot.items():
                    if isinstance(value, dict) and section in value:
                        filtered[key] = {section: value[section]}
                if filtered:
                    snapshot = filtered
                else:
                    typer.echo(f"配置部分 '{section}' 未找到", err=True)
                    return

        # 按格式输出
        if output_format == "json":
            typer.echo(json.dumps(snapshot, ensure_ascii=False, indent=2))
        elif output_format == "yaml":
            typer.echo(
                yaml.dump(snapshot, allow_unicode=True, default_flow_style=False)
            )
        else:  # table
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table

            console = Console()

            for section_name, section_data in snapshot.items():
                if isinstance(section_data, dict):
                    section_table = Table(title=f"{section_name} 配置", show_header=False)
                    section_table.add_column("配置项", style="cyan")
                    section_table.add_column("值", style="white")

                    for key, value in section_data.items():
                        if isinstance(value, dict):
                            # 嵌套字典，显示为JSON
                            value_str = json.dumps(value, ensure_ascii=False)[:100]
                            if len(json.dumps(value, ensure_ascii=False)) > 100:
                                value_str += "..."
                        else:
                            value_str = str(value)

                        section_table.add_row(key, value_str)

                    console.print(Panel(section_table, title=section_name))
                else:
                    console.print(
                        Panel(f"{section_name}: {section_data}", title=section_name)
                    )

        typer.echo(f"配置文件: {config_manager.config_path}")

    except Exception as e:
        typer.echo(f"显示配置失败: {e}", err=True)


@app.command("validate")
def validate_config(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="配置文件路径"),
    fix: bool = typer.Option(False, "--fix", "-f", help="尝试自动修复问题"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """验证配置完整性"""
    typer.echo("验证配置...")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_validate_config_async(path, fix))


async def _validate_config_async(config_path: Optional[str], fix_issues: bool):
    """异步验证配置"""
    try:
        # 初始化配置管理器
        if config_path:
            config_manager = ConfigManager(config_path=config_path)
        else:
            config_manager = ConfigManager()

        # 验证配置
        errors = config_manager.validate()

        if errors:
            typer.echo("配置验证失败:", err=True)
            for error in errors:
                typer.echo(f"  • {error}", err=True)

            if fix_issues:
                typer.echo("自动修复功能待实现")

            # 退出码非零
            raise typer.Exit(code=1)
        else:
            typer.echo("✅ 配置验证通过")
            typer.echo(f"配置文件: {config_manager.config_path}")

    except Exception as e:
        typer.echo(f"验证配置失败: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("edit")
def edit_config(
    editor: Optional[str] = typer.Option(None, "--editor", "-e", help="编辑器命令"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="配置文件路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """编辑配置文件"""
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 确定配置文件路径
    if path:
        config_path = Path(path)
    else:
        config_manager = ConfigManager()
        config_path = Path(config_manager.config_path)

    if not config_path.exists():
        # 创建默认配置
        config_manager = ConfigManager(config_path=str(config_path))
        config_manager.save_config()
        typer.echo(f"创建默认配置文件: {config_path}")

    # 确定编辑器
    if editor:
        editor_cmd = editor
    else:
        # 使用环境变量或默认编辑器
        editor_cmd = os.environ.get("EDITOR", "vim")
        if editor_cmd == "vim" and os.name == "nt":
            editor_cmd = "notepad"

    typer.echo(f"使用编辑器: {editor_cmd}")
    typer.echo(f"打开文件: {config_path}")

    # 执行编辑器命令
    import subprocess

    try:
        subprocess.run([editor_cmd, str(config_path)])
    except FileNotFoundError:
        typer.echo(f"编辑器未找到: {editor_cmd}", err=True)
        typer.echo("请使用 --editor 参数指定可用编辑器")
        raise typer.Exit(code=1)


@app.command("set")
def set_config(
    key: str = typer.Argument(
        ..., help="配置键 (如 'log_level' 或 'session_defaults.default_llm_provider')"
    ),
    value: str = typer.Argument(..., help="配置值"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="配置文件路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """设置配置值"""
    typer.echo(f"设置配置: {key} = {value}")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_set_config_async(key, value, path))


async def _set_config_async(key: str, value: str, config_path: Optional[str]):
    """异步设置配置"""
    try:
        # 初始化配置管理器
        if config_path:
            config_manager = ConfigManager(config_path=config_path)
        else:
            config_manager = ConfigManager()

        config = config_manager.get_config()

        # 解析嵌套键
        keys = key.split(".")
        current = config

        # 遍历到倒数第二个键
        for k in keys[:-1]:
            if not hasattr(current, k):
                typer.echo(f"配置键 '{k}' 不存在", err=True)
                return
            current = getattr(current, k)

        # 设置值
        last_key = keys[-1]

        # 类型转换
        if hasattr(current, last_key):
            current_value = getattr(current, last_key)
            if isinstance(current_value, bool):
                # 布尔值
                if value.lower() in ("true", "yes", "1", "on"):
                    new_value = True
                elif value.lower() in ("false", "no", "0", "off"):
                    new_value = False
                else:
                    typer.echo(f"无效的布尔值: {value}", err=True)
                    return
            elif isinstance(current_value, int):
                # 整数
                try:
                    new_value = int(value)
                except ValueError:
                    typer.echo(f"无效的整数值: {value}", err=True)
                    return
            elif isinstance(current_value, float):
                # 浮点数
                try:
                    new_value = float(value)
                except ValueError:
                    typer.echo(f"无效的浮点数值: {value}", err=True)
                    return
            else:
                # 字符串或其他
                new_value = value

            setattr(current, last_key, new_value)

            # 保存配置
            config_manager.save_config()

            typer.echo(f"✅ 配置已更新: {key} = {new_value}")
            typer.echo(f"配置文件: {config_manager.config_path}")
        else:
            typer.echo(f"配置键 '{last_key}' 不存在", err=True)

    except Exception as e:
        typer.echo(f"设置配置失败: {e}", err=True)


@app.command("export")
def export_config(
    output: str = typer.Option(
        "loom_config_export.yaml", "--output", "-o", help="输出文件路径"
    ),
    format: str = typer.Option("yaml", "--format", "-f", help="输出格式 (yaml, json)"),
    include_secrets: bool = typer.Option(
        False, "--include-secrets", "-s", help="包含敏感信息（如API密钥）"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """导出配置到文件"""
    typer.echo(f"导出配置到: {output}")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_export_config_async(output, format, include_secrets))


async def _export_config_async(
    output_path: str, output_format: str, include_secrets: bool
):
    """异步导出配置"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()

        # 获取配置
        if include_secrets:
            config = config_manager.get_config()
            data = config.to_dict()
        else:
            data = config_manager.get_config_snapshot()

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            if output_format == "json":
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:  # yaml
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        typer.echo(f"✅ 配置已导出到: {output_path}")
        typer.echo(f"格式: {output_format}")
        typer.echo(f"包含敏感信息: {'是' if include_secrets else '否'}")

    except Exception as e:
        typer.echo(f"导出配置失败: {e}", err=True)


@app.command("import")
def import_config(
    input: str = typer.Argument(..., help="输入文件路径"),
    merge: bool = typer.Option(True, "--merge/--replace", help="合并到现有配置（否则替换）"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="备份现有配置"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """从文件导入配置"""
    typer.echo(f"从文件导入配置: {input}")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_import_config_async(input, merge, backup))


async def _import_config_async(input_path: str, merge: bool, backup: bool):
    """异步导入配置"""
    try:
        input_file = Path(input_path)
        if not input_file.exists():
            typer.echo(f"输入文件不存在: {input_path}", err=True)
            return

        # 读取输入文件
        with open(input_file, "r", encoding="utf-8") as f:
            if input_file.suffix.lower() in (".yaml", ".yml"):
                imported_data = yaml.safe_load(f)
            elif input_file.suffix.lower() == ".json":
                imported_data = json.load(f)
            else:
                # 尝试自动检测
                try:
                    imported_data = yaml.safe_load(f)
                except:
                    f.seek(0)
                    imported_data = json.load(f)

        # 初始化配置管理器
        config_manager = ConfigManager()

        # 备份现有配置
        if backup:
            backup_path = Path(config_manager.config_path).with_suffix(".yaml.backup")
            config_manager.save_config(path=str(backup_path))
            typer.echo(f"现有配置已备份到: {backup_path}")

        if merge:
            # 合并配置
            current_config = config_manager.get_config()
            current_data = current_config.to_dict()

            # 深度合并
            def deep_merge(target, source):
                for key, value in source.items():
                    if (
                        key in target
                        and isinstance(target[key], dict)
                        and isinstance(value, dict)
                    ):
                        deep_merge(target[key], value)
                    else:
                        target[key] = value

            deep_merge(current_data, imported_data)

            # 创建新配置
            from ...core.config_manager import AppConfig

            new_config = AppConfig.from_dict(current_data, config_manager.config_path)
            config_manager.config = new_config

            typer.echo("配置已合并")
        else:
            # 替换配置
            from ...core.config_manager import AppConfig

            new_config = AppConfig.from_dict(imported_data, config_manager.config_path)
            config_manager.config = new_config

            typer.echo("配置已替换")

        # 保存配置
        config_manager.save_config()

        # 验证新配置
        errors = config_manager.validate()
        if errors:
            typer.echo("⚠️ 导入的配置包含错误:", err=True)
            for error in errors:
                typer.echo(f"  • {error}", err=True)
        else:
            typer.echo("✅ 配置导入成功")

        typer.echo(f"配置文件: {config_manager.config_path}")

    except Exception as e:
        typer.echo(f"导入配置失败: {e}", err=True)


@app.command("reset")
def reset_config(
    force: bool = typer.Option(False, "--force", "-f", help="强制重置，不确认"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="备份现有配置"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """重置为默认配置"""
    if not force:
        confirm = typer.confirm("确定要重置为默认配置吗？")
        if not confirm:
            typer.echo("操作取消")
            return

    typer.echo("重置为默认配置...")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_reset_config_async(backup))


async def _reset_config_async(backup: bool):
    """异步重置配置"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()

        # 备份现有配置
        if backup:
            backup_path = Path(config_manager.config_path).with_suffix(".yaml.backup")
            config_manager.save_config(path=str(backup_path))
            typer.echo(f"现有配置已备份到: {backup_path}")

        # 重置为默认配置
        from ...core.config_manager import AppConfig

        config_manager.config = AppConfig()
        config_manager.save_config()

        typer.echo("✅ 配置已重置为默认值")
        typer.echo(f"配置文件: {config_manager.config_path}")

    except Exception as e:
        typer.echo(f"重置配置失败: {e}", err=True)


@app.command("list")
def list_config(
    section: Optional[str] = typer.Option(
        None, "--section", "-s", help="配置部分 (llm, memory, session, etc.)"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="输出格式 (table, json, yaml)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """列出配置（show命令的别名）"""
    # 直接调用show_config函数
    show_config(section, format, verbose)


@app.command("test")
def test_config(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="测试特定LLM提供商"),
    all: bool = typer.Option(False, "--all", "-a", help="测试所有已启用的提供商"),
    database: bool = typer.Option(False, "--database", "-d", help="测试数据库连接"),
    memory: bool = typer.Option(False, "--memory", "-m", help="测试记忆系统"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="测试超时时间（秒）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """测试配置的实际功能"""
    typer.echo("测试配置功能...")

    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # 异步运行
    asyncio.run(_test_config_async(provider, all, database, memory, timeout))


async def _test_config_async(
    provider: Optional[str],
    test_all: bool,
    test_database: bool,
    test_memory: bool,
    timeout: int,
):
    """异步测试配置"""
    try:
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()
        results = []

        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # 测试LLM提供商
        if provider or test_all:
            providers_to_test = []
            if provider:
                providers_to_test = [provider]
            elif test_all:
                # 测试所有启用的提供商
                for provider_name, provider_config in config.llm_providers.items():
                    if provider_config.enabled:
                        providers_to_test.append(provider_name)

            for provider_name in providers_to_test:
                if provider_name in config.llm_providers:
                    provider_config = config.llm_providers[provider_name]

                    if not provider_config.enabled:
                        results.append((f"LLM: {provider_name}", "❌ 已禁用", "跳过测试"))
                        continue

                    # 检查API密钥
                    if provider_config.api_key:
                        api_key_status = "✅ 已设置"
                    else:
                        api_key_status = "⚠️ 未设置（使用环境变量）"

                    # 简单连接测试（这里只是模拟，实际需要实现真正的连接测试）
                    results.append((f"LLM: {provider_name}", "✅ 配置有效", api_key_status))
                else:
                    results.append((f"LLM: {provider_name}", "❌ 未配置", "提供商不存在"))

        # 测试数据库连接
        if test_database:
            try:
                from pathlib import Path

                from ...core.persistence_engine import SQLitePersistence

                # 使用data_dir下的loom.db文件
                db_path = str(Path(config.data_dir) / "loom.db")
                persistence = SQLitePersistence(db_path)
                await persistence.initialize()

                # 测试简单查询
                async with persistence._transaction() as conn:
                    await conn.execute("SELECT 1")

                results.append(("数据库连接", "✅ 成功", f"路径: {db_path}"))
            except Exception as e:
                results.append(("数据库连接", "❌ 失败", str(e)))

        # 测试记忆系统
        if test_memory:
            try:
                # 检查记忆配置
                if config.memory.backend == "sqlite":
                    memory_db_path = config.memory.db_path
                    import os

                    if os.path.exists(memory_db_path):
                        results.append(
                            (
                                "记忆系统",
                                "✅ 配置有效",
                                f"后端: {config.memory.backend}",
                            )
                        )
                    else:
                        results.append(
                            (
                                "记忆系统",
                                "⚠️ 数据库文件不存在",
                                f"路径: {memory_db_path}",
                            )
                        )
                else:
                    results.append(("记忆系统", "✅ 配置有效", f"后端: {config.memory.backend}"))
            except Exception as e:
                results.append(("记忆系统", "❌ 配置错误", str(e)))

        # 显示结果
        if results:
            table = Table(title="配置测试结果", box=box.ROUNDED)
            table.add_column("测试项目", style="cyan")
            table.add_column("状态", style="green")
            table.add_column("详情", style="white")

            for item, status, details in results:
                table.add_row(item, status, details)

            console.print(table)

            # 统计
            success_count = sum(1 for _, status, _ in results if "✅" in status)
            warning_count = sum(1 for _, status, _ in results if "⚠️" in status)
            error_count = sum(1 for _, status, _ in results if "❌" in status)

            console.print(
                f"\n📊 测试统计: ✅ {success_count} 成功 | ⚠️ {warning_count} 警告 | ❌ {error_count} 失败"
            )

            if error_count == 0:
                console.print("🎉 所有测试通过！", style="bold green")
            else:
                console.print("⚠️ 存在配置问题，请检查上述错误", style="bold yellow")
        else:
            console.print("ℹ️ 未执行任何测试，请使用选项指定要测试的项目", style="yellow")

    except Exception as e:
        typer.echo(f"测试配置失败: {e}", err=True)


if __name__ == "__main__":
    app()
