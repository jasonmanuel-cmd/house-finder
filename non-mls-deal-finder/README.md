# No-MLS Deal Finder System — $0 to $30/month — Kern County
**For:** Harbison Standard | **Goal:** Find off-market / pre-market / good deals WITHOUT paying for MLS or PropStream

This system finds properties using 100% free public data + free classifieds. It costs $0 if you do manual version, $0-30 if you automate with free tiers.

## How It Works (Overview)
```
FREE SOURCES → SCRAPER (Python) → SQLite DB → DEAL SCORE → Google Sheet / Slack / Email Alert
```

## Sources (All Free, No MLS)

### Tier 1 — Daily Check (Highest Deal Rate)
1. **Craigslist Bakersfield — Housing > Real Estate For Sale + By Owner**
   - URL: https://bakersfield.craigslist.org/d/real-estate/search/rea?query=Tehachapi|Bakersfield&bundleDuplicates=1&hasPic=1&srchType=T
   - RSS: https://bakersfield.craigslist.org/search/rea?format=rss&query=Tehachapi&srchType=T
   - Why: FSBO sellers, cheap land, distressed, no agent = deal
   - Cost: $0

2. **Facebook Marketplace + Facebook Groups**
   - Marketplace: Search "Tehachapi land", "Bakersfield house for sale by owner", filter max $250k
   - Groups (join these free):
     - Tehachapi Homes for Sale / Rent
     - Bakersfield Real Estate for Sale By Owner
     - Bakersfield Wholesale Real Estate
     - California City Land for Sale
     - Kern County Real Estate Investors
   - Why: 60% of cheap land in California City is sold via FB, not MLS
   - Cost: $0 — manual check 10 min/day, or automate with free Apify trial

3. **Zillow FSBO + For Sale By Owner Section**
   - URL: https://www.zillow.com/homes/for_sale/Bakersfield-CA/fsbo/
   - Also: https://www.zillow.com/homes/for_sale/Tehachapi-CA/fsbo/
   - Why: FSBO sellers often underprice, open to owner financing
   - Cost: $0 to browse

4. **Kern County Tax-Defaulted Properties (County Treasurer)**
   - URL: https://www.kcttc.co.kern.ca.us/tax-defaulted-property-sales/
   - They publish annual auction list PDF + parcel numbers. Previous lists stay online.
   - Why: Properties with 5+ years unpaid taxes = extremely motivated, can contact owner BEFORE auction
   - Cost: $0 — public record

5. **Kern County Notice of Default (NOD) — Pre-Foreclosure**
   - URL: Kern County Recorder Online Search: https://recorder.kerncounty.com/
   - Search Document Type: Notice of Default, Date: last 30 days
   - Why: Homeowner just got NOD, has 90 days to sell before auction = deal
   - Cost: $0 to search, $1-2 per doc if you want full copy (optional)

6. **Probate Cases — Kern County Superior Court**
   - URL: https://www.kern.courts.ca.gov/ — Case Search > Probate
   - Search new probate filings last 30 days
   - Why: Inherited homes often sold as-is, below market, family wants fast cash
   - Cost: $0

### Tier 2 — Weekly Check
7. **City of Bakersfield Code Violations (Open Data)**
   - URL: https://data.bakersfieldcity.us/ — search "code enforcement" or "nuisance complaints"
   - Why: House with code violations = distressed owner = deal
   - Cost: $0

8. **Wholesaler Buyers Lists (Free to Join)**
   - Search Facebook: "Bakersfield Wholesale", "Kern County Off Market"
   - Get on 10 wholesalers' email lists — they send you deals at 70% ARV
   - Why: Wholesalers find off-market, you get first dibs if you're on list
   - Cost: $0

9. **Driving for Dollars (Free, just gas)**
   - Drive Golden Hills, Bear Valley Springs, Stallion Springs, California City
   - Look for: overgrown yard, boarded windows, tarp roof, no trespassing, vacant
   - Use free app: DealMachine free trial, or just write address, look up owner free via Kern County Assessor Parcel Search: https://assessor.kerncounty.com/
   - Why: Best way to find vacant absentee owners who will sell cheap

---

## The System — 2 Options

### OPTION A: Manual $0 System (Start Today, 30 min/day)
No code needed.

**Setup (1 hour):**
1. Create Google Sheet: "Kern No-MLS Deals" with columns:
   - Date Found | Address | City | Price | Source (Craigslist/FB/Zillow/Tax/NOD/Probate/Driving) | Owner Name | Owner Phone | Motivation (Tax/Pre-foreclosure/Probate/Vacant/FSBO) | Deal Score (1-10) | Contacted? | Notes | Link

2. Create bookmarks folder "Daily Deal Check" with these links:
   - Craigslist Bakersfield RE
   - Facebook Marketplace Tehachapi land
   - Zillow FSBO Bakersfield
   - Zillow FSBO Tehachapi
   - Kern County Tax Defaulted Sales page
   - Kern County Recorder NOD search
   - Kern County Court Probate search

3. Morning Routine (30 min):
   - 6:00-6:10: Check Craigslist RSS (2-3 new posts/day), add to sheet
   - 6:10-6:20: Check FB Marketplace + 2 FB groups, add to sheet
   - 6:20-6:25: Check Zillow FSBO (usually 5-10 new/week)
   - 6:25-6:30: Score deals, call top 2

