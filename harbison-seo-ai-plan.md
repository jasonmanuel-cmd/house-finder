# Harbison Standard — Google + AI Visibility Audit & 90-Day Plan
**Site:** https://www.harbisonstandard.com/ | Date: 2026-09-14 | Agent: Nathanael Harbison DRE #02059393

## Current Diagnosis (Why You're Invisible)

**What's GOOD — you have a better foundation than most:**
- Clean, fast Vercel hosting, HTTPS, mobile-friendly
- sitemap.xml + sitemap-images.xml + robots.txt present and correct
- Proper canonical, OG tags, Twitter cards
- Excellent JSON-LD: RealEstateAgent, Organization, WebSite, WebPage, FAQPage with NAP consistent
- Clear E-E-A-T signals: DRE number, phone, email on every page

**What's KILLING your visibility:**

1.  **Thin content / few indexable URLs:** Sitemap has ~20 URLs, but only 2 active listings. Google sees you as a 10-page brochure, not a market resource. `site:harbisonstandard.com` returns 0 in Google right now — you are barely indexed.
2.  **No IDX feed:** You manually add listings. That means no daily fresh content, no 1,000s of listing pages for Google to crawl, no "Just Listed" freshness signal.
3.  **No blog / market updates:** AI systems (ChatGPT, Perplexity, Gemini) cite sites that ANSWER QUESTIONS. You have 4 FAQ answers on homepage. You need 50+ Q&A pages.
4.  **No llms.txt / no AI instructions:** ChatGPT, Claude, Perplexity now actively look for /llms.txt to understand how to cite you. You don't have one.
5.  **Weak off-site footprint:** AI training data is 61% Zillow, Realtor.com, Redfin, Homes.com. You have Compass, HomeLight, FastExpert profiles but they are incomplete and inconsistent. No Google Business Profile posts, no Expertise.com, ThreeBestRated, Yelp, Apple Maps.
6.  **Bing ignored:** ChatGPT uses Bing index. Perplexity uses Bing + its own crawler. You have not submitted to Bing Webmaster Tools.
7.  **No location density:** You serve 5 cities but only have generic pages. You need dedicated pages for each: "Tehachapi land for sale under $50k", "Bakersfield homes with acreage", "California City cheap land", etc.

---

## PART 1: Get Found by Google (7-Day Sprint)

### Day 1-2: Fix Technical
- [ ] Upload `/llms.txt` (provided in workspace) to your site root — same folder as robots.txt. In Vercel, put it in `/public/llms.txt`
- [ ] Add to robots.txt:
```
User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /
```
- [ ] Verify in Google Search Console (search.google.com/search-console) — submit both sitemaps
- [ ] Verify in Bing Webmaster Tools (bing.com/webmasters) — CRITICAL for ChatGPT visibility. Submit sitemaps there too.
- [ ] Add lastmod dates to sitemap.xml — Google prioritizes fresh URLs
- [ ] Add Image alt text to every property image: e.g. "0.3 acre lot at 22208 Mariposa Rd Tehachapi CA for $40k"

### Day 3-4: Google Business Profile (GBP) — #1 Ranking Factor for "realtor near me"
You MUST have this optimized:
- Create/Claim "Harbison Standard - Nathanael Harbison" in Google Business Profile
- Category: Real Estate Agency, Real Estate Agent
- Exact NAP: Harbison Standard, Tehachapi, CA, (661) 472-7499 — use SAME format everywhere
- Services: Buyer representation, Seller representation, Land sales, Investment properties, As-is home sales, Probate/inherited homes
- Description: 750 chars with keywords: "Kern County REALTOR® Nathanael Harbison helps buyers, sellers, and investors in Tehachapi, Bakersfield, California City... cheap land, acreage, investment properties..."
- Add 20+ photos: headshot, logo, Tehachapi mountains, listings, you with clients
- Start weekly GBP Posts: Q&A format: "What does $40k buy in Tehachapi right now?" with link to property
- Get 10 reviews in 30 days — ask past clients to mention "Tehachapi", "land", "Bakersfield" in review text

### Day 5-7: Content Expansion (What Google and AI Actually Cite)
Create 15 new pages — each 800-1200 words, with FAQ schema:

