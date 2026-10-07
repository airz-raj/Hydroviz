# HydroViz — Known Limitations

> Write this section from day one. Update after each milestone.
> This becomes part of the 6-page report and the dashboard's limitations box.

---

## Fundamental Limitations

### 1. Satellite Revisit Timing
Sentinel-1 revisits an area every **6–12 days** (depending on constellation status). The system **cannot** warn of a sudden glacier collapse minutes ahead. It can only show the aftermath once the next overpass occurs. The mapped extent reflects the **acquisition time**, not the peak flood — which may have been hours or days earlier.

### 2. Spatial Resolution (10 m)
At 10 m pixel spacing, the system **cannot**:
- Resolve individual buildings smaller than ~100 m²
- Detect damage to a single structure (it detects "exposure", not "destruction")
- Map narrow gorge channels (< 10 m wide)
- Distinguish a damaged bridge from an intact one visually

The term "exposed" means "spatially coincident with flood hazard". It is a proxy for potential damage, not confirmed damage.

### 3. SAR in Steep Terrain
Radar imaging geometry creates **shadow** (no signal behind steep ridges) and **layover** (compressed signals on steep slopes). These cause:
- **False positives:** shadow areas can mimic water (low backscatter)
- **Blind spots:** layover areas cannot be analysed

The terrain mask reduces but does not eliminate these artefacts. In deep Himalayan gorges, shadow can affect 10–30% of the valley floor.

### 4. Debris Detection Is Heuristic
No training data exists for debris in mountainous flood events. The debris layer is **rule-based** (strong backscatter change outside water, near the channel, on plausible slopes). It has **not been validated** against ground truth. Treat debris detections as low-confidence indicators.

### 5. Cloud Cover Blocks Optical Data
Sentinel-2 optical images are frequently unusable during the monsoon season. When cloud cover exceeds the threshold, the system runs **SAR-only mode**, losing:
- Visual confirmation via optical imagery
- NDWI-based water detection refinement
- True-colour pre/post comparison

### 6. OpenStreetMap Completeness
OSM coverage in **rural Nepal** is incomplete. Unmapped roads, buildings, or settlements **cannot** be assessed. A settlement classified as `unknown` means "no data", not "safe". In some areas, only major highways are mapped, while local tracks that villages depend on are missing.

### 7. Pre/Post Temporal Gap
Pre-event and post-event acquisitions may be **days to weeks apart**. Changes from other causes (agriculture, construction, seasonal water level changes) may be misattributed to the flood. The system mitigates this by using multi-temporal pre-event baselines but cannot fully eliminate it.

### 8. Flood Path Is Not Hydraulic Modelling
The bonus flood-path feature traces a **terrain-based susceptibility corridor** using D8 flow direction and HAND. It does **not** simulate:
- Flow velocity or arrival time
- Water volume or depth
- Dam-break or glacier-lake outburst dynamics
- Sediment transport

It shows "where water would flow downhill", not "what actually happened".

### 9. Domain Shift in ML Model
The segmentation model is trained primarily on **lowland flood events** (Kuro Siwo). Himalayan terrain is fundamentally different:
- Steeper slopes, narrower valleys
- More shadow/layover
- Debris flows (not in training data)
- Different land cover (terraced agriculture, sparse settlements)

Evaluation on Himalayan scenes uses weak labels and should be interpreted cautiously.

### 10. Educational Prototype
This system is built for a hackathon. It has **not** been validated for operational use. It has not undergone the testing, redundancy, and review required for emergency response tools. Real disaster response should use operationally validated systems like Copernicus EMS.

---

## Quantified Limitations (update after evaluation)

| Limitation | Measured Impact | Mitigation |
|-----------|----------------|------------|
| Shadow/layover coverage | _TBD_ % of AOI affected | Terrain mask, confidence labelling |
| Cloud cover (case study) | _TBD_ % of S2 unusable | SAR-only fallback |
| OSM road coverage | _TBD_ % of known roads mapped | `unknown` classification, document gap |
| False positive rate | _TBD_ % | Post-processing, terrain masks |
| Model domain shift | _TBD_ IoU drop on Himalayan scenes | Terrain channels, augmentation |

---

## What "Exposed" Actually Means

| We say | We mean | We do NOT mean |
|--------|---------|----------------|
| "Exposed (high)" | Building footprint overlaps high-confidence flood mask | Building is destroyed or even damaged |
| "Exposed (medium)" | Building within 10 m of hazard | Building was flooded |
| "Likely damaged" (bridge) | Bridge geometry overlaps flood AND is near river level | Bridge has collapsed |
| "Isolated" | Road connection to town/hospital appears severed | No help can reach them |
| "Unknown" | No OSM road data for this settlement | Settlement is safe |
