# DEV PLAYBOOK — Harbison Standard Fix-All
**For Developer:** https://www.harbisonstandard.com/ — Vercel + Static JS site
**Owner:** Nathanael Harbison | Goal: Rank on Google + Get Cited by ChatGPT/Perplexity/Gemini + Auto Property Feeds

---

## EXECUTIVE SUMMARY — WHAT'S BROKEN
- Site has good foundation (fast, schema, sitemap) but only 20 URLs indexed, 2 manual listings
- `site:harbisonstandard.com` = 0 results in Google = not indexed properly
- No llms.txt, no AI bot allowances, no Bing Webmaster verification = invisible to ChatGPT/Perplexity
- No IDX feed = no fresh content, no ranking for "Bakersfield homes for sale" etc.
- Thin content (300 words/page) = can't compete
- No GBP integration, no review schema, no location pages

---

## PHASE 1: TECHNICAL SEO — 1 DAY (P0 - CRITICAL)

### 1.1 Upload llms.txt and Fix robots.txt
**Files provided in workspace:** `llms.txt`

**Tasks:**
1. Add file `/public/llms.txt` (copy from workspace root llms.txt)
2. Update `/public/robots.txt` to:

```
User-agent: *
Allow: /
Disallow: /api/
Allow: /api/properties
Disallow: /hq

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

Sitemap: https://www.harbisonstandard.com/sitemap.xml
Sitemap: https://www.harbisonstandard.com/sitemap-images.xml
```

3. Verify at https://www.harbisonstandard.com/llms.txt and /robots.txt returns 200

**Acceptance:** curl -I https://www.harbisonstandard.com/llms.txt = 200, contains "Harbison Standard"

### 1.2 Sitemap Fixes
**Current sitemap.xml has no lastmod, no priority. Fix:**

Generate sitemap dynamically in build step. Example for Vercel (in `scripts/generate-sitemap.js`):

```js
const urls = [
  { loc: '/', lastmod: new Date().toISOString(), changefreq: 'daily', priority: '1.0' },
  { loc: '/properties', lastmod: new Date().toISOString(), changefreq: 'hourly', priority: '0.9' },
  { loc: '/about', changefreq: 'monthly', priority: '0.7' },
  // ... all static pages
  // Dynamically add /property/[slug] from inventory JSON
];
```

Add image sitemap entries with `<image:image>` for each property photo — you already have sitemap-images.xml, ensure it updates.

### 1.3 Add Missing Meta & Performance
- Add `<meta name="google-site-verification" content="...">` and `<meta name="msvalidate.01" content="...">` (get from GSC + Bing)
- Add preload for hero image (already done) + lazy load for property gallery
- Add `alt` attributes: Currently images have generic alt. Change to: `alt="22208 Mariposa Rd Tehachapi CA 0.3 acre lot $40k - view of lot with mountains"`
- Add width/height to images to prevent CLS
- Ensure canonical is absolute: `https://www.harbisonstandard.com/...` (already good)
- Add `lastmod` to pages via JSON-LD WebPage schema

### 1.4 Schema Enhancements (Already Good — Enhance)
You have RealEstateAgent, Organization, FAQPage. Add:

