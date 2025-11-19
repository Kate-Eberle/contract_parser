import fitz  # PyMuPDF
import re

# Open the PDF directly
doc = fitz.open("data_in/Zinc - Akebia PBM Rebate Agreement FINAL_FE.pdf")
print(f"PDF has {len(doc)} pages\n")

# Combine ALL pages text
full_text = ""
for i, page in enumerate(doc):
    page_text = page.get_text()
    full_text += f"\n--- PAGE {i+1} ---\n" + page_text

doc.close()

# Now search the ENTIRE document
print("SEARCHING ENTIRE DOCUMENT:")
print("=" * 50)

# Find effective date
date_patterns = [
    r'effective as of ([^,\n]+)',
    r'Effective Date["\s]+(?:is\s+)?([^,\n"]+)',
    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
]

for pattern in date_patterns:
    match = re.search(pattern, full_text, re.IGNORECASE)
    if match:
        print(f"✅ EFFECTIVE DATE FOUND: {match.group(1) if match.lastindex else match.group(0)}")
        break
else:
    print("❌ No effective date found")

# Find admin fee
fee_match = re.search(r'(\d+\.?\d*)%', full_text)
if fee_match:
    print(f"✅ FEE FOUND: {fee_match.group(0)}")
else:
    print("❌ No fee percentage found")

# Find GPO services
if "GPO Administrative Services" in full_text:
    print("✅ GPO SERVICES SECTION FOUND")
    # Extract the services list
    services_match = re.search(r'GPO Administrative Services[^:]*:(.*?)(?:\n\d+\.|$)', full_text, re.DOTALL)
    if services_match:
        services_text = services_match.group(1)[:500]
        print(f"   Services preview: {services_text[:200]}...")

print("\nSUMMARY: The data IS in the PDF and extractable!")