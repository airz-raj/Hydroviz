from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator

class JobRequest(BaseModel):
    job_id: Optional[str] = None
    bbox: List[float]
    event_date: str
    osm_snapshot: str = "2026-07-27"
    options: Optional[dict] = None

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError("bbox must have exactly 4 values: [minLon, minLat, maxLon, maxLat]")
        try:
            c1, c2, c3, c4 = [float(x) for x in v]
        except (ValueError, TypeError):
            raise ValueError("bbox coordinates must be valid numbers")
        
        # Auto-detect if Lat/Lon order was passed (e.g. [lat1, lon1, lat2, lon2])
        if (20.0 <= min(c1, c3) <= 35.0 and 70.0 <= min(c2, c4) <= 95.0) or (abs(c1) < 45.0 and abs(c2) > 60.0):
            min_lon = min(c2, c4)
            max_lon = max(c2, c4)
            min_lat = min(c1, c3)
            max_lat = max(c1, c3)
        else:
            min_lon = min(c1, c3)
            max_lon = max(c1, c3)
            min_lat = min(c2, c4)
            max_lat = max(c2, c4)
            
        if min_lon == max_lon:
            max_lon += 0.01
        if min_lat == max_lat:
            max_lat += 0.01

        if not (-180 <= min_lon < max_lon <= 180):
            raise ValueError("Invalid longitude range (-180 to 180)")
        if not (-90 <= min_lat < max_lat <= 90):
            raise ValueError("Invalid latitude range (-90 to 90)")
            
        return [round(min_lon, 5), round(min_lat, 5), round(max_lon, 5), round(max_lat, 5)]

class TraceRequest(BaseModel):
    bbox: List[float]
    origin: List[float]  # [lon, lat]

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError("bbox must have 4 coordinates")
        return [float(x) for x in v]

    @field_validator("origin")
    @classmethod
    def validate_origin(cls, v):
        if len(v) != 2:
            raise ValueError("origin must be [lon, lat]")
        return [float(v[0]), float(v[1])]

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    stage: str
    progress: float
    stages: dict
    partial_results: dict
    error: Optional[str] = None
    created_at: str
    updated_at: str

class JobSummary(BaseModel):
    job_id: str
    status: str
    stage: str
    progress: float
    message: str
