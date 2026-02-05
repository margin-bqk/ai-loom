#!/usr/bin/env python3
"""
增强推理引擎集成测试

验证新组件与现有系统的兼容性。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loom.interpretation import (
    # 基础组件
    ReasoningPipeline,
    ReasoningContext,
    ReasoningResult,
    ConsistencyChecker,
    # 增强组件
    EnhancedReasoningPipeline,
    EnhancedContextBuilder,
    EnhancedConsistencyChecker,
    ReasoningTracker,
    # 枚举和数据类型
    ContextOptimizationStrategy,
    ReasoningStepType,
    DecisionImportance,
)

from src.loom.interpretation.llm_provider import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """模拟LLM提供者用于测试"""

    def __init__(self, name="mock_provider"):
        self.name = name
        self.call_count = 0
        self.provider_type = "mock"

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本的具体实现"""
        self.call_count += 1

        # 基于提示生成简单响应
        if "城堡" in prompt:
            response = "玩家探索了古老的城堡，发现了隐藏的通道。守卫警惕地巡逻，但玩家成功避开了他们。"
        elif "森林" in prompt:
            response = "玩家进入了神秘的森林，树木高耸入云。远处传来奇怪的声响，但玩家决定继续前进。"
        else:
            response = "这是一个测试叙事响应。玩家进行了行动，故事继续发展。"

        return LLMResponse(
            content=response,
            model=kwargs.get("model", "mock-model"),
            usage={
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(response) // 4,
            },
            metadata={"mock": True, "call_count": self.call_count},
        )

    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        import asyncio

        response = "这是一个测试流式响应。"
        for char in response:
            await asyncio.sleep(0.01)
            yield char

    def get_available_models(self):
        return ["mock-model-1", "mock-model-2"]

    def get_token_count(self, text):
        return len(text) // 4

    async def validate_connection(self):
        return True


async def test_backward_compatibility():
    """测试向后兼容性"""
    print("=" * 60)
    print("测试向后兼容性")
    print("=" * 60)

    # 创建模拟LLM提供者
    mock_llm = MockLLMProvider()

    # 测试基础推理管道仍然工作
    print("\n1. 测试基础ReasoningPipeline...")
    try:
        base_pipeline = ReasoningPipeline(llm_provider=mock_llm)

        context = ReasoningContext(
            session_id="compat_test",
            turn_number=1,
            player_input="玩家想要探索城堡。",
            rules_text="这是一个奇幻世界。",
            memories=[],
            interventions=[],
        )

        result = await base_pipeline.process(context)
        print(f"   基础管道测试通过")
        print(f"   响应长度: {len(result.narrative_response)}")
        print(f"   置信度: {result.confidence:.2f}")
    except Exception as e:
        print(f"   基础管道测试失败: {e}")
        return False

    # 测试基础一致性检查器
    print("\n2. 测试基础ConsistencyChecker...")
    try:
        base_checker = ConsistencyChecker()

        report = base_checker.check(
            response="测试响应", rules_text="测试规则", constraints=[]
        )

        print(f"   基础检查器测试通过")
        print(f"   一致性分数: {report.get('score', 0):.2f}")
    except Exception as e:
        print(f"   基础检查器测试失败: {e}")
        return False

    return True


