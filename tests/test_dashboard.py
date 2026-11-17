"""Verify the general series stays fixed when secondary exploration changes."""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class DashboardTests(unittest.TestCase):
    def test_model_comparison_does_not_relabel_human_data_or_change_general_counts(self):
        base = Path(__file__).resolve().parents[1]
        before = (base/"data/annotations.csv").read_bytes()
        app = AppTest.from_file(str(base/"app.py"), default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        baseline = [metric.value for metric in app.metric[:4]]
        self.assertEqual(app.selectbox(key="inspect_article").value, "b30d353a15880d52e0b3")
        app.radio(key="contextual_cohort").set_value("Todos los artículos elegibles").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        self.assertEqual((base/"data/annotations.csv").read_bytes(), before)

    def test_country_focused_layout_and_evidence_search(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        baseline = [metric.value for metric in app.metric[:4]]
        self.assertGreater(int(baseline[0]), 0)
        self.assertEqual(len(app.multiselect), 0)
        self.assertEqual([tab.label for tab in app.tabs], ["Resultados", "Noticias y destinos", "Metodología y validación"])
        self.assertNotIn("Economic activities", str(app))
        self.assertNotIn("Regions and blocs", str(app))
        app.text_input(key="article_search").set_value("no_such_headline_zzxy").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        self.assertTrue(any("No hay noticias coincidentes" in item.value for item in app.info))

    def test_country_selection_and_reviewed_filter_keep_general_fixed(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Noticias y destinos", [tab.label for tab in app.tabs])
        baseline = [metric.value for metric in app.metric[:4]]
        options = app.selectbox(key="destination_country").options
        self.assertIn("Estados Unidos", options)
        self.assertIn("China", options)
        self.assertEqual(len(options), len(set(options)))
        self.assertNotIn("Latin America", options)
        app.selectbox(key="destination_country").set_value("China").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        app.checkbox(key="country_reviewed_only").set_value(True).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric[:4]], baseline)
        self.assertTrue(any("No existen vínculos confirmados" in item.value for item in app.info))

    def test_review_status_is_honest_and_form_does_not_invent_labels(self):
        base = Path(__file__).resolve().parents[1]
        path = base/"data/destination_reviews.csv"
        before = path.read_bytes()
        app = AppTest.from_file(str(base/"app.py"), default_timeout=45).run()
        metric = next(m for m in app.metric if m.label == "Exactitud de destinos")
        self.assertEqual(metric.value, "Sin medir")
        self.assertTrue(any("frente a Brasil" in item.value for item in app.caption))
        next(button for button in app.button if button.label == "Guardar revisión del país").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("revisaste personalmente" in item.value for item in app.error))
        self.assertEqual(path.read_bytes(), before)

    def test_country_exploration_and_global_inspection_share_one_article_selector(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        app.selectbox(key="destination_country").set_value("China").run()
        identity = app.selectbox(key="inspect_article").value
        app.selectbox(key="destination_country").set_value("__all__").run()
        app.selectbox(key="inspect_article").set_value(identity).run()
        self.assertEqual(len(app.exception), 0)

    def test_resumption_example_preserves_neutral_classes_and_explains_different_target(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        detail = next(frame.value for frame in app.dataframe if "P(negativo)" in frame.value.columns)
        self.assertEqual(list(detail["Clase del modelo"]), ["Neutro", "Neutro"])
        self.assertGreater(detail.iloc[0]["Puntaje"], 0)
        self.assertLess(detail.iloc[1]["Puntaje"], 0)
        self.assertTrue(any("anuncia una reanudación" in item.value for item in app.info))

    def test_united_states_filter_exposes_thirteen_articles_in_five_months(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=45).run()
        app.selectbox(key="destination_country").set_value("United States").run()
        self.assertEqual(len(app.exception), 0)
        articles = next(frame.value for frame in app.dataframe if "Clase del cuerpo" in frame.value.columns)
        self.assertEqual(len(articles), 13)
        monthly = next(frame.value for frame in app.dataframe if "Mes" in frame.value.columns and "Incertidumbre por 1.000" in frame.value.columns)
        self.assertEqual(len(monthly), 5)
        self.assertEqual(int(monthly["Artículos"].sum()), 13)


if __name__ == "__main__":
    unittest.main()
