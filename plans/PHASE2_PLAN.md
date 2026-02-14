# 阶段2：叙事解释器增强 - 高级推理和记忆

## 概述

阶段2的目标是增强解释层和规则层，实现高级推理能力，并建立世界记忆系统。基于阶段1的定位重构，本阶段将实现完整的叙事解释器工作流，支持长期记忆、上下文感知和智能推理。

## 目标

1. **增强解释层推理能力**：实现多步骤推理、一致性检查、冲突解决
2. **建立世界记忆系统**：实现结构化记忆存储、检索和摘要生成
3. **优化规则解释**：改进Markdown规则解析，支持复杂约束和动态规则
4. **集成BYOK多Provider支持**：完善LLM Provider管理，支持成本优化和故障转移
5. **实现性能基准和监控**：建立性能监控体系，确保系统可扩展性

## 时间计划

**总时长**: 3周（15个工作日）
**开始日期**: 2026-01-15
**结束日期**: 2026-02-02

## 详细任务分解

### 任务2.1：高级推理引擎（4天）

#### 子任务2.1.1：多步骤推理管道
- 实现`ReasoningPipeline`类，支持规则解释、上下文构建、LLM生成、一致性检查
- 设计推理步骤跟踪和可解释性报告
- 输出：`src/loom/interpretation/reasoning_pipeline.py`

#### 子任务2.1.2：一致性检查器
- 实现`ConsistencyChecker`，验证叙事输出与规则、记忆的一致性
- 支持冲突检测和自动解决建议
- 输出：`src/loom/interpretation/consistency_checker.py`

#### 子任务2.1.3：上下文构建器
- 实现`ContextBuilder`，动态组装规则、记忆、玩家输入到LLM提示
- 支持上下文窗口优化和令牌管理
- 输出：`src/loom/interpretation/context_builder.py`

### 任务2.2：世界记忆系统（5天）

#### 子任务2.2.1：结构化记忆存储
- 实现`StructuredStore`，支持实体、事实、关系、剧情线存储
- 基于SQLite的关系型存储，支持复杂查询
- 输出：`src/loom/memory/structured_store.py`

#### 子任务2.2.2：向量记忆存储
- 实现`VectorStore`，支持语义相似性检索
- 集成ChromaDB或Qdrant，支持向量嵌入
- 输出：`src/loom/memory/vector_store.py`

#### 子任务2.2.3：记忆摘要生成
- 实现`MemorySummarizer`，使用LLM生成记忆摘要
- 支持摘要缓存和增量更新
- 输出：`src/loom/memory/summarizer.py`

#### 子任务2.2.4：记忆查询接口
- 实现`WorldMemory`统一接口，整合结构化存储和向量存储
- 支持复杂查询：时间范围、实体关系、语义相似性
- 输出：`src/loom/memory/world_memory.py`

### 任务2.3：规则层增强（3天）

#### 子任务2.3.1：高级Markdown解析
- 增强`MarkdownCanon`，支持嵌套章节、交叉引用、动态包含
- 实现规则依赖分析和版本控制
- 输出：`src/loom/rules/markdown_canon.py`

#### 子任务2.3.2：规则验证器
- 实现`RuleValidator`，静态分析规则一致性、完整性
- 支持规则冲突检测和修复建议
- 输出：`src/loom/rules/rule_validator.py`

#### 子任务2.3.3：规则热加载
- 实现`RuleHotLoader`，支持运行时规则更新
- 支持规则变更通知和会话级规则隔离
- 输出：`src/loom/rules/rule_hot_loader.py`

### 任务2.4：LLM Provider增强（2天）

#### 子任务2.4.1：多Provider故障转移
- 增强`ProviderManager`，支持智能故障转移和负载均衡
- 实现Provider健康检查和自动切换
- 输出：`src/loom/interpretation/provider_manager.py`

#### 子任务2.4.2：成本优化
- 实现`CostOptimizer`，跟踪LLM使用成本，优化令牌使用
- 支持预算限制和告警
- 输出：`src/loom/interpretation/cost_optimizer.py`

