# HydroViz — Developer & Agent Rules

To ensure all developers and autonomous AI agents working on the HydroViz codebase maintain the same baseline and do not break the strict hackathon constraints, **everyone must strictly adhere to the following rules.**

---

## 1. The 8GB RAM Constraint (Strict)
This prototype is designed for rapid disaster response, meaning it must be able to run locally on an 8GB RAM laptop. 
- **No Training from Scratch:** Do not attempt to train massive deep learning models inside the Docker containers. Use pre-trained weights (e.g., ONNX format) downloaded separately.
- **No PyTorch in Containers:** Do not add `torch` to any `requirements.txt` meant for production containers. Use `onnxruntime` for CPU-optimized inference.
- **Memory Chunking:** When processing satellite imagery, **never** load an entire 2500x2500 TIFF into memory. Always use `rasterio.windows` to process in 512x512 chunks sequentially. 
- **Garbage Collection:** Always `del` large variables and run `gc.collect()` at the end of loops when handling raster arrays.

## 2. Dynamic Documentation (For AI Agents & Humans)
The architecture and implementation plan of this project are living documents. 
- **Rule of Synchronization:** Any AI agent or developer making structural changes, pivoting a technical approach, or discovering a limitation **MUST simultaneously update the relevant `.md` files** (`IMPLEMENTATION_PLAN.md`, `ARCHITECTURE.md`, `DECISIONS.md`, or `docs/limitations.md`).
- **Do not drift from the baseline:** Do not implement "ghost features" that aren't documented. If you write the code, you write the documentation. This ensures that the next agent or teammate picking up the context has a perfectly accurate understanding of the current system state.

## 3. Strict One-Way Data Flow
- Data must flow in one direction: `Ingestion -> Shared COG Store -> Feature Extraction -> ML Inference -> Geo Core -> Report -> Dashboard`. 
- Containers must communicate via shared volumes (`/data`, `/shared`) and the Redis job queue, not via convoluted ad-hoc HTTP requests between microservices, unless explicitly defined in the architecture (e.g. gateway endpoints).

## 4. No EMSR927 Data in Pipeline
- Copernicus EMSR927 maps and data are strictly for **validation only** (`/validation/`). 
- Do **not** use them to tune thresholds, train models, or calibrate post-processing rules. Any use of EMSR927 data in the core pipeline will immediately disqualify the team.

## 5. Environment Variables & Paths
- Always use relative paths bound to the `/data` or `/shared` volume (e.g., `/data/models/flood_seg_v1.onnx`) inside containers.
- Never hardcode absolute paths like `/Users/admin/...` or `./models/...` in scripts intended to run inside Docker. Always fall back to `os.getenv()`.

## 6. Heuristic and Confidence Tracking
- Debris detection is heuristic, not a trained ML class.
- Always append the methodology and filters used to the provenance log via `shared.attribution.add_provenance`. This ensures the final Situation Report accurately reflects what algorithms generated the data.

## 7. Changelog Maintenance
- After every update via agent, you must update the `CHANGELOG.md` file to reflect the changes made. This ensures the project history remains transparent and up-to-date.
