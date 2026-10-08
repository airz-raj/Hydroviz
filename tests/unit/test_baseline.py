import pytest
import numpy as np
from services.flood_ml.processors.baseline import detect_flood_baseline

def test_detect_flood_baseline():
    # Pre images have high backscatter (~0 dB)
    pre1 = np.full((10, 10), 0.0)
    pre2 = np.full((10, 10), 0.0)
    # Post image has some water (dark, -20 dB) and some land (0 dB)
    post = np.full((10, 10), 0.0)
    post[2:8, 2:8] = -20.0
    
    slope = np.zeros((10, 10))
    invalid = np.zeros((10, 10))
    
    mask = detect_flood_baseline(pre1, pre2, post, slope, invalid)
    
    # Should detect flood in the center
    assert mask[5, 5] == 1
    # No flood on the edges
    assert mask[0, 0] == 0
