import numpy as np
from metrics import compute_iou, compute_precision_recall_f1

def compare_flood_extent():
    """
    Compares the predicted flood mask against the EMSR927 delineation map.
    """
    print("Comparing Flood Extent...")
    
    # Mock masks (e.g. 100x100)
    pred_mask = np.random.choice([True, False], size=(100, 100), p=[0.2, 0.8])
    true_mask = np.random.choice([True, False], size=(100, 100), p=[0.25, 0.75])
    
    iou = compute_iou(pred_mask, true_mask)
    precision, recall, f1 = compute_precision_recall_f1(pred_mask, true_mask)
    
    print(f"IoU: {iou:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")

if __name__ == "__main__":
    compare_flood_extent()
