import json
import os
import pytest
from services.geo_core.python.geo_core_py import classify_settlements

def test_settlement_disconnected_from_start_is_unknown():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "synthetic_graph.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data["nodes"]
    edges = data["edges"]
    targets = data["targets"]
    settlements = data["settlements"]

    # Even with no flood, village_isolated_island is disconnected from baseline targets
    classified = classify_settlements(nodes, edges, targets, settlements, flooded_edge_ids=set())
    island = next(s for s in classified if s["osm_id"] == 1003)
    
    # Must be 'unknown', NOT 'isolated'
    assert island["status"] == "unknown"
    assert island["baseline_distance_m"] is None
