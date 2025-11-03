# src/pipeline.py
from __future__ import annotations
from pathlib import Path
import logging
from typing import List
from .config import (
    DATA_IN, DATA_OUT, LOG_DIR, OUTPUT_CSV,
    SKIPPED_LOG, ERROR_LOG, RUN_LOG, ENTITY_TYPES
)
from .parsers_pdf import extract_pdf_pages
from .parsers_docx import extract_docx_pages
from .extractors import build_record
from .qc_validate import as_csv_row, header
from .utils_csv import write_rfc4180_csv

# Setup logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=RUN_LOG,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def _iter_contract_files(root: Path):
    """Recursively find all PDF and DOCX files."""
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in {".pdf", ".docx"}:
            yield p

def run_pipeline(
    input_dir: Path = DATA_IN,
    output_csv: Path = OUTPUT_CSV,
    entity_type: str | None = None
):
    """
    Main pipeline orchestrator.
    
    Steps:
    1. Find all PDF/DOCX files in input_dir
    2. Extract text via Phase 3-4 parsers
    3. Build record via extractors
    4. Convert to CSV row via qc_validate
    5. Write CSV with row-count validation
    6. Write auxiliary logs (skipped, errors)
    """
    # Validate entity type if provided
    if entity_type and entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid ENTITY_TYPE '{entity_type}'. Allowed: {sorted(ENTITY_TYPES)}")

    # Find input files
    files = list(_iter_contract_files(input_dir))
    if not files:
        logging.warning("No input files found.")
        print("WARNING: No PDF or DOCX files found in input directory.")
        return
    
    print(f"Found {len(files)} contract files to process.")
    
    # Initialize output rows with header
    rows: List[List[str]] = [header()]
    
    # Track skipped/errored files
    skipped = []
    errors = []
    
    # Process each file
    ref_counter = 0
    for f in files:
        try:
            ref_counter += 1
            
            # Extract pages based on file type
            if f.suffix.lower() == ".pdf":
                pages_dicts = extract_pdf_pages(str(f))
                pages = [(pg["page"], pg["text"]) for pg in pages_dicts]
                title_guess = f.stem
                
            elif f.suffix.lower() == ".docx":
                # Use Phase 4 bridge (true pagination if enabled)
                pages_dicts = extract_docx_pages(str(f))
                pages = [(pg["page"], pg["text"]) for pg in pages_dicts]
                # Try to get title from first page
                title_guess = pages[0][1][:100].strip() if pages else f.stem
                
            else:
                skipped.append((str(f), "Unsupported extension"))
                continue
            
            # Build record via extractors
            rec = build_record(
                ref=ref_counter,
                filename=f.name,
                pages=pages,
                title_guess=title_guess,
                entity_type=entity_type
            )
            
            # Convert to CSV row
            csv_row = as_csv_row(rec)
            rows.append(csv_row)
            
            logging.info(f"Processed: {f.name}")
            print(f"  [{ref_counter}/{len(files)}] {f.name}")
            
        except Exception as e:
            errors.append((str(f), repr(e)))
            logging.exception(f"Error processing {f.name}: {e}")
            print(f"  [ERROR] {f.name}: {e}")
    
    # ROW COUNT VALIDATION (critical requirement)
    produced_rows = len(rows) - 1  # Exclude header
    expected_rows = len([f for f in files if f.suffix.lower() in {".pdf", ".docx"}])
    
    if produced_rows != expected_rows:
        msg = f"ERROR: ROW COUNT MISMATCH — expected {expected_rows} rows, produced {produced_rows}."
        logging.error(msg)
        _write_aux_logs(skipped, errors)
        raise SystemExit(msg)
    
    # Write CSV
    write_rfc4180_csv(output_csv, rows)
    
    # Write auxiliary logs
    _write_aux_logs(skipped, errors)
    
    print(f"\n✅ Done. Wrote: {output_csv} (rows={produced_rows})")
    if errors:
        print(f"⚠️  {len(errors)} files had errors (see {ERROR_LOG})")
    if skipped:
        print(f"⚠️  {len(skipped)} files skipped (see {SKIPPED_LOG})")

def _write_aux_logs(skipped, errors):
    """Write skipped_files.log and errors.log."""
    if skipped:
        Path(SKIPPED_LOG).write_text(
            "\n".join(f"{p}\t{why}" for p, why in skipped),
            encoding="utf-8"
        )
    if errors:
        Path(ERROR_LOG).write_text(
            "\n".join(f"{p}\t{err}" for p, err in errors),
            encoding="utf-8"
        )