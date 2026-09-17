"""
Run sources, persist every source outcome, and return structured results.

Sources:
- craigslist       — Craigslist RSS feeds for Kern County metros (timeout-bounded HTTP).
- zillow_fsbo      — Zillow FSBO search pages (403 to automated access; manual resource).
- kern_tax         — Kern County Tax Auction: general page → GovEase browse page (public).
- bakersfield_code — Bakersfield code enforcement availability check.
- browser_sources  — Playwright browser investigation of public-government surfaces
                     (assessor, permits, probate, code enforcement, auctions). Only runs
                     when playwright + a chromium browser are available; in every other case
                     the orchestrator skips it and still records a scrape_log row for the
                     source so the dashboard shows it was considered.
"""
import argparse
import time
from datetime import datetime, timezone
from database import init_db, get_conn
from scrapers.kern_code_cases import scrape_kern_code_cases
from scrapers.newspaper_auctions import scrape_newspaper_auctions
from scrapers.craigslist import scrape_craigslist
from scrapers.kern_tax import scrape_kern_tax
from scrapers.bakersfield_code import scrape_bakersfield_code
from scrapers.zillow_fsbo import scrape_zillow_fsbo
try:
    from scrapers.browser_source import scrape_browser_sources as _scrape_browser_sources
    scrape_browser_sources = _scrape_browser_sources
except Exception:
    scrape_browser_sources = None


def run_all() -> dict[str, dict]:
    init_db()
    results: dict[str, dict] = {}
    source_summary: dict[str, dict] = {}
    total_found = 0
    total_new = 0
    sources = [
        ('kern_code_cases', scrape_kern_code_cases),
        ('newspaper_auctions', scrape_newspaper_auctions),
        ('craigslist', scrape_craigslist),
        ('zillow_fsbo', scrape_zillow_fsbo),
        ('kern_tax', scrape_kern_tax),
        ('bakersfield_code', scrape_bakersfield_code),
    ]
    if scrape_browser_sources is not None:
        sources.append(('browser_sources', scrape_browser_sources))
    for source, scrape in sources:
        try:
            found, new, errors = scrape()
        except Exception as exc:
            found, new, errors = 0, 0, f'{type(exc).__name__}: {exc}'
        created_at = datetime.now(timezone.utc).isoformat()
        result = dict(found=found, new=new, errors=errors, err=errors, created_at=created_at)
        source_summary[source] = result
        total_found += found
        total_new += new
        results[source] = result
        print(f'{source}: found={found}, new={new}, errors={errors or "none"}')
    conn = get_conn()
    try:
        with conn:
            for source, result in source_summary.items():
                conn.execute(
                    'INSERT INTO scrape_log (source, source_type, found, new_leads, error, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (source,
                     'browser_sources' if source == 'browser_sources' else 'http',
                     result['found'],
                     result['new'],
                     result['errors'],
                     result['created_at']),
                )
    finally:
        conn.close()
    try:
        from database import save_last_run_summary
        save_last_run_summary(source_summary, total_found, total_new)
    except Exception:
        pass
    return results


def run_loop() -> None:
    while True:
        run_all()
        time.sleep(3600)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--once', action='store_true', help='Run once (default)')
    mode.add_argument('--loop', action='store_true', help='Run every hour')
    args = parser.parse_args()
    if args.loop:
        run_loop()
    else:
        run_all()
