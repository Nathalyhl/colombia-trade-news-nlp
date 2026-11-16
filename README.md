# Colombian Goods Export News: Sentiment & Uncertainty

An independent research project studying Spanish-language news about **exports of Colombian goods to the world from March 2020 onward**. Services and inbound exports to Colombia are outside scope. Source articles remain in Spanish; code, documentation and dashboard are in English.

The project implements the article-text measurement procedure described in [Mora-Quiñones, Orozco-Gallo & Mora-Pérez (2026), Borradores de Economía 1340](https://doi.org/10.32468/be.1340): the published positive/negative dictionary, sentiment and uncertainty formulas, text-length and sentence-length conditions, and economic-activity taxonomy. It is an **adaptation to an export-news corpus**, not the Bank’s official series or a reproduction of its forecasting results.

The main result is a **general monthly export-news index**. Destination countries are a secondary view, with evidence and review tools. There is one subject—exports—rather than a separate export-theme taxonomy.

The **Destinations** tab contains countries only. Select a country to inspect linked articles, whole-article sentiment, uncertainty and the reason for each assignment. **Quality & review** shows actual review status, a corrected real-world error and forms for independent country, corpus and sentiment judgments. There is no economic-activity tab, regional/bloc selector or general geographic-mention mode. See the [country protocol](docs/DESTINATIONS.md).

## Executed historical snapshot

Publication window: **1 March 2020–31 October 2026**; 1 November is excluded. All **80 calendar months** are retained.

| Stage | Records |
| --- | ---: |
| Real discovery candidates | 1374 |
| Retrieved publisher article texts | 840 |
| Eligible, deduplicated texts, provisional scope | 696 |
| Human corpus decisions | 0 |

Google News discovery supplied 730 candidates but encountered HTTP 429 limits. The public **Analdex WordPress archive** supplied 644 separately identified institutional publications. Its public API exposes original publication dates and article content; robots rules permit access. Historical Google links not yet resolved remain retrieval failures, with no headline fallback. These are real source records, not generated observations.

**Coverage is incomplete and the source mix changes over time.** The eligible texts for **2020–2025 currently come only from Analdex**; 2026 adds other publishers. This is not a representative sample of all Colombian press. The dashboard shows monthly source composition and a fixed-source sensitivity comparison using Analdex throughout. All 80 months have provisional estimates, but this does not establish adequate or uniform coverage. Source dates, hashes, retrieval status and monthly pooled counts are inspectable.

Corpus inclusion and country links are automatic proposals pending independent human review. Country and sentiment accuracy remain **not measured**. No official export figures or human judgments were invented. Economic validation is deferred until the researcher supplies the numerical dataset.

## Measurement

For month `t`, pool occurrences over eligible article bodies:

```text
SENT_t   = (P_t - N_t) / (P_t + N_t)
UNCERT_t = 1000 * U_t / W_t
```

`P` and `N` are positive and negative word occurrences from the complete Annex 3 list: **188 positive and 376 negative forms**. `U` counts `incertidumbre`, `incertidumbres`, `incierto`, `inciertos`, `incierta`, `inciertas`; `W` counts processed words. A word can contribute to both uncertainty and negative sentiment if it belongs to both source lists.

No positive/negative matches means **no sentiment estimate**, not neutral. Zero sentiment requires equal, nonzero counts. No articles means no estimate for either measure. The index describes news language, not observed export growth, economic benefit or a validated forecast.

There are no additions for “duplican” or “triplicaron”: neither appears in the published dictionary. Article text supplies more context than a headline, but an unchanged dictionary can still miss export-specific wording. All matched terms and counts are inspectable.

## Run locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
# Activate the environment using your operating system's normal command.
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The dashboard opens the committed snapshot without collecting news. The general index remains fixed while exploring a country or searching article titles.

```bash
# Rebuild decisions and monthly counts from committed article features, offline.
python -m trade_news analyze
python -m trade_news validate

# Prepare or refresh the separate geographic evidence (no fresh web collection).
python -m trade_news destinations

# If this machine has the ignored local article archive, also repeat text NLP.
python -m trade_news analyze --verify-local-text

# Retrieve a NEW snapshot in a separate directory. Public access only.
python -m trade_news collect --start 2020-03-01 --end 2026-11-01 --data-dir data_new
# Separately identified institutional archive supplement.
python -m trade_news publisher-archive --start 2020-03-01 --end 2026-11-01 --data-dir data_new
python -m trade_news fetch --data-dir data_new
python -m trade_news analyze --data-dir data_new

# Software checks and exact feature-aggregate reproduction.
python -m unittest discover -s tests -v
python scripts/check_snapshot.py
```

Google News is a non-exhaustive discovery source. Publisher-reported `datePublished` or `article:published_time` determines the analysis month; an RSS timestamp is never substituted for it. Only retrieved article-body text contributes to the index. A missing body never falls back to its headline. Paywalls, access controls and robots restrictions are not bypassed.

## Academic review and Colab

Start with [methodology](docs/METHODOLOGY.md), [reference comparison](docs/RESEARCH_REFERENCE.md), [snapshot report](docs/SNAPSHOT_REPORT.md), and [human validation protocol](docs/VALIDATION.md). Inspect `trade_news/bank_method.py` for measurement and `trade_news/corpus.py` for corpus decisions and aggregation. Quality & review supports documented human decisions: country labels use `data/destination_reviews.csv`, while corpus inclusion and sentiment use `data/annotations.csv`.

For Colab, upload `Colombia_Trade_News.ipynb`, then upload a ZIP downloaded from this private repository while signed in. The notebook does not request a GitHub token. Its offline cells reproduce the feature aggregates; optional retrieval is disabled by default. Run Streamlit locally for the dashboard.

The repository distributes article metadata, source links, hashes, matched dictionary forms and derived counts. Publisher bodies and HTML stay in the ignored local `data/raw/` archive. This makes the released feature calculations reproducible; repeating text extraction and NLP requires that archive or a new public retrieval, whose contents may change.

The Annex 2 activity vocabulary remains in the reference files for source fidelity and historical compatibility, but its sparse dashboard view has been removed. The source study’s exact tokenizer, stopword file and original curated corpus were not supplied with the paper. We document those implementation choices rather than claiming identical source code. The main chart displays monthly estimates and a trailing three-month mean without imputation; the exact alignment is a documented project choice. Its econometric validation has not been reproduced. See [construction protocol](docs/METHODOLOGY.md), [real diagnostic cases](docs/DIAGNOSTIC_CASES.md) and [related research](docs/RELATED_WORK.md). Third-party dictionary and stopword attribution is in [THIRD_PARTY_NOTICES.md](docs/THIRD_PARTY_NOTICES.md).
