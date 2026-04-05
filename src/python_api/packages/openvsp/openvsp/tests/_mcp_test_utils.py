"""Shared test utilities for OpenVSP MCP server tests."""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import types
from unittest.mock import MagicMock, patch

_OPENVSP_DIR = pathlib.Path(__file__).parent.parent
_MCP_DIR = _OPENVSP_DIR / "mcp"


def _make_fake_vsp():
    """Return a MagicMock that mimics the openvsp module's public surface."""
    vsp = MagicMock(name="openvsp")

    vsp.GetVSPVersion.return_value = "3.49.0"
    vsp.GetVSPVersionMajor.return_value = 3
    vsp.GetVSPVersionMinor.return_value = 49
    vsp.GetVSPVersionChange.return_value = 0

    vsp.GetVSPFileName.return_value = "model.vsp3"

    vsp.GetGeomTypes.return_value = [
        "WING",
        "FUSELAGE",
        "POD",
        "PROPELLER",
        "ELLIPSOID",
    ]

    vsp.FindGeoms.return_value = ["geom1", "geom2"]
    vsp.FindGeomsWithName.return_value = ["geom1"]
    vsp.FindGeom.return_value = "geom1"
    vsp.AddGeom.return_value = "new_geom_id"
    vsp.GetGeomName.return_value = "Wing"
    vsp.GetGeomTypeName.return_value = "Wing"
    vsp.GetGeomParent.return_value = ""
    vsp.GetGeomChildren.return_value = ["child1"]
    vsp.GetGeomParmIDs.return_value = ["parm1", "parm2"]

    vsp.FindParm.return_value = "parm1"
    vsp.GetParmName.return_value = "Span"
    vsp.GetParmVal.return_value = 10.0
    vsp.SetParmVal.return_value = 10.0

    vsp.GetSetName.return_value = "SET_ALL"

    vsp.ListAnalysis.return_value = ["CompGeom", "MassProp", "VSPAEROSweep"]
    vsp.GetAnalysisDoc.return_value = "Computes geometry intersection."
    vsp.GetAnalysisInputNames.return_value = ["Set", "HalfMesh"]
    vsp.GetAnalysisInputDoc.return_value = "Geometry set index."
    vsp.ExecAnalysis.return_value = "results_abc123"

    vsp.GetAllResultsNames.return_value = ["CompGeom", "MassProp"]
    vsp.GetAllDataNames.return_value = ["Total_Wet_Area", "Total_Volume"]

    vsp.ComputeMassProps.return_value = "mass_results_id"
    vsp.ComputeCompGeom.return_value = "comp_geom_results"
    vsp.ComputeDegenGeom.return_value = None
    vsp.ComputeCFDMesh.return_value = None

    # Integer-valued export / import / computation type constants
    for attr in [
        "COMP_GEOM_CSV_TYPE",
        "COMP_GEOM_TXT_TYPE",
        "DEGEN_GEOM_CSV_TYPE",
        "DEGEN_GEOM_M_TYPE",
        "CFD_STL_TYPE",
        "CFD_GMSH_TYPE",
        "CFD_OBJ_TYPE",
        "CFD_DAT_TYPE",
        "CFD_KEY_TYPE",
        "CFD_TKEY_TYPE",
        "CFD_FACET_TYPE",
        "CFD_VSPGEOM_TYPE",
        "SET_NONE",
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
        "IMPORT_STL",
        "IMPORT_NASCART",
        "IMPORT_CART3D_TRI",
        "IMPORT_PTS",
        "IMPORT_V2",
        "IMPORT_BEM",
        "IMPORT_XSEC_MESH",
        "IMPORT_XSEC_WIRE",
        "IMPORT_P3D_WIRE",
    ]:
        setattr(vsp, attr, 0)

    vsp.ExportFile.return_value = ""
    vsp.ImportFile.return_value = "imported_geom_id"

    # XSec
    vsp.GetNumXSecSurfs.return_value = 1
    vsp.GetXSecSurf.return_value = "xsec_surf_1"
    vsp.GetNumXSec.return_value = 4
    vsp.GetXSec.return_value = "xsec_id_1"
    vsp.GetXSecShape.return_value = 7  # XS_FOUR_SERIES
    vsp.GetXSecWidth.return_value = 1.5
    vsp.GetXSecHeight.return_value = 0.5

    # SubSurface
    vsp.AddSubSurf.return_value = "ss_id_1"
    vsp.GetSubSurf.return_value = "ss_id_1"
    vsp.GetSubSurfIDVec.return_value = ["ss_id_1", "ss_id_2"]
    vsp.GetAllSubSurfIDs.return_value = ["ss_id_1", "ss_id_2", "ss_id_3"]
    vsp.GetNumSubSurf.return_value = 2
    vsp.GetSubSurfType.return_value = 3  # SS_CONTROL
    vsp.GetSubSurfName.return_value = "Aileron"
    vsp.GetSubSurfIndex.return_value = 1
    vsp.GetSubSurfParmIDs.return_value = ["sp1", "sp2"]

    # Group transforms - vec3d mock
    _mock_vec3d = MagicMock()
    vsp.vec3d.return_value = _mock_vec3d

    # Variable presets
    vsp.GetVarPresetGroups.return_value = ["grp1", "grp2"]
    vsp.AddVarPresetGroup.return_value = "grp_new"
    vsp.GetVarPresetSettings.return_value = ["set1", "set2"]
    vsp.AddVarPresetSetting.return_value = "set_new"
    vsp.GetVarPresetParmIDs.return_value = ["parm1", "parm2"]
    vsp.GetVarPresetParmVal.return_value = 5.0

    # VSPAERO CS groups
    vsp.GetNumControlSurfaceGroups.return_value = 3
    vsp.CreateVSPAEROControlSurfaceGroup.return_value = 3
    vsp.GetVSPAEROControlGroupName.return_value = "Aileron_Group"

    # Surface query - vec3d return values
    def _make_vec3d(x, y, z):
        v = MagicMock()
        v.x.return_value = x
        v.y.return_value = y
        v.z.return_value = z
        return v

    vsp.GetGeomBBoxMin.return_value = _make_vec3d(-1.0, -5.0, 0.0)
    vsp.GetGeomBBoxMax.return_value = _make_vec3d(1.0, 5.0, 2.0)
    vsp.CompPnt01.return_value = _make_vec3d(0.5, 2.0, 1.0)
    vsp.CompNorm01.return_value = _make_vec3d(0.0, 0.0, 1.0)
    vsp.CompTanU01.return_value = _make_vec3d(1.0, 0.0, 0.0)
    vsp.CompTanW01.return_value = _make_vec3d(0.0, 1.0, 0.0)
    vsp.ProjPnt01.return_value = (0.02, 0.3, 0.7)

    # FEA
    vsp.NumFeaStructures.return_value = 2
    vsp.GetFeaStructIDVec.return_value = ["fea_s1", "fea_s2"]
    vsp.AddFeaStruct.return_value = 0
    vsp.GetFeaStructID.return_value = "fea_s1"
    vsp.GetFeaStructName.return_value = "WingStruct"
    vsp.NumFeaParts.return_value = 3
    vsp.GetFeaPartIDVec.return_value = ["fp1", "fp2", "fp3"]
    vsp.AddFeaPart.return_value = "fp_new"
    vsp.GetFeaPartName.return_value = "Rib_1"
    vsp.GetFeaPartType.return_value = 1  # FEA_RIB
    vsp.NumFeaSubSurfs.return_value = 1
    vsp.GetFeaSubSurfIDVec.return_value = ["fss1"]
    vsp.AddFeaSubSurf.return_value = "fss_new"
    vsp.AddFeaMaterial.return_value = "mat1"
    vsp.AddFeaProperty.return_value = "prop1"
    vsp.GetFeaPartPerpendicularSparID.return_value = "fp2"
    for attr in [
        "FEA_SLICE",
        "FEA_RIB",
        "FEA_SPAR",
        "FEA_FIX_POINT",
        "FEA_DOME",
        "FEA_RIB_ARRAY",
        "FEA_SLICE_ARRAY",
        "FEA_SKIN",
        "FEA_TRIM",
        "SS_LINE",
        "SS_RECTANGLE",
        "SS_ELLIPSE",
        "SS_CONTROL",
        "SS_LINE_ARRAY",
        "XS_CIRCLE",
        "XS_FOUR_SERIES",
        "XS_FILE_AIRFOIL",
        "XSEC_BOTH_SIDES",
        "XSEC_TOP",
        "XSEC_BOTTOM",
    ]:
        setattr(vsp, attr, 0)

    # PCurve
    vsp.PCurveGetTVec.return_value = [0.0, 0.5, 1.0]
    vsp.PCurveGetValVec.return_value = [1.0, 0.8, 0.5]
    vsp.PCurveGetType.return_value = 2
    vsp.PCurveSplit.return_value = 2

    # Advanced Links
    vsp.GetAdvLinkNames = MagicMock(return_value=["Link1"])
    vsp.AddAdvLink = MagicMock()
    vsp.DelAdvLink = MagicMock()
    vsp.DelAllAdvLinks = MagicMock()
    vsp.AddAdvLinkInput = MagicMock()
    vsp.AddAdvLinkOutput = MagicMock()
    vsp.DelAdvLinkInput = MagicMock()
    vsp.DelAdvLinkOutput = MagicMock()
    vsp.GetAdvLinkInputNames = MagicMock(return_value=["len"])
    vsp.GetAdvLinkOutputNames = MagicMock(return_value=["x"])
    vsp.GetAdvLinkInputParms = MagicMock(return_value=["parm1"])
    vsp.GetAdvLinkOutputParms = MagicMock(return_value=["parm2"])
    vsp.SetAdvLinkCode = MagicMock()
    vsp.GetAdvLinkCode = MagicMock(return_value="x = 10.0 - len;")
    vsp.BuildAdvLinkScript = MagicMock(return_value=True)
    vsp.ValidateAdvLinkParms = MagicMock(return_value=True)
    vsp.SearchReplaceAdvLinkCode = MagicMock()

    # CFD (low-level)
    vsp.SetCFDMeshVal = MagicMock()
    vsp.DeleteAllCFDSources = MagicMock()
    vsp.SetCFDWakeFlag = MagicMock()
    vsp.AddCFDSource = MagicMock()

    # Analysis (extended)
    vsp.GetNumAnalysis = MagicMock(return_value=5)
    vsp.SetAnalysisInputDefaults = MagicMock()
    vsp.SetIntAnalysisInput = MagicMock()
    vsp.SetDoubleAnalysisInput = MagicMock()
    vsp.SetStringAnalysisInput = MagicMock()
    vsp.GetIntAnalysisInput = MagicMock(return_value=[1])
    vsp.GetDoubleAnalysisInput = MagicMock(return_value=[1.0])
    vsp.GetStringAnalysisInput = MagicMock(return_value=["str1"])
    vsp.GetResultsName = MagicMock(return_value="VSPAEROSweep")
    vsp.GetResultsType = MagicMock(return_value=1)

    return vsp


