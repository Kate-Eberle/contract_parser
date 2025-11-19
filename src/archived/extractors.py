# src/extractors_enhanced.py

"""
Extraction module for Contract Parsing Version 3.2.5.
Extracts exactly what's needed for the 12-column (+11 spacer) CSV format.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .archived.config import (
    ADMIN_FEE_PATTERNS,
    SERVICE_SECTION_HEADINGS,
    PASS_THROUGH_KEYWORDS,
    ENTITY_SERVICES,
    SERVICES_NEGATIVE_FILTERS,
    format_date
)

# ==============================================================================
# DATE EXTRACTION
# ==============================================================================

def extract_effective_date(text: str) -> str:
    """
    Extract effective date following spec rules:
    1. First paragraph of body
    2. Dedicated "Effective Date" section  
    3. Signature block
    Never from filename.
    """
    # Common date patterns
    date_patterns = [
        r'(?:effective|commencement)\s+date[:\s]+(?:is\s+)?([^,\n]+)',
        r'(?:effective|commencing)\s+(?:as\s+of|on)\s+([^,\n]+)',
        r'(?:dated?|entered\s+into)\s+(?:as\s+of|this)\s+([^,\n]+)',
        r'made\s+and\s+entered\s+into\s+as\s+of\s+([^,\n]+)'
    ]
    
    # Search first 2000 chars (first paragraph area)
    search_text = text[:2000] if len(text) > 2000 else text
    
    for pattern in date_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            # Parse and normalize the date
            normalized = normalize_date(date_str)
            if normalized != "Unknown":
                return normalized
    
    # Try to find any date in first paragraph
    generic_date = find_first_date(search_text)
    if generic_date:
        return generic_date
    
    return "Unknown"


def normalize_date(date_str: str) -> str:
    """
    Normalize date to spec format:
    Full: YYYY-MM-DD
    Partial: YYYY-MM-DD=Unknown or YYYY-MM=Unknown-DD=Unknown
    """
    import dateutil.parser
    
    # Clean the string
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    date_str = date_str.strip(' .,')
    
    try:
        parsed = dateutil.parser.parse(date_str, fuzzy=False)
        return f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"
    except:
        # Try to extract year at minimum
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            if 1990 <= year <= 2050:  # Reasonable range
                # Check for month
                month_match = re.search(
                    r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
                    date_str, re.IGNORECASE
                )
                if month_match:
                    months = {
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                    }
                    month = months[month_match.group(1)[:3].lower()]
                    return format_date(year, month)
                return format_date(year)
    
    return "Unknown"


def find_first_date(text: str) -> Optional[str]:
    """Find and return the first reasonable date in text."""
    # Common date patterns
    patterns = [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',  # MM/DD/YYYY
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',  # YYYY-MM-DD
        r'\b([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b',  # Month DD, YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return normalize_date(match.group(1))
    
    return None


# ==============================================================================
# ADMIN/SERVICE FEE EXTRACTION
# ==============================================================================

def extract_admin_fee(text: str) -> str:
    """
    Extract admin/service fee per spec:
    - Administrative/GPO/Data/Service fee
    - % of WAC/Net or $/claim or $/month
    - NOT rebates, discounts, chargebacks
    """
    # Look for fee percentages
    for pattern in ADMIN_FEE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Format the fee
            if '%' in pattern or 'percent' in pattern:
                value = match.group(1)
                # Check context for fee type
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                
                if 'data' in context.lower():
                    if 'admin' in context.lower():
                        return f"{value}% WAC + Data Fee"
                    return f"{value}% WAC Data"
                else:
                    return f"{value}% WAC"
            
            elif '$' in pattern:
                value = match.group(1)
                unit = "claim" if "claim" in text[match.start():match.end()+20].lower() else "month"
                return f"${value}/{unit}"
    
    # Check for flat percentages without WAC
    simple_pattern = r'(?:admin(?:istrative)?|service|data)\s+fee[:\s]+(\d+(?:\.\d+)?)\s*%'
    match = re.search(simple_pattern, text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}%"
    
    return ""  # Empty for Unknown per spec


# ==============================================================================
# SERVICES EXTRACTION
# ==============================================================================

def extract_services(text: str, has_fee: bool, entity_type: str = None) -> Tuple[str, str]:
    """
    Extract services per spec with hard gate.
    Returns: (services_text, page_numbers)
    
    Gate: Only if admin fee is present.
    Source: Only from explicit services sections.
    Format: ADMIN: [phrases]; DATA: [phrases]
    Max 7 phrases per bracket, each ≤ 5 words.
    """
    if not has_fee:
        return "", ""
    
    services_admin = []
    services_data = []
    page_refs = []
    
    # Find services sections
    for heading in SERVICE_SECTION_HEADINGS:
        pattern = rf'(?:^|\n)\s*(?:\d+\.?\s*)?{re.escape(heading)}[:\s]*\n'
        matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
        
        for match in matches:
            # Get section content (up to next section or 1500 chars)
            start = match.end()
            end = min(start + 1500, len(text))
            section_text = text[start:end]
            
            # Check for negative filters
            if any(neg in section_text.lower() for neg in SERVICES_NEGATIVE_FILTERS):
                continue
            
            # Determine if admin or data services
            is_data = 'data' in heading.lower() or 'data service' in section_text[:200].lower()
            
            # Extract service items (bullets or numbered)
            items = extract_service_items(section_text, entity_type)
            
            if items:
                if is_data:
                    services_data.extend(items[:7])  # Max 7 per spec
                else:
                    services_admin.extend(items[:7])
                
                # Track page (simplified - would need actual page mapping)
                page = find_page_number(text, match.start())
                if page:
                    page_refs.append(f"{'Data' if is_data else 'Admin'}: p.{page}")
    
    # Format output per spec
    result_parts = []
    if services_admin:
        admin_str = '; '.join(services_admin[:7])
        result_parts.append(f"ADMIN: [{admin_str}]")
    if services_data:
        data_str = '; '.join(services_data[:7])
        result_parts.append(f"DATA: [{data_str}]")
    
    services_text = '; '.join(result_parts) if result_parts else ""
    page_str = '; '.join(page_refs) if page_refs else ""
    
    return services_text, page_str


def extract_service_items(text: str, entity_type: str = None) -> List[str]:
    """
    Extract individual service items from text.
    Returns list of short phrases (≤ 5 words each).
    """
    items = []
    
    # Try bullet points first
    bullet_pattern = r'[•·\-\*]\s*([^•·\-\*\n]+)'
    bullets = re.findall(bullet_pattern, text)
    
    if not bullets:
        # Try numbered list
        bullets = re.findall(r'\d+\.\s*([^0-9\n]+)', text)
    
    # Process and shorten items
    for item in bullets[:15]:  # Process more than 7 to have options
        # Clean and shorten
        clean = item.strip().rstrip('.,;')
        # Take first 5 words
        words = clean.split()[:5]
        short = ' '.join(words)
        
        # Check if relevant to entity type
        if entity_type and entity_type in ENTITY_SERVICES:
            keywords = ENTITY_SERVICES[entity_type]
            if any(kw in short.lower() for kw in keywords):
                items.append(short)
        elif len(short) > 3:  # Generic acceptance if no entity type
            items.append(short)
    
    return items


# ==============================================================================
# PASS-THROUGH LANGUAGE
# ==============================================================================

def extract_pass_through(text: str) -> str:
    """
    Extract pass-through language per spec.
    Must be fee-sharing/price-concession language.
    Format: page + quote or 'None'
    """
    for keyword in PASS_THROUGH_KEYWORDS:
        pattern = rf'([^.]*{re.escape(keyword)}[^.]*\.)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            quote = match.group(1).strip()
            # Clean encoding issues
            quote = quote.replace('â€œ', '"').replace('â€', '"')
            quote = quote.replace('â€™', "'").replace('â€"', '-')
            
            # Find page
            page = find_page_number(text, match.start())
            
            # Truncate if needed
            if len(quote) > 150:
                quote = quote[:147] + '...'
            
            return f"p.{page}: {quote}" if page else quote
    
    return "None"


# ==============================================================================
# OTHER EXTRACTIONS
# ==============================================================================

def extract_termination_date(text: str) -> str:
    """Extract termination date per spec."""
    patterns = [
        r'(?:terminat|expir)[^.]*?(?:on|through|until)\s+([^,\n.]+\d{4})',
        r'(?:agreement|contract)\s+(?:term|period)[^.]*?(?:through|until)\s+([^,\n.]+\d{4})',
        r'initial\s+term[^.]*?(?:of\s+)?(\d+)\s+year',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if 'year' in pattern:
                # Calculate from effective date if available
                return f"{match.group(1)} year term"
            else:
                return normalize_date(match.group(1))
    
    return "Unknown"


def extract_relevant_product(text: str) -> str:
    """Extract relevant products per spec."""
    # Look for product tables/schedules
    patterns = [
        r'(?:schedule|exhibit|appendix)\s+[a-z0-9]+[:\s]*products?([^.]+)',
        r'products?\s+covered[:\s]+([^.\n]+)',
        r'(?:includes?|covers?)\s+(?:the\s+)?(?:following\s+)?products?[:\s]+([^.\n]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            products = match.group(1).strip()
            # Clean up
            products = re.sub(r'\s+', ' ', products)
            if len(products) > 100:
                products = products[:97] + '...'
            return products
    
    # Look for specific drug names
    drug_pattern = r'\b([A-Z][a-z]+(?:mab|nib|tide|cept|mus|ase|ine|ate))\b'
    drugs = re.findall(drug_pattern, text)
    if drugs:
        return '; '.join(drugs[:3])  # First 3 drugs
    
    return "N/A"


def detect_duplicate(text: str, other_texts: List[str]) -> str:
    """
    Detect if this is a duplicate contract.
    Returns 'Yes' or 'No'.
    """
    # Simple check - would need more sophisticated comparison
    text_lower = text.lower()[:1000]  # Check first 1000 chars
    
    for other in other_texts:
        other_lower = other.lower()[:1000]
        # Check similarity (simplified)
        if text_lower == other_lower:
            return "Yes"
    
    return "No"


def extract_modifications(text: str) -> str:
    """
    Extract modifications for amendments.
    State the delta precisely.
    """
    if 'amendment' not in text[:500].lower():
        return "N/A"
    
    patterns = [
        r'section\s+([IVX\d]+)\s+(?:is\s+)?(?:replaced|amended|modified)',
        r'(?:replace|amend|modify)\s+section\s+([IVX\d]+)',
        r'(?:add|insert)\s+(?:new\s+)?section\s+([IVX\d]+)',
    ]
    
    modifications = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            section = match.group(1)
            # Look for what changed
            context = text[match.start():match.end()+200]
            if 'fee' in context.lower():
                fee_match = re.search(r'(\d+(?:\.\d+)?)\s*%', context)
                if fee_match:
                    modifications.append(f"Section {section} replaced; Admin Fee {fee_match.group(1)}% WAC")
            else:
                modifications.append(f"Section {section} modified")
    
    return '; '.join(modifications) if modifications else "N/A"


# ==============================================================================
# UTILITIES
# ==============================================================================

def find_page_number(text: str, position: int) -> Optional[int]:
    """
    Find approximate page number for a position in text.
    Simplified - would need actual page boundaries.
    """
    # Estimate ~3000 chars per page
    page = (position // 3000) + 1
    return page


def generate_qc_flags(extracted: Dict[str, Any]) -> str:
    """Generate QC flags based on extracted data."""
    flags = []
    
    if extracted.get('effective_date') == 'Unknown':
        flags.append('Ambiguous effective date')
    
    if not extracted.get('admin_fee') and 'nda' not in extracted.get('contract_title', '').lower():
        # Don't flag missing fees for NDAs
        pass  # Per spec: Do not flag "Admin/Data fee not found"
    
    if extracted.get('has_fee') and not extracted.get('services'):
        flags.append('Services section not found')
    
    if extracted.get('duplicate') == 'Maybe':
        flags.append('Possible duplicate - review text')
    
    return '; '.join(flags) if flags else ""


# ==============================================================================
# MAIN EXTRACTION FUNCTION
# ==============================================================================

def extract_all_fields(pages: List[Dict[str, Any]], 
                       filename: str = "",
                       entity_type: str = None,
                       other_contracts: List[str] = None) -> Dict[str, Any]:
    """
    Extract all fields for one contract per spec.
    
    Args:
        pages: List of page dictionaries with 'text' field
        filename: Original filename for Contract Title
        entity_type: One of [PBM, SP, WHSL, SD, GPO, 3PL/HUB]
        other_contracts: Other contract texts for duplicate detection
    
    Returns:
        Dictionary with all extracted fields
    """
    # Combine all text
    full_text = '\n'.join(page.get('text', '') for page in pages)
    
    # Extract all fields
    effective_date = extract_effective_date(full_text)
    admin_fee = extract_admin_fee(full_text)
    has_fee = bool(admin_fee)
    
    services, services_pages = extract_services(full_text, has_fee, entity_type)
    pass_through = extract_pass_through(full_text)
    termination_date = extract_termination_date(full_text)
    relevant_product = extract_relevant_product(full_text)
    modifications = extract_modifications(full_text)
    
    # Duplicate detection
    duplicate = "No"
    if other_contracts:
        duplicate = detect_duplicate(full_text, other_contracts)
    
    # Build result
    result = {
        'ref': 0,  # Will be assigned after sorting
        'effective_date': effective_date,
        'contract_title': filename or "Unknown",
        'admin_fee': admin_fee or "Unknown",
        'services': services,
        'duplicate': duplicate,
        'modifications': modifications,
        'qc_flags': "",  # Generated after
        'services_pg_number': services_pages,
        'termination_date': termination_date,
        'pass_through_language': pass_through,
        'relevant_product': relevant_product,
        
        # Metadata
        'has_fee': has_fee,
        'page_count': len(pages),
        'entity_type': entity_type or ""
    }
    
    # Generate QC flags
    result['qc_flags'] = generate_qc_flags(result)
    
    return result


if __name__ == "__main__":
    # Test extraction
    sample = """
    DISTRIBUTION SERVICES AGREEMENT
    
    This Agreement is effective as of January 1, 2024 between
    Manufacturer and Express Scripts (PBM).
    
    3. Administrative Fee: PBM receives 2.5% of WAC.
    
    4. Administrative Services:
    • Rebate calculations  
    • Eligibility checks
    • Utilization reporting
    • Invoice support
    
    GPO may share Administrative Fees with Members.
    
    Agreement terminates December 31, 2025.
    """
    
    pages = [{'text': sample}]
    result = extract_all_fields(pages, "test_agreement.pdf", "PBM")
    
    print("Extracted fields:")
    for key, value in result.items():
        if key != 'has_fee':  # Skip internal field
            print(f"  {key}: {value}")

def build_record(ref, filename, pages, title_guess, entity_type=None):
    '''Build a record for pipeline compatibility.'''
    # The pages are already in the right format from parsers_pdf
    # They're a list of dicts with 'page' and 'text' keys
    
    # Just pass them directly to extract_all_fields
    result = extract_all_fields(pages, filename, entity_type)
    
    # Add ref number
    result['ref'] = ref
    result['title_guess'] = title_guess
    
    return result

