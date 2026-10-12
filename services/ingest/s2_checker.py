import os
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from .auth import auth_manager

CATALOG_URL = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"

def check_s2_cloud_cover(bbox: List[float], event_date: str, cloud_threshold_pct: float = 40.0) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Check if a clear post-event Sentinel-2 scene is available via CDSE STAC catalogue.
    Returns (is_usable, clear_fraction, scene_metadata).
    If CDSE credentials are not configured or no clear scene exists, returns (False, 0.0, {}).
    """
    if not auth_manager.is_configured():
        return False, 0.0, {}

    try:
        token = auth_manager.get_token()
    except Exception:
        return False, 0.0, {}

    try:
        dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
    except Exception:
        dt = datetime(2026, 8, 26)

    start_date = dt.strftime("%Y-%m-%d")
    end_date = (dt + timedelta(days=14)).strftime("%Y-%m-%d")

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": bbox,
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "limit": 10,
        "query": {
            "eo:cloud_cover": {"lt": int(cloud_threshold_pct)}
        }
    }

    try:
        response = httpx.post(CATALOG_URL, headers=headers, json=payload, timeout=5.0)
        if response.status_code == 200:
            features = response.json().get("features", [])
            if features:
                # Pick lowest cloud cover scene
                features.sort(key=lambda f: f.get("properties", {}).get("eo:cloud_cover", 100.0))
                best = features[0]
                cc = float(best.get("properties", {}).get("eo:cloud_cover", 0.0))
                clear_fraction = round(max(0.0, (100.0 - cc) / 100.0), 3)
                return True, clear_fraction, best
    except Exception:
        pass

    return False, 0.0, {}