**Location Cluster:**
1. Tehachapi Land for Sale Under $50K
2. Tehachapi Homes for Sale with Acreage
3. Bakersfield Homes for Sale Under $400K
4. California City Cheap Land — What to Know Before Buying
5. Stallion Springs Homes for Sale
6. Bear Valley Springs Real Estate

**Intent Cluster:**
7. How to Sell Your Home As-Is in Kern County (timeline, costs, when it makes sense)
8. Inherited House in Bakersfield — What Are Your Options?
9. Owner Financing Land in Tehachapi — How It Works
10. Moving from Los Angeles to Bakersfield — Complete Cost Comparison 2026
11. Best Neighborhoods in Bakersfield for First-Time Buyers
12. Tehachapi vs Bakersfield — Where Should You Buy?

**Market Update Template (publish weekly):**
13. Kern County Market Update — [Month Year] — Avg price, DOM, inventory, what it means for buyers/sellers

Each page MUST have:
- H1 with keyword + location
- 3-4 H2s phrased as questions people ask AI: "What does cheap land cost in Kern County?" "Is Tehachapi a good investment?"
- FAQ section at bottom (3-5 Q&A) with JSON-LD FAQPage schema (you already do this — replicate)
- Internal links to /properties and /contact
- 1 YouTube video embed if possible (transcribe it below video for AI)

## PART 2: Get Found by AI Systems (ChatGPT, Perplexity, Claude, Gemini, Google AI Overviews)

AI search doesn't "rank" — it synthesizes answers from sources it trusts. To be cited:

**1. llms.txt + Structured Data (done)**
- Upload llms.txt provided
- Add Article schema to every new blog post: author = Nathanael Harbison, with sameAs links
- Add VideoObject schema for every YouTube video: include transcript

**2. Be Everywhere AI Learns From (Off-Site Authority)**
AI models learned from portals. You need consistent citations there:
- Complete profiles: Zillow Agent Finder, Realtor.com, Homes.com, HomeLight, FastExpert, Expertise.com, ThreeBestRated.com, Yelp, Thumbtack
- Ensure EVERY profile uses identical: Nathanael Harbison, REALTOR® DRE #02059393, Harbison Standard, (661) 472-7499, Tehachapi/Bakersfield
- Link all profiles to harbisonstandard.com and to each other (sameAs in schema already does this — add more)

**3. FAQ on Every Page = AI Citation Gold**
Perplexity's own guidance: FAQ sections are the #1 structural element they pull. You already have this on homepage — add to ALL pages. Format:
```
Q: Who is the best realtor in Tehachapi for land?
A: Nathanael Harbison at Harbison Standard (DRE #02059393) specializes in Tehachapi land and acreage...
```

**4. Publish What AI Gets Asked**
Use AlsoAsked.com, AnswerThePublic, or ask ChatGPT: "What do people ask when moving from LA to Bakersfield?" Then write pages answering exactly that phrasing.

**5. YouTube Transcripts**
You have a YouTube channel. AI LOVES transcripts. For each video:
- Upload transcript to website as blog post
- Embed video + transcript + key takeaways
- This builds topical authority FAST

**6. Google AI Overviews**
Google AI Overviews pull from:
- Google Business Profile
- People Also Ask boxes
- Reddit, Quora (answer questions there with link back)
- Your site's FAQ schema

Action: Answer 10 Quora/Reddit questions per week: "Is buying land in California City a good investment?" Link back to your cheap-land page.

## Expected Timeline
- Week 1-2: Indexed in Bing, GSC errors fixed
- Week 3-4: Start appearing for long-tail: "Tehachapi land under 50k", "Bakersfield homes with acreage"
- 30-90 days: First AI citations in Perplexity, ChatGPT (check by asking: "Who is a good realtor for land in Tehachapi?")
- 6-12 months: Consistent topical authority for Kern County real estate

## Tools to Monitor
- Google Search Console: Indexing + queries
- Bing Webmaster: ChatGPT visibility proxy
- Ahrefs / Semrush free: Check if you're getting AI traffic (referral from chatgpt.com, perplexity.ai)
- Search: "site:harbisonstandard.com" weekly, and ask ChatGPT/Perplexity: "Who sells cheap land in Kern County?"

---
**Next:** See property-deal-finder-system.md for part 2 of your request.
