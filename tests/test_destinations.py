"""Synthetic relation diagnostics; geographic tags are not trade statistics."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from trade_news.bank_method import aggregate
from trade_news.destinations import build_destinations, coverage, identify, monthly_series, select_articles


def row(identity="one", **changes):
    item = dict(record_id=identity, title="Exportaciones de Colombia a EE. UU.", eligible_for_index=True,
                month="2026-01", activity="Agriculture", publisher="Synthetic publisher", review_status="pending",
                positive_count=3, negative_count=1, uncertainty_count=1, processed_tokens=20, fetch_status="not_fetched")
    item.update(changes)
    return item


class DestinationTests(unittest.TestCase):
    def test_explicit_direction_and_alias(self):
        result = identify("Exportaciones de cacao de Colombia hacia Estados Unidos se triplicaron")
        self.assertEqual(result["destinations"], ["United States"])
        self.assertEqual(identify("Colombia exporta café a EE. UU.")["destinations"], ["United States"])

    def test_mentions_are_not_automatically_destinations(self):
        result = identify("China y Colombia discuten política comercial", "Estados Unidos anuncia aranceles para México.")
        self.assertEqual(result["destinations"], [])
        self.assertEqual(result["market_mentions"], ["China", "Mexico", "United States"])

    def test_inbound_exports_do_not_become_colombian_destinations(self):
        self.assertEqual(identify("Brasil aumenta sus exportaciones a Colombia")["destinations"], [])

    def test_buyer_role_and_no_country_from_region(self):
        self.assertEqual(identify("Estados Unidos compra cerca de 40% del café que exporta Colombia")["destinations"], ["United States"])
        result = identify("Colombia exporta bienes hacia Europa")
        self.assertEqual(result["destinations"], ["Europe"])
        self.assertNotIn("European Union", result["market_mentions"])
        self.assertNotIn("Germany", result["market_mentions"])

    def test_longest_alias_and_word_boundaries(self):
        self.assertEqual(identify("Colombia exporta carne hacia Asia-Pacífico")["destinations"], ["Asia-Pacific"])
        self.assertEqual(identify("La industria colombiana exporta mercancías")["market_mentions"], [])

    def test_counts_overlap_but_articles_contribute_once_per_market(self):
        features = [{"record_id": "one", **identify("Colombia exporta bienes a China", "China China Estados Unidos.")}]
        articles = [row()]
        self.assertEqual(coverage(articles, features, "market_mentions"), [{"market": "China", "articles": 1}, {"market": "United States", "articles": 1}])
        self.assertEqual(len(select_articles(articles, features, "China")), 1)

    def test_subset_formulas_missing_month_and_general_unchanged(self):
        articles = [row(), row("two", positive_count=0, negative_count=1)]
        features = [{"record_id": "one", **identify("Colombia exporta café a China")},
                    {"record_id": "two", **identify("Colombia exporta cacao a México")}]
        baseline = aggregate(articles, ["2026-01", "2026-02"])
        subset = monthly_series(articles, features, "China", ["2026-01", "2026-02"])
        self.assertEqual(subset[0]["sentiment"], .5)
        self.assertEqual(subset[0]["uncertainty_per_1000"], 50)
        self.assertIsNone(subset[1]["sentiment"])
        self.assertEqual(aggregate(articles, ["2026-01", "2026-02"]), baseline)

    def test_ineligible_article_not_counted(self):
        features = [{"record_id": "one", **identify("Colombia exporta café a China")}]
        self.assertEqual(coverage([row(eligible_for_index=False)], features), [])

    def test_body_cache_reproduces_without_publisher_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            archive = directory/"raw/articles"
            archive.mkdir(parents=True)
            text = "Café colombiano para clientes de Japón."
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            (archive/"one.txt").write_text(text, encoding="utf8")
            record = row(fetch_status="article_extracted", text_sha256=text_hash)
            first = build_destinations(directory, [record])
            (archive/"one.txt").unlink()
            self.assertEqual(build_destinations(directory, [record]), first)
            self.assertIn("Japan", first[0]["market_mentions"])
            record["title"] = "A changed source headline"
            with self.assertRaisesRegex(ValueError, "stale"):
                build_destinations(directory, [record])


if __name__ == "__main__":
    unittest.main()
