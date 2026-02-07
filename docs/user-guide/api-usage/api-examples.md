# API 示例

## 概述

本文档提供 LOOM API 的详细使用示例，涵盖常见的使用场景和最佳实践。每个示例都包含完整的代码和解释。

## 1. 基础示例

### 1.1 创建简单会话

```python
import asyncio
from loom import SessionManager, SessionConfig

async def basic_session():
    """创建基础会话示例"""
    # 初始化会话管理器
    session_manager = SessionManager()
    
    # 配置会话
    config = SessionConfig(
        session_type="quick_chat",
        initial_prompt="你好，请介绍一下你自己",
        max_turns=3
    )
    
    # 创建会话
    session = await session_manager.create_session(config)
    print(f"会话ID: {session.session_id}")
    
    # 运行会话
    await session.run()
    
    # 显示所有回合
    for turn in session.turns:
        print(f"\n回合 {turn.turn_number}:")
        print(f"提示: {turn.prompt[:50]}...")
        print(f"响应: {turn.response[:100]}...")
    
    return session

# 运行示例
asyncio.run(basic_session())
```

### 1.2 使用特定 LLM 提供商

```python
async def use_specific_provider():
    """使用 DeepSeek 提供商"""
    from loom.interpretation import LLMProviderFactory
    
    # 配置 DeepSeek 提供商
    deepseek_config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat",
        "temperature": 0.8,
        "max_tokens": 1000
    }
    
    # 创建提供商
    provider = LLMProviderFactory.create_provider(deepseek_config)
    
    # 生成文本
    response = await provider.generate(
        "用中文写一首关于秋天的诗",
        temperature=0.7
    )
    
    print(f"模型: {response.model}")
    print(f"响应:\n{response.content}")
    print(f"令牌使用: {response.usage}")
    print(f"成本: ${response.cost:.6f}")
    
    return response

asyncio.run(use_specific_provider())
```

## 2. DeepSeek 特定示例

### 2.1 中文内容生成

```python
async def chinese_content_generation():
    """使用 DeepSeek 生成中文内容"""
    from loom.interpretation import LLMProviderFactory
    
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat",
        "temperature": 0.9,
        "max_tokens": 2000
    }
    
    provider = LLMProviderFactory.create_provider(config)
    
    # 中文内容生成任务
    tasks = [
        {
            "name": "故事创作",
            "prompt": "写一个关于未来城市的科幻短篇故事，不少于500字"
        },
        {
            "name": "文章改写",
            "prompt": "将以下英文技术文章摘要改写成中文：'Artificial intelligence is transforming industries...'"
        },
        {
            "name": "诗歌创作",
            "prompt": "创作一首七言律诗，主题为山水田园"
        }
    ]
    
    for task in tasks:
        print(f"\n=== {task['name']} ===")
        response = await provider.generate(task["prompt"])
        print(f"生成内容:\n{response.content[:300]}...")
        print(f"长度: {len(response.content)} 字符")
        print(f"成本: ${response.cost:.6f}")
    
    return True

asyncio.run(chinese_content_generation())
```

### 2.2 推理模式使用

```python
async def reasoning_mode_example():
    """使用 DeepSeek Reasoner 进行推理"""
    from loom.interpretation import LLMProviderFactory
    
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-reasoner",
        "thinking_enabled": True,  # 启用推理模式
        "max_tokens": 4000
    }
    
    provider = LLMProviderFactory.create_provider(config)
    
    # 推理问题
    reasoning_problems = [
        {
            "category": "逻辑推理",
            "problem": "如果所有鸟都会飞，企鹅是鸟，那么企鹅会飞吗？请展示推理过程。"
        },
        {
            "category": "数学问题",
            "problem": "一个水池有进水管和出水管。进水管单独注满水池需要3小时，出水管单独排空水池需要4小时。如果同时打开进水管和出水管，需要多少小时才能注满水池？"
        },
        {
            "category": "科学推理",
            "problem": "解释为什么冰会浮在水面上，而大多数固体都会下沉。"
        }
    ]
    
    for problem in reasoning_problems:
        print(f"\n=== {problem['category']} ===")
        print(f"问题: {problem['problem']}")
        
        response = await provider.generate(
            problem["problem"],
            temperature=0.3  # 降低温度以获得更确定的推理
        )
        
        print(f"\n推理结果:\n{response.content}")
        print(f"模型: {response.model}")
        print(f"推理模式: {response.metadata.get('thinking_enabled', False)}")
        print(f"令牌使用: {response.usage.get('total_tokens', 0)}")
    
    return True

asyncio.run(reasoning_mode_example())
```

