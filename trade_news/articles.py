"""Retrieve public publisher article text; never substitute a headline for a body."""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from .bank_method import clean_text, process_text
from .classification import normalized, propose

USER_AGENT = "ColombiaExportResearch/0.3"


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text("utf8").splitlines() if s.strip()]


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows), encoding="utf8")


def reference_fingerprint():
    from .bank_method import REFERENCE
    return hashlib.sha256((REFERENCE / "manifest.json").read_bytes()).hexdigest()


def publication_metadata(html_bytes):
    from lxml import html as lhtml
    tree = lhtml.fromstring(html_bytes)
    objects = []
    for value in tree.xpath('//script[@type="application/ld+json"]/text()'):
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            continue
        def visit(obj):
            if isinstance(obj, list):
                for item in obj:
                    visit(item)
            elif isinstance(obj, dict):
                kinds = obj.get("@type", [])
                kinds = [kinds] if isinstance(kinds, str) else kinds
                if any(k in {"NewsArticle", "Article", "BlogPosting", "ReportageNewsArticle"} for k in kinds):
                    objects.append(obj)
                if "@graph" in obj:
                    visit(obj["@graph"])
        visit(parsed)
    for obj in objects:
        if obj.get("isAccessibleForFree") in {False, "false", "False"}:
            return {"paywall": True}
    dates = [(obj.get("datePublished"), "JSON-LD datePublished") for obj in objects if obj.get("datePublished")]
    dates += [(date, "meta article:published_time") for date in tree.xpath('//meta[@property="article:published_time"]/@content')]
    if not dates:
        return {"paywall": False, "publication_date": None, "date_source": "missing_explicit_publication_date"}
    value, source = dates[0]
    date = str(value)[:10]
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        date = None
    titles = [obj["headline"] for obj in objects if obj.get("headline")]
    titles += tree.xpath('//meta[@property="og:title"]/@content')
    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    return {"paywall": False, "publication_date": date, "date_source": source,
            "publisher_date_value": value, "publisher_title": titles[0] if titles else None,
            "canonical_url": canonical[0] if canonical else None}


def fetch_public_article(record, url, directory, robots_cache, start, end):
    import trafilatura
    row = {**record, "resolved_url": url, "retrieved_article_at": datetime.now(timezone.utc).isoformat(),
           "reference_fingerprint": reference_fingerprint(), "fetch_status": "not_fetched", "text_source": None}
    try:
        parsed = urlparse(url)
        source_host = urlparse(record.get("publisher_url", "")).hostname or ""
        host = parsed.hostname or ""
        root = source_host.removeprefix("www.")
        if parsed.scheme not in {"https", "http"} or not root or not (host == root or host.endswith("."+root)):
            return {**row, "fetch_status": "publisher_domain_mismatch"}
        origin = parsed.scheme+"://"+parsed.netloc
        if origin not in robots_cache:
            robots = RobotFileParser(origin+"/robots.txt")
            try:
                with urlopen(Request(origin+"/robots.txt", headers={"User-Agent": USER_AGENT}), timeout=12) as response:
                    rules = response.read(1_000_000).decode("utf8", "replace")
                robots.parse(rules.splitlines())
                robots_cache[origin] = robots
            except Exception as error:
                robots_cache[origin] = str(error)
        robots = robots_cache[origin]
        if isinstance(robots, str):
            return {**row, "fetch_status": "robots_unavailable", "fetch_error": robots}
        if not robots.can_fetch(USER_AGENT, url):
            return {**row, "fetch_status": "robots_disallowed"}
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=15) as response:
            payload = response.read(5_000_001)
            final_url = response.url
            content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type or len(payload) > 5_000_000:
            return {**row, "fetch_status": "unsupported_or_oversized_response"}
        metadata = publication_metadata(payload)
        row.update(metadata)
        if metadata.get("paywall"):
            return {**row, "fetch_status": "paywall_not_accessed"}
        if not metadata.get("publication_date"):
            return {**row, "fetch_status": "publication_date_unverified"}
        date = metadata["publication_date"]
        if not start <= date < end:
            return {**row, "fetch_status": "publisher_date_outside_period"}
        body = trafilatura.extract(payload, url=final_url, include_comments=False, include_tables=False,
                                    favor_precision=True, deduplicate=True)
        if not body:
            return {**row, "fetch_status": "article_text_unavailable"}
        text = clean_text(body)
        if any(phrase in normalized(text) for phrase in ["suscribete para continuar", "contenido exclusivo para suscriptores", "inicia sesion para seguir leyendo", "radware captcha"]):
            return {**row, "fetch_status": "access_restriction_not_bypassed"}
        publisher_title = metadata.get("publisher_title") or record["title"]
        lines = text.splitlines()
        if lines and normalized(lines[0]) == normalized(publisher_title):
            text = "\n".join(lines[1:]).strip()
        archive = directory / "raw" / "articles"
        archive.mkdir(parents=True, exist_ok=True)
        (archive / (record["record_id"]+".html")).write_bytes(payload)
        (archive / (record["record_id"]+".txt")).write_text(text, encoding="utf8")
        return {**row, "fetch_status": "article_extracted", "text_source": "publisher_article",
                "article_url": metadata.get("canonical_url") or final_url, "publication_date": date, "month": date[:7],
                "html_sha256": hashlib.sha256(payload).hexdigest(), "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "extraction_method": "trafilatura_2.3.1_precision_no_comments_no_tables",
                **process_text(text), **propose(publisher_title, text)}
    except Exception as error:
        return {**row, "fetch_status": "fetch_failed", "fetch_error": f"{type(error).__name__}: {error}"}


