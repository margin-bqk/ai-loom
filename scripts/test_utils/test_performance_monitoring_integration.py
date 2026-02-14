#!/usr/bin/env python3
"""
性能监控系统集成测试

验证性能监控系统与AI-Loom现有系统的集成兼容性。
测试PerformanceMonitor、BenchmarkFramework和ResourceAnalyzer的集成功能。
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loom.interpretation import (
    BenchmarkFramework,
    PerformanceMonitor,
    ResourceAnalyzer,
    get_benchmark_framework,
    get_performance_monitor,
    get_resource_analyzer,
)
from src.loom.interpretation.performance_optimizer import get_performance_optimizer


async def test_performance_monitor_integration():
    """测试性能监控器集成"""
    print("=" * 80)
    print("测试性能监控器集成")
    print("=" * 80)

    # 获取性能监控器
    monitor = get_performance_monitor(
        {
            "enable_system_metrics": False,  # 测试中禁用系统指标
            "enable_prometheus": False,
            "metrics_store": {"max_metrics": 100},
            "alert_manager": {
                "alert_rules": [
                    {
                        "name": "test_high_latency",
                        "condition": {
                            "metric_type": "latency",
                            "operator": ">",
                            "threshold": 5000,
                        },
                        "severity": "warning",
                        "message": "测试高延迟：{metric_name}={metric_value}ms",
                    }
                ]
            },
        }
    )

    # 记录测试指标
    print("记录测试指标...")
    monitor.record_latency("api.users.get", 120.5, {"method": "GET", "status": "200"})
    monitor.record_throughput("api.users", 150.2, {"method": "GET"})
    monitor.record_error_rate("api.users", 2.5, {"method": "GET"})
    monitor.record_memory_usage("app.memory", 256.8, {"type": "heap"})
    monitor.record_cpu_usage("app.cpu", 45.3, {"core": "0"})
    monitor.record_token_usage(
        "llm.tokens", 1250, {"provider": "openai", "model": "gpt-4"}
    )
    monitor.record_cost("llm.cost", 0.025, {"provider": "openai", "model": "gpt-4"})

    # 获取指标
    metrics = monitor.get_metrics()
    print(f"已记录指标数量: {len(metrics)}")

    # 获取性能报告
    report = monitor.get_performance_report()
    print(f"性能报告生成成功")
    print(f"  时间范围: {report.time_range[0]} 到 {report.time_range[1]}")
    print(f"  指标总数: {report.summary.get('total_metrics', 0)}")
    print(f"  告警数量: {len(report.alerts)}")
    print(f"  优化建议: {len(report.recommendations)}")

    # 获取监控统计
    stats = monitor.get_stats()
    print(f"监控统计: {stats['metrics_store']['total_metrics']} 个指标")

    return True


async def test_benchmark_framework_integration():
    """测试基准测试框架集成"""
    print("\n" + "=" * 80)
    print("测试基准测试框架集成")
    print("=" * 80)

    # 获取基准测试框架
    framework = get_benchmark_framework(
        {
            "results_store": {
                "max_results": 20,
                "retention_days": 7,
                "storage_path": "./test_benchmark_results",
            },
            "regression_threshold": 10.0,
        }
    )

    # 定义测试基准测试函数
    async def mock_llm_inference(params):
        """模拟LLM推理基准测试"""
        # 模拟推理延迟
        await asyncio.sleep(0.02)

        # 模拟令牌使用
        input_tokens = params.get("input_tokens", 100)
        output_tokens = params.get("output_tokens", 50)

        return {
            "latency_ms": 20.5,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }

    async def mock_memory_operation(params):
        """模拟内存操作基准测试"""
        # 模拟内存操作
        await asyncio.sleep(0.01)

        # 创建一些测试数据
        test_data = [i for i in range(10000)]

        return {
            "latency_ms": 10.2,
            "memory_usage_mb": len(test_data) * 8 / (1024 * 1024),
        }

    # 注册基准测试
    framework.register_benchmark("llm_inference", mock_llm_inference)
    framework.register_benchmark("memory_operation", mock_memory_operation)

    # 运行基准测试
    print("运行LLM推理基准测试...")
    llm_result = await framework.run_benchmark(
        "llm_inference",
        {
            "iterations": 5,
            "warmup_iterations": 2,
            "parameters": {"input_tokens": 150, "output_tokens": 75},
        },
    )

    print("运行内存操作基准测试...")
    memory_result = await framework.run_benchmark(
        "memory_operation", {"iterations": 5, "warmup_iterations": 2}
    )

    # 验证结果
    print(f"LLM推理基准测试结果: {llm_result.status.value}")
    print(f"  基准测试ID: {llm_result.benchmark_id}")
    print(f"  迭代次数: {llm_result.config.iterations}")
    print(f"  延迟指标: {len(llm_result.metrics.get('latency_ms', []))} 个样本")

    print(f"内存操作基准测试结果: {memory_result.status.value}")
    print(f"  基准测试ID: {memory_result.benchmark_id}")
    print(f"  迭代次数: {memory_result.config.iterations}")

    # 生成综合报告
    report = framework.generate_comprehensive_report(format="text")
    print(f"\n基准测试综合报告生成成功")

    # 检测回归
    regressions = framework.detect_regressions()
    print(f"检测到回归: {len(regressions)} 个")

    return True


async def test_resource_analyzer_integration():
    """测试资源分析器集成"""
    print("\n" + "=" * 80)
    print("测试资源分析器集成")
    print("=" * 80)

    # 获取资源分析器
    analyzer = get_resource_analyzer(
        {
            "collection_interval": 2,  # 测试中使用较短的间隔
            "max_history_size": 10,
            "memory": {
                "enable_memory_tracking": False,
                "high_memory_threshold": 90.0,
                "memory_leak_threshold": 50.0,
            },
            "cpu": {"high_cpu_threshold": 90.0},
            "disk": {
                "low_disk_threshold": 5.0,
                "monitored_paths": ["."],  # 监控当前目录
            },
            "thread": {"thread_leak_threshold": 100},
        }
    )

    # 开始自动收集
    analyzer.start_collection()
    print("资源收集已启动")

    # 等待收集一些数据
    await asyncio.sleep(3)

    # 停止收集
    analyzer.stop_collection()
    print("资源收集已停止")

    # 收集当前资源使用
    print("收集当前资源使用...")
    resources = analyzer.collect_all_resources()

    print("资源使用情况:")
    if "memory" in resources:
        mem = resources["memory"]
        print(
            f"  内存: {mem.usage_value / (1024*1024):.2f} MB ({mem.usage_percent:.1f}%)"
        )

    if "cpu" in resources:
        cpu = resources["cpu"]
        print(f"  CPU: {cpu.usage_value:.1f}% (系统: {cpu.usage_percent:.1f}%)")

    if "thread" in resources:
        thread = resources["thread"]
        print(f"  线程: {thread.usage_value} 个")

    # 分析资源问题
    print("分析资源问题...")
    issues = analyzer.analyze_resource_issues()
    print(f"检测到资源问题: {len(issues)} 个")

    for i, issue in enumerate(issues, 1):
        print(f"  问题 {i}: {issue.issue_type.value} - {issue.severity}")
        print(f"    描述: {issue.description}")

    # 生成分析报告
    print("生成资源分析报告...")
    report = analyzer.generate_analysis_report()

    print(f"资源分析报告:")
    print(f"  时间范围: {report.time_range[0]} 到 {report.time_range[1]}")
    print(f"  问题数量: {len(report.issues_detected)}")
    print(f"  优化建议: {len(report.optimization_recommendations)}")

    # 获取分析器统计
    stats = analyzer.get_stats()
    print(f"分析器统计:")
    print(f"  资源历史记录: {stats['resource_history_count']}")
    print(f"  检测到的问题: {stats['detected_issues_count']}")
    print(f"  收集运行中: {stats['collection_running']}")

    return True


async def test_performance_optimizer_integration():
    """测试性能优化器集成"""
    print("\n" + "=" * 80)
    print("测试性能优化器集成")
    print("=" * 80)

    # 获取性能优化器
    optimizer = get_performance_optimizer()

    # 获取统计信息
    stats = optimizer.get_stats()

    print("性能优化器统计:")
    print(f"  连接池: {len(stats['connection_pools'])} 个")
    print(f"  响应缓存大小: {stats['response_cache']['cache_size']}")
    print(f"  批处理器待处理请求: {stats['batch_processor']['total_pending_requests']}")
    print(f"  令牌计数器: {stats['token_counter']['total_tokens']} 个令牌")

    return True


async def test_full_integration():
    """测试完整集成"""
    print("\n" + "=" * 80)
    print("测试完整集成工作流")
    print("=" * 80)

    # 获取所有组件
    monitor = get_performance_monitor()
    framework = get_benchmark_framework()
    analyzer = get_resource_analyzer()

    # 设置基准测试框架使用性能监控器
    framework.set_performance_monitor(monitor)

    # 定义集成基准测试函数
    async def integrated_workflow(params):
        """集成工作流基准测试"""
        start_time = time.time()

        # 模拟工作流步骤
        steps = params.get("steps", 3)

        for step in range(steps):
            # 模拟每个步骤的工作
            await asyncio.sleep(0.01)

            # 记录步骤指标
            step_latency = (time.time() - start_time) * 1000 / (step + 1)
            monitor.record_latency(
                f"workflow.step.{step}",
                step_latency,
                {"workflow": "integrated", "step": str(step)},
            )

        total_latency = (time.time() - start_time) * 1000

        # 记录资源使用
        resources = analyzer.collect_all_resources()
        if "memory" in resources:
            monitor.record_memory_usage(
                "workflow.memory",
                resources["memory"].usage_value / (1024 * 1024),  # 转换为MB
                {"workflow": "integrated"},
            )

        return {
            "total_latency_ms": total_latency,
            "steps": steps,
            "avg_latency_per_step": total_latency / steps,
        }

    # 注册并运行集成基准测试
    framework.register_benchmark("integrated_workflow", integrated_workflow)

    print("运行集成工作流基准测试...")
    result = await framework.run_benchmark(
        "integrated_workflow",
        {"iterations": 3, "warmup_iterations": 1, "parameters": {"steps": 5}},
    )

    print(f"集成基准测试结果: {result.status.value}")
    print(f"  基准测试ID: {result.benchmark_id}")

    # 验证监控器记录了指标
    workflow_metrics = monitor.get_metrics(name__contains="workflow.")
    print(f"  工作流相关指标: {len(workflow_metrics)} 个")

    # 生成资源分析报告
    resource_report = analyzer.generate_analysis_report()
    print(f"  资源分析报告问题: {len(resource_report.issues_detected)} 个")

    return True


async def main():
    """主测试函数"""
    print("AI-Loom 性能监控系统集成测试")
    print("=" * 80)

    test_results = {}

    try:
        # 测试性能监控器集成
        test_results[
            "performance_monitor"
        ] = await test_performance_monitor_integration()

        # 测试基准测试框架集成
        test_results[
            "benchmark_framework"
        ] = await test_benchmark_framework_integration()

        # 测试资源分析器集成
        test_results["resource_analyzer"] = await test_resource_analyzer_integration()

        # 测试性能优化器集成
        test_results[
            "performance_optimizer"
        ] = await test_performance_optimizer_integration()

        # 测试完整集成
        test_results["full_integration"] = await test_full_integration()

    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 汇总测试结果
    print("\n" + "=" * 80)
    print("集成测试结果汇总")
    print("=" * 80)

    all_passed = True
    for test_name, passed in test_results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name:30} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("所有集成测试通过！性能监控系统已成功集成。")
        return True
    else:
        print("部分集成测试失败，请检查上述错误。")
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())

    # 清理测试文件
    import shutil

    test_benchmark_dir = Path("./test_benchmark_results")
    if test_benchmark_dir.exists():
        shutil.rmtree(test_benchmark_dir)
        print(f"\n清理测试目录: {test_benchmark_dir}")

    sys.exit(0 if success else 1)
