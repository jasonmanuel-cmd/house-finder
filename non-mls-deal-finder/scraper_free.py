"""
No-MLS Free Deal Finder — Main Scraper
Aggregates: Craigslist, Zillow FSBO (via search URLs), Kern County public records checklist

Cost: $0 — no API keys required for basic version
Run: python scraper_free.py --once
     python scraper_free.py --loop (every hour)

Requirements: pip install feedparser requests beautifulsoup4 lxml
"""

import argparse
import time
import sqlite3
import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Import craigslist scraper
try:
    from craigslist_rss import scrape as scrape_craigslist, init_db
except ImportError:
    from craigslist_rss import scrape as scrape_craigslist, init_db

DB_PATH = "deals.db"
GOOGLE_SHEET_WEBHOOK = ""  # Optional: Add Zapier webhook URL to push to Google Sheets

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def init_db_full():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS zillow_fsbo (
            id TEXT PRIMARY KEY,
            address TEXT,
            city TEXT,
            price INTEGER,
            link TEXT,
            zestimate INTEGER,
            deal_score INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def score_free_deal(price, description, zestimate=0):
    score = 0
    desc = description.lower()
    # Price vs Zestimate
    if zestimate > 0 and price > 0:
        discount = (zestimate - price) / zestimate
        if discount >= 0.15:
            score += 4
        elif discount >= 0.10:
            score += 2
        elif discount >= 0.05:
            score += 1
    # Motivation
    for kw in ["as-is", "motivated", "estate", "probate", "tlc", "fixer", "must sell", "vacant", "owner financing"]:
        if kw in desc:
            score += 2
    # Cheap
    if price and price < 50000:
        score += 2
    return min(score, 10)

def scrape_zillow_fsbo_free():
    """
    Free version: Zillow blocks scraping heavily. This is a placeholder that shows HOW to do it manually,
    and provides search URLs for manual checking. For automated, use their RSS or use Apify free tier.

    To avoid getting blocked, we just log the URLs to check manually — this keeps it $0 and legal.
    """
    print("\n--- ZILLOW FSBO (Manual Check URLs - Free) ---")
    urls = [
        "https://www.zillow.com/homes/for_sale/Bakersfield-CA/fsbo/",
        "https://www.zillow.com/homes/for_sale/Tehachapi-CA/fsbo/",
        "https://www.zillow.com/homes/for_sale/California-City-CA/fsbo/",
        "https://www.zillow.com/homes/for_sale/93308_fsbo/  # Bakersfield NW",
    ]
    for u in urls:
        print(f"Check: {u}")
    print("Tip: Open each, filter Price Max $250k, sort Newest. Add good ones to your Google Sheet manually.")
    # If you want automated: Use Apify.com free tier actor "zillow-scraper" —  $0 for 100 listings/month
    return 0

def scrape_kern_tax_defaulted():
    """
    Kern County Treasurer Tax-Defaulted List — Free PDF
    """
    print("\n--- KERN COUNTY TAX-DEFAULTED (Free Public Record) ---")
    url = "https://www.kcttc.co.kern.ca.us/tax-defaulted-property-sales/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'lxml')
            # Find PDF links
            pdfs = [a['href'] for a in soup.find_all('a', href=True) if 'tax-defaulted' in a['href'].lower() or a['href'].endswith('.pdf')]
            print(f"Found {len(pdfs)} tax-defaulted PDFs:")
            for pdf in pdfs[:5]:
                print(f"  PDF: {pdf}")
            print(f"Full page: {url}")
            print("Action: Download latest PDF, extract parcel numbers, look up owners via Assessor (free), contact before auction.")
        else:
            print(f"Could not fetch {url} — status {r.status_code}. Visit manually.")
    except Exception as e:
        print(f"Error fetching tax list: {e} — visit {url} manually")
    return 0

def scrape_kern_nod_instructions():
    print("\n--- KERN COUNTY NOTICE OF DEFAULT (Pre-Foreclosure) — Free Search ---")
    print("URL: https://recorder.kerncounty.com/")
    print("Steps:")
    print("  1. Go to Official Records Search > Grantor/Grantee")
    print("  2. Document Type: NOTICE OF DEFAULT")
    print("  3. Date Range: Last 30 days")
    print("  4. Results show APN + owner name + property address")
    print("  5. Look up owner free via TruePeopleSearch.com for phone")
    print("  6. Add to Google Sheet with Motivation = Pre-foreclosure")
    print("Cost: $0 to search, $0 to get basic info")

def scrape_kern_probate_instructions():
    print("\n--- KERN COUNTY PROBATE (Inherited Homes) — Free ---")
    print("URL: https://www.kern.courts.ca.gov/ > Online Services > Case Search")
    print("Steps:")
    print("  1. Search Case Type: Probate, Filed Date: Last 30 days")
    print("  2. Each case shows Decedent name + Petitioner (heir)")
    print("  3. Cross-reference decedent name with Assessor to find property owned")
    print("  4. Contact heir: often wants to sell as-is for cash")
    print("Cost: $0")

def run_once():
    init_db_full()
    print(f"=== No-MLS Deal Finder Run: {datetime.now()} ===")
    print("Database:", os.path.abspath(DB_PATH))

    # 1. Craigslist (automated, free)
    print("\n[1/5] Scraping Craigslist Bakersfield...")
    scrape_craigslist()

    # 2. Zillow FSBO (manual URLs, free)
    print("\n[2/5] Zillow FSBO...")
    scrape_zillow_fsbo_free()

    # 3. Tax-defaulted
    print("\n[3/5] Kern County Tax-Defaulted...")
    scrape_kern_tax_defaulted()

    # 4. NOD instructions
    print("\n[4/5] NOD Pre-Foreclosure...")
    scrape_kern_nod_instructions()

    # 5. Probate instructions
    print("\n[5/5] Probate...")
    scrape_kern_probate_instructions()

    # Summary
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM deals WHERE deal_score >= 5")
    high_score = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM deals")
    total = c.fetchone()[0]
    conn.close()

    print(f"\n=== SUMMARY ===")
    print(f"Total deals in DB: {total}")
    print(f"High score (5+): {high_score}")
    print(f"Top deals:")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, price, city, deal_score, link FROM deals ORDER BY deal_score DESC, created_at DESC LIMIT 5")
    for row in c.fetchall():
        print(f"  Score {row[3]} | ${row[1]} | {row[2]} | {row[0][:50]} | {row[4]}")
    conn.close()
    print(f"\nNext: Check deals.db with DB Browser (free) or run app.py dashboard")
    print(f"Manual: Add Zillow FSBO + Tax + NOD + Probate leads to same DB / Google Sheet")

def run_loop():
    while True:
        run_once()
        print("\nSleeping 1 hour... (Ctrl+C to stop)")
        time.sleep(3600)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once")
    parser.add_argument("--loop", action="store_true", help="Run every hour")
    args = parser.parse_args()

    if args.loop:
        run_loop()
    else:
        run_once()
