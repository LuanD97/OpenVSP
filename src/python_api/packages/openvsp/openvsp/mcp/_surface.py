"""Surface query and geometry interrogation MCP tools."""
from __future__ import annotations

from typing import Any

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# Surface Query / Geometry Interrogation
# ===========================================================================

def _vec3d_to_dict(v: Any) -> dict[str, float]:
    """Convert a VSP vec3d object to a plain dict."""
    return {"x": float(v.x()), "y": float(v.y()), "z": float(v.z())}


@mcp.tool()
def get_geom_bbox_min(
    geom_id: str, surf_index: int = 0, absolute: bool = True
) -> dict[str, float]:
    """
    Return the minimum corner of the bounding box of a geometry surface.

    Args:
        geom_id:    ID of the geometry.
        surf_index: Surface index (default 0).
        absolute:   If True, coordinates are in the absolute (world) frame;
                    if False, in the geometry's local frame.

    Returns:
        Dict with keys ``x``, ``y``, ``z``.
    """
    try:
        return _vec3d_to_dict(_vsp().GetGeomBBoxMin(geom_id, surf_index, absolute))
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def get_geom_bbox_max(
    geom_id: str, surf_index: int = 0, absolute: bool = True
) -> dict[str, float]:
    """
    Return the maximum corner of the bounding box of a geometry surface.

    Args:
        geom_id:    ID of the geometry.
        surf_index: Surface index (default 0).
        absolute:   If True, coordinates are in the absolute (world) frame.

    Returns:
        Dict with keys ``x``, ``y``, ``z``.
    """
    try:
        return _vec3d_to_dict(_vsp().GetGeomBBoxMax(geom_id, surf_index, absolute))
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def comp_pnt01(
    geom_id: str, surf_index: int, u: float, w: float
) -> dict[str, float]:
    """
    Compute the 3D point on a geometry surface at parametric coordinates (u, w).

    Both u and w are normalized to [0, 1].

    Args:
        geom_id:    ID of the geometry.
        surf_index: Surface index.
        u:          Parametric coordinate in the chordwise/length direction [0, 1].
        w:          Parametric coordinate in the spanwise/circumferential direction [0, 1].

    Returns:
        Dict with keys ``x``, ``y``, ``z``.
    """
    try:
        return _vec3d_to_dict(_vsp().CompPnt01(geom_id, surf_index, u, w))
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def comp_norm01(
    geom_id: str, surf_index: int, u: float, w: float
) -> dict[str, float]:
    """
    Compute the surface normal vector at parametric coordinates (u, w).

    Args:
        geom_id:    ID of the geometry.
        surf_index: Surface index.
        u:          Parametric u coordinate [0, 1].
        w:          Parametric w coordinate [0, 1].

    Returns:
        Dict with keys ``x``, ``y``, ``z`` (unit normal vector).
    """
    try:
        return _vec3d_to_dict(_vsp().CompNorm01(geom_id, surf_index, u, w))
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def comp_tan_u01(
    geom_id: str, surf_index: int, u: float, w: float
) -> dict[str, float]:
    """
    Compute the surface tangent vector in the u direction at (u, w).

    Args:
        geom_id:    ID of the geometry.
        surf_index: Surface index.
        u:          Parametric u coordinate [0, 1].
        w:          Parametric w coordinate [0, 1].

    Returns:
        Dict with keys ``x``, ``y``, ``z``.
    """
    try:
        return _vec3d_to_dict(_vsp().CompTanU01(geom_id, surf_index, u, w))
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def comp_tan_w01(
    geom_id: str, surf_index: int, u: float, w: float
) -> dict[str, float]:
    """
    Compute the surface tangent vector in the w direction at (u, w).

    Args:
        geom_id:    ID of the geometry.
        surf_index: Surface index.
        u:          Parametric u coordinate [0, 1].
        w:          Parametric w coordinate [0, 1].

    Returns:
        Dict with keys ``x``, ``y``, ``z``.
    """
    try:
        return _vec3d_to_dict(_vsp().CompTanW01(geom_id, surf_index, u, w))
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def proj_pnt01(
    geom_id: str, surf_index: int, x: float, y: float, z: float
) -> dict[str, Any]:
    """
    Project a 3D point onto a geometry surface and return the closest point.

    Args:
        geom_id:    ID of the geometry.
        surf_index: Surface index.
        x:          X coordinate of the point to project.
        y:          Y coordinate of the point to project.
        z:          Z coordinate of the point to project.

    Returns:
        Dict with keys ``dist`` (closest distance), ``u``, ``w`` (parametric
        coordinates of the closest point on the surface).
    """
    try:
        vsp = _vsp()
        pt = vsp.vec3d(x, y, z)
        dist, u_out, w_out = vsp.ProjPnt01(geom_id, surf_index, pt)
        return {"dist": float(dist), "u": float(u_out), "w": float(w_out)}
    except Exception as exc:
        return {"error": str(exc)}
