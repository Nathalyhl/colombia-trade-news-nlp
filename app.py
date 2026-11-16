"""Inspect the general export-news index before optional activity breakdowns."""
import csv
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from trade_news.articles import read_jsonl
from trade_news.classification import ACTIVITIES
from trade_news.corpus import REVIEW_FIELDS, build, read_reviews
from trade_news.destinations import coverage, monthly_series, select_articles

BASE = Path(__file__).resolve().parent
DATA = BASE/"data"
st.set_page_config(page_title="Colombian Goods Export News", page_icon="🇨🇴", layout="wide")


def load_json(name):
    return json.loads((DATA/name).read_text("utf8"))


def index_chart(frame, column, title, bounds=None):
    fig = go.Figure(go.Scatter(x=frame["month"], y=frame[column], mode="lines+markers", connectgaps=False,
        customdata=frame[["articles", "publishers"]],
        hovertemplate="%{x}<br>Value: %{y:.3f}<br>Articles: %{customdata[0]}<br>Publishers: %{customdata[1]}<extra></extra>"))
    fig.update_layout(title=title, xaxis_title="Publication month", yaxis_title=column.replace("_", " "), height=340)
    if bounds:
        fig.update_yaxes(range=bounds, zeroline=True)
    return fig


rows = read_jsonl(DATA/"headlines.jsonl")
indices, audit, log, validation = [load_json(name) for name in
    ["indices.json", "processing_audit.json", "collection_log.json", "validation_report.json"]]
st.caption("COLOMBIAN GOODS EXPORTS TO THE WORLD · 2026 · ARTICLE-TEXT NLP")
st.title("Export News Sentiment & Uncertainty")
st.write("A general monthly reading of the language used in news about Colombian goods exports. "
         "Activity breakdowns are available separately, following the reference study’s categories.")
st.caption(f"Publication window: {log['start']} to {log['end_exclusive']} (exclusive). "
           "The frozen snapshot covers January–October; November and December are not estimated.")
st.info("Provisional research series. Corpus inclusion and economic activities are automatic proposals pending human review. "
        "The formulas and 564-word dictionary follow Banco de la República, BE1340. This is an independent adaptation, not an official Bank index.")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Eligible article texts", audit["eligible_articles"])
c2.metric("Retrieved article texts", audit["extracted_articles"])
c3.metric("Candidate news records", audit["candidate_records"])
c4.metric("Human decisions recorded", audit["human_reviewed_articles"])
general, activities, destinations_tab, evidence, method, review_tab = st.tabs(
    ["General index", "Economic activities", "Destinations", "Articles & evidence", "Method & coverage", "Human review"])

with general:
    series = pd.DataFrame([r for r in indices["provisional"] if r["activity"] == "All exports"])
    st.subheader("All Colombian goods export news in the eligible sample")
    st.write("Sentiment pools positive and negative word occurrences across articles each month. "
             "Uncertainty counts the six published uncertainty forms per 1,000 processed words.")
    left, right = st.columns(2)
    left.plotly_chart(index_chart(series, "sentiment", "Monthly sentiment", [-1.05, 1.05]), width="stretch")
    right.plotly_chart(index_chart(series, "uncertainty_per_1000", "Monthly uncertainty"), width="stretch")
    st.caption("Gaps mean no estimate. Zero sentiment requires equal nonzero positive and negative counts; "
               "zero uncertainty is possible when processed text contains none of the six uncertainty forms.")
    st.dataframe(series[["month", "articles", "publishers", "positive_count", "negative_count", "uncertainty_count",
                         "processed_tokens", "sentiment", "uncertainty_per_1000", "status"]], hide_index=True)
    reviewed = pd.DataFrame([r for r in indices["human_reviewed"] if r["activity"] == "All exports"])
    if reviewed["articles"].sum():
        st.plotly_chart(index_chart(reviewed, "sentiment", "Human-reviewed subset", [-1.05, 1.05]), width="stretch")
        st.caption("This subset uses the same formulas. It may differ in size and composition from the provisional series.")
    else:
        st.warning("The human-reviewed series will appear after corpus review.")

with activities:
    st.subheader("Economic activities: a secondary view")
    st.write("The reference study uses 18 economic-activity labels. Several activities in one article map to Global Context. "
             "Foreign-trade articles without a resolved activity map to Other Activity. The study used manual classification; "
             "these project proposals require review.")
    selected = st.selectbox("Economic activity (Annex 2)", ACTIVITIES)
    activity_rows = [r for r in indices["provisional"] if r["activity"] == selected]
    activity_lookup = {r["month"]: r for r in activity_rows}
    empty = {"articles": 0, "publishers": 0, "sentiment": None, "uncertainty_per_1000": None}
    activity_frame = pd.DataFrame([{**empty, **activity_lookup.get(month, {}), "month": month} for month in series["month"]])
    if activity_frame["articles"].sum():
        st.plotly_chart(index_chart(activity_frame, "sentiment", selected, [-1.05, 1.05]), width="stretch")
        st.dataframe(activity_frame, hide_index=True)
    else:
        st.info("No eligible article is currently assigned to this activity. The general index above is unchanged.")

