# placeholder ingest script that produces a small sample dataset for smoke runs
import csv
import os
import random

OUT = "data/sample.csv"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["text", "label"])
    for i in range(50):
        writer.writerow([f"sample text {i}", random.choice([0, 1])])
print("Wrote", OUT)
