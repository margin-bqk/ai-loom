# DeepSeek API 集成架构图

## 系统架构概览

```mermaid
graph TB
    subgraph "现有LLM提供商架构"
        A[LLMProvider抽象基类] --> B[OpenAIProvider]
        A --> C[AnthropicProvider]
        A --> D[GoogleProvider]
        A --> E[AzureProvider]
        A --> F[LocalProvider]
    end

    subgraph "新增DeepSeek集成"
        A --> G[DeepSeekProvider]
        G --> G1[API客户端]
        G --> G2[成本计算器]
        G --> G3[错误处理器]
    end

    subgraph "核心组件"
        H[LLMProviderFactory] --> I[提供商创建]
        J[ProviderManager] --> K[提供商管理]
        L[ConfigManager] --> M[配置加载]
    end

    subgraph "配置系统"
        N[llm_providers.yaml] --> O[DeepSeek配置]
        P[default_config.yaml] --> Q[默认设置]
        R[环境变量] --> S[API密钥]
    end

    subgraph "使用层"
        T[ReasoningPipeline] --> U[推理引擎]
        V[SessionManager] --> W[会话管理]
        X[CLI命令] --> Y[用户交互]
    end

    %% 连接关系
    I --> G
    M --> O
    M --> Q
    K --> G
    U --> G
    W --> K
    Y --> X
```

## 类关系图

```mermaid
classDiagram
    class LLMProvider {
        <<abstract>>
        +config: Dict
        +name: str
        +provider_type: str
        +model: str
        +generate(prompt: str, **kwargs) LLMResponse
        +generate_stream(prompt: str, **kwargs) AsyncGenerator
        +health_check() Dict
        +get_stats() Dict
        +close() None
    }

    class OpenAIProvider {
        +api_key: str
        +base_url: str
        +_generate_impl(prompt: str, **kwargs) LLMResponse
        +_calculate_cost(response: LLMResponse) float
    }

    class AnthropicProvider {
        +api_key: str
        +base_url: str
        +version: str
        +_generate_impl(prompt: str, **kwargs) LLMResponse
        +_calculate_cost(response: LLMResponse) float
    }

    class DeepSeekProvider {
        +api_key: str
        +base_url: str
        +thinking_enabled: bool
        +_generate_impl(prompt: str, **kwargs) LLMResponse
        +_calculate_cost(response: LLMResponse) float
        +validate_config() List[str]
    }

    class LLMProviderFactory {
        <<static>>
        +create_provider(config: Dict) LLMProvider
        +create_from_configs(configs: Dict) Dict[str, LLMProvider]
        +create_provider_manager(configs: Dict) ProviderManager
    }

    class ProviderManager {
        +providers: Dict[str, LLMProvider]
        +default_provider: str
        +register_provider(name: str, provider: LLMProvider) None
        +get_provider(name: str) LLMProvider
        +generate_with_fallback(prompt: str, **kwargs) LLMResponse
    }

    class LLMResponse {
        +content: str
        +model: str
        +usage: Dict[str, int]
        +metadata: Dict[str, Any]
        +to_dict() Dict
    }

    %% 继承关系
    LLMProvider <|-- OpenAIProvider
    LLMProvider <|-- AnthropicProvider
    LLMProvider <|-- DeepSeekProvider

    %% 创建关系
    LLMProviderFactory ..> DeepSeekProvider : creates
    LLMProviderFactory ..> OpenAIProvider : creates
    LLMProviderFactory ..> AnthropicProvider : creates

    %% 管理关系
    ProviderManager --> LLMProvider : manages
```

## 数据流图

```mermaid
sequenceDiagram
    participant User as 用户/应用
    participant Session as SessionManager
    participant Pipeline as ReasoningPipeline
    participant Manager as ProviderManager
    participant Factory as LLMProviderFactory
    participant Config as ConfigManager
    participant DeepSeek as DeepSeekProvider
    participant API as DeepSeek API

    User->>Session: 创建会话(类型: chinese_content)
    Session->>Config: 获取配置
    Config-->>Session: 返回配置(包含DeepSeek)

    Session->>Pipeline: 执行推理
    Pipeline->>Manager: 请求LLM生成
    Manager->>Factory: 获取提供商实例
    Factory->>Config: 读取提供商配置
    Config-->>Factory: 返回DeepSeek配置

    Factory->>DeepSeek: 创建DeepSeekProvider实例
    DeepSeek-->>Factory: 返回实例
    Factory-->>Manager: 返回提供商

    Manager->>DeepSeek: 调用generate()
    DeepSeek->>API: POST /chat/completions
    API-->>DeepSeek: 返回响应
    DeepSeek->>DeepSeek: 计算成本
    DeepSeek-->>Manager: 返回LLMResponse

    Manager-->>Pipeline: 返回响应
    Pipeline-->>Session: 返回推理结果
    Session-->>User: 返回会话响应
```

## 配置加载流程

```mermaid
flowchart TD
    A[启动应用] --> B[加载默认配置]
    B --> C[加载用户配置]
    C --> D[合并配置]
    D --> E{检查DeepSeek配置}

    E -->|存在| F[验证API密钥]
    E -->|不存在| G[使用默认值]

    F --> H{密钥有效?}
    H -->|是| I[启用DeepSeek提供商]
    H -->|否| J[禁用DeepSeek提供商]

    G --> K[创建默认配置]
    K --> I

    I --> L[注册到ProviderManager]
    J --> M[记录警告日志]

    L --> N[应用就绪]
    M --> N
```

