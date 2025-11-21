
#!/usr/bin/env python3
import json, argparse, pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

def load_jsonl(path):
    items=[]
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
    return items

def main(args):
    input_path = Path(args.input)
    index_dir = Path(args.indexdir)
    index_dir.mkdir(parents=True, exist_ok=True)
    items = load_jsonl(input_path)
    texts = [it["text"] for it in items]
    metas = [{"id": it.get("id"), "url": it.get("source_url"), "title": it.get("title"), "date": it.get("date_fetched"), "region": it.get("region")} for it in items]
    model = SentenceTransformer(args.embed_model)
    emb = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    faiss.write_index(index, str(index_dir / "faiss.index"))
    with open(index_dir / "metas.pkl", "wb") as f:
        pickle.dump(metas, f)
    print(f"Index saved: {index_dir}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=str, default="data/processed/faqs.jsonl")
    p.add_argument("--indexdir", type=str, default="indexes")
    p.add_argument("--embed_model", type=str, default="sentence-transformers/all-mpnet-base-v2")
    args = p.parse_args()
    main(args)
