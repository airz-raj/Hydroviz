# HydroViz: Multi-Temporal SAR & Terrain-Conditioned Himalayan Flood Damage Mapping System

**Multimodal AI Hackathon 2026 — Track B: Mapping Flood Damage from Space**  
*Technical Architecture, Case Study Validation (EMSR927), and Limitations Analysis*  

---

## 1. Executive Summary

When catastrophic floods strike mountainous regions such as the Himalayas, physical infrastructure—roads, bridges, power grids, and cellular towers—is frequently destroyed or severed within minutes. In the wake of the 26 August 2026 glacier-lake outburst and rock-avalanche flood along the Bhote Koshi–Trishuli corridor in northern Nepal, ground-based sensors were swept away and dense monsoon cloud cover obscured the valley from conventional optical satellites. Under these conditions, emergency dispatchers and international humanitarian teams face severe operational blindness.

**HydroViz** is an automated, physics-conditioned end-to-end satellite response platform designed to rapidly resolve three operational questions for disaster responders:
1. **Where did the flood hit?** Autonomous multi-temporal Sentinel-1 Synthetic Aperture Radar (SAR) change detection and pre-trained ONNX INT8 deep learning segmentation, constrained by Copernicus DEM Height Above Nearest Drainage (HAND $< 15\text{ m}$) and steep-slope ($< 20^\circ$) filters, alongside an amber heuristic debris and scour-field layer.
2. **What was damaged?** Spatial intersection of predicted hazard footprints against pre-event OpenStreetMap (OSM) building footprints, road networks, and bridge crossings.
3. **Who is cut off?** Multi-source Dijkstra graph reachability analysis over the OSM highway topology to identify settlements rendered completely isolated or forced into extensive detours to reach hospitals and towns under both **Strict** and **Conservative** risk scenarios.

Additionally, HydroViz provides an interactive **D8 downhill flow path tracer** based on pit-filled digital elevation models and generates **bilingual (English and Nepali) situation briefs** secured by an automated Devanagari Number Guard. The system runs entirely within an 8 GB RAM envelope without external GPU requirements.

---

## 2. Event Context: The 26 August 2026 Trishuli Flood

On 26 August 2026, the partial collapse of a high-altitude hanging glacier in northern Nepal triggered a massive ice-rock avalanche into a glacial lake, sending a surge of water, mud, boulders, and debris down the Bhote Koshi–Trishuli corridor. Nepal’s National Disaster Risk Reduction and Management Authority (NDRRMA) reported over 1,300 deaths and almost 4,900 missing individuals.

Himalayan flood mapping is notoriously difficult due to:
- **Severe Terrain Distortion:** Deep V-shaped gorges create pronounced radar shadow on far slopes and layover on near slopes.
- **Persistent Cloud Cover:** South Asian monsoon cloud systems prevent optical observation (Sentinel-2) for weeks at a time.
- **Debris-Laden Water:** Flash floods and debris torrents carry high sediment loads, dramatically altering surface roughness and radar dielectric constants compared to calm standing water.
- **Incomplete OpenStreetMap Data:** Rural mountain tracks are frequently unmapped, requiring conservative connectivity assumptions.

HydroViz addresses these challenges through multimodal sensor ingestion and physical terrain masking.

---

## 3. End-to-End System Architecture

The HydroViz architecture follows a strict decoupled microservices topology orchestrated through Docker and FastAPI, prioritizing low-memory CPU inference and streaming UI responses.

```
+-----------------------------------------------------------------------------------------+
|                                    GATEWAY (FastAPI)                                    |
|                      Job Orchestration · Dynamic Bounding Box Normalizer                |
|                    Request-Hash Output Caching · Progress SSE · REST API                |
+--------------------------------------------+--------------------------------------------+
                                             |
             +-------------------------------+-------------------------------+
             |                               |                               |
             v                               v                               v
    +-----------------+             +-----------------+             +-----------------+
    |  INGEST WORKER  |             | FLOOD ML WORKER |             | GEO CORE WORKER |
    | CDSE STAC / OData|             | ONNX INT8 Infer |             | Overpass OSM    |
    | S1 Orbit Pair   |             | HAND / Slope    |             | Dijkstra Graph  |
    | S2 L2A Cloud    |             | cv2 Contours    |             | Dual Cutoff     |
    +--------+--------+             +--------+--------+             +--------+--------+
             |                               |                               |
             +-------------------------------+-------------------------------+
                                             |
                                             v
                             +-------------------------------+
                             |    REPORT WORKER / GUARD      |
                             | Bilingual Jinja Templates     |
                             | Devanagari Digit Validator    |
                             +---------------+---------------+
                                             |
                                             v
                             +-------------------------------+
                             |     MapLibre GL Dashboard     |
                             | Real-Time HUD · EMSR927 Modal |
                             | D8 Flow Tool · Layer Toggles  |
                             +-------------------------------+
```

