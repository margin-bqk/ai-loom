"""
增强推理引擎单元测试

测试EnhancedReasoningPipeline、EnhancedContextBuilder、
EnhancedConsistencyChecker和ReasoningTracker。
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from src.loom.interpretation import (
    ConsistencyCategory,
    ContextOptimizationStrategy,
    DecisionImportance,
    EnhancedConsistencyChecker,
    EnhancedContextBuilder,
    EnhancedReasoningPipeline,
    ReasoningContext,
    ReasoningStepType,
    ReasoningTracker,
)


class TestEnhancedReasoningPipeline:
    """测试增强推理管道"""

    @pytest.fixture
    def mock_llm_provider(self):
        """模拟LLM提供者"""
        provider = Mock()
        provider.name = "test_provider"
        provider.generate = AsyncMock(
            return_value=Mock(
                content="这是一个测试叙事响应。",
                model="test-model",
                usage={"total_tokens": 100},
                metadata={},
            )
        )
        return provider

    @pytest.fixture
    def mock_world_memory(self):
        """模拟世界记忆"""
        memory = Mock()
        memory.retrieve_facts = AsyncMock(return_value=[])
        memory.retrieve_characters = AsyncMock(return_value=[])
        memory.retrieve_events = AsyncMock(return_value=[])
        memory.store_fact = AsyncMock(return_value="fact_123")
        memory.store_event = AsyncMock(return_value="event_456")
        return memory

    @pytest.fixture
    def reasoning_context(self):
        """创建推理上下文"""
        return ReasoningContext(
            session_id="test_session_123",
            turn_number=1,
            player_input="玩家想要探索城堡。",
            rules_text="这是一个奇幻世界。魔法存在但有限制。",
            memories=[
                {"type": "fact", "content": {"summary": "城堡位于山巅"}},
                {
                    "type": "character",
                    "content": {"name": "守卫", "traits": ["忠诚", "警惕"]},
                },
            ],
            interventions=[],
            metadata={"test": True},
        )

    @pytest.fixture
    def pipeline(self, mock_llm_provider, mock_world_memory):
        """创建增强推理管道"""
        return EnhancedReasoningPipeline(
            llm_provider=mock_llm_provider,
            world_memory=mock_world_memory,
            config={"max_memories": 5},
        )

    @pytest.mark.asyncio
    async def test_initialization(self, pipeline):
        """测试初始化"""
        assert pipeline.config == {"max_memories": 5}
        assert pipeline.rule_interpreter is not None
        assert pipeline.consistency_checker is not None

    @pytest.mark.asyncio
    async def test_process_basic(self, pipeline, reasoning_context):
        """测试基本处理流程"""
        result = await pipeline.process(reasoning_context)

        assert result is not None
        assert hasattr(result, "narrative_response")
        assert hasattr(result, "confidence")
        assert hasattr(result, "reasoning_steps_detailed")
        assert hasattr(result, "consistency_report")
        assert hasattr(result, "explainability_report")

        # 验证响应内容
        assert isinstance(result.narrative_response, str)
        assert len(result.narrative_response) > 0

        # 验证置信度在合理范围内
        assert 0.0 <= result.confidence <= 1.0

        # 验证步骤记录
        assert isinstance(result.reasoning_steps_detailed, list)
        assert len(result.reasoning_steps_detailed) > 0

    @pytest.mark.asyncio
    async def test_process_without_memory(self, mock_llm_provider):
        """测试无记忆系统的处理"""
        pipeline = EnhancedReasoningPipeline(
            llm_provider=mock_llm_provider, world_memory=None
        )

        context = ReasoningContext(
            session_id="test_session",
            turn_number=1,
            player_input="测试输入",
            rules_text="测试规则",
            memories=[],
            interventions=[],
        )

        result = await pipeline.process(context)
        assert result is not None
        assert result.narrative_response is not None

    @pytest.mark.asyncio
    async def test_batch_process(self, pipeline):
        """测试批量处理"""
        contexts = [
            ReasoningContext(
                session_id=f"session_{i}",
                turn_number=i,
                player_input=f"输入{i}",
                rules_text="规则文本",
                memories=[],
                interventions=[],
            )
            for i in range(3)
        ]

        results = await pipeline.batch_process(contexts)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result is not None
            assert result.narrative_response is not None

    @pytest.mark.asyncio
    async def test_process_with_adaptive_strategy(self, pipeline, reasoning_context):
        """测试自适应策略处理"""
        result = await pipeline.process_with_adaptive_strategy(
            reasoning_context, max_iterations=2, quality_threshold=0.7
        )

        assert result is not None
        assert result.confidence >= 0.0

    def test_generate_comprehensive_report(self, pipeline):
        """测试生成综合报告"""
        # 创建模拟结果
        mock_results = []
        for i in range(3):
            result = Mock()
            result.confidence = 0.7 + i * 0.1
            result.consistency_report = {"overall_score": 0.8}
            result.explainability_report = {"score": 0.75}
            result.reasoning_steps_detailed = [
                {"step": "step1", "duration": 1.0},
                {"step": "step2", "duration": 2.0},
            ]
            mock_results.append(result)

        report = pipeline.generate_comprehensive_report(mock_results)

        assert report is not None
        assert "total_processed" in report
        assert "average_confidence" in report
        assert "quality_distribution" in report
        assert report["total_processed"] == 3


class TestEnhancedContextBuilder:
    """测试增强上下文构建器"""

    @pytest.fixture
    def context_builder(self):
        """创建增强上下文构建器"""
        return EnhancedContextBuilder(
            config={"max_memories": 5, "relevance_threshold": 0.3}
        )

    @pytest.fixture
    def reasoning_context(self):
        """创建推理上下文"""
        return ReasoningContext(
            session_id="test_session",
            turn_number=1,
            player_input="玩家想要与守卫交谈。",
            rules_text="这是一个中世纪奇幻世界。魔法存在但稀有。骑士忠诚，巫师神秘。",
            memories=[
                {
                    "type": "character",
                    "content": {
                        "name": "守卫",
                        "traits": ["忠诚", "警惕"],
                        "dialogue_style": "正式",
                    },
                },
                {
                    "type": "fact",
                    "content": {"summary": "城堡最近遭受过袭击", "importance": "high"},
                },
            ],
            interventions=[
                {
                    "type": "player",
                    "content": "玩家特别询问了城堡历史",
                    "priority": "medium",
                }
            ],
        )

    @pytest.fixture
    def mock_interpretation(self):
        """模拟解释结果"""
        interpretation = Mock()
        interpretation.constraints = [
            Mock(type="prohibition", content="禁止使用黑暗魔法", importance="high"),
            Mock(type="permission", content="允许与NPC交谈", importance="medium"),
        ]
        interpretation.narrative_output = "规则解释：这是一个有魔法限制的奇幻世界。"
        return interpretation

    @pytest.mark.asyncio
    async def test_build_optimized(
        self, context_builder, reasoning_context, mock_interpretation
    ):
        """测试构建优化上下文"""
        prompt = await context_builder.build_optimized(
            reasoning_context, mock_interpretation, reasoning_context.memories
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # 验证包含关键部分
        assert "世界观规则" in prompt or "规则" in prompt
        assert "玩家输入" in prompt or "玩家" in prompt
        assert "关键约束" in prompt or "约束" in prompt

    @pytest.mark.asyncio
    async def test_build_with_strategy(
        self, context_builder, reasoning_context, mock_interpretation
    ):
        """测试使用策略构建上下文"""
        strategies = [
            ContextOptimizationStrategy.BALANCED,
            ContextOptimizationStrategy.MEMORY_FOCUSED,
            ContextOptimizationStrategy.CONSTRAINT_FOCUSED,
            ContextOptimizationStrategy.CONCISE,
            ContextOptimizationStrategy.DETAILED,
        ]

        for strategy in strategies:
            prompt = await context_builder.build_with_strategy(
                reasoning_context,
                mock_interpretation,
                reasoning_context.memories,
                strategy,
            )

            assert isinstance(prompt, str)
            assert len(prompt) > 0

    def test_analyze_prompt_quality(self, context_builder):
        """测试分析提示质量"""
        test_prompt = """# 世界观规则
