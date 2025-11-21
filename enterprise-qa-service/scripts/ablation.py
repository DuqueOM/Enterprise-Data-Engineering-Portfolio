"""
P4 - Ablation Study Runner

Runs ablations over:
- chunk sizes for ingestion (scraper --chunk-size)
- embedding models for indexer (--model)
- top-k for evaluation (eval.py --top_k)

Outputs a CSV report at results/ablation_report.csv with EM@1 and latency stats.
Use --smoke to avoid heavy downloads (random embeddings used in index + faster eval).
"""

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: List[str]) -> int:
    print("$", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def parse_list(arg: str) -> List[str]:
    return [x.strip() for x in arg.split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-sizes", default="600,1000,1500")
    ap.add_argument("--models", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--topk", default="1,5")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--sources", default="configs/sources.yaml")
    ap.add_argument("--out", default="results/ablation_report.csv")
    args = ap.parse_args()

    chunk_sizes = [int(x) for x in parse_list(args.chunk_sizes)]
    models = parse_list(args.models)
    topks = [int(x) for x in parse_list(args.topk)]

    os.makedirs(ROOT / "results", exist_ok=True)

    report_rows = []

    for cs in chunk_sizes:
        # 1) Ingest (vary chunk size)
        rc = run([sys.executable, "src/ingestion/scraper.py", "--chunk-size", str(cs), "--config", args.sources])
        if rc != 0:
            print(f"Ingest failed for chunk-size={cs}")
            continue
        # 2) Process
        rc = run([sys.executable, "src/processing/validate_and_process.py", "--sanitize"])
        if rc != 0:
            print(f"Process failed for chunk-size={cs}")
            continue

        for model in models:
            # 3) Index (vary model)
            idx_cmd = [sys.executable, "-m", "src.search.index_knowledge_base", "--model", model]
            if args.smoke:
                idx_cmd.append("--smoke")
            rc = run(idx_cmd)
            if rc != 0:
                print(f"Index failed for model={model}")
                continue

            for k in topks:
                # 4) Eval (vary top-k)
                out_csv = ROOT / "results" / f"eval_cs{cs}_k{k}_m{Path(model).name.replace('-', '_')}.csv"
                eval_cmd = [
                    sys.executable,
                    "scripts/eval.py",
                    "--index",
                    "data/knowledge_base/index.faiss",
                    "--meta",
                    "data/knowledge_base/meta.jsonl",
                    "--test",
                    "data/test.jsonl",
                    "--out",
                    str(out_csv),
                    "--top_k",
                    str(k),
                ]
                if args.smoke:
                    eval_cmd.append("--smoke")
                rc = run(eval_cmd)
                if rc != 0:
                    print(f"Eval failed for top_k={k}")
                    continue
                # Parse EM@1 from csv
                try:
                    with open(out_csv, "r", encoding="utf8") as f:
                        rows = list(csv.DictReader(f))
                    em = sum(int(r.get("em1", 0)) for r in rows) / max(1, len(rows))
                    report_rows.append({
                        "chunk_size": cs,
                        "model": model,
                        "top_k": k,
                        "em1": f"{em:.4f}",
                        "mode": "smoke" if args.smoke else "full"
                    })
                except Exception:
                    report_rows.append({
                        "chunk_size": cs,
                        "model": model,
                        "top_k": k,
                        "em1": "n/a",
                        "mode": "smoke" if args.smoke else "full"
                    })

    # Write ablation report
    with open(ROOT / args.out, "w", newline="", encoding="utf8") as f:
        fieldnames = ["chunk_size", "model", "top_k", "em1", "mode"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in report_rows:
            writer.writerow(row)
    print(f"✔ Ablation report -> {args.out}")


if __name__ == "__main__":
    main()
