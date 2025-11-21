#!/usr/bin/env bash
set -euo pipefail

# Canary deployment script
# Usage: ./deploy_canary.sh <image-tag> <canary-replicas> <namespace>

IMAGE_TAG="${1:-latest}"
CANARY_REPLICAS="${2:-1}"
NAMESPACE="${3:-default}"
SERVICE_NAME="qna-svc"
CANARY_DEPLOY="qna-v2"
STABLE_DEPLOY="qna-v1"

echo "🚀 Starting canary deployment..."
echo "Image tag: $IMAGE_TAG"
echo "Canary replicas: $CANARY_REPLICAS"
echo "Namespace: $NAMESPACE"

# Check if kubectl is available
if ! command -v kubectl >/dev/null 2>&1; then
    echo "❌ kubectl not found in PATH"
    exit 2
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    echo "❌ Namespace '$NAMESPACE' does not exist"
    exit 3
fi

# Update canary deployment image
echo "📦 Updating canary deployment image..."
kubectl -n "$NAMESPACE" set image deployment/"$CANARY_DEPLOY" \
    qna="ghcr.io/youruser/qna:$IMAGE_TAG"

# Scale up canary
echo "📈 Scaling up canary deployment..."
kubectl -n "$NAMESPACE" scale deployment "$CANARY_DEPLOY" --replicas="$CANARY_REPLICAS"

# Wait for canary to be ready
echo "⏳ Waiting for canary pods to be ready..."
kubectl -n "$NAMESPACE" rollout status deployment/"$CANARY_DEPLOY" --timeout=300s

# Get current replica counts
STABLE_REPLICAS=$(kubectl -n "$NAMESPACE" get deployment "$STABLE_DEPLOY" -o jsonpath='{.spec.replicas}')
TOTAL_REPLICAS=$((STABLE_REPLICAS + CANARY_REPLICAS))
CANARY_PERCENTAGE=$((CANARY_REPLICAS * 100 / TOTAL_REPLICAS))

echo "📊 Traffic distribution:"
echo "  Stable (v1): $STABLE_REPLICAS replicas ($((100 - CANARY_PERCENTAGE))%)"
echo "  Canary (v2): $CANARY_REPLICAS replicas ($CANARY_PERCENTAGE%)"

# Optional: Update service to route some traffic to canary
read -p "Route traffic to canary? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Updating service to route traffic to canary..."
    kubectl -n "$NAMESPACE" patch svc "$SERVICE_NAME" \
        -p '{"spec":{"selector":{"app":"qna","version":"v2"}}}'
    echo "✅ Traffic routed to canary"
else
    echo "ℹ️  Traffic still routed to stable version"
fi

# Show current status
echo ""
echo "📋 Current deployment status:"
kubectl -n "$NAMESPACE" get pods -l app=qna -o wide

echo ""
echo "🔍 To monitor the canary:"
echo "  kubectl -n $NAMESPACE logs -l version=v2 -f"
echo "  kubectl -n $NAMESPACE get events --sort-by=.metadata.creationTimestamp"

echo ""
echo "🔄 To promote canary to stable:"
echo "  kubectl -n $NAMESPACE patch svc $SERVICE_NAME -p '{\"spec\":{\"selector\":{\"app\":\"qna\",\"version\":\"v2\"}}}'"
echo "  kubectl -n $NAMESPACE scale deployment $STABLE_DEPLOY --replicas=$CANARY_REPLICAS"
echo "  kubectl -n $NAMESPACE scale deployment $CANARY_DEPLOY --replicas=$STABLE_REPLICAS"

echo ""
echo "🔙 To rollback:"
echo "  ./rollback.sh $NAMESPACE $SERVICE_NAME"