这是一个奇幻世界。

# 关键约束
禁止使用黑暗魔法。

# 相关记忆
城堡位于山巅。

# 玩家输入
玩家想要探索城堡。

# 生成要求
请生成叙事响应。"""

        analysis = context_builder.analyze_prompt_quality(test_prompt)

        assert "statistics" in analysis
        assert "content_analysis" in analysis
        assert "quality_score" in analysis
        assert "suggestions" in analysis

        stats = analysis["statistics"]
        assert "total_length" in stats
        assert stats["total_length"] == len(test_prompt)

    @pytest.mark.asyncio
    async def test_batch_build(self, context_builder):
        """测试批量构建"""
        contexts = [
            ReasoningContext(
                session_id=f"session_{i}",
                turn_number=i,
                player_input=f"输入{i}",
                rules_text="规则文本",
                memories=[],
                interventions=[],
            )
            for i in range(3)
        ]

        interpretations = [Mock(constraints=[]) for _ in range(3)]
        memories_list = [[] for _ in range(3)]

        prompts = await context_builder.batch_build(
            contexts, interpretations, memories_list
        )

        assert len(prompts) == 3
        for prompt in prompts:
            assert isinstance(prompt, str)
            assert len(prompt) > 0


class TestEnhancedConsistencyChecker:
    """测试增强一致性检查器"""

    @pytest.fixture
    def consistency_checker(self):
        """创建增强一致性检查器"""
        return EnhancedConsistencyChecker(llm_provider=None)

    @pytest.fixture
    def reasoning_context(self):
        """创建推理上下文"""
        return ReasoningContext(
            session_id="test_session",
            turn_number=1,
            player_input="玩家攻击了怪物。",
            rules_text="这是一个奇幻世界。怪物害怕银制武器。",
            memories=[
                {
                    "type": "fact",
                    "content": {"description": "玩家有一把银剑", "certainty": "high"},
                },
                {
                    "type": "character",
                    "content": {
                        "name": "怪物",
                        "traits": ["凶猛", "害怕银"],
                        "health": "wounded",
                    },
                },
            ],
            interventions=[],
        )

    @pytest.fixture
    def mock_interpretation(self):
        """模拟解释结果"""
        interpretation = Mock()

        # 创建模拟约束
        constraint1 = Mock()
        constraint1.type = "prohibition"
        constraint1.content = "禁止怪物突然恢复健康"

        constraint2 = Mock()
        constraint2.type = "causality"
        constraint2.content = "银制武器对怪物有效"

        interpretation.constraints = [constraint1, constraint2]
        return interpretation

    @pytest.fixture
    def test_response(self):
        """测试响应"""
        return "玩家使用银剑攻击了怪物。怪物受伤后退缩，显示出对银的恐惧。"

    @pytest.mark.asyncio
    async def test_deep_check(
        self, consistency_checker, reasoning_context, mock_interpretation, test_response
    ):
        """测试深度一致性检查"""
        report = await consistency_checker.deep_check(
            test_response,
            reasoning_context,
            mock_interpretation,
            reasoning_context.memories,
        )

        assert report is not None
        assert hasattr(report, "passed")
        assert hasattr(report, "overall_score")
        assert hasattr(report, "category_scores")
        assert hasattr(report, "issues")
        assert hasattr(report, "suggestions")

        # 验证分数在合理范围内
        assert 0.0 <= report.overall_score <= 1.0

        # 验证分类分数
        for category, score in report.category_scores.items():
            assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_deep_check_with_llm(self):
        """测试使用LLM的深度检查"""
        # 创建模拟LLM提供者
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(
            return_value=Mock(
                content='{"issues": [], "overall_assessment": "consistent", "confidence": 0.9}'
            )
        )

        checker = EnhancedConsistencyChecker(llm_provider=mock_llm)

        context = ReasoningContext(
            session_id="test",
            turn_number=1,
            player_input="测试",
            rules_text="规则",
            memories=[],
            interventions=[],
        )

        interpretation = Mock()
        interpretation.constraints = []

        report = await checker.deep_check("测试响应", context, interpretation, [])

        assert report is not None

    @pytest.mark.asyncio
    async def test_batch_deep_check(self, consistency_checker):
        """测试批量深度检查"""
        responses = ["响应1", "响应2", "响应3"]

        contexts = [
            ReasoningContext(
                session_id=f"session_{i}",
                turn_number=i,
                player_input=f"输入{i}",
                rules_text="规则",
                memories=[],
                interventions=[],
            )
            for i in range(3)
        ]

        interpretations = [Mock(constraints=[]) for _ in range(3)]
        memories_list = [[] for _ in range(3)]

        reports = await consistency_checker.batch_deep_check(
            responses, contexts, interpretations, memories_list
        )

        assert len(reports) == 3
        for report in reports:
            assert report is not None
            assert hasattr(report, "overall_score")

    def test_generate_comparative_report(self, consistency_checker):
        """测试生成比较报告"""
        # 创建模拟报告
        mock_reports = []
        for i in range(3):
            report = Mock()
            report.passed = i != 0  # 第一个失败
            report.overall_score = 0.6 + i * 0.1
            report.category_scores = {
                ConsistencyCategory.RULE_SEMANTIC: 0.7,
                ConsistencyCategory.MEMORY_SEMANTIC: 0.8,
            }
            report.issues = [] if i != 0 else [Mock(type="test_issue")]
            mock_reports.append(report)

        comparative_report = consistency_checker.generate_comparative_report(
            mock_reports
        )

        assert comparative_report is not None
        assert "total_checked" in comparative_report
        assert "pass_rate" in comparative_report
        assert "average_overall_score" in comparative_report
        assert "recommendations" in comparative_report


class TestReasoningTracker:
    """测试推理跟踪器"""

    @pytest.fixture
    def tracker(self):
        """创建推理跟踪器"""
        return ReasoningTracker(session_id="test_session", turn_number=1)

    def test_initialization(self, tracker):
        """测试初始化"""
        assert tracker.session_id == "test_session"
        assert tracker.turn_number == 1
        assert tracker.current_trace is None
        assert tracker.traces == []
        assert "total_steps" in tracker.metrics

    def test_trace_lifecycle(self, tracker):
        """测试轨迹生命周期"""
        # 开始轨迹
        trace_id = tracker.start_trace(metadata={"test": True})
        assert trace_id is not None
        assert tracker.current_trace is not None
        assert tracker.current_trace.trace_id == trace_id

        # 添加步骤
        step_id = tracker.start_step(
            name="规则解释",
            step_type=ReasoningStepType.RULE_INTERPRETATION,
            input_data={"rules": "测试规则"},
        )
        assert step_id is not None

        # 结束步骤
        success = tracker.end_step(
            step_id=step_id, output_data={"interpretation": "解释结果"}, confidence=0.8
        )
        assert success is True

        # 记录决策
        decision_id = tracker.record_decision(
            step_id=step_id,
            description="选择解释策略",
            alternatives=["策略A", "策略B"],
            chosen_alternative="策略A",
            reasoning="策略A更符合规则",
            importance=DecisionImportance.MEDIUM,
            confidence=0.7,
            constraints_applied=["约束1", "约束2"],
        )
        assert decision_id is not None

        # 记录错误
        error_success = tracker.record_error(
            step_id=step_id,
            error_type="解析错误",
            error_message="规则解析失败",
            severity="medium",
            recovery_action="使用默认解析",
        )
        assert error_success is True

        # 结束轨迹
        trace = tracker.end_trace()
        assert trace is not None
        assert trace.trace_id == trace_id
        assert trace.total_duration is not None
        assert len(trace.steps) == 1
        assert len(trace.decisions) == 1

        # 验证轨迹已添加到历史
        assert len(tracker.traces) == 1
        assert tracker.current_trace is None

    def test_generate_explainability_report(self, tracker):
        """测试生成可解释性报告"""
        # 创建完整轨迹
        trace_id = tracker.start_trace()

        step_id = tracker.start_step(
            name="测试步骤", step_type=ReasoningStepType.RULE_INTERPRETATION
        )
        tracker.end_step(step_id, confidence=0.8)

        tracker.record_decision(
            step_id=step_id,
            description="测试决策",
            alternatives=["选项A", "选项B"],
            chosen_alternative="选项A",
            reasoning="测试推理",
            importance=DecisionImportance.MEDIUM,
            confidence=0.7,
            constraints_applied=["约束1"],
        )

        tracker.end_trace()

        # 生成报告
        report = tracker.generate_explainability_report(trace_id)

        assert report is not None
        assert "trace_id" in report
        assert "step_breakdown" in report
        assert "decision_analysis" in report
        assert "confidence_analysis" in report
        assert "key_insights" in report

        # 验证步骤分解
        step_breakdown = report["step_breakdown"]
        assert isinstance(step_breakdown, list)
        assert len(step_breakdown) == 1

    def test_generate_visualization_data(self, tracker):
        """测试生成可视化数据"""
        trace_id = tracker.start_trace()

        step_id = tracker.start_step(
            name="可视化测试步骤", step_type=ReasoningStepType.LLM_GENERATION
        )
        tracker.end_step(step_id, confidence=0.85)

        tracker.end_trace()

        viz_data = tracker.generate_visualization_data(trace_id)

        assert viz_data is not None
        assert "timeline" in viz_data
        assert "decision_tree" in viz_data
        assert "confidence_radar" in viz_data

        timeline = viz_data["timeline"]
        assert isinstance(timeline, list)
        assert len(timeline) == 1

    def test_export_trace(self, tracker):
        """测试导出轨迹"""
        trace_id = tracker.start_trace(metadata={"export_test": True})

        step_id = tracker.start_step(
            name="导出测试步骤", step_type=ReasoningStepType.CONSISTENCY_CHECK
        )
        tracker.end_step(step_id)

        tracker.end_trace()

        # 导出为JSON
        json_export = tracker.export_trace(trace_id, format="json")
        assert json_export is not None
        assert "trace_id" in json_export
        assert "steps_summary" in json_export

        # 导出为结构化格式
        structured_export = tracker.export_trace(trace_id, format="structured")
        assert structured_export is not None
        assert "header" in structured_export
        assert "steps" in structured_export

        # 测试不支持格式
        invalid_export = tracker.export_trace(trace_id, format="invalid")
        assert "error" in invalid_export

    def test_get_trace_statistics(self, tracker):
        """测试获取轨迹统计"""
        # 创建多个轨迹
        for i in range(3):
            tracker.start_trace()
            step_id = tracker.start_step(f"步骤{i}", ReasoningStepType.OTHER)
            tracker.end_step(step_id, confidence=0.7 + i * 0.1)

            if i == 0:  # 第一个轨迹添加错误
                tracker.record_error(
                    step_id=step_id,
                    error_type="测试错误",
                    error_message="错误消息",
                    severity="low",
                )

            tracker.end_trace()

        stats = tracker.get_trace_statistics()

        assert stats is not None
        assert stats["total_traces"] == 3
        assert stats["total_steps"] == 3
        assert stats["total_errors"] == 1
        assert "average_duration" in stats
        assert "success_rate" in stats

    def test_compare_traces(self, tracker):
        """测试比较轨迹"""
        trace_ids = []

        # 创建3个不同特征的轨迹
        for i in range(3):
            trace_id = tracker.start_trace()
            trace_ids.append(trace_id)

            step_id = tracker.start_step(f"比较步骤{i}", ReasoningStepType.OTHER)
            tracker.end_step(step_id, confidence=0.5 + i * 0.2)

            if i > 0:  # 后两个轨迹添加决策
                tracker.record_decision(
                    step_id=step_id,
                    description=f"决策{i}",
                    alternatives=["A", "B"],
                    chosen_alternative="A",
                    reasoning="测试",
                    importance=DecisionImportance.LOW,
                    confidence=0.6,
                    constraints_applied=[],
                )

            tracker.end_trace()

        # 比较轨迹
        comparison = tracker.compare_traces(trace_ids)

        assert comparison is not None
        assert "trace_count" in comparison
        assert comparison["trace_count"] == 3
        assert "duration_comparison" in comparison
        assert "confidence_comparison" in comparison
        assert "error_comparison" in comparison
        assert "recommendations" in comparison

    def test_add_substep(self, tracker):
        """测试添加子步骤"""
        tracker.start_trace()

        parent_step_id = tracker.start_step(
            "父步骤", ReasoningStepType.RULE_INTERPRETATION
        )

        # 添加子步骤
        substep_id = tracker.add_substep(
            parent_step_id=parent_step_id,
            name="子步骤",
            details={"detail": "测试详情"},
            step_type=ReasoningStepType.OTHER,
        )

        assert substep_id is not None

        tracker.end_step(parent_step_id)
        tracker.end_trace()

        # 验证子步骤添加成功
        trace = tracker.traces[0]
        parent_step = trace.steps[0]
        assert len(parent_step.substeps) == 1
        assert parent_step.substeps[0].name == "子步骤"

    def test_record_error_with_recovery(self, tracker):
        """测试记录带恢复行动的错误"""
        tracker.start_trace()
        step_id = tracker.start_step("错误测试步骤", ReasoningStepType.ERROR_HANDLING)

        success = tracker.record_error(
            step_id=step_id,
            error_type="网络超时",
            error_message="请求超时",
            severity="high",
            recovery_action="重试请求",
            metadata={"attempt": 1, "max_attempts": 3},
        )

        assert success is True

        tracker.end_step(step_id)
        tracker.end_trace()

        # 验证错误记录
        trace = tracker.traces[0]
        step = trace.steps[0]
        assert len(step.errors) == 1

        error = step.errors[0]
        assert error["type"] == "网络超时"
        assert error["recovery_action"] == "重试请求"
        assert error["metadata"]["attempt"] == 1


class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def integrated_system(self):
        """创建集成系统"""
        # 模拟组件
        mock_llm = Mock()
        mock_llm.name = "test_llm"
        mock_llm.generate = AsyncMock(
            return_value=Mock(
                content="集成测试叙事响应。", model="test-model", usage={}, metadata={}
            )
        )

        mock_memory = Mock()
        mock_memory.retrieve_facts = AsyncMock(return_value=[])
        mock_memory.retrieve_characters = AsyncMock(return_value=[])
        mock_memory.retrieve_events = AsyncMock(return_value=[])

        # 创建组件实例
        pipeline = EnhancedReasoningPipeline(
            llm_provider=mock_llm, world_memory=mock_memory
        )

        context_builder = EnhancedContextBuilder()
        consistency_checker = EnhancedConsistencyChecker(llm_provider=None)
        tracker = ReasoningTracker(session_id="integration_test", turn_number=1)

        return {
            "pipeline": pipeline,
            "context_builder": context_builder,
            "consistency_checker": consistency_checker,
            "tracker": tracker,
        }

    @pytest.mark.asyncio
    async def test_integrated_reasoning_flow(self, integrated_system):
        """测试集成推理流程"""
        pipeline = integrated_system["pipeline"]
        tracker = integrated_system["tracker"]

        # 开始跟踪
        tracker.start_trace(metadata={"integration_test": True})

        # 创建上下文
        context = ReasoningContext(
            session_id="integration_session",
            turn_number=1,
            player_input="集成测试：玩家想要了解世界历史。",
            rules_text="这是一个集成的测试世界。规则简单明了。",
            memories=[
                {
                    "type": "fact",
                    "content": {"summary": "世界由测试数据构成", "certainty": "high"},
                }
            ],
            interventions=[],
        )

        # 记录推理步骤
        step_id = tracker.start_step(
            name="集成推理",
            step_type=ReasoningStepType.LLM_GENERATION,
            input_data={"context": str(context)[:100]},
        )

        # 执行推理
        result = await pipeline.process(context)

        # 记录步骤结果
        tracker.end_step(
            step_id=step_id,
            output_data={"result_summary": str(result)[:100]},
            confidence=result.confidence,
        )

        # 记录决策
        tracker.record_decision(
            step_id=step_id,
            description="生成叙事响应",
            alternatives=["详细响应", "简洁响应"],
            chosen_alternative="详细响应",
            reasoning="测试需要详细响应",
            importance=DecisionImportance.MEDIUM,
            confidence=result.confidence,
            constraints_applied=["测试约束"],
        )

        # 结束跟踪
        trace = tracker.end_trace()

        # 验证结果
        assert result is not None
        assert trace is not None
        assert len(trace.steps) == 1
        assert len(trace.decisions) == 1

        # 生成报告
        report = tracker.generate_explainability_report(trace.trace_id)
        assert report is not None
        assert report["trace_id"] == trace.trace_id

    @pytest.mark.asyncio
    async def test_consistency_check_integration(self, integrated_system):
        """测试一致性检查集成"""
        context_builder = integrated_system["context_builder"]
        consistency_checker = integrated_system["consistency_checker"]

        # 创建测试数据
        context = ReasoningContext(
            session_id="consistency_test",
            turn_number=1,
            player_input="测试一致性",
            rules_text="规则：禁止矛盾。",
            memories=[],
            interventions=[],
        )

        interpretation = Mock()
        interpretation.constraints = [Mock(type="prohibition", content="禁止自相矛盾")]

        # 构建上下文
        prompt = await context_builder.build_optimized(context, interpretation, [])

        # 测试响应
        test_response = "这是一个没有矛盾的响应。"

        # 检查一致性
        report = await consistency_checker.deep_check(
            test_response, context, interpretation, []
        )

        assert report is not None
        assert hasattr(report, "passed")
        assert hasattr(report, "overall_score")

        # 验证提示质量
        prompt_analysis = context_builder.analyze_prompt_quality(prompt)
        assert prompt_analysis is not None
        assert "quality_score" in prompt_analysis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
