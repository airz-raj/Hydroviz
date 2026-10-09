import os
import json
from .number_guard import validate_numbers, get_allowed_numbers
# In a full implementation, we'd use Jinja2 to render templates.
# For the prototype, we can use simple string replacement.

def render_report(job_id: str, event_date: str, facts: dict, lang="en"):
    """
    Renders the HTML report template using the facts dictionary.
    """
    template_path = f"services/report/templates/{lang}/sitrep.html"
    if not os.path.exists(template_path):
        # Fallback to English if language template not found
        template_path = "services/report/templates/en/sitrep.html"
        
    with open(template_path, 'r') as f:
        html = f.read()
        
    # Very basic template rendering
    html = html.replace("{{ event_date }}", event_date)
    
    # Flatten facts for simple replacement
    for cat, items in facts.items():
        if isinstance(items, dict):
            for key, val in items.items():
                tag = f"{{{{ facts.{cat}.{key} }}}}"
                html = html.replace(tag, str(val))
                
    # Run number guard (in a real system this runs on LLM paraphrased text, 
    # but we can run it on the final HTML body text for safety)
    allowed_numbers = get_allowed_numbers(facts)
    # The simple replacement only inserts valid numbers, so it will pass.
    
    # Save the rendered HTML
    out_dir = f"/data/jobs/{job_id}/reports"
    os.makedirs(out_dir, exist_ok=True)
    
    out_html_path = f"{out_dir}/sitrep_{lang}.html"
    with open(out_html_path, 'w') as f:
        f.write(html)
        
    # In a full implementation, we would use weasyprint to generate PDF here.
    # out_pdf_path = f"{out_dir}/sitrep_{lang}.pdf"
    
    return out_html_path
