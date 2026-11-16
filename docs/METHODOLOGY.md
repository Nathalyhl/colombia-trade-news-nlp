# Measurement and corpus protocol

## Research question and unit

How does the language used in news about Colombian merchandise exports vary across publication months in 2026? The unit is a retrieved publisher article, not a headline, individual export transaction or official statistical observation. The primary series pools all eligible articles. The dashboard adds a countries-only view and a separate evidence/review workflow.

The frozen window is 2026-01-01 inclusive through 2026-11-01 exclusive. All ten completed publication months are retained, including months with missing estimates. There is no imputation for November or December and no claim that this is a complete year.

## Discovery, access and dates

1. Query Google News RSS once per month using `Colombia (exportaciones OR exportación OR exporta OR exportadores OR exportador)` and explicit date boundaries; locale `es-419`, country `CO`. Save response hashes and candidate metadata. Search coverage and rankings are provider-dependent.
2. Resolve each public RSS article link to the publisher URL. Check its publisher domain, robots rules and public access. Log failures; do not substitute text from another story, a headline, a search snippet or a model-generated summary.
3. Read explicit publisher `datePublished` in Article/NewsArticle/BlogPosting JSON-LD, then `article:published_time` if needed. Missing or out-of-window dates prevent inclusion. This independently checks the publisher’s reported date, not the truth of its publication history. `dateModified` is not a publication date.
4. Extract the article body with the pinned Trafilatura precision configuration, excluding comments and tables. Remove a leading repeated title. Store raw HTML and extracted text locally with SHA-256 hashes; keep publisher text out of the released feature files. Extraction completeness and boilerplate still need human inspection.

## Corpus and activities

The Bank’s study manually selected economic news and assigned activities. This project does not claim to have recreated that manual review. `classification.py` offers transparent keyword proposals for Colombian origin, export context, goods and activity. Ambiguous inbound exports, unresolved goods and mixed service headlines remain for review; obvious service or unrelated headlines are excluded. Co-occurrence rules can still be wrong.

An article enters the provisional series only when dated article text has eligible processed sentences and its scope proposal is include, or a documented human decision includes it. Human rejection and unresolved manual review exclude it. Canonical-URL and exact extracted-text duplicates contribute once; a human-included record takes priority over an unreviewed duplicate. Near-duplicate syndicated stories are not automatically resolved and may overweight one event.

Each retained article has one exact Annex 2 activity. Multiple activity proposals map to Global Context; unresolved foreign trade maps to Other Activity. The 18 labels are retained internally for reference compatibility; the activity dashboard has been removed. Corpus inclusion review no longer requires an activity label. An optional explicit activity override can still be supplied in the CSV. The automated cues are project-specific suggestions, not a classifier or code supplied by the Bank. They do not alter the main all-export index.

## Diagram 1 processing

- Discard cleaned texts shorter than 50 characters.
- Split at sentence punctuation, paragraphs and bullet boundaries. Lowercase with Unicode casefold and preserve accents using NFC.
- Tokenize alphabetic Unicode sequences. Remove the frozen 313-word NLTK Spanish stopword file.
- Keep sentences with more than five remaining words, following the order shown in Diagram 1.
- Count exact occurrences of all positive and negative forms in Annex 3a/3b. Do not add inflections, stem, lemmatize or reverse polarity near negation: these extra rules are not specified by the diagram.

The exact tokenizer and stopword list are not supplied in the paper. Our punctuation boundaries and NLTK file are explicit implementation choices. Stopword removal includes negation words such as `no`, so negation sensitivity is a limitation of this operational reproduction. The published list is general economic vocabulary; no export-specific dictionary has been invented.

## Equations 1 and 2

For each month, sum positive `P_t`, negative `N_t`, uncertainty `U_t` and processed word `W_t` occurrences across eligible article bodies. Compute `(P_t-N_t)/(P_t+N_t)` and `1000*U_t/W_t`. Counts are pooled before division; article scores and publisher scores are not averaged. No minimum-three-articles/two-publishers rule is imposed by this implementation.

The uncertainty forms are `incertidumbre`, `incertidumbres`, `incierto`, `inciertos`, `incierta`, `inciertas`. They may overlap with the negative dictionary. Empty sentiment denominators remain missing; positive and negative counts that are equal and nonzero produce zero. Empty word denominators remain missing; zero uncertainty with a positive word denominator is a valid zero. Country views repeat these equations on article subsets. Each article contributes once per country; articles covering several countries can occur in several subsets.

Monthly values are stored to six decimal places; article-level counts remain integers. `neutral` is the project’s diagnostic label for an article with equal nonzero polarity counts, not a separate published lexicon category. An article with no polarity matches abstains.

## Interpretation and validation boundary

Report the provisional and human-reviewed subsets separately, with article/publisher volume, matched counts, retrieval outcomes and missingness. A series value measures lexical balance within the retrieved sample. It cannot establish export performance, causality, risk probabilities or forecasting ability.

Independent human corpus review and domain labels are pending. Software tests establish implementation behavior only. No nowcasting, DFM/ARMAX comparison, economic-performance validation or Bank-equivalent benchmark result is claimed.
