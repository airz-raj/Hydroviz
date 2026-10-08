import httpx
from typing import List
from .auth import auth_manager

PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

DEM_EVAL_SCRIPT = """
//VERSION=3
function setup() {
  return {
    input: ["DEM"],
    output: { id: "default", bands: 1, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  return [sample.DEM];
}
"""

def fetch_dem_cog(bbox: List[float], output_path: str):
    """
    Fetch Copernicus 30m DEM for the AOI via CDSE Process API.
    """
    token = auth_manager.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "image/tiff"
    }
    
    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
            },
            "data": [{
                "type": "dem",
                "dataFilter": {
                    "demInstance": "COPERNICUS_30"
                }
            }]
        },
        "output": {
            "width": 1024,
            "height": 1024,
            "responses": [
                {"identifier": "default", "format": {"type": "image/tiff"}}
            ]
        },
        "evalscript": DEM_EVAL_SCRIPT
    }
    
    # Implementation stub: normally we would save the TIFF to output_path
    pass
