use pyo3::prelude::*;

#[pyfunction]
pub fn fill_dem_pits(_dem_path: String) -> PyResult<bool> {
    // Condition DEM by filling topological depressions (priority-flood algorithm stub)
    Ok(true)
}

pub fn fill_pits_grid(grid: &mut [Vec<f64>]) {
    // Basic depression filling: any cell lower than all 4 neighbors is raised to min neighbor
    let rows = grid.len();
    if rows == 0 { return; }
    let cols = grid[0].len();
    if cols == 0 { return; }

    for r in 1..(rows - 1) {
        for c in 1..(cols - 1) {
            let val = grid[r][c];
            let n1 = grid[r - 1][c];
            let n2 = grid[r + 1][c];
            let n3 = grid[r][c - 1];
            let n4 = grid[r][c + 1];
            let min_neighbor = n1.min(n2).min(n3).min(n4);
            if val < min_neighbor {
                grid[r][c] = min_neighbor;
            }
        }
    }
}
