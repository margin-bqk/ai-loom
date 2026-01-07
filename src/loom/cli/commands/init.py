"""
项目初始化命�?
支持创建新LOOM项目，包括目录结构、配置文件和示例规则�?"""

import typer
from pathlib import Path
import shutil
import json
import yaml
from datetime import datetime

app = typer.Typer(
    name="init",
    help="项目初始�?,
    no_args_is_help=True,
)

def init_project(path: str = ".", force: bool = False):
    """初始化LOOM项目"""
    project_dir = Path(path).resolve()
    
    typer.echo(f"初始�?LOOM 项目�? {project_dir}")
    
    # 检查目录是否非�?    if project_dir.exists() and any(project_dir.iterdir()):
        if not force:
            typer.echo("目录非空，使�?--force 强制初始�?, err=True)
            raise typer.Exit(code=1)
        else:
            typer.echo("警告: 目录非空，强制初始化")
    
    # 创建目录结构
    directories = [
        "canon",
        "config",
        "data",
        "docs",
        "examples",
        "logs",
        "src/loom",
        "tests",
        "scripts"
    ]
    
    for directory in directories:
        dir_path = project_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        typer.echo(f"创建目录: {directory}")
    
    # 创建配置文件
    _create_config_files(project_dir)
    
    # 创建示例规则
    _create_example_canons(project_dir)
    
    # 创建示例代码
    _create_example_code(project_dir)
    
    # 创建文档
    _create_documentation(project_dir)
    
    # 创建Git忽略文件
    _create_gitignore(project_dir)
    
    # 创建README
    _create_readme(project_dir)
    
    typer.echo("\n" + "="*50)
    typer.echo("�?LOOM 项目初始化完�?")
    typer.echo(f"项目目录: {project_dir}")
    typer.echo("\n下一�?")
    typer.echo("1. 编辑 config/default_config.yaml 配置LLM提供�?)
    typer.echo("2. 查看 examples/ 目录中的示例")
    typer.echo("3. 运行 'loom dev check' 检查系统状�?)
    typer.echo("4. 运行 'loom run interactive' 启动交互式会�?)

def _create_config_files(project_dir: Path):
    """创建配置文件"""
    config_dir = project_dir / "config"
    
    # 1. 默认配置
    default_config = {
        "llm_providers": {
            "openai": {
                "type": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000,
                "timeout": 30,
                "max_retries": 3
            },
            "anthropic": {
                "type": "anthropic",
                "model": "claude-3-haiku-20240307",
                "temperature": 0.7,
                "max_tokens": 1000,
                "timeout": 30,
                "max_retries": 3,
                "enabled": False
            }
        },
        "provider_selection": {
            "default_provider": "openai",
            "fallback_order": ["openai", "anthropic"],
            "session_type_mapping": {
                "default": {
                    "preferred_provider": "openai",
                    "preferred_model": "gpt-3.5-turbo"
                }
            }
        },
        "memory": {
            "backend": "sqlite",
            "db_path": "./data/loom_memory.db",
            "vector_store_enabled": False,
            "max_memories_per_session": 1000,
            "auto_summarize": True
        },
        "session_defaults": {
            "default_canon_path": "./canon",
            "default_llm_provider": "openai",
            "max_turns": None,
            "auto_save_interval": 5,
            "intervention_allowed": True,
            "retcon_allowed": True
        },
        "max_concurrent_turns": 3,
        "log_level": "INFO",
        "data_dir": "./data",
        "cache_enabled": True,
        "cache_ttl_minutes": 60,
        "performance": {
            "max_prompt_length": 8000,
            "max_memories_per_prompt": 10,
            "enable_response_caching": True,
            "cache_size_mb": 100
        },
        "security": {
            "allow_file_system_access": True,
            "max_session_duration_hours": 24,
            "intervention_rate_limit": 10,
            "require_justification_for_retcon": True
        },
        "monitoring": {
            "enable_metrics": True,
            "metrics_port": 9090,
            "enable_tracing": False,
            "log_retention_days": 30
        }
    }
    
    with open(config_dir / "default_config.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
    typer.echo("创建配置文件: config/default_config.yaml")
    
    # 2. LLM提供商配�?    llm_providers_config = {
        "openai": {
            "type": "openai",
            "api_key": "${OPENAI_API_KEY}",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 30,
            "max_retries": 3,
            "fallback_enabled": True
        },
        "anthropic": {
            "type": "anthropic",
            "api_key": "${ANTHROPIC_API_KEY}",
            "model": "claude-3-haiku-20240307",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 30,
            "max_retries": 3,
            "fallback_enabled": True
        },
        "ollama": {
            "type": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama2",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 60,
            "max_retries": 3,
            "enabled": False
        }
    }
    
    with open(config_dir / "llm_providers.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(llm_providers_config, f, allow_unicode=True, default_flow_style=False)
    typer.echo("创建配置文件: config/llm_providers.yaml")
    
    # 3. 环境变量示例
    env_example = """# LOOM 环境变量配置
# 复制此文件为 .env 并填写实际�?
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 通用配置
LOOM_LOG_LEVEL=INFO
LOOM_DATA_DIR=./data
LOOM_MAX_CONCURRENT_TURNS=3

# 开发配�?LOOM_DEV_MODE=false
LOOM_ENABLE_METRICS=true
"""
    
    with open(project_dir / ".env.example", 'w', encoding='utf-8') as f:
        f.write(env_example)
    typer.echo("创建环境变量示例: .env.example")

def _create_example_canons(project_dir: Path):
    """创建示例规则"""
    canon_dir = project_dir / "canon"
    
    # 1. 默认规则
    default_canon = """# 世界�?(World)

欢迎来到 LOOM 世界！这是一个示例世界设定�?
## 基本设定
- 世界类型：奇幻中世纪
- 魔法系统：元素魔法（火、水、风、土�?- 主要种族：人类、精灵、矮人、兽�?- 政治体系：封建王国制

## 地理特征
- 中央大陆：阿卡迪�?- 北方冰原：永冻之�?- 东方森林：精灵王�?- 西方山脉：矮人矿�?- 南方沙漠：古代遗�?
# 叙事基调 (Tone)

史诗奇幻风格，强调英雄主义与冒险精神�?- 允许适度的幽默和人性化时刻
- 整体保持严肃和史诗感
- 鼓励角色成长和命运主�?
# 冲突解决 (Conflict)

## 战斗系统
- 使用基于技能的骰子系统
- 魔法遵循"等价交换"原则
- 社交冲突通过角色扮演解决

## 难度设定
- 普通战斗：中等难度
- BOSS战：高难度，需要策�?- 解谜：逻辑推理为主

# 权限边界 (Permissions)

## 玩家可以
- 创建新角色、地点和物品
- 提出剧情发展方向
- 进行合理的角色扮�?
## 玩家不可�?- 直接修改世界核心法则
- 创建无敌角色或物�?- 违反已建立的因果关系

## 需要GM批准
- 重大历史事件修改
- 新魔法系统的引入
- 主要角色死亡

# 因果关系 (Causality)

## 时间规则
- 时间线性流动，不可逆转
- 允许有限的时间魔�?- 平行宇宙理论不适用

## 死亡规则
- 死亡是永久的
- 复活需要强大的魔法仪式
- 灵魂转世存在但罕�?
## 因果�?- 每个行动都有后果
- 重大决定影响世界�?- 命运可以改变但需要代�?
# 元信�?(Meta)

version: 1.0.0
author: LOOM Team
created: {date}
genre: fantasy
tags: [fantasy, medieval, magic, adventure]
""".format(date=datetime.now().strftime("%Y-%m-%d"))
    
    with open(canon_dir / "default.md", 'w', encoding='utf-8') as f:
        f.write(default_canon)
    typer.echo("创建示例规则: canon/default.md")
    
    # 2. 科幻规则示例
    scifi_canon = """# 世界�?(World)

## 宇宙设定
- 纪元�?5世纪，人类已殖民多个星系
- 科技水平：超光速旅行、人工智能、基因改�?- 主要势力：地球联邦、火星共和国、外星联�?
## 物理法则
- 遵循已知物理定律
- 允许曲速航行和虫洞旅行
- 人工智能受机器人三定律约�?
# 叙事基调 (Tone)

硬核科幻，强调科学准确性和逻辑一致性�?- 可以包含政治阴谋和生存挑�?- 注重技术细节和科学原理
- 探索未知和道德困�?
# 元信�?(Meta)

version: 1.0.0
author: LOOM Team
created: {date}
genre: scifi
""".format(date=datetime.now().strftime("%Y-%m-%d"))
    
    with open(canon_dir / "scifi_example.md", 'w', encoding='utf-8') as f:
        f.write(scifi_canon)
    typer.echo("创建示例规则: canon/scifi_example.md")

def _create_example_code(project_dir: Path):
    """创建示例代码"""
    examples_dir = project_dir / "examples"
    
    # 1. 基本世界示例
    basic_world = """# LOOM 基本世界示例

这是一个简单的 LOOM 世界构建示例�?
## 创建会话
```python
from loom.core.session_manager import SessionManager, SessionConfig
from loom.core.config_manager import ConfigManager
import asyncio

async def main():
    # 初始化配�?    config_manager = ConfigManager()
    
    # 创建会话配置
    session_config = SessionConfig(
        name="我的第一个会�?,
        canon_path="./canon/default.md",
        llm_provider="openai"
    )
    
    # 创建会话
    session_manager = SessionManager(config_manager=config_manager)
    session = await session_manager.create_session(session_config)
    
    print(f"会话创建成功: {session.id}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 运行交互式会�?```bash
# 使用 CLI
loom run interactive --name "测试会话" --canon ./canon/default.md

# 或使�?Python 脚本
python examples/player_intervention_example.py
```

## 更多示例
查看 examples/ 目录中的其他示例文件�?"""
    
    with open(examples_dir / "basic_world.md", 'w', encoding='utf-8') as f:
        f.write(basic_world)
    
    # 2. 玩家干预示例
    player_intervention_code = '''"""
玩家干预示例

展示如何使用 LOOM 进行玩家干预和故事引导�?"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loom.core.session_manager import SessionManager, SessionConfig
from src.loom.core.config_manager import ConfigManager
from src.loom.core.persistence_engine import SQLitePersistence

async def main():
    """主函�?""
    print("=== LOOM 玩家干预示例 ===")
    
    try:
        # 初始化配�?        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 初始化持久化引擎
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()
        
        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)
        
        # 创建会话配置
        session_config = SessionConfig(
            name="玩家干预示例会话",
            canon_path="./canon/default.md",
            llm_provider="openai",
            metadata={
                "example_type": "player_intervention",
                "description": "展示玩家干预功能"
            }
        )
        
        # 创建会话
        session = await session_manager.create_session(session_config)
        print(f"�?会话创建成功: {session.id}")
        print(f"会话名称: {session.name}")
        
        # 模拟玩家干预
        print("\\n=== 模拟玩家干预 ===")
        
        interventions = [
            "主角在森林中发现了一个古老的遗迹",
            "突然出现一只巨龙袭击村�?,
            "主角获得了一把魔法剑",
            "队伍中出现了叛徒"
        ]
        
        for i, intervention in enumerate(interventions, 1):
            print(f"\\n干预 {i}: {intervention}")
            
            # 这里可以添加实际的干预逻辑
            # 例如: await session_manager.process_intervention(session.id, intervention)
            
            # 模拟处理延迟
            await asyncio.sleep(0.5)
            print(f"  处理�?..")
            await asyncio.sleep(0.5)
            print(f"  �?干预已应�?)
        
        # 保存会话
        await session_manager.save_session(session, force=True)
        print(f"\\n�?会话已保�?)
        print(f"数据位置: {config.data_dir}/sessions/{session.id}.json")
        
    except Exception as e:
        print(f"�?错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(examples_dir / "player_intervention_example.py", 'w', encoding='utf-8') as f:
        f.write(player_intervention_code)
    typer.echo("创建示例代码: examples/player_intervention_example.py")

def _create_documentation(project_dir: Path):
    """创建文档"""
    docs_dir = project_dir / "docs"
    
    # 创建基本文档
    readme_content = """# LOOM 项目文档

欢迎使用 LOOM (Language-Oriented Ontology Machine)�?
## 项目结构

```
{project_name}/
├── canon/                    # 规则文件
�?  ├── default.md           # 默认规则
�?  └── scifi_example.md     # 科幻示例
├── config/                  # 配置文件
�?  ├── default_config.yaml # 应用配置
�?  └── llm_providers.yaml  # LLM提供商配�?├── data/                   # 数据存储
├── docs/                   # 文档
├── examples/               # 示例代码
├── logs/                   # 日志文件
├── src/loom/              # 源代�?├── tests/                 # 测试
└── scripts/               # 工具脚本
```

## 快速开�?
1. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，添加你�?API 密钥
   ```

2. **运行检�?*
   ```bash
   loom dev check
   ```

3. **启动交互式会�?*
   ```bash
   loom run interactive
   ```

4. **管理会话**
   ```bash
   # 列出所有会�?   loom session list
   
   # 创建新会�?   loom session create --name "我的故事"
   
   # 查看会话详情
   loom session show <session_id>
   ```

## CLI 命令参�?
### 运行命令
- `loom run interactive` - 交互式运行会�?- `loom run batch` - 批处理运�?- `loom run resume` - 恢复会话

### 会话管理
- `loom session create` - 创建新会�?- `loom session list` - 列出会话
- `loom session show` - 显示会话详情
- `loom session delete` - 删除会话
- `loom session update` - 更新会话

### 规则管理
- `loom rules