### 2.3 长上下文处理

```python
async def long_context_example():
    """利用 DeepSeek 的 128K 上下文处理长文档"""
    from loom.interpretation import LLMProviderFactory
    
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat",
        "max_tokens": 8000  # 增加输出令牌限制
    }
    
    provider = LLMProviderFactory.create_provider(config)
    
    # 模拟长文档（在实际使用中，可以加载真实的长文档）
    long_document = """
    # 人工智能发展报告（2025年）
    
    ## 第一章：技术进展
    
    2025年，人工智能技术取得了显著进展...
    （此处省略大量内容，实际文档可能长达数万字）
    
    ## 第二章：行业应用
    
    人工智能在各行业的应用日益广泛...
    
    ## 第三章：伦理挑战
    
    随着AI技术的发展，伦理问题也日益突出...
    
    ## 第四章：未来展望
    
    展望未来，人工智能将继续深刻改变人类社会...
    """
    
    # 处理长文档的摘要任务
    prompt = f"""
    请阅读以下长文档并完成以下任务：
    
    文档内容：
    {long_document[:5000]}...（文档截断显示）
    
    任务：
    1. 总结文档的主要观点（不超过300字）
    2. 提取3个最重要的技术进展
    3. 提出2个主要的伦理挑战
    4. 给出1个未来发展的建议
    """
    
    print("正在处理长文档...")
    response = await provider.generate(prompt)
    
    print(f"\n=== 长文档处理结果 ===")
    print(response.content)
    print(f"\n文档处理统计:")
    print(f"输入令牌: {response.usage.get('prompt_tokens', 'N/A')}")
    print(f"输出令牌: {response.usage.get('completion_tokens', 'N/A')}")
    print(f"总令牌: {response.usage.get('total_tokens', 'N/A')}")
    print(f"成本: ${response.cost:.6f}")
    
    return response

asyncio.run(long_context_example())
```

## 3. 高级会话管理

### 3.1 多轮对话 with DeepSeek

```python
async def multi_turn_conversation():
    """多轮对话示例"""
    from loom import SessionManager, SessionConfig
    
    session_manager = SessionManager()
    
    # 配置使用 DeepSeek
    config = SessionConfig(
        session_type="chinese_content",
        initial_prompt="我们来讨论人工智能的未来发展",
        llm_provider="deepseek",
        llm_model="deepseek-chat",
        max_turns=5,
        memory_enabled=True  # 启用记忆系统
    )
    
    session = await session_manager.create_session(config)
    
    # 定义对话流程
    conversation_flow = [
        "首先，请谈谈AI在医疗领域的应用前景",
        "那么在教育领域呢？AI会如何改变教育方式？",
        "这些发展会带来哪些伦理问题？",
        "对于个人来说，应该如何准备迎接AI时代？",
        "最后，请总结一下AI发展的关键趋势"
    ]
    
    print("=== 多轮对话开始 ===")
    
    for i, user_input in enumerate(conversation_flow, 1):
        print(f"\n[用户] 第{i}轮: {user_input}")
        
        # 发送用户输入
        turn = await session.add_turn(user_input)
        
        print(f"[AI] 响应: {turn.response[:200]}...")
        print(f"模型: {turn.model}")
        print(f"成本: ${turn.cost:.6f}")
        
        # 模拟用户思考时间
        await asyncio.sleep(1)
    
    print(f"\n=== 对话结束 ===")
    print(f"总回合数: {len(session.turns)}")
    print(f"总成本: ${sum(t.cost for t in session.turns):.6f}")
    print(f"总令牌: {sum(t.usage.get('total_tokens', 0) for t in session.turns)}")
    
    return session

asyncio.run(multi_turn_conversation())
```

