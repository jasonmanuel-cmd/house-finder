"""
Investigation script for public-government surfaces.

Visits each configured surface, captures what's reachable, and persists a
structured report under artifacts/.
"""
from __future__ import annotations
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.browser_source import (
    SOURCES,
    build_browser,
    is_likely_public_surface,
    snapshot_page,
)

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)


def normalize(text: str | None) -> str:
    return " ".join((text or "").split())


def candidate_links_from_snap(snap: dict) -> list[dict]:
    links = snap.get("links") or []
    out = []
    seen = set()
    for link in links[:120]:
        text = normalize(link.get("text", "")).lower()
        href = link.get("href", "") or ""
        title_attr = normalize(link.get("title", "")).lower()
        combined = text + " " + title_attr
        if any(k in combined for k in [
            "auction", "parcel", "tax", "probate", "permit", "code",
            "vacant", "building", "planning", "recorder", "assessor",
            "owner", "deed", "sale", "notice", "default", "foreclosure",
            "nodel", "lis pendens",
        ]):
            if href and href not in seen:
                seen.add(href)
                out.append({
                    "text": link.get("text", "")[:160],
                    "href": href,
                    "title": link.get("title", "")[:80],
                    "classes": link.get("classes", [])[:6],
                })
    return out


def visible_parcel_text_from_html(html: str) -> str:
    out = ""
    for line in html.split("\n"):
        if any(ch.isdigit() for ch in line):
            out += line.strip()[:200] + "\n"
    return out[:3000]


def report_surface(page, source) -> dict:
    label = getattr(source, "label", str(source))
    key = getattr(source, "key", "")
    start_url = getattr(source, "start_url", "")
    notes = getattr(source, "notes", "")
    logging.info("Visiting %s -> %s", key, start_url)
    base: dict = {
        "source_key": key,
        "label": label,
        "start_url": start_url,
        "final_url": "",
        "status": None,
        "title": "",
        "reachable": False,
        "candidate_links": [],
        "link_count": 0,
        "text_sample": "",
        "notes": notes,
        "screenshot_path": "",
        "error": "",
    }
    try:
        raw = snapshot_page(page, start_url, wait_until="domcontentloaded")
    except Exception as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"
        logging.warning("Snapshot failed for %s: %s", key, base["error"])
        return base

    status = raw.get("status")
    title = raw.get("title") or ""
    browser_url = raw.get("browser_url") or ""
    links = raw.get("links") or []
    text_head = raw.get("text_head") or ""
    html = text_head[:12000]
    reachable = is_likely_public_surface(raw)

    base["final_url"] = browser_url
    base["status"] = status
    base["title"] = title
    base["reachable"] = reachable
    base["link_count"] = len(links)
    base["candidate_links"] = candidate_links_from_snap(raw)
    base["text_sample"] = visible_parcel_text_from_html(html)
    return base


def run() -> dict:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    browser = page = pw_context = None
    results: dict = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "sources": [],
        "summary": {},
    }
    try:
        browser, page, pw_context = build_browser(headless=True)
        for source in SOURCES:
            r = report_surface(page, source)
            results["sources"].append(r)
            results["summary"][r["source_key"]] = {
                "reachable": r["reachable"],
                "status": r["status"],
                "candidate_links": len(r["candidate_links"]),
                "link_count": r["link_count"],
                "error": r.get("error", ""),
                "title": r.get("title", ""),
            }
            line = f"{r['source_key']} | reachable={r['reachable']} | status={r['status']} | links={r['link_count']} | candidates={len(r['candidate_links'])}"
            if r.get("error"):
                line += f" | error={r['error'][:120]}"
            print(line)
            for cl in r["candidate_links"][:6]:
                print(f"    - {cl['text'][:90]} -> {cl['href']}")
            time.sleep(1.5)
    except Exception as exc:
        results["summary"]["_error"] = f"{type(exc).__name__}: {exc}"
        logging.exception("Investigation failed")
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if pw_context is not None:
            try:
                pw_context.__exit__(None, None, None)
            except Exception:
                pass
    return results


if __name__ == "__main__":
    out = run()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path_json = os.path.join(ARTIFACT_DIR, f"gov_surface_investigation_{ts}.json")
    path_txt = os.path.join(ARTIFACT_DIR, f"gov_surface_investigation_{ts}.txt")
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    with open(path_txt, "w", encoding="utf-8") as f:
        f.write("Public government surface investigation\n")
        f.write(f"Run at: {out['run_at']}\n\n")
        for src in out["sources"]:
            f.write(f"=== {src['label']} ({src['source_key']}) ===\n")
            f.write(f"start_url: {src['start_url']}\n")
            f.write(f"final_url: {src['final_url']}\n")
            f.write(f"status: {src['status']}\n")
            f.write(f"reachable: {src['reachable']}\n")
            f.write(f"title: {src['title']}\n")
            f.write(f"candidate_links ({len(src['candidate_links'])}):\n")
            for cl in src["candidate_links"]:
                f.write(f"  - {cl['text'][:120]} -> {cl['href']}\n")
            if src.get("error"):
                f.write(f"error: {src['error']}\n")
            f.write(f"text_sample:\n{src.get('text_sample', '')}\n\n")
    print(f"\nWrote {path_json} and {path_txt}")
