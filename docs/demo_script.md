# HydroViz — Demo Script (3-Minute Video)

> Target: judges who want to see the system work end-to-end, understand the AI component, and trust the results.

---

## Timing Plan

| Time | Section | Duration |
|------|---------|----------|
| 0:00 | Opening — problem + what we built | 20s |
| 0:20 | Live demo: submit a job | 15s |
| 0:35 | Results: flood map on dashboard | 30s |
| 1:05 | Exposure + damage assessment | 25s |
| 1:30 | Cut-off analysis | 25s |
| 1:55 | AI model: Pre-trained ONNX deployment | 25s |
| 2:20 | Situation report (EN + NE) | 15s |
| 2:35 | Case study: EMSR927 comparison | 15s |
| 2:50 | Limitations + closing | 10s |

---

## Script

### Opening (0:00 – 0:20)

> "On August 26th 2026, a glacier collapse in northern Nepal sent a devastating flood down the Bhote Koshi and Trishuli rivers. When roads, bridges, and phone lines are gone, rescuers need to know: where is the damage, and who is cut off?
>
> HydroViz answers that — from space. Give it an area and a date, and it uses free satellite radar data to map the flood, assess damage to infrastructure, and identify which villages have lost their road connection."

*Show: title screen with project name, then the dashboard.*

### Live Demo: Submit Job (0:20 – 0:35)

> "Let me show you. I draw an area on the map, enter the flood date, and submit."

*Action: draw bbox on map, enter date, click submit. Show progress indicator streaming stages.*

> "The system is now fetching Sentinel-1 radar images — a before-image and an after-image from the same satellite orbit — so we can compare them pixel by pixel."

### Flood Map (0:35 – 1:05)

> "Here's the result. The blue areas are where the system detected flooding — water and sediment that wasn't there before the event."

*Action: toggle flood layer on. Zoom to a clear flood area. Show opacity slider.*

> "It uses radar, which sees through monsoon clouds — unlike optical satellites. The red overlay shows a debris layer — a heuristic detection of disturbed ground, clearly labelled as lower confidence."

*Action: toggle debris layer. Point to the confidence labelling.*

> "Every pixel has a confidence score. We also permanently show where we CAN'T see — radar shadow in steep gorges — so nobody mistakes a gap for safety."

*Action: show shadow/layover mask briefly.*

### Exposure + Damage (1:05 – 1:30)

> "Next: what was hit? We overlay OpenStreetMap buildings, roads, and bridges from BEFORE the event on the flood map."

*Action: toggle building layer. Show colour coding: high exposure = red, medium = orange.*

> "Orange buildings are within 10 metres of the hazard. Red ones are directly in it. Important: at 10-metre resolution, we say 'exposed', not 'destroyed' — we can't confirm individual building damage from space."

*Action: zoom to a bridge. Show status.*

> "Bridges are checked against the flood mask AND their height above the river. This one is flagged 'likely damaged'."

### Cut-off Analysis (1:30 – 1:55)

> "The critical question: who is cut off? We build the road network from pre-event OpenStreetMap, then block every road segment that's flooded and every bridge that's likely damaged."

*Action: show cut-off layer. Red dots = isolated, yellow = detour, green = reachable, grey = unknown.*

> "Red dots are settlements that were connected before the flood but are now unreachable. We run two scenarios: strict — only high-confidence flood — and conservative, including medium confidence. The difference shows uncertainty."

*Action: toggle strict/conservative. Show the sidebar list with settlement names.*

> "Grey means 'unknown' — we have no road data in OSM for these villages. Unknown does NOT mean safe."

### AI Model (1:55 – 2:20)

> "The AI component: we deployed a lightweight pre-trained U-Net segmentation model using ONNX Runtime. The model was originally trained on the Kuro Siwo dataset — over 40 flood events from Sentinel-1."

*Action: show model evaluation metrics (table or chart).*

> "Challenge: the base model is trained mostly on lowland floods. We optimized it for 8GB RAM using INT8 quantization and memory chunking, and evaluated it on Himalayan scenes it never saw during training."

*Show: Himalayan evaluation numbers, comparison with baseline.*

> "The learned model outperforms our log-ratio baseline by [X] points in IoU."

### Situation Report (2:20 – 2:35)

> "Everything feeds into a one-page situation report, generated in English and Nepali."

*Action: show sitrep. Scroll through it briefly.*

> "Every number comes from the data pipeline — none are invented. A number guard checks every figure against the source database before the report is released."

### Case Study (2:35 – 2:50)

> "We compared our results with the official Copernicus Emergency Management Service maps for this event."

*Action: show case-study tab with comparison metrics.*

> "Our flood extent agrees at [X]% IoU. Where we disagree, it's mostly in narrow gorges where radar shadow limits our view — and we document that honestly."

### Closing (2:50 – 3:00)

> "HydroViz is an educational prototype. It can't replace professional emergency response. But it shows that free satellite data, combined with AI and geographic analysis, can answer the questions that matter most — fast enough to help.
>
> Thank you."

---

## Technical Notes for Recording

- Pre-warm the cache for the case study area so the demo doesn't wait for API calls
- But show the live path briefly (with a fast-forward cut) to prove it works end-to-end
- Keep the dashboard on a dark theme for readability on projector screens
- No images of victims anywhere — use only satellite imagery and map layers
- Attribution footer must be visible in all dashboard shots