### 3.2 会话持久化和恢复

```python
async def session_persistence():
    """会话持久化示例"""
    from loom import SessionManager, SessionConfig
    import json
    
    session_manager = SessionManager()
    
    # 创建新会话
    config = SessionConfig(
        session_type="world_building",
        initial_prompt="创建一个奇幻世界的设定",
        llm_provider="deepseek",
        llm_model="deepseek-chat"
    )
    
    session = await session_manager.create_session(config)
    
    # 进行一些对话
    await session.add_turn("这个世界的主要种族有哪些？")
    await session.add_turn("描述这个世界的魔法系统")
    
    print(f"会话ID: {session.session_id}")
    print(f"当前回合数: {len(session.turns)}")
    
    # 保存会话状态
    session_data = session.to_dict()
    
    with open(f"session_{session.session_id}.json", "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    print(f"会话已保存到: session_{session.session_id}.json")
    
    # 模拟应用重启后恢复会话
    print("\n=== 模拟应用重启 ===")
    
    with open(f"session_{session.session_id}.json", "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    
    # 从数据恢复会话
    restored_session = await session_manager.load_session(session.session_id)
    
    if restored_session:
        print(f"会话恢复成功: {restored_session.session_id}")
        print(f"恢复的回合数: {len(restored_session.turns)}")
        
        # 继续对话
        new_turn = await restored_session.add_turn("这个世界的历史是怎样的？")
        print(f"新响应: {new_turn.response[:150]}...")
    
    return session

asyncio.run(session_persistence())
```

## 4. 批量处理示例

### 4.1 批量文本生成

```python
async def batch_generation():
    """批量文本生成示例"""
    from loom.interpretation import LLMProviderFactory
    import asyncio
    
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat",
        "enable_batching": True,
        "batch_size": 10,
        "batch_timeout": 1.0
    }
    
    provider = LLMProviderFactory.create_provider(config)
    
    # 批量生成任务
    batch_prompts = [
        "写一句产品标语，主题是环保",
        "生成一个随机的人名",
        "写一个简短的天气描述",
        "创作一句励志名言",
        "描述一杯咖啡的味道",
        "写一个简短的笑话",
        "生成一个购物清单项目",
        "描述夕阳的景象",
        "写一句欢迎语",
        "生成一个任务名称"
    ]
    
    print("开始批量生成...")
    
    # 创建所有任务
    tasks = [provider.generate(prompt) for prompt in batch_prompts]
    
    # 并行执行
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    total_cost = 0
    total_tokens = 0
    
    for i, (prompt, response) in enumerate(zip(batch_prompts, responses), 1):
        if isinstance(response, Exception):
            print(f"{i}. 错误: {prompt[:30]}... -> {response}")
            continue
            
        print(f"{i}. {prompt[:30]}...")
        print(f"   响应: {response.content}")
        print(f"   令牌: {response.usage.get('total_tokens', 0)}")
        print(f"   成本: ${response.cost:.6f}")
        print()
        
        total_cost += response.cost
        total_tokens += response.usage.get('total_tokens', 0)
    
    print(f"=== 批量处理统计 ===")
    print(f"总任务数: {len(batch_prompts)}")
    print(f"成功数: {sum(1 for r in responses if not isinstance(r, Exception))}")
    print(f"总令牌: {total_tokens}")
    print(f"总成本: ${total_cost:.6f}")
    print(f"平均每任务成本: ${total_cost/len(batch_prompts):.6f}")
    
    return responses

asyncio.run(batch_generation())
```

### 4.2 成本优化批量处理

