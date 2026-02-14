# 快速 API 开始指南

## 概述

本文档提供 LOOM API 的快速入门指南，帮助您快速开始使用 LOOM 的 API 功能。LOOM 提供多种 API 接口，包括 Python 客户端、HTTP REST API 和 CLI 命令。

## 1. Python 客户端 API

### 1.1 安装和导入

```python
# 安装 LOOM
# pip install ai-loom

# 导入核心模块
from loom import SessionManager, SessionConfig
from loom.interpretation import LLMProviderFactory
```

### 1.2 创建会话管理器

```python
import asyncio

async def create_session():
    # 创建会话管理器
    session_manager = SessionManager()

    # 配置会话
    config = SessionConfig(
        session_type="chinese_content",
        initial_prompt="用中文写一个科幻故事开头",
        max_turns=10
    )

    # 创建会话
    session = await session_manager.create_session(config)
    print(f"会话创建成功: {session.session_id}")

    # 运行会话
    await session.run()

    # 获取响应
    for turn in session.turns:
        print(f"回合 {turn.turn_number}: {turn.response[:100]}...")

    return session

# 运行异步函数
asyncio.run(create_session())
```

### 1.3 使用 DeepSeek 提供商

```python
from loom.interpretation import LLMProviderFactory

async def use_deepseek():
    # 配置 DeepSeek 提供商
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat",
        "thinking_enabled": False,
        "temperature": 1.0,
        "max_tokens": 4096
    }

    # 创建提供商
    provider = LLMProviderFactory.create_provider(config)

    # 生成文本
    response = await provider.generate(
        "用中文解释量子计算的基本原理",
        temperature=0.8,
        max_tokens=1000
    )

    print(f"响应: {response.content}")
    print(f"模型: {response.model}")
    print(f"使用令牌: {response.usage}")
    print(f"成本: ${response.cost:.6f}")

    return response

asyncio.run(use_deepseek())
```

### 1.4 推理模式示例

```python
async def use_deepseek_reasoner():
    # 配置 DeepSeek Reasoner（推理模式）
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-reasoner",
        "thinking_enabled": True,  # 启用推理模式
        "max_tokens": 32000
    }

    provider = LLMProviderFactory.create_provider(config)

    # 复杂推理任务
    prompt = """
    问题：如果一只猫从3米高的树上跳下，落地时的速度是多少？
    请展示完整的推理过程。
    """

    response = await provider.generate(prompt)

    print("=== 推理模式响应 ===")
    print(response.content)
    print(f"推理步骤: {response.metadata.get('thinking_steps', 'N/A')}")

    return response

asyncio.run(use_deepseek_reasoner())
```

## 2. HTTP REST API

### 2.1 启动 API 服务器

```bash
# 启动开发服务器
loom api serve --port 8000 --host 0.0.0.0

# 启动生产服务器（使用 uvicorn）
uvicorn loom.api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2.2 API 端点示例

#### 创建会话 (POST /api/v1/sessions)

```bash
curl -X POST "http://localhost:8000/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "session_type": "chinese_content",
    "initial_prompt": "用中文写一首关于春天的诗",
    "config": {
      "llm_provider": "deepseek",
      "llm_model": "deepseek-chat",
      "max_turns": 5
    }
  }'
```

**响应示例**:
```json
{
  "session_id": "sess_1234567890",
  "status": "created",
  "created_at": "2026-02-07T09:08:00Z",
  "config": {
    "llm_provider": "deepseek",
    "llm_model": "deepseek-chat"
  }
}
```

#### 发送消息 (POST /api/v1/sessions/{session_id}/turns)

```bash
curl -X POST "http://localhost:8000/api/v1/sessions/sess_1234567890/turns" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "继续写第二段",
    "metadata": {
      "user_id": "user_001",
      "request_source": "web_app"
    }
  }'
