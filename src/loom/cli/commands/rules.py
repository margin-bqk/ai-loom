"""
规则管理命令

支持规则加载、验证、创建、编辑等操作。
"""

import typer
import asyncio
from pathlib import Path
from typing import Optional, List
import json
import yaml
from datetime import datetime

from ...rules.rule_loader import RuleLoader
from ...rules.markdown_canon import MarkdownCanon
from ...utils.logging_config import setup_logging

app = typer.Typer(
    name="rules",
    help="规则管理",
    no_args_is_help=True,
)

@app.command("load")
def load_rules(
    canon: str = typer.Option(
        "default", "--canon", "-c", help="规则集名称"
    ),
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="规则文件路径（覆盖默认路径）"
    ),
    validate: bool = typer.Option(
        True, "--validate/--no-validate", help="是否验证规则"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="输出格式 (table, json, yaml)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """加载规则集"""
    typer.echo(f"加载规则集: {canon}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_load_rules_async(canon, path, validate, format))

async def _load_rules_async(
    canon_name: str,
    canon_path: Optional[str],
    validate: bool,
    output_format: str,
):
    """异步加载规则"""
    try:
        # 初始化规则加载器
        if canon_path:
            loader = RuleLoader(canon_dir=canon_path)
        else:
            loader = RuleLoader()
        
        # 加载规则
        canon = loader.load_canon(canon_name)
        if not canon:
            typer.echo(f"规则集 {canon_name} 不存在", err=True)
            return
        
        # 验证规则
        errors = []
        if validate:
            errors = canon.validate()
        
        # 按格式输出
        if output_format == "json":
            result = {
                "canon": canon_name,
                "path": str(canon.path),
                "metadata": canon.metadata,
                "sections": list(canon.sections.keys()),
                "section_count": len(canon.sections),
                "validation_errors": errors,
                "is_valid": len(errors) == 0
            }
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif output_format == "yaml":
            result = {
                "canon": canon_name,
                "path": str(canon.path),
                "metadata": canon.metadata,
                "sections": list(canon.sections.keys()),
                "section_count": len(canon.sections),
                "validation_errors": errors,
                "is_valid": len(errors) == 0
            }
            typer.echo(yaml.dump(result, allow_unicode=True, default_flow_style=False))
        else:  # table
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            
            console = Console()
            
            # 基本信息表
            info_table = Table(title="规则集信息", show_header=False)
            info_table.add_column("字段", style="cyan")
            info_table.add_column("值", style="white")
            
            info_table.add_row("名称", canon_name)
            info_table.add_row("路径", str(canon.path))
            info_table.add_row("章节数", str(len(canon.sections)))
            info_table.add_row("验证状态", "通过" if len(errors) == 0 else "失败")
            
            console.print(Panel(info_table, title="基本信息"))
            
            # 章节列表
            if canon.sections:
                sections_table = Table(title="章节列表")
                sections_table.add_column("章节", style="green")
                sections_table.add_column("行数", style="yellow")
                sections_table.add_column("字数", style="blue")
                
                for section_name, section_content in canon.sections.items():
                    lines = len(section_content.split('\n'))
                    words = len(section_content.split())
                    sections_table.add_row(section_name, str(lines), str(words))
                
                console.print(Panel(sections_table, title="章节详情"))
            
            # 元数据
            if canon.metadata:
                meta_table = Table(title="元数据", show_header=False)
                meta_table.add_column("键", style="cyan")
                meta_table.add_column("值", style="white")
                
                for key, value in canon.metadata.items():
                    meta_table.add_row(key, str(value))
                
                console.print(Panel(meta_table, title="元数据"))
            
            # 验证错误
            if errors:
                error_panel = Panel(
                    "\n".join([f"• {error}" for error in errors]),
                    title="验证错误",
                    style="red"
                )
                console.print(error_panel)
        
        if errors:
            typer.echo(f"规则集包含 {len(errors)} 个错误", err=True)
        else:
            typer.echo("规则集加载成功")
        
    except Exception as e:
        typer.echo(f"加载规则失败: {e}", err=True)

@app.command("list")
def list_rules(
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="规则目录路径"
    ),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", help="是否递归搜索"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="输出格式 (table, json, csv)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """列出所有规则集"""
    typer.echo("列出规则集...")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_list_rules_async(path, recursive, format))

async def _list_rules_async(
    rules_path: Optional[str],
    recursive: bool,
    output_format: str,
):
    """异步列出规则集"""
    try:
        # 初始化规则加载器
        if rules_path:
            loader = RuleLoader(canon_dir=rules_path, recursive=recursive)
        else:
            loader = RuleLoader(recursive=recursive)
        
        # 获取所有规则集
        canons = loader.load_all_canons()
        
        if not canons:
            typer.echo("没有找到规则集")
            return
        
        # 按格式输出
        if output_format == "json":
            result = {}
            for name, canon in canons.items():
                result[name] = {
                    "path": str(canon.path),
                    "sections": list(canon.sections.keys()),
                    "metadata": canon.metadata
                }
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif output_format == "csv":
            typer.echo("name,path,sections,metadata_count")
            for name, canon in canons.items():
                sections_count = len(canon.sections)
                metadata_count = len(canon.metadata)
                typer.echo(f"{name},{str(canon.path)},{sections_count},{metadata_count}")
        else:  # table
            from rich.console import Console
            from rich.table import Table
            
            console = Console()
            table = Table(title="规则集列表")
            table.add_column("名称", style="cyan")
            table.add_column("路径", style="white")
            table.add_column("章节", style="green")
            table.add_column("元数据", style="yellow")
            table.add_column("状态", style="blue")
            
            for name, canon in canons.items():
                # 验证规则
                errors = canon.validate()
                status = "有效" if len(errors) == 0 else f"无效 ({len(errors)} 错误)"
                
                table.add_row(
                    name,
                    str(canon.path),
                    str(len(canon.sections)),
                    str(len(canon.metadata)),
                    status
                )
            
            console.print(table)
        
        typer.echo(f"总计: {len(canons)} 个规则集")
        
    except Exception as e:
        typer.echo(f"列出规则集失败: {e}", err=True)

@app.command("validate")
def validate_rules(
    canon: Optional[str] = typer.Option(
        None, "--canon", "-c", help="规则集名称（如未指定则验证所有）"
    ),
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="规则目录路径"
    ),
    fix: bool = typer.Option(
        False, "--fix", "-f", help="尝试自动修复问题"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="输出格式 (table, json)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """验证规则集"""
    if canon:
        typer.echo(f"验证规则集: {canon}")
    else:
        typer.echo("验证所有规则集...")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_validate_rules_async(canon, path, fix, format))

async def _validate_rules_async(
    canon_name: Optional[str],
    rules_path: Optional[str],
    fix_issues: bool,
    output_format: str,
):
    """异步验证规则"""
    try:
        # 初始化规则加载器
        if rules_path:
            loader = RuleLoader(canon_dir=rules_path)
        else:
            loader = RuleLoader()
        
        validation_results = {}
        
        if canon_name:
            # 验证单个规则集
            canon = loader.load_canon(canon_name)
            if not canon:
                typer.echo(f"规则集 {canon_name} 不存在", err=True)
                return
            
            errors = canon.validate()
            validation_results[canon_name] = {
                "errors": errors,
                "is_valid": len(errors) == 0
            }
            
            # 尝试修复
            if fix_issues and errors:
                typer.echo("自动修复功能待实现")
        else:
            # 验证所有规则集
            canons = loader.load_all_canons()
            for name, canon in canons.items():
                errors = canon.validate()
                validation_results[name] = {
                    "errors": errors,
                    "is_valid": len(errors) == 0
                }
        
        # 按格式输出
        if output_format == "json":
            typer.echo(json.dumps(validation_results, ensure_ascii=False, indent=2))
        else:  # table
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            
            console = Console()
            
            # 汇总表
            summary_table = Table(title="验证汇总")
            summary_table.add_column("规则集", style="cyan")
            summary_table.add_column("状态", style="green")
            summary_table.add_column("错误数", style="red")
            summary_table.add_column("详情", style="white")
            
            total_errors = 0
            valid_count = 0
            
            for name, result in validation_results.items():
                errors = result["errors"]
                error_count = len(errors)
                total_errors += error_count
                
                if error_count == 0:
                    status = "✅ 有效"
                    valid_count += 1
                    details = ""
                else:
                    status = "❌ 无效"
                    details = "; ".join(errors[:3])  # 显示前3个错误
                    if len(errors) > 3:
                        details += f" ... (共{error_count}个错误)"
                
                summary_table.add_row(name, status, str(error_count), details)
            
            console.print(summary_table)
            
            # 统计信息
            total_canons = len(validation_results)
            console.print(Panel(
                f"总计: {total_canons} 个规则集\n"
                f"有效: {valid_count}\n"
                f"无效: {total_canons - valid_count}\n"
                f"总错误数: {total_errors}",
                title="统计信息"
            ))
        
    except Exception as e:
        typer.echo(f"验证规则失败: {e}", err=True)

@app.command("create")
def create_rules(
    name: str = typer.Option(..., "--name", "-n", help="规则集名称"),
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="规则目录路径"
    ),
    template: str = typer.Option(
        "default", "--template", "-t", help="模板类型 (default, fantasy, scifi, minimal)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="强制覆盖现有文件"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """创建新的规则集"""
    typer.echo(f"创建规则集: {name}")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_create_rules_async(name, path, template, force))

async def _create_rules_async(
    canon_name: str,
    rules_path: Optional[str],
    template_type: str,
    force_overwrite: bool,
):
    """异步创建规则集"""
    try:
        # 初始化规则加载器
        if rules_path:
            loader = RuleLoader(canon_dir=rules_path)
        else:
            loader = RuleLoader()
        
        # 检查文件是否已存在
        canon_path = loader.canon_dir / f"{canon_name}.md"
        if canon_path.exists() and not force_overwrite:
            typer.echo(f"规则集 {canon_name} 已存在，使用 --force 覆盖", err=True)
            return
        
        # 根据模板创建内容
        template_content = _get_template_content(template_type, canon_name)
        
        # 写入文件
        with open(canon_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        typer.echo(f"规则集创建成功: {canon_path}")
        typer.echo(f"模板类型: {template_type}")
        
        # 验证新创建的规则集
        canon = loader.load_canon(canon_name)
        if canon:
            errors = canon.validate()
            if errors:
                typer.echo(f"警告: 新规则集包含 {len(errors)} 个验证错误")
                for error in errors:
                    typer.echo(f"  • {error}")
        
    except Exception as e:
        typer.echo(f"创建规则集失败: {e}", err=True)

def _get_template_content(template_type: str, canon_name: str) -> str:
    """获取模板内容"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    templates = {
        "default": f"""# 世界观 (World)

这是你的世界的基本设定。描述世界的物理法则、历史背景、主要种族、文化特点等。

# 叙事基调 (Tone)

描述故事的风格和情绪。是黑暗奇幻、轻松喜剧、硬核科幻还是其他风格？

# 冲突解决 (Conflict)

定义如何解决故事中的冲突。是偏向现实主义、戏剧性还是规则化？

# 权限边界 (Permissions)

定义玩家可以做什么，不可以做什么。哪些类型的干预是允许的？

# 因果关系 (Causality)

定义时间、死亡、因果关系等形而上学规则。

# 元信息 (Meta)

version: 1.0.0
author: LOOM User
created: {date_str}
""",
        "fantasy": f"""# 世界观 (World)

这是一个奇幻世界，包含魔法、巨龙、精灵、矮人等经典元素。
世界由多个大陆组成，每个大陆有独特的文化和政治体系。
魔法是世界的核心法则，分为元素魔法、神圣魔法、黑暗魔法等派系。

# 叙事基调 (Tone)

史诗奇幻风格，强调英雄主义、命运与牺牲。
允许适度的幽默和人性化时刻，但整体保持严肃和史诗感。

# 冲突解决 (Conflict)

战斗使用基于技能的骰子系统。
魔法冲突遵循"等价交换"原则。
社交冲突通过角色扮演和说服解决。

# 权限边界 (Permissions)

玩家可以创建新角色、地点和物品。
玩家不能直接修改世界核心法则。
重大历史事件需要GM批准。

# 因果关系 (Causality)

时间线性流动，不可逆转。
死亡是永久的，除非使用强大的复活魔法。
因果律严格，每个行动都有后果。

# 元信息 (Meta)

version: 1.0.0
author: {canon_name} Creator
created: {date_str}
genre: fantasy
""",
        "scifi": f"""# 世界观 (World)

这是一个硬核科幻宇宙，遵循已知物理定律。
包含多个星际文明、人工智能、外星物种和未来科技。
重点放在科学合理性和技术细节上。

# 叙事基调 (Tone)

硬核科幻，强调科学准确性和逻辑一致性。
可以包含政治阴谋、探索未知和生存挑战。

# 冲突解决 (Conflict)

太空战斗使用物理模拟系统。
技术问题通过科学知识和工程解决。
社交冲突通过外交和谈判解决。

# 权限边界 (Permissions)

玩家可以设计新科技，但需符合物理定律。
不能引入超自然或魔法元素。
时间旅行需要特殊许可。

# 因果关系 (Causality)

遵循相对论和时间因果律。
人工智能行为受机器人三定律约束。
平行宇宙理论适用。

# 元信息 (Meta)

version: 1.0.0
author: {canon_name} Creator
created: {date_str}
genre: scifi
""",
        "minimal": f"""# 世界观 (World)

简要描述世界。

# 叙事基调 (Tone)

简要描述叙事风格。

# 元信息 (Meta)

version: 1.0.0
created: {date_str}
"""
    }
    
    return templates.get(template_type, templates["default"])

