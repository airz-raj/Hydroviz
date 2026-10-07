# HydroViz — Validation Guide (CHECK ONLY)

> ⚠️ This package is CHECK ONLY. It compares pipeline outputs against reference data.
> **Data flows one way: pipeline → validation. NEVER validation → pipeline.**
> No data from this package may be used for training, tuning, or model selection.

---

## Purpose

Compare HydroViz results with:
1. **Copernicus EMS EMSR927** — official emergency mapping for this event
2. **Government damage reports** — reported bridge/road damage figures (qualitative check)

---

## Reference Data

### EMSR927

**Source:** https://mapping.emergency.copernicus.eu (activation EMSR927)

**Products to download:**
- Delineation maps (flood extent polygons)
- Grading maps (damage assessment per building/infrastructure)
- Available as GeoPackage or GeoJSON

**Storage:** `validation/reference_data/emsr927/`

**Attribution:** "European Union, Copernicus Emergency Management Service data"

### Government Reports

**Source:** NDRRMA situation reports (as cited in Track B brief)

**Data points:**
- Reported bridge damage count
- Reported road damage km
- Settlement impact reports

**Storage:** `validation/reference_data/government/`

---

## Comparison Methodology

### 1. Flood Extent Comparison

```python
# Rasterise both to same grid (10m, matching our output)
our_mask = rasterise(our_flood_polygons, grid)        # binary
ems_mask = rasterise(emsr927_delineation, grid)       # binary

# Compute metrics
tp = (our_mask & ems_mask).sum()
fp = (our_mask & ~ems_mask).sum()
fn = (~our_mask & ems_mask).sum()

iou = tp / (tp + fp + fn)
precision = tp / (tp + fp)
recall = tp / (tp + fn)
f1 = 2 * precision * recall / (precision + recall)
```

**Important caveats to document:**
- Timing difference: our S1 acquisition vs EMS reference acquisition may differ
- EMS uses manual interpretation + multiple sources; we use automated SAR only
- EMS delineation may include areas we classify as debris, or vice versa
- Resolution differences possible

### 2. Building Exposure Comparison

| Our Output | EMS Output | Comparison |
|-----------|-----------|------------|
| `exposed_high` count | `destroyed` + `damaged` count | These measure DIFFERENT things |
| `exposed_medium` count | — | No EMS equivalent |

**We measure "exposed"** = spatially coincident with flood at 10m resolution.
**EMS measures "damaged"** = observed structural damage from high-resolution imagery + field reports.

Report both numbers with this explanation. Do NOT claim they should match.

### 3. Bridge Comparison

| Our Output | Reference | Notes |
|-----------|-----------|-------|
| `likely_damaged` bridges | Reported damaged bridges | Our method: spatial overlap + HAND height |
| | | Government reports may include different bridges |

### 4. Spatial Agreement Map

Generate a map showing:
- **Green:** Both agree (flood in both)
- **Blue:** Only our system detects (our FP or EMS miss)
- **Red:** Only EMS detects (our FN or EMS FP)
- **Grey:** Both agree (no flood)

Annotate disagreement clusters with likely causes:
- Gorge shadow
- Timing difference
- Different flood definition (standing water vs debris)
- Resolution

---

## Scripts

| Script | Purpose |
|--------|---------|
| `download_emsr927.py` | Download EMSR927 reference products |
| `compare_flood.py` | Flood extent IoU/F1 comparison |
| `compare_exposure.py` | Building/bridge count comparison |
| `metrics.py` | Shared metric computation functions |
| `report.py` | Generate comparison tables and figures |

---

## Output

Generate into `validation/output/`:
- `flood_comparison_metrics.json` — IoU, F1, precision, recall
- `spatial_agreement_map.png` — colour-coded agreement map
- `building_comparison_table.md` — side-by-side counts with caveats
- `bridge_comparison_table.md` — bridge-level comparison
- `disagreement_analysis.md` — annotated explanation of discrepancies

---

## Rules (enforced)

1. ❌ Never import from `validation/` in any service code
2. ❌ Never use EMSR927 polygons as training labels
3. ❌ Never tune thresholds to improve EMSR927 agreement
4. ❌ Never copy EMSR927 building damage counts into facts.json
5. ✅ Only read pipeline outputs (facts.json, masks, vectors)
6. ✅ Only read from `validation/reference_data/`
7. ✅ Write comparison outputs to `validation/output/`
