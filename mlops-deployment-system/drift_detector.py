"""Detector simple de drift por embeddings.
- Usa sentence-transformers para embeddings.
- Compara embeddings nuevos contra baseline (pickle).
- Loggea en W&B y puede notificar via Slack / GitHub.
"""

import argparse
import logging
import os
import pickle
import sys

import numpy as np
import requests
import wandb
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drift-detector")

MODEL_NAME = os.environ.get("EMB_MODEL", "all-mpnet-base-v2")


def load_baseline(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Baseline no encontrada en {path}")
    with open(path, "rb") as f:
        return pickle.load(f)  # espera numpy array shape (N,D)


def compute_embeddings(texts: list[str], model):
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)


def detect_embedding_drift(baseline_emb: np.ndarray, new_emb: np.ndarray):
    # Compute cosine similarity matrix between new embeddings and baseline
    sims = cosine_similarity(new_emb, baseline_emb)
    # For each new embedding, take the best (maximum) similarity to any baseline vector
    max_sims = np.max(sims, axis=1)
    mean_sim = float(np.mean(max_sims))
    drift = 1.0 - mean_sim
    return drift, mean_sim


def notify_slack(webhook_url: str, message: str):
    payload = {"text": message}
    try:
        requests.post(webhook_url, json=payload, timeout=6)
    except Exception as e:
        logger.warning("Slack notify failed: %s", e)


def create_github_issue(token: str, repo: str, title: str, body: str):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Authorization": f"token {token}"}
    data = {"title": title, "body": body}
    try:
        r = requests.post(url, json=data, headers=headers, timeout=6)
        if r.status_code not in (200, 201):
            logger.warning("GitHub issue create failed: %s %s", r.status_code, r.text)
    except Exception as e:
        logger.warning("GitHub issue create error: %s", e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=str, default="baseline_emb.pkl")
    parser.add_argument(
        "--input_texts",
        type=str,
        required=True,
        help="Archivo .txt con un texto por línea (batch a evaluar)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.12,
        help="Umbral de drift para alertar (ej: 0.12)",
    )
    parser.add_argument(
        "--slack_webhook", type=str, default=os.environ.get("SLACK_WEBHOOK")
    )
    parser.add_argument(
        "--github_token", type=str, default=os.environ.get("GITHUB_TOKEN")
    )
    parser.add_argument(
        "--github_repo", type=str, default=os.environ.get("GITHUB_REPO")
    )
    parser.add_argument("--wandb_project", type=str, default="drift-monitor")
    parser.add_argument(
        "--update_baseline",
        action="store_true",
        help="Si se indica, actualiza baseline con el batch actual",
    )
    args = parser.parse_args()

    model = SentenceTransformer(MODEL_NAME)
    logger.info("Modelo de embeddings cargado: %s", MODEL_NAME)

    with open(args.input_texts, encoding="utf-8") as f:
        new_texts = [line.strip() for line in f if line.strip()]

    if len(new_texts) == 0:
        logger.error("No hay textos en %s", args.input_texts)
        sys.exit(2)

    new_emb = compute_embeddings(new_texts, model)

    if os.path.exists(args.baseline) and not args.update_baseline:
        baseline_emb = load_baseline(args.baseline)
    else:
        baseline_emb = new_emb
        with open(args.baseline, "wb") as f:
            pickle.dump(baseline_emb, f)
        logger.info("Baseline creada/actualizada en %s", args.baseline)

    drift, mean_sim = detect_embedding_drift(baseline_emb, new_emb)
    logger.info("Drift: %.4f  mean_sim: %.4f", drift, mean_sim)

    try:
        wandb.init(project=args.wandb_project, reinit=True)
        wandb.log(
            {
                "embedding_drift": drift,
                "mean_similarity": mean_sim,
                "n_new": len(new_texts),
            }
        )
        wandb.finish()
    except Exception as e:
        logger.warning("W&B log falló: %s", e)

    if drift > args.threshold:
        msg = (
            f"DRIFT ALERT: drift={drift:.4f} "
            f"(threshold={args.threshold}) mean_sim={mean_sim:.4f}"
        )
        logger.warning(msg)
        if args.slack_webhook:
            notify_slack(args.slack_webhook, msg)
        if args.github_token and args.github_repo:
            body = (
                f"Automatic drift alert\n\n"
                f"Metrics:\n- drift: {drift}\n- mean_sim: {mean_sim}\n"
                f"- sample_count: {len(new_texts)}\n\n"
                f"Investigate and consider retraining."
            )
            create_github_issue(
                args.github_token, args.github_repo, "DRIFT ALERT", body
            )
        sys.exit(3)
    else:
        logger.info(
            "No drift detected (drift=%.4f <= threshold=%.4f)", drift, args.threshold
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
