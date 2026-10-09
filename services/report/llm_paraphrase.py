from typing import Dict, Any, Tuple
from .number_guard import validate_numbers, get_allowed_numbers

def paraphrase_summary(facts: Dict[str, Any], candidate_summary: str = None) -> Tuple[str, bool]:
    """
    Generate or validate an LLM-paraphrased executive summary.
    Enforces that ANY numeral in the summary strictly exists in facts.json.
    If hallucinated numbers are detected, reverts to the deterministic factual template.
    """
    allowed_numbers = get_allowed_numbers(facts)
    
    # Deterministic baseline template
    flood_area = facts.get("flood", {}).get("flooded_area_km2", 0.0)
    buildings = facts.get("exposure", {}).get("buildings_exposed_high", 0)
    settlements = facts.get("cutoff", {}).get("isolated_settlements", 0)
    roads_m = facts.get("exposure", {}).get("roads_exposed_length_m", 0.0)
    
    fallback_summary = (
        f"Rapid satellite analysis confirmed {flood_area} sq km of inundation. "
        f"A total of {buildings} structures and {settlements} settlements were identified "
        f"with significant vehicular cut-off affecting {roads_m} meters of regional roads."
    )
    
    if not candidate_summary:
        return fallback_summary, True
        
    is_valid, offending_num = validate_numbers(candidate_summary, allowed_numbers)
    if is_valid:
        return candidate_summary, True
    else:
        # Hallucination caught by Number Guard!
        return fallback_summary, False
