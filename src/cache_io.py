# src/cache_io.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import json
from datetime import datetime, timezone

from .config import TEXT_CACHE_DIR, TEXT_MD_DIR

def compute_sha256(path: Path | str, chunk_size: int = 1 << 20) -> str:
    """Return SHA256 of a binary file."""
    h = hashlib.sha256()
    p = Path(path)
    with p.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def cache_stem_for(source_path: Path, sha256: str) -> str:
    """Make a stable filename stem using the source stem + short hash."""
    short = sha256[:8]
    return f"{source_path.stem}__{short}"

def save_jsonl_cache(
    source_path: Path | str,
    doc_type: str,
    pages: List[Dict],                # [{"page": int, "text": str, "ocr_used": Optional[bool]}]
    engine_meta: Dict[str, str] | None = None,
    sha256: Optional[str] = None,
) -> Path:
    """
    Write a JSONL file where EACH LINE is one page record:
    {"source_path": "...", "source_sha256": "...", "doc_type": "...",
     "page": 1, "text": "...", "ocr_used": false, "extracted_at": "...", "engine": {...}}
    """
    source_path = Path(source_path)
    TEXT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    sha256 = sha256 or compute_sha256(source_path)
    stem = cache_stem_for(source_path, sha256)
    out = TEXT_CACHE_DIR / f"{stem}.jsonl"

    ts = datetime.now(timezone.utc).isoformat()
    engine_meta = engine_meta or {}

    with out.open("w", encoding="utf-8") as f:
        for p in pages:
            rec = {
                "source_path": str(source_path),
                "source_sha256": sha256,
                "doc_type": doc_type,
                "page": int(p.get("page")),
                "text": (p.get("text") or ""),
                "ocr_used": bool(p.get("ocr_used", False)),
                "extracted_at": ts,
                "engine": engine_meta,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return out

def load_jsonl_cache_if_fresh(source_path: Path | str, expected_sha256: str) -> Optional[Dict]:
    """
    Load a JSONL cache file (one line per page) and reconstruct the previous
    single-object shape:
      {
        "source_path": "...",
        "source_sha256": "...",
        "doc_type": "...",
        "pages": [ {"page":1,"text":"...","ocr_used":false}, ... ],
        "extracted_at": "...",
        "engine": {...}
      }
    Return None if the cache doesn't match this file/sha.
    """
    source_path = Path(source_path)
    stem = cache_stem_for(source_path, expected_sha256)
    cache_file = TEXT_CACHE_DIR / f"{stem}.jsonl"
    if not cache_file.exists():
        return None

    pages: List[Dict] = []
    engine: Dict[str, str] = {}
    doc_type: str = ""
    extracted_at: Optional[str] = None

    with cache_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)

            # hard miss if any line doesn't match
            if obj.get("source_sha256") != expected_sha256 or obj.get("source_path") != str(source_path):
                return None

            # collect fields (same per line)
            engine = obj.get("engine", engine) or engine
            doc_type = obj.get("doc_type", doc_type) or doc_type
            extracted_at = obj.get("extracted_at", extracted_at) or extracted_at

            pages.append({
                "page": obj.get("page"),
                "text": obj.get("text") or "",
                "ocr_used": obj.get("ocr_used", False),
            })

    if not pages:
        return None

    return {
        "source_path": str(source_path),
        "source_sha256": expected_sha256,
        "doc_type": doc_type,
        "pages": pages,
        "extracted_at": extracted_at,
        "engine": engine,
    }



def save_markdown_preview(
    source_path: Path | str,
    pages: List[Dict],
    sha256: str,
    ocr_pages: Optional[List[int]] = None,
    extra_meta: Optional[Dict[str, str]] = None,
) -> Path:
    """
    Write a human-readable Markdown file with per-page sections.
    """
    source_path = Path(source_path)
    TEXT_MD_DIR.mkdir(parents=True, exist_ok=True)
    stem = cache_stem_for(source_path, sha256)
    out = TEXT_MD_DIR / f"{stem}.md"

    ocr_pages = ocr_pages or []
    meta_lines = [
        f"# {source_path.name} (cached)",
        "",
        f"- SHA256: `{sha256}`",
        f"- Pages: {len(pages)}",
        f"- OCR used on: {', '.join(map(str, ocr_pages)) if ocr_pages else 'None'}",
    ]
    if extra_meta:
        for k, v in extra_meta.items():
            meta_lines.append(f"- {k}: {v}")

    body = []
    for p in pages:
        page_no = p.get("page")
        text = (p.get("text") or "").strip()
        tag = " (OCR)" if page_no in ocr_pages else ""
        body.append(f"\n---\n\n## Page {page_no}{tag}\n\n{text}\n")

    out.write_text("\n".join(meta_lines) + "\n" + "".join(body), encoding="utf-8")
    return out
