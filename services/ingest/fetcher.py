import httpx
import backoff
import rasterio
from typing import List, Dict, Any
from .auth import auth_manager

PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Evaluation script for Sentinel-1 GRD (GAMMA0_TERRAIN)
EVAL_SCRIPT = """
//VERSION=3
function setup() {
  return {
    input: ["VV", "VH", "dataMask"],
    output: [
      { id: "VV", bands: 1, sampleType: "FLOAT32" },
      { id: "VH", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1, sampleType: "UINT8" }
    ]
  };
}
function evaluatePixel(samples) {
  return {
    VV: [samples.VV],
    VH: [samples.VH],
    dataMask: [samples.dataMask]
  };
}
"""

@backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3)
def fetch_s1_cog(bbox: List[float], start_time: str, end_time: str, output_path: str):
    """
    Fetch S1 GRD data via Sentinel Hub Process API and save as COG.
    Requests orthorectified GAMMA0_TERRAIN using Copernicus 30m DEM.
    """
    token = auth_manager.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/tar"
    }
    
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
                        "from": start_time,
                        "to": end_time
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
            "width": 1024,  # Adjust based on bbox size for 10m resolution
            "height": 1024,
            "responses": [
                {"identifier": "VV", "format": {"type": "image/tiff"}},
                {"identifier": "VH", "format": {"type": "image/tiff"}},
                {"identifier": "dataMask", "format": {"type": "image/tiff"}}
            ]
        },
        "evalscript": EVAL_SCRIPT
    }
    
    # In a real implementation, we would handle the tar response and save COGs.
    # We would also calculate the exact width/height based on bbox to ensure 10m resolution.
    # This is a stub for the hackathon prototype.
    pass