```python
async def cost_optimized_batch():
    """成本优化的批量处理"""
    from loom.interpretation import LLMProviderFactory
    
    # 配置多个提供商用于成本优化
    providers_config = {
        "deepseek": {
            "type": "deepseek",
            "api_key": "your-deepseek-api-key",
            "model": "deepseek-chat",
            "cost_per_token": 0.0000007  # 每令牌成本估算
        },
        "openai": {
            "type": "openai",
            "api_key": "your-openai-api-key",
            "model": "gpt-3.5-turbo",
            "cost_per_token": 0.000002  # 更高的成本
        }
    }
    
    # 根据任务复杂度选择提供商
    tasks = [
        {
            "prompt": "简单的问候语",
            "complexity": "low",
            "expected_tokens": 50
        },
        {
            "prompt": "中等复杂度的产品描述",
            "complexity": "medium",
            "expected_tokens": 200
        },
        {
            "prompt": "复杂的技术文档分析",
            "complexity": "high",
            "expected_tokens": 1000
        }
    ]
    
    # 创建提供商实例
    providers = {}
    for name, config in providers_config.items():
        providers[name] = LLMProviderFactory.create_provider(config)
    
    results = []
    
    for task in tasks:
        # 根据复杂度选择提供商
        if task["complexity"] == "low":
            provider = providers["deepseek"]  # 低成本提供商处理简单任务
            print(f"使用 DeepSeek 处理简单任务: {task['prompt'][:30]}...")
        elif task["complexity"] == "high":
            provider = providers["openai"]  # 高质量提供商处理复杂任务
            print(f"使用 OpenAI 处理复杂任务: {task['prompt'][:30]}...")
        else:
            # 中等复杂度任务，根据成本选择
            provider = providers["deepseek"]  # DeepSeek 成本更低
            print(f"使用 DeepSeek 处理中等任务: {task['prompt'][:30]}...")
        
        response = await provider.generate(task["prompt"])
        
        results.append({
            "task": task["prompt"],
            "provider": provider.provider_type,
            "response": response.content,
            "cost": response.cost,
            "tokens": response.usage.get("total_tokens", 0)
        })
    
    # 输出结果
    print("\n=== 成本优化处理结果 ===")
    total_cost = 0
    
    for result in results:
        print(f"\n任务: {result['task'][:40]}...")
        print(f"提供商: {result['provider']}")
        print(f"成本: ${result['cost']:.6f}")
        print(f"令牌: {result['tokens']}")
        total_cost += result["cost"]
    
    print(f"\n总成本: ${total_cost:.6f}")
    
    return results

asyncio.run(cost_optimized_batch())
```

## 5. 错误处理和重试

### 5.1 健壮的 API 调用

```python
async def robust_api_call():
    """包含错误处理和重试的健壮 API 调用"""
    from loom.interpretation import LLMProviderFactory
    import asyncio
    from tenacity import retry, stop_after_attempt, wait_exponential
    
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat",
        "max_retries": 3,
        "retry_delay": 2.0
    }
    
    # 创建重试装饰器
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_with_retry(prompt):
        provider = LLMProviderFactory.create_provider(config)
        return await provider.generate(prompt)
    
    try:
        response = await generate_with_retry(
            "这是一个测试提示，可能会失败"
        )
        print(f"成功: {response.content[:100]}...")
        return response
        
    except Exception as e:
        print(f"所有重试都失败了: {e}")
        
        # 尝试回退到其他提供商
        fallback_config = {
            "type": "openai",
            "api_key": "your-openai-api-key",
            "model": "gpt-3.5-turbo"
        }
        
        try:
            fallback_provider = LLMProviderFactory.create_provider(fallback_config)
            response = await fallback_provider.generate("这是一个测试提示")
            print(f"回退成功: {response.model}")
            return response
        except Exception as fallback_error:
            print(f"回退也失败了: {fallback_error}")
            return None

asyncio.run(robust_api_call())
```

### 5.2 监控和日志记录

