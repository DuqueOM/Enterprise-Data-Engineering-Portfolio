import os
import tempfile
import json
from src.processing.validate_and_process import validate_and_process


def test_validate_and_process_single_record():
    fd, in_path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    out_fd, out_path = tempfile.mkstemp(suffix=".jsonl")
    os.close(out_fd)

    try:
        rec = {
            "id": "t1",
            "source_url": "https://example.org",
            "region": "NA",
            "text": "This is a sufficiently long sample text for validation in tests.",
            "date_fetched": "2025-01-01",
        }
        with open(in_path, "w", encoding="utf8") as f:
            f.write(json.dumps(rec) + "\n")
        n = validate_and_process(in_path, out_path)
        assert n == 1
        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf8") as f:
            lines = [line for line in f if line.strip()]
        assert len(lines) == 1
    finally:
        for p in [in_path, out_path]:
            if os.path.exists(p):
                os.remove(p)
