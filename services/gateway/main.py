import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional
import uuid

# In Docker, shared module is mounted at /shared
sys.path.insert(0, '/shared')
# For local dev, fall back to relative path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))

from attribution import get_all_attributions

app = FastAPI(
    title="HydroViz Gateway API",
    description="Himalayan Flood Response Prototype — Educational use only",
    version="0.1.0"
)

from fastapi.staticfiles import StaticFiles

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




class JobRequest(BaseModel):
    bbox: list[float]
    event_date: str
    osm_snapshot: str = "2026-07-27"
    options: Optional[dict] = None

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError("bbox must have exactly 4 values: [minLon, minLat, maxLon, maxLat]")
        min_lon, min_lat, max_lon, max_lat = v
        if not (-180 <= min_lon < max_lon <= 180):
            raise ValueError("Invalid longitude range")
        if not (-90 <= min_lat < max_lat <= 90):
            raise ValueError("Invalid latitude range")
        return v


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "gateway"}


@app.get("/attribution")
def get_attribution():
    return get_all_attributions()


@app.post("/jobs")
def create_job(request: JobRequest):
    job_id = str(uuid.uuid4())
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job creation stub — pipeline not yet connected"
    }


@app.get("/jobs/{job_id}/status")
def get_job_status(job_id: str):
    return {
        "job_id": job_id,
        "status": "queued",
        "stage": None,
        "progress": 0.0,
        "message": "Status tracking stub"
    }

# Serve the dashboard UI at the root (must be placed after all API routes)
app.mount("/", StaticFiles(directory="/dashboard", html=True), name="dashboard")
