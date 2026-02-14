# LOOM v0.10.0 Docker 镜像
# 构建: docker build -t loom:0.10.0 -t loom:latest .
# 运行: docker run -p 8000:8000 loom:0.10.0

# 使用 Python 3.12 作为基础镜像（支持最新特性）
FROM python:3.12-slim as builder

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml README.md ./

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -e .[api,cli,vector]

# 第二阶段：运行阶段
FROM python:3.12-slim as runtime

WORKDIR /app

# 创建非 root 用户
RUN groupadd -r loom && useradd -r -g loom loom

# 复制 Python 依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/canon && \
    chown -R loom:loom /app

# 切换到非 root 用户
USER loom

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); import loom; print('LOOM health check passed')" || exit 1

# 运行命令
CMD ["uvicorn", "loom.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
