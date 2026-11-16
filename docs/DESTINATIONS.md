# Destinations and geographic evidence

This tab is a project-specific exploratory extension. It is not a destination taxonomy, relation model or result supplied by Banco de la República. The general all-export index and its eligible corpus are unchanged.

## Two distinct modes

**Explicit export links in headlines** is the default. A headline must name Colombia or a Colombian adjective and contain export/foreign-sales wording. A recognized foreign market also needs a bounded directional phrase such as exports *to* a market, or a named buyer/destination role. Only headline evidence is used for these conservative relation proposals. A country merely mentioned in the body is not promoted into this category.

**All market mentions in article text** includes recognized names in the title or retrieved body. These names can identify buyers, suppliers, competitors, policy actors or unrelated context. This mode is explicitly exploratory and cannot establish export direction. It is useful for finding source articles that the conservative headline rules miss.

Both modes are automatic proposals pending human inspection. Explicit wording can describe a historical, potential, disrupted or negated trade relationship; it does not verify a current shipment or its commercial value. No destination has been independently certified by these rules. Missing tags are unresolved evidence, not evidence of no exports.

## Geography and evidence

`trade_news/destinations.py` contains a finite, inspectable vocabulary of Spanish market names and common aliases. Matching ignores accents and case and uses word boundaries. The longest overlapping alias wins, so Asia-Pacific is not automatically counted as Asia. This vocabulary is not a complete named-entity recognizer; unsupported names and ambiguous wording can be missed.

Countries and regions/blocs can be explored separately. Europe is distinct from the European Union. No countries are inferred from a regional label, and no bloc membership is inferred from a country mention. Colombia is not offered as a foreign destination.

`data/destinations.jsonl` holds one evidence record per news record, with the recognized markets, matched aliases, evidence source, offsets in the normalized field, relation rule, title hash, optional body hash and configuration hash. It includes no publisher article body or newly copied article excerpt. The linked publisher article allows a reader to examine context.

`python -m trade_news destinations` rebuilds the evidence without web collection, using the existing local body archive when available. Without that archive, compatible body-derived evidence is preserved from the committed cache; headline evidence remains reproducible directly. Changes to the rules, title or body hash invalidate cached body evidence and require the archived text for a complete rebuild. `python -m trade_news analyze` also refreshes destination evidence after rebuilding the corpus.

## Charts and interpretation

Only eligible, deduplicated articles from the existing corpus enter a market view. Each article contributes once to a selected market. Articles mentioning several markets can appear in several views, so totals across markets overlap. The overview ranks **news coverage**, not export values, trade-partner importance or market shares. No missing geography is redistributed to a country.

Monthly sentiment and uncertainty pool the saved word counts for the entire article texts in the selected subset, using the same formulas as the general series. They do not isolate sentiment in sentences specifically about that market. An article covering several countries can therefore contribute the same whole-article counts to each subset. Publication-month coverage and source composition matter; empty months remain missing.

The general index does not change when the user selects a destination, a geography group or an evidence mode. Geographic relation accuracy and independent destination annotation remain pending. Human corpus/activity decisions and sentiment labels in the existing review sheet do not certify destination tags.
