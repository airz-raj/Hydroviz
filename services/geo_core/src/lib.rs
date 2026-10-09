use pyo3::prelude::*;
use crate::exposure::run_exposure_analysis;
use crate::cutoff::run_cutoff_analysis;
use crate::flowpath::run_flow_path_tracing;
use crate::dem::fill_dem_pits;

pub mod types;
pub mod exposure;
pub mod cutoff;
pub mod flowpath;
pub mod dem;

#[pymodule]
fn geo_core(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<types::Building>()?;
    m.add_class::<types::Road>()?;
    m.add_class::<types::Bridge>()?;
    m.add_class::<types::Settlement>()?;
    m.add_class::<types::ExposureResult>()?;
    
    m.add_function(wrap_pyfunction!(run_exposure_analysis, m)?)?;
    m.add_function(wrap_pyfunction!(run_cutoff_analysis, m)?)?;
    m.add_function(wrap_pyfunction!(run_flow_path_tracing, m)?)?;
    m.add_function(wrap_pyfunction!(fill_dem_pits, m)?)?;
    Ok(())
}
