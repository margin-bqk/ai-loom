"""
é¡¹ç®åå§åå½ä»?
æ¯æåå»ºæ°LOOMé¡¹ç®ï¼åæ¬ç®å½ç»æãéç½®æä»¶åç¤ºä¾è§åã?"""

import typer
from pathlib import Path
import shutil
import json
import yaml
from datetime import datetime

app = typer.Typer(
    name="init",
    help="é¡¹ç®åå§å?,
    no_args_is_help=True,
)

def init_project(path: str = ".", force: bool = False):
    """åå§åLOOMé¡¹ç®"""
    project_dir = Path(path).resolve()
    
    typer.echo(f"åå§å?LOOM é¡¹ç®å? {project_dir}")
    
    # æ£æ¥ç®å½æ¯å¦éç©?    if project_dir.exists() and any(project_dir.iterdir()):
        if not force:
            typer.echo("ç®å½éç©ºï¼ä½¿ç?--force å¼ºå¶åå§å?, err=True)
            raise typer.Exit(code=1)
        else:
            typer.echo("è­¦å: ç®å½éç©ºï¼å¼ºå¶åå§å")
    
    # åå»ºç®å½ç»æ
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
        typer.echo(f"åå»ºç®å½: {directory}")
    
    # åå»ºéç½®æä»¶
    _create_config_files(project_dir)
    
    # åå»ºç¤ºä¾è§å
    _create_example_canons(project_dir)
    
    # åå»ºç¤ºä¾ä»£ç 
    _create_example_code(project_dir)
    
    # åå»ºææ¡£
    _create_documentation(project_dir)
    
    # åå»ºGitå¿½ç¥æä»¶
    _create_gitignore(project_dir)
    
    # åå»ºREADME
    _create_readme(project_dir)
    
    typer.echo("\n" + "="*50)
    typer.echo("â?LOOM é¡¹ç®åå§åå®æ?")
    typer.echo(f"é¡¹ç®ç®å½: {project_dir}")
    typer.echo("\nä¸ä¸æ­?")
    typer.echo("1. ç¼è¾ config/default_config.yaml éç½®LLMæä¾å?)
    typer.echo("2. æ¥ç examples/ ç®å½ä¸­çç¤ºä¾")
    typer.echo("3. è¿è¡ 'loom dev check' æ£æ¥ç³»ç»ç¶æ?)
    typer.echo("4. è¿è¡ 'loom run interactive' å¯å¨äº¤äºå¼ä¼è¯?)

def _create_config_files(project_dir: Path):
    """åå»ºéç½®æä»¶"""
    config_dir = project_dir / "config"
    
    # 1. é»è®¤éç½®
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
    typer.echo("åå»ºéç½®æä»¶: config/default_config.yaml")
    
    # 2. LLMæä¾åéç½?    llm_providers_config = {
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
    typer.echo("åå»ºéç½®æä»¶: config/llm_providers.yaml")
    
    # 3. ç¯å¢åéç¤ºä¾
    env_example = """# LOOM ç¯å¢åééç½®
# å¤å¶æ­¤æä»¶ä¸º .env å¹¶å¡«åå®éå?
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# éç¨éç½®
LOOM_LOG_LEVEL=INFO
LOOM_DATA_DIR=./data
LOOM_MAX_CONCURRENT_TURNS=3

# å¼åéç½?LOOM_DEV_MODE=false
LOOM_ENABLE_METRICS=true
"""
    
    with open(project_dir / ".env.example", 'w', encoding='utf-8') as f:
        f.write(env_example)
    typer.echo("åå»ºç¯å¢åéç¤ºä¾: .env.example")

def _create_example_canons(project_dir: Path):
    """åå»ºç¤ºä¾è§å"""
    canon_dir = project_dir / "canon"
    
    # 1. é»è®¤è§å
    default_canon = """# ä¸çè§?(World)

æ¬¢è¿æ¥å° LOOM ä¸çï¼è¿æ¯ä¸ä¸ªç¤ºä¾ä¸çè®¾å®ã?
## åºæ¬è®¾å®
- ä¸çç±»åï¼å¥å¹»ä¸­ä¸çºª
- é­æ³ç³»ç»ï¼åç´ é­æ³ï¼ç«ãæ°´ãé£ãåï¼?- ä¸»è¦ç§æï¼äººç±»ãç²¾çµãç®äººãå½äº?- æ¿æ²»ä½ç³»ï¼å°å»ºçå½å¶

## å°çç¹å¾
- ä¸­å¤®å¤§éï¼é¿å¡è¿ªäº?- åæ¹å°åï¼æ°¸å»ä¹å?- ä¸æ¹æ£®æï¼ç²¾çµçå?- è¥¿æ¹å±±èï¼ç®äººç¿å?- åæ¹æ²æ¼ ï¼å¤ä»£éè¿?
# åäºåºè° (Tone)

å²è¯å¥å¹»é£æ ¼ï¼å¼ºè°è±éä¸»ä¹ä¸åé©ç²¾ç¥ã?- åè®¸éåº¦çå¹½é»åäººæ§åæ¶å»
- æ´ä½ä¿æä¸¥èåå²è¯æ
- é¼å±è§è²æé¿åå½è¿ä¸»é¢?
# å²çªè§£å³ (Conflict)

## ææç³»ç»
- ä½¿ç¨åºäºæè½çéª°å­ç³»ç»
- é­æ³éµå¾ª"ç­ä»·äº¤æ¢"åå
- ç¤¾äº¤å²çªéè¿è§è²æ®æ¼è§£å³

## é¾åº¦è®¾å®
- æ®éææï¼ä¸­ç­é¾åº¦
- BOSSæï¼é«é¾åº¦ï¼éè¦ç­ç?- è§£è°ï¼é»è¾æ¨çä¸ºä¸»

# æéè¾¹ç (Permissions)

## ç©å®¶å¯ä»¥
- åå»ºæ°è§è²ãå°ç¹åç©å
- æåºå§æåå±æ¹å
- è¿è¡åççè§è²æ®æ¼?
## ç©å®¶ä¸å¯ä»?- ç´æ¥ä¿®æ¹ä¸çæ ¸å¿æ³å
- åå»ºæ æè§è²æç©å?- è¿åå·²å»ºç«çå æå³ç³»

## éè¦GMæ¹å
- éå¤§åå²äºä»¶ä¿®æ¹
- æ°é­æ³ç³»ç»çå¼å¥
- ä¸»è¦è§è²æ­»äº¡

# å æå³ç³» (Causality)

## æ¶é´è§å
- æ¶é´çº¿æ§æµå¨ï¼ä¸å¯éè½¬
- åè®¸æéçæ¶é´é­æ³?- å¹³è¡å®å®çè®ºä¸éç¨

## æ­»äº¡è§å
- æ­»äº¡æ¯æ°¸ä¹ç
- å¤æ´»éè¦å¼ºå¤§çé­æ³ä»ªå¼
- çµé­è½¬ä¸å­å¨ä½ç½è§?
## å æå¾?- æ¯ä¸ªè¡å¨é½æåæ
- éå¤§å³å®å½±åä¸ççº?- å½è¿å¯ä»¥æ¹åä½éè¦ä»£ä»?
# åä¿¡æ?(Meta)

version: 1.0.0
author: LOOM Team
created: {date}
genre: fantasy
tags: [fantasy, medieval, magic, adventure]
""".format(date=datetime.now().strftime("%Y-%m-%d"))
    
    with open(canon_dir / "default.md", 'w', encoding='utf-8') as f:
        f.write(default_canon)
    typer.echo("åå»ºç¤ºä¾è§å: canon/default.md")
    
    # 2. ç§å¹»è§åç¤ºä¾
    scifi_canon = """# ä¸çè§?(World)

## å®å®è®¾å®
- çºªåï¼?5ä¸çºªï¼äººç±»å·²æ®æ°å¤ä¸ªæç³»
- ç§ææ°´å¹³ï¼è¶åéæè¡ãäººå·¥æºè½ãåºå æ¹é?- ä¸»è¦å¿åï¼å°çèé¦ãç«æå±åå½ãå¤æèç?
## ç©çæ³å
- éµå¾ªå·²ç¥ç©çå®å¾
- åè®¸æ²éèªè¡åè«æ´æè¡
- äººå·¥æºè½åæºå¨äººä¸å®å¾çº¦æ?
# åäºåºè° (Tone)

ç¡¬æ ¸ç§å¹»ï¼å¼ºè°ç§å­¦åç¡®æ§åé»è¾ä¸è´æ§ã?- å¯ä»¥åå«æ¿æ²»é´è°åçå­ææ?- æ³¨éææ¯ç»èåç§å­¦åç
- æ¢ç´¢æªç¥åéå¾·å°å¢?
# åä¿¡æ?(Meta)

version: 1.0.0
author: LOOM Team
created: {date}
genre: scifi
""".format(date=datetime.now().strftime("%Y-%m-%d"))
    
    with open(canon_dir / "scifi_example.md", 'w', encoding='utf-8') as f:
        f.write(scifi_canon)
    typer.echo("åå»ºç¤ºä¾è§å: canon/scifi_example.md")

def _create_example_code(project_dir: Path):
    """åå»ºç¤ºä¾ä»£ç """
    examples_dir = project_dir / "examples"
    
    # 1. åºæ¬ä¸çç¤ºä¾
    basic_world = """# LOOM åºæ¬ä¸çç¤ºä¾

è¿æ¯ä¸ä¸ªç®åç LOOM ä¸çæå»ºç¤ºä¾ã?
## åå»ºä¼è¯
```python
from loom.core.session_manager import SessionManager, SessionConfig
from loom.core.config_manager import ConfigManager
import asyncio

async def main():
    # åå§åéç½?    config_manager = ConfigManager()
    
    # åå»ºä¼è¯éç½®
    session_config = SessionConfig(
        name="æçç¬¬ä¸ä¸ªä¼è¯?,
        canon_path="./canon/default.md",
        llm_provider="openai"
    )
    
    # åå»ºä¼è¯
    session_manager = SessionManager(config_manager=config_manager)
    session = await session_manager.create_session(session_config)
    
    print(f"ä¼è¯åå»ºæå: {session.id}")

if __name__ == "__main__":
    asyncio.run(main())
```

## è¿è¡äº¤äºå¼ä¼è¯?```bash
# ä½¿ç¨ CLI
loom run interactive --name "æµè¯ä¼è¯" --canon ./canon/default.md

# æä½¿ç?Python èæ¬
python examples/player_intervention_example.py
```

## æ´å¤ç¤ºä¾
æ¥ç examples/ ç®å½ä¸­çå¶ä»ç¤ºä¾æä»¶ã?"""
    
    with open(examples_dir / "basic_world.md", 'w', encoding='utf-8') as f:
        f.write(basic_world)
    
    # 2. ç©å®¶å¹²é¢ç¤ºä¾
    player_intervention_code = '''"""
ç©å®¶å¹²é¢ç¤ºä¾

å±ç¤ºå¦ä½ä½¿ç¨ LOOM è¿è¡ç©å®¶å¹²é¢åæäºå¼å¯¼ã?"""
import asyncio
import sys
from pathlib import Path

# æ·»å é¡¹ç®æ ¹ç®å½å° Python è·¯å¾
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loom.core.session_manager import SessionManager, SessionConfig
from src.loom.core.config_manager import ConfigManager
from src.loom.core.persistence_engine import SQLitePersistence

async def main():
    """ä¸»å½æ?""
    print("=== LOOM ç©å®¶å¹²é¢ç¤ºä¾ ===")
    
    try:
        # åå§åéç½?        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # åå§åæä¹åå¼æ
        persistence = SQLitePersistence(config.data_dir)
        await persistence.initialize()
        
        # åå§åä¼è¯ç®¡çå¨
        session_manager = SessionManager(persistence, config_manager)
        
        # åå»ºä¼è¯éç½®
        session_config = SessionConfig(
            name="ç©å®¶å¹²é¢ç¤ºä¾ä¼è¯",
            canon_path="./canon/default.md",
            llm_provider="openai",
            metadata={
                "example_type": "player_intervention",
                "description": "å±ç¤ºç©å®¶å¹²é¢åè½"
            }
        )
        
        # åå»ºä¼è¯
        session = await session_manager.create_session(session_config)
        print(f"â?ä¼è¯åå»ºæå: {session.id}")
        print(f"ä¼è¯åç§°: {session.name}")
        
        # æ¨¡æç©å®¶å¹²é¢
        print("\\n=== æ¨¡æç©å®¶å¹²é¢ ===")
        
        interventions = [
            "ä¸»è§å¨æ£®æä¸­åç°äºä¸ä¸ªå¤èçéè¿¹",
            "çªç¶åºç°ä¸åªå·¨é¾è¢­å»æåº?,
            "ä¸»è§è·å¾äºä¸æé­æ³å",
            "éä¼ä¸­åºç°äºåå¾"
        ]
        
        for i, intervention in enumerate(interventions, 1):
            print(f"\\nå¹²é¢ {i}: {intervention}")
            
            # è¿éå¯ä»¥æ·»å å®éçå¹²é¢é»è¾
            # ä¾å¦: await session_manager.process_intervention(session.id, intervention)
            
            # æ¨¡æå¤çå»¶è¿
            await asyncio.sleep(0.5)
            print(f"  å¤çä¸?..")
            await asyncio.sleep(0.5)
            print(f"  â?å¹²é¢å·²åºç?)
        
        # ä¿å­ä¼è¯
        await session_manager.save_session(session, force=True)
        print(f"\\nâ?ä¼è¯å·²ä¿å­?)
        print(f"æ°æ®ä½ç½®: {config.data_dir}/sessions/{session.id}.json")
        
    except Exception as e:
        print(f"â?éè¯¯: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(examples_dir / "player_intervention_example.py", 'w', encoding='utf-8') as f:
        f.write(player_intervention_code)
    typer.echo("åå»ºç¤ºä¾ä»£ç : examples/player_intervention_example.py")

def _create_documentation(project_dir: Path):
    """åå»ºææ¡£"""
    docs_dir = project_dir / "docs"
    
    # åå»ºåºæ¬ææ¡£
    readme_content = """# LOOM é¡¹ç®ææ¡£

æ¬¢è¿ä½¿ç¨ LOOM (Language-Oriented Open Mythos)ï¼?
## é¡¹ç®ç»æ

```
{project_name}/
âââ canon/                    # è§åæä»¶
â?  âââ default.md           # é»è®¤è§å
â?  âââ scifi_example.md     # ç§å¹»ç¤ºä¾
âââ config/                  # éç½®æä»¶
â?  âââ default_config.yaml # åºç¨éç½®
â?  âââ llm_providers.yaml  # LLMæä¾åéç½?âââ data/                   # æ°æ®å­å¨
âââ docs/                   # ææ¡£
âââ examples/               # ç¤ºä¾ä»£ç 
âââ logs/                   # æ¥å¿æä»¶
âââ src/loom/              # æºä»£ç ?âââ tests/                 # æµè¯
âââ scripts/               # å·¥å·èæ¬
```

## å¿«éå¼å§?
1. **éç½®ç¯å¢åé**
   ```bash
   cp .env.example .env
   # ç¼è¾ .env æä»¶ï¼æ·»å ä½ ç?API å¯é¥
   ```

2. **è¿è¡æ£æ?*
   ```bash
   loom dev check
   ```

3. **å¯å¨äº¤äºå¼ä¼è¯?*
   ```bash
   loom run interactive
   ```

4. **ç®¡çä¼è¯**
   ```bash
   # ååºææä¼è¯?   loom session list
   
   # åå»ºæ°ä¼è¯?   loom session create --name "æçæäº"
   
   # æ¥çä¼è¯è¯¦æ
   loom session show <session_id>
   ```

## CLI å½ä»¤åè?
### è¿è¡å½ä»¤
- `loom run interactive` - äº¤äºå¼è¿è¡ä¼è¯?- `loom run batch` - æ¹å¤çè¿è¡?- `loom run resume` - æ¢å¤ä¼è¯

### ä¼è¯ç®¡ç
- `loom session create` - åå»ºæ°ä¼è¯?- `loom session list` - ååºä¼è¯
- `loom session show` - æ¾ç¤ºä¼è¯è¯¦æ
- `loom session delete` - å é¤ä¼è¯
- `loom session update` - æ´æ°ä¼è¯

### è§åç®¡ç
- `loom rules