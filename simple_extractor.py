import fitz
import csv
import re
from pathlib import Path
from pattern_library import ADMIN_FEE_PATTERNS, DATA_FEE_PATTERNS
import pytesseract
from PIL import Image
import io
import json


def load_service_library():
    """Load the service library from JSON file."""
    library_path = Path('config/service_library.json')
    with open(library_path, 'r') as f:
        return json.load(f)


# Load the library ONCE at module level (after function is defined)
SERVICE_LIBRARY = load_service_library()


def match_services(contract_text, entity_type='GPO'):
    """Match services from contract text using service library."""
    
    matched_services = []
    matched_evidence = []
    
    if entity_type not in SERVICE_LIBRARY:
        return "", ""
    
    for service_key, service_data in SERVICE_LIBRARY[entity_type].items():
        for pattern in service_data['variations']:
            match = re.search(pattern, contract_text, re.IGNORECASE | re.DOTALL)
            if match:
                # Capture and CLEAN the snippet
                start = max(0, match.start() - 50)
                end = min(len(contract_text), match.end() + 50)
                snippet = contract_text[start:end]
                
                # CLEAN IT - remove problematic characters
                snippet = snippet.replace('\n', ' ').replace('\r', ' ')
                snippet = snippet.replace('"', "'")  # Replace quotes
                snippet = ' '.join(snippet.split())  # Collapse whitespace
                snippet = snippet[:200]  # Limit length
                
                matched_services.append(service_data['standard_name'])
                matched_evidence.append(f"{service_data['standard_name']}: ...{snippet}...")
                break
    
    return "; ".join(matched_services), "\n\n".join(matched_evidence)


def extract_contract(pdf_path):
    """Extract text from contract, using OCR if needed."""
    doc = fitz.open(str(pdf_path))
    full_text = ""
    
    print(f"     Extracting text from {len(doc)} pages...")

    for page_num, page in enumerate(doc):
        # Try normal text extraction first
        text = page.get_text()

        # If no text found, use OCR
        if len(text.strip()) < 50:  # Likely an image
            print(f"    OCR needed for page {page_num + 1}")
            
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            text = pytesseract.image_to_string(img)
        
        full_text += text
    
    doc.close()
    
    print(f"    📊 Extracting data... (text length: {len(full_text)} chars)")

    # DEBUG: Show snippet around "Administrative Fee"
    if 'administrative fee' in full_text.lower():
        idx = full_text.lower().index('administrative fee')
        snippet = full_text[max(0, idx-50):idx+150]
        print(f"      [DEBUG] Found 'Administrative Fee' at position {idx}")
        print(f"      [DEBUG] Context: {repr(snippet)}")
    else:
        print(f"      [DEBUG] 'Administrative Fee' not found in text at all!")
        # Show first 500 chars to see what we got
        print(f"      [DEBUG] First 500 chars: {full_text[:500]}")

        
    # Now extract data from full_text
    # Extract effective date
    date_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})', full_text, re.IGNORECASE)
    effective_date = date_match.group(1) if date_match else ""
    

    # Extract admin fee using pattern library
    admin_fee = ""
    for pattern_dict in ADMIN_FEE_PATTERNS:
        pattern = pattern_dict['pattern']
        fee_match = re.search(pattern, full_text, re.IGNORECASE)
        if fee_match:
            admin_fee = f"{fee_match.group(1)}%"
            print(f"      ✓ Admin Fee: {admin_fee} (pattern: {pattern_dict['name']})")
            break
    
    
    if not admin_fee and 'schedule' in full_text.lower():
        print(f"      🔍 Searching for schedule table...")
    schedule_patterns = [
        r'Administrative\s+Fee\*{1,2}\s*[\n\r\s]+(\d+)%',
        r'\|\s*Administrative\s+Fee\*{0,2}\s*\|\s*\n[^\n]*?(\d+)%',
        r'Administrative\s+Fee\*{0,2}\s*\n[^\n]*?(\d+)%'
    ]
    for pattern in schedule_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
        if match:
            admin_fee = f"{match.group(1)}%"
            print(f"      ✓ Found in schedule: {admin_fee}")
            break
    
    
    
    if not admin_fee:
        print(f"      ⚠ No admin fee found")    



    # Extract data fee using pattern library
    data_fee = ""
    for pattern_dict in DATA_FEE_PATTERNS:
        pattern = pattern_dict['pattern']
        data_match = re.search(pattern, full_text, re.IGNORECASE)
        if data_match:
            data_fee = f"{data_match.group(1)}%"
            print(f"      ✓ Data Fee: {data_fee} (pattern: {pattern_dict['name']})")
            break
        
    if not data_fee:
        print(f"      ⚠ No data fee found")

    # USE SERVICE LIBRARY TO MATCH ALL SERVICES
    all_services, service_patterns = match_services(full_text, entity_type='GPO')
    return [effective_date, admin_fee, all_services, data_fee, "", service_patterns]


# Process all PDFs
print("\n" + "="*60)
print(" CONTRACT PARSER STARTING")
print("="*60 + "\n")


# Process all PDFs
results = []
for pdf in Path("data_in").glob("**/*.pdf"):  # ** means check subfolders too
    print(f"  {pdf.name}")
    data = extract_contract(pdf)
    results.append([pdf.name] + data)

# Write simple CSV
print(" Writing results to CSV...")
with open("WORKING_OUTPUT.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["FileName", "Effective Date", "Admin Fee", "Services", "DataFee", "Notes", "Service Evidence"])
    writer.writerows(results)

# Calculate success rates
total = len(results)
dates_found = sum(1 for r in results if r[1])  # Effective Date is index 1
admin_fees_found = sum(1 for r in results if r[2])  # Admin Fee is index 2
data_fees_found = sum(1 for r in results if r[4])  # Data Fee is index 4
services_found = sum(1 for r in results if r[3])  # Services is index 3


print(f" SUCCESS! Created WORKING_OUTPUT.csv with {total} contracts")
print("\n EXTRACTION SUMMARY:")
print(f"   Effective Dates: {dates_found}/{total} ({dates_found/total*100:.0f}%)")
print(f"   Admin Fees:      {admin_fees_found}/{total} ({admin_fees_found/total*100:.0f}%)")
print(f"   Data Fees:       {data_fees_found}/{total} ({data_fees_found/total*100:.0f}%)")
print(f"   Services:        {services_found}/{total} ({services_found/total*100:.0f}%)")
print("="*60 + "\n")