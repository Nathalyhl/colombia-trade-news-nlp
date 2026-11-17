"""Spanish research dashboard; source data and code identifiers remain unchanged."""
import csv
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from trade_news.articles import read_jsonl
from trade_news.bank_method import aggregate
from trade_news.charts import index_chart
from trade_news.contextual import aggregate_scores, verify_scores
from trade_news.corpus import REVIEW_FIELDS, build, read_reviews
from trade_news.destinations import COUNTRIES
from trade_news.country_review import (assignments, country_coverage, evaluate_countries,
    read_country_reviews, save_country_review, title_hash)

BASE = Path(__file__).resolve().parent
DATA = BASE/"data"
LABELS_ES = {"POS": "Positivo", "NEU": "Neutro", "NEG": "Negativo"}
RULE_LABELS_ES = {
    "export_to_market_in_headline": "El titular relaciona las exportaciones colombianas con este país mediante una expresión de destino.",
    "named_destination_or_buyer_role_in_headline": "El titular presenta al país como destino, comprador o cliente.",
    "named_buyer_in_Colombian_export_headline": "El titular identifica al país como comprador en un contexto de exportaciones colombianas.",
    "comparison_or_source_not_destination": "El país aparece como competidor, comparación u origen; no como destino.",
}
COUNTRY_NAMES = {"United States": "Estados Unidos", "Brazil": "Brasil", "Peru": "Perú", "Mexico": "México",
    "Canada": "Canadá", "Panama": "Panamá", "Dominican Republic": "República Dominicana", "Haiti": "Haití",
    "Trinidad and Tobago": "Trinidad y Tobago", "United Kingdom": "Reino Unido", "Spain": "España",
    "France": "Francia", "Germany": "Alemania", "Italy": "Italia", "Netherlands": "Países Bajos",
    "Belgium": "Bélgica", "Switzerland": "Suiza", "Sweden": "Suecia", "Norway": "Noruega", "Denmark": "Dinamarca",
    "Finland": "Finlandia", "Poland": "Polonia", "Ireland": "Irlanda", "Greece": "Grecia", "Romania": "Rumania",
    "Russia": "Rusia", "Ukraine": "Ucrania", "Turkey": "Turquía", "Egypt": "Egipto", "Algeria": "Argelia",
    "Morocco": "Marruecos", "South Africa": "Sudáfrica", "Kenya": "Kenia", "Saudi Arabia": "Arabia Saudita",
    "United Arab Emirates": "Emiratos Árabes Unidos", "Jordan": "Jordania", "Lebanon": "Líbano", "Iraq": "Irak",
    "Iran": "Irán", "Japan": "Japón", "South Korea": "Corea del Sur", "Philippines": "Filipinas",
    "Malaysia": "Malasia", "Singapore": "Singapur", "Thailand": "Tailandia", "Pakistan": "Pakistán",
    "Bangladesh": "Bangladés", "New Zealand": "Nueva Zelanda", "Qatar": "Catar"}


def country_name(country):
    return "Todos los destinos" if country == "__all__" else COUNTRY_NAMES.get(country, country)


def load_json(name):
    return json.loads((DATA/name).read_text("utf8"))


def headline(row):
    return row.get("publisher_title") or row["title"]


def monthly_table(records):
    columns = {"month": "Mes", "articles": "Artículos", "publishers": "Fuentes", "mean_probability_balance": "Tono del modelo",
               "positive_count": "P", "negative_count": "N", "uncertainty_count": "U", "processed_tokens": "W",
               "sentiment": "Balance del diccionario", "uncertainty_per_1000": "Incertidumbre por 1.000"}
    frame = pd.DataFrame(records)
    return frame[[key for key in columns if key in frame]].rename(columns=columns)


st.set_page_config(page_title="Noticias de exportaciones colombianas", page_icon="🇨🇴", layout="wide")
rows = read_jsonl(DATA/"headlines.jsonl")
indices, audit, log, validation = [load_json(name) for name in
    ["indices.json", "processing_audit.json", "collection_log.json", "validation_report.json"]]
