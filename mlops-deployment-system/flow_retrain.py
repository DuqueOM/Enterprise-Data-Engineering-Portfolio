"""Flow de reentreno con Prefect v2.
- fetch_data: llama a scripts/ingest.py (o dvc pull)
- validate_data: corre tests de esquema
- train_model: llama a train.py y guarda artefactos
- push_artifacts: sube a W&B / HF / S3
"""
from prefect import flow, task, get_run_logger
import subprocess
import os
import json
import wandb
import mlflow
import mlflow.sklearn

@task(retries=2, retry_delay_seconds=60)
def fetch_data():
    logger = get_run_logger()
    logger.info("Fetching data (ingest.py / dvc pull)")
    if os.path.exists("dvc.yaml"):
        subprocess.run(["dvc", "pull"], check=False)
    if os.path.exists("scripts/ingest.py"):
        subprocess.run(["python", "scripts/ingest.py"], check=True)

@task
def validate_data():
    logger = get_run_logger()
    logger.info("Validating data with pytest")
    result = subprocess.run(["pytest", "tests/test_data_schema.py", "-q"], check=True, capture_output=True, text=True)
    logger.info(f"Data validation result: {result.stdout}")

@task
def train_model(epochs: int = 1, wandb_project: str = "production-train"):
    logger = get_run_logger()
    logger.info("Training model (train.py)")
    out_dir = "artifacts/latest"
    os.makedirs(out_dir, exist_ok=True)
    
    # Start MLflow run
    with mlflow.start_run() as run:
        cmd = ["python", "train.py", "--epochs", str(epochs), "--output_dir", out_dir, "--wandb_project", wandb_project]
        subprocess.run(cmd, check=True)
        
        # Log model to MLflow
        model_path = os.path.join(out_dir, "model.joblib")
        if os.path.exists(model_path):
            mlflow.sklearn.log_model(sklearn_model=model_path, artifact_path="model")
            
        # Log metrics
        meta_path = os.path.join(out_dir, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                metrics = json.load(f)
            mlflow.log_metrics(metrics)
            
        logger.info(f"MLflow run ID: {run.info.run_id}")
    
    return out_dir

@task
def push_artifacts(out_dir: str):
    logger = get_run_logger()
    logger.info("Pushing artifacts to W&B and optional model registry")
    
    # Push to W&B if configured
    if os.environ.get("WANDB_API_KEY"):
        try:
            wandb.init(project="model-registry", job_type="model-upload")
            artifact = wandb.Artifact("production-model", type="model")
            artifact.add_dir(out_dir)
            wandb.log_artifact(artifact)
            wandb.finish()
            logger.info("Artifacts uploaded to W&B")
        except Exception as e:
            logger.warning(f"W&B upload failed: {e}")
    
    logger.info("Artifacts ready at %s", out_dir)

@flow(name="retrain-flow", retries=0)
def retrain_flow(epochs: int = 1):
    fetch_data()
    validate_data()
    out = train_model(epochs=epochs)
    push_artifacts(out)
    return out

if __name__ == "__main__":
    # Set MLflow tracking URI from environment
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(os.environ.get("MLFLOW_EXPERIMENT_NAME", "production"))
    
    retrain_flow(epochs=1)
