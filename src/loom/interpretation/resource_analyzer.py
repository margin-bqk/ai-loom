"""
资源使用分析器

实现资源使用分析、内存泄漏检测、CPU使用监控和优化建议。
支持资源使用分析和优化建议生成。
"""

import asyncio
import gc
import statistics
import threading
import time
import tracemalloc
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import objgraph
import psutil

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ResourceType(Enum):
    """资源类型"""

    MEMORY = "memory"  # 内存
    CPU = "cpu"  # CPU
    DISK = "disk"  # 磁盘
    NETWORK = "network"  # 网络
    THREAD = "thread"  # 线程
    FILE = "file"  # 文件句柄


class ResourceIssueType(Enum):
    """资源问题类型"""

    MEMORY_LEAK = "memory_leak"  # 内存泄漏
    HIGH_MEMORY_USAGE = "high_memory_usage"  # 高内存使用
    HIGH_CPU_USAGE = "high_cpu_usage"  # 高CPU使用
    DISK_SPACE_LOW = "disk_space_low"  # 磁盘空间不足
    THREAD_LEAK = "thread_leak"  # 线程泄漏
    FILE_HANDLE_LEAK = "file_handle_leak"  # 文件句柄泄漏


@dataclass
class ResourceUsage:
    """资源使用情况"""

    resource_type: ResourceType
    usage_value: float
    usage_percent: Optional[float] = None
    unit: str = "bytes"
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "resource_type": self.resource_type.value,
            "usage_value": self.usage_value,
            "usage_percent": self.usage_percent,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


@dataclass
class ResourceIssue:
    """资源问题"""

    issue_type: ResourceIssueType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    resource_usage: Optional[ResourceUsage] = None
    detected_at: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity,
            "description": self.description,
            "resource_usage": (
                self.resource_usage.to_dict() if self.resource_usage else None
            ),
            "detected_at": self.detected_at.isoformat(),
            "recommendations": self.recommendations,
        }


@dataclass
class ResourceAnalysisReport:
    """资源分析报告"""

    time_range: Tuple[datetime, datetime]
    resource_usage_summary: Dict[str, Any]
    issues_detected: List[ResourceIssue]
    optimization_recommendations: List[str]
    trend_analysis: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "time_range": {
                "start": self.time_range[0].isoformat(),
                "end": self.time_range[1].isoformat(),
            },
            "resource_usage_summary": self.resource_usage_summary,
            "issues_count": len(self.issues_detected),
            "issues_detected": [issue.to_dict() for issue in self.issues_detected],
            "optimization_recommendations": self.optimization_recommendations,
            "trend_analysis": self.trend_analysis,
        }