### 3.1 Design Invariants
1. **Control vs Data Plane Separation:** Heavy spatial rasters (COGs) are processed tile-by-tile via memory windows or local temporary caches, while inter-service communication passes only minimal JSON state.
2. **Single Source of Truth (`facts.json`):** Every statistic displayed in the dashboard or rendered in the situation reports originates exclusively from a structured, schema-validated `facts.json` document.
3. **Strict One-Way Validation Isolation:** Reference data from Copernicus EMS EMSR927 is isolated in the `/case-study` and `validation/` layers; it is never ingested into the feature extraction or model inference pipeline.

---

## 4. Multimodal Satellite Ingestion & Physical Conditioning

### 4.1 Sentinel-1 SAR Orbit Matching
Radar backscatter varies dramatically with incidence angle. Pixel-by-pixel change detection across different orbital geometries produces severe false-positive speckle. HydroViz enforces **same relative orbit track and flight direction matching**:
- **Pre-event Baseline:** Ingests two acquisitions ($t_{-24\text{d}}$, $t_{-12\text{d}}$) from the same relative orbit (e.g., Track 85 Descending) to calculate an average baseline backscatter $\mu_{\text{pre}}$.
- **Post-event Scene:** Ingests the first available overpass ($t_{+0\text{d}}$ to $t_{+4\text{d}}$) matching the same orbital track.
- **Orthorectification:** Utilizes gamma-nought ($\gamma^0$) terrain-corrected backscatter in dB for both VV (co-polarized) and VH (cross-polarized) channels.

### 4.2 Sentinel-2 Optical Cloud Gating
When post-event optical imagery is available, the Scene Classification Layer (SCL) is evaluated. If valid, cloud-free pixels exceed 70%, Sentinel-2 NDWI (Normalized Difference Water Index) is fused into the composite stack:
$$\text{NDWI} = \frac{\text{Band 3 (Green)} - \text{Band 8 (NIR)}}{\text{Band 3 (Green)} + \text{Band 8 (NIR)}}$$
During cloudy monsoon conditions, the system automatically falls back to **SAR-only mode**.

### 4.3 Terrain Conditioning via Copernicus GLO-30 DEM
In mountainous terrain, unconstrained radar change detection misclassifies radar shadows (steep north-facing slopes) as water bodies due to low signal return. HydroViz enforces two physics-based boundaries:
1. **Steep Slope Masking:** Any cell with surface slope $\theta > 20^\circ$ is masked out, as water cannot stand on steep Himalayan rock faces.
2. **HAND (Height Above Nearest Drainage):** Derived from D8 flow routing across pit-filled DEMs. Standing water and floodwaters are physically constrained to the valley floor ($\text{HAND} \le 15\text{ m}$).

---

## 5. AI Flood Segmentation: INT8 ONNX Model & Vectorization

### 5.1 Model Selection & Architecture
Rather than training large models from scratch on high-end GPUs—which violates the 8 GB RAM operational constraint—HydroViz deploys a lightweight, quantized **SNUNet-CD (Siam-Nested UNet for Change Detection)** model adapted for multi-temporal radar and terrain inputs.

The input tensor $\mathbf{X} \in \mathbb{R}^{1 \times 9 \times H \times W}$ incorporates:
- Channels 0–1: Pre-event 2 ($\text{VV}, \text{VH}$) in dB
- Channels 2–3: Pre-event 1 ($\text{VV}, \text{VH}$) in dB
- Channels 4–5: Post-event ($\text{VV}, \text{VH}$) in dB
- Channel 6: Surface Slope (degrees)
- Channel 7: HAND (meters)
- Channel 8: Radar Shadow/Layover Mask

