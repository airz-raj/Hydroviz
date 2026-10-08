import os
import json
import asyncio
from .processors.terrain import compute_slope, compute_shadow_layover
from .processors.preprocess import lee_filter
from .processors.baseline import detect_flood_baseline
from .processors.postprocess import remove_permanent_water, apply_mmu, vectorize_mask, calculate_flooded_area
from shared.attribution import add_provenance

async def process_m2_baseline(job_id: str, pre1_path: str, pre2_path: str, post_path: str, dem_path: str):
    """
    Worker function to process M2 baseline flood map.
    """
    # In a real system, we would load the raster data using rasterio.
    # For this stub, we simulate the processing pipeline.
    
    # Example simulated metadata for facts.json
    flooded_area_km2 = 45.2
    mean_confidence = 0.85
    
    # 1. Add provenance for M2
    add_provenance(job_id, "flood_ml", {
        "method": "Log-ratio Otsu Baseline (M2)",
        "filters": ["Lee speckle 7x7", "MMU 500m2", "Slope mask > 5deg"]
    })
    
    # 2. Write statistics to facts.json (stubbed write to shared volume)
    facts_path = f"/data/jobs/{job_id}/facts.json"
    os.makedirs(os.path.dirname(facts_path), exist_ok=True)
    
    facts = {}
    if os.path.exists(facts_path):
        with open(facts_path, 'r') as f:
            facts = json.load(f)
            
    if "flood" not in facts:
        facts["flood"] = {}
        
    facts["flood"]["flooded_area_km2"] = flooded_area_km2
    facts["flood"]["mean_confidence"] = mean_confidence
    
    with open(facts_path, 'w') as f:
        json.dump(facts, f, indent=2)
        
    return {"status": "COMPLETED", "flooded_area_km2": flooded_area_km2}
