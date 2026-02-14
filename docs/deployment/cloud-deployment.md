# Cloud Deployment

## 概述

LOOM 支持在主流云平台上部署，包括 AWS、Azure 和 Google Cloud Platform。本文档提供了完整的云部署指南，涵盖容器化部署、Kubernetes 编排、监控配置和最佳实践。

## 云平台选择

| 平台 | 推荐服务 | 适用场景 | 复杂度 |
|------|----------|----------|--------|
| **AWS** | ECS Fargate, EKS | 企业级部署，需要与 AWS 生态集成 | 中等 |
| **Azure** | AKS, Container Instances | Azure 生态用户，Windows 混合环境 | 中等 |
| **GCP** | GKE, Cloud Run | 数据科学工作负载，需要 GCP AI 服务 | 中等 |
| **通用** | Kubernetes (任何云) | 多云部署，需要平台无关性 | 高 |

## 通用前提条件

### 1. 工具安装

```bash
# Docker
# 参考: https://docs.docker.com/get-docker/

# Kubernetes CLI (kubectl)
# 参考: https://kubernetes.io/docs/tasks/tools/

# 云平台 CLI
# AWS: aws-cli
# Azure: azure-cli
# GCP: gcloud-cli
```

### 2. 账户配置

- 云平台账户和订阅
- 足够的配额和权限
- 计费设置完成

### 3. 本地准备

```bash
# 克隆仓库
git clone https://github.com/your-org/loom.git
cd loom

# 构建本地镜像（用于测试）
docker build -t loom:latest .
```

## AWS 部署

### 1. AWS ECS Fargate 部署

使用提供的部署脚本：

```bash
# 授予执行权限
chmod +x deploy/cloud/aws-deploy.sh

# 运行部署脚本
./deploy/cloud/aws-deploy.sh
```

#### 手动部署步骤

##### 1.1 配置 ECR 仓库

```bash
# 创建 ECR 仓库
aws ecr create-repository --repository-name loom --region us-east-1

# 登录 ECR
aws ecr get-login-password --region us-east-1 | docker login \
  --username AWS \
  --password-stdin $(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.us-east-1.amazonaws.com
```

##### 1.2 构建和推送镜像

```bash
# 构建镜像
docker build -t loom:latest .

# 标记镜像
docker tag loom:latest $(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.us-east-1.amazonaws.com/loom:latest

# 推送镜像
docker push $(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.us-east-1.amazonaws.com/loom:latest
```

##### 1.3 创建 ECS 集群和服务

```bash
# 创建 ECS 集群
aws ecs create-cluster --cluster-name loom-cluster --region us-east-1

# 创建任务定义
aws ecs register-task-definition \
  --cli-input-json file://deploy/aws/task-definition.json \
  --region us-east-1

# 创建服务
aws ecs create-service \
  --cluster loom-cluster \
  --service-name loom-service \
  --task-definition loom-task:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration file://deploy/aws/network-config.json \
  --region us-east-1
```

### 2. AWS EKS 部署

```bash
# 创建 EKS 集群
eksctl create cluster \
  --name loom-eks \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5

# 部署到 EKS
kubectl apply -f kubernetes/
```

### 3. AWS 特定配置

#### 3.1 Secrets Manager 集成

```yaml
# 在任务定义中引用 Secrets Manager
secrets:
  - name: OPENAI_API_KEY
    valueFrom: arn:aws:secretsmanager:us-east-1:123456789012:secret:loom/openai-api-key
```

#### 3.2 CloudWatch 日志

```yaml
logConfiguration:
  logDriver: awslogs
  options:
    awslogs-group: /ecs/loom
    awslogs-region: us-east-1
    awslogs-stream-prefix: ecs
```

#### 3.3 IAM 角色

创建 ECS 任务执行角色：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
```

## Azure 部署

### 1. Azure AKS 部署

使用提供的部署脚本：

```bash
# 授予执行权限
chmod +x deploy/cloud/azure-deploy.sh

# 运行部署脚本
./deploy/cloud/azure-deploy.sh
```

#### 手动部署步骤

##### 1.1 创建资源组和 ACR

```bash
# 登录 Azure
az login

# 创建资源组
az group create --name loom-rg --location eastus

# 创建 Azure 容器注册表
az acr create --resource-group loom-rg --name loomacr --sku Basic

