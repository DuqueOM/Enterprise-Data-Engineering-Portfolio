"""
Comprehensive tests for train.py - MLOps Training Pipeline

Tests cover:
- Configuration dataclasses
- Data generation and validation
- Model training
- Metrics computation
- Artifact saving
- Experiment tracking (MLflow, W&B)
- Error handling
- Reproducibility

Author: Portfolio Team
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import joblib
import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from train module
from train import (
    TrainingConfig,
    TrainingMetrics,
    evaluate_model,
    generate_synthetic_data,
    log_to_mlflow,
    log_to_wandb,
    parse_args,
    save_artifacts,
    set_seed,
    train_model,
)


class TestTrainingConfig:
    """Test TrainingConfig dataclass."""

    def test_training_config_creation(self):
        """Test creating TrainingConfig with all parameters."""
        config = TrainingConfig(
            max_steps=100,
            batch_size=32,
            output_dir="artifacts/test",
            wandb_project="test-project",
            mlflow_tracking_uri="http://localhost:5000",
            epochs=10,
            random_seed=42,
            n_samples=1000,
            n_features=20,
            test_size=0.2,
            model_name="test-model",
        )

        assert config.max_steps == 100
        assert config.batch_size == 32
        assert config.output_dir == "artifacts/test"
        assert config.wandb_project == "test-project"
        assert config.epochs == 10
        assert config.random_seed == 42

    def test_training_config_to_dict(self):
        """Test converting TrainingConfig to dictionary."""
        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir="test",
            wandb_project=None,
            mlflow_tracking_uri=None,
            epochs=1,
            random_seed=42,
            n_samples=500,
            n_features=10,
            test_size=0.2,
            model_name="model",
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["max_steps"] == 50
        assert config_dict["batch_size"] == 16
        assert config_dict["random_seed"] == 42
        assert config_dict["wandb_project"] is None


class TestTrainingMetrics:
    """Test TrainingMetrics dataclass."""

    def test_training_metrics_creation(self):
        """Test creating TrainingMetrics."""
        metrics = TrainingMetrics(
            accuracy=0.95,
            precision=0.94,
            recall=0.96,
            f1=0.95,
            roc_auc=0.98,
            training_time=10.5,
            n_samples=200,
            n_features=16,
        )

        assert metrics.accuracy == 0.95
        assert metrics.precision == 0.94
        assert metrics.recall == 0.96
        assert metrics.f1 == 0.95
        assert metrics.roc_auc == 0.98
        assert metrics.training_time == 10.5

    def test_training_metrics_to_dict(self):
        """Test converting TrainingMetrics to dictionary."""
        metrics = TrainingMetrics(
            accuracy=0.90,
            precision=0.89,
            recall=0.91,
            f1=0.90,
            roc_auc=0.95,
            training_time=5.0,
            n_samples=100,
            n_features=10,
        )

        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert metrics_dict["accuracy"] == 0.90
        assert metrics_dict["f1"] == 0.90
        assert metrics_dict["training_time"] == 5.0


class TestSeedSetting:
    """Test random seed functionality."""

    def test_set_seed_numpy(self):
        """Test that set_seed affects numpy random generation."""
        set_seed(42)
        random_1 = np.random.rand(5)

        set_seed(42)
        random_2 = np.random.rand(5)

        np.testing.assert_array_equal(random_1, random_2)

    def test_set_seed_different_values(self):
        """Test different seeds produce different results."""
        set_seed(42)
        random_1 = np.random.rand(5)

        set_seed(123)
        random_2 = np.random.rand(5)

        # Should be different
        with pytest.raises(AssertionError):
            np.testing.assert_array_equal(random_1, random_2)


class TestDataGeneration:
    """Test synthetic data generation."""

    def test_generate_synthetic_data_basic(self):
        """Test basic data generation."""
        X_train, X_test, y_train, y_test = generate_synthetic_data(
            n_samples=1000, n_features=20, random_seed=42, test_size=0.2
        )

        assert X_train.shape[0] == 800  # 80% of 1000
        assert X_test.shape[0] == 200  # 20% of 1000
        assert X_train.shape[1] == 20
        assert X_test.shape[1] == 20
        assert len(y_train) == 800
        assert len(y_test) == 200

    def test_generate_synthetic_data_reproducibility(self):
        """Test that same seed produces same data."""
        X1, _, y1, _ = generate_synthetic_data(
            n_samples=500, n_features=10, random_seed=42
        )

        X2, _, y2, _ = generate_synthetic_data(
            n_samples=500, n_features=10, random_seed=42
        )

        np.testing.assert_array_equal(X1, X2)
        np.testing.assert_array_equal(y1, y2)

    def test_generate_synthetic_data_different_sizes(self):
        """Test data generation with different test sizes."""
        X_train, X_test, _, _ = generate_synthetic_data(
            n_samples=1000, n_features=15, random_seed=42, test_size=0.3
        )

        assert X_train.shape[0] == 700  # 70%
        assert X_test.shape[0] == 300  # 30%

    def test_generate_synthetic_data_small_dataset(self):
        """Test data generation with small dataset."""
        X_train, X_test, y_train, y_test = generate_synthetic_data(
            n_samples=50, n_features=5, random_seed=42, test_size=0.2
        )

        assert X_train.shape[0] == 40
        assert X_test.shape[0] == 10
        assert len(y_train) == 40
        assert len(y_test) == 10

    def test_generate_synthetic_data_features_validation(self):
        """Test that generated data has correct feature count."""
        for n_features in [8, 16, 32, 64]:
            X_train, X_test, _, _ = generate_synthetic_data(
                n_samples=200, n_features=n_features, random_seed=42
            )

            assert X_train.shape[1] == n_features
            assert X_test.shape[1] == n_features


class TestModelTraining:
    """Test model training functionality."""

    def test_train_model_basic(self):
        """Test basic model training."""
        config = TrainingConfig(
            max_steps=100,
            batch_size=16,
            output_dir="test",
            wandb_project=None,
            mlflow_tracking_uri=None,
            epochs=1,
            random_seed=42,
            n_samples=100,
            n_features=10,
            test_size=0.2,
            model_name="test",
        )

        X_train = np.random.rand(80, 10)
        y_train = np.random.randint(0, 2, 80)

        model = train_model(X_train, y_train, config)

        assert isinstance(model, LogisticRegression)
        assert hasattr(model, "coef_")
        assert hasattr(model, "intercept_")

    def test_train_model_predictions(self):
        """Test that trained model can make predictions."""
        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir="test",
            wandb_project=None,
            mlflow_tracking_uri=None,
            epochs=1,
            random_seed=42,
            n_samples=100,
            n_features=10,
            test_size=0.2,
            model_name="test",
        )

        X_train, X_test, y_train, y_test = generate_synthetic_data(
            n_samples=200, n_features=10, random_seed=42
        )

        model = train_model(X_train, y_train, config)
        predictions = model.predict(X_test)

        assert len(predictions) == len(y_test)
        assert set(predictions).issubset({0, 1})

    def test_train_model_multiple_epochs(self):
        """Test training with multiple epochs."""
        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir="test",
            wandb_project=None,
            mlflow_tracking_uri=None,
            epochs=5,
            random_seed=42,
            n_samples=100,
            n_features=10,
            test_size=0.2,
            model_name="test",
        )

        X_train = np.random.rand(80, 10)
        y_train = np.random.randint(0, 2, 80)

        model = train_model(X_train, y_train, config)

        assert isinstance(model, LogisticRegression)
        # Model should be trained (has coefficients)
        assert model.coef_ is not None


class TestModelEvaluation:
    """Test model evaluation and metrics computation."""

    def test_evaluate_model_basic(self):
        """Test basic model evaluation."""
        # Create a simple trained model
        X_train = np.random.rand(100, 10)
        y_train = np.random.randint(0, 2, 100)
        model = LogisticRegression(max_iter=100, random_state=42)
        model.fit(X_train, y_train)

        X_test = np.random.rand(20, 10)
        y_test = np.random.randint(0, 2, 20)

        metrics = evaluate_model(model, X_test, y_test, training_time=1.0)

        assert isinstance(metrics, TrainingMetrics)
        assert 0.0 <= metrics.accuracy <= 1.0
        assert 0.0 <= metrics.precision <= 1.0
        assert 0.0 <= metrics.recall <= 1.0
        assert 0.0 <= metrics.f1 <= 1.0
        assert 0.0 <= metrics.roc_auc <= 1.0
        assert metrics.training_time == 1.0

    def test_evaluate_model_perfect_predictions(self):
        """Test evaluation with perfect predictions."""
        # Create dataset where model can perfectly separate
        X_train = np.random.rand(100, 10)
        y_train = (X_train[:, 0] > 0.5).astype(int)

        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train, y_train)

        X_test = np.random.rand(50, 10)
        y_test = (X_test[:, 0] > 0.5).astype(int)

        metrics = evaluate_model(model, X_test, y_test, training_time=2.0)

        # With simple separation, should get high accuracy
        assert metrics.accuracy > 0.7
        assert metrics.training_time == 2.0

    def test_evaluate_model_metrics_range(self):
        """Test that all metrics are in valid range."""
        X_train, X_test, y_train, y_test = generate_synthetic_data(
            n_samples=200, n_features=15, random_seed=42
        )

        model = LogisticRegression(max_iter=100, random_state=42)
        model.fit(X_train, y_train)

        metrics = evaluate_model(model, X_test, y_test, training_time=1.5)

        assert 0.0 <= metrics.accuracy <= 1.0
        assert 0.0 <= metrics.precision <= 1.0
        assert 0.0 <= metrics.recall <= 1.0
        assert 0.0 <= metrics.f1 <= 1.0
        assert 0.0 <= metrics.roc_auc <= 1.0
        assert metrics.n_samples == len(y_test)
        assert metrics.n_features == X_test.shape[1]


class TestArtifactSaving:
    """Test artifact saving and persistence."""

    def test_save_artifacts_creates_files(self, tmp_path):
        """Test that save_artifacts creates expected files."""
        # Train a simple model
        X_train, X_test, y_train, y_test = generate_synthetic_data(
            n_samples=100, n_features=10, random_seed=42
        )
        model = LogisticRegression(max_iter=50, random_state=42)
        model.fit(X_train, y_train)

        metrics = TrainingMetrics(
            accuracy=0.9,
            precision=0.89,
            recall=0.91,
            f1=0.90,
            roc_auc=0.95,
            training_time=1.0,
            n_samples=20,
            n_features=10,
        )

        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir=str(tmp_path / "artifacts"),
            wandb_project=None,
            mlflow_tracking_uri=None,
            epochs=1,
            random_seed=42,
            n_samples=100,
            n_features=10,
            test_size=0.2,
            model_name="test",
        )

        paths = save_artifacts(model, metrics, config)

        # Check files exist
        assert Path(paths["model"]).exists()
        assert Path(paths["metadata"]).exists()

        # Verify model can be loaded
        loaded_model = joblib.load(paths["model"])
        assert isinstance(loaded_model, LogisticRegression)

        # Verify metadata
        with open(paths["metadata"]) as f:
            metadata = json.load(f)

        assert "timestamp" in metadata
        assert "metrics" in metadata
        assert "config" in metadata
        assert metadata["metrics"]["accuracy"] == 0.9

    def test_save_artifacts_metadata_structure(self, tmp_path):
        """Test metadata file structure."""
        X_train = np.random.rand(50, 8)
        y_train = np.random.randint(0, 2, 50)
        model = LogisticRegression(max_iter=50)
        model.fit(X_train, y_train)

        metrics = TrainingMetrics(
            accuracy=0.85,
            precision=0.84,
            recall=0.86,
            f1=0.85,
            roc_auc=0.90,
            training_time=0.5,
            n_samples=10,
            n_features=8,
        )

        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir=str(tmp_path / "output"),
            wandb_project="test",
            mlflow_tracking_uri=None,
            epochs=1,
            random_seed=123,
            n_samples=50,
            n_features=8,
            test_size=0.2,
            model_name="test-model",
        )

        paths = save_artifacts(model, metrics, config)

        with open(paths["metadata"]) as f:
            metadata = json.load(f)

        # Verify structure
        assert "timestamp" in metadata
        assert "metrics" in metadata
        assert "config" in metadata
        assert "model_path" in metadata
        assert "model_type" in metadata

        assert metadata["model_type"] == "LogisticRegression"
        assert metadata["config"]["random_seed"] == 123


class TestExperimentTracking:
    """Test experiment tracking integrations."""

    @patch("train.WANDB_AVAILABLE", True)
    @patch("train.wandb")
    def test_log_to_wandb_success(self, mock_wandb):
        """Test successful W&B logging."""
        mock_run = Mock()
        mock_wandb.init.return_value = mock_run

        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir="test",
            wandb_project="test-project",
            mlflow_tracking_uri=None,
            epochs=1,
            random_seed=42,
            n_samples=100,
            n_features=10,
            test_size=0.2,
            model_name="test",
        )

        metrics = TrainingMetrics(
            accuracy=0.9,
            precision=0.89,
            recall=0.91,
            f1=0.90,
            roc_auc=0.95,
            training_time=1.0,
            n_samples=20,
            n_features=10,
        )

        model = LogisticRegression()

        log_to_wandb(config, metrics, model)

        mock_wandb.init.assert_called_once()
        mock_wandb.log.assert_called_once()
        mock_wandb.finish.assert_called_once()

    @patch("train.WANDB_AVAILABLE", False)
    def test_log_to_wandb_unavailable(self):
        """Test W&B logging when wandb is not available."""
        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir="test",
            wandb_project="test",
            mlflow_tracking_uri=None,
            epochs=1,
            random_seed=42,
            n_samples=100,
            n_features=10,
            test_size=0.2,
            model_name="test",
        )

        metrics = TrainingMetrics(
            accuracy=0.9,
            precision=0.89,
            recall=0.91,
            f1=0.90,
            roc_auc=0.95,
            training_time=1.0,
            n_samples=20,
            n_features=10,
        )

        model = LogisticRegression()

        # Should not raise exception
        log_to_wandb(config, metrics, model)

    @patch("train.MLFLOW_AVAILABLE", True)
    @patch("train.mlflow")
    def test_log_to_mlflow_success(self, mock_mlflow):
        """Test successful MLflow logging."""
        mock_context = MagicMock()
        mock_mlflow.start_run.return_value.__enter__.return_value = mock_context

        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir="test",
            wandb_project=None,
            mlflow_tracking_uri="http://localhost:5000",
            epochs=1,
            random_seed=42,
            n_samples=100,
            n_features=10,
            test_size=0.2,
            model_name="test",
        )

        metrics = TrainingMetrics(
            accuracy=0.9,
            precision=0.89,
            recall=0.91,
            f1=0.90,
            roc_auc=0.95,
            training_time=1.0,
            n_samples=20,
            n_features=10,
        )

        model = LogisticRegression()

        log_to_mlflow(config, metrics, model)

        mock_mlflow.set_tracking_uri.assert_called_once_with("http://localhost:5000")
        mock_mlflow.start_run.assert_called_once()
        mock_mlflow.log_params.assert_called_once()
        mock_mlflow.log_metrics.assert_called_once()


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_parse_args_defaults(self):
        """Test parsing with default arguments."""
        with patch("sys.argv", ["train.py"]):
            args = parse_args()

        assert args.max_steps == 100
        assert args.batch_size == 16
        assert args.output_dir == "artifacts/latest"
        assert args.epochs == 1
        assert args.seed == 42

    def test_parse_args_custom_values(self):
        """Test parsing with custom arguments."""
        test_args = [
            "train.py",
            "--max_steps",
            "200",
            "--batch_size",
            "32",
            "--epochs",
            "5",
            "--n_samples",
            "2000",
            "--n_features",
            "32",
            "--model_name",
            "custom-model",
            "--seed",
            "123",
        ]

        with patch("sys.argv", test_args):
            args = parse_args()

        assert args.max_steps == 200
        assert args.batch_size == 32
        assert args.epochs == 5
        assert args.n_samples == 2000
        assert args.n_features == 32
        assert args.model_name == "custom-model"
        assert args.seed == 123


class TestEndToEndWorkflow:
    """Integration tests for complete training workflow."""

    def test_complete_training_pipeline(self, tmp_path):
        """Test complete training pipeline from data to artifacts."""
        # Configuration
        config = TrainingConfig(
            max_steps=50,
            batch_size=16,
            output_dir=str(tmp_path / "artifacts"),
            wandb_project=None,
            mlflow_tracking_uri=None,
            epochs=1,
            random_seed=42,
            n_samples=200,
            n_features=16,
            test_size=0.2,
            model_name="integration-test",
        )

        # Set seed
        set_seed(config.random_seed)

        # Generate data
        X_train, X_test, y_train, y_test = generate_synthetic_data(
            n_samples=config.n_samples,
            n_features=config.n_features,
            random_seed=config.random_seed,
            test_size=config.test_size,
        )

        # Train model
        model = train_model(X_train, y_train, config)

        # Evaluate model
        metrics = evaluate_model(model, X_test, y_test, training_time=1.0)

        # Save artifacts
        paths = save_artifacts(model, metrics, config)

        # Verify all artifacts exist
        assert Path(paths["model"]).exists()
        assert Path(paths["metadata"]).exists()

        # Verify model works
        loaded_model = joblib.load(paths["model"])
        predictions = loaded_model.predict(X_test)
        assert len(predictions) == len(y_test)

        # Verify metrics are reasonable
        assert 0.0 <= metrics.accuracy <= 1.0
        assert metrics.n_samples == len(y_test)
        assert metrics.n_features == X_test.shape[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=train", "--cov-report=term-missing"])
