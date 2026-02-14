#!/bin/bash
# LOOM Azure 部署脚本
# 前提条件：已安装 Azure CLI、Docker

set -e

echo "=== LOOM Azure 部署 ==="

# 配置变量
RESOURCE_GROUP="loom-rg"
LOCATION="eastus"
ACR_NAME="loomacr"
AKS_NAME="loom-aks"
IMAGE_TAG="latest"

# 检查 Azure CLI
if ! command -v az &> /dev/null; then
    echo "错误: Azure CLI 未安装"
    exit 1
fi

# 登录 Azure
echo "1. 登录 Azure..."
az login

echo "2. 创建资源组..."
az group create --name $RESOURCE_GROUP --location $LOCATION

echo "3. 创建 Azure 容器注册表 (ACR)..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

echo "4. 登录 ACR..."
az acr login --name $ACR_NAME

echo "5. 构建 Docker 镜像..."
docker build -t loom:$IMAGE_TAG .

echo "6. 标记镜像..."
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
docker tag loom:$IMAGE_TAG $ACR_LOGIN_SERVER/loom:$IMAGE_TAG

echo "7. 推送镜像到 ACR..."
docker push $ACR_LOGIN_SERVER/loom:$IMAGE_TAG

echo "8. 创建 AKS 集群（如果不存在）..."
if ! az aks show --resource-group $RESOURCE_GROUP --name $AKS_NAME &> /dev/null; then
    az aks create \
        --resource-group $RESOURCE_GROUP \
        --name $AKS_NAME \
        --node-count 2 \
        --enable-addons monitoring \
        --generate-ssh-keys \
        --node-vm-size Standard_B2s
    echo "AKS 集群已创建"
else
    echo "AKS 集群已存在"
fi

echo "9. 获取 AKS 凭证..."
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME --overwrite-existing

echo "10. 将 ACR 附加到 AKS..."
az aks update --resource-group $RESOURCE_GROUP --name $AKS_NAME --attach-acr $ACR_NAME

echo "11. 部署 Kubernetes 配置..."
kubectl apply -f ../../kubernetes/namespace.yaml
kubectl apply -f ../../kubernetes/configmap.yaml
kubectl apply -f ../../kubernetes/secret.yaml
kubectl apply -f ../../kubernetes/pvc.yaml

# 更新 deployment.yaml 中的镜像
cat > deployment-azure.yaml << EOF
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
        image: $ACR_LOGIN_SERVER/loom:$IMAGE_TAG
        ports:
        - containerPort: 8000
        env:
        - name: LOOM_LOG_LEVEL
          value: "INFO"
        - name: LOOM_ENABLE_METRICS
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
EOF

kubectl apply -f deployment-azure.yaml
kubectl apply -f ../../kubernetes/service.yaml

echo "12. 等待 Pod 就绪..."
kubectl wait --namespace=loom --for=condition=ready pod -l app=loom --timeout=300s

echo "13. 创建负载均衡器服务..."
cat > loadbalancer.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: loom-lb
  namespace: loom
spec:
  selector:
    app: loom
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
EOF

kubectl apply -f loadbalancer.yaml

echo ""
echo "=== 部署完成 ==="
echo "资源组: $RESOURCE_GROUP"
echo "ACR: $ACR_NAME"
echo "AKS 集群: $AKS_NAME"
echo "镜像: $ACR_LOGIN_SERVER/loom:$IMAGE_TAG"
echo ""
echo "获取负载均衡器 IP..."
kubectl get svc loom-lb -n loom -w
