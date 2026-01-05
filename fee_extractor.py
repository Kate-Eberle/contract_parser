import re
import csv
import json
from pathlib import Path
from difflib import SequenceMatcher
import ollama
from keywords import ACCEPT_KEYWORDS, REJECT_KEYWORDS

def extract_section_number(markdown_before):
    """Find the most recent section header before the fee"""
    sections = re.findall(r'#{1,6}\s+(.+)', markdown_before)
    return sections[-1].strip() if sections else "Unknown"

def fuzzy_match(text, keyword, threshold=0.6):
    """Match keywords even with OCR errors using fuzzy matching"""
    text_lower = text.lower()
    words = text_lower.split()
    
    for word in words:
        # Remove punctuation from word
        clean_word = re.sub(r'[^a-z0-9]', '', word)
        if len(clean_word) < 3:  # Skip very short words
            continue
        
        similarity = SequenceMatcher(None, clean_word, keyword).ratio()
        if similarity > threshold:
            return True
    
    return False

def is_service_fee(context_text):
    """Check if percentage context matches service fee (with fuzzy matching for OCR)"""
    text_lower = context_text.lower()
    
    # If reject keywords present (exact or fuzzy), skip
    for keyword in REJECT_KEYWORDS:
        if keyword in text_lower or fuzzy_match(context_text, keyword, threshold=0.65):
            return False
    
    # If accept keywords present (exact or fuzzy), extract
    for keyword in ACCEPT_KEYWORDS:
        if keyword in text_lower or fuzzy_match(context_text, keyword, threshold=0.65):
            return True
    
    return None

def extract_fee_from_table(markdown_content):
    """Fallback: Extract fee from markdown table if found in Fee column"""
    # Look for table rows with "Fee" in header and percentage in data
    pattern = r'\|\s*.*?(Administrative|Service).*?Fee.*?\|\s*(\d+\.?\d+%)'
    match = re.search(pattern, markdown_content, re.IGNORECASE)
    
    if match:
        percentage = match.group(2)
        return {
            'percentage': percentage,
            'section': 'Table'
        }
    
    return None

def extract_fee_with_ollama(markdown_content):
    """Fallback: Use Ollama/Mistral to extract fee from markdown"""
    try:
        prompt = f"""Extract the service/administrative fee and section number from this contract markdown.
Only extract fees related to services (administrative, distribution, etc). Do NOT extract rebates, discounts, or chargebacks.

Return ONLY a valid JSON object with this format:
{{"fee": "X%", "section": "Y"}}

If no service fee is found, return:
{{"fee": null, "section": null}}

Contract:
{markdown_content}"""

        response = ollama.chat(
            model='mistral',
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        # Extract the response text
        response_text = response['message']['content'].strip()
        
        # Find JSON in response (in case Mistral adds extra text)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            return None
        
        json_str = response_text[json_start:json_end]
        data = json.loads(json_str)
        
        # Validate response
        if data.get('fee') and data.get('section'):
            return {
                'percentage': data['fee'],
                'section': data['section']
            }
        
        return None
    
    except Exception as e:
        print(f"    Ollama error: {e}")
        return None

def extract_fee_from_markdown(file_path):
    """Extract service fee and section from markdown file.
    
    Try in order:
    1. Regex + fuzzy matching (fast)
    2. Table extraction (for structured data)
    3. Ollama/Mistral (accurate fallback)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try 1: Regex + fuzzy matching
    pattern = r'(\d+\.?\d+%)'
    matches = list(re.finditer(pattern, content))
    
    for match in matches:
        percentage = match.group(1)
        start = max(0, match.start() - 150)
        end = min(len(content), match.end() + 150)
        context = content[start:end]
        
        # Check if this is a service fee
        is_service = is_service_fee(context)
        
        if is_service:
            # Find section number
            markdown_before = content[:match.start()]
            section = extract_section_number(markdown_before)
            
            return {
                'percentage': percentage,
                'section': section
            }
    
    # Try 2: Check if fee is in a table
    table_fee = extract_fee_from_table(content)
    if table_fee:
        return table_fee
    
    # Try 3: Fallback to Ollama
    ollama_fee = extract_fee_with_ollama(content)
    if ollama_fee:
        return ollama_fee
    
    return None

def main():
    output_dir = Path('output')
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    markdown_files = sorted(output_dir.glob('output_*.md'))
    
    csv_data = []
    
    print("=" * 60)
    print("Fee Extraction (Regex → Table → Ollama)")
    print("=" * 60)
    
    for md_file in markdown_files:
        file_name = md_file.stem.replace('output_', '')
        
        print(f"\nProcessing: {file_name}")
        
        try:
            fee_data = extract_fee_from_markdown(md_file)
            
            if fee_data:
                csv_data.append({
                    'File Name': file_name,
                    'Service Fee': fee_data['percentage'],
                    'Section #': fee_data['section']
                })
                print(f"  ✅ Found: {fee_data['percentage']} in {fee_data['section']}")
            else:
                print(f"  ❌ No service fee found")
                csv_data.append({
                    'File Name': file_name,
                    'Service Fee': 'NOT FOUND',
                    'Section #': ''
                })
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            csv_data.append({
                'File Name': file_name,
                'Service Fee': 'ERROR',
                'Section #': ''
            })
    
    # Write CSV
    csv_file = results_dir / 'service_fees.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['File Name', 'Service Fee', 'Section #'])
        writer.writeheader()
        writer.writerows(csv_data)
    
    print("\n" + "=" * 60)
    print(f"Results saved to: {csv_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()