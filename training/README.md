# HydroViz — Training Guide

> How to train, evaluate, and export the flood segmentation model.

---

## Overview

| Aspect | Detail |
|--------|--------|
| **Task** | Semantic segmentation: pixel-wise classification of SAR imagery |
| **Classes** | 0 = no water, 1 = permanent water, 2 = flood |
| **Input** | 9 channels: [pre2_VV, pre2_VH, pre1_VV, pre1_VH, post_VV, post_VH, slope, HAND, shadow_mask] |
| **Output** | H×W probability map per class |
| **Architecture** | U-Net with ResNet-34 encoder (or DeepLabv3+) |
| **Training data** | Kuro Siwo benchmark webdataset |
| **Optional data** | Sen1Floods11 |
| **Runtime** | PyTorch → ONNX → ONNX Runtime |

---

## 1. Dataset Preparation

### 1.1 Kuro Siwo

**Source:** https://github.com/Orion-AI-Lab/KuroSiwo

**Steps:**
1. Check the benchmark webdataset release (NOT the full 1.33 TB archive)
2. Verify size before downloading: `curl -sI <url> | grep Content-Length`
3. Download and extract
4. Verify label schema from the repository docs: confirm class mapping
5. Record licence (MIT per NeurIPS paper; CC BY per README)

**Expected structure (verify):**
```
kuro_siwo/
├── train/
│   ├── event_001/
│   │   ├── pre1_vv.tif, pre1_vh.tif
│   │   ├── pre2_vv.tif, pre2_vh.tif
│   │   ├── post_vv.tif, post_vh.tif
│   │   └── label.tif
│   └── ...
├── val/
└── test/
```

**Critical: verify this structure against the actual download before writing the dataloader.**

### 1.2 Terrain Channel Augmentation

The training data lacks terrain channels. For each training event:
1. Download the corresponding Copernicus DEM tile
2. Compute slope and HAND
3. Compute shadow/layover mask from DEM + S1 incidence angle metadata
4. Append these 3 channels to the SAR stack

This is essential for mountain domain shift mitigation.

### 1.3 Sen1Floods11 (Optional)

**Source:** https://github.com/cloudtostreet/Sen1Floods11

Only use if:
- Additional training data improves mountain performance
- Licence is acceptable for educational use (CC BY 4.0 per mirrors)
- Cite Bonafilia et al. 2020

### 1.4 Himalayan Evaluation Set

Build weak-label evaluation data from earlier Himalayan floods:

| Event | Date | Region |
|-------|------|--------|
| Chamoli | 2021-02-07 | Uttarakhand, India |
| Melamchi | 2021-06-15 | Sindhupalchok, Nepal |
| South Lhonak | 2023-10-04 | Sikkim, India |

**Method:**
1. Find cloud-free Sentinel-2 scene shortly after each event
2. Compute NDWI = (Green - NIR) / (Green + NIR)
3. Threshold to create weak flood labels (NDWI > 0.3 approximately)
4. Manual review for obvious errors
5. Label these as "weak labels — not ground truth" in all reporting

---

## 2. Data Augmentation

Mountain domain shift is the biggest challenge. Augmentations:

| Augmentation | Purpose |
|-------------|---------|
| Random horizontal/vertical flip | Basic invariance |
| Random 90° rotation | Rotation invariance |
| Random crop (256×256 from 512×512) | Scale variation |
| Random brightness/contrast (SAR dB) | Radiometric variation |
| Simulated shadow injection | Train robustness to shadow artefacts |
| Slope-conditioned dropout | Simulate steep terrain information loss |

---

## 3. Model Architecture

### 3.1 Primary: U-Net with ResNet-34

```
Input (9 channels)
  → 1×1 Conv to adapt 9ch → 3ch (for pretrained encoder)
  → ResNet-34 encoder (pretrained on ImageNet)
  → U-Net decoder with skip connections
  → 1×1 Conv → 3 classes
  → Softmax
```

**Why ResNet-34:** good balance of depth and speed. Pretrained weights help even though the domain is different (features like edges, textures transfer).

### 3.2 Alternative: DeepLabv3+

If U-Net underperforms (especially on large-scale flood features):
- DeepLabv3+ with atrous spatial pyramid pooling
- Better multi-scale feature extraction
- Same encoder/channel adaptation approach

### 3.3 Loss Function

```
L = 0.5 × WeightedCE(pred, target) + 0.5 × DiceLoss(pred, target)
```

