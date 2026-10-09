import json
import os
import pytest
from services.geo_core.python.geo_core_py import classify_settlements, dijkstra_shortest_paths

def load_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "synthetic_graph.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_cutoff_baseline_and_blocked():
    data = load_fixture()
    nodes = data["nodes"]
    edges = data["edges"]
    targets = data["targets"]
    settlements = data["settlements"]

    # Baseline: edge_primary_access is open
    classified_baseline = classify_settlements(nodes, edges, targets, settlements, flooded_edge_ids=set())
    melamchi = next(s for s in classified_baseline if s["osm_id"] == 1001)
    assert melamchi["status"] == "reachable"
    assert melamchi["baseline_distance_m"] == 1000.0

    # Flood blocks edge_primary_access:
    # Alternate path exists via junction_1: 3000 + 500 = 3500. Detour factor = 3500/1000 = 3.5 (> 1.5 threshold)
    classified_flood = classify_settlements(
        nodes, edges, targets, settlements,
        flooded_edge_ids={"edge_primary_access"},
        detour_threshold_factor=1.5
    )
    melamchi_post = next(s for s in classified_flood if s["osm_id"] == 1001)
    assert melamchi_post["status"] == "detour"
    assert melamchi_post["detour_factor"] == 3.5

    # If both primary and detour are blocked, settlement becomes isolated
    classified_isolated = classify_settlements(
        nodes, edges, targets, settlements,
        flooded_edge_ids={"edge_primary_access", "edge_detour_highland"}
    )
    melamchi_iso = next(s for s in classified_isolated if s["osm_id"] == 1001)
    assert melamchi_iso["status"] == "isolated"
    assert melamchi_iso["post_event_distance_m"] is None