with destinations_tab:
    st.subheader("Explore export news by destination")
    st.write("Compare news coverage, sentiment and uncertainty for a country, region or bloc. "
             "Destination links are automatic proposals; broader geographic mentions are available separately.")
    destination_path = DATA/"destinations.jsonl"
    if not destination_path.exists():
        st.info("Destination evidence is not available for this snapshot. Run python -m trade_news destinations to prepare it.")
    else:
        destination_features = read_jsonl(destination_path)
        evidence_choice = st.radio("Destination evidence", ["Explicit export links in headlines", "All market mentions in article text"],
                                   horizontal=True, key="destination_mode")
        destination_mode = "destinations" if evidence_choice == "Explicit export links in headlines" else "market_mentions"
        geography_kind = st.radio("Geography", ["Countries", "Regions and blocs", "All"], horizontal=True, key="destination_kind")
        st.caption("Automatic geographic evidence. Counts describe news coverage, not export values. "
                   "The broader mention mode can also identify suppliers, competitors or policy actors.")
        overview = coverage(rows, destination_features, destination_mode, geography_kind)
        destination_lookup = {r["record_id"]: r for r in destination_features}
        linked_articles = sum(bool(destination_lookup.get(r["record_id"], {}).get(destination_mode))
                              for r in rows if r["eligible_for_index"])
        if not overview:
            st.info("No markets match this evidence mode and geography group. Try Countries or the broader market-mention mode.")
        else:
            destination_market = st.selectbox("Destination or market", [r["market"] for r in overview], key="destination_market")
            selected_articles = select_articles(rows, destination_features, destination_market, destination_mode)
            overview_frame = pd.DataFrame(overview)
            overview_chart = go.Figure(go.Bar(x=overview_frame.head(15)["articles"], y=overview_frame.head(15)["market"], orientation="h"))
            overview_chart.update_layout(title="News coverage by market · top 15", xaxis_title="Eligible articles", yaxis_title="",
                                         yaxis={"autorange": "reversed"}, height=430)
            st.subheader(destination_market)
            d1, d2, d3 = st.columns(3)
            d1.metric("Articles in this market view", len(selected_articles))
            d2.metric("Publishers in this market view", len({r["publisher"] for r in selected_articles}))
            d3.metric("Articles with polarity matches", sum(r["positive_count"]+r["negative_count"] > 0 for r in selected_articles))
            destination_frame = pd.DataFrame(monthly_series(rows, destination_features, destination_market, series["month"].tolist(), destination_mode))
            dl, dr = st.columns(2)
            dl.plotly_chart(index_chart(destination_frame, "sentiment", f"{destination_market}: article sentiment", [-1.05, 1.05]),
                            width="stretch", key="destination_sentiment")
            dr.plotly_chart(index_chart(destination_frame, "uncertainty_per_1000", f"{destination_market}: article uncertainty"),
                            width="stretch", key="destination_uncertainty")
            st.caption("These indices pool the entire eligible article texts in this subset using the same formulas as the general index. "
                       "They do not isolate sentences about this destination. Gaps remain missing; the general index is unchanged.")
            st.dataframe(destination_frame[["month", "articles", "publishers", "positive_count", "negative_count", "sentiment", "uncertainty_per_1000"]],
                         hide_index=True)
            destination_table = []
            evidence_key = "destination_evidence" if destination_mode == "destinations" else "mention_evidence"
            for article in selected_articles:
                matches = [hit for hit in destination_lookup[article["record_id"]][evidence_key] if hit["market"] == destination_market]
                destination_table.append({"title": article.get("publisher_title") or article["title"],
                    "publication_date": article["publication_date"], "publisher": article["publisher"], "activity": article["activity"],
                    "evidence_source": ", ".join(sorted({hit["field"] for hit in matches})),
                    "matched_names": ", ".join(sorted({hit["alias"] for hit in matches})),
                    "relation_rule": ", ".join(sorted({hit.get("rule", "geographic_mention_only") for hit in matches})),
                    "article_url": article["article_url"]})
            st.subheader("Source articles and geographic evidence")
            st.dataframe(pd.DataFrame(destination_table), hide_index=True,
                         column_config={"article_url": st.column_config.LinkColumn("Read publisher article")})
            with st.expander("Compare news coverage across markets"):
                st.plotly_chart(overview_chart, width="stretch", key="destination_coverage")
                st.caption(f"Across the eligible corpus, {linked_articles} articles have evidence in this mode; "
                           f"{audit['eligible_articles']-linked_articles} have no identified market in this mode. "
                           "A missing tag is not evidence that a destination is absent from Colombian exports. "
                           "Articles can appear under several markets, so market totals overlap. No bloc membership is inferred.")
            with st.expander("Supported countries, regions and aliases"):
                from trade_news.destinations import MARKETS, COUNTRIES
                st.dataframe(pd.DataFrame([{"market": name, "kind": "country" if name in COUNTRIES else "region_or_bloc",
                    "aliases": ", ".join(aliases)} for name, aliases in MARKETS.items()]), hide_index=True)
                st.caption("This finite project vocabulary is not a complete geography recognizer. Unlisted names and ambiguous relations can be missed. "
                           "No destination has been manually certified by these automatic rules.")

