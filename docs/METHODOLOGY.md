# Measurement and corpus protocol

## Research question and unit

How does the language used in news about Colombian merchandise exports vary across publication months from March 2020 onward? The unit is a retrieved publisher article, not a headline, individual export transaction or official statistical observation. The primary series pools all eligible articles. The dashboard adds a countries-only view and a separate evidence/review workflow.

The frozen window is 2020-03-01 inclusive through 2026-11-01 exclusive. All 80 completed publication months are retained, including months with missing estimates. There is no imputation for November or December and no claim that this is a complete year.

## Discovery, access and dates

1. Query Google News RSS once per month using `Colombia (exportaciones OR exportación OR exporta OR exportadores OR exportador)` and explicit date boundaries; locale `es-419`, country `CO`. Save response hashes and candidate metadata. Search coverage and rankings are provider-dependent.
2. Resolve each public RSS article link to the publisher URL. Check its publisher domain, robots rules and public access. Log failures; do not substitute text from another story, a headline, a search snippet or a model-generated summary.
3. Read explicit publisher `datePublished` in Article/NewsArticle/BlogPosting JSON-LD, then `article:published_time` if needed. Missing or out-of-window dates prevent inclusion. This independently checks the publisher’s reported date, not the truth of its publication history. `dateModified` is not a publication date.
4. Extract the article body with the pinned Trafilatura precision configuration, excluding comments and tables. Remove a leading repeated title. Store raw HTML and extracted text locally with SHA-256 hashes; keep publisher text out of the released feature files. Extraction completeness and boilerplate still need human inspection.

The public Analdex WordPress archive is a separate institutional-source supplement. The query searches `exportaciones` in posts between the same date boundaries, ordered by date, with public pagination. Each response has a timestamp, request URL, SHA-256 and provider page counts. Post `date` is the publisher-local publication date; `date_gmt` is retained for UTC lineage. Neither `modified` nor the statistical period discussed in the article supplies the index date. Article content comes from `content.rendered`, extracted with the same pinned precision configuration. Full API responses and content stay in the ignored local archive. Analdex post IDs distinguish this route from Google RSS discovery.

The monthly source-composition chart distinguishes Analdex from other publishers. It is a coverage diagnostic, not a correction for selection bias. The historical sample cannot establish media representativeness; publisher-mix changes may affect the time series. HTTP 429/403 stops provider requests; unattempted requests remain visible. No alternate hosts, proxies or access-control bypasses are used.

## Corpus and activities

The Bank’s study manually selected economic news and assigned activities. This project does not claim to have recreated that manual review. `classification.py` offers transparent keyword proposals for Colombian origin, export context, goods and activity. Ambiguous inbound exports, unresolved goods and mixed service headlines remain for review; obvious service or unrelated headlines are excluded. Co-occurrence rules can still be wrong.

An article enters the provisional series only when dated article text has eligible processed sentences and its scope proposal is include, or a documented human decision includes it. Human rejection and unresolved manual review exclude it. Canonical-URL and exact extracted-text duplicates contribute once; a human-included record takes priority over an unreviewed duplicate. Near-duplicate syndicated stories are not automatically resolved and may overweight one event.

Each retained article has one exact Annex 2 activity. Multiple activity proposals map to Global Context; unresolved foreign trade maps to Other Activity. The 18 labels are retained internally for reference compatibility; the activity dashboard has been removed. Corpus inclusion review no longer requires an activity label. An optional explicit activity override can still be supplied in the CSV. The automated cues are project-specific suggestions, not a classifier or code supplied by the Bank. They do not alter the main all-export index.

## Diagram 1 processing

- Discard cleaned texts shorter than 50 characters.
- Split at sentence punctuation, paragraphs and bullet boundaries; remove numeric, letter and roman list markers at line starts. Lowercase with Unicode casefold and preserve accents using NFC.
- Tokenize alphabetic Unicode sequences. Remove the frozen 313-word NLTK Spanish stopword file.
- Keep sentences with more than five remaining words, following the order shown in Diagram 1.
- Count exact occurrences of all positive and negative forms in Annex 3a/3b. Do not add inflections, stem, lemmatize or reverse polarity near negation: these extra rules are not specified by the diagram.

The exact tokenizer and stopword list are not supplied in the paper. Our punctuation boundaries and NLTK file are explicit implementation choices. Stopword removal includes negation words such as `no`, so negation sensitivity is a limitation of this operational reproduction. The published list is general economic vocabulary; no export-specific dictionary has been invented.

## Equations 1 and 2

For each month, sum positive `P_t`, negative `N_t`, uncertainty `U_t` and processed word `W_t` occurrences across eligible article bodies. Compute `(P_t-N_t)/(P_t+N_t)` and `1000*U_t/W_t`. Counts are pooled before division; article scores and publisher scores are not averaged. No minimum-three-articles/two-publishers rule is imposed by this implementation.

