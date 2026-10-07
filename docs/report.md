# HydroViz — Report (Draft)

> Maximum 6 pages. Include limitations section.
> Update after each milestone as results become available.

---

## Title
**HydroViz: Satellite-Based Flood Damage Mapping and Cut-Off Analysis for Himalayan Disaster Response**

*Multimodal AI Hackathon 2026 — Track B*

---

## Abstract (0.25 pages)

HydroViz is a prototype system that maps flood damage from free satellite data for rescue teams. Given an area and a flood date, it: (1) detects flooded and debris-covered areas from Sentinel-1 radar change detection, (2) identifies exposed buildings, roads, and bridges using pre-event OpenStreetMap data, (3) determines which settlements have lost road access to towns and hospitals, and (4) uses a trained segmentation model to improve flood detection accuracy. We demonstrate the system on the August 2026 Bhote Koshi–Trishuli flood in Nepal and compare results with Copernicus Emergency Management Service maps. We report limitations honestly, particularly regarding the 10 m resolution, radar shadow in steep terrain, and incomplete OSM coverage.

---

## 1. Introduction (0.5 pages)

### 1.1 Problem
On 26 August 2026, a partial glacier collapse in northern Nepal triggered a catastrophic flood of water, mud, and debris down the Bhote Koshi–Trishuli river corridor. Ground sensors were swept away. Roads, bridges, and communications failed. Rescue teams needed answers: where is the damage worst, and which villages are cut off?

### 1.2 Approach
Free satellite data covers every valley of the Himalaya. Synthetic aperture radar (SAR) penetrates monsoon clouds. OpenStreetMap provides pre-disaster infrastructure data. We combine these into an end-to-end pipeline that answers three core questions automatically.

### 1.3 Scope
HydroViz is an educational prototype. It demonstrates what is achievable with freely available data and modern AI, but has not been validated for operational emergency response.

---

## 2. System Design (1 page)

### 2.1 Architecture
[Refer to ARCHITECTURE.md — include simplified data flow diagram here]

Five services: ingest (data acquisition), flood-ml (detection), geo-core (analysis), report (situation report), and gateway (API + dashboard).

### 2.2 Data Sources
- **Sentinel-1 C-band SAR** (IW GRD, 10 m): before/after change detection
- **Sentinel-2 optical** (L2A, 10 m): supplementary when cloud-free
- **Copernicus DEM GLO-30**: terrain features
- **OpenStreetMap** (pre-event snapshot via ohsome API): infrastructure

### 2.3 Key Design Decisions
- Control plane (JSON messages) separated from data plane (shared files + PostGIS)
- Every user-facing number sourced from a single `facts.json` store
- Rust for performance-critical graph and spatial operations
- Template-first reporting with a number guard that rejects fabricated figures

---

## 3. Flood Detection (1.25 pages)

### 3.1 Baseline: Log-Ratio Change Detection
[Description of VV/VH log-ratio, adaptive thresholding, terrain masks]

### 3.2 Learned Model: Segmentation
[Architecture (U-Net + terrain channels), training data (Kuro Siwo), loss function, training procedure]

### 3.3 Post-Processing
[Permanent water removal, shadow/layover suppression, minimum mapping unit, confidence assignment]

### 3.4 Debris Layer
[Rule-based heuristic, clearly labelled as unvalidated]

### 3.5 Results
[Metrics table: baseline vs learned model, held-out test set]

---

## 4. Damage Assessment and Cut-Off Analysis (1 page)

### 4.1 Exposure Analysis
[Building, road, bridge overlay method. R-tree spatial indexing. Distinction between "exposed" and "damaged".]

### 4.2 Cut-Off Analysis
[Road graph construction. Two scenarios (strict/conservative). Multi-source routing. Settlement classification.]

### 4.3 OSM Coverage Limitation
[Discussion of incomplete coverage, "unknown" classification]

---

## 5. AI Component: Evaluation (0.75 pages)

### 5.1 Training Details
[Dataset, splits, augmentation, hyperparameters]

### 5.2 Held-Out Performance
[Table: per-class IoU, F1, precision, recall]

### 5.3 Himalayan Evaluation
[Weak-label methodology. Results. Domain shift analysis. Performance stratified by slope and shadow.]

### 5.4 Model Card Summary
[Data provenance, licences, known failure modes]

---

## 6. Case Study: August 2026 Trishuli Flood (0.75 pages)

### 6.1 Comparison with EMSR927
[IoU, precision, recall for flood extent. Building count comparison with caveats.]

### 6.2 Where We Agree and Disagree
[Spatial maps showing agreement/disagreement. Analysis of causes: gorge geometry, shadow, timing.]

---

## 7. Limitations (0.5 pages)

[Condensed from docs/limitations.md. Key points:]

1. Satellite revisit: days, not minutes. Cannot warn in real-time.
2. 10 m resolution: "exposed" ≠ "damaged". Cannot resolve individual buildings.
3. Radar shadow in steep terrain: blind spots and false positives.
4. Debris detection: heuristic, not trained. Low confidence.
5. Cloud cover: SAR-only when optical is unavailable.
6. OSM incompleteness: unmapped ≠ safe.
7. Flow path: terrain susceptibility corridor, not hydraulic model.
8. Educational prototype: not validated for operations.

---

## References

- Bountos, N.I., et al. (2024). Kuro Siwo: A global multi-temporal SAR dataset for rapid flood mapping. *NeurIPS Datasets and Benchmarks*.
- Bonafilia, D., et al. (2020). Sen1Floods11: A georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1. *CVPR Workshops*.
- [Additional references to be added]

---

## Attributions

> Contains modified Copernicus Sentinel data 2026.
>
> Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.
>
> © OpenStreetMap contributors.
>
> European Union, Copernicus Emergency Management Service data (validation comparison only).
