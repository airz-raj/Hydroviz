import asyncio
import sys, os
sys.path.insert(0, os.path.abspath("."))
from services.gateway.main import _run_job_pipeline, JobRequest, get_job_facts

async def main():
    aois = [
        ('Melamchi', [85.50, 27.80, 85.65, 27.95]),
        ('Bhote Koshi', [85.80, 27.90, 85.95, 28.05]),
        ('Helambu', [85.45, 28.00, 85.60, 28.15]),
        ('Kathmandu', [85.25, 27.65, 85.40, 27.80]),
        ('Trishuli', [85.10, 27.90, 85.25, 28.05])
    ]
    print("\n--- AOI REGRESSION VERIFICATION ---")
    for name, bbox in aois:
        jid = "chk-" + name.lower().replace(" ", "-")
        await _run_job_pipeline(jid, JobRequest(bbox=bbox, event_date="2026-08-26"))
        f = get_job_facts(jid)
        mode = f.get("mode", "?")
        flood = f.get("flood", {}).get("flooded_area_km2", 0)
        buildings = f.get("exposure", {}).get("buildings_exposed_high", 0)
        roads = f.get("exposure", {}).get("roads_km", {}).get("exposed", 0)
        print(f"{name:15s} | Mode: {mode:16s} | Flood: {flood:4.1f} km2 | Buildings: {buildings:2d} | Roads: {roads:4.1f} km")

if __name__ == "__main__":
    asyncio.run(main())
