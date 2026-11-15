# Colombia Trade News Observatory

An exploratory NLP project on Colombian foreign trade and its relationships with the world. It collects real Spanish-language headline metadata, identifies commercial themes and explicit sector/partner mentions, computes a monthly **Headline Tone Index**, and exposes the results in an interactive dashboard.

The project connects data collection, text processing, interpretable NLP, aggregation, evaluation and research communication in one reproducible workflow. The interface and documentation are in English; source headlines remain in Spanish.

## Explore the project

| Component | Start here |
| --- | --- |
| Guided analysis in Google Colab or Jupyter | [Research notebook](Colombia_Trade_News.ipynb) |
| Interactive dashboard | [app.py](app.py) |
| Collection and text-analysis code | [trade_news](trade_news) |
| Research design and index formula | [Methodology](docs/METHODOLOGY.md) |
| Real data, query history and field definitions | [Data sources](docs/DATA_SOURCES.md) |
| Reference-label review and evaluation | [Validation guide](docs/VALIDATION.md) |
| Executed work and next research steps | [Project status](docs/PROJECT_STATUS.md) |

## Included real snapshot

The initial collection was executed on **15 November 2026**, querying six complete calendar months: **May–October 2026**. It retained **160 real metadata records**, of which **127** satisfy the initial headline relevance rules. Every record preserves a source link, publisher, provider date, collection time and search URL. These are a retrieved search sample, not a complete inventory of Colombian trade news.

The baseline keeps its decisions inspectable: the exact words behind every topic, sector, partner and sentiment cue are stored with each headline. The dashboard supports month, sector, partner, theme and text filters, recalculates the index after filtering, and displays volume, tone coverage, source links and quality information.

**Research interpretation:** the index describes lexical tone in this sample. It does not measure trade performance or predict the Colombian economy. Classification quality awaits human reference labels; no accuracy score or benchmark result is invented. This is an operational research baseline, with evaluation tools ready for the next stage.

## Run locally

Use Python 3.11 or later. From this repository directory:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The dashboard opens the included snapshot without making network requests. The collection, NLP and evaluation modules use only the Python standard library; pandas, Plotly and Streamlit support exploration and presentation.

```bash
# Rebuild the included analysis offline (preserves existing annotation work).
python -m trade_news analyze
python -m trade_news validate

# Collect a NEW real snapshot into a separate directory; end date is exclusive.
python -m trade_news all --start 2026-05-01 --end 2026-11-01 --data-dir data_new

# Software and snapshot checks, without live collection.
python -m unittest discover -s tests -v
python scripts/check_snapshot.py
```

To replace the dashboard snapshot, first inspect a new collection's log and results, then copy its reviewed data files into `data/`. Search responses change over time; recollection is not expected to reproduce the original corpus byte for byte.

## Use Google Colab

Open [Colab](https://colab.research.google.com/), choose **Upload**, and select `Colombia_Trade_News.ipynb`. Download this private repository as a ZIP while signed in to GitHub, then upload that ZIP when the notebook asks. This avoids putting a GitHub token in notebook cells. The notebook reads the real snapshot, runs the same pipeline, plots monthly trends and provides an optional fresh-collection cell.

Colab supports the analysis workflow. Run the Streamlit dashboard locally using the command above; a hosted dashboard has not been deployed by this repository.

## Research workflow

1. Retrieve Google News RSS search results in explicit month windows; log requests, failures and raw-response hashes.
2. Validate metadata, normalize accents/case, remove exact URLs or normalized-headline duplicates, and audit exclusions.
3. Apply transparent Spanish phrase dictionaries and a cue-based sentiment baseline, preserving matched evidence.
4. Aggregate scored headlines within publishers, then average publishers equally; report sample coverage alongside the index.
5. Review relevance, sentiment and multi-label tags against human references using the supplied annotation sheet and metrics.
6. Explore trends, comparisons and individual decisions in the dashboard; retain the source trail for academic discussion.

No publisher articles are scraped. No API keys, database passwords, original thesis code or private trade databases are required. News metadata remains subject to source rights; the repository does not claim ownership of publisher material. Keep the repository private while deciding what to share for academic review. A viewer who can read repository code can also copy it.
