"""Colombian goods export news: general trends, countries and auditable review."""
import csv
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from trade_news.articles import read_jsonl
from trade_news.corpus import REVIEW_FIELDS, build, read_reviews
from trade_news.bank_method import aggregate, trailing_quarterly_mean
from trade_news.destinations import COUNTRIES, RULE_LABELS
from trade_news.country_review import (assignments, country_coverage, evaluate_countries,
    read_country_reviews, save_country_review, title_hash)

BASE = Path(__file__).resolve().parent
DATA = BASE/"data"
st.set_page_config(page_title="Colombian Goods Export News", page_icon="🇨🇴", layout="wide")


def load_json(name):
    return json.loads((DATA/name).read_text("utf8"))


def index_chart(frame, column, title, bounds=None):
    records = frame.to_dict("records")
    fig = go.Figure(go.Scatter(x=frame["month"], y=frame[column], mode="lines", name="Monthly estimate",
        line={"color": "#b2b9c1", "width": 1}, connectgaps=False,
        customdata=frame[["articles", "publishers"]],
        hovertemplate="%{x}<br>Value: %{y:.3f}<br>Articles: %{customdata[0]}<br>Publishers: %{customdata[1]}<extra></extra>"))
    fig.add_trace(go.Scatter(x=frame["month"], y=trailing_quarterly_mean(records, column),
        mode="lines", name="Trailing 3-month mean", line={"color": "#142330", "width": 2.5}, connectgaps=False))
    fig.update_layout(title=title, xaxis_title="Publication month", yaxis_title=column.replace("_", " "), height=390,
        template="plotly_white", font={"family": "Georgia, serif", "color": "#182631"},
        paper_bgcolor="white", plot_bgcolor="white", legend={"orientation": "h", "y": -0.25},
        margin={"l": 40, "r": 20, "t": 55, "b": 70})
    fig.update_xaxes(type="date", dtick="M12", tickformat="%b %Y", showgrid=False)
    fig.update_yaxes(zeroline=True, zerolinecolor="#657380")
    if bounds:
        fig.update_yaxes(range=bounds, zeroline=True)
    return fig


rows = read_jsonl(DATA/"headlines.jsonl")
indices, audit, log, validation = [load_json(name) for name in
    ["indices.json", "processing_audit.json", "collection_log.json", "validation_report.json"]]
features = read_jsonl(DATA/"destinations.jsonl")
feature_lookup = {r["record_id"]: r for r in features}
country_reviews = read_country_reviews(DATA, rows)
country_report = evaluate_countries(rows, features, country_reviews)
country_rows = assignments(rows, features, country_reviews)
eligible = [r for r in rows if r["eligible_for_index"]]
months = [r["month"] for r in log["requests"]]
st.caption("COLOMBIAN GOODS EXPORTS TO THE WORLD · RESEARCH OBSERVATORY")
st.title("Export News: Sentiment & Uncertainty")
st.write("A dictionary-based study of Spanish-language news about exports of Colombian goods.")
st.caption("March 2020–October 2026 · Publication months · Independent adaptation of BE1340 · Corpus review pending")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Eligible news articles", len(eligible))
c2.metric("News sources", len({r["publisher"] for r in eligible}))
c3.metric("Publication months", len(months))
c4.metric("Articles linked to countries", len({r["record_id"] for r in country_rows}))
general, destinations_tab, evidence, quality, method = st.tabs(
    ["General index", "Destinations", "Articles & evidence", "Quality & review", "Method"])


