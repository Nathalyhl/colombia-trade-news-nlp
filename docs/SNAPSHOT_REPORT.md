# Executed snapshot report

Computed from the included real metadata snapshot collected on 15 November 2026. These are descriptive outputs of the initial rules, not independently validated news classifications or economic findings.

## Corpus and scoring coverage

The parser retained **160** records, and the relevance baseline selected **127**. The selected sample contains **36 publisher labels**. The sentiment lexicon scored **36 of 127 headlines (28.3%)**; the rest are explicit abstentions.

Low scoring coverage limits interpretation: the index represents the scored subset, not the tone of every retrieved headline. Coverage varies by month. The minimum thresholds are operational choices, not guarantees of reliability.

| Month | Relevant | Scored | Scored publishers | Scoring coverage | Provisional HTI |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-05 | 17 | 3 | 2 | 17.6% | 50.00 |
| 2026-06 | 16 | 3 | 3 | 18.8% | 0.00 |
| 2026-07 | 37 | 9 | 6 | 24.3% | 11.11 |
| 2026-08 | 15 | 5 | 4 | 33.3% | -12.50 |
| 2026-09 | 12 | 4 | 3 | 33.3% | 33.33 |
| 2026-10 | 30 | 12 | 10 | 40.0% | 40.00 |

HTI averages scored headlines within each publisher, averages publishers equally, and scales to −100 to +100. It measures lexical tone and cannot establish stronger exports, healthier trade relations, or a causal economic trend.

## Predicted labels

### Sentiment

| Predicted label | Headlines |
| --- | ---: |
| unscored | 91 |
| positive | 19 |
| negative | 12 |
| neutral | 5 |

### Themes

| Predicted label | Headlines |
| --- | ---: |
| trade_flows | 85 |
| tariffs_and_policy | 49 |
| exchange_and_prices | 3 |

### Sectors

| Predicted label | Headlines |
| --- | ---: |
| energy_and_mining | 13 |
| agriculture | 7 |
| food | 3 |
| services | 1 |
| manufacturing | 1 |

### Partners

| Predicted label | Headlines |
| --- | ---: |
| United States | 37 |
| Ecuador | 18 |
| China | 8 |
| Venezuela | 2 |
| Brazil | 1 |

Tags may overlap and cover only the predefined vocabulary. Partner counts are explicit mentions, not measured bilateral trade or verified relationships. No tag should be inferred from a missing mention.

## What remains to establish

Human references are still blank. Accuracy, macro-F1 and multi-label quality therefore remain pending. The next defensible research result is an annotated error analysis using [the validation protocol](VALIDATION.md). The snapshot already supports inspection of actual headlines, provenance, cue evidence and calculation behavior.
