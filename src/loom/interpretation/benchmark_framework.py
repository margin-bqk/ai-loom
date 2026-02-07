"""
基准测试框架

实现标准化基准测试、性能对比、回归检测和报告生成。
支持自动化基准测试和性能对比分析。
"""

import asyncio
import time
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
from pathlib import Path
import yaml
from collections import defaultdict

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class BenchmarkType(Enum):
    """基准测试类型"""

    LATENCY = "latency"  # 延迟测试
    THROUGHPUT = "throughput"  # 吞吐量测试
    LOAD = "load"  # 负载测试
    STRESS = "stress"  # 压力测试
    ENDURANCE = "endurance"  # 耐久性测试
    FUNCTIONAL = "functional"  # 功能测试


class BenchmarkStatus(Enum):
    """基准测试状态"""

    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class BenchmarkConfig:
    """基准测试配置"""

    name: str
    benchmark_type: BenchmarkType
    iterations: int = 10
    warmup_iterations: int = 3
    concurrency: int = 1
    timeout_seconds: int = 300
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.benchmark_type.value,
            "iterations": self.iterations,
            "warmup_iterations": self.warmup_iterations,
            "concurrency": self.concurrency,
            "timeout_seconds": self.timeout_seconds,
            "parameters": self.parameters,
        }


