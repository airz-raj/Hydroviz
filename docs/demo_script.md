# HydroViz Demo Script

## Setup (0:00 - 0:30)
- **Narrator**: "Welcome to the HydroViz demonstration. Today we will show how our system rapidly maps flood extent and identifies isolated settlements using Sentinel-1 SAR imagery."
- **Action**: Open the MapLibre dashboard.
- **Action**: Draw a bounding box over the Bhote Koshi corridor in Nepal.
- **Action**: Select the event date: August 26, 2026.
- **Action**: Click "Run Analysis".

## Processing (0:30 - 1:30)
- **Narrator**: "The system automatically queries the STAC catalog for pre- and post-event Sentinel-1 imagery, processes it into a 9-channel tensor, and runs it through our 8GB RAM-optimized KuroSiwo SNUNet-CD model."
- **Action**: Show the progress bar streaming SSE updates. 
- **Narrator**: "Notice how we process in 512x512 chunks to stay strictly within container memory limits."

## Results (1:30 - 2:30)
- **Action**: The map loads the output layers.
- **Narrator**: "The flood mask is now generated. We can toggle the baseline vs learned mask."
- **Action**: Toggle the `Cut-off Settlements` layer.
- **Narrator**: "Our Rust-based `geo_core` has overlaid this mask with OpenStreetMap data, running a multi-source Dijkstra routing algorithm to identify settlements that are now isolated from hospitals and major towns."

## Reporting (2:30 - 3:00)
- **Action**: Click "View Report".
- **Narrator**: "Finally, HydroViz generates a situation report in both English and Nepali. Our Number Guard system ensures that the LLM paraphrasing never hallucinates exposure metrics."
- **Action**: Show the generated PDF report.
- **Narrator**: "Thank you. HydroViz is an open-source educational prototype built for rapid disaster response."
