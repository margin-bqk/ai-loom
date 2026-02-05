# 架构概述

## 概述

LOOM（Language-Oriented Open Mythos）是一个基于 Markdown 规则的非承载式叙事引擎。本文档详细描述 LOOM 的系统架构、设计原则和核心组件。

## 设计哲学

### 1. 非承载式架构 (Non-Carrying Architecture)

LOOM 采用非承载式架构，将叙事规则完全从框架代码中分离出来：

- **规则与代码分离**: 规则以纯 Markdown 文件定义，框架代码不包含任何特定世界的逻辑
- **叙事失明**: 解释器对规则内容保持"失明"，仅负责规则的传递、解释和执行
- **规则即数据**: 规则是数据而非代码，可以动态加载、修改和版本控制

### 2. 语言导向设计

- **Markdown 作为规则语言**: 使用标准 Markdown 语法定义世界规则
- **自然语言接口**: 通过自然语言与系统交互
- **可扩展的 DSL**: 支持通过插件扩展规则语言

### 3. 异步优先架构

- **全异步设计**: 所有 I/O 操作都是异步的
- **高并发支持**: 支持大量并发会话
- **事件驱动**: 基于事件的消息传递

## 五层架构

LOOM 采用五层架构设计，每层有明确的职责和接口：

```
┌─────────────────────────────────┐
│       玩家干预层                │ ← 玩家输入/编辑/Retcon
├─────────────────────────────────┤
│       世界记忆层                │ ← 记忆存储/检索/摘要
├─────────────────────────────────┤
│       解释层                    │ ← LLM 推理/规则解释
├─────────────────────────────────┤
│       规则层                    │ ← 规则加载/验证/版本
├─────────────────────────────────┤
│       运行时核心层              │ ← 会话管理/持久化/调度
└─────────────────────────────────┘
```

### 依赖关系
- 上层可以依赖下层，下层不能依赖上层
- 层间通过明确定义的接口通信
- 每层可以独立测试和替换

## 核心层详解

### 1. 运行时核心层

#### 职责
- 会话生命周期管理
- 配置管理和环境抽象
- 持久化存储引擎
- 回合调度和状态管理
- 插件系统管理

#### 关键组件
- **SessionManager**: 会话管理器，负责创建、加载、保存会话
- **ConfigManager**: 配置管理器，统一管理所有配置
- **PersistenceEngine**: 持久化引擎，支持多种存储后端
- **TurnScheduler**: 回合调度器，管理会话回合流程
- **NarrativeFactory**: 叙事工厂，创建叙事组件

#### 设计模式
- **工厂模式**: 创建不同类型的会话和组件
- **策略模式**: 可插拔的持久化策略
- **观察者模式**: 会话状态变更通知

### 2. 规则层

#### 职责
- Markdown 规则解析和规范化
- 规则验证和完整性检查
- 规则版本控制和历史追踪
- 规则热加载和动态更新

#### 关键组件
- **RuleLoader**: 规则加载器，从文件系统加载规则
- **MarkdownCanon**: Markdown 解析器，解析规则结构
- **VersionControl**: 版本控制器，管理规则变更历史
- **RuleValidator**: 规则验证器，检查规则有效性

#### 规则文件结构
```markdown
# 世界名称

## 世界设定
- **时代背景**: [描述]
- **魔法系统**: [描述]
- **主要种族**: [列表]

## 角色规则
### 角色创建
1. [规则1]
2. [规则2]

### 角色发展
1. [规则1]
2. [规则2]

## 物理规则
### 战斗系统
- [规则细节]

### 魔法规则  
- [规则细节]
```

### 3. 解释层

#### 职责
- LLM 推理流水线管理
- 规则解释和执行
- 上下文构建和优化
- 一致性检查和约束验证

#### 关键组件
- **ReasoningPipeline**: 推理流水线，多步骤推理过程
- **RuleInterpreter**: 规则解释器，解释和执行规则
- **ConsistencyChecker**: 一致性检查器，确保叙事一致性
- **ContextBuilder**: 上下文构建器，构建 LLM 提示
- **LLMProvider**: LLM 提供商抽象，支持多种 LLM

#### 推理流程
```
1. 接收玩家输入
2. 构建上下文（规则 + 历史 + 记忆）
3. 执行规则解释
4. 生成 LLM 提示
5. 调用 LLM 获取响应
6. 一致性检查
7. 更新记忆
8. 返回响应
```

### 4. 世界记忆层

#### 职责
- 结构化记忆存储和管理
- 向量记忆检索和相似性搜索
- 记忆摘要生成和压缩
- 记忆一致性维护

