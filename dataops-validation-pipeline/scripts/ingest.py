
#!/usr/bin/env python3
# ingest.py - lightweight ingestor for public pages (static + optional Playwright)

import argparse, json, time, uuid, re
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False

def safe_filename(url: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z-_]+", "-", url)
    short = uuid.uuid4().hex[:8]
    return f"{cleaned[:120]}-{short}".strip("-")

def fetch_static(url: str, timeout: int = 15):
    headers = {"User-Agent": "asistente-pyme-bot/0.1 (+https://example.org)"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text

def fetch_playwright(url: str, timeout: int = 30):
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright not available. Install playwright and run playwright install.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=timeout*1000)
        content = page.content()
        browser.close()
        return content

def extract_text_blocks(html: str):
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    candidates = soup.find_all(["h1","h2","h3","h4","p","li","dd","dt"], limit=1000)
    blocks = [el.get_text(" ", strip=True) for el in candidates if el.get_text(" ", strip=True)]
    if not blocks:
        body = soup.get_text(" ", strip=True)
        if body:
            blocks = [body]
    return {"title": title, "blocks": blocks}

def chunk_text_by_words(text: str, words_per_chunk: int = 250, overlap: int = 30):
    words = text.split()
    chunks = []
    i = 0
    n = len(words)
    while i < n:
        end = min(i + words_per_chunk, n)
        chunk = " ".join(words[i:end]).strip()
        if chunk:
            chunks.append(chunk)
        i = end - overlap
        if i < 0: i = 0
        if i >= n: break
    return chunks

def detect_language_safe(text: str):
    try:
        return detect(text)
    except Exception:
        return "es"

def auto_extract_qa(blocks: list):
    qas = []
    for i, block in enumerate(blocks):
        if "?" in block or "¿" in block:
            q = block.strip()
            a = blocks[i+1].strip() if i+1 < len(blocks) else ""
            if len(q)>5 and len(a)>0:
                qas.append({"question": q, "answer": a})
    return qas

def process_url(url: str, outdir: Path, region: str = None, use_playwright: bool = False, chunk_words: int = 250):
    print(f"Processing {url}")
    raw_name = safe_filename(url)
    raw_path = outdir / "raw" / f"{raw_name}.html"
    proc_path = outdir / "processed" / f"{raw_name}_chunks.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    proc_path.parent.mkdir(parents=True, exist_ok=True)
    if use_playwright:
        html = fetch_playwright(url)
    else:
        html = fetch_static(url)
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(html)
    parsed = extract_text_blocks(html)
    blocks = parsed.get("blocks", [])
    full_text = "\\n\\n".join(blocks)
    chunks = chunk_text_by_words(full_text, words_per_chunk=chunk_words)
    results = []
    ts = datetime.utcnow().isoformat()+"Z"
    for i,c in enumerate(chunks):
        item = {
            "id": f"{raw_name}_chunk_{i:04d}",
            "source_url": url,
            "title": parsed.get("title",""),
            "text": c,
            "region": region,
            "date_fetched": ts,
            "language": detect_language_safe(c),
            "tags": []
        }
        results.append(item)
    with open(proc_path, "w", encoding="utf-8") as f:
        for it in results:
            f.write(json.dumps(it, ensure_ascii=False) + "\\n")
    qas = auto_extract_qa(blocks)
    if qas:
        qafile = outdir / "processed" / f"{raw_name}_qas.jsonl"
        with open(qafile, "w", encoding="utf-8") as f:
            for q in qas:
                f.write(json.dumps(q, ensure_ascii=False) + "\\n")
    print(f"Saved raw: {raw_path} processed: {proc_path} chunks: {len(results)}")
    return results

def main():
    import argparse
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", type=str)
    group.add_argument("--urls", type=str)
    p.add_argument("--outdir", type=str, default="data")
    p.add_argument("--region", type=str, default=None)
    p.add_argument("--use-playwright", action="store_true")
    p.add_argument("--chunk-words", type=int, default=250)
    args = p.parse_args()
    urls = []
    if args.url:
        urls=[args.url]
    else:
        with open(args.urls,"r",encoding="utf-8") as f:
            urls = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    outdir = Path(args.outdir)
    all_chunks = []
    for u in urls:
        res = process_url(u, outdir, region=args.region, use_playwright=args.use_playwright, chunk_words=args.chunk_words)
        all_chunks.extend(res)
    # consolidate
    consolidated = outdir / "processed" / "faqs.jsonl"
    consolidated.parent.mkdir(parents=True, exist_ok=True)
    with open(consolidated, "w", encoding="utf-8") as fout:
        for p in (outdir / "processed").glob("*_chunks.jsonl"):
            with open(p, "r", encoding="utf-8") as fin:
                for line in fin:
                    fout.write(line)
    print("Consolidated:", consolidated)

if __name__ == '__main__':
    main()