## 错误处理流程

```mermaid
stateDiagram-v2
    [*] --> 正常状态

    正常状态 --> API调用: 用户请求
    API调用 --> 成功响应: HTTP 200
    API调用 --> 认证错误: HTTP 401
    API调用 --> 速率限制: HTTP 429
    API调用 --> 服务器错误: HTTP 5xx
    API调用 --> 网络超时: Timeout

    成功响应 --> 正常状态: 返回结果

    认证错误 --> 禁用提供商: 标记为不可用
    禁用提供商 --> 回退其他提供商: 自动切换
    回退其他提供商 --> 正常状态: 使用备用提供商

    速率限制 --> 等待重试: 指数退避
    等待重试 --> API调用: 重新尝试

    服务器错误 --> 临时禁用: 短时间禁用
    临时禁用 --> 健康检查: 定期检查
    健康检查 --> 正常状态: 恢复可用

    网络超时 --> 增加超时: 调整配置
    增加超时 --> API调用: 重新尝试
```

## 成本监控架构

```mermaid
graph LR
    subgraph "成本计算层"
        A[DeepSeekProvider] --> B[成本计算器]
        B --> C[定价模型]
        C --> D[输入: $0.28/1M tokens]
        C --> E[输出: $0.42/1M tokens]
    end

    subgraph "监控层"
        F[成本聚合器] --> G[实时监控]
        H[预算管理器] --> I[告警系统]
        J[使用分析] --> K[优化建议]
    end

    subgraph "报告层"
        L[成本报告] --> M[每日摘要]
        N[使用趋势] --> O[预测分析]
        P[提供商对比] --> Q[成本效益分析]
    end

    B --> F
    F --> L
    F --> N
    F --> P
    G --> I
    H --> I
    J --> K
```

## 集成测试架构

```mermaid
graph TB
    subgraph "测试金字塔"
        A1[单元测试] --> A2[DeepSeekProvider测试]
        B1[集成测试] --> B2[提供商管理器测试]
        C1[端到端测试] --> C2[完整会话测试]
    end

    subgraph "测试组件"
        D[Mock API服务器] --> E[模拟响应]
        F[测试配置] --> G[隔离环境]
        H[测试数据] --> I[验证用例]
    end

    subgraph "验证点"
        J[API兼容性] --> K[OpenAI格式兼容]
        L[错误处理] --> M[重试机制]
        N[成本计算] --> O[定价准确性]
        P[性能指标] --> Q[响应时间]
    end

    A2 --> D
    B2 --> F
    C2 --> H
    E --> J
    E --> L
    E --> N
    E --> P
```

## 部署阶段图

```mermaid
timeline
    title DeepSeek集成部署时间线
    section 第1周: 核心实现
        实现DeepSeekProvider类
        添加提供商工厂支持
        基础单元测试

    section 第2周: 配置集成
        更新配置文件
        CLI命令集成
        集成测试

    section 第3周: 测试优化
        端到端测试
        性能测试
        文档更新

    section 第4周: 部署发布
        预发布环境
        金丝雀发布
        全面发布
```

---

## 关键设计决策

### 1. API兼容性设计
- **决策**: 采用OpenAI兼容的API格式
- **理由**: DeepSeek API与OpenAI API高度兼容，减少适配成本
- **影响**: 可以利用现有的OpenAI SDK模式和测试用例

### 2. 成本计算模型
- **决策**: 实现精确的按token成本计算
- **理由**: DeepSeek采用独特的缓存命中/未命中定价
- **影响**: 需要特殊处理缓存token的成本计算

### 3. 错误处理策略
- **决策**: 实现多层错误处理和回退机制
- **理由**: DeepSeek服务可能在不同地区有不同可用性
- **影响**: 增加系统复杂性，但提高可靠性

### 4. 配置管理
- **决策**: 支持环境变量和配置文件双重配置
- **理由**: 符合现有系统的配置模式
- **影响**: 用户可以选择最方便的配置方式

### 5. 测试策略
- **决策**: 使用Mock API进行隔离测试
- **理由**: 避免测试时产生实际API成本
- **影响**: 需要维护Mock服务器和测试数据

---

## 技术规格总结

| 组件 | 规格 | 备注 |
|------|------|------|
| **API端点** | `https://api.deepseek.com/chat/completions` | 生产环境 |
| **认证方式** | Bearer Token | 与OpenAI相同 |
| **支持模型** | `deepseek-chat`, `deepseek-reasoner` | 128K上下文 |
| **定价模型** | $0.28/1M输入, $0.42/1M输出 | 缓存未命中价格 |
| **速率限制** | 无硬性限制 | 高流量时可能延迟 |
| **超时设置** | 默认60秒 | 可配置 |
| **重试策略** | 指数退避，最多3次 | 可配置 |
| **成本计算** | 基于实际token使用量 | 支持缓存命中统计 |

---

*图表最后更新: 2026-02-07*
*架构版本: 1.0*
