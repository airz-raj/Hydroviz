from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI(title="HydroViz Ingest Service")

class IngestRequest(BaseModel):
    job_id: Optional[str] = None
    bbox: List[float]
    event_date: str

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ingest"}

@app.post("/ingest")
async def trigger_ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    from .worker import process_job
    job_id = req.job_id or str(uuid.uuid4())
    background_tasks.add_task(process_job, job_id, req.bbox, req.event_date)
    return {"status": "accepted", "job_id": job_id}
