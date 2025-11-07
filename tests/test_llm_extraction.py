# tests/test_llm_extraction.py
"""
Test LLM-based extraction on a single contract.
This helps us validate prompts before integrating into the pipeline.
"""

import requests
import json
from pathlib import Path
import sys

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers_pdf import extract_pdf_pages


def call_ollama(prompt: str, model: str = "llama3.1:8b") -> str:
    """
    Call Ollama API to get LLM response.
    
    Args:
        prompt: The prompt to send to the LLM
        model: Model to use (default: llama3.1:8b)
    
    Returns:
        LLM response as string
    """
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for deterministic extraction
            "num_predict": 100,  # Limit response length (we just want the field value)
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"ERROR calling Ollama: {e}")
        return ""


def extract_admin_fee_llm(text: str) -> str:
    """
    Extract administrative/service fee using LLM.
    
    Returns format: "X.XX% (Fee Type)" or empty string if not found.
    """
    # Limit text to first 15000 chars to fit in LLM context
    # (Fees are usually in first few pages or attachments)
    text_sample = text[:15000]
    
    prompt = f"""You are a contract analyst. Extract the administrative fee or service fee from this contract text.

IMPORTANT:
- Look for fees labeled as "Administrative Fee", "Service Fee", "GPO Fee", "Data Fee"
- Return ONLY the percentage and fee type
- If you find multiple fees, return the primary administrative fee
- If no fee is found, return "NOT FOUND"

Examples:
- "Administrative Fee: 4.25%" → 4.25% (Admin)
- "GPO Admin Fee of 3.0% of WAC" → 3.0% (GPO Admin)
- "Service Fee of 2.5%" → 2.5% (Service)

Contract text:
{text_sample}

Extract the fee (format: X.XX% (Type) or NOT FOUND):"""

    response = call_ollama(prompt)
    
    # Clean up response
    if "NOT FOUND" in response.upper():
        return ""
    
    return response


def extract_product_llm(text: str) -> str:
    """
    Extract pharmaceutical product name using LLM.
    
    Returns product name or "N/A" if not found.
    """
    # Look in first 10000 chars and last 10000 chars (attachments often at end)
    text_sample = text[:10000] + "\n...\n" + text[-10000:]
    
    prompt = f"""You are a contract analyst. Find the pharmaceutical product name covered by this rebate agreement.

IMPORTANT:
- Look for product names in sections like "Covered Products", "REBATES FOR [PRODUCT]", or product tables
- Return ONLY the product name (typically capitalized, e.g., "Auryxia", "Eliquis")
- Ignore generic terms like "Product", "Products", "Drug"
- If no specific product is named, return "NOT FOUND"

Examples:
- "REBATES FOR AURYXIA" → Auryxia
- "Covered Product: Eliquis" → Eliquis
- Table with "Product | Auryxia" → Auryxia

Contract text:
{text_sample}

Extract the product name (or NOT FOUND):"""

    response = call_ollama(prompt)
    
    # Clean up response
    if "NOT FOUND" in response.upper():
        return "N/A"
    
    # Remove common filler words
    response = response.replace("The product name is", "").replace("Product:", "").strip()
    
    return response


def test_extraction(pdf_path: str):
    """Test LLM extraction on a single PDF."""
    print(f"\n{'='*60}")
    print(f"Testing LLM extraction on: {Path(pdf_path).name}")
    print(f"{'='*60}\n")
    
    # Extract text from PDF
    print("1. Extracting text from PDF...")
    pages = extract_pdf_pages(pdf_path)
    full_text = "\n".join(pg["text"] for pg in pages)
    print(f"   ✓ Extracted {len(pages)} pages, {len(full_text)} chars\n")
    
    # Test admin fee extraction
    print("2. Extracting Admin Fee (this may take 5-10 seconds)...")
    admin_fee = extract_admin_fee_llm(full_text)
    print(f"   Result: {admin_fee if admin_fee else '(not found)'}\n")
    
    # Test product extraction
    print("3. Extracting Product Name (this may take 5-10 seconds)...")
    product = extract_product_llm(full_text)
    print(f"   Result: {product}\n")
    
    print(f"{'='*60}")
    print("SUMMARY:")
    print(f"  Admin Fee: {admin_fee if admin_fee else '❌ Not extracted'}")
    print(f"  Product:   {product if product != 'N/A' else '❌ Not extracted'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Test on the Ascent base agreement (we know this has 4.00% fee and Auryxia)
    test_pdf = "data_in/base_only/FINAL.Akebia.AHS.Rebate Agreement.pdf"
    
    if not Path(test_pdf).exists():
        print(f"ERROR: Test file not found: {test_pdf}")
        print("Please ensure the Ascent agreement is in data_in/base_only/")
        sys.exit(1)
    
    test_extraction(test_pdf)