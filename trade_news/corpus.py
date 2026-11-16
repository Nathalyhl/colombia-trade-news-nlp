"""Separate collection, automatic proposals, human decisions and monthly estimates."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from .articles import read_jsonl, write_jsonl, reference_fingerprint
from .bank_method import aggregate, process_text, METHOD
from .classification import ACTIVITIES, propose, SCREENING_METHOD

REVIEW_FIELDS = ["record_id", "title", "url", "include", "activity", "reviewer", "annotation_origin", "notes", "sentiment_gold"]


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf8")


def read_reviews(path):
    if not Path(path).exists():
        return {}
    with Path(path).open(encoding="utf8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(REVIEW_FIELDS) <= set(reader.fieldnames or []):
            raise ValueError("Annotation schema changed. Preserve the old file before creating the article-review sheet.")
        reviews = {}
        for row in reader:
            identity = row["record_id"]
            if identity in reviews:
                raise ValueError("Duplicate review record ID")
            reviews[identity] = row
        return reviews


def apply_reviews(records, reviews):
    known = {r["record_id"] for r in records}
    if set(reviews) - known:
        raise ValueError("The review sheet contains IDs outside the current corpus")
    output = []
    for original in records:
        row = dict(original)
        identity = row["record_id"]
        review = reviews.get(identity, {})
        decision = review.get("include", "").strip()
        gold = review.get("sentiment_gold", "").strip()
        if decision not in {"", "yes", "no", "review"}:
            raise ValueError("Use yes, no, review or blank for include")
        if decision in {"yes", "no"} or gold:
            if not review.get("reviewer", "").strip() or review.get("annotation_origin") != "human":
                raise ValueError("Human decisions require a reviewer and annotation_origin=human")
        if gold and gold not in {"positive", "negative", "neutral"}:
            raise ValueError("Use positive, negative or neutral reference sentiment")
        valid_text = row.get("fetch_status") == "article_extracted" and row.get("processing_status") == "processed"
        if decision == "yes":
            if not valid_text:
                raise ValueError("An included article needs verified dated text")
            if review.get("activity") and review["activity"] not in ACTIVITIES:
                raise ValueError("An optional activity override must use an Annex 2 label")
        row["activity"] = review["activity"] if decision == "yes" and review.get("activity") else row.get("activity_proposal", "Other Activity")
        row["review_status"] = "human_reviewed" if decision in {"yes", "no"} else "pending"
        row["review_decision"] = decision or "pending"
        row["eligible_for_index"] = valid_text and (decision == "yes" or (not decision and row.get("scope_proposal") == "include"))
        if decision == "no" or decision == "review":
            row["eligible_for_index"] = False
        output.append(row)
    # One canonical URL or exact article-text hash contributes once.
    output.sort(key=lambda r: (0 if r.get("review_decision") == "yes" else 1 if r["eligible_for_index"] else 2,
                               r.get("publication_date") or "", r["record_id"]))
    seen_urls, seen_texts = {}, {}
    for row in output:
        if row.get("fetch_status") != "article_extracted":
            continue
        url = row.get("article_url") or row.get("resolved_url")
        checksum = row["text_sha256"]
        duplicate = seen_urls.get(url) or seen_texts.get(checksum)
        row["duplicate_of"] = duplicate
        if duplicate:
            row["eligible_for_index"] = False
        else:
            seen_urls[url] = row["record_id"]
            seen_texts[checksum] = row["record_id"]
    return sorted(output, key=lambda r: (r.get("publication_date") or "", r["record_id"]))


def evaluate_sentiment(records, reviews):
    lookup = {r["record_id"]: r for r in records}
    pairs = [(review["sentiment_gold"], lookup[identity].get("sentiment_label", "not_estimated"))
             for identity, review in reviews.items() if review.get("sentiment_gold", "").strip()]
    if not pairs:
        return {"status": "human_labels_pending", "n_labeled": 0, "accuracy": None, "macro_f1": None,
                "note": "No human reference sentiment labels. Software tests are not a domain accuracy score."}
    classes = ["positive", "negative", "neutral"]
    matrix = {label: {predicted: 0 for predicted in classes+["abstention"]} for label in classes}
    for gold, predicted in pairs:
        matrix[gold][predicted if predicted in classes else "abstention"] += 1
    f1 = []
    for label in classes:
        tp = matrix[label][label]
        fp = sum(matrix[g][label] for g in classes if g != label)
        fn = sum(value for p, value in matrix[label].items() if p != label)
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    return {"status": "evaluated_on_supplied_human_labels", "n_labeled": len(pairs),
            "accuracy": sum(g == p for g, p in pairs)/len(pairs), "macro_f1": sum(f1)/3,
            "confusion_matrix": matrix, "note": "Reviewer provenance is declared, not independently certified; this is not a held-out benchmark."}


def build(directory, verify_local_text=False):
    directory = Path(directory)
    records = read_jsonl(directory/"article_manifest.jsonl")
    fingerprint = reference_fingerprint()
    for row in records:
        host = urlparse(row.get("publisher_url") or row.get("article_url") or "").hostname
        row["publisher_group"] = host.removeprefix("www.") if host else row["publisher"]
        if row.get("fetch_status") != "article_extracted":
            continue
        text_path = directory/"raw"/"articles"/(row["record_id"]+".txt")
        stale = (row.get("reference_fingerprint") != fingerprint or row.get("method") != METHOD
                 or row.get("screening_method") != SCREENING_METHOD)
        if text_path.exists() and (verify_local_text or stale):
            text = text_path.read_text("utf8")
            if hashlib.sha256(text.encode()).hexdigest() != row["text_sha256"]:
                raise ValueError("The local article archive differs from its saved hash")
            row.update(process_text(text))
            row.update(propose(row.get("publisher_title") or row["title"], text))
            row["reference_fingerprint"] = fingerprint
        elif stale:
            raise ValueError("Source features use a different reference version; reprocess the local article archive")
    write_jsonl(directory/"article_manifest.jsonl", records)
    sheet = directory/"annotations.csv"
    existing_reviews = read_reviews(sheet)
    missing_reviews = [r for r in records if r.get("fetch_status") == "article_extracted" and r["record_id"] not in existing_reviews]
    if not sheet.exists() or missing_reviews:
        with sheet.open("w", encoding="utf8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDS)
            writer.writeheader()
            writer.writerows(existing_reviews.values())
            writer.writerows({"record_id": r["record_id"], "title": r.get("publisher_title") or r["title"],
                              "url": r.get("article_url") or r.get("resolved_url")} for r in missing_reviews)
    reviews = read_reviews(sheet)
    rows = apply_reviews(records, reviews)
    log = json.loads((directory/"collection_log.json").read_text("utf8"))
    months = [r["month"] for r in log["requests"]]
    indices = {"provisional": aggregate(rows, months), "human_reviewed": aggregate(rows, months, reviewed_only=True)}
    write_jsonl(directory/"headlines.jsonl", rows)
    write_json(directory/"indices.json", indices)
    audit = {"method": METHOD, "reference_fingerprint": fingerprint,
             "candidate_records": len(rows), "extracted_articles": sum(r.get("fetch_status") == "article_extracted" for r in rows),
             "eligible_articles": sum(r["eligible_for_index"] for r in rows),
             "human_reviewed_articles": sum(r["review_status"] == "human_reviewed" for r in rows),
             "duplicates": [{"record_id": r["record_id"], "duplicate_of": r["duplicate_of"]} for r in rows if r.get("duplicate_of")],
             "fetch_status_counts": dict(Counter(r["fetch_status"] for r in rows)),
             "scope_proposals": dict(Counter(r.get("scope_proposal", "not_extracted") for r in rows)),
             "document_role_proposals": dict(Counter(r.get("document_role_proposal", "not_extracted") for r in rows)),
             "collection_failures": sum(r["status"] == "failed" for r in log["requests"]),
             "raw_metadata_sha256": hashlib.sha256((directory/"headlines_raw.jsonl").read_bytes()).hexdigest(),
             "article_manifest_sha256": hashlib.sha256((directory/"article_manifest.jsonl").read_bytes()).hexdigest(),
             "analysis_scope": f"Colombian goods exports, {log['start']} to {log['end_exclusive']} exclusive; publisher article-body text only",
             "months_requested": len(months),
             "months_with_eligible_articles": len({r['month'] for r in rows if r['eligible_for_index']}),
             "discovery_status_counts": dict(Counter(str(r['status']) for r in log['requests'])),
             "manual_corpus_validation": "pending" if not any(r["review_status"] == "human_reviewed" for r in rows) else "partially_reviewed"}
    write_json(directory/"processing_audit.json", audit)
    write_json(directory/"validation_report.json", evaluate_sentiment(rows, reviews))
    from .destinations import build_destinations
    build_destinations(directory, rows)
    return rows, indices
