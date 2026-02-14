# 本地部署

## 概述

本文档介绍如何在本地环境中部署 LOOM，包括单机部署、开发环境部署和测试环境部署。

## 部署选项

### 1. 基础单机部署
最简单的部署方式，适合个人使用和小型项目。

### 2. 开发环境部署
包含完整开发工具的部署，适合团队开发。

### 3. 测试环境部署
模拟生产环境的部署，用于测试和验证。

## 系统要求

### 最低配置
- **CPU**: 2 核心
- **内存**: 4GB RAM
- **存储**: 10GB 可用空间
- **操作系统**: Linux (Ubuntu 20.04+), macOS 10.15+, Windows 10/11

### 推荐配置
- **CPU**: 4 核心或更多
- **内存**: 8GB RAM 或更多
- **存储**: 50GB 可用空间（用于向量存储和日志）
- **操作系统**: Linux (Ubuntu 22.04 LTS)

### 网络要求
- 出站互联网访问（用于 LLM API）
- 本地网络访问（用于 Web 界面）
- 防火墙端口: 8000 (Web), 5432 (PostgreSQL, 可选)

## 基础单机部署

### 步骤 1: 准备环境

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# 或
brew update && brew upgrade            # macOS

# 安装 Python 3.10+
sudo apt install python3.10 python3.10-venv python3.10-dev -y

# 安装 Git
sudo apt install git -y

# 安装 SQLite（已包含在 Python 中）
# 安装其他工具
sudo apt install curl wget unzip -y
```

### 步骤 2: 获取代码

```bash
# 克隆仓库
git clone https://github.com/your-org/loom.git
cd loom

# 或下载发布版本
wget https://github.com/your-org/loom/releases/latest/download/loom.tar.gz
tar -xzf loom.tar.gz
cd loom
```

### 步骤 3: 创建虚拟环境

```bash
# 创建虚拟环境
python3.10 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 验证 Python 版本
python --version
```

### 步骤 4: 安装依赖

```bash
# 安装核心依赖
pip install -e .

# 或安装生产依赖
pip install -r requirements.txt

# 安装向量存储支持（可选）
pip install chromadb
```

### 步骤 5: 配置环境变量

```bash
# 创建环境文件
cp .env.example .env

# 编辑环境变量
vim .env  # 或使用其他编辑器
```

`.env` 文件配置示例：

```env
# 基础配置
LOOM_ENV=production
LOOM_LOG_LEVEL=INFO
LOOM_DATA_DIR=./data

# LLM 提供商配置
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# 数据库配置
LOOM_DB_TYPE=sqlite
LOOM_DB_PATH=./data/loom.db

# Web 服务器配置
LOOM_WEB_HOST=0.0.0.0
LOOM_WEB_PORT=8000
LOOM_WEB_WORKERS=4

# 安全配置
LOOM_SECRET_KEY=your-secret-key-here
LOOM_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 步骤 6: 初始化数据库

```bash
# 创建数据目录
mkdir -p data
mkdir -p logs

# 初始化数据库
loom init --force

# 或使用初始化脚本
python scripts/init_database.py
```

### 步骤 7: 启动服务

#### 选项 A: 使用 CLI 启动

```bash
# 启动 Web 服务器
loom web start

# 或直接运行
python -m loom.web.app
```

#### 选项 B: 使用 systemd 服务（Linux）

创建 `/etc/systemd/system/loom.service`:

```ini
[Unit]
Description=LOOM Narrative Engine
After=network.target

[Service]
Type=simple
User=loom
Group=loom
WorkingDirectory=/opt/loom
EnvironmentFile=/opt/loom/.env
ExecStart=/opt/loom/venv/bin/python -m loom.web.app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable loom
sudo systemctl start loom
sudo systemctl status loom
```

#### 选项 C: 使用 Supervisor（跨平台）

创建 `/etc/supervisor/conf.d/loom.conf`:

```ini
[program:loom]
command=/opt/loom/venv/bin/python -m loom.web.app
directory=/opt/loom
user=loom
autostart=true
autorestart=true
stderr_logfile=/var/log/loom/error.log
stdout_logfile=/var/log/loom/out.log
environment=LOOM_ENV="production"
```

### 步骤 8: 验证部署