#### 关键组件
- **WorldMemory**: 世界记忆管理器，统一记忆接口
- **StructuredStore**: 结构化存储，存储实体和关系
- **VectorStore**: 向量存储，支持语义搜索
- **Summarizer**: 摘要生成器，压缩长期记忆
- **MemoryConsistencyChecker**: 记忆一致性检查器

#### 记忆类型
- **短期记忆**: 最近的事件和对话（容量有限）
- **长期记忆**: 重要事件和知识（持久化存储）
- **工作记忆**: 当前会话的临时记忆
- **语义记忆**: 向量化的概念和关系

### 5. 玩家干预层

#### 职责
- OOC (Out-of-Character) 注释处理
- 世界状态编辑和修改
- Retcon (追溯修改) 处理
- 权限验证和访问控制

#### 关键组件
- **PlayerIntervention**: 玩家干预处理器，统一干预接口
- **OOCHandler**: OOC 处理器，处理玩家注释
- **RetconHandler**: Retcon 处理器，处理追溯修改
- **WorldEditor**: 世界编辑器，修改世界状态
- **PermissionValidator**: 权限验证器，检查操作权限

#### 干预类型
- **OOC 注释**: `((这是OOC注释))`
- **世界编辑**: `!edit 添加一个新地点`
- **Retcon**: `!retcon 修正之前的描述`
- **配置修改**: `!config 设置参数值`

## 数据流

### 正常会话流程

```
玩家输入
    ↓
[玩家干预层] → 处理干预命令
    ↓
[世界记忆层] → 检索相关记忆
    ↓  
[解释层] → 构建上下文 + 规则解释
    ↓
[规则层] → 提供当前规则
    ↓
[运行时核心] → 管理会话状态
    ↓
LLM 推理
    ↓
[解释层] → 一致性检查
    ↓
[世界记忆层] → 存储新记忆
    ↓
响应输出
```

### 数据持久化流程

```
会话状态变更
    ↓
[运行时核心] → 序列化会话状态
    ↓
PersistenceEngine → 选择存储策略
    ↓
存储后端 (SQLite/PostgreSQL/文件)
    ↓
定期备份和归档
```

## 接口设计

### 1. 核心接口

```python
class SessionInterface(Protocol):
    """会话接口"""
    async def execute_action(self, action: str) -> str: ...
    async def save(self) -> None: ...
    async def load(self) -> None: ...
    def get_state(self) -> SessionState: ...

class MemoryInterface(Protocol):
    """记忆接口"""
    async def store(self, key: str, value: Any) -> None: ...
    async def retrieve(self, key: str) -> Optional[Any]: ...
    async def search(self, query: str, limit: int = 10) -> List[Any]: ...

class RuleInterface(Protocol):
    """规则接口"""
    async def load(self, path: str) -> RuleSet: ...
    async def validate(self, rule_set: RuleSet) -> ValidationResult: ...
    async def interpret(self, rule_set: RuleSet, context: Context) -> Interpretation: ...
```

### 2. 插件接口

```python
class PluginInterface(Protocol):
    """插件接口"""
    def initialize(self, config: Dict[str, Any]) -> None: ...
    def cleanup(self) -> None: ...
    def get_metadata(self) -> PluginMetadata: ...

class LLMProviderPlugin(PluginInterface):
    """LLM 提供商插件"""
    async def generate(self, prompt: str, **kwargs) -> str: ...
    async def embed(self, text: str) -> List[float]: ...

class MemoryBackendPlugin(PluginInterface):
    """记忆后端插件"""
    async def store(self, data: MemoryData) -> str: ...
    async def query(self, query: MemoryQuery) -> List[MemoryData]: ...
```

## 扩展性设计

### 1. 插件系统

LOOM 支持多种类型的插件：

- **LLM 提供商插件**: 添加新的 LLM 服务支持
- **记忆后端插件**: 添加新的存储后端
- **规则验证器插件**: 添加自定义规则验证
- **输出格式化插件**: 添加新的输出格式
- **监控插件**: 添加监控和指标收集

### 2. 配置系统

分层配置系统：

```
命令行参数 (最高优先级)
    ↓
环境变量
    ↓  
用户配置文件 (~/.loom/config.yaml)
    ↓
项目配置文件 (./config/*.yaml)
    ↓
默认配置 (最低优先级)
```

### 3. 存储抽象

支持多种存储后端：

- **SQLite**: 默认存储，适合单机部署
- **PostgreSQL**: 生产级关系数据库
- **文件系统**: 简单文件存储
- **内存存储**: 测试和开发环境
- **自定义后端**: 通过插件支持

## 性能考虑

### 1. 异步架构优势

