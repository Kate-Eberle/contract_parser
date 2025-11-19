# src/config_enhanced.py
"""
Configuration for pharma contract parser.
Based on Contract Parsing Version 3.2.5 specification.
"""

from pathlib import Path

# ==============================================================================
# PATHS
# ==============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_IN = PROJECT_ROOT / "data_in"
DATA_OUT = PROJECT_ROOT / "data_out"
CACHE_DIR = DATA_OUT / "cache"
PREVIEW_DIR = DATA_OUT / "preview"
OUTPUT_CSV = DATA_OUT / "contracts.csv"

# Phase 4: DOCX to PDF conversion
DOCX_AS_PDF_DIR = DATA_OUT / "docx_as_pdf"
DOCX_TO_PDF_ENABLED = False  # Set True when MS Word is available

# ==============================================================================
# CACHE SETTINGS
# ==============================================================================

CACHE_VERSION = "v0.4.0"  # Bump when extraction logic changes
CACHE_MAX_AGE_DAYS = 30

# ==============================================================================
# CSV OUTPUT SCHEMA - CORRECT VERSION 3.2.5
# ==============================================================================

# The actual column names (without spacers)
DATA_COLUMNS = [
    'Ref',
    'Effective Date',
    'Contract Title', 
    'Admin / Service Fee',
    'Services',
    'Duplicate',
    'Modifications',
    'QC Flags',
    'Services Pg Number',
    'Termination Date',
    'Pass-Through Language (page + quote or None)',
    'Relevant Product'
]

# Full CSV structure with spacer columns (23 total)
CSV_COLUMNS = []
for i, col in enumerate(DATA_COLUMNS):
    CSV_COLUMNS.append(col)
    if i < len(DATA_COLUMNS) - 1:  # Add spacer after each column except last
        CSV_COLUMNS.append('')

# This gives us exactly 23 columns: 12 data + 11 spacers
NUM_COLUMNS = 23
HEADER = '"' + '","'.join(CSV_COLUMNS) + '"'

# ==============================================================================
# ENTITY TYPE (User-supplied for batch)
# ==============================================================================

VALID_ENTITY_TYPES = ['PBM', 'SP', 'WHSL', 'SD', 'GPO', '3PL/HUB']

# ==============================================================================
# EXTRACTION PATTERNS
# ==============================================================================

# Admin/Service Fee patterns (from spec)
ADMIN_FEE_PATTERNS = [
    r'(?:administrative|admin|gpo|data|service)\s+fee[^.]*?(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:of\s+)?(?:WAC|Net)',
    r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:of\s+)?WAC\s*(?:admin|administrative|service|data)\s*fee',
    r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*per\s+(?:claim|script|month)',
]

# Services section headings (from spec)
SERVICE_SECTION_HEADINGS = [
    'administrative services',
    'GPO Administrative Services',
    'PBM Administrative Services'
    'SD Administrative Services', 
    'SP Administrative Services', 
    '3PL/HUB Administrative Services',
    'WHSL Administrative Services',
    'data services', 
    'scope of services',
    'distribution services',
    'services',
    'exhibit',
    'attachment',
    'services provided',
    'distributor services',
    'performance obligations'
]

# Pass-through keywords (from spec)
PASS_THROUGH_KEYWORDS = [
    "share Administrative Fees", "price concession", "treated as a price concession",
    "point-of-sale price reduction", "POS price reduction", "remit", "share all or some of", "remitted fee", "share administrative fee", 
    "may share", "remit", "pass-through", "pass-through",  "GPO's agreements with its GPO Members may require GPO to share",
    "require GPO to share some or all of the GPO Fees",
    "GPO Administrative Fee is remitted",
    "share some or all of the Administrative fees",
    'share administrative fees',
    'price concession',
    'treated as a price concession',
    'point-of-sale price reduction',
    'pos price reduction',
    'remit',
    'share all or some of',
    'remitted fee',
    'may share',
    'pass-through',
    'pass through',
    'gpo to share',
    'safe harbor'
    
]

