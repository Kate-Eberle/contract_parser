# src/utils_csv.py
import csv
from pathlib import Path
from typing import List
from .schema import HEADER, NUM_COLUMNS

def ensure_crlf(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")

def write_rfc4180_csv(path: Path, rows: List[List[str]]) -> None:
    # Enforce quoting of all non-empty data fields; we’ll construct rows already with quotes/spacers
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
        for row in rows:
            if len(row) != NUM_COLUMNS:
                raise ValueError(f"Row length != {NUM_COLUMNS}")
            w.writerow(row)
    # rewrite to enforce CRLF (defensive)
    content = tmp.read_text(encoding="utf-8")
    tmp.write_text(ensure_crlf(content), encoding="utf-8")
    tmp.replace(path)

def header_row() -> List[str]:
    return HEADER.copy()

def quoted(v: str) -> str:
    # csv.writer will handle double quote escaping; we still want to sanitize CR/LF
    return v.replace("\r", " ").replace("\n", " ").strip()

def row_with_spacers(fields: List[str]) -> List[str]:
    """
    Given the 12 data fields in order:
    [Ref, Effective Date, Contract Title, Admin/Service Fee, Services, Duplicate,
     Modifications, QC Flags, Services Pg Number, Termination Date,
     Pass-Through Language, Relevant Product]
    Return the 23 columns with "" spacers interleaved, except after the last.
    """
    if len(fields) != 12:
        raise ValueError("Expected 12 data fields (without spacers).")
    out = []
    for i, v in enumerate(fields):
        out.append(quoted(v))
        if i != len(fields)-1:
            out.append("")  # spacer
    return out

