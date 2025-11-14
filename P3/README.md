# 🤖 AIOps Auto-Retrain Pipeline

**Sistema completo de gestión automática para modelos de IA con MLOps**

Este proyecto demuestra un pipeline de MLOps de nivel semi-senior que implementa integración y despliegue continuo (CI/CD) aplicado a modelos de machine learning, con monitoreo, detección de drift, y rollback automático.

## 🎯 Objetivo del Proyecto

Resolver el problema común donde los modelos funcionan en el laboratorio pero fallan en producción. El sistema asegura que:
- ✅ El modelo se entrene, pruebe y actualice automáticamente
- ✅ Se vigile su rendimiento en producción continuamente
- ✅ Se detecten errores o cambios en el entorno (data drift)
- ✅ Se actualice con seguridad mediante canary releases y rollback automático

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub CI     │    │   Docker Hub    │    │  Kubernetes     │
│   (Build/Test)  │───▶│   (Registry)    │───▶│   (Deployment)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MLflow        │    │   Weights &     │    │   Prometheus    │
│   (Tracking)    │    │   Biases        │    │   (Metrics)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prefect       │    │   Drift         │    │   Grafana       │
│   (Orchestration)│   │   Detection     │    │   (Dashboard)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 4. Endpoint de versión de la API [P4]

La API expone un endpoint para conocer la versión de servicio y del modelo:  # [P4]

```bash
curl http://localhost:8080/version  # [P4]
```

Respuesta:

```json
{  # [P4]
  "api_version": "v1.0.0",  # [P4]
  "model_version": "v1.0.0",  # [P4]
  "service": "qna-model-service"  # [P4]
}
```

Puedes configurar la versión de API mediante la variable de entorno `API_VERSION`.  # [P4]

## 📁 Estructura del Proyecto

```
P3/
├── .github/workflows/
│   └── ci_smoke.yml          # Pipeline CI/CD completo
├── space/
│   ├── app.py               # API FastAPI con métricas Prometheus
│   └── __init__.py
├── scripts/
│   ├── ingest.py            # Ingestión de datos
│   └── generate_baseline.py # Generación de baseline para drift
├── tests/
│   ├── test_app.py          # Tests de la API
│   └── test_data_schema.py  # Tests de validación de datos
├── monitoring/
│   ├── prometheus.yml       # Configuración de Prometheus
│   └── grafana-dashboard.json # Dashboard de Grafana
├── k8s/
│   └── deployment.yaml      # Manifests Kubernetes (canary)
├── drift_detector.py        # Detector de drift con embeddings
├── flow_retrain.py          # Pipeline de reentreno con Prefect
├── train.py                 # Script de entrenamiento
├── rollback.sh              # Script de rollback automático
├── Dockerfile               # Imagen Docker optimizada
├── requirements.txt         # Dependencias Python
└── .env.example            # Variables de entorno ejemplo
```

## 🚀 Guía de Instalación y Configuración

### Prerrequisitos

- Python 3.10+
- Docker y Docker Compose
- kubectl y acceso a cluster Kubernetes
- Git
- Cuentas en: GitHub, Weights & Biases, Docker Hub

### 1. Configuración del Entorno Local

```bash
# Clonar el repositorio
git clone <repository-url>
cd P3

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Configurar Variables de Entorno

Edita el archivo `.env` con tus credenciales:

```bash
# Weights & Biases (requerido para tracking)
WANDB_API_KEY=tu_api_key_aqui

# Container Registry (requerido para CI/CD)
CR_PAT=tu_token_docker_hub

# Integraciones opcionales
SLACK_WEBHOOK=tu_webhook_slack
GITHUB_TOKEN=tu_token_github
GITHUB_REPO=tu_usuario/tu_repo

# Configuración de MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=production
```

### 3. Ejecución Local (Smoke Test)

```bash
# 1. Generar datos de ejemplo
python scripts/ingest.py

# 2. Entrenamiento rápido (smoke test)
python train.py --max_steps 10 --batch_size 2 --wandb_project smoke-ci

# 3. Iniciar API local
uvicorn space.app:app --host 0.0.0.0 --port 8080 --reload

# 4. Probar endpoints (en otra terminal)
curl http://localhost:8080/health
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]}'

# 5. Ver métricas de Prometheus
curl http://localhost:8080/metrics
```

## 🐳 Despliegue con Docker

### 1. Construir Imagen Local

```bash
# Construir imagen
docker build -t qna-model:latest .

