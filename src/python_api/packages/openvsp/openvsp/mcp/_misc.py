"""Parasite drag, propeller PCurve, Advanced Links, and CFD Mesh MCP tools."""
from __future__ import annotations

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# Parasite Drag
# ===========================================================================

@mcp.tool()
def add_excrescence(name: str, excres_type: int, value: float) -> str:
    """
    Add an excrescence (parasitic drag increment) to the parasite drag model.

    Args:
        name:        Label for the excrescence.
        excres_type: Excrescence type integer (see EXCRES_TYPE constants in the
                     OpenVSP API — e.g. 0 = drag counts, 1 = CD, 2 = % total,
                     3 = f (wetted area × Cf), 4 = D/q).
        value:       Magnitude of the excrescence.

    Returns:
        Confirmation message.
    """
    try:
        _vsp().AddExcrescence(name, excres_type, value)
        return f"Added excrescence '{name}' (type={excres_type}, value={value})."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_excrescence(index: int) -> str:
    """
    Delete an excrescence from the parasite drag model by index.

    Args:
        index: Zero-based index of the excrescence to remove.
    """
    try:
        _vsp().DeleteExcrescence(index)
        return f"Deleted excrescence at index {index}."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def update_parasite_drag() -> str:
    """Recompute the parasite drag model (call after changing geometry or excrescences)."""
    try:
        _vsp().UpdateParasiteDrag()
        return "Parasite drag updated."
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Propeller Blade Curves (PCurve)
# ===========================================================================

@mcp.tool()
def set_pcurve(
    geom_id: str,
    pcurve_id: int,
    t_vec: list[float],
    val_vec: list[float],
    curve_type: int = 2,
) -> str:
    """
    Set the control points of a propeller blade curve (PCurve).

    PCurves define spanwise distributions of chord, twist, thickness, rake,
    skew, and other propeller blade parameters.

    Args:
        geom_id:    ID of the propeller geometry.
        pcurve_id:  PCurve identifier integer:
                    0=chord, 1=twist, 2=rake, 3=skew, 4=sweep,
                    5=axial, 6=tangential, 7=thickness, 8=CLI.
        t_vec:      List of spanwise parameter values (0 = root, 1 = tip).
        val_vec:    List of curve values at the corresponding t positions.
        curve_type: Curve type integer (0=LINEAR, 1=PCHIP, 2=APPROX_CEDIT,
                    3=CEDIT; default 2).

    Returns:
        Confirmation message.
    """
    try:
        if len(t_vec) != len(val_vec):
            return (
                f"Error: t_vec length ({len(t_vec)}) must match "
                f"val_vec length ({len(val_vec)})"
            )
        _vsp().SetPCurve(geom_id, pcurve_id, t_vec, val_vec, curve_type)
        return f"Set PCurve {pcurve_id} on geometry '{geom_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def pcurve_get_tvec(geom_id: str, pcurve_id: int) -> list[float]:
    """
    Return the spanwise parameter (t) values of a propeller blade curve.

    Args:
        geom_id:   ID of the propeller geometry.
        pcurve_id: PCurve identifier integer (0=chord, 1=twist, …).
    """
    try:
        return list(_vsp().PCurveGetTVec(geom_id, pcurve_id))
    except Exception as exc:
        return []


@mcp.tool()
def pcurve_get_val_vec(geom_id: str, pcurve_id: int) -> list[float]:
    """
    Return the values of a propeller blade curve at its control points.

    Args:
        geom_id:   ID of the propeller geometry.
        pcurve_id: PCurve identifier integer (0=chord, 1=twist, …).
    """
    try:
        return list(_vsp().PCurveGetValVec(geom_id, pcurve_id))
    except Exception as exc:
        return []


@mcp.tool()
def pcurve_get_type(geom_id: str, pcurve_id: int) -> int:
    """
    Return the curve type integer of a propeller blade curve.

    Args:
        geom_id:   ID of the propeller geometry.
        pcurve_id: PCurve identifier integer.
    """
    try:
        return _vsp().PCurveGetType(geom_id, pcurve_id)
    except Exception as exc:
        return -1


