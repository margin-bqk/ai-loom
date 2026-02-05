# 代码组织

## 概述

本文档介绍 LOOM 项目的代码组织结构、设计模式和架构原则。了解代码组织有助于您更好地理解和贡献代码。

## 项目结构

### 顶层目录结构

```
loom/
├── src/                    # 源代码目录
│   └── loom/              # Python 包根目录
├── tests/                 # 测试代码
├── docs/                  # 文档
├── config/                # 配置文件
├── examples/              # 示例代码
├── templates/             # 模板文件
├── scripts/               # 工具脚本
├── plans/                 # 项目计划
├── data/                  # 数据文件（git忽略）
└── logs/                  # 日志文件（git忽略）
```

### 源代码结构 (`src/loom/`)

```
src/loom/
├── __init__.py           # 包初始化
├── core/                 # 核心运行时
│   ├── __init__.py
│   ├── config_manager.py
│   ├── session_manager.py
│   ├── narrative_factory.py
│   ├── persistence_engine.py
│   ├── turn_scheduler.py
│   └── interfaces.py     # 核心接口定义
├── interpretation/       # 解释层
│   ├── __init__.py
│   ├── reasoning_pipeline.py
│   ├── rule_interpreter.py
│   ├── consistency_checker.py
│   ├── llm_provider.py
│   └── interfaces.py
├── memory/               # 记忆系统
│   ├── __init__.py
│   ├── world_memory.py
│   ├── structured_store.py
│   ├── vector_store.py
│   ├── summarizer.py
│   └── interfaces.py
├── rules/                # 规则层
│   ├── __init__.py
│   ├── rule_loader.py
│   ├── markdown_canon.py
│   ├── version_control.py
│   └── interfaces.py
├── intervention/         # 玩家干预
│   ├── __init__.py
│   ├── player_intervention.py
│   ├── ooc_handler.py
│   ├── retcon_handler.py
│   ├── world_editor.py
│   └── interfaces.py
├── cli/                  # 命令行界面
│   ├── __init__.py
│   └── commands/         # CLI 命令
│       ├── __init__.py
│       ├── run.py
│       ├── config.py
│       ├── session.py
│       └── rules.py
├── web/                  # Web 界面
│   ├── __init__.py
│   ├── app.py
│   ├── static/           # 静态文件
│   └── templates/        # HTML 模板
├── plugins/              # 插件系统
│   ├── __init__.py
│   └── example_plugins.py
└── utils/                # 工具函数
    ├── __init__.py
    ├── async_helpers.py
    └── logging_config.py
```

## 架构原则

### 1. 分层架构

LOOM 采用五层架构设计：

```
┌─────────────────────────────────┐
│       玩家干预层                │ ← 玩家输入/编辑
├─────────────────────────────────┤
│       世界记忆层                │ ← 记忆存储/检索
├─────────────────────────────────┤
│       解释层                    │ ← LLM 推理/规则解释
├─────────────────────────────────┤
│       规则层                    │ ← 规则加载/验证
├─────────────────────────────────┤
│       运行时核心层              │ ← 会话管理/持久化
└─────────────────────────────────┘
```

### 2. 依赖方向

依赖关系从上到下，上层可以依赖下层，但下层不能依赖上层：

```
玩家干预 → 世界记忆 → 解释层 → 规则层 → 运行时核心
```

### 3. 接口隔离

每层通过明确定义的接口进行通信：

```python
# 示例：记忆系统接口
class MemoryInterface(Protocol):
    async def store(self, key: str, value: Any) -> None: ...
    async def retrieve(self, key: str) -> Optional[Any]: ...
    async def search(self, query: str, limit: int = 10) -> List[Any]: ...
```

## 核心模块详解

### 1. 运行时核心层 (`core/`)

#### 主要职责
- 会话生命周期管理
- 配置管理
- 持久化存储
- 回合调度

#### 关键类
- `SessionManager`: 会话管理器
- `ConfigManager`: 配置管理器  
- `PersistenceEngine`: 持久化引擎
- `TurnScheduler`: 回合调度器

#### 设计模式
- **工厂模式**: `NarrativeFactory` 创建叙事组件
- **策略模式**: 可插拔的持久化策略
- **观察者模式**: 会话状态变更通知

### 2. 规则层 (`rules/`)

#### 主要职责
- Markdown 规则解析
- 规则验证和规范化
- 规则版本控制
- 规则热加载

#### 关键类
- `RuleLoader`: 规则加载器
- `MarkdownCanon`: Markdown 解析器
- `VersionControl`: 版本控制器

#### 设计模式
- **解释器模式**: 规则解释器
- **访问者模式**: 规则树遍历
- **备忘录模式**: 规则状态保存

### 3. 解释层 (`interpretation/`)