def article_evidence(article, context):
    st.write(article.get("publisher_title") or article["title"])
    st.caption(f"{article['publisher']} · {article.get('publication_date', 'Date unavailable')}")
    url = article.get("article_url") or article.get("resolved_url") or article["url"]
    st.link_button("Read source article", url, key=context+"_source")
    if article.get("fetch_status") != "article_extracted":
        st.info("Publisher article text was not retrieved for this record. No article sentiment or uncertainty estimate is available.")
        st.json({k: article.get(k) for k in ["fetch_status", "fetch_error", "resolution_error", "date_source"]})
        return
    a, b, c = st.columns(3)
    a.metric("Positive word occurrences", article.get("positive_count", 0))
    b.metric("Negative word occurrences", article.get("negative_count", 0))
    c.metric("Uncertainty word occurrences", article.get("uncertainty_count", 0))
    matches = article.get("matched_terms", [])
    if matches:
        st.dataframe(pd.DataFrame(matches).rename(columns={"word": "Matched word", "polarity": "Dictionary class", "count": "Occurrences"}), hide_index=True, key=context+"_words")
    else:
        st.info("No dictionary polarity matches: the sentiment estimate is missing, not neutral.")
    polar = article.get("positive_count", 0)+article.get("negative_count", 0)
    st.caption(f"Lexical support: {polar} polarity matches across {article.get('processed_tokens', 0)} retained words. "
               "The score describes the article's dictionary balance, not whether its export event is beneficial.")
    if polar == 1:
        st.info("Only one polarity word matched. An article score of −1 or +1 here reflects that single word, not strong or validated sentiment.")
    st.caption("Publication month determines index timing. A reference to 2025 inside a 2026 article may describe a previous-year comparison; "
               "it does not change the publication month. The statistical reference period has not been independently annotated.")
    with st.expander("Source and processing trace"):
        st.json({k: article.get(k) for k in ["record_id", "article_url", "publication_date", "date_source", "text_sha256",
            "text_characters", "candidate_sentences", "tokens_before_stopwords", "tokens_after_stopwords",
            "retained_sentences", "discarded_short_sentences", "processed_tokens", "method",
            "processing_status", "scope_reason", "goods_evidence", "fetch_status", "fetch_error"]})


with general:
    st.subheader("Export-news sentiment index")
    st.caption("Coverage: 2020–2025 currently contains Analdex institutional publications only; 2026 adds other publishers. "
               "Use the fixed-source comparison below before interpreting changes across this boundary.")
    series = pd.DataFrame([r for r in indices["provisional"] if r["activity"] == "All exports"])
    st.plotly_chart(index_chart(series, "sentiment", "Colombian goods export news · sentiment", [-1.05, 1.05]), width="stretch", key="general_sentiment")
    st.caption("Thin gray: monthly estimate. Dark line: trailing mean of three consecutive available months, with no gap filling or future values. "
               "The Bank's Figure 3 uses a quarterly moving average; trailing alignment is our documented convention.")
    st.subheader("Export-news uncertainty index")
    st.plotly_chart(index_chart(series, "uncertainty_per_1000", "Colombian goods export news · uncertainty"), width="stretch", key="general_uncertainty")
    st.caption("Sentiment balances positive and negative dictionary words from −1 to +1. Uncertainty counts the six reference forms per 1,000 processed words. "
               "These measures describe news language; they do not measure export growth. Missing estimates stay missing.")
    st.subheader("How much news supports each month?")
    institutional = [sum(r["month"] == month and r["publisher"] == "Analdex" for r in eligible) for month in months]
    volume = go.Figure()
    volume.add_bar(x=months, y=institutional, name="Analdex · institutional source", marker_color="#8a9cae")
    volume.add_bar(x=months, y=[int(n)-a for n, a in zip(series["articles"], institutional)], name="Other publishers", marker_color="#1e465e")
    volume.update_layout(height=250, barmode="stack", template="plotly_white", margin={"t": 15, "b": 20},
                         yaxis_title="Eligible articles", xaxis_title="Publication month", legend={"orientation": "h"})
    st.plotly_chart(volume, width="stretch", key="general_volume")
    with st.expander("Source sensitivity: keep Analdex fixed across the whole period"):
        st.write("The same dictionary and equations are applied to eligible Analdex articles in every month. "
                 "This removes the 2026 addition of other publishers from this comparison; it does not remove institutional selection bias.")
        fixed_rows = [r for r in eligible if r["publisher"] == "Analdex"]
        fixed_series = pd.DataFrame([r for r in aggregate(fixed_rows, months) if r["activity"] == "All exports"])
        for column, label in [("sentiment", "Sentiment"), ("uncertainty_per_1000", "Uncertainty per 1,000 words")]:
            comparison = go.Figure()
            comparison.add_scatter(x=months, y=trailing_quarterly_mean(series.to_dict("records"), column),
                mode="lines", name="All retrieved sources", line={"color": "#142330"}, connectgaps=False)
            comparison.add_scatter(x=months, y=trailing_quarterly_mean(fixed_series.to_dict("records"), column),
                mode="lines", name="Analdex only", line={"color": "#467b9b", "dash": "dash"}, connectgaps=False)
            comparison.update_layout(title=label+" · trailing 3-month means", template="plotly_white", height=300,
                legend={"orientation": "h"}, xaxis_title="Publication month")
            st.plotly_chart(comparison, width="stretch", key="fixed_source_"+column)
        st.dataframe(fixed_series[["month", "articles", "positive_count", "negative_count", "uncertainty_count",
                                 "processed_tokens", "sentiment", "uncertainty_per_1000"]], hide_index=True)
    st.info("Historical coverage is incomplete. Analdex's public archive supplements limited Google News discovery. "
            "The source mix changes over time, so movements may reflect coverage as well as news language. Human corpus review is pending.")
    with st.expander("Monthly construction table: P, N, U, W and estimates"):
        st.dataframe(series[["month", "articles", "publishers", "positive_count", "negative_count", "uncertainty_count",
                             "processed_tokens", "sentiment", "uncertainty_per_1000"]], hide_index=True)
    st.caption("Source: authors' calculations from retrieved publisher texts, using the BE1340 dictionary and formulas. "
               "This is an independent export-news adaptation, not an official Bank series. The snapshot ends before 1 November 2026.")

