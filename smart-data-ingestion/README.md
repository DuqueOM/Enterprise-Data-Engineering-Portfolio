# 🌐 Smart Data Ingestion - Professional Web Scraping & Dataset Creation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code Quality](https://img.shields.io/badge/code%20quality-A+-brightgreen.svg)](.)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-success.svg)](.)

> **Production-Grade Data Collection System**  
> Automated web scraping, data validation, and structured dataset generation for NLP and ML workflows.

## 🎯 Overview

This project implements a complete **DataOps** solution that treats data as a product. Instead of managing disorganized Excel files, we create an automated pipeline that:

✅ **Saves Time & Costs** - Prevents manual data errors  
✅ **Improves Quality** - Automated validation and quality metrics  
✅ **Facilitates Collaboration** - Teams can work with trustworthy data  
✅ **Version Control** - Always know which data version was used  
✅ **Scalable** - Can be replicated to other projects without starting from scratch  

## 🏗️ System Architecture

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

## 📁 Project Structure

```
smart-data-ingestion/
├── .github/workflows/          # CI/CD pipelines
│   └── ci.yml                 # GitHub Actions workflow
├── data/                       # Data (DVC-versioned)
│   ├── raw/                   # Raw data (not in Git)
│   └── processed/             # Processed data
├── scripts/                    # Pipeline scripts
│   ├── ingest.py              # Data collection
│   ├── clean.py               # Data cleaning
│   ├── validate_schema.py     # Schema validation
│   ├── data_quality.py        # Quality analysis
│   ├── train_baseline.py      # Baseline model
│   └── export_dataset.py      # Dataset export
├── notebooks/                  # Exploratory analysis
│   └── EDA.ipynb              # Jupyter notebook for EDA
├── tests/                      # Automated tests
│   ├── test_ingestion.py      # Ingestion tests
│   └── test_validation.py     # Validation tests
├── config.yaml                 # Configuration file
├── dvc.yaml                   # DVC pipeline definition
├── Dockerfile                  # Docker container
├── setup.py                    # Package setup
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.10 or higher
- Git
- Optional: Docker (for containerization)
- Optional: GitHub/GitLab account (for CI/CD)

### Step 1: Clone and Configure Environment

```bash
# Clone the repository
git clone https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio.git
cd Enterprise-Data-Engineering-Portfolio/smart-data-ingestion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Configure DVC (Data Version Control)

```bash
# Initialize DVC
dvc init

# Configure remote storage (optional)
# Example with Google Drive:
dvc remote add -d myremote gdrive://<FOLDER-ID>
# Or with S3:
dvc remote add -d myremote s3://bucket-name/path

# Push existing data (if any)
dvc push
```

### Step 3: Run Pipeline Locally

```bash
# 1. Collect data (with optional flags)
python scripts/ingest.py \
  --output data/processed/faqs.jsonl \
  --region "Antioquia" \
  --chunk-size 1500

# 2. Clean data
python scripts/clean.py

# 3. Validate schema and quality
python scripts/validate_schema.py

# 4. Quality analysis
python scripts/data_quality.py

# 5. Train baseline model
python scripts/train_baseline.py

# Or run everything with DVC
dvc repro
```

### Step 4: Configure Annotation (Optional)

```bash
# Start Label Studio with Docker
docker run -it -p 8080:8080 -v $(pwd)/data:/label-studio/data heartexlabs/label-studio:latest

# Configure environment variables
export LABEL_STUDIO_URL="http://localhost:8080"
export LABEL_STUDIO_API_KEY="YOUR-API-KEY"
export LABEL_STUDIO_PROJECT_ID="1"

# Import annotation tasks
python scripts/annotate.py
```

### Step 5: Analyze Results

```bash
# Open Jupyter for exploratory analysis
jupyter notebook notebooks/EDA.ipynb

# View quality report
open reports/quality_report.html
```

## 🔧 Pipeline Configuration

### Customize Data Sources

Edit `scripts/ingest.py` to add your own URLs:

```python
urls = [
    ("https://government-site-1.gov/faq", "Antioquia"),
    ("https://government-site-2.gov/faq", "Valle del Cauca"),
    # Add more URLs here
]
```

### Configure Validations

Modify `scripts/validate_schema.py` to adjust validation rules:

```python
SCHEMA = {
    "required": ["id", "source_url", "text", "date_fetched"],
    "properties": {
        "text": {"minLength": 50},  # Minimum 50 characters
        # ... more rules
    }
}
```

### Customize Quality Metrics