```

**响应示例**:
```json
{
  "turn_id": "turn_1234567890",
  "session_id": "sess_1234567890",
  "prompt": "继续写第二段",
  "response": "春天的第二段描写...",
  "model": "deepseek-chat",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 120,
    "total_tokens": 135
  },
  "cost": 0.0000567,
  "created_at": "2026-02-07T09:08:30Z"
}
```

#### 使用 DeepSeek 特定参数

```bash
curl -X POST "http://localhost:8000/api/v1/sessions/sess_1234567890/turns" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "解决这个数学问题：计算圆的面积，半径为5cm",
    "llm_config": {
      "provider": "deepseek",
      "model": "deepseek-reasoner",
      "thinking_enabled": true,
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }'
```

### 2.3 流式响应

```bash
# 使用 Server-Sent Events (SSE) 获取流式响应
curl -N "http://localhost:8000/api/v1/sessions/sess_1234567890/turns/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "用中文讲述一个神话故事",
    "stream": true
  }'
```

**流式响应示例**:
```
data: {"chunk": "很久", "finished": false}
data: {"chunk": "很久以前", "finished": false}
data: {"chunk": "很久以前，在", "finished": false}
data: {"chunk": null, "finished": true, "usage": {"total_tokens": 150}}
```

## 3. 配置 API 客户端

### 3.1 Python 客户端配置

```python
from loom.api import APIClient

# 创建 API 客户端
client = APIClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",  # 可选，用于认证
    timeout=30
)

# 使用 DeepSeek 作为默认提供商
client.set_default_provider("deepseek")
client.set_default_model("deepseek-chat")

# 创建会话
session = client.create_session(
    session_type="reasoning_tasks",
    initial_prompt="解释相对论的基本概念"
)

# 发送消息
response = client.send_message(
    session_id=session.id,
    prompt="用更简单的方式解释"
)

print(f"响应: {response.content}")
```

### 3.2 环境变量配置

```bash
# API 服务器配置
export LOOM_API_HOST="0.0.0.0"
export LOOM_API_PORT="8000"
export LOOM_API_KEY="your-secret-key"

# DeepSeek 配置
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export DEEPSEEK_MODEL="deepseek-chat"
export DEEPSEEK_THINKING_ENABLED="false"
```

### 3.3 配置文件

创建 `api_config.yaml`:

```yaml
api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  debug: false

  authentication:
    enabled: true
    api_keys:
      - "your-secret-key-1"
      - "your-secret-key-2"

  cors:
    enabled: true
    origins:
      - "http://localhost:3000"
      - "https://your-app.com"

llm_providers:
  deepseek:
    enabled: true
    api_key: ${DEEPSEEK_API_KEY:}
    default_model: "deepseek-chat"
    thinking_enabled: false

  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY:}
    default_model: "gpt-3.5-turbo"
```

## 4. 使用示例

### 4.1 中文内容生成

```python
import asyncio
from loom import SessionManager, SessionConfig

async def generate_chinese_content():
    """使用 DeepSeek 生成中文内容"""
    session_manager = SessionManager()

    config = SessionConfig(
        session_type="chinese_content",
        initial_prompt="""
        请写一篇关于人工智能未来发展的短文，要求：
        1. 使用中文
        2. 不少于300字
        3. 包含技术、伦理、社会影响三个方面
        """,
        llm_provider="deepseek",
        llm_model="deepseek-chat",
        max_turns=1
    )

    session = await session_manager.create_session(config)
    await session.run()

    response = session.turns[0].response
    print(f"生成内容:\n{response}")

    # 保存到文件
    with open("ai_future_chinese.txt", "w", encoding="utf-8") as f:
        f.write(response)

    return session

asyncio.run(generate_chinese_content())
```

### 4.2 推理任务处理

```python
async def solve_reasoning_problem():
    """使用 DeepSeek Reasoner 解决推理问题"""
    from loom.interpretation import LLMProviderFactory

    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-reasoner",
        "thinking_enabled": True
    }

    provider = LLMProviderFactory.create_provider(config)

    problems = [
        "如果所有猫都怕水，而汤姆是一只猫，那么汤姆怕水吗？请推理。",
        "一个篮子里有5个苹果，你拿走了2个，你还剩几个苹果？",
        "解释为什么天空是蓝色的，使用科学原理。"
    ]

    for i, problem in enumerate(problems, 1):
        print(f"\n问题 {i}: {problem}")
        response = await provider.generate(problem)
        print(f"回答: {response.content[:200]}...")
        print(f"推理模式: {response.metadata.get('thinking_enabled', False)}")

