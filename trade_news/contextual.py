"""Pinned PySentimiento/RoBERTuito adaptation for real export-news text.

The pretrained model and preprocessing are upstream work. Full-body chunking
and monthly probability aggregation are explicit project adaptations. This is
not the BE1340 word-count method or a replication of another study's accuracy.
"""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path

from .articles import read_jsonl

MODEL_ID = "pysentimiento/robertuito-sentiment-analysis"
REVISION = "a2cc0f67ebd705c55191e25a05ba23d885fcc09b"
UPSTREAM = "60822acfd805ad5d95437c695daa33c18dbda060"
METHOD = "robertuito_full_body_nonoverlap128_token_weighted_v1"
LABELS = ("NEG", "NEU", "POS")
MODEL_FILES = ("config.json", "model.safetensors", "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json")


def checksum(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf8")
    temporary.replace(path)


def chunk_ids(ids, capacity=126):
    if capacity < 1:
        raise ValueError("Chunk capacity must be positive")
    return [ids[left:left+capacity] for left in range(0, len(ids), capacity)]


def combine(probabilities, weights):
    if not probabilities or len(probabilities) != len(weights) or any(w <= 0 for w in weights):
        raise ValueError("Supply positive token counts for each predicted chunk")
    for probability in probabilities:
        if set(probability) != set(LABELS) or any(not math.isfinite(v) or not 0 <= v <= 1 for v in probability.values()):
            raise ValueError("Invalid model probabilities")
        if not math.isclose(sum(probability.values()), 1, abs_tol=1e-5):
            raise ValueError("Probabilities must sum to one")
    total = sum(weights)
    pooled = {label: sum(p[label]*w for p, w in zip(probabilities, weights))/total for label in LABELS}
    return {"probabilities": pooled, "label": max(LABELS, key=pooled.get), "score": pooled["POS"]-pooled["NEG"],
            "max_probability": max(pooled.values()), "chunks": len(weights), "tokens": total}


class LocalModel:
    def __init__(self, directory, threads=4):
        os.environ["HF_HOME"] = str(Path(directory).resolve().parent/".huggingface")
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from .pysentimiento_preprocessing import preprocess_tweet
        torch.set_num_threads(threads)
        self.torch = torch
        self.preprocess = preprocess_tweet
        self.tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(directory, local_files_only=True,
                                                                       use_safetensors=True, trust_remote_code=False).eval()
        self.labels = {int(k): v for k, v in self.model.config.id2label.items()}
        if set(self.labels.values()) != set(LABELS):
            raise ValueError("Model labels differ from the pinned three-class sentiment model")
        self.capacity = 128-self.tokenizer.num_special_tokens_to_add(pair=False)

    def predict(self, text, batch_size=16):
        prepared = self.preprocess(text, lang="es")
        ids = self.tokenizer.encode(prepared, add_special_tokens=False, truncation=False, verbose=False)
        chunks = chunk_ids(ids, self.capacity)
        if not chunks:
            raise ValueError("No tokens remain after upstream preprocessing")
        probabilities = []
        for start in range(0, len(chunks), batch_size):
            batch = [self.tokenizer.prepare_for_model(chunk, add_special_tokens=True, truncation=False,
                     return_attention_mask=True) for chunk in chunks[start:start+batch_size]]
            inputs = self.tokenizer.pad(batch, padding=True, return_tensors="pt")
            if inputs["input_ids"].shape[1] > 128:
                raise ValueError("A model input exceeds the upstream 128-token limit")
            with self.torch.inference_mode():
                logits = self.model(**inputs).logits
                values = self.torch.softmax(logits, dim=-1).cpu().tolist()
            probabilities.extend({self.labels[i]: float(value) for i, value in enumerate(row)} for row in values)
        result = combine(probabilities, [len(chunk) for chunk in chunks])
        if result["tokens"] != len(ids):
            raise ValueError("Some source tokens were lost during chunking")
        return result


def aggregate_scores(scores, rows, months, dictionary_matched=False):
    """Equal-article means: compensated summation and 12-decimal portable output."""
    lookup = {r["record_id"]: r for r in rows if r["eligible_for_index"] and
              (not dictionary_matched or r["positive_count"]+r["negative_count"] > 0)}
    result = []
    for month in months:
        subset = [score for score in scores if score["record_id"] in lookup and lookup[score["record_id"]]["month"] == month]
        values = [s["body"]["score"] for s in subset]
        result.append({"month": month, "articles": len(subset),
            "publishers": len({lookup[s["record_id"]].get("publisher_group", lookup[s["record_id"]]["publisher"]) for s in subset}),
            "mean_probability_balance": round(math.fsum(values)/len(values), 12) if values else None,
            "labels": {label: sum(s["body"]["label"] == label for s in subset) for label in LABELS},
            "status": "model_predictions_not_human_validated" if values else "no_scored_articles"})
    return result


def verify_scores(directory, scores, manifest):
    directory = Path(directory)
    rows = read_jsonl(directory/"headlines.jsonl")
    if manifest.get("method") != METHOD or manifest.get("model_revision") != REVISION or manifest.get("model_id") != MODEL_ID:
        raise ValueError("Unexpected contextual method or model version")
    reference = json.loads((Path(__file__).resolve().parents[1]/"reference/contextual_model.json").read_text("utf8"))
    if manifest.get("model_files_sha256") != reference["model_files_sha256"]:
        raise ValueError("Saved predictions use different model weights or tokenizer files")
    if manifest.get("preprocessing_sha256") != checksum(Path(__file__).with_name("pysentimiento_preprocessing.py")):
        raise ValueError("Saved predictions use different upstream preprocessing")
    if checksum(directory/"headlines.jsonl") != manifest["source_features_sha256"]:
        raise ValueError("Contextual predictions refer to a different corpus snapshot")
    eligible = {r["record_id"]: r for r in rows if r["eligible_for_index"]}
    identities = [s["record_id"] for s in scores]
    if len(set(identities)) != len(identities) or set(identities)-set(eligible):
        raise ValueError("Duplicate or out-of-corpus contextual predictions")
    if manifest.get("status") == "complete":
        if set(identities) != set(eligible) or manifest.get("scored_articles") != len(scores):
            raise ValueError("Completed contextual run is missing eligible articles")
        if checksum(directory/"contextual_scores.jsonl") != manifest.get("scores_sha256"):
            raise ValueError("Saved contextual predictions differ from their manifest hash")
    for score in scores:
        row = eligible[score["record_id"]]
        if score["body_sha256"] != row["text_sha256"] or score["title_sha256"] != hashlib.sha256((row.get("publisher_title") or row["title"]).encode()).hexdigest():
            raise ValueError("The predicted source body or title changed")
        for unit in ("body", "headline"):
            value = score[unit]
            repeated = combine([value["probabilities"]], [value["tokens"]])
            if value["label"] != repeated["label"] or not math.isclose(value["score"], repeated["score"], abs_tol=1e-9):
                raise ValueError("A score or class disagrees with its saved probabilities")
    return rows


def rebuild(directory):
    directory = Path(directory)
    scores = read_jsonl(directory/"contextual_scores.jsonl")
    manifest = json.loads((directory/"contextual_manifest.json").read_text("utf8"))
    rows = verify_scores(directory, scores, manifest)
    months = [r["month"] for r in json.loads((directory/"collection_log.json").read_text("utf8"))["requests"]]
    output = {"all_eligible": aggregate_scores(scores, rows, months),
              "dictionary_matched": aggregate_scores(scores, rows, months, dictionary_matched=True)}
    save_json(directory/"contextual_indices.json", output)
    return output


def run(directory, model_directory):
    directory, model_directory = Path(directory), Path(model_directory)
    rows = read_jsonl(directory/"headlines.jsonl")
    eligible = [r for r in rows if r["eligible_for_index"]]
    config = {"method": METHOD, "model_id": MODEL_ID, "model_revision": REVISION,
        "upstream_source_commit": UPSTREAM, "source_features_sha256": checksum(directory/"headlines.jsonl"),
        "preprocessing_sha256": checksum(Path(__file__).with_name("pysentimiento_preprocessing.py")),
        "model_files_sha256": {name: checksum(model_directory/name) for name in MODEL_FILES},
        "runtime": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "safetensors", "emoji")},
        "interpretation": "Local pretrained model outputs; no human accuracy or predictive-value claim. Not BE1340 word counts.",
        "text_handling": "Upstream Spanish preprocessing; nonoverlapping content-token chunks fitting 128 tokens including specials; token-weighted chunk probabilities; no silent truncation.",
        "aggregation": "Monthly equal-article mean of P(POS)-P(NEG); no full-sample normalization or base-50 rescaling.",
        "model_origin": "Spanish TASS tweets; economic-news and Colombian-export domain transfer is unvalidated.",
        "license": "Scientific/non-commercial research; upstream model/data restrictions apply; model weights not redistributed."}
    manifest_path = directory/"contextual_manifest.json"
    output_path = directory/"contextual_scores.jsonl"
    previous = {}
    if output_path.exists() and not manifest_path.exists():
        raise ValueError("Predictions without a provenance manifest cannot be reused")
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text("utf8"))
        if any(previous.get(k) != value for k, value in config.items()):
            raise ValueError("Existing contextual run has a different source, model or configuration; preserve it before a new run")
    manifest = {**config, "started_at": previous.get("started_at", datetime.now(timezone.utc).isoformat()), "status": "running", "eligible_articles": len(eligible)}
    scores = read_jsonl(output_path) if output_path.exists() else []
    verify_scores(directory, scores, manifest)
    seen = {s["record_id"] for s in scores}
    save_json(manifest_path, manifest)
    engine = LocalModel(model_directory)
    for row in eligible:
        if row["record_id"] in seen:
            continue
        path = directory/"raw/articles"/(row["record_id"]+".txt")
        text = path.read_text("utf8")
        if hashlib.sha256(text.encode()).hexdigest() != row["text_sha256"]:
            raise ValueError("Source archive differs from its saved hash")
        title = row.get("publisher_title") or row["title"]
        score = {"record_id": row["record_id"], "body_sha256": row["text_sha256"],
            "title_sha256": hashlib.sha256(title.encode()).hexdigest(),
            "body": engine.predict(text), "headline": engine.predict(title)}
        with output_path.open("a", encoding="utf8") as stream:
            stream.write(json.dumps(score, ensure_ascii=False, allow_nan=False)+"\n")
        scores.append(score)
        if len(scores) % 10 == 0:
            print(f"Predicted {len(scores)}/{len(eligible)} real articles, full bodies and headlines", flush=True)
    manifest.update(status="complete", completed_at=datetime.now(timezone.utc).isoformat(), scored_articles=len(scores),
                    scores_sha256=checksum(output_path), human_reference_labels=0)
    save_json(manifest_path, manifest)
    rebuild(directory)
    print(f"Completed local model inference for {len(scores)} real articles; no human labels generated.", flush=True)
    return manifest