def _load_submodule(fake_vsp, submodule_file: str):
    """
    Load a specific MCP submodule with VSP replaced by fake_vsp.
    """
    # Remove any previously loaded openvsp.mcp.* modules to avoid conflicts
    for key in list(sys.modules.keys()):
        if key.startswith("openvsp.mcp"):
            del sys.modules[key]
    if "openvsp" in sys.modules:
        del sys.modules["openvsp"]

    # Load _core.py — creates real FastMCP instance, _vsp() is lazy
    core_path = str(_MCP_DIR / "_core.py")
    core_spec = importlib.util.spec_from_file_location(
        "openvsp.mcp._core", core_path
    )
    core_mod = importlib.util.module_from_spec(core_spec)
    sys.modules["openvsp.mcp._core"] = core_mod
    core_spec.loader.exec_module(core_mod)

    # Override _vsp to return fake_vsp
    core_mod._vsp = lambda: fake_vsp

    # Create a minimal openvsp.mcp package namespace
    fake_mcp_pkg = types.ModuleType("openvsp.mcp")
    fake_mcp_pkg.mcp = core_mod.mcp
    fake_mcp_pkg._core = core_mod

    # Patch sys.modules so submodule imports resolve correctly
    sys.modules["openvsp"] = fake_vsp
    sys.modules["openvsp.mcp"] = fake_mcp_pkg

    # Load the target submodule
    submodule_name = os.path.splitext(os.path.basename(submodule_file))[0]
    spec = importlib.util.spec_from_file_location(
        f"openvsp.mcp.{submodule_name}",
        submodule_file,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"openvsp.mcp.{submodule_name}"] = mod
    spec.loader.exec_module(mod)

    # Return both the module and the mcp instance for tool lookup
    mod._mcp = core_mod.mcp
    return mod


