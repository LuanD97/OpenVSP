"""XSec, Airfoil, and Sub-Surface MCP tools."""
from __future__ import annotations

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# XSecSurf / XSec / Airfoil
# ===========================================================================

@mcp.tool()
def get_num_xsec_surfs(geom_id: str) -> int:
    """
    Return the number of XSecSurf objects on a geometry component.

    Args:
        geom_id: ID of the geometry.
    """
    try:
        return _vsp().GetNumXSecSurfs(geom_id)
    except Exception as exc:
        return -1


@mcp.tool()
def get_xsec_surf(geom_id: str, index: int = 0) -> str:
    """
    Return the ID of an XSecSurf object on a geometry component.

    Args:
        geom_id: ID of the geometry.
        index:   XSecSurf index (most geoms have exactly one, at index 0).
    """
    try:
        return _vsp().GetXSecSurf(geom_id, index)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_num_xsec(xsec_surf_id: str) -> int:
    """
    Return the number of cross-sections (XSecs) in an XSecSurf.

    Args:
        xsec_surf_id: ID of the XSecSurf (from get_xsec_surf()).
    """
    try:
        return _vsp().GetNumXSec(xsec_surf_id)
    except Exception as exc:
        return -1


@mcp.tool()
def get_xsec(xsec_surf_id: str, xsec_index: int) -> str:
    """
    Return the ID of a cross-section in an XSecSurf by index.

    Args:
        xsec_surf_id: ID of the XSecSurf.
        xsec_index:   Zero-based index of the XSec.
    """
    try:
        return _vsp().GetXSec(xsec_surf_id, xsec_index)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def insert_xsec(geom_id: str, index: int, xsec_type: str) -> str:
    """
    Insert a new cross-section into a geometry at the given index.

    Args:
        geom_id:    ID of the geometry.
        index:      Position at which to insert the new XSec.
        xsec_type:  XSec shape type constant name, e.g. ``'XS_CIRCLE'``,
                    ``'XS_ELLIPSE'``, ``'XS_FOUR_SERIES'``, ``'XS_FILE_AIRFOIL'``,
                    ``'XS_GENERAL_FUSE'``, ``'XS_SUPER_ELLIPSE'``,
                    ``'XS_ROUNDED_RECTANGLE'``, ``'XS_POINT'``.

    Returns:
        The ID of the newly created XSec, or an empty string.
    """
    try:
        vsp = _vsp()
        xtype = int(getattr(vsp, xsec_type))
        vsp.InsertXSec(geom_id, index, xtype)
        # After insert the XSec is at index+1; retrieve it from the XSecSurf.
        xsec_surf_id = vsp.GetXSecSurf(geom_id, 0)
        return vsp.GetXSec(xsec_surf_id, index + 1)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def cut_xsec(geom_id: str, index: int) -> str:
    """
    Cut (remove and place on clipboard) a cross-section from a geometry.

    Args:
        geom_id: ID of the geometry.
        index:   Zero-based index of the XSec to cut.
    """
    try:
        _vsp().CutXSec(geom_id, index)
        return f"Cut XSec {index} from geometry '{geom_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def copy_xsec(geom_id: str, index: int) -> str:
    """
    Copy a cross-section to the clipboard without removing it.

    Args:
        geom_id: ID of the geometry.
        index:   Zero-based index of the XSec to copy.
    """
    try:
        _vsp().CopyXSec(geom_id, index)
        return f"Copied XSec {index} from geometry '{geom_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def paste_xsec(geom_id: str, index: int) -> str:
    """
    Paste the clipboard cross-section into a geometry at the given index.

    Args:
        geom_id: ID of the geometry.
        index:   Position at which to paste.
    """
    try:
        _vsp().PasteXSec(geom_id, index)
        return f"Pasted XSec at index {index} in geometry '{geom_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def change_xsec_shape(xsec_surf_id: str, xsec_index: int, xsec_type: str) -> str:
    """
    Change the shape type of an existing cross-section.

    Args:
        xsec_surf_id: ID of the XSecSurf.
        xsec_index:   Zero-based index of the XSec to change.
        xsec_type:    New shape type constant name (see insert_xsec for valid values).
    """
    try:
        vsp = _vsp()
        xtype = int(getattr(vsp, xsec_type))
        vsp.ChangeXSecShape(xsec_surf_id, xsec_index, xtype)
        return f"Changed XSec {xsec_index} shape to '{xsec_type}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_xsec_shape(xsec_id: str) -> str:
    """
    Return the shape-type constant name of a cross-section.

    Args:
        xsec_id: ID of the XSec.
    """
    try:
        vsp = _vsp()
        shape_int = vsp.GetXSecShape(xsec_id)
        # Build a reverse map of the XS_* integer constants.
        xs_map = {
            0: "XS_POINT", 1: "XS_CIRCLE", 2: "XS_ELLIPSE",
            3: "XS_SUPER_ELLIPSE", 4: "XS_ROUNDED_RECTANGLE",
            5: "XS_GENERAL_FUSE", 6: "XS_FILE_FUSE",
            7: "XS_FOUR_SERIES", 8: "XS_SIX_SERIES",
            9: "XS_BICONVEX", 10: "XS_WEDGE", 11: "XS_EDIT_CURVE",
            12: "XS_FILE_AIRFOIL", 13: "XS_CST_AIRFOIL",
            14: "XS_VKT_AIRFOIL", 15: "XS_FOUR_DIGIT_MOD",
            16: "XS_FIVE_DIGIT", 17: "XS_FIVE_DIGIT_MOD",
            18: "XS_ONE_SIX_SERIES",
        }
        return xs_map.get(shape_int, str(shape_int))
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_xsec_width(xsec_id: str) -> float:
    """
    Return the width of a cross-section.

    Args:
        xsec_id: ID of the XSec.
    """
    try:
        return _vsp().GetXSecWidth(xsec_id)
    except Exception as exc:
        return 0.0


