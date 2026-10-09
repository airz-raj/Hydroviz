import re

def extract_numbers(text):
    """Extracts all standalone numerals (including decimals) from a text string."""
    # Find numbers like 10, 3.14, .5
    return re.findall(r'\b\d+(?:\.\d+)?\b', text)

def validate_numbers(text, allowed_numbers):
    """
    Checks if every number in 'text' exists in 'allowed_numbers'.
    Returns (is_valid, offending_number).
    """
    extracted = extract_numbers(text)
    # Convert all to float for safe comparison
    allowed_floats = [float(n) for n in allowed_numbers]
    
    for num_str in extracted:
        try:
            val = float(num_str)
            # If the number is not in the allowed facts (allow small floating point tolerance)
            if not any(abs(val - allowed) < 1e-5 for allowed in allowed_floats):
                return False, num_str
        except ValueError:
            pass
            
    return True, None

def get_allowed_numbers(facts_dict):
    """Extracts all numerical values from the nested facts dictionary."""
    allowed = []
    
    def extract_from_dict(d):
        for k, v in d.items():
            if isinstance(v, (int, float)):
                allowed.append(v)
            elif isinstance(v, dict):
                extract_from_dict(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, (int, float)):
                        allowed.append(item)
                    elif isinstance(item, dict):
                        extract_from_dict(item)
                        
    extract_from_dict(facts_dict)
    return allowed