features = read_jsonl(DATA/"destinations.jsonl")
feature_lookup = {r["record_id"]: r for r in features}
country_reviews = read_country_reviews(DATA, rows)
country_report = evaluate_countries(rows, features, country_reviews)
country_rows = assignments(rows, features, country_reviews)
eligible = [r for r in rows if r["eligible_for_index"]]
row_lookup = {r["record_id"]: r for r in eligible}
months = [r["month"] for r in log["requests"]]
bank_series = [r for r in indices["provisional"] if r["activity"] == "All exports"]
score_lookup, model_manifest, model_indices = {}, {}, {}
if (DATA/"contextual_manifest.json").exists():
    model_manifest = load_json("contextual_manifest.json")
    if model_manifest.get("status") == "complete":
        model_scores = read_jsonl(DATA/"contextual_scores.jsonl")
        try:
            verify_scores(DATA, model_scores, model_manifest)
        except ValueError as error:
            st.error("Las predicciones no corresponden al corpus actual: "+str(error))
        else:
            score_lookup = {r["record_id"]: r for r in model_scores}
            # Rebuild small aggregates directly from verified predictions.
            model_indices = {key: aggregate_scores(model_scores, eligible, months, dictionary_matched=matched)
                             for key, matched in [("all_eligible", False), ("dictionary_matched", True)]}

st.caption("COLOMBIA · EXPORTACIONES DE BIENES AL MUNDO · INVESTIGACIÓN NLP")
st.title("El lenguaje de las noticias de exportaciones")
st.write("Sentimiento e incertidumbre en noticias sobre exportaciones colombianas de bienes.")
st.caption("Marzo de 2020–octubre de 2026 · Mes de publicación · Adaptación independiente de métodos publicados")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Artículos elegibles", len(eligible))
c2.metric("Dominios de fuentes", len({r.get("publisher_group", r["publisher"]) for r in eligible}))
c3.metric("Meses con noticias", f"{len({r['month'] for r in eligible})} / {len(months)}")
c4.metric("Etiquetas humanas", validation["n_labeled"])
results_tab, news_tab, method_tab = st.tabs(["Resultados", "Noticias y destinos", "Metodología y validación"])


def article_evidence(article):
    identity = article["record_id"]
    st.subheader(headline(article))
    st.caption(f"{article['publisher']} · {article['publication_date']}")
    st.link_button("Leer noticia original", article["article_url"], key="article_source")
    if identity in score_lookup:
        score = score_lookup[identity]
        st.write("**Tono estimado por el modelo:** titular y cuerpo se analizan por separado.")
        details = []
        for unit, label in [("headline", "Titular"), ("body", "Cuerpo completo, fragmentado")]:
            prediction = score[unit]
            details.append({"Texto": label, "Clase del modelo": LABELS_ES[prediction["label"]], "Puntaje": prediction["score"],
                "P(negativo)": prediction["probabilities"]["NEG"], "P(neutro)": prediction["probabilities"]["NEU"],
                "P(positivo)": prediction["probabilities"]["POS"], "Fragmentos": prediction["chunks"]})
        st.dataframe(pd.DataFrame(details).round(4), hide_index=True, width="stretch")
        st.caption("Clase = probabilidad más alta. Puntaje = P(positivo) − P(negativo). Una clase neutra puede tener un puntaje distinto de cero. "
                   "Las probabilidades no son porcentajes de acierto comprobados.")
    if identity == "b30d353a15880d52e0b3":
        st.info("Lectura del titular: «reactivará» anuncia una reanudación de exportaciones. El modelo estima el tono del texto, "
                "que también describe antecedentes de suspensión y conflicto. Un puntaje negativo del cuerpo no significa que reanudar "
                "exportaciones sea negativo. Esta explicación del ejemplo no se guarda como etiqueta humana de evaluación.")
    st.caption("El mes corresponde a la publicación. El período estadístico mencionado y la base de comparación —interanual, mensual o acumulada— "
               "deben verificarse por separado; todavía no están anotados sistemáticamente.")
    links = [r for r in country_rows if r["record_id"] == identity]
    with st.expander("Evidencia del país de destino"):
        if not links:
            st.write("Sin vínculo de destino resuelto. Esto no significa que Colombia no exporte a los países mencionados.")
        for link in links:
            st.write("**"+country_name(link["country"])+"** · "+("Confirmado por una persona" if link["country_status"] == "Human confirmed" else "Propuesta automática pendiente de revisión"))
            if link["country_status"] == "Human confirmed":
                st.write(link["country_reason"])
            else:
                for hit in feature_lookup[identity].get("destination_evidence", []):
                    if hit["market"] == link["country"]:
                        st.write(RULE_LABELS_ES[hit["rule"]])
    with st.expander("Comparación léxica y trazabilidad"):
        st.write(f"Diccionario sobre el cuerpo: **P={article['positive_count']}, N={article['negative_count']}, "
                 f"U={article['uncertainty_count']}, W={article['processed_tokens']}**. Balance: {article['sentiment_score']}.")
        matches = article.get("matched_terms", [])
        if matches:
            match_frame = pd.DataFrame(matches).rename(columns={"word": "Palabra", "polarity": "Clase del diccionario", "count": "Ocurrencias"})
            st.dataframe(match_frame, hide_index=True)
        else:
            st.write("Sin coincidencias de polaridad: sentimiento léxico sin estimación; no equivale a neutralidad.")
        if article["positive_count"]+article["negative_count"] == 1:
            st.warning("El balance −1 o +1 depende aquí de una sola palabra. No indica intensidad comprobada ni dirección del acontecimiento exportador.")
        st.json({k: article.get(k) for k in ["record_id", "article_url", "publication_date", "date_source", "text_sha256",
            "text_characters", "candidate_sentences", "tokens_before_stopwords", "tokens_after_stopwords", "retained_sentences",
            "discarded_short_sentences", "processed_tokens", "method", "scope_reason", "document_role_proposal", "document_role_evidence"]})


