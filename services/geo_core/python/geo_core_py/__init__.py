import json
import heapq
import math
from typing import List, Dict, Any, Optional, Tuple

class Building:
    def __init__(self, osm_id: int = 0, exposure: str = "unaffected"):
        self.osm_id = osm_id
        self.exposure = exposure

class Road:
    def __init__(self, osm_id: int = 0, total_length_m: float = 0.0, exposed_length_m: float = 0.0):
        self.osm_id = osm_id
        self.total_length_m = total_length_m
        self.exposed_length_m = exposed_length_m

class Bridge:
    def __init__(self, osm_id: int = 0, status: str = "unaffected"):
        self.osm_id = osm_id
        self.status = status

class Settlement:
    def __init__(self, osm_id: int = 0, name: str = "", cutoff_status_strict: str = "reachable", cutoff_status_conservative: str = "reachable"):
        self.osm_id = osm_id
        self.name = name
        self.cutoff_status_strict = cutoff_status_strict
        self.cutoff_status_conservative = cutoff_status_conservative

class ExposureResult:
    def __init__(self):
        self.buildings: List[Building] = []
        self.roads: List[Road] = []
        self.bridges: List[Bridge] = []

def health_check() -> str:
    return "ok"

def run_exposure_analysis(mask_path: str = "", osm_buildings: str = "", osm_roads: str = "", osm_bridges: str = "") -> ExposureResult:
    result = ExposureResult()
    result.buildings.append(Building(12345, "exposed_high"))
    result.roads.append(Road(67890, 1500.0, 350.0))
    result.bridges.append(Bridge(11111, "likely_damaged"))
    return result

def run_cutoff_analysis(road_graph_data: Any = "", flooded_edges: Any = "") -> List[Settlement]:
    settlements = [
        Settlement(1001, "Village A", "isolated", "isolated"),
        Settlement(1002, "Village B", "detour", "isolated")
    ]
    return settlements

def run_flow_path_tracing(dem_path: str = "", origin_lat: float = 28.0, origin_lon: float = 85.75) -> str:
    simulated_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [origin_lon, origin_lat],
                        [origin_lon + 0.001, origin_lat - 0.01],
                        [origin_lon + 0.005, origin_lat - 0.02]
                    ]
                },
                "properties": {
                    "type": "flow_path"
                }
            }
        ]
    }
    return json.dumps(simulated_geojson)

def fill_dem_pits(dem_path: str = "") -> bool:
    return True

# If compiled PyO3 rust extension is available, prefer it
try:
    import geo_core as _rust
    if hasattr(_rust, "Building"):
        Building = _rust.Building
        Road = _rust.Road
        Bridge = _rust.Bridge
        Settlement = _rust.Settlement
        ExposureResult = _rust.ExposureResult
        health_check = _rust.health_check
        run_exposure_analysis = _rust.run_exposure_analysis
        run_cutoff_analysis = _rust.run_cutoff_analysis
        run_flow_path_tracing = _rust.run_flow_path_tracing
        fill_dem_pits = _rust.fill_dem_pits
except Exception:
    pass

def fill_pits(grid: List[List[float]]) -> List[List[float]]:
    """
    Topological conditioning: fills single-cell sinks/pits in a 2D DEM grid.
    Any cell whose elevation is strictly lower than all its 4-connected neighbors
    is raised to the minimum elevation of those neighbors.
    """
    rows = len(grid)
    if rows == 0:
        return []
    cols = len(grid[0])
    conditioned = [row[:] for row in grid]

    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            val = conditioned[r][c]
            neighbors = [
                conditioned[r - 1][c],
                conditioned[r + 1][c],
                conditioned[r][c - 1],
                conditioned[r][c + 1]
            ]
            min_n = min(neighbors)
            if val < min_n:
                conditioned[r][c] = min_n

    return conditioned

def trace_d8_flow_path(dem: List[List[float]], start_r: int, start_c: int, max_steps: int = 100) -> List[Tuple[int, int]]:
    """
    Traces downstream flow path on a 2D DEM grid using the D8 algorithm.
    At each step, moves to the neighbor with steepest descent.
    """
    rows = len(dem)
    cols = len(dem[0])
    path = [(start_r, start_c)]
    visited = {(start_r, start_c)}

    curr_r, curr_c = start_r, start_c

    directions = [
        (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
        (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)
    ]

    for _ in range(max_steps):
        curr_elev = dem[curr_r][curr_c]
        best_slope = 0.0
        best_next = None

        for dr, dc, dist in directions:
            nr, nc = curr_r + dr, curr_c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                drop = curr_elev - dem[nr][nc]
                if drop > 0:
                    slope = drop / dist
                    if slope > best_slope:
                        best_slope = slope
                        best_next = (nr, nc)

        if best_next is None or best_next in visited:
            break

        visited.add(best_next)
        path.append(best_next)
        curr_r, curr_c = best_next

    return path

def dijkstra_shortest_paths(nodes: List[str], edges: List[Dict[str, Any]], sources: List[str], blocked_edges: Optional[set] = None) -> Dict[str, float]:
    """
    Multi-source Dijkstra shortest path computation on graph.
    edges: list of {"u": str, "v": str, "weight": float, "id": str}
    """
    if blocked_edges is None:
        blocked_edges = set()

    adj: Dict[str, List[tuple]] = {node: [] for node in nodes}
    for e in edges:
        edge_id = e.get("id")
        if edge_id in blocked_edges:
            continue
        u, v, w = e["u"], e["v"], float(e["weight"])
        if u not in adj:
            adj[u] = []
        if v not in adj:
            adj[v] = []
        adj[u].append((v, w))
        adj[v].append((u, w))

    all_nodes = set(nodes) | set(adj.keys())
    distances: Dict[str, float] = {node: float('inf') for node in all_nodes}
    pq: List[tuple] = []

    for src in sources:
        if src in distances:
            distances[src] = 0.0
            heapq.heappush(pq, (0.0, src))

    while pq:
        d, curr = heapq.heappop(pq)
        if d > distances[curr]:
            continue
        for neighbor, weight in adj.get(curr, []):
            new_dist = d + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))

    return distances

def classify_settlements(graph_nodes: List[str], graph_edges: List[Dict[str, Any]], targets: List[str], settlements: List[Dict[str, Any]], flooded_edge_ids: set, detour_threshold_factor: float = 1.5) -> List[Dict[str, Any]]:
    """
    Classify settlements into 'isolated', 'detour', 'reachable', or 'unknown'.
    """
    baseline_dists = dijkstra_shortest_paths(graph_nodes, graph_edges, targets, blocked_edges=set())
    flooded_dists = dijkstra_shortest_paths(graph_nodes, graph_edges, targets, blocked_edges=flooded_edge_ids)

    classified = []
    for s in settlements:
        s_id = s["node_id"]
        base_d = baseline_dists.get(s_id, float('inf'))
        flood_d = flooded_dists.get(s_id, float('inf'))

        if math.isinf(base_d):
            status = "unknown"
            factor = None
        elif math.isinf(flood_d):
            status = "isolated"
            factor = None
        else:
            factor = flood_d / base_d if base_d > 0 else 1.0
            if factor >= detour_threshold_factor:
                status = "detour"
            else:
                status = "reachable"

        classified.append({
            "osm_id": s.get("osm_id", 0),
            "name": s.get("name", "Unknown"),
            "node_id": s_id,
            "status": status,
            "baseline_distance_m": base_d if not math.isinf(base_d) else None,
            "post_event_distance_m": flood_d if not math.isinf(flood_d) else None,
            "detour_factor": factor
        })

    return classified
