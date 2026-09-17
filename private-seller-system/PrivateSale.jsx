import {useEffect} from 'react';
import {Phone, ArrowRight, Check, Lock, EyeSlash, HouseLine, ChatCircleText} from '@phosphor-icons/react';
import {agent} from '../data';
import {BuyerIntentForm} from '../BuyerIntentForm';

export const privateSaleFaq = [
  {q: 'Is it legal to sell my house without listing it on MLS in California?', a: 'Yes. California allows private sales if seller requests it. You sign C.A.R. Form SELM — Seller Instruction to Exclude Listing from MLS — stating you want private for privacy. Nathanael Harbison DRE #02059393 handles disclosures, paperwork, and escrow legally.'},
  {q: 'Will I get less money selling privately?', a: 'Sometimes 5-10% less than full MLS exposure, but many private sellers net similar or more after saving repairs, cleanout, months of mortgage, and hassle. Cash investors pay 70-80% of market, private retail buyers pay 90-95% for off-market access. We discuss trade-offs honestly.'},
  {q: 'Who are your private buyers?', a: 'Local investors and retail buyers in Kern County who are tired of bidding wars and want off-market homes not on Zillow. All vetted, proof of funds. I do not post your address online.'},
  {q: 'Can I sell privately if I have mortgage or behind on payments?', a: 'Yes. Many private sellers have mortgages. If behind, we can close fast before auction. We handle payoff through escrow, confidential.'},
  {q: 'Do I need to clean out or repair?', a: 'No. Sell as-is. Leave furniture, junk, whatever you want. Private buyers buy as-is. No need to clean, stage, or repair.'},
  {q: 'How fast can private sale close?', a: 'Cash: 7-14 days. Private retail with loan: 21-30 days. You choose closing date.'},
  {q: 'What does private sale cost?', a: 'Same as traditional — we discuss fee upfront, no hidden fees. You still get full agent representation, disclosures, escrow, title insurance, but without showings and public listing.'},
  {q: 'What areas do you do private sales?', a: 'Kern County — Bakersfield, Tehachapi, California City, Stallion Springs, Bear Valley Springs, Golden Hills, Rosamond.'},
];