@mcp.tool()
def pcurve_convert_to(geom_id: str, pcurve_id: int, new_type: int) -> str:
    """
    Convert a propeller blade curve to a different curve type.

    Args:
        geom_id:   ID of the propeller geometry.
        pcurve_id: PCurve identifier integer.
        new_type:  Target curve type (0=LINEAR, 1=PCHIP, 2=APPROX_CEDIT, 3=CEDIT).
    """
    try:
        _vsp().PCurveConvertTo(geom_id, pcurve_id, new_type)
        return f"Converted PCurve {pcurve_id} to type {new_type}."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def pcurve_delete_pt(geom_id: str, pcurve_id: int, index: int) -> str:
    """
    Delete a control point from a propeller blade curve.

    Args:
        geom_id:   ID of the propeller geometry.
        pcurve_id: PCurve identifier integer.
        index:     Zero-based index of the control point to delete.
    """
    try:
        _vsp().PCurveDeletePt(geom_id, pcurve_id, index)
        return f"Deleted control point {index} from PCurve {pcurve_id}."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def pcurve_split(geom_id: str, pcurve_id: int, t_split: float) -> int:
    """
    Split a propeller blade curve at a given spanwise position.

    Args:
        geom_id:   ID of the propeller geometry.
        pcurve_id: PCurve identifier integer.
        t_split:   Spanwise position at which to insert a split point [0, 1].

    Returns:
        The index of the newly inserted point.
    """
    try:
        return _vsp().PCurveSplit(geom_id, pcurve_id, t_split)
    except Exception as exc:
        return -1


@mcp.tool()
def approximate_all_propeller_pcurves(geom_id: str) -> str:
    """
    Approximate all blade curves for a propeller geometry with CEDIT control points.

    This converts free-form PCHIP curves to editable control-point curves,
    making them easier to modify while preserving the blade shape.

    Args:
        geom_id: ID of the propeller geometry.
    """
    try:
        _vsp().ApproximateAllPropellerPCurves(geom_id)
        return f"Approximated all PCurves for propeller '{geom_id}'."
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Advanced Links
# ===========================================================================

