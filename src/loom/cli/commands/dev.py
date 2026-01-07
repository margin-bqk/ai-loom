"""
开发工具命令

支持代码质量检查、测试运行、构建打包等开发工作流。
"""

import typer
import subprocess
import sys
from pathlib import Path
from typing import Optional, List
import os

app = typer.Typer(
    name="dev",
    help="开发工具",
    no_args_is_help=True,
)

@app.command("lint")
def lint_code(
    path: str = typer.Option(
        ".", "--path", "-p", help="检查路径"
    ),
    fix: bool = typer.Option(
        False, "--fix", "-f", help="自动修复问题"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """运行代码质量检查"""
    typer.echo("运行代码质量检查...")
    
    # 检查是否安装了开发依赖
    try:
        import black
        import flake8
        import mypy
        import isort
    except ImportError:
        typer.echo("开发依赖未安装，请运行: pip install loom[dev]", err=True)
        raise typer.Exit(code=1)
    
    errors_found = False
    
    # 1. Black 代码格式化
    typer.echo("\n1. 运行 Black 代码格式化检查...")
    black_cmd = ["black", "--check", path]
    if fix:
        black_cmd = ["black", path]
    
    result = subprocess.run(black_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        errors_found = True
        typer.echo(f"Black 检查失败:\n{result.stdout}{result.stderr}", err=True)
        if not fix:
            typer.echo("使用 --fix 自动格式化", err=True)
    else:
        typer.echo("✅ Black 检查通过")
    
    # 2. isort 导入排序
    typer.echo("\n2. 运行 isort 导入排序检查...")
    isort_cmd = ["isort", "--check-only", path]
    if fix:
        isort_cmd = ["isort", path]
    
    result = subprocess.run(isort_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        errors_found = True
        typer.echo(f"isort 检查失败:\n{result.stdout}{result.stderr}", err=True)
        if not fix:
            typer.echo("使用 --fix 自动排序导入", err=True)
    else:
        typer.echo("✅ isort 检查通过")
    
    # 3. flake8 代码风格检查
    typer.echo("\n3. 运行 flake8 代码风格检查...")
    flake8_cmd = ["flake8", path]
    
    result = subprocess.run(flake8_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        errors_found = True
        typer.echo(f"flake8 检查失败:\n{result.stdout}", err=True)
    else:
        typer.echo("✅ flake8 检查通过")
    
    # 4. mypy 类型检查
    typer.echo("\n4. 运行 mypy 类型检查...")
    mypy_cmd = ["mypy", path]
    
    result = subprocess.run(mypy_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        errors_found = True
        typer.echo(f"mypy 检查失败:\n{result.stdout}", err=True)
    else:
        typer.echo("✅ mypy 检查通过")
    
    # 总结
    typer.echo("\n" + "="*50)
    if errors_found:
        typer.echo("❌ 代码质量检查发现错误", err=True)
        raise typer.Exit(code=1)
    else:
        typer.echo("✅ 所有代码质量检查通过")

@app.command("test")
def run_tests(
    path: str = typer.Option(
        "tests", "--path", "-p", help="测试路径"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
    coverage: bool = typer.Option(
        False, "--coverage", "-c", help="生成覆盖率报告"
    ),
    markers: Optional[str] = typer.Option(
        None, "--markers", "-m", help="测试标记过滤"
    ),
):
    """运行测试"""
    typer.echo("运行测试...")
    
    # 构建 pytest 命令
    pytest_cmd = ["pytest", path]
    
    if verbose:
        pytest_cmd.append("-v")
    
    if coverage:
        pytest_cmd.extend(["--cov=src/loom", "--cov-report=term", "--cov-report=html"])
    
    if markers:
        pytest_cmd.extend(["-m", markers])
    
    # 运行测试
    typer.echo(f"执行命令: {' '.join(pytest_cmd)}")
    result = subprocess.run(pytest_cmd)
    
    if result.returncode != 0:
        typer.echo("❌ 测试失败", err=True)
        raise typer.Exit(code=result.returncode)
    else:
        typer.echo("✅ 测试通过")

@app.command("build")
def build_package(
    clean: bool = typer.Option(
        False, "--clean", "-c", help="清理构建目录"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """构建包"""
    typer.echo("构建包...")
    
    # 清理构建目录
    if clean:
        typer.echo("清理构建目录...")
        clean_cmd = ["python", "-m", "build", "--clean"]
        result = subprocess.run(clean_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            typer.echo(f"清理失败: {result.stderr}", err=True)
        else:
            typer.echo("✅ 清理完成")
    
    # 构建包
    typer.echo("构建包...")
    build_cmd = ["python", "-m", "build"]
    
    if verbose:
        result = subprocess.run(build_cmd)
    else:
        result = subprocess.run(build_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        typer.echo("❌ 构建失败", err=True)
        if not verbose and hasattr(result, 'stderr'):
            typer.echo(f"错误: {result.stderr}", err=True)
        raise typer.Exit(code=result.returncode)
    else:
        typer.echo("✅ 构建成功")
        typer.echo("构建产物在 dist/ 目录中")

@app.command("docs")
def build_docs(
    clean: bool = typer.Option(
        False, "--clean", "-c", help="清理文档构建目录"
    ),
    serve: bool = typer.Option(
        False, "--serve", "-s", help="构建后启动本地服务器"
    ),
    port: int = typer.Option(
        8000, "--port", "-p", help="服务器端口"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """构建文档"""
    typer.echo("构建文档...")
    
    # 检查文档目录
    docs_dir = Path("docs")
    if not docs_dir.exists():
        typer.echo("文档目录不存在: docs/", err=True)
        typer.echo("请创建文档目录或使用 Sphinx/MkDocs 初始化")
        raise typer.Exit(code=1)
    
    # 检查是否有 mkdocs.yml 或 conf.py
    if (docs_dir / "mkdocs.yml").exists():
        # 使用 MkDocs
        typer.echo("检测到 MkDocs 配置")
        
        if clean:
            typer.echo("清理文档构建目录...")
            site_dir = docs_dir / "site"
            if site_dir.exists():
                import shutil
                shutil.rmtree(site_dir)
                typer.echo("✅ 清理完成")
        
        # 构建文档
        build_cmd = ["mkdocs", "build"]
        if verbose:
            build_cmd.append("--verbose")
        
        result = subprocess.run(build_cmd, cwd="docs")
        if result.returncode != 0:
            typer.echo("❌ 文档构建失败", err=True)
            raise typer.Exit(code=result.returncode)
        
        typer.echo("✅ 文档构建成功")
        typer.echo(f"文档生成在: docs/site/")
        
        # 启动本地服务器
        if serve:
            typer.echo(f"启动本地服务器在 http://localhost:{port}")
            serve_cmd = ["mkdocs", "serve", "--dev-addr", f"127.0.0.1:{port}"]
            subprocess.run(serve_cmd, cwd="docs")
    
    elif (docs_dir / "conf.py").exists():
        # 使用 Sphinx
        typer.echo("检测到 Sphinx 配置")
        
        build_dir = docs_dir / "_build"
        
        if clean and build_dir.exists():
            typer.echo("清理文档构建目录...")
            import shutil
            shutil.rmtree(build_dir)
            typer.echo("✅ 清理完成")
        
        # 构建文档
        build_cmd = ["sphinx-build", "-b", "html", ".", "_build/html"]
        if verbose:
            build_cmd.insert(1, "-v")
        
        result = subprocess.run(build_cmd, cwd="docs")
        if result.returncode != 0:
            typer.echo("❌ 文档构建失败", err=True)
            raise typer.Exit(code=result.returncode)
        
        typer.echo("✅ 文档构建成功")
        typer.echo(f"文档生成在: docs/_build/html/")
        
        # 启动本地服务器
        if serve:
            typer.echo(f"启动本地服务器在 http://localhost:{port}")
            import http.server
            import socketserver
            
            os.chdir(build_dir / "html")
            handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", port), handler) as httpd:
                typer.echo(f"服务器运行在端口 {port}")
                typer.echo("按 Ctrl+C 停止")
                httpd.serve_forever()
    
    else:
        typer.echo("未检测到文档构建配置", err=True)
        typer.echo("请创建 mkdocs.yml 或 conf.py 文件")
        raise typer.Exit(code=1)

@app.command("check")
def check_dependencies(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """检查依赖和系统状态"""
    typer.echo("检查依赖和系统状态...")
    
    checks_passed = True
    
    # 1. 检查 Python 版本
    typer.echo("\n1. 检查 Python 版本...")
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 10:
        typer.echo(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} 符合要求 (>=3.10)")
    else:
        typer.echo(f"❌ Python 版本 {python_version.major}.{python_version.minor} 不符合要求 (需要 >=3.10)", err=True)
        checks_passed = False
    
    # 2. 检查必需依赖
    typer.echo("\n2. 检查必需依赖...")
    required_packages = [
        "aiohttp",
        "aiosqlite", 
        "pydantic",
        "sqlalchemy",
        "markdown-it-py",
        "typer",
        "pyyaml",
        "watchdog",
        "python-dotenv"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            typer.echo(f"✅ {package} 已安装")
        except ImportError:
            typer.echo(f"❌ {package} 未安装", err=True)
            checks_passed = False
    
    # 3. 检查可选依赖
    typer.echo("\n3. 检查可选依赖...")
    optional_packages = [
        ("pytest", "测试框架"),
        ("black", "代码格式化"),
        ("mypy", "类型检查"),
        ("flake8", "代码风格检查"),
        ("isort", "导入排序"),
        ("rich", "终端美化"),
        ("fastapi", "API 框架"),
        ("chromadb", "向量存储"),
    ]
    
    for package, description in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            typer.echo(f"✅ {package} ({description}) 已安装")
        except ImportError:
            typer.echo(f"⚠️  {package} ({description}) 未安装（可选）")
    
    # 4. 检查配置文件
    typer.echo("\n4. 检查配置文件...")
    config_paths = [
        Path("config/default_config.yaml"),
        Path("config/llm_providers.yaml"),
        Path(".env.example")
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            typer.echo(f"✅ {config_path} 存在")
        else:
            typer.echo(f"⚠️  {config_path} 不存在（可能需要创建）")
    
    # 5. 检查数据目录
    typer.echo("\n5. 检查数据目录...")
    data_dir = Path("data")
    if data_dir.exists():
        typer.echo(f"✅ 数据目录 {data_dir} 存在")
        
        # 检查是否可写
        test_file = data_dir / ".test_write"
        try:
            test_file.touch()
            test_file.unlink()
            typer.echo(f"✅ 数据目录可写")
        except Exception as e:
            typer.echo(f"❌ 数据目录不可写: {e}", err=True)
            checks_passed = False
    else:
        typer.echo(f"⚠️  数据目录 {data_dir} 不存在（将在运行时自动创建）")
    
    # 6. 检查规则目录
    typer.echo("\n6. 检查规则目录...")
    canon_dir = Path("canon")
    if canon_dir.exists():
        md_files = list(canon_dir.glob("*.md"))
        if md_files:
            typer.echo(f"✅ 规则目录包含 {len(md_files)} 个规则文件")
        else:
            typer.echo(f"⚠️  规则目录为空（需要创建规则文件）")
    else:
        typer.echo(f"⚠️  规则目录 {canon_dir} 不存在（将在运行时自动创建）")
    
    # 总结
    typer.echo("\n" + "="*50)
    if checks_passed:
        typer.echo("✅ 所有必需检查通过")
        typer.echo("系统准备就绪")
    else:
        typer.echo("❌ 检查发现错误", err=True)
        typer.echo("请修复上述错误后重试")
        raise typer.Exit(code=1)

@app.command("clean")
def clean_project(
    all: bool = typer.Option(
        False, "--all", "-a", help="清理所有生成文件"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="详细输出"
    ),
):
    """清理项目生成文件"""
    typer.echo("清理项目生成文件...")
    
    # 要清理的目录和文件模式
    clean_patterns = [
        "dist/",
        "build/",
        "*.egg-info/",
        ".pytest_cache/",
        ".mypy_cache/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".coverage",
        "htmlcov/",
        ".benchmarks/",
    ]
    
    if all:
        clean_patterns.extend([
            "data/*.db",
            "data/*.log",
            "logs/",
            "temp/",
            "tmp/",
        ])
    
    import shutil
    import glob
    
    cleaned_count = 0
    
    for pattern in clean_patterns:
        matches = glob.glob(pattern, recursive=True)
        for match in matches:
            try:
                if os.path.isdir(match):
                    shutil.rmtree(match)
                    if verbose:
                        typer.echo(f"删除目录: {match}")
                else:
                    os.remove(match)
                    if verbose:
                        typer.echo(f"删除文件: {match}")
                cleaned_count += 1
            except Exception as e:
                if verbose:
                    typer.echo(f"无法删除 {match}: {e}")
    
    typer.echo(f"✅ 清理完成，删除了 {cleaned_count} 个文件/目录")

if __name__ == "__main__":
    app()