"""
P4 - Validación y procesamiento de datos
Valida campos mínimos y normaliza texto para indexación.
Compatible con P4 y con formato JSONL de P2 (id, source_url, region, text, date_fetched).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from typing import Dict, Iterable

from pydantic import BaseModel, Field, ValidationError

try:
    # Optional import; processing can run without sanitizer
    from scripts.pii_sanitizer import sanitize_record  # type: ignore
except Exception:  # pragma: no cover
    sanitize_record = None  # type: ignore


class Record(BaseModel):
    id: str
    source_url: str
    region: str
    text: str = Field(min_length=30)
    date_fetched: str
    title: str | None = None  # optional passthrough


def normalize_text(t: str) -> str:
    t = re.sub(r"\s+", " ", t or "").strip()
    return t


def iter_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def validate_and_process(input_path: str, output_path: str, sanitize: bool = False) -> int:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    ok = 0
    with open(output_path, "w", encoding="utf8") as out:
        for raw in iter_jsonl(input_path):
            # Normalización simple
            raw["text"] = normalize_text(raw.get("text", ""))
            raw["region"] = normalize_text(raw.get("region", ""))
            if sanitize and sanitize_record is not None:
                raw = sanitize_record(raw)
            # Fecha a ISO si es posible
            df = raw.get("date_fetched")
            try:
                if df:
                    # Acepta YYYY-MM-DD o ISO
                    if len(df) == 10:
                        raw["date_fetched"] = datetime.strptime(df, "%Y-%m-%d").date().isoformat()
                else:
                    raw["date_fetched"] = datetime.utcnow().date().isoformat()
            except Exception:
                raw["date_fetched"] = datetime.utcnow().date().isoformat()

            try:
                rec = Record(**raw)
            except ValidationError:
                continue
            out.write(json.dumps(rec.model_dump(), ensure_ascii=False) + "\n")
            ok += 1
    return ok


def main():
    parser = argparse.ArgumentParser(description="Validate and process JSONL records")
    parser.add_argument("--input", default="data/raw/scraped_data.jsonl", help="Input JSONL path")
    parser.add_argument("--output", default="data/processed/clean.jsonl", help="Output JSONL path")
    parser.add_argument("--sanitize", action="store_true", help="Apply PII sanitization where available")
    args = parser.parse_args()

    count = validate_and_process(args.input, args.output, sanitize=args.sanitize)
    print(f"✔ Processed {count} valid records -> {args.output}")


if __name__ == "__main__":
    main()
