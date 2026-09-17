"""Public-government lead sources for Kern County private sellers.

Legitimate targets only: county assessor, recorder, court, city/county public
records. Commercial listing sites are out of scope for automated retrieval.
"""
from config import HEADERS
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

logger = logging.getLogger('govleads')
SESSION_HEADERS = {**HEADERS, 'Accept-Language': 'en-US,en;q=0.9'}

def now_iso():
    return datetime.now(timezone.utc).isoformat()