# Services by entity type (from spec appendix)
ENTITY_SERVICES = {
    'SP': [
        # Program Setup & Implementation
        'start up services', 'program setup', 'it setup', 'implementation', 'onboarding',
        # Dispensing & Pharmacy Operations
        'dispense fee', 'pharmacy dispensing', 'pap dispensing', 'free goods dispensing',
        'prescription fulfillment', 'inventory management',
        # Program Management
        'program management', 'program manager', 'dedicated liaison', 'manufacturer liaison',
        # Data & Reporting
        'data reporting', 'enhanced data', 'dispense reporting', 'status reporting',
        'inventory reporting', 'kpi reporting', 'ad hoc reporting',
        # AE & Product Complaints
        'ae reporting', 'adverse event', 'product complaint', 'pqc reconciliation',
        # Patient Support & Case Management
        'case manager', 'case management', 'adherence programs', 'patient education',
        'nurse support', 'pharmacist support',
        # Hub Collaboration
        'hub collaboration', 'triage to hub', 'warm transfers',
        # PAP/Bridge/Copay
        'pap product', 'copay assistance', 'bridge program', 'patient assistance',
        # Returns
        'returns', 'recalls', 'lost product', 'shipment replacement'
    ],
    
    'SD': [
        # Inventory Management
        'inventory management', 'product intake', 'reconciliation', 'pipeline management',
        # Order Management
        'order management', 'emergency orders', 'drop ship', 'order fulfillment',
        'routine orders', '24/7 orders',
        # Pick Pack Ship
        'pick pack ship', 'packing', 'shipment', 'temperature controlled',
        'next day delivery',
        # AR Management
        'ar management', 'accounts receivable', 'credit billing', 'invoicing',
        'collections',
        # Contracts & Chargebacks
        'contracts administration', 'chargeback admin', 'chargeback processing',
        # Data & Reporting
        'data reporting', 'edi 852', 'edi 867', 'demand planning',
        'inventory data', 'sales data',
        # Returns
        'returns management', 'product returns', 'destruction',
        # Customer Service
        'customer service', 'customer support',
        # Compliance
        'compliance', 'audit', 'inspection'
    ],
    
    'WHSL': [
        # Contract & Chargeback
        'contracts administration', 'chargeback admin', 'chargeback processing',
        # Inventory
        'inventory management', 'stock product', 'maintain inventory', 'storage conditions',
        # Order Fulfillment
        'pick pack ship', 'emergency shipments', 'order fulfillment',
        # Returns
        'returns management', 'returns processing', 'recalls',
        # Data Reporting
        'data reporting', 'edi 852', 'edi 867', 'pipeline data',
        # AR/Billing
        'credit billing', 'ar management', 'accounts receivable',
        # Customer Service
        'customer service', 'customer support',
        # Compliance
        'legal compliance', 'record maintenance', 'audit support'
    ],
    
    'GPO': [
        # Contract Admin
        'maintain agreements', 'manage agreements', 'contract summary', 'contract summaries',
        # Membership
        'membership list', 'member onboarding', 'member offboarding', 'provide membership',
        # Rebate Program
        'administer rebate', 'rebate program', 'off invoice', 'discount admin',
        # Member Communication
        'member communication', 'contract changes', 'product availability',
        # Performance Tracking
        'track performance', 'member performance', 'purchase data', 'member purchase',
        # Business Reviews
        'business review', 'business reviews', 'qbrs',
        # Compliance
        'monitor compliance', 'compliance obligations', 'safe harbor'
    ],
    
    'PBM': [
        # Rebate Program
        'calculate rebates', 'provide invoice', 'allocate rebates', 'distribute rebates',
        'rebate calc', 'rebate distribution', 'rebate processing',
        # Contracting
        'negotiate contract', 'payor contracting', 'gpo contracting',
        # Utilization Reporting
        'utilization reports', 'utilization reporting', 'data portal', 'portal access',
        # Formulary
        'formulary status', 'formulary management', 'membership list',
        # Compliance
        'rebate payment', 'internal controls', 'eligibility monitoring',
        'compliance monitoring'
    ],
    
    '3PL': [
        # Order Management
        'order placement', 'account management', 'call center', 'order portal',
        # Distribution
        'distribution services', 'warehousing', 'pick pack ship', 'climate controlled',
        'inventory management', 'returns',
        # Sales Support
        'sales support', 'sales rep management', 'training', 'compliance',
        # Insurance & Claims
        'insurance verification', 'claims processing', 'financial reporting',
        # Quality & Compliance
        'quality assurance', 'cgmp program', 'risk management', 'regulatory compliance',
        # Recall & Complaints
        'recalls', 'complaints', 'adverse event', 'product recall'
    ],
    
    'HUB': [
        # Setup/Implementation
        'operations project', 'implementation management', 'system setup', 'configuration',
        'it setup', 'team licensing',
        # Case Management
        'case manager', 'dedicated case', 'nurse case', 'quality specialist',
        # Data & Reporting
        'data feed', 'data aggregation', 'analytics', 'reporting portal',
        'ad hoc reporting', 'variable development',
        # Benefit Investigation
        'electronic bi', 'benefit investigation', 'pharmacy eligibility', 'medical eligibility',
        'prior authorization', 'prescriber license',
        # Patient Support
        'field team portal', 'patient access', 'copay setup', 'accumulator setup',
        # Program Management
        'program management', 'monthly management', 'program manager', 'business reviews'
    ]
}

