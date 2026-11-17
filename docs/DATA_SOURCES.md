# Data lineage and access

## Optional contextual comparison

`contextual_scores.jsonl` contains actual local pretrained-model predictions for eligible articles, with independent body/headline probabilities, argmax classes, probability balances, token/chunk counts and source hashes. It contains no publisher body text. `contextual_manifest.json` records completion, the corpus fingerprint, fixed model revision, upstream source commit, model/preprocessing file hashes and inference-library versions. `contextual_indices.json` stores monthly equal-article probability-balance means for all eligible articles and for the dictionary-matched subset. These are separate from the BE1340 word-count aggregates in indices.json.

The checkpoint and tokenizer file fingerprints are frozen in `reference/contextual_model.json`; the upstream scientific/non-commercial-use notice is preserved separately. Weights stay outside the release and can be downloaded from the public fixed revision. Rebuilding saved monthly arithmetic does not require model weights; reproducing source-text inference requires the optional environment and the ignored publisher archive. See CONTEXTUAL_REPLICATION_ES.md and CONTEXTUAL_RESULTS_ES.md for the adaptation boundary and actual outputs.

## Committed records

| File | Meaning |
| --- | --- |
| `headlines_raw.jsonl` | Real publisher-declared sitemap, Google News and Analdex discovery records; date hints remain distinct from verified article publication dates; not the NLP input |
| `collection_log.json` | Per-month query URLs, retrieval times, HTTP outcomes, item counts and raw RSS hashes |
| `resolved_urls.jsonl` | Public RSS URL resolution outcomes and resolved publisher links |
| `article_manifest.jsonl` | Every article retrieval outcome; extracted articles carry publisher dates, body hashes, reference fingerprint, counts, matched words and scope/activity proposals |
| `annotations.csv` | Human-review sheet; blank decisions are unreviewed, not negative labels |
| `headlines.jsonl` | Historical filename retained for compatibility; now contains article retrieval records with decisions and duplicate status |
| `indices.json` | Separate provisional and human-reviewed monthly aggregates |
| `processing_audit.json` | Counts, failures, scope proposals, duplicates and snapshot hashes |
| `validation_report.json` | Actual supplied human-reference evaluation, initially pending with null scores |
| `destinations.jsonl` | Countries-only automatic links, country mentions and rejected comparison/source evidence, with source and configuration hashes |
| `destination_reviews.csv` | Actual human article-country decisions, reviewer, rationale, declared human origin and source headline hash; initially header only |
| `destination_validation.json` | Metrics against supplied human country labels, evaluated before overrides; initially pending with null scores |

## Local-only source archive

`data/raw/YYYY-MM.xml` holds RSS responses. `data/raw/articles/<record_id>.html` and `.txt` hold the retrieved public publisher response and extracted article text. The whole directory is ignored by Git. No publisher article body, search snippet or AI-generated substitute is distributed in the feature snapshot.

The repository can reproduce monthly arithmetic and review decisions offline from committed features. Exact source-to-count NLP reproduction requires the local text archive and its saved hashes. A new web retrieval may change or fail, and cannot be assumed byte-identical. The source PDF has its own hash in `reference/manifest.json`.

`data/raw/publisher_api/` stores Analdex public API response pages, metadata and robots rules. `collection_log.json.publisher_archive` records the exact search, page count, accepted item count, hashes and retrieval times. `discovery_source=analdex_public_wordpress_archive` and `source_post_id` identify these records. They use SHA-256 of the publisher link for the record ID, while RSS candidates use the RSS link. Canonical URL and exact extracted-text deduplication are applied across routes.

Analdex is an industry association/institutional publisher. Its historical articles and trade reports differ from a general press sample. Its WordPress API publication fields are explicit publisher dates, a distinct provenance from web-page JSON-LD metadata. Full content is used locally but is not redistributed. Counts and title links alone permit feature-aggregate reproduction; text-level reproduction requires the archive.

## Constraints and selection effects

Google News search is not an exhaustive census, a stable historical archive or a representative sampling design. Query vocabulary, provider ranking, domain access, date metadata, article extraction and coverage of the dictionary all affect inclusion. Publisher labels are not independently reconciled to media ownership groups.

The public retrieval pipeline checks publisher domains and robots rules, skips explicit subscription-only material, and records access or extraction failures. It never uses a headline score as a replacement for unavailable article text. Automatic extraction can retain boilerplate or miss portions of text; review the linked article and local archive before treating the corpus as curated. Exact duplicate detection does not remove all syndication or event-level duplication.

Candidate RSS dates and publisher publication dates are retained separately. Only explicit in-window publisher dates determine the index month. Reporting months within an article are different from publication months; the index groups by publication, not by the export-statistics reference period.

## Additional review artifacts

review_sample.csv contains 60 real retrieved-source metadata records with blank human judgments; review_sample_manifest.json records deterministic diagnostic selection and its feature hash. These are separate from active annotations.csv and do not change human-label metrics. Document-role and screening proposals are derived features, not source-supplied labels. Publisher domains are grouped without overwriting the original publisher label.

## Primary historical press frame and numerical input

The primary frame uses publisher-declared sitemaps from Valora Analitik and La República; El Colombiano adds complementary 2020 texts. Raw compressed XML responses and request hashes remain local. lastmod is never accepted as an article publication date. Source-specific article containers exclude linked recommendations and exact personalization blocks, with extracted-body hashes retained. Access refusals are recorded; no authentication, CAPTCHA or subscription restriction is bypassed. Discovery is vocabulary-limited and exact deduplication is not event-level deduplication.

`source_coverage.json` fixes the coverage-based period, identifies single-source months and retains strict-window sensitivities. `study_manifest.json` records assembly and corpus hashes. `evaluation_sample_manifest.json` locks a 200-record independent sample; the three `evaluation_*.csv` files contain blank human fields. `independent_evaluation.json` cannot report accuracy without actual references.

`exports_monthly_supplied.csv` contains 309 numeric observations extracted from the researcher-supplied workbook, with SHA-256 and cell references. `exports_source_audit.json` reconciles totals without redistributing the workbook. Original release/vintage dates remain blank. `economic_*.json` files distinguish assumed-timing scenarios, diagnostics, skipped folds and source/reporting sensitivities. See ECONOMIC_RESULTS_ES.md for partial source cross-checks and interpretation limits.
