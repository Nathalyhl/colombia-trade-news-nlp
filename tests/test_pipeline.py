"""Synthetic software diagnostics, separate from real news and human validation."""
from pathlib import Path
import tempfile
import unittest

from trade_news.articles import publication_metadata, fetch_public_article, reference_fingerprint, write_jsonl
from trade_news.bank_method import aggregate, load_reference, process_text
from trade_news.classification import ACTIVITIES, propose
from trade_news.collect import month_windows, parse_feed
from trade_news.corpus import apply_reviews, build, evaluate_sentiment

TEXT = "El panorama colombiano ofrece oportunidades y recuperación junto con dificultades e incertidumbre comercial internacional."


def article(identity="one", **changes):
    row = dict(record_id=identity, title="Exportaciones colombianas de café", publisher="Synthetic test publisher",
        article_url="https://example.org/"+identity, publication_date="2026-01-05", month="2026-01",
        text_sha256=identity, fetch_status="article_extracted", scope_proposal="include", activity_proposal="Agriculture",
        reference_fingerprint=reference_fingerprint(), **process_text(TEXT))
    row.update(changes)
    return row


def human(identity="one", **changes):
    row = dict(record_id=identity, include="yes", activity="Agriculture", reviewer="Synthetic test reviewer",
               annotation_origin="human", sentiment_gold="", title="", url="", notes="")
    row.update(changes)
    return row


class MeasurementTests(unittest.TestCase):
    def test_complete_published_dictionary(self):
        lexicon, stops = load_reference()
        self.assertEqual(sum(p == "positive" for p in lexicon.values()), 188)
        self.assertEqual(sum(p == "negative" for p in lexicon.values()), 376)
        self.assertEqual(len(stops), 313)
        self.assertNotIn("duplican", lexicon)
        self.assertNotIn("triplicaron", lexicon)

    def test_actual_occurrences_and_uncertainty_formula(self):
        result = process_text(TEXT)
        self.assertEqual((result["positive_count"], result["negative_count"], result["uncertainty_count"]), (2, 2, 1))
        self.assertEqual(result["sentiment_score"], 0)
        self.assertAlmostEqual(result["uncertainty_per_1000"], 1000/result["processed_tokens"])

    def test_minimum_text_length(self):
        self.assertEqual(process_text("oportunidades")["processing_status"], "too_short")

    def test_sentence_threshold_after_stopwords(self):
        text = "oportunidades economía comercio mundial bienes. "*4
        self.assertEqual(process_text(text)["processed_tokens"], 0)
        result = process_text("oportunidades economía comercio mundial bienes Colombia. "*2)
        self.assertEqual(result["processed_tokens"], 12)

    def test_repetition_counts_and_case_normalization(self):
        result = process_text("OPORTUNIDADES oportunidades recuperación economía comercio colombiano mundial.")
        self.assertEqual(result["positive_count"], 3)

    def test_no_invented_inflection_or_negation_flip(self):
        result = process_text("No duplican ni triplicaron exportaciones colombianas bienes textiles mundiales.")
        self.assertIsNone(result["sentiment_score"])
        result = process_text("No oportunidades economía comercio mundial bienes colombianos textiles.")
        self.assertEqual(result["positive_count"], 1)

    def test_no_polar_match_is_missing_not_neutral(self):
        result = process_text("Colombia exportaciones bienes textiles mercados comercio internacional mensual.")
        self.assertEqual(result["sentiment_label"], "no_polar_matches")
        self.assertIsNone(result["sentiment_score"])
        self.assertEqual(result["uncertainty_per_1000"], 0)

    def test_balance_is_neutral_only_with_matches(self):
        result = process_text("oportunidades dificultades economía comercio internacional colombiano mensual.")
        self.assertEqual(result["sentiment_label"], "neutral")
        self.assertEqual(result["sentiment_score"], 0)

    def test_monthly_formula_pools_counts_not_article_scores(self):
        rows = apply_reviews([article(positive_count=9, negative_count=1), article("two", positive_count=0, negative_count=1)], {})
        index = aggregate(rows, ["2026-01"])[0]
        self.assertEqual(index["sentiment"], round(7/11, 6))
        self.assertEqual(index["articles"], 2)

    def test_missing_month_and_reviewed_subset(self):
        rows = apply_reviews([article()], {})
        result = aggregate(rows, ["2026-01", "2026-02"])
        missing = next(r for r in result if r["month"] == "2026-02")
        self.assertIsNone(missing["sentiment"])
        self.assertIsNone(missing["uncertainty_per_1000"])
        self.assertEqual(aggregate(rows, ["2026-01"], reviewed_only=True)[0]["articles"], 0)

    def test_activities_are_exact_reference_labels(self):
        self.assertEqual(len(ACTIVITIES), 18)
        self.assertIn("Other Activity", ACTIVITIES)
        result = propose("Exportaciones colombianas de café y petróleo", "Colombia exporta café y petróleo al mundo.")
        self.assertEqual(result["activity_proposal"], "Global Context")
        self.assertEqual(result["topic"], "exports")

    def test_services_and_inbound_need_distinct_treatment(self):
        self.assertEqual(propose("Colombia exporta servicios de software", "Colombia exporta servicios de software.")["scope_proposal"], "exclude")
        self.assertEqual(propose("Brasil exporta café a Colombia", "Exportaciones de café hacia Colombia.")["scope_proposal"], "review")

    def test_multitopic_roundup_is_not_an_export_article(self):
        self.assertEqual(propose("Colombia, exportaciones, Ucrania: las noticias del jueves", "Colombia exporta productos y café.")["scope_proposal"], "review")