with destinations_tab:
    st.subheader("Destinations by country")
    st.write("Only countries linked to Colombian exports enter this view. Each assignment has a source headline and an explanation.")
    reviewed_only = st.checkbox("Show human-confirmed assignments only", key="country_reviewed_only")
    view = assignments(rows, features, country_reviews, reviewed_only=reviewed_only)
    overview = country_coverage(view)
    if not overview:
        st.info("No human-confirmed country assignments are available yet." if reviewed_only else "No country assignments are available for this snapshot.")
    else:
        country = st.selectbox("Destination country", [r["country"] for r in overview], key="destination_country")
        selected_country = [r for r in view if r["country"] == country]
        d1, d2, d3 = st.columns(3)
        d1.metric("Linked articles", len(selected_country))
        d2.metric("Sources for this country", len({r["publisher"] for r in selected_country}))
        d3.metric("Human-confirmed links", sum(r["country_status"] == "Human confirmed" for r in selected_country))
        destination_frame = pd.DataFrame([r for r in aggregate(selected_country, months) if r["activity"] == "All exports"])
        dl, dr = st.columns(2)
        dl.plotly_chart(index_chart(destination_frame, "sentiment", f"{country}: article sentiment", [-1.05, 1.05]),
                        width="stretch", key="country_sentiment")
        dr.plotly_chart(index_chart(destination_frame, "uncertainty_per_1000", f"{country}: article uncertainty"),
                        width="stretch", key="country_uncertainty")
        st.caption("Automatic links remain proposals until reviewed. Scores use the whole article body, not country-specific sentences. "
                   "News may discuss historical, potential or interrupted exports. The general index stays fixed.")
        st.subheader("Why these articles belong to this country")
        table = [{"Date": r["publication_date"], "Headline": r.get("publisher_title") or r["title"], "Source": r["publisher"],
                  "Country label": r["country_status"], "Reason": r["country_reason"], "Read source": r["article_url"]} for r in selected_country]
        st.dataframe(pd.DataFrame(table), hide_index=True, column_config={"Read source": st.column_config.LinkColumn("Read source")})
        inspect_id = st.selectbox("Inspect country evidence", [r["record_id"] for r in selected_country], key="country_evidence",
            format_func=lambda identity: next((r.get("publisher_title") or r["title"]) for r in selected_country if r["record_id"] == identity))
        inspected = next(r for r in selected_country if r["record_id"] == inspect_id)
        st.info(inspected["country_reason"])
        article_evidence(inspected, "country_article")
        with st.expander("Compare country news coverage"):
            overview_frame = pd.DataFrame(overview)
            chart = go.Figure(go.Bar(x=overview_frame["articles"], y=overview_frame["country"], orientation="h"))
            chart.update_layout(height=300, yaxis={"autorange": "reversed"}, xaxis_title="Linked news articles")
            st.plotly_chart(chart, width="stretch", key="country_coverage")
            st.caption("Article counts are not export values or trade shares. An article can discuss several countries, so country totals may overlap. "
                       "A missing country label means the relation is unresolved, not that Colombia has no exports there.")

