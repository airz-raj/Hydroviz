import os
import json
import threading
from typing import Dict, Any, List

ATTRIBUTION_SENTINEL = "Contains modified Copernicus Sentinel data 2026."
ATTRIBUTION_DEM = "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."
ATTRIBUTION_OSM = "© OpenStreetMap contributors."
ATTRIBUTION_EMS = "European Union, Copernicus Emergency Management Service data"
ATTRIBUTION_KURO_SIWO = "Bountos, N.I., et al. (2024). Kuro Siwo: A global multi-temporal SAR dataset for rapid flood mapping. NeurIPS Datasets and Benchmarks."
ATTRIBUTION_SEN1FLOODS11 = "Bonafilia, D., et al. (2020). Sen1Floods11: A georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1. CVPR Workshops."

_provenance_lock = threading.Lock()
_job_provenance: Dict[str, List[Dict[str, Any]]] = {}

def get_all_attributions() -> Dict[str, str]:
    return {
        "sentinel": ATTRIBUTION_SENTINEL,
        "dem": ATTRIBUTION_DEM,
        "osm": ATTRIBUTION_OSM,
        "ems": ATTRIBUTION_EMS,
        "kuro_siwo": ATTRIBUTION_KURO_SIWO,
        "sen1floods11": ATTRIBUTION_SEN1FLOODS11
    }

def add_provenance(job_id: str, stage: str, metadata: Dict[str, Any]) -> None:
    """
    Append provenance records for a given job and stage.
    Maintains in-memory registry and synchronizes with facts.json if present.
    """
    record = {
        "stage": stage,
        "metadata": metadata
    }
    with _provenance_lock:
        if job_id not in _job_provenance:
            _job_provenance[job_id] = []
        _job_provenance[job_id].append(record)

    # Optional sync to facts.json if directory exists
    data_dir = os.getenv("DATA_DIR", "/data")
    facts_path = os.path.join(data_dir, "jobs", job_id, "facts.json")
    if os.path.exists(facts_path):
        try:
            with open(facts_path, "r", encoding="utf-8") as f:
                facts = json.load(f)
            if "provenance" not in facts:
                facts["provenance"] = []
            facts["provenance"].append(record)
            with open(facts_path, "w", encoding="utf-8") as f:
                json.dump(facts, f, indent=2)
        except Exception:
            pass

def get_provenance(job_id: str) -> List[Dict[str, Any]]:
    """Retrieve all provenance entries recorded for a job."""
    with _provenance_lock:
        return list(_job_provenance.get(job_id, []))
