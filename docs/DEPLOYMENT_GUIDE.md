# LOOM 部署指南

本指南介绍如何将 LOOM 系统部署到不同环境，包括本地开发、生产服务器和云平台。

## 1. 部署选项概览

### 1.1 部署方式比较
| 方式 | 适用场景 | 复杂度 | 成本 | 推荐度 |
|------|----------|--------|------|--------|
| 本地运行 | 开发测试 | 低 | 低 | ★★★★★ |
| Docker | 生产环境 | 中 | 中 | ★★★★★ |
| Docker Compose | 多服务 | 中 | 中 | ★★★★☆ |
| Kubernetes | 大规模部署 | 高 | 高 | ★★★☆☆ |
| 云平台 | 托管服务 | 中 | 高 | ★★★★☆ |

### 1.2 系统要求
- **CPU**: 2+ 核心（推荐 4+）
- **内存**: 4GB+（推荐 8GB+）
- **存储**: 10GB+ 可用空间
- **网络**: 稳定的互联网连接（用于 LLM API）
- **操作系统**: Linux, macOS, Windows（WSL2 推荐）

## 2. 本地部署

### 2.1 基础安装
```bash
# 克隆仓库
git clone https://github.com/loom-project/loom.git
cd loom

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[all]"

# 初始化配置
loom config init
```

### 2.2 环境配置
```bash
# 复制环境变量
cp .env.example .env

# 编辑 .env 文件
nano .env

# 设置必要的 API 密钥
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite:///loom.db
```

### 2.3 启动服务
```bash
# 启动 Web UI
loom web start --host 0.0.0.0 --port 8000

# 或使用生产服务器
uvicorn src.loom.web.app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 3. Docker 部署

### 3.1 使用预构建镜像
```bash
# 拉取最新镜像
docker pull ghcr.io/loom-project/loom:latest

# 运行容器
docker run -d \
  --name loom \
  -p 8000:8000 \
  -v ./data:/app/data \
  -v ./config:/app/config \
  -e OPENAI_API_KEY=your_key_here \
  ghcr.io/loom-project/loom:latest
```

### 3.2 构建自定义镜像
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml .
COPY requirements.txt .
COPY src/ ./src/
COPY config/ ./config/

# 安装 Python 依赖
RUN pip install --no-cache-dir -e .

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV LOOM_DATA_DIR=/app/data
ENV LOOM_LOG_DIR=/app/logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.loom.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：
```bash
# 构建镜像
docker build -t loom:latest .

# 运行容器
docker run -d \
  --name loom-app \
  -p 8000:8000 \
  -v loom-data:/app/data \
  -v loom-logs:/app/logs \
  -e OPENAI_API_KEY=your_key \
  loom:latest
```

## 4. Docker Compose 部署

### 4.1 基础配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  loom:
    image: ghcr.io/loom-project/loom:latest
    container_name: loom
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/loom
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - loom-network

  db:
    image: postgres:15-alpine
    container_name: loom-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=loom
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - loom-network

  redis:
    image: redis:7-alpine
    container_name: loom-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data
    networks:
      - loom-network

  nginx:
    image: nginx:alpine
    container_name: loom-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - loom
    networks:
      - loom-network

volumes:
  postgres-data:
  redis-data:

networks:
  loom-network:
    driver: bridge
```

### 4.2 Nginx 配置
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream loom_backend {
        server loom:8000;
    }

    server {
        listen 80;
        server_name loom.example.com;
        
        # 重定向到 HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name loom.example.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://loom_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket 支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # 静态文件
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API 文档
        location /docs {
            proxy_pass http://loom_backend/docs;
        }

        # 健康检查
        location /health {
            proxy_pass http://loom_backend/health;
        }
    }
}
```

### 4.3 部署脚本
```bash
#!/bin/bash
# deploy.sh

set -e

echo "开始部署 LOOM..."

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 创建必要目录
mkdir -p data config logs ssl

# 生成 SSL 证书（自签名，生产环境请使用 Let's Encrypt）
if [ ! -f ssl/cert.pem ]; then
    echo "生成 SSL 证书..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem -out ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=loom.example.com"
fi

# 启动服务
echo "启动 Docker Compose 服务..."
docker-compose up -d

# 等待服务就绪
echo "等待服务启动..."
sleep 10

# 运行数据库迁移
echo "运行数据库迁移..."
docker-compose exec loom loom db migrate

# 检查服务状态
echo "检查服务状态..."
curl -f http://localhost:8000/health || {
    echo "服务健康检查失败"
    docker-compose logs loom
    exit 1
}

