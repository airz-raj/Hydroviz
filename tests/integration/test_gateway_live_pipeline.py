import os
import json
import pytest
from fastapi.testclient import TestClient
from services.gateway.main import app, _run_job_pipeline, JobRequest

client = TestClient(app)

@pytest.mark.asyncio
async def test_gateway_live_pipeline_full(tmp_path):
    os.environ["DATA_DIR"] = str(tmp_path)

    # 1. Test Coordinate Normalization: Pass [lat, lon, lat, lon] format
    # Melamchi / Bhote Koshi area in Nepal: Lat ~27.8, Lon ~85.5
    raw_bbox_lat_lon = [27.50, 85.20, 28.15, 85.90]
    payload = {
        "bbox": raw_bbox_lat_lon,
        "event_date": "2026-08-26",
        "osm_snapshot": "2026-07-27",
        "options": {
            "hand_threshold_m": 15.0,
            "steep_slope_deg": 20.0
        }
    }

    # Verify JobRequest normalizes to [minLon, minLat, maxLon, maxLat]
    job_req = JobRequest(**payload)
    assert job_req.bbox[0] < job_req.bbox[2]
    assert 85.0 <= job_req.bbox[0] <= 86.0
    assert 27.0 <= job_req.bbox[1] <= 29.0

    # 2. Run actual pipeline directly through _run_job_pipeline
    job_id = "test-live-pipeline-001"
    await _run_job_pipeline(job_id, job_req)

    # 3. Check /jobs/{id}/status endpoint
    res_status = client.get(f"/jobs/{job_id}/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["status"] == "complete"
    assert status_data["progress"] == 1.0

    # 4. Check /jobs/{id}/facts endpoint
    res_facts = client.get(f"/jobs/{job_id}/facts")
    assert res_facts.status_code == 200
    facts = res_facts.json()

    # Verify flood & debris physics metrics
    assert "flood" in facts
    assert facts["flood"]["flooded_area_km2"] > 0
    assert facts["flood"]["debris_area_km2"] > 0
    assert facts["flood"]["mean_confidence"] >= 0.8

    # Verify exposure metrics
    assert "exposure" in facts
    assert facts["exposure"]["buildings_exposed_high"] > 0
    assert facts["exposure"]["roads_exposed_length_m"] > 0
    assert "bridges" in facts["exposure"]

    # Verify dual cutoff scenarios (strict and conservative)
    assert "cutoff" in facts
    assert "scenarios" in facts["cutoff"]
    assert "strict" in facts["cutoff"]["scenarios"]
    assert "conservative" in facts["cutoff"]["scenarios"]
    
    strict_scen = facts["cutoff"]["scenarios"]["strict"]
    cons_scen = facts["cutoff"]["scenarios"]["conservative"]
    assert "isolated_settlements" in strict_scen
    assert "detour_settlements" in strict_scen
    assert "settlements" in strict_scen

    # Verify GeoJSON vector layers
    assert "layers" in facts
    assert "flood" in facts["layers"]
    assert "debris" in facts["layers"]
    assert "buildings" in facts["layers"]
    assert "roads" in facts["layers"]
    assert "settlements" in facts["layers"]
    assert len(facts["layers"]["flood"]["features"]) > 0

    # 5. Test /jobs/{id}/layers endpoint
    res_layers = client.get(f"/jobs/{job_id}/layers")
    assert res_layers.status_code == 200
    layers = res_layers.json()
    assert "flood" in layers
    assert "debris" in layers

    # 6. Test D8 flow path tracing (/trace)
    res_trace = client.post("/trace", json={
        "bbox": facts["aoi"]["bbox"],
        "origin": [85.55, 27.85]
    })
    assert res_trace.status_code == 200
    trace_data = res_trace.json()
    assert "path" in trace_data
    assert trace_data["path"]["type"] == "Feature"
    props = trace_data["path"]["properties"]
    assert props["drop_m"] >= 0
    assert props["distance_km"] > 0
    assert props["steps"] > 1

    # Test memoized trace caching
    res_trace_cached = client.post("/trace", json={
        "bbox": facts["aoi"]["bbox"],
        "origin": [85.55, 27.85]
    })
    assert res_trace_cached.status_code == 200
    assert res_trace_cached.json() == trace_data

    # 7. Test Copernicus EMSR927 check-only benchmark
    res_ems = client.get("/case-study/emsr927")
    assert res_ems.status_code == 200
    ems_data = res_ems.json()
    assert ems_data["activation"] == "EMSR927"
    assert ems_data["metrics"]["iou"] == 0.74
    assert ems_data["metrics"]["f1_score"] == 0.82
    assert "exposure_comparison" in ems_data

    # 8. Test bilingual situation reports (English & Nepali)
    res_rep_en = client.get(f"/jobs/{job_id}/report/en")
    assert res_rep_en.status_code == 200
    assert "text/html" in res_rep_en.headers["content-type"]
    assert "Flood Situation Report" in res_rep_en.text
    assert str(facts["flood"]["flooded_area_km2"]) in res_rep_en.text

    res_rep_ne = client.get(f"/jobs/{job_id}/report/ne")
    assert res_rep_ne.status_code == 200
    assert "text/html" in res_rep_ne.headers["content-type"]
    assert "बाढी तथा पहिरो विपद् स्थिति प्रतिवेदन" in res_rep_ne.text

    # 9. Test Job-Level Output Caching on identical re-request
    res_cached_job = client.post("/jobs", json=payload)
    assert res_cached_job.status_code == 200
    cached_resp = res_cached_job.json()
    assert cached_resp["status"] == "complete"
    assert "cache" in cached_resp["message"].lower()
