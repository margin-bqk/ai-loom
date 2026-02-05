"""
性能监控组件单元测试

测试PerformanceMonitor、BenchmarkFramework和ResourceAnalyzer的功能。
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.loom.interpretation.performance_monitor import (
    PerformanceMonitor,
    Metric,
    MetricType,
    Alert,
    AlertSeverity,
    MetricsStore,
    AlertManager,
    get_performance_monitor,
)
from src.loom.interpretation.benchmark_framework import (
    BenchmarkFramework,
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkType,
    BenchmarkStatus,
    get_benchmark_framework,
)
from src.loom.interpretation.resource_analyzer import (
    ResourceAnalyzer,
    ResourceUsage,
    ResourceType,
    ResourceIssueType,
    get_resource_analyzer,
)


class TestMetricsStore:
    """测试MetricsStore"""

    def test_store_and_query_metrics(self):
        """测试存储和查询指标"""
        store = MetricsStore({"max_metrics": 100, "retention_days": 7})

        # 创建测试指标
        metric1 = Metric(
            name="test.latency",
            value=100.0,
            metric_type=MetricType.LATENCY,
            tags={"endpoint": "/api/test"},
        )

        metric2 = Metric(
            name="test.throughput",
            value=50.0,
            metric_type=MetricType.THROUGHPUT,
            tags={"endpoint": "/api/test"},
        )

        # 存储指标
        store.store(metric1)
        store.store(metric2)

        # 查询所有指标
        all_metrics = store.query()
        assert len(all_metrics) == 2

        # 按类型查询
        latency_metrics = store.query(metric_type="latency")
        assert len(latency_metrics) == 1
        assert latency_metrics[0].name == "test.latency"

        # 按名称查询
        throughput_metrics = store.query(name="test.throughput")
        assert len(throughput_metrics) == 1
        assert throughput_metrics[0].metric_type == MetricType.THROUGHPUT

    def test_store_alerts(self):
        """测试存储告警"""
        store = MetricsStore({"max_metrics": 100, "retention_days": 7})

        metric = Metric(
            name="test.latency", value=100.0, metric_type=MetricType.LATENCY
        )

        alert = Alert(
            id="test_alert_1",
            severity=AlertSeverity.WARNING,
            message="High latency detected",
            metric=metric,
        )

        store.store_alert(alert)

        alerts = store.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].id == "test_alert_1"
        assert alerts[0].severity == AlertSeverity.WARNING

    def test_cleanup_old_metrics(self):
        """测试清理过期指标"""
        store = MetricsStore({"max_metrics": 100, "retention_days": 1})

        # 创建过期指标
        old_time = datetime.now() - timedelta(days=2)
        with patch(
            "src.loom.interpretation.performance_monitor.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = old_time
            old_metric = Metric(
                name="old.metric", value=1.0, metric_type=MetricType.LATENCY
            )
            store.store(old_metric)

        # 创建新指标
        new_metric = Metric(
            name="new.metric", value=2.0, metric_type=MetricType.LATENCY
        )
        store.store(new_metric)

        # 查询指标，应该只有新指标
        metrics = store.query()
        assert len(metrics) == 1
        assert metrics[0].name == "new.metric"


class TestAlertManager:
    """测试AlertManager"""

    def test_check_metric_triggers_alert(self):
        """测试指标触发告警"""
        config = {
            "alert_rules": [
                {
                    "name": "high_latency",
                    "condition": {
                        "metric_type": "latency",
                        "name": "api.latency",
                        "operator": ">",
                        "threshold": 1000,
                    },
                    "severity": "warning",
                    "message": "High latency: {metric_name}={metric_value}ms",
                }
            ]
        }

        manager = AlertManager(config)

        # 创建触发告警的指标
        metric = Metric(
            name="api.latency", value=1500.0, metric_type=MetricType.LATENCY  # 超过阈值
        )

        alerts = manager.check_metric(metric)
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.WARNING
        assert "High latency" in alerts[0].message

    def test_check_metric_no_alert(self):
        """测试指标不触发告警"""
        config = {
            "alert_rules": [
                {
                    "name": "high_latency",
                    "condition": {
                        "metric_type": "latency",
                        "operator": ">",
                        "threshold": 1000,
                    },
                    "severity": "warning",
                }
            ]
        }

        manager = AlertManager(config)

        # 创建不触发告警的指标
        metric = Metric(
            name="api.latency", value=500.0, metric_type=MetricType.LATENCY  # 低于阈值
        )

        alerts = manager.check_metric(metric)
        assert len(alerts) == 0


class TestPerformanceMonitor:
    """测试PerformanceMonitor"""

    def test_record_metrics(self):
        """测试记录指标"""
        config = {
            "enable_system_metrics": False,
            "enable_prometheus": False,
            "metrics_store": {"max_metrics": 100},
        }

        monitor = PerformanceMonitor(config)

        # 记录延迟指标
        monitor.record_latency("test.endpoint", 150.0, {"method": "GET"})

        # 记录吞吐量指标
        monitor.record_throughput("test.endpoint", 10.0, {"method": "GET"})

        # 获取指标
        metrics = monitor.get_metrics()
        assert len(metrics) >= 2

        # 验证指标类型
        latency_metrics = monitor.get_metrics(metric_type="latency")
        assert len(latency_metrics) >= 1

        throughput_metrics = monitor.get_metrics(metric_type="throughput")
        assert len(throughput_metrics) >= 1

    def test_get_performance_report(self):
        """测试获取性能报告"""
        config = {"enable_system_metrics": False, "enable_prometheus": False}

        monitor = PerformanceMonitor(config)

        # 记录一些指标
        for i in range(5):
            monitor.record_latency(f"test.endpoint.{i}", 100.0 + i * 10)

        # 获取报告
        report = monitor.get_performance_report()

        assert report.time_range is not None
        assert report.summary is not None
        assert "total_metrics" in report.summary
        assert report.metrics is not None
        assert report.alerts is not None
        assert report.recommendations is not None

    def test_global_instance(self):
        """测试全局实例"""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        # 应该是同一个实例
        assert monitor1 is monitor2


class TestBenchmarkFramework:
    """测试BenchmarkFramework"""

    @pytest.mark.asyncio
    async def test_register_and_run_benchmark(self):
        """测试注册和运行基准测试"""
        framework = BenchmarkFramework({"results_store": {"max_results": 10}})

        # 定义基准测试函数
        async def test_benchmark(params):
            await asyncio.sleep(0.01)  # 模拟工作
            return {"throughput": 100.0}

        # 注册基准测试
        framework.register_benchmark("test_benchmark", test_benchmark)

        # 运行基准测试
        result = await framework.run_benchmark(
            "test_benchmark", {"iterations": 3, "warmup_iterations": 1}
        )

        assert result.status == BenchmarkStatus.COMPLETED
        assert result.config.name == "test_benchmark"
        assert "latency_ms" in result.metrics
        assert len(result.metrics["latency_ms"]) == 3

    @pytest.mark.asyncio
    async def test_benchmark_comparison(self):
        """测试基准测试比较"""
        framework = BenchmarkFramework({"results_store": {"max_results": 10}})

        # 定义基准测试函数
        async def fast_benchmark(params):
            await asyncio.sleep(0.005)
            return {}

        async def slow_benchmark(params):
            await asyncio.sleep(0.015)
            return {}

        framework.register_benchmark("fast", fast_benchmark)
        framework.register_benchmark("slow", slow_benchmark)

        # 运行两个基准测试
        result1 = await framework.run_benchmark("fast", {"iterations": 2})
        result2 = await framework.run_benchmark("slow", {"iterations": 2})

        # 比较结果
        comparison = await framework.runner.compare(
            result1.benchmark_id, result2.benchmark_id
        )

        assert comparison.benchmark_a == result1
        assert comparison.benchmark_b == result2
        assert "latency_ms" in comparison.comparison_metrics

    def test_generate_report(self):
        """测试生成报告"""
        framework = BenchmarkFramework({"results_store": {"max_results": 10}})

        # 生成报告
        report = framework.generate_comprehensive_report(format="json")

        # 报告应该是有效的JSON
        import json

        report_data = json.loads(report)

        assert "generated_at" in report_data
        assert "total_benchmarks" in report_data
        assert "benchmarks" in report_data


class TestResourceAnalyzer:
    """测试ResourceAnalyzer"""

    @patch("psutil.Process")
    @patch("psutil.virtual_memory")
    def test_collect_memory_usage(self, mock_virtual_memory, mock_process):
        """测试收集内存使用情况"""
        # 模拟内存信息
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
        mock_memory_info.vms = 200 * 1024 * 1024
        mock_memory_info.shared = 10 * 1024 * 1024
        mock_memory_info.text = 5 * 1024 * 1024
        mock_memory_info.data = 20 * 1024 * 1024
        mock_memory_info.lib = 2 * 1024 * 1024
        mock_memory_info.dirty = 1 * 1024 * 1024

        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process.return_value = mock_process_instance

        # 模拟系统内存
        mock_system_memory = Mock()
        mock_system_memory.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_system_memory.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_system_memory.percent = 50.0
        mock_virtual_memory.return_value = mock_system_memory

        analyzer = ResourceAnalyzer(
            {"memory": {"enable_memory_tracking": False}, "collection_interval": 60}
        )

        resources = analyzer.collect_all_resources()

        assert "memory" in resources
        memory_usage = resources["memory"]
        assert memory_usage.resource_type == ResourceType.MEMORY
        assert memory_usage.usage_value > 0
        assert memory_usage.usage_percent is not None

    @patch("psutil.cpu_percent")
    @patch("psutil.Process")
    def test_collect_cpu_usage(self, mock_process, mock_cpu_percent):
        """测试收集CPU使用情况"""
        # 模拟CPU使用率
        mock_cpu_percent.side_effect = [25.0, 30.0]  # 进程, 系统

        mock_process_instance = Mock()
        mock_process_instance.cpu_percent.return_value = 25.0
        mock_process_instance.cpu_times.return_value = Mock(
            user=10.0, system=5.0, children_user=0.0, children_system=0.0
        )
        mock_process.return_value = mock_process_instance

        analyzer = ResourceAnalyzer(
            {"cpu": {"sampling_interval": 5}, "collection_interval": 60}
        )

        resources = analyzer.collect_all_resources()

        assert "cpu" in resources
        cpu_usage = resources["cpu"]
        assert cpu_usage.resource_type == ResourceType.CPU
        assert cpu_usage.usage_value == 25.0
        assert cpu_usage.usage_percent == 30.0

    def test_analyze_resource_issues(self):
        """测试分析资源问题"""
        analyzer = ResourceAnalyzer(
            {
                "memory": {
                    "high_memory_threshold": 10.0,  # 低阈值便于测试
                    "enable_memory_tracking": False,
                },
                "cpu": {"high_cpu_threshold": 10.0},  # 低阈值便于测试
                "collection_interval": 60,
            }
        )

        # 模拟高内存使用
        with patch.object(
            analyzer.memory_analyzer, "collect_memory_usage"
        ) as mock_memory:
            mock_memory.return_value = ResourceUsage(
                resource_type=ResourceType.MEMORY,
                usage_value=100 * 1024 * 1024,
                usage_percent=15.0,  # 超过阈值
                unit="bytes",
            )

            with patch.object(
                analyzer.memory_analyzer, "analyze_memory_leak"
            ) as mock_leak:
                mock_leak.return_value = None

                with patch.object(
                    analyzer.cpu_analyzer, "collect_cpu_usage"
                ) as mock_cpu:
                    mock_cpu.return_value = ResourceUsage(
                        resource_type=ResourceType.CPU,
                        usage_value=5.0,  # 低于阈值
                        usage_percent=20.0,
                        unit="percent",
                    )

                    issues = analyzer.analyze_resource_issues()

        # 应该检测到高内存使用问题
        assert len(issues) >= 1
        memory_issues = [
            i for i in issues if i.issue_type == ResourceIssueType.HIGH_MEMORY_USAGE
        ]
        assert len(memory_issues) >= 1

    def test_generate_analysis_report(self):
        """测试生成分析报告"""
        analyzer = ResourceAnalyzer({"collection_interval": 60, "max_history_size": 10})

        # 收集一些资源数据
        analyzer.collect_all_resources()

        # 生成报告
        report = analyzer.generate_analysis_report()

        assert report.time_range is not None
        assert report.resource_usage_summary is not None
        assert report.issues_detected is not None
        assert report.optimization_recommendations is not None
        assert report.trend_analysis is not None


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_monitor_benchmark_integration(self):
        """测试监控和基准测试集成"""
        # 获取性能监控器
        monitor = get_performance_monitor(
            {"enable_system_metrics": False, "enable_prometheus": False}
        )

        # 获取基准测试框架
        framework = get_benchmark_framework({"results_store": {"max_results": 10}})

        # 设置性能监控器
        framework.set_performance_monitor(monitor)

        # 定义基准测试函数
        async def integrated_benchmark(params):
            start_time = time.time()
            await asyncio.sleep(0.01)
            latency_ms = (time.time() - start_time) * 1000

            # 记录指标到监控器
            monitor.record_latency(
                "benchmark.latency", latency_ms, {"benchmark": "integrated_test"}
            )

            return {"latency_ms": latency_ms}

        # 注册并运行基准测试
        framework.register_benchmark("integrated_test", integrated_benchmark)
        result = await framework.run_benchmark("integrated_test", {"iterations": 2})

        assert result.status == BenchmarkStatus.COMPLETED

        # 验证监控器记录了指标
        metrics = monitor.get_metrics(name="benchmark.latency")
        assert len(metrics) >= 2  # 至少2次迭代的记录


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
