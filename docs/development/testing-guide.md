# LOOM 测试指南

## 目录

1. [测试概述](#测试概述)
2. [测试策略](#测试策略)
3. [单元测试](#单元测试)
   - [测试框架](#测试框架)
   - [测试结构](#测试结构)
   - [测试示例](#测试示例)
4. [集成测试](#集成测试)
   - [组件集成测试](#组件集成测试)
   - [端到端测试](#端到端测试)
5. [性能测试](#性能测试)
   - [基准测试](#基准测试)
   - [负载测试](#负载测试)
   - [压力测试](#压力测试)
6. [兼容性测试](#兼容性测试)
   - [Python版本兼容性](#python版本兼容性)
   - [操作系统兼容性](#操作系统兼容性)
   - [LLM提供商兼容性](#llm提供商兼容性)
7. [测试工具](#测试工具)
   - [测试数据生成](#测试数据生成)
   - [测试环境管理](#测试环境管理)
   - [测试报告生成](#测试报告生成)
8. [测试覆盖率](#测试覆盖率)
   - [覆盖率目标](#覆盖率目标)
   - [覆盖率报告](#覆盖率报告)
   - [覆盖率提升](#覆盖率提升)
9. [持续集成](#持续集成)
   - [GitHub Actions](#github-actions)
   - [测试流水线](#测试流水线)
   - [质量门禁](#质量门禁)
10. [故障注入测试](#故障注入测试)
    - [错误处理测试](#错误处理测试)
    - [恢复测试](#恢复测试)
    - [边界条件测试](#边界条件测试)

## 测试概述

LOOM 采用全面的测试策略，确保系统的可靠性、性能和可维护性。测试覆盖从单元测试到端到端测试的各个层面。

### 测试金字塔

```
        ┌─────────────────┐
        │   端到端测试     │  ~10%
        └─────────────────┘
        ┌─────────────────┐
        │   集成测试      │  ~20%
        └─────────────────┘
        ┌─────────────────┐
        │   单元测试      │  ~70%
        └─────────────────┘
```

### 测试目标

- **功能正确性**: 确保所有功能按预期工作
- **性能要求**: 满足性能指标和响应时间要求
- **可靠性**: 系统在异常情况下保持稳定
- **兼容性**: 支持多种环境和配置
- **安全性**: 防止安全漏洞和数据泄露

## 测试策略

### 测试类型矩阵

| 测试类型 | 范围 | 频率 | 工具 | 目标覆盖率 |
|----------|------|------|------|------------|
| 单元测试 | 单个函数/类 | 每次提交 | pytest | >90% |
| 集成测试 | 组件间交互 | 每日 | pytest + docker | >80% |
| 端到端测试 | 完整工作流 | 每周 | playwright | >70% |
| 性能测试 | 系统性能 | 每月 | locust + k6 | 关键路径100% |
| 兼容性测试 | 环境兼容性 | 每版本 | tox | 所有支持环境 |

### 测试环境

- **开发环境**: 本地开发，快速反馈
- **测试环境**: 隔离环境，模拟生产
- **预生产环境**: 与生产环境一致
- **生产环境**: 监控和告警

## 单元测试

### 测试框架

#### 主要工具
- **pytest**: 主要测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-mock**: Mock对象支持
- **hypothesis**: 属性测试
- **pytest-cov**: 覆盖率报告

#### 配置文件
```yaml
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --cov=src.loom
    --cov-report=term-missing
    --cov-report=html
asyncio_mode = auto
```

### 测试结构

#### 测试目录组织
```
tests/
├── test_core/                    # 核心层测试
│   ├── test_config_manager.py
│   ├── test_session_manager.py
│   ├── test_turn_scheduler.py
│   ├── test_persistence_engine.py
│   └── test_prompt_assembler.py
├── test_rules/                   # 规则层测试
│   ├── test_markdown_canon.py
│   ├── test_rule_loader.py
│   └── test_version_control.py
├── test_interpretation/          # 解释层测试
│   ├── test_rule_interpreter.py
│   ├── test_llm_provider.py
│   ├── test_reasoning_pipeline.py
│   └── test_consistency_checker.py
├── test_memory/                  # 记忆层测试
│   ├── test_world_memory.py
│   ├── test_structured_store.py
│   ├── test_vector_store.py
│   └── test_memory_summarizer.py
├── test_intervention/            # 干预层测试
│   ├── test_player_intervention.py
│   ├── test_world_editor.py
│   ├── test_retcon_handler.py
│   └── test_ooc_handler.py
├── test_cli/                     # CLI测试
│   ├── test_commands.py
│   └── test_integration.py
├── test_web/                     # Web测试
│   ├── test_api.py
│   └── test_integration.py
├── test_utils/                   # 工具函数测试
│   ├── test_async_helpers.py
│   └── test_logging_config.py
├── conftest.py                   # 测试配置
└── fixtures/                     # 测试夹具
    ├── session_fixtures.py
    ├── memory_fixtures.py
    └── rule_fixtures.py
```

#### 测试类结构
```python
class TestComponentName:
    """组件测试类"""

    @pytest.fixture
    def setup_component(self):
        """设置测试组件"""
        pass

    def test_basic_functionality(self, setup_component):
        """测试基本功能"""
        pass

    @pytest.mark.asyncio
    async def test_async_functionality(self, setup_component):
        """测试异步功能"""
        pass

    @pytest.mark.parametrize("input,expected", [
        ("input1", "expected1"),
        ("input2", "expected2"),
    ])
    def test_with_parameters(self, input, expected):
        """参数化测试"""
        pass

    def test_error_handling(self):
        """测试错误处理"""
        with pytest.raises(ExpectedError):
            function_that_raises()
```

### 测试示例

#### 配置管理器测试
```python
# tests/test_core/test_config_manager.py
import pytest
import tempfile
import os
from src.loom.core.config_manager import ConfigManager

class TestConfigManager:
    """ConfigManager测试类"""

    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
            llm_providers:
              openai:
                type: openai
                model: gpt-3.5-turbo
            log_level: INFO
            """)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_load_config(self, temp_config_file):
        """测试配置加载"""
        config_manager = ConfigManager(config_path=temp_config_file)
        config = config_manager.get_config()

        assert config.log_level == "INFO"
        assert "openai" in config.llm_providers
        assert config.llm_providers["openai"].model == "gpt-3.5-turbo"

    def test_env_var_override(self, temp_config_file):
        """测试环境变量覆盖"""
        import os
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("LOOM_LOG_LEVEL", "DEBUG")
            config_manager = ConfigManager(config_path=temp_config_file)
            config = config_manager.get_config()

            assert config.log_level == "DEBUG"
```

#### 异步组件测试
```python
# tests/test_core/test_session_manager.py
import pytest
import asyncio
from src.loom.core.session_manager import SessionManager

class TestSessionManager:
    """SessionManager测试类"""

    @pytest.fixture
    async def session_manager(self):
        """创建SessionManager实例"""
        manager = SessionManager()
        await manager.initialize()
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """测试创建会话"""
        session = await session_manager.create_session(
            name="测试会话",
            config={"llm_provider": "openai"}
        )

        assert session.id is not None
        assert session.name == "测试会话"
        assert session.config["llm_provider"] == "openai"

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, session_manager):
        """测试并发会话创建"""
        tasks = []
        for i in range(5):
            task = session_manager.create_session(
                name=f"会话{i}",
                config={"llm_provider": "openai"}
            )
            tasks.append(task)

        sessions = await asyncio.gather(*tasks)
        assert len(sessions) == 5
        assert all(s.id is not None for s in sessions)
```

#### Mock测试
```python
# tests/test_interpretation/test_llm_provider.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.loom.interpretation.llm_provider import LLMProvider

class TestLLMProvider:
    """LLMProvider测试类"""

    @pytest.fixture
    def mock_llm_provider(self):
        """创建Mock LLM提供商"""
        provider = Mock(spec=LLMProvider)
        provider.generate = AsyncMock(return_value="Mock响应")
        provider.generate_stream = AsyncMock()
        provider.get_cost_estimate = Mock(return_value=0.001)
        return provider

    @pytest.mark.asyncio
    async def test_generate_response(self, mock_llm_provider):
        """测试生成响应"""
        response = await mock_llm_provider.generate("测试Prompt")
        assert response == "Mock响应"
        mock_llm_provider.generate.assert_called_once_with("测试Prompt")

    @pytest.mark.asyncio
    async def test_cost_estimation(self, mock_llm_provider):
        """测试成本估算"""
        cost = mock_llm_provider.get_cost_estimate("Prompt", "Response")
        assert cost == 0.001
```

## 集成测试

### 组件集成测试

#### 测试目标
- 验证组件间正确交互
- 测试数据流和状态传递
- 确保接口兼容性

#### 示例：规则解释集成测试
```python
# tests/test_integration/test_rule_interpretation.py
import pytest
from src.loom.rules.rule_loader import RuleLoader
from src.loom.interpretation.rule_interpreter import RuleInterpreter
from src.loom.memory.world_memory import WorldMemory

class TestRuleInterpretationIntegration:
    """规则解释集成测试"""

    @pytest.fixture
    async def integration_setup(self):
        """集成测试设置"""
        # 加载规则
        rule_loader = RuleLoader()
        canon = rule_loader.load_canon("test_canon")

        # 初始化解释器
        interpreter = RuleInterpreter()

        # 初始化记忆
        memory = WorldMemory(session_id="test_session")
        await memory.initialize()

        yield {
            "rule_loader": rule_loader,
            "interpreter": interpreter,
            "memory": memory,
            "canon": canon
        }

        await memory.cleanup()

    @pytest.mark.asyncio
    async def test_full_interpretation_flow(self, integration_setup):
        """测试完整解释流程"""
        setup = integration_setup

        # 解释规则
        interpretation = setup["interpreter"].interpret(setup["canon"])

        # 验证解释结果
        assert interpretation is not None
        assert len(interpretation.constraints) > 0
        assert len(interpretation.key_themes) > 0

        # 存储记忆
        memory_entity = {
            "type": "fact",
            "content": {"text": "测试事实"},
            "metadata": {"source": "test"}
        }
        await setup["memory"].store_entity(memory_entity)

        # 检索记忆
        entities = await setup["memory"].search_entities("测试")
        assert len(entities) > 0
```

### 端到端测试

#### 测试目标
- 验证完整工作流
- 测试用户交互场景
- 确保系统整体功能

#### 示例：完整会话测试
```python
# tests/test_e2e/test_full_session.py
import pytest
import asyncio
from src.loom.api.client import LoomClient

class TestFullSession:
    """完整会话端到端测试"""

    @pytest.fixture
    async def loom_client(self):
        """创建LOOM客户端"""
        client = LoomClient(base_url="http://localhost:8000")
        await client.connect()
        yield client
        await client.disconnect()

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_create_and_run_session(self, loom_client):
        """测试创建和运行会话"""
        # 创建会话
        session = await loom_client.create_session(
            name="端到端测试会话",
            canon_path="examples/basic_world.md",
            config={
                "llm_provider": "openai",
                "model": "gpt-3.5-turbo"
            }
        )

        assert session.id is not None
        assert session.status == "created"

        # 运行回合
        response = await loom_client.submit_turn(
            session_id=session.id,
            player_input="我观察周围环境"
        )

        assert response.turn_id is not None
        assert response.llm_response is not None
        assert len(response.llm_response) > 0

        # 获取会话状态
        session_status = await loom_client.get_session_status(session.id)
        assert session_status.current_turn == 1
        assert session_status.status == "active"

        # 导出会话
        export_data = await loom_client.export_session(
            session.id,
            format="json"
        )

        assert "session" in export_data
        assert "turns" in export_data
        assert len(export_data["turns"]) == 1
```

## 性能测试

### 基准测试

#### 测试目标
- 建立性能基准
- 检测性能回归
- 优化关键路径

#### 示例：回合处理基准测试
```python
# tests/performance/test_turn_processing.py
import pytest
import asyncio
import time
from src.loom.core.turn_scheduler import TurnScheduler

class TestTurnProcessingPerformance:
    """回合处理性能测试"""

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_turn_processing_latency(self, benchmark):
        """测试回合处理延迟"""
        scheduler = TurnScheduler(max_concurrent=3)

        def process_turn():
            turn = {
                "session_id": "test_session",
                "player_input": "测试输入",
                "timestamp": time.time()
            }
            result = asyncio.run(scheduler.submit_turn(turn))
            return result

        # 运行基准测试
        result = benchmark(process_turn)
        assert result is not None

    @pytest.mark.performance
    def test_concurrent_turn_processing(self):
        """测试并发回合处理"""
        scheduler = TurnScheduler(max_concurrent=5)

        async def submit_multiple_turns():
            tasks = []
            for i in range(10):
                turn = {
                    "session_id": f"session_{i}",
                    "player_input": f"输入{i}",
                    "timestamp": time.time()
                }
                task = scheduler.submit_turn(turn)
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return results

        # 测量执行时间
        start_time = time.time()
        results = asyncio.run(submit_multiple_turns())
        end_time = time.time()

        execution_time = end_time - start_time
        assert len(results) == 10
        assert execution_time < 5.0  # 5秒内完成
```

### 负载测试

#### 使用Locust进行负载测试
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class LoomUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_session(self):
        """创建会话"""
        self.client.post("/api/v1/sessions", json={
            "name": "负载测试会话",
            "canon": "basic_world.md"
        })

    @task(3)
    def submit_turn(self):
        """提交回合"""
        self.client.post("/api/v1/sessions/test_session/turns", json={
            "player_input": "测试输入"
        })

    @task
    def get_session_status(self):
        """获取会话状态"""
        self.client.get("/api/v1/sessions/test_session")
```

### 压力测试

#### 测试目标
- 测试系统极限
- 验证错误处理
- 确保资源清理

#### 示例：内存压力测试
```python
# tests/performance/test_memory_pressure.py
import pytest
import asyncio
from src.loom.memory.world_memory import WorldMemory

class TestMemoryPressure
