"""OLX search results: 52 listings for 1 credit.

Verified live on 2026-09-15 against olx.pl.

Select on data-testid attributes, never on the Emotion class names such as
css-1tqlkj0. Those are generated and rotate whenever the CSS changes. The
test ids exist for OLX's own test suite, so their CI breaks if they move.
Set SCRAPINGBEE_API_KEY in your environment before running.
"""

import json
import os
import re
from urllib.parse import parse_qs, quote, urlsplit

import requests

BASE = "https://app.scrapingbee.com/api/v1/"
HEADERS = {"Authorization": f"Bearer {os.environ['SCRAPINGBEE_API_KEY']}"}

RULES = {
    "listings": {
        "selector": 'div[data-testid="l-card"]',
        "type": "list",
        "output": {
            # aria-label carries the FULL title. The visible anchor text is
            # truncated with an ellipsis when the title is long.
            "title": {"selector": 'a[data-testid="card-title-link"]', "output": "@aria-label"},
            "url": {"selector": 'a[data-testid="card-title-link"]', "output": "@href"},
            "price": 'p[data-testid="ad-price"]',
            "location_date": 'p[data-testid="location-date"]',
        },
    }
}

# The tail of the slug is -ID<code>.html and that code is the stable key.
# The rest of the slug changes when a seller edits the title.
LISTING_ID = re.compile(r"-ID([A-Za-z0-9]+)\.html")


def search(query, domain="olx.pl"):
    """1 credit. 52 listings per page.

    OLX is a family of national marketplaces, so the domain decides the
    country, language and currency. olx.ro, olx.bg, olx.ua and olx.kz are
    separate sites with the same markup.

    Do NOT add render_js. All 52 cards are in the delivered HTML.
    """
    url = f"https://www.{domain}/d/oferty/q-{quote(query)}/"
    r = requests.get(
        BASE,
        headers=HEADERS,
        params={"url": url, "extract_rules": json.dumps(RULES), "mode": "auto"},
        timeout=180,
    )
    r.raise_for_status()
    rows = r.json().get("listings") or []
    return [_clean(row, domain) for row in rows], r.headers.get("spb-cost")


def _clean(row, domain):
    raw = row.get("url") or ""
    parts = urlsplit(raw)

    # search_reason=search|promoted marks a paid placement, so promotion is
    # readable from the URL without a separate field.
    reason = parse_qs(parts.query).get("search_reason", [""])[0]

    # href is relative, so prefix the host. Strip the query before you
    # deduplicate or the same listing appears twice.
    clean_url = f"https://www.{domain}{parts.path}" if parts.path else None
    match = LISTING_ID.search(parts.path or "")

    return {
        "listing_id": match.group(1) if match else None,
        "title": row.get("title"),
        "price": row.get("price"),
        "location_date": row.get("location_date"),
        "url": clean_url,
        "promoted": "promoted" in reason,
    }


def organic_only(rows):
    """Drop paid placements before you compute market prices."""
    return [r for r in rows if not r["promoted"]]


if __name__ == "__main__":
    rows, cost = search("iphone")
    promoted = [r for r in rows if r["promoted"]]
    print(f"{len(rows)} listings for {cost} credit, {len(promoted)} promoted")

    for row in organic_only(rows)[:6]:
        print(f"  [{row['listing_id']}] {str(row['price'])[:14]:<14} {str(row['title'])[:52]}")
        print(f"      {row['location_date']}")

    ids = {r["listing_id"] for r in rows if r["listing_id"]}
    print(f"\nunique listing ids: {len(ids)} of {len(rows)} rows")
