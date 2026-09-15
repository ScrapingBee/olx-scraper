# OLX Scraper

<p align="center">
  <a href="https://www.scrapingbee.com/">
    <img src="REPLACE_WITH_SCREENSHOT_URL" alt="olx-scraper" />
  </a>
</p>

[![checks](https://github.com/ScrapingBee/olx-scraper/workflows/checks/badge.svg)](https://github.com/ScrapingBee/olx-scraper/actions)
[![license](https://img.shields.io/github/license/ScrapingBee/olx-scraper.svg)](LICENSE)

OLX ships a 3.7 MB page built with Emotion, so the class names look like `css-1tqlkj0` and rotate whenever the CSS changes. Selecting on those is how an [olx scraper](https://www.scrapingbee.com/scrapers/olx-api/) breaks silently a month after you write it.

The page also ships `data-testid` attributes on every element you actually want. Those exist for OLX's own test suite, which means their CI breaks when they move. That is the contract this repo builds on, and it returns **52 listings for 1 credit**.

Built on [ScrapingBee's web scraping API](https://www.scrapingbee.com/features/ai-web-scraping-api/). Verified live on 2026-09-15 against `olx.pl`.

## Four attributes, 52 rows

```python
rules = {"listings": {"selector": 'div[data-testid="l-card"]', "type": "list", "output": {
    "title": {"selector": 'a[data-testid="card-title-link"]', "output": "@aria-label"},
    "url":   {"selector": 'a[data-testid="card-title-link"]', "output": "@href"},
    "price":         'p[data-testid="ad-price"]',
    "location_date": 'p[data-testid="location-date"]',
}}}
```

Live result, 1 credit:

```json
{
  "title": "Wymiana baterii iPhone 15 PRO MAX na poczekaniu Mińsk Mazowiecki",
  "url": "/d/oferta/wymiana-baterii-iphone-15-pro-max-...-ID1an6LV.html?search_reason=search%7Cpromoted",
  "price": "...",
  "location_date": "..."
}
```

52 cards on one page, which is roughly double what most marketplace listings return per request.

### Take the title from `aria-label`, not the link text

The visible anchor text is truncated with an ellipsis when a title is long. The `aria-label` on the same element carries the **full untruncated title**, because screen readers need it. One attribute change, complete data.

### The URL is relative, and carries tracking

`href` comes back as `/d/oferta/...` with no host, so prefix the domain you queried. It also carries a `search_reason` query parameter, and `search_reason=search|promoted` is how you tell a paid placement from an organic one without a separate field:

```python
from urllib.parse import urlsplit, parse_qs

parts = urlsplit(row["url"])
promoted = "promoted" in parse_qs(parts.query).get("search_reason", [""])[0]
clean = f"https://www.olx.pl{parts.path}"
```

Strip the query before you deduplicate, or the same listing appears twice because it was reached two ways.

### The listing ID is in the path

The tail of the slug is `-ID<code>.html`, for example `ID1an6LV`. That code is the stable key across repeated pulls. The rest of the slug is cosmetic and changes when a seller edits the title.

## One domain per country

OLX is a family of national marketplaces, not one site. The verified page here is `olx.pl`, which is Poland, and the landing page for this target names `olx.pl` as the source too. Other countries live on their own domains, such as `olx.ro`, `olx.bg`, `olx.ua` and `olx.kz`, each with its own currency and language.

The search path shape on the Polish site is:

```
https://www.olx.pl/d/oferta/          one listing
https://www.olx.pl/d/oferty/q-<query>/  a search
```

Prices come back as display strings in local currency, complete with the local thousands separator and a `zł` suffix on the Polish site, so normalise per domain rather than with one global parser.

The request also reported `spb-initial-status-code: 301`, meaning OLX redirects to a canonical form. That is a redirect being followed, not a problem.

## Why 1 credit is the right configuration

`mode=auto` walked the ladder and settled on the cheapest rung. The delivered HTML already contains all 52 cards, so there is nothing for a browser to add.

Two structured data blocks also come down with the page, a `WebPage` and a `BreadcrumbList`. The breadcrumb gives you the category path, which saves parsing it out of the URL.

## Credit cost

Measured from `spb-cost` response headers:

| Call | Credits |
|---|---|
| A search results page via `mode=auto` | 1 |
| Rejected request | 0 |

`mode=auto` bills only the rung that worked and nothing at all if every rung fails. It cannot be combined with `render_js`, `premium_proxy` or `stealth_proxy`, and sending both returns HTTP 400 while billing nothing.

At 52 listings per credit, tracking 20 search queries hourly is 480 credits a day. The entry paid tier of 250,000 credits covers that comfortably. ScrapingBee does not cache, so poll on the cadence your prices actually move.

Plan tiers are on the [pricing page](https://www.scrapingbee.com/pricing).

## Scope

Public listing and search pages. Seller accounts, the messaging system, phone numbers revealed only after a click and anything requiring a signed in session are out of reach, and scraping under login credentials is prohibited by ScrapingBee's terms of service.

OLX is a consumer to consumer marketplace, so most sellers are private individuals rather than businesses. Listing text, location and any contact detail are personal data, and harvesting seller contact information is specifically not what this is for. Track prices, categories and market supply, and leave the people out of your dataset. [OLX's Regulamin](https://pomoc.olx.pl/olxplhelp/s/article/aktualny-regulamin-V32-olx) governs the Polish site, with equivalents per country domain.

Reference: [extraction rules](https://www.scrapingbee.com/documentation/data-extraction/), [data extraction feature](https://www.scrapingbee.com/features/data-extraction/), [markdown output](https://www.scrapingbee.com/features/markdown-scraper/).

Adjacent marketplace endpoints: [classified API](https://www.scrapingbee.com/scrapers/classified-api/), [Craigslist API](https://www.scrapingbee.com/scrapers/craigslist-api/), [Craigslist ad API](https://www.scrapingbee.com/scrapers/craigslist-ad-api/), [Gumtree API](https://www.scrapingbee.com/scrapers/gumtree-api/), [Avito RU API](https://www.scrapingbee.com/scrapers/avito-ru-api/), [eBay scraper](https://www.scrapingbee.com/scrapers/ebay-scraper/), [marketplace API](https://www.scrapingbee.com/scrapers/marketplace-api/), [Etsy API](https://www.scrapingbee.com/scrapers/etsy-api/).

## FAQ

**Why are my OLX selectors breaking?**
Because you selected on an Emotion class such as `css-1tqlkj0`. Those are generated and rotate. Use the `data-testid` attributes, which OLX's own tests depend on.

**Why is my title cut off with an ellipsis?**
Because you read the anchor text. Read `@aria-label` on the same element for the full title.

**How do I tell promoted listings from organic ones?**
The `search_reason` query parameter on the listing URL. `search|promoted` marks a paid placement.

**Which OLX domain should I use?**
The one for the country you care about. OLX is a set of national marketplaces, and the verified example here is `olx.pl`.

**What is the stable ID for a listing?**
The `ID<code>` segment at the end of the URL path. The slug before it changes when a seller edits the title.

**Do I need JavaScript rendering?**
No. All 52 cards are in the delivered HTML at 1 credit.

## License

MIT. See [LICENSE](LICENSE).
