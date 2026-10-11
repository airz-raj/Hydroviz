# HydroViz — Himalayan Flood Response Prototype

## What It Does

Given an **area (bbox)** and a **flood date**, HydroViz uses free satellite data to answer three questions for rescue teams:

1. **Where did the flood hit?** — Sentinel-1 radar change detection (works through clouds) + Sentinel-2 optical when clear
2. **What was damaged?** — Buildings, roads and bridges from OpenStreetMap overlaid on the hazard map
3. **Who is cut off?** — Road network analysis showing which settlements lost access to towns and hospitals

Plus: AI flood segmentation model using lightweight pre-trained ONNX weights (optimized for 8GB RAM), flood path tracing from elevation data, and case-study comparison with Copernicus EMS.

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2
- CDSE account ([register free](https://dataspace.copernicus.eu/))
- 16 GB RAM minimum (32 GB recommended)

### Setup

```bash
# 1. Clone
git clone https://github.com/YOUR_ORG/hydroviz.git
cd hydroviz

# 2. Configure
cp .env.example .env
# Edit .env with your CDSE credentials and a PostgreSQL password

# 3. Start
docker compose up --build

# 4. Open
# Dashboard: http://localhost:8000
# API docs:  http://localhost:8000/docs
```

### Run Analysis via API

```bash
# 1. Submit an AOI Scan (Accepts [Lon, Lat] or [Lat, Lon] automatically)
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [85.20, 27.50, 85.90, 28.15],
    "event_date": "2026-08-26",
    "osm_snapshot": "2026-07-27",
    "options": {
      "hand_threshold_m": 15.0,
      "steep_slope_deg": 20.0
    }
  }'

# 2. Check Job Status
curl http://localhost:8000/jobs/{job_id}/status

# 3. Retrieve Computed Facts & Metrics
curl http://localhost:8000/jobs/{job_id}/facts

# 4. Interactive Downhill D8 Flow Path Tracing (Bonus)
curl -X POST http://localhost:8000/trace \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [85.20, 27.50, 85.90, 28.15],
    "origin": [85.55, 27.85]
  }'

# 5. Access Check-Only Copernicus EMSR927 Benchmark Metrics
curl http://localhost:8000/case-study/emsr927

# 6. View Humanitarian Situation Briefings
# English: http://localhost:8000/jobs/{job_id}/report/en
# Nepali:  http://localhost:8000/jobs/{job_id}/report/ne
```

### Running Tests

```bash
# Run full unit and live pipeline integration suite
pytest -v
```

---

## Repository Structure

```
hydroviz/
├── README.md                           ← You are here
├── ARCHITECTURE.md                     ← System design, data flow, schemas
├── IMPLEMENTATION_PLAN.md              ← Step-by-step build guide (M0–M8)
├── DECISIONS.md                        ← Decision log and open questions
├── AGENT_BRIEF.md                      ← Original engineering specification
├── docker-compose.yml                  ← Full stack orchestration
├── .env.example                        ← Required environment variables
│
├── contracts/                          ← JSON Schemas
│   ├── job_request.schema.json
│   ├── job_status.schema.json
│   └── facts.schema.json
│
├── services/
│   ├── gateway/                        ← FastAPI: jobs, progress SSE, dashboard
│   ├── ingest/                         ← Catalogue search, S1/S2 fetch, OSM, cache
│   ├── flood_ml/                       ← Terrain features, segmentation, post-processing
│   ├── geo_core/                       ← Rust: exposure, cut-off, flood path
│   └── report/                         ← Sitrep templates (EN/NE), number guard, PDF
│
├── training/                           ← Model evaluation, ONNX export, and quantization
│   ├── datasets/                       ← Kuro Siwo + Sen1Floods11 loaders (for evaluation)
│   ├── configs/                        ← Inference hyperparameters
│   └── model_card.md                   ← Data, metrics, failure modes
│
├── dashboard/                          ← MapLibre GL JS frontend
│   ├── layers/                         ← Flood, exposure, cut-off, path layers
│   ├── components/                     ← Sidebar, swipe, job form
│   └── assets/                         ← Icons, fonts
│
├── validation/                         ← CHECK ONLY: EMSR927 comparison
│   ├── reference_data/                 ← Downloaded EMS products
│   └── notebooks/                      ← Analysis notebooks
│
├── tests/                              ← Unit, integration, smoke tests
│   ├── unit/
│   ├── integration/
│   ├── smoke/
│   └── fixtures/                       ← Synthetic test data
│
├── docs/                               ← Report, limitations, demo script
│   ├── report.md                       ← 6-page report
│   ├── limitations.md                  ← What the system cannot do
│   ├── demo_script.md                  ← 3-minute demo walkthrough
│   └── figures/                        ← Report figures
│
└── scripts/                            ← Utility scripts
```

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, service topology, database schema, data flow |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Procedural build guide with acceptance criteria per milestone |
| [DECISIONS.md](DECISIONS.md) | All technical decisions, deviations, and open questions |
| [AGENT_BRIEF.md](AGENT_BRIEF.md) | Original engineering specification |

---

## Data Sources

| Source | Use | Licence |
|--------|-----|---------|
| [Sentinel-1 / Sentinel-2](https://dataspace.copernicus.eu) | Before/after imagery | Copernicus free, full and open |
| [Copernicus DEM GLO-30](https://dataspace.copernicus.eu) | Terrain analysis | See attribution below |
| [OpenStreetMap via ohsome](https://api.ohsome.org/v1) | Buildings, roads, bridges | ODbL |
| [Kuro Siwo](https://github.com/Orion-AI-Lab/KuroSiwo) | Pre-trained Weights Source | MIT / CC BY |
| [Sen1Floods11](https://github.com/cloudtostreet/Sen1Floods11) | Pre-trained Weights Source (optional) | CC BY 4.0 |
| [Copernicus EMS EMSR927](https://mapping.emergency.copernicus.eu) | **Check only** | Free with attribution |

---

## Required Attribution & Humanitarian Responsibility

### A note on responsibility:
> This disaster is recent, and many families are still affected. Treat the topic with respect: do not use images of victims in demos or reports. Systems built here are educational prototypes, not operational tools.

### Mandatory Submission Attribution:
> Contains modified Copernicus Sentinel data 2026.

> Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.

> © OpenStreetMap contributors.

**Pre-trained weights citations:**
- Bountos, N.I., et al. (2024). Kuro Siwo: A global multi-temporal SAR dataset for rapid flood mapping. *NeurIPS Datasets and Benchmarks*.
- Bonafilia, D., et al. (2020). Sen1Floods11: A georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1. *CVPR Workshops*.

**Validation data:**
- European Union, Copernicus Emergency Management Service data (EMSR927 activation — strictly check-only).

---

## License

This software is licensed under the open-source **[MIT License](LICENSE)**.

### Upstream & Dataset Licenses
In accordance with the Track B guidelines:
- **HydroViz Codebase:** [MIT License](LICENSE)
- **Sentinel-1 & Sentinel-2 Satellite Data:** [Copernicus Free, Full, and Open Data Policy](https://dataspace.copernicus.eu/) (any use allowed).
- **Copernicus WorldDEM-30:** © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the EU and ESA; all rights reserved.
- **OpenStreetMap Data:** [Open Database License (ODbL 1.0)](https://opendatacommons.org/licenses/odbl/) — any published derivative OSM data remains under ODbL.
- **Kuro Siwo Pre-trained Weights:** [MIT License](https://github.com/Orion-AI-Lab/KuroSiwo) (NeurIPS 2024 / CC BY). Free use with credit; cite Bountos et al., 2024.
- **Sen1Floods11 Pre-trained Weights:** [CC BY 4.0](https://github.com/cloudtostreet/Sen1Floods11) for non-commercial educational use; cite Bonafilia et al., 2020.
- **Copernicus EMS (EMSR927):** Check-only validation data provided free with attribution.
