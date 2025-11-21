# 🔄 DataOps Validation Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DVC](https://img.shields.io/badge/DVC-enabled-blue.svg)](https://dvc.org/)

> **Production-Grade DataOps System**  
> Complete CI/CD pipeline for datasets with automated validation, normalization, versioning, and quality reporting.

## 🎯 Overview

### Technical Perspective
This project sits at the intersection of DataOps and MLOps, implementing:

- **Data Infrastructure**: CI/CD pipeline for datasets using containers (Docker) and versioning (DVC/Git)
- **Complete Automation**: When a new dataset enters or is modified, the pipeline:
  - ✅ Validates (schema, duplicates, integrity)
  - ✅ Normalizes (types, encoding)
  - ✅ Versions and stores in distributed storage
  - ✅ Generates quality reports (Great Expectations)
- **Baseline Model**: Trains a reference model to detect drift when new data arrives

### Business Value
This project creates a **trusted data library** so AI teams can work without wasting time searching, correcting, or cleaning information.

- **Reduces Costs & Time**: Organized, ready-to-use data
- **Prevents Errors**: Detects incomplete, duplicate, or inconsistent data
- **Enables Auditing**: Tracks data changes (regulatory compliance)
- **Improves Collaboration**: Everyone uses the same official data version

🔹 An investment in quality, transparency, and efficiency for any data-driven organization.

## 🏗️ Architecture

```
dataops-validation-pipeline/
├── .github/                    # CI/CD workflows
│   └── workflows/
│       └── smoke.yml           # Smoke test pipeline
├── docker/                     # Docker containers
│   ├── Dockerfile.validator    # Data validator
│   └── Dockerfile.processor    # Data processor
├── scripts/                    # Pipeline scripts
│   ├── ingest.py               # Data ingestion
│   ├── index.py                # FAISS indexing
│   ├── eval.py                 # Evaluation
│   ├── train_lora.py           # LoRA training
│   ├── validate_data.py        # Great Expectations validation
│   └── setup_demo.py           # Demo environment generator
├── configs/                    # Configurations
│   ├── great_expectations/     # Validation configuration
│   └── data_schema.yaml        # Data schema
├── data/                       # DVC-versioned data
│   ├── raw/                    # Raw data
│   ├── processed/              # Processed data
│   └── reports/                # Quality reports
├── docs/                       # Documentation
├── notebooks/                  # Jupyter notebooks
├── space/                      # Deployment space
├── dvc.yaml                    # DVC pipeline definition
├── docker-compose.yml          # Multi-service orchestration
└── requirements.txt            # Python dependencies
```

## 🚀 Quick Start Guide

### Prerequisites
```bash
# Python 3.10+
python --version

# Docker and Docker Compose
docker --version
docker-compose --version

# Git and DVC
git --version
dvc --version
```

> **Note**: This repository includes a demo environment generator. To create example scripts (validate_data.py, normalize_data.py, train_baseline.py, etc.) and minimal data/config structure, run:

```bash
python scripts/setup_demo.py --rows 500
```
This will create files in `scripts/`, `data/`, `configs/` and `docs/` so you can run the complete end-to-end pipeline with the names used in the documentation.

### Step 1: Environment Setup

```bash
# 1. Clone the repository
git clone https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio.git
cd Enterprise-Data-Engineering-Portfolio/dataops-validation-pipeline

# 2. Create virtual environment (or use conda)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize DVC (if not initialized)
dvc init
git add .dvc
git commit -m "Initialize DVC"
```

### Step 2: Configure Remote Storage

```bash
# Option A: Local storage (for development)
dvc remote add -d myremote /tmp/dvc-storage

# Option B: Cloud storage (for production)
# AWS S3
dvc remote add -d myremote s3://my-bucket/dataops-pipeline
dvc remote modify myremote region us-west-2

# Google Cloud
dvc remote add -d myremote gs://my-bucket/dataops-pipeline

# Azure Blob
dvc remote add -d myremote azure://mycontainer/dataops-pipeline
```

### Step 3: Configure Validation Pipeline