@dataclass
class BenchmarkResult:
    """基准测试结果"""

    benchmark_id: str
    config: BenchmarkConfig
    status: BenchmarkStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: Dict[str, List[float]] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "benchmark_id": self.benchmark_id,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration(),
            "metrics_summary": self.get_summary(),
            "errors_count": len(self.errors),
            "metadata": self.metadata,
        }

    def get_duration(self) -> Optional[float]:
        """获取持续时间（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}

        for metric_name, values in self.metrics.items():
            if values:
                summary[f"{metric_name}_count"] = len(values)
                summary[f"{metric_name}_mean"] = statistics.mean(values)
                summary[f"{metric_name}_min"] = min(values)
                summary[f"{metric_name}_max"] = max(values)
                summary[f"{metric_name}_median"] = statistics.median(values)
                if len(values) > 1:
                    summary[f"{metric_name}_std"] = statistics.stdev(values)
                    summary[f"{metric_name}_p95"] = sorted(values)[
                        int(len(values) * 0.95)
                    ]
                    summary[f"{metric_name}_p99"] = sorted(values)[
                        int(len(values) * 0.99)
                    ]

        return summary


@dataclass
class ComparisonResult:
    """对比结果"""

    benchmark_a: BenchmarkResult
    benchmark_b: BenchmarkResult
    comparison_metrics: Dict[str, Dict[str, float]]
    regression_detected: bool = False
    regression_details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "benchmark_a": self.benchmark_a.benchmark_id,
            "benchmark_b": self.benchmark_b.benchmark_id,
            "comparison_metrics": self.comparison_metrics,
            "regression_detected": self.regression_detected,
            "regression_details": self.regression_details,
        }


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results_store = BenchmarkResultsStore(config.get("results_store", {}))
        self.performance_monitor = None  # 将在运行时注入

        logger.info("BenchmarkRunner initialized")

    def set_performance_monitor(self, performance_monitor):
        """设置性能监控器"""
        self.performance_monitor = performance_monitor

    async def run(
        self,
        benchmark_name: str,
        benchmark_func: Callable,
        config: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkResult:
        """运行基准测试"""
        # 合并配置
        merged_config = self.config.get("benchmarks", {}).get(benchmark_name, {})
        if config:
            merged_config.update(config)

        # 创建基准测试配置
        benchmark_config = BenchmarkConfig(
            name=benchmark_name,
            benchmark_type=BenchmarkType(merged_config.get("type", "latency")),
            iterations=merged_config.get("iterations", 10),
            warmup_iterations=merged_config.get("warmup_iterations", 3),
            concurrency=merged_config.get("concurrency", 1),
            timeout_seconds=merged_config.get("timeout_seconds", 300),
            parameters=merged_config.get("parameters", {}),
        )

        # 生成基准测试ID
        benchmark_id = self._generate_benchmark_id(benchmark_config)

        # 创建基准测试结果
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            config=benchmark_config,
            status=BenchmarkStatus.RUNNING,
            start_time=datetime.now(),
        )

        logger.info(f"Starting benchmark: {benchmark_name} (ID: {benchmark_id})")

        try:
            # 运行基准测试
            await self._execute_benchmark(result, benchmark_func)

            # 标记为完成
            result.status = BenchmarkStatus.COMPLETED
            result.end_time = datetime.now()

            logger.info(
                f"Benchmark completed: {benchmark_name} (duration: {result.get_duration():.2f}s)"
            )

        except asyncio.TimeoutError:
            result.status = BenchmarkStatus.FAILED
            result.end_time = datetime.now()
            result.errors.append(
                {
                    "type": "timeout",
                    "message": f"Benchmark timed out after {benchmark_config.timeout_seconds} seconds",
                }
            )
            logger.error(f"Benchmark timed out: {benchmark_name}")

        except Exception as e:
            result.status = BenchmarkStatus.FAILED
            result.end_time = datetime.now()
            result.errors.append(
                {
                    "type": "exception",
                    "message": str(e),
                    "exception_type": type(e).__name__,
                }
            )
            logger.error(f"Benchmark failed: {benchmark_name} - {e}")

        finally:
            # 存储结果
            self.results_store.store_result(result)

        return result

    async def _execute_benchmark(
        self, result: BenchmarkResult, benchmark_func: Callable
    ) -> None:
        """执行基准测试"""
        config = result.config

        # 预热阶段
        if config.warmup_iterations > 0:
            logger.info(f"Warmup phase: {config.warmup_iterations} iterations")
            for i in range(config.warmup_iterations):
                try:
                    await benchmark_func(config.parameters)
                except Exception as e:
                    logger.warning(f"Warmup iteration {i+1} failed: {e}")

        # 主测试阶段
        logger.info(f"Main test phase: {config.iterations} iterations")

        metrics = {
            "latency_ms": [],
            "throughput_rps": [],
            "memory_usage_mb": [],
            "cpu_usage_percent": [],
        }

        for i in range(config.iterations):
            try:
                # 记录开始时间
                start_time = time.time()

                # 执行基准测试函数
                iteration_result = await benchmark_func(config.parameters)

                # 记录结束时间
                end_time = time.time()

                # 计算延迟
                latency_ms = (end_time - start_time) * 1000
                metrics["latency_ms"].append(latency_ms)

                # 如果基准测试函数返回了额外指标，记录它们
                if isinstance(iteration_result, dict):
                    if "throughput" in iteration_result:
                        metrics["throughput_rps"].append(iteration_result["throughput"])
                    if "memory_usage" in iteration_result:
                        metrics["memory_usage_mb"].append(
                            iteration_result["memory_usage"]
                        )
                    if "cpu_usage" in iteration_result:
                        metrics["cpu_usage_percent"].append(
                            iteration_result["cpu_usage"]
                        )

                # 记录性能指标
                if self.performance_monitor:
                    self.performance_monitor.record_latency(
                        f"benchmark.{result.config.name}",
                        latency_ms,
                        {"iteration": str(i + 1), "benchmark_id": result.benchmark_id},
                    )

                logger.debug(f"Iteration {i+1}/{config.iterations}: {latency_ms:.2f}ms")

            except Exception as e:
                result.errors.append(
                    {
                        "iteration": i + 1,
                        "type": "iteration_error",
                        "message": str(e),
                        "exception_type": type(e).__name__,
                    }
                )
                logger.warning(f"Iteration {i+1} failed: {e}")

        # 更新结果指标
        result.metrics = {k: v for k, v in metrics.items() if v}

    def _generate_benchmark_id(self, config: BenchmarkConfig) -> str:
        """生成基准测试ID"""
        content = f"{config.name}:{config.benchmark_type.value}:{config.iterations}:{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    async def compare(
        self, benchmark_id_a: str, benchmark_id_b: str
    ) -> ComparisonResult:
        """比较两个基准测试结果"""
        result_a = self.results_store.get_result(benchmark_id_a)
        result_b = self.results_store.get_result(benchmark_id_b)

        if not result_a or not result_b:
            raise ValueError("One or both benchmark results not found")

        comparison_metrics = {}
        regression_detected = False
        regression_details = []

        # 比较每个指标
        for metric_name in set(result_a.metrics.keys()) | set(result_b.metrics.keys()):
            if metric_name in result_a.metrics and metric_name in result_b.metrics:
                values_a = result_a.metrics[metric_name]
                values_b = result_b.metrics[metric_name]

                if values_a and values_b:
                    mean_a = statistics.mean(values_a)
                    mean_b = statistics.mean(values_b)

                    # 计算变化百分比
                    if mean_a != 0:
                        change_percent = ((mean_b - mean_a) / mean_a) * 100
                    else:
                        change_percent = float("inf") if mean_b != 0 else 0

                    comparison_metrics[metric_name] = {
                        "mean_a": mean_a,
                        "mean_b": mean_b,
                        "change_percent": change_percent,
                        "improvement": change_percent < 0,  # 负值表示改进（降低延迟等）
                    }

                    # 检测回归（性能下降超过阈值）
                    regression_threshold = self.config.get(
                        "regression_threshold", 10.0
                    )  # 10%
                    if change_percent > regression_threshold:
                        regression_detected = True
                        regression_details.append(
                            f"{metric_name}: 性能下降 {change_percent:.1f}% "
                            f"(从 {mean_a:.2f} 到 {mean_b:.2f})"
                        )

        return ComparisonResult(
            benchmark_a=result_a,
            benchmark_b=result_b,
            comparison_metrics=comparison_metrics,
            regression_detected=regression_detected,
            regression_details=regression_details,
        )

    def generate_report(self, benchmark_id: str, format: str = "json") -> str:
        """生成基准测试报告"""
        result = self.results_store.get_result(benchmark_id)
        if not result:
            raise ValueError(f"Benchmark result not found: {benchmark_id}")

        if format == "json":
            return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        elif format == "yaml":
            return yaml.dump(result.to_dict(), allow_unicode=True)
        elif format == "text":
            return self._generate_text_report(result)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_text_report(self, result: BenchmarkResult) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"基准测试报告: {result.config.name}")
        lines.append("=" * 80)
        lines.append(f"基准测试ID: {result.benchmark_id}")
        lines.append(f"状态: {result.status.value}")
        lines.append(f"开始时间: {result.start_time}")
        lines.append(f"结束时间: {result.end_time}")
        lines.append(f"持续时间: {result.get_duration():.2f}秒")
        lines.append("")

        # 配置信息
        lines.append("配置信息:")
        lines.append(f"  类型: {result.config.benchmark_type.value}")
        lines.append(f"  迭代次数: {result.config.iterations}")
        lines.append(f"  预热次数: {result.config.warmup_iterations}")
        lines.append(f"  并发数: {result.config.concurrency}")
        lines.append("")

        # 指标摘要
        summary = result.get_summary()
        if summary:
            lines.append("指标摘要:")
            for key, value in summary.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # 错误信息
        if result.errors:
            lines.append(f"错误 ({len(result.errors)}个):")
            for error in result.errors:
                lines.append(
                    f"  - {error.get('type', 'unknown')}: {error.get('message', 'No message')}"
                )
            lines.append("")

        return "\n".join(lines)


class BenchmarkResultsStore:
    """基准测试结果存储"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_results = config.get("max_results", 100)
        self.retention_days = config.get("retention_days", 30)

        # 内存存储
        self._results: Dict[str, BenchmarkResult] = {}
        self._results_by_name: Dict[str, List[BenchmarkResult]] = defaultdict(list)

        # 持久化存储路径
        self.storage_path = Path(config.get("storage_path", "./benchmark_results"))
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"BenchmarkResultsStore initialized with max_results={self.max_results}, "
            f"retention_days={self.retention_days}"
        )

    def store_result(self, result: BenchmarkResult) -> None:
        """存储基准测试结果"""
        # 清理过期结果
        self._cleanup_old_results()

        # 检查存储限制
        if len(self._results) >= self.max_results:
            # 移除最旧的结果
            oldest_id = min(
                self._results.keys(), key=lambda k: self._results[k].start_time
            )
            del self._results[oldest_id]

        # 存储到内存
        self._results[result.benchmark_id] = result
        self._results_by_name[result.config.name].append(result)

        # 存储到文件
        self._save_to_file(result)

        logger.debug(f"Stored benchmark result: {result.benchmark_id}")

    def get_result(self, benchmark_id: str) -> Optional[BenchmarkResult]:
        """获取基准测试结果"""
        # 首先从内存获取
        if benchmark_id in self._results:
            return self._results[benchmark_id]

        # 尝试从文件加载
        return self._load_from_file(benchmark_id)

    def get_results_by_name(
        self, benchmark_name: str, limit: int = 10
    ) -> List[BenchmarkResult]:
        """按名称获取基准测试结果"""
        results = self._results_by_name.get(benchmark_name, [])
        results.sort(key=lambda r: r.start_time, reverse=True)
        return results[:limit]

    def get_all_results(self, limit: int = 50) -> List[BenchmarkResult]:
        """获取所有基准测试结果"""
        results = list(self._results.values())
        results.sort(key=lambda r: r.start_time, reverse=True)
        return results[:limit]

    def _cleanup_old_results(self) -> None:
        """清理过期结果"""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)

        # 清理内存中的过期结果
        expired_ids = []
        for benchmark_id, result in self._results.items():
            if result.start_time < cutoff_time:
                expired_ids.append(benchmark_id)

        for benchmark_id in expired_ids:
            del self._results[benchmark_id]

        # 清理按名称索引的过期结果
        for benchmark_name in list(self._results_by_name.keys()):
            self._results_by_name[benchmark_name] = [
                r
                for r in self._results_by_name[benchmark_name]
                if r.start_time >= cutoff_time
            ]
            if not self._results_by_name[benchmark_name]:
                del self._results_by_name[benchmark_name]

    def _save_to_file(self, result: BenchmarkResult) -> None:
        """保存结果到文件"""
        try:
            file_path = self.storage_path / f"{result.benchmark_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    result.to_dict(), f, indent=2, ensure_ascii=False, default=str
                )

            logger.debug(f"Saved benchmark result to file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save benchmark result to file: {e}")

    def _load_from_file(self, benchmark_id: str) -> Optional[BenchmarkResult]:
        """从文件加载结果"""
        try:
            file_path = self.storage_path / f"{benchmark_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 重新创建BenchmarkResult对象
            # 注意：这里简化了，实际应该完整反序列化
            # 为了简单起见，我们只返回None，让调用者处理
            logger.debug(f"Loaded benchmark result from file: {file_path}")
            return None  # 简化实现

        except Exception as e:
            logger.error(f"Failed to load benchmark result from file: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        return {
            "total_results": len(self._results),
            "results_by_name": {k: len(v) for k, v in self._results_by_name.items()},
            "max_results": self.max_results,
            "retention_days": self.retention_days,
            "storage_path": str(self.storage_path),
        }


