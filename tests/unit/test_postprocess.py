import pytest
import numpy as np
from services.flood_ml.processors.postprocess import remove_permanent_water, apply_mmu

def test_remove_permanent_water():
    flood_mask = np.ones((5, 5))
    pre1 = np.full((5, 5), 0.0)
    pre2 = np.full((5, 5), 0.0)
    
    # One pixel is water in both pre-images
    pre1[2, 2] = -20.0
    pre2[2, 2] = -18.0
    
    clean = remove_permanent_water(flood_mask, pre1, pre2)
    assert clean[2, 2] == 0
    assert clean[0, 0] == 1

def test_apply_mmu():
    mask = np.zeros((10, 10))
    mask[0, 0] = 1 # Single pixel
    
    mask[5:10, 5:10] = 1 # 25 pixels
    
    clean = apply_mmu(mask, mmu_pixels=5)
    
    assert clean[0, 0] == 0 # Removed
    assert clean[7, 7] == 1 # Kept
