# Colombia Goods Export Sentiment Observatory

An exploratory NLP project measuring news sentiment about **exports of Colombian goods to the world**. It collects real Spanish-language headline metadata, identifies goods, export themes, sectors and explicit market mentions, and presents a monthly **Export News Sentiment Index** in an interactive dashboard. Services are outside the analysis scope.

The project connects data collection, text processing, interpretable NLP, aggregation, evaluation and research communication in one reproducible workflow. The interface and documentation are in English; source headlines remain in Spanish.

## Explore the project

| Component | Start here |
| --- | --- |
| Guided analysis in Google Colab or Jupyter | [Research notebook](Colombia_Trade_News.ipynb) |
| Interactive dashboard | [app.py](app.py) |
| Collection and text-analysis code | [trade_news](trade_news) |
| Research design and index formula | [Methodology](docs/METHODOLOGY.md) |
| Banco de la República reference and adaptation choices | [Research reference](docs/RESEARCH_REFERENCE.md) |
| Real data, query history and field definitions | [Data sources](docs/DATA_SOURCES.md) |
| Reference-label review and evaluation | [Validation guide](docs/VALIDATION.md) |
| Executed work and next research steps | [Project status](docs/PROJECT_STATUS.md) |
| Descriptive outputs of the executed snapshot | [Snapshot report](docs/SNAPSHOT_REPORT.md) |

## Included real snapshot

The export-specific collection was executed on **15 November 2026**, querying **May–October 2026**. It retained **152 real candidate metadata records**. The goods-and-origin baseline selects **63** headlines, holds **33** for review and excludes **56**. Every candidate preserves a source link, publisher, provider date, collection time and search URL. Only included goods-export headlines enter the index; the search sample is not a complete inventory of Colombian export news.

The scope requires an explicit export cue, a phrase linking exports to Colombian origin and an explicit goods cue. Imports, inbound exports to Colombia and services do not enter the index. Unspecified goods, unresolved direction and mixed goods/services headlines are held for review.

The baseline keeps its decisions inspectable: the exact words behind every topic, sector, partner and sentiment cue are stored with each headline. The dashboard supports month, sector, partner, theme and text filters, recalculates the index after filtering, and displays volume, tone coverage, source links and quality information.

**Research reference:** the primary index adopts the pooled positive/negative balance formula from [Mora-Quiñones, Orozco-Gallo and Mora-Pérez (2026), Borradores de Economía 1340](https://doi.org/10.32468/be.1340). This is an independent adaptation using headlines, a different provisional lexicon and explicit goods-export filters. It does not reproduce the Bank’s series or predictive results.

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

1. Retrieve export-related Google News RSS search results in explicit month windows; log requests, failures and raw-response hashes.
2. Validate metadata, normalize accents/case, remove exact URLs or normalized-headline duplicates, and audit exclusions.
3. Apply transparent Spanish phrase dictionaries and a cue-based sentiment baseline, preserving matched evidence.
4. Pool positive and negative cue occurrences by month/group: `(positive - negative) / (positive + negative)`, from −1 to +1. Retain an equal-publisher tone score separately for sensitivity analysis; show coverage with both measures.
5. Review relevance, sentiment and multi-label tags against human references using the supplied annotation sheet and metrics.
6. Explore trends, comparisons and individual decisions in the dashboard; retain the source trail for academic discussion.

No publisher articles are scraped. No API keys, database passwords, original thesis code or private trade databases are required. News metadata remains subject to source rights; the repository does not claim ownership of publisher material. Keep the repository private while deciding what to share for academic review. A viewer who can read repository code can also copy it.
