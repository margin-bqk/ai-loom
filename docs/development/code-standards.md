# LOOM 重构代码质量标准和审查流程

## 概述

本文档定义了 LOOM 项目重构期间的代码质量标准和审查流程，确保重构代码符合项目架构原则，保持高质量和可维护性。

## 代码质量标准

### 1. 架构符合性标准

#### 1.1 五层架构分离
- ✅ 运行时核心层保持叙事失明
- ✅ 规则层完全独立于框架代码
- ✅ 解释层不存储叙事状态
- ✅ 记忆层不解析规则内容
- ✅ 干预层不修改核心层行为

#### 1.2 接口设计标准
- 所有层间通信通过明确定义的接口
- 接口使用抽象基类或协议定义
- 依赖注入而非硬编码依赖
- 配置驱动而非硬编码参数

#### 1.3 数据流标准
- 单向数据流：玩家输入 → 规则解释 → 记忆更新 → 输出响应
- 无循环依赖：各层之间不允许循环引用
- 事件驱动：使用异步事件而非同步调用

### 2. 代码风格标准

#### 2.1 格式化标准
- **Black**: 行长度 88 字符，遵循 Black 默认配置
- **isort**: 导入排序，分组顺序：标准库 → 第三方库 → 本地模块
- **flake8**: 遵循 PEP 8，启用 docstring 检查

#### 2.2 命名约定
- **类名**: `PascalCase` (如 `SessionManager`)
- **函数/方法名**: `snake_case` (如 `create_session`)
- **变量名**: `snake_case` (如 `session_id`)
- **常量**: `UPPER_SNAKE_CASE` (如 `MAX_RETRIES`)
- **私有成员**: `_leading_underscore` (如 `_internal_state`)

#### 2.3 文档标准
- **模块文档**: 每个模块顶部有 docstring，说明职责和架构位置
- **类文档**: 说明类的职责、架构层归属、主要方法
- **函数文档**: 使用 Google 风格，包含参数、返回值和异常说明
- **类型注解**: 所有公共 API 必须有完整的类型注解

### 3. 测试标准

#### 3.1 测试覆盖率要求
- **单元测试**: 核心逻辑 ≥ 90%
- **集成测试**: 层间接口 ≥ 80%
- **端到端测试**: 关键用户场景 100% 覆盖

#### 3.2 测试分类
- **单元测试**: 测试单个函数或类的行为
- **集成测试**: 测试层间接口和数据流
- **端到端测试**: 测试完整会话流程
- **性能测试**: 测试关键路径性能指标

#### 3.3 测试质量
- 测试独立，不依赖外部服务
- 使用 fixture 减少重复代码
- 测试名称清晰描述测试场景
- 包含边界条件和错误场景

### 4. 安全标准

#### 4.1 输入验证
- 所有用户输入必须验证和清理
- 使用 Pydantic 模型进行数据验证
- 防止 SQL 注入和 XSS 攻击

#### 4.2 敏感数据处理
- API 密钥等敏感信息使用环境变量
- 日志中不记录敏感数据
- 配置文件中的敏感数据加密存储

#### 4.3 权限控制
- 会话级别的访问控制
- 规则层定义的权限边界
- 审计日志记录所有关键操作

### 5. 性能标准

#### 5.1 响应时间
- 单回合处理时间 < 5 秒（LLM 调用除外）
- 记忆检索时间 < 100 毫秒
- 会话加载时间 < 1 秒

#### 5.2 资源使用
- 内存使用：单会话 < 50MB
- 数据库增长：< 1MB/1000 回合
- 并发支持：≥ 100 个活跃会话

#### 5.3 可扩展性
- 无状态设计支持水平扩展
- 数据库连接池管理
- 缓存策略减少重复计算

## 代码审查流程

### 1. 审查前准备

#### 1.1 提交前检查
```bash
# 运行本地检查
pre-commit run --all-files

# 运行测试
pytest --cov=src/loom --cov-report=term

# 类型检查
mypy src/loom
```

#### 1.2 提交规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:
- `feat`: 新功能（重构期间使用 `refactor`）
- `refactor`: 重构（不改变外部行为）
- `fix`: 缺陷修复
- `perf`: 性能优化
- `test`: 测试相关
- `docs`: 文档更新
- `chore`: 构建过程或辅助工具变更

**范围**:
- `core`: 运行时核心层
- `rules`: 规则层
- `interpretation`: 解释层
- `memory`: 记忆层
- `intervention`: 干预层
- `api`: API 接口
- `cli`: 命令行界面
- `config`: 配置管理

### 2. 审查流程

#### 2.1 审查人员
- **主要审查者**: 架构负责人或领域专家
- **次要审查者**: 至少一名其他开发人员
- **质量保证**: QA 工程师（可选）

#### 2.2 审查重点
1. **架构符合性**: 代码是否符合五层架构原则
2. **接口设计**: 接口是否清晰、稳定、可扩展
3. **测试覆盖**: 是否有足够的测试覆盖
4. **代码质量**: 是否符合代码风格标准
5. **性能影响**: 是否影响系统性能
6. **向后兼容**: 是否保持向后兼容性

#### 2.3 审查清单
- [ ] 代码通过所有预提交检查
- [ ] 测试覆盖率满足要求
- [ ] 类型注解完整
- [ ] 文档更新及时
- [ ] 无硬编码依赖
- [ ] 配置可外部化
- [ ] 错误处理完善
- [ ] 日志记录适当
- [ ] 性能影响评估
- [ ] 安全考虑周全

