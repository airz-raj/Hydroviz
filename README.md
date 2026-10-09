# HydroViz — Himalayan Flood Response Prototype

> Multimodal AI Hackathon 2026 · Track B: Mapping Flood Damage from Space

⚠️ **Educational prototype — not for operational decisions.**

---

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

### Run a Job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [85.0, 27.5, 86.5, 28.5],
    "event_date": "2026-08-26",
    "osm_snapshot": "2026-07-27"
  }'
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

## Required Attribution

> Contains modified Copernicus Sentinel data 2026.

> Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.

> © OpenStreetMap contributors.

**Pre-trained weights citations:**
- Bountos, N.I., et al. (2024). Kuro Siwo: A global multi-temporal SAR dataset for rapid flood mapping. *NeurIPS Datasets and Benchmarks*.
- Bonafilia, D., et al. (2020). Sen1Floods11: A georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1. *CVPR Workshops*.

**Validation data:**
- European Union, Copernicus Emergency Management Service data.

---

## Licence

[TBD — confirm with team]
