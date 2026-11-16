"""Collect real headline metadata from Google News RSS without article scraping."""
from datetime import datetime, timezone, date
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import xml.etree.ElementTree as ET

SCOPE = "Colombian exports to the world"


def search_url(start, end):
    query = f'Colombia (exportaciones OR exportación OR exporta OR exportadores OR exportador) after:{start} before:{end}'
    return "https://news.google.com/rss/search?" + urlencode({"q": query, "hl": "es-419", "gl": "CO", "ceid": "CO:es-419"})


def month_windows(start, end):
    first, stop = date.fromisoformat(start), date.fromisoformat(end)
    if first >= stop or first.day != 1 or stop.day != 1:
        raise ValueError("Use increasing first-of-month dates; the end is exclusive")
    while first < stop:
        following = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
        yield first.isoformat(), following.isoformat()
        first = following


def parse_feed(payload, feed_url, retrieved_at, start, end):
    root = ET.fromstring(payload)
    records, rejected = [], 0
    for item in root.findall(".//item"):
        title, link = item.findtext("title", "").strip(), item.findtext("link", "").strip()
        source = item.find("source")
        try:
            published = parsedate_to_datetime(item.findtext("pubDate", ""))
            if published.tzinfo is None:
                raise ValueError("Missing timezone")
            published = published.astimezone(timezone.utc)
            if not start <= published.date().isoformat() < end:
                raise ValueError("Out-of-window provider date")
            if not title or urlparse(link).scheme not in {"http", "https"}:
                raise ValueError("Missing headline or article link")
        except (ValueError, TypeError, OverflowError):
            rejected += 1
            continue
        publisher = source.text.strip() if source is not None and source.text else "Unknown publisher"
        suffix = " - " + publisher
        if title.endswith(suffix):
            title = title[:-len(suffix)]
        records.append({
            "record_id": hashlib.sha256(link.encode()).hexdigest()[:20],
            "title": title, "url": link, "publisher": publisher,
            "publisher_url": source.get("url", "") if source is not None else "",
            "published_at": published.isoformat(), "retrieved_at": retrieved_at,
            "date_origin": "Google News RSS pubDate; publisher date not independently verified",
            "feed_url": feed_url, "collection_month": start[:7],
        })
    return records, {"provider_items": len(root.findall('.//item')), "rejected_items": rejected}


def collect(start, end, output, pause=1.0):
    output = Path(output)
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    all_records, requests = [], []
    limited = False
    for left, right in month_windows(start, end):
        if limited:
            requests.append({"month": left[:7], "status": "not_attempted", "reason": "Provider access/rate limit earlier in this run"})
            continue
        url = search_url(left, right)
        retrieved = datetime.now(timezone.utc).isoformat()
        request = Request(url, headers={"User-Agent": "ColombiaTradeNewsResearch/0.1 (headline metadata only)"})
        try:
            with urlopen(request, timeout=30) as response:
                payload = response.read(5_000_001)
                status = response.status
            if len(payload) > 5_000_000:
                raise ValueError("Feed exceeds the response size limit")
            rows, diagnostics = parse_feed(payload, url, retrieved, left, right)
            (raw / f"{left[:7]}.xml").write_bytes(payload)
            all_records.extend(rows)
            requests.append({"month": left[:7], "url": url, "retrieved_at": retrieved,
                             "status": status, "sha256": hashlib.sha256(payload).hexdigest(),
                             "accepted_items": len(rows), **diagnostics,
                             "possible_provider_cap": diagnostics["provider_items"] >= 100})
        except HTTPError as error:
            requests.append({"month": left[:7], "url": url, "retrieved_at": retrieved,
                             "status": "failed", "http_status": error.code,
                             "retry_after": error.headers.get("Retry-After"), "error": f"HTTPError: {error}"})
            if error.code in {429, 403}:
                limited = True  # Preserve the calendar and respect provider limits.
        except Exception as error:
            requests.append({"month": left[:7], "url": url, "retrieved_at": retrieved,
                             "status": "failed", "error": f"{type(error).__name__}: {error}"})
        time.sleep(pause)
    (output / "collection_log.json").write_text(json.dumps({"start": start, "end_exclusive": end,
        "source": "Google News RSS search", "scope": SCOPE, "requests": requests}, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    (output / "headlines_raw.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in all_records), encoding="utf8")
    if not all_records:
        raise RuntimeError("No real records collected. Inspect collection_log.json; no fallback data were generated.")
    return all_records
