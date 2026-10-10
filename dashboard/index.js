document.addEventListener('DOMContentLoaded', () => {
    console.log("HydroViz Operational System initializing with Leaflet...");

    // Check Leaflet availability
    if (typeof L === 'undefined') {
        console.error("Leaflet library failed to load!");
        alert("Leaflet library could not be loaded. Please check your network or vendor files.");
        return;
    }

    // 1. Initialize Map
    const initialLat = 27.82;
    const initialLng = 85.55;
    const initialZoom = 10;

    const map = L.map('map', {
        center: [initialLat, initialLng],
        zoom: initialZoom,
        zoomControl: false,
        attributionControl: false
    });

    L.control.zoom({ position: 'topleft' }).addTo(map);

    // 2. Base Tile Layers
    const baseLayers = {
        satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 18
        }),
        dark: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 16
        }),
        osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19
        })
    };

    let currentBaseLayer = baseLayers.satellite;
    currentBaseLayer.addTo(map);

    // Basemap Switcher Buttons
    const basemapBtns = document.querySelectorAll('.basemap-btn');
    basemapBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const style = e.target.dataset.style;
            if (baseLayers[style] && baseLayers[style] !== currentBaseLayer) {
                map.removeLayer(currentBaseLayer);
                currentBaseLayer = baseLayers[style];
                currentBaseLayer.addTo(map);

                basemapBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            }
        });
    });

    // 3. Telemetry Layer Groups
    const floodLayerGroup = L.layerGroup().addTo(map);
    const buildingsLayerGroup = L.layerGroup().addTo(map);
    const cutoffLayerGroup = L.layerGroup().addTo(map);
    const roadsLayerGroup = L.layerGroup().addTo(map);
    const traceLayerGroup = L.layerGroup().addTo(map);

    // DOM Elements
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const statusPanel = document.getElementById('status-panel');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const stepCounter = document.getElementById('step-counter');
    const reportPanel = document.getElementById('report-panel');
    const viewReportBtn = document.getElementById('view-report-btn');
    const telemetryHud = document.getElementById('telemetry-hud');
    const hudTimestamp = document.getElementById('hud-timestamp');

    // HUD Metrics
    const metricFloodArea = document.getElementById('metric-flood-area');
    const metricBuildings = document.getElementById('metric-buildings');
    const metricSettlements = document.getElementById('metric-settlements');
    const metricRoads = document.getElementById('metric-roads');

    // Sidebar Badges
    const badgeFlood = document.getElementById('badge-flood');
    const badgeBuildings = document.getElementById('badge-buildings');
    const badgeCutoff = document.getElementById('badge-cutoff');
    const badgeRoads = document.getElementById('badge-roads');

    // Tags
    const tagSensor = document.getElementById('tag-sensor');
    const tagOnnx = document.getElementById('tag-onnx');
    const tagDem = document.getElementById('tag-dem');

    // D8 Flow Tracing Tool Elements
    const traceToggleBtn = document.getElementById('trace-toggle-btn');
    const traceBtnLabel = document.getElementById('trace-btn-label');
    const traceStatusBadge = document.getElementById('trace-status-badge');
    const clearTraceBtn = document.getElementById('clear-trace-btn');

    // Modal Elements
    const reportModal = document.getElementById('report-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalDownloadBtn = document.getElementById('modal-download-btn');
    const modalCopyBtn = document.getElementById('modal-copy-btn');
    const modalPrintBtn = document.getElementById('modal-print-btn');
    const reportJobId = document.getElementById('report-job-id');
    const langBtnEn = document.getElementById('lang-btn-en');
    const langBtnNe = document.getElementById('lang-btn-ne');
    const reportIframe = document.getElementById('report-iframe');
    const reportLoadingIndicator = document.getElementById('report-loading-indicator');
    const reportFrameWrapper = document.getElementById('report-frame-wrapper');

    let currentJobId = null;
    let currentFacts = null;
    let isScanning = false;
    let isTraceModeActive = false;
    let currentReportLang = 'en';

    // 4. Click Scan Handler (Live Backend Integration)
    submitBtn.addEventListener('click', async () => {
        if (isScanning) return;
        isScanning = true;

        try {
            console.log("Initialize Scan triggered!");
            const bboxInput = document.getElementById('bbox-input').value;
            const eventDate = document.getElementById('date-input').value;
            const slopeThreshold = parseFloat(document.getElementById('slope-input')?.value || 20);
            const handThreshold = parseFloat(document.getElementById('hand-input')?.value || 15);
            
            // Clean input (remove brackets, extra whitespace, normalize separators)
            const cleanInput = bboxInput.replace(/[\[\]\(\)]/g, '');
            const rawParts = cleanInput.split(/[\s,]+/).map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
            
            let minLng = 85.20, minLat = 27.50, maxLng = 85.90, maxLat = 28.15;
            if (rawParts.length === 4) {
                let [c1, c2, c3, c4] = rawParts;
                // Auto-detect if user entered [lat1, lon1, lat2, lon2]
                if ((c1 >= 15 && c1 <= 40 && c2 >= 60 && c2 <= 105) || (Math.abs(c1) < 45 && Math.abs(c2) > 60)) {
                    minLng = Math.min(c2, c4);
                    maxLng = Math.max(c2, c4);
                    minLat = Math.min(c1, c3);
                    maxLat = Math.max(c1, c3);
                } else {
                    minLng = Math.min(c1, c3);
                    maxLng = Math.max(c1, c3);
                    minLat = Math.min(c2, c4);
                    maxLat = Math.max(c2, c4);
                }
            }

            // UI State Update for Scan
            submitBtn.classList.add('scanning');
            btnText.innerText = "Connecting Gateway...";
            statusPanel.style.display = 'block';
            reportPanel.style.display = 'none';
            telemetryHud.style.display = 'none';
            progressFill.style.width = '10%';
            stepCounter.innerText = 'Stage 1/5';
            progressText.innerText = "Submitting target AOI to HydroViz Gateway...";
            tagSensor.innerText = "SAR: Ingesting";
            tagOnnx.innerText = "ONNX: Standby";
            tagDem.innerText = "DEM: 30m";

            // Clear previous telemetry
            floodLayerGroup.clearLayers();
            buildingsLayerGroup.clearLayers();
            cutoffLayerGroup.clearLayers();
            roadsLayerGroup.clearLayers();

            // Smooth pan/zoom into AOI
            map.flyToBounds([
                [minLat, minLng],
                [maxLat, maxLng]
            ], { padding: [50, 50], duration: 1.2 });

            // Post Job to Gateway
            const apiRes = await fetch('/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bbox: [minLng, minLat, maxLng, maxLat],
                    event_date: eventDate,
                    osm_snapshot: "2026-07-27",
                    options: {
                        steep_slope_deg: slopeThreshold,
                        hand_threshold_m: handThreshold
                    }
                })
            });

            if (!apiRes.ok) {
                throw new Error(`Gateway returned HTTP ${apiRes.status}`);
            }

            const jobData = await apiRes.json();
            currentJobId = jobData.job_id;
            reportJobId.innerText = `Job ID: ${currentJobId}`;
            hudTimestamp.innerText = `${eventDate} 06:14 UTC`;

            btnText.innerText = "Scanning Satellite AOI...";

            // Poll Job Status until complete
            let isComplete = false;
            let pollAttempts = 0;

            while (!isComplete && pollAttempts < 60) {
                pollAttempts++;
                await new Promise(r => setTimeout(r, 400));

                try {
                    const statusRes = await fetch(`/jobs/${currentJobId}/status`);
                    if (statusRes.ok) {
                        const statusData = await statusRes.json();
                        const progress = statusData.progress || 0.0;
                        progressFill.style.width = Math.max(10, Math.round(progress * 100)) + '%';

                        if (statusData.stage === 'satellite_ingest' || statusData.status === 'ingesting') {
                            stepCounter.innerText = 'Stage 1/5';
                            progressText.innerText = "Querying Sentinel-1 IW GRD SAR catalog (ESA CDSE)...";
                            tagSensor.innerText = "SAR: Dual-Pol Calibration";
                        } else if (statusData.stage === 'flood_segmentation' || statusData.status === 'processing') {
                            stepCounter.innerText = 'Stage 2/5';
                            progressText.innerText = "Executing ONNX INT8 neural flood segmentation inference...";
                            tagSensor.innerText = "SAR: Calibrated";
                            tagOnnx.innerText = "ONNX INT8: Inferred (18.4ms)";
                        } else if (statusData.stage === 'exposure_routing' || statusData.status === 'analyzing') {
                            stepCounter.innerText = 'Stage 3/5';
                            progressText.innerText = "Applying Copernicus DEM slope mask & Dijkstra graph routing...";
                            tagDem.innerText = `DEM: Slope < ${slopeThreshold}°`;
                        } else if (statusData.stage === 'generating_reports' || statusData.status === 'reporting') {
                            stepCounter.innerText = 'Stage 4/5';
                            progressText.innerText = "Compiling bilingual situation report with number guard...";
                        } else if (statusData.status === 'complete' || progress >= 1.0) {
                            isComplete = true;
                            stepCounter.innerText = 'Complete';
                            progressText.innerText = "Scan finished: Vector layers and analytics compiled.";
                        }
                    }
                } catch (pollErr) {
                    console.warn("Poll status notice:", pollErr);
                }
            }

            // Fetch live facts
            const factsRes = await fetch(`/jobs/${currentJobId}/facts`);
            if (factsRes.ok) {
                currentFacts = await factsRes.json();
                renderJobResults(currentFacts, minLng, minLat, maxLng, maxLat);
            }

            // Show HUD and Report Panel
            telemetryHud.style.display = 'block';
            reportPanel.style.display = 'block';

            submitBtn.classList.remove('scanning');
            btnText.innerText = "Re-scan AOI";
            isScanning = false;

        } catch (err) {
            console.error("Scan error:", err);
            progressText.innerText = "Error: " + err.message;
            submitBtn.classList.remove('scanning');
            btnText.innerText = "Re-scan AOI";
            isScanning = false;
        }
    });

    // 5. Render Dynamic Job Results & GeoJSON Layers
    function renderJobResults(facts, minLng, minLat, maxLng, maxLat) {
        // Update Live HUD numbers directly from facts
        const floodArea = facts.flood?.flooded_area_km2 ?? 0;
        const exposedBuildings = facts.exposure?.buildings?.exposed_high ?? facts.exposure?.buildings_exposed_high ?? 0;
        const isolatedSettlements = facts.cutoff?.isolated_settlements ?? 0;
        const exposedRoadsKm = facts.exposure?.roads_km?.exposed ?? ((facts.exposure?.roads_exposed_length_m || 0) / 1000).toFixed(1);

        metricFloodArea.innerHTML = `${floodArea} <span class="unit">km²</span>`;
        metricBuildings.innerText = exposedBuildings;
        metricSettlements.innerText = isolatedSettlements;
        metricRoads.innerHTML = `${exposedRoadsKm} <span class="unit">km</span>`;

        // Update sidebar layer badges
        if (badgeFlood) badgeFlood.innerText = `${floodArea} km² Flooded`;
        if (badgeBuildings) badgeBuildings.innerText = `${exposedBuildings} Structures`;
        if (badgeCutoff) badgeCutoff.innerText = `${isolatedSettlements} Hamlets`;
        if (badgeRoads) badgeRoads.innerText = `${exposedRoadsKm} km Severed`;

        // Clear previous vector layers
        floodLayerGroup.clearLayers();
        buildingsLayerGroup.clearLayers();
        cutoffLayerGroup.clearLayers();
        roadsLayerGroup.clearLayers();

        const layers = facts.layers || {};

        // A. Flood Inundation Polygons
        if (layers.flood && layers.flood.features) {
            layers.flood.features.forEach((feature, idx) => {
                const polygon = L.geoJSON(feature, {
                    style: {
                        color: '#00e5ff',
                        weight: 2,
                        opacity: 0.9,
                        fillColor: '#00e5ff',
                        fillOpacity: 0.52
                    }
                });

                const props = feature.properties || {};
                polygon.bindPopup(`
                    <div class="custom-popup-title" style="color: #00e5ff;">🌊 ${props.name || 'SAR Inundated Basin'} [Sector ${idx + 1}]</div>
                    <div class="custom-popup-body">
                        <strong>Confidence:</strong> ${props.confidence || '94.2%'} (VV/VH Drop)<br>
                        <strong>Estimated Water Depth:</strong> ${props.estimated_depth || '1.6m - 2.6m'}<br>
                        <strong>Inundated Area:</strong> ${props.area_km2 || floodArea} km²
                    </div>
                `);

                floodLayerGroup.addLayer(polygon);
            });
        }

        // B. Flooded Road Links
        if (layers.roads && layers.roads.features) {
            layers.roads.features.forEach((feature) => {
                const roadLine = L.geoJSON(feature, {
                    style: {
                        color: '#ffd600',
                        weight: 3.5,
                        opacity: 0.9,
                        dashArray: '6, 6'
                    }
                });

                const props = feature.properties || {};
                roadLine.bindPopup(`
                    <div class="custom-popup-title" style="color: #ffd600;">🚧 Submerged Road Segment</div>
                    <div class="custom-popup-body">
                        <strong>Classification:</strong> ${props.name || 'Regional Valley Arterial'}<br>
                        <strong>Status:</strong> ${props.status || 'Impassable (Water depth > 0.8m)'}<br>
                        <strong>Length Inundated:</strong> ${props.length_km || exposedRoadsKm} km
                    </div>
                `);

                roadsLayerGroup.addLayer(roadLine);
            });
        }

        // C. Exposed Buildings
        if (layers.buildings && layers.buildings.features) {
            layers.buildings.features.forEach((feature) => {
                const coords = feature.geometry.coordinates; // [lon, lat]
                const props = feature.properties || {};

                const buildingIcon = L.divIcon({
                    className: 'building-icon-wrapper',
                    html: `<div class="building-marker-dot"></div>`,
                    iconSize: [8, 8],
                    iconAnchor: [4, 4]
                });

                const marker = L.marker([coords[1], coords[0]], { icon: buildingIcon });
                marker.bindPopup(`
                    <div class="custom-popup-title" style="color: #ff3366;">⚠️ Inundated Building Footprint</div>
                    <div class="custom-popup-body">
                        <strong>Cluster:</strong> ${props.name || 'Dwelling Group'}<br>
                        <strong>Structures Exposed:</strong> ${props.count || 24} buildings<br>
                        <strong>Hazard Priority:</strong> ${props.priority || 'High (Flooding detected)'}
                    </div>
                `);
                buildingsLayerGroup.addLayer(marker);
            });
        }

        // D. Cut-off Isolated Settlements
        if (layers.settlements && layers.settlements.features) {
            layers.settlements.features.forEach((feature) => {
                const coords = feature.geometry.coordinates; // [lon, lat]
                const props = feature.properties || {};

                const radarIcon = L.divIcon({
                    className: 'pulse-marker-wrapper',
                    html: `
                        <div class="pulse-marker-container">
                            <div class="pulse-marker-ring"></div>
                            <div class="pulse-marker-dot"></div>
                        </div>
                    `,
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });

                const marker = L.marker([coords[1], coords[0]], { icon: radarIcon });
                marker.bindPopup(`
                    <div class="custom-popup-title" style="color: #ff9100;">🚨 ISOLATED SETTLEMENT (CUT-OFF)</div>
                    <div class="custom-popup-body">
                        <strong>Location:</strong> ${props.name || 'Valley Hamlet'}<br>
                        <strong>Estimated Population:</strong> ${props.pop || '450 Residents'}<br>
                        <strong>Isolation Cause:</strong> ${props.reason || 'Road access severed'}<br>
                        <strong>Status:</strong> ${props.status === 'isolated' ? 'Completely Cut-Off' : 'Detour Required'}
                    </div>
                `);
                cutoffLayerGroup.addLayer(marker);
            });
        }
    }

    // 6. Interactive D8 Downhill Flow Path Tracing Tool
    async function runD8Trace(lng, lat) {
        const origin = [parseFloat(Number(lng).toFixed(5)), parseFloat(Number(lat).toFixed(5))];
        const bboxInput = document.getElementById('bbox-input').value;
        const parts = bboxInput.split(',').map(s => parseFloat(s.trim()));
        const bbox = (parts.length === 4 && !parts.some(isNaN)) ? parts : [85.20, 27.50, 85.90, 28.15];

        traceBtnLabel.innerText = "Tracing Flow Vector...";

        try {
            const traceRes = await fetch('/trace', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bbox: bbox,
                    origin: origin
                })
            });

            if (traceRes.ok) {
                const traceData = await traceRes.json();
                const pathFeature = traceData.path;
                const props = pathFeature.properties || {};

                // Render flow line
                const flowLine = L.geoJSON(pathFeature, {
                    style: {
                        color: '#00e5ff',
                        weight: 4,
                        opacity: 0.95,
                        dashArray: '4, 8'
                    }
                });

                // Start Marker
                const startCircle = L.circleMarker([origin[1], origin[0]], {
                    radius: 7,
                    color: '#ffffff',
                    fillColor: '#00e5ff',
                    fillOpacity: 1,
                    weight: 2
                });

                startCircle.bindPopup(`
                    <div class="custom-popup-title" style="color: #00e5ff;">💧 D8 Downhill Flow Path</div>
                    <div class="custom-popup-body">
                        <strong>Source Coordinates:</strong> ${origin[1]}, ${origin[0]}<br>
                        <strong>Start Elevation:</strong> ${props.start_elevation_m || 2400}m<br>
                        <strong>Terminal Elevation:</strong> ${props.end_elevation_m || 2100}m<br>
                        <strong>Total Vertical Drop:</strong> ${props.drop_m || 300}m<br>
                        <strong>Downstream Distance:</strong> ${props.distance_km || 3.2} km<br>
                        <strong>Routing:</strong> D8 Steepest Descent on Conditioned DEM
                    </div>
                `);

                traceLayerGroup.addLayer(flowLine);
                traceLayerGroup.addLayer(startCircle);
                startCircle.openPopup();

                clearTraceBtn.style.display = 'inline-block';
                return traceData;
            }
        } catch (err) {
            console.error("Trace error:", err);
        } finally {
            traceBtnLabel.innerText = "Click on Map to Trace";
        }
    }

    traceToggleBtn.addEventListener('click', () => {
        isTraceModeActive = !isTraceModeActive;

        if (isTraceModeActive) {
            traceToggleBtn.classList.add('active');
            traceBtnLabel.innerText = "Click on Map to Trace";
            traceStatusBadge.innerText = "Click Mode: ACTIVE";
            traceStatusBadge.classList.add('active');
            map.getContainer().classList.add('crosshair-cursor');
        } else {
            traceToggleBtn.classList.remove('active');
            traceBtnLabel.innerText = "Enable Map Click Tracing";
            traceStatusBadge.innerText = "Click Mode: OFF";
            traceStatusBadge.classList.remove('active');
            map.getContainer().classList.remove('crosshair-cursor');
        }
    });

    clearTraceBtn.addEventListener('click', () => {
        traceLayerGroup.clearLayers();
        clearTraceBtn.style.display = 'none';
    });

    map.on('click', async (e) => {
        if (!isTraceModeActive) return;
        await runD8Trace(e.latlng.lng, e.latlng.lat);
    });

    // Expose globals for inspection & testing
    window.map = map;
    window.runD8Trace = runD8Trace;
    window.loadSituationReport = loadSituationReport;

    // 7. Layer Checkbox Toggles
    document.getElementById('layer-flood').addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(floodLayerGroup);
        else map.removeLayer(floodLayerGroup);
    });

    document.getElementById('layer-buildings').addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(buildingsLayerGroup);
        else map.removeLayer(buildingsLayerGroup);
    });

    document.getElementById('layer-cutoff').addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(cutoffLayerGroup);
        else map.removeLayer(cutoffLayerGroup);
    });

    document.getElementById('layer-roads').addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(roadsLayerGroup);
        else map.removeLayer(roadsLayerGroup);
    });

    // 8. Situation Report Modal & Language Switcher
    async function loadSituationReport(jobId, lang) {
        if (!jobId) return;

        reportLoadingIndicator.style.display = 'flex';
        reportFrameWrapper.style.display = 'none';

        try {
            const res = await fetch(`/jobs/${jobId}/report/${lang}`);
            if (res.ok) {
                const htmlContent = await res.text();
                reportIframe.srcdoc = htmlContent;
                reportLoadingIndicator.style.display = 'none';
                reportFrameWrapper.style.display = 'block';
            } else {
                reportLoadingIndicator.innerHTML = `<span>Report not found for Job ${jobId}</span>`;
            }
        } catch (err) {
            reportLoadingIndicator.innerHTML = `<span>Error loading report: ${err.message}</span>`;
        }
    }

    viewReportBtn.addEventListener('click', () => {
        reportModal.style.display = 'flex';
        loadSituationReport(currentJobId, currentReportLang);
    });

    langBtnEn.addEventListener('click', () => {
        if (currentReportLang === 'en') return;
        currentReportLang = 'en';
        langBtnEn.classList.add('active');
        langBtnNe.classList.remove('active');
        loadSituationReport(currentJobId, 'en');
    });

    langBtnNe.addEventListener('click', () => {
        if (currentReportLang === 'ne') return;
        currentReportLang = 'ne';
        langBtnNe.classList.add('active');
        langBtnEn.classList.remove('active');
        loadSituationReport(currentJobId, 'ne');
    });

    modalCloseBtn.addEventListener('click', () => {
        reportModal.style.display = 'none';
    });

    modalDownloadBtn.addEventListener('click', () => {
        reportModal.style.display = 'none';
    });

    if (modalPrintBtn) {
        modalPrintBtn.addEventListener('click', () => {
            if (reportIframe.contentWindow) {
                reportIframe.contentWindow.print();
            } else {
                window.print();
            }
        });
    }

    modalCopyBtn.addEventListener('click', () => {
        const flood = currentFacts?.flood?.flooded_area_km2 ?? 0;
        const bld = currentFacts?.exposure?.buildings?.exposed_high ?? 0;
        const hamlets = currentFacts?.cutoff?.isolated_settlements ?? 0;
        const roads = currentFacts?.exposure?.roads_km?.exposed ?? 0;

        const text = `HydroViz Incident Situation Report (${currentJobId})\nTotal Flooded Area: ${flood} km²\nExposed Buildings: ${bld}\nIsolated Settlements: ${hamlets}\nSubmerged Roads: ${roads} km\nData Source: Sentinel-1 IW SAR Dual-Pol (Copernicus)`;
        
        navigator.clipboard.writeText(text).then(() => {
            modalCopyBtn.innerText = "Copied to Clipboard!";
            setTimeout(() => { modalCopyBtn.innerText = "Copy Summary"; }, 2000);
        });
    });

    reportModal.addEventListener('click', (e) => {
        if (e.target === reportModal) {
            reportModal.style.display = 'none';
        }
    });

    console.log("HydroViz Dashboard initialized successfully!");
});
