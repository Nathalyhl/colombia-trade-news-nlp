# Research reference and adaptation

Mora-Quiñones, R. C. A., Orozco-Gallo, A. J., and Mora-Pérez, D. A. (2026). *Sentiment and Uncertainty Indices from economic news in Colombia*. Borradores de Economía, No. 1340, Banco de la República. [DOI and study](https://doi.org/10.32468/be.1340), [official summary](https://investiga.banrep.gov.co/es/borradores/be-1340), [full paper](https://repositorio.banrep.gov.co/bitstream/handle/20.500.12134/11323/be_1340.pdf).

## Methodological connection

Section 4, equation (1), defines sentiment through pooled positive and negative word counts: `(P - N) / (P + N)`. The study analyzes economic article text and uses a Spanish dictionary originating from Banco de España. Its sentiment and uncertainty measures have national/regional coverage; it also evaluates macroeconomic nowcasting. Those are results of that study, not of this project.

## What this implementation changes

| Choice | This project |
| --- | --- |
| Research scope | News about goods exported from Colombia to the world |
| Available text | RSS headlines and metadata, not complete article narratives |
| Included observations | Explicit goods evidence plus Colombian export-origin phrases; services and unresolved scope stay outside the index |
| Sentiment vocabulary | A small, transparent project-authored Spanish cue list; not the Bank's published dictionary |
| Context handling | Accent-insensitive matching and a local negation heuristic; not a reproduction of the study's preprocessing |
| Primary aggregation | Pooled signed cue balance, from −1 to +1, using the polarity-balance form in equation (1) |
| Sensitivity measure | A separate equal-publisher tone score, from −100 to +100 |
| Coverage safeguard | At least three scored headlines and two scored publisher labels; these are project choices |
| Validation status | Human reference labels and economic validation pending |

This is an independent **methodological adaptation**, not a replication of the Bank's dataset, published series, dictionary or forecasting results. It has no institutional affiliation or endorsement. Uncertainty measurement is a separate potential extension and is not implemented here.

## Research question

Can a news-based sentiment measure restricted to Colombian merchandise exports provide useful descriptive information, and eventually information beyond past official export values or volumes?

The current prototype answers the implementation part: it can collect candidates, filter scope, trace language cues and calculate reproducible indices. To answer the empirical part, independently annotate a review set, obtain a longer dated corpus, and compare against official [DANE goods-export statistics](https://www.dane.gov.co/index.php/estadisticas-por-tema/comercio-internacional/exportaciones). Keep value and quantity outcomes distinct and respect release dates. Freeze vocabulary decisions before a time-held-out evaluation against an explicit baseline. No such economic validation has yet been executed.
