# LOOM API 参考

本文档提供 LOOM 各层组件的详细 API 参考。

## 核心运行时层 API

### SessionManager

会话管理器，负责会话的生命周期管理。

```python
class SessionManager:
    def __init__(self, persistence_engine=None, config_manager=None):
        """
        初始化会话管理器

        Args:
            persistence_engine: 持久化引擎实例（可选）
            config_manager: 配置管理器实例（可选）
        """

    async def create_session(self, config: SessionConfig) -> Session:
        """
        创建新会话

        Args:
            config: 会话配置

        Returns:
            Session: 创建的会话对象
        """

    async def load_session(self, session_id: str, force_reload: bool = False) -> Optional[Session]:
        """
        加载会话

        Args:
            session_id: 会话ID
            force_reload: 是否强制重新加载（忽略缓存）

        Returns:
            Optional[Session]: 加载的会话，如果不存在则返回None
        """

    async def save_session(self, session: Session, force: bool = False) -> bool:
        """
        保存会话

        Args:
            session: 要保存的会话
            force: 是否强制保存（忽略自动保存设置）

        Returns:
            bool: 是否保存成功
        """

    async def delete_session(self, session_id: str, permanent: bool = True) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID
            permanent: 是否永久删除（True=永久删除，False=归档）

        Returns:
            bool: 是否删除成功
        """

    async def list_sessions(self, include_inactive: bool = False) -> Dict[str, Session]:
        """
        列出所有会话

        Args:
            include_inactive: 是否包含非活跃会话（已归档、已完成等）

        Returns:
            Dict[str, Session]: 会话ID到会话对象的映射
        """

    async def update_session_status(self, session_id: str, status: SessionStatus) -> bool:
        """
        更新会话状态

        Args:
            session_id: 会话ID
            status: 新的会话状态（SessionStatus枚举值）

        Returns:
            bool: 是否更新成功
        """

    async def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict[str, Any]]: 会话统计信息字典，包含：
                - session_id: 会话ID
                - name: 会话名称
                - status: 会话状态
                - current_turn: 当前回合数
                - total_turns: 总回合数
                - created_at: 创建时间
                - last_activity: 最后活动时间
                - uptime_hours: 运行时长（小时）
                - turns_per_hour: 每小时回合数
                - config: 配置信息
        """

    async def cleanup_inactive_sessions(self, max_inactive_hours: int = 24) -> int:
        """
        清理不活跃的会话

        Args:
            max_inactive_hours: 最大不活跃小时数（默认24小时）

        Returns:
            int: 清理的会话数量
        """

    async def search_sessions(self, query: Dict[str, Any]) -> List[Session]:
        """
        搜索会话

        Args:
            query: 搜索查询字典，支持以下字段：
                - name: 按名称搜索（模糊匹配）
                - status: 按状态搜索（精确匹配）
                - created_after: 创建时间之后（ISO格式字符串或datetime对象）
                - created_before: 创建时间之前（ISO格式字符串或datetime对象）

        Returns:
            List[Session]: 匹配的会话列表
        ```
```

### TurnScheduler

回合调度器，管理异步回合队列和并发。

```python
class TurnScheduler:
    def __init__(self, max_concurrent: int = 3):
        """
        初始化回合调度器

        Args:
            max_concurrent: 最大并发回合数
        """

    async def start(self):
        """启动调度器"""

    async def stop(self):
        """停止调度器"""

    async def submit_turn(self, turn: Turn) -> str:
        """
        提交回合到队列

        Args:
            turn: 回合对象

        Returns:
            str: 回合ID
        """

    async def get_turn_status(self, turn_id: str) -> Optional[TurnStatus]:
        """
        获取回合状态

        Args:
            turn_id: 回合ID

        Returns:
            Optional[TurnStatus]: 回合状态
        """

    def get_queue_size(self) -> int:
        """
        获取队列大小

        Returns:
            int: 队列中的回合数
        ```
```

### PromptAssembler

Prompt组装器，动态组装Prompt。

```python
class PromptAssembler:
    def __init__(self):
        """初始化Prompt组装器"""

    def assemble(self, context: PromptContext) -> str:
        """
        组装Prompt

        Args:
            context: Prompt上下文

        Returns:
            str: 组装后的Prompt
        """

    def register_template(self, name: str, template: str):
        """
        注册自定义模板

        Args:
            name: 模板名称
            template: 模板内容
        """

    def list_templates(self) -> List[str]:
        """
        列出所有可用模板

        Returns:
            List[str]: 模板名称列表
        ```
```

## 规则层 API

### RuleLoader

规则加载器，负责加载规则文件。

