import pytest
from services.geo_core.python.geo_core_py import Building, Road, Bridge, ExposureResult

def classify_building_exposure(building_poly, flood_polys):
    """
    Classify building footprint based on flood mask intersection:
    - exposed_high: intersects flood polygon
    - exposed_medium: within buffer distance
    - unaffected: no proximity
    """
    bx, by = building_poly["center"]
    for fp in flood_polys:
        fx, fy = fp["center"]
        dist = ((bx - fx)**2 + (by - fy)**2)**0.5
        if dist <= fp["radius"]:
            return "exposed_high"
        elif dist <= fp["radius"] + 10.0:
            return "exposed_medium"
    return "unaffected"

def test_building_exposure_classification():
    flood_zones = [
        {"center": (100.0, 100.0), "radius": 20.0, "confidence": 0.9}
    ]

    # Building directly inside flood zone
    b_direct = {"id": 1, "center": (105.0, 105.0)}
    assert classify_building_exposure(b_direct, flood_zones) == "exposed_high"

    # Building in 10m buffer zone (dist ≈ 22.8m, radius = 20m)
    b_buffer = {"id": 2, "center": (100.0, 122.0)}
    assert classify_building_exposure(b_buffer, flood_zones) == "exposed_medium"

    # Building far away (dist = 100m)
    b_far = {"id": 3, "center": (200.0, 100.0)}
    assert classify_building_exposure(b_far, flood_zones) == "unaffected"

def test_exposure_result_structure():
    result = ExposureResult()
    result.buildings.append(Building(osm_id=101, exposure="exposed_high"))
    result.roads.append(Road(osm_id=202, total_length_m=500.0, exposed_length_m=120.0))
    result.bridges.append(Bridge(osm_id=303, status="likely_damaged"))

    assert len(result.buildings) == 1
    assert result.buildings[0].exposure == "exposed_high"
    assert result.roads[0].exposed_length_m == 120.0
    assert result.bridges[0].status == "likely_damaged"
