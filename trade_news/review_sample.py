"""Prepare a deterministic diagnostic review sample, without supplying judgments."""
from collections import defaultdict, deque
import csv
import hashlib
import json
from pathlib import Path

from .articles import read_jsonl
from .corpus import REVIEW_FIELDS

SEED = "export-news-review-v1"
CASES = {"b30d353a15880d52e0b3", "a1348320f184c51f24f5"}


def select_records(records, size=60):
    rows = [r for r in records if r.get("fetch_status") == "article_extracted"]
    selected = sorted([r for r in rows if r["record_id"] in CASES], key=lambda r: r["record_id"])[:size]
    seen = {r["record_id"] for r in selected}
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["record_id"] in seen:
            continue
        support = min(2, row["positive_count"]+row["negative_count"])
        facet = (row.get("document_role_proposal", "unresolved"), row.get("scope_proposal"), row.get("publisher_group", row["publisher"]), support)
        groups[row["publication_date"][:4]][facet].append(row)
    queues = {}
    key = lambda row: hashlib.sha256((SEED+row["record_id"]).encode()).hexdigest()
    for year, facets in sorted(groups.items()):
        buckets = [deque(sorted(group, key=key)) for _, group in sorted(facets.items())]
        ordered = []
        while any(buckets):
            for bucket in buckets:
                if bucket:
                    ordered.append(bucket.popleft())
        queues[year] = deque(ordered)
    while len(selected) < size and any(queues.values()):
        for year in sorted(queues):
            if queues[year] and len(selected) < size:
                selected.append(queues[year].popleft())
    return selected


def prepare(directory, size=60):
    directory = Path(directory)
    output = directory/"review_sample.csv"
    if output.exists():
        with output.open(encoding="utf8", newline="") as stream:
            previous = list(csv.DictReader(stream))
        if any(any(row.get(k, "").strip() for k in ["include", "reviewer", "sentiment_gold", "notes", "document_role_gold", "reported_period", "comparison_base"]) for row in previous):
            raise ValueError("The sample contains review work; preserve it instead of overwriting")
    records = read_jsonl(directory/"headlines.jsonl")
    selected = select_records(records, size)
    fields = REVIEW_FIELDS+["publisher", "publication_date", "selection_reason", "document_role_gold", "reported_period", "comparison_base"]
    with output.open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({"record_id": r["record_id"], "title": r.get("publisher_title") or r["title"],
            "url": r["article_url"], "publisher": r["publisher"], "publication_date": r["publication_date"],
            "selection_reason": "Known diagnostic case" if r["record_id"] in CASES else "Year and cue-facet diagnostic sampling"}
            for r in selected)
    manifest = {"seed": SEED, "requested_size": size, "selected_size": len(selected),
        "source_features_sha256": hashlib.sha256((directory/"headlines.jsonl").read_bytes()).hexdigest(),
        "selection": "Two prespecified real diagnostic cases, then round-robin years and role/scope/domain/lexical-support facets; SHA-256 ordering within facets.",
        "sampling_claim": "Purposive diagnostic coverage, not probability sampling or an independent held-out benchmark.",
        "human_labels_generated": 0, "record_ids": [r["record_id"] for r in selected]}
    (directory/"review_sample_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    return manifest
