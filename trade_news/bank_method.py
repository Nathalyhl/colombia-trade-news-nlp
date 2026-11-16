"""Operational implementation of BE1340 Diagram 1, Eq. 1/2 and Annex 3.

The paper does not supply its exact stopword file or tokenizer code. This
implementation freezes those choices explicitly; it does not invent a lexicon.
"""
from collections import Counter
import csv
import hashlib
import html
import json
from pathlib import Path
import re
import unicodedata

REFERENCE = Path(__file__).resolve().parents[1] / "reference"
METHOD = "be1340_annex3_surface_counts_v2"
UNCERTAINTY = {"incertidumbre", "incertidumbres", "incierto", "inciertos", "incierta", "inciertas"}


def normalize(text):
    return unicodedata.normalize("NFC", text).casefold()


def load_reference():
    manifest = json.loads((REFERENCE / "manifest.json").read_text("utf8"))
    content = (REFERENCE / "moreno_gonzalez_2020.csv").read_bytes()
    if hashlib.sha256(content).hexdigest() != manifest["lexicon_sha256"]:
        raise ValueError("The published dictionary file has changed")
    with (REFERENCE / "moreno_gonzalez_2020.csv").open(encoding="utf8", newline="") as stream:
        entries = list(csv.DictReader(stream))
    lexicon = {normalize(row["word"]): row["polarity"] for row in entries}
    if len(lexicon) != 564 or Counter(lexicon.values()) != {"positive": 188, "negative": 376}:
        raise ValueError("Reference dictionary counts do not match Annex 3")
    stopword_bytes = (REFERENCE / "spanish_stopwords.txt").read_bytes()
    if hashlib.sha256(stopword_bytes).hexdigest() != manifest["stopwords_sha256"]:
        raise ValueError("The frozen stopword file has changed")
    stopwords = {normalize(word.strip()) for word in stopword_bytes.decode("utf8").splitlines() if word.strip()}
    return lexicon, stopwords


def clean_text(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return unicodedata.normalize("NFC", "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines())).strip()


def process_text(text):
    lexicon, stopwords = load_reference()
    text = clean_text(text)
    result = {"method": METHOD, "text_characters": len(text), "processed_tokens": 0,
              "retained_sentences": 0, "discarded_short_sentences": 0,
              "candidate_sentences": 0, "tokens_before_stopwords": 0, "tokens_after_stopwords": 0,
              "positive_count": 0, "negative_count": 0, "uncertainty_count": 0,
              "sentiment_score": None, "uncertainty_per_1000": None,
              "sentiment_label": "not_estimated", "matched_terms": [], "processing_status": "too_short"}
    # Diagram 1: discard text with fewer than 50 characters.
    if len(text) < 50:
        return result
    tokens = []
    # Operational boundaries: Diagram 1 lists punctuation, paragraphs, numbering
    # and bullets. Number/letter/roman list markers only apply at line starts.
    prepared = re.sub(r"(?m)^\s*(?:\d+|[a-z]|[ivxlcdm]+)[.)]\s+", "", normalize(text))
    sentences = re.split(r"(?<=[.!?;])\s+|\n+|[•▪●]", prepared)
    for sentence in sentences:
        words = re.findall(r"[^\W\d_]+", sentence, flags=re.UNICODE)
        if not words:
            continue
        result["candidate_sentences"] += 1
        result["tokens_before_stopwords"] += len(words)
        words = [word for word in words if word not in stopwords]
        result["tokens_after_stopwords"] += len(words)
        # Diagram 1 places stopword removal before the >5-word sentence condition.
        if len(words) <= 5:
            result["discarded_short_sentences"] += bool(words)
            continue
        result["retained_sentences"] += 1
        tokens.extend(words)
    frequencies = Counter(tokens)
    positive = sum(n for word, n in frequencies.items() if lexicon.get(word) == "positive")
    negative = sum(n for word, n in frequencies.items() if lexicon.get(word) == "negative")
    uncertain = sum(frequencies[word] for word in UNCERTAINTY)
    result.update({"processed_tokens": len(tokens), "positive_count": positive, "negative_count": negative,
                   "uncertainty_count": uncertain,
                   "matched_terms": [{"word": word, "polarity": lexicon[word], "count": n}
                                     for word, n in sorted(frequencies.items()) if word in lexicon],
                   "processing_status": "processed" if tokens else "no_eligible_sentences"})
    if tokens:
        result["uncertainty_per_1000"] = 1000 * uncertain / len(tokens)
    if positive + negative:
        score = (positive - negative) / (positive + negative)
        result.update(sentiment_score=score, sentiment_label="positive" if score > 0 else "negative" if score < 0 else "neutral")
    elif tokens:
        result["sentiment_label"] = "no_polar_matches"
    return result


def aggregate(records, months, reviewed_only=False):
    """Pool article word counts, rather than average article sentiment scores."""
    output = []
    eligible = [r for r in records if r.get("eligible_for_index") and
                (not reviewed_only or r.get("review_status") == "human_reviewed")]
    for month in months:
        for activity in ["All exports"] + sorted({r["activity"] for r in eligible if r["month"] == month}):
            rows = [r for r in eligible if r["month"] == month and (activity == "All exports" or r["activity"] == activity)]
            positive = sum(r["positive_count"] for r in rows)
            negative = sum(r["negative_count"] for r in rows)
            tokens = sum(r["processed_tokens"] for r in rows)
            uncertain = sum(r["uncertainty_count"] for r in rows)
            output.append({"month": month, "activity": activity, "articles": len(rows),
                           "publishers": len({r["publisher"] for r in rows}),
                           "articles_with_polar_matches": sum(r["positive_count"]+r["negative_count"] > 0 for r in rows),
                           "processed_tokens": tokens, "positive_count": positive, "negative_count": negative,
                           "uncertainty_count": uncertain,
                           "sentiment": round((positive-negative)/(positive+negative), 6) if positive+negative else None,
                           "uncertainty_per_1000": round(1000*uncertain/tokens, 6) if tokens else None,
                           "status": "no_articles" if not rows else "no_polar_matches" if not positive+negative else
                                     "reviewed_sample" if reviewed_only else "provisional_scope_review_pending"})
    return output


def trailing_quarterly_mean(series, column):
    """Three consecutive calendar months, no filling or future observations.

    Figure 3 says quarterly moving average without specifying alignment. The
    trailing alignment here is an explicit project convention, not Bank code.
    """
    from datetime import date
    output = []
    for i, row in enumerate(series):
        window = series[max(0, i-2):i+1]
        dates = [date.fromisoformat(r["month"]+"-01") for r in window]
        ordinals = [d.year*12+d.month for d in dates]
        consecutive = len(window) == 3 and ordinals == list(range(ordinals[0], ordinals[0]+3))
        values = [r.get(column) for r in window]
        output.append(sum(values)/3 if consecutive and all(v is not None for v in values) else None)
    return output
