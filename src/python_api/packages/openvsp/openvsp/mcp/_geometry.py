"""Geometry management, parameters, sets, and model I/O MCP tools."""

from __future__ import annotations

import json
from typing import Any

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# Version / info
# ===========================================================================


@mcp.tool()
def get_vsp_version() -> dict[str, Any]:
    """Return the OpenVSP version as a dict with major, minor, change, and full string."""
    try:
        vsp = _vsp()
        return {
            "version": vsp.GetVSPVersion(),
            "major": vsp.GetVSPVersionMajor(),
            "minor": vsp.GetVSPVersionMinor(),
            "change": vsp.GetVSPVersionChange(),
        }
    except Exception as exc:
        return {"error": str(exc)}


# ===========================================================================
# Model file I/O
# ===========================================================================


@mcp.tool()
def clear_model() -> str:
    """Clear the current VSP model, removing all geometry."""
    try:
        _vsp().ClearVSPModel()
        return "Model cleared."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def read_vsp_file(file_name: str) -> str:
    """
    Read a VSP model file (.vsp3) from disk and load it as the current model.

    Args:
        file_name: Absolute path to the .vsp3 file to read.
    """
    try:
        _vsp().ReadVSPFile(file_name)
        return f"Loaded '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def write_vsp_file(file_name: str, set_index: int = 0) -> str:
    """
    Write the current VSP model to a .vsp3 file.

    Args:
        file_name:  Absolute path for the output file.
        set_index:  Geometry set to export (0 = SET_ALL).
    """
    try:
        _vsp().WriteVSPFile(file_name, set_index)
        return f"Wrote model to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_vsp_filename() -> str:
    """Return the file name associated with the current VSP model."""
    try:
        return _vsp().GetVSPFileName()
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Geometry types
# ===========================================================================


@mcp.tool()
def get_geom_types() -> list[str]:
    """Return the list of geometry type names that can be added (e.g. 'WING', 'FUSELAGE', 'POD')."""
    try:
        return _vsp().GetGeomTypes()
    except Exception as exc:
        return [f"Error: {exc}"]


# ===========================================================================
# Geometry management
# ===========================================================================


@mcp.tool()
def find_geoms() -> list[str]:
    """Return the IDs of all geometry components in the current model."""
    try:
        return _vsp().FindGeoms()
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def find_geoms_with_name(name: str) -> list[str]:
    """
    Return the IDs of all geometry components whose name matches *name* exactly.

    Args:
        name: The geometry name to search for.
    """
    try:
        return _vsp().FindGeomsWithName(name)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def find_geom(name: str, index: int = 0) -> str:
    """
    Return the ID of the geometry component matching *name* at position *index*.

    Args:
        name:  Geometry name to search for.
        index: Index when multiple components share the same name (default 0).
    """
    try:
        return _vsp().FindGeom(name, index)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def add_geom(geom_type: str, parent_id: str = "") -> str:
    """
    Add a new geometry component to the model.

    Args:
        geom_type: Type string such as 'WING', 'FUSELAGE', 'POD', 'ELLIPSOID',
                   'STACK', 'CUSTOM', 'PROPELLER', 'BLANK', 'CONFORMAL', etc.
                   Use get_geom_types() to see all available types.
        parent_id: ID of the parent geometry (empty string for top-level).

    Returns:
        The ID string of the newly created geometry.
    """
    try:
        return _vsp().AddGeom(geom_type, parent_id)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_geom(geom_id: str) -> str:
    """
    Delete a geometry component from the model.

    Args:
        geom_id: ID of the geometry to delete.
    """
    try:
        _vsp().DeleteGeom(geom_id)
        return f"Deleted geometry '{geom_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_geom_name(geom_id: str) -> str:
    """
    Return the name of a geometry component.

    Args:
        geom_id: ID of the geometry.
    """
    try:
        return _vsp().GetGeomName(geom_id)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_geom_name(geom_id: str, name: str) -> str:
    """
    Set the name of a geometry component.

    Args:
        geom_id: ID of the geometry.
        name:    New name to assign.
    """
    try:
        _vsp().SetGeomName(geom_id, name)
        return f"Renamed geometry '{geom_id}' to '{name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_geom_type_name(geom_id: str) -> str:
    """
    Return the type name of a geometry component (e.g. 'Wing', 'Fuselage').

    Args:
        geom_id: ID of the geometry.
    """
    try:
        return _vsp().GetGeomTypeName(geom_id)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_geom_parent(geom_id: str) -> str:
    """
    Return the ID of the parent geometry, or an empty string if at the top level.

    Args:
        geom_id: ID of the geometry.
    """
    try:
        return _vsp().GetGeomParent(geom_id)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_geom_children(geom_id: str) -> list[str]:
    """
    Return the IDs of all direct children of a geometry component.

    Args:
        geom_id: ID of the geometry.
    """
    try:
        return _vsp().GetGeomChildren(geom_id)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_geom_parm_ids(geom_id: str) -> list[str]:
    """
    Return the parameter IDs belonging to a geometry component.

    Args:
        geom_id: ID of the geometry.
    """
    try:
        return _vsp().GetGeomParmIDs(geom_id)
    except Exception as exc:
        return [f"Error: {exc}"]


