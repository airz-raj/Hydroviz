import httpx
from typing import List, Dict, Any
from .auth import auth_manager

CATALOG_URL = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"

def search_s1_acquisitions(bbox: List[float], start_date: str, end_date: str) -> List[Dict[Any, Any]]:
    """
    Search CDSE STAC catalogue for Sentinel-1 GRD acquisitions over the AOI and time window.
    Filters client-side for IW instrument mode.
    """
    token = auth_manager.get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Ensure ISO UTC formatting
    s_dt = f"{start_date}T00:00:00Z" if "T" not in start_date else start_date
    e_dt = f"{end_date}T23:59:59Z" if "T" not in end_date else end_date

    payload = {
        "collections": ["sentinel-1-grd"],
        "bbox": bbox,
        "datetime": f"{s_dt}/{e_dt}",
        "limit": 100
    }
    
    response = httpx.post(CATALOG_URL, headers=headers, json=payload, timeout=15.0)
    response.raise_for_status()
    
    features = response.json().get("features", [])
    
    # Filter client-side for Interferometric Wide swath (IW) mode
    iw_features = [
        f for f in features
        if f.get("properties", {}).get("sar:instrument_mode", "IW").upper() == "IW"
    ]
    
    return iw_features if iw_features else features
