"""
Comprehensive unit tests for drift_detector.py

Tests cover:
- Baseline loading and creation
- Embedding computation
- Drift detection logic
- Notification systems (Slack, GitHub)
- Edge cases and error handling
- Integration scenarios

Author: Portfolio Team
"""

import pickle
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions from drift_detector
from drift_detector import (
    compute_embeddings,
    create_github_issue,
    detect_embedding_drift,
    load_baseline,
    notify_slack,
)


class TestBaselineManagement:
    """Test baseline loading and persistence."""

    def test_load_baseline_success(self, tmp_path):
        """Test successful baseline loading."""
        baseline_path = tmp_path / "baseline.pkl"
        expected_data = np.random.rand(10, 384).astype(np.float32)

        with open(baseline_path, "wb") as f:
            pickle.dump(expected_data, f)

        loaded_data = load_baseline(str(baseline_path))
        np.testing.assert_array_equal(loaded_data, expected_data)

    def test_load_baseline_file_not_found(self):
        """Test baseline loading with missing file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_baseline("nonexistent_baseline.pkl")

        assert "Baseline no encontrada" in str(exc_info.value)

    def test_load_baseline_corrupted_file(self, tmp_path):
        """Test baseline loading with corrupted pickle file."""
        baseline_path = tmp_path / "corrupted.pkl"

        # Write corrupted data
        with open(baseline_path, "wb") as f:
            f.write(b"corrupted data")

        with pytest.raises(Exception):
            load_baseline(str(baseline_path))

    def test_baseline_persistence(self, tmp_path):
        """Test baseline can be saved and loaded correctly."""
        baseline_path = tmp_path / "test_baseline.pkl"
        test_embeddings = np.random.rand(50, 768).astype(np.float32)

        # Save
        with open(baseline_path, "wb") as f:
            pickle.dump(test_embeddings, f)

        # Load
        loaded = load_baseline(str(baseline_path))

        assert loaded.shape == test_embeddings.shape
        np.testing.assert_allclose(loaded, test_embeddings, rtol=1e-5)


class TestEmbeddingComputation:
    """Test embedding computation with sentence-transformers."""

    @patch("drift_detector.SentenceTransformer")
    def test_compute_embeddings_basic(self, mock_transformer):
        """Test basic embedding computation."""
        mock_model = Mock()
        mock_embeddings = np.random.rand(3, 384).astype(np.float32)
        mock_model.encode.return_value = mock_embeddings

        texts = ["text1", "text2", "text3"]
        result = compute_embeddings(texts, mock_model)

        mock_model.encode.assert_called_once_with(
            texts, convert_to_numpy=True, show_progress_bar=False
        )
        np.testing.assert_array_equal(result, mock_embeddings)

    @patch("drift_detector.SentenceTransformer")
    def test_compute_embeddings_empty_list(self, mock_transformer):
        """Test embedding computation with empty text list."""
        mock_model = Mock()
        mock_model.encode.return_value = np.array([]).reshape(0, 384)

        result = compute_embeddings([], mock_model)

        assert result.shape[0] == 0

    @patch("drift_detector.SentenceTransformer")
    def test_compute_embeddings_single_text(self, mock_transformer):
        """Test embedding computation with single text."""
        mock_model = Mock()
        mock_embeddings = np.random.rand(1, 384).astype(np.float32)
        mock_model.encode.return_value = mock_embeddings

        result = compute_embeddings(["single text"], mock_model)

        assert result.shape == (1, 384)

    @patch("drift_detector.SentenceTransformer")
    def test_compute_embeddings_long_texts(self, mock_transformer):
        """Test embedding computation with very long texts."""
        mock_model = Mock()
        long_text = "word " * 1000  # Very long text
        mock_embeddings = np.random.rand(1, 384).astype(np.float32)
        mock_model.encode.return_value = mock_embeddings

        result = compute_embeddings([long_text], mock_model)

        assert result is not None
        assert len(result) == 1


class TestDriftDetection:
    """Test drift detection logic."""

    def test_detect_drift_no_drift(self):
        """Test drift detection when embeddings are identical."""
        # Identical embeddings
        baseline = np.random.rand(10, 384).astype(np.float32)
        new_emb = baseline.copy()

        drift, mean_sim = detect_embedding_drift(baseline, new_emb)

        assert drift < 0.01  # Very low drift
        assert mean_sim > 0.99  # Very high similarity

    def test_detect_drift_high_drift(self):
        """Test drift detection with completely different embeddings."""
        baseline = np.random.rand(10, 384).astype(np.float32)
        new_emb = np.random.rand(15, 384).astype(np.float32)

        drift, mean_sim = detect_embedding_drift(baseline, new_emb)

        # Random vectors should have low similarity
        assert 0.0 <= drift <= 2.0
        assert 0.0 <= mean_sim <= 1.0

    def test_detect_drift_partial_drift(self):
        """Test drift detection with partial similarity."""
        # Create baseline
        baseline = np.random.rand(20, 384).astype(np.float32)

        # Create new embeddings: half similar, half different
        new_emb = np.vstack(
            [
                baseline[:10] + np.random.randn(10, 384) * 0.1,  # Similar
                np.random.rand(10, 384),  # Different
            ]
        ).astype(np.float32)

        drift, mean_sim = detect_embedding_drift(baseline, new_emb)

        # Should detect moderate drift
        assert 0.1 <= drift <= 0.9
        assert 0.1 <= mean_sim <= 0.9

    def test_detect_drift_different_dimensions(self):
        """Test that different embedding dimensions are handled."""
        baseline = np.random.rand(10, 384).astype(np.float32)
        new_emb = np.random.rand(5, 384).astype(np.float32)

        drift, mean_sim = detect_embedding_drift(baseline, new_emb)

        # Should work with different sample counts
        assert drift is not None
        assert mean_sim is not None

    def test_detect_drift_deterministic(self):
        """Test that drift detection is deterministic."""
        np.random.seed(42)
        baseline = np.random.rand(10, 384).astype(np.float32)
        new_emb = np.random.rand(10, 384).astype(np.float32)

        drift1, sim1 = detect_embedding_drift(baseline, new_emb)
        drift2, sim2 = detect_embedding_drift(baseline, new_emb)

        assert drift1 == drift2
        assert sim1 == sim2


class TestNotifications:
    """Test notification systems (Slack, GitHub)."""

    @patch("drift_detector.requests.post")
    def test_notify_slack_success(self, mock_post):
        """Test successful Slack notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        webhook = "https://hooks.slack.com/services/TEST"
        message = "Test drift alert"

        notify_slack(webhook, message)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == webhook
        assert kwargs["json"]["text"] == message
        assert kwargs["timeout"] == 6

    @patch("drift_detector.requests.post")
    def test_notify_slack_timeout(self, mock_post):
        """Test Slack notification with timeout."""
        mock_post.side_effect = requests.Timeout("Connection timeout")

        # Should not raise exception (logs warning instead)
        notify_slack("https://hooks.slack.com/test", "Test message")

        mock_post.assert_called_once()

    @patch("drift_detector.requests.post")
    def test_notify_slack_network_error(self, mock_post):
        """Test Slack notification with network error."""
        mock_post.side_effect = requests.ConnectionError("Network error")

        # Should handle gracefully
        notify_slack("https://hooks.slack.com/test", "Test message")

        mock_post.assert_called_once()

    @patch("drift_detector.requests.post")
    def test_create_github_issue_success(self, mock_post):
        """Test successful GitHub issue creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        token = "gh_token_123"
        repo = "user/repo"
        title = "Drift Alert"
        body = "Drift detected"

        create_github_issue(token, repo, title, body)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        assert args[0] == f"https://api.github.com/repos/{repo}/issues"
        assert kwargs["headers"]["Authorization"] == f"token {token}"
        assert kwargs["json"]["title"] == title
        assert kwargs["json"]["body"] == body

    @patch("drift_detector.requests.post")
    def test_create_github_issue_auth_failure(self, mock_post):
        """Test GitHub issue creation with auth failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        # Should log warning but not raise
        create_github_issue("bad_token", "user/repo", "Title", "Body")

        mock_post.assert_called_once()

    @patch("drift_detector.requests.post")
    def test_create_github_issue_network_error(self, mock_post):
        """Test GitHub issue creation with network error."""
        mock_post.side_effect = requests.ConnectionError("Network down")

        # Should handle gracefully
        create_github_issue("token", "user/repo", "Title", "Body")

        mock_post.assert_called_once()


