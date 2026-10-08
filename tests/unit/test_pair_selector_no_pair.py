import pytest
from services.ingest.pair_selector import select_s1_pair

def test_pair_selector_no_pair():
    # Missing 2nd pre-event image for the orbit
    features = [
        {"properties": {"datetime": "2026-08-27T00:00:00Z"}, "sat:relative_orbit": 1, "sat:orbit_state": "ascending", "id": "post1"},
        {"properties": {"datetime": "2026-08-15T00:00:00Z"}, "sat:relative_orbit": 1, "sat:orbit_state": "ascending", "id": "pre1"}
    ]
    event_date = "2026-08-26"
    pair = select_s1_pair(features, event_date)
    assert pair is None
