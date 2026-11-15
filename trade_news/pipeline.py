"""Clean records, audit duplicates, and calculate source-balanced headline tone."""
from collections import defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from statistics import mean
from urllib.parse import urlparse

from .nlp import analyze, normalize, METHOD


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text("utf8").splitlines() if line.strip()]


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def prepare(records):
    output, duplicates, rejected, seen_urls, seen_titles = [], [], [], set(), set()
    for record in sorted(records, key=lambda r: (r.get("published_at", ""), r.get("url", ""))):
        try:
            stamp = datetime.fromisoformat(record["published_at"])
            if stamp.tzinfo is None or not record["title"].strip() or urlparse(record["url"]).scheme not in {"http", "https"}:
                raise ValueError("Invalid metadata")
        except (ValueError, KeyError, TypeError):
            rejected.append(record.get("record_id", "missing_id"))
            continue
        key = normalize(record["title"])
        if record["url"] in seen_urls or key in seen_titles:
            duplicates.append({"record_id": record["record_id"], "reason": "same_url_or_normalized_headline"})
            continue
        seen_urls.add(record["url"])
        seen_titles.add(key)
        output.append({**record, "month": stamp.strftime("%Y-%m"), **analyze(record["title"])})
    return output, {"input_records": len(records), "retained_records": len(output),
                    "duplicates": duplicates, "rejected_metadata": rejected}


def aggregate(rows, months=None, min_scored=3, min_sources=2):
    if min_scored < 1 or min_sources < 1:
        raise ValueError("Coverage thresholds must be positive")
    groups = defaultdict(list)
    for month in months or []:
        groups[(month, "overall", "All relevant headlines")] = []
    for row in rows:
        if not row["relevant"]:
            continue
        groups[(row["month"], "overall", "All relevant headlines")].append(row)
        for dimension, field in [("sector", "sectors"), ("partner", "partners"), ("theme", "themes")]:
            for label in row[field] or ["Not mentioned"]:
                groups[(row["month"], dimension, label)].append(row)
    output = []
    for (month, dimension, group), records in sorted(groups.items()):
        by_source = defaultdict(list)
        scored = [r for r in records if r["tone_score"] is not None]
        for row in scored:
            by_source[row["publisher"]].append(row["tone_score"])
        sufficient = len(scored) >= min_scored and len(by_source) >= min_sources
        output.append({"month": month, "dimension": dimension, "group": group,
                       "n_records": len(records), "n_scored": len(scored),
                       "n_scored_publishers": len(by_source),
                       "score_coverage": len(scored)/len(records) if records else 0.0,
                       "headline_tone_index": round(100*mean(mean(v) for v in by_source.values()), 4) if sufficient else None,
                       "status": "provisional" if sufficient else "insufficient_coverage",
                       "min_scored": min_scored, "min_sources": min_sources})
    return output


def build(data_dir):
    data_dir = Path(data_dir)
    raw_path = data_dir / "headlines_raw.jsonl"
    rows, audit = prepare(read_jsonl(raw_path))
    log = json.loads((data_dir / "collection_log.json").read_text("utf8"))
    months = [r["month"] for r in log["requests"]]
    indices = aggregate(rows, months)
    (data_dir / "headlines.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows), encoding="utf8")
    write_json(data_dir / "indices.json", indices)
    write_json(data_dir / "processing_audit.json", {**audit, "relevant_records": sum(r["relevant"] for r in rows),
        "method": METHOD, "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "human_validation_status": "pending", "collection_failures": sum(r["status"] == "failed" for r in log["requests"])})
    # Include excluded relevance predictions so false negatives can be reviewed too.
    selected = sorted(rows, key=lambda r: hashlib.sha256(r["record_id"].encode()).hexdigest())[:40]
    annotation = data_dir / "annotations.csv"
    if not annotation.exists():
        with annotation.open("w", encoding="utf8", newline="") as stream:
            fields = ["record_id", "title", "url", "relevance_gold", "sentiment_gold", "themes_gold", "sectors_gold", "partners_gold", "annotator", "annotation_origin"]
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows({"record_id": r["record_id"], "title": r["title"], "url": r["url"]} for r in selected)
    return rows, indices