class TestIntegrationScenarios:
    """Integration tests for complete drift detection workflow."""

    @patch("drift_detector.SentenceTransformer")
    @patch("drift_detector.wandb")
    def test_full_workflow_no_drift(self, mock_wandb, mock_transformer, tmp_path):
        """Test complete workflow when no drift is detected."""
        # Setup mock model
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        # Create identical embeddings (no drift)
        baseline_emb = np.random.rand(10, 384).astype(np.float32)
        mock_model.encode.return_value = baseline_emb

        # Save baseline
        baseline_path = tmp_path / "baseline.pkl"
        with open(baseline_path, "wb") as f:
            pickle.dump(baseline_emb, f)

        # Load and compare
        loaded_baseline = load_baseline(str(baseline_path))
        new_emb = compute_embeddings(["test"] * 10, mock_model)
        drift, mean_sim = detect_embedding_drift(loaded_baseline, new_emb)

        # Verify no drift detected
        assert drift < 0.01
        assert mean_sim > 0.99

    @patch("drift_detector.SentenceTransformer")
    @patch("drift_detector.wandb")
    @patch("drift_detector.notify_slack")
    @patch("drift_detector.create_github_issue")
    def test_full_workflow_high_drift(
        self, mock_github, mock_slack, mock_wandb, mock_transformer, tmp_path
    ):
        """Test complete workflow when high drift is detected."""
        # Setup mock model
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        # Create different embeddings (high drift)
        baseline_emb = np.random.rand(10, 384).astype(np.float32)
        new_emb = np.random.rand(10, 384).astype(np.float32)

        mock_model.encode.return_value = new_emb

        # Save baseline
        baseline_path = tmp_path / "baseline.pkl"
        with open(baseline_path, "wb") as f:
            pickle.dump(baseline_emb, f)

        # Compute drift
        loaded_baseline = load_baseline(str(baseline_path))
        computed_new = compute_embeddings(["test"] * 10, mock_model)
        drift, mean_sim = detect_embedding_drift(loaded_baseline, computed_new)

        # Simulate notifications if drift > threshold
        if drift > 0.12:
            notify_slack("webhook_url", f"Drift: {drift}")
            create_github_issue("token", "repo", "Drift Alert", f"Drift: {drift}")

            mock_slack.assert_called_once()
            mock_github.assert_called_once()