# Ejecutar contenedor
docker run -p 8080:8080 \
  -e MODEL_PATH=/app/artifacts/latest/model.joblib \
  -v $(pwd)/artifacts:/app/artifacts \
  qna-model:latest
```

### 2. Docker Compose (Stack Completo)

```bash
# Crear docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - MODEL_PATH=/app/artifacts/latest/model.joblib
    volumes:
      - ./artifacts:/app/artifacts
    depends_on:
      - mlflow
  
  mlflow:
    image: python:3.10-slim
    ports:
      - "5000:5000"
    command: >
      bash -c "pip install mlflow && 
               mlflow server --host 0.0.0.0 --port 5000"
  
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
EOF

# Iniciar stack completo
docker-compose up -d

# Acceder a servicios:
# API: http://localhost:8080
# MLflow: http://localhost:5000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

## ☸️ Despliegue en Kubernetes

### 1. Configurar Cluster

```bash
# Verificar conexión al cluster
kubectl cluster-info

# Crear namespace (opcional)
kubectl create namespace mlops-demo
kubectl config set-context --current --namespace=mlops-demo
```

### 2. Desplegar Aplicación

```bash
# Aplicar manifests
kubectl apply -f k8s/deployment.yaml

# Verificar despliegue
kubectl get pods -l app=qna
kubectl get svc qna-svc

# Hacer port-forward para pruebas
kubectl port-forward svc/qna-svc 8080:80
```

### 3. Canary Release

```bash
# Actualizar imagen para canary
kubectl set image deployment/qna-v2 qna=ghcr.io/tu_usuario/qna:new-version

# Escalar canary (5% tráfico)
kubectl scale deployment qna-v2 --replicas=1

# Redirigir parte del tráfico al canary
kubectl patch svc qna-svc -p '{"spec":{"selector":{"version":"v2"}}}'

# Monitorear y validar
kubectl logs -l version=v2 -f
```

### 4. Rollback Automático

```bash
# Usar script de rollback
chmod +x rollback.sh
./rollback.sh mlops-demo qna-svc

# O rollback manual con kubectl
kubectl rollout undo deployment/qna-v2
kubectl scale deployment qna-v2 --replicas=0
```

## 🔄 Pipeline CI/CD con GitHub Actions

El pipeline se activa automáticamente en cada push/PR a main/master:

### 1. Configurar Secrets en GitHub

Ve a `Settings > Secrets and variables > Actions` en tu repositorio:

```
WANDB_API_KEY: tu_api_key_de_wandb
CR_PAT: tu_personal_access_token_docker_hub
SLACK_WEBHOOK: tu_webhook_slack (opcional)
GITHUB_TOKEN: tu_token_github (opcional)
```

### 2. Ejecución del Pipeline

El pipeline ejecuta:

1. **Lint & Tests**: Validación de código y tests unitarios
2. **Smoke Training**: Entrenamiento rápido para validar el pipeline
3. **Build & Push**: Construcción y publicación de imagen Docker
4. **Artifact Upload**: Guarda logs y artefactos del entrenamiento

### 3. Monitoreo del Pipeline

```bash
# Ver estado del workflow
gh run list --repo tu_usuario/tu_repo

# Descargar artefactos
gh run download RUN_ID --repo tu_usuario/tu_repo
```

## 📊 Monitoreo y Observabilidad

### 1. Métricas Prometheus

La API expone métricas en `/metrics`:

- `predictions_total`: Número total de predicciones
- `prediction_duration_seconds`: Tiempo de inferencia
- `model_version`: Versión del modelo desplegado

### 2. Dashboard Grafana

Importa el dashboard preconfigurado:

```bash
# Importar dashboard via API
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana-dashboard.json
```

### 3. Tracking con MLflow

```bash
# Iniciar servidor MLflow
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri ./mlruns

# Ver experimentos en http://localhost:5000
```

## 🚨 Detección de Drift

### 1. Generar Baseline

```bash
# Crear baseline con datos de entrenamiento
python scripts/generate_baseline.py \
  --input_file data/training_texts.txt \
  --output_file baseline_emb.pkl
```

### 2. Monitorear Drift

```bash
# Detectar drift en nuevos datos
python drift_detector.py \
  --baseline baseline_emb.pkl \
  --input_texts data/new_batch.txt \
  --threshold 0.12 \
  --slack_webhook $SLACK_WEBHOOK \
  --wandb_project drift-monitor
```

