"""Browser investigation of public government surfaces, not lead ingestion.

Save access evidence and research links under artifacts/browser. Landing-page
addresses and example APNs do not establish property-level seller records.
Canonical auction ingestion is owned exclusively by the HTTP scraper.
No credentials, commercial listing sites, or access-challenge bypasses.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

from playwright.sync_api import Page, Browser, sync_playwright

logger = logging.getLogger("govleads.browser")
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "browser"

# ---------------------------------------------------------------------------
# Source catalogue — updated to live domains
# ---------------------------------------------------------------------------

@dataclass
class SourceSpec:
    key: str
    label: str
    start_url: str
    kind: str
    tags: list[str] = field(default_factory=list)
    notes: str = ""


SOURCES: list[SourceSpec] = [
    # Kern County Assessor-Recorder (current domain; old kerncountyca.gov has no A records)
    SourceSpec(
        key="kern_county_assessor_recorder",
        label="Kern County Assessor-Recorder",
        start_url="https://www.kerncounty.com/assessor-recorder",
        kind="assessor",
        tags=["public-records", "javascript-heavy"],
        notes="Current Kern County Assessor-Recorder landing page (kerncounty.com).",
    ),
    # Kern County Treasurer-Tax Collector — tax Default / lien / auction info
    SourceSpec(
        key="kern_county_treasurer_tax",
        label="Kern County Treasurer & Tax Collector",
        start_url="https://www.kcttc.co.kern.ca.us/index.cfm?fuseaction=kcttcinternet.showGeneralTaxSaleInfo",
        kind="tax_audit",
        tags=["tax", "public-records"],
        notes="Kern County Treasurer & Tax Collector general tax sale info page (still resolves).",
    ),
    # Bakersfield Building Permits — live, real content
    SourceSpec(
        key="bakersfield_building_permits",
        label="City of Bakersfield Building Permits",
        start_url="https://www.bakersfieldcity.us/building-permits",
        kind="code",
        tags=["building-permits", "code-enforcement", "javascript-heavy"],
        notes="City of Bakersfield building permits page (bakersfieldcity.us) — returns real content.",
    ),
    # Bakersfield online permit application and status
    SourceSpec(
        key="bakersfield_permit_status",
        label="City of Bakersfield Online Permit Status",
        start_url="https://www.bakersfieldcity.us/online-permit-application-and-status",
        kind="code",
        tags=["building-permits", "permit-search"],
        notes="Online permit application and status lookup.",
    ),
    # Tehachapi city site — current domain confirmed: liveuptehachapi.com (CivicPlus)
    SourceSpec(
        key="tehachapi_city",
        label="City of Tehachapi",
        start_url="https://www.liveuptehachapi.com/",
        kind="city_portal",
        tags=["city-portal", "javascript-heavy"],
        notes="Tehachapi city site (liveuptehachapi.com, CivicPlus).",
    ),
    # GovEase auctions are handled exclusively by the canonical HTTP scraper.
]


# ---------------------------------------------------------------------------
# Browser lifecycle
# ---------------------------------------------------------------------------

def build_browser_launch(
    headless: bool = True,
    user_agent: str | None = None,
    viewport: dict[str, int] | None = None,
) -> tuple[Browser, Page, Any]:
    """Launch a browser that stays alive — caller must close it."""
    vp = viewport or {"width": 1366, "height": 900}
    pw_context = sync_playwright()
    pw = pw_context.__enter__()
    try:
        browser = pw.chromium.launch(headless=headless)
        options = {"viewport": vp, "locale": "en-US", "java_script_enabled": True}
        if user_agent is not None:
            options["user_agent"] = user_agent
        ctx = browser.new_context(**options)
        page = ctx.new_page()
        logger.info("Browser launched for public-record investigation")
        return browser, page, pw_context
    except Exception:
        try:
            pw_context.__exit__(None, None, None)
        except Exception:
            pass
        raise


# Back-compat alias used by investigate_gov_surfaces.py
build_browser = build_browser_launch


def _has_access_challenge(text: str) -> bool:
    markers = (
        "just a moment", "verify you are human", "verify that you are human",
        "checking your browser", "access denied", "captcha", "cf-chl-",
        "challenge-platform", "sign in to continue", "login required",
    )
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def snapshot_page(
    page: Page, revisit_url: str, wait_until: str = "domcontentloaded"
) -> dict:
    """Grab basic page evidence after a navigation for later parsing."""
    resp = page.goto(revisit_url, wait_until=wait_until, timeout=45000)
    status = resp.status if resp else None
    title = page.title()
    links: list[dict[str, str]] = []
    for handle in page.eval_on_selector_all(
        "a",
        """els => els.map(e => ({
            text: (e.innerText || '').trim(),
            href: e.href,
            title: (e.title || ''),
            classes: (e.className || '').split(' ').filter(Boolean)
        }))""",
    ):
        links.append(handle)
    html = page.content()
    return {
        "url": revisit_url,
        "status": status,
        "title": title,
        "links": links[:200],
        "text_head": html[:12000],
        "access_challenge": _has_access_challenge(title + " " + html),
        "browser_url": page.url,
    }


def is_likely_public_surface(response: dict) -> bool:
    """Conservative evidence check, not proof of property-level records.

    Redirect/error responses and challenge/login pages are not successful
    research. Never attempt to solve or bypass an access challenge.
    """
    if not response or response.get("status") != 200:
        return False
    html = (response.get("text_head") or "")
    evidence = (response.get("title") or "") + " " + html
    if response.get("access_challenge") or _has_access_challenge(evidence):
        return False
    if "<html" not in html.lower() and "<!doctype" not in html.lower():
        return False
    links = response.get("links") or []
    return len(links) >= 2


# ---------------------------------------------------------------------------
# Research helpers — candidate strings only, never verified leads
# ---------------------------------------------------------------------------

_PARCEL_RE = re.compile(r"\b\d{2,3}-\d{2,3}-\d{2,3}-\d{2,3}-\d{1,3}\b")
_APN_OR_ADDRESS_RE = re.compile(
    r"\b(\d{2,3}-\d{2,3}-\d{2,3}-\d{2,3}-\d{1,3})\b"
    r"|(\d{3,5}\s+[A-Z][a-zA-Z0-9 .\u2019'-]{4,50}\s+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane| Ct|Court|Pl|Place|Way|Blvd|Boulevard|Ter|Terrace|Circle|Cir|Loop| Hwy|Highway|Camino|Del|De|Rancho|Pkwy|Parkway|Way|Trial|Trl|Canyon|Cyn|Cc|Calle|Oaks|Oak))",
    re.IGNORECASE,
)


def extract_parcels_from_text(text: str) -> list[str]:
    """Find APN-style identifiers in visible text."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _PARCEL_RE.finditer(text):
        apn = m.group(0)
        if apn not in seen:
            seen.add(apn)
            out.append(apn)
    return out


