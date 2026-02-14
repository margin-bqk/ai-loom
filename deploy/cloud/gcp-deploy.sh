#!/bin/bash
# LOOM Google Cloud Platform 部署脚本
# 前提条件：已安装 gcloud CLI、Docker、kubectl

set -e

echo "=== LOOM GCP 部署 ==="

# 配置变量
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ZONE="us-central1-a"
CLUSTER_NAME="loom-cluster"
IMAGE_TAG="latest"
REPO_NAME="loom"

# 检查 gcloud
if ! command -v gcloud &> /dev/null; then
    echo "错误: gcloud CLI 未安装"
    exit 1
fi

echo "1. 设置项目..."
gcloud config set project $PROJECT_ID

echo "2. 启用所需 API..."
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable monitoring.googleapis.com

echo "3. 创建 Google 容器注册表 (GCR) 镜像..."
IMAGE_NAME="gcr.io/$PROJECT_ID/$REPO_NAME:$IMAGE_TAG"

echo "4. 构建 Docker 镜像..."
docker build -t $IMAGE_NAME .

echo "5. 推送镜像到 GCR..."
gcloud auth configure-docker
docker push $IMAGE_NAME

echo "6. 创建 GKE 集群（如果不存在）..."
if ! gcloud container clusters describe $CLUSTER_NAME --zone $ZONE &> /dev/null; then
    gcloud container clusters create $CLUSTER_NAME \
        --zone $ZONE \
        --num-nodes=2 \
        --machine-type=e2-medium \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=5 \
        --enable-ip-alias \
        --enable-stackdriver-kubernetes
    echo "GKE 集群已创建"
else
    echo "GKE 集群已存在"
fi

echo "7. 获取集群凭证..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE

echo "8. 部署 Kubernetes 配置..."
kubectl apply -f ../../kubernetes/namespace.yaml
kubectl apply -f ../../kubernetes/configmap.yaml
kubectl apply -f ../../kubernetes/secret.yaml
kubectl apply -f ../../kubernetes/pvc.yaml

# 更新 deployment.yaml 中的镜像
cat > deployment-gcp.yaml << EOF
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
        image: $IMAGE_NAME
        ports:
        - containerPort: 8000
        env:
        - name: LOOM_LOG_LEVEL
          value: "INFO"
        - name: LOOM_ENABLE_METRICS
          value: "true"
        - name: GOOGLE_CLOUD_PROJECT
          value: "$PROJECT_ID"
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

kubectl apply -f deployment-gcp.yaml
kubectl apply -f ../../kubernetes/service.yaml

echo "9. 创建负载均衡器..."
cat > loadbalancer.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: loom-lb
  namespace: loom
  annotations:
    cloud.google.com/load-balancer-type: "External"
spec:
  selector:
    app: loom
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
EOF

kubectl apply -f loadbalancer.yaml

echo "10. 等待 Pod 就绪..."
kubectl wait --namespace=loom --for=condition=ready pod -l app=loom --timeout=300s

echo "11. 部署 Stackdriver 监控..."
cat > stackdriver-monitoring.yaml << EOF
apiVersion: monitoring.googleapis.com/v1
kind: PodMonitoring
metadata:
  name: loom-monitoring
  namespace: loom
spec:
  selector:
    matchLabels:
      app: loom
  endpoints:
  - port: metrics
    interval: 30s
  filter: 'resource.type="k8s_container"'
EOF

kubectl apply -f stackdriver-monitoring.yaml 2>/dev/null || echo "Stackdriver 监控配置已跳过（可能需要手动启用）"

echo ""
echo "=== 部署完成 ==="
echo "项目: $PROJECT_ID"
echo "GKE 集群: $CLUSTER_NAME"
echo "镜像: $IMAGE_NAME"
echo ""
echo "获取负载均衡器 IP..."
kubectl get svc loom-lb -n loom -w