```python
class RuleLoader:
    def __init__(self, canon_dir: str = "./canon"):
        """
        初始化规则加载器

        Args:
            canon_dir: 规则目录路径
        """

    def load_canon(self, canon_name: str = "default") -> Optional[MarkdownCanon]:
        """
        加载规则集

        Args:
            canon_name: 规则集名称

        Returns:
            Optional[MarkdownCanon]: 加载的规则集
        """

    def get_all_canons(self) -> Dict[str, MarkdownCanon]:
        """
        获取所有规则集

        Returns:
            Dict[str, MarkdownCanon]: 规则集名称到规则集的映射
        """

    def start_watching(self):
        """开始监听文件变化"""

    def stop_watching(self):
        """停止监听文件变化"""

    def create_default_canon(self, canon_name: str = "default") -> bool:
        """
        创建默认规则集

        Args:
            canon_name: 规则集名称

        Returns:
            bool: 是否创建成功
        ```
```

### MarkdownCanon

Markdown规则集，表示解析后的规则。

```python
class MarkdownCanon:
    def __init__(self, path: Path, raw_content: str = ""):
        """
        初始化规则集

        Args:
            path: 规则文件路径
            raw_content: 原始Markdown内容
        """

    def get_section(self, name: str) -> Optional[CanonSection]:
        """
        获取指定章节

        Args:
            name: 章节名称

        Returns:
            Optional[CanonSection]: 章节对象
        """

    def get_section_by_type(self, section_type: CanonSectionType) -> Optional[CanonSection]:
        """
        按类型获取章节

        Args:
            section_type: 章节类型

        Returns:
            Optional[CanonSection]: 章节对象
        """

    def get_full_text(self) -> str:
        """
        获取完整规则文本

        Returns:
            str: 完整规则文本
        """

    def validate(self) -> List[str]:
        """
        验证规则完整性

        Returns:
            List[str]: 错误信息列表
        """

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        ```
```

## 解释层 API

### RuleInterpreter

规则解释器，解释Markdown规则。

```python
class RuleInterpreter:
    def __init__(self):
        """初始化规则解释器"""

    def interpret(self, canon: MarkdownCanon, use_cache: bool = True) -> InterpretationResult:
        """
        解释规则集

        Args:
            canon: 规则集
            use_cache: 是否使用缓存

        Returns:
            InterpretationResult: 解释结果
        """

    def clear_cache(self):
        """清空缓存```
```

### LLMProvider

LLM提供者抽象基类。

```python
class LLMProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM提供者

        Args:
            config: 配置字典
        """

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        生成文本

        Args:
            prompt: 输入提示
            **kwargs: 额外参数

        Returns:
            LLMResponse: LLM响应
        """

    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs):
        """
        流式生成文本

        Args:
            prompt: 输入提示
            **kwargs: 额外参数

        Yields:
            str: 生成的文本块
        """

    def get_cost_estimate(self, prompt: str, response: str = "") -> float:
        """
        估算成本

        Args:
            prompt: 输入提示
            response: 响应文本

        Returns:
            float: 估算成本
        ```
```

### DeepSeekProvider

DeepSeek API 提供者，支持中文优化和推理模式。

```python
class DeepSeekProvider(LLMProvider):
    """DeepSeek API提供者"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化DeepSeek提供者

        Args:
            config: 配置字典，包含以下字段：
                - api_key: DeepSeek API密钥
                - base_url: API基础URL（默认: https://api.deepseek.com）
                - model: 模型名称（deepseek-chat 或 deepseek-reasoner）
                - thinking_enabled: 是否启用推理模式
                - max_tokens: 最大生成令牌数
                - temperature: 温度参数
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.deepseek.com")
        self.thinking_enabled = config.get("thinking_enabled", False)

        # DeepSeek特定配置
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 1.0)

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """
        生成文本的具体实现

        Args:
            prompt: 输入提示
            **kwargs: 额外参数

        Returns:
            LLMResponse: LLM响应

        Raises:
            Exception: API调用失败时抛出异常
        ```
```

## 增强组件 API

### EnhancedReasoningPipeline

增强推理管道，提供高级推理和分析功能。

```python
class EnhancedReasoningPipeline:
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化增强推理管道

        Args:
            config: 配置字典，包含以下字段：
                - enable_semantic_analysis: 是否启用语义分析
                - enable_consistency_check: 是否启用一致性检查
                - enable_explainability: 是否启用可解释性分析
                - confidence_threshold: 置信度阈值（0.0-1.0）
        """

    async def process(self, context: ReasoningContext) -> EnhancedInterpretationResult:
        """
        处理推理请求

        Args:
            context: 推理上下文

        Returns:
            EnhancedInterpretationResult: 增强解释结果，包含：
                - interpretation: 基础解释结果
                - semantic_analysis: 语义分析结果
                - consistency_report: 一致性检查报告
                - explainability_report: 可解释性报告
                - confidence_score: 综合置信度（0.0-1.0）
                - confidence_breakdown: 置信度细分
                - metadata_enhanced: 增强元数据
        ```
```

### EnhancedContextBuilder

增强上下文构建器，提供智能上下文管理。

```python
class EnhancedContextBuilder:
    def __init__(self, memory_backend=None):
        """
        初始化增强上下文构建器

        Args:
            memory_backend: 记忆后端实例（可选）
        """

    async def build_context(self, session_id: str, query: str) -> EnhancedContext:
        """
        构建增强上下文

        Args:
            session_id: 会话ID
            query: 查询文本

        Returns:
            EnhancedContext: 增强上下文，包含：
                - base_context: 基础上下文
                - relevant_memories: 相关记忆
                - semantic_connections: 语义连接
                - contextual_embeddings: 上下文嵌入
                - temporal_awareness: 时间感知信息
        ```
```