with evidence:
    st.subheader("Inspect the news and the words behind the score")
    search = st.text_input("Find words in an article title", key="article_search")
    only_eligible = st.checkbox("Show only eligible articles", value=True)
    visible = [r for r in rows if (not only_eligible or r["eligible_for_index"]) and
               search.casefold() in (r.get("publisher_title") or r["title"]).casefold()]
    st.caption(f"{len(visible)} records match. This search does not change any general or country index.")
    if not visible:
        st.info("No matching articles. Clear the search or include retrieval failures to inspect coverage.")
    else:
        st.dataframe(pd.DataFrame([{"Date": r.get("publication_date"), "Headline": r.get("publisher_title") or r["title"],
            "Source": r["publisher"], "Dictionary balance": r.get("sentiment_score"), "P": r.get("positive_count"),
            "N": r.get("negative_count"), "Eligible": r["eligible_for_index"],
            "Retrieval": r["fetch_status"]} for r in visible]), hide_index=True)
        chosen = st.selectbox("Inspect an article", [r["record_id"] for r in visible], key="inspect_article",
            format_func=lambda identity: next((r.get("publisher_title") or r["title"]) for r in visible if r["record_id"] == identity))
        article_evidence(next(r for r in visible if r["record_id"] == chosen), "news_article")

