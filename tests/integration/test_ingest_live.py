import os
import pytest

try:
    import rasterio
except ImportError:
    rasterio = None

from services.shared.env_loader import load_env
load_env()
from services.ingest.auth import auth_manager
from services.ingest.catalogue import search_s1_acquisitions
from services.ingest.pair_selector import select_s1_pair
from services.ingest.fetcher import fetch_s1_cog
from services.ingest.dem_fetcher import fetch_dem_cog

def test_ingest_live(tmp_path):
    """
    Live Copernicus Data Space Ecosystem (CDSE) Ingestion Integration Test.
    Verifies authentication, catalogue STAC search, relative orbit pair matching,
    and genuine SAR & DEM GeoTIFF raster retrieval.
    """
    if rasterio is None:
        pytest.skip("rasterio not installed in this environment")
    if not auth_manager.is_configured():
        pytest.skip("CDSE credentials not configured in local environment")

    # Bounding box for Melamchi valley test sector
    bbox = [85.50, 27.80, 85.65, 27.95]
    event_date = "2026-08-26"

    # 1. Verify STAC catalog acquisition search
    features = search_s1_acquisitions(bbox, "2026-08-01", "2026-09-08")
    assert len(features) > 0, "No Sentinel-1 acquisitions returned by CDSE STAC catalogue"

    # 2. Verify same-orbit pairing
    pair = select_s1_pair(features, event_date)
    assert pair is not None, "Failed to pair Sentinel-1 pre/post acquisitions on matching relative orbit"
    assert "orbit" in pair
    assert "pre_1" in pair
    assert "post" in pair
    assert pair["pre_1"]["properties"]["sat:relative_orbit"] == pair["post"]["properties"]["sat:relative_orbit"]

    post_dt = pair["post"]["properties"]["datetime"][:10]
    pre_dt = pair["pre_1"]["properties"]["datetime"][:10]

    # 3. Retrieve genuine Copernicus DEM raster
    dem_path = str(tmp_path / "copernicus_dem_30m.tif")
    dem_ok = fetch_dem_cog(bbox, dem_path)
    assert dem_ok is True, "Failed to retrieve Copernicus DEM raster"
    assert os.path.exists(dem_path)
    with rasterio.open(dem_path) as src_dem:
        assert src_dem.count == 1
        dem_data = src_dem.read(1)
        assert dem_data.min() > 300.0, "DEM elevations in Himalaya must be > 300m"

    # 4. Retrieve genuine Sentinel-1 SAR GeoTIFF (dual-pol VV+VH)
    post_path = str(tmp_path / "s1_post_gamma0.tif")
    post_ok = fetch_s1_cog(bbox, post_dt, post_dt, post_path)
    assert post_ok is True, "Failed to retrieve live Sentinel-1 post-event GeoTIFF from CDSE"
    assert os.path.exists(post_path)

    with rasterio.open(post_path) as src_s1:
        assert src_s1.count >= 2, "Sentinel-1 GRD must contain dual polarization (VV + VH bands)"
        assert src_s1.crs.to_string() == "EPSG:4326"
        vv = src_s1.read(1)
        vh = src_s1.read(2)
        assert vv.shape == (512, 512)
        assert (vv > 0).sum() > 100000, "VV band contains insufficient valid radiometric power"
