"""
Harbison Standard Branded Dashboard — Private Lead Scraper
Matches main site: navy #031c2b, gold #edc66f, fonts Libre Caslon Display + Open Sans
Run: python app.py
Render: Uses PORT env var
"""
from flask import Flask, render_template_string, request, jsonify, redirect, session, Response
import secrets
import threading
from copy import deepcopy
from contextlib import closing
import sys, os
sys.path.append(os.path.dirname(__file__))
from database import get_leads, get_stats, get_conn, init_db, get_recent_scrapes, load_last_run_summary
from datetime import datetime
from uuid import uuid4
from urllib.parse import urlsplit


def safe_url(value):
    """Only absolute HTTP(S) links, including for previously stored leads."""
    if not value or any(ord(c) < 33 for c in value) or '\\' in value:
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ('http', 'https') and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False

app = Flask(__name__)
_app_secret = os.environ.get("SECRET_KEY", "").strip()
app.config.update(
    SECRET_KEY=_app_secret or secrets.token_urlsafe(48),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=bool(os.environ.get('RENDER')),
    MAX_CONTENT_LENGTH=1024 * 1024,
)


@app.before_request
def prepare_database():
    token = os.environ.get('DASHBOARD_TOKEN', '')
    if os.environ.get('RENDER') and not token:
        return jsonify(error='Dashboard disabled: configure DASHBOARD_TOKEN'), 503
    if token:
        auth = request.authorization
        if not auth or auth.type != 'basic' or not secrets.compare_digest((auth.password or '').encode(), token.encode()):
            return Response('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Private dashboard"'})
    elif urlsplit(request.host_url).hostname not in ('localhost', '127.0.0.1', '::1'):
        return jsonify(error='Local access only without DASHBOARD_TOKEN'), 403
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        expected = urlsplit(request.host_url)
        supplied = urlsplit(origin or referer or request.host_url)
        if request.headers.get('Sec-Fetch-Site') == 'cross-site' or (supplied.scheme, supplied.netloc) != (expected.scheme, expected.netloc):
            return jsonify(error='Cross-origin request rejected'), 403
        csrf = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
        if not csrf or not secrets.compare_digest(csrf.encode(), session.get('csrf_token', '').encode()):
            return jsonify(error='Invalid CSRF token; refresh the dashboard'), 403
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    init_db()


