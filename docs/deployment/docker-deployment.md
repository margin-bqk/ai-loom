# Docker Deployment

## 概述

LOOM 提供了完整的 Docker 部署方案，支持单容器部署和多容器编排。使用 Docker 可以快速部署 LOOM 应用及其依赖服务（数据库、缓存、监控等），确保环境一致性并简化部署流程。

## 前提条件

- Docker Engine 20.10+ 或 Docker Desktop 4.0+
- Docker Compose 2.0+（用于多容器部署）
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

## 快速开始

### 1. 构建 Docker 镜像

```bash
# 克隆仓库
git clone https://github.com/your-org/loom.git
cd loom

# 构建镜像
docker build -t loom:latest -t loom:0.10.0 .
```

### 2. 运行单容器应用

```bash
# 运行 LOOM 应用
docker run -d \
  --name loom-app \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  -e LOOM_LOG_LEVEL=INFO \
  loom:latest
```

### 3. 验证部署

```bash
# 检查容器状态
docker ps

# 查看日志
docker logs loom-app

# 测试 API 端点
curl http://localhost:8000/health
```

## Docker Compose 部署

LOOM 提供了完整的 `docker-compose.yml` 文件，支持以下服务：

- **loom**: LOOM 主应用
- **postgres**: PostgreSQL 数据库（可选）
- **redis**: Redis 缓存（可选）
- **prometheus**: Prometheus 监控
- **grafana**: Grafana 仪表板
- **nginx**: Nginx 反向代理（可选）

### 1. 基础部署（仅 LOOM 应用）

```bash
# 启动基础服务
docker-compose up loom

# 后台运行
docker-compose up -d loom
```

### 2. 完整部署（包含所有服务）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 环境配置

创建 `.env` 文件配置环境变量：

```env
# LOOM 配置
LOOM_LOG_LEVEL=INFO
LOOM_DATA_DIR=/app/data
LOOM_ENABLE_METRICS=true

# 数据库配置（如果使用 PostgreSQL）
POSTGRES_USER=loom
POSTGRES_PASSWORD=loom_password
POSTGRES_DB=loom_db

# API 密钥配置
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## 多环境部署

LOOM 支持多环境部署，为不同环境提供专门的 Docker Compose 配置文件：

### 1. 环境配置文件

| 环境 | Docker Compose 文件 | 环境变量文件 | 用途 |
|------|---------------------|--------------|------|
| **开发环境** | `docker-compose.yml` | `.env.development` | 本地开发和测试 |
| **预发布环境** | `docker-compose.staging.yml` | `.env.staging` | 集成测试和验证 |
| **生产环境** | `docker-compose.prod.yml` | `.env.production` | 线上生产部署 |

### 2. 使用部署脚本

使用 `deploy/deploy.sh` 脚本简化多环境部署：

```bash
# 启动开发环境
./deploy/deploy.sh development up

# 启动生产环境
./deploy/deploy.sh production up

# 启动预发布环境
./deploy/deploy.sh staging up

# 停止环境
./deploy/deploy.sh production down

# 查看日志
./deploy/deploy.sh staging logs

# 构建镜像
./deploy/deploy.sh development build

# 查看状态
./deploy/deploy.sh production status

# 更新服务
./deploy/deploy.sh production update

# 备份数据
./deploy/deploy.sh production backup
```

### 3. 环境配置差异

#### 开发环境 (`docker-compose.yml`)
- 使用本地目录挂载，便于开发调试
- 资源限制较宽松
- 启用详细日志
- 端口映射：8000:8000

#### 预发布环境 (`docker-compose.staging.yml`)
- 中等资源限制
- 包含 Jaeger 分布式追踪
- 启用调试端点
- 端口映射：8080:8000（避免与开发环境冲突）
- 7天数据保留期

#### 生产环境 (`docker-compose.prod.yml`)
- 严格的资源限制和健康检查
- 使用命名卷确保数据持久化
- 增强的安全配置
- 30天数据保留期
- 独立的网络配置

### 4. 手动部署命令

如果不使用部署脚本，可以手动指定配置文件：

```bash
# 开发环境
docker-compose -f docker-compose.yml --env-file .env.development up -d

# 生产环境
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# 预发布环境
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

### 5. 环境切换最佳实践

1. **开发到预发布**: 在预发布环境验证开发成果
2. **预发布到生产**: 通过预发布环境进行完整测试
3. **生产回滚**: 使用备份和回滚脚本
4. **数据迁移**: 使用导出/导入功能迁移数据

### 6. 环境特定配置示例

#### 生产环境 PostgreSQL 配置
```yaml
# docker-compose.prod.yml 中的 PostgreSQL 配置
postgres:
  command: >
    postgres
    -c max_connections=100
    -c shared_buffers=256MB
    -c effective_cache_size=768MB
    -c maintenance_work_mem=64MB
```