def render_review_tools():
    st.subheader("¿Cómo comprobar las clasificaciones?")
    st.write("Revisa las fuentes, registra juicios humanos independientes y compáralos con las predicciones. "
             "Las pruebas del programa no demuestran precisión del clasificador.")
    q1, q2, q3 = st.columns(3)
    q1.metric("Pares noticia-país revisados", country_report["reviewed_pairs"])
    q2.metric("Exactitud de destinos", "Sin medir" if country_report["accuracy"] is None else f"{100*country_report['accuracy']:.1f}%")
    q3.metric("Etiquetas humanas de sentimiento", validation["n_labeled"])
    if not country_report["evaluated_pairs"]:
        st.info("La exactitud de destinos sigue sin medir: no hay juicios humanos de referencia. "
                "El formulario registra revisiones reales; no completa porcentajes automáticamente.")
    else:
        st.caption(country_report["note"])
        st.json(country_report)
    st.subheader("Ejemplo de relación: ¿competidor o destino?")
    comparison_cases = [(r, hit) for r in eligible for hit in feature_lookup[r["record_id"]].get("non_destination_evidence", [])]
    if comparison_cases:
        example, hit = next((pair for pair in comparison_cases if pair[0]["record_id"] == "a1348320f184c51f24f5"), comparison_cases[0])
        st.write(example.get("publisher_title") or example["title"])
        st.write(f"**{country_name(hit['market'])} no se asigna como destino.** {RULE_LABELS_ES[hit['rule']]}")
        st.link_button("Consultar esta fuente", example["article_url"])
        st.caption("«frente a Brasil» señala una comparación en esta fuente. Es un ejemplo diagnóstico; "
                   "no es una estimación de exactitud ni una etiqueta humana de evaluación.")
    st.subheader("Revisar una relación con un país")
    review_id = st.selectbox("Noticia para revisar", [r["record_id"] for r in eligible], key="review_article",
        format_func=lambda identity: next((r.get("publisher_title") or r["title"]) for r in eligible if r["record_id"] == identity))
    review_article = next(r for r in eligible if r["record_id"] == review_id)
    feature = feature_lookup[review_id]
    suggested = list(dict.fromkeys(feature.get("destinations", [])+feature.get("market_mentions", [])))
    options = [c for c in suggested if c in COUNTRIES]+sorted(set(COUNTRIES)-set(suggested))
    review_country = st.selectbox("País que vas a comprobar", options, key="review_country", format_func=country_name)
    st.write(review_article.get("publisher_title") or review_article["title"])
    st.link_button("Leer la noticia antes de etiquetar", review_article["article_url"])
    st.caption("Pregunta: ¿se presenta este país como destino de exportaciones colombianas de bienes? "
               "Se incluyen vínculos históricos, potenciales o interrumpidos; ser competidor o proveedor no basta. "
               "Decide antes de abrir la explicación automática.")
    with st.expander("Ver la explicación automática después de decidir"):
        auto = review_country in feature.get("destinations", [])
        st.write("Predicción automática: se menciona como destino" if auto else "Predicción automática: sin vínculo explícito de destino")
        hits = [h for h in feature.get("destination_evidence", [])+feature.get("non_destination_evidence", []) if h["market"] == review_country]
        for hit in hits:
            st.write(RULE_LABELS_ES[hit["rule"]])
        if not hits:
            st.write("El nombre de un país no establece la dirección del comercio. Consulta la fuente.")
    previous = country_reviews.get((review_id, review_country))
    if previous:
        st.caption(f"Decisión guardada: {previous['decision']} · Revisor: {previous['reviewer']} · {previous['notes']}")
    with st.form("country_review_form"):
        decision = st.selectbox("Tu decisión", ["Elige una decisión", "Se presenta como destino", "No es un destino", "No puedo determinarlo"])
        reviewer_name = st.text_input("Nombre de quien revisa")
        review_note = st.text_area("Explica la evidencia de la fuente")
        confirmed = st.checkbox("Leí personalmente la fuente y tomé esta decisión.")
        save = st.form_submit_button("Guardar revisión del país")
    if save:
        if not confirmed or decision == "Elige una decisión":
            st.error("Elige una decisión y confirma que revisaste personalmente la fuente.")
        else:
            review = {"record_id": review_id, "country": review_country,
                "decision": {"Se presenta como destino": "yes", "No es un destino": "no", "No puedo determinarlo": "unsure"}[decision],
                "reviewer": reviewer_name.strip(), "annotation_origin": "human", "notes": review_note.strip(), "title_sha256": title_hash(review_article)}
            try:
                save_country_review(DATA, rows, features, review)
            except ValueError as error:
                st.error(str(error))
            else:
                st.rerun()
    with st.expander("Revisar inclusión en el corpus y sentimiento"):
        st.write("Estas decisiones evalúan la pertenencia al corpus y el tono de la noticia. "
                 "Los destinos se revisan en el formulario anterior.")
        reviews = read_reviews(DATA/"annotations.csv")
        frame = pd.DataFrame(list(reviews.values()), columns=REVIEW_FIELDS).fillna("").drop(columns=["activity"])
        with st.form("corpus_review"):
            edited = st.data_editor(frame, hide_index=True, disabled=["record_id", "title", "url", "annotation_origin"],
                column_config={"url": st.column_config.LinkColumn("Leer fuente"),
                    "include": st.column_config.SelectboxColumn("Incluir", options=["", "yes", "no", "review"]),
                    "sentiment_gold": st.column_config.SelectboxColumn("Etiqueta opcional de sentimiento", options=["", "positive", "negative", "neutral"])}, width="stretch")
            confirm = st.checkbox("Revisé personalmente las decisiones y etiquetas que voy a guardar.")
            save_corpus = st.form_submit_button("Guardar revisión del corpus y recalcular")
        if save_corpus:
            if not confirm:
                st.error("Confirma que las decisiones corresponden a tu revisión humana.")
            else:
                pending = [{**reviews[row["record_id"]], **row} for row in edited.fillna("").to_dict("records")]
                for row in pending:
                    if row["include"] in {"yes", "no"} or row["sentiment_gold"]:
                        row["annotation_origin"] = "human"
                from trade_news.corpus import apply_reviews
                try:
                    apply_reviews(read_jsonl(DATA/"article_manifest.jsonl"), {r["record_id"]: r for r in pending})
                    with (DATA/"annotations.csv").open("w", encoding="utf8", newline="") as stream:
                        writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDS)
                        writer.writeheader()
                        writer.writerows(pending)
                    build(DATA)
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.rerun()
    st.caption("Las métricas comparan la predicción original con las etiquetas humanas aportadas, antes de corregirla. "
               "Una revisión por conveniencia no es una evaluación independiente. Validar sentimiento y validar utilidad económica son tareas diferentes.")


