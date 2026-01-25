## 1. 五层架构详细设计

### 1.1 运行时核心层 (Runtime Core)

**职责**：生命周期管理、调度、持久化、Session管理、Prompt组装、Memory读写、回合调度、崩溃恢复。

**模块划分**：
- `SessionManager`：会话生命周期（创建、加载、保存、删除）
- `TurnScheduler`：异步回合调度器，管理回合队列和并发
- `PersistenceEngine`：持久化存储接口（SQLite/DuckDB）
- `PromptAssembler`：动态组装Prompt，注入规则、记忆、玩家输入
- `SafetyBoundary`：崩溃恢复、异常处理、资源清理
- `ConfigManager`：配置加载与环境变量管理

**数据流**：
```
Session → TurnScheduler → PromptAssembler → LLM → Memory → Persistence
```

**约束**：
- 保持叙事失明：不解析规则内容，仅传递文本
- 无状态设计：核心层不存储叙事状态
- 异步优先：所有I/O操作使用async/await

### 1.2 规则层 (Markdown Canon)

**职责**：纯Markdown编写的世界观、叙事基调、冲突解决哲学等。

**文件结构**：
```
canon/
├── world.md          # 世界观与形而上学
├── tone.md           # 叙事基调与风格
├── conflict.md       # 冲突解决哲学
├── permissions.md    # 玩家权限边界
├── causality.md      # 死亡、时间、因果关系
└── meta.md           # 规则元信息（版本、作者等）
```

**规则特性**：
- 人类可读，LLM可解释
- 支持Markdown扩展语法（如`:::rule`自定义块）
- 版本控制通过Git管理
- 热加载：运行时监听文件变化

**验证机制**：
- 语法检查（Markdown解析）
- 冲突检测（规则间矛盾）
- 完整性检查（必需章节）

### 1.3 解释层 (LLM Reasoning)

**职责**：每回合重新解释规则，推导符合规则的叙事结果。

**组件**：
- `RuleInterpreter`：加载并解释Markdown规则
- `LLMProvider`：抽象LLM提供商接口
- `ReasoningPipeline`：推理流水线（理解→分析→推导→输出）
- `ConsistencyChecker`：检查输出与规则/记忆一致性

**工作流程**：
1. 加载当前规则集（完整Markdown）
2. 加载相关记忆摘要
3. 接收玩家输入（含干预意图）
4. 组装Prompt，调用LLM
5. 解析LLM响应，提取叙事结果
6. 更新记忆和状态

**设计原则**：
- 非确定性：允许软逻辑和启发式推理
- 解释缓存：缓存常见规则解释以减少LLM调用
- 回退机制：当LLM响应不符合要求时的降级策略

### 1.4 世界记忆层 (World Memory)

**职责**：结构化叙事状态存储（Canon事实、角色、剧情线、地点等）。

**数据结构**：
```python
# 记忆实体类型
MemoryEntity:
  - id: UUID
  - type: "character" | "location" | "fact" | "plotline" | "style"
  - content: JSON (结构化数据)
  - created_at: timestamp
  - updated_at: timestamp
  - version: int

# 记忆关系
MemoryRelation:
  - source_id: UUID
  - target_id: UUID
  - relation_type: "part_of" | "caused_by" | "located_at" | "related_to"
```

**存储方案**：
- 主存储：SQLite（关系型数据）
- 可选向量存储：Chroma/Qdrant（语义检索）
- 缓存层：Redis（可选，热数据）

**检索接口**：
- `get_relevant_memories(context, limit=10)`：获取相关记忆
- `summarize_memories(time_range)`：生成LLM驱动的摘要
- `update_memory(entity, delta)`：增量更新
- `rollback_memory(version)`：版本回滚

**记忆管理**：
- 自动摘要：定期压缩旧记忆
- 一致性检查：检测矛盾事实
- 垃圾回收：清理无关记忆

### 1.5 玩家干预层 (Player Intervention)

**职责**：支持OOC注释、世界编辑、Retcon、基调调整等。

**干预类型**：
1. **OOC注释**：`(OOC: ...)` 格式，不影响叙事
2. **世界编辑**：`[EDIT: ...]` 直接修改世界状态
3. **Retcon**：`[RETCON: ...]` 追溯性修改历史
4. **基调调整**：`[TONE: ...]` 调整叙事风格
5. **意图声明**：`[INTENT: ...]` 声明玩家意图

**处理流程**：
```
玩家输入 → 干预解析器 → 意图识别 → 规则验证 → 吸收处理 → 状态更新
```

**组件**：
- `InterventionParser`：解析干预语法
- `IntentRecognizer`：识别玩家意图
- `PermissionValidator`：基于规则层验证权限
- `AbsorptionEngine`：将干预融入叙事状态
- `AuditLogger`：记录干预历史

