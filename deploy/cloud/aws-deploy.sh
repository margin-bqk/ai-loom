#!/bin/bash
# LOOM AWS 部署脚本
# 前提条件：已安装 AWS CLI、Docker、并配置了 AWS 凭证

set -e

echo "=== LOOM AWS 部署 ==="

# 配置变量
REGION="us-east-1"
ECR_REPO="loom"
IMAGE_TAG="latest"
CLUSTER_NAME="loom-cluster"
SERVICE_NAME="loom-service"
TASK_DEFINITION="loom-task"

# 检查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo "错误: AWS CLI 未安装"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

echo "1. 登录 AWS ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.$REGION.amazonaws.com

echo "2. 创建 ECR 仓库（如果不存在）..."
if ! aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION &> /dev/null; then
    aws ecr create-repository --repository-name $ECR_REPO --region $REGION
    echo "ECR 仓库已创建"
else
    echo "ECR 仓库已存在"
fi

echo "3. 构建 Docker 镜像..."
docker build -t $ECR_REPO:$IMAGE_TAG .

echo "4. 标记镜像..."
ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION --query 'repositories[0].repositoryUri' --output text)
docker tag $ECR_REPO:$IMAGE_TAG $ECR_URI:$IMAGE_TAG

echo "5. 推送镜像到 ECR..."
docker push $ECR_URI:$IMAGE_TAG

echo "6. 创建 ECS 任务定义..."
cat > task-definition.json << EOF
{
    "family": "$TASK_DEFINITION",
    "networkMode": "awsvpc",
    "executionRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query 'Account' --output text):role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "loom",
            "image": "$ECR_URI:$IMAGE_TAG",
            "portMappings": [
                {
                    "containerPort": 8000,
                    "hostPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "LOOM_LOG_LEVEL",
                    "value": "INFO"
                },
                {
                    "name": "LOOM_ENABLE_METRICS",
                    "value": "true"
                }
            ],
            "secrets": [
                {
                    "name": "OPENAI_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:$REGION:$(aws sts get-caller-identity --query 'Account' --output text):secret:loom/openai-api-key"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/loom",
                    "awslogs-region": "$REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ],
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024"
}
EOF

echo "7. 注册任务定义..."
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION

echo "8. 创建 CloudWatch 日志组..."
aws logs create-log-group --log-group-name "/ecs/loom" --region $REGION 2>/dev/null || true

echo "9. 创建 ECS 集群（如果不存在）..."
if ! aws ecs describe-clusters --clusters $CLUSTER_NAME --region $REGION --query 'clusters[0].clusterName' --output text &> /dev/null; then
    aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION
    echo "ECS 集群已创建"
else
    echo "ECS 集群已存在"
fi

echo "10. 创建安全组和 VPC 配置（需要根据实际情况调整）..."
echo "请确保已配置正确的网络设置"

echo ""
echo "=== 部署完成 ==="
echo "下一步："
echo "1. 配置负载均衡器和目标组"
echo "2. 创建 ECS 服务"
echo "3. 设置自动扩缩容"
echo ""
echo "镜像 URI: $ECR_URI:$IMAGE_TAG"
echo "任务定义: $TASK_DEFINITION"
echo "集群: $CLUSTER_NAME"