def extract_address_candidates(text: str) -> list[dict]:
    """Pull candidate address strings from visible page text.

    Returns a list of {'raw': ..., 'apn': ... or None, 'street': ... or None}.
    """
    candidates: list[dict] = []
    seen_raw: set[str] = set()
    for m in _APN_OR_ADDRESS_RE.finditer(text):
        apn = m.group(1)
        street = m.group(2)
        if street:
            raw = street.strip()
            if raw and len(raw) > 8 and raw not in seen_raw:
                seen_raw.add(raw)
                candidates.append({"raw": raw, "apn": apn, "street": raw})
        elif apn:
            if apn not in seen_raw:
                seen_raw.add(apn)
                candidates.append({"raw": apn, "apn": apn, "street": ""})
    return candidates


# ---------------------------------------------------------------------------
# Retired parser compatibility — generic surfaces produce no leads
# ---------------------------------------------------------------------------

def parse_bakersfield_building_permits(page: Page, source_key: str) -> list[dict]:
    """Generic permit landing pages are research evidence, not property leads."""
    return []


def parse_govease_auction(page: Page, source_key: str, auction_id: str) -> list[dict]:
    """Compatibility no-op: canonical auction records belong to kern_tax.py.

    The retired browser parser fabricated bids and duplicate identities. Never
    replace richer HTTP records with incomplete browser discoveries.
    """
    return []


def parse_kern_assessor_recorder(page: Page, source_key: str) -> list[dict]:
    """Assessor office addresses and sample APNs do not identify seller leads."""
    return []


# ---------------------------------------------------------------------------
# Main scrape entry point (called from run.py)
# ---------------------------------------------------------------------------

def scrape_browser_sources() -> tuple[int, int, str]:
    """Investigate configured surfaces; save evidence, never database leads.

    Return the historical (found, new, errors) contract with both lead counts
    zero. Candidate links require manual review; none are followed implicitly.
    """
    browser = page = pw_context = None
    errors_parts: list[str] = []
    now = datetime.now(timezone.utc)
    report = {"run_at": now.isoformat(), "sources": []}
    try:
        browser, page, pw_context = build_browser(headless=True)
        for source in SOURCES:
            item = {
                "source_key": source.key, "label": source.label,
                "start_url": source.start_url, "notes": source.notes,
                "status": None, "reachable": False, "candidate_links": [],
                "leads_extracted": 0, "error": "",
            }
            report["sources"].append(item)
            try:
                snap = snapshot_page(page, source.start_url)
                item.update(
                    status=snap.get("status"),
                    reachable=is_likely_public_surface(snap),
                    final_url=snap.get("browser_url"),
                    title=snap.get("title"), snap=snap,
                )
                if not item["reachable"]:
                    item["error"] = (
                        f"HTTP {item['status']}: inaccessible, challenged, or unsupported surface; "
                        "manual review required"
                    )
                    errors_parts.append(f"{source.key}: {item['error']}")
                    continue
                seen = set()
                keywords = (
                    "auction", "parcel", "tax", "probate", "permit", "code",
                    "vacant", "building", "planning", "recorder", "assessor",
                    "owner", "deed", "sale", "notice", "default", "foreclosure",
                    "lis pendens", "property search", "document search",
                )
                for link in snap.get("links", []):
                    href = link.get("href") or ""
                    label = ((link.get("text") or "") + " " +
                             (link.get("title") or "")).lower()
                    if href and href not in seen and any(k in label for k in keywords):
                        seen.add(href)
                        item["candidate_links"].append(link)
            except Exception as exc:
                item["error"] = f"{type(exc).__name__}: {exc}"
                errors_parts.append(f"{source.key}: {item['error']}")
    except Exception as exc:
        errors_parts.append(f"browser_investigation: {type(exc).__name__}: {exc}")
    finally:
        for resource in (page, browser):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    logger.warning("Browser resource cleanup failed", exc_info=True)
        if pw_context is not None:
            try:
                pw_context.__exit__(None, None, None)
            except Exception:
                logger.warning("Playwright cleanup failed", exc_info=True)

    report["errors"] = errors_parts.copy()
    try:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        artifact = ARTIFACT_DIR / f"investigation_{now.strftime('%Y%m%dT%H%M%S_%fZ')}.json"
        with artifact.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        logger.info("Browser investigation report: %s", artifact)
    except Exception as exc:
        errors_parts.append(f"browser_report: {type(exc).__name__}: {exc}")
    return 0, 0, "; ".join(errors_parts)

