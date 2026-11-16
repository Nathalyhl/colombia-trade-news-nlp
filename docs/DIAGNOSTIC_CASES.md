# Real diagnostic cases: counts versus interpretation

These source-linked cases explain implementation behavior. They are not human reference annotations, solved semantic tasks or a benchmark.

## Reactivation and a single negative dictionary match

[DW, “Colombia reactivará exportaciones de carbón a Israel”](https://www.dw.com/es/colombia-reactivar%C3%A1-exportaciones-de-carb%C3%B3n-a-israel/a-78466460), publisher date 22 August 2026, record `b30d353a15880d52e0b3`. The archived body discusses the planned resumption and the previous suspension. Exact Annex 3 matching finds `suspensión` once, with no positive match. P=0, N=1 yields −1 for this article. The published list contains `reactivación` and `reactivándose`, but not `reactivará`. No form is added or polarity reversed to make the headline appear positive.

This is a sparse lexical-balance observation over the article body, not a judgment that reopening trade is economically harmful. The article remains in the eligible sample. Its words are pooled with other articles before monthly division; −1 is not averaged into the monthly index as an article-level vote. The dashboard shows the one-word support explicitly. An export-event or aspect-specific interpretation would require a separately specified method and independent labels.

## Competitor versus destination

Record `a1348320f184c51f24f5`, title “Exportaciones de ganado caen 49,6% y el peso fuerte le resta mercado a Colombia frente a Brasil”, compares Colombia with Brazil. The country rule retains the comparison evidence and does not assign Brazil as a destination. This diagnostic motivated an explicit comparison guard, but it does not establish overall country-classifier accuracy.

## Publication and reported periods

An article published in 2026 may report 2025 totals or year-on-year changes. The publication date places it in the news index. A previous year in the headline is not proof of a date error. The relevant export-statistics period, comparison base and value/volume unit must be separately verified before a later numerical comparison. No such periods or numerical outcomes have been inferred merely from `creció` or a year mention.
