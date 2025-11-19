# simple_solution.py
import fitz, csv, re
from pathlib import Path

def extract_contract(pdf_path):
    doc = fitz.open(pdf_path)
    text = "".join([p.get_text() for p in doc])
    doc.close()
    
    # Find what we actually need
    date = re.search(r'effective as of ([^,\n]+\d{4})', text, re.I)
    fee = re.search(r'GPO Administrative Fee[^%]*?(\d+\.?\d*)%', text, re.I)
    
    return {
        'file': pdf_path.name,
        'date': date.group(1) if date else 'Unknown',
        'fee': f"{fee.group(1)}%" if fee else 'Unknown'
    }

# Process all files
results = [extract_contract(p) for p in Path("data_in").glob("*.pdf")]

# Write simple CSV
with open("simple_working.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['file', 'date', 'fee'])
    writer.writeheader()
    writer.writerows(results)

print("Done. Check simple_working.csv")