#!/usr/bin/env python3
"""
测试第二阶段组件导入
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import(module_path, class_name=None):
    """测试导入模块或类"""
    try:
        if class_name:
            # 导入特定类
            exec(f"from {module_path} import {class_name}")
            print(f"✓ 成功导入 {class_name} from {module_path}")
            return True
        else:
            # 导入整个模块
            exec(f"import {module_path}")
            print(f"✓ 成功导入模块 {module_path}")
            return True
    except Exception as e:
        print(f"✗ 导入失败 {module_path}{f'.{class_name}' if class_name else ''}: {e}")
        return False


def main():
    print("=" * 60)
    print("AI-Loom 第二阶段组件导入测试")
    print("=" * 60)

    # 第二阶段核心组件列表
    components = [
        # 1. 高级推理引擎
        (
            "loom.interpretation.enhanced_reasoning_pipeline",
            "EnhancedReasoningPipeline",
        ),
        ("loom.interpretation.enhanced_context_builder", "EnhancedContextBuilder"),
        (
            "loom.interpretation.enhanced_consistency_checker",
            "EnhancedConsistencyChecker",
        ),
        ("loom.interpretation.reasoning_tracker", "ReasoningTracker"),
        # 2. 世界记忆系统
        ("loom.memory.vector_memory_store", "VectorMemoryStore"),
        ("loom.memory.memory_summarizer", "MemorySummarizer"),
        ("loom.memory.enhanced_world_memory", "EnhancedWorldMemory"),
        ("loom.memory.memory_consistency_checker", "MemoryConsistencyChecker"),
        # 3. 规则层增强
        ("loom.rules.advanced_markdown_canon", "AdvancedMarkdownCanon"),
        ("loom.rules.rule_validator", "RuleValidator"),
        ("loom.rules.rule_hot_loader", "RuleHotLoader"),
        # 4. LLM Provider增强
        ("loom.interpretation.enhanced_provider_manager", "EnhancedProviderManager"),
        ("loom.interpretation.cost_optimizer", "CostOptimizer"),
        ("loom.interpretation.local_model_provider", "LocalModelProvider"),
        # 5. 性能监控系统
        ("loom.interpretation.performance_monitor", "PerformanceMonitor"),
        ("loom.interpretation.benchmark_framework", "BenchmarkFramework"),
        ("loom.interpretation.resource_analyzer", "ResourceAnalyzer"),
    ]

    success_count = 0
    total_count = len(components)

    for module_path, class_name in components:
        if test_import(module_path, class_name):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"导入测试结果: {success_count}/{total_count} 成功")
    print("=" * 60)

    if success_count == total_count:
        print("✓ 所有第二阶段组件导入成功！")
        return 0
    else:
        print(f"⚠️  {total_count - success_count} 个组件导入失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
