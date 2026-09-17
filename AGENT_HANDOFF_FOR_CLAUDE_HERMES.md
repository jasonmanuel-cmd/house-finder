# AGENT HANDOFF — Harbison Standard Private Seller System
**For: Claude Code / Hermes / Any AI Coding Agent**
**Paste this entire file into Claude Code to finish the project**

---

## PROJECT OVERVIEW — What We're Trying To Do

**Owner:** Nathanael Harbison, REALTOR® DRE #02059393, Harbison Standard, Kern County CA (Bakersfield, Tehachapi, California City)
**Main Site:** https://www.harbisonstandard.com/ (Vercel, Vite + React, repo: Harbison-Standard2)
**Goal 1:** Get harbisonstandard.com found by Google AND AI systems (ChatGPT, Perplexity, Claude, Gemini, Google AI Overviews)
**Goal 2:** Build a system that finds houses NO ONE knows how to find — homeowners who want to sell PRIVATELY without MLS, Zillow, open houses — and want a private guy like Nathanael to handle it quietly

**Two Repos:**
1. **Main Site:** https://github.com/jasonmanuel-cmd/Harbison-Standard2 — Vercel deploys from main
2. **Private Lead System:** https://github.com/jasonmanuel-cmd/private-seller-system — Render deploys dashboard + scraper

---

## WHAT'S BEEN DONE (So You Don't Redo)

