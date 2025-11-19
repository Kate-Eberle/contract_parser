# Direct test without imports
import fitz
import re

# Just test the extraction logic directly
doc = fitz.open("data_in/Zinc - Akebia PBM Rebate Agreement FINAL_FE.pdf")
full_text = ""
for page in doc:
    full_text += page.get_text()
doc.close()

# Test what extract_services would return
def test_services(text):
    # Simplified version
    if "GPO Administrative Services" in text:
        return "ADMIN: [test services]", "p.20"
    return "", ""

result = test_services(full_text)
print(f"Services returns: {type(result)} - {result}")

# The issue might be in build_record
# Let's check if that's working
test_rec = {
    'services': result,  # This might be the problem
    'admin_fee': '4.0%'
}
print(f"If services is a tuple in dict: {test_rec}")