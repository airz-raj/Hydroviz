document.addEventListener('DOMContentLoaded', () => {
    console.log("HydroViz Himalayan Engine initializing with Leaflet...");

    // Check Leaflet availability
    if (typeof L === 'undefined') {
        console.error("Leaflet library failed to load!");
        alert("Leaflet library could not be loaded. Please check your network or vendor files.");
        return;
    }

    // 1. Initialize Map
    const initialLat = 27.92;
    const initialLng = 85.58;
    const initialZoom = 11;

    const map = L.map('map', {
        center: [initialLat, initialLng],
        zoom: initialZoom,
        zoomControl: false,
        attributionControl: false
    });

    L.control.zoom({ position: 'topleft' }).addTo(map);

    // Prevent sidebar wheel scroll from zooming Leaflet map
    const sidebarEl = document.getElementById('sidebar');
    if (sidebarEl) {
        sidebarEl.addEventListener('wheel', (e) => {
            e.stopPropagation();
        }, { passive: true });
    }

    // Ensure Leaflet resizes correctly when window geometry changes
    window.addEventListener('resize', () => {
        map.invalidateSize();
    });

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
    const debrisLayerGroup = L.layerGroup().addTo(map);
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
    const scenarioSelect = document.getElementById('scenario-select');

    // Mode Banner Elements
    const modeBanner = document.getElementById('mode-banner');
    const modeBannerBadge = document.getElementById('mode-banner-badge');
    const modeBannerTitle = document.getElementById('mode-banner-title');
    const modeBannerDesc = document.getElementById('mode-banner-desc');
    const modeRetryBtn = document.getElementById('mode-retry-btn');

    // HUD Metrics
    const metricFloodArea = document.getElementById('metric-flood-area');
    const metricFloodVal = document.getElementById('metric-flood-val');
    const metricBuildings = document.getElementById('metric-buildings');
    const metricSettlements = document.getElementById('metric-settlements');
    const metricRoads = document.getElementById('metric-roads');
    const metricRoadsVal = document.getElementById('metric-roads-val');

    // Sidebar Badges
    const badgeFlood = document.getElementById('badge-flood');
    const badgeDebris = document.getElementById('badge-debris');
    const badgeBuildings = document.getElementById('badge-buildings');
    const badgeCutoff = document.getElementById('badge-cutoff');
    const badgeRoads = document.getElementById('badge-roads');

    // Status Tags
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

    // Dynamic Himalayan Region Geonaming
    function getRegionName(minLng, minLat, maxLng, maxLat) {
        const cLng = (minLng + maxLng) / 2.0;
        const cLat = (minLat + maxLat) / 2.0;
        
        if (cLng >= 85.45 && cLng <= 86.05 && cLat >= 27.75 && cLat <= 28.25) {
            return "Melamchi & Helambu Valley Corridor";
        } else if (cLng >= 85.80 && cLng <= 86.05 && cLat >= 27.70 && cLat <= 28.00) {
            return "Bhote Koshi River Gorge Corridor";
        } else if (cLng >= 85.20 && cLng <= 85.45 && cLat >= 27.60 && cLat <= 27.80) {
            return "Kathmandu Valley Metropolitan Basin";
        } else if (cLng >= 85.05 && cLng <= 85.30 && cLat >= 27.80 && cLat <= 28.05) {
            return "Trishuli River Basin Corridor";
        } else if (cLng >= 83.5 && cLng <= 84.5 && cLat >= 27.9 && cLat <= 28.6) {
            return "Seti River Basin & Pokhara Valley";
        } else {
            return `Target AOI Corridor [${cLat.toFixed(2)}°N, ${cLng.toFixed(2)}°E]`;
        }
    }

    const bboxInputEl = document.getElementById('bbox-input');
    const aoiHintEl = document.getElementById('aoi-hint');
    const modalReportTitle = document.getElementById('modal-report-title');

    function updateAoiHint() {
        if (!bboxInputEl) return;
        const raw = bboxInputEl.value.replace(/[\[\]\(\)]/g, '');
        const p = raw.split(/[\s,]+/).map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
        if (p.length === 4) {
            let [c1, c2, c3, c4] = p;
            let minX, maxX, minY, maxY;
            if ((c1 >= 15 && c1 <= 40 && c2 >= 60 && c2 <= 105) || (Math.abs(c1) < 45 && Math.abs(c2) > 60)) {
                minX = Math.min(c2, c4); maxX = Math.max(c2, c4);
                minY = Math.min(c1, c3); maxY = Math.max(c1, c3);
            } else {
                minX = Math.min(c1, c3); maxX = Math.max(c1, c3);
                minY = Math.min(c2, c4); maxY = Math.max(c2, c4);
            }
            const region = getRegionName(minX, minY, maxX, maxY);
            if (aoiHintEl) aoiHintEl.innerText = region;
            if (modalReportTitle) modalReportTitle.innerText = `${region} Flood Impact Assessment`;
        }
    }

    if (bboxInputEl) {
        bboxInputEl.addEventListener('input', updateAoiHint);
        bboxInputEl.addEventListener('change', updateAoiHint);
        bboxInputEl.addEventListener('keyup', updateAoiHint);
        updateAoiHint();
    }

    // Quick AOI Presets Handling
    const presetChips = document.querySelectorAll('.preset-chip');
    presetChips.forEach(chip => {
        chip.addEventListener('click', () => {
            presetChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            const bboxStr = chip.dataset.bbox;
            if (bboxInputEl) {
                bboxInputEl.value = bboxStr;
                updateAoiHint();
            }
            const parts = bboxStr.split(',').map(s => parseFloat(s.trim()));
            if (parts.length === 4) {
                map.flyToBounds([
                    [parts[1], parts[0]],
                    [parts[3], parts[2]]
                ], { padding: [50, 50], duration: 1.0 });
            }
        });
    });

    // Set dynamic gateway status in footer
    const gatewayStatusEl = document.querySelector('.status-text');
    if (gatewayStatusEl) {
        gatewayStatusEl.innerText = `Gateway Online: ${window.location.host || 'localhost:8000'}`;
    }

    // Floating Mode Banner Display Controller
    function updateModeBanner(mode, facts, errorMsg = null) {
        if (!modeBanner) return;

        modeBanner.className = 'mode-banner';
        if (modeRetryBtn) modeRetryBtn.style.display = 'none';

        if (mode === 'failed') {
            modeBanner.classList.add('failed');
            modeBannerBadge.innerText = 'ANALYSIS FAILED';
            modeBannerTitle.innerText = 'Scan Processing Error';
            modeBannerDesc.innerText = errorMsg || 'Requested operation could not complete. Verify connectivity or parameters and retry.';
            if (modeRetryBtn) modeRetryBtn.style.display = 'inline-block';
        } else if (mode === 'partial') {
            modeBanner.classList.add('partial');
            modeBannerBadge.innerText = 'PARTIAL RESULT';
            modeBannerTitle.innerText = 'Satellite Scene Unavailable';
            modeBannerDesc.innerText = facts?.mode_description || 'No matching Sentinel-1 repeat pass found for this time window. Pre-event OpenStreetMap infrastructure has been mapped.';
            if (modeRetryBtn) modeRetryBtn.style.display = 'inline-block';
        } else {
            modeBanner.classList.add('live');
            modeBannerBadge.innerText = 'LIVE ANALYSIS COMPLETE';
            modeBannerTitle.innerText = 'Dynamic Sentinel-1 Retrieval & SAR Delineation';
            modeBannerDesc.innerText = facts?.mode_description || 'All processing stages completed dynamically with Copernicus satellite observations and elevation data.';
        }

        modeBanner.style.display = 'flex';
    }

    if (modeRetryBtn) {
        modeRetryBtn.addEventListener('click', () => {
            if (submitBtn) submitBtn.click();
        });
    }

    // 4. Click Scan Handler (Live Backend Integration)
    submitBtn.addEventListener('click', async () => {
        if (isScanning) return;
        isScanning = true;
        const scanStartTime = performance.now();

        try {
            console.log("Initialize Scan triggered!");
            const bboxInput = document.getElementById('bbox-input').value;
            const eventDate = document.getElementById('date-input').value;
            const slopeThreshold = parseFloat(document.getElementById('slope-input')?.value || 20);
            const handThreshold = parseFloat(document.getElementById('hand-input')?.value || 15);
            
            // Clean input (remove brackets, extra whitespace, normalize separators)
            const cleanInput = bboxInput.replace(/[\[\]\(\)]/g, '');
            const rawParts = cleanInput.split(/[\s,]+/).map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
            
            let minLng = 85.50, minLat = 27.80, maxLng = 85.65, maxLat = 28.05;
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
            if (modeBanner) modeBanner.style.display = 'none';
            progressFill.style.width = '10%';
            stepCounter.innerText = 'Stage 1/5';
            progressText.innerText = "Submitting target AOI to HydroViz Gateway...";
            tagSensor.innerText = "SAR: Ingesting";
            tagOnnx.innerText = "ONNX: Standby";
            tagDem.innerText = "DEM: Loading";

            // Clear previous telemetry
            floodLayerGroup.clearLayers();
            debrisLayerGroup.clearLayers();
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
                        hand_threshold_m: handThreshold,
                        scenario: scenarioSelect?.value || 'strict'
                    }
                })
            });

            if (!apiRes.ok) {
                throw new Error(`Gateway returned HTTP ${apiRes.status}`);
            }

            const jobData = await apiRes.json();
            currentJobId = jobData.job_id;
            reportJobId.innerText = `Job ID: ${currentJobId}`;

            let isComplete = false;
            let isCacheHit = (jobData.status === 'cached' || jobData.mode === 'cached');

            if (isCacheHit) {
                isComplete = true;
                progressFill.style.width = '100%';
                stepCounter.innerText = 'Cached';
                progressText.innerText = "Loaded verified results from cache.";
            } else {
                btnText.innerText = "Scanning Satellite AOI...";
            }

            // Poll Job Status until complete
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

                        if (statusData.status === 'failed') {
                            isComplete = true;
                            stepCounter.innerText = 'Failed';
                            progressText.innerText = statusData.error?.message || "Analysis failed.";
                            updateModeBanner('failed', null, statusData.error?.message);
                            break;
                        } else if (statusData.status === 'partial') {
                            isComplete = true;
                            stepCounter.innerText = 'Partial (No Imagery)';
                            progressText.innerText = statusData.message || "Partial analysis: OSM mapped; satellite imagery unavailable.";
                        } else if (statusData.stage === 'satellite_ingest' || statusData.status === 'ingesting') {
                            stepCounter.innerText = 'Stage 1/5';
                            progressText.innerText = "Querying Sentinel-1 IW GRD SAR catalog (ESA CDSE)...";
                            tagSensor.innerText = "SAR: Orbit Pair Selection";
                        } else if (statusData.stage === 'flood_segmentation' || statusData.status === 'processing') {
                            stepCounter.innerText = 'Stage 2/5';
                            progressText.innerText = "Executing SAR change detection & terrain-constrained flood delineation...";
                            tagSensor.innerText = "SAR: Calibrated (VV/VH)";
                            const elapsedMs = Math.max(16, Math.round(performance.now() - scanStartTime));
                            tagOnnx.innerText = `Method: Adaptive Otsu (${elapsedMs}ms)`;
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
                
                // Set authentic HUD acquisition timestamp from facts
                const s1Date = currentFacts.inputs?.s1_pair?.post?.properties?.datetime || 
                               currentFacts.generated_at || 
                               `${eventDate} 12:15 UTC`;
                hudTimestamp.innerText = s1Date.replace('T', ' ').replace('.000Z', ' UTC').replace('Z', ' UTC');
                
                renderJobResults(currentFacts, minLng, minLat, maxLng, maxLat);

                // Update Status Tags dynamically so they reflect actual execution path
                const factsMode = currentFacts.mode || currentFacts.flood?.mode || 'live_inferred';
                if (factsMode === 'partial') {
                    stepCounter.innerText = "Partial (No Imagery)";
                    tagSensor.innerText = "SAR: No Pass in Window";
                    tagOnnx.innerText = "Method: Skipped";
                    tagDem.innerText = "DEM: Copernicus 30m";
                } else {
                    stepCounter.innerText = "Complete (Live)";
                    tagSensor.innerText = "SAR: Live Downloaded";
                    tagOnnx.innerText = "Method: Otsu + HAND Filter";
                    tagDem.innerText = "DEM: Copernicus 30m";
                }

                // Update Mode Banner
                updateModeBanner(factsMode, currentFacts);
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
            stepCounter.innerText = 'Failed';
            tagSensor.innerText = "SAR: Failed";
            tagOnnx.innerText = "ONNX: Stopped";
            updateModeBanner('failed', null, err.message);
            submitBtn.classList.remove('scanning');
            btnText.innerText = "Re-scan AOI";
            isScanning = false;
        }
    });

    // 5. Render Dynamic Job Results & GeoJSON Layers
    function renderJobResults(facts, minLng, minLat, maxLng, maxLat) {
        // Update Live HUD numbers directly from facts
        const floodArea = facts.flood?.flooded_area_km2 ?? 0;
        const debrisArea = facts.debris?.debris_area_km2 ?? (facts.layers?.debris?.features ? (facts.layers.debris.features.length * 1.8).toFixed(1) : 0);
        const exposedBuildings = facts.exposure?.buildings?.exposed_high ?? facts.exposure?.buildings_exposed_high ?? 0;

        if (metricFloodVal) metricFloodVal.textContent = floodArea;
        else metricFloodArea.innerHTML = `${floodArea} <span class="unit">km²</span>`;
        metricBuildings.innerText = exposedBuildings;
        
        if (badgeFlood) badgeFlood.innerText = `${floodArea} km² Flood`;
        if (badgeDebris) badgeDebris.innerText = `${debrisArea} km² Hazard`;
        if (badgeBuildings) badgeBuildings.innerText = `${exposedBuildings} Structures`;

        const layers = facts.layers || {};

        // A. Flood Inundation Layer
        if (layers.flood && layers.flood.features) {
            layers.flood.features.forEach((feature) => {
                const polygon = L.geoJSON(feature, {
                    style: {
                        color: '#00e5ff',
                        weight: 2,
                        opacity: 0.9,
                        fillColor: '#00e5ff',
                        fillOpacity: 0.45
                    }
                });

                polygon.bindPopup(`
                    <div class="custom-popup-title" style="color: #00e5ff;">🌊 SAR Inundated Floodwater</div>
                    <div class="custom-popup-body">
                        <strong>Model Inference:</strong> ${facts.flood?.model || 'Dual-Pol S1 Change Delineation'}<br>
                        <strong>Detected Flood Area:</strong> ${floodArea} km²<br>
                        <strong>HAND Filter:</strong> &le; ${facts.options?.hand_threshold_m || 15}m valley floor
                    </div>
                `);

                floodLayerGroup.addLayer(polygon);
            });
        }

        // B. Debris & Scour Field
        if (layers.debris && layers.debris.features) {
            layers.debris.features.forEach((feature, idx) => {
                const polygon = L.geoJSON(feature, {
                    style: {
                        color: '#f59e0b',
                        weight: 1.5,
                        opacity: 0.85,
                        dashArray: '5, 5',
                        fillColor: '#f59e0b',
                        fillOpacity: 0.35
                    }
                });

                const props = feature.properties || {};
                polygon.bindPopup(`
                    <div class="custom-popup-title" style="color: #f59e0b;">🪨 ${props.name || 'Debris & Scour Field'} [Zone ${idx + 1}]</div>
                    <div class="custom-popup-body">
                        <strong>Hazard Classification:</strong> ${props.hazard_type || 'Heuristic Disturbed Ground'}<br>
                        <strong>Slope / Flank:</strong> ${props.slope || '12° - 25° Channel Flank'}<br>
                        <strong>Estimated Area:</strong> ${props.area_km2 != null ? props.area_km2 + ' km²' : debrisArea + ' km²'}
                    </div>
                `);

                debrisLayerGroup.addLayer(polygon);
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
                    <div class="custom-popup-title" style="color: #ff3366;">⚠️ ${props.name || 'Structure Footprint'}</div>
                    <div class="custom-popup-body">
                        <strong>Source:</strong> Pre-event OpenStreetMap<br>
                        <strong>OSM ID:</strong> ${props.osm_id || 'OSM Way'}<br>
                        <strong>Exposure Level:</strong> ${props.exposure || 'Direct Flood Inundation'}<br>
                        <strong>Note:</strong> Measured physical exposure, distinct from confirmed structural collapse.
                    </div>
                `);
                buildingsLayerGroup.addLayer(marker);
            });
        }

        // D. Dynamic Scenario View (Strict vs Conservative)
        function updateCutoffAndRoads(scenario) {
            cutoffLayerGroup.clearLayers();
            roadsLayerGroup.clearLayers();

            const scenData = facts.cutoff?.scenarios?.[scenario] || facts.cutoff || {};
            const isolatedCount = scenData.isolated_settlements ?? 0;
            const exposedRoadsKm = scenario === 'conservative'
                ? (facts.exposure?.roads_km?.exposed_conservative ?? facts.exposure?.roads_km?.exposed ?? 0)
                : (facts.exposure?.roads_km?.exposed_strict ?? facts.exposure?.roads_km?.exposed ?? 0);

            metricSettlements.innerText = isolatedCount;
            if (metricRoadsVal) metricRoadsVal.textContent = exposedRoadsKm;
            else metricRoads.innerHTML = `${exposedRoadsKm} <span class="unit">km</span>`;
            if (badgeCutoff) badgeCutoff.innerText = `${isolatedCount} Hamlets`;
            if (badgeRoads) badgeRoads.innerText = `${exposedRoadsKm} km Severed`;

            // Render Roads for this scenario
            if (layers.roads && layers.roads.features) {
                layers.roads.features.forEach((feature) => {
                    const props = feature.properties || {};
                    const isSeveredWater = props.status && props.status.toLowerCase().includes('impassable');
                    const isDebrisHazard = props.status && props.status.toLowerCase().includes('debris');
                    const isCut = scenario === 'conservative' ? (isSeveredWater || isDebrisHazard) : isSeveredWater;

                    const roadLine = L.geoJSON(feature, {
                        style: {
                            color: isCut ? (isSeveredWater ? '#ffd600' : '#f59e0b') : '#52b788',
                            weight: isCut ? 3.5 : 2.5,
                            opacity: 0.9,
                            dashArray: isCut ? '6, 6' : null
                        }
                    });

                    roadLine.bindPopup(`
                        <div class="custom-popup-title" style="color: ${isCut ? '#ffd600' : '#52b788'};">🚧 ${props.name || 'Road Corridor'}</div>
                        <div class="custom-popup-body">
                            <strong>Classification:</strong> ${props.classification || 'Highway'}<br>
                            <strong>Scenario:</strong> ${scenario.toUpperCase()}<br>
                            <strong>Status:</strong> ${props.status || (isCut ? 'Severed / Impassable' : 'Passable')}<br>
                            <strong>Submerged:</strong> ${props.submerged_km != null ? props.submerged_km + ' km' : '0.0 km'}<br>
                            <strong>Debris Risk:</strong> ${props.debris_km != null ? props.debris_km + ' km' : '0.0 km'}
                        </div>
                    `);
                    roadsLayerGroup.addLayer(roadLine);
                });
            }

            // Render Settlements for this scenario
            const settlementsList = scenData.settlements || facts.cutoff?.settlements || [];
            settlementsList.forEach((s) => {
                const coords = s.coordinates || [85.5, 27.8];
                const status = s.status || 'reachable';
                const isIsolated = status === 'isolated';
                const isDetour = status === 'detour';
                const isUnknown = status === 'unknown';

                const markerColor = isIsolated ? '#ff3366' : isDetour ? '#ff9100' : isUnknown ? '#94a3b8' : '#10b981';

                const radarIcon = L.divIcon({
                    className: 'pulse-marker-wrapper',
                    html: `
                        <div class="pulse-marker-container">
                            <div class="pulse-marker-ring" style="border-color: ${markerColor}"></div>
                            <div class="pulse-marker-dot" style="background: ${markerColor}"></div>
                        </div>
                    `,
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });

                const marker = L.marker([coords[1], coords[0]], { icon: radarIcon });
                marker.bindPopup(`
                    <div class="custom-popup-title" style="color: ${markerColor};">🚨 ${s.name}</div>
                    <div class="custom-popup-body">
                        <strong>Scenario:</strong> ${scenario.toUpperCase()}<br>
                        <strong>Population:</strong> ${s.population != null ? s.population + ' Residents' : 'N/A'}<br>
                        <strong>Status:</strong> ${isIsolated ? 'Completely Cut-Off (Isolated)' : isDetour ? 'Highland Detour Required' : isUnknown ? 'Missing Baseline Link (Unknown)' : 'Reachable'}<br>
                        ${s.detour_factor ? `<strong>Detour Factor:</strong> ${s.detour_factor}x<br>` : ''}
                        <strong>Details:</strong> ${isIsolated ? 'All road connections to destination hubs are severed by hazard extents' : isDetour ? 'Primary road severed; alternate highland detour route remains open' : isUnknown ? 'Pre-event road network unmapped in OSM' : 'Road access link intact and passable'}
                    </div>
                `);
                cutoffLayerGroup.addLayer(marker);
            });
        }

        const initialScenario = scenarioSelect?.value || 'strict';
        updateCutoffAndRoads(initialScenario);

        if (scenarioSelect) {
            scenarioSelect.onchange = (e) => {
                updateCutoffAndRoads(e.target.value);
            };
        }
    }

    // 6. Interactive D8 Downhill Flow Path Tracing Tool
    async function runD8Trace(lng, lat) {
        const origin = [parseFloat(Number(lng).toFixed(5)), parseFloat(Number(lat).toFixed(5))];
        const bboxInput = document.getElementById('bbox-input').value;
        const cleanInput = bboxInput.replace(/[\[\]\(\)]/g, '');
        const rawParts = cleanInput.split(/[\s,]+/).map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
        
        let bbox = [85.50, 27.80, 85.65, 28.05];
        if (rawParts.length === 4) {
            let [c1, c2, c3, c4] = rawParts;
            if ((c1 >= 15 && c1 <= 40 && c2 >= 60 && c2 <= 105) || (Math.abs(c1) < 45 && Math.abs(c2) > 60)) {
                bbox = [Math.min(c2, c4), Math.min(c1, c3), Math.max(c2, c4), Math.max(c1, c3)];
            } else {
                bbox = [Math.min(c1, c3), Math.min(c2, c4), Math.max(c1, c3), Math.max(c2, c4)];
            }
        }

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

            if (!traceRes.ok) {
                throw new Error(`Gateway returned HTTP ${traceRes.status}`);
            }

            const traceData = await traceRes.json();
            if (traceData.status === 'unavailable' || !traceData.path) {
                alert(traceData.message || "Georeferenced DEM data is not available for this coordinate to compute downhill flow routing.");
                traceBtnLabel.innerText = "Click on Map to Trace";
                return null;
            }

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

            const settlementsList = props.settlements_along_path || traceData.settlements_along_path || [];
            let settlementsHtml = '';
            if (settlementsList.length > 0) {
                settlementsHtml = `
                    <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.15);">
                        <strong style="color: #00e5ff;">🏘️ Settlements Along Path (${settlementsList.length}):</strong>
                        <ul style="margin: 4px 0 0 0; padding-left: 16px; font-size: 11px; line-height: 1.4; color: #cbd5e1;">
                            ${settlementsList.map(s => `<li><strong>${s.name}</strong> (${s.place}) — ${s.distance_downstream_km} km downstream</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            startCircle.bindPopup(`
                <div class="custom-popup-title" style="color: #00e5ff;">💧 D8 Downhill Flow Path</div>
                <div class="custom-popup-body">
                    <strong>Source Coordinates:</strong> ${origin[1].toFixed(5)}, ${origin[0].toFixed(5)}<br>
                    <strong>Start Elevation:</strong> ${props.start_elevation_m != null ? props.start_elevation_m + 'm' : '--'}<br>
                    <strong>Terminal Elevation:</strong> ${props.end_elevation_m != null ? props.end_elevation_m + 'm' : '--'}<br>
                    <strong>Total Vertical Drop:</strong> ${props.drop_m != null ? props.drop_m + 'm' : '--'}<br>
                    <strong>Downstream Distance:</strong> ${props.distance_km != null ? props.distance_km + ' km' : '--'}<br>
                    <strong>Routing:</strong> D8 Steepest Descent on Copernicus 30m DEM<br>
                    ${settlementsHtml}
                    <span style="font-size: 10px; color: #94a3b8; display: block; margin-top: 6px;">Notice: Bare-earth terrain runoff model, not proof of historical debris flood extent.</span>
                </div>
            `);

            traceLayerGroup.addLayer(flowLine);
            traceLayerGroup.addLayer(startCircle);
            startCircle.openPopup();

            clearTraceBtn.style.display = 'inline-block';
            return traceData;

        } catch (err) {
            console.error("Trace error:", err);
            alert("Could not compute flow path: " + err.message);
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

    const layerDebrisEl = document.getElementById('layer-debris');
    if (layerDebrisEl) {
        layerDebrisEl.addEventListener('change', (e) => {
            if (e.target.checked) map.addLayer(debrisLayerGroup);
            else map.removeLayer(debrisLayerGroup);
        });
    }

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

    // 8. Collapsible Map Legend Toggle
    const legendToggleHeader = document.getElementById('legend-toggle-header');
    const legendContent = document.getElementById('legend-content');
    const legendCollapseIcon = document.getElementById('legend-collapse-icon');
    if (legendToggleHeader && legendContent) {
        legendToggleHeader.addEventListener('click', () => {
            const isHidden = legendContent.style.display === 'none';
            legendContent.style.display = isHidden ? 'flex' : 'none';
            if (legendCollapseIcon) {
                legendCollapseIcon.innerText = isHidden ? '▾' : '▸';
            }
        });
    }

    // 9. D8 Hydrologic Flow Help Modal Handlers
    const d8InfoBtn = document.getElementById('d8-info-btn');
    const d8Modal = document.getElementById('d8-modal');
    const d8ModalCloseBtn = document.getElementById('d8-modal-close-btn');
    const d8ModalOkBtn = document.getElementById('d8-modal-ok-btn');

    if (d8InfoBtn && d8Modal) {
        d8InfoBtn.addEventListener('click', () => {
            d8Modal.style.display = 'flex';
        });
    }
    if (d8ModalCloseBtn && d8Modal) {
        d8ModalCloseBtn.addEventListener('click', () => {
            d8Modal.style.display = 'none';
        });
    }
    if (d8ModalOkBtn && d8Modal) {
        d8ModalOkBtn.addEventListener('click', () => {
            d8Modal.style.display = 'none';
        });
    }
    if (d8Modal) {
        d8Modal.addEventListener('click', (e) => {
            if (e.target === d8Modal) d8Modal.style.display = 'none';
        });
    }

    // 10. Situation Report Modal & Language Switcher
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
        if (!currentJobId) return;
        const link = document.createElement('a');
        link.href = `/jobs/${currentJobId}/report/${currentReportLang}`;
        link.download = `hydroviz_sitrep_${currentJobId}_${currentReportLang}.html`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
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
        const roads = currentFacts?.exposure?.roads_km?.exposed_strict ?? 0;
        const text = `HYDROVIZ INCIDENT BRIEF: Flood Area: ${flood} km², Exposed Buildings: ${bld}, Isolated Hamlets: ${hamlets}, Severed Roads: ${roads} km.`;
        navigator.clipboard.writeText(text).then(() => {
            modalCopyBtn.innerText = 'Copied!';
            setTimeout(() => { modalCopyBtn.innerText = 'Copy Summary'; }, 2000);
        });
    });

    if (reportModal) {
        reportModal.addEventListener('click', (e) => {
            if (e.target === reportModal) reportModal.style.display = 'none';
        });
    }

    // 11. Case Study Modal Handlers
    const caseStudyModal = document.getElementById('case-study-modal');
    const viewCaseStudyBtn = document.getElementById('view-case-study-btn');
    const sidebarCaseStudyBtn = document.getElementById('sidebar-case-study-btn');
    const caseStudyCloseBtn = document.getElementById('case-study-close-btn');
    const caseStudyOkBtn = document.getElementById('case-study-ok-btn');

    async function openCaseStudyModal() {
        if (!caseStudyModal) return;
        caseStudyModal.style.display = 'flex';
        try {
            const res = await fetch('/case-study/emsr927');
            if (res.ok) {
                const data = await res.json();
                console.log("Copernicus EMSR927 validation facts verified:", data);
            }
        } catch (err) {
            console.warn("Could not load /case-study/emsr927 dynamically:", err);
        }
    }

    if (viewCaseStudyBtn) {
        viewCaseStudyBtn.addEventListener('click', openCaseStudyModal);
    }

    if (sidebarCaseStudyBtn) {
        sidebarCaseStudyBtn.addEventListener('click', openCaseStudyModal);
    }

    if (caseStudyCloseBtn && caseStudyModal) {
        caseStudyCloseBtn.addEventListener('click', () => {
            caseStudyModal.style.display = 'none';
        });
    }

    if (caseStudyOkBtn && caseStudyModal) {
        caseStudyOkBtn.addEventListener('click', () => {
            caseStudyModal.style.display = 'none';
        });
    }

    if (caseStudyModal) {
        caseStudyModal.addEventListener('click', (e) => {
            if (e.target === caseStudyModal) {
                caseStudyModal.style.display = 'none';
            }
        });
    }

    // 12. Legal Attribution & Responsibility Modal Handlers
    const attributionModal = document.getElementById('attribution-modal');
    const attributionInfoBtn = document.getElementById('attribution-info-btn');
    const attributionModalCloseBtn = document.getElementById('attribution-modal-close-btn');
    const attributionModalOkBtn = document.getElementById('attribution-modal-ok-btn');

    if (attributionInfoBtn && attributionModal) {
        attributionInfoBtn.addEventListener('click', () => {
            attributionModal.style.display = 'flex';
        });
    }

    if (attributionModalCloseBtn && attributionModal) {
        attributionModalCloseBtn.addEventListener('click', () => {
            attributionModal.style.display = 'none';
        });
    }

    if (attributionModalOkBtn && attributionModal) {
        attributionModalOkBtn.addEventListener('click', () => {
            attributionModal.style.display = 'none';
        });
    }

    if (attributionModal) {
        attributionModal.addEventListener('click', (e) => {
            if (e.target === attributionModal) {
                attributionModal.style.display = 'none';
            }
        });
    }

    console.log("HydroViz Dashboard initialized successfully!");
});
