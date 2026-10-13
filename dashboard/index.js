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
            maxZoom: 18,
            attribution: 'Esri, Maxar, Earthstar Geographics'
        }),
        dark: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 16,
            attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors'
        }),
        osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors'
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
        } else if (cLng >= 84.70 && cLng <= 85.05 && cLat >= 28.20 && cLat <= 28.65) {
            return "Budhi Gandaki & Manaslu Valley Corridor";
        } else if (cLng >= 84.20 && cLng <= 84.70 && cLat >= 28.00 && cLat <= 28.70) {
            return "Marsyangdi River Basin & Lamjung Corridor";
        } else if (cLng >= 83.5 && cLng <= 84.5 && cLat >= 27.9 && cLat <= 28.6) {
            return "Seti River Basin & Pokhara Valley";
        } else {
            return `Target AOI Corridor [${cLat.toFixed(2)}°N, ${cLng.toFixed(2)}°E]`;
        }
    }

    const bboxInputEl = document.getElementById('bbox-input');
    const aoiHintEl = document.getElementById('aoi-hint');
    const modalReportTitle = document.getElementById('modal-report-title');

    const presetChips = document.querySelectorAll('.preset-chip');

    function syncPresetChips(currentBboxStr) {
        if (!currentBboxStr) {
            presetChips.forEach(c => c.classList.remove('active'));
            return;
        }
        const raw = currentBboxStr.replace(/[\[\]\(\)]/g, '');
        const p = raw.split(/[\s,]+/).map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
        if (p.length !== 4) {
            presetChips.forEach(c => c.classList.remove('active'));
            return;
        }
        let [c1, c2, c3, c4] = p;
        let minX, maxX, minY, maxY;
        if ((c1 >= 15 && c1 <= 40 && c2 >= 60 && c2 <= 105) || (Math.abs(c1) < 45 && Math.abs(c2) > 60)) {
            minX = Math.min(c2, c4); maxX = Math.max(c2, c4);
            minY = Math.min(c1, c3); maxY = Math.max(c1, c3);
        } else {
            minX = Math.min(c1, c3); maxX = Math.max(c1, c3);
            minY = Math.min(c2, c4); maxY = Math.max(c2, c4);
        }

        let matched = false;
        presetChips.forEach(chip => {
            const cp = chip.dataset.bbox.split(/[\s,]+/).map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
            if (cp.length === 4) {
                const isClose = Math.abs(minX - cp[0]) <= 0.05 &&
                                Math.abs(minY - cp[1]) <= 0.05 &&
                                Math.abs(maxX - cp[2]) <= 0.05 &&
                                Math.abs(maxY - cp[3]) <= 0.05;
                if (isClose) {
                    chip.classList.add('active');
                    matched = true;
                } else {
                    chip.classList.remove('active');
                }
            } else {
                chip.classList.remove('active');
            }
        });
        if (!matched) {
            presetChips.forEach(c => c.classList.remove('active'));
        }
    }

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
        syncPresetChips(bboxInputEl.value);
    }

    if (bboxInputEl) {
        bboxInputEl.addEventListener('input', updateAoiHint);
        bboxInputEl.addEventListener('change', updateAoiHint);
        bboxInputEl.addEventListener('keyup', updateAoiHint);
        updateAoiHint();
    }

    // Quick AOI Presets Handling
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

    let bannerDismissTimer = null;

    function dismissModeBanner() {
        if (!modeBanner) return;
        modeBanner.style.opacity = '0';
        setTimeout(() => {
            if (modeBanner.style.opacity === '0') {
                modeBanner.style.display = 'none';
            }
        }, 360);
    }

    const modeBannerCloseBtn = document.getElementById('mode-banner-close');
    if (modeBannerCloseBtn) {
        modeBannerCloseBtn.addEventListener('click', dismissModeBanner);
    }

    // Floating Mode Banner Display Controller
    function updateModeBanner(mode, facts, errorMsg = null) {
        if (!modeBanner) return;

        if (bannerDismissTimer) {
            clearTimeout(bannerDismissTimer);
            bannerDismissTimer = null;
        }

        modeBanner.className = 'mode-banner';
        modeBanner.style.opacity = '1';
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
            modeBannerTitle.innerText = facts?.mode_label || 'Satellite Scene Unavailable';
            modeBannerDesc.innerText = facts?.mode_description || 'No matching Sentinel-1 repeat pass found for this time window. Pre-event OpenStreetMap infrastructure has been mapped.';
            if (modeRetryBtn) modeRetryBtn.style.display = 'inline-block';
            bannerDismissTimer = setTimeout(dismissModeBanner, 3500);
        } else if (mode === 'reference_case') {
            modeBanner.classList.add('reference');
            modeBannerBadge.innerText = 'REFERENCE CASE';
            modeBannerTitle.innerText = facts?.mode_label || 'Curated Reference Case';
            modeBannerDesc.innerText = facts?.mode_description || 'Curated Copernicus Sentinel-1 reference case validated against Copernicus EMS EMSR927.';
            bannerDismissTimer = setTimeout(dismissModeBanner, 3000);
        } else if (mode === 'demo_simulated') {
            modeBanner.classList.add('partial');
            modeBannerBadge.innerText = 'TERRAIN SIMULATION';
            modeBannerTitle.innerText = facts?.mode_label || 'Topographic Simulation Mode';
            modeBannerDesc.innerText = facts?.mode_description || 'Physics-conditioned demonstration simulation using Copernicus DEM HAND (<15m) and slope (<20°).';
            bannerDismissTimer = setTimeout(dismissModeBanner, 3000);
        } else {
            modeBanner.classList.add('live');
            modeBannerBadge.innerText = 'LIVE ANALYSIS COMPLETE';
            modeBannerTitle.innerText = facts?.mode_label || 'Dynamic Sentinel-1 Retrieval & SAR Delineation';
            modeBannerDesc.innerText = facts?.mode_description || 'All processing stages completed dynamically with Copernicus satellite observations and elevation data.';
            bannerDismissTimer = setTimeout(dismissModeBanner, 3000);
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
            let eventDate = document.getElementById('date-input')?.value || "2026-08-26";
            eventDate = eventDate.trim();
            if (eventDate.includes('/')) {
                const dp = eventDate.split('/');
                if (dp.length === 3 && dp[2].length === 4) {
                    eventDate = `${dp[2]}-${dp[1].padStart(2, '0')}-${dp[0].padStart(2, '0')}`;
                }
            }
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

            // Poll Job Status until backend reports a terminal status (allowing up to 10 minutes for multi-scene downloads)
            let pollAttempts = 0;
            const maxPollAttempts = 600;
            let lastStatusData = null;
            while (!isComplete && pollAttempts < maxPollAttempts) {
                pollAttempts++;
                await new Promise(r => setTimeout(r, 1000));

                try {
                    const statusRes = await fetch(`/jobs/${currentJobId}/status`);
                    if (statusRes.ok) {
                        const statusData = await statusRes.json();
                        lastStatusData = statusData;
                        const progress = statusData.progress || 0.0;
                        progressFill.style.width = Math.max(10, Math.round(progress * 100)) + '%';

                        if (statusData.status === 'failed') {
                            isComplete = true;
                            const errStage = statusData.error?.stage || statusData.stage || 'unknown';
                            const errMsg = statusData.error?.message || statusData.message || "Analysis failed.";
                            throw new Error(`[Stage: ${errStage}] ${errMsg}`);
                        } else if (statusData.status === 'partial') {
                            isComplete = true;
                            stepCounter.innerText = 'Partial (No Imagery)';
                            progressText.innerText = statusData.message || "Partial analysis: OSM mapped; satellite imagery unavailable.";
                        } else if (statusData.status === 'reference_case') {
                            isComplete = true;
                            stepCounter.innerText = 'Complete (Reference)';
                            progressText.innerText = statusData.message || "Curated reference benchmark loaded.";
                        } else if (statusData.status === 'demo_simulated') {
                            isComplete = true;
                            stepCounter.innerText = 'Complete (Simulation)';
                            progressText.innerText = statusData.message || "Physics-conditioned topographic simulation completed.";
                        } else if (statusData.stage === 'satellite_ingest' || statusData.status === 'ingesting') {
                            stepCounter.innerText = 'Stage 1/5';
                            progressText.innerText = statusData.message || "Querying Sentinel-1 IW GRD SAR catalog (ESA CDSE)...";
                            tagSensor.innerText = "SAR: Ingesting";
                        } else if (statusData.stage === 'flood_segmentation' || statusData.status === 'processing') {
                            stepCounter.innerText = 'Stage 2/5';
                            progressText.innerText = statusData.message || "Executing SAR change detection & terrain-constrained flood delineation...";
                            tagSensor.innerText = "SAR: Calibrated (VV/VH)";
                            const elapsedMs = Math.max(16, Math.round(performance.now() - scanStartTime));
                            tagOnnx.innerText = `Method: ONNX Segmentation (${elapsedMs}ms)`;
                        } else if (statusData.stage === 'exposure_routing' || statusData.status === 'analyzing') {
                            stepCounter.innerText = 'Stage 3/5';
                            progressText.innerText = statusData.message || "Applying Copernicus DEM slope mask & Dijkstra graph routing...";
                            tagDem.innerText = `DEM: Slope < ${slopeThreshold}°`;
                        } else if (statusData.stage === 'generating_reports' || statusData.status === 'reporting') {
                            stepCounter.innerText = 'Stage 4/5';
                            progressText.innerText = statusData.message || "Compiling bilingual situation report with number guard...";
                        } else if (statusData.status === 'complete' || progress >= 1.0) {
                            isComplete = true;
                            stepCounter.innerText = 'Complete';
                            progressText.innerText = statusData.message || "Scan finished: Vector layers and analytics compiled.";
                        }
                    }
                } catch (pollErr) {
                    if (lastStatusData && lastStatusData.status === 'failed') {
                        throw pollErr;
                    }
                    console.warn("Poll status notice:", pollErr);
                }
            }

            if (!isComplete) {
                const stageName = lastStatusData?.stage || lastStatusData?.status || 'satellite_ingest';
                throw new Error(`Analysis job timed out in stage '${stageName}' after ${pollAttempts}s without reaching terminal status.`);
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
                const hasS1Rasters = currentFacts.inputs?.has_s1_rasters === true;
                const hasS1Pair = Boolean(currentFacts.inputs?.s1_pair);
                const demUsed = Boolean(currentFacts.inputs?.dem || currentFacts.applied_thresholds);

                if (factsMode === 'partial') {
                    stepCounter.innerText = "Partial (No Imagery)";
                    tagSensor.innerText = "SAR: No Pass in Window";
                    tagOnnx.innerText = "Method: Skipped";
                } else if (factsMode === 'reference_case') {
                    stepCounter.innerText = "Complete (Reference)";
                    tagSensor.innerText = "SAR: Reference Benchmark";
                    tagOnnx.innerText = "Method: Curated Ground Truth";
                } else if (factsMode === 'demo_simulated') {
                    stepCounter.innerText = "Complete (Simulation)";
                    tagSensor.innerText = "SAR: Not Used (Simulation)";
                    tagOnnx.innerText = "Method: Terrain Heuristic";
                } else if (factsMode === 'live_inferred') {
                    stepCounter.innerText = "Complete (Live)";
                    tagSensor.innerText = hasS1Rasters ? "SAR: Live Downloaded" : (hasS1Pair ? "SAR: Catalog Matched" : "SAR: Live Query");
                    tagOnnx.innerText = "Method: Otsu + HAND Filter";
                } else {
                    stepCounter.innerText = `Complete (${factsMode})`;
                    tagSensor.innerText = hasS1Rasters ? "SAR: Live Downloaded" : "SAR: Catalog Matched";
                    tagOnnx.innerText = currentFacts.flood?.method ? "Method: SAR Delineation" : "Method: Unassessed";
                }

                tagDem.innerText = demUsed ? "DEM: Copernicus 30m" : "DEM: Not Applied";

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

    // Smooth polygon coordinates with Chaikin's corner-cutting algorithm
    // to give water and debris polygons organic, fluid, natural boundaries
    function smoothRingChaikin(ring, iterations = 2) {
        if (!ring || ring.length < 4) return ring;
        let pts = ring.slice(0, ring.length - 1);
        for (let it = 0; it < iterations; it++) {
            const next = [];
            const n = pts.length;
            for (let i = 0; i < n; i++) {
                const p0 = pts[i];
                const p1 = pts[(i + 1) % n];
                next.push([
                    0.75 * p0[0] + 0.25 * p1[0],
                    0.75 * p0[1] + 0.25 * p1[1]
                ]);
                next.push([
                    0.25 * p0[0] + 0.75 * p1[0],
                    0.25 * p0[1] + 0.75 * p1[1]
                ]);
            }
            pts = next;
        }
        pts.push([pts[0][0], pts[0][1]]);
        return pts;
    }

    function smoothFeatureGeometry(feature) {
        if (!feature || !feature.geometry) return feature;
        const geom = feature.geometry;
        if (geom.type === 'Polygon' && geom.coordinates) {
            const smoothedRings = geom.coordinates.map(r => smoothRingChaikin(r, 2));
            return {
                ...feature,
                geometry: {
                    ...geom,
                    coordinates: smoothedRings
                }
            };
        } else if (geom.type === 'MultiPolygon' && geom.coordinates) {
            const smoothedPolys = geom.coordinates.map(poly => poly.map(r => smoothRingChaikin(r, 2)));
            return {
                ...feature,
                geometry: {
                    ...geom,
                    coordinates: smoothedPolys
                }
            };
        }
        return feature;
    }

    // 5. Render Dynamic Job Results & GeoJSON Layers
    function renderJobResults(facts, minLng, minLat, maxLng, maxLat) {
        // Update Live HUD numbers directly from facts
        const floodArea = facts.flood?.flooded_area_km2 ?? 0;
        const isDebrisAssessed = facts.debris && facts.debris.status !== 'not_assessed' && facts.debris.debris_area_km2 != null;
        const debrisArea = isDebrisAssessed ? facts.debris.debris_area_km2 : null;
        const exposedBuildings = facts.exposure?.buildings?.exposed_high || facts.exposure?.buildings_exposed_high || (facts.layers?.buildings?.features ? facts.layers.buildings.features.length : 0);

        if (metricFloodVal) metricFloodVal.textContent = floodArea;
        else metricFloodArea.innerHTML = `${floodArea} <span class="unit">km²</span>`;
        metricBuildings.innerText = exposedBuildings;
        
        if (badgeFlood) badgeFlood.innerText = `${floodArea} km² Flood`;
        if (badgeDebris) {
            if (isDebrisAssessed) {
                badgeDebris.innerText = `${debrisArea} km² Hazard`;
            } else {
                badgeDebris.innerText = 'Debris: Not Assessed';
                badgeDebris.title = 'Neural model classifies floodwater; debris scour is not assessed';
            }
        }
        if (badgeBuildings) badgeBuildings.innerText = `${exposedBuildings} Structures`;

        const layers = facts.layers || {};

        // A. Flood Inundation Layer (Fluid Curvilinear Meandering)
        if (layers.flood && layers.flood.features) {
            layers.flood.features.forEach((feature) => {
                const smoothedFeature = smoothFeatureGeometry(feature);
                const polygon = L.geoJSON(smoothedFeature, {
                    style: {
                        color: '#2563eb',          // Classic deep royal/sapphire blue
                        weight: 1.5,
                        opacity: 0.75,
                        fillColor: '#3b82f6',      // Fluid alpine river blue
                        fillOpacity: 0.28,         // Soft translucent water blending with terrain
                        lineJoin: 'round',
                        lineCap: 'round'
                    }
                });

                polygon.bindPopup(`
                    <div class="custom-popup-title" style="color: #2563eb;">🌊 SAR Inundated Floodwater</div>
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
                const smoothedFeature = smoothFeatureGeometry(feature);
                const polygon = L.geoJSON(smoothedFeature, {
                    style: {
                        color: '#d97706',          // Earthy sediment amber
                        weight: 1.4,
                        opacity: 0.8,
                        dashArray: '4, 4',
                        fillColor: '#d97706',
                        fillOpacity: 0.22,
                        lineJoin: 'round'
                    }
                });

                const props = feature.properties || {};
                polygon.bindPopup(`
                    <div class="custom-popup-title" style="color: #d97706;">🪨 ${props.name || 'Debris & Scour Field'} [Zone ${idx + 1}]</div>
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

        // Auto-show explainer guide after scan completion unless user suppressed it
        const dontShow = localStorage.getItem('hydroviz_hide_explainer') === 'true';
        if (!dontShow) {
            setTimeout(() => {
                showExplainerModal(facts);
            }, 700);
        }
    }

    // Explainer Modal Controller
    function showExplainerModal(facts) {
        const explainerModal = document.getElementById('explainer-modal');
        if (!explainerModal) return;

        const f = facts || currentFacts || {};
        const floodArea = f.flood?.flooded_area_km2 ?? 0;
        const isDebrisAssessed = f.debris && f.debris.status !== 'not_assessed' && f.debris.debris_area_km2 != null;
        const debrisText = isDebrisAssessed ? `${f.debris.debris_area_km2} km²` : 'Not Assessed (No AI debris class)';
        const exposedBuildings = f.exposure?.buildings?.exposed_high || f.exposure?.buildings_exposed_high || (f.layers?.buildings?.features ? f.layers.buildings.features.length : 0);
        const exposedRoadsKm = f.exposure?.roads_km?.exposed_strict ?? f.exposure?.roads_km?.exposed ?? (f.exposure?.roads_exposed_length_m ? (f.exposure.roads_exposed_length_m / 1000).toFixed(1) : 0);
        const isolatedHamlets = f.cutoff?.isolated_settlements ?? (f.cutoff?.settlements ? f.cutoff.settlements.filter(s => s.status === 'isolated').length : 0);

        const elFlood = document.getElementById('expl-flood-val');
        if (elFlood) elFlood.innerText = `${floodArea} km²`;
        const elDebris = document.getElementById('expl-debris-val');
        if (elDebris) elDebris.innerText = debrisText;
        const elBld = document.getElementById('expl-bld-val');
        if (elBld) elBld.innerText = `${exposedBuildings}`;
        const elRoads = document.getElementById('expl-roads-val');
        if (elRoads) elRoads.innerText = `${exposedRoadsKm} km`;
        const elSettle = document.getElementById('expl-settle-val');
        if (elSettle) elSettle.innerText = `${isolatedHamlets}`;
        const elJobId = document.getElementById('explainer-job-id');
        if (elJobId) elJobId.innerText = `Job ID: ${currentJobId || 'Latest Scan'}`;

        const dontShowCb = document.getElementById('dont-show-explainer-cb');
        if (dontShowCb) {
            dontShowCb.checked = localStorage.getItem('hydroviz_hide_explainer') === 'true';
        }

        explainerModal.style.display = 'flex';
    }

    // 6. Interactive D8 Downhill Flow Path Tracing Tool
    const traceHintBanner = document.getElementById('trace-hint-banner');

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

        // Clear prior traces on new click so old markers do not clutter the map
        traceLayerGroup.clearLayers();

        // Provide instant visual feedback at click point while calculating
        const tempPulseMarker = L.circleMarker([lat, lng], {
            radius: 7,
            color: '#ffffff',
            fillColor: '#2563eb',
            fillOpacity: 0.85,
            weight: 2
        }).addTo(traceLayerGroup);
        tempPulseMarker.bindTooltip("💧 Simulating D8 downhill runoff path...", { permanent: true, direction: "top" }).openTooltip();

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
            traceLayerGroup.removeLayer(tempPulseMarker);

            if (traceData.status === 'unavailable' || !traceData.path) {
                alert(traceData.message || "Georeferenced DEM data is not available for this coordinate to compute downhill flow routing.");
                traceBtnLabel.innerText = "Click on Map to Trace";
                return null;
            }

            const pathFeature = traceData.path;
            const props = pathFeature.properties || {};

            // Render prominent dual-stroke flow line with high contrast on satellite basemap
            const flowLineCasing = L.geoJSON(pathFeature, {
                style: {
                    color: '#0f172a',
                    weight: 6.5,
                    opacity: 0.85,
                    lineCap: 'round',
                    lineJoin: 'round'
                }
            });

            const flowLine = L.geoJSON(pathFeature, {
                style: {
                    color: '#38bdf8',
                    weight: 3.5,
                    opacity: 1.0,
                    dashArray: '6, 6',
                    lineCap: 'round',
                    lineJoin: 'round'
                }
            });

            // Start Marker (Origin)
            const startCircle = L.circleMarker([origin[1], origin[0]], {
                radius: 7,
                color: '#ffffff',
                fillColor: '#2563eb',
                fillOpacity: 1,
                weight: 2.5
            });

            // Outflow Terminus Marker (Downstream End)
            let endCircle = null;
            const pathCoords = (pathFeature.geometry && pathFeature.geometry.coordinates) || [];
            if (pathCoords.length > 1) {
                const lastPt = pathCoords[pathCoords.length - 1];
                endCircle = L.circleMarker([lastPt[1], lastPt[0]], {
                    radius: 6,
                    color: '#ffffff',
                    fillColor: '#10b981',
                    fillOpacity: 1,
                    weight: 2
                }).bindTooltip(`🌊 Outflow Terminus: ${props.end_elevation_m != null ? props.end_elevation_m + 'm' : ''}`, { direction: 'bottom' });
            }

            const settlementsList = props.settlements_along_path || traceData.settlements_along_path || [];
            let settlementsHtml = '';
            if (settlementsList.length > 0) {
                settlementsHtml = `
                    <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.15);">
                        <strong style="color: #38bdf8;">🏘️ Settlements Along Path (${settlementsList.length}):</strong>
                        <ul style="margin: 4px 0 0 0; padding-left: 16px; font-size: 11px; line-height: 1.4; color: #cbd5e1;">
                            ${settlementsList.map(s => `<li><strong>${s.name}</strong> (${s.place}) — ${s.distance_downstream_km} km downstream</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            const popupHtml = `
                <div class="custom-popup-title" style="color: #2563eb; display: flex; align-items: center; gap: 6px;">
                    <span>💧</span>
                    <span>D8 Downhill Flow Path</span>
                </div>
                <div class="custom-popup-body" style="font-size: 12px; line-height: 1.55;">
                    <div style="display: grid; grid-template-columns: auto auto; gap: 4px 12px; margin-bottom: 6px;">
                        <span style="color: #94a3b8;">Source:</span>
                        <strong style="color: #f1f5f9;">${origin[1].toFixed(5)}, ${origin[0].toFixed(5)}</strong>
                        <span style="color: #94a3b8;">Start Elevation:</span>
                        <strong style="color: #38bdf8;">${props.start_elevation_m != null ? props.start_elevation_m + 'm' : '--'}</strong>
                        <span style="color: #94a3b8;">Terminal Elevation:</span>
                        <strong style="color: #10b981;">${props.end_elevation_m != null ? props.end_elevation_m + 'm' : '--'}</strong>
                        <span style="color: #94a3b8;">Total Vertical Drop:</span>
                        <strong style="color: #f59e0b;">${props.drop_m != null ? props.drop_m + 'm' : '--'}</strong>
                        <span style="color: #94a3b8;">Downstream Distance:</span>
                        <strong style="color: #f1f5f9;">${props.distance_km != null ? props.distance_km + ' km' : '--'}</strong>
                        ${props.slope_percent != null ? `<span style="color: #94a3b8;">Average Slope:</span><strong style="color: #f1f5f9;">${props.slope_percent}%</strong>` : ''}
                    </div>
                    <div style="font-size: 11px; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 5px;">
                        <strong>DEM Source:</strong> Copernicus WorldDEM-30 (D8 Steepest Descent)
                    </div>
                    ${settlementsHtml}
                    <span style="font-size: 10px; color: #64748b; display: block; margin-top: 6px;">Notice: Bare-earth terrain runoff model, not proof of historical debris flood extent.</span>
                </div>
            `;

            startCircle.bindPopup(popupHtml);
            if (endCircle) endCircle.bindPopup(popupHtml);
            flowLine.bindPopup(popupHtml);
            flowLineCasing.bindPopup(popupHtml);

            traceLayerGroup.addLayer(flowLineCasing);
            traceLayerGroup.addLayer(flowLine);
            if (endCircle) traceLayerGroup.addLayer(endCircle);
            traceLayerGroup.addLayer(startCircle);
            startCircle.openPopup();

            clearTraceBtn.style.display = 'inline-block';
            return traceData;

        } catch (err) {
            traceLayerGroup.removeLayer(tempPulseMarker);
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
            if (traceHintBanner) traceHintBanner.style.display = 'flex';
        } else {
            traceToggleBtn.classList.remove('active');
            traceBtnLabel.innerText = "Enable Map Click Tracing";
            traceStatusBadge.innerText = "Click Mode: OFF";
            traceStatusBadge.classList.remove('active');
            map.getContainer().classList.remove('crosshair-cursor');
            if (traceHintBanner) traceHintBanner.style.display = 'none';
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

    // Wire Scenario Select Dropdown (Active immediately upon changes)
    if (scenarioSelect) {
        scenarioSelect.addEventListener('change', (e) => {
            if (currentFacts) {
                renderJobResults(currentFacts, 85.50, 27.80, 85.65, 28.05);
            }
        });
    }

    // Wire Advanced Parameters Drawer Summary toggle
    const advSummary = document.querySelector('.advanced-summary');
    const advDrawer = document.getElementById('advanced-settings');
    if (advSummary && advDrawer) {
        advSummary.addEventListener('click', (e) => {
            e.preventDefault();
            advDrawer.open = !advDrawer.open;
        });
    }

    // Wire Explainer Modal Handlers
    const explainerModal = document.getElementById('explainer-modal');
    const explainerCloseBtn = document.getElementById('explainer-close-btn');
    const explainerOkBtn = document.getElementById('explainer-ok-btn');
    const explainerViewReportBtn = document.getElementById('explainer-view-report-btn');
    const dontShowExplainerCb = document.getElementById('dont-show-explainer-cb');
    const hudGuideBtn = document.getElementById('hud-guide-btn');
    const openExplainerBtn = document.getElementById('open-explainer-btn');

    if (explainerCloseBtn) explainerCloseBtn.onclick = () => { if (explainerModal) explainerModal.style.display = 'none'; };
    if (explainerOkBtn) explainerOkBtn.onclick = () => { if (explainerModal) explainerModal.style.display = 'none'; };
    if (explainerViewReportBtn) explainerViewReportBtn.onclick = () => {
        if (explainerModal) explainerModal.style.display = 'none';
        if (viewReportBtn) viewReportBtn.click();
    };
    if (dontShowExplainerCb) {
        dontShowExplainerCb.onchange = (e) => {
            localStorage.setItem('hydroviz_hide_explainer', e.target.checked ? 'true' : 'false');
        };
    }
    if (hudGuideBtn) hudGuideBtn.onclick = () => showExplainerModal(currentFacts);
    if (openExplainerBtn) openExplainerBtn.onclick = () => showExplainerModal(currentFacts);

    // Close modals on escape key or clicking backdrop
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (explainerModal) explainerModal.style.display = 'none';
            if (reportModal) reportModal.style.display = 'none';
        }
    });

    if (explainerModal) {
        explainerModal.addEventListener('click', (e) => {
            if (e.target === explainerModal) explainerModal.style.display = 'none';
        });
    }

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

    // =========================================================================
    // 13. Real-Time System Logger & Client-Side API Activity Console
    // =========================================================================
    const toggleLoggerBtn = document.getElementById('toggle-logger-btn');
    const loggerWindow = document.getElementById('system-logger-window');
    const closeLoggerBtn = document.getElementById('close-logger-btn');
    const clearLoggerBtn = document.getElementById('clear-logger-btn');
    const autoscrollLoggerBtn = document.getElementById('autoscroll-logger-btn');
    const loggerEntries = document.getElementById('logger-entries');
    const loggerSearchInput = document.getElementById('logger-search-input');
    const loggerCountPill = document.getElementById('logger-count-pill');
    const loggerFooterCounter = document.getElementById('logger-footer-counter');
    const loggerFilterBtns = document.querySelectorAll('.log-filter-btn');

    let allLogs = [];
    let currentCategory = 'ALL';
    let searchQuery = '';
    let autoScroll = true;
    let loggerOpen = false;
    let seenLogIds = new Set();

    // Monkey-patch window.fetch to capture client-side API telemetry
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0]?.url || '');
        const options = args[1] || {};
        const method = options.method || 'GET';
        const startTime = performance.now();

        // Avoid infinite loop on internal telemetry polling
        const isTelemetryPoll = url.includes('/system/logs');

        try {
            const response = await originalFetch.apply(this, args);
            const durationMs = Math.round(performance.now() - startTime);

            if (!isTelemetryPoll) {
                const status = response.status;
                const level = status >= 400 ? 'ERROR' : (status >= 300 ? 'WARN' : 'INFO');
                addClientLog({
                    timestamp: new Date().toISOString(),
                    level: level,
                    category: 'API',
                    event: `${method} ${url}`,
                    message: `${method} ${url} -> HTTP ${status} (${durationMs}ms)`,
                    details: { status, durationMs }
                });
            }

            return response;
        } catch (error) {
            const durationMs = Math.round(performance.now() - startTime);
            if (!isTelemetryPoll) {
                addClientLog({
                    timestamp: new Date().toISOString(),
                    level: 'ERROR',
                    category: 'API',
                    event: `${method} ${url}`,
                    message: `${method} ${url} -> FAILED (${error.message})`,
                    details: { error: error.message, durationMs }
                });
            }
            throw error;
        }
    };

    function formatTime(isoStr) {
        if (!isoStr) return '';
        try {
            const d = new Date(isoStr);
            return d.toTimeString().split(' ')[0] + '.' + String(d.getMilliseconds()).padStart(3, '0');
        } catch {
            return isoStr.slice(11, 19);
        }
    }

    function addClientLog(logObj) {
        logObj.id = logObj.id || ('client_' + Math.random().toString(36).substr(2, 9));
        if (seenLogIds.has(logObj.id)) return;
        seenLogIds.add(logObj.id);
        allLogs.push(logObj);
        if (allLogs.length > 500) allLogs.shift();
        updateLogCount();
        renderFilteredLogs();
    }

    function updateLogCount() {
        const cnt = allLogs.length;
        if (loggerCountPill) loggerCountPill.textContent = cnt;
        if (loggerFooterCounter) loggerFooterCounter.textContent = `${cnt} events recorded`;
    }

    function renderFilteredLogs() {
        if (!loggerEntries) return;

        const filtered = allLogs.filter(log => {
            const catUpper = (log.category || '').toUpperCase();
            const matchesCat = currentCategory === 'ALL' || 
                catUpper === currentCategory || 
                catUpper.startsWith(currentCategory + ':') ||
                catUpper.startsWith(currentCategory + '_') ||
                (currentCategory === 'API' && catUpper.startsWith('API'));
            const matchesSearch = !searchQuery || 
                (log.message && log.message.toLowerCase().includes(searchQuery)) ||
                (log.event && log.event.toLowerCase().includes(searchQuery)) ||
                (log.level && log.level.toLowerCase().includes(searchQuery)) ||
                (log.category && log.category.toLowerCase().includes(searchQuery));
            return matchesCat && matchesSearch;
        });

        loggerEntries.innerHTML = '';
        if (filtered.length === 0) {
            loggerEntries.innerHTML = '<div style="color: #64748b; padding: 12px; text-align: center; font-style: italic;">No log events matching current filter</div>';
            return;
        }

        filtered.forEach(log => {
            const row = document.createElement('div');
            const levelClass = (log.level || 'info').toLowerCase();
            const catClass = (log.category || 'system').toLowerCase();
            
            row.className = `log-row ${levelClass === 'error' ? 'error-row' : (levelClass === 'success' ? 'success-row' : '')}`;
            
            const timeSpan = document.createElement('span');
            timeSpan.className = 'log-time';
            timeSpan.textContent = formatTime(log.timestamp);
            
            const badgeSpan = document.createElement('span');
            badgeSpan.className = `log-badge ${levelClass}`;
            badgeSpan.textContent = log.level || 'INFO';

            const catSpan = document.createElement('span');
            catSpan.className = `log-cat ${catClass}`;
            catSpan.textContent = log.category || 'SYS';

            const msgSpan = document.createElement('span');
            msgSpan.className = 'log-msg';
            msgSpan.textContent = log.message || log.event || '';

            row.appendChild(timeSpan);
            row.appendChild(badgeSpan);
            row.appendChild(catSpan);
            row.appendChild(msgSpan);

            loggerEntries.appendChild(row);
        });

        if (autoScroll) {
            loggerEntries.scrollTop = loggerEntries.scrollHeight;
        }
    }

    async function fetchSystemLogs() {
        try {
            const res = await originalFetch('/system/logs?limit=150');
            if (res.ok) {
                const data = await res.json();
                const serverLogs = data.logs || [];
                let newAdded = false;
                serverLogs.forEach(sLog => {
                    if (!seenLogIds.has(sLog.id)) {
                        seenLogIds.add(sLog.id);
                        allLogs.push(sLog);
                        newAdded = true;
                    }
                });
                if (newAdded) {
                    allLogs.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                    if (allLogs.length > 500) allLogs = allLogs.slice(-500);
                    updateLogCount();
                    renderFilteredLogs();
                }
            }
        } catch (err) {
            // silent catch during offline/startup
        }
    }

    // Toggle button handler
    if (toggleLoggerBtn && loggerWindow) {
        toggleLoggerBtn.addEventListener('click', () => {
            loggerOpen = !loggerOpen;
            loggerWindow.style.display = loggerOpen ? 'flex' : 'none';
            if (loggerOpen) {
                renderFilteredLogs();
                fetchSystemLogs();
            }
        });
    }

    if (closeLoggerBtn && loggerWindow) {
        closeLoggerBtn.addEventListener('click', () => {
            loggerOpen = false;
            loggerWindow.style.display = 'none';
        });
    }

    if (clearLoggerBtn) {
        clearLoggerBtn.addEventListener('click', async () => {
            allLogs = [];
            seenLogIds.clear();
            try {
                await originalFetch('/system/logs', { method: 'DELETE' });
            } catch (e) {}
            updateLogCount();
            renderFilteredLogs();
        });
    }

    if (autoscrollLoggerBtn) {
        autoscrollLoggerBtn.addEventListener('click', () => {
            autoScroll = !autoScroll;
            autoscrollLoggerBtn.classList.toggle('active', autoScroll);
            autoscrollLoggerBtn.textContent = autoScroll ? 'Scroll: ON' : 'Scroll: OFF';
            if (autoScroll && loggerEntries) {
                loggerEntries.scrollTop = loggerEntries.scrollHeight;
            }
        });
    }

    if (loggerSearchInput) {
        loggerSearchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            renderFilteredLogs();
        });
    }

    loggerFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            loggerFilterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = btn.dataset.cat || 'ALL';
            renderFilteredLogs();
        });
    });

    // Start background polling for telemetry
    setInterval(fetchSystemLogs, 1500);
    // Initial fetch to load historical startup logs
    fetchSystemLogs();

    console.log("HydroViz Dashboard initialized successfully!");
});
