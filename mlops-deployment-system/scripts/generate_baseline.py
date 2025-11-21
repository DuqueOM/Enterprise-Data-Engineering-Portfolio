"""Generate baseline embeddings for drift detection."""

import argparse
import pickle

from sentence_transformers import SentenceTransformer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file", type=str, required=True, help="Text file with baseline texts"
    )
    parser.add_argument(
        "--output_file", type=str, default="baseline_emb.pkl", help="Output pickle file"
    )
    parser.add_argument(
        "--model_name", type=str, default="all-mpnet-base-v2", help="Embedding model"
    )
    args = parser.parse_args()

    print(f"Loading model: {args.model_name}")
    model = SentenceTransformer(args.model_name)

    print(f"Reading texts from: {args.input_file}")
    with open(args.input_file, encoding="utf-8") as f:
        texts = [line.strip() for line in f if line.strip()]

    if len(texts) == 0:
        print("No texts found in input file")
        return

    print(f"Generating embeddings for {len(texts)} texts...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    print(f"Saving embeddings to: {args.output_file}")
    with open(args.output_file, "wb") as f:
        pickle.dump(embeddings, f)

    print(f"Baseline embeddings saved: shape={embeddings.shape}")


if __name__ == "__main__":
    main()
