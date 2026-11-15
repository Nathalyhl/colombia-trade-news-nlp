"""Exercise actual snapshot, filters and empty results through Streamlit AppTest."""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class DashboardTests(unittest.TestCase):
    def test_dashboard_and_filters(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreater(int(app.metric[0].value), 0)
        baseline_count = int(app.metric[0].value)
        app.multiselect[2].set_value(["China"]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertLess(int(app.metric[0].value), baseline_count)
        app.text_input[0].set_value("no_such_headline_zzxy").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "0")
        app.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
