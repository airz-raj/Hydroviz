from fastapi import FastAPI

app = FastAPI(title="HydroViz Flood ML Service")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "flood_ml"}
