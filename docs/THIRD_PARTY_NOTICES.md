# Third-party material and attribution

## PySentimiento and RoBERTuito comparison

The optional comparison uses `pysentimiento/robertuito-sentiment-analysis`, published by the PySentimiento authors. The model card identifies Spanish TASS tweet training data and requests citation of PySentimiento, RoBERTuito and TASS. It is not a model trained by this project on Colombian export news.

`trade_news/pysentimiento_preprocessing.py` preserves upstream `pysentimiento/preprocessing.py` below an attribution header, from source commit `60822acfd805ad5d95437c695daa33c18dbda060`. Its source is https://github.com/pysentimiento/pysentimiento. The upstream scientific/non-commercial use notice is reproduced in `reference/PYSENTIMIENTO_LICENSE.txt`; model and dataset restrictions also apply. Model weights are downloaded from their public source when needed and are not redistributed in this repository. Their revision and SHA-256 hashes are in `reference/contextual_model.json`.

`trade_news/contextual.py` is this project's local inference and aggregation adapter. It follows the published softmax/argmax model-output logic; nonoverlapping full-article chunking and token-weighted chunk pooling are explicit project choices. Dávila and Chasi's Ecuador economic-news study is credited as a related application, not represented as source code we obtained or results we replicated. No published benchmark accuracy is assigned to this corpus.

## Published dictionary and activities

`reference/moreno_gonzalez_2020.csv` transcribes the complete word lists in Annex 3a and 3b of Mora-Quiñones, Orozco-Gallo & Mora-Pérez (2026), *Sentiment and Uncertainty Indices from economic news in Colombia*, Borradores de Economía 1340, Banco de la República, DOI https://doi.org/10.32468/be.1340. The paper credits the dictionary to **Moreno and González (2020)**; that credit is retained. `reference/activities.csv` transcribes Annex 2 labels.

The [source repository item](https://repositorio.banrep.gov.co/items/608d9c82-f70c-4ca1-89e4-d5f8be6f6c45) identifies the document license as [Creative Commons Attribution–NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/). Source lists are reformatted to CSV with page/provenance columns, without altering words, polarity or activity labels. This academic adaptation does not imply endorsement by the authors or Banco de la República. The reference license and attribution remain applicable to that third-party material.

## Spanish stopwords

`reference/spanish_stopwords.txt` freezes the Spanish file from the [NLTK stopwords corpus](https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/stopwords.zip). The corpus README credits the PostgreSQL/Snowball stopword collection. This is our implementation choice, not a file supplied by the Bank. The [Snowball Spanish list](https://snowballstem.org/algorithms/spanish/stop.txt) and [Snowball license](https://snowballstem.org/license.html) document its upstream source. The applicable Snowball notice is retained in `reference/STOPWORDS_LICENSE.txt`.

## News publishers and software

Publisher articles remain the material of their respective sources. The repository provides source links, metadata and derived word-count features; publisher bodies and HTML are not included in the release. These notices do not grant rights over publisher articles or the repository’s original code.

Python dependencies retain their respective upstream licenses, available in their installed distributions. No private thesis code, credentials or proprietary trade database is required by this project.