with results_tab:
    st.subheader("¿Cómo cambia el tono de las noticias?")
    st.write("El puntaje resume el balance entre lenguaje positivo y negativo estimado en el cuerpo de los artículos. "
             "Describe esta muestra de noticias; no mide el crecimiento de las exportaciones ni demuestra capacidad de pronóstico.")
    st.warning("Cobertura histórica: entre 2020 y 2025 los artículos elegibles proceden únicamente de Analdex; en 2026 se añaden otros medios. "
               "Los cambios pueden reflejar tanto el lenguaje como la composición de las fuentes.")
    if model_indices:
        st.plotly_chart(index_chart(model_indices["all_eligible"], "mean_probability_balance", "Tono de las noticias · modelo en español",
                                   [-1.05, 1.05], language="es"), width="stretch", key="general_sentiment")
        st.caption("Puntos: promedio mensual de P(positivo) − P(negativo), con el mismo peso para cada artículo. "
                   "Línea oscura: media del mes actual y los dos anteriores, solo si los tres tienen datos. "
                   "La agregación mensual y la alineación hacia atrás son decisiones de esta adaptación; no se rellenan vacíos.")
    else:
        st.info("No hay una ejecución completa y vigente del modelo. No se muestra una serie parcial o desactualizada.")
    st.subheader("¿Cuánto lenguaje de incertidumbre aparece?")
    st.plotly_chart(index_chart(bank_series, "uncertainty_per_1000", "Incertidumbre textual · diccionario del Banco de la República",
                               language="es"), width="stretch", key="general_uncertainty")
    st.caption("Ocurrencias de seis formas de «incertidumbre / incierto» por cada 1.000 palabras procesadas. "
               "Es una medida léxica de las noticias; no es la incertidumbre del modelo ni el riesgo comprobado de exportar.")
    with st.expander("Cobertura mensual y sensibilidad a las fuentes"):
        institutional = [sum(r["month"] == month and r.get("publisher_group") == "analdex.org" for r in eligible) for month in months]
        volume = go.Figure()
        volume.add_bar(x=months, y=institutional, name="Analdex", marker_color="#8a9cae")
        volume.add_bar(x=months, y=[r["articles"]-a for r, a in zip(bank_series, institutional)], name="Otros medios", marker_color="#1e465e")
        volume.update_layout(height=260, barmode="stack", template="plotly_white", yaxis_title="Artículos elegibles",
                             xaxis_title="Mes de publicación", legend={"orientation": "h"})
        st.plotly_chart(volume, width="stretch", key="general_volume")
        fixed_rows = [r for r in eligible if r.get("publisher_group") == "analdex.org"]
        if score_lookup:
            fixed_series = aggregate_scores(list(score_lookup.values()), fixed_rows, months)
            fixed_chart = go.Figure()
            for records, label in [(model_indices["all_eligible"], "Todas las fuentes"), (fixed_series, "Solo Analdex")]:
                fixed_chart.add_scatter(x=months, y=[r["mean_probability_balance"] for r in records], mode="lines+markers", name=label, connectgaps=False)
            fixed_chart.update_layout(title="Mismo modelo; composición de fuentes distinta", template="plotly_white", height=300,
                                      xaxis_title="Mes de publicación", yaxis_title="Balance de probabilidades", legend={"orientation": "h"})
            st.plotly_chart(fixed_chart, width="stretch", key="fixed_source_sentiment")
        st.caption("Mantener Analdex como fuente permite examinar el cambio de composición. No elimina el sesgo institucional ni demuestra representatividad.")
        st.dataframe(monthly_table(model_indices.get("all_eligible", bank_series)), hide_index=True)
    st.caption("Fuente: cálculos del proyecto sobre artículos recuperados. Modelos y métodos originales conservan sus créditos. "
               "Las mediciones automáticas están pendientes de evaluación humana.")

