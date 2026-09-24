"""Craigslist by-owner real estate leads via the sapi search API.

RSS is dead (404/403); the site itself uses sapi.craigslist.org, which works
with plain requests. Non-JSON or challenge responses are failures, not empty
feeds. No owner identity is invented: these are public by-owner listings.
"""
import json
import re
from datetime import datetime, timezone

import requests

from config import CRAIGSLIST_API, CRAIGSLIST_QUERIES, HEADERS
from scoring import score_lead, extract_price
from database import upsert_lead

KERN_CITIES = ('California City', 'Stallion Springs', 'Tehachapi', 'Bakersfield',
               'Mojave', 'Rosamond', 'California City', 'Maricopa', 'Buttonwillow',
               'Shafter', 'Wasco', 'Delano', 'Arvin', 'Lamont', 'Oildale',
               'Ridgecrest', 'Inyokern', 'Trona', 'Mojave', 'Taft')


def _decode_item(item):
    """Decode one sapi item row into (id, price, slug, title, beds, baths, sqft, url).

    Observed shape (positional):
    [post_id, account_id?, 143, price_int, "geo", "code", -3, [13,"viewKey"],
     [4, image ids...], [6, "slug"], [10, "$price"], "title", [beds, baths, sqft]]
    """
    if not isinstance(item, list) or len(item) < 9:
        return None
    post_id = item[0]
    price_int = item[3] if isinstance(item[3], int) else 0
    view_key = None
    slug = None
    price_text = ''
    title = None
    beds = baths = sqft = 0
    for entry in item[6:]:
        if not (isinstance(entry, list) and entry):
            continue
        tag = entry[0]
        if tag == 13 and len(entry) > 1:
            view_key = entry[1]
        elif tag == 6 and len(entry) > 1:
            slug = entry[1]
        elif tag == 10 and len(entry) > 1:
            price_text = entry[1]
        elif tag == 5 and len(entry) >= 3:
            beds, baths, sqft = entry[1], entry[2], entry[3] if len(entry) > 3 else 0
    # Title is the standalone long string near the end.
    strings = [x for x in item if isinstance(x, str) and len(x) > 10
               and not x.startswith('1:') and not x.startswith('2:')]
    title = strings[-1] if strings else ''
    if not post_id or not view_key:
        return None
    url = f'https://www.craigslist.org/view/d/{slug}/{view_key}' if slug else \
          f'https://bakersfield.craigslist.org/realestate/{post_id}.html'
    return dict(post_id=str(post_id), price=price_int, price_text=price_text,
                title=title, beds=beds, baths=baths, sqft=sqft, url=url)


def scrape_craigslist(session=None):
    found = new = 0
    errors = []
    seen = set()
    own_session = session is None
    session = session if session is not None else requests.Session()
    try:
        for query in CRAIGSLIST_QUERIES:
            params = {'batch': '0-0-360-0-0', 'lang': 'en', 'cc': 'us'}
            params.update(query)
            try:
                response = session.get(CRAIGSLIST_API, params=params,
                                       headers={'Accept': 'application/json', **HEADERS},
                                       timeout=(5, 20))
                response.raise_for_status()
                payload = response.json()
                items = ((payload.get('data') or {}).get('items')) or []
                if not isinstance(items, list):
                    raise ValueError('Unexpected API shape (no items list)')
                for item in items:
                    try:
                        decoded = _decode_item(item)
                        if not decoded:
                            continue
                        if decoded['post_id'] in seen:
                            continue
                        seen.add(decoded['post_id'])
                        title = decoded['title']
                        if not title:
                            continue
                        by_owner = 'srchType' in query
                        text = ' '.join(filter(None, [title, decoded['price_text']]))
                        city = next((c for c in KERN_CITIES if c.lower() in text.lower()), '')
                        price = decoded['price'] or extract_price(text)
                        source_type = 'fsbo' if by_owner else 'real_estate'
                        score, reasons, motivation = score_lead(title, decoded['price_text'], price, source_type)
                        now = datetime.now(timezone.utc).isoformat()
                        lead = dict(
                            id=f"craigslist_{decoded['post_id']}",
                            address=title[:100], city=city,
                            price=price, price_text=decoded['price_text'] or (f'${price:,}' if price else ''),
                            source='craigslist', source_type=source_type, link=decoded['url'],
                            description=(f"{title} | beds {decoded['beds']} baths {decoded['baths']} "
                                         f"sqft {decoded['sqft']} | SCORE REASONS: {reasons}"),
                            owner_name='', owner_mailing='', motivation=motivation,
                            deal_score=score, equity_estimate='', status='new',
                            created_at=now, updated_at=now,
                            raw_data=json.dumps(decoded))
                        found += 1
                        new += bool(upsert_lead(lead))
                    except Exception as exc:
                        errors.append(f"item: {type(exc).__name__}: {exc}")
            except Exception as exc:
                errors.append(f"{query}: {type(exc).__name__}: {exc}")
    finally:
        if own_session:
            session.close()
    return found, new, '; '.join(errors)