@mcp.tool()
def get_xsec_height(xsec_id: str) -> float:
    """
    Return the height of a cross-section.

    Args:
        xsec_id: ID of the XSec.
    """
    try:
        return _vsp().GetXSecHeight(xsec_id)
    except Exception as exc:
        return 0.0


@mcp.tool()
def set_xsec_width(xsec_id: str, width: float) -> str:
    """
    Set the width of a cross-section.

    Args:
        xsec_id: ID of the XSec.
        width:   New width value.
    """
    try:
        _vsp().SetXSecWidth(xsec_id, width)
        return f"Set XSec width to {width}."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_xsec_height(xsec_id: str, height: float) -> str:
    """
    Set the height of a cross-section.

    Args:
        xsec_id: ID of the XSec.
        height:  New height value.
    """
    try:
        _vsp().SetXSecHeight(xsec_id, height)
        return f"Set XSec height to {height}."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_xsec_width_height(xsec_id: str, width: float, height: float) -> str:
    """
    Set both the width and height of a cross-section simultaneously.

    Args:
        xsec_id: ID of the XSec.
        width:   New width value.
        height:  New height value.
    """
    try:
        _vsp().SetXSecWidthHeight(xsec_id, width, height)
        return f"Set XSec width={width}, height={height}."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_xsec_tan_angles(
    xsec_id: str,
    side: str,
    top: float,
    right: float = -1e12,
    bottom: float = -1e12,
    left: float = -1e12,
) -> str:
    """
    Set the tangent angles on one or more sides of a cross-section blend.

    Args:
        xsec_id: ID of the XSec.
        side:    Which side(s) to set — one of ``'XSEC_BOTH_SIDES'``,
                 ``'XSEC_TOP'``, ``'XSEC_BOTTOM'``, ``'XSEC_LEFT'``,
                 ``'XSEC_RIGHT'``.
        top:     Tangent angle for the top (degrees). Used when side includes top.
        right:   Tangent angle for the right (degrees, default = no change).
        bottom:  Tangent angle for the bottom (degrees, default = no change).
        left:    Tangent angle for the left (degrees, default = no change).
    """
    try:
        vsp = _vsp()
        side_val = int(getattr(vsp, side))
        vsp.SetXSecTanAngles(xsec_id, side_val, top, right, bottom, left)
        return f"Set tangent angles on side '{side}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def read_file_airfoil(xsec_id: str, file_name: str) -> str:
    """
    Load an airfoil coordinate file (Selig or Lednicer format) into an XSec.

    The XSec must have type ``XS_FILE_AIRFOIL`` (use change_xsec_shape first if
    needed).

    Args:
        xsec_id:   ID of the XSec to load the airfoil into.
        file_name: Absolute path to the airfoil coordinate file (.dat).
    """
    try:
        _vsp().ReadFileAirfoil(xsec_id, file_name)
        return f"Loaded airfoil from '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Sub-Surfaces
