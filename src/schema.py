# src/schema.py
HEADER = [
    "Ref","","Effective Date","","Contract Title","","Admin / Service Fee","",
    "Services","","Duplicate","","Modifications","","QC Flags","",
    "Services Pg Number","","Termination Date","",
    "Pass-Through Language (page + quote or None)","",
    "Relevant Product"
]

NUM_COLUMNS = 23  # including spacer columns
NUM_COMMAS_PER_ROW = NUM_COLUMNS - 1

STANDARD_LITERALS = {
    "UNKNOWN": "Unknown",
    "NA": "N/A",
    "NONE": "None",
    "DUP_YES": "Yes",
    "DUP_NO": "No",
}

DATE_FORMAT_NOTE = "YYYY-MM-DD"

