import fitz
import re

doc = fitz.open("data_in/Zinc - Akebia PBM Rebate Agreement FINAL_FE.pdf")

# Check page 20 (index 19) where the screenshot shows the fees
page = doc[19]  # Page 20 is index 19
text = page.get_text()

print("PAGE 20 CONTENT:")
print("=" * 50)
print(text[:1000])  # First 1000 chars
print("=" * 50)

# Look for percentages
percentages = re.findall(r'\d+\.\d+%', text)
print(f"\nPercentages found: {percentages}")

# Look for "GPO Administrative Fees"
if "GPO Administrative Fee" in text:
    print("Found GPO Administrative Fee section!")
    
# Look for services
if "GPO Administrative Services" in text:
    print("Found GPO Administrative Services section!")

doc.close()