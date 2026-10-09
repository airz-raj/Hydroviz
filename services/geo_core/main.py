import os
import sys
from fastapi import FastAPI

# In Docker, shared module is mounted at /shared
sys.path.insert(0, '/shared')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'python')))

try:
    import geo_core
except ImportError:
    import geo_core_py as geo_core

app = FastAPI(title="HydroViz Geo Core Service")

@app.get("/health")
def health_check():
    status = geo_core.health_check()
    return {"status": status, "service": "geo_core"}
