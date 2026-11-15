# Executed goods-export snapshot report

Computed from the included export-specific real metadata snapshot collected on 15 November 2026. Only headlines passing the Colombian-origin and goods-only rules enter this report's indices. These are descriptive outputs, not independently validated news classifications or economic findings.

## Corpus and scoring coverage

The parser retained **152** records, and the relevance baseline selected **63**. The selected sample contains **25 publisher labels**. The sentiment lexicon scored **25 of 63 headlines (39.7%)**; the rest are explicit abstentions.

Low scoring coverage limits interpretation: the index represents the scored subset, not the tone of every retrieved headline. Coverage varies by month. The minimum thresholds are operational choices, not guarantees of reliability.

Scope audit: 63 included, 33 held for review and 56 excluded. Service stories and ambiguous goods/origin are not counted in the index.

| Month | Goods-export headlines | Scored | Scored publishers | Scoring coverage | Export sentiment (−1 to +1) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-05 | 10 | 2 | 2 | 20.0% | Missing: insufficient coverage |
| 2026-06 | 3 | 2 | 2 | 66.7% | Missing: insufficient coverage |
| 2026-07 | 14 | 3 | 2 | 21.4% | 0.5000 |
| 2026-08 | 10 | 2 | 2 | 20.0% | Missing: insufficient coverage |
| 2026-09 | 6 | 4 | 4 | 66.7% | 0.6000 |
| 2026-10 | 20 | 12 | 8 | 60.0% | 0.4000 |

The primary index pools positive and negative cue counts as (P − N)/(P + N), following the polarity-balance form in the [research reference](RESEARCH_REFERENCE.md). The vocabulary and headline corpus differ from that study. The equal-publisher sensitivity measure remains in indices.json. Neither index establishes export growth, healthier trade relations or economic causality.

## Predicted labels

### Sentiment

| Predicted label | Headlines |
| --- | ---: |
| unscored | 38 |
| positive | 17 |
| negative | 6 |
| neutral | 2 |

### Themes

| Predicted label | Headlines |
| --- | ---: |
| exports | 63 |
| logistics | 3 |
| trade_agreements | 1 |
| exchange_and_prices | 1 |

### Sectors

| Predicted label | Headlines |
| --- | ---: |
| agriculture | 29 |
| energy_and_mining | 22 |
| food | 8 |
| manufacturing | 8 |

### Partners

| Predicted label | Headlines |
| --- | ---: |
| United States | 6 |
| Israel | 4 |
| China | 3 |
| Ecuador | 3 |
| Philippines | 2 |
| Venezuela | 1 |

Tags may overlap and cover only the predefined vocabulary. Partner counts are explicit mentions, not measured bilateral trade or verified relationships. No tag should be inferred from a missing mention.

## What remains to establish

Human references are still blank. Accuracy, macro-F1 and multi-label quality therefore remain pending. The next defensible research result is an annotated error analysis using [the validation protocol](VALIDATION.md). The snapshot already supports inspection of actual headlines, provenance, cue evidence and calculation behavior.
