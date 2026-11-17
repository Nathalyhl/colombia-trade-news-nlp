# Human review and validation

## Current status

No human reference labels or corpus decisions have been invented. The initial review sheet is blank. `human_labels_pending`, null accuracy and null macro-F1 mean that classification quality has not yet been measured. Automated software diagnostics use explicitly synthetic test fixtures, kept out of the real-news dataset.

## Corpus review

Use Metodología y validación → Registrar revisiones humanas → Revisar inclusión en el corpus y sentimiento, or edit `data/annotations.csv`:

1. Open the publisher article and, when available locally, compare its text with the archived extraction. Check public access, reported date and extraction completeness.
2. Decide whether the article substantially discusses Colombian **goods exports** to foreign markets. Exclude service exports, imports, other countries’ exports to Colombia, unrelated uses and unresolved or inaccessible material. Mixed articles require judgment; record the reason.
3. Set `include=yes`, `no` or `review`. The dashboard no longer asks for economic activities. Optional activity overrides remain supported in the CSV for historical compatibility, but are not required to review inclusion.
4. Identify the reviewer and set `annotation_origin=human` for actual yes/no decisions. The dashboard requires an explicit personal-review declaration before saving. This records declared provenance, not independent certification.
5. Rebuild with `python -m trade_news analyze`. The provisional series respects overrides; the human-reviewed series includes only eligible articles with actual yes decisions. Exact duplicate handling applies to both.

Uncertainty or absence of a review is not a no label. Reviewers should not alter the published dictionary to make particular news score positively.

## Sentiment diagnostics

Optionally enter `sentiment_gold` as positive, negative or neutral, based on the overall export-related tone of the article, before inspecting the dictionary prediction. This is a project validation design, not an annotation protocol claimed to come from the Bank. Keep factual export growth distinct from article tone; write ambiguous cases in notes. Identify the human reviewer and origin.

`python -m trade_news validate` reports labeled count, accuracy, three-class macro-F1 and a confusion matrix that includes model abstentions. Absence of polarity words is an abstention and counts as an error when a human reference label is present. Scores on a small, convenience-reviewed set are descriptive diagnostics, not held-out generalization claims.

Before academic claims of quality: define a dated sampling plan across months, publishers and activities; use independent double annotation where possible; document disagreement and adjudication; report exclusions, abstentions, class support and uncertainty in metrics. No inter-annotator agreement or confidence interval is reported until the corresponding human data exist.

## Country validation

Use the separate country-review form in Metodología y validación → Registrar revisiones humanas. Read the article, select the country, decide whether it is discussed as a destination, and explain the source evidence. Judge before opening the automatic explanation. Save a reviewer name and explicit personal-review declaration. Historical, potential and interrupted export links count as discussed destinations; competitors or suppliers alone do not.

`data/destination_reviews.csv` preserves actual human pair decisions. Country rejection or uncertainty removes the assignment from the country view. A human yes can confirm or add an assignment. `data/destination_validation.json` evaluates the uncorrected automatic predictions against those references, including false positives and missed positives. Unsure cases are not converted to negative labels. No real human reference labels exist in the initial release.

These convenience labels do not by themselves establish held-out performance or full-corpus recall. Use a predeclared sample that includes automatic positives and unresolved mentions; otherwise missed destinations cannot be assessed. Model/agent diagnostics are kept distinct from human labels.

## Economic validation boundary

The Bank tests incremental information in forecasting models. This project executes a smaller export comparison using the supplied workbook, lagged news, coverage controls and expanding temporal origins. It uses an explicitly assumed publication calendar and revised history. Residual autocorrelation and inconclusive stationarity diagnostics prevent a validated-predictor claim. The original dynamic-factor ARMAX exercise is not replicated; see ECONOMIC_RESULTS_ES.md for results and limits.

## Prepared diagnostic review sample

`data/review_sample.csv` contains 60 real retrieved articles, with blank human fields and no automatic score columns. Two prespecified diagnostic cases are followed by round-robin years and document-role/scope/domain/lexical-support facets, with fixed SHA-256 ordering within facets. The seed, IDs and source-feature hash are recorded separately. Selection is purposive, not probability sampling or an independent held-out benchmark. The generator refuses to overwrite existing review work.

Read the original article before predictions. Complete include (yes/no/review), reviewer, annotation_origin=human and an evidence note. Optional sentiment_gold concerns the export-related interpretation, not the dictionary word count. For document_role_gold use statistical_reporting, event_or_expectation, mixed or unsure according to the actual article; reported_period and comparison_base remain blank unless verified. A source mentioning DANE can still contain other information. If the role or period is ambiguous, preserve uncertainty instead of inventing a value.

This sheet is a diagnostic artifact. Filling it does not silently replace active annotations or create accuracy metrics. The separate 200-record independent sample excludes diagnostic IDs and is locked before review. Its year/domain strata and inverse-stratum weights are retained; no population accuracy is implied by an unweighted or incompletely reviewed subset.

## Independent evaluation procedure

Give `evaluation_reviewer_a.csv` and `evaluation_reviewer_b.csv` to two independent human readers without model scores. Read the exact archived body when available; if only a changed live article is available, record the mismatch and do not silently label a different text. Judge inclusion, document role, overall tone, export-event direction, reference periods and comparison type separately. Use uncertain when evidence is insufficient. Record a reviewer name and annotation_origin=human; never copy model output into a reference field.

Adjudicate disagreements into `evaluation_adjudicated.csv` after preserving the two original sheets. `python scripts/evaluate_news.py evaluate --data-dir data` checks IDs/body hashes and computes only metrics with actual references: inclusion confusion/precision/recall, tone confusion/class metrics/macro-F1, dictionary abstentions, Cohen kappa, multiclass Brier and ten-bin ECE with counts. Report class and stratum support, missing labels and selection limits. Do not modify the frozen sample after seeing mistakes. This validates the retrieved frame, not recall over the entire press universe.

## Current execution

The primary frame now has 1,011 direct-sitemap press articles in all 80 months, March 2020–October 2026; both domains appear in 78 months. Analdex is complementary. A separate 200-record independent evaluation packet is locked, with zero adjudicated labels. The researcher supplied 309 monthly export observations; retrospective economic comparisons are executed, with assumed timing and adverse diagnostics disclosed in [ECONOMIC_RESULTS_ES.md](ECONOMIC_RESULTS_ES.md). This supersedes earlier pending-data and Analdex-only current-state descriptions. It does not establish human classification accuracy or real-time predictive validity.