@app.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Private Lead Dashboard — Harbison Standard</title>
<meta name="description" content="Kern County private leads — off-market deals not on MLS. Harbison Standard Private Lead System">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Libre+Caslon+Display&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
@import url('https://www.harbisonstandard.com/assets/fonts.css');
:root{--navy:#031c2b;--gold:#edc66f;--muted-gold:#b78b43;--light:#f6f5ef;--border:#e3ddcf}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Open Sans',sans-serif;background:var(--light);color:#08142e;line-height:1.5;-webkit-font-smoothing:antialiased}
h1,h2,h3,.motto{font-family:'Libre Caslon Display',Georgia,serif;font-weight:400}
a{color:inherit;text-decoration:none}
header{height:92px;background:var(--navy);display:flex;align-items:center;padding:0 4%;gap:5%;color:white;position:sticky;top:0;z-index:10}
.brand{width:250px;flex-shrink:0}
.brand img{display:block;width:100%}
nav{display:flex;align-items:center;gap:27px;margin-left:auto}
nav a{font-size:10px;white-space:nowrap;text-transform:uppercase;letter-spacing:.4px;font-weight:600;color:white;padding:14px 0;position:relative}
nav a.active{color:var(--gold)}
nav a.active:after{content:'';position:absolute;bottom:3px;left:0;right:0;border-bottom:2px solid var(--gold)}
.gold{display:inline-flex;align-items:center;justify-content:center;gap:10px;background:var(--gold);color:#07131c;min-height:42px;min-width:176px;padding:11px 22px;border-radius:2px;font-weight:700;font-size:12px;letter-spacing:1px;text-transform:uppercase;box-shadow:inset 0 0 18px #ffeba65c;border:0;cursor:pointer}
.gold:hover{filter:brightness(1.05)}
.text-link{display:inline-flex;align-items:center;gap:8px;background:none;padding:0;color:var(--navy);text-transform:uppercase;font-size:11px;font-weight:700;letter-spacing:1px;border:0;cursor:pointer}
.text-link span{border-bottom:1px solid #d9d6cb;padding-bottom:2px}
.container{max-width:1180px;margin:0 auto;padding:0 4%}
.page-heading{padding:38px 0 18px}
.eyebrow{text-transform:uppercase;font-size:11px;font-weight:700;letter-spacing:1.8px;color:#986f31;margin-bottom:8px}
.page-heading h1{font-size:54px;line-height:.95;letter-spacing:-1.2px;color:var(--navy)}
.page-heading h1 em{font-family:'Libre Caslon Text',Georgia,serif;color:var(--muted-gold);font-style:italic;font-size:.88em}
.page-lede{font-size:16px;line-height:1.5;max-width:720px;margin-top:14px;color:#4b585d}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0}
.stat{background:var(--navy);color:#fff;border-radius:4px;padding:20px 22px;border-bottom:3px solid var(--gold)}
.stat span{font-family:'Libre Caslon Display',Georgia,serif;font-size:32px;color:var(--gold);display:block;line-height:1}
.stat p{margin:6px 0 0;font-size:10px;letter-spacing:1.4px;text-transform:uppercase;color:#cfd8dd}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 22px}
.filters a{padding:8px 14px;background:#fff;border:1px solid var(--border);border-radius:3px;font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#596365}
.filters a.active{background:var(--navy);color:var(--gold);border-color:var(--navy)}
.card{background:#fff;border:1px solid var(--border);border-radius:4px;padding:20px 22px;margin-bottom:14px;transition:.2s;position:relative}
.card:hover{border-color:var(--muted-gold);box-shadow:0 10px 30px -20px rgba(3,28,43,.3)}
.card.hot{border-left:4px solid #c53030}
.card.warm{border-left:4px solid var(--gold)}
.card.cold{border-left:4px solid #cbd5e0}
.price{font-family:'Libre Caslon Display',Georgia,serif;font-size:26px;color:var(--navy);line-height:1}
.price em{color:var(--muted-gold);font-style:normal;font-size:20px}
.meta{font-size:11px;color:#7c8590;letter-spacing:.3px;margin-top:6px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.badge{display:inline-block;padding:3px 8px;border-radius:3px;font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase}
.badge-hot{background:#f3e4bf;color:#7a5c14;border:1px solid #d6b268}
.badge-warm{background:#fbfaf5;color:#5a4f3a;border:1px solid var(--border)}
.badge-source{background:var(--navy);color:var(--gold);border:1px solid var(--navy)}
.title{font-family:Georgia,serif;font-size:18px;font-weight:700;color:var(--navy);margin:8px 0 4px}
.desc{font-size:13px;line-height:1.6;color:#4b585d;margin-top:8px}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:2px;font-size:11px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;border:1px solid var(--border);background:#fff;color:#596365;cursor:pointer}
.btn-gold{background:var(--gold);color:#07131c;border-color:var(--gold);box-shadow:inset 0 0 12px #ffeba65c}
.btn-dark{background:var(--navy);color:var(--gold);border-color:var(--navy)}
.form-wrap{background:#fff;border:1px solid var(--border);border-radius:6px;padding:28px;margin-top:30px}
.form-wrap h3{font-size:24px;color:var(--navy);margin-bottom:6px}
.form-wrap p.small{font-size:12px;color:#7c8590;line-height:1.5;margin-bottom:14px}
.input{width:100%;padding:10px 12px;border-radius:3px;border:1px solid #c9c0ab;font-size:13px;margin-bottom:10px;font-family:inherit;background:#fff;color:#08142e}
.input:focus{outline:2px solid var(--gold);outline-offset:2px;border-color:transparent}
label{font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#7c8590;margin-bottom:4px;display:block}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.closing{margin-top:40px;background:var(--navy) url('https://www.harbisonstandard.com/assets/mountains.webp') center/cover no-repeat;padding:45px 7.8% 28px 6.1%;display:flex;justify-content:space-between;align-items:center;color:white;border-radius:4px}
.footer-logo{width:240px;display:block}
.closing .motto{font-size:28px;line-height:1.02;font-style:italic}
.closing .motto em{font-size:1em}
.site-footer{margin-top:18px;background:var(--navy);color:white;display:flex;align-items:center;justify-content:space-between;padding:18px 3.8%;border-top:1px solid #9f8038;border-radius:4px}
.site-footer p{text-transform:uppercase;letter-spacing:1px;font-size:8px}
@media(max-width:900px){.stats{grid-template-columns:repeat(2,1fr)}.page-heading h1{font-size:42px}header{height:80px}.brand{width:200px}nav{display:none}.row{grid-template-columns:1fr}.closing{flex-direction:column;align-items:flex-start;gap:20px}}
@media(max-width:480px){.filters{flex-direction:column}.stats{grid-template-columns:1fr}.page-heading h1{font-size:34px}.page-lede{font-size:14px}.form-wrap{padding:20px}.closing{padding:30px 6.1% 20px 6.1%}}
</style>
</head>
<body>
<header>
<a class="brand" href="https://www.harbisonstandard.com/" aria-label="Harbison Standard home"><img src="https://www.harbisonstandard.com/assets/logo.webp" alt="Harbison Standard — Real Estate and Investing"></a>
<nav aria-label="Main navigation">
<a href="https://www.harbisonstandard.com/">Home</a>
<a href="https://www.harbisonstandard.com/properties">Properties</a>
<a href="https://www.harbisonstandard.com/private-sale" class="active">Private Sale</a>
<a href="https://www.harbisonstandard.com/off-market-deals" class="active">Off-Market Deals</a>
<a href="https://www.harbisonstandard.com/contact">Contact</a>
</nav>
<a class="gold" href="https://www.harbisonstandard.com/contact" style="margin-left:auto">Let's talk</a>
</header>

<div class="container">
<section class="page-heading">
<p class="eyebrow">Harbison Standard — Private Lead System — {{stats.total}} leads</p>
<h1>Private leads <em>no one knows how to find.</em></h1>
<p class="page-lede">Off-market deals in Kern County — tax-defaulted, pre-foreclosure, probate, FSBO, vacant, Facebook, wholesaler — scored 1-10 for deal quality. Same system Nathanael uses to find private sellers who want to sell quietly without MLS.</p>
<div style="display:flex;gap:12px;margin-top:18px;flex-wrap:wrap">
<form method="POST" action="/run" id="run-form" style="display:inline"><input type="hidden" name="csrf_token" value="{{session['csrf_token']}}"><button type="submit" class="gold" {% if run_status.running %}disabled{% endif %}>{{ 'Checking sources…' if run_status.running else '▶ Run Scraper Now' }}</button></form>
{% if run_status.running %}<p role="status">Source check running. Refresh this page to see updated results.</p>{% endif %}
<a class="text-link" href="/export"><span>⬇ Export CSV</span></a>
<a class="text-link" href="https://www.harbisonstandard.com/private-sale"><span>Private Sale Program →</span></a>
</div>
</section>

<div class="stats">
<div class="stat"><span>{{stats.total}}</span><p>Total Leads</p></div>
<div class="stat"><span>{{stats.hot}}</span><p>Hot 7+ Score</p></div>
<div class="stat"><span>{{stats.warm}}</span><p>Warm 5+ Score</p></div>
<div class="stat"><span>{{stats.by_source.get('craigslist',0) + stats.by_source.get('facebook',0)}}</span><p>FSBO + Private</p></div>
</div>

<div class="filters">
<a href="/?min_score=0" class="{{'active' if min_score==0 else ''}}">All ({{stats.total}})</a>
<a href="/?min_score=7" class="{{'active' if min_score==7 else ''}}">🔥 Hot 7+ ({{stats.hot}})</a>
<a href="/?min_score=5" class="{{'active' if min_score==5 else ''}}">Warm 5+ ({{stats.warm}})</a>
<a href="/?city=Tehachapi" class="{{'active' if city_filter=='Tehachapi' else ''}}">Tehachapi</a>
<a href="/?city=Bakersfield" class="{{'active' if city_filter=='Bakersfield' else ''}}">Bakersfield</a>
<a href="/?city=California%20City" class="{{'active' if city_filter=='California City' else ''}}">California City</a>
<a href="/?source=craigslist" class="{{'active' if source_filter=='craigslist' else ''}}">Craigslist</a>
<a href="/?source=newspaper_auction" class="{{'active' if source_filter=='newspaper_auction' else ''}}">Auction Notices</a>
<a href="/?source=kern_tax" class="{{'active' if source_filter=='kern_tax' else ''}}">Tax-Defaulted</a>
<a href="/?source=kern_recorder" class="{{'active' if source_filter=='kern_recorder' else ''}}">Pre-Foreclosure</a>
</div>
{% if run_status.recent_logs %}
<section class="recent-run" id="run-status" style="margin-top:24px">
  <h2 class="eyebrow">Recent source runs</h2>
  <p class="page-lede" style="margin:6px 0 14px">Most recent source outcomes are listed below. A source page, brochure, or auction portal is research material, not a lead. Scores are heuristics for research priority, not valuations.</p>
  {% for log in run_status.recent_logs %}
  <article class="card {{ 'hot' if log.status == 'blocked' else 'warm' if log.status == 'manual_only' else 'cold' }}">
    <div class="meta"><span class="badge badge-source">{{ log.source }}</span><span>{{ log.status }}</span><span>{{ log.created_at[:16] }}</span></div>
    <div class="desc">Found {{ log.found }} | New {{ log.new_leads }}</div>
    {% if log.error %}<p style="font-size:12px;color:#7c8590;margin-top:4px">{{ log.error }}</p>{% endif %}
  </article>
  {% endfor %}
</section>
{% endif %}

{% for lead in leads %}
<article class="card {{'hot' if lead['deal_score']>=7 else 'warm' if lead['deal_score']>=5 else 'cold'}}">
<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap">
<div>
<div class="price">{{lead['price_text'] or 'Private Price'}} <em>| Score {{lead['deal_score']}}/10</em> <span class="badge {{'badge-hot' if lead['deal_score']>=7 else 'badge-warm'}}" style="margin-left:8px">{{'HOT' if lead['deal_score']>=7 else 'WARM' if lead['deal_score']>=5 else 'COLD'}}</span></div>
<div class="title">{{lead['address']}} — {{lead['city']}}</div>
<div class="meta"><span class="badge badge-source">{{lead['source']}}</span><span>{{lead['motivation']}}</span><span>{{lead['created_at'][:16]}}</span><span>Status: {{lead['status']}}</span><span>Type: {{lead['source_type']}}</span></div>
</div>
</div>
<div class="desc">{{lead['description'][:600]}}</div>
<div class="actions">
{% if safe_url(lead['link']) %}<a class="btn btn-gold" href="{{lead['link']}}" target="_blank" rel="noopener noreferrer">View Original →</a>{% endif %}
<a class="btn" href="https://assessor.kerncounty.com/parcel-search/" target="_blank" rel="noopener noreferrer">Assessor Lookup</a>
<button class="btn btn-dark contact-button" type="button" data-lead-id="{{lead['id']}}">Mark Contacted</button>
<span class="contact-error" role="alert"></span>
</div>
</article>
{% endfor %}

{% if not leads %}
<article class="card"><p style="font-size:14px">No leads match filter. Click "Run Scraper Now" or check filters. Add manual leads from Facebook Marketplace below.</p></article>
{% endif %}

<div class="form-wrap">
<h3>Add manual private lead</h3>
<p class="small">Found a lead on Facebook Marketplace, driving for dollars, wholesaler email, or referral? Add it here — it will be scored automatically 1-10 using same system (private sale, as-is, estate, tax-defaulted keywords).</p>
<form method="POST" action="/add">
<input type="hidden" name="csrf_token" value="{{session['csrf_token']}}">
<div class="row"><div><label>Address *</label><input class="input" name="address" required placeholder="123 Main St, Bakersfield"></div><div><label>City *</label><input class="input" name="city" required placeholder="Bakersfield"></div></div>
<div class="row"><div><label>Price</label><input class="input" name="price" type="number" placeholder="150000"></div><div><label>Source *</label><select class="input" name="source"><option value="facebook">Facebook Marketplace/Group</option><option value="driving">Driving for Dollars</option><option value="referral">Referral ($500)</option><option value="wholesaler">Wholesaler</option><option value="zillow_fsbo">Zillow FSBO</option><option value="craigslist">Craigslist</option><option value="other">Other</option></select></div></div>
<label>Link (Facebook post, Zillow link, etc)</label><input class="input" name="link" placeholder="https://...">
<label>Description / Why private? *</label><textarea class="input" name="description" rows="3" required placeholder="e.g., Divorce, inherited, as-is, needs work, owner in LA, wants private sale, no MLS, owner financing..."></textarea>
<button type="submit" class="gold" style="width:100%;margin-top:8px">Add Lead & Score →</button>
</form>

<div style="margin-top:14px;padding:12px 14px;background:#fff;border:1px solid var(--border);border-left:4px solid var(--gold);border-radius:4px">
<p style="font-size:12px;color:#4b585d;line-height:1.6;margin:0"><strong>Zillow note:</strong> zillow.com blocks automated scraping (403). Zillow FSBO listings are a manual research resource, not leads in this dashboard — open the link, filter Price Max $250k, sort Newest, look for as-is / motivated / estate / owner financing, and add promising owners via the form below.</p>
</div>

<div style="margin-top:28px;padding:24px;background:#fff;border:1px solid var(--border);border-radius:6px">
<h3 style="font-size:22px;color:var(--navy);margin-bottom:8px">Manual research resources</h3>
<p style="font-size:13px;color:#4b585d;line-height:1.6">These are research materials and starting points, not deal listings and not a valuation. Confirm every detail with the owner, listing, and county records before outreach.</p>
<ol style="margin:16px 0 0 18px;font-size:13px;line-height:1.7;color:#4b585d">
<li><strong>Zillow FSBO:</strong> zillow.com — browse Bakersfield/Tehachapi/California City FSBO listings, filter Price Max $250k, sort Newest. Add promising owners manually via the form below.</li>
<li><strong>Facebook Marketplace:</strong> facebook.com/marketplace — search "Tehachapi land", "Bakersfield house for sale by owner" + local groups → Add via form → auto-scored.</li>
<li><strong>County records:</strong> Kern Tax-Defaulted (kcttc.co.kern.ca.us), Recorder NOD (recorder.kerncounty.com), Court Probate (kern.courts.ca.gov) → Add manually.</li>
<li><strong>Driving for dollars:</strong> Golden Hills, Bear Valley, Oildale — overgrown, boarded, tarp roof → Add via form → Assessor lookup free.</li>
</ol>
<p style="margin-top:14px;font-size:12px;color:#7c8590">All leads saved in data/leads.db (SQLite). Export CSV anytime.</p>
</div>

<div class="closing"><a href="https://www.harbisonstandard.com/" aria-label="Harbison Standard home"><img class="footer-logo" src="https://www.harbisonstandard.com/assets/logo.webp" alt="Harbison Standard"></a><div><p class="motto">It's not what you do,<br><em>it's how you do it.</em></p><a class="gold" href="https://www.harbisonstandard.com/contact">Let's talk</a></div></div>
<div class="site-footer"><div><p>Bakersfield · Tehachapi · Kern County</p><p>Nathanael Harbison · REALTOR® · Harbison Standard · DRE #02059393</p><p>Private Lead System — No MLS, No Zillow, Private Sellers Only</p></div><div style="display:flex;gap:12px;font-size:10px"><a href="https://www.harbisonstandard.com/private-sale">Private Sale</a><a href="https://www.harbisonstandard.com/off-market-deals">Off-Market Deals</a></div></div>

</div>
<script>
const csrfToken = {{session['csrf_token']|tojson}};
async function markContacted(button){
  const error = button.parentElement.querySelector('.contact-error');
  error.textContent = '';
  button.disabled = true;
  try {
    const response = await fetch('/mark_contacted/'+encodeURIComponent(button.dataset.leadId), {method:'POST', headers:{'X-CSRF-Token':csrfToken}});
    if (!response.ok) throw new Error('Could not update lead (HTTP '+response.status+'). Refresh and try again.');
    location.reload();
  } catch (err) { error.textContent = err.message; button.disabled = false; }
}
document.querySelectorAll('.contact-button').forEach(button => button.addEventListener('click', () => markContacted(button)));
</script>
</body>
</html>
"""

@app.route("/")
def index():
    try:
        min_score = int(request.args.get("min_score", 0))
        if not 0 <= min_score <= 10:
            raise ValueError
    except ValueError:
        return jsonify(error="min_score must be an integer from 0 to 10"), 400
    city_filter = request.args.get("city", "")
    source_filter = request.args.get("source", "")
    
    init_db()
    stats = get_stats()
    
    from database import get_conn
    conn = get_conn()
    c = conn.cursor()
    query = "SELECT * FROM leads WHERE deal_score >= ?"
    params = [min_score]
    if city_filter:
        query += " AND city LIKE ?"
        params.append(f"%{city_filter}%")
    if source_filter:
        query += " AND source LIKE ?"
        params.append(f"%{source_filter}%")
    query += " ORDER BY deal_score DESC, created_at DESC LIMIT 100"
    c.execute(query, params)
    leads = c.fetchall()
    conn.close()
    
    return render_template_string(
        DASHBOARD_HTML,
        leads=leads,
        stats=stats,
        min_score=min_score,
        city_filter=city_filter,
        source_filter=source_filter,
        safe_url=safe_url,
        run_status=get_run_status(),
        recent_logs=get_recent_scrapes(limit=8),
        now_iso=datetime.now().isoformat(),
    )

_run_lock = threading.Lock()
_run_state = dict(running=False, status='idle', started_at=None, finished_at=None, results={}, error=None)


def _background_run():
    try:
        from run import run_all
        results = run_all()
        if not isinstance(results, dict) or not results:
            raise RuntimeError('Scraper returned no source outcomes')
        failed = any(r.get('err') or r.get('errors') or r.get('error') for r in results.values())
        with _run_lock:
            _run_state.update(results=results, status='completed_with_errors' if failed else 'completed')
    except Exception as exc:
        # No traceback or exception text in logs: upstream messages may contain credentials.
        with _run_lock:
            _run_state.update(status='failed', error=f'{type(exc).__name__}: scraper run failed; inspect source outcomes')
    finally:
        with _run_lock:
            _run_state.update(running=False, finished_at=datetime.now().isoformat())


def get_run_status():
    with _run_lock:
        state = deepcopy(_run_state)
    with closing(get_conn()) as conn:
        logs = [dict(row) for row in conn.execute('SELECT * FROM scrape_log ORDER BY id DESC LIMIT 20')]
    for log in logs:
        error = (log.get('error') or '').lower()
        log['status'] = ('blocked' if any(word in error for word in ('403', '429', 'blocked', 'captcha'))
                         else 'manual_only' if 'manual' in error else 'error' if error else 'completed')
    state['recent_logs'] = logs
    return state


@app.route('/scrape-status')
def scrape_status():
    return jsonify(get_run_status())


@app.route("/run", methods=['POST'])
def run_scraper():
    with _run_lock:
        if _run_state['running']:
            return jsonify(error='A scraper run is already active'), 409
        _run_state.update(running=True, status='running', started_at=datetime.now().isoformat(),
                          finished_at=None, results={}, error=None)
        try:
            threading.Thread(target=_background_run, name='dashboard-scraper', daemon=True).start()
        except Exception:
            _run_state.update(running=False, status='failed', error='Could not start scraper thread')
            return jsonify(error='Could not start scraper thread'), 500
    if request.accept_mimetypes.best == 'text/html':
        return redirect('/', code=303)
    return jsonify(status='running', status_url='/scrape-status'), 202

@app.route("/add", methods=["POST"])
def add_manual():
    from scoring import score_lead
    from database import upsert_lead
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    source = request.form.get("source", "").strip()
    link = request.form.get("link", "").strip()
    description = request.form.get("description", "").strip()
    if not all((address, city, source, description)):
        return jsonify(error="Address, city, source and description are required"), 400
    try:
        price = int(request.form.get("price", "").strip() or 0)
        if not 0 <= price <= 9223372036854775807:
            raise ValueError
    except ValueError:
        return jsonify(error="Price must be a non-negative whole number within the supported range"), 400
    if link and not safe_url(link):
        return jsonify(error="Link must be an absolute http:// or https:// URL"), 400
    
    score, reasons, motivation = score_lead(address, description, price, source)
    
    lead = {
        "id": f"manual_{uuid4().hex}",
        "address": address,
        "city": city,
        "price": price,
        "price_text": f"${price}" if price else "",
        "source": source,
        "source_type": "manual",
        "link": link,
        "description": f"{description} | SCORE REASONS: {reasons}",
        "owner_name": "",
        "owner_mailing": "",
        "motivation": motivation,
        "deal_score": score,
        "equity_estimate": "",
        "status": "new",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "raw_data": description
    }
    upsert_lead(lead)
    return redirect(f"/?min_score=0")

@app.route("/mark_contacted/<lead_id>", methods=["POST"])
def mark_contacted(lead_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE leads SET status='contacted', updated_at=? WHERE id=?", (datetime.now().isoformat(), lead_id))
    conn.commit()
    conn.close()
    if c.rowcount == 0:
        return jsonify(error="Lead not found"), 404
    return jsonify({"ok": True})

def csv_safe(value):
    if isinstance(value, str) and (value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n'))):
        return "'" + value
    return value


@app.route("/export")
def export_csv():
    from database import get_conn
    import csv
    from io import StringIO
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM leads ORDER BY deal_score DESC")
    rows = c.fetchall()
    conn.close()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(rows[0].keys() if rows else ["id","address","city","price","source","link","description","motivation","deal_score"])
    for r in rows:
        writer.writerow([csv_safe(r[k]) for k in r.keys()])
    
    from flask import Response
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=kern_private_leads.csv"})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Harbison Standard Branded Dashboard at http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