asyncio.run(solve_reasoning_problem())
```

### 4.3 批量处理

```python
async def batch_process():
    """批量处理多个请求"""
    from loom.interpretation import LLMProviderFactory

    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat",
        "enable_batching": True,
        "batch_size": 5,
        "batch_timeout": 0.5
    }

    provider = LLMProviderFactory.create_provider(config)

    prompts = [
        "写一句关于春天的诗",
        "翻译'Hello, world!'到中文",
        "计算2+2等于多少",
        "解释什么是机器学习",
        "推荐一本好书"
    ]

    # 批量生成
    responses = await asyncio.gather(
        *[provider.generate(prompt) for prompt in prompts]
    )

    for i, (prompt, response) in enumerate(zip(prompts, responses), 1):
        print(f"{i}. 提示: {prompt}")
        print(f"   响应: {response.content}")
        print(f"   成本: ${response.cost:.6f}")
        print()

asyncio.run(batch_process())
```

## 5. 错误处理

### 5.1 处理 API 错误

```python
import asyncio
from loom.api import APIClient, APIError

client = APIClient(base_url="http://localhost:8000")

async def safe_api_call():
    try:
        # 尝试创建会话
        session = await client.create_session(
            session_type="chinese_content",
            initial_prompt="测试"
        )
        return session

    except APIError as e:
        print(f"API 错误: {e.status_code} - {e.message}")

        if e.status_code == 401:
            print("认证失败，请检查 API 密钥")
        elif e.status_code == 429:
            print("请求过于频繁，请稍后重试")
        elif e.status_code == 500:
            print("服务器内部错误")

        return None

    except asyncio.TimeoutError:
        print("请求超时，请检查网络连接或增加超时时间")
        return None

    except Exception as e:
        print(f"未知错误: {type(e).__name__}: {e}")
        return None

asyncio.run(safe_api_call())
```

### 5.2 处理提供商错误

```python
async def handle_provider_errors():
    from loom.interpretation import LLMProviderFactory

    config = {
        "type": "deepseek",
        "api_key": "invalid-key",  # 无效的密钥
        "model": "deepseek-chat"
    }

    try:
        provider = LLMProviderFactory.create_provider(config)
        response = await provider.generate("测试")

    except Exception as e:
        print(f"提供商错误: {e}")

        # 尝试回退到其他提供商
        fallback_config = {
            "type": "openai",
            "api_key": "valid-openai-key",
            "model": "gpt-3.5-turbo"
        }

        fallback_provider = LLMProviderFactory.create_provider(fallback_config)
        response = await fallback_provider.generate("测试")
        print(f"使用回退提供商成功: {response.model}")

asyncio.run(handle_provider_errors())
```

## 6. 性能优化

### 6.1 启用缓存

```python
config = {
    "type": "deepseek",
    "api_key": "your-deepseek-api-key",
    "model": "deepseek-chat",
    "enable_caching": True,
    "cache_ttl": 300,  # 5分钟
    "cache_max_size": 1000  # 最大缓存条目数
}
```

### 6.2 连接池配置

```python
config = {
    "type": "deepseek",
    "api_key": "your-deepseek-api-key",
    "connection_pool_size": 10,  # 连接池大小
    "timeout": 60,  # 超时时间
    "max_retries": 3,  # 最大重试次数
    "retry_delay": 2.0  # 重试延迟
}
```

### 6.3 监控和日志

```python
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("loom.api")

# 监控指标
from loom.monitoring import MetricsCollector

metrics = MetricsCollector()

async def monitored_call():
    with metrics.timer("api_call"):
        response = await client.send_message(
            session_id="test",
            prompt="测试"
        )

    metrics.increment_counter("api_calls_total")
    metrics.record_gauge("response_tokens", response.usage.get("total_tokens", 0))

    logger.info(f"API调用完成: {response.model}, 令牌: {response.usage}")
```

## 下一步

1. **探索更多示例**: 查看 [API 示例](api-examples.md)
2. **了解详细 API**: 查看 [HTTP API 参考](http-api.md)
3. **学习 Python 客户端**: 查看 [Python 客户端指南](python-client.md)
4. **配置生产环境**: 查看 [部署指南](../../deployment/deployment-guide.md)
