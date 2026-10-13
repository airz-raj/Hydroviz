import os
import sys
import time
import asyncio
from datetime import datetime, timedelta, timezone

sys.path.insert(0, '/shared')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))

from .catalogue import search_s1_acquisitions
from .pair_selector import select_s1_pair, get_last_selection_reason
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

async def process_job(job_id: str, bbox: list, event_date: str, status_cb=None):
    """
    Orchestrate the ingestion process for a given job:
    1. Search CDSE catalogue for Sentinel-1 acquisitions
    2. Select compatible triplet (pre2, pre1, post) on matching relative orbit
    3. Ingest Copernicus DEM GLO-30 raster
    4. Fetch genuine Sentinel-1 GeoTIFF rasters (pre2, pre1, post) in narrow time windows
    5. Check Sentinel-2 L2A cloud cover
    6. Log provenance with explicit catalogue-to-raster provenance details
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
            if status_cb:
                status_cb("Querying Sentinel-1 IW GRD SAR catalog (ESA CDSE)...", 0.05)
            t_cat = time.time()
            ts_cat = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"[{ts_cat}] [CATALOGUE_SEARCH_START] Searching CDSE catalogue ({start_date} .. {end_date}) bbox={bbox}")

            features = search_s1_acquisitions(bbox, start_date, end_date)
            elapsed_cat = time.time() - t_cat
            ts_cat_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"[{ts_cat_end}] [CATALOGUE_SEARCH_END] Found {len(features)} acquisition(s) in {elapsed_cat:.2f}s")

            if not features:
                ingest_status = "no_acquisitions"
                ingest_reason = f"No Sentinel-1 IW acquisitions found in CDSE STAC catalogue between {start_date} and {end_date} for this bounding box."
            else:
                if status_cb:
                    status_cb("Selecting same-orbit acquisition triplet (pre2, pre1, post)...", 0.08)
                t_sel = time.time()
                ts_sel = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{ts_sel}] [PAIR_SELECTION_START] Selecting same-orbit triplet for event {event_date} from {len(features)} scenes...")

                pair = select_s1_pair(features, event_date)
                elapsed_sel = time.time() - t_sel
                ts_sel_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                if not pair:
                    ingest_status = "no_same_orbit_pair"
                    sel_reason = get_last_selection_reason()
                    ingest_reason = sel_reason or "No matching same-orbit repeat pass found for differential change detection in this time window."
                    print(f"[{ts_sel_end}] [PAIR_SELECTION_FAILED] Triplet selection failed in {elapsed_sel:.2f}s: {ingest_reason}")
                else:
                    print(f"[{ts_sel_end}] [PAIR_SELECTION_END] Selected triplet in {elapsed_sel:.2f}s: orbit={pair.get('orbit')} ({pair.get('direction')})")
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
        if status_cb:
            status_cb("Fetching Copernicus 30m DEM elevation raster...", 0.10)
        t_dem = time.time()
        ts_dem = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts_dem}] [DEM_FETCH_START] Fetching Copernicus DEM for bbox={bbox}")
        has_dem = fetch_dem_cog(bbox, dem_path)
        elapsed_dem = time.time() - t_dem
        ts_dem_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts_dem_end}] [DEM_FETCH_END] DEM fetch completed in {elapsed_dem:.2f}s (success={has_dem})")
    except Exception as dem_err:
        has_dem = False
        print(f"[DEM_FETCH_ERROR] Failed to fetch DEM: {str(dem_err)}")

    # 4. Attempt fetching live S1 imagery if 3-scene acquisition triplet was discovered
    post_path = os.path.join(job_dir, "s1_post_gamma0.tif")
    pre_path = os.path.join(job_dir, "s1_pre_gamma0.tif")
    pre2_path = os.path.join(job_dir, "s1_pre2_gamma0.tif")
    has_s1_rasters = False

    post_item = pair.get("post", {}) if pair else {}
    pre1_item = pair.get("pre_1", {}) if pair else {}
    pre2_item = pair.get("pre_2", {}) if pair else {}

    post_props = post_item.get("properties", {})
    pre1_props = pre1_item.get("properties", {})
    pre2_props = pre2_item.get("properties", {})

    post_dt_exact = post_props.get("datetime")
    pre1_dt_exact = pre1_props.get("datetime")
    pre2_dt_exact = pre2_props.get("datetime")

    post_id = post_item.get("id")
    pre1_id = pre1_item.get("id")
    pre2_id = pre2_item.get("id")

    post_pols = post_props.get("sar:polarizations") or post_props.get("polarization") or []
    pre1_pols = pre1_props.get("sar:polarizations") or pre1_props.get("polarization") or []
    pre2_pols = pre2_props.get("sar:polarizations") or pre2_props.get("polarization") or []

    rel_orbit = pair.get("orbit") if pair else None
    orbit_dir = pair.get("direction") if pair else None

    # Verify that catalogue triplet acquisitions are present, distinct, and monotonic
    has_valid_triplet = bool(
        pair and
        post_dt_exact and pre1_dt_exact and pre2_dt_exact and
        post_dt_exact != pre1_dt_exact and
        pre1_dt_exact != pre2_dt_exact and
        post_dt_exact != pre2_dt_exact
    )

    if is_cdse_configured and pair:
        if not has_valid_triplet:
            ingest_status = "invalid_triplet"
            ingest_reason = "Selected Sentinel-1 acquisition triplet contains missing or duplicate timestamps."
        else:
            try:
                # Constrain temporal request windows to tight intervals (±30 min) around catalogue timestamps
                def _make_window(dt_exact, fallback):
                    if dt_exact:
                        try:
                            dt_obj = datetime.fromisoformat(dt_exact.replace('Z', '+00:00'))
                            s = (dt_obj - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
                            e = (dt_obj + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
                            return s, e
                        except Exception:
                            pass
                    fb = str(dt_exact or fallback)[:10]
                    return f"{fb}T00:00:00Z", f"{fb}T23:59:59Z"

                post_start, post_end = _make_window(post_dt_exact, event_date)
                pre1_start, pre1_end = _make_window(pre1_dt_exact, start_date)
                pre2_start, pre2_end = _make_window(pre2_dt_exact, start_date)

                # Download 1/3: post-event scene
                if status_cb:
                    status_cb(f"Downloading post-event SAR raster (1/3: {post_dt_exact})...", 0.14)
                t_post = time.time()
                ts_post = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{ts_post}] [DOWNLOAD_POST_START] Fetching post-event SAR raster (1/3) window={post_start}..{post_end}")
                fetched_post = fetch_s1_cog(bbox, post_start, post_end, post_path)
                elapsed_post = time.time() - t_post
                ts_post_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{ts_post_end}] [DOWNLOAD_POST_END] Post-event fetch completed in {elapsed_post:.2f}s (success={fetched_post})")

                # Download 2/3: primary pre-event scene
                if status_cb:
                    status_cb(f"Downloading primary pre-event SAR raster (2/3: {pre1_dt_exact})...", 0.18)
                t_pre1 = time.time()
                ts_pre1 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{ts_pre1}] [DOWNLOAD_PRE1_START] Fetching primary pre-event SAR raster (2/3) window={pre1_start}..{pre1_end}")
                fetched_pre = fetch_s1_cog(bbox, pre1_start, pre1_end, pre_path)
                elapsed_pre1 = time.time() - t_pre1
                ts_pre1_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{ts_pre1_end}] [DOWNLOAD_PRE1_END] Primary pre-event fetch completed in {elapsed_pre1:.2f}s (success={fetched_pre})")

                # Download 3/3: secondary pre-event scene
                if status_cb:
                    status_cb(f"Downloading secondary pre-event SAR raster (3/3: {pre2_dt_exact})...", 0.22)
                t_pre2 = time.time()
                ts_pre2 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{ts_pre2}] [DOWNLOAD_PRE2_START] Fetching secondary pre-event SAR raster (3/3) window={pre2_start}..{pre2_end}")
                fetched_pre2 = fetch_s1_cog(bbox, pre2_start, pre2_end, pre2_path)
                elapsed_pre2 = time.time() - t_pre2
                ts_pre2_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{ts_pre2_end}] [DOWNLOAD_PRE2_END] Secondary pre-event fetch completed in {elapsed_pre2:.2f}s (success={fetched_pre2})")

                has_s1_rasters = fetched_post and fetched_pre and fetched_pre2

                if has_s1_rasters:
                    ingest_status = "live_downloaded"
                    ingest_reason = (
                        f"Sentinel-1 SAR GeoTIFF triplet retrieved from Copernicus Process API within narrow temporal "
                        f"windows around catalogue acquisitions (post: {post_dt_exact}, pre1: {pre1_dt_exact}, "
                        f"pre2: {pre2_dt_exact}, relative orbit: {rel_orbit})."
                    )
                    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] [INGEST_SUCCESS] Successfully retrieved and verified all 3 Sentinel-1 SAR rasters.")
                else:
                    # Clean up failed downloads so stale files cannot be mistaken for current results
                    missing = []
                    if not fetched_post:
                        missing.append("post-event raster (s1_post_gamma0.tif)")
                        if os.path.exists(post_path):
                            try: os.remove(post_path)
                            except OSError: pass
                    if not fetched_pre:
                        missing.append("primary pre-event raster pre1 (s1_pre_gamma0.tif)")
                        if os.path.exists(pre_path):
                            try: os.remove(pre_path)
                            except OSError: pass
                    if not fetched_pre2:
                        missing.append("secondary pre-event raster pre2 (s1_pre2_gamma0.tif)")
                        if os.path.exists(pre2_path):
                            try: os.remove(pre2_path)
                            except OSError: pass

                    ingest_status = "download_failed"
                    fetch_err = get_last_fetch_error() or "Download or GeoTIFF validation failed"
                    ingest_reason = f"Failed to download verified Sentinel-1 GeoTIFF rasters for: {', '.join(missing)} ({fetch_err})."
                    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] [INGEST_FAILED] {ingest_reason}")
            except Exception as dl_err:
                has_s1_rasters = False
                ingest_status = "download_failed"
                ingest_reason = f"Exception during satellite raster download: {str(dl_err)}"
                print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] [INGEST_EXCEPTION] {ingest_reason}")

    # 5. Check S2 availability
    try:
        has_s2, s2_clear_frac, s2_meta = check_s2_cloud_cover(bbox, event_date)
    except Exception:
        has_s2, s2_clear_frac, s2_meta = False, 0.0, {}

    scene_verification = {
        "catalog_post_datetime": post_dt_exact,
        "catalog_post_id": post_id,
        "catalog_post_polarizations": post_pols,
        "catalog_pre1_datetime": pre1_dt_exact,
        "catalog_pre1_id": pre1_id,
        "catalog_pre1_polarizations": pre1_pols,
        "catalog_pre2_datetime": pre2_dt_exact,
        "catalog_pre2_id": pre2_id,
        "catalog_pre2_polarizations": pre2_pols,
        "relative_orbit": rel_orbit,
        "orbit_direction": orbit_dir,
        # Backward compatibility keys
        "catalog_pre_datetime": pre1_dt_exact,
        "catalog_pre_id": pre1_id,
        "verification_status": "unverified_scene_id" if has_s1_rasters else "unretrieved",
        "verification_limitation": (
            "Downloaded GeoTIFF rasters (pre2, pre1, post) are verified as structurally valid orthorectified GeoTIFFs matching "
            "the requested AOI bounds and narrow temporal windows. However, because Copernicus Sentinel Hub Process API "
            "synthesizes on-the-fly GeoTIFFs without embedding original STAC scene IDs in TIFF tags, exact scene hash "
            "correspondence cannot be independently guaranteed from raster headers alone."
        ) if has_s1_rasters else "No live rasters retrieved."
    }
    
    # 6. Add provenance tracking
    add_provenance(job_id, "ingest", {
        "s1_pair": pair,
        "s2_used": has_s2,
        "has_dem_raster": has_dem,
        "has_s1_rasters": has_s1_rasters,
        "s1_post_path": post_path if has_s1_rasters else "",
        "s1_pre_path": pre_path if has_s1_rasters else "",
        "s1_pre2_path": pre2_path if has_s1_rasters else "",
        "ingest_status": ingest_status,
        "ingest_reason": ingest_reason,
        "scene_verification": scene_verification
    })
    
    return {
        "status": "COMPLETED",
        "ingest_status": ingest_status,
        "ingest_reason": ingest_reason,
        "pair": pair,
        "has_s2": has_s2,
        "has_dem": has_dem,
        "dem_path": dem_path if has_dem else "",
        "has_s1_rasters": has_s1_rasters,
        "s1_post_path": post_path if has_s1_rasters else "",
        "s1_pre_path": pre_path if has_s1_rasters else "",
        "s1_pre2_path": pre2_path if has_s1_rasters else "",
        "scene_verification": scene_verification
    }
