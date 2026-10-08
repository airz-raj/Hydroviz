import asyncio
from .catalogue import search_s1_acquisitions
from .pair_selector import select_s1_pair
from .s2_checker import check_s2_cloud_cover
from .fetcher import fetch_s1_cog
from .dem_fetcher import fetch_dem_cog
from .osm_client import fetch_pre_event_buildings, fetch_pre_event_roads
from shared.attribution import add_provenance

async def process_job(job_id: str, bbox: list, event_date: str):
    """
    Orchestrate the ingestion process for a given job.
    """
    # 1. Search catalogue for S1
    # For a realistic window, we look 30 days before and 14 days after
    start_date = "2026-07-26" # Stub: calculate dynamically based on event_date - 30 days
    end_date = "2026-09-09"   # Stub: calculate dynamically based on event_date + 14 days
    
    features = search_s1_acquisitions(bbox, start_date, end_date)
    
    # 2. Select matching S1 pair
    pair = select_s1_pair(features, event_date)
    if not pair:
        return {"status": "FAILED", "reason": "NO_VALID_PAIR"}
        
    # 3. Check S2 availability
    has_s2, s2_clear_frac, s2_meta = check_s2_cloud_cover(bbox, event_date)
    
    # 4. In a real system, we would enqueue tasks to fetch these COGs in parallel
    # fetch_s1_cog(bbox, pair['pre_1']['properties']['datetime'], ...)
    # fetch_dem_cog(bbox, ...)
    # fetch_pre_event_buildings(bbox, event_date)
    
    # 5. Add provenance tracking
    add_provenance(job_id, "ingest", {
        "s1_pair": pair,
        "s2_used": has_s2
    })
    
    return {"status": "COMPLETED", "pair": pair, "has_s2": has_s2}
