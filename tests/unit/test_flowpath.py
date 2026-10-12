import pytest
from services.geo_core.python.geo_core_py import trace_d8_flow_path

def test_trace_d8_flow_path_valley():
    # Valley DEM: water flows down column 1 from row 0 to row 3
    dem = [
        [100.0, 90.0, 100.0],
        [ 90.0, 70.0,  90.0],
        [ 80.0, 50.0,  80.0],
        [ 70.0, 30.0,  70.0]
    ]

    path = trace_d8_flow_path(dem, start_r=0, start_c=1)
    
    # Path should start at (0, 1) and follow steepest descent along the center channel
    assert path[0] == (0, 1)
    assert path[1] == (1, 1)
    assert path[2] == (2, 1)
    assert path[3] == (3, 1)
    assert len(path) == 4

def test_copernicus_dem_sampling():
    from services.geo_core.dem_sampler import sample_elevation_grid
    # Test sampling near Melamchi
    grid, lats, lons = sample_elevation_grid(27.83, 85.58, grid_size=9, span_deg=0.02)
    assert len(grid) == 9
    assert len(grid[0]) == 9
    assert len(lats) == 9
    assert len(lons) == 9
    # Elevations in this region should be realistic Himalayan altitudes (500m - 5000m)
    center_elev = grid[4][4]
    assert 400.0 <= center_elev <= 5000.0

