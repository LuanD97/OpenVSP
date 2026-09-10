"""Point cloud access and Fit Model (point-cloud-to-parametric fitting) MCP tools."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import Any

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# Helpers
# ===========================================================================


def _capture(fn) -> tuple[Any, list[dict[str, Any]]]:
    """
    Run *fn(vsp)* while capturing only the ``ErrorMgr`` entries it pushes.

    Silences engine error printing (so stdout, which carries the stdio
    transport, is never polluted), records the error-queue length before the
    call, then pops exactly the entries added during the call, oldest first.
    Errors already on the queue before the call are left alone.
    """
    vsp = _vsp()
    em = vsp.ErrorMgrSingleton.getInstance()
    em.SilenceErrors()
    base = em.GetNumTotalErrors()
    result = fn(vsp)
    num_new = max(0, em.GetNumTotalErrors() - base)
    popped = [em.PopLastError() for _ in range(num_new)]
    popped.reverse()  # PopLastError is LIFO; report oldest first.
    errors = [{"code": e.GetErrorCode(), "message": e.GetErrorString()} for e in popped]
    return result, errors


def _error(message: str, **extra: Any) -> dict[str, Any]:
    """Build an Error Result: ``{"error": message, **extra}``."""
    return {"error": message, **extra}


def _engine_failed(errors: list[dict[str, Any]], context: str) -> dict[str, Any] | None:
    """Return an Error Result joining *errors*' messages, or None if *errors* is empty."""
    if not errors:
        return None
    joined = "; ".join(e["message"] for e in errors)
    return _error(f"{context}: {joined}", vsp_errors=errors)


def _parse_fit_type(value: Any) -> tuple[int | None, str | None]:
    """Parse a `"FREE"`/`"FIXED"` string (case-insensitive) to a FIT_* code, or a reason."""
    vsp = _vsp()
    if isinstance(value, str):
        upper = value.upper()
        if upper == "FREE":
            return vsp.FIT_FREE, None
        if upper == "FIXED":
            return vsp.FIT_FIXED, None
    return None, f"must be 'FREE' or 'FIXED', got {value!r}"


def _fit_type_name(code: int) -> str:
    """Convert a FIT_* code back to `"FIXED"`/`"FREE"`."""
    return "FREE" if code == _vsp().FIT_FREE else "FIXED"


def _vec3_list(v: Any) -> list[float]:
    """Convert a vec3d object to a plain `[x, y, z]` list."""
    return [float(v.x()), float(v.y()), float(v.z())]


def _finite(*vals: Any) -> bool:
    """True if every value is a finite number. Non-numbers count as not finite."""
    try:
        return all(math.isfinite(v) for v in vals)
    except TypeError:
        return False


