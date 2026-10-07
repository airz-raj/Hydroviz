import json
import os
import jsonschema
import pytest

SCHEMA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../contracts'))

def load_schema(filename):
    with open(os.path.join(SCHEMA_DIR, filename), 'r') as f:
        return json.load(f)

def test_job_request_schema():
    schema = load_schema('job_request.schema.json')
    # Validate a valid instance
    valid_instance = {
        "bbox": [85.0, 27.5, 86.5, 28.5],
        "event_date": "2026-08-26",
        "osm_snapshot": "2026-07-27"
    }
    jsonschema.validate(instance=valid_instance, schema=schema)

def test_job_status_schema():
    schema = load_schema('job_status.schema.json')
    valid_instance = {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "ingesting",
        "stage": "catalogue_search"
    }
    jsonschema.validate(instance=valid_instance, schema=schema)

def test_facts_schema():
    schema = load_schema('facts.schema.json')
    valid_instance = {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "aoi": {"bbox": [85.0, 27.5, 86.5, 28.5], "area_km2": 1500.0},
        "event_date": "2026-08-26",
        "generated_at": "2026-08-26T12:00:00Z",
        "inputs": {
            "s1_pre": [],
            "s1_post": {},
            "s2_post": None,
            "osm_snapshot": "2026-07-27",
            "dem": "COPERNICUS_30",
            "model": {}
        },
        "flood": {
            "flooded_area_km2": 0.0,
            "debris_area_km2": 0.0,
            "mean_confidence": 0.0,
            "mode": "sar_only"
        },
        "exposure": {
            "buildings": {"total": 0, "exposed_high": 0, "exposed_medium": 0},
            "roads_km": {"total": 0.0, "exposed": 0.0},
            "bridges": []
        },
        "cutoff": {
            "mode": "road_only",
            "scenario": "strict",
            "settlements": []
        }
    }
    jsonschema.validate(instance=valid_instance, schema=schema)