Edit `scripts/data_quality.py` to add custom metrics:

```python
def custom_quality_checks(df):
    # Add your own validations
    pass
```

## 🔄 CI/CD Pipeline

The automated pipeline runs automatically when:

- **Push to main/develop**: Runs validation, tests, and training
- **Pull Request**: Runs quality tests
- **Manual**: Can be triggered manually from GitHub

### Pipeline Stages

1. **Data Validation**: Validates schema and data quality
2. **Data Tests**: Runs automated tests
3. **Security Scan**: Scans for vulnerabilities
4. **Model Monitoring**: Verifies model performance
5. **Deploy**: Deploys to staging/production

### Configure Secrets in GitHub

Go to `Settings > Secrets and variables > Actions` and configure:

- `DVC_REMOTE_URL`: Remote storage URL
- `SLACK_WEBHOOK_URL`: For notifications (optional)

## 📊 Metrics and Monitoring

### Automatic Metrics

The pipeline automatically generates:

- **Completeness**: Percentage of non-null data
- **Uniqueness**: Duplicate detection
- **Consistency**: Format validation
- **Text Quality**: Length, special characters
- **Model Performance**: Accuracy, important features

### Reports

- **HTML Report**: `reports/quality_report.html`
- **JSON Metrics**: `metrics/quality.json`
- **Model Metrics**: `models/metrics.json`

## 🐛 Troubleshooting

### Common Issues

**Error: "File not found" in validation**
```bash
# Make sure you've run previous steps
python scripts/ingest.py
python scripts/clean.py
```

**Error: DVC remote not configured**
```bash
# Configure a remote or use local storage
dvc remote add -d local /tmp/dvc-storage
```

**Error: Missing dependencies**
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Logs and Debugging

```bash
# View detailed logs
export PYTHONPATH=$(pwd)
python -v scripts/validate_schema.py

# View DVC pipeline status
dvc status
dvc dag
```

## 🚀 Production Deployment

### Option 1: GitHub Actions (Automatic)

The pipeline deploys automatically when pushing to `main`.

### Option 2: Manual

```bash
# 1. Version data
dvc add data/processed/faqs_clean.jsonl
dvc push

# 2. Create version tag
git tag dataset-v1.0.0
git push origin dataset-v1.0.0

# 3. Deploy to production
# (add your infrastructure-specific commands)
```

### Integration with Hugging Face

```python
from datasets import Dataset
import json

# Load data
with open('data/processed/faqs_clean.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Create dataset
dataset = Dataset.from_list(data)

# Upload to Hugging Face
dataset.push_to_hub("your-username/pyme-qa-dataset")
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=scripts --cov-report=html

# Run specific tests
pytest tests/test_ingestion.py -v
```

## 📈 Scaling the Project

### For Larger Datasets

1. **Parallel Processing**:
```python
from multiprocessing import Pool
with Pool(processes=4) as pool:
    results = pool.map(process_url, urls)
```

2. **Cloud Storage**:
```bash
# Configure S3
dvc remote add -d s3 s3://bucket-name
dvc push
```

3. **Distributed Computing**:
Consider using Dask or Spark for very large datasets.

### For Multiple Sources

```python
# Add support for APIs, databases, etc.
def fetch_from_api(endpoint):
    # API logic
    pass

def fetch_from_database(query):
    # Database logic
    pass
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [DVC](https://dvc.org/) - For data versioning
- [Label Studio](https://labelstud.io/) - For data annotation
- [Pandera](https://pandera.readthedocs.io/) - For data validation
- [Scikit-learn](https://scikit-learn.org/) - For baseline models

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio/discussions)
- **Documentation**: [Main README](../README.md)

---

**🎉 Ready!** You now have a professional automated DataOps pipeline.

To get started, simply run:
```bash
git clone https://github.com/DuqueOM/Enterprise-Data-Engineering-Portfolio.git
cd Enterprise-Data-Engineering-Portfolio/smart-data-ingestion
pip install -r requirements.txt
python scripts/ingest.py
```

And follow the steps described in this guide.

---

## Optional Integration with Enterprise QA Service

To export data directly to the format/location expected by the Enterprise QA Service:

```bash
python scripts/ingest.py \
  --output ../enterprise-qa-service/data/raw/faqs.jsonl \
  --region "Bogotá" \
  --chunk-size 1500
```

**Notes:**
- The `--output` flag is optional and doesn't change default behavior
- The generated format is compatible (JSONL with fields: id, source_url, region, text, date_fetched)
- This doesn't affect independent project execution

