"""Public Analdex WordPress archive, a separately identified institutional source.

This supplements, rather than replaces or bypasses, Google discovery. Source
composition must be reported: institutional articles are not a press census.
"""
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from .articles import read_jsonl, write_jsonl, reference_fingerprint
from .bank_method import clean_text, process_text
from .classification import propose

ORIGIN = "https://www.analdex.org"
AGENT = "ColombiaExportResearch/0.6"


def collect_archive(directory, start, end):
    import trafilatura
    directory = Path(directory)
    archive = directory/"raw"/"publisher_api"
    archive.mkdir(parents=True, exist_ok=True)
    article_dir = directory/"raw"/"articles"
    article_dir.mkdir(parents=True, exist_ok=True)
    robots = RobotFileParser()
    with urlopen(Request(ORIGIN+"/robots.txt", headers={"User-Agent": AGENT}), timeout=20) as response:
        robots_bytes = response.read(1_000_000)
    robots.parse(robots_bytes.decode("utf8", "replace").splitlines())
    (archive/"robots.txt").write_bytes(robots_bytes)
    candidates = {r["record_id"]: r for r in read_jsonl(directory/"headlines_raw.jsonl")}
    manifest = {r["record_id"]: r for r in read_jsonl(directory/"article_manifest.jsonl")}
    requests = []
    page, total_pages = 1, 1
    while page <= total_pages:
        query = urlencode({"search": "exportaciones", "after": start+"T00:00:00", "before": end+"T00:00:00",
                           "per_page": 100, "page": page, "orderby": "date", "order": "asc",
                           "_fields": "id,date,date_gmt,link,title,content"})
        url = ORIGIN+"/wp-json/wp/v2/posts?"+query
        if not robots.can_fetch(AGENT, url):
            raise RuntimeError("Publisher API disallowed by robots.txt")
        cached = archive/f"analdex-{page:03d}.json"
        meta = cached.with_suffix(".meta.json")
        if cached.exists() and meta.exists():
            payload = cached.read_bytes()
            request = json.loads(meta.read_text("utf8"))
            if request["url"] != url or hashlib.sha256(payload).hexdigest() != request["sha256"]:
                raise ValueError("Cached publisher response differs from its query or saved hash; use a new directory")
        else:
            retrieved = datetime.now(timezone.utc).isoformat()
            try:
                with urlopen(Request(url, headers={"User-Agent": AGENT}), timeout=30) as response:
                    payload = response.read(15_000_001)
                    total_pages = int(response.headers.get("X-WP-TotalPages", 1))
                    total = int(response.headers.get("X-WP-Total", 0))
                if len(payload) > 15_000_000:
                    raise ValueError("Publisher response exceeds size limit")
                request = {"url": url, "retrieved_at": retrieved, "status": 200, "page": page,
                           "total_pages": total_pages, "provider_total": total,
                           "sha256": hashlib.sha256(payload).hexdigest()}
                cached.write_bytes(payload)
                meta.write_text(json.dumps(request, indent=2)+"\n", encoding="utf8")
            except HTTPError as error:
                requests.append({"url": url, "retrieved_at": retrieved, "status": "failed", "http_status": error.code})
                break
            time.sleep(2)
        total_pages = request["total_pages"]
        posts = json.loads(payload)
        accepted = 0
        for post in posts:
            date = post["date"][:10]
            if not start <= date < end:
                continue
            link = post["link"]
            identity = hashlib.sha256(link.encode()).hexdigest()[:20]
            title = clean_text(html.unescape(post["title"]["rendered"]))
            record = {"record_id": identity, "title": title, "url": link, "publisher": "Analdex",
                      "publisher_url": ORIGIN, "published_at": post["date_gmt"]+"+00:00",
                      "retrieved_at": request["retrieved_at"], "date_origin": "Publisher WordPress post date/date_gmt",
                      "feed_url": url, "collection_month": date[:7], "discovery_source": "analdex_public_wordpress_archive",
                      "source_post_id": post["id"], "source_response_sha256": request["sha256"]}
            candidates[identity] = record
            accepted += 1
            if identity in manifest:
                continue
            content = post["content"]["rendered"]
            text = trafilatura.extract("<html><body><article>"+content+"</article></body></html>",
                                      include_comments=False, include_tables=False, favor_precision=True, deduplicate=True)
            if not text:
                manifest[identity] = {**record, "fetch_status": "article_text_unavailable"}
                continue
            text = clean_text(text)
            raw_html = content.encode("utf8")
            (article_dir/(identity+".html")).write_bytes(raw_html)
            (article_dir/(identity+".txt")).write_text(text, encoding="utf8")
            manifest[identity] = {**record, "fetch_status": "article_extracted", "text_source": "publisher_article",
                "article_url": link, "resolved_url": link, "publication_date": date, "month": date[:7],
                "publisher_title": title, "date_source": "Publisher WordPress API post.date (local publication date)",
                "publisher_date_value": post["date"], "retrieved_article_at": request["retrieved_at"],
                "reference_fingerprint": reference_fingerprint(), "html_sha256": hashlib.sha256(raw_html).hexdigest(),
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "extraction_method": "trafilatura_2.3.1_precision_public_wordpress_content_v1",
                **process_text(text), **propose(title, text)}
        requests.append({**request, "accepted_items": accepted})
        write_jsonl(directory/"headlines_raw.jsonl", list(candidates.values()))
        write_jsonl(directory/"article_manifest.jsonl", list(manifest.values()))
        print(f"Analdex archive page {page}/{total_pages}: {accepted} real posts", flush=True)
        page += 1
    log_path = directory/"collection_log.json"
    log = json.loads(log_path.read_text("utf8"))
    log["publisher_archive"] = {"source": "Analdex public WordPress archive", "search": "exportaciones",
        "start": start, "end_exclusive": end, "requests": requests,
        "note": "Institutional source supplement; search is not exhaustive. Source/date composition differs from general press."}
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    return requests
