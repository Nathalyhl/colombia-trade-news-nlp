# Research methodology

## Question and unit of observation

How does lexical tone in a retrieved sample of Spanish-language headlines about exports of Colombian goods to the world vary by month, export theme, mentioned sector and mentioned market?

The unit is a headline record returned by Google News RSS, not a full article, trade transaction or economic outcome. This is a descriptive prototype. Associations in media framing cannot establish economic causality or predict export values.

## Collection and cleaning

`collect.py` requests one search feed per calendar month, in the Colombian Spanish locale. It retains headlines, publisher attribution, Google News article links, RSS publication timestamps and collection provenance. The requested end date is exclusive. The parser independently filters provider timestamps to the requested UTC-date interval; malformed or out-of-window items are counted in the log. Network failures are recorded, never replaced with synthetic headlines.

`pipeline.prepare` validates nonempty titles, HTTP(S) URLs and timezone-aware dates. It sorts records deterministically, removes duplicate URLs or exactly equal normalized headlines, and records excluded IDs. Normalization removes markup, expands HTML entities, collapses spaces, lowercases and removes diacritics for matching. The source title remains intact; the cleaned representation also removes the trailing `| El Colombiano` outlet brand so it cannot be mistaken for Colombian origin. Near-duplicate or syndicated stories with different headlines can remain; no semantic deduplication is claimed.

## Interpretable NLP baseline

`nlp.py` contains the complete versioned dictionaries and functions. No learned sentiment model, fine-tuning, embedding model or discovered-topic model is used in this version.

The project-authored lexicon explicitly lists selected verb inflections (for example, growth and decline forms). It is versioned as `spanish_headline_lexicon_v2`; no trained lemmatizer or reproduction of the source study's dictionary is claimed.

| Task | Implemented method | Interpretation |
| --- | --- | --- |
| Relevance | Explicit export cue, bounded phrases linking exports to Colombia, and an explicit goods cue; inbound/conflicting origin, services and ambiguous cases kept outside the index | Conservative headline-level rules, subject to false positives/negatives |
| Export themes | Whole normalized phrase matches | Multi-label dictionary tags, not unsupervised topics |
| Sectors | Whole normalized phrase matches | Explicit sector cues; categories may overlap |
| Partners | Country/bloc names and selected demonyms | Mentions only; no relation extraction or verified trading relationship |
| Sentiment | Fixed +1/−1 cue weights, negation in the preceding three tokens | Lexical headline tone, not favorable/unfavorable impact on Colombia |

For headline *i*, score `s_i` is the mean of its signed cue weights and lies in [−1, +1]. Positive, negative or exactly balanced scores map to `positive`, `negative` and `neutral`. A headline with no recognized cue receives `tone_score = null` and `sentiment = unscored`. Abstention is never silently converted to neutrality. The matched terms, weights and negation flags accompany each record.

Negation is a deliberately simple local heuristic. Removing punctuation can broaden its scope incorrectly; double negation, quotations, irony, conditional statements and economic context require further work. “Aumentan los aranceles para Colombia” receives positive lexical tone because `aumentan` is a positive cue; it is not evidence that rising tariffs benefit Colombia. This synthetic diagnostic is explicitly tested to expose the method's semantics.

## Export News Sentiment Index

The primary measure follows the polarity-balance form of equation (1) in [Mora-Quiñones, Orozco-Gallo and Mora-Pérez (2026)](https://doi.org/10.32468/be.1340), applied to our own headline corpus and provisional lexicon. See [the reference comparison](RESEARCH_REFERENCE.md). For month *m* and group *g*, pool all signed cue occurrences from included headlines after deduplication and filters:

```text
P_m,g = number of positive cue occurrences after the local negation rule
N_m,g = number of negative cue occurrences after the local negation rule
export_sentiment_index = (P_m,g - N_m,g) / (P_m,g + N_m,g)
```

The range is [−1, +1]. A zero cue denominator gives a missing index, never zero. Headlines with more recognized cues contribute more to this pooled measure. This differs from averaging headline scores.

For sensitivity analysis, `headline_tone_index` retains the earlier equal-publisher measure on a [−100, +100] scale:

```text
publisher_mean_p = mean(tone_score_i for scored headlines attributed to p)
headline_tone_index = 100 * mean(publisher_mean_p over scored publishers)
```

Equal publisher weights reduce domination by an outlet with more retrieved headlines. They do not correct retrieval bias, publisher-name aliases, syndication, or nonindependent coverage. A source is the RSS publisher label, not a verified independent editorial organization.

An index is shown only with at least **3 scored headlines** and **2 scored publisher labels** in the month/group. These are transparent operational thresholds, not statistically derived confidence criteria. Other groups retain `null` with `insufficient_coverage`. Adequate groups remain `provisional`; a coverage threshold does not establish validity. No confidence interval or significance claim is made.

Outputs retain total records, scored records, scored publishers and scoring coverage. The month grid includes requested months with no observations; their index remains missing. Each multi-label group is calculated separately, so category counts are not additive. The dashboard recomputes these same functions after filters; a missing point does not become zero.

## Goods-only scope decisions

The scope is legal merchandise exports, including agricultural products, manufactured goods, minerals, fuels and electricity. Services (including software, tourism and cybersecurity), illicit trade and player-transfer stories are outside scope. A headline must contain goods cues as well as Colombian export-origin evidence. General export totals are not assumed to refer to goods; if the headline does not resolve that distinction, it receives `needs_review`. Mixed goods/services headlines remain outside the index because their whole-headline tone cannot be assigned specifically to goods.

Export-related tariffs, logistics and trade agreements are secondary themes only after the headline passes the goods-export scope. Country tags indicate mentions and do not establish destinations. The filter is intentionally conservative and can miss relevant stories. `goods_evidence`, `export_origin_evidence`, `service_evidence`, `scope_status` and `scope_reason` make those choices inspectable.

## Evaluation and research extensions

The repository supplies a deterministic, hash-selected review sample of up to 40 records from all retained records, including relevance exclusions. Gold fields begin blank. Review instructions and executable metrics are in [VALIDATION.md](VALIDATION.md). Unit fixtures test implementation behavior; the included live metadata and offline snapshot checks test lineage and reproducibility. Neither supplies human domain accuracy.

A future economic validation should compare the index with official [DANE goods-export statistics](https://www.dane.gov.co/index.php/estadisticas-por-tema/comercio-internacional/exportaciones), preserving publication dates and distinguishing values from quantities. No such test or forecasting experiment has been executed. Six months of retrospectively collected search headlines cannot establish predictive performance.

Next research steps are independent annotation, error analysis, vocabulary revision on a development split, a publisher/time-held-out test set, a comparison with a documented Spanish sentiment model, contextual economic favorability labels, better syndication handling and expanded query coverage. These are proposals, not completed experiments.