**On /properties page:**
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Current Listings in Kern County",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "RealEstateListing",
        "name": "22208 Mariposa Rd, Tehachapi CA 93561",
        "offers": { "@type": "Offer", "price": "40000", "priceCurrency": "USD" },
        "address": { "@type": "PostalAddress", "streetAddress": "22208 Mariposa Rd", "addressLocality": "Tehachapi", "addressRegion": "CA", "postalCode": "93561" }
      }
    }
  ]
}
```

**On each property page:**
Add `SingleFamilyResidence` or `Landform` + `Offer` + `BreadcrumbList`

**On homepage:**
Add `AggregateRating` once you have 5+ Google reviews:
```json
"aggregateRating": { "@type": "AggregateRating", "ratingValue": "5.0", "reviewCount": "12" }
```

---

## PHASE 2: INDEXING — 1 DAY (P0)

### 2.1 Google Search Console + Bing Webmaster
1. Add site to https://search.google.com/search-console — verify via DNS or meta tag
2. Submit sitemap.xml and sitemap-images.xml
3. Check Coverage > Pages — fix any "Crawled - not indexed" by adding internal links
4. Add site to https://www.bing.com/webmasters — CRITICAL for ChatGPT (ChatGPT uses Bing index)
5. Submit same sitemaps to Bing
6. Enable Bing Webmaster > URL Inspection > Request indexing for homepage + /properties + top 5 pages

### 2.2 Internal Linking
Currently footer links only. Add:
- In homepage, link to /cheap-land-kern-county, /bakersfield-home-prices, /why-tehachapi with keyword-rich anchor: "cheap land in Kern County" not "Explore land"
- On each property page, add "Similar properties in Tehachapi" section linking to 3 other properties + link to /properties?city=Tehachapi
- Add breadcrumbs: Home > Properties > 22208 Mariposa Rd

---

## PHASE 3: CONTENT EXPANSION — 3 DAYS (P1 - HIGH)

### 3.1 Create Location + Intent Pages (Template Provided)
You have 5 resource pages. Need 20 more. Use this template for each:

**File structure:** `/src/pages/[slug].astro` or similar — replicate existing design

**Each page must have:**
- H1: Keyword + Location: "Tehachapi Land for Sale Under $50K | Harbison Standard"
- Intro 150 words: What page is about, who it's for
- H2s phrased as questions (for AI citation):
  - "What does $50K buy in Tehachapi?"
  - "What should I check before buying cheap land in Kern County?"
  - "Is owner financing available?"
- 800-1200 words total, include bullet lists, budget breakdowns
- FAQ section at bottom (3-5 Q&A) + JSON-LD FAQPage schema
- CTA: Buyer profile form + Call button
- Internal links: 3+ to /properties and other guides

**Pages to create (priority order):**
1. `/tehachapi-land-under-50k`
2. `/tehachapi-homes-with-acreage`
3. `/bakersfield-homes-under-400k`
4. `/california-city-cheap-land`
5. `/stallion-springs-homes-for-sale`
6. `/bear-valley-springs-real-estate`
7. `/sell-home-as-is-kern-county`
8. `/inherited-house-bakersfield`
9. `/owner-financing-land-tehachapi`
10. `/bakersfield-homes-with-shop`
11. `/kern-county-investment-properties`
12. `/moving-from-la-to-bakersfield` (enhance existing, add cost table)
13. `/tehachapi-vs-bakersfield`
14. `/cheap-land-california-city-vs-tehachapi`
15. Blog: `/blog/kern-county-market-update-[month-year]` — template that pulls from data

**For dev:** Create markdown-driven pages: `/content/guides/*.md` with frontmatter (title, description, faqs) and render via Astro.

### 3.2 Add Blog / Market Update System
- Create `/blog` index page
- Create dynamic route `/blog/[slug]`
- Each post needs Article schema: author Nathanael Harbison, datePublished, dateModified, sameAs links
- First 5 posts:
  - "Kern County Market Update — September 2026"
  - "What $40K Buys in Tehachapi Right Now"
  - "How to Check Utilities Before Buying Land in Kern County"
  - "Bakersfield Neighborhoods: Seven Oaks vs Stockdale vs Southwest"
  - "Owner Financing vs Cash: Land in Tehachapi"

---

## PHASE 4: AI VISIBILITY — 1 DAY (P1)

### 4.1 llms.txt Already Done (Phase 1)
Verify it serves with `Content-Type: text/plain` or `text/markdown`

### 4.2 Add /.well-known/ai.txt (Optional but future-proof)
```
# AI Usage
User-agent: *
Allow: /

# Contact for licensing
Contact: nate85.realtor@gmail.com
```

### 4.3 Structured Data for AI
- Add `author` to all Article pages: 
```json
"author": { "@type": "Person", "name": "Nathanael Harbison", "url": "https://www.harbisonstandard.com/about", "sameAs": [...] }
```
- Add `speakable` schema to FAQ sections for voice search
- Ensure all pages have `inLanguage: en-US`

### 4.4 GBP Integration
- Embed Google Maps on contact page with place_id
- Add "Review us on Google" link: `https://search.google.com/local/writereview?placeid=YOUR_PLACE_ID`
- Add review schema once you have reviews

---

## PHASE 5: IDX INTEGRATION — 2 DAYS (P0 FOR LEAD GEN)

### Current Problem: Manual inventory JSON at `hs-inventory-data`
You have `<script id="hs-inventory-data">` with 2 properties. Need live feed.

### Solution A (Recommended, Low Dev): Showcase IDX
1. Client signs up at showcaseidx.com, connects CRMLS credentials (broker must approve)
2. Showcase provides WordPress plugin, but you are on Vercel static. Options:
   - **Option A1 (Easiest):** Create subdomain `search.harbisonstandard.com` running WordPress + Showcase IDX template, link from main site nav "Search MLS"
   - **Option A2 (JS Widget):** Showcase provides `<div id="showcase-idx"></div><script src="...">` — embed on `/properties` page
   - **Option A3 (API):** Use Showcase API to pull listings into your existing inventory JSON format, regenerate daily via Vercel Cron

**For Option A3, create Vercel Cron:**
`vercel.json`:
```json
{
  "crons": [{ "path": "/api/cron/sync-idx", "schedule": "0 * * * *" }]
}
```
`/api/cron/sync-idx.js` fetches from Showcase API, writes to `/public/api/properties.json`, updates sitemap.

### Solution B: IDX Broker
Similar, provides `$50/mo` feed, gives you `https://idx.harbisonstandard.com` wrapper.

### Result After IDX:
- /properties shows 1000+ live listings, not 2
- Auto-create pages: /properties/just-listed, /coming-soon, /price-reduced, /tehachapi, /bakersfield
- Each listing page becomes indexable: /mls/CRMLS-12345
- Sitemap grows from 20 to 2000 URLs = massive SEO boost

**Acceptance:** /properties shows "Coming Soon" filter, updates hourly without manual deploy

---

## PHASE 6: CONVERSION & TRACKING

### 6.1 Forms
- Currently using Formspree. Add hidden fields: `page_url`, `utm_source`, `property_interest`
- Add conversion tracking: `gtag('event', 'generate_lead', { property: slug })` on form submit
- Add call tracking: Use CallRail or simple `tel:` click event

### 6.2 Analytics
- Add Google Analytics 4 + Google Tag Manager
- Track events: property_view, inquiry_submit, call_click, text_click
- Add Bing Clarity (free heatmaps)

### 6.3 Speed
- Run Lighthouse, aim for 90+ on all
- Compress images: Convert /assets/property/*.jpg to WebP + AVIF, serve responsive srcset
- Add CDN caching headers for /assets/* (Vercel does automatically, but verify)

---

## DELIVERABLES CHECKLIST FOR DEV

- [ ] /public/llms.txt live and returns 200
- [ ] /public/robots.txt updated with AI bots allowed
- [ ] Sitemap has lastmod, priority, image tags, updates dynamically
- [ ] GSC + Bing Webmaster verified, sitemaps submitted
- [ ] Alt text on all images, width/height set
- [ ] 15 new location/intent pages live, each with FAQ schema + 800+ words
- [ ] /blog system live with 5 posts + Article schema
- [ ] ItemList + RealEstateListing schema on /properties
- [ ] IDX integration live — /properties shows 100+ live listings, Coming Soon filter works
- [ ] Internal linking + breadcrumbs added
- [ ] GA4 + Clarity + conversion tracking
- [ ] Lighthouse 90+ mobile/desktop

## ESTIMATED TIME
- Phase 1+2: 1 day
- Phase 3: 2-3 days (content can be written by AI + edited by Nathanael)
- Phase 4: 0.5 day
- Phase 5: 1-2 days depending on IDX option
- Total: 5-7 dev days

## AFTER DEV DONE — OWNER TASKS
- Get 10 Google reviews
- Post weekly GBP post + weekly blog market update
- Create profiles on Expertise.com, ThreeBestRated, Yelp
- Start answering Quora/Reddit

---
Questions? Reference files: harbison-seo-ai-plan.md, llms.txt
