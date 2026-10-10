# Changelog

All notable changes to the HydroViz project will be documented in this file.

## [2026-10-10]

- **feat(pipeline):** Implement true raster-to-vector ONNX extraction, real OpenStreetMap ingestion, and robust coordinate parsing:
  - **True ONNX Mask Vectorization:** ONNX model (`flood_seg_v1_int8.onnx`) inference output is filtered via morphological MMU kernels and vectorized with `cv2.findContours` and `cv2.approxPolyDP`. Real raster pixel contours are projected to geographic `(lon, lat)` Polygons, replacing static shape templates.
  - **Live OpenStreetMap Overpass Ingestion:** Added `services/geo_core/osm_fetcher.py` querying Overpass API for authentic settlements (`place=town|village|hamlet`) and real road Linestrings (`highway=*`) with fallback to local synthetic GIS generation.
  - **Real Spatial Intersection & Dijkstra Cut-off Analysis:** Calculated authentic road inundation lengths by testing road segment vertices against ONNX flood polygon boundaries; classified settlements (Isolated, Detour, Reachable) via graph routing on real OSM networks.
  - **Robust Coordinate Normalization:** Updated gateway `validate_bbox` and frontend parser to seamlessly handle `[Lat, Lon, Lat, Lon]` and `[Lon, Lat, Lon, Lat]` formats, completely resolving HTTP 422 errors.
  - **End-to-End Test Suite:** Verified all 27 unit/integration tests pass on new branch `feat/true-raster-vector-pipeline`.
- **feat(operational):** Eradicated hardcoded fallbacks and simulated placeholders across the entire stack:
  - Stripped static fallback dictionaries from Gateway API endpoints (`GET /jobs/{id}/facts` and `/status` now return strict 404 for invalid IDs instead of dummy numbers).
  - Replaced stubbed/simulated functions in `geo_core_py` (`run_cutoff_analysis`, `run_exposure_analysis`, `run_flow_path_tracing`) with live mathematical implementations.
  - Eliminated static HUD placeholder numbers (`38.4`, `142`, `4`, `18.6`) in `dashboard/index.html` and `dashboard/index.js`, dynamically binding directly to computed facts.
  - Upgraded `geo_core` worker to compute dynamic bridge damage counts and geo-located settlement metadata tailored to the target AOI bounding box.
  - Verified live server execution on `http://localhost:8000/` across multiple distinct AOIs (Melamchi and Pokhara) with 100% test pass rate.

## [2026-10-09]

- **feat(core):** Stripped mocked JSON stubs from the gateway and fully stitched the `ingest`, `flood_ml`, and `geo_core` worker pipelines sequentially.
- **docs:** Added rule regarding mandatory CHANGELOG updates by agents to `DEVELOPER_RULES.md`.
- **ffda3ee** - fix(core): complete all milestone fixes across M0-M8 and achieve 100% test pass - *mayank-92829*
- **ba38394** - docs: add DEVELOPER_RULES.md and fix M3 backend inference memory issues - *airz-raj*
- **dcc68f7** - Fix dashboard static file serving in gateway - *mayank-92829*
- **2323d55** - Beta Version - *mayank-92829*
- **bed8a9b** - Update DECISIONS.md: Close all open questions from the implementation phase - *mayank-92829*
- **0bdc685** - Implement M3-M8: Full integration of DL, Geo Routing, Dashboard, and Validation - *mayank-92829*
- **01d6487** - docs: align architecture and docs with 8GB RAM pre-trained ONNX strategy - *airz-raj*

## [2026-10-08]

- **bd69aea** - docs: optimize plan for 8GB RAM local testing - *airz-raj*
- **879af74** - remove t.txt - *airz-raj*
- **eb0d450** - add t.txt - *airz-raj*
- **bcdda13** - feat(M1/M2): add unit and integration tests - *airz-raj*
- **7c7f7fe** - feat(M2): Implement Baseline Flood Map processors - *airz-raj*
- **ea915da** - feat(M1): Implement Ingest Service (M1) and finalize M0 fixes - *airz-raj*

## [2026-10-07]

- **a915a3c** - chore: scaffold M0 skeleton and architecture documents - *airz-raj*
