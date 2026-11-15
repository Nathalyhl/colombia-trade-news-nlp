"""Evaluate human-supplied references; leave unannotated tasks explicitly pending."""
import csv
from pathlib import Path
from .nlp import THEMES, SECTORS, PARTNERS


def classification_metrics(pairs, classes):
    predictions = list(classes) + (["unscored"] if "unscored" not in classes else [])
    matrix = {g: {p: 0 for p in predictions} for g in classes}
    for gold, predicted in pairs:
        matrix[gold][predicted] += 1
    f1 = []
    for label in classes:
        tp = matrix[label][label]
        fp = sum(matrix[g][label] for g in classes if g != label)
        fn = sum(v for p, v in matrix[label].items() if p != label)
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    return {"status": "evaluated_on_supplied_labels", "n_labeled": len(pairs),
            "accuracy": sum(g == p for g, p in pairs)/len(pairs),
            "macro_f1": sum(f1)/len(classes), "confusion_matrix": matrix,
            "unscored_rate": sum(p == "unscored" for _, p in pairs)/len(pairs)}


def validate(rows, annotations):
    lookup = {r["record_id"]: r for r in rows}
    tasks = {k: [] for k in ["sentiment", "relevance", "themes", "sectors", "partners"]}
    seen = set()
    with Path(annotations).open(encoding="utf8", newline="") as stream:
        for a in csv.DictReader(stream):
            if not any(a.get(k + "_gold", "").strip() for k in tasks):
                continue
            identity = a["record_id"]
            if identity not in lookup or identity in seen:
                raise ValueError("Unknown or duplicate annotation ID")
            seen.add(identity)
            if a.get("annotation_origin") != "human" or not a.get("annotator", "").strip():
                raise ValueError("Reference labels require a named annotator and annotation_origin=human")
            row = lookup[identity]
            for task, classes in [("sentiment", ["negative", "neutral", "positive"]), ("relevance", ["yes", "no"])]:
                gold = a.get(task + "_gold", "").strip()
                if gold:
                    if gold not in classes:
                        raise ValueError(f"Invalid {task} reference label: {gold}")
                    predicted = row["sentiment"] if task == "sentiment" else "yes" if row["relevant"] else "no"
                    tasks[task].append((gold, predicted))
            for task, vocab in [("themes", THEMES), ("sectors", SECTORS), ("partners", PARTNERS)]:
                value = a.get(task + "_gold", "").strip()
                if value:
                    gold = set() if value == "-" else {s.strip() for s in value.split("|")}
                    if not gold <= vocab.keys():
                        raise ValueError(f"Unknown {task} reference labels: {gold - vocab.keys()}")
                    tasks[task].append((gold, set(row[task])))
    pending = {"status": "human_labels_pending", "n_labeled": 0, "accuracy": None, "macro_f1": None}
    reports = {}
    for task, classes in [("sentiment", ["negative", "neutral", "positive"]), ("relevance", ["yes", "no"])]:
        reports[task] = classification_metrics(tasks[task], classes) if tasks[task] else dict(pending)
    for task in ["themes", "sectors", "partners"]:
        pairs = tasks[task]
        if not pairs:
            reports[task] = dict(pending)
            continue
        tp = sum(len(g & p) for g, p in pairs)
        fp = sum(len(p - g) for g, p in pairs)
        fn = sum(len(g - p) for g, p in pairs)
        reports[task] = {"status": "evaluated_on_supplied_labels", "n_labeled": len(pairs),
                         "exact_match": sum(g == p for g, p in pairs)/len(pairs),
                         "micro_f1": 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                         "tp": tp, "fp": fp, "fn": fn}
    return {**reports["sentiment"], "tasks": reports,
            "note": "Reference provenance is annotator-declared. Software tests do not establish domain accuracy; developer-reviewed samples do not establish held-out generalization."}
