"""
Config for Kern County No-MLS Lead Scraper

Live sources (as of 2026-09-15):
- Kern County Tax Auction: discovered from the public general tax page, then parsed from the live
  GovEase auction browse page (public parcel listings, no login required).
- Kern County Assessor-Recorder: current domain is kerncounty.com (old kerncountyca.gov has no A records);
  site returns 403 to plain HTTP / headless browser without proper session — manual research resource.
- Bakersfield Building Permits: bakersfieldcity.us (CivicPlus) — live, reachable via browser.
- Tehachapi: current domain being confirmed; tehachapica.gov has no A records.

Sources that are blocked for automated retrieval and must be checked manually:
- Zillow FSBO: returns 403 to automated requests. Use the Zillow note on the dashboard to
  browse manually and add promising owners via the Add Manual Lead form.
- Craigslist: may return 403 or malformed/non-RSS responses; treat as best-effort and verify
  manually when blocked.
- Kern County Assessor-Recorder (kerncounty.com): 403 to browser; manual resource.

Scoring:
- SCORE_KEYWORDS and extra scoring logic live in scoring.py.
- Headers are reused across request-based scrapers; the browser-based scraper keeps its own
  controlled browser fingerprint.
"""
import os

# Database path can be overridden for tests or hosted disk mounts (e.g. Render volume).
DB_PATH = os.environ.get("DB_PATH") or os.path.join(os.path.dirname(__file__), "data", "leads.db")


# --- Kern County Tax Auction ---
KERN_TAX_GENERAL_PAGE = "https://www.kcttc.co.kern.ca.us/index.cfm?fuseaction=kcttcinternet.showGeneralTaxSaleInfo"
GOVEGEASE_AUCTION_HOST = "https://liveauctions.govease.com"
GOVEGEASE_BROWSE_PATH = "/ca/cakern/{auction_id}/browsestandard"

# Kern County Assessor-Recorder (current domain; site 403s automated access — manual resource)
KERN_COUNTY_ASSESSOR_URL = "https://www.kerncounty.com/assessor-recorder"

# Bakersfield building permits (live, reachable via browser)
BAKERSFIELD_PERMITS_URL = "https://www.bakersfieldcity.us/building-permits"
BAKERSFIELD_PERMIT_STATUS_URL = "https://www.bakersfieldcity.us/online-permit-application-and-status"

# Tehachapi — current domain confirmed: liveuptehachapi.com (CivicPlus)
TEHACHAPI_CITY_URL = "https://www.liveuptehachapi.com/"


# --- Public record / government source URLs ---
GOV_SOURCES = {
    "kern_county_assessor_recorder": {
        "label": "Kern County Assessor / Recorder",
        "start_url": KERN_COUNTY_ASSESSOR_URL,
        "kind": "government",
        "tags": ["public-records", "javascript-heavy"],
        "notes": "County assessor/recorder public-records landing surface (kerncounty.com; 403 to automated access).",
    },
    "kern_county_probate": {
        "label": "Kern County Probate",
        "start_url": "https://www.kerncounty.com/county-services/probate",
        "kind": "government",
        "tags": ["public-records", "case-search"],
        "notes": "Probate court public-case surface.",
    },
    "bakersfield_building_safety": {
        "label": "City of Bakersfield Building and Safety",
        "start_url": BAKERSFIELD_PERMITS_URL,
        "kind": "government",
        "tags": ["code-enforcement", "building-permits"],
        "notes": "Building / code-enforcement public surface (bakersfieldcity.us / CivicPlus).",
    },
    "bakersfield_planning": {
        "label": "City of Bakersfield Planning Department",
        "start_url": "https://www.bakersfieldcity.us/departments/community-services/planning",
        "kind": "government",
        "tags": ["planning", "javascript-heavy"],
        "notes": "City planning surface; may hold permits / zoning / vacant-lot references.",
    },
    "tehachapi_city": {
        "label": "City of Tehachapi",
        "start_url": TEHACHAPI_CITY_URL,
        "kind": "government",
        "tags": ["city-portal", "javascript-heavy"],
        "notes": "Tehachapi city site; may link to building / permits / code surfaces.",
    },
}


# --- Scoring keywords (documented in scoring.py) ---
SCORE_KEYWORDS = {
    "as-is": 3, "as is": 3, "motivated": 3, "must sell": 3, "estate": 3, "probate": 4,
    "trust sale": 3, "tlc": 2, "handyman": 2, "fixer": 2, "investor": 2, "needs work": 2,
    "vacant": 3, "owner financing": 3, "owner will carry": 3, "private sale": 4,
    "no mls": 4, "off market": 3, "divorce": 3, "relocating": 2, "behind on payments": 4
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

ZILLOW_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.zillow.com/",
}

# Craigslist search API (current public endpoint the site itself uses; RSS is dead).
# searchPath=rea is real estate listings; srchType=T filters to by-owner posts.
CRAIGSLIST_API = "https://sapi.craigslist.org/web/v8/postings/search/full"
CRAIGSLIST_QUERIES = [
    {"cat": "rea", "searchPath": "area/bakersfield", "srchType": "T"},  # by-owner real estate
    {"cat": "rea", "searchPath": "area/bakersfield"},                    # all real estate
]

# Zillow FSBO search pages to inspect as a manual research resource.
ZILLOW_FSBO_URLS = [
    "https://www.zillow.com/search/GetSearchPageState.htm?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22usersSearchTerm%22%3A%22Bakersfield%2CA%20CA%22%2C%22spatialMetadata%22%3A%7B%22debounce%22%3A300%2C%22userInput%22%3A%22Bakersfield%2CA%20CA%22%7D%2C%22searchType%22%3A%22default%22%2C%22-canonicalValue%22%3Atrue%7D",
]

# Kern County Tax Auction general info page (for auction-ID discovery; actual parcels come from GovEase).
KERN_TAX_URLS = [
    "https://www.kcttc.co.kern.ca.us/index.cfm?fuseaction=kcttcinternet.showGeneralTaxSaleInfo",
]
