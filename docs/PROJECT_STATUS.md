# Project status

## Implemented and executed

- Live monthly Google News RSS collection for May–October 2026, executed on 15 November 2026.
- 160 metadata records; 127 retained as relevant by the initial rules. All six feed requests succeeded. No synthetic headlines are mixed into the corpus.
- Metadata validation, exact deduplication, inspectable Spanish NLP rules, matched evidence and source-balanced monthly/group index calculations.
- A snapshot-first Streamlit dashboard with filters, trends, source links and method/coverage information.
- A Colab/Jupyter notebook, blank reference-label review sample, per-task evaluator, software tests and deterministic snapshot checks.
- Local verification: 27 tests passed, including dashboard/filter/empty-result checks; deterministic snapshot rebuild and Ruff checks passed. These are implementation checks, not human classification metrics.

## Research decisions still requiring review

Human reference annotation and domain accuracy remain pending. Theme dictionaries, sector coverage, partner aliases, cue weights, relevance rules and minimum coverage thresholds are initial methodological choices. The index is a descriptive lexical baseline, not an established economic indicator.

No learned model has been trained or evaluated, no full-article NLP has been performed, and no causal or predictive economic finding is claimed. A hosted dashboard has not been deployed. The notebook is provided without saved execution outputs; the included JSON/JSONL files preserve the executed pipeline snapshot.

## Suggested next session

Review the 40-row annotation sample, run the evaluator, discuss actual errors, and freeze a first evaluated baseline before expanding collection or comparing with a Spanish pretrained model. This makes the next academic claim depend on observed evidence rather than presentation polish.
