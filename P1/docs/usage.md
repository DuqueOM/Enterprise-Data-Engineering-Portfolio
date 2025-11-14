
# DataOps Pipeline - Guía de Uso

## 🚀 Inicio Rápido

### 1. Configuración Inicial
```bash
# Clonar repositorio y configurar entorno
git clone <repository-url>
cd dataops-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Inicializar DVC
dvc init
git add .dvc
git commit -m "Initialize DVC"
```

### 2. Configurar Storage
```bash
# Storage local (desarrollo)
dvc remote add -d myremote /tmp/dvc-storage

# O cloud storage (producción)
dvc remote add -d myremote s3://my-bucket/dataops-pipeline
dvc remote modify myremote region us-west-2
```

### 3. Preparar Datos de Ejemplo
```bash
# Crear directorios
mkdir -p data/raw data/processed data/reports data/metrics models/baseline

# Generar datos de ejemplo
python scripts/generate_sample_data.py --output data/raw/sample_data.csv --rows 1000
```

## 📋 Ejecución del Pipeline

### Opción A: Ejecución Manual Paso a Paso

```bash
# 1. Ingestión de datos
python scripts/ingest_data.py --source /path/to/your/data.csv --output data/raw/

# 2. Validación de calidad
python scripts/validate_data.py --data-path data/raw/ --config-path configs/great_expectations/ --output data/reports/

# 3. Normalización y procesamiento
python scripts/normalize_data.py --input data/raw/ --output data/processed/

# 4. Generar reportes de calidad
python scripts/generate_quality_report.py --data-path data/processed/ --output data/reports/

# 5. Entrenar modelo baseline
python scripts/train_baseline.py --data-path data/processed/ --model-path models/baseline/

# 6. Evaluar modelo
python scripts/evaluate_model.py --model-path models/baseline/ --test-data data/processed/test.csv

# 7. Detección de drift
python scripts/detect_drift.py --baseline-data data/processed/baseline.csv --new-data data/processed/latest.csv
```

### Opción B: Ejecutar Pipeline Completo con DVC

```bash
# Ejecutar todo el pipeline
dvc repro

# Ejecutar etapa específica
dvc repro validate
dvc repro train_baseline

# Ver métricas del pipeline
dvc metrics show
dvc plots show
```

### Opción C: Ejecución con Docker

```bash
# Construir imágenes
docker build -f docker/Dockerfile.validator -t dataops-validator .
docker build -f docker/Dockerfile.processor -t dataops-processor .

# Ejecutar con docker-compose
docker-compose up --build

# Monitorear ejecución
docker-compose logs -f
```

## 📊 Monitoreo y Reportes

### Ver Reportes de Calidad
```bash
# Reporte HTML interactivo
open data/reports/quality_dashboard.html

# Resumen en consola
python scripts/quality_summary.py --report-path data/reports/latest.json

# Métricas del pipeline
dvc metrics show
```

### Monitoreo en Tiempo Real
```bash
# Iniciar dashboard de monitoreo
streamlit run scripts/monitoring_dashboard.py

# O con Gradio
gradio scripts/monitoring_app.py
```

## 🔧 Configuración Avanzada

### Personalizar Validaciones
Edita `configs/data_schema.yaml` para modificar reglas de negocio:

```yaml
columns:
  nueva_columna:
    type: "string"
    nullable: false
    pattern: "^[A-Z]{3}[0-9]{4}$"
    description: "Identificador personalizado"
```

### Configurar Notificaciones
```bash
# Configurar Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Configurar email
export SMTP_HOST="smtp.gmail.com"
export SMTP_USER="tu-email@gmail.com"
export SMTP_PASS="tu-password"

# Enviar reporte automáticamente
python scripts/send_notifications.py --report-path data/reports/latest.json
```

### Programar Ejecuciones
```bash
# Usar crontab para ejecución diaria
0 2 * * * cd /path/to/dataops-pipeline && dvc repro

# O con Airflow/Prefect
python scripts/schedule_pipeline.py --schedule "daily" --time "02:00"
```

## 🧪 Testing y Validación

### Ejecutar Tests
```bash
# Todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_validation.py -v
pytest tests/test_processing.py -v
pytest tests/test_integration.py -v

# Con cobertura
pytest tests/ --cov=scripts --cov-report=html
```

### Validación de Datos Manual
```bash
# Validar dataset específico
python scripts/validate_data.py \
  --data-path data/raw/new_dataset.csv \
  --config-path configs/great_expectations/ \
  --output data/reports/new_dataset_validation/

# Comparar con schema
python scripts/validate_schema.py \
  --data-path data/raw/dataset.csv \
  --schema-path configs/data_schema.yaml
```

## 🚨 Solución de Problemas

### Errores Comunes

1. **Error de validación de schema**
   ```bash
   # Ver detalles del error
   cat data/reports/validation_report.json | jq '.validation_results'
   
   # Corregir y re-ejecutar
   python scripts/fix_data_issues.py --input data/raw/problematic.csv --output data/raw/fixed.csv
   ```

2. **Problemas de conexión con storage remoto**
   ```bash
   # Verificar configuración de DVC
   dvc remote list
   dvc remote modify myremote url
   
   # Probar conexión
   dvc push
   ```

3. **Fallo en entrenamiento de modelo**
   ```bash
   # Ver logs de entrenamiento
   cat models/baseline/training.log
   
   # Re-entrenar con diferentes parámetros
   python scripts/train_baseline.py --data-path data/processed/ --model-path models/baseline_v2/ --params configs/model_params.yaml
   ```

### Depuración
```bash
# Habilitar logging detallado
export DVC_LOG_LEVEL=DEBUG
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ejecutar con modo debug
python scripts/validate_data.py --data-path data/raw/ --debug

# Ver estado del pipeline
dvc status
dvc dag
```

## 📈 Integración con Sistemas Externos

### Conectar a Base de Datos
```bash
# Configurar conexión
export DATABASE_URL="postgresql://user:pass@host:port/db"

# Extraer datos de BD
python scripts/extract_from_db.py --query "SELECT * FROM customers" --output data/raw/db_extract.csv
```

### API para Monitoreo
```bash
# Iniciar API server
uvicorn scripts.api:app --host 0.0.0.0 --port 8000

# Endpoints disponibles:
# GET /health - Estado del sistema
# GET /metrics - Métricas del pipeline
# POST /validate - Validar nuevos datos
# GET /reports - Lista de reportes disponibles
```

## 🔄 Mantenimiento del Sistema

### Limpieza de Datos
```bash
# Limpiar archivos temporales
python scripts/cleanup.py --dry-run
python scripts/cleanup.py --execute

# Archivar datos antiguos
python scripts/archive_data.py --older-than 30days --destination archive/
```

### Actualización del Sistema
```bash
# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Migrar configuración
python scripts/migrate_config.py --from-version 1.0 --to-version 2.0

# Re-entrenar modelos con nueva configuración
dvc repro train_baseline
```

---

## 📞 Soporte

- **Documentación técnica**: `/docs/`
- **Issues y problemas**: GitHub Issues
- **Consultas técnicas**: GitHub Discussions
- **Contacto directo**: soporte@empresa.com

**💡 Tip**: Para empezar rápidamente, ejecuta `python scripts/setup_demo.py` que configurará un entorno de demostración completo con datos de ejemplo.
