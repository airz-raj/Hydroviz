use pyo3::prelude::*;

#[pyfunction]
fn health_check() -> PyResult<String> {
    Ok("ok".to_string())
}

#[pymodule]
fn geo_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(health_check, m)?)?;
    Ok(())
}
