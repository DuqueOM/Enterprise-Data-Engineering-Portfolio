#!/usr/bin/env bash
set -euo pipefail

# rollback.sh
# Uso: ./rollback.sh [namespace] [service-name]
NAMESPACE="${1:-default}"
SVC_NAME="${2:-qna-svc}"
DEPLOY_CANARY="qna-v2"
DEPLOY_STABLE="qna-v1"

echo "Rollback: namespace=$NAMESPACE svc=$SVC_NAME"

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl no está disponible en PATH" >&2
  exit 2
fi

echo "Scaling down canary deployment ${DEPLOY_CANARY} -> 0 replicas"
kubectl -n "$NAMESPACE" scale deploy "$DEPLOY_CANARY" --replicas=0 || true

echo "Patching Service ${SVC_NAME} selector -> version=v1"
kubectl -n "$NAMESPACE" patch svc "$SVC_NAME" -p '{"spec": {"selector": {"app":"qna","version":"v1"}}}' || true

echo "Attempting rollout undo on ${DEPLOY_CANARY}"
kubectl -n "$NAMESPACE" rollout undo deployment/"$DEPLOY_CANARY" || true

echo "Rollback completed. Verifica pods y estado:"
kubectl -n "$NAMESPACE" get pods -l app=qna -o wide