Class weights (adjust after checking class balance):
- no_water: 1.0
- permanent_water: 2.0
- flood: 5.0 (minority class in most training scenes)

---

## 4. Training Configuration

```yaml
# training/configs/default.yaml
data:
  dataset: kuro_siwo
  train_split: train
  val_split: val
  test_split: test
  input_channels: 9       # 6 SAR + 3 terrain
  num_classes: 3
  patch_size: 256
  stride: 128              # 50% overlap for training patches

model:
  architecture: unet
  encoder: resnet34
  pretrained: true

training:
  epochs: 100
  batch_size: 16
  learning_rate: 0.001
  optimizer: adam
  scheduler: cosine_annealing
  weight_decay: 0.0001
  mixed_precision: true
  early_stopping:
    patience: 10
    metric: val_flood_iou
    mode: max
  class_weights: [1.0, 2.0, 5.0]

augmentation:
  horizontal_flip: true
  vertical_flip: true
  rotation_90: true
  random_crop: true
  brightness_range: [-2, 2]  # dB
  shadow_injection: true

inference:
  window_size: 256
  stride: 192               # 75% of window
  blend: gaussian
  batch_size: 32
```

---

## 5. Evaluation Protocol

### 5.1 Metrics

| Metric | Per-class | Overall |
|--------|-----------|---------|
| IoU (Intersection over Union) | ✅ | ✅ (mean) |
| F1 Score | ✅ | ✅ (macro) |
| Precision | ✅ | ✅ |
| Recall | ✅ | ✅ |

### 5.2 Stratified Analysis

Report all metrics stratified by:
- **Slope bin:** 0-10°, 10-20°, 20-30°, 30°+
- **Shadow fraction:** 0-10%, 10-30%, 30%+
- **Event type:** riverine, flash flood, debris flow (if labelled)

### 5.3 Comparison with Baseline

| Method | Flood IoU | Flood F1 | Perm Water IoU |
|--------|-----------|----------|----------------|
| M2: Log-ratio baseline | _TBD_ | _TBD_ | _TBD_ |
| M3: Learned model | _TBD_ | _TBD_ | _TBD_ |
| Δ improvement | _TBD_ | _TBD_ | _TBD_ |

### 5.4 Himalayan Evaluation (weak labels)

| Event | Flood IoU | Notes |
|-------|-----------|-------|
| Chamoli 2021 | _TBD_ | Snow/ice confusion possible |
| Melamchi 2021 | _TBD_ | Closest analogue to case study |
| South Lhonak 2023 | _TBD_ | GLOF event |

**Caveat:** These use weak labels from NDWI thresholding. Results should be interpreted as indicative, not definitive.

### 5.5 Failure Case Analysis

Document at least 5 failure cases with:
- Input image (SAR)
- Predicted mask vs label
- Likely cause (shadow, debris confusion, thin river channel, etc.)
- Potential mitigation

---

## 6. ONNX Export

```bash
cd training
python export_onnx.py \
  --checkpoint checkpoints/best.pt \
  --output ../services/flood_ml/models/flood_seg_v1.onnx \
  --opset 17 \
  --input-shape 1,9,256,256

# Verify
python -c "
import onnxruntime as ort
import numpy as np
sess = ort.InferenceSession('flood_seg_v1.onnx')
dummy = np.random.randn(1, 9, 256, 256).astype(np.float32)
out = sess.run(None, {sess.get_inputs()[0].name: dummy})
print('Output shape:', out[0].shape)  # Expected: (1, 3, 256, 256)
"
```

---

## 7. Model Card

Create `training/model_card.md` with:

| Field | Content |
|-------|---------|
| **Model name** | hydroviz-flood-seg |
| **Version** | v1.0.0 |
| **Architecture** | U-Net, ResNet-34 encoder |
| **Task** | SAR flood segmentation (3 classes) |
| **Training data** | Kuro Siwo benchmark (Bountos et al. 2024) |
| **Training data licence** | MIT / CC BY |
| **Input** | 9 channels: VV×3, VH×3, slope, HAND, shadow_mask |
| **Output** | 3-class probability map |
| **Performance** | _TBD_ |
| **Known failure modes** | Shadow/layover FP, thin channels, debris confusion |
| **Intended use** | Educational prototype for flood mapping |
| **Not intended for** | Operational emergency response |
| **SHA256** | _TBD_ |
