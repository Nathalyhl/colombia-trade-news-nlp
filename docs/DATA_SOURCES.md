# Data lineage and access

## Committed records

| File | Meaning |
| --- | --- |
| `headlines_raw.jsonl` | Real Google News candidate titles, provider timestamps, publishers and source links; not the NLP input |
| `collection_log.json` | Per-month query URLs, retrieval times, HTTP outcomes, item counts and raw RSS hashes |
| `resolved_urls.jsonl` | Public RSS URL resolution outcomes and resolved publisher links |
| `article_manifest.jsonl` | Every article retrieval outcome; extracted articles carry publisher dates, body hashes, reference fingerprint, counts, matched words and scope/activity proposals |
| `annotations.csv` | Human-review sheet; blank decisions are unreviewed, not negative labels |
| `headlines.jsonl` | Historical filename retained for compatibility; now contains article retrieval records with decisions and duplicate status |
| `indices.json` | Separate provisional and human-reviewed monthly aggregates |
| `processing_audit.json` | Counts, failures, scope proposals, duplicates and snapshot hashes |
| `validation_report.json` | Actual supplied human-reference evaluation, initially pending with null scores |

## Local-only source archive

`data/raw/YYYY-MM.xml` holds RSS responses. `data/raw/articles/<record_id>.html` and `.txt` hold the retrieved public publisher response and extracted article text. The whole directory is ignored by Git. No publisher article body, search snippet or AI-generated substitute is distributed in the feature snapshot.

The repository can reproduce monthly arithmetic and review decisions offline from committed features. Exact source-to-count NLP reproduction requires the local text archive and its saved hashes. A new web retrieval may change or fail, and cannot be assumed byte-identical. The source PDF has its own hash in `reference/manifest.json`.

## Constraints and selection effects

Google News search is not an exhaustive census, a stable historical archive or a representative sampling design. Query vocabulary, provider ranking, domain access, date metadata, article extraction and coverage of the dictionary all affect inclusion. Publisher labels are not independently reconciled to media ownership groups.

The public retrieval pipeline checks publisher domains and robots rules, skips explicit subscription-only material, and records access or extraction failures. It never uses a headline score as a replacement for unavailable article text. Automatic extraction can retain boilerplate or miss portions of text; review the linked article and local archive before treating the corpus as curated. Exact duplicate detection does not remove all syndication or event-level duplication.

Candidate RSS dates and publisher publication dates are retained separately. Only explicit in-window publisher dates determine the index month. Reporting months within an article are different from publication months; the index groups by publication, not by the export-statistics reference period.
