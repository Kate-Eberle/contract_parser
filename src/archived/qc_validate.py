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
    Convert record to CSV row - handles dict format from extractors.
    """
    # Handle dictionary format (what we're actually getting)
    if isinstance(rec, dict):
        fields = [
            str(rec.get('ref', '')),
            rec.get('effective_date', ''),
            rec.get('contract_title', ''),
            rec.get('admin_fee', ''),
            rec.get('services', ''),
            rec.get('duplicate', ''),
            rec.get('modifications', ''),
            rec.get('qc_flags', ''),
            rec.get('services_pg_number', ''),
            rec.get('termination_date', ''),
            rec.get('pass_through_language', ''),
            rec.get('relevant_product', '')
        ]
    else:
        # Handle object format (old code path)
        fields = [
            str(rec.ref),
            rec.effective_date,
            rec.contract_title,
            rec.admin_service_fee,
            rec.services,
            rec.duplicate,
            rec.modifications,
            rec.qc_flags,
            rec.services_pg,
            rec.termination_date,
            rec.passthrough,
            rec.relevant_product
        ]
    
    # Add spacer columns
    row = row_with_spacers(fields)
    
    # Validate before returning
    validate_row_shape(row)
    return row

def header() -> List[str]:
    """Return the standard 23-column header row.""" 
    return HEADER.copy()