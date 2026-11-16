# Project status

## Implemented

Version 0.4 adds a Destinations tab to the publisher-article measurement pipeline introduced in version 0.3. The pipeline uses the complete BE1340 Annex 3 vocabulary, the published sentiment/uncertainty formulas and the Annex 2 activity labels. The main dashboard shows the general Colombian goods-export news series. Activity and destination exploration and article searches do not alter that primary series. The export-theme filter and the former source-weighted headline score are retired.

The executed Jan–Oct 2026 snapshot contains 247 real candidate records, 196 retrieved article texts and 172 provisionally eligible deduplicated articles. Retrieval failures and publication-date checks are auditable. Raw publisher text remains local and ignored; derived features can be checked offline.

The project includes a local Streamlit dashboard, a Colab/Jupyter analysis notebook, actual source lineage, a human-review interface and sheet, source-reference hashes and software checks. The previous headline snapshot is preserved in repository history and a separate local backup.

Local release verification passed 38 software tests, the offline source-feature/aggregate check and Ruff checks. The tests include destination aliases, explicit links versus geographic mentions, overlapping groups, subset formulas, cached body evidence and stable general-index behavior. Every offline notebook code cell executed, producing three figures from the real snapshot with fresh collection disabled. These checks do not measure classification accuracy on real news.

Destination rules are a project-specific extension, distinct from the Bank's activity taxonomy and measurement method. Strict headline links and broad body/title mentions are separate modes. The published general indices remain byte-identical to version 0.3. See [DESTINATIONS.md](DESTINATIONS.md) for interpretation and limitations.

## Remaining research work

Human corpus review, activity verification, extraction inspection and independent sentiment labels remain pending. No Bank-equivalent accuracy, official endorsement, economic validation, nowcasting or forecasting result is claimed. The exact original stopword list, tokenizer and curated dataset are unavailable from the paper and are not represented as reproduced.

November and December 2026 are not estimated in this frozen snapshot. A hosted dashboard has not been deployed. Software checks validate calculations and behavior; they are not a substitute for the remaining research review.