```python
async def monitored_api_call():
    """包含监控和日志的 API 调用"""
    import logging
    from datetime import datetime
    from loom.interpretation import LLMProviderFactory
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("loom.api")
    
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat"
    }
    
    provider = LLMProviderFactory.create_provider(config)
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"开始 API 调用: {start_time}")
    
    try:
        response = await provider.generate(
            "测试监控和日志功能",
            temperature=0.7
        )
        
        # 记录成功信息
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"API 调用成功")
        logger.info(f"模型: {response.model}")
        logger.info(f"响应时间: {duration:.2f}秒")
        logger.info(f"令牌使用: {response.usage}")
        logger.info(f"成本: ${response.cost:.6f}")
        
        # 记录到监控系统
        monitor_data = {
            "timestamp": end_time.isoformat(),
            "provider": "deepseek",
            "model": response.model,
            "duration": duration,
            "tokens": response.usage.get("total_tokens", 0),
            "cost": response.cost,
            "success": True
        }
        
        # 这里可以添加将监控数据发送到监控系统的代码
        # 例如: send_to_monitoring_system(monitor_data)
        
        return response
        
    except Exception as e:
        # 记录错误信息
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.error(f"API 调用失败: {e}")
        logger.error(f"失败时间: {duration:.2f}秒")
        
        # 记录错误到监控系统
        monitor_data = {
            "timestamp": end_time.isoformat(),
            "provider": "deepseek",
            "duration": duration,
            "success": False,
            "error": str(e)
        }
        
        raise e

asyncio.run(monitored_api_call())
```

## 6. 集成示例

### 6.1 与 Web 框架集成

```python
# FastAPI 集成示例
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from loom.interpretation import LLMProviderFactory

app = FastAPI(title="LOOM API 服务")

# 请求模型
class GenerationRequest(BaseModel):
    prompt: str
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 1000

# 响应模型
class GenerationResponse(BaseModel):
    content: str
    model: str
    usage: dict
    cost: float
    duration: float

# 全局提供商实例
deepseek_provider = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化提供商"""
    global deepseek_provider
    
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat"
    }
    
    deepseek_provider = LLMProviderFactory.create_provider(config)
    print("DeepSeek 提供商初始化完成")

@app.post("/api/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    """文本生成端点"""
    import time
    
    if not deepseek_provider:
        raise HTTPException(status_code=500, detail="提供商未初始化")
    
    start_time = time.time()
    
    try:
        response = await deepseek_provider.generate(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        duration = time.time() - start_time
        
        return GenerationResponse(
            content=response.content,
            model=response.model,
            usage=response.usage,
            cost=response.cost,
            duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 运行: uvicorn example:app --reload
```

### 6.2 与数据库集成

```python
async def database_integration():
    """与数据库集成的示例"""
    import sqlite3
    from datetime import datetime
    from loom.interpretation import LLMProviderFactory
    
    # 初始化数据库
    conn = sqlite3.connect("loom_usage.db")
    cursor = conn.cursor()
    
    # 创建使用记录表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        prompt_tokens INTEGER,
        completion_tokens INTEGER,
        total_tokens INTEGER,
        cost REAL,
        duration REAL,
        success BOOLEAN
    )
    """)
    
    # 配置提供商
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat"
    }
    
    provider = LLMProviderFactory.create_provider(config)
    
    # 记录使用情况
    async def record_usage(provider, model, usage, cost, duration, success=True):
        cursor.execute("""
        INSERT INTO api_usage 
        (timestamp, provider, model, prompt_tokens, completion_tokens, total_tokens, cost, duration, success)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            provider,
            model,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
            usage.get("total_tokens", 0),
            cost,
            duration,
            success
        ))
        conn.commit()
    
    # 使用示例
    import time
    
    prompts = [
        "数据库集成测试1",
        "数据库集成测试2",
        "数据库集成测试3"
    ]
    
    for prompt in prompts:
        start_time = time.time()
        
        try:
            response = await provider.generate(prompt)
            duration = time.time() - start_time
            
            # 记录成功使用
            await record_usage(
                provider="deepseek",
                model=response.model,
                usage=response.usage,
                cost=response.cost,
                duration=duration,
                success=True
            )
            
            print(f"成功: {prompt} -> {response.content[:50]}...")
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 记录失败使用
            await record_usage(
                provider="deepseek",
                model=config["model"],
                usage={},
                cost=0,
                duration=duration,
                success=False
            )
            
            print(f"失败: {prompt} -> {e}")
    
    # 查询使用统计
    cursor.execute("""
    SELECT 
        provider,
        COUNT(*) as total_calls,
        SUM(total_tokens) as total_tokens,
        SUM(cost) as total_cost,
        AVG(duration) as avg_duration
    FROM api_usage 
    WHERE success = 1
    GROUP BY provider
    """)
    
    stats = cursor.fetchall()
    
    print("\n=== 使用统计 ===")
    for stat in stats:
        print(f"提供商: {stat[0]}")
        print(f"  总调用: {stat[1]}")
        print(f"  总令牌: {stat[2]}")
        print(f"  总成本: ${stat[3]:.6f}")
        print(f"  平均耗时: {stat[4]:.2f}秒")
    
    conn.close()
    return stats

asyncio.run(database_integration())
```

