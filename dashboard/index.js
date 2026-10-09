document.addEventListener('DOMContentLoaded', () => {
    // Initialize MapLibre GL JS
    const map = new maplibregl.Map({
        container: 'map',
        style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
        center: [85.75, 28.0],
        zoom: 9
    });

    map.addControl(new maplibregl.NavigationControl());

    const submitBtn = document.getElementById('submit-btn');
    const statusPanel = document.getElementById('status-panel');
    const progressText = document.getElementById('progress-text');
    const reportPanel = document.getElementById('report-panel');
    const viewReportBtn = document.getElementById('view-report-btn');

    let currentJobId = null;

    submitBtn.addEventListener('click', async () => {
        const bbox = document.getElementById('bbox-input').value;
        const date = document.getElementById('date-input').value;
        
        statusPanel.style.display = 'block';
        reportPanel.style.display = 'none';
        progressText.innerText = "Submitting job...";
        
        try {
            // Stubbed API call for prototype
            // const response = await fetch('/jobs', { ... })
            // const data = await response.json()
            
            // Simulate SSE progress
            currentJobId = "stub-job-id-1234";
            
            setTimeout(() => { progressText.innerText = "Ingesting satellite data..."; }, 1000);
            setTimeout(() => { progressText.innerText = "Processing baseline flood map..."; }, 2500);
            setTimeout(() => { progressText.innerText = "Running ONNX model..."; }, 4000);
            setTimeout(() => { progressText.innerText = "Analyzing exposure and cut-offs..."; }, 6000);
            setTimeout(() => { 
                progressText.innerText = "Report generated.";
                reportPanel.style.display = 'block';
                loadMapLayers();
            }, 8000);
            
        } catch (error) {
            progressText.innerText = "Error: " + error.message;
        }
    });
    
    viewReportBtn.addEventListener('click', () => {
        if (currentJobId) {
            // Usually this would open the generated PDF/HTML
            alert("Situation Report opened for Job: " + currentJobId);
        }
    });

    function loadMapLayers() {
        // Example logic for adding raster tiles and geojson
        console.log("Loading layers for job: ", currentJobId);
        // map.addSource('flood', { ... })
        // map.addLayer({ ... })
    }
    
    // Layer toggles
    document.getElementById('layer-flood').addEventListener('change', (e) => {
        // if (map.getLayer('flood-layer')) map.setLayoutProperty('flood-layer', 'visibility', e.target.checked ? 'visible' : 'none');
    });
});
