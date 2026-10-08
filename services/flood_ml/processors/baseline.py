import numpy as np

def compute_log_ratio(pre1: np.ndarray, pre2: np.ndarray, post: np.ndarray) -> np.ndarray:
    """
    Compute log-ratio difference between post-event and mean pre-event.
    Assuming inputs are already in dB:
    difference = post_dB - mean(pre1_dB, pre2_dB)
    """
    pre_mean = (pre1 + pre2) / 2.0
    return post - pre_mean

def otsu_threshold(image: np.ndarray, bins: int = 256) -> float:
    """
    Compute Otsu's threshold for an image.
    Since we are looking for negative change (flooded water is darker), 
    we apply this to the inverted difference or just find the threshold separating the modes.
    """
    # Filter out nans/infs
    valid_pixels = image[np.isfinite(image)]
    if valid_pixels.size == 0:
        return 0.0
        
    hist, bin_edges = np.histogram(valid_pixels, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    total = valid_pixels.size
    sum_total = np.sum(bin_centers * hist)
    
    weight_b = 0.0
    sum_b = 0.0
    var_max = 0.0
    threshold = bin_centers[0]
    
    for i in range(bins):
        weight_b += hist[i]
        if weight_b == 0:
            continue
            
        weight_f = total - weight_b
        if weight_f == 0:
            break
            
        sum_b += bin_centers[i] * hist[i]
        
        mean_b = sum_b / weight_b
        mean_f = (sum_total - sum_b) / weight_f
        
        var_between = weight_b * weight_f * (mean_b - mean_f) ** 2
        
        if var_between > var_max:
            var_max = var_between
            threshold = bin_centers[i]
            
    return threshold

def detect_flood_baseline(pre1_vv: np.ndarray, pre2_vv: np.ndarray, post_vv: np.ndarray, 
                          slope_deg: np.ndarray, invalid_mask: np.ndarray) -> np.ndarray:
    """
    M2: Log-ratio change detection using Otsu's method and terrain masking.
    Returns binary mask: 1 = flood, 0 = no flood.
    """
    diff = compute_log_ratio(pre1_vv, pre2_vv, post_vv)
    
    # We only care about areas where backscatter DECREASED significantly (water is dark)
    # We invert the diff so Otsu finds the threshold separating the strong decreases
    # Alternatively, just apply Otsu to pixels < 0
    neg_diff = diff.copy()
    neg_diff[neg_diff > 0] = 0
    
    threshold = otsu_threshold(neg_diff)
    
    # Flood is where difference is more negative than threshold
    # Since threshold is on neg_diff, it will be a negative number
    flood_mask = (diff < threshold).astype(np.uint8)
    
    # Apply terrain masks
    # Exclude slopes > 5 degrees
    flood_mask[slope_deg > 5] = 0
    
    # Exclude shadow/layover regions
    flood_mask[invalid_mask == 1] = 0
    
    return flood_mask
