# Kubernetes Manifests for MLOps Deployment

Production-grade Kubernetes manifests for deploying the MLOps system with high availability, security, and observability.

## 📁 Manifest Files

| File | Purpose | Key Features |
|------|---------|--------------|
| `deployment.yaml` | Application deployment | Multi-version deployments (v1, v2), health checks, resource limits |
| `hpa.yaml` | Horizontal Pod Autoscaler | CPU/memory-based scaling, custom metrics, scale policies |
| `configmap.yaml` | Configuration management | App config, Prometheus alerts, Nginx settings |
| `secrets.template.yaml` | Secret templates | API keys, DB credentials, cloud provider keys |
| `ingress.yaml` | Ingress controller | TLS termination, rate limiting, canary deployments |
| `networkpolicy.yaml` | Network security | Zero-trust networking, least-privilege access |
| `servicemonitor.yaml` | Prometheus monitoring | Metrics scraping, alerting rules, SLIs/SLOs |
| `pvc.yaml` | Persistent storage | Model artifacts, data cache, logs |

## 🚀 Quick Deployment

### Prerequisites

1. **Kubernetes cluster** (version 1.24+)
   - AWS EKS, GCP GKE, Azure AKS, or local (minikube, kind)
2. **kubectl** configured
3. **Ingress controller** (nginx-ingress)
4. **Prometheus Operator** (optional, for ServiceMonitor)

### Deployment Steps

```bash
# 1. Create namespace
kubectl create namespace mlops

# 2. Create secrets from template
cp secrets.template.yaml secrets.yaml
# Edit secrets.yaml with actual credentials
kubectl apply -f secrets.yaml

# 3. Apply ConfigMaps
kubectl apply -f configmap.yaml

# 4. Create PersistentVolumeClaims
kubectl apply -f pvc.yaml

# 5. Deploy application
kubectl apply -f deployment.yaml

# 6. Configure autoscaling
kubectl apply -f hpa.yaml

# 7. Set up network policies
kubectl apply -f networkpolicy.yaml

# 8. Configure ingress
kubectl apply -f ingress.yaml

# 9. Set up monitoring (if Prometheus Operator is installed)
kubectl apply -f servicemonitor.yaml

# 10. Verify deployment
kubectl get all -n mlops
kubectl get pods -n mlops -w
```

### Quick Deploy (All-in-One)

```bash
# Deploy everything except secrets
kubectl apply -f . --exclude secrets.yaml

# Or deploy everything (if secrets.yaml is configured)
kubectl apply -f .
```

## 🔒 Security Configuration

### 1. Create Secrets

**Never commit `secrets.yaml` to git!** It's in `.gitignore`.

```bash
# Copy template
cp secrets.template.yaml secrets.yaml

# Edit with actual values
vim secrets.yaml

# Apply
kubectl apply -f secrets.yaml

# Verify (values are hidden)
kubectl get secrets -n mlops
kubectl describe secret mlops-secrets -n mlops
```

### 2. TLS Certificates

**Option A: cert-manager (Recommended)**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Certificates will be automatically issued for ingress resources
```

**Option B: Manual certificates**

```bash
# Generate self-signed certificate (testing only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=mlops.example.com"

# Create secret
kubectl create secret tls mlops-tls -n mlops \
  --cert=tls.crt --key=tls.key

# Clean up local files
rm tls.key tls.crt
```

### 3. Network Policies

Network policies implement zero-trust networking:

```bash
# Verify network policy support
kubectl get networkpolicies -n mlops

# Test connectivity (should fail from unauthorized pods)
kubectl run test-pod --rm -it --image=busybox -n default -- \
  wget -O- http://qna-svc.mlops.svc.cluster.local/health
```

## 📊 Monitoring and Observability

### Prometheus Operator

If you have Prometheus Operator installed:

```bash
# Apply ServiceMonitor
kubectl apply -f servicemonitor.yaml

# Verify metrics are being scraped
kubectl port-forward svc/prometheus-operated 9090:9090 -n monitoring
# Visit http://localhost:9090/targets
```

### Grafana Dashboards

Import dashboards for visualization:

1. **Kubernetes Cluster Monitoring** (ID: 7249)
2. **Kubernetes Pod Monitoring** (ID: 6417)
3. **NGINX Ingress Controller** (ID: 9614)

```bash
# Port forward to Grafana
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Visit http://localhost:3000
# Default credentials: admin/admin
```

### Logs

```bash
# View application logs
kubectl logs -f deployment/qna-v1 -n mlops

# View logs from all pods with label
kubectl logs -f -l app=qna -n mlops

