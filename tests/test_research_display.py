"""Synthetic diagnostics verify sparse-series display and conservative screening."""
import math
from pathlib import Path
import tempfile
import unittest
from trade_news.charts import index_chart
from trade_news.bank_method import trailing_quarterly_mean
from trade_news.classification import propose
from trade_news.review_sample import select_records, prepare


def series(values):
    return [{"month": f"2026-{i:02d}", "sentiment": value, "articles": int(value is not None), "publishers": 1,
             "positive_count": 1, "negative_count": 0, "processed_tokens": 10} for i, value in enumerate(values, 1)]


class ResearchDisplayTests(unittest.TestCase):
    def test_preparing_sample_preserves_existing_human_notes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"review_sample.csv"
            content = "record_id,notes\none,Existing human work\n"
            path.write_text(content, encoding="utf8")
            with self.assertRaisesRegex(ValueError, "review work"):
                prepare(folder)
            self.assertEqual(path.read_text("utf8"), content)

    def test_isolated_values_have_markers_without_invented_smoother(self):
        fig = index_chart(series([.2, None, -.4]), "sentiment", "Synthetic", focus_observed=True)
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.data[0].mode, "lines+markers")
        self.assertFalse(fig.data[0].connectgaps)
        self.assertEqual(tuple(fig.data[0].y), (.2, None, -.4))

    def test_zero_is_a_visible_observation_and_missing_is_not(self):
        fig = index_chart(series([0, None, 0]), "sentiment", "Synthetic")
        self.assertEqual(tuple(fig.data[0].y), (0, None, 0))
        self.assertFalse(fig.layout.yaxis.zeroline)

    def test_three_consecutive_values_enable_smoother(self):
        fig = index_chart(series([.2, .4, .6]), "sentiment", "Synthetic")
        self.assertEqual(len(fig.data), 2)
        self.assertAlmostEqual(fig.data[1].y[-1], .4)

    def test_nan_never_enables_a_three_month_mean(self):
        self.assertEqual(trailing_quarterly_mean(series([.2, math.nan, .4]), "sentiment"), [None]*3)

    def test_empty_selection_has_explicit_annotation(self):
        fig = index_chart(series([None, None]), "sentiment", "Synthetic")
        self.assertEqual(len(fig.data), 0)
        self.assertIn("No monthly index", fig.layout.annotations[0].text)

    def test_incidental_export_mention_does_not_include_import_or_investment_story(self):
        body = "Colombia exporta café y bienes. El resto del artículo trata otro asunto."
        for title in ["Importaciones caen en Colombia", "Inversión extranjera directa creció"]:
            self.assertEqual(propose(title, body)["scope_proposal"], "review")

    def test_report_role_and_event_role_are_separate_unvalidated_cues(self):
        self.assertEqual(propose("Informe de exportaciones colombianas", "Datos del DANE sobre bienes.")["document_role_proposal"], "statistical_reporting_candidate")
        self.assertEqual(propose("Colombia reactivará exportaciones de carbón", "Colombia exporta carbón.")["document_role_proposal"], "event_or_expectation_candidate")
        self.assertEqual(propose("Exportaciones de Colombia", "Colombia exporta café.")["document_role_proposal"], "unresolved")

    def test_review_selection_is_deterministic_across_input_order(self):
        rows = [{"record_id": str(i), "fetch_status": "article_extracted", "publication_date": f"202{int(i/4)}-01-01",
                 "positive_count": i%3, "negative_count": 0, "scope_proposal": "include", "publisher": "Synthetic"} for i in range(12)]
        first, second = select_records(rows, 7), select_records(list(reversed(rows)), 7)
        self.assertEqual([r["record_id"] for r in first], [r["record_id"] for r in second])
        self.assertEqual(len({r["record_id"] for r in first}), 7)