# 登录 ACR
az acr login --name loomacr
```

##### 1.2 构建和推送镜像

```bash
# 构建镜像
docker build -t loom:latest .

# 标记镜像
ACR_LOGIN_SERVER=$(az acr show --name loomacr --query loginServer --output tsv)
docker tag loom:latest $ACR_LOGIN_SERVER/loom:latest

# 推送镜像
docker push $ACR_LOGIN_SERVER/loom:latest
```

##### 1.3 创建 AKS 集群

```bash
# 创建 AKS 集群
az aks create \
  --resource-group loom-rg \
  --name loom-aks \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --node-vm-size Standard_B2s

# 获取凭证
az aks get-credentials --resource-group loom-rg --name loom-aks
```

##### 1.4 部署到 AKS

```bash
# 部署 Kubernetes 配置
kubectl apply -f kubernetes/

# 创建负载均衡器
kubectl apply -f deploy/azure/loadbalancer.yaml
```

### 2. Azure 容器实例 (ACI)

```bash
# 快速部署单容器
az container create \
  --resource-group loom-rg \
  --name loom-aci \
  --image $ACR_LOGIN_SERVER/loom:latest \
  --cpu 1 \
  --memory 1.5 \
  --ports 8000 \
  --environment-variables LOOM_LOG_LEVEL=INFO \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $(az acr credential show --name loomacr --query username -o tsv) \
  --registry-password $(az acr credential show --name loomacr --query passwords[0].value -o tsv)
```

### 3. Azure 特定配置

#### 3.1 Azure Key Vault 集成

```yaml
# 在 Pod 中挂载 Key Vault 卷
volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: loom-secrets
```

#### 3.2 Azure Monitor

```yaml
# 启用容器洞察
az aks enable-addons --addons monitoring --name loom-aks --resource-group loom-rg
```

#### 3.3 托管身份

```bash
# 为 AKS 分配托管身份
az aks update \
  --resource-group loom-rg \
  --name loom-aks \
  --enable-managed-identity
```

## Google Cloud Platform 部署

### 1. GKE 部署

使用提供的部署脚本：

```bash
# 授予执行权限
chmod +x deploy/cloud/gcp-deploy.sh

# 运行部署脚本
./deploy/cloud/gcp-deploy.sh
```

#### 手动部署步骤

##### 1.1 设置项目和启用 API

```bash
# 设置项目
gcloud config set project your-project-id

# 启用所需 API
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

##### 1.2 构建和推送镜像到 GCR

```bash
# 构建镜像
docker build -t gcr.io/your-project-id/loom:latest .

# 推送镜像
gcloud auth configure-docker
docker push gcr.io/your-project-id/loom:latest
```

##### 1.3 创建 GKE 集群

```bash
# 创建集群
gcloud container clusters create loom-cluster \
  --zone us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5
```

##### 1.4 部署到 GKE

```bash
# 获取凭证
gcloud container clusters get-credentials loom-cluster --zone us-central1-a

# 部署应用
kubectl apply -f kubernetes/
```

### 2. Cloud Run 部署（无服务器）

```bash
# 部署到 Cloud Run
gcloud run deploy loom \
  --image gcr.io/your-project-id/loom:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars LOOM_LOG_LEVEL=INFO
```

### 3. GCP 特定配置

#### 3.1 Secret Manager 集成

```yaml
# 在 Pod 中访问 Secret Manager
env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: loom-secrets
        key: openai-api-key
```

#### 3.2 Stackdriver 监控

```yaml
# 启用 Stackdriver Kubernetes 监控
gcloud container clusters update loom-cluster \
  --zone us-central1-a \
  --enable-stackdriver-kubernetes
```

#### 3.3 Cloud IAM 角色

```bash
# 为服务账户分配角色
gcloud projects add-iam-policy-binding your-project-id \
  --member serviceAccount:loom-sa@your-project-id.iam.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor
```

## 多云部署策略

### 1. 使用 Terraform 进行基础设施即代码

```hcl
# main.tf - AWS 示例
resource "aws_ecs_cluster" "loom" {
  name = "loom-cluster"
}

resource "aws_ecs_task_definition" "loom" {
  family = "loom-task"
  container_definitions = file("task-definition.json")
}
```

### 2. 使用 Helm 进行 Kubernetes 部署

```bash
# 创建 Helm chart
helm create loom-chart

# 部署 Helm chart
helm install loom ./loom-chart \
  --namespace loom \
  --set image.repository=gcr.io/your-project-id/loom \
  --set image.tag=latest
```

