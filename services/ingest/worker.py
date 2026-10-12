import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone

sys.path.insert(0, '/shared')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))

from .catalogue import search_s1_acquisitions
from .pair_selector import select_s1_pair
from .s2_checker import check_s2_cloud_cover
from .fetcher import fetch_s1_cog
from .dem_fetcher import fetch_dem_cog

try:
    from shared.attribution import add_provenance
except ImportError:
    def add_provenance(job_id, stage, metadata):
        pass

def _get_data_dir() -> str:
    data_dir = os.getenv("DATA_DIR")
    if not data_dir:
        local_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        data_dir = local_data if os.path.exists(local_data) else os.path.abspath("./data")
    return data_dir

async def process_job(job_id: str, bbox: list, event_date: str):
    """
    Orchestrate the ingestion process for a given job:
    1. Search CDSE catalogue for Sentinel-1 acquisitions
    2. Select compatible pre/post pair (same orbit and direction)
    3. Ingest Copernicus DEM GLO-30 raster
    4. Check Sentinel-2 L2A cloud cover
    5. Log provenance
    """
    data_dir = _get_data_dir()
    job_dir = os.path.join(data_dir, "jobs", job_id)
    os.makedirs(job_dir, exist_ok=True)

    # 1. Search catalogue for S1 dynamically around event_date
    try:
        dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
    except Exception:
        dt = datetime(2026, 8, 26, tzinfo=timezone.utc)
        
    start_date = (dt - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (dt + timedelta(days=14)).strftime("%Y-%m-%d")
    
    # Check CDSE configuration state
    from .auth import auth_manager
    from .fetcher import get_last_fetch_error

    is_cdse_configured = auth_manager.is_configured()
    ingest_status = "offline"
    ingest_reason = ""
    features = []
    pair = None

    if not is_cdse_configured:
        ingest_status = "credentials_missing"
        ingest_reason = "CDSE credentials (CDSE_CLIENT_ID / CDSE_CLIENT_SECRET) not configured in .env."
    else:
        try:
            features = search_s1_acquisitions(bbox, start_date, end_date)
            if not features:
                ingest_status = "no_acquisitions"
                ingest_reason = f"No Sentinel-1 IW acquisitions found in CDSE STAC catalogue between {start_date} and {end_date} for this bounding box."
            else:
                pair = select_s1_pair(features, event_date)
                if not pair:
                    ingest_status = "no_same_orbit_pair"
                    ingest_reason = "No matching same-orbit repeat pass found for differential change detection in this time window."
        except PermissionError as pe:
            ingest_status = "auth_failed"
            ingest_reason = str(pe)
        except Exception as se:
            ingest_status = "catalogue_error"
            ingest_reason = f"CDSE catalogue query failed: {str(se)}"

    # 3. Fetch Copernicus 30m DEM for the AOI
    dem_path = os.path.join(job_dir, "dem_copernicus_30m.tif")
    has_dem = False
    try:
        has_dem = fetch_dem_cog(bbox, dem_path)
    except Exception:
        has_dem = False

    # 4. Attempt fetching live S1 imagery if pair was discovered
    post_path = os.path.join(job_dir, "s1_post_gamma0.tif")
    pre_path = os.path.join(job_dir, "s1_pre_gamma0.tif")
    has_s1_rasters = False

    if is_cdse_configured and pair:
        try:
            post_dt = pair.get("post", {}).get("properties", {}).get("datetime", event_date)[:10]
            pre_dt = pair.get("pre_1", {}).get("properties", {}).get("datetime", start_date)[:10]
            fetched_post = fetch_s1_cog(bbox, post_dt, post_dt, post_path)
            fetched_pre = fetch_s1_cog(bbox, pre_dt, pre_dt, pre_path)
            has_s1_rasters = fetched_post and fetched_pre
            if has_s1_rasters:
                ingest_status = "live_downloaded"
                ingest_reason = "Live Sentinel-1 SAR GeoTIFF rasters successfully retrieved from Copernicus Process API."
            else:
                ingest_status = "download_failed"
                fetch_err = get_last_fetch_error() or "Download failed"
                ingest_reason = f"Failed to download Sentinel-1 GeoTIFF rasters from Copernicus Process API ({fetch_err})."
        except Exception as dl_err:
            has_s1_rasters = False
            ingest_status = "download_failed"
            ingest_reason = f"Exception during satellite raster download: {str(dl_err)}"

    # 5. Check S2 availability
    try:
        has_s2, s2_clear_frac, s2_meta = check_s2_cloud_cover(bbox, event_date)
    except Exception:
        has_s2, s2_clear_frac, s2_meta = False, 0.0, {}
    
    # 6. Add provenance tracking
    add_provenance(job_id, "ingest", {
        "s1_pair": pair,
        "s2_used": has_s2,
        "has_dem_raster": has_dem,
        "has_s1_rasters": has_s1_rasters,
        "ingest_status": ingest_status,
        "ingest_reason": ingest_reason
    })
    
    return {
        "status": "COMPLETED" if has_s1_rasters else "PARTIAL",
        "ingest_status": ingest_status,
        "ingest_reason": ingest_reason,
        "pair": pair,
        "has_s2": has_s2,
        "has_dem": has_dem,
        "dem_path": dem_path if has_dem else "",
        "has_s1_rasters": has_s1_rasters,
        "s1_post_path": post_path if has_s1_rasters else "",
        "s1_pre_path": pre_path if has_s1_rasters else ""
    }
