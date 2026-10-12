import os
import io
import tarfile
import httpx
try:
    import backoff
except ImportError:
    class _MockBackoff:
        @staticmethod
        def on_exception(*args, **kwargs):
            def decorator(f):
                return f
            return decorator
        expo = None
    backoff = _MockBackoff()

try:
    import rasterio
except ImportError:
    rasterio = None

from typing import List, Dict, Any, Optional
from .auth import auth_manager

PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

EVAL_SCRIPT_TIFF = """
//VERSION=3
function setup() {
  return {
    input: ["VV", "VH"],
    output: { id: "default", bands: 2, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(samples) {
  return [samples.VV, samples.VH];
}
"""

_last_fetch_error: Optional[str] = None

def get_last_fetch_error() -> Optional[str]:
    return _last_fetch_error

@backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3)
def fetch_s1_cog(bbox: List[float], start_time: str, end_time: str, output_path: str) -> bool:
    """
    Fetch S1 GRD data via Sentinel Hub Process API and save as GeoTIFF.
    Requests orthorectified GAMMA0_TERRAIN (VV + VH) using Copernicus 30m DEM.
    Returns True if successfully retrieved and saved, False otherwise.
    """
    global _last_fetch_error
    _last_fetch_error = None

    if not auth_manager.is_configured():
        _last_fetch_error = "CDSE credentials not configured in .env (CDSE_CLIENT_ID / CDSE_CLIENT_SECRET)"
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    try:
        token = auth_manager.get_token()
    except Exception as e:
        _last_fetch_error = str(e)
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "image/tiff"
    }

    # Format timestamps for CDSE API
    s_time = start_time if "T" in start_time else f"{start_time}T00:00:00Z"
    e_time = end_time if "T" in end_time else f"{end_time}T23:59:59Z"

    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
            },
            "data": [{
                "type": "sentinel-1-grd",
                "dataFilter": {
                    "timeRange": {
                        "from": s_time,
                        "to": e_time
                    },
                    "acquisitionMode": "IW",
                    "polarization": "DV",
                    "resolution": "HIGH"
                },
                "processing": {
                    "backCoeff": "GAMMA0_TERRAIN",
                    "orthorectify": True,
                    "demInstance": "COPERNICUS_30"
                }
            }]
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [
                {"identifier": "default", "format": {"type": "image/tiff"}}
            ]
        },
        "evalscript": EVAL_SCRIPT_TIFF
    }

    try:
        response = httpx.post(PROCESS_URL, headers=headers, json=payload, timeout=60.0)
        if response.status_code == 200 and len(response.content) > 1000:
            content_type = response.headers.get("content-type", "")
            if "tar" in content_type:
                # Extract first TIFF from tar
                with tarfile.open(fileobj=io.BytesIO(response.content)) as tar:
                    for member in tar.getmembers():
                        if member.name.endswith(".tif") or member.name.endswith(".tiff"):
                            f = tar.extractfile(member)
                            if f:
                                with open(output_path, "wb") as out:
                                    out.write(f.read())
                                return True
            else:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
        else:
            _last_fetch_error = f"CDSE Process API returned HTTP {response.status_code}: {response.text[:180]}"
    except Exception as e:
        _last_fetch_error = f"CDSE Process API network exception: {str(e)}"

    return False
