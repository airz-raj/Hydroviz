# HydroViz Demo Script

> **A note on responsibility:**
> This disaster is recent, and many families are still affected. Treat the topic with respect: do not use images of victims in demos or reports. Systems built here are educational prototypes, not operational tools.

## Setup (0:00 - 0:30)
- **Narrator**: "Welcome to the HydroViz demonstration. Before we begin, an important note on humanitarian responsibility: this disaster is recent, and many families are still affected. We treat this topic with the utmost respect — HydroViz strictly contains no imagery of victims, and this system is an educational prototype, not an operational tool. Today we will show how our system rapidly maps flood extent and identifies isolated settlements using Sentinel-1 SAR imagery."
- **Action**: Open the interactive dashboard.
- **Action**: Draw a bounding box over the Bhote Koshi corridor in Nepal.
- **Action**: Select the event date: August 26, 2026.
- **Action**: Click "Run Analysis".

## Processing (0:30 - 1:30)
- **Narrator**: "The system automatically queries the STAC catalog for pre- and post-event Sentinel-1 imagery, processes it into a tensor, and runs it through our 8GB RAM-optimized KuroSiwo SNUNet-CD ONNX model."
- **Action**: Show the progress bar streaming SSE updates. 
- **Narrator**: "Notice how we process in 512x512 chunks to stay strictly within container memory limits."

## Results (1:30 - 2:30)
- **Action**: The map loads the output layers.
- **Narrator**: "The flood mask is now generated. We can toggle between confirmed floodwater and the heuristic debris scour field."
- **Action**: Toggle the `Isolated Hamlets` layer and inspect Strict vs Conservative cutoff scenarios.
- **Narrator**: "Our Rust-based `geo_core` has overlaid this mask with OpenStreetMap data, running a multi-source Dijkstra routing algorithm to identify settlements that are now isolated from hospitals and major towns."

## Reporting & Attributions (2:30 - 3:00)
- **Action**: Click "Inspect Situation Report" and open the "Legal & Responsibility" modal.
- **Narrator**: "HydroViz compiles incident briefings in English and Nepali. Our Devanagari Number Guard ensures that paraphrasing never hallucinates exposure metrics. In accordance with submission guidelines, all mandatory attributions are clearly stated: 'Contains modified Copernicus Sentinel data 2026.', 'Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.', and '© OpenStreetMap contributors.'"
- **Action**: Show the generated bilingual report.
- **Narrator**: "Thank you. HydroViz is an open-source educational prototype built for rapid disaster response."
