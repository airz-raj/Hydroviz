import os
import json
from .number_guard import validate_numbers, get_allowed_numbers

def render_report(job_id: str, event_date: str, facts: dict, lang="en") -> str:
    """
    Renders the HTML report template using the facts dictionary.
    Supports English ('en') and Nepali ('ne').
    """
    base_dir = os.path.dirname(__file__)
    template_path = os.path.join(base_dir, "templates", lang, "sitrep.html")
    if not os.path.exists(template_path):
        template_path = os.path.join(base_dir, "templates", "en", "sitrep.html")
        
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # Replace global variables
    html = html.replace("{{ event_date }}", str(event_date))
    html = html.replace("{{ job_id }}", str(job_id))
    
    # Flatten nested facts for tag replacement
    def flatten_dict(d, prefix="facts"):
        items = {}
        for k, v in d.items():
            key = f"{prefix}.{k}"
            if isinstance(v, dict):
                items.update(flatten_dict(v, key))
                # Also allow direct access if leaf contains common names
                for sub_k, sub_v in v.items():
                    if not isinstance(sub_v, dict):
                        items[f"{key}.{sub_k}"] = sub_v
            else:
                items[key] = v
        return items

    flat_facts = flatten_dict(facts)
    for tag_name, val in flat_facts.items():
        placeholder = f"{{{{ {tag_name} }}}}"
        html = html.replace(placeholder, str(val))
        
    # Run number guard
    allowed_numbers = get_allowed_numbers(facts)
    for part in str(event_date).split('-'):
        try:
            allowed_numbers.append(float(part))
        except ValueError:
            pass
    # Allow known metadata and template constants (Sentinel-1, 10m, 15m HAND, 20 deg slope, WorldDEM-30, copyright years 2010-2018, citation years 2020/2024, 2026, etc.)
    allowed_numbers.extend([1.0, 2.0, 10.0, 15.0, 20.0, 30.0, 2010.0, 2014.0, 2018.0, 2020.0, 2024.0, 2026.0])
    
    is_valid, bad_num = validate_numbers(html, allowed_numbers)
    if not is_valid:
        print(f"Number Guard Notice: Detected unwhitelisted numeral '{bad_num}' in {lang} report")
    
    # Resolve output directory
    data_dir = os.getenv("DATA_DIR")
    if not data_dir:
        local_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        if os.path.exists(local_data):
            data_dir = local_data
        elif os.name != 'nt' and os.path.exists('/data'):
            data_dir = '/data'
        else:
            data_dir = os.path.abspath("./data")
    out_dir = os.path.join(data_dir, "jobs", job_id, "reports")
    os.makedirs(out_dir, exist_ok=True)
    
    out_html_path = os.path.join(out_dir, f"sitrep_{lang}.html")
    with open(out_html_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    return out_html_path
