# Data lineage and access

## Committed records

| File | Meaning |
| --- | --- |
| `headlines_raw.jsonl` | Real Google News and Analdex public archive discovery records, provider timestamps, publishers and source links; not the NLP input |
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