**设计原则**：
- 吸收而非拒绝：尽可能满足玩家意图
- 权限边界：尊重规则层定义的权限
- 审计追踪：所有干预可追溯、可撤销

## 2. 技术栈选型

### 2.1 编程语言和框架
- **语言**：Python 3.10+
- **异步框架**：asyncio + aiohttp
- **Web框架**：FastAPI（用于API服务）
- **CLI框架**：Typer 或 Click
- **配置管理**：Pydantic Settings

### 2.2 数据库系统
- **主数据库**：SQLite（嵌入式，零配置）
- **分析数据库**：DuckDB（可选，用于复杂查询）
- **向量数据库**：Chroma（本地）或 Qdrant（云）
- **缓存**：Redis（可选，用于会话缓存）

### 2.3 LLM接入方案
- **抽象层**：Provider无关设计
- **支持提供商**：
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - 本地模型 (Llama, Phi via Ollama)
  - 其他 (Google Gemini, Azure OpenAI)
- **BYOK设计**：用户提供API密钥
- **成本控制**：令牌计数、预算告警

### 2.4 版本控制集成
- **规则版本**：Git仓库管理
- **会话版本**：每个会话对应Git分支
- **回滚能力**：可恢复到任意历史状态
- **差异查看**：规则变化可视化

### 2.5 异步任务处理
- **任务队列**：asyncio队列
- **并发控制**：信号量限制LLM并发
- **超时处理**：可配置超时时间
- **重试机制**：指数退避重试

### 2.6 序列化和数据格式
- **配置格式**：YAML + JSON
- **规则格式**：Markdown + 自定义扩展
- **数据序列化**：JSON（存储） + MessagePack（可选）
- **API格式**：JSON Schema + OpenAPI

## 3. 组件接口设计

### 3.1 层间API接口

**运行时核心层接口**：
```python
class RuntimeCore:
    async def create_session(config: SessionConfig) -> Session
    async def load_session(session_id: str) -> Session
    async def save_session(session: Session)
    async def schedule_turn(turn: Turn) -> TurnResult
    async def assemble_prompt(context: PromptContext) -> str
```

**规则层接口**：
```python
class RuleLayer:
    def load_canon(path: str) -> Canon
    def get_rule_section(section: str) -> str
    def validate_canon(canon: Canon) -> ValidationResult
    def watch_for_changes(callback: Callable)
```

**解释层接口**：
```python
class InterpretationLayer:
    async def interpret(
        rules: str,
        memories: List[Memory],
        player_input: str
    ) -> InterpretationResult
    async def check_consistency(
        result: InterpretationResult,
        rules: str
    ) -> ConsistencyReport
```

**世界记忆层接口**：
```python
class WorldMemory:
    async def store(entity: MemoryEntity)
    async def retrieve(
        query: str,
        filters: Optional[Dict] = None
    ) -> List[MemoryEntity]
    async def summarize(
        entities: List[MemoryEntity]
    ) -> str
    async def rollback(to_version: int)
```

**玩家干预层接口**：
```python
class PlayerIntervention:
    def parse_input(input: str) -> ParsedInput
    async def process_intervention(
        intervention: Intervention,
        session: Session
    ) -> ProcessedResult
    def validate_permission(
        intervention: Intervention,
        rules: Canon
    ) -> bool
```

### 3.2 数据流设计

**正常叙事流**：
```
玩家输入 → 干预解析 → 规则加载 → 记忆检索 → Prompt组装 → LLM调用 → 结果解析 → 记忆更新 → 状态保存 → 输出响应
```

**错误处理流**：
```
异常发生 → 错误分类 → 恢复策略选择 → 状态回滚 → 重试/降级 → 日志记录 → 用户通知
```

### 3.3 错误处理和恢复机制

**错误分类**：
1. **LLM错误**：API失败、超时、配额不足
2. **规则错误**：语法错误、冲突、缺失
3. **记忆错误**：存储失败、检索超时、一致性冲突
4. **系统错误**：内存不足、磁盘满、网络中断

**恢复策略**：
- **重试**：可重试错误（网络超时）
- **降级**：功能降级（使用缓存、简化推理）
- **回滚**：状态回滚到上一个稳定点
- **人工干预**：严重错误时暂停并等待干预

**监控指标**：
- 回合延迟（P50, P95, P99）
- LLM调用成功率
- 记忆检索命中率
- 错误率与分类

### 3.4 配置管理和热加载

**配置层级**：
1. **环境配置**：API密钥、数据库路径
2. **会话配置**：规则路径、记忆策略
3. **运行时配置**：并发数、超时时间
4. **LLM配置**：模型选择、温度参数

**热加载支持**：
- 规则文件变化自动重载
- 配置更新无需重启
- 插件系统动态加载

## 4. 部署架构

### 4.1 本地运行模式

**单机部署**：
```
用户机器
├── LOOM CLI
├── SQLite数据库
├── 规则Markdown文件
└── 本地LLM（可选）
```

