
# Dataset Card — Asistente PYME (MVP / Portfolio)

## Overview
Dataset of text chunks and Q/A pairs extracted from public, official sources (government portals).
Each chunk records provenance: source_url and date_fetched. Use only public data and respect site licenses.

## Format
JSONL with fields:
- id, source_url, date_fetched, title, text, language, region, tags

## Provenance & License
Record source_url and capture date for each chunk. Ensure compliance with robots.txt and site terms.
Include original license information for each source in the dataset metadata.
