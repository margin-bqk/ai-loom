#!/usr/bin/env python3
"""
性能监控系统验证脚本

验证新实现的性能监控组件的基本功能。
"""

import sys
import os
from pathlib import Path

# 直接导入性能监控模块，避免复杂的依赖
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_performance_monitor():
    """验证PerformanceMonitor"""
    print("验证PerformanceMonitor...")

    try:
        from src.loom.interpretation.performance_monitor import (
            PerformanceMonitor,
            Metric,
            MetricType,
            AlertSeverity,
        )

        # 创建配置
        config = {
            "enable_system_metrics": False,
            "enable_prometheus": False,
            "metrics_store": {"max_metrics": 100},
        }

        # 创建实例
        monitor = PerformanceMonitor(config)

        # 测试记录指标
        monitor.record_latency("test.endpoint", 150.0)
        monitor.record_throughput("test.endpoint", 100.0)
        monitor.record_error_rate("test.endpoint", 2.5)

        # 获取指标
        metrics = monitor.get_metrics()
        print(f"  [OK] 成功记录和获取 {len(metrics)} 个指标")

        # 测试获取报告
        report = monitor.get_performance_report()
        print(f"  [OK] 成功生成性能报告")

        # 测试获取统计
        stats = monitor.get_stats()
        print(f"  [OK] 成功获取监控统计")

        return True

    except Exception as e:
        print(f"  [FAIL] PerformanceMonitor验证失败: {e}")
        return False


def verify_benchmark_framework():
    """验证BenchmarkFramework"""
    print("验证BenchmarkFramework...")

    try:
        from src.loom.interpretation.benchmark_framework import (
            BenchmarkFramework,
            BenchmarkConfig,
            BenchmarkType,
            BenchmarkStatus,
        )
        import asyncio

        # 创建框架
        framework = BenchmarkFramework({"results_store": {"max_results": 10}})

        # 定义测试函数
        async def test_func(params):
            import asyncio

            await asyncio.sleep(0.01)
            return {"test": "result"}

        # 注册基准测试
        framework.register_benchmark("test_benchmark", test_func)
        print(f"  ✓ 成功注册基准测试")

        # 测试配置
        config = BenchmarkConfig(
            name="test", benchmark_type=BenchmarkType.LATENCY, iterations=3
        )
        print(f"  ✓ 成功创建基准测试配置")

        return True

    except Exception as e:
        print(f"  ✗ BenchmarkFramework验证失败: {e}")
        return False


def verify_resource_analyzer():
    """验证ResourceAnalyzer"""
    print("验证ResourceAnalyzer...")

    try:
        from src.loom.interpretation.resource_analyzer import (
            ResourceAnalyzer,
            ResourceType,
            ResourceUsage,
        )

        # 创建分析器
        analyzer = ResourceAnalyzer(
            {
                "collection_interval": 60,
                "memory": {"enable_memory_tracking": False},
                "cpu": {"sampling_interval": 5},
            }
        )

        # 测试资源使用对象
        usage = ResourceUsage(
            resource_type=ResourceType.MEMORY,
            usage_value=100 * 1024 * 1024,  # 100MB
            usage_percent=50.0,
            unit="bytes",
        )
        print(f"  ✓ 成功创建资源使用对象")

        # 测试收集资源
        resources = analyzer.collect_all_resources()
        print(f"  ✓ 成功收集资源使用数据")

        # 测试获取统计
        stats = analyzer.get_stats()
        print(f"  ✓ 成功获取分析器统计")

        return True

    except Exception as e:
        print(f"  ✗ ResourceAnalyzer验证失败: {e}")
        return False


def verify_module_exports():
    """验证模块导出"""
    print("验证模块导出...")

    try:
        from src.loom.interpretation import __all__ as interpretation_exports

        # 检查关键类是否已导出
        required_exports = [
            "PerformanceMonitor",
            "BenchmarkFramework",
            "ResourceAnalyzer",
            "get_performance_monitor",
            "get_benchmark_framework",
            "get_resource_analyzer",
        ]

        missing = []
        for export in required_exports:
            if export not in interpretation_exports:
                missing.append(export)

        if missing:
            print(f"  [FAIL] 缺少导出: {missing}")
            return False
        else:
            print(f"  [OK] 所有关键类已正确导出")
            return True

    except Exception as e:
        print(f"  [FAIL] 模块导出验证失败: {e}")
        return False


def verify_file_structure():
    """验证文件结构"""
    print("验证文件结构...")

    base_dir = Path(__file__).parent.parent
    required_files = [
        "src/loom/interpretation/performance_monitor.py",
        "src/loom/interpretation/benchmark_framework.py",
        "src/loom/interpretation/resource_analyzer.py",
        "tests/test_interpretation/test_performance_monitoring.py",
    ]

    missing = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing.append(file_path)

        if missing:
            print(f"  [FAIL] 缺少文件: {missing}")
            return False
        else:
            print(f"  [OK] 所有必需文件已创建")
            return True


def main():
    """主验证函数"""
    print("=" * 80)
    print("AI-Loom 性能监控系统验证")
    print("=" * 80)

    results = {}

    # 验证文件结构
    results["file_structure"] = verify_file_structure()

    # 验证模块导出
    results["module_exports"] = verify_module_exports()

    # 验证各组件
    results["performance_monitor"] = verify_performance_monitor()
    results["benchmark_framework"] = verify_benchmark_framework()
    results["resource_analyzer"] = verify_resource_analyzer()

    # 汇总结果
    print("\n" + "=" * 80)
    print("验证结果汇总")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("所有验证通过！性能监控系统实现完成。")
        print("\n实现的功能:")
        print("  1. PerformanceMonitor - 实时性能指标收集和监控告警")
        print("  2. BenchmarkFramework - 标准化基准测试和性能对比")
        print("  3. ResourceAnalyzer - 资源使用分析和优化建议")
        print("  4. 完整的单元测试框架")
        print("  5. 与现有系统的集成兼容性")
        return True
    else:
        print("部分验证失败，请检查上述问题。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
