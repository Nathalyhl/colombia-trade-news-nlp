"""Offline feature/count reproduction; article-text NLP requires the local archive."""
import hashlib
import csv
import json
from pathlib import Path
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trade_news.articles import read_jsonl, reference_fingerprint
from trade_news.bank_method import aggregate, load_reference
from trade_news.collect import month_windows
from trade_news.corpus import apply_reviews, evaluate_sentiment, read_reviews
from trade_news.destinations import configuration_hash, identify, MARKETS
from trade_news.country_review import evaluate_countries, read_country_reviews
from trade_news.contextual import verify_scores, aggregate_scores

base = Path(__file__).resolve().parents[1]
data = base/"data"
read = lambda name: json.loads((data/name).read_text("utf8"))
load_reference()
raw = read_jsonl(data/"headlines_raw.jsonl")
manifest = read_jsonl(data/"article_manifest.jsonl")
reviews = read_reviews(data/"annotations.csv")
rows = apply_reviews(manifest, reviews)
log, audit = read("collection_log.json"), read("processing_audit.json")
months = [r["month"] for r in log["requests"]]
assert log["start"] == "2020-03-01" and log["end_exclusive"] == "2026-11-01"
assert months == [left[:7] for left, _ in month_windows(log["start"], log["end_exclusive"])]
assert len(months) == 80
assert len(raw) == sum(r.get("accepted_items", 0) for r in log["requests"])+sum(
    r.get("accepted_items", 0) for r in log.get("publisher_archive", {}).get("requests", []))
assert {r["record_id"] for r in raw} == {r["record_id"] for r in manifest}
assert len({r["record_id"] for r in manifest}) == len(manifest)
assert rows == read_jsonl(data/"headlines.jsonl"), "Stored decisions are stale"
assert {"provisional": aggregate(rows, months), "human_reviewed": aggregate(rows, months, True)} == read("indices.json")
assert evaluate_sentiment(rows, reviews) == read("validation_report.json")
assert audit["reference_fingerprint"] == reference_fingerprint()
assert audit["eligible_articles"] == sum(r["eligible_for_index"] for r in rows)
assert audit["extracted_articles"] == sum(r["fetch_status"] == "article_extracted" for r in rows)
for name, key in [("headlines_raw.jsonl", "raw_metadata_sha256"), ("article_manifest.jsonl", "article_manifest_sha256")]:
    assert hashlib.sha256((data/name).read_bytes()).hexdigest() == audit[key]
for row in raw:
    assert urlparse(row["url"]).hostname in {"news.google.com", "analdex.org", "www.analdex.org"}
    assert row["record_id"] == hashlib.sha256(row["url"].encode()).hexdigest()[:20]
    assert log["start"] <= row["published_at"][:10] < log["end_exclusive"]
for row in manifest:
    assert not any(key in row for key in ["body", "article_text", "html", "text"]), "Publisher bodies must remain in the local archive"
    if row["fetch_status"] != "article_extracted":
        continue
    assert row["reference_fingerprint"] == reference_fingerprint()
    assert row["text_source"] == "publisher_article"
    assert log["start"] <= row["publication_date"] < log["end_exclusive"]
    assert row["month"] == row["publication_date"][:7]
    assert sum(t["count"] for t in row["matched_terms"] if t["polarity"] == "positive") == row["positive_count"]
    assert sum(t["count"] for t in row["matched_terms"] if t["polarity"] == "negative") == row["negative_count"]
destinations = read_jsonl(data/"destinations.jsonl")
lookup = {r["record_id"]: r for r in rows}
assert len(destinations) == len(rows)
assert {r["record_id"] for r in destinations} == set(lookup)
for feature in destinations:
    row = lookup[feature["record_id"]]
    title = row.get("publisher_title") or row["title"]
    strict = identify(title)
    assert feature["configuration_sha256"] == configuration_hash()
    assert feature["title_sha256"] == hashlib.sha256(title.encode()).hexdigest()
    assert feature["destinations"] == strict["destinations"]
    assert feature["destination_evidence"] == strict["destination_evidence"]
    assert feature["non_destination_evidence"] == strict["non_destination_evidence"]
    assert set(strict["market_mentions"]) <= set(feature["market_mentions"]) <= set(MARKETS)
    if feature["body_sha256"]:
        assert feature["body_sha256"] == row.get("text_sha256")
    for hit in feature["mention_evidence"]:
        assert hit["alias"] in MARKETS[hit["market"]]
        assert hit["start"] >= 0 and hit["end"] > hit["start"]
    assert not any(key in feature for key in ["body", "article_text", "text", "html"])
assert evaluate_countries(rows, destinations, read_country_reviews(data, rows)) == read("destination_validation.json")
if (data/"contextual_manifest.json").exists():
    contextual_manifest = read("contextual_manifest.json")
    assert contextual_manifest["status"] == "complete", "Do not release partial model inference"
    contextual_scores = read_jsonl(data/"contextual_scores.jsonl")
    verify_scores(data, contextual_scores, contextual_manifest)
    assert {"all_eligible": aggregate_scores(contextual_scores, rows, months),
            "dictionary_matched": aggregate_scores(contextual_scores, rows, months, True)} == read("contextual_indices.json")
    assert contextual_manifest["human_reference_labels"] == read("validation_report.json")["n_labeled"]
sample_manifest = read("review_sample_manifest.json")
assert sample_manifest["source_features_sha256"] == hashlib.sha256((data/"headlines.jsonl").read_bytes()).hexdigest()
with (data/"review_sample.csv").open(encoding="utf8", newline="") as stream:
    sample = list(csv.DictReader(stream))
assert len(sample) == sample_manifest["selected_size"] == len({r["record_id"] for r in sample})
assert {r["record_id"] for r in sample} == set(sample_manifest["record_ids"]) <= set(lookup)
for review in sample:
    assert review["document_role_gold"] in {"", "statistical_reporting", "event_or_expectation", "mixed", "unsure"}
    if review["include"] in {"yes", "no"} or review["sentiment_gold"] or review["document_role_gold"]:
        assert review["reviewer"].strip() and review["annotation_origin"] == "human"
for notebook_path in base.glob("*.ipynb"):
    notebook = json.loads(notebook_path.read_text("utf8"))
    assert notebook["nbformat"] == 4
    assert len({c["id"] for c in notebook["cells"]}) == len(notebook["cells"])
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code" and not any(s.lstrip().startswith(("!", "%")) for s in cell["source"]):
            compile("".join(cell["source"]), notebook_path.name, "exec")
print(f"Verified lineage for {len(raw)} real candidates; reproduced article decisions, monthly feature aggregates and human-label evaluation offline.")