#### 主要职责
- LLM 推理流水线
- 规则解释和执行
- 一致性检查
- 上下文构建

#### 关键类
- `ReasoningPipeline`: 推理流水线
- `RuleInterpreter`: 规则解释器
- `ConsistencyChecker`: 一致性检查器
- `LLMProvider`: LLM 提供商抽象

#### 设计模式
- **责任链模式**: 多步骤推理管道
- **适配器模式**: 不同 LLM 提供商适配
- **模板方法模式**: 推理算法模板

### 4. 世界记忆层 (`memory/`)

#### 主要职责
- 结构化记忆存储
- 向量记忆检索
- 记忆摘要生成
- 记忆一致性维护

#### 关键类
- `WorldMemory`: 世界记忆管理器
- `StructuredStore`: 结构化存储
- `VectorStore`: 向量存储
- `Summarizer`: 摘要生成器

#### 设计模式
- **仓库模式**: 记忆存储抽象
- **装饰器模式**: 记忆增强功能
- **迭代器模式**: 记忆遍历

### 5. 玩家干预层 (`intervention/`)

#### 主要职责
- OOC (Out-of-Character) 处理
- 世界状态编辑
- Retcon (追溯修改) 处理
- 权限验证

#### 关键类
- `PlayerIntervention`: 玩家干预处理器
- `OOCHandler`: OOC 处理器
- `RetconHandler`: Retcon 处理器
- `WorldEditor`: 世界编辑器

#### 设计模式
- **命令模式**: 干预命令封装
- **状态模式**: 干预处理状态
- **中介者模式**: 干预协调

## 代码规范

### 1. 命名约定

#### 文件和目录
- 使用小写字母和下划线: `session_manager.py`
- 测试文件: `test_session_manager.py`
- 目录: 使用小写字母: `core/`, `interpretation/`

#### 类和类型
- 使用 PascalCase: `class SessionManager:`
- 协议接口: `class MemoryInterface(Protocol):`
- 异常类: `class ValidationError(Exception):`

#### 函数和方法
- 使用 snake_case: `def create_session():`
- 异步方法: `async def load_rules_async():`
- 私有方法: `def _internal_helper():`

#### 变量和常量
- 变量: snake_case: `session_id`
- 常量: UPPER_SNAKE_CASE: `DEFAULT_MAX_TURNS`
- 类型提示: 使用明确的类型注解

### 2. 导入组织

```python
# 标准库导入
import os
import sys
from typing import Dict, List, Optional

# 第三方库导入
import yaml
import sqlite3
from pydantic import BaseModel

# 本地导入
from ..core.interfaces import SessionInterface
from .rule_loader import RuleLoader
```

### 3. 类型提示

```python
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

def create_session(
    name: str,
    canon_path: str,
    max_turns: Optional[int] = None,
    metadata: Dict[str, Any] = None
) -> Session:
    """创建新会话"""
    # 实现代码
```

### 4. 文档字符串

使用 Google 风格文档字符串：

```python
def process_action(action: str, context: Dict[str, Any]) -> str:
    """
    处理玩家行动并生成响应。
    
    Args:
        action: 玩家行动描述
        context: 当前会话上下文
        
    Returns:
        str: 生成的响应文本
        
    Raises:
        ValidationError: 行动格式无效
        RuntimeError: 处理过程中发生错误
        
    Example:
        >>> response = process_action("我去酒馆", {"location": "城镇"})
        >>> print(response[:50])
        '你走进酒馆，看到几个冒险者正在...'
    """
    # 实现代码
```

## 设计模式应用

### 1. 依赖注入

```python
class SessionManager:
    def __init__(
        self,
        config_manager: ConfigManager,
        persistence_engine: PersistenceEngine,
        rule_loader: Optional[RuleLoader] = None
    ):
        self.config = config_manager
        self.persistence = persistence_engine
        self.rule_loader = rule_loader or RuleLoader()
```

### 2. 策略模式

```python
class PersistenceStrategy(Protocol):
    async def save(self, session: Session) -> None: ...
    async def load(self, session_id: str) -> Optional[Session]: ...

class SQLitePersistence:
    async def save(self, session: Session) -> None:
        # SQLite 实现
        
class PostgreSQLPersistence:
    async def save(self, session: Session) -> None:
        # PostgreSQL 实现
```

### 3. 工厂模式

```python
class NarrativeFactory:
    @classmethod
    def create_session(
        cls,
        session_type: str,
        **kwargs
    ) -> Session:
        if session_type == "interactive":
            return InteractiveSession(**kwargs)
        elif session_type == "batch":
            return BatchSession(**kwargs)
        else:
            raise ValueError(f"未知会话类型: {session_type}")
```

### 4. 观察者模式

