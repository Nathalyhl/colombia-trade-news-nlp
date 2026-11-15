# Reference study and replication boundary

Rocío Clara Alexandra Mora-Quiñones, Antonio José Orozco-Gallo and Dora Alicia Mora-Pérez (2026). *Sentiment and Uncertainty Indices from economic news in Colombia*. Borradores de Economía 1340, Banco de la República. [DOI](https://doi.org/10.32468/be.1340); [official summary](https://investiga.banrep.gov.co/es/borradores/be-1340); [repository item and license](https://repositorio.banrep.gov.co/items/608d9c82-f70c-4ca1-89e4-d5f8be6f6c45).

The study covers general national and regional economic news. Its manually assembled corpus contains 59,648 articles from March 2020 to September 2024. Economic activities are used for classification; the reported indices include national and regional aggregates. It is not an export-theme dashboard. This project narrows the corpus to Colombian goods exports in 2026 and keeps a general monthly indicator as its primary view.

Page references below use the printed page numbers; PDF page numbers include three opening pages.

| Component | Source | This project |
| --- | --- | --- |
| Sentiment | Eq. 1, p. 8 (PDF 11) | Same pooled positive-minus-negative / positive-plus-negative form |
| Uncertainty | Eq. 2, p. 8 (PDF 11) | Same six forms per 1,000 processed words |
| Short text/sentences | Diagram 1, p. 9 (PDF 12) | 50-character text cutoff and >5 post-stopword words per sentence |
| Polarity dictionary | Annex 3a/3b, pp. 37–38 (PDF 40–41), attributed to Moreno & González (2020) | All 188 positive and 376 negative forms, unchanged, with source page per entry |
| Activities | Annex 2, p. 36 (PDF 39) | All 18 original labels; Global Context for several activities, Other Activity includes foreign trade |
| Tokenizer and stopword file | Exact files/code not supplied | Documented Unicode tokenizer and frozen NLTK Spanish stopwords; not claimed to be identical |
| Corpus construction | Professional manual selection and classification | Google News discovery and public publisher extraction; automatic proposals pending actual human review |
| Time and geography | March 2020–September 2024; national and seven regional groupings | Jan–Oct 2026; Colombian goods exports to the world; no regional series inferred |
| Econometric evaluation | DFM/ARMAX and activity comparisons in the paper | Not reproduced; ten months and no independent human labels do not support an equivalent claim |

`reference/manifest.json` identifies the source PDF by SHA-256, table extraction, source license and frozen reference-file hashes. Source words and labels were extracted from the actual tables and visually checked. Formatting changes put the lists into CSV; words were not extended or assigned new polarity. The original paper is not represented as this project’s own research.

“Replicate” here therefore means implement the published **measurement procedure where specified**, documenting unspecified choices and changes of corpus. It does not mean duplicate the Bank’s full curated dataset, original program, published series or predictive findings.
