# LOOM 部署故障排除指南

本文档提供了 LOOM 部署过程中常见问题的解决方案和调试技巧。

## 快速诊断

### 1. 检查服务状态

```bash
# Docker
docker ps -a | grep loom
docker logs loom-app

# Kubernetes
kubectl get pods -n loom
kubectl logs deployment/loom -n loom

# 系统服务
systemctl status loom
```

### 2. 检查健康端点

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/metrics
```

### 3. 检查日志

```bash
# 查看实时日志
docker logs -f loom-app
kubectl logs -f deployment/loom -n loom

# 查看历史日志
journalctl -u loom.service --since "1 hour ago"
```

## 常见问题

### 1. 应用无法启动

**症状**: 容器不断重启，服务无法访问

**可能原因**:
- 端口冲突
- 依赖项缺失
- 配置错误
- 权限问题

**解决方案**:

```bash
# 检查端口占用
netstat -tulpn | grep :8000
lsof -i :8000

# 检查依赖项
docker run --rm loom:latest python -c "import loom; print('导入成功')"

# 检查配置
docker run --rm -e LOOM_LOG_LEVEL=DEBUG loom:latest

# 检查权限
docker run --rm -u root loom:latest ls -la /app/data
```

### 2. 数据库连接问题

**症状**: 应用启动但无法访问数据库

**可能原因**:
- 数据库文件权限错误
- 数据库损坏
- 存储空间不足

**解决方案**:

```bash
# 检查数据库文件
ls -la data/loom.db
sqlite3 data/loom.db "SELECT COUNT(*) FROM sessions;"

# 修复权限
chown -R 1000:1000 data/
chmod 755 data/

# 检查存储空间
df -h
du -sh data/
```

### 3. LLM API 连接失败

**症状**: 应用运行但无法调用 LLM 服务

**可能原因**:
- API 密钥错误或过期
- 网络连接问题
- 提供商服务不可用

**解决方案**:

```bash
# 测试 API 连接
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# 检查环境变量
echo $OPENAI_API_KEY
docker exec loom-app env | grep API

# 验证网络连接
docker exec loom-app curl -v https://api.openai.com
```

### 4. 内存不足

**症状**: 容器被 OOM 杀死，应用崩溃

**可能原因**:
- 内存限制过低
- 内存泄漏
- 向量存储占用过多内存

**解决方案**:

```bash
# 检查内存使用
docker stats loom-app
kubectl top pod -n loom

# 调整内存限制
# Docker: --memory=1g
# Kubernetes: resources.limits.memory

# 启用内存监控
export LOOM_ENABLE_METRICS=true
```

### 5. 性能问题

**症状**: 响应缓慢，高延迟

**可能原因**:
- 资源不足
- 数据库查询慢
- LLM 响应时间长

**解决方案**:

```bash
# 检查性能指标
curl http://localhost:8000/metrics | grep loom

# 分析慢查询
sqlite3 data/loom.db ".timer on" "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 10;"

# 启用性能分析
export LOOM_PERF_PROFILING=true
```

## 部署环境特定问题

### Docker 部署

#### 问题: 卷挂载失败
```bash
# 错误: Permission denied
# 解决方案: 使用正确的用户权限
docker run -v $(pwd)/data:/app/data:z -u 1000 loom:latest
```

#### 问题: 网络连接问题
```bash
# 错误: Cannot connect to the Docker daemon
# 解决方案: 确保 Docker 服务运行
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### Kubernetes 部署

#### 问题: Pod 处于 Pending 状态
```bash
# 检查事件
kubectl describe pod loom-xxxx -n loom

# 常见原因: 资源不足、节点选择器不匹配
kubectl get nodes
kubectl describe node <node-name>
```

#### 问题: Service 无法访问
```bash
# 检查服务类型和端口
kubectl get svc -n loom
kubectl describe svc loom-service -n loom

# 测试集群内访问
kubectl run test --rm -i --tty --image=busybox -- nslookup loom-service.loom
```

#### 问题: Ingress 配置错误
```bash
# 检查 Ingress 状态
kubectl get ingress -n loom
kubectl describe ingress loom-ingress -n loom

# 检查 Ingress 控制器日志
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

### 云部署

#### AWS ECS 问题
```bash
# 检查任务状态
aws ecs describe-tasks --cluster loom-cluster --tasks <task-id>

# 检查 CloudWatch 日志
aws logs get-log-events --log-group-name /ecs/loom --log-stream-name ecs/loom/xxxx
```

#### Azure AKS 问题
```bash
# 检查节点状态
az aks show --resource-group loom-rg --name loom-aks --query "agentPoolProfiles"

