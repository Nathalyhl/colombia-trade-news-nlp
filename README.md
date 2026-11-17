# Colombian Goods Export News: Measurement and Validation

Can Spanish-language news about Colombian goods exports add information beyond the available export history? This independent research project studies corpus construction, text measurement and economic evaluation as separate questions. It adapts published methods and preserves their authorship; it does not claim to reproduce either central bank's original experiment.

## Review the work

Start with the [Spanish study protocol](docs/STUDY_PROTOCOL_ES.md), [executed economic findings](docs/ECONOMIC_RESULTS_ES.md) and the three dashboard views: **Resultados**, **Noticias y destinos**, **Metodología y validación**. Code identifiers remain in English; articles, dashboard and the first methodological explanation are in Spanish. The two notebooks reproduce saved features without collecting news or downloading a model by default.

| Evidence | Frozen snapshot |
| --- | --- |
| Primary press frame | 1,011 eligible articles, Valora Analitik and La República |
| Publication coverage | March 2020–October 2026, 80/80 months; both domains in 78 |
| Complete acquisition archive | 3,517 candidates; 2,868 extracted texts; 1,423 provisionally eligible |
| Numerical input | 309 national monthly observations, January 2001–September 2026; researcher-supplied workbook |
| Independent text evaluation | 200 locked records, two blank reviewer sheets and one adjudication sheet |
| Adjudicated human tone labels | 0; classification accuracy remains unmeasured |

The primary period is selected from news coverage, without export outcomes or sentiment values. November 2020 and December 2024 have one primary domain; the strict two-domain window remains a documented sensitivity. Analdex and other publishers are complementary, separately identified. Reports of already released statistics are not treated as verified new information: document-role rules produce review proposals, not gold labels.

## Executed findings

For October 2025–September 2026, adding lagged tone to the coverage-controlled baseline changes RMSE from **8.741 to 8.593** (annual nominal FOB log-growth points, twelve common origins). Adding uncertainty produces **8.964**. These are retrospective scenario results, using an explicitly assumed publication lag and current numerical history.

**This is not a validated forecasting indicator.** All twelve fits in each of the four main specifications show residual autocorrelation; training ADF tests do not reject a unit root. The small error reduction is insufficient to establish useful incremental prediction. Alternative availability lags, source frames and a reporting-candidate exclusion are reported, including an unestimable La República-only sensitivity. Two simple diagnostic comparators were added after observing the residual failures; their timing is disclosed. No order search is performed on the test months.

## Methods and code to inspect

* `trade_news/history.py`: publisher-declared sitemap discovery, robots/access checks, immutable response hashes and publication-date separation.
* `trade_news/articles.py`, `classification.py`, `corpus.py`: body extraction, transparent scope/document proposals, exact deduplication and human-review provenance.
* `trade_news/bank_method.py`: unchanged 188 positive / 376 negative dictionary forms and six uncertainty forms from [BE1340](https://doi.org/10.32468/be.1340). Monthly sentiment is pooled (P−N)/(P+N); uncertainty is 1000U/W. Missing polarity support remains missing.
* `trade_news/contextual.py`: pinned public [PySentimiento/RoBERTuito](https://huggingface.co/pysentimiento/robertuito-sentiment-analysis), separately scored headlines and complete bodies, nonoverlapping chunks, token-weighted probabilities and equal-article monthly means of P(POS)−P(NEG). Spanish tweet training does not establish export-news accuracy.
* `trade_news/evaluation.py`: frozen independent sample, reviewer/adjudication provenance, agreement, abstentions, classification and calibration metrics only when human labels exist.
* `trade_news/economics.py`: availability masks before growth calculation, expanding-origin comparisons, training-only scaling, source/volume controls, common origins and retained diagnostics.

[Dávila & Chasi, Banco Central del Ecuador](https://doi.org/10.47550/RCE/35.2.1) informs direct acquisition, contextual measurement and independent evaluation. [Mora-Quiñones, Orozco-Gallo & Mora-Pérez, Banco de la República](https://doi.org/10.32468/be.1340) supplies the dictionary instrument and motivates an incremental forecasting comparison. The latter's dynamic-factor ARMAX exercise is not reproduced by this smaller export experiment. The exact author scripts were not obtained from the consulted journal/official records. Public PySentimiento code and weights retain their [credits and scientific/noncommercial conditions](docs/THIRD_PARTY_NOTICES.md).

## Reproduce the saved research sample

```bash
python -m venv .venv
# Activate this environment using your operating system's usual command.
python -m pip install -r requirements.txt
python -m streamlit run app.py
python scripts/check_snapshot.py
python -m unittest discover -s tests -v
python scripts/run_contextual.py --offline
python scripts/evaluate_news.py evaluate --data-dir data
```

Optional full text inference uses a separate environment with `requirements-contextual.txt`, `scripts/download_contextual_model.py` and the ignored, hash-checked local article archive. No weights or full publisher bodies are distributed. Optional economic estimation uses Python 3.12+ and `requirements-econometrics.txt` in a separate environment:

```bash
python scripts/run_economic_study.py --data-dir data
```

That command explicitly reproduces assumed-timing, revised-history scenarios. The strict `scripts/evaluate_exports.py compare` route remains blocked if actual release/vintage dates are missing. The source workbook stays local; `scripts/audit_export_workbook.py --workbook PATH --output-dir data` extracts observed rows and traces each to its sheet, cells and SHA-256 without changing the workbook. The committed derived CSV retains unknown historical dates as blanks.

## Interpretation and limits

Publication month differs from the export reference period discussed in the article. A resumption announcement can coexist with negative historical language; overall tone and export-event direction require separate labels. Nominal FOB growth differs from physical volume. Country links are an unvalidated headline-relation pilot, not destination export totals or representative country sentiment indexes.

The corpus is a documented retrieval frame, not a census. URL vocabulary, exact-only duplicate detection, editorial selection, extraction and retrospective page changes limit inference. Numeric source checks are partial; unavailable historical releases/vintages and model availability prevent real-time claims. Independent human review and a new, diagnostically adequate forecasting specification with fresh temporal evaluation remain required. A negative or inconclusive result is retained as research evidence.
