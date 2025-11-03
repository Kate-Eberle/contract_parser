# src/extractors.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import re
from .schema import STANDARD_LITERALS as LIT
from .config import SERVICE_SECTION_HEADINGS, PASSTHROUGH_CUES, ENTITY_TYPES
from .utils_text import find_first_date_like, collapse_spaces, semicolon_join_phrases

# Fee patterns for Admin/Service Fee extraction
FEE_PATTERNS = [
    r'\b(\d{1,2}(?:\.\d{1,2})?)\s*%\s*(?:of\s*)?(WAC|Net Sales|Net)\b',
    r'\$\s?\d{1,6}(?:\.\d{2})?\s*/\s?(?:claim|month|script|transaction)\b',
    r'\b(Admin(?:istrative)?|Data)\s*Fee[s]?:?\s*(\d{1,2}(?:\.\d{1,2})?)\s*%\s*WAC\b',
]

# Service item splitter (bullets, dashes, semicolons, newlines)
SERVICES_SPLIT = re.compile(r'[\u2022•\-\–;]\s+|(?:\r?\n)+')

@dataclass
class SectionHit:
    """Represents a found section with heading and text."""
    heading: str
    page_label: str
    text: str

@dataclass
class Extracted:
    """Extracted fields for one contract (maps to CSV row)."""
    ref: str
    effective_date: str
    contract_title: str
    admin_service_fee: str
    services: str
    duplicate: str
    modifications: str
    qc_flags: List[str] = field(default_factory=list)
    services_pg: str = ""
    termination_date: str = ""
    passthrough: str = ""
    relevant_product: str = ""

def _page_label(n: int) -> str:
    """Format page number as 'p.N'."""
    return f"p.{n}"

def _search_sections(pages: List[Tuple[int, str]], headings: List[str]) -> List[SectionHit]:
    """
    Search for service section headings across all pages.
    Returns list of SectionHit with heading, page label, and text snippet.
    """
    hits: List[SectionHit] = []
    for pnum, text in pages:
        for h in headings:
            if re.search(re.escape(h), text, re.IGNORECASE):
                match = re.search(re.escape(h), text, re.IGNORECASE)
                idx = match.start()
                snippet = text[idx: idx + 3000]  # Extract ~3000 chars after heading
                hits.append(SectionHit(heading=h, page_label=_page_label(pnum), text=snippet))
    return hits

def _extract_effective_date(pages: List[Tuple[int, str]], qc: List[str]) -> str:
    """
    Extract effective date. Search order:
    1. First page (first 3000 chars)
    2. Last page (signature block area)
    If ambiguous, add QC flag and return Unknown.
    """
    # Try first page
    for pnum, text in pages[:1]:
        d = find_first_date_like(text[:3000])
        if d:
            return d
    
    # Try last page (signature area)
    if pages:
        d = find_first_date_like(pages[-1][1])
        if d:
            return d
    
    qc.append("Ambiguous effective date")
    return LIT["UNKNOWN"]

def _extract_title(filename: str, title_guess: str) -> str:
    """Use filename if available, else document heading, else Unknown."""
    return filename if filename else (title_guess or LIT["UNKNOWN"])

def _extract_fees(full_text: str) -> str:
    """
    Extract Admin/Service/Data fees only (not rebates/discounts).
    Returns formatted string like '3.0% WAC' or '3.0% WAC + 2.0% WAC Data'.
    """
    matches: List[str] = []
    for pat in FEE_PATTERNS:
        for m in re.finditer(pat, full_text, re.IGNORECASE):
            matches.append(collapse_spaces(m.group(0)))
    
    # Deduplicate while preserving order
    uniq = list(dict.fromkeys(matches))
    return " + ".join(uniq) if uniq else ""

def _extract_services(section_hits: List[SectionHit], has_fee: bool) -> Tuple[str, str, List[str]]:
    """
    Extract services from explicit service sections.
    Hard gate: only populate if has_fee is True.
    Returns: (services_text, page_numbers, qc_flags)
    """
    qc: List[str] = []
    
    # Gate: no services without fees
    if not has_fee:
        return "", "", qc
    
    if not section_hits:
        qc.append("Services section not found")
        return "", "", qc
    
    admin_phrases: List[str] = []
    data_phrases: List[str] = []
    page_labels: List[str] = []
    
    for hit in section_hits:
        page_labels.append(hit.page_label)
        raw = hit.text
        
        # Split on bullets, dashes, semicolons, newlines
        items = [s.strip() for s in SERVICES_SPLIT.split(raw) if s.strip()]
        
        # Categorize by heading type
        if re.search(r'\bData\b', hit.heading, re.IGNORECASE):
            data_phrases.extend(items)
        elif re.search(r'\bAdmin|Administrative\b', hit.heading, re.IGNORECASE):
            admin_phrases.extend(items)
        else:
            admin_phrases.extend(items)  # Default to admin
    
    # Format with semicolons (max 7 phrases per category, 5 words each)
    admin_fmt = semicolon_join_phrases(admin_phrases[:7])
    data_fmt = semicolon_join_phrases(data_phrases[:7])
    
    # Combine into single field
    if admin_fmt and data_fmt:
        out = f"ADMIN: [{admin_fmt}]; DATA: [{data_fmt}]"
    elif admin_fmt:
        out = f"ADMIN: [{admin_fmt}]"
    elif data_fmt:
        out = f"DATA: [{data_fmt}]"
    else:
        out = ""
        qc.append("Services text could not be summarized")
    
    pages = "; ".join(sorted(set(page_labels)))
    return out, pages, qc

