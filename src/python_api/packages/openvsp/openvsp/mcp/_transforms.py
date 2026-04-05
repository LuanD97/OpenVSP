"""Group/Set transformations, Variable Presets, and VSPAERO Control Surface Group MCP tools."""
from __future__ import annotations

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# Group / Set Transformations
# ===========================================================================

@mcp.tool()
def scale_set(set_index: int, scale: float) -> str:
    """
    Uniformly scale all geometry in a set about the origin.

    Args:
        set_index: Geometry set to scale (0 = SET_ALL).
        scale:     Scale factor (1.0 = no change, 2.0 = double size).
    """
    try:
        _vsp().ScaleSet(set_index, scale)
        return f"Scaled set {set_index} by factor {scale}."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def rotate_set(set_index: int, x_rot_deg: float, y_rot_deg: float, z_rot_deg: float) -> str:
    """
    Rotate all geometry in a set about the X, Y, and Z axes.

    Args:
        set_index:   Geometry set to rotate (0 = SET_ALL).
        x_rot_deg:   Rotation about X axis (degrees).
        y_rot_deg:   Rotation about Y axis (degrees).
        z_rot_deg:   Rotation about Z axis (degrees).
    """
    try:
        _vsp().RotateSet(set_index, x_rot_deg, y_rot_deg, z_rot_deg)
        return f"Rotated set {set_index} by ({x_rot_deg}, {y_rot_deg}, {z_rot_deg}) degrees."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def translate_set(set_index: int, x: float, y: float, z: float) -> str:
    """
    Translate (move) all geometry in a set by a displacement vector.

    Args:
        set_index: Geometry set to translate (0 = SET_ALL).
        x:         Translation along X axis.
        y:         Translation along Y axis.
        z:         Translation along Z axis.
    """
    try:
        vsp = _vsp()
        vsp.TranslateSet(set_index, vsp.vec3d(x, y, z))
        return f"Translated set {set_index} by ({x}, {y}, {z})."
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Variable Presets
# ===========================================================================

@mcp.tool()
def get_var_preset_groups() -> list[str]:
    """Return the IDs of all variable preset groups in the current model."""
    try:
        return _vsp().GetVarPresetGroups()
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def add_var_preset_group(group_name: str) -> str:
    """
    Create a new variable preset group.

    A group holds a set of parameters and multiple named settings (variants)
    for those parameters.

    Args:
        group_name: Name for the new group.

    Returns:
        The group ID string.
    """
    try:
        return _vsp().AddVarPresetGroup(group_name)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_var_preset_group(group_id: str) -> str:
    """
    Delete a variable preset group and all its settings.

    Args:
        group_id: ID of the group to delete.
    """
    try:
        _vsp().DeleteVarPresetGroup(group_id)
        return f"Deleted variable preset group '{group_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_var_preset_settings(group_id: str) -> list[str]:
    """
    Return the IDs of all settings (variants) in a variable preset group.

    Args:
        group_id: ID of the group.
    """
    try:
        return _vsp().GetVarPresetSettings(group_id)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def add_var_preset_setting(group_id: str, setting_name: str) -> str:
    """
    Add a new named setting (design variant) to a variable preset group.

    Args:
        group_id:     ID of the group.
        setting_name: Name for the new setting.

    Returns:
        The setting ID string.
    """
    try:
        return _vsp().AddVarPresetSetting(group_id, setting_name)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_var_preset_setting(group_id: str, setting_id: str) -> str:
    """
    Delete a setting from a variable preset group.

    Args:
        group_id:   ID of the group.
        setting_id: ID of the setting to delete.
    """
    try:
        _vsp().DeleteVarPresetSetting(group_id, setting_id)
        return f"Deleted setting '{setting_id}' from group '{group_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_var_preset_parm_ids(group_id: str) -> list[str]:
    """
    Return the parameter IDs tracked by a variable preset group.

    Args:
        group_id: ID of the group.
    """
    try:
        return _vsp().GetVarPresetParmIDs(group_id)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def add_var_preset_parm(group_id: str, parm_id: str) -> str:
    """
    Add a parameter to a variable preset group so it is tracked across settings.

    Args:
        group_id: ID of the group.
        parm_id:  Parameter ID to track.
    """
    try:
        _vsp().AddVarPresetParm(group_id, parm_id)
        return f"Added parameter '{parm_id}' to preset group '{group_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_var_preset_parm(group_id: str, parm_id: str) -> str:
    """
    Remove a parameter from a variable preset group.

    Args:
        group_id: ID of the group.
        parm_id:  Parameter ID to remove.
    """
    try:
        _vsp().DeleteVarPresetParm(group_id, parm_id)
        return f"Removed parameter '{parm_id}' from preset group '{group_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_var_preset_parm_val(
    group_id: str, setting_id: str, parm_id: str, value: float
) -> str:
    """
    Set the value of a parameter within a specific preset setting.

    Args:
        group_id:   ID of the preset group.
        setting_id: ID of the setting.
        parm_id:    Parameter ID.
        value:      Value to assign.
    """
    try:
        _vsp().SetVarPresetParmVal(group_id, setting_id, parm_id, value)
        return f"Set parm '{parm_id}' = {value} in setting '{setting_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_var_preset_parm_val(group_id: str, setting_id: str, parm_id: str) -> float:
    """
    Return the value of a parameter within a specific preset setting.

    Args:
        group_id:   ID of the preset group.
        setting_id: ID of the setting.
        parm_id:    Parameter ID.
    """
    try:
        return _vsp().GetVarPresetParmVal(group_id, setting_id, parm_id)
    except Exception as exc:
        return 0.0


