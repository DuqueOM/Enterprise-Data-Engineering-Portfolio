# 🤖 P4 - Servicio de Atención Automatizada con IA

**Sistema integrado de atención automatizada que recopila, organiza y entrega respuestas citadas a consultas administrativas**

## TL;DR

```bash
# Local (venv)
cd P4 && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/ingestion/scraper.py && \
python src/processing/validate_and_process.py --sanitize && \
python -m src.search.index_knowledge_base --smoke && \
uvicorn src.api.main:app --host 0.0.0.0 --port 8081

# Docker Compose
docker-compose up --build -d

# CI smoke (GitHub Actions)
# .github/workflows/ci_smoke.yml ejecuta: ruff + pytest + build índice --smoke
```

## 🎯 Concepto

Un servicio de atención automatizada que hace tres cosas valiosas:
1. **Recopila información oficial** (leyes, formularios, guías)
2. **Organiza esa información** para que sea fácil de buscar por tema o pregunta
3. **Entrega respuestas claras y citadas** a preguntas concretas con versionado y auditoría

### ¿Por qué es útil para una organización/pyme?
- ✅ **Reduce tiempo de respuesta** en atención a consultas administrativas
- ✅ **Evita respuestas obsoletas** porque el contenido está versionado y actualizable
- ✅ **Permite auditar** de dónde sale cada respuesta (fuente y fecha)
- ✅ **Similar a tener un asistente experto** que siempre cita el documento oficial

## 🏗️ Arquitectura Integrada

El proyecto P4 integra las capacidades de P1, P2 y P3:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   P1 - DataOps  │    │   P2 - QA Data  │    │   P3 - AIOps    │
│   (Validación)  │    │   (Scraping)    │    │   (API/Deploy)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │      P4         │
                    │  Servicio QA    │
                    │  Integrado      │
                    └─────────────────┘
```

### Flujo del Sistema

1. **Ingestión de Datos** (P2) → Recopila información oficial de fuentes web
2. **Validación y Procesamiento** (P1) → Valida calidad y normaliza datos
3. **Indexación y Búsqueda** → Organiza información para búsqueda eficiente
4. **API de Consultas** (P3) → Entrega respuestas citadas vía API
5. **Monitoreo y Versionado** (P1+P3) → Audita cambios y mantiene calidad

## 📁 Estructura del Proyecto

```
P4/
├── .github/workflows/          # CI/CD integrado
├── data/                       # Datos versionados (P1)
│   ├── raw/                   # Datos originales
│   ├── processed/             # Datos procesados
│   └── knowledge_base/        # Base de conocimiento indexada
├── src/                       # Código fuente principal
│   ├── ingestion/             # Módulo de ingestión (P2)
│   ├── processing/            # Módulo de procesamiento (P1)
│   ├── search/                # Motor de búsqueda
│   ├── api/                   # API FastAPI (P3)
│   └── monitoring/            # Monitoreo (P3)
├── scripts/                   # Scripts de automatización
├── configs/                   # Configuraciones
├── tests/                     # Tests
├── docker/                    # Docker (P1+P3)
├── k8s/                       # Kubernetes (P3)
├── docs/                      # Documentación
└── requirements.txt           # Dependencias integradas
```

## 🚀 Guía de Inicio Rápido

### Prerrequisitos
- Python 3.9+
- Docker y Docker Compose
- Git y DVC

### Paso 1: Configuración del Entorno

```bash
# Clonar el repositorio
git clone <repository-url>
cd P4

# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar DVC
dvc init
```

### Paso 2: Configurar Fuentes de Datos

```bash
# Editar configuración de fuentes
nano configs/sources.yaml

# Ejemplo:
sources:
  - name: "DIAN - Formularios"
    url: "https://www.dian.gov.co/formularios"
    type: "forms"
    region: "Nacional"
  - name: "Cámara de Comercio"
    url: "https://www.camaracomercio.com.co"
    type: "guides"
    region: "Bogotá"
```

### Paso 3: Ejecutar Pipeline Completo

```bash
# 1. Ingestión de datos
python src/ingestion/scraper.py