def _extract_modifications(full_text: str, is_amendment_guess: bool) -> str:
    """
    For amendments: extract section replacement details.
    For base agreements: return N/A.
    """
    if not is_amendment_guess:
        return LIT["NA"]
    
    candidates = []
    patterns = [
        r"Section\s+[IVXLC]+(?:\s+[\w\-]+)?\s+(?:replaced|amended|added)",
        r"Attachment\s+[A-Z]\-?\d?\s+(?:replaced|amended)"
    ]
    
    for pat in patterns:
        for m in re.finditer(pat, full_text, re.IGNORECASE):
            candidates.append(m.group(0))
    
    return "; ".join(candidates) if candidates else "Amendment detected; details unspecified"

def _extract_termination(full_text: str) -> str:
    """
    Extract termination date if explicitly stated.
    Returns normalized date or Unknown.
    """
    m = re.search(
        r'\bterminat(?:ion|e|es)\b[^\n]{0,120}?(\b(?:\w+\s+\d{1,2},\s*)?\d{4}\b)',
        full_text,
        re.IGNORECASE
    )
    if not m:
        return LIT["UNKNOWN"]
    
    from .utils_text import normalize_date
    d = normalize_date(m.group(1))
    return d or LIT["UNKNOWN"]

def _extract_passthrough(pages: List[Tuple[int, str]]) -> str:
    """
    Search for pass-through/price concession language.
    Returns 'p.N: quote' or 'None'.
    """
    for pnum, text in pages:
        for cue in PASSTHROUGH_CUES:
            if cue.lower() in text.lower():
                lines = text.splitlines()
                for ln in lines:
                    if cue.lower() in ln.lower():
                        quote = ln.strip()
                        return f"{_page_label(pnum)}: {quote}"
    return LIT["NONE"]

def _extract_products(full_text: str) -> str:
    """
    Extract relevant product mentions.
    Returns semicolon-separated list or N/A.
    """
    m = re.search(r'(Covered Products?|Products?)[\s:]*\n([\s\S]{0,1000})', full_text, re.IGNORECASE)
    if not m:
        return LIT["NA"]
    
    lines = [l.strip(" •-\t") for l in m.group(2).splitlines() if l.strip()]
    return "; ".join(lines[:10]) if lines else LIT["NA"]

def guess_amendment(filename: str, text0: str) -> bool:
    """
    Heuristic to detect if document is an amendment.
    Checks filename and first page text.
    """
    if re.search(r'\bAmendment|Amended|Addendum|Modification\b', filename, re.IGNORECASE):
        return True
    if re.search(r'\bAmendment|Addendum|Modification\b', text0, re.IGNORECASE):
        return True
    return False

def build_record(
    ref: int,
    filename: str,
    pages: List[Tuple[int, str]],
    title_guess: str,
    entity_type: Optional[str] = None
) -> Extracted:
    """
    Main extraction orchestrator.
    Takes raw page text, returns Extracted dataclass with all fields.
    """
    qc: List[str] = []
    
    # Merge all page text for full-document searches
    full_text = "\n".join(t for _, t in pages)
    
    # Extract each field
    eff = _extract_effective_date(pages, qc)
    title = _extract_title(filename, title_guess)
    fee = _extract_fees(full_text)
    has_fee = bool(fee.strip())
    
    # Services (gated on fee presence)
    sect_hits = _search_sections(pages, SERVICE_SECTION_HEADINGS)
    services, services_pg, qc2 = _extract_services(sect_hits, has_fee)
    qc.extend(qc2)
    
    # Other fields
    duplicate = LIT["DUP_NO"]  # TODO: Phase 10 duplicate detection
    mods = _extract_modifications(full_text, guess_amendment(filename, pages[0][1] if pages else ""))
    term = _extract_termination(full_text)
    passthrough = _extract_passthrough(pages)
    products = _extract_products(full_text)
    
    return Extracted(
        ref=str(ref),
        effective_date=eff,
        contract_title=title,
        admin_service_fee=fee,
        services=services,
        duplicate=duplicate,
        modifications=mods,
        qc_flags=qc,
        services_pg=services_pg,
        termination_date=term,
        passthrough=passthrough,
        relevant_product=products
    )