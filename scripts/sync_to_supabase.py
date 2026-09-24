"""Sync local SQLite leads.db into the Supabase lead pipeline (REST-only, no DDL).

Flow: local leads -> raw_lead_intake (REST insert) -> process_pending_intake (RPC)
which creates properties, distress_events, lead_scores, and deals rows.

Usage:
    python scripts/sync_to_supabase.py            # sync + process
    python scripts/sync_to_supabase.py --dry-run  # show what would sync
    python scripts/sync_to_supabase.py --process-only  # only run the pipeline RPC

Env (or .env next to this file / parent dir):
    SUPABASE_URL, SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_ROLE_KEY)

Source mapping (local source -> lead_sources.id + distress event_type):
    craigslist          -> craigslist_fsbo (listing, not distress)
    kern_tax            -> kern_tax_auction, tax_default
    newspaper_auction   -> newspaper_auction, tax_default
    kern_code_cases     -> kern_code_cases, code_violation
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv  # type: ignore
    for candidate in (ROOT / '.env', ROOT.parent / '.env'):
        if candidate.exists():
            load_dotenv(candidate)
            break
except ImportError:
    pass

SUPABASE_URL = (os.environ.get('SUPABASE_URL') or '').rstrip('/')
SUPA_KEY = (os.environ.get('SUPABASE_SECRET_KEY')
            or os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or '')
DB_PATH = Path(os.environ.get('DB_PATH', ROOT / 'data' / 'leads.db'))

BATCH = 200
JURISDICTION_ID = '39583dcc-f41e-4b86-a3c4-fd6943827fa9'  # CA / Kern

SOURCE_MAP = {
    'craigslist': ('craigslist_fsbo', None),
    'kern_tax': ('kern_tax_auction', 'tax_default'),
    'newspaper_auction': ('newspaper_auction', 'tax_default'),
    'kern_code_cases': ('kern_code_cases', 'code_violation'),
    'browser_investigation': ('manual_entry', None),
}

# Valid distress_events.event_type values (probed against the check constraint).
VALID_EVENTS = {'notice_of_default', 'notice_of_trustee_sale', 'notice_of_rescission',
                'tax_default', 'power_to_sell', 'probate_opened', 'letters_testamentary',
                'code_violation'}

HEADERS_BASE = {'apikey': SUPA_KEY, 'Authorization': f'Bearer {SUPA_KEY}',
                'Content-Type': 'application/json'}


def ensure_sources(session):
    payload = []
    for local, (source_id, _) in SOURCE_MAP.items():
        if source_id == 'manual_entry':
            continue  # already seeded by the schema
        payload.append({
            'id': source_id,
            'jurisdiction_id': JURISDICTION_ID,
            'source_type': 'public_record',
            'active': True,
            'notes': f'Synced from local private-seller-system ({local})',
        })
    if not payload:
        return
    response = session.post(f'{SUPABASE_URL}/rest/v1/lead_sources?on_conflict=id',
                            headers={**HEADERS_BASE, 'Prefer': 'resolution=ignore-duplicates'},
                            json=payload, timeout=30)
    response.raise_for_status()


def read_local_leads():
    if not DB_PATH.exists():
        raise SystemExit(f'No database at {DB_PATH} — run the scrapers first.')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute('SELECT * FROM leads')]
    finally:
        conn.close()


def lead_to_intake(lead):
    local_source = lead.get('source') or ''
    source_id, event_type = SOURCE_MAP.get(local_source, ('manual_entry', None))
    try:
        raw = json.loads(lead.get('raw_data') or '{}')
    except (json.JSONDecodeError, TypeError):
        raw = {}

    address = (lead.get('address') or '').strip()
    apn = raw.get('apn') or raw.get('parcel')
    payload = {
        'source_name': source_id,
        'source_type': event_type or 'listing',
        'source_record_id': lead.get('id'),
        'source_url': lead.get('link') or None,
        'raw_state': 'CA',
        'raw_county': 'Kern',
        'raw_apn': apn,
        'raw_address': address or None,
        'raw_city': lead.get('city') or None,
        'raw_owner_name': lead.get('owner_name') or None,
        'raw_payload': {
            'local_id': lead.get('id'),
            'price': lead.get('price') or 0,
            'price_text': lead.get('price_text'),
            'deal_score': lead.get('deal_score') or 0,
            'motivation': lead.get('motivation'),
            'description': lead.get('description'),
            'link': lead.get('link'),
            'owner_mailing': lead.get('owner_mailing'),
            'equity_estimate': lead.get('equity_estimate'),
            'status': lead.get('status'),
            'raw': raw,
        },
    }
    # The pipeline keys properties on address or APN; skip rows with neither.
    if not address and not apn:
        return None
    return payload


def push_intake_batch(session, batch):
    response = session.post(f'{SUPABASE_URL}/rest/v1/raw_lead_intake',
                            headers={**HEADERS_BASE, 'Prefer': 'return=minimal'},
                            json=batch, timeout=60)
    response.raise_for_status()


def run_pipeline(session):
    total_processed = 0
    for _ in range(60):
        response = session.post(f'{SUPABASE_URL}/rest/v1/rpc/process_pending_intake',
                                headers=HEADERS_BASE, json={}, timeout=120)
        response.raise_for_status()
        result = response.json()
        processed = result.get('processed', 0)
        total_processed += processed
        print(f'  pipeline processed: {processed}')
        if not processed:
            break
    return total_processed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--process-only', action='store_true')
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPA_KEY:
        raise SystemExit('Missing SUPABASE_URL or SUPABASE_SECRET_KEY environment variables.')

    session = requests.Session()
    session.headers.update(HEADERS_BASE)

    if args.process_only:
        print('Running pipeline only...')
        run_pipeline(session)
        return

    leads = read_local_leads()
    print(f'Local leads: {len(leads)}')

    payloads = []
    skipped = 0
    for lead in leads:
        payload = lead_to_intake(lead)
        if payload:
            payloads.append(payload)
        else:
            skipped += 1
    print(f'Convertible: {len(payloads)} | Skipped (no address/apn): {skipped}')

    if args.dry_run:
        by_source = {}
        for p in payloads:
            by_source[p['source_name']] = by_source.get(p['source_name'], 0) + 1
        for source, count in sorted(by_source.items(), key=lambda kv: -kv[1]):
            print(f'  {source}: {count}')
        print('Dry run — nothing synced.')
        return

    ensure_sources(session)
    print('Sources ensured.')

    started = time.time()
    pushed = 0
    for i in range(0, len(payloads), BATCH):
        batch = payloads[i:i + BATCH]
        try:
            push_intake_batch(session, batch)
            pushed += len(batch)
            print(f'  pushed {pushed}/{len(payloads)}')
        except Exception as exc:
            print(f'BATCH FAILED at {i}: {type(exc).__name__}: {exc}', file=sys.stderr)
            raise
    print(f'Pushed {pushed} intake rows in {time.time() - started:.1f}s')

    print('Processing pipeline...')
    processed = run_pipeline(session)
    print(f'Done: {pushed} pushed, {processed} processed.')


if __name__ == '__main__':
    main()
