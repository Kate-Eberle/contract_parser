from pathlib import Path
from src.cache_io import compute_sha256, save_jsonl_cache, save_markdown_preview
from src.config import PROJECT_ROOT, WRITE_TEXT_CACHE, WRITE_MD_PREVIEW
from src.parsers_docx import render_docx_to_pdf_then_extract

def main():
    din = PROJECT_ROOT / "data_in"
    sample = next((p for p in din.glob("*.docx")), None)
    if not sample:
        print("No DOCX found in data_in. Add a DOCX and rerun.")
        return

    print(f"Extracting DOCX: {sample.name}")
    pages, pdf_path, used_pdf = render_docx_to_pdf_then_extract(sample)
    print(f"Used PDF pipeline: {used_pdf}")
    if pdf_path:
        print(f"Rendered PDF: {pdf_path}")

    print("Page count:", len(pages))
    preview = (pages[0].get("text") or "")[:200].replace("\n", " ")
    print("First 200 chars of p1:", preview)

    sha = compute_sha256(sample)
    if WRITE_TEXT_CACHE:
        save_jsonl_cache(sample, "docx", pages, engine_meta={"docx_mode": "pdf" if used_pdf else "paragraph"}, sha256=sha)
        print("JSONL cache written.")
    if WRITE_MD_PREVIEW:
        save_markdown_preview(sample, pages, sha, ocr_pages=[], extra_meta={"docx_mode": "pdf" if used_pdf else "paragraph"})
        print("Markdown preview written.")
    print("DONE.")

if __name__ == "__main__":
    main()
