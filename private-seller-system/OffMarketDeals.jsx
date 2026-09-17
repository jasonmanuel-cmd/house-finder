import {useEffect} from 'react';
import {Phone, ArrowRight, Check, MagnifyingGlass, Lock, HouseLine} from '@phosphor-icons/react';
import {agent} from '../data';
import {BuyerIntentForm} from '../BuyerIntentForm';

export const offMarketFaq = [
  {q: 'What are off-market deals?', a: 'Off-market deals are properties for sale that are not listed on MLS, Zillow, or Realtor.com. They include private sales, FSBO, tax-defaulted, pre-foreclosure, probate, and vacant houses. Harbison Standard finds them through county records, direct mail, driving for dollars, and private seller network.'},
  {q: 'How do you find off-market deals in Kern County?', a: 'We scrape Craigslist by owner, Zillow FSBO, Kern County tax-defaulted auction lists, Notice of Default filings, probate cases, code violations, Facebook Marketplace, wholesaler lists, and driving for dollars in Golden Hills, Bear Valley Springs, Stallion Springs, and California City. All scored 1-10 for deal quality.'},
  {q: 'Can I get alerts for off-market deals?', a: 'Yes. Create a buyer profile with your budget, area (Tehachapi, Bakersfield, California City), and type (land under $50k, flip under $250k, etc). We text you within 1 hour when a private lead matches — 21 days before Zillow.'},
  {q: 'Are off-market deals cheaper?', a: 'Often 10-30% below market. Tax-defaulted $5k-20k, pre-foreclosure 15% below, probate as-is, vacant distressed. We comp every deal: price per sqft vs 90-day comps, DOM, motivation keywords.'},
  {q: 'Do you work with investors?', a: 'Yes. 70% of off-market buyers are investors. We have private buyer network of 20+ cash buyers who want off-market not on MLS. Join by telling us your buy box.'},
];