def _load_full_server(fake_vsp):
    """Load the complete MCP server (all submodules) for integration-style tests."""
    # Remove any previously loaded openvsp.mcp.* modules to avoid conflicts
    for key in list(sys.modules.keys()):
        if key.startswith("openvsp.mcp"):
            del sys.modules[key]
    if "openvsp" in sys.modules:
        del sys.modules["openvsp"]

    # Load _core.py
    core_path = str(_MCP_DIR / "_core.py")
    core_spec = importlib.util.spec_from_file_location(
        "openvsp.mcp._core", core_path
    )
    core_mod = importlib.util.module_from_spec(core_spec)
    sys.modules["openvsp.mcp._core"] = core_mod
    core_spec.loader.exec_module(core_mod)

    # Override _vsp to return fake_vsp
    core_mod._vsp = lambda: fake_vsp

    fake_mcp_pkg = types.ModuleType("openvsp.mcp")
    fake_mcp_pkg.mcp = core_mod.mcp
    fake_mcp_pkg._core = core_mod

    sys.modules["openvsp"] = fake_vsp
    sys.modules["openvsp.mcp"] = fake_mcp_pkg

    submodules = [
        "_geometry",
        "_analysis",
        "_io",
        "_xsec",
        "_transforms",
        "_surface",
        "_fea",
        "_misc",
    ]
    for name in submodules:
        path = str(_MCP_DIR / f"{name}.py")
        spec = importlib.util.spec_from_file_location(
            f"openvsp.mcp.{name}", path
        )
        sub_mod = importlib.util.module_from_spec(spec)
        sys.modules[f"openvsp.mcp.{name}"] = sub_mod
        spec.loader.exec_module(sub_mod)
        setattr(fake_mcp_pkg, name, sub_mod)

    return core_mod.mcp
