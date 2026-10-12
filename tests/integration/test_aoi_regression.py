import os
import pytest
from services.gateway.main import _run_job_pipeline, JobRequest, get_job_facts

@pytest.mark.asyncio
async def test_aoi_regression_variability(tmp_path):
    """
    Verifies the 5 screenshot regression cases:
    - Melamchi standard AOI
    - Bhote Koshi AOI
    - Helambu AOI
    - Kathmandu Valley AOI
    - Trishuli AOI
    Ensures that metrics and geometries vary truthfully based on actual geospatial observations,
    rather than producing fixed numbers (e.g. frozen 89 exposed buildings or 4.8 km2 flood area).
    """
    os.environ["DATA_DIR"] = str(tmp_path)

    aois = {
        "melamchi": [85.50, 27.80, 85.65, 27.95],
        "bhote_koshi": [85.80, 27.90, 85.95, 28.05],
        "helambu": [85.45, 28.00, 85.60, 28.15],
        "kathmandu": [85.25, 27.65, 85.40, 27.80],
        "trishuli": [85.10, 27.90, 85.25, 28.05]
    }

    results = {}

    for name, bbox in aois.items():
        job_id = f"test-regression-{name}"
        req = JobRequest(bbox=bbox, event_date="2026-08-26")
        await _run_job_pipeline(job_id, req)
        facts = get_job_facts(job_id)
        
        flood_km2 = facts.get("flood", {}).get("flooded_area_km2", 0.0)
        buildings_exp = facts.get("exposure", {}).get("buildings_exposed_high", 0)
        mode = facts.get("mode")

        results[name] = {
            "flood_km2": flood_km2,
            "buildings_exp": buildings_exp,
            "mode": mode
        }

    # 1. Verify building count is NEVER uniformly 89
    building_counts = [r["buildings_exp"] for r in results.values()]
    assert all(c != 89 for c in building_counts), "Regression: Exposed building count is still hardcoded to 89!"
    assert not all(c == building_counts[0] for c in building_counts), "Regression: All AOIs produced identical building counts!"

    # 2. Verify genuine differences in building exposure across presets
    assert results["melamchi"]["buildings_exp"] == 11
    assert results["bhote_koshi"]["buildings_exp"] == 0
    assert results["kathmandu"]["buildings_exp"] == 3
    assert results["trishuli"]["buildings_exp"] == 3

    # 3. Verify flooded area varies across different AOIs based on real geodata
    flood_areas = [r["flood_km2"] for r in results.values()]
    assert not all(a == 4.8 for a in flood_areas), "Regression: Flooded area is still hardcoded to 4.8 km2 across all AOIs!"
    assert results["melamchi"]["flood_km2"] == 4.8
    assert results["bhote_koshi"]["flood_km2"] == 0.1
    assert results["kathmandu"]["flood_km2"] == 2.4
    assert results["trishuli"]["flood_km2"] == 1.9

    # 4. Verify all presets are valid reference cases
    for name in aois:
        assert results[name]["mode"] == "reference_case"

    # 5. Verify arbitrary custom AOI without CDSE credentials runs simulation fallback
    custom_jid = "test-custom-aoi-fallback"
    old_cid = os.environ.get("CDSE_CLIENT_ID", "")
    old_sec = os.environ.get("CDSE_CLIENT_SECRET", "")
    os.environ["CDSE_CLIENT_ID"] = ""
    os.environ["CDSE_CLIENT_SECRET"] = ""
    try:
        await _run_job_pipeline(custom_jid, JobRequest(bbox=[83.9, 28.2, 84.1, 28.35], event_date="2026-08-26"))
        custom_facts = get_job_facts(custom_jid)
        assert custom_facts.get("mode") == "demo_simulated"
        assert custom_facts.get("flood", {}).get("flooded_area_km2", 0) > 0.0
    finally:
        os.environ["CDSE_CLIENT_ID"] = old_cid
        os.environ["CDSE_CLIENT_SECRET"] = old_sec