with quality:
    st.subheader("How can you tell whether the classifications are right?")
    st.write("Inspect the source evidence, record independent human judgments and compare those judgments with the automatic predictions. "
             "A working dashboard or passing software tests cannot establish classification accuracy.")
    q1, q2, q3 = st.columns(3)
    q1.metric("Country pairs reviewed", country_report["reviewed_pairs"])
    q2.metric("Country-label accuracy", "Not measured" if country_report["accuracy"] is None else f"{100*country_report['accuracy']:.1f}%")
    q3.metric("Human sentiment labels", validation["n_labeled"])
    if not country_report["evaluated_pairs"]:
        st.info("Country accuracy has not been measured: no human country reference labels have been supplied. "
                "The review form below records real judgments; no accuracy percentage is filled in automatically.")
    else:
        st.caption(country_report["note"])
        st.json(country_report)
    st.subheader("Classification check: competitor or destination?")
    comparison_cases = [(r, hit) for r in eligible for hit in feature_lookup[r["record_id"]].get("non_destination_evidence", [])]
    if comparison_cases:
        example, hit = next((pair for pair in comparison_cases if pair[0]["record_id"] == "a1348320f184c51f24f5"), comparison_cases[0])
        st.write(example.get("publisher_title") or example["title"])
        st.write(f"**{hit['market']} is not assigned as a destination.** {RULE_LABELS[hit['rule']]}")
        st.link_button("Check this source", example["article_url"])
        st.caption("‘frente a Brasil’ identifies a comparison in this source. This diagnostic is separate from the human reference labels "
                   "and is not an overall accuracy estimate.")
    st.subheader("Review or correct a country assignment")
    review_id = st.selectbox("Article to review", [r["record_id"] for r in eligible], key="review_article",
        format_func=lambda identity: next((r.get("publisher_title") or r["title"]) for r in eligible if r["record_id"] == identity))
    review_article = next(r for r in eligible if r["record_id"] == review_id)
    feature = feature_lookup[review_id]
    suggested = list(dict.fromkeys(feature.get("destinations", [])+feature.get("market_mentions", [])))
    options = [c for c in suggested if c in COUNTRIES]+sorted(set(COUNTRIES)-set(suggested))
    review_country = st.selectbox("Country to check", options, key="review_country")
    st.write(review_article.get("publisher_title") or review_article["title"])
    st.link_button("Read the article before labeling", review_article["article_url"])
    st.caption("Question: is this country discussed as a destination for Colombian goods exports? "
               "Historical, potential or interrupted export links count; competitors or suppliers alone do not. "
               "Make your judgment before opening the automatic explanation.")
    with st.expander("Inspect the automatic explanation after making your judgment"):
        auto = review_country in feature.get("destinations", [])
        st.write("Automatic prediction: destination discussed" if auto else "Automatic prediction: no explicit destination link identified")
        hits = [h for h in feature.get("destination_evidence", [])+feature.get("non_destination_evidence", []) if h["market"] == review_country]
        for hit in hits:
            st.write(RULE_LABELS[hit["rule"]])
        if not hits:
            st.write("A country name alone does not establish export direction. Read the source to resolve the relation.")
    previous = country_reviews.get((review_id, review_country))
    if previous:
        st.caption(f"Saved decision: {previous['decision']} · Reviewer: {previous['reviewer']} · {previous['notes']}")
    with st.form("country_review_form"):
        decision = st.selectbox("Your judgment", ["Choose a decision", "Destination discussed", "Not a destination", "Uncertain"])
        reviewer_name = st.text_input("Reviewer name")
        review_note = st.text_area("Explain the evidence in the source")
        confirmed = st.checkbox("I personally read the source and made this judgment.")
        save = st.form_submit_button("Save country review")
    if save:
        if not confirmed or decision == "Choose a decision":
            st.error("Choose a decision and confirm that you personally reviewed the source.")
        else:
            review = {"record_id": review_id, "country": review_country,
                "decision": {"Destination discussed": "yes", "Not a destination": "no", "Uncertain": "unsure"}[decision],
                "reviewer": reviewer_name.strip(), "annotation_origin": "human", "notes": review_note.strip(), "title_sha256": title_hash(review_article)}
            try:
                save_country_review(DATA, rows, features, review)
            except ValueError as error:
                st.error(str(error))
            else:
                st.rerun()
    with st.expander("Review corpus inclusion and sentiment"):
        st.write("These separate judgments assess whether an article belongs in the goods-export corpus and its overall export-related tone. "
                 "Country labels have their own review form above.")
        reviews = read_reviews(DATA/"annotations.csv")
        frame = pd.DataFrame(list(reviews.values()), columns=REVIEW_FIELDS).fillna("").drop(columns=["activity"])
        with st.form("corpus_review"):
            edited = st.data_editor(frame, hide_index=True, disabled=["record_id", "title", "url", "annotation_origin"],
                column_config={"url": st.column_config.LinkColumn("Read publisher article"),
                    "include": st.column_config.SelectboxColumn("Include", options=["", "yes", "no", "review"]),
                    "sentiment_gold": st.column_config.SelectboxColumn("Optional sentiment label", options=["", "positive", "negative", "neutral"])}, width="stretch")
            confirm = st.checkbox("I personally reviewed the corpus decisions or sentiment labels I am saving.")
            save_corpus = st.form_submit_button("Save corpus review and rebuild")
        if save_corpus:
            if not confirm:
                st.error("Confirm that the saved decisions are your own human review.")
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
    st.caption("Country metrics compare automatic predictions before any human correction with the supplied human article-country labels. "
               "A small convenience review is not a held-out benchmark. Sentiment validation and economic validation are separate tasks.")