The uncertainty forms are `incertidumbre`, `incertidumbres`, `incierto`, `inciertos`, `incierta`, `inciertas`. They may overlap with the negative dictionary. Empty sentiment denominators remain missing; positive and negative counts that are equal and nonzero produce zero. Empty word denominators remain missing; zero uncertainty with a positive word denominator is a valid zero. Country views repeat these equations on article subsets. Each article contributes once per country; articles covering several countries can occur in several subsets.

Monthly values are stored to six decimal places; article-level counts remain integers. `neutral` is the project’s diagnostic label for an article with equal nonzero polarity counts, not a separate published lexicon category. An article with no polarity matches abstains.

## Three-month display and construction trace

The monthly equations remain the estimators. Following the quarterly-moving-average presentation in the reference Figure 3, the dark display line is the arithmetic mean of the current and previous two monthly estimates. All three must exist and be consecutive calendar months. March and April 2020 have raw estimates but no three-month mean. A gap interrupts the smoother; no zero, interpolation or future observation fills it. The paper does not specify centering or endpoint handling, so trailing alignment is an explicit project convention. This does not reproduce the Bank's original curve or event annotations.

Every processed article records cleaned characters, candidate sentences, alphabetic tokens before and after stopword removal, retained/short sentences, retained tokens, P, N, U and matched polarity forms. Metodología y validación maps these stages to the published construction sequence. Its model/dictionary comparison expands to the monthly construction table with article/source support, pooled P, N, U, W and both lexical indices. A method-version change requires reprocessing from the hash-checked local archive, rather than mixing old and new preprocessing features.

## Publication versus statistical reference periods

The index is timed by publication, not the period an article reports. A publication can discuss the preceding month, an annual total or a cumulative comparison. Words such as creció do not identify the base. Reference periods and comparison types are separate fields in the independent review packet and are not automatically asserted. The received 309-month numerical series uses explicit reference months; its unknown publication/vintage dates are retained as missing. Economic scenarios and their limitations are documented in ECONOMIC_RESULTS_ES.md.

## Interpretation and validation boundary

Report the provisional and human-reviewed subsets separately, with article/publisher volume, matched counts, retrieval outcomes and missingness. A series value measures lexical balance within the retrieved sample. It cannot establish export performance, causality, risk probabilities or forecasting ability.

Independent human corpus review and domain labels remain pending. Software tests establish implementation behavior only. A small export forecasting comparison has been executed with assumed timing and current numerical history; adverse diagnostics prevent predictive-validity claims. The original Bank dynamic-factor ARMAX experiment is not reproduced.

## Fixed-source sensitivity comparison

The primary frame uses direct publisher-declared sitemaps from Valora Analitik and La República across 80 months. Both domains contribute in 78 months. The dashboard compares equal-article and equal-source weighting; the latter requires both domains within that month. Other publishers, including Analdex, remain complementary. This is a composition sensitivity, not a representativeness or accuracy correction.

## Conservative export focus and document-role proposals (version 0.7)

Automatic inclusion now additionally requires an export-related headline and holds mixed import/export headlines for human review. This improves inspectability but can lose relevant contextual stories; no precision/recall improvement is claimed without reference judgments. Explicit human decisions remain separate. A screening-method version change requires reprocessing from the archived text. Original candidate records, extraction outcomes and non-eligible records are preserved.

Document roles are proposed by transparent title/body cues: report-title phrases or retrospective title verbs plus statistical-source mentions suggest statistical reporting; an enumerated title vocabulary identifies event/expectation cues. Overlap gives mixed cues, and absence gives unresolved. Each component is stored as evidence. These project rules are not supplied by the Bank, are not validated classifications and do not establish information novelty. The diagnostic holdout excludes statistical-reporting and mixed candidates without calling the remainder a verified forward-looking corpus.

Source counts group saved publisher URL domains after removing www while preserving publisher labels. This does not reconcile corporate media ownership. The primary frame fixes Valora Analitik and La República; source-specific and equal-source sensitivities are explicit.

Monthly chart values use visible markers, including isolated observations and valid zeroes. Missing months are not connected, the zero reference line is disabled, and a moving-average trace is created only when at least one three-month window exists. NaN is treated as missing. Country views expose the number of supported months, observed-span axes and the monthly construction table; sparse points do not justify a continuous country-trend claim.

## Current execution

The primary frame now has 1,011 direct-sitemap press articles in all 80 months, March 2020–October 2026; both domains appear in 78 months. Analdex is complementary. A separate 200-record independent evaluation packet is locked, with zero adjudicated labels. The researcher supplied 309 monthly export observations; retrospective economic comparisons are executed, with assumed timing and adverse diagnostics disclosed in [ECONOMIC_RESULTS_ES.md](ECONOMIC_RESULTS_ES.md). This supersedes earlier pending-data and Analdex-only current-state descriptions. It does not establish human classification accuracy or real-time predictive validity.
