"""Offline checks: source lineage, exact rebuild and unaltered annotation evaluation."""
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trade_news.pipeline import aggregate, prepare, read_jsonl
from trade_news.validation import validate

base = Path(__file__).resolve().parents[1]
data = base/"data"
read = lambda name: json.loads((data/name).read_text("utf8"))
raw = read_jsonl(data/"headlines_raw.jsonl")
rows, audit = prepare(raw)
log, saved_audit = read("collection_log.json"), read("processing_audit.json")
assert rows == read_jsonl(data/"headlines.jsonl"), "Enrichment is not reproducible"
assert aggregate(rows, [r["month"] for r in log["requests"]]) == read("indices.json"), "Index rebuild differs"
assert validate(rows, data/"annotations.csv") == read("validation_report.json"), "Validation report is stale"
assert hashlib.sha256((data/"headlines_raw.jsonl").read_bytes()).hexdigest() == saved_audit["raw_sha256"]
assert len(raw) == sum(r.get("accepted_items", 0) for r in log["requests"])
assert len({r["record_id"] for r in rows}) == len(rows)
for row in raw:
    assert urlparse(row["url"]).hostname == "news.google.com"
    assert urlparse(row["feed_url"]).hostname == "news.google.com"
    assert log["start"] <= row["published_at"][:10] < log["end_exclusive"]
    assert row["record_id"] == hashlib.sha256(row["url"].encode()).hexdigest()[:20]
    assert row["retrieved_at"] and row["date_origin"]
for key, value in audit.items():
    assert saved_audit[key] == value
for path in base.glob("*.ipynb"):
    notebook = json.loads(path.read_text("utf8"))
    assert notebook["nbformat"] == 4
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code" and not any(s.lstrip().startswith(("!", "%")) for s in cell["source"]):
            compile("".join(cell["source"]), path.name, "exec")
print(f"Verified {len(raw)} real metadata records, {len(rows)} deterministic enriched records, indices and validation state.")