def _validate_target_spec(
    spec: dict[str, Any], position: int, geom_ids: set[str]
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Validate and normalise one target-point spec.

    Returns ``({point, geom_id, u, w, u_type, w_type}, None)`` on success, or
    ``(None, reason)`` naming the failing field.
    """
    for field in ("x", "y", "z", "geom_id"):
        if field not in spec:
            return None, f"missing required field '{field}'"

    x, y, z, geom_id = spec["x"], spec["y"], spec["z"], spec["geom_id"]
    if not _finite(x, y, z):
        return None, "x, y, z must be finite numbers"

    if geom_id not in geom_ids:
        return None, f"geom_id '{geom_id}' does not exist in the model"

    u = spec.get("u", 0.5)
    w = spec.get("w", 0.5)
    if not _finite(u) or not (0.0 <= u <= 1.0):
        return None, f"u must be within [0, 1], got {u!r}"
    if not _finite(w) or not (0.0 <= w <= 1.0):
        return None, f"w must be within [0, 1], got {w!r}"

    u_type, reason = _parse_fit_type(spec.get("u_type", "FREE"))
    if reason is not None:
        return None, f"u_type {reason}"
    w_type, reason = _parse_fit_type(spec.get("w_type", "FREE"))
    if reason is not None:
        return None, f"w_type {reason}"

    return (
        {
            "point": [float(x), float(y), float(z)],
            "geom_id": geom_id,
            "u": float(u),
            "w": float(w),
            "u_type": u_type,
            "w_type": w_type,
        },
        None,
    )


def _parm_geom_map(vsp: Any) -> dict[str, str]:
    """Map every parm ID to its owning geom ID by scanning `GetGeomParmIDs` (R9)."""
    parm_map: dict[str, str] = {}
    for geom_id in vsp.FindGeoms():
        for parm_id in vsp.GetGeomParmIDs(geom_id):
            parm_map[parm_id] = geom_id
    return parm_map


def _describe_var(vsp: Any, parm_id: str, parm_map: dict[str, str]) -> dict[str, Any]:
    """Describe one Fit Variable. Orphaned (invalid) vars report no name/group/value."""
    valid = bool(vsp.ValidParm(parm_id))
    geom_id = parm_map.get(parm_id)
    geom_name = vsp.GetGeomName(geom_id) if geom_id is not None else None
    if not valid:
        return {
            "parm_id": parm_id,
            "name": None,
            "group": None,
            "geom_id": geom_id,
            "geom_name": geom_name,
            "value": None,
            "valid": False,
        }
    return {
        "parm_id": parm_id,
        "name": vsp.GetParmName(parm_id),
        "group": vsp.GetParmGroupName(parm_id),
        "geom_id": geom_id,
        "geom_name": geom_name,
        "value": float(vsp.GetParmVal(parm_id)),
        "valid": True,
    }


def _list_vars(vsp: Any) -> list[dict[str, Any]]:
    """Describe every Fit Variable, in engine order."""
    parm_map = _parm_geom_map(vsp)
    return [_describe_var(vsp, parm_id, parm_map) for parm_id in vsp.GetFitModelVarIDs()]


def _describe_target(vsp: Any, index: int) -> dict[str, Any]:
    """Describe one Target Point (Target Point shape)."""
    point = vsp.GetFitModelTargetPt(index)
    uw = vsp.GetFitModelTargetUW(index)
    return {
        "index": index,
        "point": _vec3_list(point),
        "geom_id": vsp.GetFitModelTargetGeomID(index),
        "u": float(uw.x()),
        "w": float(uw.y()),
        "u_type": _fit_type_name(vsp.GetFitModelTargetUType(index)),
        "w_type": _fit_type_name(vsp.GetFitModelTargetWType(index)),
    }


def _dangling(vsp: Any) -> tuple[list[int], list[str]]:
    """
    Find dangling references before solving (R10).

    Returns ``(dangling_target_indices, dangling_var_ids)``: targets whose
    geom no longer exists, and variables whose parm no longer exists.
    """
    geom_ids = set(vsp.FindGeoms())
    dangling_targets = [
        i
        for i in range(vsp.GetNumFitModelTargetPts())
        if vsp.GetFitModelTargetGeomID(i) not in geom_ids
    ]
    dangling_vars = [
        parm_id for parm_id in vsp.GetFitModelVarIDs() if not vsp.ValidParm(parm_id)
    ]
    return dangling_targets, dangling_vars


_MAX_BATCH = 10000


def _add_target_batch(vsp: Any, specs: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Add a batch of target-point specs, all-or-nothing (R6).

    Pre-validates every spec in Python, then adds each through the engine.
    If any engine call fails, every target this call added is deleted
    (highest index first) so the setup is left unchanged.
    """
    if not specs:
        return _error("targets must not be empty")
    if len(specs) > _MAX_BATCH:
        return _error(f"batch of {len(specs)} exceeds the {_MAX_BATCH} target cap")

    geom_ids = set(vsp.FindGeoms())
    normalised: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for position, spec in enumerate(specs):
        norm, reason = _validate_target_spec(spec, position, geom_ids)
        if reason is not None:
            invalid.append({"position": position, "reason": reason})
        else:
            normalised.append(norm)
    if invalid:
        return _error("invalid target spec(s)", invalid=invalid)

    added_indices: list[int] = []
    invalid = []
    for position, norm in enumerate(normalised):
        pt = vsp.vec3d(*norm["point"])
        result, errors = _capture(
            lambda v, n=norm, p=pt: v.AddFitModelTargetPt(
                p, n["geom_id"], n["u"], n["u_type"], n["w"], n["w_type"]
            )
        )
        if errors or result is None or result < 0:
            reason = "; ".join(e["message"] for e in errors) if errors else "rejected by the engine"
            invalid.append({"position": position, "reason": reason})
            continue  # Keep going so every rejection is reported (R6).
        added_indices.append(result)

    if invalid:
        for idx in sorted(added_indices, reverse=True):
            vsp.DeleteFitModelTargetPt(idx)
        return _error("engine rejected target spec(s)", invalid=invalid)

    return {
        "count": len(added_indices),
        "first_index": added_indices[0],
        "last_index": added_indices[-1],
        "num_targets": vsp.GetNumFitModelTargetPts(),
    }


# ===========================================================================
# Point cloud
# ===========================================================================


@mcp.tool()
def import_point_cloud(file_name: str) -> dict[str, Any]:
    """
    Import a point cloud from a plain-text .pts file and add it as a PtCloud component.

    Step 1 of the fitting workflow (see the module contract for the full recommended
    order): import_point_cloud -> get_point_cloud_summary -> build/adjust geometry ->
    reset_fit_model -> add_fit_model_vars -> add_fit_model_targets[_from_cloud] ->
    fit_model_to_convergence -> write_vsp_file.

    Args:
        file_name: Absolute path to a plain-text file, one "x y z" point per line,
                   in model units.

    Returns:
        {geom_id, num_points} on success. An empty or missing file is an error
        naming the file, and no component is left behind.
    """
    try:
        vsp = _vsp()
        geom_id, errors = _capture(lambda v: v.ImportFile(file_name, v.IMPORT_PTS, ""))
        failed = _engine_failed(errors, "import_point_cloud")
        if failed is not None:
            return failed
        if not geom_id or geom_id == "NONE":
            return _error(f"failed to import point cloud from '{file_name}'")

        num_points = len(vsp.GetPtCloudPnts(geom_id))
        if num_points == 0:
            vsp.DeleteGeom(geom_id)
            return _error(f"'{file_name}' contains no points")

        return {"geom_id": geom_id, "num_points": num_points}
    except Exception as exc:
        return {"error": str(exc)}


def _cloud_points(vsp: Any, cloud_id: str) -> list[tuple[float, float, float]]:
    """Return the `(x, y, z)` points of a PtCloud component, validating its type."""
    if vsp.GetGeomTypeName(cloud_id) != "PtCloud":
        raise ValueError(f"'{cloud_id}' is not a point cloud")
    return [(p.x(), p.y(), p.z()) for p in vsp.GetPtCloudPnts(cloud_id)]


@mcp.tool()
def get_point_cloud_summary(cloud_id: str) -> dict[str, Any]:
    """
    Summarise a point cloud: point count, bounding box, and centroid. No coordinates.

    Step 2 of the fitting workflow, right after import_point_cloud, so an agent
    can see roughly where the cloud sits before building or adjusting geometry.

    Args:
        cloud_id: ID of a PtCloud component (from import_point_cloud).

    Returns:
        {geom_id, num_points, bbox_min, bbox_max, centroid}, all in model units.
    """
    try:
        vsp = _vsp()
        points = _cloud_points(vsp, cloud_id)
        if not points:
            return {
                "geom_id": cloud_id,
                "num_points": 0,
                "bbox_min": None,
                "bbox_max": None,
                "centroid": None,
            }
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]
        n = len(points)
        return {
            "geom_id": cloud_id,
            "num_points": n,
            "bbox_min": [min(xs), min(ys), min(zs)],
            "bbox_max": [max(xs), max(ys), max(zs)],
            "centroid": [sum(xs) / n, sum(ys) / n, sum(zs) / n],
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def get_point_cloud_points(
    cloud_id: str, start: int = 0, count: int = 1000, stride: int = 1
) -> dict[str, Any]:
    """
    Page through a point cloud's raw coordinates (model units). Never returns
    more than 1000 points per call; page with `next_start` for larger clouds.

    Args:
        cloud_id: ID of a PtCloud component.
        start:    Index of the first point to return (default 0).
        count:    Number of points to return, clamped to [1, 1000] (default 1000).
        stride:   Keep every Nth point starting at *start* (default 1).

    Returns:
        {total, start, stride, returned, next_start, points}, points as
        [x, y, z] in model units. next_start is null when there is nothing
        left to page.
    """
    try:
        vsp = _vsp()
        points = _cloud_points(vsp, cloud_id)
        total = len(points)
        if not (0 <= start < total) and total > 0:
            return _error(f"start {start} is out of range [0, {total})")
        if stride < 1:
            return _error(f"stride must be >= 1, got {stride}")
        count = max(1, min(count, 1000))

        selected = points[start::stride][:count]
        last_taken = start + (len(selected) - 1) * stride if selected else start
        next_index = last_taken + stride
        next_start = next_index if next_index < total else None

        return {
            "total": total,
            "start": start,
            "stride": stride,
            "returned": len(selected),
            "next_start": next_start,
            "points": [list(p) for p in selected],
        }
    except Exception as exc:
        return {"error": str(exc)}


# ===========================================================================
# Setup state
# ===========================================================================


@mcp.tool()
def reset_fit_model() -> dict[str, Any]:
    """
    Clear the Fit Model setup entirely: variables, targets, and the cached distance.

    Step 4 of the fitting workflow, after building or adjusting geometry and
    before add_fit_model_vars, so a fresh setup never mixes with a stale one.
    """
    try:
        vsp = _vsp()
        vsp.ResetFitModel()
        return {
            "num_vars": vsp.GetNumFitModelVars(),
            "num_targets": vsp.GetNumFitModelTargetPts(),
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def clear_fit_model_vars() -> dict[str, Any]:
    """Clear only the Fit Model variables (e.g. to re-pick them), leaving targets in place."""
    try:
        vsp = _vsp()
        vsp.ClearFitModelVars()
        return {
            "num_vars": vsp.GetNumFitModelVars(),
            "num_targets": vsp.GetNumFitModelTargetPts(),
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def clear_fit_model_targets() -> dict[str, Any]:
    """Clear only the Fit Model target points (e.g. to re-select a region), leaving variables in place."""
    try:
        vsp = _vsp()
        vsp.ClearFitModelTargetPts()
        return {
            "num_vars": vsp.GetNumFitModelVars(),
            "num_targets": vsp.GetNumFitModelTargetPts(),
        }
    except Exception as exc:
        return {"error": str(exc)}


# ===========================================================================
# Variables
# ===========================================================================


_MAX_VARS = 1000


@mcp.tool()
def add_fit_model_vars(parm_ids: list[str]) -> dict[str, Any]:
    """
    Add one or more parameters as Fit Model variables the optimizer may change.

    Step 5 of the fitting workflow, after reset_fit_model and before adding
    targets. All-or-nothing: every ID must pass ValidParm and not already be
    a variable (in the model or within this list), or nothing is added.

    Args:
        parm_ids: 1-1000 parameter IDs (from get_geom_parm_ids() or find_parm()).

    Returns:
        {added, vars} on success, or an error with `invalid` entries naming each
        bad ID and why.
    """
    try:
        vsp = _vsp()
        if not parm_ids:
            return _error("parm_ids must not be empty")
        if len(parm_ids) > _MAX_VARS:
            return _error(f"{len(parm_ids)} parm_ids exceeds the {_MAX_VARS} cap")

        existing = set(vsp.GetFitModelVarIDs())
        invalid: list[dict[str, Any]] = []
        seen: set[str] = set()
        for position, parm_id in enumerate(parm_ids):
            if not vsp.ValidParm(parm_id):
                invalid.append({"position": position, "reason": f"'{parm_id}' is not a valid parm"})
            elif parm_id in existing:
                invalid.append({"position": position, "reason": f"'{parm_id}' is already a Fit Model variable"})
            elif parm_id in seen:
                invalid.append({"position": position, "reason": f"'{parm_id}' is duplicated in this request"})
            else:
                seen.add(parm_id)
        if invalid:
            return _error("invalid parm_id(s)", invalid=invalid)

        added: list[str] = []
        for parm_id in parm_ids:
            result, errors = _capture(lambda v, p=parm_id: v.AddFitModelVar(p))
            if errors or not result:
                for added_id in reversed(added):
                    vsp.DeleteFitModelVar(added_id)
                failed = _engine_failed(errors, f"add_fit_model_vars('{parm_id}')")
                return failed if failed is not None else _error(f"engine rejected parm '{parm_id}'")
            added.append(parm_id)

        return {"added": len(added), "vars": _list_vars(vsp)}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def delete_fit_model_var(parm_id: str) -> dict[str, Any]:
    """
    Remove a parameter from the Fit Model variable list.

    Args:
        parm_id: ID of the variable to remove.
    """
    try:
        vsp = _vsp()
        _, errors = _capture(lambda v: v.DeleteFitModelVar(parm_id))
        failed = _engine_failed(errors, f"delete_fit_model_var('{parm_id}')")
        if failed is not None:
            return failed
        return {"num_vars": vsp.GetNumFitModelVars()}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def list_fit_model_vars() -> dict[str, Any]:
    """List every current Fit Model variable, in engine order."""
    try:
        vsp = _vsp()
        vars_list = _list_vars(vsp)
        return {"num_vars": len(vars_list), "vars": vars_list}
    except Exception as exc:
        return {"error": str(exc)}


# ===========================================================================
# Targets
# ===========================================================================


@mcp.tool()
def get_fit_model_target(index: int) -> dict[str, Any]:
    """
    Return one target point by its index. Its `point` is [x, y, z] in model units.

    Args:
        index: Position in the target list, 0-based.
    """
    try:
        vsp = _vsp()
        num_targets = vsp.GetNumFitModelTargetPts()
        if not (0 <= index < num_targets):
            return _error(f"index {index} is out of range [0, {num_targets})")
        return _describe_target(vsp, index)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def list_fit_model_targets(start: int = 0, count: int = 1000) -> dict[str, Any]:
    """
    Page through the current target points (each `point` is [x, y, z] in model
    units). Never returns more than 1000 entries per call; page with
    `next_start` for more.

    Args:
        start: Index of the first target to return (default 0).
        count: Number of targets to return, clamped to [1, 1000] (default 1000).
    """
    try:
        vsp = _vsp()
        if start < 0:
            return _error(f"start must be >= 0, got {start}")
        total = vsp.GetNumFitModelTargetPts()
        count = max(1, min(count, 1000))
        end = min(start + count, total)
        targets = [_describe_target(vsp, i) for i in range(start, end)] if start < total else []
        next_start = end if end < total else None
        return {
            "total": total,
            "start": start,
            "returned": len(targets),
            "next_start": next_start,
            "targets": targets,
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def update_fit_model_target(
    index: int,
    x: float | None = None,
    y: float | None = None,
    z: float | None = None,
    geom_id: str | None = None,
    u: float | None = None,
    w: float | None = None,
    u_type: str | None = None,
    w_type: str | None = None,
) -> dict[str, Any]:
    """
    Update one or more fields of an existing target point. Omitted fields keep
    their current values.

    Args:
        index:   Position of the target to update.
        x, y, z: New coordinates in model units (all three are read from the
                 current point if any is omitted).
        geom_id: New owning component ID.
        u, w:    New parametric coordinates, within [0, 1].
        u_type, w_type: New "FREE"/"FIXED" fixity.
    """
    try:
        vsp = _vsp()
        num_targets = vsp.GetNumFitModelTargetPts()
        if not (0 <= index < num_targets):
            return _error(f"index {index} is out of range [0, {num_targets})")

        current = _describe_target(vsp, index)
        spec = {
            "x": current["point"][0] if x is None else x,
            "y": current["point"][1] if y is None else y,
            "z": current["point"][2] if z is None else z,
            "geom_id": current["geom_id"] if geom_id is None else geom_id,
            "u": current["u"] if u is None else u,
            "w": current["w"] if w is None else w,
            "u_type": current["u_type"] if u_type is None else u_type,
            "w_type": current["w_type"] if w_type is None else w_type,
        }
        normalised, reason = _validate_target_spec(spec, index, set(vsp.FindGeoms()))
        if reason is not None:
            return _error(reason)

        pt = vsp.vec3d(*normalised["point"])
        _, errors = _capture(
            lambda v: v.SetFitModelTargetPt(
                index, pt, normalised["geom_id"], normalised["u"], normalised["u_type"],
                normalised["w"], normalised["w_type"],
            )
        )
        failed = _engine_failed(errors, f"update_fit_model_target({index})")
        if failed is not None:
            return failed

        return {
            "index": index,
            "point": normalised["point"],
            "geom_id": normalised["geom_id"],
            "u": normalised["u"],
            "w": normalised["w"],
            "u_type": _fit_type_name(normalised["u_type"]),
            "w_type": _fit_type_name(normalised["w_type"]),
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def delete_fit_model_target(index: int) -> dict[str, Any]:
    """
    Delete one target point. Every later index shifts down by one.

    Args:
        index: Position of the target to delete.
    """
    try:
        vsp = _vsp()
        _, errors = _capture(lambda v: v.DeleteFitModelTargetPt(index))
        failed = _engine_failed(errors, f"delete_fit_model_target({index})")
        if failed is not None:
            return failed
        return {"num_targets": vsp.GetNumFitModelTargetPts()}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def add_fit_model_targets_from_cloud(
    cloud_id: str,
    geom_id: str,
    bbox_min: list[float],
    bbox_max: list[float],
    stride: int = 1,
    u_type: str = "FREE",
    w_type: str = "FREE",
) -> dict[str, Any]:
    """
    Turn every cloud point inside an axis-aligned box into a target on *geom_id*.

    Selects existing cloud points and does no projection: it only filters which
    coordinates become targets (u/w still default to 0.5 and are matched to the
    surface by search_fit_model_target_uw / fit_model_to_convergence). No point
    coordinates pass through the caller or appear in the result.

    Args:
        cloud_id:  ID of a PtCloud component (from import_point_cloud).
        geom_id:   ID of the component the new targets constrain.
        bbox_min:  [x, y, z] lower corner of the selection box (inclusive),
                   in model units.
        bbox_max:  [x, y, z] upper corner of the selection box (inclusive),
                   in model units. Must be >= bbox_min on every axis.
        stride:    Keep every Nth matching point in cloud order (default 1).
        u_type:    "FREE" or "FIXED" for every new target's u (default "FREE").
        w_type:    "FREE" or "FIXED" for every new target's w (default "FREE").

    Returns:
        {matched, count, first_index, last_index, num_targets} on success (no
        coordinates). 0 matches, more than 10,000 selected, or stride < 1 is an
        error.
    """
    try:
        vsp = _vsp()
        if len(bbox_min) != 3 or len(bbox_max) != 3:
            return _error("bbox_min and bbox_max must each have 3 elements")
        if not _finite(*bbox_min, *bbox_max):
            return _error("bbox_min and bbox_max must be finite")
        if any(bbox_min[i] > bbox_max[i] for i in range(3)):
            return _error(f"bbox_min {bbox_min} must be <= bbox_max {bbox_max} on every axis")
        if stride < 1:
            return _error(f"stride must be >= 1, got {stride}")
        # Check the arguments shared by every selected point once here, so a bad
        # value is one error rather than one `invalid` entry per point.
        if geom_id not in set(vsp.FindGeoms()):
            return _error(f"geom_id '{geom_id}' does not exist in the model")
        for name, value in (("u_type", u_type), ("w_type", w_type)):
            _, reason = _parse_fit_type(value)
            if reason is not None:
                return _error(f"{name} {reason}")

        points = _cloud_points(vsp, cloud_id)
        matched = [
            p
            for p in points
            if bbox_min[0] <= p[0] <= bbox_max[0]
            and bbox_min[1] <= p[1] <= bbox_max[1]
            and bbox_min[2] <= p[2] <= bbox_max[2]
        ]
        if not matched:
            return _error(f"no cloud points fall within box {bbox_min} .. {bbox_max}")

        selected = matched[::stride]
        if not selected:
            return _error(f"no cloud points fall within box {bbox_min} .. {bbox_max}")
        if len(selected) > _MAX_BATCH:
            return _error(
                f"{len(selected)} selected points exceed the {_MAX_BATCH} target cap",
                matched=len(matched),
                selected=len(selected),
            )

        specs = [
            {"x": p[0], "y": p[1], "z": p[2], "geom_id": geom_id, "u_type": u_type, "w_type": w_type}
            for p in selected
        ]
        result = _add_target_batch(vsp, specs)
        if "error" in result:
            return result
        return {"matched": len(matched), **result}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def add_fit_model_targets(targets: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Add one or more target points the fitted surface should pass through.

    Step 6 of the fitting workflow, after add_fit_model_vars and before
    fit_model_to_convergence. All-or-nothing (1-10,000 entries): every entry
    is validated, then added through the engine; any rejection rolls the
    whole batch back. This call does not match targets to the surface -- run
    search_fit_model_target_uw (or fit_model_to_convergence) afterward.

    Args:
        targets: list of {x, y, z, geom_id, u?, w?, u_type?, w_type?}, x/y/z
                 in model units. u/w default to 0.5 and must be within
                 [0, 1]; u_type/w_type default to "FREE" ("FREE" or "FIXED",
                 case-insensitive).

    Returns:
        {count, first_index, last_index, num_targets} on success, or an error
        with `invalid: [{position, reason}]`.
    """
    try:
        vsp = _vsp()
        return _add_target_batch(vsp, targets)
    except Exception as exc:
        return {"error": str(exc)}


# ===========================================================================
# Solving
# ===========================================================================


_INFO_MEANINGS = {
    0: "Improper input, or rejected by an engine precondition (see vsp_errors)",
    1: "Converged: relative reduction in the sum of squares is within tolerance",
    2: "Converged: relative change in the parameters is within tolerance",
    3: "Converged: both relative reduction and relative parameter change are within tolerance",
    4: "Residuals are orthogonal to the Jacobian columns (stationary point)",
    5: "Stopped: function evaluation limit reached",
    6: "Stopped: tolerance too small, no further reduction in the sum of squares possible",
    7: "Stopped: tolerance too small, no further improvement in the parameters possible",
}


def _dangling_error(vsp: Any) -> dict[str, Any] | None:
    """Return an Error Result if any target or variable is dangling (R10), else None."""
    dangling_targets, dangling_vars = _dangling(vsp)
    if not dangling_targets and not dangling_vars:
        return None
    return _error(
        "the Fit Model setup has dangling references; resolve them before solving",
        dangling_target_indices=dangling_targets,
        dangling_var_ids=dangling_vars,
    )


@mcp.tool()
def search_fit_model_target_uw() -> dict[str, Any]:
    """
    Match every target point to its nearest (u, w) on its component's surface.

    Run after adding targets and before measuring distance or optimizing
    (fit_model_to_convergence does this automatically each pass). Rejects
    with `dangling_target_indices`/`dangling_var_ids` if any reference is
    stale (R10), without calling the engine.
    """
    try:
        vsp = _vsp()
        failed = _dangling_error(vsp)
        if failed is not None:
            return failed
        _, errors = _capture(lambda v: v.SearchFitModelTargetUW())
        failed = _engine_failed(errors, "search_fit_model_target_uw")
        if failed is not None:
            return failed
        return {"num_targets": vsp.GetNumFitModelTargetPts()}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def refine_fit_model_target_uw() -> dict[str, Any]:
    """Locally refine each target's matched (u, w) (run after search_fit_model_target_uw)."""
    try:
        vsp = _vsp()
        failed = _dangling_error(vsp)
        if failed is not None:
            return failed
        _, errors = _capture(lambda v: v.RefineFitModelTargetUW())
        failed = _engine_failed(errors, "refine_fit_model_target_uw")
        if failed is not None:
            return failed
        return {"num_targets": vsp.GetNumFitModelTargetPts()}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def update_fit_model_distance() -> dict[str, Any]:
    """
    Recompute the RMS distance (model units) between targets and the current
    surface. With 0 targets, returns {rms: 0.0, num_targets: 0} without an
    engine call (R11), rather than the engine's "No target points" error.
    """
    try:
        vsp = _vsp()
        if vsp.GetNumFitModelTargetPts() == 0:
            return {"rms": 0.0, "num_targets": 0}
        failed = _dangling_error(vsp)
        if failed is not None:
            return failed
        rms, errors = _capture(lambda v: v.UpdateFitModelDistance())
        failed = _engine_failed(errors, "update_fit_model_distance")
        if failed is not None:
            return failed
        return {"rms": float(rms), "num_targets": vsp.GetNumFitModelTargetPts()}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def get_fit_model_distance() -> dict[str, Any]:
    """
    Return the cached RMS distance (model units) from the last
    update_fit_model_distance/optimize_fit_model/fit_model_to_convergence
    call. Does not recompute.
    """
    try:
        vsp = _vsp()
        return {
            "rms": float(vsp.GetFitModelDistance()),
            "num_targets": vsp.GetNumFitModelTargetPts(),
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def optimize_fit_model() -> dict[str, Any]:
    """
    Run one Levenberg-Marquardt optimization pass against the current target matches.

    One pass solves against frozen target-to-surface matches and can stop short
    when the model starts far from the scan. Prefer fit_model_to_convergence,
    which is step 7 of the fitting workflow and repeats search/refine/optimize
    until the fit stops improving.

    Returns:
        {info, info_meaning, rms_before, rms_after, vars}.
    """
    try:
        vsp = _vsp()
        failed = _dangling_error(vsp)
        if failed is not None:
            return failed

        def _run(v):
            before = v.UpdateFitModelDistance()
            code = v.OptimizeFitModel()
            after = v.GetFitModelDistance()
            return before, code, after

        (rms_before, info, rms_after), errors = _capture(_run)
        failed = _engine_failed(errors, "optimize_fit_model")
        if failed is not None:
            return failed

        return {
            "info": info,
            "info_meaning": _INFO_MEANINGS.get(info, "Unknown info code"),
            "rms_before": float(rms_before),
            "rms_after": float(rms_after),
            "vars": _list_vars(vsp),
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def fit_model_to_convergence(
    max_passes: int = 10, tolerance: float = 1e-6, refine: bool = True
) -> dict[str, Any]:
    """
    Fit the model to its current targets, repeating search/refine/optimize passes
    until the RMS distance stops improving.

    Step 7 of the fitting workflow, after adding targets and before
    write_vsp_file. This is the recommended fitting tool: a single
    optimize_fit_model pass solves against target-to-surface matches that
    were frozen when it started, and can stop short when the model starts
    far from the scan (see optimize_fit_model). This loop re-matches targets
    each pass and keeps going until convergence.

    Args:
        max_passes: Maximum passes to run, 1-100 (default 10).
        tolerance:  Stop when the relative RMS improvement falls below this,
                    must be > 0 (default 1e-6).
        refine:     Run refine_fit_model_target_uw after each search (default True).

    Returns:
        {passes, stop_reason, rms_history, rms_initial, rms_final, vars}.
        stop_reason is one of "converged", "no_improvement", "pass_limit", "error".
        On "error", also includes `error` and `vsp_errors`.
    """
    try:
        vsp = _vsp()
        if not (1 <= max_passes <= 100):
            return _error(f"max_passes must be within [1, 100], got {max_passes}")
        if not (tolerance > 0):
            return _error(f"tolerance must be > 0, got {tolerance}")

        failed = _dangling_error(vsp)
        if failed is not None:
            return failed

        rms_history: list[dict[str, Any]] = []
        rms_initial: float | None = None
        prev_rms: float | None = None
        stop_reason = "pass_limit"
        error_result: dict[str, Any] | None = None

        for pass_num in range(1, max_passes + 1):

            def _run(v):
                v.SearchFitModelTargetUW()
                if refine:
                    v.RefineFitModelTargetUW()
                before = v.UpdateFitModelDistance()
                code = v.OptimizeFitModel()
                after = v.GetFitModelDistance()
                return before, code, after

            (rms_before, info, rms_after), errors = _capture(_run)
            if rms_initial is None:
                rms_initial = rms_before
            if prev_rms is None:
                prev_rms = rms_before

            if errors:
                failed = _engine_failed(errors, f"fit_model_to_convergence (pass {pass_num})")
                error_result = {
                    **failed,
                    "passes": pass_num - 1,
                    "stop_reason": "error",
                    "rms_history": rms_history,
                    "rms_initial": rms_initial,
                    "rms_final": prev_rms,
                    "vars": _list_vars(vsp),
                }
                stop_reason = "error"
                break

            rms_history.append(
                {"pass": pass_num, "rms_before": float(rms_before), "rms_after": float(rms_after), "info": info}
            )

            if rms_after == 0:
                stop_reason = "converged"
            else:
                rel_impr = (prev_rms - rms_after) / prev_rms if prev_rms else 0.0
                if 0 <= rel_impr < tolerance:
                    stop_reason = "converged"
                elif rms_after > prev_rms:
                    stop_reason = "no_improvement"
                else:
                    stop_reason = "pass_limit"  # provisional; loop continues unless last pass

            prev_rms = rms_after

            if stop_reason in ("converged", "no_improvement"):
                break
            if pass_num == max_passes:
                stop_reason = "pass_limit"
                break

        if error_result is not None:
            return error_result

        return {
            "passes": len(rms_history),
            "stop_reason": stop_reason,
            "rms_history": rms_history,
            "rms_initial": float(rms_initial) if rms_initial is not None else 0.0,
            "rms_final": float(prev_rms) if prev_rms is not None else 0.0,
            "vars": _list_vars(vsp),
        }
    except Exception as exc:
        return {"error": str(exc)}


# ===========================================================================
# Persistence
# ===========================================================================


def _fit_file_parm_ids(path: str) -> list[str]:
    """Read every `Variable/ParmID` from a `.fit` XML file. Returns [] on a parse error."""
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return []
    return [
        parm_id.text
        for parm_id in tree.getroot().findall("./Variable/ParmID")
        if parm_id.text
    ]


@mcp.tool()
def save_fit_model(file_name: str) -> dict[str, Any]:
    """
    Save the current Fit Model setup (variables and targets) to a .fit file.

    This saves the fitting *setup* for reuse across sessions -- it is
    separate from the model geometry, which write_vsp_file saves to .vsp3.

    Args:
        file_name: Absolute path for the output .fit file.
    """
    try:
        vsp = _vsp()
        ok, errors = _capture(lambda v: v.SaveFitModel(file_name))
        failed = _engine_failed(errors, "save_fit_model")
        if failed is not None:
            return failed
        if not ok:
            return _error(f"failed to save Fit Model setup to '{file_name}'")
        return {
            "file_name": file_name,
            "num_vars": vsp.GetNumFitModelVars(),
            "num_targets": vsp.GetNumFitModelTargetPts(),
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def load_fit_model(file_name: str, append: bool = False) -> dict[str, Any]:
    """
    Load a Fit Model setup (variables and targets) from a .fit file.

    Unresolved references are reported rather than silently dropped: variables
    in the file that no longer exist in the model, and targets whose component
    no longer exists. Use this to resume a setup saved by save_fit_model, not
    to load model geometry (see read_vsp_file for .vsp3 files).

    Args:
        file_name: Absolute path to the .fit file.
        append:    If True, add to the current setup instead of replacing it
                   (default False).
    """
    try:
        vsp = _vsp()
        _, errors = _capture(lambda v: v.LoadFitModel(file_name, not append))
        failed = _engine_failed(errors, "load_fit_model")
        if failed is not None:
            return failed

        file_parm_ids = _fit_file_parm_ids(file_name)
        current_vars = set(vsp.GetFitModelVarIDs())
        missing_parm_ids = [p for p in file_parm_ids if p not in current_vars]
        dangling_targets, _dangling_vars = _dangling(vsp)

        num_vars = vsp.GetNumFitModelVars()
        num_targets = vsp.GetNumFitModelTargetPts()
        if missing_parm_ids or dangling_targets:
            return _error(
                "the Fit Model setup was loaded without some unresolved references",
                missing_parm_ids=missing_parm_ids,
                dangling_target_indices=dangling_targets,
                num_vars=num_vars,
                num_targets=num_targets,
            )
        return {"num_vars": num_vars, "num_targets": num_targets}
    except Exception as exc:
        return {"error": str(exc)}
