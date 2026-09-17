"""Bounded RSS fetching. HTML/challenges are failures, not empty feeds."""
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
import feedparser
from bs4 import BeautifulSoup
from config import CRAIGSLIST_RSS, HEADERS
from scoring import score_lead, extract_price
from database import upsert_lead


def scrape_craigslist():
    found = new = 0
    errors = []
    seen = set()
    for url in CRAIGSLIST_RSS:
        response = None
        try:
            response = requests.get(url, headers=HEADERS, timeout=(5, 15))
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            if not feed.get('version') or feed.get('bozo'):
                raise ValueError('Invalid RSS/Atom response (HTML, challenge, or malformed feed)')
            for entry in feed.entries:
                try:
                    title = BeautifulSoup(entry.get('title', ''), 'html.parser').get_text(' ', strip=True)
                    link = entry.get('link', '')
                    host = urlparse(link).hostname or ''
                    if not title or urlparse(link).scheme not in ('http', 'https') or not host.endswith('.craigslist.org') or not re.search(r'/\d+\.html$', urlparse(link).path):
                        raise ValueError('Entry missing title or Craigslist property URL')
                    # Listing URL identity deduplicates overlapping RSS searches.
                    identity = re.search(r'/(\d+)\.html$', urlparse(link).path).group(1)
                    if identity in seen:
                        continue
                    desc = BeautifulSoup(entry.get('description', ''), 'html.parser').get_text(' ', strip=True)[:2000]
                    text = title + ' ' + desc
                    city = next((city for city in ('California City', 'Stallion Springs', 'Tehachapi', 'Bakersfield') if city.lower() in text.lower()), '')
                    source_type = 'fsbo' if '/reo' in urlparse(url).path else 'real_estate'
                    price = extract_price(text)
                    score, reasons, motivation = score_lead(title, desc, price, source_type)
                    now = datetime.now(timezone.utc).isoformat()
                    lead = dict(id=f'craigslist_{identity}', address=title[:100], city=city,
                                price=price, price_text=f'${price:,}' if price else '',
                                source='craigslist', source_type=source_type, link=link,
                                description=f'{title} | {desc} | SCORE REASONS: {reasons}',
                                owner_name='', owner_mailing='', motivation=motivation,
                                deal_score=score, equity_estimate='', status='new',
                                created_at=now, updated_at=now, raw_data=json.dumps(dict(entry)))
                    seen.add(identity)
                    found += 1
                    new += bool(upsert_lead(lead))
                except Exception as exc:
                    errors.append(f'{url}: entry: {type(exc).__name__}: {exc}')
        except Exception as exc:
            errors.append(f'{url}: {type(exc).__name__}: {exc}')
            if response is not None and response.status_code in (403, 429):
                break
    return found, new, '; '.join(errors)