### EnhancedConsistencyChecker

增强一致性检查器，提供高级一致性验证。

```python
class EnhancedConsistencyChecker:
    def __init__(self, llm_provider=None):
        """
        初始化增强一致性检查器

        Args:
            llm_provider: LLM提供者实例（可选）
        """

    async def check_consistency(self, rules: List[str], context: Dict[str, Any]) -> ConsistencyReport:
        """
        检查规则一致性

        Args:
            rules: 规则列表
            context: 上下文信息

        Returns:
            ConsistencyReport: 一致性报告，包含：
                - is_consistent: 是否一致
                - conflicts: 冲突列表
                - severity_scores: 严重性评分
                - resolution_suggestions: 解决建议
                - semantic_analysis: 语义分析结果
        ```
```

### EnhancedProviderManager

增强提供者管理器，提供智能LLM提供者选择。

```python
class EnhancedProviderManager:
    def __init__(self, config_manager=None):
        """
        初始化增强提供者管理器

        Args:
            config_manager: 配置管理器实例（可选）
        """

    async def select_provider(self, session_type: str, requirements: Dict[str, Any]) -> LLMProvider:
        """
        智能选择LLM提供者

        Args:
            session_type: 会话类型
            requirements: 需求字典，包含：
                - language_preference: 语言偏好
                - reasoning_required: 是否需要推理
                - cost_constraint: 成本约束
                - latency_requirement: 延迟要求

        Returns:
            LLMProvider: 选择的LLM提供者实例
        ```
```

### EnhancedWorldMemory

增强世界记忆，提供高级记忆管理。

```python
class EnhancedWorldMemory:
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化增强世界记忆

        Args:
            config: 配置字典，包含以下字段：
                - summarizer_enabled: 是否启用总结器
                - semantic_indexing: 是否启用语义索引
                - temporal_awareness: 是否启用时间感知
                - relationship_tracking: 是否启用关系跟踪
        """

    async def store_memory(self, session_id: str, memory: MemoryEntry) -> str:
        """
        存储记忆

        Args:
            session_id: 会话ID
            memory: 记忆条目

        Returns:
            str: 记忆ID
        """

    async def query_memories(self, session_id: str, query: str,
                           semantic_search: bool = True) -> List[MemoryEntry]:
        """
        查询记忆

        Args:
            session_id: 会话ID
            query: 查询文本
            semantic_search: 是否使用语义搜索

        Returns:
            List[MemoryEntry]: 匹配的记忆条目列表
        ```
```

## 使用示例

### 基本会话管理

```python
from src.loom.core.session_manager import SessionManager, SessionConfig
from src.loom.core.config_manager import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager()

# 初始化会话管理器
session_manager = SessionManager(config_manager=config_manager)

# 创建会话配置
config = SessionConfig(
    name="奇幻冒险会话",
    canon_path="./canon/fantasy_basic.md",
    memory_backend="sqlite",
    llm_provider="deepseek",
    max_turns=100,
    auto_save=True,
    auto_save_interval=5
)

# 创建会话
session = await session_manager.create_session(config)

# 获取会话统计
stats = await session_manager.get_session_stats(session.id)
print(f"会话统计: {stats}")

# 搜索会话
query = {
    "name": "奇幻",
    "status": "active",
    "created_after": "2024-01-01T00:00:00"
}
sessions = await session_manager.search_sessions(query)
print(f"找到 {len(sessions)} 个匹配的会话")
```

### 使用增强组件

```python
from src.loom.interpretation.enhanced_reasoning_pipeline import EnhancedReasoningPipeline
from src.loom.interpretation.enhanced_context_builder import EnhancedContextBuilder
from src.loom.memory.enhanced_world_memory import EnhancedWorldMemory

# 初始化增强组件
reasoning_pipeline = EnhancedReasoningPipeline({
    "enable_semantic_analysis": True,
    "enable_consistency_check": True,
    "confidence_threshold": 0.7
})

context_builder = EnhancedContextBuilder()
world_memory = EnhancedWorldMemory({
    "summarizer_enabled": True,
    "semantic_indexing": True
})

# 构建增强上下文
enhanced_context = await context_builder.build_context(
    session_id="session_123",
    query="主角遇到了什么危险？"
)

# 使用增强推理管道
result = await reasoning_pipeline.process(enhanced_context)
print(f"推理置信度: {result.confidence_score}")
print(f"语义分析: {result
