
# DataOps Pipeline - CI/CD para Datasets

Un sistema completo de DataOps y MLOps que implementa un pipeline CI/CD para datasets, automatizando la validación, normalización, versionado y generación de reportes de calidad de datos.

## 🎯 Concepto

### Perspectiva Técnica
Este proyecto se ubica en la intersección de DataOps y MLOps, implementando:

- **Infraestructura de datos**: Pipeline CI/CD para datasets usando contenedores (Docker) y versionado (DVC/Git)
- **Automatización completa**: Cuando un nuevo dataset entra o se modifica, el pipeline:
  - ✅ Valida (esquema, duplicados, integridad)
  - ✅ Normaliza (tipos, codificación)
  - ✅ Versiona y guarda en storage distribuido
  - ✅ Genera reportes de calidad (Great Expectations)
- **Baseline model**: Entrena un modelo de referencia para detectar drift cuando lleguen nuevos datos

### Perspectiva de Negocio
Este proyecto es como crear una **biblioteca confiable de datos** para que equipos de inteligencia artificial puedan trabajar sin perder tiempo buscando, corrigiendo o limpiando información.

- **Reduce costos y tiempo**: Datos organizados y listos para usar
- **Evita errores**: Detecta datos incompletos, duplicados, inconsistentes
- **Permite auditoría**: Rastrea cambios en los datos (cumplimiento normativo)
- **Mejora colaboración**: Todos usan la misma versión oficial de los datos

🔹 Es una inversión en calidad, transparencia y eficiencia para cualquier empresa que trabaje con datos.

## 🏗️ Arquitectura

```
DataOps Pipeline/
├── .github/                    # CI/CD workflows
│   └── workflows/
│       ├── data-validation.yml # Pipeline de validación
│       └── data-deployment.yml # Pipeline de despliegue
├── docker/                     # Contenedores Docker
│   ├── Dockerfile.validator    # Validador de datos
│   └── Dockerfile.processor    # Procesador de datos
├── scripts/                    # Scripts del pipeline
│   ├── validate_data.py        # Validación con Great Expectations
│   ├── normalize_data.py       # Normalización y limpieza
│   ├── train_baseline.py       # Modelo baseline
│   └── detect_drift.py         # Detección de drift
├── configs/                    # Configuraciones
│   ├── great_expectations/     # Configuración de validación
│   └── data_schema.yaml        # Esquema de datos
├── data/                       # Datos versionados con DVC
│   ├── raw/                    # Datos crudos
│   ├── processed/              # Datos procesados
│   └── reports/                # Reportes de calidad
├── tests/                      # Tests del pipeline
└── docs/                       # Documentación
```

## 🚀 Guía Rápida de Implementación

### Prerrequisitos
```bash
# Python 3.8+
python --version

# Docker y Docker Compose
docker --version
docker-compose --version

# Git y DVC
git --version
dvc --version
```

> Nota: este repositorio incluye un generador de entorno demo. Si deseas crear los scripts de ejemplo mencionados en este README (validate_data.py, normalize_data.py, train_baseline.py, etc.) y una estructura mínima de datos/configuración, ejecuta:

```bash
python scripts/setup_demo.py --rows 500
```
Esto creará archivos en `scripts/`, `data/`, `configs/` y `docs/` para que puedas correr el pipeline completo end-to-end con los nombres usados en la documentación.

### Paso 1: Configuración del Entorno

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd dataops-pipeline

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar DVC (si no está inicializado)
dvc init
git add .dvc
git commit -m "Initialize DVC"
```

### Paso 2: Configurar Storage Remoto

```bash
# Opción A: Storage local (para desarrollo)
dvc remote add -d myremote /tmp/dvc-storage

# Opción B: Cloud storage (para producción)
# AWS S3
dvc remote add -d myremote s3://my-bucket/dataops-pipeline
dvc remote modify myremote region us-west-2

# Google Cloud
dvc remote add -d myremote gs://my-bucket/dataops-pipeline

# Azure Blob
dvc remote add -d myremote azure://mycontainer/dataops-pipeline
```

### Paso 3: Configurar el Pipeline de Validación

```bash
# 1. Editar configuración de Great Expectations
cp configs/great_expectations/great_expectations.yaml.example configs/great_expectations/great_expectations.yaml

# 2. Definir esquema de datos esperado
nano configs/data_schema.yaml

# 3. Probar validación con datos de ejemplo
python scripts/validate_data.py --data-path data/raw/sample.csv --config-path configs/great_expectations/
```

### Paso 4: Ejecutar el Pipeline Completo

```bash
# 1) Ingesta desde URLs de ejemplo
python scripts/ingest.py --urls example_urls.txt --outdir data --region "Bogotá" --chunk-words 250

