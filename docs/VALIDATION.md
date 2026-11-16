# Human review and validation

## Current status

No human reference labels or corpus decisions have been invented. The initial review sheet is blank. `human_labels_pending`, null accuracy and null macro-F1 mean that classification quality has not yet been measured. Automated software diagnostics use explicitly synthetic test fixtures, kept out of the real-news dataset.

## Corpus review

Use Quality & review → Review corpus inclusion and sentiment, or edit `data/annotations.csv`:

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

Use the separate country-review form in Quality & review. Read the article, select the country, decide whether it is discussed as a destination, and explain the source evidence. Judge before opening the automatic explanation. Save a reviewer name and explicit personal-review declaration. Historical, potential and interrupted export links count as discussed destinations; competitors or suppliers alone do not.

`data/destination_reviews.csv` preserves actual human pair decisions. Country rejection or uncertainty removes the assignment from the country view. A human yes can confirm or add an assignment. `data/destination_validation.json` evaluates the uncorrected automatic predictions against those references, including false positives and missed positives. Unsure cases are not converted to negative labels. No real human reference labels exist in the initial release.

These convenience labels do not by themselves establish held-out performance or full-corpus recall. Use a predeclared sample that includes automatic positives and unresolved mentions; otherwise missed destinations cannot be assessed. Model/agent diagnostics are kept distinct from human labels.

## Economic validation boundary

The Bank also tests its indices against economic activity in forecasting models. This project has not reproduced that stage. A credible export comparison needs a longer historical news series, official DANE merchandise-export data aligned to publication timing, a dated out-of-sample design and predeclared baselines. Do not equate a positive news score with a rise in exports or claim improved forecasts from this implementation.
