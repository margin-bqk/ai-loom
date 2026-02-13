"""
性能监控器

实现实时性能指标收集、监控告警、性能报告和趋势分析。
支持Prometheus/Grafana监控集成和REST API用于外部监控。
"""

import asyncio
import json
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import prometheus_client
import psutil
from prometheus_client import Counter, Gauge, Histogram, Summary

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """指标类型"""

    LATENCY = "latency"  # 延迟（毫秒）
    THROUGHPUT = "throughput"  # 吞吐量（请求/秒）
    ERROR_RATE = "error_rate"  # 错误率（百分比）
    MEMORY_USAGE = "memory_usage"  # 内存使用（MB）
    CPU_USAGE = "cpu_usage"  # CPU使用率（百分比）
    TOKEN_USAGE = "token_usage"  # 令牌使用量
    COST = "cost"  # 成本（美元）
    CUSTOM = "custom"  # 自定义指标


class AlertSeverity(Enum):
    """告警严重级别"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重


@dataclass
class Metric:
    """性能指标"""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class Alert:
    """告警"""

    id: str
    severity: AlertSeverity
    message: str
    metric: Optional[Metric] = None
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_resolved(self) -> bool:
        """是否已解决"""
        return self.resolved_at is not None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "message": self.message,
            "metric": self.metric.to_dict() if self.metric else None,
            "triggered_at": self.triggered_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata,
        }


@dataclass
class PerformanceReport:
    """性能报告"""

    time_range: Tuple[datetime, datetime]
    summary: Dict[str, Any]
    metrics: List[Metric]
    alerts: List[Alert]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "time_range": {
                "start": self.time_range[0].isoformat(),
                "end": self.time_range[1].isoformat(),
            },
            "summary": self.summary,
            "metrics_count": len(self.metrics),
            "alerts_count": len(self.alerts),
            "alerts": [alert.to_dict() for alert in self.alerts],
            "recommendations": self.recommendations,
        }


class MetricsStore:
    """指标存储"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_metrics = config.get("max_metrics", 10000)
        self.retention_days = config.get("retention_days", 7)

        # 内存存储
        self._metrics: List[Metric] = []
        self._alerts: List[Alert] = []
        self._lock = threading.RLock()

        # 索引
        self._metrics_by_type: Dict[str, List[Metric]] = defaultdict(list)
        self._metrics_by_name: Dict[str, List[Metric]] = defaultdict(list)

        logger.info(
            f"MetricsStore initialized with max_metrics={self.max_metrics}, retention_days={self.retention_days}"
        )

    def store(self, metric: Metric) -> None:
        """存储指标"""
        with self._lock:
            # 清理过期指标
            self._cleanup_old_metrics()

            # 检查存储限制
            if len(self._metrics) >= self.max_metrics:
                # 移除最旧的指标
                self._metrics.pop(0)

            # 存储指标
            self._metrics.append(metric)

            # 更新索引
            self._metrics_by_type[metric.metric_type.value].append(metric)
            self._metrics_by_name[metric.name].append(metric)

            logger.debug(
                f"Stored metric: {metric.name}={metric.value} ({metric.metric_type.value})"
            )

    def store_alert(self, alert: Alert) -> None:
        """存储告警"""
        with self._lock:
            self._alerts.append(alert)
            logger.debug(f"Stored alert: {alert.severity.value} - {alert.message}")

    def query(
        self,
        metric_type: Optional[str] = None,
        name: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[Metric]:
        """查询指标"""
        with self._lock:
            # 确定查询范围
            if metric_type and name:
                source_lists = [self._metrics_by_name.get(name, [])]
            elif metric_type:
                source_lists = [self._metrics_by_type.get(metric_type, [])]
            elif name:
                source_lists = [self._metrics_by_name.get(name, [])]
            else:
                source_lists = [self._metrics]

            # 合并结果
            results = []
            for metric_list in source_lists:
                for metric in metric_list:
                    # 时间范围过滤
                    if time_range:
                        if not (time_range[0] <= metric.timestamp <= time_range[1]):
                            continue

                    # 标签过滤
                    if tags:
                        if not all(metric.tags.get(k) == v for k, v in tags.items()):
                            continue

                    results.append(metric)

            return results

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        resolved: Optional[bool] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> List[Alert]:
        """获取告警"""
        with self._lock:
            results = []
            for alert in self._alerts:
                # 严重级别过滤
                if severity and alert.severity != severity:
                    continue

                # 解决状态过滤
                if resolved is not None:
                    if resolved != alert.is_resolved():
                        continue

                # 时间范围过滤
                if time_range:
                    if not (time_range[0] <= alert.triggered_at <= time_range[1]):
                        continue

                results.append(alert)

            return results

    def _cleanup_old_metrics(self) -> None:
        """清理过期指标"""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)

        with self._lock:
            # 清理主列表
            new_metrics = []
            for metric in self._metrics:
                if metric.timestamp >= cutoff_time:
                    new_metrics.append(metric)

            # 重建索引
            self._metrics = new_metrics
            self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        """重建索引"""
        self._metrics_by_type.clear()
        self._metrics_by_name.clear()

        for metric in self._metrics:
            self._metrics_by_type[metric.metric_type.value].append(metric)
            self._metrics_by_name[metric.name].append(metric)

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        with self._lock:
            return {
                "total_metrics": len(self._metrics),
                "total_alerts": len(self._alerts),
                "metrics_by_type": {
                    k: len(v) for k, v in self._metrics_by_type.items()
                },
                "metrics_by_name": {
                    k: len(v) for k, v in self._metrics_by_name.items()
                },
                "max_metrics": self.max_metrics,
                "retention_days": self.retention_days,
            }


