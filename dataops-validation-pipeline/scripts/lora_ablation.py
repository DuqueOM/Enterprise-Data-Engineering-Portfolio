"""
P1 - LoRA Ablation Runner [P4]

Runs a small grid over LoRA hyperparameters using train_lora.py with --max_steps
and writes a CSV report with the tried configurations and exit codes.
This is a lightweight harness intended for smoke experiments. [P4]
"""

import argparse  # [P4]
import csv  # [P4]
import os  # [P4]
import subprocess  # [P4]
import sys  # [P4]
from itertools import product  # [P4]
from pathlib import Path  # [P4]

ROOT = Path(__file__).resolve().parents[1]  # [P4]


def run_cmd(cmd):  # [P4]
    print("$", " ".join(cmd), flush=True)  # [P4]
    return subprocess.call(cmd, cwd=str(ROOT))  # [P4]


def main():  # [P4]
    ap = argparse.ArgumentParser()  # [P4]
    ap.add_argument("--train", required=True, help="Path to train jsonl with fields: input_text,target_text")  # [P4]
    ap.add_argument("--validation", default=None)  # [P4]
    ap.add_argument("--model", default="google/flan-t5-base")  # [P4]
    ap.add_argument("--r", default="4,8")  # [P4]
    ap.add_argument("--alpha", default="16,32")  # [P4]
    ap.add_argument("--dropout", default="0.05,0.1")  # [P4]
    ap.add_argument("--max_steps", type=int, default=10)  # [P4]
    ap.add_argument("--epochs", type=int, default=0)  # [P4]
    ap.add_argument("--out", default="results/lora_ablation.csv")  # [P4]
    args = ap.parse_args()  # [P4]

    r_vals = [int(x) for x in args.r.split(",") if x]  # [P4]
    alpha_vals = [int(x) for x in args.alpha.split(",") if x]  # [P4]
    dropout_vals = [float(x) for x in args.dropout.split(",") if x]  # [P4]

    os.makedirs(ROOT / "results", exist_ok=True)  # [P4]

    rows = []  # [P4]
    for r, a, d in product(r_vals, alpha_vals, dropout_vals):  # [P4]
        out_dir = ROOT / f"out/lora_r{r}_a{a}_d{d}"  # [P4]
        cmd = [  # [P4]
            sys.executable,
            "scripts/train_lora.py",
            "--model_name", args.model,
            "--train", args.train,
            "--output_dir", str(out_dir),
            "--max_steps", str(args.max_steps),
            "--epochs", str(args.epochs),
            "--lora_r", str(r),
            "--lora_alpha", str(a),
            "--lora_dropout", str(d),
            "--fp16",
        ]
        if args.validation:
            cmd += ["--validation", args.validation]
        rc = run_cmd(cmd)  # [P4]
        rows.append({  # [P4]
            "r": r,
            "alpha": a,
            "dropout": d,
            "max_steps": args.max_steps,
            "epochs": args.epochs,
            "exit_code": rc,
            "output_dir": str(out_dir),
        })

    with open(ROOT / args.out, "w", newline="", encoding="utf8") as f:  # [P4]
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["r","alpha","dropout","max_steps","epochs","exit_code","output_dir"])  # [P4]
        writer.writeheader()  # [P4]
        for r in rows:  # [P4]
            writer.writerow(r)  # [P4]
    print(f"✔ LoRA ablation report -> {args.out}")  # [P4]


if __name__ == "__main__":  # [P4]
    main()  # [P4]