export function OffMarketDeals(){
 useEffect(()=>{
  document.title='Off-Market Deals in Kern County — Private Listings Not on Zillow | Harbison Standard';
  const setMeta=(sel,attr,val)=>document.querySelector(sel)?.setAttribute(attr,val);
  setMeta('meta[name="description"]','content','Off-market deals in Bakersfield, Tehachapi, California City — private listings not on MLS or Zillow. Tax-defaulted, pre-foreclosure, probate, FSBO, vacant. Get alerts 21 days before Zillow. Harbison Standard Private Lead System.');
  setMeta('link[rel="canonical"]','href','https://www.harbisonstandard.com/off-market-deals');
  setMeta('meta[property="og:title"]','content','Off-Market Deals in Kern County — Private Listings Not on Zillow | Harbison Standard');
  setMeta('meta[property="og:description"]','content','Off-market deals in Kern County — private listings not on MLS or Zillow. Tax-defaulted, pre-foreclosure, probate, FSBO, vacant. Get alerts before Zillow.');
  setMeta('meta[property="og:url"]','content','https://www.harbisonstandard.com/off-market-deals');
 },[]);
 return <>
  <section className="page-heading page-wrap"><p className="eyebrow">Private Inventory — Not on Zillow</p><h1>Off-market deals in <em>Kern County.</em></h1><p className="page-lede">Private listings, tax-defaulted, pre-foreclosure, probate, and FSBO homes that never hit MLS or Zillow — found through county records, direct mail, and private seller network. Get alerts 21 days before public portals.</p><div className="hero-actions"><a className="gold" href="#buyer-form"><MagnifyingGlass/> Get Off-Market Alerts</a><a className="text-link" href="/private-sale"><span>Sell Privately</span><ArrowRight/></a></div></section>

  <section className="svc"><div className="svc-head"><div><p className="eyebrow">Where we find deals no one knows</p><h2>How we find <em>private inventory.</em></h2></div><p>95% of agents fight over 5% of homes on MLS. We hunt the other 95% — homeowners who want to sell quietly without MLS.</p></div><div className="cards4">{[
   ['Craigslist By Owner','FSBO sellers in Bakersfield/Tehachapi who post on Craigslist to avoid MLS fees. Scraped hourly via RSS.'],
   ['Zillow FSBO','For Sale By Owner on Zillow — often underpriced, open to owner financing and private sale.'],
   ['Tax-Defaulted Auction','Kern County Treasurer list — 300+ parcels 5+ years unpaid taxes, $5k-20k min bids. Contact owner BEFORE auction.'],
   ['Pre-Foreclosure NOD','Notice of Default filed last 90 days — homeowner 90 days to sell before auction, wants private sale.'],
   ['Probate / Inherited','Probate cases last 90 days — heir out-of-state, house vacant full of stuff, wants as-is cash sale.'],
   ['Vacant / Code Violation','Bakersfield code enforcement + driving for dollars in Golden Hills, Bear Valley, Oildale — overgrown, boarded, distressed.'],
   ['Facebook Marketplace + Groups','60% of cheap land in California City sold via Facebook, not MLS. Daily manual check + private groups.'],
   ['Wholesaler Network','10 wholesalers in Bakersfield send off-market deals at 70% ARV — free to join buyers list.'],
  ].map(([title,copy])=><article className="card-t" key={title}><h3>{title}</h3><p>{copy}</p></article>)}</div></section>

  <section className="svc svc--tint"><div className="svc-split"><div><p className="eyebrow">How you get them first</p><h2>Get alerts <em>before Zillow.</em></h2><p className="svc-body">Our scraper scores every lead 1-10 for deal quality. 7+ = call immediately. You get text within 1 hour when private lead matches your buy box — 21 days before it hits Zillow via CRMLS Coming Soon syndication.</p></div><ul className="check-grid">{[
   'Create buyer profile: budget, area, type (land under $50k, flip under $250k)',
   'We scrape free sources hourly + check county records weekly',
   'Scoring: as-is +3, private sale +4, no MLS +4, estate/probate +3, tax-defaulted +4',
   'Hot 7+ leads = text you immediately with address, price, motivation, link',
   'You walk property privately with Nathanael — no bidding war',
   'Close in 7-30 days, as-is, you choose',
  ].map(item=><li key={item}><Check weight="bold"/><span>{item}</span></li>)}</ul></div></section>

  <section className="svc"><div className="svc-head"><div><p className="eyebrow">What good deals look like</p><h2>How we spot <em>real deals.</em></h2></div></div><div className="cards3">{[
   ['Price 15%+ Below Comps','Price per sqft vs 90-day comps same zip +/-200 sqft. If $150/sqft vs avg $200-250, dig deeper.'],
   ['Motivation Keywords','Remarks: as-is, motivated, estate, probate, trust sale, needs TLC, must sell, owner financing = deal.'],
   ['Stale = Leverage','DOM >60 Bakersfield, >90 Tehachapi land — seller tired, negotiates. DOM 0-1 priced low = multiple offers coming — act fast.'],
  ].map(([title,copy])=><article className="card-t" key={title}><h3>{title}</h3><p>{copy}</p></article>)}</div></section>

  <section className="svc svc--tint"><div className="svc-head"><div><p className="eyebrow">Private deals FAQ</p><h2>Off-market, <em>answered.</em></h2></div></div><div className="faq">{offMarketFaq.map(({q,a})=><details key={q}><summary>{q}</summary><p>{a}</p></details>)}</div></section>

  <section id="buyer-form" className="inquiry-section"><div><p className="eyebrow">Get off-market alerts before Zillow</p><h2>Build your <em>buyer profile.</em></h2><p>Tell Nathanael your budget, area, and type — land under $50k, flip under $250k, Bakersfield 3/2 under $400k, etc. We text you within 1 hour when private lead matches. No spam, only relevant deals.</p><ul className="check-grid" style={{marginTop:16}}>{['21 days before Zillow via Coming Soon','Private leads not on MLS — no bidding war','Scored 1-10 — only 7+ hot deals','Free — no mailing list, only relevant alerts'].map(item=><li key={item}><Check weight="bold"/><span>{item}</span></li>)}</ul></div><BuyerIntentForm source="off-market-deals" /></section>

  <section className="final-cta"><div><p className="eyebrow">Want to see private inventory?</p><h2>Start with your <em>buy box.</em></h2><p>Tell us what you want — we will send private deals matching it before they hit public portals.</p></div><div className="actions"><a className="gold" href="#buyer-form"><MagnifyingGlass/> Get Off-Market Alerts</a><a className="inline-link" href="/private-sale">Sell Privately <ArrowRight/></a></div></section>
 </>
}
