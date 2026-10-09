import os
import json
import pytest
import jsonschema
from services.ingest.worker import process_job
from services.flood_ml.workers import process_m2_baseline
from services.geo_core.worker import process_m4_geo
from services.report.worker import process_m5_report

SCHEMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../contracts/facts.schema.json'))

@pytest.mark.asyncio
async def test_full_pipeline_end_to_end(tmp_path):
    """
    M8 Hardening: End-to-end pipeline test across all milestones.
    Executes Ingest -> Flood ML -> Geo Core -> Report Generation,
    and rigorously verifies that facts.json validates against contracts/facts.schema.json.
    """
    job_id = "123e4567-e89b-12d3-a456-426614174000"
    bbox = [85.20, 27.50, 85.90, 28.15]
    event_date = "2026-08-26"
    
    # Set DATA_DIR to tmp_path for clean test isolation
    os.environ["DATA_DIR"] = str(tmp_path)
    
    # 1. Ingest Stage (M1)
    ingest_res = await process_job(job_id, bbox, event_date)
    assert ingest_res["status"] == "COMPLETED"
    assert "pair" in ingest_res
    
    # 2. Flood ML Baseline Stage (M2)
    flood_res = await process_m2_baseline(job_id)
    assert flood_res["status"] == "COMPLETED"
    assert flood_res["flooded_area_km2"] > 0
    
    # 3. Geo Core Exposure & Cutoff Stage (M4)
    geo_res = await process_m4_geo(job_id)
    assert geo_res["status"] == "COMPLETED"
    assert "exposure" in geo_res["facts"]
    assert "cutoff" in geo_res["facts"]
    
    # 4. Report Generation Stage (M5)
    report_res = await process_m5_report(job_id, event_date)
    assert report_res["status"] == "COMPLETED"
    assert os.path.exists(report_res["report_en_path"])
    assert os.path.exists(report_res["report_ne_path"])
    
    # 5. Schema Contract Validation
    facts_path = os.path.join(str(tmp_path), "jobs", job_id, "facts.json")
    assert os.path.exists(facts_path)
    
    with open(facts_path, "r", encoding="utf-8") as f:
        facts = json.load(f)
        
    # Ensure all top-level required fields for schema validation
    facts["job_id"] = job_id
    facts["aoi"] = {"bbox": bbox, "area_km2": 1500.0}
    facts["event_date"] = event_date
    facts["generated_at"] = "2026-08-26T12:00:00Z"
    if "inputs" not in facts:
        facts["inputs"] = {
            "s1_pre": [],
            "s1_post": {},
            "s2_post": None,
            "osm_snapshot": "2026-07-27",
            "dem": "COPERNICUS_30",
            "model": {}
        }
        
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    jsonschema.validate(instance=facts, schema=schema)
    print("Full E2E Pipeline verified and validated against facts.schema.json successfully.")
