"""
P4 - Eval (EM@1 + latency p50/p95)

Evaluates retrieval exact match@1 using the FAISS index and meta.
Optionally uses --smoke to avoid downloading models (random embeddings).

Usage:
  python scripts/eval.py \
    --test data/test.jsonl \
    --index data/knowledge_base/index.faiss \
    --meta data/knowledge_base/meta.jsonl \
    --out results/eval_results.csv \
    --smoke

Test file format (JSONL):
  {"question": "...", "expected_url": "https://..."}
"""

import argparse
import csv
import json
import os
import statistics
import time
from typing import List, Tuple

import faiss  # type: ignore
import numpy as np


def load_tests(path: str) -> List[dict]:
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        # Minimal sample
        with open(path, "w", encoding="utf8") as f:
            f.write(json.dumps({"question": "What is a company?", "expected_url": "https://example.org/1"}) + "\n")
            f.write(json.dumps({"question": "How to register a business?", "expected_url": "https://example.org/2"}) + "\n")
    with open(path, "r", encoding="utf8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_meta(meta_path: str) -> List[dict]:
    with open(meta_path, "r", encoding="utf8") as f:
        return [json.loads(line) for line in f if line.strip()]


def embed_queries(questions: List[str], model_name: str, smoke: bool) -> np.ndarray:
    if smoke:
        rng = np.random.RandomState(0)
        return rng.randn(len(questions), 8).astype("float32")
    from sentence_transformers import SentenceTransformer  # type: ignore

    model = SentenceTransformer(model_name)
    vecs = model.encode(questions, convert_to_numpy=True)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10
    return (vecs / norms).astype("float32")


def search(index_path: str, queries: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    index = faiss.read_index(index_path)
    return index.search(queries, top_k)


def evaluate(args) -> None:
    tests = load_tests(args.test)
    metas = load_meta(args.meta)
    questions = [t["question"] for t in tests]

    q_emb = embed_queries(questions, args.model, args.smoke)

    start = time.time()
    scores, idxs = search(args.index, q_emb, top_k=args.top_k)
    latency = time.time() - start

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    em_hits = []
    lats = []

    with open(args.out, "w", newline="", encoding="utf8") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "expected_url", "top1_url", "em1", "latency_s"])
        for i, t in enumerate(tests):
            top1_idx = idxs[i][0]
            top1_url = metas[top1_idx].get("source_url") if 0 <= top1_idx < len(metas) else None
            em1 = 1 if (top1_url and top1_url == t.get("expected_url")) else 0
            writer.writerow([t["question"], t.get("expected_url"), top1_url, em1, latency])
            em_hits.append(em1)
            lats.append(latency)

    p50 = statistics.median(lats) if lats else 0.0
    p95 = float(np.percentile(lats, 95)) if lats else 0.0
    em = sum(em_hits) / max(1, len(em_hits))
    print(f"EM@1={em:.3f} p50={p50:.3f}s p95={p95:.3f}s -> {args.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", default="data/test.jsonl")
    ap.add_argument("--index", default="data/knowledge_base/index.faiss")
    ap.add_argument("--meta", default="data/knowledge_base/meta.jsonl")
    ap.add_argument("--out", default="results/eval_results.csv")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--top_k", type=int, default=5)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.index) or not os.path.exists(args.meta):
        raise SystemExit("Index/meta not found. Build index first.")

    evaluate(args)


if __name__ == "__main__":
    main()