with news_tab:
    st.subheader("De la gráfica a la noticia")
    st.write("Consulta las fuentes y compara el titular con el cuerpo. El filtro por país muestra vínculos de destino propuestos, no valores de exportación.")
    left, right = st.columns(2)
    coverage = country_coverage(country_rows)
    country = left.selectbox("País de destino", ["__all__"]+[r["country"] for r in coverage], format_func=country_name, key="destination_country")
    search = right.text_input("Buscar en los titulares", key="article_search")
    reviewed_only = st.checkbox("Solo vínculos de país confirmados por una persona", key="country_reviewed_only")
    view = assignments(rows, features, country_reviews, reviewed_only=reviewed_only)
    linked_ids = {r["record_id"] for r in view if country == "__all__" or r["country"] == country}
    visible = [r for r in eligible if (country == "__all__" and not reviewed_only or r["record_id"] in linked_ids)
               and search.casefold() in headline(r).casefold()]
    st.caption(f"{len(visible)} noticias coinciden. Estos filtros no modifican los resultados generales.")
    if not visible:
        st.info("No hay noticias coincidentes. No existen vínculos confirmados por una persona en esta selección." if reviewed_only
                else "No hay noticias coincidentes. Borra la búsqueda o cambia el país.")
    else:
        if country != "__all__":
            observed_months = len({r["month"] for r in visible})
            st.info(f"{country_name(country)}: {len(visible)} noticias en {observed_months} meses de publicación. "
                    "La cobertura puede ser discontinua; no establece una tendencia representativa del país. El tono corresponde al artículo completo.")
            with st.expander("Resumen mensual de las noticias seleccionadas"):
                selected_bank = [r for r in aggregate(visible, months) if r["activity"] == "All exports"]
                if score_lookup:
                    selected_model = aggregate_scores(list(score_lookup.values()), visible, months)
                    st.plotly_chart(index_chart(selected_model, "mean_probability_balance", country_name(country)+" · tono de artículos vinculados",
                                               [-1.05, 1.05], focus_observed=True, language="es"), width="stretch", key="country_sentiment")
                    selected_lookup = {r["month"]: r for r in selected_model}
                    selected_bank = [{**r, "mean_probability_balance": selected_lookup[r["month"]]["mean_probability_balance"]} for r in selected_bank]
                st.dataframe(monthly_table([r for r in selected_bank if r["articles"]]), hide_index=True)
                st.caption("Solo se dibuja una media móvil cuando existen tres meses consecutivos con valor. Un vacío no equivale a cero. "
                           "Los países son menciones relacionadas con exportaciones; sus noticias pueden solaparse.")
        table = [{"Fecha": r["publication_date"], "Titular": headline(r), "Fuente": r["publisher"],
                  "Clase del cuerpo": LABELS_ES[score_lookup[r["record_id"]]["body"]["label"]] if r["record_id"] in score_lookup else "Sin predicción",
                  "Leer fuente": r["article_url"]} for r in visible]
        st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch",
                     column_config={"Leer fuente": st.column_config.LinkColumn("Leer fuente")})
        options = sorted((r["record_id"] for r in visible), key=lambda identity: (identity != "b30d353a15880d52e0b3", row_lookup[identity]["publication_date"], identity))
        chosen = st.selectbox("Inspeccionar una noticia", options, format_func=lambda identity: headline(row_lookup[identity]), key="inspect_article")
        article_evidence(row_lookup[chosen])

