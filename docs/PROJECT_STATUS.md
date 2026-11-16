# Project status

Version 0.5 focuses the dashboard on General index, Destinations, Articles & evidence, Quality & review and Method. The economic-activity view and all region/bloc destination controls have been removed. Country labels expose headlines, source links, reasons and review status. Sentiment inspection exposes actual matched words and occurrence counts.

The frozen Jan–Oct 2026 snapshot remains 247 real candidates, 196 retrieved article texts and 172 provisionally eligible articles. The general index is byte-identical to the previous release. The revised country rules produce 24 article-country links across five countries; this is limited explicit-headline coverage, not a census of Colombia's foreign destinations.

An actual false destination was found and corrected: Brazil was a competitor in a headline containing `frente a Brasil`. The agent inspected the stored article and headline. That diagnostic is shown transparently and is not counted as a human gold label or benchmark. The direction rule also rejects cases where Colombia is mentioned only after another country's export flow.

Country review is stored separately from corpus/sentiment review. Yes/no/unsure decisions require reviewer provenance, a source explanation and a personal-review declaration. Human changes affect country views, while accuracy compares the automatic predictions before those changes with supplied reference labels. Pending references produce no percentage. Human labels, extraction review and domain accuracy remain pending.

Local verification passed 50 software tests, the feature/aggregate provenance check and Ruff checks. Tests cover the real competitor regression, country-only layout, source evidence, provenance requirements, review persistence, evaluation before overrides and stable general indices. Notebook cells run offline with three plots and fresh collection disabled. None of these software results is an accuracy estimate on real news.

The published dictionary and sentiment/uncertainty formulas remain unchanged. Exact original tokenizer/stopword files, the Bank's curated corpus, econometric validation and forecasting results are not reproduced. Raw publisher text stays in the ignored local archive. November/December are not estimated and a hosted dashboard has not been deployed.
