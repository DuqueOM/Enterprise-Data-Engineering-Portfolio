#!/usr/bin/env python3
"""
MLOps Training Pipeline - Production Model Training

This module implements a production-grade training pipeline with:
- Experiment tracking (MLflow, W&B)
- Model versioning and artifact management
- Comprehensive metrics logging
- Reproducibility (seeds, versioning)
- Error handling and validation

Author: Portfolio Team
License: MIT
"""

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

import joblib
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report
)
from sklearn.model_selection import train_test_split

# Optional dependencies
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('training.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
DEFAULT_OUTPUT_DIR = "artifacts/latest"
DEFAULT_N_SAMPLES = 1000
DEFAULT_N_FEATURES = 16
DEFAULT_TEST_SIZE = 0.2


@dataclass
class TrainingConfig:
    """Training configuration dataclass."""
    max_steps: int
    batch_size: int
    output_dir: str
    wandb_project: Optional[str]
    mlflow_tracking_uri: Optional[str]
    epochs: int
    random_seed: int
    n_samples: int
    n_features: int
    test_size: float
    model_name: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)


@dataclass
class TrainingMetrics:
    """Training metrics dataclass."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    training_time: float
    n_samples: int
    n_features: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)


def set_seed(seed: int = RANDOM_SEED) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed value
    """
    np.random.seed(seed)
    logger.info(f"Random seed set to: {seed}")


def generate_synthetic_data(
    n_samples: int,
    n_features: int,
    random_seed: int,
    test_size: float = DEFAULT_TEST_SIZE
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate synthetic classification dataset.
    
    Args:
        n_samples: Number of samples to generate
        n_features: Number of features
        random_seed: Random seed for reproducibility
        test_size: Proportion of test set
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    logger.info(f"Generating synthetic dataset: {n_samples} samples, {n_features} features")
    
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=int(n_features * 0.7),
        n_redundant=int(n_features * 0.2),
        random_state=random_seed,
        flip_y=0.1  # Add some noise
    )
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_seed, stratify=y
    )
    
    logger.info(f"Train set: {X_train.shape}, Test set: {X_test.shape}")
    return X_train, X_test, y_train, y_test


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    config: TrainingConfig
) -> LogisticRegression:
    """
    Train logistic regression model.
    
    Args:
        X_train: Training features
        y_train: Training labels
        config: Training configuration
        
    Returns:
        Trained model
    """
    logger.info("Starting model training...")
    start_time = time.time()
    
    model = LogisticRegression(
        max_iter=config.max_steps,
        random_state=config.random_seed,
        solver='lbfgs',
        n_jobs=-1  # Use all CPU cores
    )
    
    # Train for specified epochs
    for epoch in range(config.epochs):
        model.fit(X_train, y_train)
        
        if config.max_steps < 50:
            # Simulate processing time for smoke tests
            time.sleep(0.1)
        
        if epoch > 0 and epoch % 10 == 0:
            train_acc = model.score(X_train, y_train)
            logger.info(f"Epoch {epoch}/{config.epochs} - Train accuracy: {train_acc:.4f}")
    
    training_time = time.time() - start_time
    logger.info(f"Training completed in {training_time:.2f}s")
    
    return model


def evaluate_model(
    model: LogisticRegression,
    X_test: np.ndarray,
    y_test: np.ndarray,
    training_time: float
) -> TrainingMetrics:
    """
    Evaluate trained model and compute metrics.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        training_time: Time taken for training
        
    Returns:
        TrainingMetrics with all computed metrics
    """
    logger.info("Evaluating model...")
    
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = TrainingMetrics(
        accuracy=float(accuracy_score(y_test, y_pred)),
        precision=float(precision_score(y_test, y_pred, average='binary')),
        recall=float(recall_score(y_test, y_pred, average='binary')),
        f1=float(f1_score(y_test, y_pred, average='binary')),
        roc_auc=float(roc_auc_score(y_test, y_pred_proba)),
        training_time=training_time,
        n_samples=len(X_test),
        n_features=X_test.shape[1]
    )
    
    logger.info(f"Evaluation metrics:")
    logger.info(f"  Accuracy:  {metrics.accuracy:.4f}")
    logger.info(f"  Precision: {metrics.precision:.4f}")
    logger.info(f"  Recall:    {metrics.recall:.4f}")
    logger.info(f"  F1 Score:  {metrics.f1:.4f}")
    logger.info(f"  ROC AUC:   {metrics.roc_auc:.4f}")
    
    # Detailed classification report
    report = classification_report(y_test, y_pred)
    logger.info(f"\nClassification Report:\n{report}")
    
    return metrics


def save_artifacts(
    model: LogisticRegression,
    metrics: TrainingMetrics,
    config: TrainingConfig
) -> Dict[str, str]:
    """
    Save model artifacts and metadata.
    
    Args:
        model: Trained model
        metrics: Evaluation metrics
        config: Training configuration
        
    Returns:
        Dictionary with paths to saved artifacts
    """
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = output_dir / "model.joblib"
    joblib.dump(model, model_path)
    logger.info(f"Model saved to: {model_path}")
    
    # Save metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics.to_dict(),
        "config": config.to_dict(),
        "model_path": str(model_path),
        "model_type": type(model).__name__
    }
    
    meta_path = output_dir / "metadata.json"
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to: {meta_path}")
    
    return {
        "model": str(model_path),
        "metadata": str(meta_path)
    }


