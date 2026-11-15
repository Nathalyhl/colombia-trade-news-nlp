# Research methodology

## Question and unit of observation

How does lexical tone in a retrieved sample of Spanish-language headlines about Colombian foreign trade vary by month, commercial theme, mentioned sector and mentioned partner?

The unit is a headline record returned by Google News RSS, not a full article, trade transaction or economic outcome. This is a descriptive prototype. Associations in media framing cannot establish economic causality or predict export values.

## Collection and cleaning

`collect.py` requests one search feed per calendar month, in the Colombian Spanish locale. It retains headlines, publisher attribution, Google News article links, RSS publication timestamps and collection provenance. The requested end date is exclusive. The parser independently filters provider timestamps to the requested UTC-date interval; malformed or out-of-window items are counted in the log. Network failures are recorded, never replaced with synthetic headlines.

`pipeline.prepare` validates nonempty titles, HTTP(S) URLs and timezone-aware dates. It sorts records deterministically, removes duplicate URLs or exactly equal normalized headlines, and records excluded IDs. Normalization removes markup, expands HTML entities, collapses spaces, lowercases and removes diacritics for matching. The source title remains intact. Near-duplicate or syndicated stories with different headlines can remain; no semantic deduplication is claimed.

## Interpretable NLP baseline

`nlp.py` contains the complete versioned dictionaries and functions. No learned sentiment model, fine-tuning, embedding model or discovered-topic model is used in this version.

| Task | Implemented method | Interpretation |
| --- | --- | --- |
| Relevance | Explicit Colombia/demonym plus trade-flow, tariff, agreement or logistics phrase; known static-page patterns excluded | Headline-level filter, subject to false positives/negatives |
| Commercial themes | Whole normalized phrase matches | Multi-label dictionary tags, not unsupervised topics |
| Sectors | Whole normalized phrase matches | Explicit sector cues; categories may overlap |
| Partners | Country/bloc names and selected demonyms | Mentions only; no relation extraction or verified trading relationship |
| Sentiment | Fixed +1/−1 cue weights, negation in the preceding three tokens | Lexical headline tone, not favorable/unfavorable impact on Colombia |

For headline *i*, score `s_i` is the mean of its signed cue weights and lies in [−1, +1]. Positive, negative or exactly balanced scores map to `positive`, `negative` and `neutral`. A headline with no recognized cue receives `tone_score = null` and `sentiment = unscored`. Abstention is never silently converted to neutrality. The matched terms, weights and negation flags accompany each record.

Negation is a deliberately simple local heuristic. Removing punctuation can broaden its scope incorrectly; double negation, quotations, irony, conditional statements and economic context require further work. “Aumentan los aranceles para Colombia” receives positive lexical tone because `aumentan` is a positive cue; it is not evidence that rising tariffs benefit Colombia. This synthetic diagnostic is explicitly tested to expose the method's semantics.

## Headline Tone Index

For month *m* and selected group *g*, let `S_p` contain the scored, relevant headlines attributed to publisher *p* after deduplication and dashboard filters.

```text
publisher_mean_p = sum(s_i for i in S_p) / len(S_p)
HTI_m,g = 100 * sum(publisher_mean_p for p in scored_publishers) / number_of_scored_publishers
```

Equal publisher weights reduce domination by an outlet with more retrieved headlines. They do not correct retrieval bias, publisher-name aliases, syndication, or nonindependent coverage. A source is the RSS publisher label, not a verified independent editorial organization.

An index is shown only with at least **3 scored headlines** and **2 scored publisher labels** in the month/group. These are transparent operational thresholds, not statistically derived confidence criteria. Other groups retain `null` with `insufficient_coverage`. Adequate groups remain `provisional`; a coverage threshold does not establish validity. No confidence interval or significance claim is made.

Outputs retain total records, scored records, scored publishers and scoring coverage. The month grid includes requested months with no observations; their index remains missing. Each multi-label group is calculated separately, so category counts are not additive. The dashboard recomputes these same functions after filters; a missing point does not become zero.

## Evaluation and research extensions

The repository supplies a deterministic, hash-selected review sample of up to 40 records from all retained records, including relevance exclusions. Gold fields begin blank. Review instructions and executable metrics are in [VALIDATION.md](VALIDATION.md). Unit fixtures test implementation behavior; the included live metadata and offline snapshot checks test lineage and reproducibility. Neither supplies human domain accuracy.

Next research steps are independent annotation, error analysis, vocabulary revision on a development split, a publisher/time-held-out test set, a comparison with a documented Spanish sentiment model, contextual economic favorability labels, better syndication handling and expanded query coverage. These are proposals, not completed experiments.
