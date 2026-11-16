"""Synthetic mechanics tests; no fabricated reference labels or model accuracy."""
import unittest
from trade_news.contextual import chunk_ids, combine, aggregate_scores


class ContextualTests(unittest.TestCase):
    def test_chunks_preserve_all_tokens_without_overlap(self):
        ids = list(range(513))
        chunks = chunk_ids(ids)
        self.assertEqual([token for chunk in chunks for token in chunk], ids)
        self.assertTrue(all(len(chunk) <= 126 for chunk in chunks))
        self.assertEqual(len(chunks), 5)

    def test_token_weighted_probabilities_and_argmax(self):
        value = combine([{"POS": .8, "NEU": .1, "NEG": .1}, {"POS": .1, "NEU": .2, "NEG": .7}], [1, 3])
        self.assertAlmostEqual(value["score"], -.275)
        self.assertEqual(value["label"], "NEG")
        self.assertEqual(value["tokens"], 4)

    def test_neutral_class_can_have_nonzero_probability_balance(self):
        value = combine([{"POS": .3, "NEU": .5, "NEG": .2}], [12])
        self.assertEqual(value["label"], "NEU")
        self.assertAlmostEqual(value["score"], .1)

    def test_invalid_or_incomplete_probabilities_are_rejected(self):
        for probability in [{"POS": 1}, {"POS": .9, "NEG": .9, "NEU": 0}, {"POS": float("nan"), "NEG": 0, "NEU": 1}]:
            with self.assertRaises(ValueError):
                combine([probability], [1])

    def test_monthly_mean_uses_articles_and_preserves_missing_months(self):
        rows = [{"record_id": str(i), "eligible_for_index": True, "month": "2026-01", "publisher": "Synthetic",
                 "positive_count": i, "negative_count": 0} for i in range(2)]
        scores = [{"record_id": str(i), "body": {"score": score, "label": label}} for i, score, label in [(0, .8, "POS"), (1, -.2, "NEG")]]
        all_rows = aggregate_scores(scores, rows, ["2026-01", "2026-02"])
        self.assertEqual(all_rows[0]["mean_probability_balance"], .3)
        self.assertIsNone(all_rows[1]["mean_probability_balance"])
        subset = aggregate_scores(scores, rows, ["2026-01"], dictionary_matched=True)
        self.assertAlmostEqual(subset[0]["mean_probability_balance"], -.2)
        self.assertEqual(subset[0]["articles"], 1)
