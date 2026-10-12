import os
import math
import httpx
from typing import List
from .auth import auth_manager

try:
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.transform import from_bounds as transform_from_bounds
except ImportError:
    rasterio = None

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

def fetch_dem_cog(bbox: List[float], output_path: str) -> bool:
    """
    Fetch Copernicus 30m DEM for the AOI and save as GeoTIFF.
    Prioritizes:
    1. CDSE Process API if credentials configured
    2. Public AWS Copernicus GLO-30 COG via rasterio
    Returns True if successfully saved, False otherwise.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    min_lon, min_lat, max_lon, max_lat = bbox

    # 1. Try CDSE Process API if configured
    if auth_manager.is_configured():
        try:
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
                    "width": 512,
                    "height": 512,
                    "responses": [
                        {"identifier": "default", "format": {"type": "image/tiff"}}
                    ]
                },
                "evalscript": DEM_EVAL_SCRIPT
            }
            response = httpx.post(PROCESS_URL, headers=headers, json=payload, timeout=30.0)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
        except Exception:
            pass

    # 2. Try streaming from AWS Copernicus WorldDEM-30 COG
    if rasterio:
        try:
            ilat = int(math.floor((min_lat + max_lat) / 2.0))
            ilon = int(math.floor((min_lon + max_lon) / 2.0))
            ns = "N" if ilat >= 0 else "S"
            ew = "E" if ilon >= 0 else "W"
            tile_name = f"Copernicus_DSM_COG_10_{ns}{abs(ilat):02d}_00_{ew}{abs(ilon):03d}_00_DEM"
            url = f"/vsicurl/https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/{tile_name}/{tile_name}.tif"

            with rasterio.open(url, timeout=6.0) as src:
                win = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
                data = src.read(1, window=win)
                h, w = data.shape
                transform = transform_from_bounds(min_lon, min_lat, max_lon, max_lat, w, h)
                meta = {
                    "driver": "GTiff",
                    "dtype": "float32",
                    "nodata": -9999.0,
                    "width": w,
                    "height": h,
                    "count": 1,
                    "crs": "EPSG:4326",
                    "transform": transform
                }
                with rasterio.open(output_path, "w", **meta) as dst:
                    dst.write(data.astype("float32"), 1)
                return True
        except Exception:
            pass

    return False