@mcp.tool()
def get_adv_link_names() -> list[str]:
    """Get list of all advanced link names defined in the VSP model.

    Advanced links allow scripted parametric relationships between parms.

    Returns:
        list of str: Names of all advanced links.
    """
    try:
        vsp = _vsp()
        return list(vsp.GetAdvLinkNames())
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def add_adv_link(name: str) -> str:
    """Add a new advanced link with the given name.

    Args:
        name: Name for the new advanced link.

    Returns:
        str: Confirmation message with link name.
    """
    try:
        vsp = _vsp()
        vsp.AddAdvLink(name)
        return f"Added advanced link: {name}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def del_adv_link(index: int) -> str:
    """Delete the advanced link at the given index.

    Args:
        index: Zero-based index of the advanced link to delete.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.DelAdvLink(index)
        return f"Deleted advanced link at index {index}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def del_all_adv_links() -> str:
    """Delete all advanced links in the VSP model.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.DelAllAdvLinks()
        return "Deleted all advanced links"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def add_adv_link_input(index: int, parm_id: str, var_name: str) -> str:
    """Add an input parm to an advanced link.

    Args:
        index: Zero-based index of the advanced link.
        parm_id: Parm ID to use as input.
        var_name: Variable name to use in the link script.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.AddAdvLinkInput(index, parm_id, var_name)
        return f"Added input {var_name} to advanced link {index}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def add_adv_link_output(index: int, parm_id: str, var_name: str) -> str:
    """Add an output parm to an advanced link.

    Args:
        index: Zero-based index of the advanced link.
        parm_id: Parm ID to use as output.
        var_name: Variable name to use in the link script.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.AddAdvLinkOutput(index, parm_id, var_name)
        return f"Added output {var_name} to advanced link {index}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def del_adv_link_input(index: int, var_name: str) -> str:
    """Delete an input variable from an advanced link.

    Args:
        index: Zero-based index of the advanced link.
        var_name: Name of the input variable to remove.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.DelAdvLinkInput(index, var_name)
        return f"Deleted input {var_name} from advanced link {index}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def del_adv_link_output(index: int, var_name: str) -> str:
    """Delete an output variable from an advanced link.

    Args:
        index: Zero-based index of the advanced link.
        var_name: Name of the output variable to remove.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.DelAdvLinkOutput(index, var_name)
        return f"Deleted output {var_name} from advanced link {index}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_adv_link_input_names(index: int) -> list[str]:
    """Get input variable names for an advanced link.

    Args:
        index: Zero-based index of the advanced link.

    Returns:
        list of str: Input variable names.
    """
    try:
        vsp = _vsp()
        return list(vsp.GetAdvLinkInputNames(index))
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_adv_link_output_names(index: int) -> list[str]:
    """Get output variable names for an advanced link.

    Args:
        index: Zero-based index of the advanced link.

    Returns:
        list of str: Output variable names.
    """
    try:
        vsp = _vsp()
        return list(vsp.GetAdvLinkOutputNames(index))
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_adv_link_input_parms(index: int) -> list[str]:
    """Get input parm IDs for an advanced link.

    Args:
        index: Zero-based index of the advanced link.

    Returns:
        list of str: Parm IDs used as inputs.
    """
    try:
        vsp = _vsp()
        return list(vsp.GetAdvLinkInputParms(index))
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_adv_link_output_parms(index: int) -> list[str]:
    """Get output parm IDs for an advanced link.

    Args:
        index: Zero-based index of the advanced link.

    Returns:
        list of str: Parm IDs used as outputs.
    """
    try:
        vsp = _vsp()
        return list(vsp.GetAdvLinkOutputParms(index))
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def set_adv_link_code(index: int, code: str) -> str:
    """Set the AngelScript code for an advanced link.

    Args:
        index: Zero-based index of the advanced link.
        code: AngelScript code string for the link.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.SetAdvLinkCode(index, code)
        return f"Set code for advanced link {index}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_adv_link_code(index: int) -> str:
    """Get the AngelScript code for an advanced link.

    Args:
        index: Zero-based index of the advanced link.

    Returns:
        str: AngelScript code string.
    """
    try:
        vsp = _vsp()
        return str(vsp.GetAdvLinkCode(index))
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def build_adv_link_script(index: int) -> str:
    """Build/compile the AngelScript for an advanced link.

    Args:
        index: Zero-based index of the advanced link.

    Returns:
        str: "true" if build succeeded, "false" otherwise.
    """
    try:
        vsp = _vsp()
        result = vsp.BuildAdvLinkScript(index)
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def validate_adv_link_parms(index: int) -> str:
    """Validate parms for an advanced link.

    Args:
        index: Zero-based index of the advanced link.

    Returns:
        str: "true" if parms are valid, "false" otherwise.
    """
    try:
        vsp = _vsp()
        result = vsp.ValidateAdvLinkParms(index)
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def search_replace_adv_link_code(index: int, from_str: str, to_str: str) -> str:
    """Search and replace text in an advanced link's code.

    Args:
        index: Zero-based index of the advanced link.
        from_str: String to search for.
        to_str: Replacement string.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.SearchReplaceAdvLinkCode(index, from_str, to_str)
        return f"Search/replaced in advanced link {index} code"
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# CFD Mesh (low-level)
# ===========================================================================

@mcp.tool()
def set_cfd_mesh_val(type: int, val: float) -> str:
    """Set a CFD mesh setting value.

    Args:
        type: CFD mesh setting type integer constant.
        val: Value to set.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.SetCFDMeshVal(type, val)
        return f"Set CFD mesh val type={type} to {val}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_all_cfd_sources() -> str:
    """Delete all CFD mesh sources.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.DeleteAllCFDSources()
        return "Deleted all CFD sources"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_cfd_wake_flag(geom_id: str, flag: bool) -> str:
    """Set the wake flag for a geometry in CFD meshing.

    Args:
        geom_id: ID of the geometry.
        flag: True to enable wake, False to disable.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.SetCFDWakeFlag(geom_id, flag)
        return f"Set CFD wake flag for {geom_id} to {flag}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def add_cfd_source(
    type: int,
    geom_id: str,
    surf_index: int,
    l1: float,
    r1: float,
    u1: float,
    w1: float,
) -> str:
    """Add a CFD mesh source to a geometry surface.

    Args:
        type: Source type integer constant.
        geom_id: ID of the geometry to add source to.
        surf_index: Surface index on the geometry.
        l1: Length scale parameter.
        r1: Radius parameter.
        u1: U parameter location.
        w1: W parameter location.

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.AddCFDSource(type, geom_id, surf_index, l1, r1, u1, w1)
        return f"Added CFD source type={type} to geom {geom_id} surf {surf_index}"
    except Exception as exc:
        return f"Error: {exc}"
