"""Human country decisions and evaluation against pre-override predictions."""
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path

from .destinations import COUNTRIES, RULE_LABELS

FIELDS = ["record_id", "country", "decision", "reviewer", "annotation_origin", "notes", "title_sha256"]


def title_hash(row):
    return hashlib.sha256((row.get("publisher_title") or row["title"]).encode()).hexdigest()


def validate_reviews(reviews, rows):
    source = {r["record_id"]: r for r in rows}
    for key, review in reviews.items():
        if review["record_id"] not in source or review["country"] not in COUNTRIES:
            raise ValueError("Country review must refer to a source article and a supported country")
        if key != (review["record_id"], review["country"]):
            raise ValueError("Country review key does not match its record")
        if review["decision"] not in {"yes", "no", "unsure"}:
            raise ValueError("Country decisions must be yes, no or unsure")
        if not review["reviewer"].strip() or review["annotation_origin"] != "human" or not review["notes"].strip():
            raise ValueError("Identify the human reviewer and explain the source evidence")
        if review["title_sha256"] != title_hash(source[review["record_id"]]):
            raise ValueError("The reviewed source headline changed; review it again")
    return reviews


def read_country_reviews(directory, rows):
    path = Path(directory)/"destination_reviews.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf8", newline="") as stream:
        reader = csv.DictReader(stream)
        if set(reader.fieldnames or []) != set(FIELDS):
            raise ValueError("Unexpected country-review schema")
        reviews = {}
        for review in reader:
            key = (review["record_id"], review["country"])
            if key in reviews:
                raise ValueError("Duplicate article-country review pair")
            reviews[key] = review
    return validate_reviews(reviews, rows)


def assignments(rows, features, reviews=None, reviewed_only=False):
    """Each eligible article-country pair appears once; unknown mentions stay out."""
    reviews = validate_reviews(reviews or {}, rows)
    lookup = {r["record_id"]: r for r in features}
    output = []
    for row in rows:
        if not row.get("eligible_for_index"):
            continue
        feature = lookup.get(row["record_id"], {})
        automatic = set(feature.get("destinations", [])) & set(COUNTRIES)
        candidates = automatic | {country for identity, country in reviews if identity == row["record_id"]}
        for country in sorted(candidates):
            review = reviews.get((row["record_id"], country))
            if review and review["decision"] != "yes":
                continue
            if reviewed_only and not review:
                continue
            hits = [h for h in feature.get("destination_evidence", []) if h["market"] == country]
            output.append({**row, "country": country,
                "country_status": "Human confirmed" if review else "Automatic · pending review",
                "country_reason": review["notes"] if review else " ".join(dict.fromkeys(RULE_LABELS[h["rule"]] for h in hits)),
                "country_reviewer": review["reviewer"] if review else "",
                "country_aliases": ", ".join(sorted({h["alias"] for h in hits})),
                "country_auto_prediction": country in automatic})
    return output


def country_coverage(assignments_list):
    counts = Counter(row["country"] for row in assignments_list)
    return [{"country": country, "articles": count} for country, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def evaluate_countries(rows, features, reviews):
    validate_reviews(reviews, rows)
    eligible = {r["record_id"] for r in rows if r.get("eligible_for_index")}
    predicted = {r["record_id"]: set(r.get("destinations", [])) for r in features}
    counts = {"true_positive": 0, "false_positive": 0, "false_negative": 0, "true_negative": 0}
    for (identity, country), review in reviews.items():
        if identity not in eligible or review["decision"] == "unsure":
            continue
        auto, gold = country in predicted.get(identity, set()), review["decision"] == "yes"
        counts[("true_" if auto == gold else "false_")+("positive" if auto else "negative")] += 1
    n = sum(counts.values())
    tp, fp, fn = counts["true_positive"], counts["false_positive"], counts["false_negative"]
    return {"status": "human_labels_pending" if not n else "evaluated_on_supplied_human_pairs",
        "reviewed_pairs": len(reviews), "evaluated_pairs": n, "counts": counts,
        "accuracy": (tp+counts["true_negative"])/n if n else None,
        "precision": tp/(tp+fp) if tp+fp else None, "recall": tp/(tp+fn) if tp+fn else None,
        "note": "Evaluates automatic predictions BEFORE human overrides on supplied article-country pairs only. "
                "A convenience review is not an independent held-out benchmark or full-corpus recall estimate."}


def refresh_country_validation(directory, rows, features):
    directory = Path(directory)
    path = directory/"destination_reviews.csv"
    if not path.exists():
        buffer = io.StringIO(newline="")
        csv.DictWriter(buffer, fieldnames=FIELDS).writeheader()
        path.write_text(buffer.getvalue(), encoding="utf8", newline="")
    report = evaluate_countries(rows, features, read_country_reviews(directory, rows))
    (directory/"destination_validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf8")
    return report


def save_country_review(directory, rows, features, review):
    current = read_country_reviews(directory, rows)
    current[(review["record_id"], review["country"])] = review
    validate_reviews(current, rows)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(current[key] for key in sorted(current))
    (Path(directory)/"destination_reviews.csv").write_text(buffer.getvalue(), encoding="utf8", newline="")
    return refresh_country_validation(directory, rows, features)