echo "部署完成！"
echo "访问地址: https://localhost"
echo "API 地址: https://localhost/api/v1"
echo "文档地址: https://localhost/docs"
```

## 5. Kubernetes 部署

### 5.1 部署清单
```yaml
# loom-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loom
  namespace: loom
spec:
  replicas: 3
  selector:
    matchLabels:
      app: loom
  template:
    metadata:
      labels:
        app: loom
    spec:
      containers:
      - name: loom
        image: ghcr.io/loom-project/loom:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: loom-secrets
              key: openai-api-key
        - name: DATABASE_URL
          value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@loom-postgres:5432/loom"
        envFrom:
        - configMapRef:
            name: loom-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
# Service
apiVersion: v1
kind: Service
metadata:
  name: loom-service
  namespace: loom
spec:
  selector:
    app: loom
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
# Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: loom-ingress
  namespace: loom
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: loom.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: loom-service
            port:
              number: 80
```

### 5.2 配置和密钥
```yaml
# loom-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: loom-config
  namespace: loom
data:
  LOG_LEVEL: "INFO"
  CACHE_ENABLED: "true"
  MAX_SESSIONS: "100"
---
# loom-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: loom-secrets
  namespace: loom
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  anthropic-api-key: <base64-encoded-key>
  database-password: <base64-encoded-password>
```

### 5.3 部署命令
```bash
# 创建命名空间
kubectl create namespace loom

# 应用配置
kubectl apply -f loom-configmap.yaml -n loom
kubectl apply -f loom-secrets.yaml -n loom

# 部署应用
kubectl apply -f loom-deployment.yaml -n loom

# 检查状态
kubectl get all -n loom
kubectl get pods -n loom
```

## 6. 云平台部署

### 6.1 AWS ECS
```json
{
  "family": "loom",
  "taskRoleArn": "arn:aws:iam::123456789012:role/loom-task-role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecs-task-execution-role",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "loom",
      "image": "ghcr.io/loom-project/loom:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-key-here"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:ssm:region:account-id:parameter/loom/database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/loom",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024"
}
```

### 6.2 Google Cloud Run
```bash
# 构建和推送镜像
gcloud builds submit --tag gcr.io/PROJECT-ID/loom

# 部署到 Cloud Run
gcloud run deploy loom \
  --image gcr.io/PROJECT-ID/loom \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="OPENAI_API_KEY=your-key" \
  --memory 1Gi \
  --cpu 1
```

### 6.3 Azure Container Instances
```bash
# 创建容器实例
az container create \
  --resource-group loom-rg \
  --name loom-container \
  --image ghcr.io/loom-project/loom:latest \
  --ports 8000 \
  --environment-variables \
    OPENAI_API_KEY=your-key \
    DATABASE_URL=your-db-url \
  --memory 1.5 \
  --cpu 1.0
```

## 7. 数据库配置

### 7.1 PostgreSQL 设置
```sql
-- 创建数据库和用户
CREATE DATABASE loom;
CREATE USER loom_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE loom TO loom_user;

-- 创建扩展（如果需要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### 7.2 数据库迁移
```bash
# 初始化数据库
loom db init

# 运行迁移
loom db migrate

# 创建备份
loom db backup --output backup_$(date +%Y%m%d).sql

# 恢复备份
loom db restore --file backup_20241230.sql
```

## 8. 监控和日志

### 8.1 监控配置
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'loom'
    static_configs:
      - targets: ['loom:8000']
    metrics_path: '/metrics'
```

### 8.2 日志收集
```bash
# 使用 ELK Stack
docker-compose -f elk-stack.yml up -d

# 配置日志驱动
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 8.3 健康检查端点
```bash
# 检查服务健康
curl http://localhost:8000/health

# 检查数据库连接
curl http://localhost:8000/health/db

# 检查外部服务
curl http://localhost:8000/health/external
```

## 9. 安全配置

### 9.1 SSL/TLS 配置
```bash
# 使用 Let's Encrypt
certbot certonly --nginx -d loom.example.com

# 自动续期
certbot renew --quiet
```

### 9.2 防火墙规则
```bash
# 只开放必要端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
```

### 9.3 访问控制
```yaml
# 配置 API 密钥认证
security:
  api_keys:
    - name: "admin"
      key: "secure-api-key-here"
      permissions: ["read", "write", "admin"]
    - name: "user"
      key: "user-api-key-here"
      permissions: ["read", "write"]
```

## 10. 备份和恢复

### 10.1 备份脚本
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/loom"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose exec db pg_dump -U postgres loom > $BACKUP_DIR/db_