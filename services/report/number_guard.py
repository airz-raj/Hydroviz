import re
from typing import List, Tuple, Optional, Any

DEVANAGARI_DIGITS = {
    '०': '0',
    '१': '1',
    '२': '2',
    '३': '3',
    '४': '4',
    '५': '5',
    '६': '6',
    '७': '7',
    '८': '8',
    '९': '9'
}

def normalise_devanagari_digits(text: str) -> str:
    """Replaces all Devanagari digits (०-९) with ASCII Arabic digits (0-9)."""
    return "".join(DEVANAGARI_DIGITS.get(ch, ch) for ch in text)

def extract_numbers(text: str) -> List[str]:
    """
    Extracts all standalone numerals (including decimals) from text.
    Handles Devanagari digits and comma-separated numbers (e.g. 1,000).
    Strips HTML style/script blocks and tags so styling numbers do not interfere with factual auditing.
    """
    # Strip style and script blocks
    cleaned_html = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    cleaned_html = re.sub(r'<script.*?>.*?</script>', '', cleaned_html, flags=re.DOTALL | re.IGNORECASE)
    cleaned_html = re.sub(r'<[^>]+>', ' ', cleaned_html)
    normalized = normalise_devanagari_digits(cleaned_html)
    # Remove commas between digits to handle formatting like 1,500
    cleaned = re.sub(r'(?<=\d),(?=\d)', '', normalized)
    return re.findall(r'\b\d+(?:\.\d+)?\b', cleaned)

def validate_numbers(text: str, allowed_numbers: List[Any], tolerance: float = 1e-4) -> Tuple[bool, Optional[str]]:
    """
    Checks if every number present in 'text' exists in 'allowed_numbers'.
    Returns (is_valid, offending_number).
    """
    extracted = extract_numbers(text)
    allowed_floats = []
    for n in allowed_numbers:
        try:
            allowed_floats.append(float(n))
        except (ValueError, TypeError):
            pass
            
    for num_str in extracted:
        try:
            val = float(num_str)
            # Check if val matches any allowed number within tolerance
            if not any(abs(val - allowed) < tolerance for allowed in allowed_floats):
                return False, num_str
        except ValueError:
            pass
            
    return True, None

def get_allowed_numbers(facts_dict: dict) -> List[float]:
    """Extracts all numerical values from any arbitrarily nested facts structure."""
    allowed = []
    
    def extract_recursive(val):
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            allowed.append(float(val))
        elif isinstance(val, dict):
            for v in val.values():
                extract_recursive(v)
        elif isinstance(val, (list, tuple, set)):
            for item in val:
                extract_recursive(item)
                
    extract_recursive(facts_dict)
    return allowed
