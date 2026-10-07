from fastapi import FastAPI
import geo_core

app = FastAPI(title="HydroViz Geo Core Service")

@app.get("/health")
def health_check():
    status = geo_core.health_check()
    return {"status": status, "service": "geo_core"}
