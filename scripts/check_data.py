#!/usr/bin/env python3
import csv
import re
from pathlib import Path

D = Path("data/ecommerce")
REQ = ["doc_id", "title", "source_url", "retrieved_at", "document_version", "audience"]

if not D.exists():
    print(f"Directory {D} does not exist.")
    exit(1)

mds = sorted(D.glob("*.md"))
sources_path = D / "sources.csv"
rows = list(csv.DictReader(open(sources_path, encoding="utf-8"))) if sources_path.exists() else []

ids = []
auds = {}

for p in mds:
    content = p.read_text(encoding="utf-8")
    parts = content.split("---")
    if len(parts) >= 3:
        fm = {}
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip("\"'")
        doc_id = fm.get("doc_id")
        ids.append(doc_id)
        aud = fm.get("audience")
        auds[aud] = auds.get(aud, 0) + 1
        
        is_ok = all(k in fm for k in REQ) and doc_id == p.stem
        status = "OK" if is_ok else "THIEU METADATA"
        print(f"{p.name:40} {status}")

print("-" * 50)
print(f"so file : {len(mds)} (can 5-10)")
csv_ids = sorted(r["doc_id"] for r in rows)
is_match = sorted(filter(None, ids)) == csv_ids
print(f"csv     : {'khop' if is_match else 'LECH'}")
print(f"audience: {auds}")
