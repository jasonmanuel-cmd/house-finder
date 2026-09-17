"""Parse explicit FSBO records only; never pair independent HTML regex matches."""
import json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from config import ZILLOW_FSBO_URLS, HEADERS
from database import upsert_lead
from scoring import score_lead


def scrape_zillow_fsbo():
    found = new = 0
    errors = []
    seen = set()
    for url in ZILLOW_FSBO_URLS:
        try:
            response = requests.get(url, headers=HEADERS, timeout=(5, 15))
            response.raise_for_status()
            script = BeautifulSoup(response.text, 'html.parser').find('script', id='__NEXT_DATA__')
            if not script:
                raise ValueError('Unsupported listing structure or challenge page; no __NEXT_DATA__')
            data = json.loads(script.get_text())
            state = data['props']['pageProps']['searchPageState']
            if isinstance(state, str):
                state = json.loads(state)
            listings = state['cat1']['searchResults']['listResults']
            if not isinstance(listings, list):
                raise ValueError('Unsupported listResults structure')
            for item in listings:
                try:
                    if item.get('listingSubType', {}).get('is_FSBO') is not True:
                        continue
                    zpid = str(item.get('zpid') or '')
                    address = item.get('addressStreet')
                    city = item.get('addressCity', '')
                    link = urljoin(url, item.get('detailUrl') or '')
                    if not zpid or not address or not item.get('detailUrl') or urlparse(link).hostname not in ('www.zillow.com', 'zillow.com'):
                        raise ValueError('FSBO record missing identity/address/property URL')
                    if zpid in seen:
                        continue
                    value = item.get('unformattedPrice')
                    price = int(value) if isinstance(value, (int, float)) and value > 0 else 0
                    score, reasons, motivation = score_lead(address, 'FSBO Zillow', price, 'fsbo')
                    now = datetime.now(timezone.utc).isoformat()
                    lead = dict(id=f'zillow_fsbo_{zpid}', address=address, city=city,
                                price=price, price_text=f'${price:,}' if price else '',
                                source='zillow_fsbo', source_type='fsbo', link=link,
                                description=f'Zillow FSBO listing | SCORE: {reasons}',
                                owner_name='', owner_mailing='', motivation=motivation,
                                deal_score=score, equity_estimate='', status='new',
                                created_at=now, updated_at=now, raw_data=json.dumps(item))
                    found += 1
                    seen.add(zpid)
                    new += bool(upsert_lead(lead))
                except Exception as exc:
                    errors.append(f'{url}: listing: {type(exc).__name__}: {exc}')
        except Exception as exc:
            errors.append(f'{url}: {type(exc).__name__}: {exc}')
            # Never retry another URL on this host after an explicit access block.
            if 'response' in locals() and response.status_code in (403, 429):
                break
    return found, new, '; '.join(errors)
