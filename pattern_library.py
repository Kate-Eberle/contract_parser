"""
Contract extraction patterns library
Last updated: November 2024
"""

# Admin Fee Patterns (ordered from most specific to least specific)
ADMIN_FEE_PATTERNS = [
    # TIER 1: Highest specificity - exact phrase matches with context
     {
        'name': 'schedule_table_fee',
        'pattern': r'Administrative\s+Fee\*{1,2}\s*[\n\s]+(\d+\.?\d*)%',
        'example': 'Administrative Fee**\n3%'
    },
    {
        'name': 'standard_fee_percentage',
        'pattern': r'Administrative\s+Fee\s*[\*]*\s*Percentage[:\s]*(\d+\.?\d*)%',
        'example': 'Administrative Fee Percentage: 3.00%'
    },
    {
        'name': 'fee_shall_equal',
        'pattern': r'Administrative\s+Fees?\s+shall\s+be\s+equal\s+to\s*\(?\w?\)?\s*(\d+\.?\d*)%',
        'example': 'Administrative Fees shall be equal to (i) 3.0%'
    },
    {
        'name': 'fee_of_wac',
        'pattern': r'(?:administrative|admin)\s+fees?.*?(\d+\.?\d*)%\s+of\s+(?:each\s+)?(?:WAC|wholesale)',
        'example': '3.0% of each WAC'
    },
    
    # TIER 2: Medium specificity - structural markers (colons, asterisks)
    {
        'name': 'fee_with_colon',
        'pattern': r'Administrative\s+Fee[\*\s]*:[\s]*(\d+\.?\d*)%',
        'example': 'Administrative Fee*: 3%'
    },
    {
        'name': 'table_asterisk_fee',
        'pattern': r'Administrative\s+Fee\*+[\s\n]*(\d+\.?\d*)\s*%',
        'example': 'Administrative Fee** 3%'
    },
    {
        'name': 'table_cell_fee',
        'pattern': r'Administrative\s+Fee[\*\s]*\s*\n\s*(\d+\.?\d*)%',
        'example': 'Administrative Fee\n3%'
    },
    
    # TIER 3: Lower specificity - whitespace and basic structure
    {
        'name': 'table_fee_with_whitespace',
        'pattern': r'Admin\w*\s+Fee[\*\s]+(\d+\.?\d*)\s*%',
        'example': 'Administrative Fee    3.00 %'
    },
    {
        'name': 'simple_fee',
        'pattern': r'Administrative\s+Fees?\s+(\d+\.?\d*)%',
        'example': 'Administrative Fees 3%'
    },
    {
        'name': 'percentage_after_fee_row',
        'pattern': r'Admin\w*\s+Fee[\s|:\*]{1,20}(\d+\.?\d*)\s*%',
        'example': 'Administrative Fee | 3.00%'
    },
    
    # TIER 4: Last resort - very loose patterns (could match wrong things)
    {
        'name': 'fee_in_next_cell',
        'pattern': r'Fee\s*[\*\n\t]+\s*(\d+\.?\d*)\s*%',
        'example': 'Fee\n3%'
    }
]

# Data Fee Patterns (ordered by specificity)
DATA_FEE_PATTERNS = [
    {
        'name': 'portal_fee',
        'pattern': r'Portal\s+Fee[^%\d]*(\d+\.?\d*)%',
        'example': 'Portal Fee: 2.0%'
    },
    {
        'name': 'data_fee',
        'pattern': r'Data\s+Fees?[^%\d]*(\d+\.?\d*)%',
        'example': 'Data Fee shall equal 2%'
    }
]

# Placeholder for future pattern groups
TERMINATION_DATE_PATTERNS = []
EFFECTIVE_DATE_PATTERNS = []