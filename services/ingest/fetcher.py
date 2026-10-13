import os
import io
import time
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
from datetime import datetime, timezone
from .auth import auth_manager

import numpy as np

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

def _format_iso_time(t: str, is_end: bool = False) -> str:
    """Normalize timestamp string into standard ISO-8601 UTC format (YYYY-MM-DDTHH:MM:SSZ)."""
    if not t:
        return ""
    try:
        if "T" in t:
            dt = datetime.fromisoformat(str(t).replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            return f"{t}T23:59:59Z" if is_end else f"{t}T00:00:00Z"
    except Exception:
        if "T" in t:
            base = t.split('.')[0]
            if not base.endswith('Z'):
                base += 'Z'
            return base
        return f"{t}T23:59:59Z" if is_end else f"{t}T00:00:00Z"

def _validate_geotiff_bytes(content: bytes) -> tuple[bool, Optional[str]]:
    """
    Validates that content bytes form a valid, readable GeoTIFF with:
    - Standard TIFF magic header bytes
    - Valid non-empty dimensions (width, height, count)
    - Valid non-empty CRS
    - Non-degenerate geospatial transform
    - Positive spatial bounds
    - Non-zero count of finite, valid (non-nodata) pixels
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if len(content) < 512:
        msg = f"Response payload is too small to be a valid GeoTIFF ({len(content)} bytes < 512 bytes)."
        print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
        return False, msg

    # Validate TIFF header magic bytes (little-endian 'II*\0' or big-endian 'MM\0*')
    if not (content.startswith(b'II*\x00') or content.startswith(b'MM\x00*')):
        msg = "Response payload does not contain standard TIFF header magic bytes."
        print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
        return False, msg

    if rasterio is None:
        msg = "Rasterio is not available to validate GeoTIFF structure."
        print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
        return False, msg

    try:
        from rasterio.io import MemoryFile
        with MemoryFile(content) as memfile:
            with memfile.open() as ds:
                # 1. Dimensions check
                if ds.width < 16 or ds.height < 16:
                    msg = f"Invalid GeoTIFF dimensions: {ds.width}x{ds.height} (expected >= 16x16)."
                    print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
                    return False, msg
                if ds.count < 1:
                    msg = "GeoTIFF contains 0 raster bands."
                    print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
                    return False, msg

                # 2. CRS check
                if ds.crs is None or not ds.crs.is_valid:
                    msg = f"Invalid or missing CRS in GeoTIFF: {ds.crs}."
                    print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
                    return False, msg

                # 3. Transform check
                if ds.transform is None or ds.transform.is_identity:
                    msg = "GeoTIFF transform is missing or degenerate identity matrix."
                    print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
                    return False, msg

                # 4. Bounds check
                b = ds.bounds
                if not (b.right > b.left and b.top > b.bottom):
                    msg = f"Invalid GeoTIFF spatial bounds: [{b.left}, {b.bottom}, {b.right}, {b.top}]."
                    print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
                    return False, msg

                # 5. Nodata and valid pixels check (Band 1: VV)
                arr = ds.read(1)
                nodata = ds.nodata
                if nodata is not None:
                    valid_mask = (arr != nodata) & np.isfinite(arr)
                else:
                    valid_mask = np.isfinite(arr) & (arr > 0)

                valid_pixel_count = int(np.sum(valid_mask))
                if valid_pixel_count == 0:
                    msg = "GeoTIFF contains 0 valid pixels in band 1 (all pixels are nodata or non-finite)."
                    print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
                    return False, msg

                # If dual polarization is provided (Band 2: VH), verify it has valid pixels
                if ds.count >= 2:
                    arr2 = ds.read(2)
                    if nodata is not None:
                        valid_mask2 = (arr2 != nodata) & np.isfinite(arr2)
                    else:
                        valid_mask2 = np.isfinite(arr2) & (arr2 > 0)
                    if int(np.sum(valid_mask2)) == 0:
                        msg = "GeoTIFF band 2 (VH) contains 0 valid pixels (all pixels are nodata or non-finite)."
                        print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
                        return False, msg

                print(f"[{ts}] [RASTER_VALIDATION_PASSED] Valid GeoTIFF: {ds.width}x{ds.height}, {ds.count} bands, CRS={ds.crs}, valid_pixels={valid_pixel_count}")
                return True, None
    except Exception as val_err:
        msg = f"Rasterio could not parse GeoTIFF: {str(val_err)}"
        print(f"[{ts}] [RASTER_VALIDATION_FAILED] {msg}")
        return False, msg

@backoff.on_exception(
    backoff.expo,
    (httpx.RequestError, httpx.TimeoutException),
    max_tries=2,
    max_time=150
)
def fetch_s1_cog(bbox: List[float], start_time: str, end_time: str, output_path: str) -> bool:
    """
    Fetch S1 GRD data via Sentinel Hub Process API and save as GeoTIFF.
    Requests orthorectified GAMMA0_TERRAIN (VV + VH) using Copernicus 30m DEM.
    Validates GeoTIFF structure (CRS, transform, bounds, dimensions, valid pixels)
    before saving to output_path. Returns True on verified success, False otherwise.
    Cleans up output_path on any failure so stale files cannot be mistaken for valid results.
    Does not restart successful downloads unnecessarily if valid GeoTIFF is already present.
    """
    global _last_fetch_error
    _last_fetch_error = None
    ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Do not restart successful downloads unnecessarily if valid raster already exists on disk
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        try:
            with open(output_path, "rb") as existing_f:
                existing_bytes = existing_f.read()
            is_valid, _ = _validate_geotiff_bytes(existing_bytes)
            if is_valid:
                print(f"[{ts_now}] [DOWNLOAD_REUSE] Valid GeoTIFF already exists at {output_path} ({os.path.getsize(output_path)} bytes); skipping redundant download.")
                return True
        except Exception:
            pass
        # File exists but is corrupt or invalid; remove before downloading fresh
        try:
            os.remove(output_path)
        except OSError:
            pass
    elif os.path.exists(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass

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
    s_time = _format_iso_time(start_time, is_end=False)
    e_time = _format_iso_time(end_time, is_end=True)

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

    t0 = time.time()
    ts_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts_start}] [CDSE_REQUEST_START] Requesting S1 GRD GeoTIFF from CDSE Process API ({s_time} .. {e_time}) -> {os.path.basename(output_path)}")

    try:
        # Finite request timeout (90s) with 15s connect timeout for satellite provider processing
        req_timeout = httpx.Timeout(90.0, connect=15.0)
        response = httpx.post(PROCESS_URL, headers=headers, json=payload, timeout=req_timeout)
        elapsed = time.time() - t0
        ts_resp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts_resp}] [CDSE_REQUEST_END] Process API response {response.status_code} in {elapsed:.2f}s ({len(response.content)} bytes)")

        if response.status_code == 200 and len(response.content) > 1000:
            content_type = response.headers.get("content-type", "")
            tiff_bytes = None
            if "tar" in content_type:
                # Extract first TIFF from tar
                with tarfile.open(fileobj=io.BytesIO(response.content)) as tar:
                    for member in tar.getmembers():
                        if member.name.endswith(".tif") or member.name.endswith(".tiff"):
                            f = tar.extractfile(member)
                            if f:
                                tiff_bytes = f.read()
                                break
            else:
                tiff_bytes = response.content

            if not tiff_bytes:
                _last_fetch_error = "CDSE Process API response did not contain TIFF image data."
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass
                return False

            # Validate that the response is actually a readable, structurally valid GeoTIFF
            is_valid, val_err = _validate_geotiff_bytes(tiff_bytes)
            if not is_valid:
                _last_fetch_error = f"GeoTIFF response validation failed: {val_err}"
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass
                return False

            with open(output_path, "wb") as out:
                out.write(tiff_bytes)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] [DOWNLOAD_SUCCESS] Successfully saved {os.path.basename(output_path)} ({os.path.getsize(output_path)} bytes)")
                return True
            else:
                _last_fetch_error = "Written GeoTIFF file is empty or missing."
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass
                return False
        else:
            _last_fetch_error = f"CDSE Process API returned HTTP {response.status_code}: {response.text[:180]}"
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] [CDSE_REQUEST_FAILED] {_last_fetch_error}")
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass
    except httpx.TimeoutException as te:
        elapsed = time.time() - t0
        _last_fetch_error = f"CDSE Process API request timed out after {elapsed:.1f}s: {str(te)}"
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] [CDSE_REQUEST_TIMEOUT] {_last_fetch_error}")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
    except Exception as e:
        elapsed = time.time() - t0
        _last_fetch_error = f"CDSE Process API network exception after {elapsed:.1f}s: {str(e)}"
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] [CDSE_REQUEST_ERROR] {_last_fetch_error}")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

    return False
