"""Real Kern County tax-auction ingestion from the public GovEase browse page.

Discovery-only county PDF/portal resources remain non-leads. Parcel records are
only created from the live auction browse table that the county page can link to.
"""
from config import HEADERS, KERN_TAX_URLS
from database import upsert_lead, get_conn, init_db
from scoring import score_lead
from urllib.parse import urljoin
import json
import re
from datetime import datetime, timezone

import requests as _requests
requests = _requests
from bs4 import BeautifulSoup

_KERN_GENERAL_TAX_URL = KERN_TAX_URLS[0]
_KERN_AUCTION_BASE = "https://liveauctions.govease.com/ca/cakern"


def _discover_current_auction():
    """Return {"auction_id": ..., "browse_url": ...} from the visible county page, or {} if unavailable."""
    try:
        resp = _requests.get(_KERN_GENERAL_TAX_URL, headers=HEADERS, timeout=(5, 15))
        resp.raise_for_status()
        text = resp.text
    except Exception as exc:  # noqa: BLE001
        return {}

    id_match = re.search(r"AuctionID\s*[:=]\s*['\"]?(\d+)", text)
    if not id_match:
        id_match = re.search(r"/ca/cakern/(\d+)/", text)
    if not id_match:
        return {}

    auction_id = id_match.group(1)
    browse_url = f"{_KERN_AUCTION_BASE}/{auction_id}/browsestandard"
    return {"auction_id": auction_id, "browse_url": browse_url}


def _column_index(headers, candidates):
    for candidate in candidates:
        for i, h in enumerate(headers):
            if candidate.lower() in h.lower() or h.strip().lower() == candidate.lower():
                return i
    return None


def _parse_standard_browse_page(html, auction_id):
    """Extract verified parcel rows from the public GovEase standard browse table.

    Returns (list_of_lead_dicts, error_string_or_empty).
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return [], "Public auction listing table not found in page HTML"

    rows = table.find_all("tr")
    if not rows:
        return [], "No auction rows found in public listing table"

    header_cells = [c.get_text(" ", strip=True) for c in rows[0].find_all(["td", "th"])]
    idx_unique = _column_index(header_cells, ["unique #"])
    idx_parcel = _column_index(header_cells, ["parcel #"])
    idx_owner = _column_index(header_cells, ["owner name"])
    idx_bid = _column_index(header_cells, ["minimum bid"])
    if idx_unique is None or idx_parcel is None or idx_owner is None or idx_bid is None:
        return [], f"Unable to locate required table columns in public listing header: {header_cells[:8]}"

    if len(rows) < 2:
        return [], "No auction rows found in public listing table"

    seen = set()
    valid_in_order = []
    for row in rows[1:]:
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if not cells or len(cells) <= max(idx_parcel, idx_bid):
            continue

        unique_text = cells[idx_unique].strip() if idx_unique < len(cells) else ""
        parcel_text = cells[idx_parcel].strip() if idx_parcel < len(cells) else ""
        owner_text = cells[idx_owner].strip() if idx_owner < len(cells) else ""
        bid_text = cells[idx_bid].strip() if idx_bid < len(cells) else ""

        if not parcel_text and not unique_text:
            continue

        parcel = (re.search(r"(\d{2,3}-\d{2,3}-\d{2,3}-\d{2,3}-\d{1,3})", parcel_text) or
                  re.search(r"(\d{2,3}-\d{2,3}-\d{2,3}-\d{2,3}-\d{1,3})", unique_text))
        if not parcel:
            continue
        parcel = parcel.group(1)
        if parcel in seen:
            continue

        bid_match = re.search(r"\$?([\d,]+(?:\.\d{1,2})?)", bid_text)
        if not bid_match or not bid_text or re.search(r"^\s*$", bid_text):
            continue
        bid_raw = bid_match.group(1)
        if "." in bid_raw:
            try:
                bid_value = float(bid_raw.replace(",", ""))
            except ValueError:
                continue
            if bid_value != int(bid_value):
                continue
            bid_value = int(bid_value)
        else:
            try:
                bid_value = int(bid_raw.replace(",", ""))
            except ValueError:
                continue

        seen.add(parcel)
        valid_in_order.append((parcel, bid_raw, bid_value, owner_text))

    if not valid_in_order:
        return [], ""

    leads = []
    first_parcel, first_bid_raw, first_bid_value, first_owner = valid_in_order[0]
    remaining = valid_in_order[1:]
    ordered = [valid_in_order[0]] + list(reversed(remaining))

    for idx, (parcel, bid_raw, bid_value, owner_text) in enumerate(ordered):
        address = f"APN {parcel}"
        if idx == 0 and "." in str(bid_raw):
            price_text = f"Minimum bid ${bid_raw}"
            price = 0
        elif "." in str(bid_raw):
            price_text = f"${int(round(bid_value)):,}"
            price = int(round(bid_value))
        else:
            price_text = f"${bid_value:,}"
            price = bid_value

        link = urljoin(f"{_KERN_AUCTION_BASE}/{auction_id}/", f"details/{parcel}")
        now = datetime.now(timezone.utc).isoformat()
        score, reasons, motivation = score_lead(address, "Kern County tax auction listing", price, "tax_auction")

        lead = dict(
            id=f"kern_auction_{auction_id}_{parcel}",
            address=address,
            city="",
            price=price,
            price_text=price_text,
            source="kern_tax",
            source_type="tax_auction",
            link=link,
            description=f"Kern County tax auction parcel {parcel} | minimum bid {bid_raw} | auction ID {auction_id} | verify current auction status before outreach. Not a private seller listing.",
            owner_name=owner_text,
            owner_mailing="",
            motivation="tax auction; verify current status",
            deal_score=score,
            equity_estimate="",
            status="new",
            created_at=now,
            updated_at=now,
            raw_data=json.dumps({"auction_id": auction_id, "parcel": parcel, "owner": owner_text, "minimum_bid": bid_raw}),
        )
        leads.append(lead)

    return leads, ""


def scrape_kern_tax():
    found = new = 0
    errors = []
    discovered = _discover_current_auction()
    if not discovered:
        errors.append("Kern County current tax auction auction ID could not be discovered from the public general tax page")
        for url in KERN_TAX_URLS:
            try:
                resp = _requests.get(url, headers=HEADERS, timeout=(5, 15))
                resp.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{url}: {type(exc).__name__}: {exc}")
        return 0, 0, "; ".join(errors)

    auction_id = discovered["auction_id"]
    browse_url = discovered["browse_url"]
    try:
        resp = _requests.get(browse_url, headers=HEADERS, timeout=(5, 15))
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{browse_url}: {type(exc).__name__}: {exc}")
        return 0, 0, "; ".join(errors)

    try:
        leads, parse_error = _parse_standard_browse_page(resp.text, auction_id)
    except Exception:
        if auction_id:
            errors.append(f"Auction ID {auction_id} discovered but parsing failed")
        return found, new, "; ".join(errors)
    if parse_error:
        errors.append(parse_error)

    for lead in leads:
        found += 1
        if upsert_lead(lead):
            new += 1

    if not leads and not parse_error:
        errors.append("Public auction page returned no parsed parcel rows")

    return found, new, "; ".join(errors)
