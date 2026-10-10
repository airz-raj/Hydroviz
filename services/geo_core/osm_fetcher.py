import os
import json
import httpx
from typing import Tuple, List, Dict, Any

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

def fetch_real_osm_features(bbox: List[float], timeout_sec: float = 6.0) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Queries OpenStreetMap Overpass API for real settlements and road networks
    within the specified bounding box: [min_lon, min_lat, max_lon, max_lat].
    Returns (settlements, roads).
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    headers = {"User-Agent": "HydroViz-Disaster-Response/1.0"}
    
    # 1. Fetch Settlements
    settlements = []
    q_settlements = f"""
    [out:json][timeout:10];
    node["place"~"town|village|hamlet"]({min_lat},{min_lon},{max_lat},{max_lon});
    out body 20;
    """
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            r = httpx.post(endpoint, data={"data": q_settlements}, headers=headers, timeout=timeout_sec)
            if r.status_code == 200:
                for el in r.json().get("elements", []):
                    name = el.get("tags", {}).get("name:en") or el.get("tags", {}).get("name") or "Settlement"
                    settlements.append({
                        "osm_id": el["id"],
                        "name": str(name),
                        "lat": float(el["lat"]),
                        "lon": float(el["lon"]),
                        "place": el.get("tags", {}).get("place", "hamlet")
                    })
                if settlements:
                    break
        except Exception:
            continue
            
    # 2. Fetch Road Network
    roads = []
    q_roads = f"""
    [out:json][timeout:10];
    way["highway"~"primary|secondary|tertiary|trunk|unclassified"]({min_lat},{min_lon},{max_lat},{max_lon});
    out geom 25;
    """
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            r = httpx.post(endpoint, data={"data": q_roads}, headers=headers, timeout=timeout_sec)
            if r.status_code == 200:
                for el in r.json().get("elements", []):
                    geom = el.get("geometry", [])
                    coords = [[round(pt["lon"], 6), round(pt["lat"], 6)] for pt in geom]
                    if len(coords) >= 2:
                        name = el.get("tags", {}).get("name:en") or el.get("tags", {}).get("name") or el.get("tags", {}).get("highway") or "Road"
                        roads.append({
                            "osm_id": el["id"],
                            "name": str(name),
                            "highway": el.get("tags", {}).get("highway", "road"),
                            "coordinates": coords
                        })
                if roads:
                    break
        except Exception:
            continue
            
    return settlements, roads
