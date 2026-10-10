import os
import sys
import json
from .generator import render_report

sys.path.insert(0, '/shared')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))

try:
    from shared.attribution import add_provenance
except ImportError:
    def add_provenance(job_id, stage, metadata):
        pass

async def process_m5_report(job_id: str, event_date: str):
    """
    Worker function to process M5 report generation.
    Generates situation reports in English and Nepali.
    """
    add_provenance(job_id, "report", {
        "method": "Template rendering with number guard (M5)"
    })
    
    # Load facts
    data_dir = os.getenv("DATA_DIR", "/data")
    if not os.path.exists(data_dir):
        if not os.path.isabs(data_dir):
            data_dir = os.path.abspath(data_dir)
        else:
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception:
                data_dir = os.path.abspath("./data")
    facts_path = os.path.join(data_dir, "jobs", job_id, "facts.json")
        
    if not os.path.exists(facts_path):
        raise FileNotFoundError(f"Cannot generate report: facts.json for job {job_id} not found at {facts_path}")
        
    with open(facts_path, 'r', encoding='utf-8') as f:
        facts = json.load(f)
            
    # Generate English report
    en_html = render_report(job_id, event_date, facts, lang="en")
    
    # Generate Nepali report
    ne_html = render_report(job_id, event_date, facts, lang="ne")
    
    return {
        "status": "COMPLETED",
        "report_en_path": en_html,
        "report_ne_path": ne_html
    }
