"""
Simple Dashboard for No-MLS Deal Finder — Free
Run: pip install flask
     python app.py
Then open: http://localhost:5000
"""
from flask import Flask, render_template_string, request
import sqlite3
import os

DB_PATH = "deals.db"
app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kern No-MLS Deal Finder — Harbison Standard</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#031c2b;color:#fff;margin:0;padding:20px}
h1{color:#d4a574;margin:0 0 10px}
.sub{color:#8aa0b0;margin-bottom:20px}
.card{background:#0a2a3f;border-radius:12px;padding:16px;margin-bottom:12px;border-left:4px solid #d4a574}
.card.high{border-left-color:#ff4d4d}
.card.med{border-left-color:#ffcc00}
.card.low{border-left-color:#4caf50}
.meta{font-size:13px;color:#8aa0b0}
.price{font-size:22px;font-weight:700;color:#d4a574}
a{color:#d4a574;text-decoration:none}
a:hover{text-decoration:underline}
.filter{margin-bottom:20px;display:flex;gap:10px;flex-wrap:wrap}
.filter a{padding:8px 14px;background:#0a2a3f;border:1px solid #1a3a4f;border-radius:8px;color:#fff}
.filter a.active{background:#d4a574;color:#031c2b;font-weight:700}
.btn{display:inline-block;padding:8px 12px;background:#d4a574;color:#031c2b;border-radius:6px;font-weight:600;margin-top:8px}
.small{font-size:12px;color:#8aa0b0}
</style>
</head>
<body>
<h1>🏜️ Kern No-MLS Deal Finder</h1>
<div class="sub">Harbison Standard — Free sources: Craigslist, FB, Zillow FSBO, Tax-Defaulted, NOD, Probate | DB: {{total}} deals</div>

<div class="filter">
<a href="/?min_score=0" class="{{'active' if min_score==0 else ''}}">All ({{total}})</a>
<a href="/?min_score=5" class="{{'active' if min_score==5 else ''}}">Score 5+ ({{count5}})</a>
<a href="/?min_score=7" class="{{'active' if min_score==7 else ''}}">Score 7+ Hot ({{count7}})</a>
<a href="/?city=Tehachapi" class="{{'active' if city_filter=='Tehachapi' else ''}}">Tehachapi</a>
<a href="/?city=Bakersfield" class="{{'active' if city_filter=='Bakersfield' else ''}}">Bakersfield</a>
<a href="/?city=California%20City" class="{{'active' if city_filter=='California City' else ''}}">California City</a>
</div>

{% for d in deals %}
<div class="card {{'high' if d[6]>=7 else 'med' if d[6]>=5 else 'low'}}">
<div class="price">${{d[2]}} <span class="meta">| Score {{d[6]}}/10 | {{d[3]}} | {{d[5]}}</span></div>
<div style="font-weight:600;margin:6px 0">{{d[0]}}</div>
<div class="meta">{{d[4][:300]}}</div>
<div style="margin-top:10px">
<a class="btn" href="{{d[1]}}" target="_blank">View Original →</a>
<a class="btn" style="background:#0a2a3f;color:#fff;border:1px solid #1a3a4f;margin-left:8px" href="https://www.truepeoplesearch.com/results?name={{d[0][:20]}}" target="_blank">Skip Trace Free</a>
</div>
<div class="small" style="margin-top:8px">Found: {{d[7]}} | Source: {{d[5]}} | ID: {{d[8][:20]}}</div>
</div>
{% endfor %}

{% if not deals %}
<p>No deals match filter. Run <code>python craigslist_rss.py</code> first.</p>
{% endif %}

<hr style="margin:30px 0;border:0;border-top:1px solid #1a3a4f">
<div class="small">
<h3>How to use (Free, No MLS)</h3>
<ol>
<li>Run <code>python craigslist_rss.py</code> daily — auto-fills DB</li>
<li>Manually check Zillow FSBO + FB Marketplace + add to Google Sheet</li>
<li>Weekly: Check Kern County Treasurer tax-defaulted PDF + Recorder NOD + Court Probate (see kern_county_sources.md)</li>
<li>Score 7+ = call immediately. Use TruePeopleSearch.com for free phone.</li>
<li>Template sheet: <a href="/static/template.csv">Download CSV Template</a></li>
</ol>
<p>Full guide: README.md | Dev Playbook: ../DEV_PLAYBOOK_HARBISON.md</p>
</div>
</body>
</html>
"""

def get_counts():
    if not os.path.exists(DB_PATH):
        return 0,0,0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM deals")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM deals WHERE deal_score>=5")
        c5 = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM deals WHERE deal_score>=7")
        c7 = c.fetchone()[0]
    except:
        total=c5=c7=0
    conn.close()
    return total,c5,c7

@app.route("/")
def index():
    min_score = int(request.args.get("min_score", 0))
    city_filter = request.args.get("city", "")

    if not os.path.exists(DB_PATH):
        deals = []
        total=c5=c7=0
    else:
        total,c5,c7 = get_counts()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = "SELECT title, link, price, city, description, source, deal_score, created_at, id FROM deals WHERE deal_score>=? "
        params = [min_score]
        if city_filter:
            query += " AND city LIKE ? "
            params.append(f"%{city_filter}%")
        query += " ORDER BY deal_score DESC, created_at DESC LIMIT 100"
        try:
            c.execute(query, params)
            deals = c.fetchall()
        except Exception as e:
            deals = []
        conn.close()

    return render_template_string(HTML, deals=deals, total=total, count5=c5, count7=c7, min_score=min_score, city_filter=city_filter)

if __name__ == "__main__":
    print("Starting dashboard at http://localhost:5000")
    print("If no deals, run: python craigslist_rss.py first")
    app.run(host="0.0.0.0", port=5000, debug=True)
