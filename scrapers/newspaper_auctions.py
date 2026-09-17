"""Public Kern County tax-auction legal notices from newspaper publications.

California Revenue and Taxation Code Sections 3381-3385 require these to be
published in newspapers of general circulation. They are public records.

Sources:
- The Mojave Desert News (desertnews.com) — eastern Kern County
- Taft Midway Driller (taftmidwaydriller.com) — western / Taft area
- Kern Valley Sun (kernvalleysun.com) — Kern River Valley

Each paper publishes only a portion of the county's notices; no single
source covers the whole county.
"""
import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import HEADERS
import database
from scoring import score_lead

# Known public auction notice URLs — these are the permalink pages that the
# county directs residents to. They are not search results.
NOTICE_URLS = {
    "mojave_desert_news": [
        "https://www.desertnews.com/classifieds/community/announcements/legal/ad_e177b8a0-dd9c-11ef-a49e-7feb983276d4.html",
        "https://www.desertnews.com/classifieds/community/announcements/legal/ad_c10c198a-f964-4392-b29e-b0af47e57e7a.html",
    ],
    "taft_midway_driller": [
        "https://bloximages.newyork1.vip.townnews.com/taftmidwaydriller.com/content/tncms/assets/v3/classifieds/9/78/97814f14-6195-427d-be72-ccd7024e252f/6877dec801175.pdf.pdf",
    ],
    "kern_valley_sun": [
        "https://kernvalleysun.com/stories/notice-of-public-auction-on-march-09-2026-to-march-11-2026-of-tax-defaulted-property-for,56411",
    ],
}

# APN pattern: map book - page - block - parcel - strip
_APN_RE = re.compile(
    r"\b(\d{2,3}-\d{2,3}-\d{2,3}-\d{2,3}-\d{1,3})\b"
)

# Amount pattern: $X,XXX.XX or $XXX
_AMOUNT_RE = re.compile(r"\$([\d,]+(?:\.\d{1,2})?)")

# Street address candidates
_ADDRESS_RE = re.compile(
    r"\b(\d{3,5}\s+[A-Z][a-zA-Z0-9 .'-]{3,40}\s+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Blvd|Boulevard|Ter|Terrace|Circle|Cir|Loop|Hwy|Highway|Wy|Way))\b",
    re.IGNORECASE,
)


def _parse_amount(text):
    """Extract dollar amount in cents as integer; return 0 if none."""
    match = _AMOUNT_RE.search(text)
    if not match:
        return 0
    raw = match.group(1).replace(",", "")
    if "." in raw:
        try:
            return int(round(float(raw)))
        except ValueError:
            return 0
    try:
        return int(raw)
    except ValueError:
        return 0


def _parse_owner_and_address(lines, start_idx):
    """Given lines starting at a parcel row, extract owner name and address."""
    owner = ""
    address = ""
    for offset in range(1, min(4, len(lines) - start_idx + 1)):
        idx = start_idx + offset
        if idx >= len(lines):
            break
        line = lines[idx].strip()
        if not line:
            continue
        # Skip if it looks like another APN/amount row
        if _APN_RE.match(line) or line.startswith("$"):
            continue
        # Skip publication date markers
        if line.startswith("(PUB:") or line.startswith("PUB:"):
            continue
        # First non-empty non-APN line is the owner
        if not owner:
            owner = line
            continue
        # Second non-empty line might be the property address
        addr_match = _ADDRESS_RE.search(line)
        if addr_match and not address:
            address = addr_match.group(1)
    return owner, address


