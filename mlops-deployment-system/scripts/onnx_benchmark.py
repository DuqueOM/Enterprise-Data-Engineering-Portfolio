"""
P3 - ONNX / Quantization Benchmark [P4]

Benchmark inference latency for a scikit-learn model:
- Native sklearn (joblib-loaded)
- ONNX via onnxruntime
- ONNX (quantized) via onnxruntime.quantization

Outputs CSV report with p50/p95 latency and optional accuracy if labels provided. [P4]
"""

import argparse  # [P4]
import csv  # [P4]
import os  # [P4]
import statistics  # [P4]
import time  # [P4]
from pathlib import Path  # [P4]

import joblib  # [P4]
import numpy as np  # [P4]
from onnxruntime import InferenceSession, SessionOptions  # [P4]
from onnxruntime.quantization import QuantType, quantize_dynamic  # [P4]
from skl2onnx import convert_sklearn  # [P4]
from skl2onnx.common.data_types import FloatTensorType  # [P4]

ROOT = Path(__file__).resolve().parents[1]  # [P4]


def load_sklearn_model(model_path: str):  # [P4]
    return joblib.load(model_path)  # [P4]


def prepare_inputs(model, n_samples: int, X_csv: str | None) -> np.ndarray:  # [P4]
    if X_csv and os.path.exists(X_csv):  # [P4]
        data = np.loadtxt(X_csv, delimiter=",", dtype=np.float32)  # [P4]
        return (
            data[:n_samples] if data.ndim == 2 else data.reshape(-1, 1)[:n_samples]
        )  # [P4]
    n_features = getattr(model, "n_features_in_", 16)  # [P4]
    rng = np.random.RandomState(0)  # [P4]
    return rng.randn(n_samples, n_features).astype(np.float32)  # [P4]


def bench_sklearn(model, X: np.ndarray, runs: int) -> tuple[float, float]:  # [P4]
    latencies: list[float] = []  # [P4]
    for _ in range(runs):  # [P4]
        t0 = time.time()  # [P4]
        _ = model.predict(X)  # [P4]
        latencies.append(time.time() - t0)  # [P4]
    return statistics.median(latencies), float(np.percentile(latencies, 95))  # [P4]


def export_onnx(model, n_features: int, onnx_path: str):  # [P4]
    onnx_model = convert_sklearn(
        model, initial_types=[("input", FloatTensorType([None, n_features]))]
    )  # [P4]
    with open(onnx_path, "wb") as f:  # [P4]
        f.write(onnx_model.SerializeToString())  # [P4]


def bench_onnx(onnx_path: str, X: np.ndarray, runs: int) -> tuple[float, float]:  # [P4]
    so = SessionOptions()  # [P4]
    sess = InferenceSession(
        onnx_path, sess_options=so, providers=["CPUExecutionProvider"]
    )  # [P4]
    input_name = sess.get_inputs()[0].name  # [P4]
    latencies: list[float] = []  # [P4]
    for _ in range(runs):  # [P4]
        t0 = time.time()  # [P4]
        _ = sess.run(None, {input_name: X})  # [P4]
        latencies.append(time.time() - t0)  # [P4]
    return statistics.median(latencies), float(np.percentile(latencies, 95))  # [P4]


def main():  # [P4]
    ap = argparse.ArgumentParser()  # [P4]
    ap.add_argument("--model_path", default="artifacts/latest/model.joblib")  # [P4]
    ap.add_argument(
        "--X_csv", default=None, help="CSV file with features (no header)"
    )  # [P4]
    ap.add_argument("--runs", type=int, default=10)  # [P4]
    ap.add_argument("--out", default="results/onnx_benchmarks.csv")  # [P4]
    ap.add_argument("--quantize", action="store_true")  # [P4]
    args = ap.parse_args()  # [P4]

    os.makedirs(ROOT / "results", exist_ok=True)  # [P4]

    model = load_sklearn_model(args.model_path)  # [P4]
    X = prepare_inputs(model, n_samples=128, X_csv=args.X_csv)  # [P4]

    p50_skl, p95_skl = bench_sklearn(model, X, runs=args.runs)  # [P4]

    n_features = X.shape[1]  # [P4]
    onnx_path = ROOT / "artifacts" / "latest" / "model.onnx"  # [P4]
    os.makedirs(onnx_path.parent, exist_ok=True)  # [P4]
    export_onnx(model, n_features, str(onnx_path))  # [P4]
    p50_onnx, p95_onnx = bench_onnx(str(onnx_path), X, runs=args.runs)  # [P4]

    p50_q, p95_q = None, None  # [P4]
    if args.quantize:  # [P4]
        q_path = str(onnx_path).replace(".onnx", ".int8.onnx")  # [P4]
        quantize_dynamic(str(onnx_path), q_path, weight_type=QuantType.QInt8)  # [P4]
        p50_q, p95_q = bench_onnx(q_path, X, runs=args.runs)  # [P4]

    out_csv = ROOT / args.out  # [P4]
    with open(out_csv, "w", newline="", encoding="utf8") as f:  # [P4]
        writer = csv.writer(f)  # [P4]
        writer.writerow(["variant", "p50_s", "p95_s"])  # [P4]
        writer.writerow(["sklearn", f"{p50_skl:.6f}", f"{p95_skl:.6f}"])  # [P4]
        writer.writerow(["onnx", f"{p50_onnx:.6f}", f"{p95_onnx:.6f}"])  # [P4]
        if p50_q is not None:  # [P4]
            writer.writerow(["onnx_int8", f"{p50_q:.6f}", f"{p95_q:.6f}"])  # [P4]

    print(f"✔ Benchmarks written to {out_csv}")  # [P4]


if __name__ == "__main__":  # [P4]
    main()  # [P4]