# View previous pod logs (after crash)
kubectl logs deployment/qna-v1 -n mlops --previous
```

## 🔄 Canary Deployments

The setup supports canary deployments with traffic splitting:

```bash
# 1. Deploy new version as v2
kubectl apply -f deployment.yaml  # v2 has replicas: 0 initially

# 2. Scale up canary (10% traffic via ingress)
kubectl scale deployment qna-v2 -n mlops --replicas=1

# 3. Monitor metrics
kubectl top pods -n mlops
kubectl logs -f deployment/qna-v2 -n mlops

# 4. Gradually increase traffic (edit ingress.yaml)
# Change nginx.ingress.kubernetes.io/canary-weight: "10" to "50"
kubectl apply -f ingress.yaml

# 5. Full rollout
kubectl scale deployment qna-v2 -n mlops --replicas=3
kubectl scale deployment qna-v1 -n mlops --replicas=0

# 6. Rollback if needed
kubectl scale deployment qna-v1 -n mlops --replicas=3
kubectl scale deployment qna-v2 -n mlops --replicas=0
```

## 🎯 Autoscaling

### Horizontal Pod Autoscaler

```bash
# Check HPA status
kubectl get hpa -n mlops

# Describe HPA for details
kubectl describe hpa mlops-deployment-hpa -n mlops

# Generate load for testing
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh
# Inside the pod:
while true; do wget -q -O- http://qna-svc.mlops.svc.cluster.local/predict; done

# Watch pods scaling
kubectl get pods -n mlops -w
```

### Vertical Pod Autoscaler (Optional)

```bash
# Install VPA
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/download/vertical-pod-autoscaler-0.14.0/vertical-pod-autoscaler.yaml

# Create VPA resource
cat <<EOF | kubectl apply -f -
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: mlops-vpa
  namespace: mlops
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: qna-v1
  updatePolicy:
    updateMode: "Auto"
EOF
```

## 🧪 Health Checks and Debugging

```bash
# Check pod health
kubectl get pods -n mlops

# Describe pod for events
kubectl describe pod <pod-name> -n mlops

# Check readiness/liveness probes
kubectl get pods -n mlops -o json | jq '.items[].status.conditions'

# Port forward for local testing
kubectl port-forward svc/qna-svc 8080:80 -n mlops
curl http://localhost:8080/health
curl http://localhost:8080/metrics

# Exec into pod
kubectl exec -it deployment/qna-v1 -n mlops -- /bin/bash

# Get resource usage
kubectl top pods -n mlops
kubectl top nodes
```

## 🔧 Configuration Updates

### Update ConfigMap

```bash
# Edit configmap
kubectl edit configmap mlops-config -n mlops

# Or apply from file
kubectl apply -f configmap.yaml

# Restart deployment to pick up changes
kubectl rollout restart deployment/qna-v1 -n mlops
```

### Update Secrets

```bash
# Update secret
kubectl create secret generic mlops-secrets -n mlops \
  --from-literal=WANDB_API_KEY=new_key \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment
kubectl rollout restart deployment/qna-v1 -n mlops
```

## 🗑️ Cleanup

```bash
# Delete all resources in namespace
kubectl delete namespace mlops

# Or delete specific resources
kubectl delete -f .

# Force delete stuck resources
kubectl delete pod <pod-name> -n mlops --force --grace-period=0
```

## 📖 Best Practices

1. **Resource Limits**: Always set requests and limits
2. **Health Checks**: Configure readiness and liveness probes
3. **Security**: Use network policies and non-root containers
4. **Monitoring**: Export metrics and set up alerts
5. **High Availability**: Run multiple replicas across zones
6. **Rolling Updates**: Use RollingUpdate strategy with maxSurge/maxUnavailable
7. **Secrets Management**: Never commit secrets, use external secret managers
8. **Namespace Isolation**: Use separate namespaces for environments

## 🆘 Troubleshooting

### Pod Stuck in Pending

```bash
kubectl describe pod <pod-name> -n mlops
# Common causes: insufficient resources, PVC not bound, node selector mismatch
```

### ImagePullBackOff

```bash
# Check image exists and is accessible
docker pull <image-name>

# Check image pull secrets
kubectl get secrets -n mlops
```

### CrashLoopBackOff

```bash
# View logs
kubectl logs <pod-name> -n mlops

# Check previous logs
kubectl logs <pod-name> -n mlops --previous
```

### Network Issues

```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup qna-svc.mlops.svc.cluster.local

# Test connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://qna-svc.mlops.svc.cluster.local/health
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Production Checklist](https://learnk8s.io/production-best-practices)
- [Security Best Practices](https://kubernetes.io/docs/concepts/security/overview/)
