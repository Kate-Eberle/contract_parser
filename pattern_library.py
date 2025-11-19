"""
Contract extraction patterns library
Last updated: November 2024
"""

# Admin Fee Patterns (percentage-based)
ADMIN_FEE_PATTERNS = [
    {
        'name': 'standard_fee_percentage',
        'pattern': r'Administrative\s+Fee\s*[\*]*\s*Percentage[:\s]*(\d+\.?\d*)%',
        'example': 'Administrative Fee Percentage: 3.00%',
        'confidence': 0.95
    },
    {
        'name': 'fee_with_colon',
        'pattern': r'Administrative\s+Fee[\*\s]*:[:\s]*(\d+\.?\d*)%',
        'example': 'Administrative Fee: 3%',
        'confidence': 0.90
    },
    {
        'name': 'fee_shall_equal',
        'pattern': r'Administrative\s+Fees?\s+shall\s+be\s+equal\s+to\s*\(?\w?\)?\s*(\d+\.?\d*)%',
        'example': 'Administrative Fees shall be equal to (i) 3.0%',
        'confidence': 0.95
    },
    {
        'name': 'table_cell_fee',
        'pattern': r'Administrative\s+Fee[\*\s]*\s*\n\s*(\d+\.?\d*)%',
        'example': 'Administrative Fee\n3%',
        'confidence': 0.85
    },
    {
        'name': 'fee_of_wac',
        'pattern': r'(?:administrative|admin)\s+fees?.*?(\d+\.?\d*)%\s+of\s+(?:each\s+)?(?:WAC|wholesale)',
        'example': '3.0% of each WAC',
        'confidence': 0.90
    },
    {
        'name': 'simple_fee',
        'pattern': r'Administrative\s+Fees?\s+(\d+\.?\d*)%',
        'example': 'Administrative Fees 3%',
        'confidence': 0.80
    },
    {
        'name': 'table_fee_with_whitespace',
        'pattern': r'Admin\w*\s+Fee[\*\s]+(\d+\.?\d*)\s*%',
        'example': 'Administrative Fee    3.00 %',
        'confidence': 0.85
    },
    {
        'name': 'fee_in_next_cell',
        'pattern': r'Fee\s*[\*\n\t]+\s*(\d+\.?\d*)\s*%',
        'example': 'Fee\n3%',
        'confidence': 0.80
    },
    {
        'name': 'percentage_after_fee_row',
        'pattern': r'Admin\w*\s+Fee[^\d%]{0,50}(\d+\.?\d*)\s*%',
        'example': 'Administrative Fee | 3.00%',
        'confidence': 0.75
    } 
]

# Data Fee Patterns
DATA_FEE_PATTERNS = [
    {
        'name': 'portal_fee',
        'pattern': r'Portal\s+Fee[^%\d]*(\d+\.?\d*)%',
        'example': 'Portal Fee: 2.0%',
        'confidence': 0.90
    },
    {
        'name': 'data_fee',
        'pattern': r'Data\s+Fees?[^%\d]*(\d+\.?\d*)%',
        'example': 'Data Fee shall equal 2%',
        'confidence': 0.90
    }
]



# Add more pattern groups as needed
TERMINATION_DATE_PATTERNS = [...]
EFFECTIVE_DATE_PATTERNS = [...]



'''
Need to add ??


 # Extract effective date - WORKING PATTERN
    date_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})', full_text, re.IGNORECASE)
    effective_date = date_match.group(1) if date_match else ""
    
    
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

'''