# Data sources and provenance

## Live source used

The included corpus was obtained from **Google News RSS search**, using:

```text
https://news.google.com/rss/search
q=Colombia (exportaciones OR exportación OR exporta OR exportadores OR exportador) after:YYYY-MM-01 before:YYYY-MM-01
hl=es-419 & gl=CO & ceid=CO:es-419
```

See [the search service](https://news.google.com/) and the exact URLs, collection timestamps, HTTP results and SHA-256 response hashes in `data/collection_log.json`. The export-specific run on 2026-11-15 queried May through October 2026. All six requests succeeded: accepted records per month were **18, 10, 46, 20, 15, 43**. **5** additional returned items failed the date/metadata filter. These counts describe this executed retrieval only.

RSS search is a convenience source, not a contracted or documented historical research API with completeness guarantees. Search ranking, coverage, pagination limitations and later provider changes can affect the sample. A response with 100 or more items receives a `possible_provider_cap` flag; being below that heuristic threshold does not establish completeness. Publisher labels and dates are provider-supplied and have not been independently verified against each publisher page.

Only headlines and metadata are collected. Google News links can redirect to publisher articles and may later expire. The collector does not bypass paywalls, scrape article bodies or infer missing article text. Attribution and source URLs stay with the data. Access to metadata does not imply an unrestricted redistribution license; publisher and platform terms still apply.

The search retrieves export-related candidates, including off-topic and service records. Goods-only and outbound-origin filtering occurs locally, after retrieval; exclusions remain in the metadata audit and never enter the index. The collection log describes the query scope; `processing_audit.json` records the narrower goods-export analysis scope.

## Files

| File | Contents |
| --- | --- |
| `headlines_raw.jsonl` | Parsed real metadata before local deduplication/NLP; not full RSS payloads |
| `collection_log.json` | Requested window, exact monthly URLs, timestamps, status, counts and raw XML hashes |
| `headlines.jsonl` | Cleaned metadata, relevance, tags, sentiment and matched evidence |
| `indices.json` | Monthly overall/sector/partner/theme groups, coverage and index/null |
| `processing_audit.json` | Deduplication/exclusion IDs, totals, method version and metadata-file hash |
| `annotations.csv` | Review sample with empty human-reference fields |
| `validation_report.json` | Per-task evaluation state; metrics remain null until labels exist |
| `raw/YYYY-MM.xml` | Original RSS responses retained locally and excluded from Git |

Index files store `export_sentiment_index` (pooled cue balance, −1 to +1), positive/negative cue counts and `headline_tone_index` (separate equal-publisher sensitivity score, −100 to +100). Neither is an official economic statistic.

## Record dictionary

- `record_id`: first 20 hexadecimal characters of SHA-256 of the RSS article link. This identifies a link, not a canonical publisher story.
- `title`, `publisher`, `publisher_url`, `url`: source headline and attribution; article link comes from Google News RSS.
- `published_at`: RSS `pubDate`, converted to UTC. `date_origin` states that the publisher date is not independently verified.
- `retrieved_at`, `feed_url`, `collection_month`: collection provenance.
- `month`: month derived from the UTC provider timestamp.
- `title_clean`, `title_normalized`: readable cleaned text and matching representation.
- `relevant`, `relevance_method`: goods-export inclusion decision and method identifier.
- `scope_status`, `scope_reason`: included, excluded or needs_review, with the decision reason.
- `goods_evidence`, `export_origin_evidence`, `service_evidence`: matched goods terms, Colombian export-origin phrases and service terms (if present).
- `themes`, `sectors`, `partners`, `tag_evidence`: multi-label predictions and exact matched phrases.
- `sentiment`, `tone_score`, `sentiment_evidence`, `sentiment_method`: lexical tone decision, numeric score/null and cue trace.
- `validated_for_domain`: false in this baseline; human evaluation does not automatically certify the model.

Response hashes support local integrity checks when raw archives are available. The committed metadata hash and offline rebuild checks establish internal reproducibility, not independent proof of publisher truth or feed authenticity. Future collection should use a fresh directory to preserve the original snapshot and any annotation work.
