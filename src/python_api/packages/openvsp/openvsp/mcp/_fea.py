"""FEA Mesh and Structural Parts MCP tools."""
from __future__ import annotations

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# FEA Mesh & Structural Parts
# ===========================================================================

@mcp.tool()
def num_fea_structures() -> int:
    """Return the total number of FEA structures in the current model."""
    try:
        return _vsp().NumFeaStructures()
    except Exception as exc:
        return -1


@mcp.tool()
def get_fea_struct_id_vec() -> list[str]:
    """Return the IDs of all FEA structures in the current model."""
    try:
        return _vsp().GetFeaStructIDVec()
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def add_fea_struct(geom_id: str, init_skin: bool = True, surf_index: int = 0) -> int:
    """
    Add an FEA structure to a geometry component.

    Args:
        geom_id:    ID of the geometry to add the structure to.
        init_skin:  If True, initialise the outer skin as an FEA element (default True).
        surf_index: Surface index on the geometry (default 0).

    Returns:
        Integer index of the new FEA structure.
    """
    try:
        return _vsp().AddFeaStruct(geom_id, init_skin, surf_index)
    except Exception as exc:
        return -1


@mcp.tool()
def delete_fea_struct(geom_id: str, fea_struct_ind: int) -> str:
    """
    Delete an FEA structure from a geometry component.

    Args:
        geom_id:       ID of the geometry.
        fea_struct_ind: Index of the FEA structure to delete.
    """
    try:
        _vsp().DeleteFeaStruct(geom_id, fea_struct_ind)
        return f"Deleted FEA structure {fea_struct_ind} from geometry '{geom_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_fea_struct_id(geom_id: str, fea_struct_ind: int) -> str:
    """
    Return the ID of an FEA structure by its geometry and structure index.

    Args:
        geom_id:        ID of the geometry.
        fea_struct_ind: Index of the FEA structure.
    """
    try:
        return _vsp().GetFeaStructID(geom_id, fea_struct_ind)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_fea_struct_name(geom_id: str, fea_struct_ind: int) -> str:
    """
    Return the name of an FEA structure.

    Args:
        geom_id:        ID of the geometry.
        fea_struct_ind: Index of the FEA structure.
    """
    try:
        return _vsp().GetFeaStructName(geom_id, fea_struct_ind)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_fea_struct_name(geom_id: str, fea_struct_ind: int, name: str) -> str:
    """
    Set the name of an FEA structure.

    Args:
        geom_id:        ID of the geometry.
        fea_struct_ind: Index of the FEA structure.
        name:           New name for the structure.
    """
    try:
        _vsp().SetFeaStructName(geom_id, fea_struct_ind, name)
        return f"Renamed FEA structure {fea_struct_ind} to '{name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def num_fea_parts(fea_struct_id: str) -> int:
    """
    Return the number of FEA parts in a structure.

    Args:
        fea_struct_id: ID of the FEA structure.
    """
    try:
        return _vsp().NumFeaParts(fea_struct_id)
    except Exception as exc:
        return -1


@mcp.tool()
def get_fea_part_id_vec(fea_struct_id: str) -> list[str]:
    """
    Return the IDs of all FEA parts in a structure.

    Args:
        fea_struct_id: ID of the FEA structure.
    """
    try:
        return _vsp().GetFeaPartIDVec(fea_struct_id)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def add_fea_part(geom_id: str, fea_struct_ind: int, fea_part_type: str) -> str:
    """
    Add an FEA structural part to a structure.

    Args:
        geom_id:        ID of the geometry.
        fea_struct_ind: Index of the FEA structure.
        fea_part_type:  Part type constant name — one of ``'FEA_SLICE'``,
                        ``'FEA_RIB'``, ``'FEA_SPAR'``, ``'FEA_FIX_POINT'``,
                        ``'FEA_DOME'``, ``'FEA_RIB_ARRAY'``,
                        ``'FEA_SLICE_ARRAY'``, ``'FEA_SKIN'``, ``'FEA_TRIM'``.

    Returns:
        The ID string of the newly created FEA part.
    """
    try:
        vsp = _vsp()
        ptype = int(getattr(vsp, fea_part_type))
        return vsp.AddFeaPart(geom_id, fea_struct_ind, ptype)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_fea_part(geom_id: str, fea_struct_ind: int, part_id: str) -> str:
    """
    Delete an FEA part from a structure.

    Args:
        geom_id:        ID of the geometry.
        fea_struct_ind: Index of the FEA structure.
        part_id:        ID of the FEA part to delete.
    """
    try:
        _vsp().DeleteFeaPart(geom_id, fea_struct_ind, part_id)
        return f"Deleted FEA part '{part_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_fea_part_name(part_id: str) -> str:
    """
    Return the name of an FEA part.

    Args:
        part_id: ID of the FEA part.
    """
    try:
        return _vsp().GetFeaPartName(part_id)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_fea_part_name(part_id: str, name: str) -> str:
    """
    Set the name of an FEA part.

    Args:
        part_id: ID of the FEA part.
        name:    New name for the part.
    """
    try:
        _vsp().SetFeaPartName(part_id, name)
        return f"Renamed FEA part '{part_id}' to '{name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_fea_part_type(part_id: str) -> str:
    """
    Return the type constant name of an FEA part.

    Args:
        part_id: ID of the FEA part.
    """
    try:
        vsp = _vsp()
        ptype = vsp.GetFeaPartType(part_id)
        type_map = {
            0: "FEA_SLICE", 1: "FEA_RIB", 2: "FEA_SPAR",
            3: "FEA_FIX_POINT", 4: "FEA_DOME", 5: "FEA_RIB_ARRAY",
            6: "FEA_SLICE_ARRAY", 7: "FEA_SKIN", 8: "FEA_TRIM",
        }
        return type_map.get(ptype, str(ptype))
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def num_fea_sub_surfs(fea_struct_id: str) -> int:
    """
    Return the number of FEA sub-surfaces in a structure.

    Args:
        fea_struct_id: ID of the FEA structure.
    """
    try:
        return _vsp().NumFeaSubSurfs(fea_struct_id)
    except Exception as exc:
        return -1