```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查版本
curl http://localhost:8000/api/v1/version

# 测试 API
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "测试会话", "canon": "fantasy_basic"}'
```

## 开发环境部署

### 额外步骤 1: 安装开发工具

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装代码质量工具
pip install black flake8 isort mypy

# 安装测试工具
pip install pytest pytest-cov pytest-asyncio

# 安装文档工具
pip install mkdocs mkdocs-material
```

### 额外步骤 2: 配置开发环境

```bash
# 创建开发配置文件
cp config/default_config.yaml config/development.yaml

# 编辑开发配置
vim config/development.yaml
```

`config/development.yaml` 示例：

```yaml
environment: development

llm_providers:
  openai:
    enabled: true
    model: gpt-3.5-turbo  # 使用便宜模型开发

  ollama:
    enabled: true  # 启用本地模型测试

session:
  auto_save_interval: 1  # 频繁保存用于调试

logging:
  level: DEBUG  # 详细日志

monitoring:
  enabled: false  # 开发环境禁用监控
```

### 额外步骤 3: 启动开发服务器

```bash
# 使用热重载启动
loom web dev

# 或使用 uvicorn 开发服务器
uvicorn loom.web.app:app --reload --host 0.0.0.0 --port 8000

# 带调试信息
uvicorn loom.web.app:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 额外步骤 4: 运行测试套件

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_core/ -v

# 生成覆盖率报告
pytest --cov=src/loom --cov-report=html

# 运行集成测试
python scripts/test_runtime_integration.py
```

## 测试环境部署

### 额外步骤 1: 创建测试配置

```bash
# 创建测试配置文件
cp config/default_config.yaml config/testing.yaml

# 编辑测试配置
vim config/testing.yaml
```

`config/testing.yaml` 示例：

```yaml
environment: testing

llm_providers:
  openai:
    enabled: false  # 测试环境禁用真实 API

  mock:
    enabled: true
    type: mock
    responses:
      default: "这是一个测试响应"

session:
  persistence:
    enabled: false  # 测试环境禁用持久化

logging:
  level: INFO
  file: ./logs/test.log

testing:
  enabled: true
  mock_llm: true
  fast_fail: true
```

### 额外步骤 2: 设置测试数据库

```bash
# 使用内存数据库
export LOOM_DB_TYPE=sqlite
export LOOM_DB_PATH=:memory:

# 或使用临时文件
export LOOM_DB_PATH=/tmp/loom_test.db

# 初始化测试数据库
loom init --env testing
```

### 额外步骤 3: 运行测试环境

```bash
# 使用测试配置启动
LOOM_ENV=testing loom web start

# 或直接指定配置文件
loom --config config/testing.yaml web start
```

### 额外步骤 4: 自动化测试

```bash
# 创建测试脚本
cat > run_tests.sh << 'EOF'
#!/bin/bash
set -e

echo "=== 设置测试环境 ==="
export LOOM_ENV=testing
export LOOM_LOG_LEVEL=WARNING

echo "=== 运行单元测试 ==="
pytest tests/ -v --tb=short

echo "=== 运行集成测试 ==="
python scripts/test_runtime_integration.py

echo "=== 运行性能测试 ==="
python scripts/test_performance_benchmark.py --quick

echo "=== 所有测试通过 ==="
EOF

chmod +x run_tests.sh
./run_tests.sh
```

## 高级配置

### 1. 使用 PostgreSQL 数据库

```bash
# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE loom;
CREATE USER loom WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE loom TO loom;
\c loom
GRANT ALL ON SCHEMA public TO loom;
EOF

# 更新环境变量
echo "LOOM_DB_TYPE=postgresql" >> .env
echo "LOOM_DB_HOST=localhost" >> .env
echo "LOOM_DB_PORT=5432" >> .env
echo "LOOM_DB_NAME=loom" >> .env
echo "LOOM_DB_USER=loom" >> .env
echo "LOOM_DB_PASSWORD=your-password" >> .env

# 安装 PostgreSQL 驱动
pip install psycopg2-binary

# 初始化数据库
loom init --force
```

### 2. 配置 Redis 缓存

```bash
# 安装 Redis
sudo apt install redis-server -y

# 启动 Redis
sudo systemctl start redis
sudo systemctl enable redis