# ===========================================================================

@mcp.tool()
def add_sub_surf(geom_id: str, sub_surf_type: str, surf_index: int = 0) -> str:
    """
    Add a sub-surface to a geometry component.

    Sub-surfaces define regions on a surface (control surfaces, panels, etc.).

    Args:
        geom_id:       ID of the geometry.
        sub_surf_type: Sub-surface type constant name — one of
                       ``'SS_LINE'``, ``'SS_RECTANGLE'``, ``'SS_ELLIPSE'``,
                       ``'SS_CONTROL'``, ``'SS_LINE_ARRAY'``.
        surf_index:    Surface index on the geometry (default 0).

    Returns:
        The ID string of the newly created sub-surface.
    """
    try:
        vsp = _vsp()
        sstype = int(getattr(vsp, sub_surf_type))
        return vsp.AddSubSurf(geom_id, sstype, surf_index)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_sub_surf(sub_id: str) -> str:
    """
    Delete a sub-surface by its ID.

    Args:
        sub_id: ID of the sub-surface to delete.
    """
    try:
        _vsp().DeleteSubSurf(sub_id)
        return f"Deleted sub-surface '{sub_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_sub_surf_by_index(geom_id: str, index: int) -> str:
    """
    Return the ID of the sub-surface at a given index on a geometry.

    Args:
        geom_id: ID of the geometry.
        index:   Zero-based index of the sub-surface.
    """
    try:
        return _vsp().GetSubSurf(geom_id, index)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_sub_surf_by_name(geom_id: str, name: str) -> list[str]:
    """
    Return the IDs of all sub-surfaces with the given name on a geometry.

    Args:
        geom_id: ID of the geometry.
        name:    Sub-surface name to search for.
    """
    try:
        return _vsp().GetSubSurf(geom_id, name)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_sub_surf_id_vec(geom_id: str) -> list[str]:
    """
    Return the IDs of all sub-surfaces on a geometry component.

    Args:
        geom_id: ID of the geometry.
    """
    try:
        return _vsp().GetSubSurfIDVec(geom_id)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_all_sub_surf_ids() -> list[str]:
    """Return the IDs of all sub-surfaces in the current model."""
    try:
        return _vsp().GetAllSubSurfIDs()
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_num_sub_surf(geom_id: str) -> int:
    """
    Return the number of sub-surfaces on a geometry component.

    Args:
        geom_id: ID of the geometry.
    """
    try:
        return _vsp().GetNumSubSurf(geom_id)
    except Exception as exc:
        return -1


@mcp.tool()
def get_sub_surf_type(sub_id: str) -> str:
    """
    Return the type constant name of a sub-surface.

    Args:
        sub_id: ID of the sub-surface.
    """
    try:
        vsp = _vsp()
        sstype = vsp.GetSubSurfType(sub_id)
        ss_map = {0: "SS_LINE", 1: "SS_RECTANGLE", 2: "SS_ELLIPSE",
                  3: "SS_CONTROL", 4: "SS_LINE_ARRAY", 5: "SS_FINITE_LINE"}
        return ss_map.get(sstype, str(sstype))
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_sub_surf_name(sub_id: str) -> str:
    """
    Return the name of a sub-surface.

    Args:
        sub_id: ID of the sub-surface.
    """
    try:
        return _vsp().GetSubSurfName(sub_id)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_sub_surf_name(sub_id: str, name: str) -> str:
    """
    Set the name of a sub-surface.

    Args:
        sub_id: ID of the sub-surface.
        name:   New name to assign.
    """
    try:
        _vsp().SetSubSurfName(sub_id, name)
        return f"Renamed sub-surface '{sub_id}' to '{name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_sub_surf_index(sub_id: str) -> int:
    """
    Return the index of a sub-surface within its parent geometry.

    Args:
        sub_id: ID of the sub-surface.
    """
    try:
        return _vsp().GetSubSurfIndex(sub_id)
    except Exception as exc:
        return -1


@mcp.tool()
def get_sub_surf_parm_ids(sub_id: str) -> list[str]:
    """
    Return the parameter IDs for a sub-surface.

    Args:
        sub_id: ID of the sub-surface.
    """
    try:
        return _vsp().GetSubSurfParmIDs(sub_id)
    except Exception as exc:
        return [f"Error: {exc}"]