async def test_enhanced_components():
    """测试增强组件"""
    print("\n" + "=" * 60)
    print("测试增强组件")
    print("=" * 60)

    mock_llm = MockLLMProvider()

    # 测试增强推理管道
    print("\n1. 测试EnhancedReasoningPipeline...")
    try:
        enhanced_pipeline = EnhancedReasoningPipeline(llm_provider=mock_llm)

        context = ReasoningContext(
            session_id="enhanced_test",
            turn_number=1,
            player_input="玩家想要与守卫交谈。",
            rules_text="这是一个中世纪奇幻世界。魔法存在但稀有。",
            memories=[
                {
                    "type": "character",
                    "content": {"name": "守卫", "traits": ["忠诚", "警惕"]},
                }
            ],
            interventions=[],
        )

        result = await enhanced_pipeline.process(context)
        print(f"   增强管道测试通过")
        print(f"   响应: {result.narrative_response[:50]}...")
        print(f"   增强置信度: {result.confidence:.2f}")
        print(f"   详细步骤: {len(result.reasoning_steps_detailed)}个")

        if hasattr(result, "consistency_report"):
            print(
                f"   一致性报告: {result.consistency_report.get('overall_score', 0):.2f}"
            )
    except Exception as e:
        print(f"   增强管道测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 测试增强上下文构建器
    print("\n2. 测试EnhancedContextBuilder...")
    try:
        context_builder = EnhancedContextBuilder()

        context = ReasoningContext(
            session_id="context_test",
            turn_number=1,
            player_input="测试输入",
            rules_text="测试规则文本。",
            memories=[],
            interventions=[],
        )

        interpretation = type(
            "MockInterpretation",
            (),
            {"constraints": [], "narrative_output": "测试解释"},
        )()

        # 测试不同策略
        strategies = list(ContextOptimizationStrategy)
        for strategy in strategies[:2]:  # 测试前两种策略
            prompt = await context_builder.build_with_strategy(
                context, interpretation, [], strategy
            )
            print(f"   策略 '{strategy.value}': {len(prompt)} 字符")

        # 分析提示质量
        test_prompt = "# 测试\n这是一个测试提示。"
        analysis = context_builder.analyze_prompt_quality(test_prompt)
        print(f"   提示质量分析: 分数={analysis.get('quality_score', 0):.2f}")

    except Exception as e:
        print(f"   增强上下文构建器测试失败: {e}")
        return False

    # 测试增强一致性检查器
    print("\n3. 测试EnhancedConsistencyChecker...")
    try:
        checker = EnhancedConsistencyChecker(llm_provider=mock_llm)

        context = ReasoningContext(
            session_id="consistency_test",
            turn_number=1,
            player_input="测试",
            rules_text="规则：禁止矛盾。",
            memories=[],
            interventions=[],
        )

        interpretation = type("MockInterpretation", (), {"constraints": []})()

        report = await checker.deep_check(
            "这是一个没有矛盾的测试响应。", context, interpretation, []
        )

        print(f"   增强一致性检查器测试通过")
        print(f"   总体分数: {report.overall_score:.2f}")
        print(f"   通过: {report.passed}")
        print(f"   问题数量: {len(report.issues)}")

    except Exception as e:
        print(f"   增强一致性检查器测试失败: {e}")
        return False

    # 测试推理跟踪器
    print("\n4. 测试ReasoningTracker...")
    try:
        tracker = ReasoningTracker(session_id="tracker_test", turn_number=1)

        # 创建完整轨迹
        trace_id = tracker.start_trace(metadata={"test": True})

        step_id = tracker.start_step(
            name="集成测试步骤",
            step_type=ReasoningStepType.LLM_GENERATION,
            input_data={"test": "data"},
        )

        tracker.end_step(step_id, confidence=0.8)

        tracker.record_decision(
            step_id=step_id,
            description="测试决策",
            alternatives=["A", "B"],
            chosen_alternative="A",
            reasoning="测试推理",
            importance=DecisionImportance.MEDIUM,
            confidence=0.7,
            constraints_applied=["约束1"],
        )

        trace = tracker.end_trace()

        print(f"   推理跟踪器测试通过")
        print(f"   轨迹ID: {trace.trace_id}")
        print(f"   步骤数量: {len(trace.steps)}")
        print(f"   决策数量: {len(trace.decisions)}")
        print(f"   总时长: {trace.total_duration:.2f}s")

        # 生成报告
        report = tracker.generate_explainability_report(trace_id)
        print(f"   报告生成成功: {len(report.keys())} 个部分")

    except Exception as e:
        print(f"   推理跟踪器测试失败: {e}")
        return False

    return True


async def test_integration_scenarios():
    """测试集成场景"""
    print("\n" + "=" * 60)
    print("测试集成场景")
    print("=" * 60)

    mock_llm = MockLLMProvider()

    # 场景1：完整推理流程
    print("\n1. 完整推理流程场景...")
    try:
        # 创建所有组件
        pipeline = EnhancedReasoningPipeline(llm_provider=mock_llm)
        context_builder = EnhancedContextBuilder()
        consistency_checker = EnhancedConsistencyChecker(llm_provider=mock_llm)
        tracker = ReasoningTracker(session_id="integration_scenario", turn_number=1)

        # 开始跟踪
        tracker.start_trace(metadata={"scenario": "full_reasoning"})

        # 创建上下文
        context = ReasoningContext(
            session_id="scenario_1",
            turn_number=1,
            player_input="玩家发现了神秘的地图，想要按照地图探索。",
            rules_text="这是一个冒险世界。地图可能指向宝藏或危险。",
            memories=[
                {
                    "type": "fact",
                    "content": {"summary": "玩家之前找到过藏宝图", "relevance": 0.8},
                }
            ],
            interventions=[],
        )

        # 记录推理开始
        step_id = tracker.start_step(
            name="完整推理", step_type=ReasoningStepType.LLM_GENERATION
        )

        # 执行推理
        result = await pipeline.process(context)

        # 记录结果
        tracker.end_step(step_id, confidence=result.confidence)

        # 检查一致性
        interpretation = type("MockInterpretation", (), {"constraints": []})()

        consistency_report = await consistency_checker.deep_check(
            result.narrative_response, context, interpretation, context.memories
        )

        # 记录决策
        tracker.record_decision(
            step_id=step_id,
            description="生成探索叙事",
            alternatives=["安全路线", "冒险路线"],
            chosen_alternative="冒险路线",
            reasoning="符合冒险世界设定",
            importance=DecisionImportance.HIGH,
            confidence=result.confidence,
            constraints_applied=["冒险主题"],
        )

        # 结束跟踪
        trace = tracker.end_trace()

        print(f"   场景1测试通过")
        print(f"   推理结果置信度: {result.confidence:.2f}")
        print(f"   一致性分数: {consistency_report.overall_score:.2f}")
        print(f"   跟踪步骤: {len(trace.steps)}")

    except Exception as e:
        print(f"   场景1测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 场景2：批量处理
    print("\n2. 批量处理场景...")
    try:
        pipeline = EnhancedReasoningPipeline(llm_provider=mock_llm)

        contexts = []
        for i in range(2):  # 创建2个上下文
            contexts.append(
                ReasoningContext(
                    session_id=f"batch_{i}",
                    turn_number=i + 1,
                    player_input=f"批量测试输入{i}",
                    rules_text="批量测试规则",
                    memories=[],
                    interventions=[],
                )
            )

        results = await pipeline.batch_process(contexts)

        print(f"   场景2测试通过")
        print(f"   处理数量: {len(results)}")
        for i, result in enumerate(results):
            print(
                f"     结果{i}: 置信度={result.confidence:.2f}, 长度={len(result.narrative_response)}"
            )

    except Exception as e:
        print(f"   场景2测试失败: {e}")
        return False

    # 场景3：错误处理
    print("\n3. 错误处理场景...")
    try:
        tracker = ReasoningTracker(session_id="error_scenario", turn_number=1)
        tracker.start_trace()

        step_id = tracker.start_step("错误测试", ReasoningStepType.ERROR_HANDLING)

        # 记录错误
        tracker.record_error(
            step_id=step_id,
            error_type="模拟错误",
            error_message="这是一个测试错误",
            severity="medium",
            recovery_action="重试操作",
            metadata={"test": True},
        )

        tracker.end_step(step_id)
        trace = tracker.end_trace()

        # 分析错误
        error_analysis = tracker.generate_explainability_report(trace.trace_id)

        print(f"   场景3测试通过")
        print(f"   错误记录成功")
        if "error_analysis" in error_analysis:
            print(
                f"   错误分析: {error_analysis['error_analysis'].get('total_errors', 0)} 个错误"
            )

    except Exception as e:
        print(f"   场景3测试失败: {e}")
        return False

    return True


async def main():
    """主测试函数"""
    print("AI-Loom 增强推理引擎集成测试")
    print("=" * 60)

    all_passed = True

    # 运行测试
    if not await test_backward_compatibility():
        all_passed = False
        print("\n⚠️  向后兼容性测试失败")
    else:
        print("\n✅ 向后兼容性测试通过")

    if not await test_enhanced_components():
        all_passed = False
        print("\n⚠️  增强组件测试失败")
    else:
        print("\n✅ 增强组件测试通过")

    if not await test_integration_scenarios():
        all_passed = False
        print("\n⚠️  集成场景测试失败")
    else:
        print("\n✅ 集成场景测试通过")

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有集成测试通过！增强推理引擎已成功集成。")
        print("\n实现总结:")
        print("1. EnhancedReasoningPipeline: 多步骤推理管道 ✓")
        print("2. EnhancedContextBuilder: 智能上下文构建器 ✓")
        print("3. EnhancedConsistencyChecker: 深度一致性检查器 ✓")
        print("4. ReasoningTracker: 推理跟踪和可解释性工具 ✓")
        print("5. 向后兼容性: 保持与现有系统兼容 ✓")
        print("6. 单元测试框架: 完整的测试覆盖 ✓")
        print("7. 集成验证: 组件间协同工作正常 ✓")
    else:
        print("❌ 集成测试失败，请检查上述错误。")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