@mcp.tool()
def get_fea_sub_surf_id_vec(fea_struct_id: str) -> list[str]:
    """
    Return the IDs of all FEA sub-surfaces in a structure.

    Args:
        fea_struct_id: ID of the FEA structure.
    """
    try:
        return _vsp().GetFeaSubSurfIDVec(fea_struct_id)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def add_fea_sub_surf(geom_id: str, fea_struct_ind: int, sub_surf_type: str) -> str:
    """
    Add a sub-surface to an FEA structure for boundary condition definition.

    Args:
        geom_id:        ID of the geometry.
        fea_struct_ind: Index of the FEA structure.
        sub_surf_type:  Sub-surface type constant name (e.g. ``'SS_LINE'``,
                        ``'SS_RECTANGLE'``, ``'SS_ELLIPSE'``,
                        ``'SS_LINE_ARRAY'``).

    Returns:
        The ID string of the new FEA sub-surface.
    """
    try:
        vsp = _vsp()
        sstype = int(getattr(vsp, sub_surf_type))
        return vsp.AddFeaSubSurf(geom_id, fea_struct_ind, sstype)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def delete_fea_sub_surf(geom_id: str, fea_struct_ind: int, ss_id: str) -> str:
    """
    Delete an FEA sub-surface from a structure.

    Args:
        geom_id:        ID of the geometry.
        fea_struct_ind: Index of the FEA structure.
        ss_id:          ID of the FEA sub-surface to delete.
    """
    try:
        _vsp().DeleteFeaSubSurf(geom_id, fea_struct_ind, ss_id)
        return f"Deleted FEA sub-surface '{ss_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def add_fea_material() -> str:
    """
    Add a new FEA material definition to the model.

    Returns:
        The ID string of the newly created FEA material.
    """
    try:
        return _vsp().AddFeaMaterial()
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def add_fea_property(property_type: int = 0) -> str:
    """
    Add a new FEA property definition to the model.

    Args:
        property_type: Property type integer (0 = shell, 1 = beam; default 0).

    Returns:
        The ID string of the newly created FEA property.
    """
    try:
        return _vsp().AddFeaProperty(property_type)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def compute_fea_mesh(struct_id: str, file_type: int = 0) -> str:
    """
    Compute the FEA mesh for a structure and export results.

    Args:
        struct_id: ID of the FEA structure to mesh.
        file_type: Output file type bitmask (0 = no file output). Use VSP FEA
                   file type constants (FEA_MASS_FILE_NAME, etc.) OR'd together.

    Returns:
        Confirmation message.
    """
    try:
        _vsp().ComputeFeaMesh(struct_id, file_type)
        return f"FEA mesh computation complete for structure '{struct_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_fea_part_perpendicular_spar_id(part_id: str, spar_id: str) -> str:
    """
    Link a rib FEA part to a spar so it stays perpendicular to it.

    Args:
        part_id: ID of the rib FEA part.
        spar_id: ID of the spar FEA part to be perpendicular to.
    """
    try:
        _vsp().SetFeaPartPerpendicularSparID(part_id, spar_id)
        return f"Set rib '{part_id}' perpendicular to spar '{spar_id}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_fea_part_perpendicular_spar_id(part_id: str) -> str:
    """
    Return the spar ID that a rib FEA part is set to be perpendicular to.

    Args:
        part_id: ID of the rib FEA part.
    """
    try:
        return _vsp().GetFeaPartPerpendicularSparID(part_id)
    except Exception as exc:
        return f"Error: {exc}"