**要求**：
- Python 3.10+
- 磁盘空间：100MB+
- 内存：2GB+（使用本地LLM需更多）

### 4.2 服务器部署方案

**微服务架构**：
```
负载均衡器
├── API服务（FastAPI）
├── 会话管理服务
├── 记忆存储服务
├── LLM网关服务
└── 规则仓库服务
```

**容器化部署**：
```docker
# Docker Compose配置
services:
  api:
    image: loom-api:latest
    ports: ["8000:8000"]
  memory:
    image: loom-memory:latest
    volumes: ["memory-data:/data"]
  llm-gateway:
    image: loom-llm-gateway:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

**云原生部署**：
- Kubernetes部署
- 自动扩缩容（基于会话数）
- 服务网格（Istio）用于流量管理

### 4.3 扩展性和性能考虑

**水平扩展**：
- 无状态API服务可水平扩展
- 会话亲和性负载均衡
- 共享记忆存储（Redis集群）

**性能优化**：
- **缓存策略**：
  - 规则解释缓存（TTL 5分钟）
  - 记忆摘要缓存
  - LLM响应缓存（相同输入）
- **批处理**：
  - 批量记忆检索
  - 并行LLM调用（多个会话）
- **懒加载**：
  - 按需加载规则章节
  - 延迟记忆检索

**容量规划**：
- 单会话内存占用：~50MB
- 数据库增长：~1MB/1000回合
- 并发会话数：受LLM API限制

## 5. 开发环境配置

### 5.1 依赖管理

**pyproject.toml**：
```toml
[project]
name = "loom"
version = "0.1.0"
dependencies = [
    "aiohttp>=3.9.0",
    "pydantic>=2.0.0",
    "sqlalchemy>=2.0.0",
    "markdown-it-py>=3.0.0",
    "typer>=0.9.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.7.0",
    "flake8>=6.0.0",
]
vector = [
    "chromadb>=0.4.0",
    "sentence-transformers>=2.2.0",
]
```

**工具链**：
- **包管理**：Poetry 或 UV
- **虚拟环境**：venv 或 conda
- **依赖锁定**：poetry.lock 或 requirements.txt

### 5.2 开发工具链

**代码质量**：
- **格式化**：Black + isort
- **静态检查**：mypy + flake8
- **安全扫描**：bandit + safety
- **复杂度检查**：radon

**开发工具**：
- **IDE配置**：VS Code配置（.vscode/）
- **调试配置**：launch.json调试配置
- **预提交钩子**：pre-commit配置
- **文档生成**：MkDocs + Swagger

**测试工具**：
- **单元测试**：pytest + pytest-asyncio
- **集成测试**：pytest + 测试数据库
- **端到端测试**：pytest + 模拟LLM
- **性能测试**：locust 或 pytest-benchmark

### 5.3 测试框架和CI/CD

**测试目录结构**：
```
tests/
├── unit/
│   ├── test_runtime.py
│   ├── test_rules.py
│   └── test_memory.py
├── integration/
│   ├── test_interpretation.py
│   └── test_intervention.py
├── e2e/
│   └── test_full_session.py
└── fixtures/
    └── sample_canon/
```

**CI/CD流水线**：
```yaml
# GitHub Actions配置
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
      - run: pip install -e ".[dev]"
      - run: pytest --cov=loom --cov-report=xml
      - run: mypy loom
      - run: black --check loom tests
      - run: flake8 loom tests
```

**部署流水线**：
- **开发环境**：自动部署到测试服务器
- **预发布环境**：手动触发部署
- **生产环境**：标签触发，蓝绿部署

## 6. 文件结构

### 6.1 项目根目录
```
loom/
├── src/
│   └── loom/
│       ├── __init__.py
│       ├── core/              # 运行时核心层
│       │   ├── session.py
│       │   ├── scheduler.py
│       │   ├── persistence.py
│       │   └── prompt.py
│       ├── rules/             # 规则层
│       │   ├── canon.py
│       │   ├── loader.py
│       │   └── validator.py
│       ├── interpretation/    # 解释层
│       │   ├── interpreter.py
│       │   ├── llm/
│       │   │   ├── provider.py
│       │   │   ├── openai.py
│       │   │   └── anthropic.py
│       │   └── pipeline.py
│       ├── memory/            # 世界记忆层
│       │   ├── entities.py
│       │   ├── storage.py
│       │   ├── retrieval.py
│       │   └── summarization.py
│       ├── intervention/      # 玩家干预层
│       │   ├── parser.py
│       │   ├── intent.py
│       │   └── absorption.py
│       └── api/               # API接口
│           ├── server.py
│           ├── routes/
│           └── schemas.py
├── tests/
├── examples/
│   ├── canons/               # 示例规则集
│   └── scripts/              # 示例脚本
├── docs/
├── py