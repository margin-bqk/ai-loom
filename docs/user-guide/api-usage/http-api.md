# LOOM API 参考

本文档提供 LOOM 各层组件的详细 API 参考。

## 核心运行时层 API

### SessionManager

会话管理器，负责会话的生命周期管理。

```python
class SessionManager:
    def __init__(self, persistence_engine=None):
        """
        初始化会话管理器
        
        Args:
            persistence_engine: 持久化引擎实例（可选）
        """
    
    async def create_session(self, config: SessionConfig) -> Session:
        """
        创建新会话
        
        Args:
            config: 会话配置
            
        Returns:
            Session: 创建的会话对象
        """
    
    async def load_session(self, session_id: str) -> Optional[Session]:
        """
        加载会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Session]: 加载的会话，如果不存在则返回None
        """
    
    async def save_session(self, session: Session) -> bool:
        """
        保存会话
        
        Args:
            session: 要保存的会话
            
        Returns:
            bool: 是否保存成功
        """
    
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否删除成功
        """
    
    async def list_sessions(self) -> Dict[str, Session]:
        """
        列出所有会话
        
        Returns:
            Dict[str, Session]: 会话ID到会话对象的映射
        """
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
        """
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
        """
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
        """
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
        """
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
        """清空缓存"""
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
        """
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
        """
        session = await self.get_session()
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            payload = {
                "model": kwargs.get("model", self.model),
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False
            }
            
            # 处理推理模式
            if self.thinking_enabled:
                payload["thinking"] = {"type": "enabled"}
            else:
                payload["thinking"] = {"type": "disabled"}
            
            # 添加其他参数
            for key in ["frequency_penalty", "presence_penalty", "top_p", "stop"]:
                if key in kwargs:
                    payload[key] = kwargs[key]
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"DeepSeek API error: {response.status} - {error_text}")
                    raise Exception(f"API error: {response.status}")
                
                data = await response.json()
                
                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data["model"],
                    usage=data.get("usage", {}),
                    metadata={
                        "id": data.get("id"),
                        "finish_reason": data["choices"][0].get("finish_reason"),
                        "provider": "deepseek",
                        "thinking_enabled": self.thinking_enabled
                    }
                )
        finally:
            await self.release_session(session)
    
    def _calculate_cost(self, response: LLMResponse) -> float:
        """
        计算DeepSeek成本
        
        Args:
            response: LLM响应
            
        Returns:
            float: 计算出的成本（美元）
        """
        if not response.usage:
            return super()._calculate_cost(response)
        
        # DeepSeek定价模型
        input_tokens = response.usage.get("prompt_tokens", 0)
        output_tokens = response.usage.get("completion_tokens", 0)
        
        # 定价：$0.28/1M输入token，$0.42/1M输出token
        input_cost = (input_tokens / 1_000_000) * 0.28
        output_cost = (output_tokens / 1_000_000) * 0.42
        
        return input_cost + output_cost
    
    def validate_config(self) -> List[str]:
        """
        验证配置
        
        Returns:
            List[str]: 错误信息列表，空列表表示配置有效
        """
        errors = []
        if not self.api_key:
            errors.append("API key is required for DeepSeek provider")
        if not self.model:
            errors.append("Model is required for DeepSeek provider")
        return errors
    
    async def generate_stream(self, prompt: str, **kwargs):
        """
        流式生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Yields:
            str: 生成的文本块
        """
        # 实现SSE流式响应处理
        session = await self.get_session()
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            payload = {
                "model": kwargs.get("model", self.model),
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": True
            }
            
            if self.thinking_enabled:
                payload["thinking"] = {"type": "enabled"}
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            ) as response:
                async for line in response.content:
                    if line.startswith(b"data: "):
                        data = line[6:].strip()
                        if data == b"[DONE]":
                            break
                        # 解析SSE数据并yield文本块
                        # 这里简化处理，实际需要解析JSON
                        yield data.decode("utf-8")
        finally:
            await self.release_session(session)
```

### ReasoningPipeline

推理流水线，实现完整的推理流程。

