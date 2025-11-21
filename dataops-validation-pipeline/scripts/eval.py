
#!/usr/bin/env python3
import argparse, pickle, json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

def load_index(indexpath):
    index = faiss.read_index(str(indexpath/"faiss.index"))
    metas = pickle.load(open(indexpath/"metas.pkl","rb"))
    return index, metas

def query_eval(index, metas, queries, emb_model, k=5):
    emb = emb_model.encode([q["question"] for q in queries], convert_to_numpy=True)
    faiss.normalize_L2(emb)
    D, I = index.search(emb, k)
    results = []
    for qi, inds in enumerate(I):
        retrieved = [metas[i] for i in inds]
        results.append(retrieved)
    return results

if __name__=="__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--indexdir", default="indexes")
    p.add_argument("--queries", default="data/processed/eval_queries.jsonl")
    p.add_argument("--embed_model", default="sentence-transformers/all-mpnet-base-v2")
    args = p.parse_args()
    index, metas = load_index(Path(args.indexdir))
    queries = [json.loads(l) for l in open(args.queries, "r", encoding="utf-8")]
    emb_model = SentenceTransformer(args.embed_model)
    res = query_eval(index, metas, queries, k=5, emb_model=emb_model)
    print("Sample retrieval for first query:", res[0])