class MemoryAnalyzer:
    """内存分析器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.snapshot_interval = config.get("snapshot_interval", 60)  # 秒
        self.memory_leak_threshold = config.get("memory_leak_threshold", 10.0)  # MB/小时
        self.high_memory_threshold = config.get("high_memory_threshold", 80.0)  # 百分比

        # 内存使用历史
        self._memory_history: List[Tuple[datetime, float]] = []  # (时间戳, 内存使用MB)
        self._max_history_size = config.get("max_history_size", 1000)

        # 内存快照
        self._snapshots: List[Tuple[datetime, Any]] = []  # (时间戳, tracemalloc快照)
        self._max_snapshots = config.get("max_snapshots", 10)

        # 启用内存跟踪
        if config.get("enable_memory_tracking", False):
            tracemalloc.start()
            logger.info("Memory tracking enabled")

        logger.info(
            f"MemoryAnalyzer initialized with interval={self.snapshot_interval}s"
        )

    def collect_memory_usage(self) -> ResourceUsage:
        """收集内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            # 获取系统内存信息
            system_memory = psutil.virtual_memory()

            usage = ResourceUsage(
                resource_type=ResourceType.MEMORY,
                usage_value=memory_info.rss,  # 驻留集大小（字节）
                usage_percent=(memory_info.rss / system_memory.total) * 100,
                unit="bytes",
                details={
                    "rss_bytes": memory_info.rss,
                    "vms_bytes": memory_info.vms,
                    "shared_bytes": memory_info.shared,
                    "text_bytes": memory_info.text,
                    "data_bytes": memory_info.data,
                    "lib_bytes": memory_info.lib,
                    "dirty_bytes": memory_info.dirty,
                    "system_total_bytes": system_memory.total,
                    "system_available_bytes": system_memory.available,
                    "system_percent": system_memory.percent,
                },
            )

            # 记录历史
            self._record_memory_history(usage.usage_value / (1024 * 1024))  # 转换为MB

            return usage

        except Exception as e:
            logger.error(f"Error collecting memory usage: {e}")
            # 返回默认值
            return ResourceUsage(
                resource_type=ResourceType.MEMORY,
                usage_value=0,
                usage_percent=0,
                unit="bytes",
            )

    def _record_memory_history(self, memory_mb: float) -> None:
        """记录内存历史"""
        self._memory_history.append((datetime.now(), memory_mb))

        # 限制历史记录大小
        if len(self._memory_history) > self._max_history_size:
            self._memory_history.pop(0)

    def take_memory_snapshot(self) -> Optional[Any]:
        """获取内存快照"""
        try:
            if tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                self._snapshots.append((datetime.now(), snapshot))

                # 限制快照数量
                if len(self._snapshots) > self._max_snapshots:
                    self._snapshots.pop(0)

                return snapshot
        except Exception as e:
            logger.error(f"Error taking memory snapshot: {e}")

        return None

    def analyze_memory_leak(self) -> Optional[ResourceIssue]:
        """分析内存泄漏"""
        if len(self._memory_history) < 2:
            return None

        # 计算内存增长趋势
        times = [t for t, _ in self._memory_history]
        values = [v for _, v in self._memory_history]

        # 简单线性回归计算增长率
        if len(values) >= 2:
            time_delta_hours = (times[-1] - times[0]).total_seconds() / 3600
            if time_delta_hours > 0:
                memory_growth_mb = values[-1] - values[0]
                growth_rate_mb_per_hour = memory_growth_mb / time_delta_hours

                if growth_rate_mb_per_hour > self.memory_leak_threshold:
                    return ResourceIssue(
                        issue_type=ResourceIssueType.MEMORY_LEAK,
                        severity="high",
                        description=f"检测到内存泄漏：内存增长率为{growth_rate_mb_per_hour:.2f}MB/小时，"
                        f"超过阈值{self.memory_leak_threshold}MB/小时",
                        resource_usage=self.collect_memory_usage(),
                        recommendations=[
                            "检查循环引用",
                            "使用弱引用",
                            "分析内存快照找出泄漏对象",
                            "考虑使用内存分析工具如memory_profiler",
                        ],
                    )

        return None

    def analyze_high_memory_usage(self) -> Optional[ResourceIssue]:
        """分析高内存使用"""
        current_usage = self.collect_memory_usage()

        if (
            current_usage.usage_percent
            and current_usage.usage_percent > self.high_memory_threshold
        ):
            return ResourceIssue(
                issue_type=ResourceIssueType.HIGH_MEMORY_USAGE,
                severity="medium",
                description=f"高内存使用：当前使用{current_usage.usage_percent:.1f}%，"
                f"超过阈值{self.high_memory_threshold}%",
                resource_usage=current_usage,
                recommendations=[
                    "优化数据结构，减少内存占用",
                    "使用生成器代替列表",
                    "及时释放不再使用的对象",
                    "考虑使用内存缓存策略",
                ],
            )

        return None

    def compare_snapshots(
        self, snapshot1: Any, snapshot2: Any, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """比较两个内存快照"""
        try:
            if not snapshot1 or not snapshot2:
                return []

            top_stats = snapshot2.compare_to(snapshot1, "lineno")

            results = []
            for stat in top_stats[:limit]:
                results.append(
                    {
                        "size_diff_kb": stat.size_diff / 1024,
                        "count_diff": stat.count_diff,
                        "traceback": str(stat.traceback),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error comparing memory snapshots: {e}")
            return []

    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取内存统计"""
        if not self._memory_history:
            return {"history_count": 0}

        values = [v for _, v in self._memory_history]

        stats = {
            "history_count": len(values),
            "current_mb": values[-1] if values else 0,
            "min_mb": min(values) if values else 0,
            "max_mb": max(values) if values else 0,
            "avg_mb": statistics.mean(values) if len(values) > 1 else values[0],
            "growth_rate_mb_per_hour": 0.0,
        }

        # 计算增长率
        if len(values) >= 2:
            times = [t for t, _ in self._memory_history]
            time_delta_hours = (times[-1] - times[0]).total_seconds() / 3600
            if time_delta_hours > 0:
                memory_growth_mb = values[-1] - values[0]
                stats["growth_rate_mb_per_hour"] = memory_growth_mb / time_delta_hours

        return stats


class CPUAnalyzer:
    """CPU分析器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.high_cpu_threshold = config.get("high_cpu_threshold", 80.0)  # 百分比
        self.sampling_interval = config.get("sampling_interval", 5)  # 秒

        # CPU使用历史
        self._cpu_history: List[Tuple[datetime, float]] = []  # (时间戳, CPU使用率%)
        self._max_history_size = config.get("max_history_size", 1000)

        logger.info(
            f"CPUAnalyzer initialized with threshold={self.high_cpu_threshold}%"
        )

    def collect_cpu_usage(self) -> ResourceUsage:
        """收集CPU使用情况"""
        try:
            process = psutil.Process()

            # 获取进程CPU使用率
            process_cpu_percent = process.cpu_percent(interval=0.1)

            # 获取系统CPU使用率
            system_cpu_percent = psutil.cpu_percent(interval=0.1)

            usage = ResourceUsage(
                resource_type=ResourceType.CPU,
                usage_value=process_cpu_percent,
                usage_percent=system_cpu_percent,
                unit="percent",
                details={
                    "process_cpu_percent": process_cpu_percent,
                    "system_cpu_percent": system_cpu_percent,
                    "cpu_count": psutil.cpu_count(),
                    "cpu_freq": (
                        psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                    ),
                    "cpu_times": process.cpu_times()._asdict(),
                },
            )

            # 记录历史
            self._record_cpu_history(process_cpu_percent)

            return usage

        except Exception as e:
            logger.error(f"Error collecting CPU usage: {e}")
            return ResourceUsage(
                resource_type=ResourceType.CPU,
                usage_value=0,
                usage_percent=0,
                unit="percent",
            )

    def _record_cpu_history(self, cpu_percent: float) -> None:
        """记录CPU历史"""
        self._cpu_history.append((datetime.now(), cpu_percent))

        # 限制历史记录大小
        if len(self._cpu_history) > self._max_history_size:
            self._cpu_history.pop(0)

    def analyze_high_cpu_usage(self) -> Optional[ResourceIssue]:
        """分析高CPU使用"""
        current_usage = self.collect_cpu_usage()

        if current_usage.usage_value > self.high_cpu_threshold:
            return ResourceIssue(
                issue_type=ResourceIssueType.HIGH_CPU_USAGE,
                severity="medium",
                description=f"高CPU使用：进程使用{current_usage.usage_value:.1f}%，"
                f"超过阈值{self.high_cpu_threshold}%",
                resource_usage=current_usage,
                recommendations=[
                    "优化算法复杂度",
                    "使用异步IO减少阻塞",
                    "考虑使用多进程或多线程",
                    "分析性能热点使用profiler",
                ],
            )

        return None

    def get_cpu_statistics(self) -> Dict[str, Any]:
        """获取CPU统计"""
        if not self._cpu_history:
            return {"history_count": 0}

        values = [v for _, v in self._cpu_history]

        return {
            "history_count": len(values),
            "current_percent": values[-1] if values else 0,
            "min_percent": min(values) if values else 0,
            "max_percent": max(values) if values else 0,
            "avg_percent": statistics.mean(values) if len(values) > 1 else values[0],
            "trend": self._calculate_trend(values),
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return "stable"

        # 简单趋势判断
        recent_values = values[-min(10, len(values)) :]
        if len(recent_values) >= 2:
            first_half = statistics.mean(recent_values[: len(recent_values) // 2])
            second_half = statistics.mean(recent_values[len(recent_values) // 2 :])

            if second_half > first_half * 1.1:
                return "increasing"
            elif second_half < first_half * 0.9:
                return "decreasing"

        return "stable"


class DiskAnalyzer:
    """磁盘分析器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.low_disk_threshold = config.get("low_disk_threshold", 10.0)  # 百分比
        self.monitored_paths = config.get("monitored_paths", ["/"])

        logger.info(
            f"DiskAnalyzer initialized with threshold={self.low_disk_threshold}%"
        )

    def collect_disk_usage(self, path: str = "/") -> Optional[ResourceUsage]:
        """收集磁盘使用情况"""
        try:
            disk_usage = psutil.disk_usage(path)

            usage = ResourceUsage(
                resource_type=ResourceType.DISK,
                usage_value=disk_usage.used,
                usage_percent=disk_usage.percent,
                unit="bytes",
                details={
                    "total_bytes": disk_usage.total,
                    "used_bytes": disk_usage.used,
                    "free_bytes": disk_usage.free,
                    "path": path,
                    "percent": disk_usage.percent,
                },
            )

            return usage

        except Exception as e:
            logger.error(f"Error collecting disk usage for {path}: {e}")
            return None

    def analyze_low_disk_space(self) -> List[ResourceIssue]:
        """分析低磁盘空间"""
        issues = []

        for path in self.monitored_paths:
            usage = self.collect_disk_usage(path)
            if (
                usage
                and usage.usage_percent
                and usage.usage_percent > (100 - self.low_disk_threshold)
            ):
                issues.append(
                    ResourceIssue(
                        issue_type=ResourceIssueType.DISK_SPACE_LOW,
                        severity="high",
                        description=f"磁盘空间不足：{path} 使用{usage.usage_percent:.1f}%，"
                        f"剩余空间不足{self.low_disk_threshold}%",
                        resource_usage=usage,
                        recommendations=[
                            "清理临时文件",
                            "归档旧日志",
                            "扩展磁盘空间",
                            "使用磁盘配额管理",
                        ],
                    )
                )

        return issues

    def get_disk_statistics(self) -> Dict[str, Any]:
        """获取磁盘统计"""
        stats = {"paths": {}}

        for path in self.monitored_paths:
            usage = self.collect_disk_usage(path)
            if usage:
                stats["paths"][path] = {
                    "total_gb": usage.details.get("total_bytes", 0) / (1024**3),
                    "used_gb": usage.details.get("used_bytes", 0) / (1024**3),
                    "free_gb": usage.details.get("free_bytes", 0) / (1024**3),
                    "percent": usage.usage_percent,
                }

        return stats


class ThreadAnalyzer:
    """线程分析器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thread_leak_threshold = config.get("thread_leak_threshold", 50)

        # 线程历史
        self._thread_history: List[Tuple[datetime, int]] = []  # (时间戳, 线程数)
        self._max_history_size = config.get("max_history_size", 1000)

        logger.info(
            f"ThreadAnalyzer initialized with threshold={self.thread_leak_threshold}"
        )

    def collect_thread_usage(self) -> ResourceUsage:
        """收集线程使用情况"""
        try:
            process = psutil.Process()
            thread_count = process.num_threads()

            usage = ResourceUsage(
                resource_type=ResourceType.THREAD,
                usage_value=thread_count,
                unit="count",
                details={
                    "thread_count": thread_count,
                    "threads": self._get_thread_details(),
                },
            )

            # 记录历史
            self._record_thread_history(thread_count)

            return usage

        except Exception as e:
            logger.error(f"Error collecting thread usage: {e}")
            return ResourceUsage(
                resource_type=ResourceType.THREAD, usage_value=0, unit="count"
            )

    def _get_thread_details(self) -> List[Dict[str, Any]]:
        """获取线程详情"""
        try:
            import threading

            threads = []

            for thread in threading.enumerate():
                threads.append(
                    {
                        "name": thread.name,
                        "ident": thread.ident,
                        "is_alive": thread.is_alive(),
                        "is_daemon": thread.daemon,
                    }
                )

            return threads
        except Exception as e:
            logger.debug(f"Error getting thread details: {e}")
            return []

    def _record_thread_history(self, thread_count: int) -> None:
        """记录线程历史"""
        self._thread_history.append((datetime.now(), thread_count))

        # 限制历史记录大小
        if len(self._thread_history) > self._max_history_size:
            self._thread_history.pop(0)

    def analyze_thread_leak(self) -> Optional[ResourceIssue]:
        """分析线程泄漏"""
        if len(self._thread_history) < 2:
            return None

        current_count = self._thread_history[-1][1]

        # 检查线程数是否持续增长
        if len(self._thread_history) >= 10:
            recent_counts = [count for _, count in self._thread_history[-10:]]
            if all(
                recent_counts[i] < recent_counts[i + 1]
                for i in range(len(recent_counts) - 1)
            ):
                return ResourceIssue(
                    issue_type=ResourceIssueType.THREAD_LEAK,
                    severity="high",
                    description=f"检测到线程泄漏：线程数持续增长，当前{current_count}个线程",
                    resource_usage=self.collect_thread_usage(),
                    recommendations=[
                        "检查线程是否正确关闭",
                        "使用线程池管理线程",
                        "避免在循环中创建新线程",
                        "使用异步编程代替多线程",
                    ],
                )

        # 检查是否超过阈值
        if current_count > self.thread_leak_threshold:
            return ResourceIssue(
                issue_type=ResourceIssueType.THREAD_LEAK,
                severity="medium",
                description=f"高线程使用：当前{current_count}个线程，超过阈值{self.thread_leak_threshold}",
                resource_usage=self.collect_thread_usage(),
                recommendations=[
                    "优化线程使用",
                    "使用线程池限制最大线程数",
                    "检查是否有线程阻塞",
                ],
            )

        return None

    def get_thread_statistics(self) -> Dict[str, Any]:
        """获取线程统计"""
        if not self._thread_history:
            return {"history_count": 0}

        counts = [c for _, c in self._thread_history]

        return {
            "history_count": len(counts),
            "current_count": counts[-1] if counts else 0,
            "min_count": min(counts) if counts else 0,
            "max_count": max(counts) if counts else 0,
            "avg_count": statistics.mean(counts) if len(counts) > 1 else counts[0],
        }


class ResourceAnalyzer:
    """资源分析器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 初始化各资源分析器
        self.memory_analyzer = MemoryAnalyzer(config.get("memory", {}))
        self.cpu_analyzer = CPUAnalyzer(config.get("cpu", {}))
        self.disk_analyzer = DiskAnalyzer(config.get("disk", {}))
        self.thread_analyzer = ThreadAnalyzer(config.get("thread", {}))

        # 资源使用历史
        self._resource_history: List[Tuple[datetime, Dict[str, ResourceUsage]]] = []
        self._max_history_size = config.get("max_history_size", 1000)

        # 检测到的问题
        self._detected_issues: List[ResourceIssue] = []

        # 自动收集线程
        self._collection_thread: Optional[threading.Thread] = None
        self._running = False
        self._collection_interval = config.get("collection_interval", 60)  # 秒

        logger.info("ResourceAnalyzer initialized")

    def start_collection(self) -> None:
        """开始自动收集资源使用数据"""
        if self._running:
            return

        self._running = True
        self._collection_thread = threading.Thread(
            target=self._collection_loop, daemon=True
        )
        self._collection_thread.start()

        logger.info(
            f"Resource collection started with interval={self._collection_interval}s"
        )

    def stop_collection(self) -> None:
        """停止自动收集"""
        self._running = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5)

        logger.info("Resource collection stopped")

    def _collection_loop(self) -> None:
        """收集循环"""
        while self._running:
            try:
                self.collect_all_resources()
            except Exception as e:
                logger.error(f"Error in resource collection loop: {e}")

            time.sleep(self._collection_interval)

    def collect_all_resources(self) -> Dict[str, ResourceUsage]:
        """收集所有资源使用数据"""
        resources = {}

        # 收集内存使用
        resources["memory"] = self.memory_analyzer.collect_memory_usage()

        # 收集CPU使用
        resources["cpu"] = self.cpu_analyzer.collect_cpu_usage()

        # 收集磁盘使用
        disk_usages = {}
        for path in self.disk_analyzer.monitored_paths:
            usage = self.disk_analyzer.collect_disk_usage(path)
            if usage:
                disk_usages[path] = usage
        resources["disk"] = disk_usages

        # 收集线程使用
        resources["thread"] = self.thread_analyzer.collect_thread_usage()

        # 记录历史
        self._record_resource_history(resources)

        # 分析问题
        self._analyze_resources(resources)

        return resources

    def _record_resource_history(self, resources: Dict[str, Any]) -> None:
        """记录资源历史"""
        self._resource_history.append((datetime.now(), resources))

        # 限制历史记录大小
        if len(self._resource_history) > self._max_history_size:
            self._resource_history.pop(0)

    def _analyze_resources(self, resources: Dict[str, Any]) -> None:
        """分析资源问题"""
        # 分析内存问题
        memory_leak = self.memory_analyzer.analyze_memory_leak()
        if memory_leak:
            self._detected_issues.append(memory_leak)

        high_memory = self.memory_analyzer.analyze_high_memory_usage()
        if high_memory:
            self._detected_issues.append(high_memory)

        # 分析CPU问题
        high_cpu = self.cpu_analyzer.analyze_high_cpu_usage()
        if high_cpu:
            self._detected_issues.append(high_cpu)

        # 分析磁盘问题
        low_disk = self.disk_analyzer.analyze_low_disk_space()
        self._detected_issues.extend(low_disk)

        # 分析线程问题
        thread_leak = self.thread_analyzer.analyze_thread_leak()
        if thread_leak:
            self._detected_issues.append(thread_leak)

    def analyze_resource_issues(self) -> List[ResourceIssue]:
        """分析资源问题"""
        # 收集当前资源使用
        resources = self.collect_all_resources()

        # 分析问题
        self._analyze_resources(resources)

        # 返回检测到的问题
        issues = self._detected_issues.copy()
        self._detected_issues.clear()  # 清空已报告的问题

        return issues

    def generate_analysis_report(
        self, time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> ResourceAnalysisReport:
        """生成资源分析报告"""
        if time_range is None:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            time_range = (start_time, end_time)

        # 获取时间范围内的资源历史
        relevant_history = [
            (timestamp, resources)
            for timestamp, resources in self._resource_history
            if start_time <= timestamp <= end_time
        ]

        # 计算资源使用摘要
        resource_summary = self._calculate_resource_summary(relevant_history)

        # 获取检测到的问题
        issues = self.analyze_resource_issues()

        # 生成优化建议
        recommendations = self._generate_optimization_recommendations(
            issues, resource_summary
        )

        # 趋势分析
        trend_analysis = self._analyze_trends(relevant_history)

        return ResourceAnalysisReport(
            time_range=time_range,
            resource_usage_summary=resource_summary,
            issues_detected=issues,
            optimization_recommendations=recommendations,
            trend_analysis=trend_analysis,
        )

    def _calculate_resource_summary(
        self, history: List[Tuple[datetime, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """计算资源使用摘要"""
        if not history:
            return {"history_count": 0}

        summary = {
            "history_count": len(history),
            "time_range": {
                "start": history[0][0].isoformat(),
                "end": history[-1][0].isoformat(),
            },
        }

        # 添加各资源分析器的统计
        summary["memory"] = self.memory_analyzer.get_memory_statistics()
        summary["cpu"] = self.cpu_analyzer.get_cpu_statistics()
        summary["disk"] = self.disk_analyzer.get_disk_statistics()
        summary["thread"] = self.thread_analyzer.get_thread_statistics()

        return summary

    def _generate_optimization_recommendations(
        self, issues: List[ResourceIssue], summary: Dict[str, Any]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 从问题中提取建议
        for issue in issues:
            recommendations.extend(issue.recommendations)

        # 基于资源使用统计生成额外建议
        memory_stats = summary.get("memory", {})
        if memory_stats.get("growth_rate_mb_per_hour", 0) > 0:
            recommendations.append("内存持续增长，建议进行内存泄漏分析")

        cpu_stats = summary.get("cpu", {})
        if cpu_stats.get("avg_percent", 0) > 70:
            recommendations.append("CPU使用率较高，建议优化计算密集型操作")

        # 去重
        return list(dict.fromkeys(recommendations))

    def _analyze_trends(
        self, history: List[Tuple[datetime, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """分析趋势"""
        if len(history) < 2:
            return {"trend_analysis": "insufficient_data"}

        trends = {}

        # 分析内存趋势
        memory_values = []
        for _, resources in history:
            if "memory" in resources and isinstance(resources["memory"], ResourceUsage):
                memory_values.append(
                    resources["memory"].usage_value / (1024 * 1024)
                )  # MB

        if len(memory_values) >= 2:
            memory_growth = memory_values[-1] - memory_values[0]
            trends["memory_trend_mb_per_hour"] = memory_growth / (
                (history[-1][0] - history[0][0]).total_seconds() / 3600
            )

        # 分析CPU趋势
        cpu_values = []
        for _, resources in history:
            if "cpu" in resources and isinstance(resources["cpu"], ResourceUsage):
                cpu_values.append(resources["cpu"].usage_value)

        if cpu_values:
            trends["cpu_avg_percent"] = statistics.mean(cpu_values)
            trends["cpu_trend"] = "stable"
            if len(cpu_values) >= 10:
                first_half = statistics.mean(cpu_values[:5])
                second_half = statistics.mean(cpu_values[-5:])
                if second_half > first_half * 1.2:
                    trends["cpu_trend"] = "increasing"
                elif second_half < first_half * 0.8:
                    trends["cpu_trend"] = "decreasing"

        return trends

    def get_stats(self) -> Dict[str, Any]:
        """获取分析器统计"""
        return {
            "resource_history_count": len(self._resource_history),
            "detected_issues_count": len(self._detected_issues),
            "collection_running": self._running,
            "collection_interval": self._collection_interval,
            "memory_analyzer": self.memory_analyzer.get_memory_statistics(),
            "cpu_analyzer": self.cpu_analyzer.get_cpu_statistics(),
            "disk_analyzer": self.disk_analyzer.get_disk_statistics(),
            "thread_analyzer": self.thread_analyzer.get_thread_statistics(),
        }


# 全局ResourceAnalyzer实例
_global_resource_analyzer: Optional[ResourceAnalyzer] = None


def get_resource_analyzer(config: Optional[Dict[str, Any]] = None) -> ResourceAnalyzer:
    """获取全局ResourceAnalyzer实例"""
    global _global_resource_analyzer
    if _global_resource_analyzer is None:
        if config is None:
            config = {
                "collection_interval": 60,
                "max_history_size": 1000,
                "memory": {
                    "snapshot_interval": 60,
                    "memory_leak_threshold": 10.0,
                    "high_memory_threshold": 80.0,
                    "enable_memory_tracking": False,
                    "max_snapshots": 10,
                },
                "cpu": {
                    "high_cpu_threshold": 80.0,
                    "sampling_interval": 5,
                    "max_history_size": 1000,
                },
                "disk": {"low_disk_threshold": 10.0, "monitored_paths": ["/"]},
                "thread": {"thread_leak_threshold": 50, "max_history_size": 1000},
            }
        _global_resource_analyzer = ResourceAnalyzer(config)

    return _global_resource_analyzer
