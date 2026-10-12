import os
import json
import httpx
from typing import Tuple, List, Dict, Any

OVERPASS_ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

def fetch_real_osm_features(bbox: List[float], timeout_sec: float = 8.0) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Queries OpenStreetMap dynamically for real settlements, road networks, bridges, and buildings
    within the specified bounding box: [min_lon, min_lat, max_lon, max_lat].
    Processes live without static pre-cached baselines or synthetic shapes.
    """
    min_lon, min_lat, max_lon, max_lat = bbox

    settlements: List[Dict[str, Any]] = []
    roads: List[Dict[str, Any]] = []
    bridges: List[Dict[str, Any]] = []
    buildings: List[Dict[str, Any]] = []

    headers = {
        "User-Agent": "HydroViz-Live-Disaster-Response/2.0 (Himalayan Flood Analysis; Pair-Programming Research)"
    }

    # Query Overpass for live OSM features
    q_combined = f"""[out:json][timeout:12];
    (
      node["place"~"city|town|village|hamlet"]({min_lat},{min_lon},{max_lat},{max_lon});
      way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential"]({min_lat},{min_lon},{max_lat},{max_lon});
      way["bridge"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
      way["building"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out body 60;
    out geom 40;"""

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            r = httpx.post(endpoint, data={"data": q_combined}, headers=headers, timeout=timeout_sec)
            if r.status_code == 200:
                elements = r.json().get("elements", [])
                for el in elements:
                    el_type = el.get("type")
                    tags = el.get("tags", {})
                    name = str(tags.get("name:en") or tags.get("name") or "")

                    if el_type == "node" and "place" in tags:
                        settlements.append({
                            "osm_id": el["id"],
                            "name": name or f"Settlement #{el['id']}",
                            "lat": float(el["lat"]),
                            "lon": float(el["lon"]),
                            "place": tags.get("place", "hamlet")
                        })
                    elif el_type == "way" and "highway" in tags:
                        geom = el.get("geometry", [])
                        coords = [[round(pt["lon"], 6), round(pt["lat"], 6)] for pt in geom]
                        if len(coords) >= 2:
                            roads.append({
                                "osm_id": el["id"],
                                "name": name or tags.get("highway", "Road"),
                                "highway": tags.get("highway", "road"),
                                "coordinates": coords
                            })
                    elif el_type == "way" and tags.get("bridge") == "yes":
                        center = el.get("center", {})
                        geom = el.get("geometry", [])
                        c_lat = float(center.get("lat") or (geom[0]["lat"] if geom else min_lat))
                        c_lon = float(center.get("lon") or (geom[0]["lon"] if geom else min_lon))
                        bridges.append({
                            "osm_id": el["id"],
                            "name": name or f"Bridge #{el['id']}",
                            "lat": c_lat,
                            "lon": c_lon,
                            "highway": tags.get("highway", "bridge")
                        })
                    elif el_type == "way" and "building" in tags:
                        center = el.get("center", {})
                        geom = el.get("geometry", [])
                        c_lat = float(center.get("lat") or (geom[0]["lat"] if geom else min_lat))
                        c_lon = float(center.get("lon") or (geom[0]["lon"] if geom else min_lon))
                        buildings.append({
                            "osm_id": el["id"],
                            "name": name or f"Building #{el['id']}",
                            "type": tags.get("building", "yes"),
                            "lat": c_lat,
                            "lon": c_lon
                        })
                if settlements or roads:
                    break
        except Exception:
            continue

    return settlements, roads, bridges, buildings
