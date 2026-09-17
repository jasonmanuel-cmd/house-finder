"""Availability check only; never manufactures parcel records."""
import requests
from config import HEADERS
from database import upsert_lead  # Shared API; no writes without verified parcel records.


def scrape_bakersfield_code():
    errors = []
    for url in ['https://data.bakersfieldcity.us/']:
        try:
            response = requests.get(url, headers=HEADERS, timeout=(5, 15))
            response.raise_for_status()
            errors.append(f"{url}: No verified code-enforcement dataset/schema configured; portal resources are not property leads.")
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    return 0, 0, "; ".join(errors)
