"""
P4 - PII Sanitizer [regex-based]
Remueve o enmascara PII común en campos de texto de un JSONL.
Uso:
  python scripts/pii_sanitizer.py --input data/raw/scraped_data.jsonl --output data/raw/scraped_data_sanitized.jsonl
"""

import argparse
import json
import os
import re
from typing import Dict

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[ -]?)?(?:\(?\d{2,4}\)?[ -]?)?\d{3,4}[ -]?\d{3,4})")
ID_RE = re.compile(r"\b\d{5,}\b")  # números largos


def sanitize_text(t: str) -> str:
    if not t:
        return t
    t = EMAIL_RE.sub("[EMAIL]", t)
    t = PHONE_RE.sub("[PHONE]", t)
    t = ID_RE.sub("[ID]", t)
    return t


def sanitize_record(obj: Dict) -> Dict:
    obj = dict(obj)
    if "text" in obj:
        obj["text"] = sanitize_text(obj["text"])
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    n = 0
    with open(args.input, "r", encoding="utf8") as fin, open(args.output, "w", encoding="utf8") as fout:
        for line in fin:
            if not line.strip():
                continue
            obj = json.loads(line)
            obj = sanitize_record(obj)
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
            n += 1
    print(f"✔ Sanitized {n} records -> {args.output}")


if __name__ == "__main__":
    main()
