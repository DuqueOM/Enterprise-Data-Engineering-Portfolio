#!/usr/bin/env python3
"""
Setup Demo Script for DataOps Pipeline
Creates a complete demo environment with sample data and configurations
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import argparse

def create_directories():
    """Create necessary directory structure"""
    directories = [
        "data/raw",
        "data/processed", 
        "data/reports",
        "data/metrics",
        "models/baseline",
        "logs",
        "configs",
        "tests",
        "archive"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def generate_sample_data(output_path: str, rows: int = 1000):
    """Generate realistic sample customer data"""
    print(f"📊 Generating sample data with {rows} rows...")
    
    np.random.seed(42)
    
    # Generate customer IDs
    customer_ids = [f"AZ{str(i).zfill(6)}" for i in range(rows)]
    
    # Generate emails
    names = [f"user{i}" for i in range(rows)]
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "company.com"]
    emails = [f"{name}@{np.random.choice(domains)}" for name in names]
    
    # Generate demographics
    ages = np.random.normal(45, 15, rows).astype(int).clip(18, 80)
    genders = np.random.choice(["M", "F", "Other"], rows, p=[0.45, 0.45, 0.10])
    
    # Generate dates
    start_date = datetime(2020, 1, 1)
    registration_dates = [
        start_date + timedelta(days=np.random.randint(0, 1200))
        for _ in range(rows)
    ]
    
    last_purchase_dates = []
    total_purchases = []
    for i, reg_date in enumerate(registration_dates):
        if np.random.random() < 0.1:  # 10% no purchase yet
            last_purchase_dates.append(None)
            total_purchases.append(0.0)
        else:
            days_since_reg = (datetime.now() - reg_date).days
            last_purchase = reg_date + timedelta(days=np.random.randint(0, days_since_reg))
            last_purchase_dates.append(last_purchase)
            total_purchases.append(np.random.exponential(500) + 50)
    
    # Generate business metrics
    avg_purchase_values = []
    for total in total_purchases:
        if total > 0:
            purchase_count = np.random.poisson(5) + 1
            avg_purchase_values.append(total / purchase_count)
        else:
            avg_purchase_values.append(0.0)
    
    # Customer segments based on purchase behavior
    customer_segments = []
    for total in total_purchases:
        if total < 100:
            customer_segments.append("Bronze")
        elif total < 500:
            customer_segments.append("Silver")
        elif total < 2000:
            customer_segments.append("Gold")
        else:
            customer_segments.append("Platinum")
    
    # Churn risk (simplified calculation)
    churn_risks = []
    for i, (total, last_purchase) in enumerate(zip(total_purchases, last_purchase_dates)):
        if last_purchase is None:
            risk = np.random.beta(2, 1)  # High risk for no purchases
        else:
            days_since_last = (datetime.now() - last_purchase).days
            risk = min(1.0, days_since_last / 365 * np.random.uniform(0.5, 1.5))
        churn_risks.append(risk)
    
    # Create DataFrame
    df = pd.DataFrame({
        'customer_id': customer_ids,
        'email': emails,
        'age': ages,
        'gender': genders,
        'registration_date': [d.strftime('%Y-%m-%d') for d in registration_dates],
        'last_purchase_date': [d.strftime('%Y-%m-%d') if d else None for d in last_purchase_dates],
        'total_purchases': total_purchases,
        'avg_purchase_value': avg_purchase_values,
        'customer_segment': customer_segments,
        'churn_risk': churn_risks
    })
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"✅ Sample data saved to: {output_path}")
    
    # Generate data summary
    summary = {
        'total_rows': len(df),
        'columns': list(df.columns),
        'data_types': df.dtypes.to_dict(),
        'null_counts': df.isnull().sum().to_dict(),
        'generated_at': datetime.now().isoformat()
    }
    
    summary_path = output_path.replace('.csv', '_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    return df

def create_dvc_config():
    """Initialize DVC configuration"""
    print("🔧 Setting up DVC configuration...")
    
    # Create .dvcignore
    dvcignore_content = """