```bash
# 1. Edit Great Expectations configuration
cp configs/great_expectations/great_expectations.yaml.example configs/great_expectations/great_expectations.yaml

# 2. Define expected data schema
nano configs/data_schema.yaml

# 3. Test validation with sample data
python scripts/validate_data.py --data-path data/raw/sample.csv --config-path configs/great_expectations/
```

### Step 4: Run Complete Pipeline

```bash
# 1) Ingest from example URLs
python scripts/ingest.py --urls example_urls.txt --outdir data --region "Bogotá" --chunk-words 250

# 2) Build FAISS index for retrieval
python scripts/index.py --input data/processed/faqs.jsonl --indexdir indexes --embed_model sentence-transformers/all-mpnet-base-v2

# 3) Create sample queries and evaluate
echo '{"question": "How do I register a company in Bogotá?"}' > data/processed/eval_queries.jsonl
python scripts/eval.py --indexdir indexes --queries data/processed/eval_queries.jsonl

# 4) (Optional) LoRA training (smoke test)
# Prepare JSONL with fields: input_text, target_text
python scripts/train_lora.py --train data/lora/train.jsonl --validation data/lora/val.jsonl \
  --output_dir out/lora --max_steps 10 --lora_r 8 --lora_alpha 32 --lora_dropout 0.05
```

### Step 5: Configure CI/CD with GitHub Actions

This repository includes `.github/workflows/smoke.yml`, which runs a quick smoke test (LoRA training with low `--max_steps`) and prevents overlapping executions via `concurrency`.

**Recommendations:**
- Use Python 3.10 in CI to align dependencies
- Keep `--max_steps` low to validate pipeline without high costs
- Adjust triggers according to your workflow (push/PR/main)

To run manually, go to the Actions tab and select "Run workflow".

## 📊 Data Quality Monitoring

### Automatic Metrics

The system automatically generates:

- **Validity Reports**: Percentage of data meeting expectations
- **Completeness Statistics**: Null values per column
- **Duplicate Analysis**: Detected duplicate records
- **Distributions**: Histograms and descriptive statistics
- **Drift Detection**: Comparison with historical data

### Visualization

```bash
# Generate quality dashboard
python scripts/quality_dashboard.py --data-path data/processed/ --output data/reports/dashboard.html

# View reports in command line
python scripts/quality_summary.py --report-path data/reports/latest.json
```

## 🐳 Dockerization

### Build Images

```bash
# Validation image
docker build -f docker/Dockerfile.validator -t dataops-validator .

# Processing image
docker build -f docker/Dockerfile.processor -t dataops-processor .
```

### Run with Docker Compose

```bash
# Start the entire stack
docker-compose up -d

# View logs
docker-compose logs -f

# Run pipeline manually
docker-compose exec validator python scripts/validate_data.py
docker-compose exec processor python scripts/normalize_data.py
```

## 📈 ML Model Integration

### Baseline Training

```bash
# Train initial model
python scripts/train_baseline.py \
  --data-path data/processed/ \
  --model-path models/baseline/ \
  --target-column target \
  --features feature1,feature2,feature3

# Evaluate model
python scripts/evaluate_model.py \
  --model-path models/baseline/ \
  --test-data data/processed/test.csv
```

### Drift Detection

```bash
# Detect drift in new data
python scripts/detect_drift.py \
  --baseline-data data/processed/baseline.csv \
  --new-data data/raw/new_data.csv \
  --threshold 0.1
```

## 🔧 Advanced Configuration

### Customize Validations

Edit `configs/great_expectations/great_expectations.yaml`:

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

### Configure Notifications

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
# Run all tests
pytest tests/ -v

# Validation tests
pytest tests/test_validation.py -v

# Processing tests
pytest tests/test_processing.py -v

# Integration tests
pytest tests/test_integration.py -v
```

## 📚 Additional Documentation

- [`docs/data_schema.md`](docs/data_schema.md) - Schema definitions
- [`docs/monitoring.md`](docs/monitoring.md) - Monitoring guide
- [`docs/troubleshooting.md`](docs/troubleshooting.md) - Troubleshooting guide

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio/discussions)
- **Documentation**: [Main README](../README.md)

---

**🎯 Final Result**: A robust DataOps system that guarantees quality, consistency, and traceability in your data pipelines, allowing your team to focus on generating value instead of cleaning data.