# 检查诊断日志
az monitor diagnostic-settings list --resource <resource-id>
```

#### GCP GKE 问题
```bash
# 检查集群状态
gcloud container clusters describe loom-cluster --zone us-central1-a

# 查看 Stackdriver 日志
gcloud logging read "resource.type=k8s_container AND resource.labels.cluster_name=loom-cluster"
```

## 监控和日志

### 配置日志级别

```bash
# 设置详细日志
export LOOM_LOG_LEVEL=DEBUG

# Docker
docker run -e LOOM_LOG_LEVEL=DEBUG loom:latest

# Kubernetes
kubectl set env deployment/loom LOOM_LOG_LEVEL=DEBUG -n loom
```

### 启用性能监控

```bash
# 启用 Prometheus metrics
export LOOM_ENABLE_METRICS=true

# 访问 metrics 端点
curl http://localhost:8001/metrics

# 关键指标
# loom_requests_total
# loom_request_duration_seconds
# loom_errors_total
# loom_memory_usage_bytes
```

### 日志收集

```bash
# 查看结构化日志
docker logs --tail 100 loom-app | jq '.'

# 搜索错误日志
kubectl logs deployment/loom -n loom | grep -i error

# 日志轮转配置
# 在 docker-compose.yml 中配置日志驱动
```

## 数据备份和恢复

### 备份数据库
```bash
# SQLite 备份
sqlite3 data/loom.db ".backup backup/loom-$(date +%Y%m%d).db"

# 完整数据备份
tar -czf backup/loom-data-$(date +%Y%m%d).tar.gz data/ canon/ config/
```

### 恢复数据
```bash
# 停止服务
docker stop loom-app

# 恢复数据库
cp backup/loom-20250101.db data/loom.db

# 恢复完整数据
tar -xzf backup/loom-data-20250101.tar.gz

# 重启服务
docker start loom-app
```

## 安全相关问题

### API 密钥泄露
1. 立即轮换所有 API 密钥
2. 检查日志中是否有异常访问
3. 更新 Kubernetes Secrets 或环境变量

### 未授权访问
1. 检查防火墙规则
2. 验证身份验证配置
3. 启用 TLS/SSL

### 依赖项漏洞
```bash
# 检查安全漏洞
safety check
pip-audit

# 更新依赖项
pip install --upgrade -r requirements.txt
```

## 性能调优

### 数据库优化
```bash
# 启用 WAL 模式
sqlite3 data/loom.db "PRAGMA journal_mode=WAL;"

# 创建索引
sqlite3 data/loom.db "CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);"

# 定期清理
sqlite3 data/loom.db "VACUUM;"
```

### 内存优化
```bash
# 调整向量存储设置
export LOOM_VECTOR_CACHE_SIZE=1000

# 限制并发请求
export LOOM_MAX_CONCURRENT_REQUESTS=10

# 启用内存监控
export LOOM_MEMORY_MONITORING=true
```

### 网络优化
```bash
# 调整连接池
export LOOM_HTTP_POOL_SIZE=10
export LOOM_HTTP_RETRY_COUNT=3

# 启用连接复用
export LOOM_HTTP_KEEPALIVE=true
```

## 紧急恢复步骤

### 1. 服务完全不可用
```bash
# 快速重启
docker-compose down && docker-compose up -d

# 或
kubectl rollout restart deployment/loom -n loom

# 检查状态
docker-compose ps
kubectl get pods -n loom
```

### 2. 数据损坏
```bash
# 从备份恢复
./scripts/rollback.py --backup backup/loom-data-latest.tar.gz

# 或手动恢复
cp backup/loom.db data/loom.db
chown 1000:1000 data/loom.db
```

### 3. 配置错误
```bash
# 回滚到上一个版本
git checkout v0.1.0
docker-compose up -d

# 或
kubectl rollout undo deployment/loom -n loom
```

## 获取帮助

### 内部资源
- [架构文档](ARCHITECTURE.md)
- [API 参考](API_REFERENCE.md)
- [部署指南](DEPLOYMENT_GUIDE.md)

### 外部资源
- [Docker 文档](https://docs.docker.com/)
- [Kubernetes 文档](https://kubernetes.io/docs/)
- [云提供商文档](https://docs.aws.amazon.com/)

### 支持渠道
- GitHub Issues: https://github.com/your-org/loom/issues
- Discord: https://discord.gg/loom
- 邮件: support@loom.dev

## 故障排除检查清单

1. [ ] 检查服务是否运行
2. [ ] 检查日志是否有错误
3. [ ] 验证健康端点
4. [ ] 检查资源使用情况
5. [ ] 验证网络连接
6. [ ] 检查配置是否正确
7. [ ] 验证依赖项状态
8. [ ] 检查安全设置

---

*最后更新: 2025-12-31*  
*版本: 1.0*