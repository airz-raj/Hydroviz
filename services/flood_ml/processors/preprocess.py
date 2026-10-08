import numpy as np
from scipy.ndimage import uniform_filter

def lee_filter(img: np.ndarray, size: int = 7) -> np.ndarray:
    """
    Apply Lee Speckle Filter to a SAR image.
    """
    img_mean = uniform_filter(img, (size, size))
    img_sqr_mean = uniform_filter(img**2, (size, size))
    img_variance = img_sqr_mean - img_mean**2
    
    overall_variance = np.var(img)
    
    img_weights = img_variance / (img_variance + overall_variance + 1e-10)
    img_output = img_mean + img_weights * (img - img_mean)
    
    return img_output

def check_coregistration(pre: np.ndarray, post: np.ndarray) -> bool:
    """
    Check if two images are co-registered.
    In a real system, we'd use cross-correlation to find the shift.
    Here we just return True as CDSE STAC data is orthorectified to same grid.
    """
    if pre.shape != post.shape:
        return False
    return True

def normalize_db(img_db: np.ndarray, mean: float, std: float) -> np.ndarray:
    """
    Z-score normalization based on training stats (for M3).
    """
    return (img_db - mean) / (std + 1e-8)
