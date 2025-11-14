# Building a Searchable, Auditable QA Service: From DataOps to AIOps

This post explains how P4 integrates P1 (validation), P2 (ingestion), and P3 (service & monitoring) to deliver a production-ready QA system with cited answers.

## TL;DR
- Ingest → Process → Index → Query, with versioned artifacts and auditable answers.
- Ablations: chunk sizes, top-k, embedding models; LoRA hparams for model fine-tuning.
- ONNX/quantization improves CPU latency while retaining accuracy (tradeoffs documented).
- SLOs and runbook with Prometheus/Grafana; CI smoke ensures fast feedback.

## Architecture
- Ingestion (P2): web scraper to JSONL; sources in YAML.
- Processing (P1): pydantic validation + optional PII sanitizer.
- Index (P4): embeddings + FAISS; smoke mode for CI.
- API (P4/P3): FastAPI; query returns sources with date/region and confidence.
- Monitoring (P3): Prometheus metrics; Grafana dashboards; SLOs and runbook.

## Ablation Study
- Script: `P4/scripts/ablation.py`
- Dimensions: chunk-size, embedding model, top-k
- Output: `results/ablation_report.csv`

## Latency via ONNX/Quantization
- Script: `P3/scripts/onnx_benchmark.py` → `results/onnx_benchmarks.csv`
- Variants: sklearn vs ONNX vs INT8
- Notes on accuracy & tradeoffs included in results/benchmarks.md

## CI/CD
- `P4/.github/workflows/ci_smoke.yml`: ruff + pytest + smoke index build
- DVC: `P4/dvc.yaml` integrates ingest→process→index→eval

## SLOs & Runbook
- See `P3/docs/SLO_RUNBOOK.md` with queries and dashboards to import

## Future Work
- PR a notebook to Hugging Face examples (10-min quickstart)
- k6 stress tests + canary
- Cost analysis doc ($/1k queries)
