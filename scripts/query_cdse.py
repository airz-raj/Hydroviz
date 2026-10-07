import os
import sys
import httpx
from datetime import datetime, timedelta

CDSE_CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CDSE_CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")
AUTH_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CATALOG_URL = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"

def get_token():
    if not CDSE_CLIENT_ID or not CDSE_CLIENT_SECRET:
        print("Error: CDSE_CLIENT_ID or CDSE_CLIENT_SECRET not set in environment.")
        print("Please configure your .env file with actual credentials.")
        sys.exit(1)

    data = {
        "grant_type": "client_credentials",
        "client_id": CDSE_CLIENT_ID,
        "client_secret": CDSE_CLIENT_SECRET
    }
    response = httpx.post(AUTH_URL, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def search_s1(token, bbox, date_start, date_end):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "collections": ["sentinel-1-grd"],
        "bbox": bbox,
        "datetime": f"{date_start}T00:00:00Z/{date_end}T23:59:59Z",
        "limit": 100
    }
    response = httpx.post(CATALOG_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    # Case study: Bhote Koshi-Trishuli flood, 26 Aug 2026
    # Approx corridor bbox
    bbox = [85.0, 27.5, 86.5, 28.5]
    event_date = datetime(2026, 8, 26)
    
    # Let's search from 30 days before to 30 days after
    date_start = (event_date - timedelta(days=30)).strftime("%Y-%m-%d")
    date_end = (event_date + timedelta(days=30)).strftime("%Y-%m-%d")
    
    print("Authenticating with CDSE...")
    token = get_token()
    print("Authentication successful.")
    
    print(f"Searching Sentinel-1 acquisitions between {date_start} and {date_end} for bbox {bbox}...")
    results = search_s1(token, bbox, date_start, date_end)
    features = results.get("features", [])
    print(f"Found {len(features)} acquisitions.")
    
    # Print available S1 acquisitions with relative orbit, direction, platform
    for f in features:
        props = f["properties"]
        platform = props.get("platform")
        orbit = props.get("sat:relative_orbit")
        direction = props.get("sat:orbit_state")
        dt = props.get("datetime")
        print(f"- {dt} | {platform} | Orbit: {orbit} ({direction}) | ID: {f['id']}")
