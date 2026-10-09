import numpy as np
from scipy import ndimage
try:
    import rasterio.features
except ImportError:
    class MockRasterio:
        class features:
            @staticmethod
            def shapes(*args, **kwargs):
                return []
    rasterio = MockRasterio()
from typing import List, Dict, Any

def remove_permanent_water(flood_mask: np.ndarray, pre1_vv: np.ndarray, pre2_vv: np.ndarray, water_threshold: float = -15.0) -> np.ndarray:
    """
    Remove permanent water from the flood mask.
    If a pixel was already water-like (<-15 dB) in BOTH pre-images, it's permanent water.
    """
    permanent_water = (pre1_vv < water_threshold) & (pre2_vv < water_threshold)
    flood_mask_clean = flood_mask.copy()
    flood_mask_clean[permanent_water] = 0
    return flood_mask_clean

def apply_mmu(flood_mask: np.ndarray, mmu_pixels: int = 5) -> np.ndarray:
    """
    Apply Minimum Mapping Unit (MMU).
    Removes connected components smaller than mmu_pixels.
    """
    # Find connected components
    labeled_array, num_features = ndimage.label(flood_mask)
    if num_features == 0:
        return flood_mask
        
    # Count pixels in each component
    component_sizes = np.bincount(labeled_array.ravel())
    
    # Create mask of components larger than MMU
    # component_sizes[0] is the background, we don't remove it
    valid_components = component_sizes >= mmu_pixels
    valid_components[0] = True 
    
    # Filter the array
    mmu_mask = valid_components[labeled_array]
    
    return flood_mask * mmu_mask

def vectorize_mask(flood_mask: np.ndarray, transform) -> List[Dict[str, Any]]:
    """
    Convert raster binary mask to vector polygons.
    """
    shapes = rasterio.features.shapes(flood_mask, mask=(flood_mask == 1), transform=transform)
    polygons = []
    for geom, val in shapes:
        polygons.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {"class": "flood"}
        })
    return polygons

def calculate_flooded_area(flood_mask: np.ndarray, resolution_m: float = 10.0) -> float:
    """
    Calculate flooded area in square kilometers.
    """
    num_flooded_pixels = np.sum(flood_mask == 1)
    area_sq_m = num_flooded_pixels * (resolution_m ** 2)
    return area_sq_m / 1_000_000.0