```python
class SessionObserver(Protocol):
    async def on_session_created(self, session: Session) -> None: ...
    async def on_turn_completed(self, session: Session, turn: Turn) -> None: ...

class SessionManager:
    def __init__(self):
        self.observers: List[SessionObserver] = []
    
    def add_observer(self, observer: SessionObserver) -> None:
        self.observers.append(observer)
    
    async def notify_observers(self, event: str, **kwargs) -> None:
        for observer in self.observers:
            await getattr(observer, f"on_{event}")(**kwargs)
```

## 异步编程模式

### 1. 异步上下文管理器

```python
class DatabaseConnection:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    async def __aenter__(self):
        self.connection = await connect(self.connection_string)
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            await self.connection.close()

# 使用示例
async with DatabaseConnection("sqlite:///data.db") as db:
    result = await db.execute("SELECT * FROM sessions")
```

### 2. 异步迭代器

```python
class SessionIterator:
    def __init__(self, session_ids: List[str]):
        self.session_ids = session_ids
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.session_ids):
            raise StopAsyncIteration
        
        session_id = self.session_ids[self.index]
        self.index += 1
        
        # 异步加载会话
        session = await load_session_async(session_id)
        return session

# 使用示例
async for session in SessionIterator(session_ids):
    await process_session(session)
```

### 3. 异步任务管理

```python
import asyncio
from typing import List, Any

async def process_batch(
    items: List[Any],
    processor: Callable[[Any], Awaitable[Any]],
    max_concurrent: int = 5
) -> List[Any]:
    """批量处理项目，限制并发数"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(item):
        async with semaphore:
            return await processor(item)
    
    tasks = [process_with_semaphore(item) for item in items]
    return await asyncio.gather(*tasks)
```

## 错误处理模式

### 1. 自定义异常层次

```python
class LOOMError(Exception):
    """LOOM 基础异常"""
    pass

class ValidationError(LOOMError):
    """验证错误"""
    pass

class ConfigurationError(LOOMError):
    """配置错误"""
    pass

class SessionError(LOOMError):
    """会话错误"""
    pass

class RuleError(ValidationError):
    """规则错误"""
    pass
```

### 2. 错误恢复策略

```python
async def execute_with_retry(
    operation: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    backoff_factor: float = 1.5
) -> T:
    """带重试的执行"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await operation()
        except (TimeoutError, ConnectionError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = backoff_factor ** attempt
                await asyncio.sleep(delay)
    
    raise last_exception
```

### 3. 上下文相关的错误处理

```python
class ErrorContext:
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
    
    def add_error(self, error: Exception, context: Dict[str, Any]) -> None:
        self.errors.append({
            "error": error,
            "context": context,
            "timestamp": datetime.now()
        })
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def get_error_summary(self) -> str:
        return f"发现 {len(self.errors)} 个错误"
```

## 测试组织

### 1. 测试目录结构

```
tests/
├── __init__.py
├── conftest.py           # 测试配置
├── test_core/            # 核心层测试
│   ├── __init__.py
│   ├── test_config_manager.py
│   ├── test_session_manager.py
│   └── test_integration.py
├── test_rules/           # 规则层测试
├── test_interpretation/  # 解释层测试
├── test_memory/          # 记忆层测试
├── test_intervention/    # 干预层测试
├── test_integration/     # 集成测试
└── test_phase1/          # 阶段1测试
```

### 2. 测试夹具组织

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_data_dir(tmp_path):
    """临时数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_rules():
    """示例规则"""
    return """
    # 测试规则
    
    ## 世界设定
    - 世界名称: 测试世界
    - 时代背景: 现代
    """
```

### 3. 异步测试模式

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_operation():
    """测试异步操作"""
    result = await async_operation()
    assert result is not None
    
@pytest.mark.asyncio
async def test_concurrent_operations():
    """测试并发操作"""
    tasks = [async_operation(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 5
```

## 性能考虑

### 1. 内存管理

```python
import weakref
from typing import Optional

class SessionCache:
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()
    
    def get(self, session_id: str) -> Optional[Session]:
        return self._cache.get(session_id)
    
    def set(self, session_id: str, session: Session) -> None:
        self._cache[session_id] = session
    
    def clear(self) -> None:
        self._cache.clear()
```

### 2. 延迟加载

```python
class LazyLoader:
    def __init__(self, loader: Callable[[], Any]):
        self.loader = loader
        self._value = None
        self._loaded = False
    
    @property
    def value(self) -> Any:
        if not self._loaded:
            self._value = self.loader()
            self._loaded = True
        return self._value
```

### 3. 缓存策略

```python
from functools import lru_cache
from datetime import datetime, timedelta

class TimedCache:
    def __init__(self, ttl_seconds: int = 300):
