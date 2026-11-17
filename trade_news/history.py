"""Publisher-declared sitemap discovery, independently of Google News redirects.

Sitemap lastmod is never used as an article publication date. All discovered
URLs still require dated publisher text, conservative scope screening and review.
"""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import time
from threading import Lock
from urllib.error import HTTPError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from lxml import etree

from .articles import fetch_public_article, read_jsonl, write_jsonl
from .classification import normalized

AGENT = "ColombiaExportResearch/1.0"
SOURCES = {
    "valora": {"publisher": "Valora Analitik", "origin": "https://www.valoraanalitik.com", "index": "/sitemap.xml"},
    "larepublica": {"publisher": "La República", "origin": "https://www.larepublica.co", "index": "/sitemapindex"},
    "elcolombiano": {"publisher": "El Colombiano", "origin": "https://www.elcolombiano.com", "index": "/megasitemap.xml"},
}
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf8")


def read_sitemap(payload):
    """Parse local XML without external entities; keep direct loc, not image loc."""
    if payload[:2] == b"\x1f\x8b":
        payload = gzip.decompress(payload)
    if len(payload) > 50_000_000:
        raise ValueError("Expanded sitemap exceeds size limit")
    root = etree.fromstring(payload, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    indexed = etree.QName(root).localname == "sitemapindex"
    result = []
    for node in root:
        loc = node.xpath('./*[local-name()="loc"]/text()')
        if not loc:
            continue
        dates = node.xpath('.//*[local-name()="publication_date"]/text()')
        titles = node.xpath('.//*[local-name()="title"]/text()')
        result.append({"url": loc[0].strip(), "publication_hint": dates[0] if dates else None,
                       "sitemap_title": titles[0] if titles else None})
    return indexed, result


def relevant_url(url):
    # Selection frame only: final inclusion uses the actual title and full body.
    return bool(re.search(r"\bexport\w*\b|\bventas externas\b", normalized(unquote(urlparse(url).path))))


def archive_month(url):
    match = re.search(r"articles_([A-Za-z]+)_(\d{4})\.xml", url)
    if match and match[1] in MONTH_NAMES:
        return f"{match[2]}-{MONTH_NAMES.index(match[1])+1:02d}"
    return None


class PublisherSession:
    def __init__(self, directory, source):
        self.directory = Path(directory)/"raw/sitemaps"/source
        self.directory.mkdir(parents=True, exist_ok=True)
        self.source = source
        self.config = SOURCES[source]
        self.requests = []
        self.last_request = 0.0
        self.blocked = False
        self.robots = None

    def get(self, url, robots=False):
        origin = self.config["origin"]
        if urlparse(url).hostname != urlparse(origin).hostname:
            raise ValueError("Sitemap URL outside configured publisher")
        if self.blocked:
            raise RuntimeError("Publisher requests stopped after access/rate restriction")
        if not robots and (not self.robots or not self.robots.can_fetch(AGENT, url)):
            raise RuntimeError("Publisher robots rules do not allow this path")
        identity = hashlib.sha256(url.encode()).hexdigest()
        cached, meta = self.directory/(identity+".gz"), self.directory/(identity+".json")
        if cached.exists() and meta.exists():
            payload = gzip.decompress(cached.read_bytes())
            record = json.loads(meta.read_text("utf8"))
            if record["url"] != url or hashlib.sha256(payload).hexdigest() != record["sha256"]:
                raise ValueError("Cached response provenance mismatch")
            self.requests.append({**record, "used_cached_response": True})
            return payload, record
        time.sleep(max(0, 1.0-(time.monotonic()-self.last_request)))
        record = {"url": url, "retrieved_at": now(), "source": self.source}
        try:
            with urlopen(Request(url, headers={"User-Agent": AGENT}), timeout=30) as response:
                payload = response.read(50_000_001)
                record.update(http_status=response.status, response_url=response.url)
            if len(payload) > 50_000_000:
                raise ValueError("Response exceeds size limit")
            if b"captcha" in payload[:10000].lower() and not robots:
                self.blocked = True
                raise RuntimeError("Publisher access challenge; not bypassed")
            record.update(status="retrieved", sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))
            cached.write_bytes(gzip.compress(payload))
            save_json(meta, record)
        except HTTPError as error:
            record.update(status="failed", http_status=error.code, error=str(error))
            self.blocked = error.code in {403, 429}
            self.requests.append(record)
            raise
        finally:
            self.last_request = time.monotonic()
        self.requests.append(record)
        return payload, record

    def load_robots(self):
        payload, _ = self.get(self.config["origin"]+"/robots.txt", robots=True)
        self.robots = RobotFileParser()
        self.robots.parse(payload.decode("utf8", "replace").splitlines())


