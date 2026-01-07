#!/bin/bash
# LOOM 部署脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 LOOM 部署脚本${NC}"

# 检查参数
ENV=${1:-"development"}
ACTION=${2:-"up"}

case $ENV in
    development|dev)
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.development"
        ;;
    production|prod)
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.production"
        ;;
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        ENV_FILE=".env.staging"
        ;;
    *)
        echo -e "${RED}错误: 未知环境 '$ENV'${NC}"
        echo "用法: $0 [development|production|staging] [up|down|build|logs]"
        exit 1
        ;;
esac

# 检查环境文件
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}警告: 环境文件 $ENV_FILE 不存在${NC}"
    echo "创建示例环境文件..."
    cp .env.example "$ENV_FILE"
    echo -e "${YELLOW}请编辑 $ENV_FILE 配置环境变量${NC}"
fi

# 执行 Docker Compose 命令
case $ACTION in
    up)
        echo -e "${GREEN}启动 $ENV 环境...${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        ;;
    down)
        echo -e "${YELLOW}停止 $ENV 环境...${NC}"
        docker-compose -f "$COMPOSE_FILE" down
        ;;
    build)
        echo -e "${GREEN}构建 $ENV 环境...${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build
        ;;
    logs)
        echo -e "${GREEN}查看 $ENV 环境日志...${NC}"
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    restart)
        echo -e "${YELLOW}重启 $ENV 环境...${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
        ;;
    status)
        echo -e "${GREEN}$ENV 环境状态:${NC}"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    update)
        echo -e "${GREEN}更新 $ENV 环境...${NC}"
        docker-compose -f "$COMPOSE_FILE" pull
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
        ;;
    backup)
        echo -e "${GREEN}备份 $ENV 环境数据...${NC}"
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # 备份数据库
        if docker-compose -f "$COMPOSE_FILE" ps postgres 2>/dev/null | grep -q "Up"; then
            echo "备份 PostgreSQL..."
            docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U loom loom_db > "$BACKUP_DIR/loom_db.sql"
        fi
        
        # 备份数据目录
        if [ -d "data" ]; then
            echo "备份数据目录..."
            tar -czf "$BACKUP_DIR/data.tar.gz" data/
        fi
        
        echo -e "${GREEN}备份完成: $BACKUP_DIR${NC}"
        ;;
    *)
        echo -e "${RED}错误: 未知操作 '$ACTION'${NC}"
        echo "用法: $0 [environment] [up|down|build|logs|restart|status|update|backup]"
        exit 1
        ;;
esac

# 显示状态
if [ "$ACTION" = "up" ] || [ "$ACTION" = "restart" ] || [ "$ACTION" = "update" ]; then
    echo ""
    echo -e "${GREEN}✅ 部署完成!${NC}"
    echo ""
    echo -e "${YELLOW}服务状态:${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo -e "${YELLOW}访问地址:${NC}"
    echo "  LOOM Web UI: http://localhost:8000"
    echo "  API 文档: http://localhost:8000/api/docs"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000 (admin/admin)"
    
    echo ""
    echo -e "${YELLOW}查看日志:${NC}"
    echo "  $0 $ENV logs"
fi