with method:
    st.subheader("Construction of the export-news indices")
    st.markdown("Reference: [Mora-Quiñones, Orozco-Gallo & Mora-Pérez (2026), BE1340](https://doi.org/10.32468/be.1340). "
                "The published dictionary and formulas measure lexical news tone. Country extraction is a separate project extension.")
    st.latex(r"SENT_t = \frac{P_t-N_t}{P_t+N_t}")
    st.latex(r"UNCERT_t = 1000\,\frac{U_t}{W_t}")
    st.markdown("**News → Cleaning → Preprocessing → Tokenization → Word counts → Monthly indices**")
    construction = [
        ("1 · Input", "Retrieved publisher article text; ID, publication date, source and URL; one subject: goods exports from Colombia."),
        ("2 · Cleaning", "Remove HTML during extraction; discard cleaned texts with fewer than 50 characters. Keep raw archive hashes."),
        ("3 · Preprocessing", "Segment punctuation, paragraphs, numbered lists and bullets; lowercase and remove frozen Spanish stopwords."),
        ("4 · Tokenization", "Unicode alphabetic tokens; retain sentences with more than five words after stopword removal."),
        ("5 · Word counts", "Count exact published forms: P (188 positive), N (376 negative), U (six uncertainty forms), W (retained words)."),
        ("6 · Monthly output", "Pool counts by publisher publication month; apply the two equations. Missing denominators remain missing."),
    ]
    st.table(pd.DataFrame(construction, columns=["Stage", "Operational rule"]).set_index("Stage"))
    st.caption("Diagram 1 and equations 1–2 provide the measurement rules. The export corpus, public API extraction, "
               "exact tokenizer, NLTK stopword file and trailing moving-average alignment are this project's documented choices.")
    st.write("Article bodies shorter than 50 characters are discarded. After splitting, lowercasing and removing stopwords, "
             "only sentences with more than five remaining words are retained. Exact dictionary matching uses 188 positive and 376 negative forms. "
             "No growth words or inflections are added to force a score.")
    st.write("No polarity matches means a missing sentiment estimate. Equal, nonzero positive and negative counts produce zero. "
             "Words such as ‘duplican’ and ‘triplicaron’ are absent from the reference vocabulary. Negation, context and export-specific language "
             "can therefore cause disagreement with a human reader; inspect the word evidence and supply independent labels.")
    st.write("The paper does not supply its exact tokenizer or stopword file. This implementation freezes NLTK Spanish stopwords and documents "
             "a Unicode tokenizer. The search corpus, public extraction and automatic inclusion rules differ from the Bank's curated corpus. "
             "No econometric forecasting validation has been reproduced.")
    st.subheader("Retrieval outcomes")
    st.dataframe(pd.DataFrame(audit["fetch_status_counts"].items(), columns=["Outcome", "Records"]), hide_index=True)
    st.caption("Google News discovery is non-exhaustive. Only retrieved article text with an explicit publisher publication date can enter the index. "
               "Publisher access, extraction completeness, source mix and dictionary coverage affect the result. Raw publisher bodies remain in the local archive.")
    with st.expander("Monthly discovery status and historical gaps"):
        st.dataframe(pd.DataFrame([{**{k: r.get(k) for k in ["month", "accepted_items", "http_status", "reason"]}, "status": str(r["status"])}
                                  for r in log["requests"]]), hide_index=True)
        st.caption("Google request failures and unattempted months are not evidence of no export news. Analdex is separately logged in collection_log.json.")