def discover_source(directory, source, start, end):
    session = PublisherSession(directory, source)
    config = SOURCES[source]
    output = Path(directory)
    candidates, sitemap_log = {}, []
    started = now()
    try:
        session.load_robots()
        index_url = config["origin"]+config["index"]
        payload, _ = session.get(index_url)
        indexed, children = read_sitemap(payload)
        if not indexed:
            raise ValueError("Expected publisher sitemap index")
        for child in children:
            url = child["url"]
            if source == "valora" and not re.search(r"/post-sitemap\d*\.xml$", url):
                continue
            if source == "larepublica":
                month = archive_month(url)
                if not month or not start[:7] <= month < end[:7]:
                    continue
            try:
                content, response = session.get(url)
                nested, entries = read_sitemap(content)
                if nested:
                    raise ValueError("Unexpected nested sitemap index")
                accepted = 0
                dates = [e["publication_hint"][:10] for e in entries if e["publication_hint"]]
                for entry in entries:
                    if not relevant_url(entry["url"]):
                        continue
                    hint = entry["publication_hint"]
                    if hint and not start <= hint[:10] < end:
                        continue
                    identity = hashlib.sha256(entry["url"].encode()).hexdigest()[:20]
                    candidates[identity] = {"record_id": identity, "url": entry["url"],
                        "title": entry["sitemap_title"] or unquote(urlparse(entry["url"]).path).strip('/').replace('-', ' '),
                        "publisher": config["publisher"], "publisher_url": config["origin"],
                        "retrieved_at": response["retrieved_at"], "published_at": hint,
                        "date_origin": "Sitemap hint only; publisher article date still required",
                        "publication_hint": hint, "archive_month_hint": archive_month(url),
                        "feed_url": url, "source_response_sha256": response["sha256"],
                        "discovery_source": "publisher_declared_sitemap", "source_key": source}
                    accepted += 1
                sitemap_log.append({"url": url, "status": "parsed", "article_urls": len(entries), "export_candidates": accepted,
                                    "publication_hint_first": min(dates) if dates else None, "publication_hint_last": max(dates) if dates else None})
                print(f"{source}: {len(sitemap_log)} sitemaps; {len(candidates)} export URL candidates", flush=True)
            except Exception as error:
                sitemap_log.append({"url": url, "status": "failed", "error": str(error)})
                if session.blocked:
                    break
            finally:
                write_jsonl(output/(source+"_candidates.jsonl"), sorted(candidates.values(), key=lambda r: r["url"]))
                save_json(output/(source+"_discovery.json"), {"source": source, "started_at": started,
                    "start": start, "end_exclusive": end, "status": "running", "sitemaps": sitemap_log, "requests": session.requests})
        status = "incomplete_access_restriction" if session.blocked else "completed_with_failures" if any(r["status"] == "failed" for r in sitemap_log) else "complete"
    except Exception as error:
        status = "failed"
        sitemap_log.append({"status": "failed", "error": str(error)})
    report = {"source": source, "started_at": started, "completed_at": now(), "start": start, "end_exclusive": end,
              "status": status, "candidates": len(candidates), "sitemaps": sitemap_log, "requests": session.requests,
              "selection": "Export-related URL terms; hints narrow discovery only; explicit article dates required; lastmod never used as publication."}
    save_json(output/(source+"_discovery.json"), report)
    return report