```python
class ReasoningPipeline:
    def __init__(self, llm_provider: LLMProvider):
        """
        初始化推理流水线
        
        Args:
            llm_provider: LLM提供者
        """
    
    async def process(self, context: ReasoningContext) -> ReasoningResult:
        """
        处理推理流程
        
        Args:
            context: 推理上下文
            
        Returns:
            ReasoningResult: 推理结果
        """
    
    async def batch_process(self, contexts: List[ReasoningContext]) -> List[ReasoningResult]:
        """
        批量处理
        
        Args:
            contexts: 推理上下文列表
            
        Returns:
            List[ReasoningResult]: 推理结果列表
        """
```

## 世界记忆层 API

### WorldMemory

世界记忆管理器，管理结构化叙事状态存储。

```python
class WorldMemory:
    def __init__(self, session_id: str, structured_store=None, vector_store=None):
        """
        初始化世界记忆
        
        Args:
            session_id: 会话ID
            structured_store: 结构化存储（可选）
            vector_store: 向量存储（可选）
        """
    
    async def store_entity(self, entity: MemoryEntity) -> bool:
        """
        存储实体
        
        Args:
            entity: 记忆实体
            
        Returns:
            bool: 是否存储成功
        """
    
    async def retrieve_entity(self, entity_id: str) -> Optional[MemoryEntity]:
        """
        检索实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Optional[MemoryEntity]: 检索到的实体
        """
    
    async def search_entities(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[MemoryEntity]:
        """
        搜索实体
        
        Args:
            query: 搜索查询
            filters: 过滤条件（可选）
            limit: 结果数量限制
            
        Returns:
            List[MemoryEntity]: 搜索到的实体列表
        """
    
    async def add_relation(self, relation: MemoryRelation) -> bool:
        """
        添加关系
        
        Args:
            relation: 记忆关系
            
        Returns:
            bool: 是否添加成功
        """
    
    async def get_related_entities(self, entity_id: str, relation_type: Optional[MemoryRelationType] = None) -> List[MemoryEntity]:
        """
        获取相关实体
        
        Args:
            entity_id: 实体ID
            relation_type: 关系类型（可选）
            
        Returns:
            List[MemoryEntity]: 相关实体列表
        """
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
```

### MemorySummarizer

记忆摘要生成器，生成记忆摘要。

```python
class MemorySummarizer:
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        初始化记忆摘要生成器
        
        Args:
            llm_provider: LLM提供者（可选）
        """
    
    async def generate_summary(self, entities: List[MemoryEntity], context: Dict[str, Any] = None) -> Optional[MemorySummary]:
        """
        生成记忆摘要
        
        Args:
            entities: 实体列表
            context: 上下文信息（可选）
            
        Returns:
            Optional[MemorySummary]: 生成的摘要
        """
    
    async def process_summarization(self, world_memory, force: bool = False) -> Optional[MemorySummary]:
        """
        处理摘要流程
        
        Args:
            world_memory: 世界记忆实例
            force: 是否强制摘要
            
        Returns:
            Optional[MemorySummary]: 生成的摘要
        """
```

## 玩家干预层 API

### PlayerIntervention

玩家干预处理器，解析和处理玩家干预。

```python
class PlayerIntervention:
    def __init__(self):
        """初始化玩家干预处理器"""
    
    def parse_input(self, player_input: str) -> Dict[str, Any]:
        """
        解析玩家输入，提取干预
        
        Args:
            player_input: 玩家输入文本
            
        Returns:
            Dict[str, Any]: 解析结果，包含清理后的输入和干预列表
        """
    
    async def process_interventions(self, interventions: List[Intervention], session_context: Dict[str, Any]) -> List[InterventionResult]:
        """
        处理干预列表
        
        Args:
            interventions: 干预列表
            session_context: 会话上下文
            
        Returns:
            List[InterventionResult]: 处理结果列表
        """
    
    async def validate_permission(self, intervention: Intervention, rules_text: str) -> bool:
        """
        验证干预权限
        
        Args:
            intervention: 干预对象
            rules_text: 规则文本
            
        Returns:
            bool: 是否允许该干预
        """
    
    def merge_interventions_into_prompt(self, clean_input: str, intervention_results: List[InterventionResult]) -> str:
        """
        将干预合并到Prompt中
        
        Args:
            clean_input: 清理后的输入
            intervention_results: 干预处理结果
            
        Returns:
            str: 合并后的Prompt
        """
```

### WorldEditor

世界编辑器，处理玩家对世界状态的直接编辑。