**Deal Scoring (Manual):**
- +3 points: Price 15%+ below Zestimate/Redfin
- +2 points: Keywords: as-is, motivated, estate, probate, needs work, must sell
- +2 points: Vacant / overgrown / no interior photos
- +2 points: Owner out-of-state (check assessor — mailing address != property address)
- +1 point: Owner financing offered
- 8-10 = Call immediately, 5-7 = Call today, <5 = watch

**Contact Script (Free):**
For FSBO: "Hi, saw your property at 123 Main on Craigslist — I'm a local agent with Harbison Standard in Tehachapi. I have buyers looking for that area. Are you open to offers? Are you flexible on price if we can close fast?"

For Tax/NOD/Probate: "Hi, I'm Nathanael, local real estate agent in Kern County. I saw public record that your property at 123 Main may have [taxes due / NOD filing / probate case]. I'm not sure your situation, but if you're considering selling as-is for cash/quick close, I have options and can help you understand what it's worth. No pressure — just wanted to reach out."

### OPTION B: Automated $0-30 System (Python Scraper + Alerts)
This is what I built for you in this folder.

**What it does:**
- Scrapes Craigslist Bakersfield RSS every hour
- Scrapes Zillow FSBO (via free search, no API key)
- Checks Kern County Treasurer tax-defaulted PDF (when updated)
- Scores each property automatically
- Saves to SQLite + Google Sheet + sends email/Slack alert for score 8+

**Files in this folder:**
- `scraper_free.py` — Main scraper
- `craigslist_rss.py` — Craigslist-specific
- `kern_county_sources.md` — How to pull county data
- `app.py` — Simple dashboard to view deals (run locally)
- `requirements.txt`

**To run (free):**
```bash
pip install -r requirements.txt
python scraper_free.py --once  # test run
python scraper_free.py --loop  # run every hour
```

Or deploy free on Render.com / Fly.io free tier, or run on your laptop via cron.

---

## Free Owner Lookup (Skip Tracing for $0)

You found address, need owner phone. Free methods:

1. **Kern County Assessor Parcel Search (free):** https://assessor.kerncounty.com/parcel-search/
   - Enter APN or address → gives owner name + mailing address
   - If mailing address != property address = absentee owner = more motivated

2. **TruePeopleSearch.com (free):** Search owner name + city → gives phone, relatives
3. **FastPeopleSearch.com (free):** Similar
4. **WhitePages.com free tier:** Gives 1-2 numbers

Paid skip tracing is $0.15 per lookup (BatchLeads, IDI), but you can start free.

---

## How to Get Deals Under Contract Without MLS

Once you find motivated seller:

1. **Call fast:** Speed wins. Call within 1 hour of posting
2. **Qualify:** Why selling? Timeline? Price flexibility? Condition? Mortgage owed?
3. **Comp it:** Use Redfin/Zillow comps last 90 days, same zip, +/-200 sqft
4. **Offer as-is, quick close, no contingencies if investor buyer**
5. **Two exit strategies:**
   - Assign to your investor buyer list (wholesale fee $5-10k) — legal in CA if you disclose
   - List it on MLS as your listing (get commission) — if seller wants retail but cheap

**Example — California City land:**
- Craigslist: 0.25 acre, $12k, owner in LA, owns 10 years, overgrown
- Assessor: Owner mailing address Los Angeles, absentee
- Comp: Similar lots selling $18-22k
- Call: "Would you take $9k cash, close in 10 days?" Owner says yes (tired of taxes)
- You assign to investor for $14k = $5k spread, or list at $18k

---

## Daily / Weekly Checklist

**Daily 30 min:**
- [ ] Run scraper or check bookmarks (Craigslist, FB, Zillow FSBO)
- [ ] Add 3-5 new leads to Google Sheet
- [ ] Score, call top 2
- [ ] Update sheet: Contacted? Response?

**Weekly 1 hour:**
- [ ] Check Kern County Treasurer tax-defaulted list (new PDFs)
- [ ] Check Recorder NOD search last 7 days
- [ ] Check Superior Court probate filings
- [ ] Drive 1 neighborhood for 1 hour (Driving for Dollars)
- [ ] Email your buyer list: "3 off-market deals this week not on Zillow"

**Monthly:**
- [ ] Attend Bakersfield REIA meetup (free), network with wholesalers
- [ ] Post in FB groups: "I pay $500 referral for off-market land/houses in Tehachapi/Bakersfield"

---

## Cost Breakdown

| Tool | Cost |
|------|------|
| Craigslist RSS | $0 |
| Facebook Marketplace/Groups | $0 |
| Zillow FSBO browsing | $0 |
| Kern County Assessor / Recorder / Treasurer / Court | $0 |
| TruePeopleSearch / FastPeopleSearch | $0 |
| Google Sheets + Gmail | $0 |
| Python scraper hosting (Render free tier) | $0 |
| DealMachine (optional) | $49/mo (free trial 7 days) |
| BatchLeads skip tracing (optional) | $0.15/lookup |
| **Total to start** | **$0** |

---

## Want Me to Deploy It?

I can:
1. Deploy the scraper to run hourly for free on Render
2. Build a simple dashboard at harbisonstandard.com/deals (password protected)
3. Connect to Google Sheets + Slack alerts
4. Create email templates for each motivation type

Say "deploy the free deal finder" and I'll build it.

