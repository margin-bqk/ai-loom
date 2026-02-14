# Monitoring

## 概述

LOOM 提供了完整的监控解决方案，涵盖应用性能监控、系统资源监控、业务指标监控和告警管理。本文档详细介绍如何配置和使用 LOOM 的监控系统，包括 Prometheus、Grafana、以及内置的性能监控组件。

## 监控架构

LOOM 监控系统采用分层架构：

```
┌─────────────────────────────────────────────────────────┐
│                   可视化层 (Grafana)                     │
├─────────────────────────────────────────────────────────┤
│                   指标收集层 (Prometheus)                │
├─────────────────────────────────────────────────────────┤
│                   应用监控层 (LOOM Metrics)              │
├─────────────────────────────────────────────────────────┤
│                   系统资源层 (Node Exporter)             │
└─────────────────────────────────────────────────────────┘
```

### 组件说明

1. **LOOM 应用指标**: 内置的性能监控器，收集应用级指标
2. **Prometheus**: 时间序列数据库，用于指标收集和存储
3. **Grafana**: 数据可视化平台，提供监控仪表板
4. **Alertmanager**: 告警管理组件，处理告警通知
5. **Node Exporter**: 系统指标收集器（可选）

## 快速开始

### 1. 使用 Docker Compose 启动监控栈

```bash
# 启动完整的监控栈（包含 Prometheus 和 Grafana）
docker-compose up -d prometheus grafana

# 查看服务状态
docker-compose ps

# 访问监控界面
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (用户名: admin, 密码: admin)
```

### 2. 验证监控端点

```bash
# 检查 LOOM 健康状态
curl http://localhost:8000/health

# 查看 Prometheus 指标
curl http://localhost:8000/metrics

# 查看应用性能指标
curl http://localhost:8000/api/v1/metrics
```

## Prometheus 配置

### 1. 基本配置

LOOM 提供了默认的 Prometheus 配置。如果需要自定义，创建 `deploy/prometheus.yml`：