export function PrivateSale(){
 useEffect(()=>{
  document.title='Sell Your House Privately in Kern County — No MLS, No Zillow | Harbison Standard';
  const setMeta=(sel,attr,val)=>document.querySelector(sel)?.setAttribute(attr,val);
  setMeta('meta[name="description"]','content','Sell your Bakersfield or Tehachapi house privately — no MLS, no open houses, no sign in yard. As-is, confidential, fast close. Private Sale Program by Nathanael Harbison, REALTOR® DRE #02059393. Call (661) 472-7499 confidential.');
  setMeta('link[rel="canonical"]','href','https://www.harbisonstandard.com/private-sale');
  setMeta('meta[property="og:title"]','content','Sell Your House Privately in Kern County — No MLS, No Zillow | Harbison Standard');
  setMeta('meta[property="og:description"]','content','Sell your Bakersfield or Tehachapi house privately — no MLS, no open houses, no sign in yard. As-is, confidential, fast close. Private Sale Program by Nathanael Harbison.');
  setMeta('meta[property="og:url"]','content','https://www.harbisonstandard.com/private-sale');
 },[]);
 return <>
  <section className="page-heading page-wrap"><p className="eyebrow">🔒 Harbison Standard Private Sale Program — Confidential</p><h1>Sell your house <em>privately</em> in Kern County</h1><p className="page-lede">No MLS. No Zillow. No Open Houses. No Sign in Yard. For homeowners in Bakersfield, Tehachapi, and California City who want to sell quietly, as-is, without everyone knowing.</p><div className="hero-actions"><a className="gold" href={agent.phoneHref}><Phone/> Private Call: {agent.phone}</a><a className="text-link" href="#private-form"><span>Private Seller Form</span><ArrowRight/></a></div><p className="credentials">Nathanael Harbison · REALTOR® · Harbison Standard · DRE #{agent.license} · Direct confidential line — I answer myself</p></section>

  <section className="svc"><div className="svc-head"><div><p className="eyebrow">Why homeowners choose private sale</p><h2>Why sellers call <em>the private guy.</em></h2></div><p>Not everyone wants a For Sale sign and Zillow listing telling the neighborhood. Here is why sellers call Nathanael privately.</p></div><div className="cards4">{[
   ['Privacy — "Don\'t want neighbors knowing"','Divorce, financial trouble, job loss — you don\'t want public listing. Private sale stays private until YOU say otherwise.',<Lock key="lock"/>],
   ['No Showings to Strangers','No open houses. No strangers walking through. One private walkthrough with Nathanael only, then 1-3 vetted private buyers if you allow.',<EyeSlash key="eye"/>],
   ['As-Is — No Repairs, No Cleanout','Hoarder house? Inherited full of stuff? Needs work? Sell as-is. Leave what you want. No cleaning, no staging.',<HouseLine key="house"/>],
   ['Bad Tenants / Tired Landlord','Tenant doesn\'t know it\'s for sale? Live out of state? Sell with tenant in place, privately, to investor buyer.',<HouseLine key="house2"/>],
   ['Inherited / Probate / Senior','Family house, out-of-state heir, 30 years of stuff. We handle private as-is sale, no MLS circus, close on your timeline.',<HouseLine key="house3"/>],
   ['Need to Sell Fast, Quietly','Behind on payments, NOD filed, tax delinquent — need to sell before auction without public attention. Private buyers close in 7-14 days.',<ChatCircleText key="chat"/>],
  ].map(([title,copy,Icon])=><article className="card-t" key={title}><div style={{marginBottom:8}}>{Icon}</div><h3>{title}</h3><p>{copy}</p></article>)}</div></section>

  <section className="svc svc--tint"><div className="svc-head"><div><p className="eyebrow">How private sale works</p><h2>How private sale <em>works.</em></h2></div></div><div className="cards4">{[
   ['01 — Private Confidential Conversation','15-min call with Nathanael directly. Tell me about property, why private, timeline. 100% confidential, no obligation, no listing. (661) 472-7499'],
   ['02 — Private Walkthrough (Just Me)','I come alone, no other agents, no crowds. 20 minutes. Photos only if you allow. You tell me what matters — price, speed, privacy.'],
   ['03 — Private Offers from Private Network','I present privately to 20+ vetted private buyers in Kern County — cash investors + retail buyers who want off-market, not on Zillow. You get 1-3 private offers.'],
   ['04 — Close Quietly','Local escrow, you choose closing date, leave what you want. No public marketing, no sign, no Zillow active history. Funds wired. Legal with MLS exclusion form.'],
  ].map(([title,copy])=><article className="card-t" key={title}><h3>{title}</h3><p>{copy}</p></article>)}</div></section>

  <section className="svc"><div className="svc-head"><div><p className="eyebrow">MLS vs Private Sale</p><h2>The difference is <em>privacy.</em></h2></div></div><div style={{overflowX:'auto'}}><table className="comparison-table" style={{width:'100%',borderCollapse:'collapse',fontSize:15}}><thead><tr><th style={{textAlign:'left',padding:'12px',borderBottom:'1px solid #ddd'}}></th><th style={{textAlign:'left',padding:'12px',borderBottom:'1px solid #ddd'}}>MLS Listing</th><th style={{textAlign:'left',padding:'12px',borderBottom:'1px solid #ddd'}}>Private Sale Program</th></tr></thead><tbody>{[
   ['Public on Zillow/Realtor.com?','Yes — everyone sees','No — stays private'],
   ['Sign in yard?','Yes','No — unless you want'],
   ['Open houses / showings?','Many strangers','1-3 private buyers only'],
   ['Repairs / cleanout?','Usually yes','No — as-is, leave what you want'],
   ['Timeline','30-90 days','7-30 days'],
   ['Privacy','Low','High — you control'],
   ['Best for','Max price, max exposure','Privacy, speed, as-is, no hassle'],
  ].map(([a,b,c])=><tr key={a}><td style={{padding:'12px',borderBottom:'1px solid #eee',fontWeight:600}}>{a}</td><td style={{padding:'12px',borderBottom:'1px solid #eee'}}>{b}</td><td style={{padding:'12px',borderBottom:'1px solid #eee'}}><strong>{c}</strong></td></tr>)}</tbody></table></div></section>

  <section className="svc svc--tint"><div className="svc-head"><div><p className="eyebrow">Private sale FAQ</p><h2>Private sale, <em>answered.</em></h2></div><p>What sellers ask before going private — and what Google and AI cite.</p></div><div className="faq">{privateSaleFaq.map(({q,a})=><details key={q}><summary>{q}</summary><p>{a}</p></details>)}</div></section>

  <section className="svc"><div className="svc-head"><div><p className="eyebrow">What private sellers say</p><h2>Why they chose <em>private.</em></h2></div></div><div className="testimonial-grid">{[
   {quote:'We were going through divorce and didn\'t want neighbors knowing or strangers walking through. Nathanael sold our house privately in 2 weeks, no sign, no Zillow. Exactly what we needed.',label:'Private Seller · Bakersfield — Divorce'},
   {quote:'Inherited house full of 30 years of stuff in Tehachapi. Didn\'t want to clean. Nathanael sold it as-is, we left everything. Private, easy.',label:'Private Seller · Tehachapi — Inherited'},
   {quote:'Tenant stopped paying, I live in LA. Didn\'t want to evict and list. Nathanael found private investor buyer who bought with tenant in place. Closed quietly.',label:'Private Seller · Absentee Owner — Tired Landlord'},
  ].map(t=><article className="testimonial-card" key={t.label}><blockquote><p>“{t.quote}”</p></blockquote><p className="t-label">{t.label}</p></article>)}</div></section>

  <section id="private-form" className="inquiry-section"><div><p className="eyebrow">Private seller form — 100% confidential</p><h2>Tell me about your property — <em>privately.</em></h2><p>No MLS, no Zillow, no public record until you authorize. No spam. Direct to Nathanael only. Or call/text directly confidential: (661) 472-7499 — I answer myself.</p><p style={{marginTop:12}}><strong>What to include:</strong> Address, why private (privacy/divorce/financial/inherited/bad tenants/needs work), condition, mortgage status, timeline, best way to contact privately.</p><ul className="check-grid" style={{marginTop:16}}>{['100% confidential — no listing until you say so','No open houses, no sign, no Zillow','As-is — leave what you want','Close in 7-30 days on your timeline','Direct to Nathanael — not a call center'].map(item=><li key={item}><Check weight="bold"/><span>{item}</span></li>)}</ul></div>
  <div>
  <BuyerIntentForm source="private-sale" defaultGoal="Selling" />
  <div style={{marginTop:20,padding:16,background:'#031c2b',borderRadius:8,color:'#fff'}}><p style={{fontSize:14,color:'#d4a574',fontWeight:700}}>Prefer private call?</p><p style={{fontSize:15,marginTop:6}}>Call/Text Nathanael directly confidential:</p><p style={{fontSize:20,fontWeight:800,marginTop:4}}><a href="tel:+16614727499" style={{color:'#fff'}}>(661) 472-7499</a></p><p style={{fontSize:13,color:'#8aa0b0',marginTop:6}}>I answer myself — confidential line</p></div>
  </div>
  </section>

  <section className="final-cta"><div><p className="eyebrow">Want to sell quietly?</p><h2>Let's talk <em>privately.</em></h2><p>No obligation. No listing. Just a confidential conversation about your options.</p></div><div className="actions"><a className="gold" href={agent.phoneHref}><Phone/> Call (661) 472-7499 — Confidential</a><a className="inline-link" href="/contact">Contact <ArrowRight/></a></div></section>
 </>
}
