# Related research and design implications

## Measurement baseline

[Mora-Quiñones, Orozco-Gallo & Mora-Pérez (2026), BE1340](https://doi.org/10.32468/be.1340) is the chosen baseline. This project implements its published dictionary/counting equations on a different corpus. The original study's curated economic news and econometric results are not reproduced by changing a dashboard's appearance.

## Spanish contextual measurement and independent review

[Dávila and Chasi, “Índice de sentimiento económico”, Banco Central del Ecuador](https://doi.org/10.47550/RCE/35.2.1) compares lexical and transformer models on Spanish economic news, defines a probability balance and evaluates classifications against human judgments. Its classifier-margin review criterion informs the optional diagnostic-priority list. The exact author scripts and model revision were not obtained from the journal record consulted; using public PySentimiento components does not establish an exact replication of that study. This project's monthly aggregation and full-body chunk pooling are explicitly its own adaptations. Its current primary descriptive dashboard series uses these existing contextual predictions; Bank lexical sentiment remains a separate comparison and Bank uncertainty retains its equation. See [the Spanish design guide](DASHBOARD_ES.md).

## Sector and trade applications

[Lee, Kim, Kwon & Yeo (2024), “Maritime supply chain risk sentiment and the Korea trade volume: A news big-data analysis perspective”](https://doi.org/10.1016/j.ajsl.2024.01.001) studies news-derived maritime supply-chain risk alongside trade measures. It supports examining a clearly defined trade-related corpus and an external numerical series. Its risk concept, Korean setting and vocabulary do not validate Colombian export sentiment or the present classifications.

[Pratap, Ranjan, Kishore & Bhoi (2022), Reserve Bank of India, “Forecasting Food Inflation using News-based Sentiment Indicators”](https://www.rbi.org.in/scripts/Bs_viewcontent.aspx?Id=4198) illustrates a sector-specific corpus and explicit comparison with numerical outcomes. Its food-price objective does not supply a ready-made export-growth classifier.

## Context-sensitive extensions, outside this baseline

[Consoli, Barbaglia & Manzan (2022), “Fine-grained, aspect-based sentiment analysis on economic and financial lexicon”](https://doi.org/10.1016/j.knosys.2022.108781) and [Barbaglia, Consoli & Manzan, “Forecasting with Economic News”](https://arxiv.org/abs/2203.15686) motivate distinguishing sentiment attached to a specific economic aspect from other language in an article. This is relevant to the DW reactivation case: political history and the export event can express different aspects. Such an extension would change the measurement method; it must be compared separately against Spanish goods-export human labels rather than silently replacing the Bank baseline.

## Planned empirical discipline

1. Review source extraction and goods-export inclusion independently of scores.
2. Establish human reference labels with explicit instructions and reviewer provenance; report agreement and abstentions.
3. Inspect source composition, lexical support, event duplication and sensitivity to institutional-source dominance.
5. Reserve predictive claims for properly separated time-based out-of-sample evaluation. A visually plausible curve is not validation.

No exact prior replication for this Colombian goods-export corpus is asserted. These studies inform the design; their reported results are not attributed to this project.

## Current execution

The primary frame now has 1,011 direct-sitemap press articles in all 80 months, March 2020–October 2026; both domains appear in 78 months. Analdex is complementary. A separate 200-record independent evaluation packet is locked, with zero adjudicated labels. The researcher supplied 309 monthly export observations; retrospective economic comparisons are executed, with assumed timing and adverse diagnostics disclosed in [ECONOMIC_RESULTS_ES.md](ECONOMIC_RESULTS_ES.md). This supersedes earlier pending-data and Analdex-only current-state descriptions. It does not establish human classification accuracy or real-time predictive validity.