def discover(directory, start="2020-03-01", end="2026-11-01", sources=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    chosen = list(sources or SOURCES)
    with ThreadPoolExecutor(max_workers=len(chosen)) as pool:
        reports = list(pool.map(lambda source: discover_source(directory, source, start, end), chosen))
    combined = {}
    for source in chosen:
        path = directory/(source+"_candidates.jsonl")
        if path.exists():
            combined.update({r["record_id"]: r for r in read_jsonl(path)})
    write_jsonl(directory/"headlines_raw.jsonl", sorted(combined.values(), key=lambda r: r["url"]))
    save_json(directory/"discovery_report.json", {"sources": reports, "candidate_urls": len(combined), "status": "discovery_only_not_article_evidence"})
    return reports


def fetch_source(directory, source, start, end):
    directory = Path(directory)
    candidates = read_jsonl(directory/(source+"_candidates.jsonl"))
    path = directory/(source+"_articles.jsonl")
    existing = {r["record_id"]: r for r in read_jsonl(path)} if path.exists() else {}
    robots_cache = {}
    pending = iter(r for r in candidates if r["record_id"] not in existing)
    gate, last_start = Lock(), [0.0]

    def limited(result):
        return result.get("fetch_error", "").startswith(("HTTPError: HTTP Error 403", "HTTPError: HTTP Error 429")) or result.get("fetch_status") in {
            "access_restriction_not_bypassed", "robots_unavailable", "robots_disallowed"}

    def retrieve(record):
        with gate:
            time.sleep(max(0, 1.0-(time.monotonic()-last_start[0])))
            last_start[0] = time.monotonic()
        return fetch_public_article(record, record["url"], directory, robots_cache, start, end)

    # Initialize the shared robots cache before two bounded requests can overlap.
    first = next(pending, None)
    if first:
        result = retrieve(first)
        existing[first["record_id"]] = result
        write_jsonl(path, list(existing.values()))
        if limited(result):
            return list(existing.values())
    stopped = False
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            running = {}
            for _ in range(2):
                record = next(pending, None)
                if record:
                    running[pool.submit(retrieve, record)] = record
            while running:
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for future in done:
                    record = running.pop(future)
                    result = future.result()
                    existing[record["record_id"]] = result
                    stopped = stopped or limited(result)
                    if len(existing) % 20 == 0:
                        print(f"{source}: retrieved {len(existing)}/{len(candidates)} outcomes", flush=True)
                    if len(existing) % 10 == 0:
                        write_jsonl(path, list(existing.values()))
                if not stopped:
                    while len(running) < 2:
                        record = next(pending, None)
                        if not record:
                            break
                        running[pool.submit(retrieve, record)] = record
    finally:
        write_jsonl(path, list(existing.values()))
    if stopped:
        print(f"{source}: publisher access restriction; stopped further requests", flush=True)
    return list(existing.values())


def fetch(directory, start="2020-03-01", end="2026-11-01", sources=None):
    chosen = list(sources or SOURCES)
    with ThreadPoolExecutor(max_workers=len(chosen)) as pool:
        groups = list(pool.map(lambda source: fetch_source(directory, source, start, end), chosen))
    rows = [row for group in groups for row in group]
    write_jsonl(Path(directory)/"article_manifest.jsonl", rows)
    save_json(Path(directory)/"retrieval_report.json", {"completed_at": now(), "sources": chosen,
        "recorded_outcomes": len(rows), "start": start, "end_exclusive": end,
        "note": "Completion of the scheduled acquisition; inspect individual failures and unattempted records before claiming source coverage."})
    return rows
