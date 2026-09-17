"""Public Kern enforcement cases: allegations, not adjudicated violations or sellers.

No owner identity, asking price, distress inference or motivation score is invented.
"""
import json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

SEARCH_URL = 'https://aca-prod.accela.com/KERNCO/Cap/CapHome.aspx?module=Enforcement&TabName=Home'


def parse_cases(html):
    """Convert verified public case rows into conservative property research leads."""
    soup = BeautifulSoup(html, 'html.parser')
    if not soup.select_one('table[id$=gdvPermitList]'):
        raise ValueError('Public case results not present (login, challenge, error, or changed schema)')
    leads = []
    now = datetime.now(timezone.utc).isoformat()
    for anchor in soup.select('a[id$=hlPermitNumber]'):
        row = anchor.find_parent('tr')
        fields = {key: row.select_one(f'[id$={suffix}]').get_text(' ', strip=True)
                  for key, suffix in [('address', 'lblPermitAddress'), ('type', 'lblType'),
                                      ('description', 'lblDescription'), ('status', 'lblStatus'),
                                      ('date', 'lblUpdatedTime')]}
        if (fields['type'] != 'Case/Violation' or fields['status'] != 'Pending Initial Inspection'
                or ', ' not in fields['address'] or not fields['address'].endswith(' CA')):
            continue
        address, city = fields['address'].rsplit(', ', 1)
        city = city.removesuffix(' CA')
        case = anchor.get_text(' ', strip=True)
        if any(lead['id'] == f'kern_code_{case}' for lead in leads):
            continue
        link = urljoin(SEARCH_URL, anchor.get('href', ''))
        parsed = urlparse(link)
        query = parse_qs(parsed.query)
        if (parsed.scheme != 'https' or parsed.netloc != 'aca-prod.accela.com'
                or parsed.path != '/KERNCO/Cap/CapDetail.aspx'
                or query.get('Module') != ['Enforcement'] or query.get('agencyCode') != ['KERNCO']
                or not all(query.get(key) for key in ('capID1', 'capID2', 'capID3'))):
            raise ValueError('Invalid Kern enforcement record link')
        leads.append(dict(id=f'kern_code_{case}', address=address, city=city,
                          price=0, price_text='', source='kern_code_cases', source_type='code_case',
                          link=link,
                          description=f"Public enforcement case {case}; {fields['status']}; opened {fields['date']}. "
                                      f"Reported: {fields['description']}. Unverified case allegation; not seller intent or a confirmed violation.",
                          owner_name='', owner_mailing='', motivation='unknown', deal_score=0,
                          equity_estimate='', status='new', created_at=now, updated_at=now,
                          raw_data=json.dumps(fields)))
    return leads


def scrape_kern_code_cases(*, session=None, save=None, start_date=None, end_date=None):
    """Read one public results page; return (found, new, warning/error).

    Default window is the last 30 days. Pagination is deliberately bounded to
    one page and is reported as partial, never represented as county-wide coverage.
    An injectable save callback supports verification without touching the database.
    """
    from datetime import timedelta
    import requests
    from database import upsert_lead

    found = new = 0
    own_session = session is None
    session = session if session is not None else requests.Session()
    save = save if save is not None else upsert_lead
    today = datetime.now(timezone.utc).date()
    try:
        response = session.get(SEARCH_URL, timeout=(5, 30))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        if not soup.select_one('a[id$=btnNewSearch]') or not soup.select_one('input[name=__VIEWSTATE]'):
            raise ValueError('Public search form missing; no search submitted')
        data = {e['name']: e.get('value', '') for e in soup.select('input[name]')
                if e.get('type') not in ('checkbox', 'radio', 'submit', 'button')}
        for element in soup.select('select[name]'):
            option = element.select_one('option[selected]') or element.select_one('option')
            data[element['name']] = option.get('value', '') if option else ''
        data['__EVENTTARGET'] = 'ctl00$PlaceHolderMain$btnNewSearch'
        data['__EVENTARGUMENT'] = ''
        prefix = 'ctl00$PlaceHolderMain$generalSearchForm$'
        data[prefix + 'txtGSStartDate'] = start_date or (today - timedelta(days=30)).strftime('%m/%d/%Y')
        data[prefix + 'txtGSEndDate'] = end_date or today.strftime('%m/%d/%Y')
        response = session.post(SEARCH_URL, data=data,
                                headers={'Referer': SEARCH_URL, 'Origin': 'https://aca-prod.accela.com'},
                                timeout=(5, 30))
        response.raise_for_status()
        leads = parse_cases(response.text)
        for lead in leads:
            found += 1
            new += bool(save(lead))
        soup = BeautifulSoup(response.text, 'html.parser')
        partial = any(a.get_text(' ', strip=True) == 'Next >' for a in soup.select('a[href]'))
        return found, new, 'Partial coverage: first results page only; more public cases available.' if partial else ''
    except Exception as exc:
        return found, new, f'{type(exc).__name__}: {exc}'
    finally:
        if own_session:
            session.close()
