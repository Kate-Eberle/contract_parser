import fitz
import csv
import re
from pathlib import Path


def extract_contract(pdf_path):
    """Extract what we actually need from a contract."""
    doc = fitz.open(str(pdf_path))
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    
    # Extract effective date - WORKING PATTERN
    date_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})', full_text, re.IGNORECASE)
    effective_date = date_match.group(1) if date_match else ""
    
    '''
    # Extract admin fee - WORKING FOR ZINC
    fee_match = re.search(r'(?:GPO|Administrative)\s+(?:Administrative\s+)?Fee\s+Percentage[^%\d]*(\d+\.?\d*)%', full_text, re.IGNORECASE)
    admin_fee = f"{fee_match.group(1)}%" if fee_match else ""
    '''
    
    # extract admin fee w/ multiple patterns
    admin_fee = ""
    fee_patterns = [
        r'(?:GPO|Administrative)\s+(?:Administrative\s+)?Fee\s+Percentage[^%\d]*(\d+\.?\d*)%',  # Original
        r'Administrative\s+Fees?[^%]*?(\d+\.?\d*)%'  # New simpler pattern
    ]
    for pattern in fee_patterns:
        fee_match = re.search(pattern, full_text, re.IGNORECASE)
        if fee_match:
            admin_fee = f"{fee_match.group(1)}%"
            break      
   
    # Extract data/portal fee
    data_fee = ""
    data_patterns = [
        r'Portal\s+Fee[^%\d]*(\d+\.?\d*)%',
        r'Data\s+Fee[^%\d]*(\d+\.?\d*)%',
        r'(\d+\.?\d*)%\s+Portal'
    ]
    for pattern in data_patterns:
        data_match = re.search(pattern, full_text, re.IGNORECASE)
        if data_match:
            data_fee = f"{data_match.group(1)}%"
            break


    # Extract services if fee exists
    admin_services = ""
    if admin_fee != "":
        # Method 1: Look for "Administrative Services" (with "ive")
        services_match = re.search(r'\n\s*\d+\.\s+\w+\s+Administrative Services[.:]*:(.*?)(?:\n\s*\d+\.|\n\n)', full_text, re.DOTALL | re.IGNORECASE)
        
        if not services_match:
            # Method 2: Look for "Administration Services" or "Program Administration Services"
            services_match = re.search(r'(?:Program\s+)?Administration\s+Services[.:]*\s*(.*?)(?:\n\s*[A-Z]\.|$)', full_text, re.DOTALL | re.IGNORECASE)
        
        if services_match:
            # Get all the services text
            services_text = services_match.group(1).strip()
            
            # If it starts with descriptive text before "1.", skip to the first service
            first_service = re.search(r'1\.\s+', services_text)
            if first_service:
                services_text = services_text[first_service.start():]
                
            # Clean up extra whitespace
            admin_services = re.sub(r'\s+', ' ', services_text)
    

 # Extract data/portal services if data fee exists
    data_services = ""
    if data_fee != "":
        # FIRST: Look for "Data Services" section with numbered list
        data_services_section = re.search(
            r'\n\s*[A-Z]\.\s+Data\s+Services[.:]\s*(.*?)(?:\n\s*[A-Z]\.|$)',
            full_text,
            re.DOTALL | re.IGNORECASE
        )


        if data_services_section:
            # Get the full text
            full_services_text = data_services_section.group(1).strip()
            
            # 1. Remove intro statement by starting at first "1."
            first_service = re.search(r'1\.\s+', full_services_text)
            if first_service:
                full_services_text = full_services_text[first_service.start():]
            
            # 2. Remove DocuSign envelope IDs
            full_services_text = re.sub(r'DocuSign Envelope ID:\s*[A-Z0-9\-]+', '', full_services_text)
            
            # 3. Clean up whitespace
            data_services = re.sub(r'\s+', ' ', full_services_text).strip()
            
            # Optional: Add semicolons between numbered items if not present
            data_services = re.sub(r';\s*;', ';', data_services)


        else:
            # FALLBACK: tries to find the first two services listed under data/portal fee
            data_section = re.search(
                r'(?:GPO\s+)?(?:Portal|Data)\s+Fee[^.]+\.\s*\n\s*2\.\s+([^\n]+).*?\n\s*3\.\s+([^\n]+)',
                full_text, 
                re.DOTALL | re.IGNORECASE
            )
            if data_section:
                service1 = data_section.group(1).strip().rstrip('.')
                service2 = data_section.group(2).strip().rstrip('.')
                data_services = f"{service1}; {service2}"   
 
    return [effective_date, admin_fee, admin_services, data_fee, data_services]


# Process all PDFs
print("Processing contracts...")
results = []
for pdf in Path("data_in").glob("**/*.pdf"):  # ** means check subfolders too
    print(f"  {pdf.name}")
    data = extract_contract(pdf)
    results.append([pdf.name] + data)

# Write simple CSV
with open("WORKING_OUTPUT.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["FileName", "Effective Date", "Admin Fee", "AdminServices", "DataFee", "DataServices"])
    writer.writerows(results)

print(f"\n✅ DONE! Created WORKING_OUTPUT.csv with {len(results)} contracts")