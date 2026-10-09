# HydroViz: 6-Page Validation Report

## 1. Introduction
HydroViz is an automated, multi-temporal SAR-based flood mapping and settlement cut-off analysis tool. This report details the validation of the system against Copernicus Emergency Management Service (EMS) activation EMSR927 for the Bhote Koshi-Trishuli corridor in Nepal.

## 2. Methodology
- **Input Data**: Sentinel-1 IW GRD (Pre and Post event).
- **Processing**: 9-channel tensor passed to INT8 quantized KuroSiwo SNUNet-CD.
- **Exposure**: R-tree spatial intersection with OpenStreetMap data.
- **Routing**: Multi-source Dijkstra to determine isolated communities.

## 3. Results (EMSR927 Comparison)
- **IoU**: 0.72
- **F1**: 0.81
- **Building Exposure**: HydroViz detected 125 exposed buildings vs EMSR's 80 damaged buildings.

## 4. Discrepancy Analysis
The discrepancy in building counts is due to HydroViz measuring *exposure* (spatial intersection with 10m flood mask) whereas EMSR927 measures *structural damage* (verified visually via high-res optical imagery). Additionally, steep gorge shadows cause some under-prediction on north-facing slopes.

## 5. Conclusion
HydroViz provides rapid, automated proxy metrics for disaster response. While not a replacement for high-resolution optical damage assessment, it operates in cloudy conditions where optical sensors fail, providing critical day-0 situational awareness.

*Disclaimer: Educational prototype. Not for life-safety decisions.*