# 更新环境变量
echo "LOOM_CACHE_TYPE=redis" >> .env
echo "LOOM_CACHE_HOST=localhost" >> .env
echo "LOOM_CACHE_PORT=6379" >> .env
echo "LOOM_CACHE_DB=0" >> .env

# 安装 Redis 客户端
pip install redis

# 测试 Redis 连接
python -c "import redis; r = redis.Redis(); print(r.ping())"
```

### 3. 配置反向代理（Nginx）

创建 `/etc/nginx/sites-available/loom`:

```nginx
server {
    listen 80;
    server_name loom.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件缓存
    location /static/ {
        alias /opt/loom/src/loom/web/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 访问日志
    access_log /var/log/nginx/loom_access.log;
    error_log /var/log/nginx/loom_error.log;
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/loom /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. 配置 SSL/TLS（使用 Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d loom.your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

## 监控和日志

### 1. 配置日志轮转

创建 `/etc/logrotate.d/loom`:

```bash
/var/log/loom/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 loom loom
    sharedscripts
    postrotate
        systemctl reload loom > /dev/null 2>&1 || true
    endscript
}
```

### 2. 配置系统监控

```bash
# 安装监控工具
sudo apt install htop iotop iftop nmon -y

# 创建监控脚本
cat > monitor_loom.sh << 'EOF'
#!/bin/bash
echo "=== LOOM 系统监控 ==="
echo "时间: $(date)"
echo ""

echo "=== 进程状态 ==="
ps aux | grep loom | grep -v grep

echo ""
echo "=== 内存使用 ==="
free -h

echo ""
echo "=== 磁盘使用 ==="
df -h /opt/loom

echo ""
echo "=== 日志最后10行 ==="
tail -10 /var/log/loom/out.log
EOF

chmod +x monitor_loom.sh
```

### 3. 配置警报

```bash
# 创建健康检查脚本
cat > health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" -eq 200 ]; then
    echo "OK: LOOM 服务正常"
    exit 0
else
    echo "CRITICAL: LOOM 服务异常 (HTTP $RESPONSE)"
    # 发送警报
    curl -X POST https://api.alertservice.com/alerts \
      -d '{"service": "loom", "status": "critical"}'
    exit 1
fi
EOF

# 添加到 crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/loom/health_check.sh") | crontab -
```

## 备份和恢复

### 1. 数据库备份

```bash
# 创建备份脚本
cat > backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/loom/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/loom_db_$DATE.sql"

mkdir -p $BACKUP_DIR

if [ "$LOOM_DB_TYPE" = "sqlite" ]; then
    cp "$LOOM_DB_PATH" "$BACKUP_DIR/loom_db_$DATE.db"
    echo "SQLite 备份完成: $BACKUP_DIR/loom_db_$DATE.db"
elif [ "$LOOM_DB_TYPE" = "postgresql" ]; then
    pg_dump -h $LOOM_DB_HOST -U $LOOM_DB_USER $LOOM_DB_NAME > $BACKUP_FILE
    gzip $BACKUP_FILE
    echo "PostgreSQL 备份完成: $BACKUP_FILE.gz"
fi

# 清理旧备份（保留最近30天）
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x backup_database.sh
```

### 2. 会话数据备份

```bash
# 备份会话数据
cat > backup_sessions.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/loom/backups/sessions"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

# 导出所有会话
loom session list --format json | jq -c '.[]' | while read session; do
    SESSION_ID=$(echo $session | jq -r '.id')
    SESSION_NAME=$(echo $session | jq -r '.name')

    # 清理文件名中的特殊字符
    SAFE_NAME=$(echo $SESSION_NAME | tr -cd '[:alnum:]-_ ')

    loom session export \
      --session-id $SESSION_ID \
      --output "$BACKUP_DIR/${DATE}_${SAFE_NAME}.json" \
      --format json
done

echo "会话备份完成: $BACKUP_DIR"
EOF
```

### 3. 完整系统备份

```bash
# 完整系统备份
cat > full_backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/loom"
DATE=$(date +%Y%m%d)
FULL_BACKUP="$BACKUP_DIR/loom_full_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

# 停止服务
systemctl stop loom

# 创建备份
tar -czf $FULL_BACKUP \
  --exclude="venv" \
  --exclude="*.pyc" \
  --exclude="__pycache
