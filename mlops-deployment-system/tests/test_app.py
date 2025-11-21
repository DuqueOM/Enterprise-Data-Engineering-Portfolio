from fastapi.testclient import TestClient
from space.app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    response_data = r.json()
    assert "status" in response_data
    assert response_data["status"] == "ok"
    assert "model_version" in response_data


def test_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200
    # Check if it's Prometheus metrics format
    assert "# HELP" in r.text
    assert "# TYPE" in r.text


def test_predict_no_model():
    """Test predict endpoint when no model is loaded."""
    r = client.post(
        "/predict",
        json={"features": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]},
    )
    # Should return error when no model is available
    assert r.status_code == 200
    assert "error" in r.json()


def test_predict_invalid_payload():
    """Test predict endpoint with invalid payload."""
    r = client.post("/predict", json={})
    assert r.status_code == 422  # Validation error


def test_predict_missing_features():
    """Test predict endpoint with missing features."""
    r = client.post("/predict", json={"features": []})
    assert r.status_code == 422  # Validation error