#### 子任务2.4.3：本地模型支持
- 增强`LocalProvider`，支持Ollama、LM Studio等本地模型
- 实现模型下载和版本管理
- 输出：`src/loom/interpretation/local_provider.py`

### 任务2.5：性能基准和监控（1天）

#### 子任务2.5.1：性能基准测试
- 创建性能测试套件，测量回合延迟、内存使用、LLM调用成本
- 建立性能基线，用于后续优化
- 输出：`tests/performance/benchmarks.py`

#### 子任务2.5.2：监控集成
- 集成Prometheus指标导出，支持Grafana仪表板
- 实现关键指标：活跃会话数、平均响应时间、错误率
- 输出：`src/loom/monitoring/`

## 技术规范

### 推理引擎设计

#### 1. 多步骤推理流程
```
1. 规则解释：解析当前规则约束
2. 记忆检索：获取相关记忆实体
3. 上下文构建：组装提示
4. LLM生成：调用LLM生成叙事
5. 一致性检查：验证输出一致性
6. 记忆更新：存储新事实
```

#### 2. 可解释性要求
- 每个推理步骤生成详细日志
- 支持推理跟踪和审计
- 提供可视化推理路径

### 记忆系统设计

#### 1. 记忆数据结构
```python
class MemoryEntity:
    id: str
    type: MemoryEntityType  # CHARACTER, LOCATION, EVENT, ITEM
    content: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

class MemoryRelation:
    source_id: str
    target_id: str
    relation_type: str  # "located_in", "knows", "owns"
    strength: float
    metadata: Dict[str, Any]
```

#### 2. 记忆检索策略
- 基于时间的检索（最近使用）
- 基于相关性的检索（向量相似性）
- 基于重要性的检索（手动标记）

### 规则增强要求

#### 1. 高级Markdown语法
```
# 世界观
## 角色
### 主角 [importance: high]
- 姓名: 艾莉丝
- 职业: 冒险家
- 性格: 勇敢、好奇

## 规则
### 约束 [priority: 1]
- 玩家不能杀死重要NPC
- 魔法需要消耗魔力
```

#### 2. 规则验证规则
- 无冲突约束
- 必填章节存在
- 引用实体存在

## 风险与缓解

### 技术风险

#### 风险1：记忆系统性能问题
- **影响**：记忆检索延迟影响回合响应时间
- **缓解**：
  - 实现记忆缓存层
  - 使用索引优化查询
  - 定期清理无用记忆

#### 风险2：LLM推理不一致性
- **影响**：相同输入产生不同输出，破坏叙事连贯性
- **缓解**：
  - 实现输出缓存
  - 使用确定性参数（temperature=0）
  - 引入后处理一致性检查

#### 风险3：规则复杂性导致解释困难
- **影响**：LLM无法正确解释复杂规则
- **缓解**：
  - 提供规则简化工具
  - 实现规则分块解释
  - 支持人工规则注解

### 进度风险

#### 风险1：记忆系统实现复杂度高
- **影响**：任务延期
- **缓解**：
  - 分阶段实现：先结构化存储，后向量存储
  - 使用现有库（SQLAlchemy、ChromaDB）
  - 简化初始版本，后续增强

#### 风险2：LLM Provider集成问题
- **影响**：多Provider支持不完整
- **缓解**：
  - 优先支持主流Provider（OpenAI、Anthropic）
  - 使用抽象层隔离Provider差异
  - 提供模拟Provider用于测试

### 质量风险

#### 风险1：记忆一致性难以保证
- **影响**：记忆冲突导致叙事矛盾
- **缓解**：
  - 实现记忆一致性检查
  - 支持记忆版本和回滚
  - 提供冲突解决界面

#### 风险2：性能基准不准确
- **影响**：无法有效评估系统性能
- **缓解**：
  - 使用标准化测试数据集
  - 多次运行取平均值
  - 监控生产环境性能

## 交付物

### 代码交付物
1. 高级推理引擎（3个模块）
2. 世界记忆系统（4个模块）
3. 规则层增强（3个模块）
4. LLM Provider增强（3个模块）
5. 性能基准工具（1套）

### 文档交付物
1. 推理引擎使用指南
2. 记忆系统API文档
3. 规则编写高级指南
4. LLM Provider配置指南
5. 性能优化建议

