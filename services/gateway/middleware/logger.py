import time
from datetime import datetime, timezone
from collections import deque
from typing import Dict, Any, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# In-memory thread-safe circular buffer for system logs (max 1000 items)
_system_logs: deque = deque(maxlen=1000)
_log_counter: int = 0

def log_system_event(
    *args,
    level: str = "INFO",
    category: str = "SYSTEM",
    message: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Appends a structured event log to the system buffer.
    Supports flexible positional and keyword signatures:
      log_system_event("INFO", "API", "message")
      log_system_event("osm_ingest", "Found features...", details={...}, level="INFO", category="GEO")
    """
    global _log_counter
    if len(args) == 3:
        level, category, message = args[0], args[1], args[2]
    elif len(args) == 2:
        category = kwargs.get("category", args[0])
        message = args[1]
    elif len(args) == 1:
        message = args[0]
        
    lvl = (kwargs.get("level") or level or "INFO").upper()
    cat = (kwargs.get("category") or category or "SYSTEM").upper()
    msg = kwargs.get("message") or message
    meta = metadata or details or kwargs.get("details") or kwargs.get("meta") or {}

    _log_counter += 1
    entry = {
        "id": _log_counter,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": lvl,
        "category": cat,
        "message": str(msg),
        "metadata": meta,
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None
    }
    _system_logs.append(entry)
    return entry

def get_system_logs(category: Optional[str] = None, limit: int = 150, **kwargs) -> List[Dict[str, Any]]:
    """Retrieves recent logs, optionally filtered by category."""
    lim = kwargs.get("limit", limit)
    cat = kwargs.get("category", category)
    logs = list(_system_logs)
    if cat and cat.upper() != "ALL":
        cat_upper = cat.upper()
        logs = [log for log in logs if log.get("category") == cat_upper or cat_upper in log.get("category", "")]
    return logs[-lim:]

def clear_system_logs() -> None:
    """Clears the in-memory log buffer."""
    _system_logs.clear()

class SystemLoggerMiddleware(BaseHTTPMiddleware):
    """
    Intercepts and logs every incoming HTTP request and response,
    recording path, method, client, status code, and latency in ms.
    """
    async def dispatch(self, request: Request, call_next):
        # Skip static asset files from flooding the log buffer
        path = request.url.path
        if any(path.endswith(ext) for ext in ('.css', '.js', '.png', '.jpg', '.ico', '.svg', '.woff2', '.ttf')):
            return await call_next(request)

        start_time = time.time()
        method = request.method
        client_ip = request.client.host if request.client else "127.0.0.1"

        try:
            response: Response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000.0

            level = "SUCCESS" if response.status_code < 400 else ("WARN" if response.status_code < 500 else "ERROR")
            log_system_event(
                level=level,
                category=f"API:{method}",
                message=f"{method} {path} -> {response.status_code}",
                metadata={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "client_ip": client_ip,
                    "query_params": dict(request.query_params)
                },
                duration_ms=duration_ms
            )
            return response
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000.0
            log_system_event(
                level="ERROR",
                category=f"API:{method}",
                message=f"{method} {path} -> Exception: {str(exc)}",
                metadata={
                    "method": method,
                    "path": path,
                    "error": str(exc),
                    "client_ip": client_ip
                },
                duration_ms=duration_ms
            )
            raise exc
