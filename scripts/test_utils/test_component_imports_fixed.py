#!/usr/bin/env python3
"""
测试第二阶段组件导入 - 修复版本
"""

import importlib
import os
import sys

# 添加src目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(project_root, "src")
sys.path.insert(0, src_dir)

print(f"Project root: {project_root}")
print(f"Python path: {sys.path[:3]}")


def test_import(module_path, class_name=None):
    """测试导入模块或类"""
    try:
        if class_name:
            # 导入特定类
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            print(f"[OK] 成功导入 {class_name} from {module_path}")
            return True
        else:
            # 导入整个模块
            importlib.import_module(module_path)
            print(f"[OK] 成功导入模块 {module_path}")
            return True
    except ImportError as e:
        print(
            f"[FAIL] 导入失败 {module_path}{f'.{class_name}' if class_name else ''}: ImportError - {e}"
        )
        return False
    except AttributeError as e:
        print(
            f"[FAIL] 导入失败 {module_path}{f'.{class_name}' if class_name else ''}: AttributeError - {e}"
        )
        return False
    except Exception as e:
        print(
            f"[FAIL] 导入失败 {module_path}{f'.{class_name}' if class_name else ''}: {type(e).__name__} - {e}"
        )
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
        print("[OK] 所有第二阶段组件导入成功！")
        return 0
    else:
        print(f"[WARN] {total_count - success_count} 个组件导入失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
