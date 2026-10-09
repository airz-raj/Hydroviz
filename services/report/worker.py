import os
import json
from .generator import render_report
from shared.attribution import add_provenance

async def process_m5_report(job_id: str, event_date: str):
    """
    Worker function to process M5 report generation.
    """
    
    add_provenance(job_id, "report", {
        "method": "Template rendering with number guard (M5)"
    })
    
    # Load facts
    facts_path = f"/data/jobs/{job_id}/facts.json"
    if not os.path.exists(facts_path):
        raise FileNotFoundError(f"Facts file missing for job {job_id}")
        
    with open(facts_path, 'r') as f:
        facts = json.load(f)
        
    # Generate English report
    en_html = render_report(job_id, event_date, facts, lang="en")
    
    # Generate Nepali report (stubbed)
    # ne_html = render_report(job_id, event_date, facts, lang="ne")
    
    return {"status": "COMPLETED", "report_path": en_html}