```yaml
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'loom'
    static_configs:
      - targets: ['loom:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

rule_files:
  - '/etc/prometheus/loom-alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### 2. 告警规则配置

创建 `deploy/prometheus-alerts.yml`：

```yaml
groups:
  - name: loom-alerts
    rules:
      - alert: LoomDown
        expr: up{job="loom"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "LOOM instance is down"
          description: "LOOM instance {{ $labels.instance }} has been down for more than 1 minute."

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on LOOM"
          description: "Error rate is above 5% for the last 5 minutes."

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on LOOM"
          description: "95th percentile latency is above 2 seconds."

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 512
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 512MB."
```

## Grafana 配置

### 1. 数据源配置

Grafana 会自动配置 Prometheus 数据源。如果需要手动配置：

1. 访问 http://localhost:3000
2. 登录（用户名: admin, 密码: admin）
3. 进入 Configuration → Data Sources
4. 添加 Prometheus 数据源：
   - URL: http://prometheus:9090
   - Access: Server (Default)

### 2. 仪表板导入

LOOM 提供了预配置的仪表板。导入步骤：

1. 进入 Dashboards → Import
2. 上传 `deploy/grafana-dashboards/loom-overview.json`
3. 选择 Prometheus 数据源
4. 点击 Import

### 3. 自定义仪表板

创建自定义仪表板监控关键指标：

| 面板类型 | 监控指标 | 用途 |
|----------|----------|------|
| **Stat** | `up{job="loom"}` | 服务状态 |
| **Graph** | `rate(http_requests_total[5m])` | 请求速率 |
| **Graph** | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | 95分位延迟 |
| **Gauge** | `process_resident_memory_bytes` | 内存使用 |
| **Table** | `loom_llm_requests_total` | LLM 请求统计 |

## LOOM 内置监控指标

### 1. 应用性能指标

LOOM 暴露以下 Prometheus 指标：

#### HTTP 请求指标
```
# 请求总数（按状态码分类）
http_requests_total{method="POST", endpoint="/api/v1/generate", status="200"}

# 请求延迟分布
http_request_duration_seconds_bucket{le="0.1", endpoint="/api/v1/generate"}
http_request_duration_seconds_sum
http_request_duration_seconds_count

# 当前活跃请求
http_requests_in_progress{endpoint="/api/v1/generate"}
```

#### LLM 相关指标
```
# LLM 请求统计
loom_llm_requests_total{provider="openai", model="gpt-4"}

# LLM 请求延迟
loom_llm_request_duration_seconds{provider="openai"}

# LLM 令牌使用
loom_llm_tokens_total{type="prompt"}
loom_llm_tokens_total{type="completion"}

# LLM 错误统计
loom_llm_errors_total{provider="openai", error_type="rate_limit"}
```

#### 内存和缓存指标
```
# 内存使用
process_resident_memory_bytes
process_virtual_memory_bytes

# 缓存命中率
loom_cache_hits_total{cache_type="response"}
loom_cache_misses_total{cache_type="response"}

# 会话统计
loom_sessions_active
loom_sessions_total
```

### 2. 业务指标

```
# 叙事生成统计
loom_narratives_generated_total{genre="fantasy"}
loom_narratives_words_total

# 用户交互统计
loom_user_interactions_total{interaction_type="edit"}
loom_user_satisfaction_score

# 规则执行统计
loom_rules_executed_total{rule_type="consistency"}
loom_rules_violations_total
```

### 3. 自定义指标

在代码中添加自定义指标：

```python
from prometheus_client import Counter, Histogram, Gauge

# 定义自定义指标
CUSTOM_REQUESTS = Counter('loom_custom_requests_total', 'Custom requests total')
CUSTOM_DURATION = Histogram('loom_custom_duration_seconds', 'Custom operation duration')
CUSTOM_ACTIVE = Gauge('loom_custom_active', 'Active custom operations')

# 使用指标
@CUSTOM_DURATION.time()
def custom_operation():
    CUSTOM_ACTIVE.inc()
    try:
        # 业务逻辑
        CUSTOM_REQUESTS.inc()
    finally:
        CUSTOM_ACTIVE.dec()
```

## Kubernetes 监控配置

### 1. ServiceMonitor 配置

使用 `kubernetes/monitoring.yaml` 配置 Prometheus Operator：

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: loom-monitor
  namespace: loom
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: loom
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
  namespaceSelector:
    matchNames:
    - loom
```

### 2. PodMonitor 配置（可选）

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: loom-pod-monitor
  namespace: loom
spec:
  selector:
    matchLabels:
      app: loom
  podMetricsEndpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### 3. 垂直 Pod 自动扩缩容 (VPA)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: loom-vpa
  namespace: loom
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: loom
  updatePolicy:
    updateMode: "Auto"
```

## 告警配置

### 1. Alertmanager 配置

创建 `deploy/alertmanager.yml`：

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'loom-alerts@example.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'team-email'

  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 10s

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@example.com'
        send_resolved: true

  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#alerts-critical'
```

### 2. 告警通知渠道

支持以下通知渠道：

- **Email**: 通过 SMTP 发送邮件告警
- **Slack**: 发送到 Slack 频道
- **Webhook**: 发送到自定义 Webhook 端点
- **PagerDuty**: 集成 PagerDuty
- **OpsGenie**: 集成 OpsGenie

### 3. 告警规则分类

| 严重级别 | 响应时间 | 通知渠道 | 示例告警 |
|----------|----------|----------|----------|
| **Critical** | 立即 | Slack, PagerDuty, Email | 服务宕机，数据丢失 |
| **Warning** | 30分钟内 | Email, Slack | 性能下降，资源使用率高 |
| **Info** | 24小时内 | Email | 配置变更，备份完成 |

## 性能监控最佳实践

### 1. 指标命名规范

遵循 Prometheus 指标命名最佳实践：

- 使用 `_total` 后缀表示计数器
- 使用 `_seconds` 后缀表示时间
- 使用 `_bytes` 后缀表示字节大小
- 使用 `namespace_metricname` 格式

### 2. 标签设计原则

```python
# 好的标签设计
http_requests_total{
  method="POST",
  endpoint="/api/v1/generate",
  status="200",
  instance="loom-1"
}

# 避免标签基数爆炸
# 错误：将用户ID作为标签
http_requests_total{user_id="12345"}
```

### 3. 采样频率优化

- 应用指标：30秒采样
- 系统指标：15秒采样
- 业务指标：1分钟采样
- 长期趋势：5分钟聚合

### 4. 存储保留策略

```yaml
# Prometheus 存储配置
storage:
  tsdb:
    retention:
      time: 15d  # 原始数据保留15天
    block_duration: 2h  # 块持续时间

# 长期存储（使用 Thanos 或 Cortex）
long_term_storage:
  retention: 1y
  downsampling:
    - interval: 5m
      retention: 30d
    - interval: 1h
      retention: 1y
```

## 故障排除

### 1. 常见问题

#### 指标无法访问

```bash
# 检查端点是否正常
curl http://localhost:8000/metrics

# 检查 Prometheus 目标状态
# 访问 http://localhost:9090/targets

# 检查网络策略
kubectl describe networkpolicy loom-network-policy
```

#### Grafana 无法显示数据

```bash
# 检查数据源连接
curl http://prometheus:9090/api/v1/query?query=up

# 检查服务发现
kubectl get endpoints -n monitoring

# 检查指标名称
curl http://localhost:8000/metrics | grep -i "http_requests"
```

#### 告警未触发

```bash
# 检查告警规则
curl http://localhost:9090/api/v1/rules

# 检查 Alertmanager 配置
curl http://alertmanager:9093/api/v1/alerts

# 检查告警表达式
curl http://localhost:9090/api/v1/query?query=up
```

### 2. 调试命令

```bash
# 查看 Prometheus 日志
docker-compose logs prometheus

# 查看应用指标
kubectl port-forward svc/loom 8000:8000
curl http://localhost:8000/metrics

# 测试告警规则
curl -X POST http://localhost:9090/api/v1/alerts -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "Test alert",
      "description": "This is a test alert"
    }
  }
]'
```

### 3. 性能优化

```bash
# 监控 Prometheus 自身性能
curl http://localhost:9090/metrics | grep prometheus

# 检查存储使用
du -sh prometheus_data/

# 优化查询性能
# 使用 recording rules 预计算复杂查询
# 使用 subquery 减少数据量
```

## 高级监控功能

### 1. 分布式追踪

集成 OpenTelemetry 进行分布式追踪：

```yaml
# 配置 OpenTelemetry
tracing:
  enabled: true
  exporter: jaeger
  endpoint: http://jaeger:14268/api/traces
  sampling_rate: 0.1
```

### 2. 日志聚合

使用 Loki 进行日志聚合：

```yaml
# Loki 配置
logging:
  enabled: true
  loki_url: http://loki:3100
  labels:
    app: loom
    namespace: loom
```

### 3. 实时分析

使用 Fluentd 和 Elasticsearch 进行日志分析：

```bash
# 部署 ELK 栈
docker-compose up -d elasticsearch kibana fluentd

# 配置日志收集
fluentd:
  config: |
    <source>
      @type forward
      port 24224
    </source>
    <match loom.**>
      @type elasticsearch
      host elasticsearch
      port 9200
      index_name loom
    </match>
```

### 4. 自定义监控插件

开发自定义监控插件：

```python
from loom.monitoring import BaseMonitorPlugin

class CustomMonitorPlugin(BaseMonitorPlugin):
    def collect_metrics(self):
        # 收集自定义指标
        return {
            'custom_metric': 42,
            'another_metric': {'value': 100, 'labels': {'type': 'test'}}
        }

    def check_health(self):
        # 健康检查逻辑
        return {'status': 'healthy', 'details': 'All systems operational'}
```

## 监控仪表板示例

### 1. 概览仪表板

监控关键业务指标：
- 服务可用性
- 请求速率和延迟
- 错误率
- 资源使用率

### 2. LLM 性能仪表板

监控 LLM 相关指标：
- 各提供商请求统计
- 令牌使用情况
- 响应时间
- 错误率和限流情况

### 3. 业务洞察仪表板

监控业务指标：
- 叙事生成统计
- 用户参与度
- 规则执行情况
- 内容质量指标

### 4. 系统健康仪表板

监控基础设施：
- 容器资源使用
- 节点健康状态
- 网络连接
- 存储使用情况

## 参考链接

- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
- [Prometheus 客户端库](https://github.com/prometheus/client_python)
- [Kubernetes 监控最佳实践](https://kubernetes.io/docs/concepts/cluster-administration/monitoring/)
- [LOOM 部署指南](./deployment-guide.md)
- [LOOM 故障排除指南](./troubleshooting.md)
