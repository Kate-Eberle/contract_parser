# src/cli.py
import sys
import argparse
from pathlib import Path
from .pipeline import run_pipeline
from .config import DATA_IN, OUTPUT_CSV

def main():
    """CLI entry point for contract parser."""
    ap = argparse.ArgumentParser(
        description="Local Pharma Contract Parser — Extract fields to RFC-4180 CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    ap.add_argument(
        "--in", dest="inp",
        default=str(DATA_IN),
        help="Input folder containing PDFs/DOCX (default: data_in/)"
    )
    
    ap.add_argument(
        "--out", dest="out",
        default=str(OUTPUT_CSV),
        help="Output CSV path (default: data_out/contracts_extracted.csv)"
    )
    
    ap.add_argument(
        "--entity", dest="entity",
        default=None,
        help="ENTITY_TYPE = {PBM|SP|WHSL|SD|GPO|3PL/HUB} (optional, for downstream heuristics)"
    )
    
    args = ap.parse_args()
    
    # Force output to flush immediately
    sys.stdout.reconfigure(line_buffering=True)
    
    try:
        # Run pipeline
        run_pipeline(
            input_dir=Path(args.inp),
            output_csv=Path(args.out),
            entity_type=args.entity
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()