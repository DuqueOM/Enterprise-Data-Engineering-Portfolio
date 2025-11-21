# 🤖 Enterprise QA Service

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Production-Grade Intelligent Q&A System**  
> Integrated automated service that collects, organizes, and delivers cited responses to administrative queries.

## 🚀 TL;DR

```bash
# Local (venv)
cd enterprise-qa-service && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/ingestion/scraper.py && \
python src/processing/validate_and_process.py --sanitize && \
python -m src.search.index_knowledge_base --smoke && \
uvicorn src.api.main:app --host 0.0.0.0 --port 8081

# Docker Compose
docker-compose up --build -d

# CI smoke (GitHub Actions)
# .github/workflows/ci_smoke.yml runs: ruff + pytest + build index --smoke
```

## 🎯 Overview

An automated Q&A service that performs three valuable functions:
1. **Collects official information** (laws, forms, guides)
2. **Organizes this information** to make it easily searchable by topic or question
3. **Delivers clear, cited responses** to specific questions with versioning and audit trails

### Business Value
- ✅ **Reduces Response Time**: Fast answers to administrative queries
- ✅ **Prevents Outdated Responses**: Versioned and updatable content
- ✅ **Enables Auditing**: Track source and date for each answer
- ✅ **Expert Assistant**: Always cites official documents

## 🏗️ Integrated Architecture

This project integrates capabilities from the entire portfolio:

```
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│  DataOps Pipeline  │    │  Smart Ingestion  │    │  MLOps System     │
│  (Validation)     │    │  (Scraping)       │    │  (API/Deploy)     │
└────────────────────┘    └────────────────────┘    └────────────────────┘
         │                       │                       │
         └──────────────────────────┴──────────────────────────┘
                                 │
                    ┌────────────────────┐
                    │  Enterprise QA    │
                    │     Service       │
                    │   (Integrated)   │
                    └────────────────────┘
```

### System Flow

1. **Data Ingestion** → Collects official information from web sources
2. **Validation & Processing** → Validates quality and normalizes data
3. **Indexing & Search** → Organizes information for efficient retrieval
4. **Query API** → Delivers cited responses via API
5. **Monitoring & Versioning** → Audits changes and maintains quality

## 📁 Project Structure

```
enterprise-qa-service/
├── .github/workflows/          # Integrated CI/CD
├── data/                       # Versioned data
│   ├── raw/                   # Raw data
│   ├── processed/             # Processed data
│   └── knowledge_base/        # Indexed knowledge base
├── src/                       # Main source code
│   ├── ingestion/             # Ingestion module
│   ├── processing/            # Processing module
│   ├── search/                # Search engine
│   ├── api/                   # FastAPI
│   └── monitoring/            # Monitoring
├── scripts/                   # Automation scripts
├── configs/                   # Configurations
├── tests/                     # Tests
├── docker/                    # Docker
├── k8s/                       # Kubernetes
├── docs/                      # Documentation
└── requirements.txt           # Integrated dependencies
```

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Docker and Docker Compose
- Git and DVC

### Step 1: Environment Setup

```bash
# Clone the repository
git clone https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio.git
cd Enterprise-Data-Engineering-Portfolio/enterprise-qa-service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize DVC
dvc init
```

### Step 2: Configure Data Sources

```bash
# Edit sources configuration
nano configs/sources.yaml

# Example:
sources:
  - name: "Tax Authority - Forms"
    url: "https://www.dian.gov.co/formularios"
    type: "forms"
    region: "National"
  - name: "Chamber of Commerce"
    url: "https://www.camaracomercio.com.co"
    type: "guides"
    region: "Bogotá"
```

### Step 3: Run Complete Pipeline

```bash
# 1. Data ingestion
python src/ingestion/scraper.py

# 2. Processing and validation
python src/processing/validate_and_process.py

# 3. Indexing for search
python src/search/index_knowledge_base.py

# 4. Start API
uvicorn src.api.main:app --host 0.0.0.0 --port 8081
```

### Step 4: Test the System

```bash
# Health check
curl http://localhost:8081/health

# Example query
curl -X POST http://localhost:8081/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What documents do I need to register a company?",
    "context": "new company, Bogotá"
  }'
```

## 🔧 Main Modules

### 1. Data Ingestion
- **Intelligent web scraping** from official sources
- **Text processing** and structure extraction
- **Change detection** in web sources

### 2. Processing & Validation
- **Quality validation** with Great Expectations
- **Data normalization** and standardization
- **Duplicate detection** and schema validation

### 3. Search Engine
- **Semantic search** with embeddings
- **Hybrid retrieval** (keyword + semantic)
- **Result ranking** by relevance

### 4. Query API
- **REST endpoints** for queries
- **Cited responses** with sources and dates
- **Metrics and monitoring** with Prometheus

### 5. Audit System
- **Content versioning** with DVC
- **Response traceability** 
- **Change reports** and updates

## 📊 API Endpoints

### Queries
```http
POST /api/v1/query
{
  "question": "What documents do I need to register a company?",
  "context": "new company, Bogotá",
  "max_results": 5
}
```

**Response:**
```json
{
  "answer": "To register a company in Bogotá you need...",
  "sources": [
    {
      "title": "Company Registration Guide",
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

### Administration
```http
GET  /health
POST /api/v1/ingest
POST /api/v1/index
```

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# Available services:
# API: http://localhost:8081
# Monitoring: http://localhost:3000 (Grafana)
# Metrics: http://localhost:9090 (Prometheus)
```

## ☸️ Kubernetes Deployment

```bash
# Deploy complete stack
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -l app=enterprise-qa-service
```

## 🔄 CI/CD Pipeline

The automated pipeline executes:

1. **Data Ingestion** → Collects new information
2. **Quality Validation** → Validates new data
3. **Index Update** → Updates knowledge base
4. **Model Testing** → Tests response quality
5. **Deploy** → Deploys updates with canary

## 📈 Monitoring and Metrics

### Key Metrics
- **Query Response Time** → Response latency
- **Answer Quality** → Response quality
- **Source Coverage** → Source coverage
- **User Satisfaction** → User satisfaction

### Alerts
- Low confidence responses
- Outdated sources
- Regulatory changes
- Service outages

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Integration tests
pytest tests/test_integration.py -v

# API tests
pytest tests/test_api.py -v
```

## 📝 License

MIT License - see `LICENSE` file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push and Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio/discussions)
- **Documentation**: [Main README](../README.md)

---

**🎯 This project integrates capabilities from the entire portfolio to create a complete automated Q&A service with cited and auditable responses.**
