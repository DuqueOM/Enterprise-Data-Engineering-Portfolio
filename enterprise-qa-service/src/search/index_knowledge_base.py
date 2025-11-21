"""
P4 - Indexación de base de conocimiento con FAISS
Lee registros limpios (JSONL), genera embeddings y construye índice FAISS.
"""

import argparse
import json
import os
from typing import List, Tuple

import faiss  # type: ignore
import numpy as np


def load_records(path: str) -> Tuple[List[str], List[dict]]:
    texts: List[str] = []
    metas: List[dict] = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            texts.append(obj["text"])  # contenido
            metas.append({k: obj.get(k) for k in ["id", "source_url", "region", "date_fetched", "title"]})
    return texts, metas


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    # Normalizamos para usar similitud coseno mediante producto interno
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10
    embeddings = embeddings / norms
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings.astype("float32"))
    return index


def save_index(index: faiss.IndexFlatIP, index_path: str):
    os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
    faiss.write_index(index, index_path)


def save_meta(metas: List[dict], meta_path: str):
    os.makedirs(os.path.dirname(meta_path) or ".", exist_ok=True)
    with open(meta_path, "w", encoding="utf8") as f:
        for meta in metas:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Index knowledge base with FAISS")
    parser.add_argument("--input", default="data/processed/clean.jsonl", help="Input JSONL path")
    parser.add_argument("--index-out", default="data/knowledge_base/index.faiss", help="FAISS index output path")
    parser.add_argument("--meta-out", default="data/knowledge_base/meta.jsonl", help="Metadata JSONL output path")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model")
    parser.add_argument("--smoke", action="store_true", help="Fast path for CI: skip heavy downloads and use random embeddings")
    args = parser.parse_args()

    texts, metas = load_records(args.input)
    if not texts:
        print("No records to index.")
        return

    if args.smoke:
        rng = np.random.RandomState(0)
        embeddings = rng.randn(len(texts), 8)
    else:
        # Importar perezosamente para evitar descarga del modelo en CI smoke
        from sentence_transformers import SentenceTransformer  # type: ignore
        model = SentenceTransformer(args.model)
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    index = build_faiss_index(embeddings)
    save_index(index, args.index_out)
    save_meta(metas, args.meta_out)
    print(f"✔ Indexed {len(texts)} records -> {args.index_out}\n✔ Metadata -> {args.meta_out}")


if __name__ == "__main__":
    main()