def acquire(directory, batch_size=30):
    from googlenewsdecoder import gnews_decoder_async
    directory = Path(directory)
    candidates = read_jsonl(directory / "headlines_raw.jsonl")
    log = json.loads((directory / "collection_log.json").read_text("utf8"))
    cache_path = directory / "resolved_urls.jsonl"
    resolutions = {r["record_id"]: r for r in read_jsonl(cache_path)} if cache_path.exists() else {}
    missing = [r for r in candidates if r["record_id"] not in resolutions]
    for offset in range(0, len(missing), batch_size):
        batch = missing[offset:offset+batch_size]
        decoded = asyncio.run(gnews_decoder_async([r["url"] for r in batch], concurrency=2, timeout=10, interval=.3))
        if not isinstance(decoded, list) or len(decoded) != len(batch):
            raise RuntimeError("Unexpected decoder batch result; no article URL will be guessed")
        for record, result in zip(batch, decoded):
            resolutions[record["record_id"]] = {"record_id": record["record_id"], "rss_url": record["url"],
                                                 "resolved_at": datetime.now(timezone.utc).isoformat(), **result}
        write_jsonl(cache_path, list(resolutions.values()))
        print(f"Resolved {min(offset+batch_size, len(missing))}/{len(missing)} candidate links", flush=True)
        if any("429" in str(r) or "captcha" in str(r).lower() for r in decoded):
            print("Provider rate/access limit encountered; remaining links left unresolved", flush=True)
            break
    manifest_path = directory / "article_manifest.jsonl"
    records = {r["record_id"]: r for r in read_jsonl(manifest_path)} if manifest_path.exists() else {}
    robots_cache = {}
    for record in candidates:
        identity = record["record_id"]
        if identity in records:
            continue
        decoded = resolutions.get(identity, {})
        if not decoded.get("success"):
            records[identity] = {**record, "fetch_status": "url_unresolved", "resolution_error": decoded.get("message", "not attempted")}
        else:
            records[identity] = fetch_public_article(record, decoded["decoded_url"], directory, robots_cache, log["start"], log["end_exclusive"])
            time.sleep(.3)
        write_jsonl(manifest_path, list(records.values()))
        if len(records) % 10 == 0:
            print(f"Processed {len(records)}/{len(candidates)} article candidates", flush=True)
    return list(records.values())