def parse_notice_html(html, source_key):
    """Parse APN / owner / amount triples from a public auction notice page.

    Returns list of lead dicts. No invented data — missing fields stay empty.
    """
    text = html
    if hasattr(html, "get_text"):
        text = html.get_text("\n", strip=True)
    elif isinstance(html, str):
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)

    lines = [line.strip() for line in text.splitlines()]
    seen_apns = set()
    leads = []

    for i, line in enumerate(lines):
        apn_match = _APN_RE.search(line)
        if not apn_match:
            continue
        apn = apn_match.group(1)
        if apn in seen_apns:
            continue

        # Amount is typically on the same line or the line immediately after
        amount_line = line
        amount = _parse_amount(amount_line)
        if amount == 0 and i + 1 < len(lines):
            amount = _parse_amount(lines[i + 1])
            if amount > 0:
                amount_line = lines[i + 1]

        owner, address = _parse_owner_and_address(lines, i)
        if not owner:
            continue  # Can't build a lead without an owner

        seen_apns.add(apn)
        full_address = f"{address}, APN {apn}" if address else f"APN {apn}"
        city = ""
        if address:
            # Try to infer city from context if nearby lines mention one
            for ctx in lines[max(0, i - 2):min(len(lines), i + 8)]:
                for candidate in ("Bakersfield", "Tehachapi", "California City",
                                  "Taft", "Maricopa", "Mojave", "Ridgecrest",
                                  "Lake Isabella", "Weldon", "Bodfish", "Kernville",
                                  "Rosamond", "Cantil", "Delano", "Shafter",
                                  "Wasco", "Arvin", "Lamont", "Buttonwillow"):
                    if candidate.lower() in ctx.lower():
                        city = candidate
                        break
                if city:
                    break

        leads.append({
            "apn": apn,
            "owner_name": owner,
            "address": full_address,
            "city": city,
            "amount": amount,
            "source_key": source_key,
            "property_address": address,
        })

    return leads


def scrape_newspaper_auctions(*, urls=None):
    """Fetch public auction notices and persist verified parcel-owner records.

    Returns (found, new, error_or_empty). Only APN + owner + amount are
    accepted; a landing page with no rows is an error, not an empty success.
    """
    if urls is None:
        urls = []
        for source_urls in NOTICE_URLS.values():
            urls.extend(source_urls)

    found = new = 0
    errors = []
    all_leads = []

    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=(5, 20))
            resp.raise_for_status()
            html = resp.text

            if not html or len(html) < 200:
                errors.append(f"{url}: empty or too short response")
                continue

            source_key = next(
                (k for k, v in NOTICE_URLS.items() if url in v), "newspaper_auction"
            )
            leads = parse_notice_html(html, source_key)

            if not leads:
                errors.append(f"{url}: no verified APN-owner rows in public notice")
                continue

            all_leads.extend(leads)

        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            if status in (403, 429):
                errors.append(f"{url}: HTTP {status} (blocked; do not retry)")
                break
            errors.append(f"{url}: HTTP {status}")
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")

    now = datetime.now(timezone.utc).isoformat()
    for record in all_leads:
        apn = record["apn"]
        owner = record["owner_name"]
        amount = record["amount"]
        source_key = record["source_key"]

        score, reasons, motivation = score_lead(
            record["address"],
            f"Kern County tax auction legal notice — public record; {source_key}; verify status",
            amount,
            "tax_auction_notice",
        )

        lead = dict(
            id=f"np_auction_{source_key}_{apn}",
            address=record["address"],
            city=record["city"],
            price=amount,
            price_text=f"${amount:,}" if amount else "See notice",
            source="newspaper_auction",
            source_type="tax_auction_notice",
            link=NOTICE_URL_URLS.get(source_key, NOTICE_URLS.get(source_key, [""])[0]
                if NOTICE_URLS.get(source_key) else ""),
            description=(
                f"Kern County tax-auction public notice — {source_key}\n"
                f"APN: {apn}\n"
                f"Owner of record: {owner}\n"
                f"Minimum bid: ${amount:,}\n" if amount else "Minimum bid: see notice\n"
            ) + "Verify current auction status and owner before outreach. Public record; not a private-seller listing.",
            owner_name=owner,
            owner_mailing="",
            motivation=motivation,
            deal_score=score,
            equity_estimate="",
            status="new",
            created_at=now,
            updated_at=now,
            raw_data=json.dumps(record, ensure_ascii=False),
        )
        found += 1
        if database.upsert_lead(lead):
            new += 1

    return found, new, "; ".join(errors)


# Convenience map used by lead.link to find a representative source page
NOTICE_URL_URLS = {
    "mojave_desert_news": "https://www.desertnews.com/classifieds/community/announcements/legal/",
    "taft_midway_driller": "https://www.taftmidwaydriller.com/classifieds/",
    "kern_valley_sun": "https://kernvalleysun.com/legals/",
}