# Ignore files and directories for DVC
.env
.venv
venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
.DS_Store
*.log
models/.gitignore
data/.gitignore
"""
    
    with open('.dvcignore', 'w') as f:
        f.write(dvcignore_content.strip())
    
    print("✅ DVC configuration created")

def create_great_expectations_config():
    """Create Great Expectations configuration files"""
    print("🔧 Setting up Great Expectations...")
    
    ge_dir = Path("configs/great_expectations")
    ge_dir.mkdir(parents=True, exist_ok=True)
    
    # Create expectations directory
    (ge_dir / "expectations").mkdir(exist_ok=True)
    
    print("✅ Great Expectations configuration created")

def create_example_scripts():
    """Create example script files"""
    print("📝 Creating example scripts...")
    
    scripts = {
        "validate_data.py": '''#!/usr/bin/env python3
"""Data validation script using Great Expectations"""
import argparse
import json
import sys
from pathlib import Path
import pandas as pd
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True, help="Path to data directory")
    parser.add_argument("--config-path", required=True, help="Path to GE config")
    parser.add_argument("--output", required=True, help="Output directory for reports")
    parser.add_argument("--debug", action="store_true")
    
    args = parser.parse_args()
    
    # Initialize Great Expectations
    context = gx.get_context(context_root_dir=args.config_path)
    
    # Validate data
    data_path = Path(args.data_path)
    for csv_file in data_path.glob("*.csv"):
        print(f"Validating {csv_file.name}...")
        
        # Create batch request
        batch_request = RuntimeBatchRequest(
            datasource_name="filesystem",
            data_connector_name="default_runtime_data_connector",
            data_asset_name=csv_file.stem,
            runtime_parameters={"batch_data": pd.read_csv(csv_file)},
            identifiers={"default_identifier_name": csv_file.stem},
        )
        
        # Run validation
        validation_results = context.run_validation_operator(
            "default_validation_operator",
            assets_to_validate=[batch_request]
        )
        
        # Save results
        output_file = Path(args.output) / f"{csv_file.stem}_validation.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(validation_results.to_json_dict(), f, indent=2)
        
        print(f"✅ Validation results saved to {output_file}")

if __name__ == "__main__":
    main()
''',
        
        "normalize_data.py": '''#!/usr/bin/env python3
"""Data normalization and processing script"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import json

def load_schema(schema_path: str) -> dict:
    """Load data schema configuration"""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema: dict) -> dict:
    """Validate DataFrame against schema"""
    results = {
        'valid': True,
        'errors': []
    }
    
    # Check required columns
    required_columns = set(schema['columns'].keys())
    actual_columns = set(df.columns)
    
    missing_columns = required_columns - actual_columns
    if missing_columns:
        results['valid'] = False
        results['errors'].append(f"Missing columns: {missing_columns}")
    
    # Check data types
    for col, config in schema['columns'].items():
        if col in df.columns:
            expected_type = config['type']
            if expected_type == 'integer' and df[col].dtype != 'int64':
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            elif expected_type == 'float' and df[col].dtype != 'float64':
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif expected_type == 'datetime':
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return results, df