# 2. Procesamiento y validación
python src/processing/validate_and_process.py

# 3. Indexación para búsqueda
python src/search/index_knowledge_base.py

# 4. Iniciar API
uvicorn src.api.main:app --host 0.0.0.0 --port 8081
```

### Paso 4: Probar el Sistema

```bash
# Health check
curl http://localhost:8081/health

# Consulta de ejemplo
curl -X POST http://localhost:8081/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué documentos necesito para registrar una empresa?",
    "context": "nueva empresa, Bogotá"
  }'
```

## 🔧 Módulos Principales

### 1. Ingestión de Datos (heredado de P2)
- **Webscraping inteligente** de fuentes oficiales
- **Procesamiento de texto** y extracción de estructura
- **Detección de cambios** en fuentes web

### 2. Procesamiento y Validación (heredado de P1)
- **Validación de calidad** con Great Expectations
- **Normalización de datos** y estandarización
- **Detección de duplicados** y validación de esquemas

### 3. Motor de Búsqueda
- **Búsqueda semántica** con embeddings
- **Recuperación híbrida** (keyword + semántica)
- **Ranking de resultados** por relevancia

### 4. API de Consultas (heredado de P3)
- **Endpoints REST** para consultas
- **Respuestas citadas** con fuentes y fechas
- **Métricas y monitoreo** con Prometheus

### 5. Sistema de Auditoría
- **Versionado de contenido** con DVC
- **Trazabilidad de respuestas** 
- **Reportes de cambios** y actualizaciones

## 📊 API Endpoints

### Consultas
```http
POST /api/v1/query
{
  "question": "¿Qué documentos necesito para registrar una empresa?",
  "context": "nueva empresa, Bogotá",
  "max_results": 5
}
```

**Respuesta:**
```json
{
  "answer": "Para registrar una empresa en Bogotá necesitas...",
  "sources": [
    {
      "title": "Guía de Constitución de Empresas",
      "url": "https://www.camaracomercio.com.co/guia",
      "snippet": "...",
      "date": "2024-01-15",
      "confidence": 0.95
    }
  ],
  "metadata": {
    "model_version": "v2.1.0",
    "processing_time": 0.23,
    "total_sources": 3
  }
}
```

### Administración
```http
GET  /health
POST /api/v1/ingest
POST /api/v1/index
```

## 🐳 Despliegue con Docker

```bash
# Construir y ejecutar
docker-compose up -d

# Servicios disponibles:
# API: http://localhost:8081
# Monitoreo: http://localhost:3000 (Grafana)
# Métricas: http://localhost:9090 (Prometheus)
```

## ☸️ Despliegue en Kubernetes

```bash
# Desplegar stack completo
kubectl apply -f k8s/

# Verificar despliegue
kubectl get pods -l app=p4-qa-service
```

## 🔄 CI/CD Pipeline

El pipeline automatizado ejecuta:

1. **Data Ingestion** → Recopila nueva información
2. **Quality Validation** → Valida datos nuevos
3. **Index Update** → Actualiza base de conocimiento
4. **Model Testing** → Prueba calidad de respuestas
5. **Deploy** → Despliega actualizaciones con canary

## 📈 Monitoreo y Métricas

### Métricas Clave
- **Query Response Time** → Tiempo de respuesta
- **Answer Quality** → Calidad de respuestas
- **Source Coverage** → Cobertura de fuentes
- **User Satisfaction** → Satisfacción del usuario

### Alertas
- Respuestas con baja confianza
- Fuentes desactualizadas
- Cambios en regulaciones
- Caídas de servicio

## 🧪 Testing

```bash
# Tests completos
pytest tests/ -v

# Tests de integración
pytest tests/test_integration.py -v

# Tests de API
pytest tests/test_api.py -v
```

## 📝 Licencia

MIT License - ver archivo `LICENSE` para detalles.

## 🤝 Contribución

1. Fork del repositorio
2. Crear feature branch
3. Commit cambios
4. Push y Pull Request

---

**🎯 Este proyecto integra P1, P2 y P3 para crear un servicio completo de atención automatizada con respuestas citadas y auditables.**