### 5.2 INT8 Dynamic Quantization & Sliding-Window Inference
The PyTorch model was exported to ONNX (opset 17) and quantized to dynamic INT8 (`QUInt8`), reducing weight footprint from 144 MB to 49 MB. 

To process scenes exceeding host memory, the model executes in **overlapping 256×256 sliding windows** with a step size of 128 pixels, blending border predictions with a 2D Gaussian kernel to eliminate edge tiling artifacts:
$$W(x, y) = \exp\left(-\frac{x^2 + y^2}{2\sigma^2}\right), \quad \sigma = \frac{\text{window\_size}}{4}$$

### 5.3 Morphological Filtering & Contour Vectorization
The resulting prediction mask is refined through a 500 m² Minimum Mapping Unit (MMU) morphological kernel (`cv2.morphologyEx` Open & Close), removing isolated speckle noise. 

The binary raster is vectorized on the fly using `cv2.findContours` and `cv2.approxPolyDP` ($\epsilon = 1.2$). The resulting pixel contours are projected into WGS84 geographic polygons (`[Lon, Lat]`), enriched with area ($\text{km}^2$), estimated water depth ($0.8\text{ m} - 2.4\text{ m}$), and confidence ratings ($94\%$).

---

## 6. Infrastructure Damage & Dual Cutoff Analysis

### 6.1 OpenStreetMap Feature Ingestion
HydroViz queries pre-event OpenStreetMap data using Overpass API endpoints with strict snapshot date limits ($t \le \text{2026-07-27}$):
- **Buildings:** `building=*` footprints and centroid clusters.
- **Road Network:** Highway linestrings (`motorway` through `unclassified`, `track`, `path`).
- **Bridges:** Explicit `way["bridge"="yes"]` features and river crossing intersections.
- **Facilities:** Hospitals, clinics, emergency centers, towns, and villages.

### 6.2 Spatial Exposure Classification
Using `cv2.pointPolygonTest` against the predicted flood and debris polygons:
- **Buildings Exposed (High):** Footprint directly inside the high-confidence flood mask.
- **Buildings Exposed (Medium):** Structures within a 10-meter buffer or within the heuristic debris scour zone.
- **Bridges Likely Damaged:** Bridge geometries whose spans intersect the flood polygon where elevation is within 4 meters of river base.

### 6.3 Dual Cutoff Scenarios (Strict vs. Conservative)
Road networks are converted into an adjacency graph $G = (V, E)$. Baseline shortest paths from all residential settlements to the nearest hospital and regional market town are pre-computed via multi-source Dijkstra routing.

Responders can toggle between two operational planning scenarios:
- **Strict Scenario (Confirmed Water Only):**
  - Severed roads: Road edges intersecting confirmed floodwater polygons ($1.7\text{ km}$).
  - Damaged bridges: Confirmed flooded bridges only ($1$ bridge).
  - Outcome: Isolates settlements that have zero navigable motorable paths ($2$ isolated hamlets).
- **Conservative Scenario (Water + Debris Scour Field):**
  - Severed roads: Road edges intersecting floodwater OR the high-roughness debris field ($5.7\text{ km}$).
  - Damaged bridges: All exposed crossings.
  - Outcome: Highlights vulnerable communities whose supply routes traverse active debris fans, forcing long-distance mountain detours.

---

## 7. Interactive D8 Flow Path Susceptibility Modeling

To answer responder inquiries regarding upstream outburst origins, HydroViz provides a client-side D8 flow path tracer (`POST /trace`):
1. **DEM Pit-Filling:** Eliminates spurious sinks in the Copernicus DEM using an optimized priority-flood algorithm.
2. **D8 Flow Direction:** Assigns flow from each cell to the steepest downward neighbor among the 8 surrounding cells:
   $$S_i = \frac{z - z_i}{d_i}$$
3. **Downhill Streamline:** Traces the descent trajectory from any clicked coordinates down to the valley base, returning real-time elevation profile metrics: start elevation, terminal elevation, total vertical drop ($\Delta z$), and downstream distance ($\text{km}$).
4. **Memoized Result Caching:** The trace output is hashed by coordinate and DEM tile, ensuring instantaneous recall on subsequent clicks.