def normalize_data(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """Apply normalization rules"""
    normalized_df = df.copy()
    
    # Handle missing values
    for col, config in schema['columns'].items():
        if col in normalized_df.columns:
            if not config.get('nullable', True):
                if normalized_df[col].dtype in ['int64', 'float64']:
                    normalized_df[col] = normalized_df[col].fillna(0)
                else:
                    normalized_df[col] = normalized_df[col].fillna('Unknown')
    
    # Remove duplicates
    if 'customer_id' in normalized_df.columns:
        initial_count = len(normalized_df)
        normalized_df = normalized_df.drop_duplicates(subset=['customer_id'])
        duplicates_removed = initial_count - len(normalized_df)
        print(f"Removed {duplicates_removed} duplicate records")
    
    return normalized_df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input data directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--schema", default="configs/data_schema.yaml", help="Schema file path")
    
    args = parser.parse_args()
    
    # Load schema
    schema = load_schema(args.schema)
    
    # Process all CSV files
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    processing_metrics = {
        'files_processed': 0,
        'total_records': 0,
        'validation_errors': 0
    }
    
    for csv_file in input_path.glob("*.csv"):
        print(f"Processing {csv_file.name}...")
        
        # Load data
        df = pd.read_csv(csv_file)
        initial_count = len(df)
        
        # Validate schema
        validation_results, df = validate_schema(df, schema)
        if not validation_results['valid']:
            print(f"⚠️  Validation errors in {csv_file.name}: {validation_results['errors']}")
            processing_metrics['validation_errors'] += 1
        
        # Normalize data
        df = normalize_data(df, schema)
        final_count = len(df)
        
        # Save processed data
        output_file = output_path / csv_file.name
        df.to_csv(output_file, index=False)
        
        # Update metrics
        processing_metrics['files_processed'] += 1
        processing_metrics['total_records'] += final_count
        
        print(f"✅ Processed {csv_file.name}: {initial_count} -> {final_count} records")
    
    # Save processing metrics
    metrics_file = output_path / "processing_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(processing_metrics, f, indent=2)
    
    print(f"📊 Processing complete. Metrics saved to {metrics_file}")

if __name__ == "__main__":
    main()
''',
        
        "train_baseline.py": '''#!/usr/bin/env python3
"""Baseline model training script"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import json
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, mean_squared_error, r2_score
import mlflow
import mlflow.sklearn

def load_data(data_path: str) -> pd.DataFrame:
    """Load training data"""
    data_path = Path(data_path)
    dfs = []
    
    for csv_file in data_path.glob("*.csv"):
        df = pd.read_csv(csv_file)
        dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True)

def prepare_features(df: pd.DataFrame, target_column: str) -> tuple:
    """Prepare features and target for training"""
    # Select numeric columns for features
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if target_column not in numeric_columns:
        raise ValueError(f"Target column {target_column} not found or not numeric")
    
    feature_columns = [col for col in numeric_columns if col != target_column]
    
    X = df[feature_columns].fillna(0)
    y = df[target_column].fillna(0)
    
    return X, y, feature_columns

def train_model(X, y, model_type: str = "classifier"):
    """Train baseline model"""
    if model_type == "classifier":
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
    else:
        model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    
    if model_type == "classifier":
        metrics = {
            "classification_report": classification_report(y_test, y_pred, output_dict=True)
        }
    else:
        metrics = {
            "mse": mean_squared_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "r2": r2_score(y_test, y_pred)
        }
    
    return model, metrics, (X_train, X_test, y_train, y_test)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True, help="Path to processed data")
    parser.add_argument("--model-path", required=True, help="Output path for model")
    parser.add_argument("--target-column", default="churn_risk", help="Target column for prediction")
    parser.add_argument("--model-type", choices=["classifier", "regressor"], default="regressor")
    
    args = parser.parse_args()
    
    # Start MLflow run
    mlflow.start_run()
    
    try:
        # Load data
        df = load_data(args.data_path)
        print(f"Loaded {len(df)} records")
        
        # Prepare features
        X, y, feature_columns = prepare_features(df, args.target_column)
        print(f"Using {len(feature_columns)} features: {feature_columns}")
        
        # Train model
        model, metrics, splits = train_model(X, y, args.model_type)
        
        # Create output directory
        output_path = Path(args.model_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_file = output_path / "model.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        
        # Save metadata
        metadata = {
            "model_type": args.model_type,
            "target_column": args.target_column,
            "feature_columns": feature_columns,
            "training_samples": len(X),
            "metrics": metrics,
            "created_at": pd.Timestamp.now().isoformat()
        }
        
        metadata_file = output_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Log to MLflow
        mlflow.log_params({
            "model_type": args.model_type,
            "target_column": args.target_column,
            "n_features": len(feature_columns)
        })
        
        if args.model_type == "classifier":
            mlflow.log_metrics({
                "accuracy": metrics["classification_report"]["accuracy"],
                "macro_avg_f1": metrics["classification_report"]["macro avg"]["f1-score"]
            })
        else:
            mlflow.log_metrics({
                "mse": metrics["mse"],
                "rmse": metrics["rmse"],
                "r2": metrics["r2"]
            })
        
        mlflow.sklearn.log_model(model, "model")
        
        print(f"✅ Model saved to {model_file}")
        print(f"📊 Metrics: {metrics}")
        
    finally:
        mlflow.end_run()

if __name__ == "__main__":
    main()
'''
    }
    
    for script_name, content in scripts.items():
        script_path = Path("scripts") / script_name
        if not script_path.exists():
            with open(script_path, 'w') as f:
                f.write(content)
            os.chmod(script_path, 0o755)
            print(f"✅ Created script: {script_name}")

def create_environment_files():
    """Create environment configuration files"""
    print("🔧 Creating environment files...")
    
    # .env template
    env_template = """# DataOps Pipeline Environment Variables

# Database Configuration
DATABASE_URL=postgresql://dataops:dataops123@localhost:5432/dataops
REDIS_URL=redis://localhost:6379/0

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=dataops-pipeline

# Cloud Storage (uncomment and configure as needed)
# AWS_S3_BUCKET=my-bucket
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_DEFAULT_REGION=us-west-2

# Google Cloud Storage
# GCS_BUCKET=my-bucket
# GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Azure Blob Storage
# AZURE_STORAGE_ACCOUNT=myaccount
# AZURE_STORAGE_KEY=mykey
# AZURE_CONTAINER=mycontainer

# Notification Configuration
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
# SMTP_HOST=smtp.gmail.com
# SMTP_USER=your-email@gmail.com
# SMTP_PASS=your-password

# Logging
LOG_LEVEL=INFO
DVC_LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("✅ Environment template created")

def main():
    parser = argparse.ArgumentParser(description="Setup DataOps Pipeline Demo")
    parser.add_argument("--rows", type=int, default=1000, help="Number of sample rows to generate")
    parser.add_argument("--skip-dvc", action="store_true", help="Skip DVC initialization")
    
    args = parser.parse_args()
    
    print("🚀 Setting up DataOps Pipeline Demo Environment")
    print("=" * 50)
    
    # Create directory structure
    create_directories()
    
    # Generate sample data
    sample_data_path = "data/raw/sample_customers.csv"
    generate_sample_data(sample_data_path, args.rows)
    
    # Create configuration files
    create_dvc_config()
    create_great_expectations_config()
    create_environment_files()
    
    # Create example scripts
    create_example_scripts()
    
    print("\n" + "=" * 50)
    print("✅ Demo setup complete!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and configure as needed")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Start services: docker-compose up -d")
    print("4. Run pipeline: dvc repro")
    print("5. View dashboard: http://localhost:8501")
    print("6. View API docs: http://localhost:8000/docs")
    print("\nFor detailed instructions, see docs/usage.md")

if __name__ == "__main__":
    main()