@app.command("stats")
def rules_stats(
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="规则目录路径"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="输出格式 (table, json)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """显示规则集统计信息"""
    typer.echo("计算规则集统计信息...")
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 异步运行
    asyncio.run(_rules_stats_async(path, format))

async def _rules_stats_async(rules_path: Optional[str], output_format: str):
    """异步计算规则统计"""
    try:
        # 初始化规则加载器
        if rules_path:
            loader = RuleLoader(canon_dir=rules_path, recursive=True)
        else:
            loader = RuleLoader(recursive=True)
        
        # 获取统计信息
        stats = loader.get_canon_stats()
        
        # 加载所有规则集以获取更多统计
        canons = loader.load_all_canons()
        
        total_sections = 0
        total_words = 0
        total_lines = 0
        
        for name, canon in canons.items():
            total_sections += len(canon.sections)
            for section_content in canon.sections.values():
                total_lines += len(section_content.split('\n'))
                total_words += len(section_content.split())
        
        stats.update({
            "total_canons": len(canons),
            "total_sections": total_sections,
            "total_lines": total_lines,
            "total_words": total_words,
            "avg_sections_per_canon": total_sections / max(1, len(canons)),
            "avg_words_per_canon": total_words / max(1, len(canons))
        })
        
        # 按格式输出
        if output_format == "json":
            typer.echo(json.dumps(stats, ensure_ascii=False, indent=2))
        else:  # table
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            
            console = Console()
            
            # 统计表
            stats_table = Table(title="规则集统计", show_header=False)
            stats_table.add_column("统计项", style="cyan")
            stats_table.add_column("值", style="white")
            
            stats_table.add_row("规则目录", stats.get("canon_dir", "N/A"))
            stats_table.add_row("递归搜索", "是" if stats.get("recursive") else "否")
            stats_table.add_row("规则集总数", str(stats.get("total_canons", 0)))
            stats_table.add_row("章节总数", str(stats.get("total_sections", 0)))
            stats_table.add_row("总行数", str(stats.get("total_lines", 0)))
            stats_table.add_row("总字数", str(stats.get("total_words", 0)))
            stats_table.add_row("平均章节数", f"{stats.get('avg_sections_per_canon', 0):.1f}")
            stats_table.add_row("平均字数", f"{stats.get('avg_words_per_canon', 0):.1f}")
            stats_table.add_row("缓存规则集数", str(stats.get("cached_canons", 0)))
            stats_table.add_row("依赖图大小", str(stats.get("dependency_graph_size", 0)))
            
            console.print(Panel(stats_table, title="统计信息"))
            
            # 文件列表
            if stats.get("available_files"):
                files_table = Table(title="可用规则文件")
                files_table.add_column("名称", style="cyan")
                files_table.add_column("路径", style="white")
                files_table.add_column("大小", style="yellow")
                files_table.add_column("缓存", style="green")
                
                for file_info in stats["available_files"][:10]:  # 显示前10个
                    size_kb = file_info.get("size", 0) / 1024
                    cached = "是" if file_info.get("cached") else "否"
                    files_table.add_row(
                        file_info.get("name", "N/A"),
                        file_info.get("path", "N/A"),
                        f"{size_kb:.1f} KB",
                        cached
                    )
                
                if len(stats["available_files"]) > 10:
                    files_table.add_row("...", f"还有 {len(stats['available_files']) - 10} 个文件", "", "")
                
                console.print(Panel(files_table, title="文件列表"))
        
    except Exception as e:
        typer.echo(f"获取统计信息失败: {e}", err=True)

if __name__ == "__main__":
    app()