with evidence:
    st.subheader("Trace each estimate to its articles and matched words")
    search = st.text_input("Find words in an article title")
    only_eligible = st.checkbox("Show only eligible articles", value=True)
    visible = [r for r in rows if (not only_eligible or r["eligible_for_index"]) and
               search.casefold() in (r.get("publisher_title") or r["title"]).casefold()]
    st.caption(f"{len(visible)} matching records. Search changes this table only; it does not change the general index.")
    if not visible:
        st.info("No matching articles. Clear the search or include retrieval failures to inspect coverage.")
    else:
        columns = ["record_id", "title", "publication_date", "publisher", "article_url", "fetch_status", "scope_proposal",
                   "activity", "review_status", "eligible_for_index", "positive_count", "negative_count", "sentiment_score"]
        table = pd.DataFrame(visible).reindex(columns=columns)
        st.dataframe(table, hide_index=True, column_config={"article_url": st.column_config.LinkColumn("Publisher article")})
        chosen = st.selectbox("Inspect a record", [r["record_id"] for r in visible],
                              format_func=lambda key: next((r.get("publisher_title") or r["title"]) for r in visible if r["record_id"] == key))
        item = next(r for r in visible if r["record_id"] == chosen)
        st.json({k: item.get(k) for k in ["article_url", "publication_date", "date_source", "text_source", "text_sha256",
            "processing_status", "processed_tokens", "matched_terms", "uncertainty_count", "scope_reason", "goods_evidence",
            "activity_evidence", "duplicate_of", "fetch_error", "resolution_error"]})

with method:
    st.subheader("What follows the paper, and what changes")
    st.markdown("Reference: [Mora-Quiñones, Orozco-Gallo & Mora-Pérez (2026), BE1340](https://doi.org/10.32468/be.1340). "
                "See the repository methodology for the implementation matrix and source attribution.")
    st.latex(r"SENT_t = \frac{P_t-N_t}{P_t+N_t}")
    st.latex(r"UNCERT_t = 1000\,\frac{U_t}{W_t}")
    st.write("The article-body pipeline discards texts shorter than 50 characters, splits sentences, lowercases, removes stopwords, "
             "and retains sentences with more than five remaining words. Matching uses the complete published Annex 3 dictionary: "
             "188 positive and 376 negative forms. No extra inflections, automatic negation reversal or growth-word additions are used.")
    st.write("The paper does not supply its exact tokenizer or stopword file. This implementation documents its Unicode tokenizer "
             "and freezes the 313-word NLTK Spanish stopword file. Google News retrieval, public web extraction and automatic "
             "scope/activity proposals also differ from the Bank’s manually curated corpus. The paper’s nowcasting models are not reproduced.")
    st.write("‘Duplican’ and ‘triplicaron’ are not in Annex 3. An article may still receive a score from other published dictionary terms "
             "in its body. No matches means no sentiment estimate, rather than a neutral score. News tone is not export growth or a forecast.")
    st.subheader("Retrieval coverage")
    st.dataframe(pd.DataFrame(audit["fetch_status_counts"].items(), columns=["Retrieval outcome", "Records"]), hide_index=True)
    st.caption("Search results are not an exhaustive or representative news census. Publisher access, extraction and dictionary coverage "
               "affect the series. Full publisher text is kept in the ignored local archive; the repository distributes links, hashes and derived counts.")
    st.json(validation)

with review_tab:
    st.subheader("Record a human corpus review")
    st.write("Read the linked publisher article. Decide whether it concerns Colombian goods exports, assign one Annex 2 activity, "
             "and identify the reviewer. Leave uncertain cases as review. Sentiment reference labels are optional and must be your own judgments.")
    reviews = read_reviews(DATA/"annotations.csv")
    if not reviews:
        st.info("No full-text article is available to review.")
    else:
        frame = pd.DataFrame(list(reviews.values()), columns=REVIEW_FIELDS).fillna("")
        with st.form("corpus_review"):
            edited = st.data_editor(frame, hide_index=True, disabled=["record_id", "title", "url", "annotation_origin"],
                column_config={"url": st.column_config.LinkColumn("Read publisher article"),
                    "include": st.column_config.SelectboxColumn("Include", options=["", "yes", "no", "review"]),
                    "activity": st.column_config.SelectboxColumn("Activity", options=[""]+ACTIVITIES),
                    "sentiment_gold": st.column_config.SelectboxColumn("Optional sentiment label", options=["", "positive", "negative", "neutral"])},
                width="stretch")
            confirm = st.checkbox("I personally reviewed the decisions or reference labels I am saving.")
            save = st.form_submit_button("Save human review and rebuild")
        if save:
            if not confirm:
                st.error("Confirm that the saved decisions are your own human review.")
            else:
                pending = edited.fillna("").to_dict("records")
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
                    st.success("Human review saved; monthly estimates rebuilt.")
                    st.rerun()