```python
class WorldEditor:
    def __init__(self, world_memory: Optional[WorldMemory] = None):
        """
        初始化世界编辑器
        
        Args:
            world_memory: 世界记忆（可选）
        """
    
    def parse_edit_command(self, edit_text: str) -> Optional[EditCommand]:
        """
        解析编辑命令文本
        
        Args:
            edit_text: 编辑命令文本
            
        Returns:
            Optional[EditCommand]: 解析后的编辑命令
        """
    
    async def execute_edit(self, command: EditCommand, session_context: Dict[str, Any]) -> EditResult:
        """
        执行编辑命令
        
        Args:
            command: 编辑命令
            session_context: 会话上下文
            
        Returns:
            EditResult: 编辑结果
        """
    
    async def validate_edit(self, command: EditCommand, rules_text: str) -> Tuple[bool, List[str]]:
        """
        验证编辑是否允许
        
        Args:
            command: 编辑命令
            rules_text: 规则文本
            
        Returns:
            Tuple[bool, List[str]]: (是否允许, 错误信息列表)
        """
```

### RetconHandler

Retcon处理器，处理追溯性修改。

```python
class RetconHandler:
    def __init__(self, world_memory: Optional[WorldMemory] = None):
        """
        初始化Retcon处理器
        
        Args:
            world_memory: 世界记忆（可选）
        """
    
    def parse_retcon_command(self, retcon_text: str) -> Optional[RetconOperation]:
        """
        解析Retcon命令
        
        Args:
            retcon_text: Retcon命令文本
            
        Returns:
            Optional[RetconOperation]: 解析后的Retcon操作
        """
    
    async def execute_retcon(self, operation: RetconOperation, session_context: Dict[str, Any]) -> RetconResult:
        """
        执行Retcon操作
        
        Args:
            operation: Retcon操作
            session_context: 会话上下文
            
        Returns:
            RetconResult: Retcon结果
        """
    
    async def rollback_to_version(self, version_id: str) -> bool:
        """
        回滚到指定版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            bool: 是否回滚成功
        """
    
    async def validate_retcon(self, operation: RetconOperation, rules_text: str) -> Tuple[bool, List[str]]:
        """
        验证Retcon是否允许
        
        Args:
            operation: Retcon操作
            rules_text: 规则文本
            
        Returns:
            Tuple[bool, List[str]]: (是否允许, 错误信息列表)
        """
```

## 工具函数 API

### 日志配置

```python
def get_logger(name: str) -> logging.Logger:
    """
    获取配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """

def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    设置日志配置
    
    Args:
        level: 日志级别
        log_file: 日志文件路径（可选）
    """
```

### 异步辅助函数

```python
async def run_with_timeout(coro, timeout: float, default=None):
    """
    带超时运行协程
    
    Args:
        coro: 协程
        timeout: 超时时间（秒）
        default: 超时时的默认返回值
        
    Returns:
        Any: 协程结果或默认值
    """

async def batch_process(items: List[Any], process_func: Callable, max_concurrent: int = 5):
    """
    批量处理项目
    
    Args:
        items: 项目列表
        process_func: 处理函数
        max_concurrent: 最大并发数
        
    Returns:
        List[Any]: 处理结果列表
    """
```

## 配置管理 API

### ConfigManager

配置管理器，负责配置加载与环境变量管理。

```python
class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径（可选）
        """
    
    def get_config(self) -> AppConfig:
        """
        获取配置
        
        Returns:
            AppConfig: 应用配置
        """
    
    def save_config(self, config: Optional[AppConfig] = None):
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置（可选，默认为当前配置）
        """
    
    def get_llm_provider_config(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """
        获取LLM提供商配置
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            Optional[LLMProviderConfig]: 提供商配置
        """
    
    def update_llm_api_key(self, provider_name: str, api_key: str):
        """
        更新LLM API密钥
        
        Args:
            provider_name: 提供商名称
            api_key: API密钥
        """
    
    def reload(self):
        """重新加载配置"""
```

## 数据模型

### 核心数据模型

```python
@dataclass
class Session:
    """会话实体"""
    id: str
    name: str
    config: SessionConfig
    created_at: datetime
    updated_at: datetime
    current_turn: int = 0
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Turn:
    """回合实体"""
    id: str
    session_id: str
    turn_number: int
    player_input: str
    status: TurnStatus = TurnStatus.PENDING
    llm_response: Optional[str] = None
    memories_used: List[str] = field(default_factory=list)
    interventions: List[Dict[str,