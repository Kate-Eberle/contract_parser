import sys
from pathlib import Path

# Test on one Zinc contract
test_file = Path("data_in/Zinc - Akebia PBM Rebate Agreement FINAL_FE.pdf")
print(f"Testing: {test_file.name}\n")

# First, let's just see if we can extract PDF text at all
import fitz  # PyMuPDF

doc = fitz.open(str(test_file))
print(f"PDF has {len(doc)} pages\n")

# Get first page text
page = doc[0]
text = page.get_text()
print(f"First 500 chars of page 1:")
print(text[:500])
print("\n" + "="*50 + "\n")

# Now let's test if basic patterns find anything
import re

# Look for dates
dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text)
print(f"Dates found: {dates[:3] if dates else 'NONE'}")

# Look for percentages
percentages = re.findall(r'\d+(?:\.\d+)?%', text)
print(f"Percentages found: {percentages[:3] if percentages else 'NONE'}")

# Look for "WAC"
if 'WAC' in text or 'wac' in text.lower():
    print("WAC mentioned: YES")
else:
    print("WAC mentioned: NO")

doc.close()