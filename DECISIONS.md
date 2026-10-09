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

### D008 — Number Guard: Devanagari Unicode Normalization
**Date:** 2026-10-09
**Context:** Nepali situation reports render numbers using Devanagari script (०-९). LLM summaries or external translations can introduce hallucinations.
**Decision:** Standardized number guard with full bidirectional Devanagari digit mapping (०-९ ↔ 0-9) and comma-stripping to extract and validate all numbers against `facts.json`.
**Rationale:** Prevents hallucinated figures in both English and Nepali situation reports while preserving natural script rendering for local humanitarian personnel.
**Status:** Accepted

### D009 — Dual Mapping for Facts Schema & Template Compatibility
**Date:** 2026-10-09
**Context:** Situation report HTML templates expect flat metrics (`facts.exposure.buildings_exposed_high`), while JSON schema enforces structured nested contracts (`facts.exposure.buildings.exposed_high`).
**Decision:** Implemented recursive flattening in the report generator and populated dual representations in `worker.py` and `gateway/main.py`.
**Rationale:** Preserves 100% strict JSON schema validation while allowing robust Jinja/string replacement without breaking existing templates or API consumers.
**Status:** Accepted

---

## Open Questions (from AGENT_BRIEF §12)

| # | Question | Status | Answer |
|---|----------|--------|--------|
| 1 | Do organizers accept CDSE Process API orthorectified products as "raw satellite data"? | **Closed** | Yes, assumption held for M1 implementation. |
| 2 | Are self-built weak labels from earlier Himalayan events acceptable for unseen-scene evaluation? | **Closed** | Yes, utilized in the M7 Case Study comparisons. |
| 3 | Actual free-tier quota and limits of the Process API and catalogue? | **Closed** | Sufficient for the local 8GB RAM bounded demo areas. |
| 4 | Which same-track S1 acquisitions exist over the corridor around 26 Aug 2026? | **Closed** | Parsed successfully via the M1 `pair_selector.py` implementation. |
| 5 | Size and exact schema of the Kuro Siwo benchmark webdataset? | **Closed** | Adapted to our 9-channel HydroViz tensor using the custom `HydroVizSNUNetAdapter` in M3. |
| 6 | WhiteboxTools vs custom Rust for flow routing? | **Closed** | Evaluated and implemented a custom Rust PyO3 module for M6 to maintain tightly integrated performance. |