### 3. 审查工具

#### 3.1 自动化检查
- **GitHub Actions**: CI/CD 流水线
- **Codecov**: 测试覆盖率报告
- **SonarQube**: 代码质量分析（可选）
- **Dependabot**: 依赖更新检查

#### 3.2 代码审查工具
- **GitHub Pull Requests**: 主要审查平台
- **Reviewable**: 代码审查增强（可选）
- **Linear**: 任务跟踪和关联

### 4. 审查决策

#### 4.1 审查结果
- **批准**: 代码符合所有标准，可以合并
- **需要修改**: 代码需要修改后重新审查
- **拒绝**: 代码不符合架构原则，需要重写

#### 4.2 修改要求
1. **轻微修改**: 代码风格、文档等小问题
   - 可以在线修改后直接合并
   - 不需要重新审查
2. **中等修改**: 接口设计、测试覆盖等问题
   - 需要修改后重新提交审查
   - 审查者验证修改
3. **重大修改**: 架构违反、性能问题等
   - 需要重新设计和实现
   - 新的 Pull Request

### 5. 审查记录

#### 5.1 审查文档
- 每个 Pull Request 必须有审查记录
- 记录审查发现的问题和解决方案
- 记录架构决策和理由

#### 5.2 知识共享
- 定期分享审查经验和最佳实践
- 维护常见问题清单
- 更新代码审查指南

## 重构特定标准

### 1. 阶段0：准备阶段
- **重点**: 环境配置、分支策略、测试验证
- **标准**: 确保现有功能正常工作
- **审查**: 架构负责人审查准备计划

### 2. 阶段1：定位重构
- **重点**: 层间接口定义、依赖注入
- **标准**: 严格解耦，无硬编码依赖
- **审查**: 接口设计审查，向后兼容性验证

### 3. 阶段2-5：各层重构
- **重点**: 各层内部实现，保持接口稳定
- **标准**: 符合各层职责，性能达标
- **审查**: 层内架构审查，测试覆盖验证

### 4. 阶段6：集成测试
- **重点**: 端到端测试，性能基准
- **标准**: 所有测试通过，性能指标达标
- **审查**: 集成测试审查，性能报告分析

## 质量指标监控

### 1. 代码质量指标
- **测试覆盖率**: ≥ 80%
- **代码重复率**: ≤ 5%
- **圈复杂度**: ≤ 10
- **技术债务比率**: ≤ 5%

### 2. 性能指标
- **响应时间**: P95 < 5 秒
- **错误率**: < 1%
- **资源使用**: 内存 < 1GB，CPU < 80%
- **并发能力**: ≥ 100 会话

### 3. 架构指标
- **层间耦合度**: 依赖注入比例 ≥ 90%
- **接口稳定性**: 接口变更频率 ≤ 1次/月
- **配置外部化**: 硬编码参数 ≤ 5%

## 持续改进

### 1. 定期评估
- 每周代码审查会议
- 每月架构符合性检查
- 每季度性能基准测试

### 2. 反馈机制
- 开发者反馈收集
- 用户问题分析
- 性能监控告警

### 3. 标准更新
- 根据项目进展更新标准
- 吸收行业最佳实践
- 适应新技术和工具

## 附录

### A. 常用命令

```bash
# 代码格式化
black src/ tests/

# 导入排序
isort src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/loom

# 安全扫描
bandit -r src/

# 测试运行
pytest --cov=src/loom --cov-report=html

# 复杂度分析
radon cc src/ -a

# 重复代码检测
flake8 --select=R src/
```

### B. 模板文件

#### 类模板
```python
"""
[模块职责说明]

架构层: [core/rules/interpretation/memory/intervention]
依赖: [列出主要依赖]
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ExampleConfig:
    """配置类示例"""

    param1: str
    param2: int = 10
    param3: Optional[bool] = None


class ExampleClass:
    """类职责说明"""

    def __init__(self, config: ExampleConfig):
        """初始化

        Args:
            config: 配置参数
        """
        self.config = config
        self._internal_state: Dict[str, Any] = {}

    async def example_method(self, input_data: str) -> Dict[str, Any]:
        """方法职责说明

        Args:
            input_data: 输入数据说明

        Returns:
            返回数据说明

        Raises:
            ValueError: 当输入无效时
        """
        if not input_data:
            raise ValueError("输入数据不能为空")

        # 方法实现
        result = {"processed": input_data}

        logger.info(f"处理完成: {input_data}")
        return result
```

#### 测试模板
```python
"""
测试模块示例
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.loom.core.example import ExampleClass, ExampleConfig


class TestExampleClass:
    """ExampleClass 测试"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return ExampleConfig(param1="test", param2=20)

    @pytest.fixture
    def example_instance(self, config):
        """测试实例"""
        return ExampleClass(config)

    @pytest.mark.asyncio
    async def test_example_method_success(self, example_instance):
        """测试成功场景"""
        result = await example_instance.example_method("test input")

        assert result["processed"] == "test input"

    @pytest.mark.asyncio
    async def test_example_method_empty_input(self, example_instance):
        """测试空输入场景"""
        with pytest.raises(ValueError, match="输入数据不能为空"):
            await example_instance.example_method("")
```

### C. 联系人
- **架构负责人**: [负责人姓名]
- **代码审查协调**: [协调人姓名]
- **质量保证**: [QA负责人]

---

**最后更新**: 2026-01-12
**版本**: 1.0
**状态**: 实施中
