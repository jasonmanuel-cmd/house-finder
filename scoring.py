"""
Deal scoring engine
"""
import re
from config import SCORE_KEYWORDS

def extract_price(text):
    if not text:
        return 0
    # Find $12,000 or $12000 or 12000
    m = re.search(r'\$([\d,]+)', text)
    if m:
        try:
            return int(m.group(1).replace(',', ''))
        except:
            return 0
    return 0

def score_lead(title, description, price=0, source_type=""):
    text = f"{title} {description}".lower()
    # Generic real-estate wording is not evidence of an inherited estate.
    text = re.sub(r'\breal\s+estate\b', 'property', text)
    def contains(keyword):
        return re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text) is not None

    score = 0
    reasons = []

    # Keyword scoring
    for kw, pts in SCORE_KEYWORDS.items():
        if contains(kw):
            score += pts
            reasons.append(f"+{pts} {kw}")

    # Price scoring - cheap = higher score for land
    if price > 0:
        if price < 20000:
            score += 4
            reasons.append("+4 under $20k (cheap land)")
        elif price < 50000:
            score += 3
            reasons.append("+3 under $50k")
        elif price < 100000:
            score += 2
            reasons.append("+2 under $100k")
        elif price < 200000:
            score += 1
            reasons.append("+1 under $200k")

    # Source bonus
    if source_type == "tax_defaulted":
        score += 4
        reasons.append("+4 tax-defaulted")
    elif source_type == "nod":
        score += 4
        reasons.append("+4 pre-foreclosure NOD")
    elif source_type == "probate":
        score += 3
        reasons.append("+3 probate/inherited")
    elif source_type == "code_violation":
        score += 3
        reasons.append("+3 code violation/vacant")
    elif source_type == "fsbo":
        score += 2
        reasons.append("+2 FSBO")
    elif source_type == "absentee":
        score += 3
        reasons.append("+3 absentee owner")

    # Acreage bonus
    if "acre" in text:
        score += 1
        reasons.append("+1 acreage")

    # Cap at 10
    score = min(score, 10)
    
    # Determine motivation
    motivation = "unknown"
    if any(contains(k) for k in ["tax", "delinquent"]):
        motivation = "tax delinquent"
    elif any(contains(k) for k in ["nod", "default", "foreclosure", "behind"]):
        motivation = "pre-foreclosure"
    elif any(contains(k) for k in ["probate", "estate", "inherited", "trust sale"]):
        motivation = "probate/inherited"
    elif any(contains(k) for k in ["divorce"]):
        motivation = "divorce"
    elif any(contains(k) for k in ["absentee", "out of state", "tired landlord", "tenant"]):
        motivation = "tired landlord/absentee"
    elif any(contains(k) for k in ["vacant", "abandoned", "code"]):
        motivation = "vacant/distressed"
    elif any(contains(k) for k in ["fsbo", "by owner", "private sale", "no mls"]):
        motivation = "private seller / FSBO"
    elif any(contains(k) for k in ["as-is", "needs work", "tlc", "fixer"]):
        motivation = "distressed / as-is"

    return score, ", ".join(reasons), motivation
