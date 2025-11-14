# 🏢 PYME QA Dataset - DataOps & CI/CD Pipeline

[![DataOps Pipeline](https://github.com/yourusername/p2-dataset-dataops/actions/workflows/dataops.yml/badge.svg)](https://github.com/yourusername/p2-dataset-dataops/actions/workflows/dataops.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Implementación profesional de DataOps + CI/CD para datasets**  
> Un sistema automatizado para recopilar, validar, versionar y desplegar datos de QA para trámites administrativos de PYMEs.

## 🎯 ¿Qué es este proyecto?

Este proyecto implementa una solución completa de **DataOps** que trata los datos como un producto. En lugar de manejar archivos Excel desorganizados, creamos un pipeline automatizado que:

✅ **Ahorra tiempo y costos** - Evita errores manuales en los datos  
✅ **Mejora la calidad** - Validación automática y métricas de calidad  
✅ **Facilita colaboración** - Equipos pueden trabajar con datos confiables  
✅ **Control de versiones** - Siempre sabes qué versión de los datos se usó  
✅ **Escalable** - Se puede replicar en otros proyectos sin empezar de cero  

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│   Ingestion      │───▶│   Validation    │
│   (Websites)    │    │   (Scripts)      │    │   (Schema/QA)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Annotation    │◀───│   Processing     │◀───│   Quality       │
│   (Label Studio)│    │   (Cleaning)     │    │   Analysis      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Deployment    │◀───│   Model Train    │◀───│   Versioning    │
│   (Production)  │    │   (Baseline)     │    │   (DVC/Git)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Estructura del Proyecto

```
P2/
├── .github/workflows/          # CI/CD pipelines
│   └── dataops.yml            # GitHub Actions workflow
├── data/                       # Datos (versionados con DVC)
│   ├── raw/                   # Datos originales (no en Git)
│   ├── processed/             # Datos procesados
│   └── annotation/            # Datos para anotación
├── scripts/                    # Scripts del pipeline
│   ├── ingest.py              # Recolección de datos
│   ├── clean.py               # Limpieza de datos
│   ├── validate_schema.py     # Validación de esquema
│   ├── data_quality.py        # Análisis de calidad
│   ├── train_baseline.py      # Modelo baseline
│   └── annotate.py            # Preparación para anotación
├── notebooks/                  # Análisis exploratorio
│   └── EDA.ipynb              # Jupyter notebook para EDA
├── tests/                      # Tests automatizados
│   └── test_schema.py         # Tests de validación
├── models/                     # Modelos entrenados
├── reports/                    # Reportes de calidad
├── metrics/                    # Métricas del pipeline
├── dvc.yaml                   # Definición del pipeline DVC
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

## 🚀 Guía de Inicio Rápido

### Prerrequisitos

- Python 3.9 o superior
- Git
- Opcional: Docker (para Label Studio)
- Opcional: Cuenta en GitHub/GitLab (para CI/CD)

### Paso 1: Clonar y Configurar Entorno

```bash
# Clonar el repositorio
git clone <URL-DEL-REPOSITORIO>
cd P2

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 2: Configurar DVC (Data Version Control)

```bash
# Inicializar DVC
dvc init

# Configurar remote storage (opcional)
# Ejemplo con Google Drive:
dvc remote add -d myremote gdrive://<ID-CARPETA>
# O con S3:
dvc remote add -d myremote s3://bucket-name/path

# Push datos existentes (si hay)
dvc push
```

### Paso 3: Ejecutar el Pipeline Localmente

```bash
# 1. Recolectar datos (con flags opcionales)
python scripts/ingest.py \
  --output data/processed/faqs.jsonl \
  --region "Antioquia" \
  --chunk-size 1500

# 2. Limpiar datos
python scripts/clean.py

# 3. Validar esquema y calidad
python scripts/validate_schema.py

# 4. Análisis de calidad
python scripts/data_quality.py

# 5. Entrenar modelo baseline
python scripts/train_baseline.py

# O ejecutar todo con DVC
dvc repro
```

### Paso 4: Configurar Anotación (Opcional)

```bash
# Iniciar Label Studio con Docker
docker run -it -p 8080:8080 -v $(pwd)/data:/label-studio/data heartexlabs/label-studio:latest

# Configurar variables de entorno
export LABEL_STUDIO_URL="http://localhost:8080"
export LABEL_STUDIO_API_KEY="TU-API-KEY"
export LABEL_STUDIO_PROJECT_ID="1"

# Importar tareas para anotación
python scripts/annotate.py
```

### Paso 5: Analizar Resultados

```bash
# Abrir Jupyter para análisis exploratorio
jupyter notebook notebooks/EDA.ipynb

# Ver reporte de calidad
open reports/quality_report.html
```

## 🔧 Configuración del Pipeline

### Personalizar Fuentes de Datos

Edita `scripts/ingest.py` para agregar tus propias URLs:

```python
urls = [
    ("https://sitio-gubernamental-1.gov/faq", "Antioquia"),
    ("https://sitio-gubernamental-2.gov/faq", "Valle del Cauca"),
    # Agrega más URLs aquí
]
```

### Configurar Validaciones

Modifica `scripts/validate_schema.py` para ajustar reglas de validación:

```python
SCHEMA = {
    "required": ["id", "source_url", "text", "date_fetched"],
    "properties": {
        "text": {"minLength": 50},  # Mínimo 50 caracteres
        # ... más reglas
    }
}
```

### Personalizar Métricas de Calidad

Edita `scripts/data_quality.py` para agregar métricas personalizadas:

```python
def custom_quality_checks(df):
    # Agrega tus propias validaciones
    pass
```

## 🔄 CI/CD Pipeline

El pipeline automatizado se ejecuta automáticamente cuando:

- **Push a main/develop**: Ejecuta validación, tests y entrenamiento
- **Pull Request**: Ejecuta tests de calidad
- **Manual**: Puede dispararse manualmente desde GitHub

### Stages del Pipeline

1. **Data Validation**: Valida esquema y calidad de datos
2. **Data Tests**: Ejecuta tests automatizados
3. **Security Scan**: Escanea vulnerabilidades
4. **Model Monitoring**: Verifica performance del modelo
5. **Deploy**: Despliega a staging/producción

### Configurar Secrets en GitHub

Ve a `Settings > Secrets and variables > Actions` y configura:

- `DVC_REMOTE_URL`: URL del storage remoto
- `SLACK_WEBHOOK_URL`: Para notificaciones (opcional)

## 📊 Métricas y Monitoreo

### Métricas Automáticas

El pipeline genera automáticamente:

- **Completitud**: Porcentaje de datos no nulos
- **Unicidad**: Detección de duplicados
- **Consistencia**: Validación de formatos
- **Calidad de texto**: Longitud, caracteres especiales
- **Performance del modelo**: Accuracy, features importantes

### Reportes

- **HTML Report**: `reports/quality_report.html`
- **JSON Metrics**: `metrics/quality.json`
- **Model Metrics**: `models/metrics.json`

## 🐛 Troubleshooting

### Problemas Comunes

**Error: "File not found" en validación**
```bash
# Asegúrate de haber ejecutado los pasos anteriores
python scripts/ingest.py
python scripts/clean.py
```

**Error: DVC remote no configurado**
```bash
# Configura un remote o usa local storage
dvc remote add -d local /tmp/dvc-storage
```

**Error: Dependencias faltantes**
```bash
# Reinstala todas las dependencias
pip install -r requirements.txt --force-reinstall
```

### Logs y Debugging

```bash
# Ver logs detallados
export PYTHONPATH=$(pwd)
python -v scripts/validate_schema.py

# Ver estado del pipeline DVC
dvc status
dvc dag
```

## 🚀 Despliegue a Producción

### Opción 1: GitHub Actions (Automático)

El pipeline se despliega automáticamente al hacer push a `main`.

### Opción 2: Manual

```bash
# 1. Versionar datos
dvc add data/processed/faqs_clean.jsonl
dvc push

# 2. Crear tag de versión
git tag dataset-v1.0.0
git push origin dataset-v1.0.0

# 3. Desplegar a producción
# (agrega comandos específicos de tu infraestructura)
```

### Integración con Hugging Face

```python
from datasets import Dataset
import json

# Cargar datos
with open('data/processed/faqs_clean.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Crear dataset
dataset = Dataset.from_list(data)

# Subir a Hugging Face
dataset.push_to_hub("tu-username/pyme-qa-dataset")
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests con coverage
pytest tests/ --cov=scripts --cov-report=html

# Ejecutar tests específicos
pytest tests/test_schema.py -v
```

## 📈 Escalando el Proyecto

### Para Datasets Más Grandes

1. **Procesamiento Paralelo**:
```python
from multiprocessing import Pool
with Pool(processes=4) as pool:
    results = pool.map(process_url, urls)
```

2. **Cloud Storage**:
```bash
# Configurar S3
dvc remote add -d s3 s3://bucket-name
dvc push
```

3. **Distributed Computing**:
Considera usar Dask o Spark para datasets muy grandes.

### Para Múltiples Fuentes

```python
# Agregar soporte para APIs, bases de datos, etc.
def fetch_from_api(endpoint):
    # Lógica para API
    pass

def fetch_from_database(query):
    # Lógica para base de datos
    pass
```

## 🤝 Contribución

1. Fork el repositorio
2. Crear rama de feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request

## 📄 Licencia

MIT License - ver archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [DVC](https://dvc.org/) - Para versionado de datos
- [Label Studio](https://labelstud.io/) - Para anotación de datos
- [Pandera](https://pandera.readthedocs.io/) - Para validación de datos
- [Scikit-learn](https://scikit-learn.org/) - Para modelos baseline

## 📞 Soporte

- 📧 Email: [tu-email@ejemplo.com]
- 💬 Slack: [canal-de-soporte]
- 📖 Docs: [enlace-a-documentación]
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/p2-dataset-dataops/issues)

---

**🎉 ¡Listo! Ahora tienes un pipeline de DataOps profesional automatizado.**

Para empezar, simplemente ejecuta:
```bash
git clone <URL>
cd P2
pip install -r requirements.txt
python scripts/ingest.py
```

Y sigue los pasos descritos en esta guía.


---

## Integración opcional con P4 [P4]

Para emitir los datos directamente al formato/ubicación esperada por P4, usa:

```bash
python scripts/ingest.py \
  --output ../P4/data/raw/faqs_p2_compatible.jsonl \
  --region "Bogotá" \
  --chunk-size 1500  # [P4]
```

Notas:
- El flag `--output` es opcional y no cambia el comportamiento por defecto.  # [P4]
- El formato generado es compatible con P2 y P4 (JSONL con campos id, source_url, region, text, date_fetched).  # [P4]
- Esto no afecta la ejecución independiente del proyecto P2.  # [P4]

