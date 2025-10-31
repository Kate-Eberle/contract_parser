# Contract Parser

Local, page-true text extraction for pharma contracts.
- **Inputs:** PDF, DOCX
- **Outputs:** JSONL text cache per file (one object with page array) + Markdown preview per page
- **Why:** Deterministic, offline, RFC4180-ready downstream CSV building

## Quick start
```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Smoke tests
python -m tests.smoke_pdf_cache
python -m tests.smoke_docx_cache
