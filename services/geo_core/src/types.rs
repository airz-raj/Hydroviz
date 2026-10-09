use pyo3::prelude::*;

#[derive(Clone, Debug)]
#[pyclass]
pub struct Building {
    #[pyo3(get, set)]
    pub osm_id: i64,
    #[pyo3(get, set)]
    pub exposure: String,
}

#[derive(Clone, Debug)]
#[pyclass]
pub struct Road {
    #[pyo3(get, set)]
    pub osm_id: i64,
    #[pyo3(get, set)]
    pub total_length_m: f64,
    #[pyo3(get, set)]
    pub exposed_length_m: f64,
}

#[derive(Clone, Debug)]
#[pyclass]
pub struct Bridge {
    #[pyo3(get, set)]
    pub osm_id: i64,
    #[pyo3(get, set)]
    pub status: String,
}

#[derive(Clone, Debug)]
#[pyclass]
pub struct Settlement {
    #[pyo3(get, set)]
    pub osm_id: i64,
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub cutoff_status_strict: String,
    #[pyo3(get, set)]
    pub cutoff_status_conservative: String,
}

#[derive(Clone, Debug)]
#[pyclass]
pub struct ExposureResult {
    #[pyo3(get, set)]
    pub buildings: Vec<Building>,
    #[pyo3(get, set)]
    pub roads: Vec<Road>,
    #[pyo3(get, set)]
    pub bridges: Vec<Bridge>,
}

#[pymethods]
impl ExposureResult {
    #[new]
    pub fn new() -> Self {
        Self {
            buildings: Vec::new(),
            roads: Vec::new(),
            bridges: Vec::new(),
        }
    }
}
