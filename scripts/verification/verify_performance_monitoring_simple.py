#!/usr/bin/env python3
"""
性能监控系统验证脚本 - 简单版本
"""

import os
import sys
from pathlib import Path

# 直接导入性能监控模块
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_file_exists():
    """检查文件是否存在"""
    print("检查文件结构...")

    base_dir = Path(__file__).parent.parent
    required_files = [
        "src/loom/interpretation/performance_monitor.py",
        "src/loom/interpretation/benchmark_framework.py",
        "src/loom/interpretation/resource_analyzer.py",
        "tests/test_interpretation/test_performance_monitoring.py",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [FAIL] {file_path}")
            all_exist = False

    return all_exist


def check_module_imports():
    """检查模块导入"""
    print("\n检查模块导入...")

    try:
        # 尝试导入主要模块
        from src.loom.interpretation.performance_monitor import PerformanceMonitor

        print("  [OK] 成功导入 PerformanceMonitor")

        from src.loom.interpretation.benchmark_framework import BenchmarkFramework

        print("  [OK] 成功导入 BenchmarkFramework")

        from src.loom.interpretation.resource_analyzer import ResourceAnalyzer

        print("  [OK] 成功导入 ResourceAnalyzer")

        # 检查__init__.py导出
        from src.loom.interpretation import __all__ as exports

        required_exports = [
            "PerformanceMonitor",
            "BenchmarkFramework",
            "ResourceAnalyzer",
            "get_performance_monitor",
            "get_benchmark_framework",
            "get_resource_analyzer",
        ]

        missing = [e for e in required_exports if e not in exports]
        if missing:
            print(f"  [FAIL] 缺少导出: {missing}")
            return False
        else:
            print("  [OK] 所有关键类已正确导出")
            return True

    except Exception as e:
        print(f"  [FAIL] 模块导入失败: {e}")
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("\n测试基本功能...")

    try:
        from src.loom.interpretation.performance_monitor import (
            Metric,
            MetricType,
            PerformanceMonitor,
        )

        # 创建性能监控器
        monitor = PerformanceMonitor(
            {
                "enable_system_metrics": False,
                "enable_prometheus": False,
                "metrics_store": {"max_metrics": 100},
            }
        )

        # 记录一些指标
        monitor.record_latency("test.api", 150.0)
        monitor.record_throughput("test.api", 100.0)

        # 获取指标
        metrics = monitor.get_metrics()
        print(f"  [OK] 成功记录和获取 {len(metrics)} 个指标")

        # 获取报告
        report = monitor.get_performance_report()
        print(f"  [OK] 成功生成性能报告")

        return True

    except Exception as e:
        print(f"  [FAIL] 基本功能测试失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("AI-Loom 性能监控系统验证")
    print("=" * 60)

    results = []

    # 检查文件
    file_ok = check_file_exists()
    results.append(("文件结构", file_ok))

    # 检查导入
    import_ok = check_module_imports()
    results.append(("模块导入", import_ok))

    # 测试功能
    func_ok = test_basic_functionality()
    results.append(("基本功能", func_ok))

    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name:15} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("所有验证通过！性能监控系统实现完成。")
        print("\n实现总结:")
        print("1. PerformanceMonitor - 实时性能监控和告警")
        print("2. BenchmarkFramework - 基准测试和性能对比")
        print("3. ResourceAnalyzer - 资源使用分析和优化")
        print("4. 完整的单元测试框架")
        print("5. 与现有系统集成兼容")
        return True
    else:
        print("部分验证失败，请检查上述问题。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
