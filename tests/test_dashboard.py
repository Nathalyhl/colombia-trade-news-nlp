"""Verify the general series stays fixed when secondary exploration changes."""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class DashboardTests(unittest.TestCase):
    def test_country_focused_layout_and_evidence_search(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        baseline = [metric.value for metric in app.metric[:4]]
        self.assertGreater(int(baseline[0]), 0)
        self.assertEqual(len(app.multiselect), 0)
        self.assertEqual([tab.label for tab in app.tabs], ["General index", "Destinations", "Articles & evidence", "Quality & review", "Method"])
        self.assertNotIn("Economic activities", str(app))
        self.assertNotIn("Regions and blocs", str(app))
        app.text_input(key="article_search").set_value("no_such_headline_zzxy").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        self.assertTrue(any("No matching articles" in item.value for item in app.info))

    def test_country_selection_and_reviewed_filter_keep_general_fixed(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Destinations", [tab.label for tab in app.tabs])
        baseline = [metric.value for metric in app.metric[:4]]
        self.assertEqual(app.selectbox(key="destination_country").options, ["United States", "Ecuador", "Israel", "Venezuela", "China"])
        app.selectbox(key="destination_country").set_value("China").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        app.checkbox(key="country_reviewed_only").set_value(True).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        self.assertTrue(any("No human-confirmed country assignments" in item.value for item in app.info))

    def test_review_status_is_honest_and_form_does_not_invent_labels(self):
        base = Path(__file__).resolve().parents[1]
        path = base/"data/destination_reviews.csv"
        before = path.read_bytes()
        app = AppTest.from_file(str(base/"app.py"), default_timeout=45).run()
        metric = next(m for m in app.metric if m.label == "Country-label accuracy")
        self.assertEqual(metric.value, "Not measured")
        self.assertTrue(any("frente a Brasil" in item.value for item in app.caption))
        next(button for button in app.button if button.label == "Save country review").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("personally reviewed" in item.value for item in app.error))
        self.assertEqual(path.read_bytes(), before)

    def test_same_article_can_be_inspected_in_country_and_news_views(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        app.selectbox(key="destination_country").set_value("China").run()
        identity = app.selectbox(key="country_evidence").value
        app.selectbox(key="inspect_article").set_value(identity).run()
        self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
