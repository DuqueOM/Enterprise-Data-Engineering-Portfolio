# scripts/clean.py
import json, os, re
from collections import defaultdict

def normalize_whitespace(s):
    return re.sub(r"\s+"," ", s).strip()

if __name__ == "__main__":
    in_path = "data/processed/faqs.jsonl"
    out_path = "data/processed/faqs_clean.jsonl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    seen = set()
    count = 0
    with open(in_path, 'r', encoding='utf8') as rf, open(out_path, 'w', encoding='utf8') as wf:
        for line in rf:
            obj = json.loads(line)
            obj['text'] = normalize_whitespace(obj.get('text',''))
            key = (obj.get('source_url'), obj.get('text')[:80])
            if key in seen:
                continue
            seen.add(key)
            wf.write(json.dumps(obj, ensure_ascii=False)+'\n')
            count += 1
    print(f"Wrote {count} cleaned records to {out_path}")