class BenchmarkFramework:
    """基准测试框架"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.runner = BenchmarkRunner(config)
        self.registered_benchmarks: Dict[str, Callable] = {}

        logger.info("BenchmarkFramework initialized")

    def register_benchmark(self, name: str, benchmark_func: Callable) -> None:
        """注册基准测试"""
        self.registered_benchmarks[name] = benchmark_func
        logger.info(f"Registered benchmark: {name}")

    def set_performance_monitor(self, performance_monitor):
        """设置性能监控器"""
        self.runner.set_performance_monitor(performance_monitor)

    async def run_benchmark(
        self, name: str, config: Optional[Dict[str, Any]] = None
    ) -> BenchmarkResult:
        """运行基准测试"""
        if name not in self.registered_benchmarks:
            raise ValueError(f"Benchmark not registered: {name}")

        benchmark_func = self.registered_benchmarks[name]
        return await self.runner.run(name, benchmark_func, config)

    async def run_all_benchmarks(
        self, config_overrides: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, BenchmarkResult]:
        """运行所有注册的基准测试"""
        results = {}

        for name in self.registered_benchmarks:
            try:
                config = None
                if config_overrides and name in config_overrides:
                    config = config_overrides[name]

                result = await self.run_benchmark(name, config)
                results[name] = result

                logger.info(f"Completed benchmark: {name} - {result.status.value}")

            except Exception as e:
                logger.error(f"Failed to run benchmark {name}: {e}")
                # 创建失败结果
                results[name] = BenchmarkResult(
                    benchmark_id=f"failed_{name}_{int(time.time())}",
                    config=BenchmarkConfig(
                        name=name, benchmark_type=BenchmarkType.LATENCY
                    ),
                    status=BenchmarkStatus.FAILED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    errors=[{"type": "framework_error", "message": str(e)}],
                )

        return results

    async def compare_with_baseline(
        self, benchmark_name: str, baseline_id: str
    ) -> ComparisonResult:
        """与基线比较"""
        # 运行新的基准测试
        new_result = await self.run_benchmark(benchmark_name)

        # 获取基线结果
        baseline_result = self.runner.results_store.get_result(baseline_id)
        if not baseline_result:
            raise ValueError(f"Baseline result not found: {baseline_id}")

        # 比较
        return await self.runner.compare(baseline_id, new_result.benchmark_id)

    def detect_regressions(
        self, threshold_percent: float = 10.0
    ) -> List[Dict[str, Any]]:
        """检测回归"""
        regressions = []

        # 获取所有基准测试的最新结果
        all_results = self.runner.results_store.get_all_results(limit=100)

        # 按名称分组
        results_by_name = defaultdict(list)
        for result in all_results:
            results_by_name[result.config.name].append(result)

        # 对每个基准测试，比较最新两个结果
        for name, results in results_by_name.items():
            if len(results) >= 2:
                # 按时间排序，最新的在前
                sorted_results = sorted(
                    results, key=lambda r: r.start_time, reverse=True
                )
                latest = sorted_results[0]
                previous = sorted_results[1]

                try:
                    comparison = asyncio.run(
                        self.runner.compare(previous.benchmark_id, latest.benchmark_id)
                    )

                    if comparison.regression_detected:
                        regressions.append(
                            {
                                "benchmark_name": name,
                                "latest_id": latest.benchmark_id,
                                "previous_id": previous.benchmark_id,
                                "regression_details": comparison.regression_details,
                                "comparison_metrics": comparison.comparison_metrics,
                            }
                        )

                except Exception as e:
                    logger.error(f"Failed to compare results for {name}: {e}")

        return regressions

    def generate_comprehensive_report(self, format: str = "json") -> str:
        """生成综合报告"""
        all_results = self.runner.results_store.get_all_results()

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_benchmarks": len(self.registered_benchmarks),
            "total_results": len(all_results),
            "benchmarks": {},
            "recent_results": [],
            "regressions": self.detect_regressions(),
        }

        # 收集每个基准测试的最新结果
        for name in self.registered_benchmarks:
            results = self.runner.results_store.get_results_by_name(name, limit=1)
            if results:
                report["benchmarks"][name] = results[0].to_dict()

        # 收集最近的结果
        for result in all_results[:10]:  # 最近10个结果
            report["recent_results"].append(result.to_dict())

        if format == "json":
            return json.dumps(report, indent=2, ensure_ascii=False, default=str)
        elif format == "yaml":
            return yaml.dump(report, allow_unicode=True, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_stats(self) -> Dict[str, Any]:
        """获取框架统计"""
        return {
            "registered_benchmarks": list(self.registered_benchmarks.keys()),
            "results_store": self.runner.results_store.get_stats(),
        }


# 全局BenchmarkFramework实例
_global_benchmark_framework: Optional[BenchmarkFramework] = None


def get_benchmark_framework(
    config: Optional[Dict[str, Any]] = None,
) -> BenchmarkFramework:
    """获取全局BenchmarkFramework实例"""
    global _global_benchmark_framework
    if _global_benchmark_framework is None:
        if config is None:
            config = {
                "results_store": {
                    "max_results": 100,
                    "retention_days": 30,
                    "storage_path": "./benchmark_results",
                },
                "regression_threshold": 10.0,
                "benchmarks": {
                    "latency_test": {
                        "type": "latency",
                        "iterations": 10,
                        "warmup_iterations": 3,
                        "concurrency": 1,
                    },
                    "throughput_test": {
                        "type": "throughput",
                        "iterations": 5,
                        "warmup_iterations": 2,
                        "concurrency": 5,
                    },
                },
            }
        _global_benchmark_framework = BenchmarkFramework(config)

    return _global_benchmark_framework
