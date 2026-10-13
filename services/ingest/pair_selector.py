from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

_last_selection_reason: Optional[str] = None

def get_last_selection_reason() -> Optional[str]:
    """Return the diagnostic reason why the last pair/triplet selection failed or succeeded."""
    return _last_selection_reason

def select_s1_pair(features: List[Dict[Any, Any]], event_date: str) -> Optional[Dict[str, Any]]:
    """
    Select pre-event and post-event acquisitions from the same relative orbit and direction.
    Requires 3 distinct acquisitions (pre2, pre1, post) matching the Kuro Siwo
    multi-temporal input format (2 pre-events + 1 post-event).
    All acquisitions must have distinct, strictly ordered timestamps:
      pre2 < pre1 < event_date <= post
    Duplicate acquisitions or fallbacks that copy pre1 into pre2 are strictly rejected.
    """
    global _last_selection_reason
    _last_selection_reason = None

    if not features:
        _last_selection_reason = "No Sentinel-1 catalogue features provided."
        return None

    def _get_prop(f: Dict[Any, Any], key: str, fallback=None):
        props = f.get("properties", {})
        if key in props and props[key] is not None:
            return props[key]
        if key in f and f[key] is not None:
            return f[key]
        return fallback

    def parse_dt(dt_str: str) -> Optional[datetime]:
        try:
            dt = datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    event_dt = parse_dt(event_date)
    if event_dt is None:
        try:
            event_dt = datetime.fromisoformat(f"{event_date[:10]}T00:00:00+00:00")
        except Exception:
            _last_selection_reason = f"Invalid event_date format: {event_date}"
            return None

    # Group features by (relative_orbit, orbit_state)
    groups = {}
    for feature in features:
        orbit = _get_prop(feature, "sat:relative_orbit")
        direction = str(_get_prop(feature, "sat:orbit_state", "")).upper()
        dt_str = _get_prop(feature, "datetime")

        if orbit is None or not direction or not dt_str:
            continue

        dt_val = parse_dt(dt_str)
        if dt_val is None:
            continue

        key = (orbit, direction)
        if key not in groups:
            groups[key] = []
        groups[key].append(feature)

    if not groups:
        _last_selection_reason = "No features found with valid relative orbit and acquisition datetime in catalogue response."
        return None

    def _has_dual_pol(feature: Dict[Any, Any]) -> bool:
        pols = _get_prop(feature, "sar:polarizations") or _get_prop(feature, "polarization") or []
        if isinstance(pols, str):
            pols = [pols]
        pols_upper = [str(p).upper() for p in pols]
        return "DV" in pols_upper or ("VV" in pols_upper and "VH" in pols_upper)

    candidate_triplets = []

    for key, group_features in groups.items():
        # Sort features chronologically
        sorted_features = sorted(
            group_features,
            key=lambda f: parse_dt(_get_prop(f, "datetime"))
        )

        # Cluster by distinct acquisition pass (timestamps within 60s belong to the same datatake/pass)
        distinct_passes = []
        for f in sorted_features:
            f_dt = parse_dt(_get_prop(f, "datetime"))
            if not distinct_passes:
                distinct_passes.append(f)
            else:
                prev_dt = parse_dt(_get_prop(distinct_passes[-1], "datetime"))
                if abs((f_dt - prev_dt).total_seconds()) > 60:
                    distinct_passes.append(f)

        pre_events = [f for f in distinct_passes if parse_dt(_get_prop(f, "datetime")) < event_dt]
        post_events = [f for f in distinct_passes if parse_dt(_get_prop(f, "datetime")) >= event_dt]

        if len(pre_events) >= 2 and len(post_events) >= 1:
            pre_2 = pre_events[-2]
            pre_1 = pre_events[-1]
            post = post_events[0]

            dt_pre2 = parse_dt(_get_prop(pre_2, "datetime"))
            dt_pre1 = parse_dt(_get_prop(pre_1, "datetime"))
            dt_post = parse_dt(_get_prop(post, "datetime"))

            # Verify strictly distinct timestamps and monotonic ordering
            if dt_pre2 < dt_pre1 < event_dt <= dt_post:
                id_pre2 = pre_2.get("id")
                id_pre1 = pre_1.get("id")
                id_post = post.get("id")
                if id_pre2 != id_pre1 and id_pre1 != id_post:
                    # Preference scoring: dual-pol compatibility, then temporal closeness
                    dual_pol_score = (
                        (1 if _has_dual_pol(pre_2) else 0) +
                        (1 if _has_dual_pol(pre_1) else 0) +
                        (1 if _has_dual_pol(post) else 0)
                    )
                    # Gap between pre1 and post in days (smaller is better for change detection)
                    gap_days = abs((dt_post - dt_pre1).total_seconds()) / 86400.0

                    candidate_triplets.append({
                        "orbit": key[0],
                        "direction": key[1],
                        "pre_2": pre_2,
                        "pre_1": pre_1,
                        "post": post,
                        "dual_pol_score": dual_pol_score,
                        "gap_days": gap_days,
                        "num_pre": len(pre_events)
                    })

    if candidate_triplets:
        # Sort candidates: highest dual_pol_score first, then smallest temporal gap
        candidate_triplets.sort(key=lambda c: (-c["dual_pol_score"], c["gap_days"], -c["num_pre"]))
        best = candidate_triplets[0]
        _last_selection_reason = (
            f"Selected compatible triplet on relative orbit {best['orbit']} ({best['direction']}) "
            f"with 2 distinct pre-event scenes and 1 post-event scene."
        )
        return {
            "orbit": best["orbit"],
            "direction": best["direction"],
            "pre_2": best["pre_2"],
            "pre_1": best["pre_1"],
            "post": best["post"]
        }

    # If no valid triplet could be formed, diagnose the exact reason
    total_pre = sum(1 for f in features if parse_dt(_get_prop(f, "datetime")) and parse_dt(_get_prop(f, "datetime")) < event_dt)
    total_post = sum(1 for f in features if parse_dt(_get_prop(f, "datetime")) and parse_dt(_get_prop(f, "datetime")) >= event_dt)

    if total_post == 0:
        _last_selection_reason = (
            f"No post-event Sentinel-1 acquisitions found after {event_date}. "
            "At least 1 post-flood scene is required for change detection."
        )
    elif total_pre == 0:
        _last_selection_reason = (
            f"No pre-event Sentinel-1 acquisitions found before {event_date}. "
            "At least 2 distinct pre-flood scenes are required for ONNX model inference."
        )
    elif total_pre < 2:
        _last_selection_reason = (
            f"Insufficient pre-event acquisitions (found {total_pre}, requires 2 distinct pre-event scenes). "
            "Synthesizing or duplicating pre-event acquisitions is strictly rejected."
        )
    else:
        # Pre and post exist in catalog, but not on the same relative orbit
        orbit_summary = []
        for (orb, direct), grp in groups.items():
            pre_count = sum(1 for f in grp if parse_dt(_get_prop(f, "datetime")) < event_dt)
            post_count = sum(1 for f in grp if parse_dt(_get_prop(f, "datetime")) >= event_dt)
            orbit_summary.append(f"orbit {orb} ({direct}): {pre_count} pre, {post_count} post")
        _last_selection_reason = (
            f"No single relative orbit contains both >= 2 pre-event scenes and >= 1 post-event scene. "
            f"Orbit coverage: {'; '.join(orbit_summary)}."
        )

    return None
