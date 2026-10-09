import pytest
from services.geo_core.python.geo_core_py import fill_pits

def test_pit_fill_single_depression():
    # 3x3 DEM grid with a pit in the center (center = 50, surrounded by 100)
    dem = [
        [100.0, 100.0, 100.0],
        [100.0,  50.0, 100.0],
        [100.0, 100.0, 100.0]
    ]
    
    conditioned = fill_pits(dem)
    # The center pit must be raised to the minimum of its 4 neighbors (100.0)
    assert conditioned[1][1] == 100.0
    # Boundary cells remain unchanged
    assert conditioned[0][0] == 100.0

def test_pit_fill_no_depression():
    # Monotonically sloping plane (no pits)
    dem = [
        [300.0, 200.0, 100.0],
        [300.0, 200.0, 100.0],
        [300.0, 200.0, 100.0]
    ]
    conditioned = fill_pits(dem)
    assert conditioned == dem