- **非阻塞 I/O**: 数据库和 API 调用不阻塞主线程
- **高并发**: 使用 asyncio 支持数千并发连接
- **资源高效**: 单进程处理多个会话

### 2. 缓存策略

- **LLM 响应缓存**: 缓存相似的 LLM 响应
- **规则缓存**: 缓存解析后的规则
- **记忆缓存**: 缓存频繁访问的记忆
- **会话状态缓存**: 缓存活跃会话状态

### 3. 优化技术

- **批处理**: 批量处理相似请求
- **延迟加载**: 按需加载资源和数据
- **连接池**: 数据库和 API 连接池
- **压缩**: 记忆和状态数据压缩

## 安全设计

### 1. 输入验证

- **规则验证**: 验证规则文件语法和结构
- **玩家输入清理**: 清理和验证玩家输入
- **上下文大小限制**: 防止提示注入攻击

### 2. 访问控制

- **会话隔离**: 不同会话完全隔离
- **权限系统**: 基于角色的访问控制
- **审计日志**: 记录所有重要操作

### 3. 数据保护

- **加密存储**: 敏感数据加密存储
- **安全传输**: 使用 HTTPS 和 TLS
- **定期清理**: 自动清理临时数据

## 监控和可观测性

### 1. 指标收集

- **性能指标**: 响应时间、吞吐量、错误率
- **资源指标**: CPU、内存、磁盘使用
- **业务指标**: 会话数、回合数、用户数

### 2. 日志系统

- **结构化日志**: JSON 格式的结构化日志
- **多级别日志**: DEBUG、INFO、WARNING、ERROR
- **日志聚合**: 集中式日志收集和分析

### 3. 追踪系统

- **请求追踪**: 端到端请求追踪
- **性能剖析**: 代码级性能剖析
- **依赖追踪**: 外部依赖调用追踪

## 部署架构

### 1. 单机部署

```
[客户端] → [Nginx] → [LOOM 应用] → [SQLite]
                     ↓
                [LLM API]
```

### 2. 高可用部署

```
[负载均衡器]
    ↓
[LOOM 实例1] [LOOM 实例2] [LOOM 实例3]
    ↓           ↓           ↓
[PostgreSQL 集群] ←→ [Redis 缓存]
    ↓
[对象存储] (规则文件、备份)
```

### 3. 云原生部署

```
[Kubernetes]
    ↓
[LOOM Deployment] → [ConfigMap] [Secret]
    ↓
[PostgreSQL StatefulSet]
    ↓
[Redis Cluster]
    ↓
[监控栈] (Prometheus, Grafana, Loki)
```

## 技术栈

### 核心技术
- **Python 3.10+**: 主要编程语言
- **Asyncio**: 异步编程框架
- **SQLite/PostgreSQL**: 数据存储
- **ChromaDB**: 向量存储
- **FastAPI**: Web 框架

### 开发工具
- **Pytest**: 测试框架
- **Black/Flake8**: 代码格式化
- **Mypy**: 类型检查
- **MkDocs**: 文档生成

### 部署工具
- **Docker**: 容器化
- **Docker Compose**: 本地开发
- **Kubernetes**: 生产部署
- **GitHub Actions**: CI/CD

## 设计决策记录

### 1. 为什么选择 Markdown 作为规则语言？

**决策**: 使用标准 Markdown 而非自定义 DSL

**理由**:
- 学习成本低，用户熟悉 Markdown
- 工具生态丰富（编辑器、预览、转换）
- 易于版本控制和协作
- 可读性强，既是文档又是规则

### 2. 为什么采用非承载式架构？

**决策**: 将规则与框架代码完全分离

**理由**:
- 规则可以独立演化和版本控制
- 框架可以保持稳定，减少升级成本
- 支持多世界、多规则集并行
- 降低框架复杂度

### 3. 为什么选择异步架构？

**决策**: 全异步设计而非同步或多进程

**理由**:
- I/O 密集型应用，异步效率更高
- 更好的资源利用率
- 简化并发编程模型
- 与现代 Python 生态对齐

## 未来扩展方向

### 1. 短期路线图
- 更多 LLM 提供商支持
- 增强的记忆系统
- 改进的规则验证
- 性能优化

### 2. 中期路线图  
- 分布式部署支持
- 高级插件系统
- 可视化规则编辑器
- 协作功能

### 3. 长期愿景
- 完全去中心化架构
- 跨平台客户端
- AI 辅助规则生成
- 生态系统建设

## 相关文档

- [API 参考](../user-guide/api-usage/http-api.md)
- [配置指南](../user-guide/configuration/config-files.md)
- [部署指南](../deployment/deployment-guide.md)
- [开发指南](../development/code-organization.md)