### Main Site (Harbison-Standard2) — Repo Cloned at /tmp/hs2 during build
- ✅ Created `src/data/PrivateSale.jsx` — Full page /private-sale — No MLS, No Zillow, private sellers — matches site design (navy #031c2b, gold #edc66f, Libre Caslon Display)
- ✅ Created `src/data/OffMarketDeals.jsx` — Full page /off-market-deals — Explains off-market deals, how we find them, how to get alerts before Zillow
- ✅ Updated `src/seo.js` — Added routes `/private-sale` and `/off-market-deals` with titles, descriptions, Service schema, FAQPage schema (8 Q&As each) — critical for AI citation
- ✅ Updated `src/App.jsx` — Added pages mapping for both routes
- ✅ Updated `scripts/prerender-metadata.mjs` — Added pageHeadings and pageContent for both routes (300+ words each for SEO), sitemap now has 22 routes including both new pages
- ✅ Updated `public/llms.txt` — Replaced with optimized version that helps ChatGPT/Perplexity/Claude understand and cite site (includes private sale program, key pages, common questions)
- ✅ Built locally: `npm run build` succeeds, `dist/client/sitemap.xml` includes `/private-sale` and `/off-market-deals`, `dist/client/private-sale/index.html` and `/off-market-deals/index.html` generated with correct JSON-LD
- ✅ Pushed to main: commits `6528698` and `825acc4`

### Private Lead System (private-seller-system) — The Scraper + Dashboard
- ✅ Built full scraper system in `lead-scraper-system/` folder (now at repo root):
  - `app.py` — Flask dashboard — NOW BRANDED to match Harbison Standard (navy #031c2b, gold #edc66f, logo https://www.harbisonstandard.com/assets/logo.webp, fonts Libre Caslon Display + Open Sans, same header/footer/motto)
  - `run.py` — Orchestrator runs all scrapers
  - `scrapers/craigslist.py` — Craigslist Bakersfield RSS (by owner + land) — FREE, no API
  - `scrapers/zillow_fsbo.py` — Zillow FSBO (tries HTML regex, creates manual check leads — Zillow blocks 403, so manual is needed)
  - `scrapers/kern_tax.py` — Kern County Tax-Defaulted auction PDFs
  - `scrapers/bakersfield_code.py` — Bakersfield vacant/code violations
  - `database.py` — SQLite DB `data/leads.db`
  - `scoring.py` — Deal scoring 1-10 based on keywords (as-is +3, private sale +4, no MLS +4, tax-defaulted +4, etc) + price + source
  - `config.py` — URLs, headers, keywords
- ✅ Dashboard features: Stats (total/hot/warm), filters (Hot 7+, city, source), cards with price/score/motivation/link, Skip Trace Free button (TruePeopleSearch), Assessor Lookup button, Add Manual Lead form (for Facebook Marketplace, driving, wholesaler), Export CSV, Run Scraper Now, Health check route
- ✅ Fixed Render deployment bug: Was hardcoded port 5000, Render uses $PORT (10000) — fixed to use `os.environ.get("PORT", 5000)` + gunicorn — commit `9b604c1` and `b751e7a`
- ✅ Added `render.yaml` — Blueprint for one-click deploy: web service (dashboard) + worker (scraper hourly) + Dockerfile backup + requirements.txt with gunicorn
- ✅ Pushed to main: https://github.com/jasonmanuel-cmd/private-seller-system

### Other Assets Built
- `DEV_PLAYBOOK_HARBISON.md` — Dev playbook to fix Google/AI visibility (technical SEO, GSC, Bing Webmaster, GBP, content expansion, IDX)
- `private-seller-system/` folder (in both repos) — Landing page copy, direct mail letters (5 handwritten letters), Facebook ads ($5/day), phone scripts, target lists (how to build absentee, senior, NOD, tax, probate lists for $0)
- `non-mls-deal-finder/` — Earlier $0 system
- `lead-scraper-system/` — Full system (now at root of private-seller-system repo)

---

## WHAT'S LEFT TO FINISH — Tasks for Claude Code / Hermes

### TASK 1: Main Site — Get /private-sale and /off-market-deals Live on Production
**Status:** Built locally, pushed to GitHub main, but https://www.harbisonstandard.com/private-sale returns 404 — Vercel hasn't auto-deployed

**Do:**
1. Check Vercel dashboard — is Harbison-Standard2 repo connected to Vercel project with auto-deploy on main? If not, connect or trigger manual deploy
2. `cd /tmp/hs2 && npm install && npm run build` — verify build succeeds (should be 22 routes)
3. Check `dist/client/sitemap.xml` includes `/private-sale` and `/off-market-deals` — if yes, deploy
4. Vercel deploy: `vercel --prod` or via dashboard Redeploy
5. After deploy, verify:
   - https://www.harbisonstandard.com/private-sale returns 200, has H1 "Sell your house privately", has FAQPage JSON-LD
   - https://www.harbisonstandard.com/off-market-deals returns 200
   - https://www.harbisonstandard.com/sitemap.xml includes both
   - https://www.harbisonstandard.com/llms.txt returns new optimized version (with private sale program section)
   - https://www.harbisonstandard.com/robots.txt allows GPTBot, PerplexityBot, ClaudeBot, Google-Extended (add to robots.txt if missing — file at `public/robots.txt`)

**Acceptance:** Both URLs return 200, sitemap includes them, llms.txt is new version

### TASK 2: Main Site — Add Nav Links + Internal Linking + GBP
**Do:**
1. In `src/App.jsx`, header nav currently has Home, Our Approach, Properties, Relocate, About, Contact — add Private Sale and Off-Market Deals to nav (or under dropdown)
2. In `src/Home.jsx`, add section linking to /private-sale and /off-market-deals with keyword-rich anchors: "sell house privately in Kern County", "off-market deals in Bakersfield"
3. In `src/data/ContentPages.jsx` CheapLand page, add link to /private-sale and /off-market-deals
4. Ensure `public/robots.txt` has AI bot allowances (see DEV_PLAYBOOK_HARBISON.md for exact block)

**Acceptance:** Nav shows Private Sale, internal links exist, robots.txt allows AI bots

### TASK 3: Private Lead System — Deploy to Render Permanent URL
**Status:** Code fixed for Render (PORT env var + gunicorn), pushed to GitHub, but Render service may be failing or not created. User gave Render outbound IPs `74.220.48.0/24` and `74.220.56.0/24` — these are Render NAT gateways used for scraping.

**Do:**
1. Check Render dashboard — does service `private-seller-dashboard` exist? If failing, check logs — should have been failing on port 5000 before fix commit `9b604c1`
2. If service exists: Manual Deploy → Deploy latest commit `b751e7a` — should now start with `gunicorn app:app --bind 0.0.0.0:$PORT`
3. If service doesn't exist: New + → Blueprint → Connect `jasonmanuel-cmd/private-seller-system` repo → Apply `render.yaml` — creates web (dashboard) + worker (scraper loop)
4. Verify dashboard loads at `https://private-seller-dashboard.onrender.com` (or similar URL) — should show branded UI with logo, navy/gold, 10 leads, filters
5. Test health route: `/health` should return JSON `{"status":"ok"}`
6. Test scraper: Click "Run Scraper Now" → should scrape Craigslist RSS (may find 0-2 new leads depending on day) + create Zillow FSBO manual check leads
7. Note: Render free tier filesystem is ephemeral — `data/leads.db` resets on each deploy. Solution: Add Render Disk (1GB free) mounted at `/app/data` OR export CSV weekly to Google Sheets. Add note to README.

**Acceptance:** Dashboard loads at permanent Render URL, branded UI visible, Run Scraper works, health check OK

### TASK 4: Private Lead System — Improve Scrapers (Optional but High Value)
**Do:**
1. Craigslist RSS currently returns 0 — check if RSS feeds in `config.py` are still valid (Craigslist changes format). Try `https://bakersfield.craigslist.org/search/reo?format=rss` — if blocked, try using `https://bakersfield.craigslist.org/d/real-estate/search/reo?format=rss`
2. Zillow FSBO returns 403 — expected, Zillow blocks. Keep manual check leads but add note to dashboard that Zillow requires manual daily check (link to FSBO URLs). Optionally add Apify free tier actor `zillow-scraper` as alternative (100 listings/month free)
3. Kern County Tax-Defaulted URL changed from `/tax-defaulted-property-sales/` to maybe `/` — check https://www.kcttc.co.kern.ca.us/ for new path, update `KERN_TAX_URL` in config.py and scraper
4. Add proxy support for Render IPs if Craigslist blocks `74.220.48.0/24` — add option to use ScraperAPI free tier or similar
5. Add Google Sheets sync: When new lead with score 7+ found, push to Google Sheet via webhook (user can add Zapier webhook URL in config)

**Acceptance:** Craigslist scraper finds at least 1-2 leads when posts exist, Zillow manual leads exist, tax scraper finds PDFs or creates manual instruction lead

### TASK 5: Documentation — How User Finds Leads (User Asked: "how do i find the lead it find")
**Do:**
1. Update `README.md` in private-seller-system repo with clear section "How to Find Leads This System Finds" — include daily 30-min routine, weekly county checks, Facebook manual workflow, driving for dollars
2. Add video or GIF of dashboard usage (optional)
3. Ensure `private-seller-system/README.md` explains Private Sale Program (why homeowners want private, how process works)

**Acceptance:** README has clear daily checklist user can follow

---

## ARCHITECTURE

```
Main Site (Harbison-Standard2):
  Vite + React + Vercel
  src/App.jsx — routing
  src/seo.js — routes, titles, descriptions, FAQ, JSON-LD
  src/data/PrivateSale.jsx — /private-sale page
  src/data/OffMarketDeals.jsx — /off-market-deals page
  scripts/prerender-metadata.mjs — generates dist/client/sitemap.xml + dist/client/[page]/index.html with SEO
  public/llms.txt — for AI citation
  public/robots.txt — should allow AI bots

Private Lead System (private-seller-system):
  Flask + SQLite + Render
  app.py — Dashboard UI (branded navy #031c2b gold #edc66f)
  run.py — Orchestrator
  scrapers/craigslist.py — RSS feedparser
  scrapers/zillow_fsbo.py — HTML regex + manual leads
  scrapers/kern_tax.py — BeautifulSoup PDF links
  scrapers/bakersfield_code.py — Open data + manual
  database.py — SQLite data/leads.db
  scoring.py — 1-10 scoring
  config.py — URLs
  render.yaml — Render Blueprint
  requirements.txt — with gunicorn
  Dockerfile — backup
  private-seller-system/ — Letters, scripts, ads, target lists, landing page copy
```

---

## HOW TO RUN LOCALLY (For Claude Code)

```bash
# Main Site
cd /tmp/hs2
npm install
npm run build
# Check dist/client/private-sale/index.html exists and sitemap.xml includes /private-sale and /off-market-deals

# Private Lead System
cd /path/to/private-seller-system
pip install -r requirements.txt
python run.py --once
python app.py
# Open http://localhost:5000
```

---

## DEPLOYMENT

**Main Site — Vercel:**
- Connected to Harbison-Standard2 main branch
- Auto-deploys on push to main (if not, trigger manually via Vercel dashboard or `vercel --prod`)
- Env: No env vars needed

**Private Lead System — Render:**
- Blueprint: render.yaml
- Web Service: `private-seller-dashboard` — Build `pip install -r requirements.txt`, Start `gunicorn app:app --bind 0.0.0.0:$PORT`, Free tier, PORT 10000
- Worker: `private-seller-scraper` — Build same, Start `python run.py --loop`, Free tier, runs hourly
- Outbound IPs: 74.220.48.0/24 and 74.220.56.0/24 (Render NAT gateways) — used for scraping, may be blocked by Craigslist/Zillow, need proxy if blocked
- DB: data/leads.db is ephemeral on free tier — will reset on deploy — need Render Disk or Google Sheets backup

---

## BRANDING — Must Match Main Site

- Navy: #031c2b
- Gold: #edc66f
- Muted Gold: #b78b43
- Light: #f6f5ef
- Border: #e3ddcf
- Fonts: Open Sans (body), Libre Caslon Display (headings), Libre Caslon Text (em)
- Logo: https://www.harbisonstandard.com/assets/logo.webp (white version on navy)
- Button: .gold class — background #edc66f, color #07131c, min-height 42px, min-width 176px, padding 11px 22px, border-radius 2px, font-weight 700, font-size 12px, letter-spacing 1px, text-transform uppercase, box-shadow inset 0 0 18px #ffeba65c
- Motto: "It's not what you do, it's how you do it."

Dashboard already branded to match — check app.py DASHBOARD_HTML

---

## USER'S EXACT WORDS — What They Want

> "i wnan find a way to find the house and listing that noone know how to find or the homeower that wanna sell their house and but dont wanna usee the mls and mainsteam way and want to have it sold by a privte guy like Nathanael"

> "can you just build me the system that will scarp all the data from all the placess to find me good leads on the places"

> "can you build me the system that will scarp all the data from all the placess to find me good leads on the places" + "how do i find the lead it find can we make a ui build off the logo and same color and style of the main page then upload both to the github"

Translation: Build scraper for off-market private sellers who want quiet sale, branded dashboard matching main site, upload to GitHub, deploy to Render permanent URL, add /private-sale and /off-market-deals pages to main site.

---

## TOKENS / SECRETS

- GitHub PAT used earlier: [REDACTED - DELETED] — USER WAS TOLD TO DELETE IT — DO NOT USE IT AGAIN — ask user for new token if needed
- No Vercel token provided yet — need to ask user or use Vercel dashboard manual deploy
- No Render token provided — user will deploy via Render dashboard Blueprint

---

## FINAL CHECKLIST FOR CLAUDE CODE / HERMES

- [ ] Main site builds with 22 routes, sitemap includes /private-sale and /off-market-deals
- [ ] https://www.harbisonstandard.com/private-sale returns 200 (after Vercel deploy)
- [ ] https://www.harbisonstandard.com/off-market-deals returns 200
- [ ] https://www.harbisonstandard.com/llms.txt is new optimized version
- [ ] https://www.harbisonstandard.com/robots.txt allows GPTBot, PerplexityBot, ClaudeBot
- [ ] Nav includes Private Sale and Off-Market Deals (optional but nice)
- [ ] Private lead dashboard loads at Render permanent URL with branded UI (navy/gold/logo)
- [ ] Dashboard health route /health returns ok
- [ ] Run Scraper Now works, adds leads to DB
- [ ] Craigslist scraper finds leads when posts exist (check RSS validity)
- [ ] README explains daily routine how user finds leads
- [ ] Both repos pushed to main with latest fixes

---

## CONTACT

Owner: Nathanael Harbison — nate85.realtor@gmail.com — (661) 472-7499
Dev: jasonmanuel-cmd on GitHub

Good luck — this system finds private sellers who want quiet sale, no MLS, no Zillow, no open houses — exactly what Nathanael wants to be known for: The Private Guy in Kern County.