## 7. 性能测试示例

### 7.1 基准测试

```python
async def benchmark_deepseek():
    """DeepSeek 性能基准测试"""
    import asyncio
    import time
    from statistics import mean, median
    from loom.interpretation import LLMProviderFactory
    
    config = {
        "type": "deepseek",
        "api_key": "your-deepseek-api-key",
        "model": "deepseek-chat"
    }
    
    provider = LLMProviderFactory.create_provider(config)
    
    # 测试用例
    test_cases = [
        {"name": "短文本", "prompt": "写一句问候语", "expected_tokens": 50},
        {"name": "中等文本", "prompt": "写一段产品描述，大约100字", "expected_tokens": 200},
        {"name": "长文本", "prompt": "写一篇关于人工智能的短文，不少于300字", "expected_tokens": 500}
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"提示: {test_case['prompt']}")
        
        # 运行多次测试取平均值
        durations = []
        tokens_list = []
        costs = []
        
        for i in range(3):  # 每个测试运行3次
            print(f"  运行 {i+1}/3...")
            
            start_time = time.time()
            
            try:
                response = await provider.generate(
                    test_case["prompt"],
                    max_tokens=test_case["expected_tokens"] * 2
                )
                
                duration = time.time() - start_time
                durations.append(duration)
                tokens_list.append(response.usage.get("total_tokens", 0))
                costs.append(response.cost)
                
                print(f"    耗时: {duration:.2f}秒")
                print(f"    令牌: {response.usage.get('total_tokens', 0)}")
                print(f"    成本: ${response.cost:.6f}")
                
            except Exception as e:
                print(f"    错误: {e}")
                durations.append(None)
        
        # 计算统计信息
        valid_durations = [d for d in durations if d is not None]
        
        if valid_durations:
            results.append({
                "name": test_case["name"],
                "avg_duration": mean(valid_durations),
                "median_duration": median(valid_durations),
                "min_duration": min(valid_durations),
                "max_duration": max(valid_durations),
                "avg_tokens": mean(tokens_list),
                "avg_cost": mean(costs)
            })
    
    # 输出基准测试结果
    print("\n" + "="*50)
    print("DeepSeek 性能基准测试结果")
    print("="*50)
    
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  平均耗时: {result['avg_duration']:.2f}秒")
        print(f"  中位耗时: {result['median_duration']:.2f}秒")
        print(f"  最小耗时: {result['min_duration']:.2f}秒")
        print(f"  最大耗时: {result['max_duration']:.2f}秒")
        print(f"  平均令牌: {result['avg_tokens']:.0f}")
        print(f"  平均成本: ${result['avg_cost']:.6f}")
        print(f"  令牌/秒: {result['avg_tokens']/result['avg_duration']:.1f}")
        print(f"  成本/千令牌: ${(result['avg_cost']/result['avg_tokens']*1000):.4f}")
    
    return results

asyncio.run(benchmark_deepseek())
```

## 下一步

1. **探索更多场景**: 尝试将 LOOM API 集成到您的具体应用场景中
2. **优化性能**: 根据基准测试结果调整配置参数
3. **监控成本**: 使用数据库集成示例跟踪 API 使用成本
4. **错误处理**: 根据您的需求完善错误处理和重试逻辑
5. **扩展功能**: 参考 [HTTP API 参考](http-api.md) 了解更多 API 功能