### 质量交付物
1. 集成测试套件（覆盖率≥85%）
2. 性能基准报告
3. 内存使用分析报告
4. 安全审计报告

## 成功标准

### 技术标准
1. ✅ 推理引擎支持多步骤推理和一致性检查
2. ✅ 记忆系统支持结构化存储和向量检索
3. ✅ 规则层支持高级Markdown语法和热加载
4. ✅ LLM Provider支持故障转移和成本优化
5. ✅ 性能基准显示回合延迟<5秒（使用GPT-3.5）

### 质量标准
1. ✅ 测试覆盖率≥85%
2. ✅ 无严重内存泄漏
3. ✅ 关键路径错误率<1%
4. ✅ 文档完整且准确

### 进度标准
1. ✅ 按计划完成所有任务
2. ✅ 交付物完整可用
3. ✅ 团队掌握新技术组件

## 团队与职责

### 核心团队
- **架构负责人**：系统设计、技术决策
- **后端开发工程师（2人）**：推理引擎、记忆系统实现
- **ML工程师**：LLM集成、向量存储优化
- **测试工程师**：集成测试、性能测试
- **文档工程师**：API文档、用户指南

### 协作机制
- **每日站会**：进度同步、障碍解决
- **每周设计评审**：架构决策、代码审查
- **双周演示**：功能演示、用户反馈收集

## 后续步骤

### 阶段2完成后
1. 创建`feature/phase3-memory-enhancement`分支
2. 开始阶段3：记忆系统优化和玩家干预集成
3. 基于阶段2成果进行用户测试

### 知识转移
1. 推理引擎使用培训
2. 记忆系统API培训
3. 规则编写高级培训

### 监控与改进
1. 收集用户反馈
2. 分析性能数据
3. 优化热点路径

## 附录

### A. 推理引擎接口示例

```python
class ReasoningPipeline:
    """推理管道"""

    async def process(self, context: ReasoningContext) -> ReasoningResult:
        """处理推理请求"""
        # 1. 规则解释
        constraints = await self.rule_interpreter.interpret(context.rules)

        # 2. 记忆检索
        memories = await self.world_memory.retrieve_relevant(
            context.session_id,
            context.player_input
        )

        # 3. 上下文构建
        prompt = await self.context_builder.build(
            constraints=constraints,
            memories=memories,
            player_input=context.player_input
        )

        # 4. LLM生成
        response = await self.llm_provider.generate(prompt)

        # 5. 一致性检查
        consistency_report = await self.consistency_checker.check(
            response=response,
            constraints=constraints,
            memories=memories
        )

        # 6. 记忆更新
        if consistency_report.passed:
            await self.world_memory.store_fact(
                session_id=context.session_id,
                fact_type="narrative_event",
                content={"text": response.content}
            )

        return ReasoningResult(
            narrative_response=response.content,
            reasoning_steps=self.get_steps(),
            constraints_applied=constraints,
            confidence=consistency_report.confidence,
            metadata={
                "model": response.model,
                "usage": response.usage,
                "consistency_passed": consistency_report.passed
            }
        )
```

### B. 记忆查询示例

```python
# 查询特定类型的所有实体
entities = await world_memory.retrieve_entities_by_type(
    session_id="test-session",
    entity_type=MemoryEntityType.CHARACTER
)

# 基于语义相似性检索
similar_entities = await world_memory.semantic_search(
    session_id="test-session",
    query="勇敢的冒险家",
    limit=5
)

# 查询实体关系
relations = await world_memory.get_entity_relations(
    entity_id="char-123",
    relation_type="knows"
)
```

### C. 性能基准配置

```yaml
benchmarks:
  turn_processing:
    iterations: 100
    warmup_iterations: 10
    metrics:
      - mean_latency_ms
      - p95_latency_ms
      - memory_usage_mb
      - llm_tokens_per_turn

  memory_operations:
    operations:
      - store_entity
      - retrieve_entity
      - semantic_search
    dataset_size: 1000
```

---

**计划制定**: 2026-01-14
**版本**: 1.0
**状态**: 待执行
**负责人**: 架构负责人
