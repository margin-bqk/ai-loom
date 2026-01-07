#!/bin/bash
# LOOM Kubernetes 一键部署脚本

set -e

echo "=== LOOM Kubernetes 部署 ==="

# 检查 kubectl 是否可用
if ! command -v kubectl &> /dev/null; then
    echo "错误: kubectl 未安装"
    exit 1
fi

# 设置命名空间
NAMESPACE="loom"

echo "1. 创建命名空间..."
kubectl apply -f namespace.yaml

echo "2. 创建配置..."
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml

echo "3. 创建持久化存储..."
kubectl apply -f pvc.yaml

echo "4. 部署 LOOM 应用..."
kubectl apply -f deployment.yaml

echo "5. 创建服务..."
kubectl apply -f service.yaml

echo "6. 创建 Ingress (可选)..."
if [ -f ingress.yaml ]; then
    kubectl apply -f ingress.yaml
    echo "Ingress 已部署"
else
    echo "跳过 Ingress (文件不存在)"
fi

echo "7. 部署监控配置..."
if [ -f monitoring.yaml ]; then
    kubectl apply -f monitoring.yaml
    echo "监控配置已部署"
else
    echo "跳过监控配置"
fi

echo "8. 等待 Pod 就绪..."
kubectl wait --namespace=$NAMESPACE --for=condition=ready pod -l app=loom --timeout=300s

echo "9. 显示部署状态..."
kubectl get all -n $NAMESPACE

echo "10. 显示服务信息..."
kubectl get svc -n $NAMESPACE

echo ""
echo "=== 部署完成 ==="
echo "LOOM 已成功部署到 Kubernetes 集群"
echo ""
echo "访问方式:"
echo "1. 集群内部: http://loom-service.loom.svc.cluster.local"
echo "2. 端口转发: kubectl port-forward svc/loom-service -n $NAMESPACE 8000:80"
echo "3. 如果配置了 Ingress，可通过外部域名访问"
echo ""
echo "监控:"
echo "- Prometheus metrics: http://loom-service.loom.svc.cluster.local:8001/metrics"
echo "- 健康检查: http://loom-service.loom.svc.cluster.local/health"