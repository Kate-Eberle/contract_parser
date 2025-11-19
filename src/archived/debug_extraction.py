import fitz
import re

# Open PDF directly
doc = fitz.open("data_in/Zinc - Akebia PBM Rebate Agreement FINAL_FE.pdf")

print(f"Number of pages: {len(doc)}")

# Check page 20 directly
page_20_text = doc[19].get_text()  # Page 20 is index 19
print(f"\nPage 20 text length: {len(page_20_text)} chars")

if '4.00%' in page_20_text:
    print("✓ 4.00% IS in page 20")
else:
    print("✗ 4.00% NOT in page 20")

# Check page 1 for date
page_1_text = doc[0].get_text()
if 'October 1, 2021' in page_1_text:
    print("✓ Date IS in page 1")
else:
    print("✗ Date NOT in page 1")
    # Try to find where it is
    for i in range(min(5, len(doc))):
        if 'October 1, 2021' in doc[i].get_text():
            print(f"  → Date found on page {i+1}")
            break

# Now check what patterns actually match
full_text = ""
for page in doc:
    full_text += page.get_text()

print("\n--- PATTERN MATCHING TEST ---")

# Test the date patterns from your extractors_enhanced.py
date_patterns = [
    r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',  # Your current pattern
    r'(?:effective|commencement)\s+date[:\s]+([^,\n]+)',  # Should catch "Effective Date"
    r'(October \d{1,2}, \d{4})',  # Specific for this contract
]

for pattern in date_patterns:
    match = re.search(pattern, full_text, re.IGNORECASE)
    if match:
        print(f"✓ Pattern worked: {pattern[:30]}... → Found: {match.group(1) if match.groups() else match.group(0)}")
    else:
        print(f"✗ Pattern failed: {pattern[:30]}...")

# Test fee extraction
if re.search(r'4\.00%', full_text):
    print("✓ 4.00% exists in text")
    # Find context
    match = re.search(r'.{0,50}4\.00%.{0,50}', full_text)
    if match:
        print(f"  Context: ...{match.group(0)}...")

doc.close()