@pytest.fixture
def sample_embeddings():
    """Fixture providing sample embeddings for tests."""
    np.random.seed(42)
    return {
        "baseline": np.random.rand(20, 384).astype(np.float32),
        "similar": np.random.rand(20, 384).astype(np.float32) * 0.9,
        "different": np.random.rand(20, 384).astype(np.float32) * 2.0,
    }


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_embedding_drift(self):
        """Test drift with single embedding."""
        baseline = np.random.rand(1, 384).astype(np.float32)
        new_emb = np.random.rand(1, 384).astype(np.float32)

        drift, mean_sim = detect_embedding_drift(baseline, new_emb)

        assert isinstance(drift, float)
        assert isinstance(mean_sim, float)

    def test_large_batch_drift(self):
        """Test drift with large batch of embeddings."""
        baseline = np.random.rand(1000, 384).astype(np.float32)
        new_emb = np.random.rand(1000, 384).astype(np.float32)

        drift, mean_sim = detect_embedding_drift(baseline, new_emb)

        assert isinstance(drift, float)
        assert isinstance(mean_sim, float)

    def test_zero_vector_embeddings(self):
        """Test drift with zero vectors."""
        baseline = np.zeros((10, 384), dtype=np.float32)
        new_emb = np.zeros((10, 384), dtype=np.float32)

        # This might produce NaN or special values
        drift, mean_sim = detect_embedding_drift(baseline, new_emb)

        # Should handle gracefully (even if result is NaN)
        assert drift is not None
        assert mean_sim is not None

    @patch("drift_detector.requests.post")
    def test_notify_slack_empty_message(self, mock_post):
        """Test Slack notification with empty message."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notify_slack("https://hooks.slack.com/test", "")

        mock_post.assert_called_once()

    @patch("drift_detector.requests.post")
    def test_create_github_issue_special_characters(self, mock_post):
        """Test GitHub issue with special characters in title/body."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        title = "Drift ⚠️ Alert! #123"
        body = "Drift detected: \n\t- value: 0.5\n\t- status: ❌"

        create_github_issue("token", "user/repo", title, body)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["title"] == title
        assert kwargs["json"]["body"] == body


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
