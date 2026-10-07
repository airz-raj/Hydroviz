import os
import sys
from fastapi import FastAPI

# Add the parent directory to sys.path to allow importing from shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.attribution import get_all_attributions

app = FastAPI(title="HydroViz Report Service")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "report"}
