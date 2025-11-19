# src/parsers_pdf.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional
import fitz  # PyMuPDF

from .archived.config import INCLUDE_TABLES_AS_MARKDOWN


def _page_text(doc: fitz.Document, i: int) -> str:
    """
    Extract text as a STRING. Prefer the 'text' extractor, but if it's empty,
    join the 'blocks' payload into a string.
    """
    page = doc.load_page(i)

    # 1) Preferred: 'text' returns a single string
    txt = page.get_text("text")
    if isinstance(txt, str) and txt.strip():
        return txt

    # 2) Fallback: 'blocks' returns a list of tuples; join their text parts
    blocks = page.get_text("blocks")
    if isinstance(blocks, list) and blocks:
        try:
            # In PyMuPDF, block tuple format is (x0, y0, x1, y1, "text", block_no, ...)
            joined = "\n".join(b[4] for b in blocks if len(b) > 4 and isinstance(b[4], str))
            if joined.strip():
                return joined
        except Exception:
            pass

    # 3) Last resort: plain 'text' without arg or empty string
    txt2 = page.get_text()  # may return empty string on image-only pages
    return txt2 if isinstance(txt2, str) else ""


def _table_markdown(tbl) -> str:
    """
    Convert a PyMuPDF table object to a markdown string.
    """
    rows = []
    for r in range(tbl.row_count):
        row = [tbl.cell(r, c).text or "" for c in range(tbl.col_count)]
        rows.append("| " + " | ".join(cell.strip().replace("\n", " ") for cell in row) + " |")
    if not rows:
        return ""
    header = rows[0]
    sep = "| " + " | ".join("---" for _ in header.split("|")[1:-1]) + " |"
    return "[TABLE]\n" + "\n".join([rows[0], sep, *rows[1:]])


def extract_pdf_pages(path: Path | str, ocr: Optional[bool] = None) -> List[Dict]:
    """
    Return a list of dicts: [{"page": 1, "text": "...", "ocr_used": False}, ...]
    If INCLUDE_TABLES_AS_MARKDOWN is True, tables are appended as markdown blocks
    directly beneath the page's text.
    """
    p = Path(path)
    pages: List[Dict] = []
    with fitz.open(p) as doc:
        for i in range(doc.page_count):
            text = _page_text(doc, i)
            ocr_used = False

            # --- Table extraction block ---
            if INCLUDE_TABLES_AS_MARKDOWN:
                try:
                    tables = doc.load_page(i).find_tables()
                    if tables and tables.tables:
                        table_blocks = []
                        for t in tables.tables:
                            md = _table_markdown(t)
                            if md:
                                table_blocks.append(md)
                        if table_blocks:
                            text = (text or "") + "\n\n" + "\n\n".join(table_blocks)
                except Exception as e:
                    print(f"[WARN] Table extraction failed on page {i+1}: {e}")
            # --- End table extraction ---

            pages.append({"page": i + 1, "text": text, "ocr_used": ocr_used})
    return pages


def join_pages(pages: List[Dict]) -> str:
    """
    Join page texts into a single string (useful later for heuristics).
    """
    return "\n\n".join((pg.get("text") or "") for pg in pages)
