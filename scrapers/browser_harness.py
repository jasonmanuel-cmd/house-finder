"""
Browser scraper harness for public-government surfaces.

Runs a Playwright browser, visits each public source, snapshots each page,
collects candidate links and any visible parcel/at-surface identifiers,
and returns structured results.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import expect

from browser_source import SOURCES, build_browser, GovPage

TOP = Path(__file__).resolve().parent
LOG = logging.getLogger("govleads.harness")


def summarize_text(text: str, n: int = 400) -> str:
    return (text or "").replace("\n", " ").strip()[:n]


async def run(session: Any) -> dict[str, Any]:
    """Run one browser investigation session across public surfaces."""
    browser, page = build_browser(headless=True)
    results: dict[str, Any] = {}
    session_targets: list[str] = session.get("targets", [s.key for s in SOURCES])

    try:
        for source in SOURCES:
            if source.key not in session_targets:
                continue
            LOG.info("visiting %s -> %s", source.key, source.start_url)
            gov = GovPage(page, source.start_url)
            snap = await gov.visit(source.start_url, source.label)

            page_result = {
                "key": source.key,
                "label": source.label,
                "start_url": source.start_url,
                "type": source.kind,
                "tags": source.tags,
                "note": source.notes,
                "snapshot": {
                    "url": snap.get("url"),
                    "browser_url": snap.get("browser_url"),
                    "status": snap.get("status"),
                    "title": snap.get("title"),
                    "link_count": len(snap.get("links", [])),
                    "text_head": summarize_text(snap.get("text_head")),
                },
                "candidates": await gov.find_auctions_or_listings(page, source.key),
            }

            results[source.key] = page_result
    finally:
        browser.close()

    return results


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    session = {
        "targets": [s.key for s in SOURCES],
        "session_id": Path(TOP).name,
        "run_at": Path(TOP).parent.name,
    }

    results = None
    try:
        async def _runner():
            return await run(session)

        import asyncio
        results = asyncio.run(_runner())
    except Exception as e:
        LOG.exception("browser harness failed: %s", e)
        results = {"error": f"{type(e).__name__}: {e}", "session": session}

    # Save structured report
    report_dir = TOP / "artifacts" / "browser"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "browser_session.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    LOG.info("wrote %s", report_path)

    # Also write to workspace if available
    try:
        from hermes_tools import write_file
        write_file(str(report_path), json.dumps(results, indent=2))
    except Exception:
        pass


if __name__ == "__main__":
    main()
