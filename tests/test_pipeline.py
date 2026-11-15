"""Synthetic unit fixtures test software behavior, never domain accuracy."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from trade_news.collect import month_windows, parse_feed
from trade_news.nlp import analyze, normalize, sentiment, tag, PARTNERS
from trade_news.pipeline import aggregate, build, prepare, read_jsonl
from trade_news.validation import validate


def fixture(identity="a", title="Colombia exportaciones crecen", publisher="Publisher A", score=1):
    return {"record_id": identity, "title": title, "url": "https://example.org/"+identity,
            "publisher": publisher, "published_at": "2026-05-04T12:00:00+00:00",
            "relevant": True, "month": "2026-05", "tone_score": score,
            "sentiment": "positive", "themes": ["trade_flows"], "sectors": [], "partners": []}


class CollectionTests(unittest.TestCase):
    def test_month_boundary_and_year_rollover(self):
        self.assertEqual(list(month_windows("2025-12-01", "2026-02-01")),
                         [("2025-12-01", "2026-01-01"), ("2026-01-01", "2026-02-01")])

    def test_invalid_window(self):
        for start, end in [("2026-05-02", "2026-06-01"), ("2026-06-01", "2026-05-01")]:
            with self.assertRaises(ValueError):
                list(month_windows(start, end))

    def test_feed_rejects_invalid_and_outside_dates(self):
        xml = b'''<rss><channel>
        <item><title>Colombia exportaciones - Outlet</title><link>https://example.org/1</link><pubDate>Tue, 05 May 2026 12:00:00 GMT</pubDate><source url="https://example.org">Outlet</source></item>
        <item><title>Out of range</title><link>https://example.org/2</link><pubDate>Mon, 01 Jun 2026 00:00:00 GMT</pubDate></item>
        <item><title>Invalid</title><link>javascript:bad</link><pubDate>bad</pubDate></item>
        </channel></rss>'''
        rows, diagnostic = parse_feed(xml, "https://example.org/rss", "2026-11-15T00:00:00Z", "2026-05-01", "2026-06-01")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Colombia exportaciones")
        self.assertEqual(diagnostic, {"provider_items": 3, "rejected_items": 2})


class NLPTests(unittest.TestCase):
    def test_html_accents_and_whitespace(self):
        self.assertEqual(normalize("<b>CAFÉ</b> &amp;  carbón"), "cafe carbon")

    def test_word_boundary(self):
        self.assertEqual(tag("Indias y mexicanismo", PARTNERS), {})

    def test_no_country_inferred_from_person(self):
        self.assertEqual(tag("Trump anuncia cambios", PARTNERS), {})

    def test_explicit_geographic_and_trade_terms(self):
        row = analyze("Exportaciones de café de Colombia a Estados Unidos crecen")
        self.assertTrue(row["relevant"])
        self.assertEqual(row["partners"], ["United States"])
        self.assertEqual(row["sectors"], ["agriculture"])
        self.assertEqual(row["tag_evidence"]["sectors"]["agriculture"], ["cafe"])

    def test_non_colombia_rejected(self):
        self.assertFalse(analyze("Exportaciones de café de Brasil crecen")["relevant"])

    def test_non_trade_rejected(self):
        self.assertFalse(analyze("Colombia gana un partido")["relevant"])

    def test_static_page_rejected(self):
        self.assertFalse(analyze("Colombia exportaciones - Observatorio de Complejidad")["relevant"])

    def test_negation_inverts_evidence(self):
        result = sentiment("Colombia no crece en exportaciones")
        self.assertEqual(result["tone_score"], -1)
        self.assertTrue(result["sentiment_evidence"][0]["negated"])

    def test_no_cue_is_abstention(self):
        self.assertEqual(sentiment("Colombia exportaciones de flores")["sentiment"], "unscored")
        self.assertIsNone(sentiment("Colombia exportaciones")["tone_score"])

    def test_balanced_cues_neutral(self):
        result = sentiment("Colombia crece pero enfrenta crisis")
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["tone_score"], 0)

    def test_known_semantic_limit_is_visible(self):
        # Literal tone is not economic favorability: a documented diagnostic, not a solved case.
        self.assertEqual(sentiment("Aumentan los aranceles para Colombia")["sentiment"], "positive")


class PipelineTests(unittest.TestCase):
    def test_exact_url_and_normalized_title_dedup(self):
        rows, audit = prepare([fixture(), fixture("b", "COLOMBIA exportaciones crecen!"), fixture("a", "Another title")])
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(audit["duplicates"]), 2)

    def test_invalid_metadata_audited(self):
        row = fixture()
        row["published_at"] = "2026-05-01"  # Missing timezone.
        rows, audit = prepare([row])
        self.assertEqual(rows, [])
        self.assertEqual(audit["rejected_metadata"], ["a"])

    def test_equal_publisher_weights(self):
        rows = [fixture(str(i)) for i in range(9)] + [fixture("other", publisher="Publisher B", score=-1)]
        overall = next(r for r in aggregate(rows) if r["dimension"] == "overall")
        self.assertEqual(overall["headline_tone_index"], 0)  # Article-weighted mean would be +80.

    def test_one_source_suppressed(self):
        result = aggregate([fixture(str(i)) for i in range(5)])[0]
        self.assertIsNone(result["headline_tone_index"])

    def test_missing_month_remains_null(self):
        result = aggregate([], ["2026-06"])[0]
        self.assertEqual(result["n_records"], 0)
        self.assertIsNone(result["headline_tone_index"])

    def test_unscored_excluded_from_score_not_counts(self):
        rows = [fixture("1"), fixture("2"), fixture("3", publisher="B", score=-1), fixture("4", publisher="C", score=None)]
        result = next(r for r in aggregate(rows) if r["dimension"] == "overall")
        self.assertEqual((result["n_records"], result["n_scored"], result["n_scored_publishers"]), (4, 3, 2))
        self.assertEqual(result["headline_tone_index"], 0)

    def test_build_preserves_human_work(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "headlines_raw.jsonl").write_text(json.dumps(fixture())+"\n", encoding="utf8")
            (base / "collection_log.json").write_text(json.dumps({"requests": [{"month": "2026-05", "status": 200}]}), encoding="utf8")
            (base / "annotations.csv").write_text("Human work must be preserved", encoding="utf8")
            build(base)
            self.assertEqual((base / "annotations.csv").read_text("utf8"), "Human work must be preserved")
            self.assertEqual(len(read_jsonl(base / "headlines.jsonl")), 1)


class ValidationTests(unittest.TestCase):
    def run_labels(self, annotations, rows=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"annotations.csv"
            fields = ["record_id", "sentiment_gold", "relevance_gold", "themes_gold", "sectors_gold", "partners_gold", "annotator", "annotation_origin"]
            with path.open("w", encoding="utf8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(annotations)
            return validate(rows or [fixture()], path)

    def test_pending_not_zero_accuracy(self):
        result = self.run_labels([{"record_id": "a"}])
        self.assertEqual(result["n_labeled"], 0)
        self.assertIsNone(result["accuracy"])

    def test_machine_labels_cannot_be_silently_gold(self):
        with self.assertRaises(ValueError):
            self.run_labels([{"record_id": "a", "sentiment_gold": "positive", "annotator": "model", "annotation_origin": "model"}])

    def test_known_confusion_counts_and_abstention(self):
        references = [{"record_id": str(i), "sentiment_gold": gold, "annotator": "Synthetic unit fixture", "annotation_origin": "human"}
                      for i, gold in enumerate(["positive", "negative", "neutral", "positive"])]
        rows = [fixture(str(i)) for i in range(4)]
        for row, prediction in zip(rows, ["positive", "negative", "neutral", "unscored"]):
            row["sentiment"] = prediction
        result = self.run_labels(references, rows)
        self.assertEqual(result["accuracy"], .75)
        self.assertAlmostEqual(result["macro_f1"], 8/9)
        self.assertEqual(result["unscored_rate"], .25)

    def test_multilabel_and_relevance(self):
        result = self.run_labels([{"record_id": "a", "relevance_gold": "yes", "themes_gold": "trade_flows|logistics", "sectors_gold": "-",
                                   "annotator": "Synthetic unit fixture", "annotation_origin": "human"}])
        self.assertEqual(result["tasks"]["relevance"]["accuracy"], 1)
        self.assertAlmostEqual(result["tasks"]["themes"]["micro_f1"], 2/3)
        self.assertEqual(result["tasks"]["sectors"]["exact_match"], 1)

    def test_duplicate_references_rejected(self):
        a = {"record_id": "a", "sentiment_gold": "positive", "annotator": "Fixture", "annotation_origin": "human"}
        with self.assertRaises(ValueError):
            self.run_labels([a, a])


if __name__ == "__main__":
    unittest.main()
