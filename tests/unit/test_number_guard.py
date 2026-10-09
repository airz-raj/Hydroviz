import pytest
from services.report.number_guard import validate_numbers, get_allowed_numbers, extract_numbers

def test_number_guard_allowed():
    facts = {
        "flood": {"flooded_area_km2": 38.4, "mean_confidence": 0.95},
        "exposure": {"buildings_exposed": 142, "roads_m": 3500.0}
    }
    allowed = get_allowed_numbers(facts)
    assert 38.4 in allowed
    assert 142.0 in allowed
    assert 3500.0 in allowed

    valid_text = "The satellite detected 38.4 sq km flooded, with 142 buildings affected."
    is_valid, offending = validate_numbers(valid_text, allowed)
    assert is_valid is True
    assert offending is None

def test_number_guard_catches_hallucination():
    facts = {
        "flood": {"flooded_area_km2": 38.4},
        "exposure": {"buildings_exposed": 142}
    }
    allowed = get_allowed_numbers(facts)

    # Hallucinated number 999 not in facts
    hallucinated_text = "The flood affected 999 structures across the valley."
    is_valid, offending = validate_numbers(hallucinated_text, allowed)
    assert is_valid is False
    assert offending == "999"
