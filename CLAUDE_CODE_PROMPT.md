# COPY-PASTE THIS INTO CLAUDE CODE / HERMES

You are finishing Harbison Standard Private Seller System. Read AGENT_HANDOFF_FOR_CLAUDE_HERMES.md for full context.

**Goal:** Find houses no one knows how to find — homeowners who want to sell PRIVATELY without MLS, Zillow, open houses — to a private guy like Nathanael Harbison (REALTOR DRE #02059393, Kern County).

**Two repos already built and pushed:**
1. Main site: https://github.com/jasonmanuel-cmd/Harbison-Standard2 — Vite + React + Vercel — has /private-sale and /off-market-deals pages built but 404 in prod because Vercel hasn't deployed. Fix: `npm run build` should show 22 routes, sitemap includes both, then `vercel --prod` or dashboard redeploy. Also ensure public/llms.txt is new optimized version and robots.txt allows GPTBot, PerplexityBot, ClaudeBot.
2. Private lead system: https://github.com/jasonmanuel-cmd/private-seller-system — Flask + SQLite + Render — dashboard branded navy #031c2b gold #edc66f matching main site, scrapes Craigslist RSS, Zillow FSBO, Kern tax-defaulted, NOD, probate, vacant, Facebook manual, wholesaler. Fixed port bug (was 5000, Render needs $PORT). Has render.yaml for one-click deploy. Check Render dashboard, deploy latest commit b751e7a, ensure dashboard loads at permanent URL with logo and branded UI, /health returns ok, Run Scraper Now works.

**Tasks left:**
- Main site: Get /private-sale and /off-market-deals live (Vercel deploy), add nav links, check llms.txt and robots.txt, internal linking
- Private system: Deploy to Render permanent URL (dashboard + worker), fix Craigslist RSS if needed (currently 0 found), handle Zillow 403 (expected, keep manual leads), fix Kern tax URL (404), note ephemeral DB on free tier needs backup
- Update READMEs with daily routine: how user finds leads (30 min morning: Run Scraper, check Hot 7+, call via TruePeopleSearch free, check Facebook Marketplace + 5 FB groups + add via dashboard form, weekly county records)

**Branding must match:** navy #031c2b, gold #edc66f, muted-gold #b78b43, light #f6f5ef, fonts Open Sans + Libre Caslon Display, logo https://www.harbisonstandard.com/assets/logo.webp, motto "It's not what you do, it's how you do it."

**Run locally:**
```
cd /tmp/hs2 && npm install && npm run build && ls dist/client/ | grep private
cd /path/to/private-seller-system && pip install -r requirements.txt && python run.py --once && python app.py
```

**Do not use old GitHub PAT ghp_5qhEqSrU... — it was deleted. Ask user for new token if push needed.**

Finish checklist in AGENT_HANDOFF_FOR_CLAUDE_HERMES.md and push to both repos main.
