import pytest
from services.ingest.pair_selector import select_s1_pair

def test_pair_selector_valid_pair():
    # Synthetic STAC features
    features = [
        {"properties": {"datetime": "2026-08-27T00:00:00Z"}, "sat:relative_orbit": 1, "sat:orbit_state": "ascending", "id": "post1"},
        {"properties": {"datetime": "2026-08-15T00:00:00Z"}, "sat:relative_orbit": 1, "sat:orbit_state": "ascending", "id": "pre1"},
        {"properties": {"datetime": "2026-08-03T00:00:00Z"}, "sat:relative_orbit": 1, "sat:orbit_state": "ascending", "id": "pre2"},
        {"properties": {"datetime": "2026-07-22T00:00:00Z"}, "sat:relative_orbit": 1, "sat:orbit_state": "ascending", "id": "pre3"}
    ]
    event_date = "2026-08-26"
    pair = select_s1_pair(features, event_date)
    assert pair is not None
    assert pair["post"]["id"] == "post1"
    assert pair["pre_1"]["id"] == "pre1"
    assert pair["pre_2"]["id"] == "pre2"
