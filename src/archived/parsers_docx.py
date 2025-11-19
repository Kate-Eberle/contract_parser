# src/parsers_docx.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Iterable, Tuple
from pathlib import Path

from docx2python import docx2python
from docx2pdf import convert as docx2pdf_convert

from .parsers_pdf import extract_pdf_pages
from .archived.config import DOCX_TO_PDF_ENABLED, DOCX_AS_PDF_DIR


# ------------------ Paragraph/table-based DOCX parsing ------------------

@dataclass
class DocxPage:
    page_num: int
    text: str

@dataclass
class DOCXParseResult:
    pages: List[DocxPage]
    title_guess: str

def _flatten_4level(nested: Iterable) -> Iterable[str]:
    """
    docx2python returns 4-level nested lists for sections->tables->rows->cells.
    Yield cell text in reading order. Each row becomes: "[TABLE] col1 | col2 | ..."
    """
    for level1 in (nested or []):          # sections
        for level2 in (level1 or []):      # tables in section
            for level3 in (level2 or []):  # rows
                cells = []
                for level4 in (level3 or []):  # cells
                    t = (level4 or "").strip()
                    if t:
                        cells.append(t)
                row = " | ".join(cells).strip()
                if row:
                    yield f"[TABLE] {row}"

def _gather_text_blocks(doc) -> List[str]:
    """
    Collect blocks from headers, body and footers.
    De-duplicate consecutive repeats (common with headers/footers).
    """
    blocks: List[str] = []
    for s in _flatten_4level(doc.header):
        blocks.append(s)
    for s in _flatten_4level(doc.body):
        blocks.append(s)
    for s in _flatten_4level(doc.footer):
        blocks.append(s)

    deduped: List[str] = []
    last = None
    for b in blocks:
        if b and b != last:
            deduped.append(b)
        last = b
    return deduped

def parse_docx(path: str | Path, page_block_size: int = 40) -> DOCXParseResult:
    """
    Convert DOCX into pseudo-pages by grouping blocks (paragraphs + table rows).
    """
    path = str(path)
    with docx2python(path) as doc:
        blocks = _gather_text_blocks(doc)
        title_guess = next((b for b in blocks if b.strip()), "")

        pages: List[DocxPage] = []
        buf: List[str] = []
        n = 0
        for i, block in enumerate(blocks, start=1):
            buf.append(block)
            if i % page_block_size == 0:
                n += 1
                pages.append(DocxPage(page_num=n, text="\n".join(buf)))
                buf = []
        if buf:
            n += 1
            pages.append(DocxPage(page_num=n, text="\n".join(buf)))

    return DOCXParseResult(pages=pages, title_guess=title_guess)


# ------------------ Phase 4: DOCX → PDF bridge (page-true) ------------------

def render_docx_to_pdf_then_extract(path: str | Path) -> Tuple[List[Dict], Path | None, bool]:
    """
    Render DOCX → PDF, then reuse the PDF extractor for true pagination.
    Returns (pages, pdf_path, used_pdf). Falls back to paragraph mode if needed.
    """
    p = Path(path)
    if not DOCX_TO_PDF_ENABLED:
        res = parse_docx(p)
        pages = [{"page": i + 1, "text": dp.text, "ocr_used": False}
                 for i, dp in enumerate(res.pages)]
        return pages, None, False

    try:
        DOCX_AS_PDF_DIR.mkdir(parents=True, exist_ok=True)
        out_pdf = DOCX_AS_PDF_DIR / (p.stem + ".pdf")
        if out_pdf.exists():
            out_pdf.unlink()  # avoid stale content
        docx2pdf_convert(str(p), str(out_pdf))
        pages = extract_pdf_pages(out_pdf)
        # normalize just in case
        for pg in pages:
            pg.setdefault("ocr_used", False)
        return pages, out_pdf, True
    except Exception:
        # Word/Office not available or conversion failed → paragraph fallback
        res = parse_docx(p)
        pages = [{"page": i + 1, "text": dp.text, "ocr_used": False}
                 for i, dp in enumerate(res.pages)]
        return pages, None, False

def extract_docx_pages(path: str | Path) -> List[Dict]:
    """
    Single entry point the rest of the pipeline can call.
    Uses the PDF route when enabled; otherwise paragraph mode.
    """
    pages, _pdf, _used = render_docx_to_pdf_then_extract(path)
    return pages
