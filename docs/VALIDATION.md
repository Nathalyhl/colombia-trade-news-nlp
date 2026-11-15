# Annotation and validation protocol

## Current state

No human reference labels have been supplied. `data/validation_report.json` therefore records `human_labels_pending`, zero labeled records and null metrics. Program tests are software checks, not a benchmark score. This distinction lets the project present working analysis without inventing its research validity.

## Review the sample

`data/annotations.csv` contains up to 40 records selected by sorting SHA-256 hashes of retained record IDs. This deterministic convenience sample includes both relevance-positive and relevance-negative predictions; it is not a held-out test set or representative of all news. The sheet omits predicted labels to reduce anchoring. Preserve record IDs and provenance.

For each reviewed row, provide a named reviewer or stable reviewer ID in `annotator` and set `annotation_origin` to `human`. The software checks these declarations but cannot verify that a person performed the annotation. Never copy predictions into reference columns or label model-generated judgments as human.

| Reference column | Allowed content | Review definition |
| --- | --- | --- |
| `relevance_gold` | `yes`, `no`, or blank | Does the headline concern goods exported from Colombia to foreign markets, including their outlook or restrictions? Services, imports, inbound foreign exports and unresolved goods/origin are outside scope. |
| `sentiment_gold` | `positive`, `negative`, `neutral`, or blank | Overall linguistic tone of the headline; do not substitute inferred economic benefit. Neutral means no clear positive/negative tone or balanced tone. |
| `themes_gold` | Exact keys from `THEMES`, separated by `|`; `-` for no tag; blank for unreviewed | All supported export themes explicitly present |
| `sectors_gold` | Exact keys from `SECTORS`, separated by `|`; `-` for no tag; blank for unreviewed | All supported sectors explicitly present |
| `partners_gold` | Exact keys from `PARTNERS`, separated by `|`; `-` for no tag; blank for unreviewed | All supported country/bloc mentions explicitly present |

Vocabulary keys and the full dictionaries are in `trade_news/nlp.py`. An unsupported country or sector should not be forced into an existing label. Record proposed new categories in separate review notes and revise the vocabulary in a new version. A headline without enough information to judge should remain blank and be logged for discussion; blank means unreviewed, not neutral or no tag.

Review `needs_review` cases for missed merchandise evidence and origin ambiguity. A generic export total must not silently become a goods-export observation. If you use source context to resolve ambiguity, retain it as a separate reviewed annotation; do not silently overwrite the reproducible headline baseline.

Judge the headline as the model sees it. Source links can establish context, but do not silently use full-article information to change a headline-only reference. If article-level relevance or economic favorability is desired, define and record a separate annotation task.

## Calculate metrics

```bash
python -m trade_news validate
```

Relevance uses binary accuracy, macro-F1 and a confusion matrix. Sentiment uses three-class accuracy and macro-F1; `unscored` predictions count as errors against any reference label, and their rate is shown explicitly. Macro-F1 averages over all predefined classes; absent classes receive zero when their F1 denominator is zero. Inspect class support and the confusion matrix before interpreting a small sample.

Multi-label theme, sector and partner tasks report exact-set match and micro-F1 from pooled true-positive, false-positive and false-negative tags. If no tag decision exists on either side, micro-F1 is null rather than an invented perfect score. Each task uses only its nonblank reference rows. Invalid categories, duplicate IDs, unknown IDs and missing human-provenance declarations raise errors.

## Academic quality review

Use at least two independent reviewers on an overlap subset, resolve disagreements after retaining original labels, and document agreement and adjudication separately. The current evaluator does not implement agreement statistics or adjudication storage. Inspect false positives, false negatives, abstentions and systematic errors by month, sector and publisher.

Freeze a revised development version before creating a separate time/publisher-held-out test set. Report annotation counts, class support, abstention rate, source coverage and uncertainty. Do not call the initial 40-row development review an unbiased benchmark, or tune and test on the same labels without disclosure.
