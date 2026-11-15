"""Snapshot-first dashboard; filters recompute the source-balanced index."""
from collections import Counter
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from trade_news.pipeline import aggregate, read_jsonl

st.set_page_config(page_title="Colombia | Trade News Observatory", page_icon="🌎", layout="wide")
BASE = Path(__file__).resolve().parent / "data"


def load_json(name):
    return json.loads((BASE / name).read_text("utf8"))


st.caption("COLOMBIA · INTERNATIONAL TRADE · EXPLORATORY NLP")
st.title("Trade News Observatory")
st.markdown("Explore how Spanish-language headlines frame Colombia’s trade with the world. "
            "Follow monthly tone, commercial themes and explicitly mentioned sectors and partners.")
if not (BASE / "headlines.jsonl").exists():
    st.info("Collect a real snapshot first: python -m trade_news all")
    st.stop()
rows = read_jsonl(BASE / "headlines.jsonl")
log, audit, report = (load_json(n) for n in ["collection_log.json", "processing_audit.json", "validation_report.json"])
months = [r["month"] for r in log["requests"]]
relevant = [r for r in rows if r["relevant"]]
st.caption(f"Provider-date window: {log['start']} to {log['end_exclusive']} (exclusive) · "
           f"Retrieved {log['requests'][-1]['retrieved_at'][:10]} · Google News RSS metadata")

with st.sidebar:
    st.header("Explore the snapshot")
    selected_months = st.multiselect("Months", months, default=months)
    def options(field):
        return sorted({v for r in relevant for v in r[field]})
    sectors = st.multiselect("Sectors mentioned", options("sectors"))
    partners = st.multiselect("Partners mentioned", options("partners"))
    themes = st.multiselect("Commercial themes", options("themes"))
    search = st.text_input("Find words in a headline")
    st.caption("Choices within one filter mean OR; different filters mean AND. "
               "Partner mentions do not establish a bilateral trade flow.")

filtered = [r for r in relevant if r["month"] in selected_months
            and (not sectors or set(sectors) & set(r["sectors"]))
            and (not partners or set(partners) & set(r["partners"]))
            and (not themes or set(themes) & set(r["themes"]))
            and search.casefold() in r["title_clean"].casefold()]
scored = [r for r in filtered if r["tone_score"] is not None]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Relevant headlines", len(filtered))
c2.metric("Publishers", len({r["publisher"] for r in filtered}))
c3.metric("Scored headlines", len(scored))
c4.metric("Lexicon coverage", f"{len(scored)/len(filtered):.0%}" if filtered else "—")
st.info("Research baseline: the Headline Tone Index measures lexical tone in this retrieved sample, "
        "not economic performance. Human classification review is pending." if report["status"] == "human_labels_pending"
        else "Research baseline: the index measures sample headline tone. See Quality & method for reference-label evaluation.")
trends, explore, quality = st.tabs(["Trends", "Headlines & evidence", "Quality & method"])

