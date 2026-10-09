from typing import List, Dict, Any, Optional
from datetime import datetime

def select_s1_pair(features: List[Dict[Any, Any]], event_date: str) -> Optional[Dict[str, Any]]:
    """
    Select 2 pre-event and 1 post-event acquisitions from the same relative orbit and direction.
    """
    from datetime import timezone
    event_dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
    if event_dt.tzinfo is None:
        event_dt = event_dt.replace(tzinfo=timezone.utc)
    
    # Group by (relative_orbit, orbit_state)
    groups = {}
    for feature in features:
        props = feature.get("properties", {})
        orbit = props.get("sat:relative_orbit")
        direction = props.get("sat:orbit_state")
        dt_str = props.get("datetime")
        
        if orbit is None or direction is None or not dt_str:
            continue
            
        key = (orbit, direction)
        if key not in groups:
            groups[key] = []
        groups[key].append(feature)
        
    for key, group_features in groups.items():
        # Sort by datetime
        sorted_features = sorted(
            group_features, 
            key=lambda f: datetime.fromisoformat(f["properties"]["datetime"].replace('Z', '+00:00'))
        )
        
        pre_events = [f for f in sorted_features if datetime.fromisoformat(f["properties"]["datetime"].replace('Z', '+00:00')) < event_dt]
        post_events = [f for f in sorted_features if datetime.fromisoformat(f["properties"]["datetime"].replace('Z', '+00:00')) >= event_dt]
        
        if len(pre_events) >= 2 and len(post_events) >= 1:
            # Take the 2 most recent pre-events
            selected_pre = pre_events[-2:]
            # Take the earliest post-event
            selected_post = post_events[0]
            
            return {
                "orbit": key[0],
                "direction": key[1],
                "pre_2": selected_pre[0],
                "pre_1": selected_pre[1],
                "post": selected_post
            }
            
    return None