# ===========================================================================
# Parameters
# ===========================================================================


@mcp.tool()
def find_parm(container_id: str, parm_name: str, group_name: str) -> str:
    """
    Find a parameter ID by its container ID, parameter name, and group name.

    Args:
        container_id: ID of the geometry or manager that owns the parameter.
        parm_name:    Name of the parameter (e.g. 'Span', 'Chord', 'XLoc').
        group_name:   Group the parameter belongs to (e.g. 'WingGeom', 'XForm').

    Returns:
        The parameter ID string, or an empty string if not found.
    """
    try:
        return _vsp().FindParm(container_id, parm_name, group_name)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_parm_name(parm_id: str) -> str:
    """
    Return the name of a parameter.

    Args:
        parm_id: Parameter ID string.
    """
    try:
        return _vsp().GetParmName(parm_id)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_parm_val(parm_id: str) -> float:
    """
    Return the current value of a parameter by its ID.

    Args:
        parm_id: Parameter ID string obtained from find_parm() or get_geom_parm_ids().
    """
    try:
        return _vsp().GetParmVal(parm_id)
    except Exception as exc:
        return 0.0


@mcp.tool()
def get_parm_val_by_name(
    geom_id: str, parm_name: str, group_name: str
) -> float:
    """
    Return the current value of a parameter by geometry ID, parameter name, and group.

    Args:
        geom_id:    ID of the geometry that owns the parameter.
        parm_name:  Name of the parameter (e.g. 'Span').
        group_name: Group name (e.g. 'WingGeom').
    """
    try:
        return _vsp().GetParmVal(geom_id, parm_name, group_name)
    except Exception as exc:
        return 0.0


@mcp.tool()
def set_parm_val(parm_id: str, value: float) -> float:
    """
    Set a parameter to a new value by its ID.

    Args:
        parm_id: Parameter ID string.
        value:   New value to assign.

    Returns:
        The value that was actually set (may be clamped to limits).
    """
    try:
        return _vsp().SetParmVal(parm_id, value)
    except Exception as exc:
        return 0.0


@mcp.tool()
def set_parm_val_by_name(
    geom_id: str, parm_name: str, group_name: str, value: float
) -> float:
    """
    Set a parameter value by geometry ID, parameter name, and group name.

    Args:
        geom_id:    ID of the geometry that owns the parameter.
        parm_name:  Parameter name (e.g. 'Span').
        group_name: Group name (e.g. 'WingGeom').
        value:      New value to assign.

    Returns:
        The value that was actually set (may be clamped to limits).
    """
    try:
        return _vsp().SetParmVal(geom_id, parm_name, group_name, value)
    except Exception as exc:
        return 0.0


# ===========================================================================
# Model update
# ===========================================================================


@mcp.tool()
def update_model() -> str:
    """Trigger a recompute of the VSP model (propagates parameter changes to geometry)."""
    try:
        _vsp().Update()
        return "Model updated."
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Sets
# ===========================================================================


@mcp.tool()
def get_set_name(index: int) -> str:
    """
    Return the name of the geometry set at the given index.

    Args:
        index: Set index (0 = SET_ALL, 1 = SET_SHOWN, 2 = SET_NOT_SHOWN, 3+ user sets).
    """
    try:
        return _vsp().GetSetName(index)
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Geometry summary helper
# ===========================================================================


@mcp.tool()
def summarize_model() -> str:
    """
    Return a human-readable summary of all geometry in the current model,
    including each component's ID, name, and type.
    """
    try:
        vsp = _vsp()
        geom_ids = vsp.FindGeoms()
        if not geom_ids:
            return "The model is empty (no geometry components)."

        lines = [
            f"Model: {vsp.GetVSPFileName() or '(unsaved)'}",
            f"Components ({len(geom_ids)}):",
        ]
        for gid in geom_ids:
            name = vsp.GetGeomName(gid)
            gtype = vsp.GetGeomTypeName(gid)
            parent = vsp.GetGeomParent(gid)
            parent_info = f", parent={parent}" if parent else ""
            lines.append(f"  [{gtype}] {name}  (id={gid}{parent_info})")

        return "\n".join(lines)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_geom_parameters(geom_id: str) -> str:
    """
    Return a JSON-formatted summary of all parameters for a geometry component,
    including each parameter's ID, name, and current value.

    Args:
        geom_id: ID of the geometry to inspect.
    """
    try:
        vsp = _vsp()
        parm_ids = vsp.GetGeomParmIDs(geom_id)
        params: list[dict[str, Any]] = []
        for pid in parm_ids:
            try:
                params.append(
                    {
                        "id": pid,
                        "name": vsp.GetParmName(pid),
                        "value": vsp.GetParmVal(pid),
                    }
                )
            except Exception:
                pass
        return json.dumps(params, indent=2)
    except Exception as exc:
        return f"Error: {exc}"
