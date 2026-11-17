"""Synthetic mechanics checks, never empirical reference labels or news."""
import json
from pathlib import Path
import tempfile
import unittest

from trade_news.articles import write_jsonl, extract_body
from trade_news.coverage import longest_window
from trade_news.evaluation import classification_metrics, agreement, prepare, load_judgments, probability_metrics
from trade_news.classification import propose
from trade_news.history import read_sitemap, archive_month


class HistoryResearchTests(unittest.TestCase):
    def test_publisher_body_preserves_negation_and_excludes_personalization_and_link_promo(self):
        payload = '''<html><head><meta charset="utf-8"></head><body><p>MI SELECCIÓN DE NOTICIAS</p><div class="html-content">
        <p>Las exportaciones colombianas no crecieron durante abril, según las cifras publicadas por la autoridad estadística nacional.</p>
        <p>Las empresas enfrentan restricciones de demanda y costos elevados, aunque algunos compradores mantuvieron sus pedidos de productos agrícolas.</p>
        <p>Lea también: <a href="https://example.org">Otro artículo recomendado sobre un asunto diferente</a></p>
        </div><p>Noticias personalizadas, de acuerdo a sus temas de interés</p></body></html>'''.encode()
        body, trace = extract_body(payload, "https://www.larepublica.co/economia/synthetic-unit-test")
        self.assertIn("no crecieron", body)
        self.assertNotIn("SELECCIÓN", body)
        self.assertNotIn("Otro artículo", body)
        self.assertEqual(trace["removed_promo_paragraphs"], 1)

    def test_foreign_origin_and_current_tense_report_are_separate_review_proposals(self):
        foreign = propose("Exportaciones de China crecen", "China vende bienes a Colombia y otros países.")
        self.assertEqual(foreign["scope_proposal"], "review")
        report = propose("Exportaciones colombianas caen en enero", "Las cifras del DANE muestran ventas de bienes al exterior.")
        self.assertEqual(report["document_role_proposal"], "statistical_reporting_candidate")

    def test_calibration_requires_references_and_uses_three_class_probabilities(self):
        self.assertIsNone(probability_metrics([])["multiclass_brier"])
        report = probability_metrics([("positive", {"POS": .8, "NEG": .1, "NEU": .1})])
        self.assertAlmostEqual(report["multiclass_brier"], .06)
        self.assertAlmostEqual(report["ece_10_bins"], .2)

    def test_sitemap_image_and_lastmod_do_not_become_article_url_and_publication(self):
        payload = b'''<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
        <url><loc>https://example.org/exportaciones</loc><lastmod>2026-01-01</lastmod>
        <image:image><image:loc>https://example.org/image.jpg</image:loc></image:image></url></urlset>'''
        index, entries = read_sitemap(payload)
        self.assertFalse(index)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["url"], "https://example.org/exportaciones")
        self.assertIsNone(entries[0]["publication_hint"])

    def test_archive_filename_is_only_a_discovery_month(self):
        self.assertEqual(archive_month("https://example.org/articles_April_2020.xml.gz"), "2020-04")
        self.assertIsNone(archive_month("https://example.org/recent_articles.xml.gz"))

    def test_period_selection_cannot_bridge_missing_calendar_month(self):
        rows = [{"month": month, "press_articles": 5, "press_domains": 2} for month in ["2020-03", "2020-05"]]
        with self.assertRaisesRegex(ValueError, "consecutive"):
            longest_window(rows)
        rows.insert(1, {"month": "2020-04", "press_articles": 0, "press_domains": 0})
        window = longest_window(rows)
        self.assertEqual(window["start"], "2020-03")
        self.assertEqual(window["months"], 1)

    def test_no_human_labels_never_produce_accuracy(self):
        self.assertIsNone(classification_metrics([])["accuracy"])
        self.assertIsNone(agreement({}, {})["cohen_kappa"])

    def test_dictionary_abstention_counts_as_missing_prediction_not_neutral(self):
        report = classification_metrics([("neutral", None), ("positive", "positive")])
        self.assertEqual(report["accuracy"], .5)
        self.assertEqual(report["prediction_coverage"], .5)
        self.assertEqual(report["confusion"]["neutral"]["abstention"], 1)

    def test_locked_sample_is_blind_preserved_and_requires_real_human_origin(self):
        import csv
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            rows = [{"record_id": str(i), "fetch_status": "article_extracted", "publication_date": "2020-04-02",
                     "publisher_group": "example.org", "publisher": "Synthetic test publisher", "title": "Synthetic unit-test text",
                     "article_url": "https://example.org/"+str(i), "text_sha256": "testhash", "eligible_for_index": False} for i in range(4)]
            write_jsonl(path/"headlines.jsonl", rows)
            manifest = prepare(path, 2, primary_only=False)
            self.assertFalse(manifest["selection_used_predictions"])
            self.assertEqual(json.loads((path/"evaluation_sample_manifest.json").read_text("utf8"))["human_labels_generated"], 0)
            with self.assertRaisesRegex(ValueError, "locked"):
                prepare(path, 2, primary_only=False)
            sheet = path/"evaluation_reviewer_a.csv"
            with sheet.open(encoding="utf8", newline="") as stream:
                reader = csv.DictReader(stream)
                fields, values = reader.fieldnames, list(reader)
            self.assertTrue(all(not row["overall_tone"] for row in values))
            values[0]["overall_tone"] = "positive"
            with sheet.open("w", encoding="utf8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader(); writer.writerows(values)
            with self.assertRaisesRegex(ValueError, "human reviewer"):
                load_judgments(sheet, manifest, rows)
