import os
import json
from typing import List

import faiss  # type: ignore
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from src.ingestion.scraper import WebScraper

app = FastAPI(title="p4-qa-service")

INDEX_PATH = os.environ.get("P4_INDEX_PATH", "data/knowledge_base/index.faiss")
META_PATH = os.environ.get("P4_META_PATH", "data/knowledge_base/meta.jsonl")
MODEL_NAME = os.environ.get("P4_EMB_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_index = None
_metas: List[dict] = []
_model = None


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


@app.on_event("startup")
def startup():
    # Carga lazy en primeras llamadas
    pass


@app.get("/health")
def health():
    return {
        "status": "ok",
        "index_exists": os.path.exists(INDEX_PATH),
        "meta_exists": os.path.exists(META_PATH),
        "model": MODEL_NAME,
    }


@app.post("/api/v1/ingest")
def api_ingest(sources_path: str = "configs/sources.yaml"):
    scraper = WebScraper(config_path=sources_path)
    chunks = scraper.scrape_all_sources()
    if not chunks:
        return {"status": "no-content"}
    out = scraper.save_chunks(chunks, "data/raw/scraped_data.jsonl")
    return {"status": "ok", "records": len(chunks), "output": out}


@app.post("/api/v1/index")
def api_index(input_path: str = "data/raw/scraped_data.jsonl"):
    from src.processing.validate_and_process import validate_and_process
    from src.search.index_knowledge_base import main as index_main

    # Procesar
    processed_path = "data/processed/clean.jsonl"
    n = validate_and_process(input_path, processed_path)
    if n == 0:
        return {"status": "no-valid-records"}
    # Indexar (reutilizamos CLI interna)
    index_main()
    # invalidate cache
    global _index, _metas, _model
    _index = None
    _metas = []
    _model = None
    return {"status": "ok", "processed": n, "index_path": INDEX_PATH}


def _ensure_loaded():
    global _index, _metas, _model
    if _index is None and os.path.exists(INDEX_PATH):
        _index = faiss.read_index(INDEX_PATH)
    if not _metas and os.path.exists(META_PATH):
        with open(META_PATH, "r", encoding="utf8") as f:
            _metas = [json.loads(line) for line in f if line.strip()]
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)


@app.post("/api/v1/query")
def query(payload: QueryRequest):
    _ensure_loaded()
    if _index is None or not _metas:
        return {"error": "index not available"}
    q_emb = _model.encode([payload.question], convert_to_numpy=True)
    # normalizar para IP ~ cos
    q_emb = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-10)
    scores, idxs = _index.search(q_emb.astype("float32"), payload.top_k)
    results = []
    for score, idx in zip(scores[0].tolist(), idxs[0].tolist()):
        if idx < 0 or idx >= len(_metas):
            continue
        m = _metas[idx]
        results.append(
            {
                "title": m.get("title"),
                "url": m.get("source_url"),
                "region": m.get("region"),
                "date": m.get("date_fetched"),
                "confidence": float(score),
            }
        )
    return {"answer": results[0] if results else None, "sources": results}
