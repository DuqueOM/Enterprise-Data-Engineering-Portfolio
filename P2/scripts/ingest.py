# scripts/ingest.py
import argparse  # [P4] añadido para soportar argumentos CLI
import hashlib
import json
import os
import time

import requests
from bs4 import BeautifulSoup


def fetch_page(url, timeout=15):
    """Download the HTML content of a page. Raises on non-200 status."""
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def parse_html_to_chunks(html, url, region, chunk_size_chars=1500):
    """Parse HTML and break into text chunks suitable for annotation and NLP tasks."""
    soup = BeautifulSoup(html, "html.parser")
    texts = [
        p.get_text(" ", strip=True)
        for p in soup.select("p, h2, li")
        if p.get_text(strip=True)
    ]
    combined = "\n".join(texts)
    out = []
    for i in range(0, len(combined), chunk_size_chars):
        chunk = combined[i : i + chunk_size_chars].strip()
        if not chunk:
            continue
        uid = hashlib.sha1((url + str(i)).encode()).hexdigest()[:12]
        out.append(
            {
                "id": f"{uid}",
                "source_url": url,
                "region": region,
                "text": chunk,
                "date_fetched": time.strftime("%Y-%m-%d"),
            }
        )
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest web content into JSONL")  # [P4]
    parser.add_argument("--output", default="data/processed/faqs.jsonl", help="Output JSONL path")  # [P4]
    parser.add_argument("--region", default="Antioquia", help="Default region for URLs")  # [P4]
    parser.add_argument("--chunk-size", type=int, default=1500, help="Chunk size in characters")  # [P4]
    args = parser.parse_args()  # [P4]

    urls = [
        ("https://example.gov/faq", args.region),  # [P4] usa la región configurable
    ]
    os.makedirs(os.path.dirname(args.output) or "data/processed", exist_ok=True)  # [P4]
    all_out = []  # [P4]
    for u, region in urls:  # [P4]
        try:
            html = fetch_page(u)
        except Exception as e:
            print(f"Error fetching {u}: {e}")
            continue
        all_out += parse_html_to_chunks(html, u, region, chunk_size_chars=args.chunk_size)  # [P4]
    out_path = args.output  # [P4]
    with open(out_path, "w", encoding="utf8") as f:
        for item in all_out:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")  # [P4]
    print(f"Wrote {len(all_out)} chunks to {out_path}")
