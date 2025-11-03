# src/qc_validate.py
from __future__ import annotations
from typing import List
from .schema import NUM_COMMAS_PER_ROW, NUM_COLUMNS, HEADER
from .utils_csv import row_with_spacers

def validate_row_shape(row: List[str]) -> None:
    """
    Validate that row has exactly NUM_COLUMNS fields.
    Raises ValueError if incorrect.
    """
    if len(row) != NUM_COLUMNS:
        raise ValueError(f"Row has {len(row)} columns, expected {NUM_COLUMNS}.")

def as_csv_row(rec) -> List[str]:
    """
    Convert Extracted dataclass to list of 23 CSV fields (with spacers).
    Returns validated row ready for CSV writing.
    """
    # Join QC flags with semicolons
    qc = "; ".join(sorted(set(rec.qc_flags))) if rec.qc_flags else ""
    
    # 12 data fields (matching CSV column order)
    fields = [
        rec.ref,
        rec.effective_date,
        rec.contract_title,
        rec.admin_service_fee,
        rec.services,
        rec.duplicate,
        rec.modifications,
        qc,
        rec.services_pg,
        rec.termination_date,
        rec.passthrough,
        rec.relevant_product
    ]
    
    # Add spacer columns (alternating pattern)
    row = row_with_spacers(fields)
    
    # Validate before returning
    validate_row_shape(row)
    return row

def header() -> List[str]:
    """Return the standard 23-column header row."""
    return HEADER.copy()