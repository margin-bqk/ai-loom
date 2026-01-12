# 阶段1：定位重构详细实施计划

## 概述

阶段1的目标是重新定位五层架构边界，确保严格解耦，为后续各层重构奠定基础。本阶段不改变各层内部实现，只关注层间接口和依赖关系。

## 目标

1. **定义清晰的层间接口**：每个层提供明确的API契约
2. **移除层间硬编码依赖**：使用依赖注入和配置驱动
3. **建立依赖注入机制**：支持运行时组件替换
4. **实现配置驱动架构**：所有参数可外部配置

## 时间计划

**总时长**: 2周（10个工作日）
**开始日期**: 2026-01-13
**结束日期**: 2026-01-24

## 详细任务分解

### 任务1.1：接口定义（3天）

#### 子任务1.1.1：运行时核心层接口
- 定义 `RuntimeCore` 抽象基类
- 定义 `SessionManager`、`TurnScheduler`、`PersistenceEngine` 接口
- 定义数据模型：`Session`、`Turn`、`SessionConfig`
- 输出：`src/loom/core/interfaces.py`

#### 子任务1.1.2：规则层接口
- 定义 `RuleLayer` 抽象基类
- 定义 `Canon`、`RuleSection`、`ValidationResult` 数据模型
- 定义规则加载、验证、热加载接口
- 输出：`src/loom/rules/interfaces.py`

#### 子任务1.1.3：解释层接口
- 定义 `InterpretationLayer` 抽象基类
- 定义 `LLMProvider`、`RuleInterpreter`、`ReasoningPipeline` 接口
- 定义 `InterpretationResult`、`ConsistencyReport` 数据模型
- 输出：`src/loom/interpretation/interfaces.py`

#### 子任务1.1.4：世界记忆层接口
- 定义 `WorldMemory` 抽象基类
- 定义 `MemoryEntity`、`MemoryRelation`、`MemoryQuery` 数据模型
- 定义记忆存储、检索、摘要接口
- 输出：`src/loom/memory/interfaces.py`

#### 子任务1.1.5：玩家干预层接口
- 定义 `PlayerIntervention` 抽象基类
- 定义 `Intervention`、`Intent`、`PermissionResult` 数据模型
- 定义干预解析、验证、处理接口
- 输出：`src/loom/intervention/interfaces.py`

### 任务1.2：依赖注入框架（2天）

#### 子任务1.2.1：容器定义
- 创建 `DependencyContainer` 类
- 支持组件注册、解析、生命周期管理
- 支持单例、工厂、作用域生命周期
- 输出：`src/loom/di/container.py`

#### 子任务1.2.2：配置集成
- 集成 Pydantic Settings 进行配置管理
- 支持环境变量、配置文件、命令行参数
- 定义配置模型：`AppConfig`、`LayerConfig`
- 输出：`src/loom/config/models.py`

#### 子任务1.2.3：组件工厂
- 创建各层组件工厂
- 支持基于配置动态创建组件
- 支持插件系统集成点
- 输出：`src/loom/di/factories.py`

### 任务1.3：接口适配器（3天）

#### 子任务1.3.1：现有代码适配
- 创建适配器类，实现新接口，包装现有实现
- 确保向后兼容性
- 逐步迁移，支持新旧接口并行
- 输出：各层的 `adapters/` 目录

#### 子任务1.3.2：配置桥接
- 创建配置适配器，将现有配置转换为新配置模型
- 支持配置迁移工具
- 输出：`src/loom/config/adapters.py`

#### 子任务1.3.3：测试适配器
- 更新测试代码使用新接口
- 创建测试适配器确保现有测试通过
- 输出：`tests/adapters/`

### 任务1.4：集成测试（2天）

#### 子任务1.4.1：接口兼容性测试
- 测试新旧接口兼容性
- 验证数据模型转换正确性
- 输出：`tests/integration/test_interface_compatibility.py`