# Negative filters for services (from spec)
SERVICES_NEGATIVE_FILTERS = [
    'rebate matrices',
    'IPP/inflation tables', 
    'rate schedules',
    'exhibit replacements',
    'audit/validation rights',
    'confidentiality/NDA',
    'general term/renewal',
    'payment timing',
    'invoice mechanics',
    'formulary proof'
]

# ==============================================================================
# DATE FORMATS (from spec)
# ==============================================================================

def format_date(year=None, month=None, day=None):
    """
    Format date according to spec rules:
    - Full: YYYY-MM-DD
    - Year-month only: YYYY-MM-DD=Unknown
    - Year only: YYYY-MM=Unknown-DD=Unknown
    """
    if year and month and day:
        return f"{year:04d}-{month:02d}-{day:02d}"
    elif year and month:
        return f"{year:04d}-{month:02d}-DD=Unknown"
    elif year:
        return f"{year:04d}-MM=Unknown-DD=Unknown"
    else:
        return "Unknown"

# ==============================================================================
# QUALITY CONTROL
# ==============================================================================

QC_FLAGS_ALLOWED = [
    'Ambiguous effective date',
    'Services section not found',
    'Possible duplicate - review text',
    'OCR quality issue on Exhibit',
    'Potential duplicate; manual compare',
    'Inherits termination from prior'
]

# ==============================================================================
# LOGGING
# ==============================================================================

import logging

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(DATA_OUT / 'parser.log', mode='a')
        ]
    )

# ==============================================================================
# DEPENDENCIES CHECK
# ==============================================================================

def check_dependencies():
    """Check if required libraries are installed."""
    required = {
        'PyMuPDF': 'fitz',
        'python-docx': 'docx',
        'docx2python': 'docx2python',
        'dateutil': 'dateutil.parser'
    }
    
    missing = []
    for name, module in required.items():
        try:
            if '.' in module:
                # For submodules like dateutil.parser
                parts = module.split('.')
                mod = __import__(parts[0])
                for part in parts[1:]:
                    mod = getattr(mod, part)
            else:
                __import__(module)
        except (ImportError, AttributeError):
            missing.append(name)
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join([m.lower().replace('pymupdf', 'pymupdf') for m in missing])}")
        return False
    
    return True

if __name__ == "__main__":
    print(f"Config loaded. Project root: {PROJECT_ROOT}")
    print(f"Data input: {DATA_IN}")
    print(f"Data output: {DATA_OUT}")
    print(f"CSV columns: {NUM_COLUMNS} (12 data + 11 spacers)")
    print(f"Header preview: {HEADER[:100]}...")
    
    if check_dependencies():
        print("✓ All dependencies installed")
    else:
        print("✗ Missing dependencies")