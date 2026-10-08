import httpx
from typing import List, Dict, Any
from .auth import auth_manager

CATALOG_URL = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"

def search_s1_acquisitions(bbox: List[float], start_date: str, end_date: str) -> List[Dict[Any, Any]]:
    """
    Search CDSE STAC catalogue for Sentinel-1 GRD acquisitions.
    """
    token = auth_manager.get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "collections": ["sentinel-1-grd"],
        "bbox": bbox,
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "limit": 100,
        "query": {
            "s1:instrument_mode": {"eq": "IW"}
        }
    }
    
    # We might need pagination in the future, but 100 should be enough for a 60-day window
    response = httpx.post(CATALOG_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json().get("features", [])
