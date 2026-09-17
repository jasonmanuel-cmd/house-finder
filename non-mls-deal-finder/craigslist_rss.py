"""
Free Craigslist Scraper — Kern County No-MLS Deal Finder
Cost: $0 — uses RSS feed, no API key
Run: python craigslist_rss.py
"""
import feedparser
import re
import sqlite3
import os
from datetime import datetime

# Craigslist RSS feeds for Kern County area
RSS_FEEDS = [
    "https://bakersfield.craigslist.org/search/rea?format=rss&query=Tehachapi&srchType=T",
    "https://bakersfield.craigslist.org/search/rea?format=rss&query=Bakersfield&bundleDuplicates=1&hasPic=1&srchType=T",
    "https://bakersfield.craigslist.org/search/rea?format=rss&query=California%20City&srchType=T",
    "https://bakersfield.craigslist.org/search/reo?format=rss&query=Tehachapi|Bakersfield&srchType=T",  # by owner
    "https://bakersfield.craigslist.org/search/rea?format=rss&query=land%20acre&srchType=T",
]

DB_PATH = "deals.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            published TEXT,
            price INTEGER,
            city TEXT,
            description TEXT,
            source TEXT,
            deal_score INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def extract_price(title):
    # Craigslist titles often like "$40,000 - 0.3 acre lot Tehachapi"
    m = re.search(r'\$([\d,]+)', title)
    if m:
        return int(m.group(1).replace(',', ''))
    return 0

def score_deal(title, description, price):
    score = 0
    text = (title + " " + description).lower()
    # Motivation keywords
    motivated_keywords = ["as-is", "as is", "motivated", "must sell", "estate", "probate", "trust sale", "tlc", "handyman", "investor", "needs work", "fixer", "vacant", "owner financing", "owner will carry"]
    for kw in motivated_keywords:
        if kw in text:
            score += 2
    # Cheap land
    if price > 0 and price < 50000:
        score += 3
    elif price > 0 and price < 100000:
        score += 1
    # Acreage
    if "acre" in text:
        score += 1
    # Absentee / out of state hint
    if "out of state" in text or "absentee" in text or "los angeles owner" in text:
        score += 2
    # Cap at 10
    return min(score, 10)

def scrape():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    new_count = 0

    for rss_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                deal_id = entry.get('id', entry.link)
                # Check if already exists
                c.execute("SELECT id FROM deals WHERE id=?", (deal_id,))
                if c.fetchone():
                    continue

                title = entry.title
                link = entry.link
                published = entry.get('published', '')
                desc = entry.get('description', '')[:2000]
                price = extract_price(title)
                # Extract city from title or rss url
                city = "Bakersfield"
                if "tehachapi" in rss_url.lower() or "tehachapi" in title.lower():
                    city = "Tehachapi"
                elif "california city" in title.lower():
                    city = "California City"

                deal_score = score_deal(title, desc, price)

                c.execute("""
                    INSERT INTO deals (id, title, link, published, price, city, description, source, deal_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (deal_id, title, link, published, price, city, desc, "craigslist", deal_score, datetime.now().isoformat()))
                new_count += 1
                print(f"[NEW] Score {deal_score}/10 | ${price} | {city} | {title[:60]} | {link}")

        except Exception as e:
            print(f"Error scraping {rss_url}: {e}")

    conn.commit()
    conn.close()
    print(f"\nDone. {new_count} new deals added to {DB_PATH}")

if __name__ == "__main__":
    scrape()