with method_tab:
    st.subheader("Una adaptación con dos mediciones complementarias")
    st.markdown("**Pregunta descriptiva:** ¿cómo evoluciona el lenguaje de las noticias sobre exportaciones colombianas de bienes? "
                "**Pregunta posterior:** ¿aporta información adicional a las estadísticas oficiales? Esa segunda pregunta sigue sin evaluar.")
    st.markdown("Referencias: [Dávila y Chasi · Banco Central del Ecuador](https://doi.org/10.47550/RCE/35.2.1), "
                "[BE1340 · Banco de la República](https://doi.org/10.32468/be.1340) y "
                "[código público de PySentimiento](https://github.com/pysentimiento/pysentimiento).")
    st.table(pd.DataFrame([
        ["Ecuador", "Sentimiento en español y evaluación con noticias etiquetadas por personas", "Modelo público de PySentimiento; evaluación humana pendiente"],
        ["Banco de la República", "Diccionario publicado, conteos auditables e incertidumbre textual", "Diccionario intacto; fórmulas por separado"],
        ["Este proyecto", "Corpus de exportaciones de bienes, artículos largos y vínculos con países", "Agregación mensual, trazabilidad y comparación entre métodos"],
    ], columns=["Referencia", "Qué aporta al diseño", "Estado de la adaptación"]))
    st.info("No se obtuvieron scripts originales de los dos estudios en los registros consultados. Se reutilizan el modelo y el preprocesamiento "
            "públicos de PySentimiento, con sus créditos y condiciones de uso científico/no comercial. No se afirma una réplica exacta de los experimentos originales.")
    st.subheader("Construcción paso a paso")
    st.markdown("**Noticias reales → extracción y fechas → selección y duplicados → dos rutas de análisis → agregación mensual → revisión humana**")
    st.table(pd.DataFrame([
        ["1 · Corpus", "Textos de los editores, URL, fecha explícita y hash; exportaciones colombianas de bienes. Muestra histórica incompleta."],
        ["2 · Selección", "Foco exportador en el titular y reglas conservadoras de alcance; casos ambiguos para revisión. Duplicados exactos y URL canónica."],
        ["3a · Modelo en español", "Preprocesamiento original de PySentimiento; cuerpo completo en fragmentos de hasta 128 tokens incluidos los especiales. Probabilidades ponderadas por tokens."],
        ["3b · Diccionario del Banco", "Mínimo 50 caracteres; segmentación, minúsculas y stopwords congeladas; oraciones con más de cinco palabras restantes; coincidencias exactas."],
        ["4 · Agregación", "Modelo: media mensual por artículo. Diccionario: sumar P, N, U y W del mes y después dividir. Mes según fecha de publicación."],
        ["5 · Validación", "Revisar extracción, alcance, tono y destinos de forma independiente. Después contrastar con datos de exportaciones y sus fechas de disponibilidad."],
    ], columns=["Etapa", "Regla operativa"]))
    st.latex(r"T_{i}=p_{i,+}-p_{i,-}, \quad T_t=\frac{1}{n_t}\sum_{i \in t}T_i")
    st.latex(r"SENT_t=\frac{P_t-N_t}{P_t+N_t}, \qquad UNCERT_t=1000\frac{U_t}{W_t}")
    st.caption("P/N: ocurrencias positivas/negativas; U: seis formas de incertidumbre; W: palabras retenidas. "
               "188 formas positivas y 376 negativas, sin añadir conjugaciones para forzar resultados. Si P+N=0 no hay estimación de sentimiento. "
               "La Figura 3 del Banco muestra una media móvil trimestral; nuestra alineación usa el mes actual y los dos anteriores. "
               "Ecuador agrega diariamente; la frecuencia mensual y el manejo de textos largos son adaptaciones propias.")
    with st.expander("Comparar el modelo con el diccionario"):
        if model_indices:
            cohort = st.radio("Artículos de la comparación", ["Con coincidencias en el diccionario", "Todos los artículos elegibles"],
                              horizontal=True, key="contextual_cohort")
            contextual_series = model_indices["dictionary_matched" if cohort == "Con coincidencias en el diccionario" else "all_eligible"]
            comparison = go.Figure()
            for records, column, label in [(bank_series, "sentiment", "Diccionario · conteos agrupados"),
                                           (contextual_series, "mean_probability_balance", "Modelo · media por artículo")]:
                comparison.add_scatter(x=months, y=[r[column] for r in records], mode="lines+markers", name=label, connectgaps=False)
            comparison.update_layout(template="plotly_white", height=360, xaxis_title="Mes de publicación", yaxis_title="Puntaje de tono",
                                     legend={"orientation": "h"})
            comparison.update_yaxes(range=[-1.05, 1.05], zeroline=False)
            st.plotly_chart(comparison, width="stretch", key="contextual_comparison")
            st.caption("Los pesos difieren: palabras en el diccionario, artículos en el modelo. La opción restringida compara el mismo subconjunto; "
                       "un desacuerdo no demuestra cuál es correcto. No se construye un índice mezclando ambas fórmulas.")
        st.dataframe(monthly_table(bank_series), hide_index=True)
    with st.expander("Corpus, fuentes y decisiones de selección"):
        st.table(pd.DataFrame([("Registros descubiertos", audit["candidate_records"]), ("Textos recuperados", audit["extracted_articles"]),
                              ("Elegibles provisionales", len(eligible)), ("Con coincidencias de polaridad", sum(r["positive_count"]+r["negative_count"] > 0 for r in eligible))],
                             columns=["Etapa", "Registros"]))
        st.write("Las reglas de inclusión y las propuestas sobre el tipo de documento no han sido validadas. "
                 "Un informe puede repetir cifras ya publicadas; una expectativa no constituye automáticamente información nueva ni predictiva.")
        subset = [r for r in eligible if r.get("document_role_proposal") not in {"statistical_reporting_candidate", "mixed_cues"}]
        st.caption(f"Diagnóstico al excluir candidatos a informe estadístico o mixto: quedan {len(subset)} de {len(eligible)} artículos. "
                   "Los roles sin resolver permanecen; no es un corpus prospectivo verificado.")
        subset_series = [r for r in aggregate(subset, months) if r["activity"] == "All exports"]
        st.plotly_chart(index_chart(subset_series, "sentiment", "Sensibilidad léxica al tipo de documento", [-1.05, 1.05], language="es"),
                        width="stretch", key="document_role_sensitivity")
        st.dataframe(pd.DataFrame(audit["fetch_status_counts"].items(), columns=["Estado de recuperación", "Registros"]), hide_index=True)
        st.caption("Las solicitudes fallidas o no intentadas no demuestran ausencia de noticias. El archivo local conserva cuerpos y HTML; el repositorio publica metadatos y resultados derivados.")
    st.subheader("Validación: qué falta para afirmar que funciona")
    st.write("Hay una muestra diagnóstica de 60 registros preparada y sin etiquetas humanas. Primero se revisan las fuentes sin ver las predicciones; "
             "después se registran discrepancias. La evaluación final requiere una muestra independiente y criterios escritos. "
             "El modelo fue entrenado con tuits en español, no con noticias de exportaciones colombianas.")
    st.markdown("1. Comprobar extracción, fechas y pertenencia al corpus.\n"
                "2. Separar **tono del texto**, **dirección del acontecimiento exportador** y **período estadístico**.\n"
                "3. Etiquetar de forma independiente y comparar clases, errores y casos sin respuesta; usar dos revisores cuando sea posible.\n"
                "4. Contrastar después con tus datos de exportaciones, respetando períodos, publicaciones y una evaluación temporal.")
    with st.expander("Priorizar casos para revisión, sin convertirlos en etiquetas"):
        if score_lookup:
            priority = []
            for identity, score in score_lookup.items():
                probabilities = sorted(score["body"]["probabilities"].values(), reverse=True)
                priority.append({"Titular": headline(row_lookup[identity]), "Fuente": row_lookup[identity]["publisher"],
                                 "Margen entre las dos clases más probables": probabilities[0]-probabilities[1],
                                 "Leer fuente": row_lookup[identity]["article_url"]})
            st.dataframe(pd.DataFrame(sorted(priority, key=lambda r: r["Margen entre las dos clases más probables"])[:20]), hide_index=True,
                         column_config={"Leer fuente": st.column_config.LinkColumn("Leer fuente")})
            st.caption("Ecuador describe muestreo por incertidumbre del clasificador. Aquí un margen pequeño solo propone casos ambiguos para diagnóstico; "
                       "no demuestra errores, no es incertidumbre económica y no sustituye una muestra independiente. No se modifica la muestra de 60 registros.")
    with st.expander("Registrar revisiones humanas"):
        render_review_tools()
    with st.expander("Código reutilizado, versiones y reproducibilidad"):
        st.markdown("Se reutilizan los pesos publicados y el preprocesamiento de PySentimiento. El adaptador de artículos largos, la selección del corpus "
                    "y el tablero son parte de este proyecto. Créditos y condiciones: `docs/THIRD_PARTY_NOTICES.md` y `reference/PYSENTIMIENTO_LICENSE.txt`. "
                    "No se redistribuyen pesos ni cuerpos completos de noticias.")
        st.json({k: model_manifest.get(k) for k in ["model_id", "model_revision", "upstream_source_commit", "method", "text_handling", "aggregation", "runtime", "license"]})
        st.caption("Las predicciones guardadas permiten reproducir los agregados sin descargar el modelo. Repetir la inferencia requiere el modelo fijado y el archivo local de textos. "
                   "Los porcentajes de precisión de otros estudios no se atribuyen a nuestra muestra.")
