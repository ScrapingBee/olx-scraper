// OLX search results: 52 listings for 1 credit.
// Verified live on 2026-09-15 against olx.pl.
//
// Select on data-testid attributes, never on the Emotion class names such as
// css-1tqlkj0. Those are generated and rotate whenever the CSS changes.

const axios = require('axios');

const BASE = 'https://app.scrapingbee.com/api/v1/';
const headers = { Authorization: `Bearer ${process.env.SCRAPINGBEE_API_KEY}` };

const RULES = {
  listings: {
    selector: 'div[data-testid="l-card"]',
    type: 'list',
    output: {
      // aria-label carries the FULL title. The visible anchor text is
      // truncated with an ellipsis when the title is long.
      title: { selector: 'a[data-testid="card-title-link"]', output: '@aria-label' },
      url: { selector: 'a[data-testid="card-title-link"]', output: '@href' },
      price: 'p[data-testid="ad-price"]',
      location_date: 'p[data-testid="location-date"]',
    },
  },
};

// The tail of the slug is -ID<code>.html and that code is the stable key.
const LISTING_ID = /-ID([A-Za-z0-9]+)\.html/;

// 1 credit. 52 listings per page. The domain decides country, language and
// currency: olx.ro, olx.bg, olx.ua and olx.kz are separate sites.
// Do NOT add render_js. All 52 cards are in the delivered HTML.
async function search(query, domain = 'olx.pl') {
  const url = `https://www.${domain}/d/oferty/q-${encodeURIComponent(query)}/`;
  const res = await axios.get(BASE, {
    headers,
    params: { url, extract_rules: JSON.stringify(RULES), mode: 'auto' },
    timeout: 180000,
  });
  const rows = (res.data.listings || []).map((row) => clean(row, domain));
  return { rows, cost: res.headers['spb-cost'] };
}

function clean(row, domain) {
  const raw = row.url || '';
  const [path, query = ''] = raw.split('?');

  // search_reason=search|promoted marks a paid placement.
  const reason = new URLSearchParams(query).get('search_reason') || '';
  const match = path.match(LISTING_ID);

  return {
    listing_id: match ? match[1] : null,
    title: row.title,
    price: row.price,
    location_date: row.location_date,
    // href is relative, so prefix the host. Strip the query before
    // deduplicating or the same listing appears twice.
    url: path ? `https://www.${domain}${path}` : null,
    promoted: reason.includes('promoted'),
  };
}

// Drop paid placements before computing market prices.
const organicOnly = (rows) => rows.filter((r) => !r.promoted);

(async () => {
  const { rows, cost } = await search('iphone');
  const promoted = rows.filter((r) => r.promoted);
  console.log(`${rows.length} listings for ${cost} credit, ${promoted.length} promoted`);

  organicOnly(rows).slice(0, 6).forEach((row) => {
    console.log(`  [${row.listing_id}] ${String(row.price).slice(0, 14)} ${String(row.title).slice(0, 52)}`);
    console.log(`      ${row.location_date}`);
  });

  const ids = new Set(rows.map((r) => r.listing_id).filter(Boolean));
  console.log(`\nunique listing ids: ${ids.size} of ${rows.length} rows`);
})();

module.exports = { search, organicOnly };
