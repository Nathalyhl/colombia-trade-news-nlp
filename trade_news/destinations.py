"""Project-specific market evidence; separate from BE1340 sentiment measurement.

Strict proposals require an explicit export/destination relation in a headline.
Body mentions remain exploratory: a named country is not necessarily a buyer.
No bloc memberships, inferred countries or trade volumes are assigned.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .articles import read_jsonl, write_jsonl
from .bank_method import aggregate
from .classification import normalized

METHOD = "country_export_links_with_comparison_guard_v2"
COUNTRIES = {
    "United States": ["estados unidos", "ee uu", "eeuu", "e e u u"],
    "China": ["china"], "Ecuador": ["ecuador"], "Venezuela": ["venezuela"],
    "Brazil": ["brasil", "brazil"], "Peru": ["peru"], "Mexico": ["mexico"],
    "Canada": ["canada"], "Argentina": ["argentina"], "Chile": ["chile"],
    "Bolivia": ["bolivia"], "Paraguay": ["paraguay"], "Uruguay": ["uruguay"],
    "Panama": ["panama"], "Costa Rica": ["costa rica"], "Guatemala": ["guatemala"],
    "El Salvador": ["el salvador"], "Honduras": ["honduras"], "Nicaragua": ["nicaragua"],
    "Dominican Republic": ["republica dominicana"], "Cuba": ["cuba"], "Jamaica": ["jamaica"],
    "Haiti": ["haiti"], "Trinidad and Tobago": ["trinidad y tobago"],
    "United Kingdom": ["reino unido"], "Spain": ["espana"], "France": ["francia"],
    "Germany": ["alemania"], "Italy": ["italia"], "Netherlands": ["paises bajos", "holanda"],
    "Belgium": ["belgica"], "Portugal": ["portugal"], "Switzerland": ["suiza"],
    "Sweden": ["suecia"], "Norway": ["noruega"], "Denmark": ["dinamarca"],
    "Finland": ["finlandia"], "Poland": ["polonia"], "Austria": ["austria"],
    "Ireland": ["irlanda"], "Greece": ["grecia"], "Romania": ["rumania"],
    "Russia": ["rusia"], "Ukraine": ["ucrania"], "Turkey": ["turquia", "turkiye"],
    "Israel": ["israel"], "Egypt": ["egipto"], "Algeria": ["argelia"],
    "Morocco": ["marruecos"], "South Africa": ["sudafrica"], "Nigeria": ["nigeria"],
    "Ghana": ["ghana"], "Kenya": ["kenia"], "Saudi Arabia": ["arabia saudita"],
    "United Arab Emirates": ["emiratos arabes unidos"], "Qatar": ["catar", "qatar"],
    "Kuwait": ["kuwait"], "Jordan": ["jordania"], "Lebanon": ["libano"],
    "Iraq": ["irak", "iraq"], "Iran": ["iran"], "India": ["india"],
    "Japan": ["japon"], "South Korea": ["corea del sur", "republica de corea"],
    "Vietnam": ["vietnam", "viet nam"], "Philippines": ["filipinas"],
    "Indonesia": ["indonesia"], "Malaysia": ["malasia"], "Singapore": ["singapur"],
    "Thailand": ["tailandia"], "Pakistan": ["pakistan"], "Bangladesh": ["banglades"],
    "Australia": ["australia"], "New Zealand": ["nueva zelanda"],
}
MARKETS = COUNTRIES
EXPORT = r"\b(?:export\w*|ventas?\s+externas?|ventas?\s+internacionales?|vender|vende\w*|vendio)\b"
ORIGIN = r"\b(?:colombia|colombian[oa]s?)\b"
DIRECTION = r"(?:\bexport\w*|\bventas?\s+externas?|\bvender|\bvende\w*|\bvendio)(?:\s+\w+){0,16}\s+(?:a|hacia|para)(?:\s+(?:el|los|la|las))?\s*$"
ROLE = r"^(?:\s+\w+){0,10}\s+(?:destino|comprador|compradores|cliente|clientes)\b"
BUYER = r"^(?:\s+\w+){0,4}\s+(?:compra\w*|importa\w*|adquier\w*)\b"
COMPARISON = r"\b(?:frente\s+a|respecto\s+a|en\s+comparacion\s+con|compite\s+con|competencia\s+de|competidor\s+de|proveniente\s+de|procedente\s+de)\s*$"
RULE_LABELS = {
    "export_to_market_in_headline": "The headline links Colombian exports to this country with directional wording.",
    "named_destination_or_buyer_role_in_headline": "The headline explicitly describes this country as a destination, buyer or customer.",
    "named_buyer_in_Colombian_export_headline": "The headline names this country as a buyer in a Colombian-export context.",
    "comparison_or_source_not_destination": "The country appears as a comparison, competitor or source, rather than an export destination.",
}


def configuration_hash():
    settings = [METHOD, MARKETS, EXPORT, ORIGIN, DIRECTION, ROLE, BUYER, COMPARISON]
    return hashlib.sha256(json.dumps(settings, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def market_hits(text, field):
    """Offsets refer to the normalized field, not to the raw publisher HTML."""
    value = normalized(text)
    matches = []
    for market, aliases in MARKETS.items():
        for alias in aliases:
            for match in re.finditer(r"(?<!\w)"+re.escape(alias)+r"(?!\w)", value):
                matches.append({"market": market, "alias": alias, "field": field,
                                "start": match.start(), "end": match.end()})
    # Longest country alias wins when spans overlap.
    accepted = []
    for match in sorted(matches, key=lambda m: (-(m["end"]-m["start"]), m["start"], m["market"])):
        if not any(match["start"] < other["end"] and other["start"] < match["end"] for other in accepted):
            accepted.append(match)
    return value, sorted(accepted, key=lambda m: (m["start"], m["market"]))


def identify(title, body=""):
    value, title_hits = market_hits(title, "title")
    _, body_hits = market_hits(body, "article_body")
    explicit, rejected = [], []
    if re.search(EXPORT, value) and re.search(ORIGIN, value):
        for hit in title_hits:
            before, after = value[:hit["start"]], value[hit["end"]:]
            rule = None
            if re.search(COMPARISON, before):
                rejected.append({**hit, "rule": "comparison_or_source_not_destination"})
                continue
            if re.search(DIRECTION, before) and re.search(ORIGIN, before):
                rule = "export_to_market_in_headline"
            elif re.search(ROLE, after):
                rule = "named_destination_or_buyer_role_in_headline"
            elif re.search(BUYER, after):
                rule = "named_buyer_in_Colombian_export_headline"
            if rule:
                explicit.append({**hit, "rule": rule})
    return {"destinations": sorted({h["market"] for h in explicit}),
            "market_mentions": sorted({h["market"] for h in title_hits+body_hits}),
            "destination_evidence": explicit,
            "non_destination_evidence": rejected,
            # First occurrence per market/field is enough to audit a mention.
            "mention_evidence": list({(h["market"], h["field"]): h for h in reversed(title_hits+body_hits)}.values())}


def build_destinations(directory, rows):
    directory = Path(directory)
    path = directory/"destinations.jsonl"
    cached = {r["record_id"]: r for r in read_jsonl(path)} if path.exists() else {}
    output = []
    for row in rows:
        title = row.get("publisher_title") or row["title"]
        title_hash = hashlib.sha256(title.encode()).hexdigest()
        previous = cached.get(row["record_id"], {})
        text_path = directory/"raw/articles"/(row["record_id"]+".txt")
        body, text_hash = "", None
        if row.get("fetch_status") == "article_extracted" and text_path.exists():
            body = text_path.read_text("utf8")
            text_hash = hashlib.sha256(body.encode()).hexdigest()
            if text_hash != row["text_sha256"]:
                raise ValueError("Destination analysis: local body differs from the saved article hash")
        elif previous.get("body_sha256"):
            if (previous.get("configuration_sha256") != configuration_hash() or previous.get("title_sha256") != title_hash
                    or previous["body_sha256"] != row.get("text_sha256")):
                raise ValueError("Destination cache is stale; restore the article archive to rebuild body mentions")
            output.append(previous)
            continue
        output.append({"record_id": row["record_id"], "method": METHOD, "configuration_sha256": configuration_hash(),
            "title_sha256": title_hash, "body_sha256": text_hash,
            "status": "automatic_proposals_pending_human_review", **identify(title, body)})
    write_jsonl(path, output)
    from .country_review import refresh_country_validation
    refresh_country_validation(directory, rows, output)
    return output


def select_articles(rows, features, market, mode="destinations"):
    if mode not in {"destinations", "market_mentions"}:
        raise ValueError("Unknown destination evidence mode")
    lookup = {r["record_id"]: r for r in features}
    return [r for r in rows if r.get("eligible_for_index") and market in lookup.get(r["record_id"], {}).get(mode, [])]


def coverage(rows, features, mode="destinations", kind="Countries"):
    if kind != "Countries":
        raise ValueError("Only country destinations are supported")
    allowed = set(COUNTRIES)
    lookup = {r["record_id"]: r for r in features}
    counts = Counter(market for row in rows if row.get("eligible_for_index")
                     for market in set(lookup.get(row["record_id"], {}).get(mode, [])) if market in allowed)
    return [{"market": market, "articles": count} for market, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))]


def monthly_series(rows, features, market, months, mode="destinations"):
    selected = select_articles(rows, features, market, mode)
    return [r for r in aggregate(selected, months) if r["activity"] == "All exports"]
