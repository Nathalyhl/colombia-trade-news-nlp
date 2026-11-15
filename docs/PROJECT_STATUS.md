# Project status

## Implemented snapshot

The project now focuses on **exports of Colombian goods to the world**. The export-specific live retrieval on 15 November 2026 queried May–October 2026 and retained 152 real candidate metadata records. The headline baseline includes 63, holds 33 for review and excludes 56. Raw candidates are preserved for audit; only included goods-export records enter indices and dashboard trends.

The implementation contains real-news collection, provenance, deduplication, explicit goods/origin checks, interpretable NLP, matched evidence, monthly/group sentiment, a Streamlit dashboard, a Colab/Jupyter notebook and human-reference evaluation tools.

The primary index uses the pooled polarity-balance formula from the Banco de la República reference study. The corpus, lexicon and processing differ; this is an independent methodological adaptation. The earlier equal-publisher score is retained separately for sensitivity analysis. See [RESEARCH_REFERENCE.md](RESEARCH_REFERENCE.md).

## Research work still pending

Human reference annotation and classification accuracy remain pending. No original Bank lexicon or series has been reproduced, no full-article NLP has been performed, and no export forecast or predictive improvement is claimed. A comparison with official DANE goods-export statistics requires more historical coverage and a dated out-of-sample design. A hosted dashboard has not been deployed.

The notebook has no saved execution outputs. The included JSON/JSONL files preserve the executed pipeline snapshot. Software tests cover export direction, goods/services distinctions, abstentions, pooled cue counts, source weighting, scope audits and dashboard filters; passing tests does not establish domain accuracy.

Local verification of this version: **38 software tests passed**, along with the deterministic snapshot rebuild and Ruff checks. The offline notebook analysis cells also execute using the included real snapshot.

The prior broad-trade snapshot remains available in repository history and a local backup. It is not mixed into the current goods-export index.