with trends:
    monthly = pd.DataFrame([r for r in aggregate(filtered, selected_months) if r["dimension"] == "overall"])
    if monthly.empty:
        st.info("Choose at least one month to explore trends.")
    else:
        figure = px.line(monthly, x="month", y="headline_tone_index", markers=True,
                         title="Monthly Headline Tone Index", range_y=[-105, 105],
                         hover_data=["n_records", "n_scored", "n_scored_publishers", "status"],
                         labels={"month": "Provider publication month", "headline_tone_index": "Source-balanced tone (−100 to +100)"})
        figure.update_traces(connectgaps=False)
        figure.add_hline(y=0, line_dash="dot", line_color="gray")
        st.plotly_chart(figure, width="stretch")
        st.caption("Each scored publisher has equal weight within a month. A point requires at least "
                   "3 scored headlines from 2 publishers; missing values remain gaps. All points are provisional.")
        left, right = st.columns(2)
        with left:
            st.plotly_chart(px.bar(monthly, x="month", y="n_records", title="Retrieved relevant headline volume",
                                  labels={"month": "Month", "n_records": "Headlines"}), width="stretch")
        with right:
            counts = Counter(r["sentiment"] for r in filtered)
            tone = pd.DataFrame([{"label": k, "count": counts[k]} for k in ["positive", "neutral", "negative", "unscored"]])
            st.plotly_chart(px.bar(tone, x="label", y="count", title="Lexical tone and abstentions",
                                  color="label", color_discrete_map={"positive": "#167d6d", "neutral": "#788496", "negative": "#bb5462", "unscored": "#d8ae5e"}), width="stretch")
    for field, title in [("themes", "Commercial themes"), ("sectors", "Sectors mentioned"), ("partners", "Partners mentioned")]:
        counts = Counter(v for r in filtered for v in r[field])
        if counts:
            table = pd.DataFrame(counts.most_common(), columns=["label", "headlines"])
            st.plotly_chart(px.bar(table, x="headlines", y="label", orientation="h", title=title), width="stretch")
    st.caption("A headline may have several tags, so tag totals can exceed the number of headlines.")
    st.subheader("Compare tone by sector or partner")
    dimension = st.selectbox("Comparison dimension", ["sector", "partner", "theme"])
    comparisons = [r for r in aggregate(filtered, selected_months) if r["dimension"] == dimension]
    st.dataframe(pd.DataFrame(comparisons), hide_index=True, width="stretch")

with explore:
    st.write("Open the source link and inspect the words behind each classification.")
    display = [{"Date (UTC)": r["published_at"][:10], "Headline": r["title_clean"], "Publisher": r["publisher"],
                "Tone": r["sentiment"], "Score": r["tone_score"], "Themes": ", ".join(r["themes"]),
                "Sectors": ", ".join(r["sectors"]), "Partners": ", ".join(r["partners"]), "Source": r["url"], "ID": r["record_id"]} for r in filtered]
    st.dataframe(pd.DataFrame(display), column_config={"Source": st.column_config.LinkColumn("Source", display_text="Open source")}, hide_index=True, width="stretch")
    if filtered:
        selected_id = st.selectbox("Inspect an individual headline", [r["record_id"] for r in filtered],
                                   format_func=lambda rid: next(r["title_clean"] for r in filtered if r["record_id"] == rid))
        record = next(r for r in filtered if r["record_id"] == selected_id)
        st.json({k: record[k] for k in ["title_clean", "sentiment", "tone_score", "sentiment_evidence", "tag_evidence", "date_origin"]})

with quality:
    st.subheader("From a real search response to an inspectable result")
    st.write(f"{audit['input_records']} metadata records → {audit['retained_records']} retained → "
             f"{audit['relevant_records']} selected by the relevance baseline. "
             f"Duplicates removed: {len(audit['duplicates'])}; invalid metadata: {len(audit['rejected_metadata'])}.")
    st.dataframe(pd.DataFrame([{k: r.get(k) for k in ["month", "status", "provider_items", "accepted_items", "rejected_items", "possible_provider_cap"]} for r in log["requests"]]), hide_index=True, width="stretch")
    st.markdown("**Method.** Accent-insensitive phrase matching assigns topics, sectors and partner mentions. "
                "A small Spanish lexicon scores positive and negative cues, with a three-token negation window. "
                "Headlines with no cue are **unscored**, not neutral. The index averages scores within each publisher, "
                "then averages publishers and multiplies by 100.")
    st.markdown("**Interpretation.** Search results are a changing, non-exhaustive sample. Dates come from RSS and "
                "are not independently verified publication dates. A positive word can describe an adverse economic "
                "event (for example, rising tariffs). Headline tone and economic favorability need separate human judgments.")
    st.subheader("Human reference-label evaluation")
    st.json(report)
    st.write("Review data/annotations.csv using docs/VALIDATION.md, then run python -m trade_news validate. "
             "No accuracy score is reported before reference labels exist. Reviewers can assess relevance, tone and all tag families.")
    st.caption("The repository contains collection provenance, annotation instructions and reproducibility steps.")
