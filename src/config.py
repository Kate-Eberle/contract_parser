# src/config.py
from pathlib import Path

# Folders
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_IN  = PROJECT_ROOT / "data_in"
DATA_OUT = PROJECT_ROOT / "data_out"
LOG_DIR  = PROJECT_ROOT / "logs"

# --- Text cache & preview (additive) ---
TEXT_CACHE_DIR = DATA_OUT / "text_cache"
TEXT_MD_DIR = DATA_OUT / "text_md"

USE_CACHE = True            # Phase 6 will honor this with a "cache-first" check
WRITE_TEXT_CACHE = True     # write JSONL cache after extraction
WRITE_MD_PREVIEW = True     # write a human-readable Markdown preview (optional)


# Output filenames
OUTPUT_CSV = DATA_OUT / "contracts_extracted.csv"
SKIPPED_LOG = LOG_DIR / "skipped_files.log"
ERROR_LOG   = LOG_DIR / "errors.log"
RUN_LOG     = LOG_DIR / "run.log"

# OCR settings (optional)
USE_OCR_FALLBACK = True   # set False if you don't want OCR fallback
TESSERACT_PATH = None     # e.g., r"C:\Program Files\Tesseract-OCR\tesseract.exe" or None to use PATH


# DOCX → PDF rendering (for page-true extraction)
DOCX_TO_PDF_ENABLED = True
DOCX_AS_PDF_DIR     = DATA_OUT / "docx_as_pdf"


# Table inclusion settings
INCLUDE_TABLES_AS_MARKDOWN = True         # append markdown tables to each page's text


# Entity types and keyword domains
ENTITY_TYPES = {"PBM", "SP", "WHSL", "SD", "GPO", "3PL/HUB"}

# Services section title cues (for extraction)
SERVICE_SECTION_HEADINGS = [
    "Administrative Services", "Data Services", "Scope of Services",
    "Distribution Services", "Services", "Exhibit A", "Attachment A"
]

# Keywords for pass-through language
PASSTHROUGH_CUES = [
    "share Administrative Fees", "price concession", "treated as a price concession",
    "point-of-sale price reduction", "POS price reduction"
]
