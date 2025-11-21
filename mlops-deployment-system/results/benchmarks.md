# Benchmarks: ONNX / Quantization [P4]

This report describes how to reproduce latency benchmarks and expected outputs.

## How to run

```bash
# Install deps
pip install -r requirements.txt

# Run benchmark (CPU)
python scripts/onnx_benchmark.py \
  --model_path artifacts/latest/model.joblib \
  --runs 20 \
  --out results/onnx_benchmarks.csv \
  --quantize
```

Outputs `results/onnx_benchmarks.csv` with rows:

- `sklearn`: native scikit-learn (joblib)
- `onnx`: ONNX via onnxruntime
- `onnx_int8`: dynamic quantization with int8 weights

Columns:
- `variant`, `p50_s`, `p95_s`

## Notes
- Quantization typically improves p95 by 20–50% on CPU-bound inference, with minimal accuracy impact for linear/tree models. Validate accuracy for your case.
- For GPU, onnxruntime-gpu may offer additional gains; update providers accordingly.
