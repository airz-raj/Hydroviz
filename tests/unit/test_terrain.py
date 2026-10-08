import pytest
import numpy as np
from services.flood_ml.processors.terrain import compute_slope, compute_shadow_layover

def test_slope():
    dem = np.array([[0, 0, 0], [0, 10, 0], [0, 0, 0]], dtype=float)
    slope = compute_slope(dem, 10.0, 10.0)
    assert slope.shape == dem.shape
    # Center pixel should have some slope
    assert slope[1, 1] == 0.0 # Wait, gradient of a peak in center is zero because central difference (10-0)/2 and (0-10)/2 cancels out. Wait, central diff: (f(x+1)-f(x-1))/2 = 0.
    # The edges will have slope
    assert slope[1, 0] > 0

def test_shadow_layover():
    slope = np.array([[10, 50], [80, 5]], dtype=float)
    incidence_angle = 40.0
    invalid = compute_shadow_layover(None, slope, incidence_angle)
    assert invalid[0, 0] == 0
    assert invalid[0, 1] == 1 # 50 > 40
    assert invalid[1, 0] == 1 # 80 > 50
    assert invalid[1, 1] == 0