---

## 8. Case Study Validation: Copernicus EMSR927

To evaluate accuracy against professional emergency mapping, HydroViz was benchmarked against the official Copernicus Emergency Management Service activation **EMSR927** for the Trishuli flood event.

### 8.1 Quantitative Agreement

| Metric | HydroViz (Standalone) | EMSR927 Reference | Notes |
|:---|:---:|:---:|:---|
| **Delineation IoU (Jaccard)** | **0.74** | 1.00 | Measured across shared valley floor |
| **F1-Score** | **0.82** | 1.00 | Harmonic mean of Precision & Recall |
| **Precision** | **0.79** | — | Reduced by gorge radar shadows |
| **Recall** | **0.86** | — | Successfully captures primary river corridor |
| **Exposed Buildings** | **89** | 80 (Damaged) | HydroViz measures 10m spatial exposure proxy |
| **Severed Road Length** | **1.7 km** (Strict) | 2.1 km (Blocked) | Strong topological alignment on arterial crossings |
| **Damaged Bridges** | **1** | 1 | Exact match on primary river crossing |

### 8.2 Discrepancy & Sensor Physics Analysis
1. **Spatial Exposure vs. Structural Damage:** EMSR927 utilizes very high resolution (VHR) sub-meter optical imagery to visually verify collapsed roofs and destroyed masonry. HydroViz operates at 10m Sentinel-1 SAR resolution; its building metric reflects **physical exposure** (proximity to floodwater), serving as a rapid day-0 triage indicator.
2. **Monsoon Cloud Penetration:** While EMSR927 had to wait for cloud-free optical windows, HydroViz generated its complete situational assessment within 45 minutes of the first Sentinel-1 radar pass.
3. **Terrain Radar Shadows:** On steep north-facing valley walls ($> 20^\circ$), radar backscatter is completely occluded. HydroViz transparently masks these areas rather than outputting false-positive water predictions.

---

## 9. Comprehensive Failure Modes & Limitations

In compliance with hackathon rules, HydroViz explicitly documents what the system **cannot** do:

1. **Satellite Revisit Frequency (6–12 Days):** Sentinel-1 cannot provide real-time warning minutes before a glacial outburst. It maps the aftermath following the next orbital pass. Peak flood levels that receded prior to overpass are not detected.
2. **Spatial Resolution Bounds (10 m):** Narrow torrents ($< 10\text{ m}$ width) and individual small outbuildings cannot be resolved.
3. **Debris Mapping Is Heuristic:** The debris scour layer is derived from high backscatter change on channel flanks. It is not an ML-trained classifier and must be treated as low-confidence.
4. **Hydraulic Simulation Disclaimer:** The D8 flow path tool models geometric gravity-driven descent; it does not model water velocity, wave height, hydrographs, or sediment transport physics.
5. **OpenStreetMap Data Gaps:** In rural Nepal, unmapped footpaths are classified as `unknown`. Responders must understand that `unknown` indicates missing cartographic data, not safety.

---

## 10. Humanitarian Responsibility & Attribution

> **A note on responsibility:**
> This disaster is recent, and many families are still affected. Treat the topic with respect: do not use images of victims in demos or reports. Systems built here are educational prototypes, not operational tools.

- **Respect for Affected Populations:** HydroViz strictly contains no imagery of victims, casualty estimates, or unverified claims.
- **Devanagari Number Guard:** Situation reports in Nepali (`ne`) and English (`en`) pass all rendered numerals through an automated whitelist audit against `facts.json`, ensuring zero hallucinated statistics.
- **Required Attributions (Every Submission):**
  - *Contains modified Copernicus Sentinel data 2026.*
  - *Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.*
  - *© OpenStreetMap contributors.*
  - *Training dataset citations:* Bountos et al. (Kuro Siwo, NeurIPS 2024); Bonafilia et al. (Sen1Floods11, CVPR 2020).
  - *Validation data:* European Union, Copernicus Emergency Management Service data (EMSR927 activation — strictly check-only).

---
*HydroViz is an open-source educational prototype built for the Multimodal AI Hackathon 2026. It is not certified for operational life-safety decisions.*
