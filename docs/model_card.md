# Model Card: HydroViz Flood Segmentation (v1)

## 1. Model Details

- **Model Name:** HydroViz-SNUNet-INT8 (adapted from KuroSiwo SNUNet-CD)
- **Architecture:** Siamese Nested U-Net (SNUNet-CD) with Ensemble Channel Attention Module (ECAM)
- **Base Authors:** Bountos et al. (Orion-AI-Lab, KuroSiwo)
- **Adapter Author:** HydroViz Team (Hackathon 2026, Track B)
- **Parameters:** ~3.2M (Base), INT8 Quantized for inference.
- **Model Type:** Semantic Segmentation (3-class output)
- **License:** CC BY 4.0 (Dataset/Weights) / MIT (Code)

## 2. Intended Use

- **Primary Use Case:** Rapid identification of floodwater and permanent water bodies using Sentinel-1 multi-temporal Synthetic Aperture Radar (SAR) and terrain features.
- **Target Environment:** 8GB RAM local deployment (runs in a 2GB Docker container using ONNX Runtime CPU with tiling).
- **Out of Scope:** This is an educational prototype and is NOT intended for operational life-safety decisions. It is not designed to segment individual buildings (10 m resolution limit).

## 3. Data and Inputs

- **Inputs:** 9-channel tensor stack: `[pre2_VV, pre2_VH, pre1_VV, pre1_VH, post_VV, post_VH, slope, HAND, shadow_mask]`
- **Sensor:** Sentinel-1 C-Band SAR (IW GRD) and Copernicus GLO-30 DEM.
- **Training Data:** Kuro Siwo benchmark (43 global flood events, 10 m resolution). 

## 4. Evaluation (Himalayan Test Set)

- **Test Regions:** Chamoli (2021), Melamchi (2021), South Lhonak (2023).
- **Methodology:** Weak labels derived from Sentinel-2 NDWI where cloud-free. 
- **Metrics:** (Pending full evaluation run)
  - Flood IoU: TBD
  - Flood F1: TBD
  - Precision: TBD
  - Recall: TBD

## 5. Known Limitations and Failure Modes

1. **Radar Shadow & Layover:** Steep terrain (like Himalayan gorges) causes radar shadow and layover. The model may under-predict in shadow areas and over-predict on slopes facing the sensor. (Mitigated via terrain masking).
2. **Debris Fields:** The model is trained on water backscatter (low, specular). High backscatter from mud, debris, or disturbed ground may not be correctly classified as "flood".
3. **Vegetation:** Heavily vegetated flooded areas (double-bounce) may cause false negatives compared to open water.
4. **Resolution:** 10 m resolution limits fine-grained urban detection.