class AlertManager:
    """告警管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules = config.get("alert_rules", [])
        self.notification_channels = config.get("notification_channels", [])

        # 告警规则缓存
        self._compiled_rules: List[Dict[str, Any]] = []
        self._compile_rules()

        logger.info(f"AlertManager initialized with {len(self.rules)} rules")

    def _compile_rules(self) -> None:
        """编译告警规则"""
        for rule in self.rules:
            compiled = {
                "name": rule.get("name", "unnamed_rule"),
                "condition": self._compile_condition(rule.get("condition", {})),
                "severity": AlertSeverity(rule.get("severity", "warning")),
                "message_template": rule.get("message", "Alert triggered"),
                "cooldown_seconds": rule.get("cooldown_seconds", 300),
            }
            self._compiled_rules.append(compiled)

    def _compile_condition(self, condition: Dict[str, Any]) -> Callable[[Metric], bool]:
        """编译条件函数"""
        metric_type = condition.get("metric_type")
        name = condition.get("name")
        operator = condition.get("operator", ">")
        threshold = condition.get("threshold", 0)
        duration_seconds = condition.get("duration_seconds", 0)

        def condition_func(metric: Metric) -> bool:
            # 类型和名称匹配
            if metric_type and metric.metric_type.value != metric_type:
                return False
            if name and metric.name != name:
                return False

            # 值比较
            if operator == ">":
                return metric.value > threshold
            elif operator == ">=":
                return metric.value >= threshold
            elif operator == "<":
                return metric.value < threshold
            elif operator == "<=":
                return metric.value <= threshold
            elif operator == "==":
                return metric.value == threshold
            elif operator == "!=":
                return metric.value != threshold
            else:
                return False

        return condition_func

    def check_metric(self, metric: Metric) -> List[Alert]:
        """检查指标是否触发告警"""
        alerts = []

        for rule in self._compiled_rules:
            try:
                if rule["condition"](metric):
                    # 创建告警
                    alert_id = f"{rule['name']}_{metric.name}_{int(time.time())}"
                    message = rule["message_template"].format(
                        metric_name=metric.name,
                        metric_value=metric.value,
                        threshold=rule.get("threshold", 0),
                    )

                    alert = Alert(
                        id=alert_id,
                        severity=rule["severity"],
                        message=message,
                        metric=metric,
                    )

                    alerts.append(alert)
                    logger.info(f"Alert triggered: {rule['name']} - {message}")
            except Exception as e:
                logger.error(f"Error checking rule {rule['name']}: {e}")

        return alerts

    def send_alert(self, alert: Alert) -> None:
        """发送告警通知"""
        for channel in self.notification_channels:
            try:
                if channel["type"] == "log":
                    self._send_log_alert(alert, channel)
                elif channel["type"] == "webhook":
                    self._send_webhook_alert(alert, channel)
                elif channel["type"] == "email":
                    self._send_email_alert(alert, channel)
                # 可以添加更多通知渠道
            except Exception as e:
                logger.error(
                    f"Error sending alert via {channel.get('type', 'unknown')}: {e}"
                )

    def _send_log_alert(self, alert: Alert, channel: Dict[str, Any]) -> None:
        """发送日志告警"""
        log_level = channel.get("log_level", "WARNING")
        log_message = f"[ALERT {alert.severity.value}] {alert.message}"

        if log_level == "ERROR":
            logger.error(log_message)
        elif log_level == "WARNING":
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def _send_webhook_alert(self, alert: Alert, channel: Dict[str, Any]) -> None:
        """发送Webhook告警"""
        # 这里应该实现实际的Webhook调用
        # 目前只是记录日志
        logger.info(
            f"Webhook alert would be sent to {channel.get('url', 'unknown')}: {alert.message}"
        )

    def _send_email_alert(self, alert: Alert, channel: Dict[str, Any]) -> None:
        """发送邮件告警"""
        # 这里应该实现实际的邮件发送
        # 目前只是记录日志
        logger.info(
            f"Email alert would be sent to {channel.get('recipients', 'unknown')}: {alert.message}"
        )


class SystemMetricsCollector:
    """系统指标收集器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collection_interval = config.get("collection_interval", 60)  # 秒
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[Metric], None]] = None

        logger.info(
            f"SystemMetricsCollector initialized with interval={self.collection_interval}s"
        )

    def start_collecting(self, callback: Callable[[Metric], None]) -> None:
        """开始收集指标"""
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        logger.info("SystemMetricsCollector started")

    def stop_collecting(self) -> None:
        """停止收集指标"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("SystemMetricsCollector stopped")

    def _collect_loop(self) -> None:
        """收集循环"""
        while self._running:
            try:
                self._collect_metrics()
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

            time.sleep(self.collection_interval)

    def _collect_metrics(self) -> None:
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        metric = Metric(
            name="system.cpu.usage",
            value=cpu_percent,
            metric_type=MetricType.CPU_USAGE,
            tags={"source": "system"},
        )
        self._callback(metric)

        # 内存使用
        memory = psutil.virtual_memory()
        metric = Metric(
            name="system.memory.usage",
            value=memory.percent,
            metric_type=MetricType.MEMORY_USAGE,
            tags={"source": "system"},
        )
        self._callback(metric)

        # 内存使用量（MB）
        metric = Metric(
            name="system.memory.used_mb",
            value=memory.used / (1024 * 1024),
            metric_type=MetricType.MEMORY_USAGE,
            tags={"source": "system", "unit": "MB"},
        )
        self._callback(metric)

        # 磁盘使用
        try:
            disk = psutil.disk_usage("/")
            metric = Metric(
                name="system.disk.usage",
                value=disk.percent,
                metric_type=MetricType.CUSTOM,
                tags={"source": "system", "mount": "/"},
            )
            self._callback(metric)
        except Exception as e:
            logger.debug(f"Could not collect disk metrics: {e}")


class PrometheusExporter:
    """Prometheus导出器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.port = config.get("port", 8000)
        self.metrics_prefix = config.get("metrics_prefix", "ai_loom_")

        # Prometheus指标
        self._latency_histogram = Histogram(
            f"{self.metrics_prefix}latency_seconds",
            "Request latency in seconds",
            ["endpoint", "method"],
        )

        self._throughput_counter = Counter(
            f"{self.metrics_prefix}requests_total",
            "Total number of requests",
            ["endpoint", "method", "status"],
        )

        self._error_rate_gauge = Gauge(
            f"{self.metrics_prefix}error_rate", "Error rate percentage", ["endpoint"]
        )

        self._memory_usage_gauge = Gauge(
            f"{self.metrics_prefix}memory_usage_bytes",
            "Memory usage in bytes",
            ["type"],
        )

        self._cpu_usage_gauge = Gauge(
            f"{self.metrics_prefix}cpu_usage_percent", "CPU usage percentage"
        )

        self._token_usage_counter = Counter(
            f"{self.metrics_prefix}tokens_total",
            "Total tokens used",
            ["provider", "model", "type"],
        )

        self._cost_counter = Counter(
            f"{self.metrics_prefix}cost_total",
            "Total cost in USD",
            ["provider", "model"],
        )

        logger.info(
            f"PrometheusExporter initialized with prefix={self.metrics_prefix}, port={self.port}"
        )

    def update_metric(self, metric: Metric) -> None:
        """更新Prometheus指标"""
        try:
            if metric.metric_type == MetricType.LATENCY:
                # 从毫秒转换为秒
                latency_seconds = metric.value / 1000.0
                endpoint = metric.tags.get("endpoint", "unknown")
                method = metric.tags.get("method", "unknown")
                self._latency_histogram.labels(
                    endpoint=endpoint, method=method
                ).observe(latency_seconds)

            elif metric.metric_type == MetricType.THROUGHPUT:
                endpoint = metric.tags.get("endpoint", "unknown")
                method = metric.tags.get("method", "unknown")
                status = metric.tags.get("status", "unknown")
                self._throughput_counter.labels(
                    endpoint=endpoint, method=method, status=status
                ).inc(metric.value)

            elif metric.metric_type == MetricType.ERROR_RATE:
                endpoint = metric.tags.get("endpoint", "unknown")
                self._error_rate_gauge.labels(endpoint=endpoint).set(metric.value)

            elif metric.metric_type == MetricType.MEMORY_USAGE:
                memory_type = metric.tags.get("type", "used")
                self._memory_usage_gauge.labels(type=memory_type).set(metric.value)

            elif metric.metric_type == MetricType.CPU_USAGE:
                self._cpu_usage_gauge.set(metric.value)

            elif metric.metric_type == MetricType.TOKEN_USAGE:
                provider = metric.tags.get("provider", "unknown")
                model = metric.tags.get("model", "unknown")
                token_type = metric.tags.get("type", "total")
                self._token_usage_counter.labels(
                    provider=provider, model=model, type=token_type
                ).inc(metric.value)

            elif metric.metric_type == MetricType.COST:
                provider = metric.tags.get("provider", "unknown")
                model = metric.tags.get("model", "unknown")
                self._cost_counter.labels(provider=provider, model=model).inc(
                    metric.value
                )

        except Exception as e:
            logger.error(f"Error updating Prometheus metric: {e}")

    def start_server(self) -> None:
        """启动Prometheus HTTP服务器"""
        try:
            prometheus_client.start_http_server(self.port)
            logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_store = MetricsStore(config.get("metrics_store", {}))
        self.alert_manager = AlertManager(config.get("alert_manager", {}))

        # 注册指标收集器
        self.collectors = []

        # 系统指标收集器
        if config.get("enable_system_metrics", True):
            system_collector = SystemMetricsCollector(config.get("system_metrics", {}))
            self.collectors.append(system_collector)

        # Prometheus导出器
        self.prometheus_exporter = None
        if config.get("enable_prometheus", False):
            self.prometheus_exporter = PrometheusExporter(config.get("prometheus", {}))

        # 启动监控
        self._start_monitoring()

        logger.info("PerformanceMonitor initialized")

    def _start_monitoring(self) -> None:
        """启动监控"""
        for collector in self.collectors:
            collector.start_collecting(self._handle_metric)

        # 启动Prometheus服务器
        if self.prometheus_exporter:
            self.prometheus_exporter.start_server()

        logger.info("Performance monitoring started")

    def _handle_metric(self, metric: Metric) -> None:
        """处理指标"""
        try:
            # 存储指标
            self.metrics_store.store(metric)

            # 更新Prometheus指标
            if self.prometheus_exporter:
                self.prometheus_exporter.update_metric(metric)

            # 检查告警条件
            alerts = self.alert_manager.check_metric(metric)
            for alert in alerts:
                self._handle_alert(alert)

        except Exception as e:
            logger.error(f"Error handling metric: {e}")

    def _handle_alert(self, alert: Alert) -> None:
        """处理告警"""
        try:
            # 存储告警
            self.metrics_store.store_alert(alert)

            # 发送告警通知
            self.alert_manager.send_alert(alert)

            logger.warning(
                f"Performance alert: {alert.severity.value} - {alert.message}"
            )

        except Exception as e:
            logger.error(f"Error handling alert: {e}")

    def record_latency(
        self, name: str, latency_ms: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录延迟指标"""
        metric = Metric(
            name=name, value=latency_ms, metric_type=MetricType.LATENCY, tags=tags or {}
        )
        self._handle_metric(metric)

    def record_throughput(
        self, name: str, count: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录吞吐量指标"""
        metric = Metric(
            name=name, value=count, metric_type=MetricType.THROUGHPUT, tags=tags or {}
        )
        self._handle_metric(metric)

    def record_error_rate(
        self, name: str, error_rate: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录错误率指标"""
        metric = Metric(
            name=name,
            value=error_rate,
            metric_type=MetricType.ERROR_RATE,
            tags=tags or {},
        )
        self._handle_metric(metric)

    def record_memory_usage(
        self, name: str, usage_mb: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录内存使用指标"""
        metric = Metric(
            name=name,
            value=usage_mb,
            metric_type=MetricType.MEMORY_USAGE,
            tags=tags or {},
        )
        self._handle_metric(metric)

    def record_cpu_usage(
        self, name: str, usage_percent: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录CPU使用率指标"""
        metric = Metric(
            name=name,
            value=usage_percent,
            metric_type=MetricType.CPU_USAGE,
            tags=tags or {},
        )
        self._handle_metric(metric)

    def record_token_usage(
        self, name: str, token_count: int, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录令牌使用量指标"""
        metric = Metric(
            name=name,
            value=float(token_count),
            metric_type=MetricType.TOKEN_USAGE,
            tags=tags or {},
        )
        self._handle_metric(metric)

    def record_cost(
        self, name: str, cost_usd: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录成本指标"""
        metric = Metric(
            name=name, value=cost_usd, metric_type=MetricType.COST, tags=tags or {}
        )
        self._handle_metric(metric)

    def record_custom_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录自定义指标"""
        metric = Metric(
            name=name, value=value, metric_type=MetricType.CUSTOM, tags=tags or {}
        )
        self._handle_metric(metric)

    def get_metrics(
        self,
        metric_type: Optional[str] = None,
        name: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[Metric]:
        """获取指标"""
        return self.metrics_store.query(metric_type, name, time_range, tags)

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        resolved: Optional[bool] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> List[Alert]:
        """获取告警"""
        return self.metrics_store.get_alerts(severity, resolved, time_range)

    def get_performance_report(
        self, time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> PerformanceReport:
        """获取性能报告"""
        if time_range is None:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            time_range = (start_time, end_time)

        # 获取指标
        metrics = self.get_metrics(time_range=time_range)

        # 获取告警
        alerts = self.get_alerts(time_range=time_range)

        # 计算统计摘要
        summary = self._calculate_summary(metrics)

        # 生成优化建议
        recommendations = self._generate_recommendations(metrics, alerts)

        return PerformanceReport(
            time_range=time_range,
            summary=summary,
            metrics=metrics,
            alerts=alerts,
            recommendations=recommendations,
        )

    def _calculate_summary(self, metrics: List[Metric]) -> Dict[str, Any]:
        """计算统计摘要"""
        if not metrics:
            return {"total_metrics": 0}

        # 按类型分组
        metrics_by_type = defaultdict(list)
        for metric in metrics:
            metrics_by_type[metric.metric_type.value].append(metric.value)

        summary = {
            "total_metrics": len(metrics),
            "metrics_by_type": {k: len(v) for k, v in metrics_by_type.items()},
        }

        # 计算每个类型的统计信息
        for metric_type, values in metrics_by_type.items():
            if values:
                summary[f"{metric_type}_avg"] = statistics.mean(values)
                summary[f"{metric_type}_min"] = min(values)
                summary[f"{metric_type}_max"] = max(values)
                if len(values) > 1:
                    summary[f"{metric_type}_std"] = statistics.stdev(values)

        return summary

    def _generate_recommendations(
        self, metrics: List[Metric], alerts: List[Alert]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 分析延迟指标
        latency_metrics = [m for m in metrics if m.metric_type == MetricType.LATENCY]
        if latency_metrics:
            avg_latency = statistics.mean([m.value for m in latency_metrics])
            if avg_latency > 1000:  # 超过1秒
                recommendations.append("高延迟检测：考虑优化网络连接或使用缓存")

        # 分析错误率
        error_metrics = [m for m in metrics if m.metric_type == MetricType.ERROR_RATE]
        if error_metrics:
            avg_error_rate = statistics.mean([m.value for m in error_metrics])
            if avg_error_rate > 5:  # 超过5%
                recommendations.append("高错误率：检查服务稳定性或重试机制")

        # 分析内存使用
        memory_metrics = [
            m for m in metrics if m.metric_type == MetricType.MEMORY_USAGE
        ]
        if memory_metrics:
            avg_memory = statistics.mean([m.value for m in memory_metrics])
            if avg_memory > 80:  # 超过80%
                recommendations.append("高内存使用：考虑内存优化或增加资源")

        # 分析告警
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        if critical_alerts:
            recommendations.append(f"有{len(critical_alerts)}个严重告警需要立即处理")

        return recommendations

    def get_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        return {
            "metrics_store": self.metrics_store.get_stats(),
            "collectors_count": len(self.collectors),
            "prometheus_enabled": self.prometheus_exporter is not None,
        }


# 全局PerformanceMonitor实例
_global_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(
    config: Optional[Dict[str, Any]] = None,
) -> PerformanceMonitor:
    """获取全局PerformanceMonitor实例"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        if config is None:
            config = {
                "enable_system_metrics": True,
                "enable_prometheus": False,
                "metrics_store": {"max_metrics": 10000, "retention_days": 7},
                "alert_manager": {
                    "alert_rules": [
                        {
                            "name": "high_latency",
                            "condition": {
                                "metric_type": "latency",
                                "operator": ">",
                                "threshold": 5000,  # 5秒
                            },
                            "severity": "warning",
                            "message": "高延迟检测：{metric_name}={metric_value}ms超过阈值{threshold}ms",
                        },
                        {
                            "name": "high_error_rate",
                            "condition": {
                                "metric_type": "error_rate",
                                "operator": ">",
                                "threshold": 10,  # 10%
                            },
                            "severity": "error",
                            "message": "高错误率：{metric_name}={metric_value}%超过阈值{threshold}%",
                        },
                    ],
                    "notification_channels": [{"type": "log", "log_level": "WARNING"}],
                },
            }
        _global_performance_monitor = PerformanceMonitor(config)

    return _global_performance_monitor
