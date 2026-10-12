from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

def select_s1_pair(features: List[Dict[Any, Any]], event_date: str) -> Optional[Dict[str, Any]]:
    """
    Select pre-event and post-event acquisitions from the same relative orbit and direction.
    Prioritizes 2 pre-event acquisitions (matching Kuro Siwo 2-pre + 1-post input format),
    falling back to 1 pre-event if only one same-track pass is available in the window.
    """
    def parse_dt(dt_str: str) -> datetime:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    event_dt = parse_dt(event_date)
    
    # Group by (relative_orbit, orbit_state)
    groups = {}
    for feature in features:
        props = feature.get("properties", {})
        orbit = props.get("sat:relative_orbit")
        direction = str(props.get("sat:orbit_state", "")).upper()
        dt_str = props.get("datetime")
        
        if orbit is None or not direction or not dt_str:
            continue
            
        key = (orbit, direction)
        if key not in groups:
            groups[key] = []
        groups[key].append(feature)
        
    # First pass: try to find a group with at least 2 pre and 1 post
    for key, group_features in groups.items():
        sorted_features = sorted(
            group_features, 
            key=lambda f: parse_dt(f["properties"]["datetime"])
        )
        
        pre_events = [f for f in sorted_features if parse_dt(f["properties"]["datetime"]) < event_dt]
        post_events = [f for f in sorted_features if parse_dt(f["properties"]["datetime"]) >= event_dt]
        
        if len(pre_events) >= 2 and len(post_events) >= 1:
            return {
                "orbit": key[0],
                "direction": key[1],
                "pre_2": pre_events[-2],
                "pre_1": pre_events[-1],
                "post": post_events[0]
            }

    # Second pass: fallback to 1 pre and 1 post if 2 pre-events not available
    for key, group_features in groups.items():
        sorted_features = sorted(
            group_features, 
            key=lambda f: parse_dt(f["properties"]["datetime"])
        )
        pre_events = [f for f in sorted_features if parse_dt(f["properties"]["datetime"]) < event_dt]
        post_events = [f for f in sorted_features if parse_dt(f["properties"]["datetime"]) >= event_dt]
        
        if len(pre_events) >= 1 and len(post_events) >= 1:
            return {
                "orbit": key[0],
                "direction": key[1],
                "pre_2": pre_events[-1],
                "pre_1": pre_events[-1],
                "post": post_events[0]
            }
            
    return None
