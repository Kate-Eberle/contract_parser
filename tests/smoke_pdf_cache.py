# tests/smoke_pdf_cache.py
from pathlib import Path
import traceback
from src.parsers_pdf import extract_pdf_pages
from src.cache_io import compute_sha256, save_jsonl_cache, save_markdown_preview
from src.config import PROJECT_ROOT, WRITE_TEXT_CACHE, WRITE_MD_PREVIEW

def main():
    try:
        data_in = PROJECT_ROOT / "data_in"
        print("Using data_in:", data_in)
        pdfs = list(data_in.glob("*.pdf"))
        print("Found PDFs:", [p.name for p in pdfs])
        sample = pdfs[0] if pdfs else None
        if not sample:
            print("No PDF found in data_in. Add a PDF and rerun.")
            return

        print("Extracting:", sample.name)
        pages = extract_pdf_pages(sample)
        print("Page count:", len(pages))
        if pages:
            preview = (pages[0].get("text") or "")[:200].replace("\n", " ")
            print("First 200 chars of page 1:", preview)

        sha = compute_sha256(sample)
        if WRITE_TEXT_CACHE:
            save_jsonl_cache(sample, "pdf", pages, engine_meta={"pdf": "PyMuPDF", "ocr": "Tesseract"}, sha256=sha)
            print("JSONL cache written.")
        if WRITE_MD_PREVIEW:
            save_markdown_preview(sample, pages, sha, ocr_pages=[])
            print("Markdown preview written.")
        print("DONE.")
    except Exception:
        print("ERROR running smoke_pdf_cache:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