### 3. Alertas Automáticas

El sistema envía alertas cuando:
- Drift > umbral configurado (default: 0.12)
- Performance del modelo decae
- Datos no validan esquema

## 🔄 Reentreno Automático con Prefect

### 1. Iniciar Servidor Prefect

```bash
# Iniciar servidor
prefect server start

# Configurar flow
prefect deployment build flow_retrain.py:retrain_flow -n "production-retrain"
prefect deployment apply "retrain-flow-production-retrain-deployment.json"
```

### 2. Ejecutar Manualmente

```bash
# Ejecutar flow local
python flow_retrain.py

# O via CLI de Prefect
prefect deployment run "retrain-flow/production-retrain"
```

### 3. Monitorear Flows

```bash
# Ver estado en UI: http://localhost:4200
# O via CLI
prefect flow-run ls
```

## 🧪 Testing y Validación

### 1. Tests Locales

```bash
# Ejecutar todos los tests
pytest -v

# Tests específicos
pytest tests/test_app.py -v
pytest tests/test_data_schema.py -v

# Con coverage
pytest --cov=. --cov-report=html
```

### 2. Tests de Integración

```bash
# Test de API completa
python -c "
import requests
import time

# Health check
r = requests.get('http://localhost:8080/health')
print('Health:', r.json())

# Predicción
payload = {'features': list(range(16))}
r = requests.post('http://localhost:8080/predict', json=payload)
print('Prediction:', r.json())

# Métricas
r = requests.get('http://localhost:8080/metrics')
print('Metrics available:', 'predictions_total' in r.text)
"
```

## 🔧 Configuración Avanzada

### 1. Variables de Entorno Completas

```bash
# Modelo
MODEL_PATH=artifacts/latest/model.joblib
MODEL_VERSION=v1.0.0

# Embeddings para drift
EMB_MODEL=all-mpnet-base-v2

# Monitoreo
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Kubernetes
NAMESPACE=default
DOCKER_REGISTRY=ghcr.io
IMAGE_NAME=qna

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2. Configuración de Recursos Kubernetes

```yaml
# Editar k8s/deployment.yaml para ajustar recursos:
resources:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "2Gi"
```

### 3. Autoscaling

```bash
# Habilitar HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment qna-v1 \
  --cpu-percent=70 \
  --min=3 \
  --max=10
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **Modelo no carga**
   ```bash
   # Verificar artefactos
   ls -la artifacts/latest/
   # Revisar logs del pod
   kubectl logs -l app=qna -f
   ```

2. **Tests fallan en CI**
   ```bash
   # Ejecutar localmente para debug
   pytest -v -s
   # Verificar dependencias
   pip check
   ```

3. **Drift detector falla**
   ```bash
   # Verificar baseline
   python -c "import pickle; print(pickle.load(open('baseline_emb.pkl','rb')).shape)"
   # Probar con datos de ejemplo
   echo "test text" > test.txt
   python drift_detector.py --baseline baseline_emb.pkl --input_texts test.txt
   ```

4. **Prometheus no scrapea métricas**
   ```bash
   # Verificar configuración
   curl http://localhost:8080/metrics
   # Revisar targets en Prometheus UI
   ```

### Logs y Debugging

```bash
# Logs de aplicación
kubectl logs -l app=qna -l version=v1 -f

# Logs de sistema
kubectl get events --sort-by=.metadata.creationTimestamp

# Debug de pods
kubectl describe pod <pod-name>
kubectl exec -it <pod-name> -- /bin/bash
```

## 📈 Mejoras Futuras

- **Feature Store**: Integración con Feast o similar
- **Model Registry**: MLflow registry avanzado
- **A/B Testing**: Integración con Optimizely o similar
- **Security**: RBAC, secrets management, TLS
- **Multi-model**: Soporte para múltiples modelos simultáneos
- **Edge Deployment**: soporte para IoT/edge devices

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver archivo `LICENSE` para detalles.

## 🤝 Contribuciones

1. Fork del repositorio
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

## 📞 Soporte

Para dudas o soporte:
- Issues en GitHub
- Documentación extendida en `/docs`
- Email: [tu-email@ejemplo.com]

---

**🎯 Este proyecto demuestra capacidades de MLOps a nivel semi-senior, ideal para portafolio y entrevistas técnicas.**
