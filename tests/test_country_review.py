"""Synthetic human-review fixtures never enter the actual news review files."""
from pathlib import Path
import tempfile
import unittest

from trade_news.country_review import (assignments, country_coverage, evaluate_countries,
    read_country_reviews, save_country_review, title_hash)
from trade_news.destinations import identify


def article(**changes):
    row = {"record_id": "test", "title": "Colombia exporta café a Estados Unidos", "eligible_for_index": True}
    row.update(changes)
    return row


def judgment(country="United States", decision="yes", **changes):
    review = {"record_id": "test", "country": country, "decision": decision, "reviewer": "Synthetic test reviewer",
              "annotation_origin": "human", "notes": "Synthetic review evidence", "title_sha256": title_hash(article())}
    review.update(changes)
    return review


class CountryReviewTests(unittest.TestCase):
    def setUp(self):
        self.rows = [article()]
        self.features = [{"record_id": "test", **identify(self.rows[0]["title"])}]

    def test_no_reference_labels_no_accuracy(self):
        report = evaluate_countries(self.rows, self.features, {})
        self.assertEqual(report["evaluated_pairs"], 0)
        self.assertIsNone(report["accuracy"])
        self.assertIsNone(report["precision"])
        self.assertIsNone(report["recall"])

    def test_human_rejection_overrides_view_but_is_an_automatic_error(self):
        reviews = {("test", "United States"): judgment(decision="no")}
        self.assertEqual(assignments(self.rows, self.features, reviews), [])
        report = evaluate_countries(self.rows, self.features, reviews)
        self.assertEqual(report["counts"]["false_positive"], 1)
        self.assertEqual(report["accuracy"], 0)

    def test_manual_addition_is_not_relabelled_as_an_automatic_success(self):
        reviews = {("test", "China"): judgment(country="China")}
        assigned = assignments(self.rows, self.features, reviews)
        chinese = next(r for r in assigned if r["country"] == "China")
        self.assertEqual(chinese["country_status"], "Human confirmed")
        self.assertFalse(chinese["country_auto_prediction"])
        self.assertEqual(evaluate_countries(self.rows, self.features, reviews)["counts"]["false_negative"], 1)

    def test_unsure_holds_assignment_and_does_not_become_a_gold_negative(self):
        reviews = {("test", "United States"): judgment(decision="unsure")}
        self.assertEqual(assignments(self.rows, self.features, reviews), [])
        report = evaluate_countries(self.rows, self.features, reviews)
        self.assertEqual(report["reviewed_pairs"], 1)
        self.assertEqual(report["evaluated_pairs"], 0)

    def test_reviewed_only_does_not_include_automatic_labels(self):
        self.assertEqual(assignments(self.rows, self.features, reviewed_only=True), [])
        reviews = {("test", "United States"): judgment()}
        self.assertEqual(country_coverage(assignments(self.rows, self.features, reviews, True)), [{"country": "United States", "articles": 1}])

    def test_provenance_and_source_checks(self):
        for changes in [{"reviewer": ""}, {"annotation_origin": "model"}, {"notes": ""}, {"title_sha256": "changed"}, {"country": "Europe"}]:
            review = judgment(**changes)
            with self.assertRaises(ValueError):
                assignments(self.rows, self.features, {("test", review["country"]): review})

    def test_saved_reviews_persist_and_invalid_changes_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            save_country_review(directory, self.rows, self.features, judgment())
            path = Path(directory)/"destination_reviews.csv"
            before = path.read_bytes()
            self.assertEqual(read_country_reviews(directory, self.rows)[("test", "United States")]["decision"], "yes")
            with self.assertRaises(ValueError):
                save_country_review(directory, self.rows, self.features, judgment(reviewer=""))
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
