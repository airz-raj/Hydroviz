import os
import math
from typing import List, Tuple, Dict, Any, Optional

try:
    import rasterio
    from rasterio.windows import from_bounds
except ImportError:
    rasterio = None

def get_copernicus_dem_tile_url(lat: float, lon: float) -> str:
    """
    Returns public AWS S3 URL for the Copernicus WorldDEM-30 (GLO-30) COG tile
    covering the integer degree box [floor(lat), floor(lon)].
    """
    ilat = int(math.floor(lat))
    ilon = int(math.floor(lon))
    ns = "N" if ilat >= 0 else "S"
    ew = "E" if ilon >= 0 else "W"
    tile_name = f"Copernicus_DSM_COG_10_{ns}{abs(ilat):02d}_00_{ew}{abs(ilon):03d}_00_DEM"
    return f"https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/{tile_name}/{tile_name}.tif"

def sample_elevation_grid(center_lat: float, center_lon: float, grid_size: int = 25, span_deg: float = 0.04) -> Tuple[List[List[float]], List[float], List[float]]:
    """
    Samples a 2D elevation grid centered around (center_lat, center_lon).
    Returns (grid, lats, lons).
    Tries real Copernicus 30m DEM first via rasterio, falls back to physics-based
    Himalayan valley elevation model if network is unavailable.
    """
    lats = [center_lat + span_deg * (0.5 - r / (grid_size - 1)) for r in range(grid_size)]
    lons = [center_lon + span_deg * (c / (grid_size - 1) - 0.5) for c in range(grid_size)]

    # 1. Check local DEM files in jobs or data directories
    dem_candidates = []
    dem_env = os.getenv("DEM_PATH")
    if dem_env:
        dem_candidates.append(dem_env)

    data_dir = os.getenv("DATA_DIR")
    if not data_dir:
        local_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        data_dir = local_data if os.path.exists(local_data) else os.path.abspath("./data")

    jobs_dir = os.path.join(data_dir, "jobs")
    if os.path.exists(jobs_dir):
        for jid in os.listdir(jobs_dir):
            j_dem = os.path.join(jobs_dir, jid, "dem_copernicus_30m.tif")
            if os.path.exists(j_dem):
                dem_candidates.append(j_dem)

    for alt_dem in ["temp/test_dem.tif", os.path.join(data_dir, "dem_copernicus_30m.tif")]:
        if os.path.exists(alt_dem):
            dem_candidates.append(alt_dem)

    if rasterio:
        for dem_path in dem_candidates:
            try:
                with rasterio.open(dem_path) as src:
                    b = src.bounds
                    if (b.left - 0.05) <= center_lon <= (b.right + 0.05) and (b.bottom - 0.05) <= center_lat <= (b.top + 0.05):
                        grid = []
                        for r in range(grid_size):
                            row = []
                            coords = [(lons[c], lats[r]) for c in range(grid_size)]
                            samples = list(src.sample(coords))
                            for s in samples:
                                val = float(s[0]) if len(s) > 0 and s[0] != src.nodata else 1000.0
                                row.append(round(val, 1))
                            grid.append(row)
                        return grid, lats, lons
            except Exception:
                continue

        # 2. Check local disk DEM cache if previously ingested
        try:
            cache_dem_dir = os.path.join(data_dir, "dem_cache")
            dem_out = os.path.join(cache_dem_dir, f"dem_{round(center_lat, 3)}_{round(center_lon, 3)}.tif")
            if os.path.exists(dem_out):
                with rasterio.open(dem_out) as src:
                    grid = []
                    for r in range(grid_size):
                        row = []
                        coords = [(lons[c], lats[r]) for c in range(grid_size)]
                        samples = list(src.sample(coords))
                        for s in samples:
                            val = float(s[0]) if len(s) > 0 and s[0] != src.nodata else 1000.0
                            row.append(round(val, 1))
                        grid.append(row)
                    return grid, lats, lons
        except Exception:
            pass

        # 3. Try streaming from AWS Copernicus GLO-30 COGs via rasterio /vsicurl/ with fast timeout
        try:
            tile_url = get_copernicus_dem_tile_url(center_lat, center_lon)
            vsi_url = f"/vsicurl/{tile_url}"
            with rasterio.open(vsi_url, timeout=2.0) as src:
                grid = []
                for r in range(grid_size):
                    row = []
                    coords = [(lons[c], lats[r]) for c in range(grid_size)]
                    samples = list(src.sample(coords))
                    for s in samples:
                        val = float(s[0]) if len(s) > 0 and s[0] != src.nodata else 1000.0
                        row.append(round(val, 1))
                    grid.append(row)
                return grid, lats, lons
        except Exception:
            pass

    # 4. Fallback: Physics-conditioned continuous downhill Himalayan valley terrain
    grid = []
    for r in range(grid_size):
        row = []
        r_lat = lats[r]
        dist_along = (center_lat - r_lat) * 111.0  # Positive heading south downstream
        for c in range(grid_size):
            c_lon = lons[c]
            # Natural thalweg channel
            v_lon = center_lon + 0.003 * math.sin(dist_along / 1.5)
            cross_dist_km = abs(c_lon - v_lon) * 111.0 * math.cos(math.radians(r_lat))
            # Downward river thalweg gradient (38m drop per km)
            base_elev = 1650.0 - dist_along * 38.0
            # V/U-shaped valley relief on flanks
            elev = base_elev + 55.0 * (cross_dist_km ** 1.5)
            row.append(round(max(200.0, elev), 1))
        grid.append(row)

    return grid, lats, lons
