"""Synthetic calendar and leakage checks; no fabricated empirical trade results."""
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from trade_news.economics import load_trade, growth_asof, make_fold, compare, assumed_availability, lead_lag


class EconomicDesignTests(unittest.TestCase):
    def test_country_rows_are_not_silently_summed_into_national_exports(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"synthetic.csv"
            path.write_text("month,fob_usd,source_url,destination\n2020-01,100,https://example.org,Country A\n", encoding="utf8")
            with self.assertRaisesRegex(ValueError, "World totals"):
                load_trade(path)

    def test_missing_calendar_months_remain_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"synthetic.csv"
            path.write_text("month,fob_usd,source_url\n2020-01,100,https://example.org\n2020-03,110,https://example.org\n", encoding="utf8")
            frame = load_trade(path)
            self.assertEqual(len(frame), 3)
            self.assertTrue(pd.isna(frame.loc["2020-02", "fob_usd"]))

    def test_unreleased_or_later_revision_value_cannot_enter_training_growth(self):
        index = pd.period_range("2019-01", periods=15, freq="M")
        frame = pd.DataFrame({"fob_usd": [100.0]*15, "release_date": pd.Timestamp("2020-02-01"),
                              "vintage_date": pd.Timestamp("2020-03-01")}, index=index)
        self.assertTrue(growth_asof(frame, "2020-02-15").isna().all())
        self.assertTrue(growth_asof(frame, "2020-01-31", True).isna().all())
        frame.loc[pd.Period("2020-01"), "fob_usd"] = 200
        self.assertAlmostEqual(growth_asof(frame, "2020-03-15").loc["2020-01"], 69.314718, places=5)

    def test_forecast_feature_scaling_and_training_ignore_future_news_and_exports(self):
        index = pd.period_range("2018-01", periods=84, freq="M")
        trade = pd.DataFrame({"fob_usd": [100+i for i in range(84)],
                              "release_date": [(p+2).start_time for p in index],
                              "vintage_date": [(p+2).start_time for p in index]}, index=index)
        news = pd.DataFrame({"tone": [i%7 for i in range(84)], "uncertainty": [i%3 for i in range(84)]}, index=index)
        first = make_fold(trade, news, "2023-01")
        self.assertEqual(first["status"], "ready")
        altered_trade, altered_news = trade.copy(), news.copy()
        altered_trade.loc["2023-01":, "fob_usd"] = 999999
        altered_news.loc["2023-01":, ["tone", "uncertainty"]] = 999999
        second = make_fold(altered_trade, altered_news, "2023-01")
        pd.testing.assert_series_equal(first["y"], second["y"])
        pd.testing.assert_frame_equal(first["x"], second["x"])
        pd.testing.assert_frame_equal(first["future_x"], second["future_x"])
        self.assertEqual(first["origin"], "2022-12-31")

    def test_missing_availability_dates_block_a_forecast_claim(self):
        index = pd.period_range("2020-01", periods=2, freq="M")
        frame = pd.DataFrame({"fob_usd": [100, 110], "release_date": pd.NaT, "vintage_date": pd.NaT}, index=index)
        report = compare(frame, pd.DataFrame())
        self.assertEqual(report["status"], "blocked_missing_release_or_vintage_dates")
        self.assertIsNone(report["metrics"])

    def test_assumed_timing_is_explicit_and_does_not_modify_source(self):
        index = pd.period_range("2020-01", periods=2, freq="M")
        frame = pd.DataFrame({"fob_usd": [100, 110], "release_date": pd.NaT, "vintage_date": pd.NaT}, index=index)
        scenario = assumed_availability(frame, 2)
        self.assertEqual(str(scenario.iloc[0]["release_date"].date()), "2020-03-31")
        self.assertTrue(frame["release_date"].isna().all())
        with self.assertRaisesRegex(ValueError, "explicit revised-history"):
            compare(frame, pd.DataFrame(), assumed_release_lag=2)

    def test_constant_source_composition_is_removed_without_using_future_variance(self):
        index = pd.period_range("2018-01", periods=84, freq="M")
        trade = pd.DataFrame({"fob_usd": [100+i for i in range(84)],
                              "release_date": [(p+2).start_time for p in index],
                              "vintage_date": [(p+2).start_time for p in index]}, index=index)
        news = pd.DataFrame({"tone": [i%7 for i in range(84)], "uncertainty": [i%3 for i in range(84)],
                             "source_share": 1.0, "log_articles": [i%5 for i in range(84)]}, index=index)
        fold = make_fold(trade, news, "2023-01")
        self.assertEqual(fold["status"], "ready")
        self.assertNotIn("source_share", fold["x"].columns)
        self.assertEqual(list(fold["x"].columns), list(fold["future_x"].columns))

    def test_previous_export_period_can_align_with_news_after_last_numeric_month(self):
        periods = pd.period_range("2019-01", periods=24, freq="M")
        trade = pd.DataFrame({"fob_usd": [100+i*i for i in range(24)]}, index=periods)
        news = pd.DataFrame({"tone": [0.1, 0.3, 0.4]}, index=pd.period_range("2020-11", periods=3, freq="M"))
        report = lead_lag(trade, news)
        earlier = next(r for r in report['pairs'] if r['export_month_minus_news_month'] == -1)
        self.assertEqual(earlier['n'], 3)
