# Research brief and academic presentation

## Research objective

Test whether the language of Colombian goods-export news contributes information beyond official export releases. The observable here is the lexical tone of source text. Export performance, event direction and useful advance information are distinct concepts. An article about reactivating exports may mention a suspension; a dictionary balance can disagree with an export-event interpretation without a programming error.

## What is implemented

1. Auditable real-source acquisition, publication dates, hashes and access-failure records.
2. A conservative goods-export screening proposal that holds ambiguous headline focus and mixed trade flows for review; human overrides remain separate.
3. BE1340 published-dictionary baseline with explicit preprocessing choices, monthly pooled counts, missing denominators and three-month display.
4. Document-role cue proposals distinguishing possible statistical reporting, event/expectation cues, mixed cues and unresolved roles, with inspectable evidence.
5. Source-composition and reporting-holdout sensitivity views, sparse-safe country charts and a reproducible unlabeled diagnostic review sample.
6. A pinned public Spanish contextual model with separately credited preprocessing, full-body chunking, stored probabilities and headline/body inspection. The consolidated dashboard shows its monthly probability balance alongside the separate Bank lexical uncertainty series; Bank sentiment remains an explicit comparison. Model-margin review priorities are diagnostic suggestions, not gold labels or an independent evaluation sample.

The research contribution at this stage is an inspectable pipeline and an empirical measurement problem, not a demonstrated forecasting result. The original paper's manual curation, models and validated results are not this project's results.

## Why statistical reporting matters

A report paraphrasing an already released DANE figure may correlate with that figure simply because it repeats it. It must not be treated as advance information about the same release. Such reporting can still be studied descriptively, but its information timing and role need explicit annotation. Conversely, an article containing expectations, restrictions or orders is not automatically new or predictive: identify the original event date and what was available at the forecast origin. Analdex's publisher identity alone cannot make this distinction.

## Measurement and domain validation plan

First review actual article extraction, publication dates and whether exports are a substantive focus. Then independently annotate document role and export-related interpretation. Use two reviewers where feasible; preserve disagreements and adjudication. Keep dictionary lexical balance separate from the direction of the export event. Report abstentions and low lexical support rather than forcing an answer. The supplied 60-record sample is purposely diagnostic, so its eventual scores would describe those cases rather than estimate population accuracy.

Only after writing the annotation guide should a separate evaluation sample be locked. Compare the fixed published dictionary against any context-sensitive extension on the same independent reference set. Tune rules on development material, not the locked evaluation records; inspect performance by period, source, role and country. Report class support and uncertainty as well as aggregate metrics. No human labels or agreement scores currently exist.

## Economic validation plan, after numerical data are supplied

- Separate nominal FOB value, physical quantity and price/composition effects. A positive value change need not mean greater volume; aggregate kilograms across heterogeneous goods also require care.
- Verify the statistical reference period and comparison base: year-on-year, month-on-month and cumulative changes answer different questions. The news publication month is not automatically the period being reported.
- Record the official release calendar and data vintage. DANE's export methodology generally records the declaration date, with a shipment-date exception for oil and derivatives; do not silently interpret all monthly exports as shipments. See [DANE's technical bulletin](https://www.dane.gov.co/files/operaciones/EXPORTACIONES/bol-EXPORTACIONES-ene2025.pdf).
- Use only news and numerical releases available at each forecast origin. Reporting about the target release must be held out from a purported prediction of that release. Revisions and retrospective web retrieval complicate a claim of real-time performance.
- Compare a predeclared seasonal/baseline model, baseline plus sentiment, and baseline plus sentiment/uncertainty in rolling or expanding time-based evaluation. Fit transformations and model selection inside the training window. Reserve a final temporal holdout; report error differences and uncertainty without presuming improvement.
- Repeat on a fixed-source corpus and with verified statistical reporting separated. Treat country analysis as exploratory until its coverage and relation labels support a time-series test. Avoid causal claims from correlation.

## Suggested academic description

“I am developing a reproducible NLP study of Colombian goods-export news. I implemented a published dictionary-based sentiment and uncertainty baseline, audited corpus selection and source composition, and exposed disagreements between lexical tone and export-event meaning. The current sample demonstrates the pipeline and its limitations; the next stage is independent annotation and a release-aware test of whether news adds information beyond official trade statistics.”

Use this as a research/code-sample description, not as a claim of an independently validated indicator, completed dissertation or published empirical result. Preserve source and collaboration credits when presenting the work.