#### 预发布环境 Redis 配置
```yaml
# docker-compose.staging.yml 中的 Redis 配置
redis:
  command: >
    redis-server
    --appendonly yes
    --appendfsync everysec
    --save 900 1
    --save 300 10
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru
```

## Dockerfile 详解

LOOM 使用多阶段构建优化镜像大小：

```dockerfile
# 第一阶段：构建阶段
FROM python:3.12-slim as builder
# 安装系统依赖和 Python 包

# 第二阶段：运行阶段
FROM python:3.12-slim as runtime
# 复制依赖和应用代码
# 创建非 root 用户
# 配置健康检查
```

### 构建参数

支持以下构建参数：

```bash
# 指定 Python 版本
docker build --build-arg PYTHON_VERSION=3.12 -t loom:custom .

# 启用开发模式
docker build --build-arg DEV_MODE=true -t loom:dev .
```

## 数据持久化

### 挂载卷配置

```yaml
volumes:
  # 应用数据
  - ./data:/app/data

  # 配置文件
  - ./config:/app/config

  # 日志文件
  - ./logs:/app/logs

  # 典藏数据
  - ./canon:/app/canon
```

### 数据库数据持久化

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: ./postgres-data
      o: bind
```

## 网络配置

### 默认网络

Docker Compose 创建 `loom-network` 网络，所有服务通过此网络通信：

```yaml
networks:
  loom-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 自定义网络

```bash
# 创建自定义网络
docker network create loom-custom

# 在 Compose 中使用
docker-compose --project-name loom-custom up -d
```

## 健康检查

LOOM 容器配置了健康检查：

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.path.insert(0, '/app/src'); import loom; print('LOOM health check passed')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 手动检查

```bash
# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' loom-app

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' loom-app | jq
```

## 监控和日志

### 日志收集

```bash
# 查看实时日志
docker-compose logs -f loom

# 查看特定时间段的日志
docker-compose logs --since 10m loom

# 导出日志到文件
docker-compose logs loom > loom.log
```

### 监控端点

- **应用指标**: `http://localhost:8000/metrics`
- **健康检查**: `http://localhost:8000/health`
- **就绪检查**: `http://localhost:8000/ready`

## 生产环境配置

### 1. 安全加固

```dockerfile
# 使用非 root 用户
USER loom

# 只读文件系统（除数据目录）
RUN chmod -R 755 /app && \
    chown -R loom:loom /app/data /app/logs
```

### 2. 资源限制

```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

### 3. 重启策略

```yaml
restart: unless-stopped
# 或
restart: always
```

## 故障排除

### 常见问题

#### 1. 端口冲突

```bash
# 检查端口占用
netstat -tulpn | grep :8000

# 修改端口映射
docker run -p 8080:8000 loom:latest
```

#### 2. 权限问题

```bash
# 修复数据目录权限
sudo chown -R 1000:1000 data logs

# 或使用 Docker 卷
docker volume create loom-data
```

#### 3. 内存不足

```bash
# 增加 Docker 内存限制
# Docker Desktop: Settings -> Resources -> Memory
# Linux: 编辑 /etc/docker/daemon.json
```

#### 4. 构建失败

```bash
# 清理构建缓存
docker builder prune

# 使用无缓存构建
docker build --no-cache -t loom:latest .
```

### 调试命令

```bash
# 进入容器
docker exec -it loom-app bash

# 检查环境变量
docker exec loom-app env

# 查看进程
docker exec loom-app ps aux

# 测试网络连接
docker exec loom-app curl http://localhost:8000/health
```

## 最佳实践

### 1. 镜像管理

```bash
# 定期清理旧镜像
docker image prune -a --filter "until=24h"

# 使用特定标签
docker tag loom:latest loom:0.10.0
docker tag loom:latest loom:production
```

### 2. 数据备份

```bash
# 备份数据卷
docker run --rm -v loom-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/loom-data-$(date +%Y%m%d).tar.gz -C /data .

# 恢复数据
docker run --rm -v loom-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/loom-data-backup.tar.gz -C /data
```

### 3. 更新策略

```bash
# 滚动更新
docker-compose pull
docker-compose up -d --no-deps --build loom

# 蓝绿部署
docker-compose -p loom-blue up -d
# 切换流量后
docker-compose -p loom-green up -d
```

### 4. 安全扫描

```bash
# 扫描镜像漏洞
docker scan loom:latest

# 使用 Trivy
docker run --rm aquasec/trivy image loom:latest
```

## 扩展部署

### Kubernetes 部署

LOOM 也支持 Kubernetes 部署，详见 [Kubernetes 部署指南](../kubernetes/)。

### 云平台部署

- **AWS ECS**: 使用 `Dockerfile` 和 `docker-compose.yml`
- **Azure Container Instances**: 直接部署镜像
- **Google Cloud Run**: 无服务器容器部署

## 参考链接

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [LOOM 本地部署指南](./local-deployment.md)
- [LOOM 监控指南](./monitoring.md)