# 2) Construir índice FAISS para recuperación
python scripts/index.py --input data/processed/faqs.jsonl --indexdir indexes --embed_model sentence-transformers/all-mpnet-base-v2

# 3) Crear archivo de consultas de ejemplo y evaluar
echo '{"question": "¿Cómo registro una empresa en Bogotá?"}' > data/processed/eval_queries.jsonl
python scripts/eval.py --indexdir indexes --queries data/processed/eval_queries.jsonl

# 4) (Opcional) Entrenamiento LoRA (smoke)
# Prepara un JSONL con campos: input_text, target_text
python scripts/train_lora.py --train data/lora/train.jsonl --validation data/lora/val.jsonl \
  --output_dir out/lora --max_steps 10 --lora_r 8 --lora_alpha 32 --lora_dropout 0.05
```

### Paso 5: Configurar CI/CD con GitHub Actions

Este repositorio incluye `.github/workflows/smoke.yml`, que ejecuta un smoke test rápido (entrenamiento LoRA con `--max_steps` bajo) y evita ejecuciones solapadas mediante `concurrency`.

Recomendaciones:
- Usa Python 3.10 en CI para alinear dependencias.
- Mantén `--max_steps` bajo para validar el pipeline sin costos altos.
- Ajusta triggers según tu flujo (push/PR/main).

Para ejecutarlo manualmente, ve a la pestaña Actions y selecciona “Run workflow”.

## 📊 Monitor de Calidad de Datos

### Métricas Automáticas

El sistema genera automáticamente:

- **Reportes de validez**: Porcentaje de datos que cumplen las expectativas
- **Estadísticas de completitud**: Valores nulos por columna
- **Análisis de duplicados**: Registros duplicados detectados
- **Distribuciones**: Histogramas y estadísticas descriptivas
- **Drift detection**: Comparación con datos históricos

### Visualización

```bash
# Generar dashboard de calidad
python scripts/quality_dashboard.py --data-path data/processed/ --output data/reports/dashboard.html

# Ver reportes en línea de comandos
python scripts/quality_summary.py --report-path data/reports/latest.json
```

## 🐳 Dockerización

### Construir Imágenes

```bash
# Imagen de validación
docker build -f docker/Dockerfile.validator -t dataops-validator .

# Imagen de procesamiento
docker build -f docker/Dockerfile.processor -t dataops-processor .
```

### Ejecutar con Docker Compose

```bash
# Iniciar todo el stack
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ejecutar pipeline manualmente
docker-compose exec validator python scripts/validate_data.py
docker-compose exec processor python scripts/normalize_data.py
```

## 📈 Integración con Modelos de ML

### Entrenamiento Baseline

```bash
# Entrenar modelo inicial
python scripts/train_baseline.py \
  --data-path data/processed/ \
  --model-path models/baseline/ \
  --target-column target \
  --features feature1,feature2,feature3

# Evaluar modelo
python scripts/evaluate_model.py \
  --model-path models/baseline/ \
  --test-data data/processed/test.csv
```

### Detección de Drift

```bash
# Detectar drift en nuevos datos
python scripts/detect_drift.py \
  --baseline-data data/processed/baseline.csv \
  --new-data data/raw/new_data.csv \
  --threshold 0.1
```

## 🔧 Configuración Avanzada

### Personalizar Validaciones

Edita `configs/great_expectations/great_expectations.yaml`:

```yaml
expectations:
  - column: email
    expectations:
      - expect_column_values_to_match_regex:
          regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
  - column: age
    expectations:
      - expect_column_values_to_be_between:
          min_value: 0
          max_value: 150
```

### Configurar Notificaciones

```bash
# Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."

# Email
export SMTP_HOST="smtp.gmail.com"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASS="your-password"
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Tests de validación
pytest tests/test_validation.py -v

# Tests de procesamiento
pytest tests/test_processing.py -v

# Tests de integración
pytest tests/test_integration.py -v
```

## 📚 Documentación Adicional

- [`docs/data_schema.md`](docs/data_schema.md) - Definición de esquemas
- [`docs/monitoring.md`](docs/monitoring.md) - Guía de monitoreo
- [`docs/troubleshooting.md`](docs/troubleshooting.md) - Solución de problemas

## 🤝 Contribución

1. Fork del repositorio
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

- **Issues**: Reporta problemas en GitHub Issues
- **Discusiones**: Usa GitHub Discussions para preguntas
- **Email**: soporte@empresa.com

---

**🎯 Resultado Final**: Un sistema robusto de DataOps que garantiza calidad, consistencia y trazabilidad en tus pipelines de datos, permitiendo a tu equipo enfocarse en generar valor en lugar de limpiar datos.
