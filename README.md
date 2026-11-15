# Colombian Goods Export News: Sentiment & Uncertainty

An independent research project studying Spanish-language news about **exports of Colombian goods to the world in 2026**. Services and inbound exports to Colombia are outside scope. Source articles remain in Spanish; code, documentation and dashboard are in English.

The project implements the article-text measurement procedure described in [Mora-Quiñones, Orozco-Gallo & Mora-Pérez (2026), Borradores de Economía 1340](https://doi.org/10.32468/be.1340): the published positive/negative dictionary, sentiment and uncertainty formulas, text-length and sentence-length conditions, and economic-activity taxonomy. It is an **adaptation to an export-news corpus**, not the Bank’s official series or a reproduction of its forecasting results.

The main result is a **general monthly export-news index**. Economic activities are a secondary breakdown. There is one subject—exports—rather than a separate export-theme taxonomy.

## Executed snapshot

| Stage | Records |
| --- | ---: |
| Real Google News candidate metadata | 247 |
| Retrieved publisher article texts | 196 |
| Eligible, deduplicated article texts, provisional scope | 172 |
| Human corpus decisions | 0 |

The frozen publication window is **1 January–31 October 2026**, with 1 November excluded. November is incomplete as of the project preparation date, 16 November 2026; December has not occurred. Neither month is filled with zeroes or fabricated news. Retrieval timestamps retain their original UTC values.

The articles are real; corpus inclusion and activities are **automatic proposals pending human review**. The dashboard keeps the provisional series separate from a human-reviewed subset. No human accuracy score exists yet. Access failures, missing publisher dates and exclusions remain visible in the audit.

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

The dashboard opens the committed snapshot without collecting news. The general index remains fixed while exploring an activity or searching article titles.

```bash
# Rebuild decisions and monthly counts from committed article features, offline.
python -m trade_news analyze
python -m trade_news validate

# If this machine has the ignored local article archive, also repeat text NLP.
python -m trade_news analyze --verify-local-text

# Retrieve a NEW snapshot in a separate directory. Public access only.
python -m trade_news collect --start 2026-01-01 --end 2026-11-01 --data-dir data_new
python -m trade_news fetch --data-dir data_new
python -m trade_news analyze --data-dir data_new

# Software checks and exact feature-aggregate reproduction.
python -m unittest discover -s tests -v
python scripts/check_snapshot.py
```

Google News is a non-exhaustive discovery source. Publisher-reported `datePublished` or `article:published_time` determines the analysis month; an RSS timestamp is never substituted for it. Only retrieved article-body text contributes to the index. A missing body never falls back to its headline. Paywalls, access controls and robots restrictions are not bypassed.

## Academic review and Colab

Start with [methodology](docs/METHODOLOGY.md), [reference comparison](docs/RESEARCH_REFERENCE.md), [snapshot report](docs/SNAPSHOT_REPORT.md), and [human validation protocol](docs/VALIDATION.md). Inspect `trade_news/bank_method.py` for measurement and `trade_news/corpus.py` for corpus decisions and aggregation. `data/annotations.csv` and the dashboard’s Human review tab support documented manual decisions.

For Colab, upload `Colombia_Trade_News.ipynb`, then upload a ZIP downloaded from this private repository while signed in. The notebook does not request a GitHub token. Its offline cells reproduce the feature aggregates; optional retrieval is disabled by default. Run Streamlit locally for the dashboard.

The repository distributes article metadata, source links, hashes, matched dictionary forms and derived counts. Publisher bodies and HTML stay in the ignored local `data/raw/` archive. This makes the released feature calculations reproducible; repeating text extraction and NLP requires that archive or a new public retrieval, whose contents may change.

The source study’s exact tokenizer, stopword file and original curated corpus were not supplied with the paper. We document those implementation choices rather than claiming identical source code. Its econometric validation is outside this ten-month implementation. Third-party dictionary and stopword attribution is in [THIRD_PARTY_NOTICES.md](docs/THIRD_PARTY_NOTICES.md).