### 3. GitOps 工作流（使用 ArgoCD）

```yaml
# application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: loom
spec:
  destination:
    namespace: loom
    server: https://kubernetes.default.svc
  source:
    path: kubernetes/
    repoURL: https://github.com/your-org/loom.git
    targetRevision: main
```

## 监控和运维

### 1. 云原生监控栈

| 平台 | 监控解决方案 | 日志管理 | 告警系统 |
|------|--------------|----------|----------|
| AWS | CloudWatch Container Insights | CloudWatch Logs | CloudWatch Alarms |
| Azure | Azure Monitor for Containers | Log Analytics | Azure Monitor Alerts |
| GCP | Cloud Monitoring | Cloud Logging | Cloud Monitoring Alerts |

### 2. 性能指标收集

```yaml
# Prometheus 配置示例
scrape_configs:
  - job_name: 'loom'
    static_configs:
      - targets: ['loom:8000']
    metrics_path: '/metrics'
```

### 3. 日志聚合

```bash
# AWS CloudWatch 日志代理
aws logs create-log-group --log-group-name /ecs/loom

# Azure Log Analytics 工作区
az monitor log-analytics workspace create --resource-group loom-rg --workspace-name loom-logs

# GCP Cloud Logging
gcloud logging sinks create loom-logs storage.googleapis.com/loom-logs-bucket
```

## 安全最佳实践

### 1. 网络安全

```yaml
# 网络策略示例
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: loom-network-policy
spec:
  podSelector:
    matchLabels:
      app: loom
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

### 2. 密钥管理

- 使用云平台的密钥管理服务（AWS Secrets Manager, Azure Key Vault, GCP Secret Manager）
- 避免在代码或配置文件中硬编码密钥
- 定期轮换密钥

### 3. 镜像安全

```bash
# 扫描镜像漏洞
docker scan loom:latest

# 使用可信的基础镜像
FROM python:3.12-slim

# 定期更新基础镜像
```

## 成本优化

### 1. 资源调整

```yaml
# 根据负载调整资源
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 2. 自动扩缩容

```yaml
# HPA 配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: loom-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: loom
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 3. 预留实例和 Spot 实例

```bash
# AWS: 使用 Spot Fleet
# Azure: 使用 Spot VM
# GCP: 使用 Preemptible VM
```

## 故障排除

### 1. 常见问题

#### 镜像拉取失败

```bash
# 检查镜像权限
docker pull gcr.io/your-project-id/loom:latest

# 验证服务账户权限
kubectl describe pod loom-xxx
```

#### 服务无法访问

```bash
# 检查服务状态
kubectl get svc loom-lb

# 检查网络策略
kubectl describe networkpolicy loom-network-policy

# 测试连接
kubectl run test --image=busybox --rm -it -- wget -O- http://loom:8000/health
```

#### 资源不足

```bash
# 查看资源使用情况
kubectl top pods

# 调整资源限制
kubectl edit deployment loom
```

### 2. 调试命令

```bash
# 查看 Pod 日志
kubectl logs -f deployment/loom

# 进入容器调试
kubectl exec -it deployment/loom -- bash

# 查看事件
kubectl get events --sort-by='.lastTimestamp'

# 描述资源状态
kubectl describe pod loom-xxx
```

## 迁移和升级

### 1. 蓝绿部署

```bash
# 部署新版本（绿色）
kubectl apply -f deployment-green.yaml

# 测试新版本
curl http://green-lb/health

# 切换流量
kubectl patch svc loom-lb -p '{"spec":{"selector":{"version":"green"}}}'
```

### 2. 金丝雀发布

```yaml
# 使用 Istio 进行流量分割
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: loom
spec:
  hosts:
  - loom.example.com
  http:
  - route:
    - destination:
        host: loom
        subset: v1
      weight: 90
    - destination:
        host: loom
        subset: v2
      weight: 10
```

## 参考链接

- [AWS ECS 文档](https://docs.aws.amazon.com/ecs/)
- [Azure AKS 文档](https://docs.microsoft.com/azure/aks/)
- [GCP GKE 文档](https://cloud.google.com/kubernetes-engine/docs)
- [Kubernetes 官方文档](https://kubernetes.io/docs/)
- [LOOM Docker 部署指南](./docker-deployment.md)
- [LOOM 监控指南](./monitoring.md)
