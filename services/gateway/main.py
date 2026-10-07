import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the parent directory to sys.path to allow importing from shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.attribution import get_all_attributions

app = FastAPI(title="HydroViz Gateway API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "gateway"}

@app.get("/attribution")
def get_attribution():
    return get_all_attributions()

class JobRequest(BaseModel):
    bbox: list[float]
    event_date: str
    osm_snapshot: str = "2026-07-27"

@app.post("/jobs")
def create_job(request: JobRequest):
    return {"message": "Job creation stub", "job_id": "dummy-uuid"}
