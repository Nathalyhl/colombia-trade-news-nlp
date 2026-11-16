"""Verify the general series stays fixed when secondary exploration changes."""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class DashboardTests(unittest.TestCase):
    def test_general_index_evidence_search_and_activity(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        baseline = [metric.value for metric in app.metric]
        self.assertGreater(int(baseline[0]), 0)
        self.assertEqual(len(app.multiselect), 0)
        self.assertNotIn("Export themes", str(app))
        app.selectbox[0].set_value("Education").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric], baseline)
        app.text_input[0].set_value("no_such_headline_zzxy").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric], baseline)
        self.assertTrue(any("No matching articles" in item.value for item in app.info))

    def test_destination_modes_keep_general_metrics_fixed(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Destinations", [tab.label for tab in app.tabs])
        baseline = [metric.value for metric in app.metric[:4]]
        app.selectbox(key="destination_market").set_value("China").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        app.radio(key="destination_mode").set_value("All market mentions in article text").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        app.radio(key="destination_kind").set_value("Regions and blocs").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)


if __name__ == "__main__":
    unittest.main()