#### 子任务1.4.2：依赖注入测试
- 测试容器功能
- 测试组件生命周期
- 测试配置驱动
- 输出：`tests/integration/test_dependency_injection.py`

#### 子任务1.4.3：端到端测试
- 测试完整会话流程
- 验证各层协作
- 性能基准测试
- 输出：`tests/e2e/test_phase1_integration.py`

## 技术规范

### 接口设计原则

#### 1. 最小接口原则
- 每个接口只暴露必要的方法
- 隐藏实现细节
- 使用属性而非方法暴露数据

#### 2. 稳定接口原则
- 接口一旦发布，保持向后兼容
- 使用版本控制管理接口变更
- 弃用而非删除旧方法

#### 3. 明确契约原则
- 接口文档完整
- 错误条件明确
- 性能预期清晰

### 数据模型规范

#### 1. 不可变数据
- 使用 `dataclass(frozen=True)` 或 `NamedTuple`
- 支持序列化/反序列化
- 包含版本信息

#### 2. 类型安全
- 完整的类型注解
- 使用 `Literal`、`TypedDict` 等高级类型
- 运行时类型验证

#### 3. 序列化友好
- 支持 JSON 序列化
- 包含 `to_dict()` 和 `from_dict()` 方法
- 支持自定义序列化器

### 配置管理规范

#### 1. 分层配置
```yaml
# 应用级配置
app:
  name: "loom"
  version: "0.2.0"
  
# 层配置
layers:
  core:
    session_timeout: 3600
    auto_save: true
    
  interpretation:
    llm_provider: "openai"
    temperature: 0.7
    
# 环境特定配置
environment: "development"
```

#### 2. 配置验证
- 使用 Pydantic 进行配置验证
- 环境变量覆盖支持
- 配置合并策略

#### 3. 热加载支持
- 配置文件变化自动重载
- 配置变更通知机制
- 运行时配置更新

## 风险与缓解

### 技术风险

#### 风险1：接口设计不合理
- **影响**: 后续重构困难，需要重新设计
- **缓解**: 
  - 设计评审会议
  - 原型验证
  - 小范围试点

#### 风险2：向后兼容性破坏
- **影响**: 现有功能无法使用
- **缓解**:
  - 接口适配器模式
  - 并行支持新旧接口
  - 详细迁移指南

#### 风险3：性能下降
- **影响**: 系统响应变慢
- **缓解**:
  - 性能基准测试
  - 性能监控
  - 优化热点路径

### 进度风险

#### 风险1：任务依赖延迟
- **影响**: 整体进度延迟
- **缓解**:
  - 明确任务依赖关系
  - 并行开发独立组件
  - 定期进度同步

#### 风险2：技术难点未预料
- **影响**: 需要额外时间解决
- **缓解**:
  - 技术预研
  - 备选方案
  - 专家咨询

### 质量风险

#### 风险1：测试覆盖不足
- **影响**: 隐藏缺陷
- **缓解**:
  - 测试覆盖率要求
  - 代码审查重点
  - 自动化测试

#### 风险2：文档不完整
- **影响**: 后续开发困难
- **缓解**:
  - 文档作为交付物
  - 文档审查
  - 示例代码

## 交付物

### 代码交付物
1. 接口定义文件（5个）
2. 依赖注入框架（3个）
3. 接口适配器（各层）
4. 集成测试（3套）
5. 配置管理（2个）

### 文档交付物
1. 接口文档（API Reference）
2. 配置指南（Configuration Guide）
3. 迁移指南（Migration Guide）
4. 架构决策记录（ADR）

### 质量交付物
1. 测试覆盖率报告（≥ 85%）
2. 性能基准报告
3. 代码审查记录
4. 缺陷跟踪报告

## 成功标准

### 技术标准
1. ✅ 所有接口明确定义并文档化
2. ✅ 无层间硬编码依赖
3. ✅ 依赖注入正常工作
4. ✅ 配置驱动架构实现
5. ✅ 向后兼容性保持

