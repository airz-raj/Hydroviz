import httpx
from typing import List

OHSOME_API_URL = "https://api.ohsome.org/v1/elements/geometry"

def fetch_pre_event_buildings(bbox: List[float], event_date: str) -> dict:
    """
    Fetch building footprints prior to the event date using ohsome API.
    """
    # ohsome expects bboxes in lon,lat,lon,lat format
    bbox_str = ",".join(map(str, bbox))
    
    # We query building=* for the snapshot exactly before the event date
    payload = {
        "bboxes": bbox_str,
        "time": event_date,
        "filter": "building=*",
        "properties": "tags"
    }
    
    # Use exponential backoff or similar in production
    response = httpx.post(OHSOME_API_URL, data=payload)
    response.raise_for_status()
    
    return response.json()

def fetch_pre_event_roads(bbox: List[float], event_date: str) -> dict:
    """
    Fetch road network prior to the event date.
    """
    bbox_str = ",".join(map(str, bbox))
    
    payload = {
        "bboxes": bbox_str,
        "time": event_date,
        "filter": "highway=*",
        "properties": "tags"
    }
    
    response = httpx.post(OHSOME_API_URL, data=payload)
    response.raise_for_status()
    
    return response.json()