@mcp.tool()
def save_var_preset_parm_vals(group_id: str, setting_id: str) -> str:
    """
    Save the current model parameter values into a preset setting.

    Call this after adjusting parameters to snapshot them into the setting.

    Args:
        group_id:   ID of the preset group.
        setting_id: ID of the setting to save into.
    """
    try:
        _vsp().SaveVarPresetParmVals(group_id, setting_id)
        return f"Saved parameter values into setting '{setting_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def apply_var_preset_setting(group_id: str, setting_id: str) -> str:
    """
    Apply a preset setting, restoring its saved parameter values to the model.

    Args:
        group_id:   ID of the preset group.
        setting_id: ID of the setting to apply.
    """
    try:
        _vsp().ApplyVarPresetSetting(group_id, setting_id)
        return f"Applied preset setting '{setting_id}'."
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# VSPAERO Control Surface Groups
# ===========================================================================

@mcp.tool()
def get_num_control_surface_groups() -> int:
    """Return the number of VSPAERO control surface groups defined in the model."""
    try:
        return _vsp().GetNumControlSurfaceGroups()
    except Exception as exc:
        return -1


@mcp.tool()
def create_vspaero_control_surface_group() -> int:
    """
    Create a new VSPAERO control surface group.

    Returns:
        The integer index of the newly created group.
    """
    try:
        return _vsp().CreateVSPAEROControlSurfaceGroup()
    except Exception as exc:
        return -1


@mcp.tool()
def get_vspaero_control_group_name(cs_group_index: int) -> str:
    """
    Return the name of a VSPAERO control surface group.

    Args:
        cs_group_index: Zero-based index of the control surface group.
    """
    try:
        return _vsp().GetVSPAEROControlGroupName(cs_group_index)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_vspaero_control_group_name(cs_group_index: int, name: str) -> str:
    """
    Set the name of a VSPAERO control surface group.

    Args:
        cs_group_index: Zero-based index of the control surface group.
        name:           New name for the group.
    """
    try:
        _vsp().SetVSPAEROControlGroupName(name, cs_group_index)
        return f"Renamed control surface group {cs_group_index} to '{name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def auto_group_vspaero_control_surfaces() -> str:
    """
    Automatically create VSPAERO control surface groups from sub-surface definitions.

    This scans all ``SS_CONTROL`` sub-surfaces and groups them by name prefix.
    """
    try:
        _vsp().AutoGroupVSPAEROControlSurfaces()
        return "Auto-grouped VSPAERO control surfaces."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def add_all_to_vspaero_control_surface_group(cs_group_index: int) -> str:
    """
    Add all available control sub-surfaces to a VSPAERO control surface group.

    Args:
        cs_group_index: Zero-based index of the control surface group.
    """
    try:
        _vsp().AddAllToVSPAEROControlSurfaceGroup(cs_group_index)
        return f"Added all control surfaces to group {cs_group_index}."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def remove_all_from_vspaero_control_surface_group(cs_group_index: int) -> str:
    """
    Remove all control sub-surfaces from a VSPAERO control surface group.

    Args:
        cs_group_index: Zero-based index of the control surface group.
    """
    try:
        _vsp().RemoveAllFromVSPAEROControlSurfaceGroup(cs_group_index)
        return f"Removed all control surfaces from group {cs_group_index}."
    except Exception as exc:
        return f"Error: {exc}"