### 质量标准
1. ✅ 测试覆盖率 ≥ 85%
2. ✅ 代码审查通过率 100%
3. ✅ 性能基准达标
4. ✅ 无严重缺陷

### 进度标准
1. ✅ 按计划完成所有任务
2. ✅ 交付物完整
3. ✅ 团队知识转移完成

## 团队与职责

### 核心团队
- **架构负责人**: 接口设计、技术决策
- **开发工程师 (2人)**: 接口实现、适配器开发
- **测试工程师**: 集成测试、质量保证
- **文档工程师**: 文档编写、示例创建

### 协作机制
- **每日站会**: 进度同步、问题解决
- **每周评审**: 设计评审、代码审查
- **里程碑会议**: 阶段总结、计划调整

## 后续步骤

### 阶段1完成后
1. 创建 `refactor/phase2-core` 分支
2. 开始阶段2：核心层重构
3. 基于阶段1接口进行实现

### 知识转移
1. 接口使用培训
2. 配置管理培训
3. 依赖注入最佳实践分享

### 监控与改进
1. 收集阶段1反馈
2. 更新重构计划
3. 优化工作流程

## 附录

### A. 接口定义示例

```python
"""
运行时核心层接口定义
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SessionConfig:
    """会话配置"""
    name: str
    canon_path: str
    llm_provider: str = "openai"
    max_turns: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "canon_path": self.canon_path,
            "llm_provider": self.llm_provider,
            "max_turns": self.max_turns,
            "metadata": self.metadata or {}
        }


class RuntimeCore(ABC):
    """运行时核心层接口"""
    
    @abstractmethod
    async def create_session(self, config: SessionConfig) -> str:
        """创建新会话
        
        Args:
            config: 会话配置
            
        Returns:
            会话ID
            
        Raises:
            ConfigurationError: 配置无效时
        """
        pass
    
    @abstractmethod
    async def schedule_turn(self, session_id: str, player_input: str) -> Dict[str, Any]:
        """调度回合
        
        Args:
            session_id: 会话ID
            player_input: 玩家输入
            
        Returns:
            回合结果
            
        Raises:
            SessionNotFoundError: 会话不存在时
            TurnProcessingError: 回合处理失败时
        """
        pass
```

### B. 配置示例

```yaml
# config/development.yaml
app:
  name: "loom"
  version: "0.2.0"
  environment: "development"
  
logging:
  level: "DEBUG"
  format: "json"
  
layers:
  core:
    session_timeout: 3600
    auto_save: true
    auto_save_interval: 5
    
  interpretation:
    llm_provider: "openai"
    fallback_providers: ["anthropic", "local"]
    temperature: 0.7
    max_tokens: 2000
    
  memory:
    backend: "sqlite"
    vector_backend: "chroma"
    cache_size: 1000
    
di:
  container: "simple"
  lifecycle: "singleton"
  validation: true
```

### C. 测试示例

```python
"""
接口兼容性测试
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.loom.core.interfaces import RuntimeCore, SessionConfig
from src.loom.core.adapters import LegacyRuntimeCoreAdapter


class TestInterfaceCompatibility:
    """接口兼容性测试"""
    
    @pytest.fixture
    def legacy_core(self):
        """传统核心实现"""
        core = Mock()
        core.create_session = AsyncMock(return_value="session-123")
        return core
    
    @pytest.fixture
    def adapter(self, legacy_core):
        """适配器实例"""
        return LegacyRuntimeCoreAdapter(legacy_core)
    
    @pytest.mark.asyncio
    async def test_create_session_compatibility(self, adapter):
        """测试会话创建兼容性"""
        config = SessionConfig(
            name="Test Session",
            canon_path="./canon"
        )
        
        session_id = await adapter.create_session(config)
        
        assert session_id == "session-123"
```

---

**计划制定**: 2026-01-12  
**版本**: 1.0  
**状态**: 待执行  
**负责人**: [架构负责人姓名]