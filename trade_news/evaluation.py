"""Locked, prediction-blind review sheets and honest reference-label evaluation."""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path

from .articles import read_jsonl

LABELS = ["positive", "negative", "neutral"]
FIELDS = ["record_id", "publication_date", "publisher", "title", "url", "body_sha256", "stratum", "sample_weight",
    "include_goods_exports", "document_role", "overall_tone", "export_event_direction", "reference_start", "reference_end",
    "comparison_basis", "event_date", "reviewer", "annotation_origin", "notes"]
ROLES = {"statistical_reporting", "event_or_expectation", "mixed", "other", "uncertain"}
DIRECTIONS = {"expansion", "contraction", "resumption", "restriction", "unchanged", "mixed", "uncertain", "not_applicable"}
BASES = {"year_on_year", "month_on_month", "cumulative_year_on_year", "other", "not_applicable", "uncertain"}


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(directory, size=200, primary_only=True, exclude_ids=()):
    directory = Path(directory)
    output_paths = [directory/("evaluation_"+reviewer+".csv") for reviewer in ("reviewer_a", "reviewer_b", "adjudicated")]
    if any(path.exists() for path in output_paths) or (directory/"evaluation_sample_manifest.json").exists():
        raise ValueError("A locked evaluation sample already exists; preserve reviewer work and sample provenance")
    rows = [r for r in read_jsonl(directory/"headlines.jsonl") if r.get("fetch_status") == "article_extracted"]
    if primary_only:
        from .coverage import in_primary_press_frame
        rows = [r for r in rows if in_primary_press_frame(r)]
    known_diagnostics = set(exclude_ids)
    if (directory/"review_sample.csv").exists():
        with (directory/"review_sample.csv").open(encoding="utf8", newline="") as stream:
            known_diagnostics.update(r["record_id"] for r in csv.DictReader(stream))
    # All retrieved export-URL-frame texts, including automatic exclusions: scope errors are observable.
    pool = [r for r in rows if r["record_id"] not in known_diagnostics and not r.get("duplicate_of")]
    strata = {}
    for row in pool:
        key = row["publication_date"][:4]+"|"+row["publisher_group"]
        strata.setdefault(key, []).append(row)
    if size < len(strata):
        raise ValueError("Sample size must cover every observed year/domain stratum")
    queues = {key: sorted(group, key=lambda r: hashlib.sha256(("export-news-evaluation-v1|"+r["record_id"]).encode()).hexdigest())
              for key, group in strata.items()}
    selected, counts = [], Counter()
    while len(selected) < min(size, len(pool)):
        for key in sorted(queues):
            if counts[key] < len(queues[key]) and len(selected) < size:
                selected.append((key, queues[key][counts[key]]))
                counts[key] += 1
    output = []
    for key, row in selected:
        output.append({**{field: "" for field in FIELDS}, "record_id": row["record_id"], "publication_date": row["publication_date"],
            "publisher": row["publisher"], "title": row.get("publisher_title") or row["title"], "url": row["article_url"],
            "body_sha256": row["text_sha256"], "stratum": key, "sample_weight": len(strata[key])/counts[key]})
    for path in output_paths:
        with path.open("w", encoding="utf8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(output)
    manifest = {"method": "year_domain_stratified_hash_selection_v1", "status": "locked_unlabeled",
        "primary_press_frame_only": primary_only,
        "source_features_sha256": checksum(directory/"headlines.jsonl"), "requested_size": size, "selected_records": len(output),
        "frame": "Retrieved deduplicated texts in the collected export-URL/discovery frame, excluding known diagnostic records; not all Colombian news.",
        "excludes_diagnostic_ids": sorted(known_diagnostics), "record_ids": [r["record_id"] for r in output],
        "strata": {key: {"frame_records": len(group), "selected_records": counts[key]} for key, group in sorted(strata.items())},
        "selection_used_predictions": False, "human_labels_generated": 0,
        "note": "Reviewer A/B work independently before inspecting predictions; adjudication is a separate human step. Inverse-stratum weights do not repair source-frame omissions or label nonresponse."}
    (directory/"evaluation_sample_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    return manifest


def load_judgments(path, manifest, rows):
    lookup = {r["record_id"]: r for r in rows}
    with Path(path).open(encoding="utf8", newline="") as stream:
        values = list(csv.DictReader(stream))
    ids = [r["record_id"] for r in values]
    if len(set(ids)) != len(ids) or set(ids) != set(manifest["record_ids"]):
        raise ValueError("Reference sheet differs from the locked evaluation sample")
    result = {}
    for row in values:
        source = lookup.get(row["record_id"])
        if not source or row["body_sha256"] != source.get("text_sha256"):
            raise ValueError("Reference sheet source body changed")
        if row["stratum"] != source["publication_date"][:4]+"|"+source["publisher_group"]:
            raise ValueError("Reference sheet sampling stratum changed")
        for field, allowed in [("include_goods_exports", {"yes", "no", "uncertain"}), ("overall_tone", set(LABELS)|{"uncertain"}),
                               ("document_role", ROLES), ("export_event_direction", DIRECTIONS), ("comparison_basis", BASES)]:
            if row.get(field) and row[field] not in allowed:
                raise ValueError("Invalid reference value for "+field)
        judged = any(row.get(field) for field in ["include_goods_exports", "overall_tone", "document_role", "export_event_direction", "comparison_basis"])
        if judged and (not row.get("reviewer", "").strip() or row.get("annotation_origin") != "human"):
            raise ValueError("Reference judgments require a named human reviewer and annotation_origin=human")
        expected_weight = manifest["strata"][row["stratum"]]["frame_records"]/manifest["strata"][row["stratum"]]["selected_records"]
        if not math.isclose(float(row["sample_weight"]), expected_weight):
            raise ValueError("Sampling weights differ from the locked design")
        result[row["record_id"]] = row
    return result


def classification_metrics(pairs):
    """Unweighted labeled-subset diagnostics; an abstention is not a neutral class."""
    if not pairs:
        return {"n_labeled": 0, "accuracy": None, "macro_f1": None, "prediction_coverage": None, "confusion": None}
    matrix = {gold: {pred: 0 for pred in LABELS+["abstention"]} for gold in LABELS}
    for gold, predicted in pairs:
        matrix[gold][predicted if predicted in LABELS else "abstention"] += 1
    n = len(pairs)
    per_class = {}
    for label in LABELS:
        tp = matrix[label][label]
        support = sum(matrix[label].values())
        predicted = sum(matrix[g][label] for g in LABELS)
        fp, fn = predicted-tp, support-tp
        per_class[label] = {"support": support, "precision": tp/predicted if predicted else None,
            "recall": tp/support if support else None, "f1": 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0}
    return {"n_labeled": n, "accuracy": sum(matrix[c][c] for c in LABELS)/n,
        "macro_f1": sum(r["f1"] for r in per_class.values())/3,
        "prediction_coverage": 1-sum(matrix[c]["abstention"] for c in LABELS)/n,
        "per_class": per_class, "confusion": matrix,
        "definition": "Unweighted diagnostics on human-included, tone-labeled sample records; fixed three-class macro F1, absent-class zero convention. Not whole-press population accuracy."}


def agreement(first, second):
    pairs = [(first[key]["overall_tone"], second[key]["overall_tone"]) for key in first.keys() & second.keys()
             if first[key].get("overall_tone") in LABELS and second[key].get("overall_tone") in LABELS]
    if not pairs:
        return {"n_common": 0, "agreement": None, "cohen_kappa": None}
    observed = sum(a == b for a, b in pairs)/len(pairs)
    expected = sum(sum(a == label for a, _ in pairs)*sum(b == label for _, b in pairs) for label in LABELS)/len(pairs)**2
    return {"n_common": len(pairs), "agreement": observed, "cohen_kappa": (observed-expected)/(1-expected) if expected < 1 else None}


def probability_metrics(pairs):
    if not pairs:
        return {"n": 0, "multiclass_brier": None, "ece_10_bins": None}
    totals, bins = [], [[] for _ in range(10)]
    key_map = {"positive": "POS", "negative": "NEG", "neutral": "NEU"}
    for gold, probabilities in pairs:
        totals.append(sum((probabilities[key_map[label]]-int(label == gold))**2 for label in LABELS))
        predicted = max(key_map, key=lambda label: probabilities[key_map[label]])
        confidence = probabilities[key_map[predicted]]
        bins[min(9, int(confidence*10))].append((confidence, int(predicted == gold)))
    ece = sum(abs(sum(c for c, _ in group)/len(group)-sum(a for _, a in group)/len(group))*len(group)/len(pairs)
              for group in bins if group)
    return {"n": len(pairs), "multiclass_brier": math.fsum(totals)/len(totals), "ece_10_bins": ece,
            "bin_counts": [len(group) for group in bins],
            "definition": "Brier sums three squared class errors (0–2); ECE uses ten equal-width maximum-probability bins. Small or incomplete samples give unstable calibration estimates."}


def evaluate(directory):
    directory = Path(directory)
    manifest = json.loads((directory/"evaluation_sample_manifest.json").read_text("utf8"))
    if checksum(directory/"headlines.jsonl") != manifest["source_features_sha256"]:
        raise ValueError("The evaluation frame changed after sample locking")
    rows = read_jsonl(directory/"headlines.jsonl")
    lookup = {r["record_id"]: r for r in rows}
    sheets = {key: load_judgments(directory/("evaluation_"+key+".csv"), manifest, rows)
              for key in ("reviewer_a", "reviewer_b", "adjudicated")}
    scores_path = directory/"contextual_scores.jsonl"
    scores = {}
    if scores_path.exists():
        from .contextual import verify_scores
        saved = read_jsonl(scores_path)
        verify_scores(directory, saved, json.loads((directory/"contextual_manifest.json").read_text("utf8")))
        scores = {s["record_id"]: s for s in saved}
    reference = {key: r for key, r in sheets["adjudicated"].items() if r.get("include_goods_exports") == "yes" and r.get("overall_tone") in LABELS}
    model_labels = {"POS": "positive", "NEG": "negative", "NEU": "neutral"}
    reports = {}
    for method in ["dictionary", "contextual"]:
        pairs = []
        for key, gold in reference.items():
            prediction = lookup[key].get("sentiment_label") if method == "dictionary" else model_labels[scores[key]["body"]["label"]] if key in scores else None
            pairs.append((gold["overall_tone"], prediction))
        reports[method] = classification_metrics(pairs)
    calibration = probability_metrics([(gold["overall_tone"], scores[key]["body"]["probabilities"]) for key, gold in reference.items() if key in scores])
    scope_pairs = [(r["include_goods_exports"] == "yes", lookup[key].get("scope_proposal") == "include")
                   for key, r in sheets["adjudicated"].items() if r.get("include_goods_exports") in {"yes", "no"}]
    tp = sum(gold and pred for gold, pred in scope_pairs)
    positive = sum(pred for _, pred in scope_pairs)
    relevant = sum(gold for gold, _ in scope_pairs)
    scope_report = {"n": len(scope_pairs), "accuracy": sum(gold == pred for gold, pred in scope_pairs)/len(scope_pairs) if scope_pairs else None,
                    "precision": tp/positive if positive else None, "recall": tp/relevant if relevant else None,
                    "note": "Automatic scope proposal before human overrides, within the collected discovery frame only."}
    return {"status": "human_reference_pending" if not reference else "diagnostics_on_supplied_human_reference",
        "locked_sample_records": manifest["selected_records"], "adjudicated_tone_labels": len(reference),
        "reviewer_agreement": agreement(sheets["reviewer_a"], sheets["reviewer_b"]), "models": reports,
        "contextual_calibration": calibration, "scope_screening": scope_report,
        "note": "No labels are generated. Partial annotation, source-frame omissions and changed domains limit inference; independent evaluation and economic value are separate questions."}
