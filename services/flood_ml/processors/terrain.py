import numpy as np
from scipy import ndimage
import math

def compute_slope(dem: np.ndarray, cell_size_x: float, cell_size_y: float) -> np.ndarray:
    """
    Compute terrain slope in degrees from a DEM.
    Uses numpy.gradient for central difference.
    """
    dy, dx = np.gradient(dem, cell_size_y, cell_size_x)
    
    # Calculate slope magnitude
    slope_pct = np.sqrt(dx**2 + dy**2)
    
    # Convert to degrees
    slope_deg = np.degrees(np.arctan(slope_pct))
    return slope_deg

def compute_hand_stub(dem: np.ndarray) -> np.ndarray:
    """
    Stub for Height Above Nearest Drainage (HAND).
    A full implementation requires D8 flow accumulation routing.
    For this prototype, we'll approximate using a simple morphological filter
    to find local minima (drainage) and subtract from DEM.
    """
    # Find local minima (proxy for drainage channels)
    min_filtered = ndimage.minimum_filter(dem, size=15)
    # HAND is approximately height above local minima
    hand = dem - min_filtered
    # Ensure no negative values
    return np.maximum(hand, 0)

def compute_shadow_layover(dem: np.ndarray, slope_deg: np.ndarray, incidence_angle: float) -> np.ndarray:
    """
    Compute simplified shadow/layover mask.
    shadow: slope > (90 - incidence_angle) on far side.
    layover: slope > incidence_angle on near side.
    Returns binary mask (1 = invalid, 0 = valid).
    """
    # We lack exact look direction in this stub, so we apply a generic slope check
    # to approximate layover/shadow affected regions
    invalid_mask = (slope_deg > incidence_angle) | (slope_deg > (90 - incidence_angle))
    return invalid_mask.astype(np.uint8)
