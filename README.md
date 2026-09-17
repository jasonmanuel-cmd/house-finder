# Private Seller System — Harbison Standard

Private, local lead-research dashboard for Kern County, California. The maintained application is **the Python application at this repository root**. The `non-mls-deal-finder/` folder is an older prototype; `private-seller-system/` contains marketing drafts and standalone page assets, not another installed website.

## Open on this Windows computer

Double-click **Start Dashboard.cmd**, then open **http://127.0.0.1:5000**. Keep the terminal window open; Ctrl+C stops the server. The launcher uses the project-specific Python 3.11 environment, not the machine's potentially incompatible default Python.

Manual setup (requires Python 3.11 or uv):

```text
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe serve.py
```

On Linux/macOS, substitute `.venv/bin/python` for `.venv/Scripts/python.exe`.

## What the system actually does

- Stores actual imported or manually entered property leads in SQLite.
- Scores descriptions using keyword, source, and price heuristics. **A score is a research-priority signal, not a valuation, verified equity estimate, or proof of seller motivation.** Confirm details with the owner and authoritative records.
- Filters leads, records contacted status, and exports CSV.
- Offers on-demand source checking with visible progress and per-source outcomes.
- Separates manual-research resources from real property leads. A search link or a tax-sale brochure is **not** a lead and must never inflate the hot-lead count.

**Source limitations:** Craigslist may block requests or no longer serve RSS. Zillow may block automation. County source URLs and auction lists change; a generic PDF is not a verified parcel listing. Facebook, probate, recorder, and wholesaler research are manual unless an actual supported import is implemented. An empty database is an honest result, not permission to generate example properties. Do not bypass access controls.

## Daily workflow

1. Open the dashboard and run a source check. Read source errors, not just the lead count.
2. Review actual leads using city/source/score filters; open the original record and confirm listing date, location, owner/agent status, and availability.
3. For sources requiring manual research, open their resource links and add a specific property using **Add Manual Lead**. Include its real source URL and factual notes.
4. Mark contacted only after outreach. Respect opt-outs, applicable calling/texting restrictions, and brokerage requirements. An assessor lookup or people-search link does not verify ownership or contact consent.
5. Export CSV regularly. For a complete restorable backup, stop the app and copy the entire `data/` directory, including any SQLite companion files. Keep backups private.

Do not promise a closing date, referral compensation, MLS exclusion, or marketing/legal compliance based only on the draft marketing documents. Obtain seller consent and brokerage/legal review for the actual transaction.

## Storage and privacy

Default database: `data/leads.db`, resolved relative to this project, not the shell working directory. Optional **DB_PATH** environment variable overrides it. Local storage survives restarts and deployments of files as long as that directory is preserved.

The supported server (`serve.py`) binds only to **127.0.0.1** by default. Do not port-forward an unprotected dashboard. Public binding requires a **DASHBOARD_TOKEN** environment variable; set a durable **SECRET_KEY** for cloud sessions. Use HTTPS before sending authentication over a network. Keep these values in your host's secret settings, never in source control or URLs.

CSV contains private research data. Share only with authorized recipients. Test fixtures are isolated from the real database.

## Optional hosting — not deployed automatically

`render.yaml` is an **optional paid** single-web-service deployment with a persistent disk. Review and approve current provider pricing before applying it. It intentionally does not launch a separate scraper worker: two independent SQLite files on two services would not share leads. On-demand scraping runs inside the dashboard process and writes to its disk.

The previous instructions incorrectly described free persistent storage and a shared database across independent services. Do not use that setup. The historical handoff and marketing files may contain outdated claims; this README describes the supported root application.

`Dockerfile` runs the same single-process server. Mount persistent storage at `/app/data` and supply `DASHBOARD_TOKEN`; the container refuses an unauthenticated public bind. Docker and Render require their own deployment verification; successful local tests do not prove a cloud deployment.

For local scheduled runs, `run.py --once` checks sources once; `run.py --loop` checks hourly while the process remains running. This does not install an operating-system startup task. Do not run multiple scrape schedulers concurrently.

## Verification

```text
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m compileall -q app.py database.py config.py scoring.py run.py serve.py scrapers
```

`GET /health` checks server/database readiness. Source availability is separate: inspect dashboard source results. This downloaded folder is not necessarily a Git checkout; no GitHub push or deployment is implied by local file changes.

## Owner

Nathanael Harbison, REALTOR®, DRE #02059393 — Harbison Standard, Kern County.
(661) 472-7499 · nate85.realtor@gmail.com
