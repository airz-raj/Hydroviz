# HydroViz — Decision Log

> Every deviation from the AGENT_BRIEF, every assumption made, and every technical choice recorded here.
> Format: date, decision, rationale, alternatives considered.

---

## Format

```
### DXXX — [Title]
**Date:** YYYY-MM-DD
**Context:** Why this decision was needed
**Decision:** What was decided
**Rationale:** Why this option was chosen
**Alternatives considered:**
1. Option A — why rejected
2. Option B — why rejected
**Status:** Accepted | Superseded by DXXX | Under review
```

---

## Decisions

### D001 — AI Component: Flood Segmentation Model
**Date:** 2026-10-08
**Context:** Track B offers two AI component choices: flood segmentation model OR situation-report copilot. Must choose one.
**Decision:** Flood segmentation model (Pre-trained ONNX procurement, evaluated on Himalayan scenes).
**Rationale:** Aligns with AGENT_BRIEF. To meet the 8GB RAM local testing constraint, we pivot from training from scratch to downloading a pre-trained model (e.g. Prithvi-EO) and running it via ONNXRuntime with INT8 quantization.
**Alternatives considered:**
1. Situation-report copilot — still partially implemented via template + optional LLM paraphrase, but not the primary AI component.
**Status:** Accepted

### D002 — geo-core Implementation: Rust with PyO3
**Date:** 2026-10-07
**Context:** geo-core needs high-performance spatial operations (R-tree overlay, graph routing). Options: pure Python, Rust standalone (gRPC), Rust with PyO3.
**Decision:** Rust with PyO3/maturin, compiled as a Python extension module.
**Rationale:** Avoids gRPC overhead for the demo. Direct function calls from Python worker. Rust gives performance for graph + spatial ops. PyO3 is mature enough.
**Alternatives considered:**
1. Pure Python (networkx + shapely) — too slow for full corridor graph routing
2. Rust standalone with gRPC — added complexity, another container, serialisation overhead
**Status:** Accepted

### D003 — Queue: In-Process for Demo, Redis Optional
**Date:** 2026-10-07
**Context:** AGENT_BRIEF suggests Redis queue but notes it's optional for demo.
**Decision:** Start with in-process async queue (Python asyncio). Add Redis later only if needed.
**Rationale:** Reduces moving parts. Demo doesn't need distributed job processing. Can upgrade to Redis without architecture change (same message format).
**Alternatives considered:**
1. Redis from day one — more infrastructure to manage during development
**Status:** Accepted

### D004 — S1 Preprocessing: CDSE Process API (not local SNAP)
**Date:** 2026-10-07
**Context:** S1 data needs terrain correction and calibration. Options: CDSE Process API (remote), local SNAP (heavy).
**Decision:** Use CDSE Sentinel Hub Process API with `orthorectify=true` and Copernicus 30m DEM, requesting gamma0 terrain in dB.
**Rationale:** Avoids installing SNAP (10+ GB, slow, complex). API handles orthorectification server-side. Need to verify free-tier limits.
**Alternatives considered:**
1. Local SNAP processing — fallback if API quota insufficient
**Status:** Accepted — must verify quota early (M1)

### D005 — Training Dataset: Pre-trained Weights (No Local Training)
**Date:** 2026-10-08
**Context:** Training a UNet from scratch on a massive dataset inside a Docker container will OOM on an 8GB machine.
**Decision:** Do not train a model from scratch. Download open-source pre-trained weights (Sen1Floods11 or Kuro Siwo) and convert to ONNX.
**Rationale:** Fits within 8GB RAM constraint. ONNX Runtime handles inference efficiently. Memory chunking and aggressive GC will be used.
**Alternatives considered:**
1. Training locally on full dataset — OOM crash guaranteed on 8GB RAM.
2. Cloud training — outside the scope of local hackathon testing.
**Status:** Accepted

### D006 — Flow Routing: Evaluate WhiteboxTools First
**Date:** 2026-10-07
**Context:** Bonus flood path needs D8 flow direction, pit filling, flow accumulation. Options: WhiteboxTools (Rust-native), custom Rust implementation.
**Decision:** Evaluate WhiteboxTools first. Fall back to custom Rust only if it doesn't integrate well.
**Rationale:** WhiteboxTools is well-tested for hydrological analysis. Avoids reimplementing complex algorithms.
**Alternatives considered:**
1. Custom Rust D8 — more control but high effort for correct implementation
2. Python richdem/pysheds — too slow for large DEMs
**Status:** Under review — evaluate during M6

### D007 — OSM Snapshot Date: 2026-07-27
**Date:** 2026-10-07
**Context:** AGENT_BRIEF states the latest pre-event OSM snapshot via ohsome is 27 July 2026.
**Decision:** Use `2026-07-27` as the default OSM snapshot date. Verify via ohsome API metadata.
**Rationale:** This is the most recent available snapshot before the event (26 Aug 2026). Must confirm via API.
**Alternatives considered:**
1. Earlier date — less complete data, no advantage
**Status:** Accepted — verify API metadata during M1

---

## Open Questions (from AGENT_BRIEF §12)

| # | Question | Status | Answer |
|---|----------|--------|--------|
| 1 | Do organizers accept CDSE Process API orthorectified products as "raw satellite data"? | **Open** | — |
| 2 | Are self-built weak labels from earlier Himalayan events acceptable for unseen-scene evaluation? | **Open** | — |
| 3 | Actual free-tier quota and limits of the Process API and catalogue? | **Open** | — |
| 4 | Which same-track S1 acquisitions exist over the corridor around 26 Aug 2026? | **Open** | Query during M1 |
| 5 | Size and exact schema of the Kuro Siwo benchmark webdataset? | **Open** | Verify during M3 |
| 6 | WhiteboxTools vs custom Rust for flow routing? | **Open** | Evaluate during M6 |
