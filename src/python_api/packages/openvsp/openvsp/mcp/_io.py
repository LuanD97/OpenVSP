"""File export and import MCP tools."""

from __future__ import annotations

from typing import Any

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# Export helpers
# ===========================================================================


def _export_type(vsp: Any, name: str) -> int:
    """Return the integer value of an EXPORT_TYPE constant, e.g. 'EXPORT_STL'."""
    return int(getattr(vsp, name))


# ===========================================================================
# Direct file exports  (ExportFile)
# ===========================================================================


@mcp.tool()
def list_export_types() -> list[str]:
    """
    Return the names of all export format constants understood by export_file().

    Use these constant names as the ``export_type`` argument of export_file(),
    or call one of the format-specific export tools directly.
    """
    try:
        return [
            "EXPORT_STL",
            "EXPORT_OBJ",
            "EXPORT_GMSH",
            "EXPORT_X3D",
            "EXPORT_STEP",
            "EXPORT_STEP_STRUCTURE",
            "EXPORT_IGES",
            "EXPORT_IGES_STRUCTURE",
            "EXPORT_DXF",
            "EXPORT_SVG",
            "EXPORT_PLOT3D",
            "EXPORT_CART3D",
            "EXPORT_VSPGEOM",
            "EXPORT_NASCART",
            "EXPORT_POVRAY",
            "EXPORT_FACET",
            "EXPORT_PMARC",
            "EXPORT_BEM",
            "EXPORT_XSEC",
            "EXPORT_SELIG_AIRFOIL",
            "EXPORT_BEZIER_AIRFOIL",
        ]
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def export_file(
    file_name: str,
    export_type: str,
    set_index: int = 0,
    include_subsurfaces: bool = True,
) -> str:
    """
    Export the model to a file using any supported format.

    Args:
        file_name:           Absolute path for the output file.
        export_type:         Export format constant name, e.g. ``'EXPORT_STL'``,
                             ``'EXPORT_IGES'``, ``'EXPORT_STEP'``, ``'EXPORT_OBJ'``.
                             Call list_export_types() for all valid names.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces (default True).

    Returns:
        A results ID string (empty for formats that do not produce one).
    """
    try:
        vsp = _vsp()
        ftype = _export_type(vsp, export_type)
        sub_flag = 1 if include_subsurfaces else 0
        return vsp.ExportFile(file_name, set_index, ftype, sub_flag) or ""
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_stl(
    file_name: str, set_index: int = 0, include_subsurfaces: bool = True
) -> str:
    """
    Export the model as an STL mesh (*.stl).

    Args:
        file_name:           Absolute path for the output .stl file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(
            file_name,
            set_index,
            vsp.EXPORT_STL,
            1 if include_subsurfaces else 0,
        )
        return f"Exported STL to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_obj(
    file_name: str, set_index: int = 0, include_subsurfaces: bool = True
) -> str:
    """
    Export the model as a Wavefront OBJ mesh (*.obj).

    Args:
        file_name:           Absolute path for the output .obj file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(
            file_name,
            set_index,
            vsp.EXPORT_OBJ,
            1 if include_subsurfaces else 0,
        )
        return f"Exported OBJ to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_step(
    file_name: str,
    set_index: int = 0,
    include_subsurfaces: bool = True,
    structure: bool = False,
) -> str:
    """
    Export the model as a STEP file (*.stp).

    Args:
        file_name:           Absolute path for the output .stp file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
        structure:           If True, export the STEP structure variant
                             (for FEA/structural use).
    """
    try:
        vsp = _vsp()
        ftype = vsp.EXPORT_STEP_STRUCTURE if structure else vsp.EXPORT_STEP
        vsp.ExportFile(
            file_name, set_index, ftype, 1 if include_subsurfaces else 0
        )
        return f"Exported STEP to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_iges(
    file_name: str,
    set_index: int = 0,
    include_subsurfaces: bool = True,
    structure: bool = False,
) -> str:
    """
    Export the model as an IGES file (*.igs).

    Args:
        file_name:           Absolute path for the output .igs file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
        structure:           If True, export the IGES structure variant
                             (for FEA/structural use).
    """
    try:
        vsp = _vsp()
        ftype = vsp.EXPORT_IGES_STRUCTURE if structure else vsp.EXPORT_IGES
        vsp.ExportFile(
            file_name, set_index, ftype, 1 if include_subsurfaces else 0
        )
        return f"Exported IGES to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_gmsh(
    file_name: str, set_index: int = 0, include_subsurfaces: bool = True
) -> str:
    """
    Export the model as a Gmsh mesh file (*.msh).

    Args:
        file_name:           Absolute path for the output .msh file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
    """
    try:
        vsp = _vsp()
        result = vsp.ExportFile(
            file_name,
            set_index,
            vsp.EXPORT_GMSH,
            1 if include_subsurfaces else 0,
        )
        return result or f"Exported Gmsh to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_dxf(file_name: str, set_index: int = 0) -> str:
    """
    Export the model as an AutoCAD DXF file (*.dxf).

    Args:
        file_name: Absolute path for the output .dxf file.
        set_index: Geometry set to export (0 = SET_ALL).
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(file_name, set_index, vsp.EXPORT_DXF)
        return f"Exported DXF to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_svg(file_name: str, set_index: int = 0) -> str:
    """
    Export the model as an SVG vector image (*.svg).

    Args:
        file_name: Absolute path for the output .svg file.
        set_index: Geometry set to export (0 = SET_ALL).
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(file_name, set_index, vsp.EXPORT_SVG)
        return f"Exported SVG to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_x3d(file_name: str, set_index: int = 0) -> str:
    """
    Export the model as an X3D file (*.x3d).

    Args:
        file_name: Absolute path for the output .x3d file.
        set_index: Geometry set to export (0 = SET_ALL).
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(file_name, set_index, vsp.EXPORT_X3D)
        return f"Exported X3D to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_plot3d(
    file_name: str, set_index: int = 0, include_subsurfaces: bool = True
) -> str:
    """
    Export the model as a PLOT3D file (*.p3d), commonly used for CFD.

    Args:
        file_name:           Absolute path for the output .p3d file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(
            file_name,
            set_index,
            vsp.EXPORT_PLOT3D,
            1 if include_subsurfaces else 0,
        )
        return f"Exported PLOT3D to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_cart3d(
    file_name: str, set_index: int = 0, include_subsurfaces: bool = True
) -> str:
    """
    Export the model as a Cart3D triangulation file (*.tri).

    Args:
        file_name:           Absolute path for the output .tri file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(
            file_name,
            set_index,
            vsp.EXPORT_CART3D,
            1 if include_subsurfaces else 0,
        )
        return f"Exported Cart3D to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_nascart(
    file_name: str, set_index: int = 0, include_subsurfaces: bool = True
) -> str:
    """
    Export the model in NASCART format (*.dat).

    Args:
        file_name:           Absolute path for the output .dat file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(
            file_name,
            set_index,
            vsp.EXPORT_NASCART,
            1 if include_subsurfaces else 0,
        )
        return f"Exported NASCART to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_vspgeom(
    file_name: str, set_index: int = 0, include_subsurfaces: bool = True
) -> str:
    """
    Export the model in VSPGeom format (*.vspgeom), used by VSPAERO.

    Args:
        file_name:           Absolute path for the output .vspgeom file.
        set_index:           Geometry set to export (0 = SET_ALL).
        include_subsurfaces: Whether to include subsurfaces.
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(
            file_name,
            set_index,
            vsp.EXPORT_VSPGEOM,
            1 if include_subsurfaces else 0,
        )
        return f"Exported VSPGeom to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_bem(file_name: str, prop_geom_id: str, set_index: int = 0) -> str:
    """
    Export a propeller geometry as a Blade Element Method file (*.bem).

    The propeller geometry must be selected before calling this function.

    Args:
        file_name:    Absolute path for the output .bem file.
        prop_geom_id: ID of the propeller geometry component to export.
        set_index:    Geometry set to export (0 = SET_ALL).
    """
    try:
        vsp = _vsp()
        vsp.SetBEMPropID(prop_geom_id)
        vsp.ExportFile(file_name, set_index, vsp.EXPORT_BEM)
        return f"Exported BEM to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_selig_airfoil(file_name: str, set_index: int = 0) -> str:
    """
    Export airfoil geometry in Selig point format (*.dat).

    Args:
        file_name: Absolute path for the output .dat file.
        set_index: Geometry set to export (0 = SET_ALL).
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(file_name, set_index, vsp.EXPORT_SELIG_AIRFOIL)
        return f"Exported Selig airfoil data to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_bezier_airfoil(file_name: str, set_index: int = 0) -> str:
    """
    Export airfoil geometry as Bezier curves (*.bz).

    Args:
        file_name: Absolute path for the output .bz file.
        set_index: Geometry set to export (0 = SET_ALL).
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(file_name, set_index, vsp.EXPORT_BEZIER_AIRFOIL)
        return f"Exported Bezier airfoil curves to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def export_xsec(file_name: str, set_index: int = 0) -> str:
    """
    Export cross-section geometry in HRM format (*.hrm).

    Args:
        file_name: Absolute path for the output .hrm file.
        set_index: Geometry set to export (0 = SET_ALL).
    """
    try:
        vsp = _vsp()
        vsp.ExportFile(file_name, set_index, vsp.EXPORT_XSEC)
        return f"Exported XSec to '{file_name}'."
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Computation-based exports
# ===========================================================================


@mcp.tool()
def compute_comp_geom(
    output_file: str,
    set_index: int = 0,
    half_mesh: bool = False,
    csv: bool = True,
    txt: bool = False,
) -> str:
    """
    Compute watertight component geometry and export the result.

    This runs the CompGeom meshing algorithm which produces an intersected,
    watertight surface mesh suitable for aerodynamic analysis.

    Args:
        output_file: Base path for output file(s) (extension added automatically).
        set_index:   Geometry set to use (0 = SET_ALL).
        half_mesh:   If True, only compute the half (symmetric) mesh.
        csv:         Export results as CSV (default True).
        txt:         Export results as text summary.

    Returns:
        The results ID string from the computation.
    """
    try:
        vsp = _vsp()
        file_types = 0
        if csv:
            vsp.SetComputationFileName(
                vsp.COMP_GEOM_CSV_TYPE, output_file + ".csv"
            )
            file_types |= vsp.COMP_GEOM_CSV_TYPE
        if txt:
            vsp.SetComputationFileName(
                vsp.COMP_GEOM_TXT_TYPE, output_file + ".txt"
            )
            file_types |= vsp.COMP_GEOM_TXT_TYPE
        results_id = vsp.ComputeCompGeom(set_index, half_mesh, file_types)
        return results_id or "CompGeom complete."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def compute_degen_geom(
    output_file: str,
    set_index: int = 0,
    csv: bool = True,
    matlab: bool = False,
) -> str:
    """
    Compute degenerate (thin-surface) geometry and export the result.

    DegenGeom produces a simplified lifting-surface representation of the model,
    used by VSPAERO and other analysis tools.

    Args:
        output_file: Base path for output file(s) (extension added automatically).
        set_index:   Geometry set to use (0 = SET_ALL).
        csv:         Export as CSV (default True).
        matlab:      Export as MATLAB .m file.
    """
    try:
        vsp = _vsp()
        file_types = 0
        if csv:
            vsp.SetComputationFileName(
                vsp.DEGEN_GEOM_CSV_TYPE, output_file + ".csv"
            )
            file_types |= vsp.DEGEN_GEOM_CSV_TYPE
        if matlab:
            vsp.SetComputationFileName(
                vsp.DEGEN_GEOM_M_TYPE, output_file + ".m"
            )
            file_types |= vsp.DEGEN_GEOM_M_TYPE
        vsp.ComputeDegenGeom(set_index, file_types)
        return "DegenGeom complete."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def compute_cfd_mesh(
    output_file: str,
    set_index: int = 0,
    degen_set_index: int = -1,
    stl: bool = True,
    gmsh: bool = False,
    obj: bool = False,
    dat: bool = False,
    key: bool = False,
    tkey: bool = False,
    facet: bool = False,
    vspgeom: bool = False,
) -> str:
    """
    Compute a CFD surface mesh and export the result in one or more formats.

    Args:
        output_file:    Base path for output file(s) (extension added automatically).
        set_index:      Geometry set to mesh (0 = SET_ALL).
        degen_set_index: Set for degenerate (thin) surfaces (-1 = SET_NONE).
        stl:            Export STL (default True).
        gmsh:           Export Gmsh .msh.
        obj:            Export OBJ.
        dat:            Export CART3D .dat.
        key:            Export CART3D .key.
        tkey:           Export CART3D .tkey.
        facet:          Export Xpatch .facet.
        vspgeom:        Export VSPGeom .vspgeom.
    """
    try:
        vsp = _vsp()
        # degen_set_index=-1 maps to SET_NONE
        dset = degen_set_index if degen_set_index >= 0 else vsp.SET_NONE

        file_types = 0
        format_map = [
            (stl, vsp.CFD_STL_TYPE, ".stl"),
            (gmsh, vsp.CFD_GMSH_TYPE, ".msh"),
            (obj, vsp.CFD_OBJ_TYPE, ".obj"),
            (dat, vsp.CFD_DAT_TYPE, ".dat"),
            (key, vsp.CFD_KEY_TYPE, ".key"),
            (tkey, vsp.CFD_TKEY_TYPE, ".tkey"),
            (facet, vsp.CFD_FACET_TYPE, ".facet"),
            (vspgeom, vsp.CFD_VSPGEOM_TYPE, ".vspgeom"),
        ]
        for enabled, ftype, ext in format_map:
            if enabled:
                file_types |= ftype

        vsp.ComputeCFDMesh(set_index, dset, file_types)
        return "CFD mesh computation complete."
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Import
# ===========================================================================


@mcp.tool()
def import_file(file_name: str, import_type: str, parent_id: str = "") -> str:
    """
    Import a geometry file into the current model.

    Args:
        file_name:   Absolute path to the file to import.
        import_type: Import type constant name, one of:
                     ``'IMPORT_STL'``, ``'IMPORT_NASCART'``,
                     ``'IMPORT_CART3D_TRI'``, ``'IMPORT_PTS'``,
                     ``'IMPORT_V2'`` (legacy OpenVSP v2), ``'IMPORT_BEM'``,
                     ``'IMPORT_XSEC_MESH'``, ``'IMPORT_XSEC_WIRE'``,
                     ``'IMPORT_P3D_WIRE'``.
        parent_id:   ID of the parent geometry (empty = top-level).

    Returns:
        The ID of the newly created geometry, or an empty string.
    """
    try:
        vsp = _vsp()
        itype = int(getattr(vsp, import_type))
        return vsp.ImportFile(file_name, itype, parent_id) or ""
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def import_stl(file_name: str, parent_id: str = "") -> str:
    """
    Import an STL file as geometry.

    Args:
        file_name: Absolute path to the .stl file.
        parent_id: ID of the parent geometry (empty = top-level).

    Returns:
        The geometry ID of the imported mesh.
    """
    try:
        vsp = _vsp()
        return vsp.ImportFile(file_name, vsp.IMPORT_STL, parent_id) or ""
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def import_v2(file_name: str, parent_id: str = "") -> str:
    """
    Import a legacy OpenVSP v2 model file (*.vsp) into the current model.

    Args:
        file_name: Absolute path to the .vsp file.
        parent_id: ID of the parent geometry (empty = top-level).

    Returns:
        The geometry ID of the imported component.
    """
    try:
        vsp = _vsp()
        return vsp.ImportFile(file_name, vsp.IMPORT_V2, parent_id) or ""
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def import_bem(file_name: str, parent_id: str = "") -> str:
    """
    Import a Blade Element Method file (*.bem) as a propeller geometry.

    Args:
        file_name: Absolute path to the .bem file.
        parent_id: ID of the parent geometry (empty = top-level).

    Returns:
        The geometry ID of the imported propeller.
    """
    try:
        vsp = _vsp()
        return vsp.ImportFile(file_name, vsp.IMPORT_BEM, parent_id) or ""
    except Exception as exc:
        return f"Error: {exc}"
