import logging
import os
import time

import joblib
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

API_VERSION = os.environ.get("API_VERSION", "v1.0.0")  # [P4] versión de API expuesta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model-service")

app = FastAPI(title="qna-model-service")

# Prometheus metrics
prediction_counter = Counter(
    "predictions_total", "Total predictions", ["model_version"]
)
prediction_duration = Histogram(
    "prediction_duration_seconds", "Time spent making predictions"
)
prediction_error_counter = Counter(  # [P4]
    "prediction_errors_total", "Total prediction errors", ["model_version"]  # [P4]
)  # [P4]


class PredictRequest(BaseModel):
    features: list[float] = Field(..., min_length=1)


MODEL_PATH = os.environ.get("MODEL_PATH", "artifacts/latest/model.joblib")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "unknown")
_model = None


def load_model():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        try:
            _model = joblib.load(MODEL_PATH)
            logger.info(f"Model loaded successfully from {MODEL_PATH}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            _model = None


@app.on_event("startup")
def startup():
    load_model()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": os.path.exists(MODEL_PATH),
        "model_version": MODEL_VERSION,
    }


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/version")  # [P4] endpoint opcional para exponer versión
def version():  # [P4]
    return {  # [P4]
        "api_version": API_VERSION,  # [P4]
        "model_version": MODEL_VERSION,  # [P4]
        "service": "qna-model-service",  # [P4]
    }  # [P4]


@app.post("/predict")
def predict(payload: PredictRequest):
    load_model()
    if _model is None:
        return {"error": "model not available"}

    start_time = time.time()
    try:
        pred = _model.predict([payload.features]).tolist()
        duration = time.time() - start_time

        # Record metrics
        prediction_counter.labels(model_version=MODEL_VERSION).inc()
        prediction_duration.observe(duration)

        return {
            "prediction": pred[0] if len(pred) == 1 else pred,
            "model_version": MODEL_VERSION,
            "processing_time": duration,
        }
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        prediction_error_counter.labels(model_version=MODEL_VERSION).inc()  # [P4]
        return {"error": str(e)}
