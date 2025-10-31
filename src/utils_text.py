# src/utils_text.py
import re
from typing import List, Tuple
from dateutil import parser as dtparser

DATE_RE = re.compile(
    r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|'
    r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|'
    r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2})[^\n]{0,30}?'
    r'(?:\d{1,2},\s*)?\d{4}\b',
    re.IGNORECASE
)

def normalize_date(text: str) -> str | None:
    """
    Try to normalize a human date string to YYYY-MM-DD.
    Returns None if cannot parse.
    """
    try:
        d = dtparser.parse(text, fuzzy=True, dayfirst=False, yearfirst=False)
        return d.strftime("%Y-%m-%d")
    except Exception:
        return None

def find_first_date_like(s: str) -> str | None:
    m = DATE_RE.search(s)
    if not m:
        return None
    return normalize_date(m.group(0))

def collapse_spaces(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()

def semicolon_join_phrases(phrases: List[str], max_count=7, max_words=5) -> str:
    cleaned: List[str] = []
    for p in phrases:
        w = collapse_spaces(p)
        if not w:
            continue
        # Keep to max 5 words
        words = w.split()
        cleaned.append(" ".join(words[:max_words]))
        if len(cleaned) >= max_count:
            break
    return "; ".join(cleaned)

