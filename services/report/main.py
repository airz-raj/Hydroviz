import os
import sys
from fastapi import FastAPI

# In Docker, shared module is mounted at /shared
sys.path.insert(0, '/shared')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))

from attribution import get_all_attributions

app = FastAPI(title="HydroViz Report Service")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "report"}


@app.get("/attribution")
def get_attribution():
    return get_all_attributions()