def log_to_wandb(
    config: TrainingConfig,
    metrics: TrainingMetrics,
    model: LogisticRegression
) -> None:
    """
    Log experiment to Weights & Biases.
    
    Args:
        config: Training configuration
        metrics: Training metrics
        model: Trained model
    """
    if not WANDB_AVAILABLE:
        logger.warning("W&B not available, skipping logging")
        return
    
    if not config.wandb_project:
        logger.info("W&B project not specified, skipping logging")
        return
    
    try:
        run = wandb.init(
            project=config.wandb_project,
            config=config.to_dict(),
            name=f"train-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        # Log metrics
        wandb.log(metrics.to_dict())
        
        # Log model artifact
        artifact = wandb.Artifact(
            name=config.model_name,
            type="model",
            description="Logistic Regression classifier"
        )
        artifact.add_file(str(Path(config.output_dir) / "model.joblib"))
        run.log_artifact(artifact)
        
        wandb.finish()
        logger.info("Successfully logged to W&B")
        
    except Exception as e:
        logger.error(f"W&B logging failed: {e}")


def log_to_mlflow(
    config: TrainingConfig,
    metrics: TrainingMetrics,
    model: LogisticRegression
) -> None:
    """
    Log experiment to MLflow.
    
    Args:
        config: Training configuration
        metrics: Training metrics
        model: Trained model
    """
    if not MLFLOW_AVAILABLE:
        logger.warning("MLflow not available, skipping logging")
        return
    
    if config.mlflow_tracking_uri:
        mlflow.set_tracking_uri(config.mlflow_tracking_uri)
    
    try:
        with mlflow.start_run(run_name=f"train-{datetime.now().strftime('%Y%m%d-%H%M%S')}"):
            # Log parameters
            mlflow.log_params(config.to_dict())
            
            # Log metrics
            mlflow.log_metrics(metrics.to_dict())
            
            # Log model
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name=config.model_name
            )
            
        logger.info("Successfully logged to MLflow")
        
    except Exception as e:
        logger.error(f"MLflow logging failed: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train ML model with experiment tracking",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--max_steps',
        type=int,
        default=100,
        help="Maximum iterations for model training"
    )
    
    parser.add_argument(
        '--batch_size',
        type=int,
        default=16,
        help="Batch size (unused for sklearn)"
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save model artifacts"
    )
    
    parser.add_argument(
        '--wandb_project',
        type=str,
        default=None,
        help="Weights & Biases project name"
    )
    
    parser.add_argument(
        '--mlflow_tracking_uri',
        type=str,
        default=None,
        help="MLflow tracking server URI"
    )
    
    parser.add_argument(
        '--epochs',
        type=int,
        default=1,
        help="Number of training epochs"
    )
    
    parser.add_argument(
        '--n_samples',
        type=int,
        default=DEFAULT_N_SAMPLES,
        help="Number of synthetic samples"
    )
    
    parser.add_argument(
        '--n_features',
        type=int,
        default=DEFAULT_N_FEATURES,
        help="Number of features"
    )
    
    parser.add_argument(
        '--model_name',
        type=str,
        default="classifier",
        help="Model name for artifact tracking"
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=RANDOM_SEED,
        help="Random seed for reproducibility"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main training pipeline.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Parse arguments
        args = parse_args()
        
        # Create configuration
        config = TrainingConfig(
            max_steps=args.max_steps,
            batch_size=args.batch_size,
            output_dir=args.output_dir,
            wandb_project=args.wandb_project,
            mlflow_tracking_uri=args.mlflow_tracking_uri,
            epochs=args.epochs,
            random_seed=args.seed,
            n_samples=args.n_samples,
            n_features=args.n_features,
            test_size=DEFAULT_TEST_SIZE,
            model_name=args.model_name
        )
        
        logger.info("=" * 80)
        logger.info("MLOps Training Pipeline Started")
        logger.info("=" * 80)
        logger.info(f"Configuration: {config}")
        
        # Set random seed
        set_seed(config.random_seed)
        
        # Generate data
        X_train, X_test, y_train, y_test = generate_synthetic_data(
            n_samples=config.n_samples,
            n_features=config.n_features,
            random_seed=config.random_seed,
            test_size=config.test_size
        )
        
        # Train model
        start_time = time.time()
        model = train_model(X_train, y_train, config)
        training_time = time.time() - start_time
        
        # Evaluate model
        metrics = evaluate_model(model, X_test, y_test, training_time)
        
        # Save artifacts
        artifact_paths = save_artifacts(model, metrics, config)
        logger.info(f"Artifacts saved: {artifact_paths}")
        
        # Log to experiment tracking platforms
        if os.environ.get('WANDB_API_KEY'):
            log_to_wandb(config, metrics, model)
        
        log_to_mlflow(config, metrics, model)
        
        logger.info("=" * 80)
        logger.info("Training pipeline completed successfully!")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.exception(f"Training pipeline failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
