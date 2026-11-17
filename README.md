# Colombian Goods Export News: An Auditable NLP Research Sample

**Research question:** Can Spanish-language news about Colombian goods exports add information beyond already published trade statistics?

This independent research prototype implements the published dictionary measurement in [Mora-Quiñones, Orozco-Gallo & Mora-Pérez (2026), Banco de la República BE1340](https://doi.org/10.32468/be.1340), then examines corpus selection, document roles, source composition and sparse country coverage. Its current contribution is a reproducible measurement and audit pipeline. Incremental economic information and predictive performance remain hypotheses to test.

Code identifiers stay in English. The consolidated dashboard, model explanation and review notebook are supplied in Spanish first; baseline technical documents remain in English. Original source articles remain in Spanish. Goods exports from Colombia to foreign markets are in scope; service exports, imports and incidental mentions require separate treatment.

## Start here for academic review

Open **Resultados** for the executed monthly news-tone and uncertainty series, **Noticias y destinos** to inspect their source articles, and **Metodología y validación** for definitions, comparisons and review tools. The [Spanish dashboard guide](docs/DASHBOARD_ES.md) explains the three-tab design. Read the [research brief and validation design](docs/RESEARCH_BRIEF.md) and inspect `trade_news/bank_method.py`, `trade_news/contextual.py` and `trade_news/classification.py`. Implemented results remain separate from claims requiring data and human judgments; third-party methods and code retain their credits.

## Nueva comparación: primero en español

Se adaptó el modelo público [PySentimiento / RoBERTuito](https://huggingface.co/pysentimiento/robertuito-sentiment-analysis) a los artículos del corpus. El repositorio conserva por separado el método léxico de BE1340. La [explicación metodológica en español](docs/CONTEXTUAL_REPLICATION_ES.md) identifica el código reutilizado, los créditos, las restricciones de uso científico/no comercial y las adaptaciones propias. `Comparacion_NLP_Exportaciones_ES.ipynb` reproduce las probabilidades y los agregados guardados; **Noticias y destinos** permite revisar titulares y cuerpos por separado. La comparación entre métodos está en un desplegable de **Metodología y validación**.

Se reutilizan los pesos publicados y el preprocesamiento original. La inferencia local emplea Transformers y PyTorch; los artículos largos se procesan completos mediante fragmentos sin superposición. El promedio ponderado de probabilidades de fragmentos y la media mensual por artículo son decisiones explícitas del proyecto. El modelo se entrenó con mensajes de Twitter en español: su utilidad para noticias de exportaciones colombianas requiere evaluación humana. No se presentan como propios los porcentajes de precisión publicados por otros autores.

La ejecución completa procesó **410 artículos**, 3.883 fragmentos de cuerpos y 463.240 tokens de contenido; produce resultados en 78 meses con textos. El [informe de resultados en español](docs/CONTEXTUAL_RESULTS_ES.md) muestra los conteos reales y el caso de reactivación de exportaciones. No se generaron etiquetas humanas.

Para reconstruir la nueva serie desde los resultados guardados, sin instalar el modelo:

```bash
python scripts/run_contextual.py --offline
```

Para repetir la inferencia, usa un entorno separado y conserva el archivo local de artículos:

```bash
python -m venv .venv-contextual
# Activate this separate environment before the following commands.
python -m pip install -r requirements-contextual.txt
python scripts/download_contextual_model.py
python scripts/run_contextual.py --model-dir data/raw/contextual_model
```

La descarga pública fijada por revisión y SHA-256 incluye unos 415 MiB de pesos. Los pesos y los cuerpos de las noticias no se distribuyen en este repositorio. Las probabilidades guardadas permiten revisar el trabajo sin efectuar esa descarga. El código de `trade_news/contextual.py` es el adaptador del proyecto; `trade_news/pysentimiento_preprocessing.py` conserva explícitamente la autoría del código original reutilizado.

## Executed sample and its limits

Publication window: **March 2020–October 2026**, with all 80 calendar months retained.

| Stage | Executed count |
| --- | ---: |
| Real discovery records | 1374 |
| Retrieved publisher texts | 840 |
| Eligible, deduplicated texts under conservative automatic scope rules | 410 |
| Eligible texts with at least one dictionary polarity match | 321 |
| Months with eligible text | 78 / 80 |
| Months with a sentiment denominator | 77 / 80 |
| Human reference labels supplied | 0 |

The previous broad co-occurrence screen admitted texts about imports, investment or general trade with incidental export mentions. The revised screen requires a resolved export focus in the headline for automatic inclusion, retaining ambiguous texts for human review. The old 696-article count is superseded by 410 provisional eligible records. This conservative rule can miss relevant contextual news; it is not a validated classifier.

Google RSS supplied 730 candidates and encountered rate limits. Analdex's public WordPress archive supplied 644 separately identified posts. **Eligible 2020–2025 texts currently come only from Analdex; 2026 adds other publishers.** Analdex includes statistical reports, commentaries and other publications. Its name does not establish document role or information novelty. This is an incomplete historical sample, not a representative press census. Original HTML/text and API responses stay in the ignored local archive.

Document-role cues currently propose **68 statistical-reporting candidates, 23 event/expectation candidates, 2 mixed cases and 317 unresolved roles** among eligible articles. These are auditable proposals, not human labels. An event cue does not prove that a story contains new information or predicts exports. The dashboard separately compares a fixed-source series and a diagnostic holdout of reporting/mixed candidates; neither is an accuracy or causal test.

## Measurement

```text
SENT_t   = (P_t - N_t) / (P_t + N_t)
UNCERT_t = 1000 * U_t / W_t
```

Counts are pooled across eligible article bodies before division. The unchanged Annex 3 dictionary contains 188 positive and 376 negative forms. The six uncertainty forms, processed-word denominator, 50-character text condition and >5 post-stopword-word sentence condition follow the published measurement description. Exact tokenizer, frozen NLTK stopwords and trailing moving-average alignment are documented project choices. See [methodology](docs/METHODOLOGY.md) and [reference comparison](docs/RESEARCH_REFERENCE.md).

No polarity matches means missing sentiment, not neutral; balanced nonzero counts yield zero. The index measures lexical tone, not export growth. A three-month moving average requires three consecutive nonmissing monthly values. Points remain visible when isolated; gaps are never connected or filled. A smoother is omitted if no such window exists. Country charts focus on the observed date span and expose monthly P, N, U, W and article support. The country view remains an automatic relation-extraction pilot, not a continuous destination index or export-value ranking.

## Reproduce the code sample

```bash
python -m venv .venv
# Activate using your operating system's normal command.
python -m pip install -r requirements.txt
python -m streamlit run app.py

# Offline decisions, monthly arithmetic and provenance checks.
python -m trade_news analyze
python -m trade_news validate
python scripts/check_snapshot.py
python -m unittest discover -s tests -v

# Re-run text processing only when the local hash-checked archive is present.
python -m trade_news analyze --verify-local-text
```

The dashboard opens the committed snapshot without collecting new news. `Colombia_Trade_News.ipynb` provides offline feature analysis in Jupyter or Colab; upload the private repository ZIP while signed in, without placing credentials in notebook cells. Full source-to-count reproduction requires the ignored local archive; public re-retrieval may fail or change.

```bash
# Collect into a NEW directory; preserve existing data and reviews.
python -m trade_news collect --start 2020-03-01 --end 2026-11-01 --data-dir data_new
python -m trade_news publisher-archive --start 2020-03-01 --end 2026-11-01 --data-dir data_new
python -m trade_news fetch --data-dir data_new
python -m trade_news analyze --data-dir data_new
```

Failed discovery leaves its logs and does not create fallback news. Public publisher dates determine the news month; the reported export period is a separate field to verify. Publisher access controls and robots restrictions are respected. Domains are normalized for source counts while the original publisher label is preserved; this does not identify ultimate media ownership.

## Next empirical step

`data/review_sample.csv` contains **60 real records with blank judgments**, selected by a reproducible diagnostic sampling procedure. The selection manifest records the feature hash and IDs. Reviewers assess scope, document role and lexical/export-event disagreements before seeing predictions. The sample deliberately includes diagnostic cases and diverse years/cues; it is not a probability sample or held-out benchmark. `python scripts/prepare_review_sample.py` preserves existing human work instead of overwriting it. See [validation instructions](docs/VALIDATION.md).

Numerical export validation is deferred until the researcher supplies the dataset. A later economic test must align reference periods, release dates and information available at prediction time, then compare predeclared baselines out of sample. Statistical reporting that repeats the target release can otherwise create a circular result. No forecast improvement, validated accuracy or causal effect is claimed.

Further reading: [snapshot tables](docs/SNAPSHOT_REPORT.md), [real diagnostic cases](docs/DIAGNOSTIC_CASES.md), [country protocol](docs/DESTINATIONS.md), [related research](docs/RELATED_WORK.md), [source lineage](docs/DATA_SOURCES.md), [third-party credits and licenses](docs/THIRD_PARTY_NOTICES.md).
