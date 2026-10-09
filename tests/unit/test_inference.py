import os
import pytest
import numpy as np
from services.flood_ml.inference import FloodInferenceONNX

def test_inference_synthetic_tile():
    """
    Test ONNX sliding-window inference on a synthetic 9-channel tile.
    Tests padding logic (e.g. 128x128 smaller than 256x256 window)
    and output mask shapes and value range.
    """
    model = FloodInferenceONNX()
    
    # Create synthetic 9-channel input tile (128x128, tests padding logic)
    tile_small = np.random.randn(9, 128, 128).astype(np.float32)
    mask_small = model._sliding_window_inference(tile_small, window_size=256, step=128)
    
    assert mask_small.shape == (128, 128)
    assert np.all(np.isin(mask_small, [0, 1, 2]))
    
    # Test tile larger than window_size (300x300, tests window stepping)
    tile_large = np.random.randn(9, 300, 300).astype(np.float32)
    mask_large = model._sliding_window_inference(tile_large, window_size=256, step=128)
    
    assert mask_large.shape == (300, 300)
    assert np.all(np.isin(mask_large, [0, 1, 2]))
