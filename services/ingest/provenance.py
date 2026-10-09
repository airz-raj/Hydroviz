import os
import json
from typing import Dict, Any, List

def write_provenance_record(job_id: str, record: Dict[str, Any], data_dir: str = None) -> str:
    """
    Write or append a provenance record for an ingestion job.
    Persists to the job's provenance log on the shared volume.
    """
    if data_dir is None:
        data_dir = os.getenv("DATA_DIR", "/data")
        
    out_dir = os.path.join(data_dir, "jobs", job_id)
    if not os.path.isabs(out_dir) or not os.path.exists(os.path.dirname(out_dir)):
        out_dir = os.path.abspath(f"./data/jobs/{job_id}")
    os.makedirs(out_dir, exist_ok=True)
    
    prov_file = os.path.join(out_dir, "provenance.json")
    records = []
    if os.path.exists(prov_file):
        try:
            with open(prov_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
            
    records.append(record)
    with open(prov_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
        
    return prov_file

def read_provenance_records(job_id: str, data_dir: str = None) -> List[Dict[str, Any]]:
    """Read provenance records for a given job."""
    if data_dir is None:
        data_dir = os.getenv("DATA_DIR", "/data")
    prov_file = os.path.join(data_dir, "jobs", job_id, "provenance.json")
    if not os.path.exists(prov_file):
        prov_file = os.path.abspath(f"./data/jobs/{job_id}/provenance.json")
    if os.path.exists(prov_file):
        with open(prov_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
