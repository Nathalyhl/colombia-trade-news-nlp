# Country destinations and classification quality

The dashboard contains countries only. The Economic activities tab, regional/bloc choices and broad geographic-mention browsing mode have been removed. The source study's activity vocabulary remains in reference/internal metadata for historical compatibility; it is not a visible analysis feature.

## Automatic country links

Country proposals use finite Spanish country names and aliases in headlines about Colombian exports. They require directional wording or a named buyer/customer/destination role. A country name alone is not promoted to a destination. Broader country mentions in the archived body remain candidate evidence for review, not assignments in the destination view. No country is inferred from Europe, Asia, a trade bloc or a regional label.

The direction rule requires Colombian-origin wording before the destination country. Comparison/source phrases such as `frente a`, `compite con` and `procedente de` prevent the country from being assigned by that directional rule. These guards reduce known errors but are not a complete semantic parser or a validated classifier.

### Actual diagnostic corrected

Record `a1348320f184c51f24f5`, **Exportaciones de ganado caen 49,6 % y el peso fuerte le resta mercado a Colombia frente a Brasil**, previously proposed Brazil because a long token window connected export wording to a later `a Brasil`. The article discusses Brazil as a competitor with a currency advantage. The revised rule records comparison evidence and leaves Brazil out of the automatic destination assignments. The source link and this explanation are visible under Metodología y validación → Registrar revisiones humanas.

This case was inspected by the agent against the stored headline and article. It is an observed diagnostic, not a human reference label, held-out example or accuracy estimate. The current country subset has 24 provisionally linked articles across five countries: United States, Ecuador, Israel, Venezuela and China. Other countries may be discussed in article bodies; unresolved relations are not treated as verified destinations.

## How to check an assignment

The country view shows the source headline, publication date, source link, plain-language rule, automatic/human status and dictionary word evidence. This allows a reader to see why a label or lexical score was produced. Explanations expose decisions; they do not establish their correctness.

Metodología y validación → Registrar revisiones humanas provides an article-country review form. Read the source, judge whether the country is discussed as a destination for Colombian goods exports, and enter yes/no/unsure, reviewer and rationale. Historical, potential, denied or interrupted export relationships can still be discussed destinations; the label does not certify a current shipment. A competitor or supplier mention alone is not a destination. The automatic explanation is collapsed so a reviewer can judge first.

Only actual submitted human decisions are stored in `destination_reviews.csv`. Names, explanations, source hashes and declared human origin are required. Yes confirms or adds an assignment; no removes it; unsure holds it out and is excluded from binary accuracy calculations. A reviewed-only filter shows only actual human yes decisions. No human judgments have been supplied in the initial release.

## Accuracy and evaluation

`destination_validation.json` compares current **automatic predictions before overrides** with the supplied human labels on eligible article-country pairs. It reports reviewed/evaluated pair counts, confusion counts, accuracy, precision and recall when their denominators exist. Correcting an automatic error changes the view but remains an error in this comparison. Pending human labels produce null metrics and the dashboard says Not measured.

A convenience review is not an independent held-out benchmark and its recall is conditional on reviewed pairs, not full-corpus recall. A credible evaluation needs a predeclared sample across months/sources, both proposed links and unresolved mentions, independent judgment before model output, and a recorded disagreement/adjudication protocol. Passing software tests is not destination accuracy.

Country review does not validate corpus inclusion, extraction completeness, sentiment accuracy or economic predictions. Those require separate reference data. The sentiment display exposes the actual published-dictionary matches and explains why missing matches are not neutral. The fixed reference vocabulary does not understand all negation, comparisons or export-specific language.

## Counts and reproducibility

Country article counts describe news coverage, not export values or partner shares. Each article contributes once per country; an article can occur under several countries. Monthly indices pool whole-article word counts, not country-specific sentences. Empty months stay missing and country selection does not alter the general index.

`destinations.jsonl` stores country aliases, normalized offsets, automatic and rejected relation evidence, source hashes and configuration hash. It contains no publisher body. Rebuilding broader body mentions requires the local archive or a compatible cache; stale body caches are rejected. `python -m trade_news destinations` refreshes the features and country-validation report without new web collection and preserves existing human reviews.

## Current execution

The primary frame now has 1,011 direct-sitemap press articles in all 80 months, March 2020–October 2026; both domains appear in 78 months. Analdex is complementary. A separate 200-record independent evaluation packet is locked, with zero adjudicated labels. The researcher supplied 309 monthly export observations; retrospective economic comparisons are executed, with assumed timing and adverse diagnostics disclosed in [ECONOMIC_RESULTS_ES.md](ECONOMIC_RESULTS_ES.md). This supersedes earlier pending-data and Analdex-only current-state descriptions. It does not establish human classification accuracy or real-time predictive validity.