class ProvenanceTests(unittest.TestCase):
    def test_no_headline_fallback(self):
        row = article(fetch_status="article_text_unavailable", text_source=None)
        self.assertFalse(apply_reviews([row], {})[0]["eligible_for_index"])

    def test_missing_publisher_dates_remain_auditable(self):
        missing = article("missing", publication_date=None, fetch_status="publication_date_unverified")
        rows = apply_reviews([article(), missing], {})
        self.assertEqual(len(rows), 2)
        self.assertFalse(next(r for r in rows if r["record_id"] == "missing")["eligible_for_index"])

    def test_human_decisions_require_provenance(self):
        with self.assertRaisesRegex(ValueError, "reviewer"):
            apply_reviews([article()], {"one": human(reviewer="")})
        with self.assertRaisesRegex(ValueError, "annotation_origin"):
            apply_reviews([article()], {"one": human(annotation_origin="model")})

    def test_human_include_requires_text_and_valid_activity(self):
        with self.assertRaises(ValueError):
            apply_reviews([article(fetch_status="fetch_failed")], {"one": human()})
        with self.assertRaises(ValueError):
            apply_reviews([article()], {"one": human(activity="invented")})

    def test_scope_review_does_not_require_retired_activity_ui(self):
        result = apply_reviews([article()], {"one": human(activity="")})[0]
        self.assertTrue(result["eligible_for_index"])
        self.assertEqual(result["activity"], "Agriculture")

    def test_review_or_rejection_excludes_article(self):
        for decision in ["no", "review"]:
            self.assertFalse(apply_reviews([article()], {"one": human(include=decision)})[0]["eligible_for_index"])

    def test_dedup_prioritizes_actual_human_inclusion(self):
        rows = apply_reviews([article(), article("two", text_sha256="one")], {"two": human("two")})
        lookup = {r["record_id"]: r for r in rows}
        self.assertTrue(lookup["two"]["eligible_for_index"])
        self.assertEqual(lookup["one"]["duplicate_of"], "two")

    def test_no_labels_no_accuracy(self):
        report = evaluate_sentiment([article()], {})
        self.assertEqual(report["n_labeled"], 0)
        self.assertIsNone(report["accuracy"])

    def test_evaluation_counts_abstentions_as_errors(self):
        rows = [article(sentiment_label="no_polar_matches")]
        report = evaluate_sentiment(rows, {"one": human(sentiment_gold="positive")})
        self.assertEqual(report["accuracy"], 0)
        self.assertEqual(report["confusion_matrix"]["positive"]["abstention"], 1)

    def test_publication_date_is_not_date_modified(self):
        html = b'<script type="application/ld+json">{"@type":"NewsArticle","dateModified":"2026-01-01"}</script>'
        self.assertIsNone(publication_metadata(html)["publication_date"])

    def test_explicit_publisher_date_and_paywall(self):
        html = b'<script type="application/ld+json">{"@graph":[{"@type":"NewsArticle","datePublished":"2026-03-02T10:00:00Z"}]}</script>'
        self.assertEqual(publication_metadata(html)["publication_date"], "2026-03-02")
        self.assertTrue(publication_metadata(b'<script type="application/ld+json">{"@type":"Article","isAccessibleForFree":false}</script>')["paywall"])

    def test_publisher_host_cannot_be_substituted(self):
        row = dict(record_id="test", title="Synthetic", publisher_url="https://example.org")
        result = fetch_public_article(row, "https://unrelated.example/article", Path("."), {}, "2026-01-01", "2026-11-01")
        self.assertEqual(result["fetch_status"], "publisher_domain_mismatch")

    def test_feed_out_of_period_rejected(self):
        xml = b'<rss><channel><item><title>Example</title><link>https://example.org</link><pubDate>Mon, 01 Dec 2025 12:00:00 GMT</pubDate></item></channel></rss>'
        self.assertEqual(parse_feed(xml, "https://example.org", "now", "2026-01-01", "2026-02-01")[1]["rejected_items"], 1)

    def test_month_boundaries(self):
        self.assertEqual(len(list(month_windows("2026-01-01", "2026-11-01"))), 10)
        with self.assertRaises(ValueError):
            list(month_windows("2026-01-02", "2026-11-01"))

    def test_changed_archive_hash_prevents_reanalysis(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory/"raw/articles").mkdir(parents=True)
            write_jsonl(directory/"article_manifest.jsonl", [article(text_sha256="wrong")])
            (directory/"raw/articles/one.txt").write_text(TEXT, encoding="utf8")
            with self.assertRaisesRegex(ValueError, "hash"):
                build(directory, verify_local_text=True)


if __name__ == "__main__":
    unittest.main()
