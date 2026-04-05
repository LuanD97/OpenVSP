"""Tests for MCP file export and import tools."""

from __future__ import annotations

import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(pathlib.Path(__file__).parent.parent / "mcp" / "_io.py")


class TestMCPIO(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def test_list_export_types(self):
        result = self.mod.list_export_types()
        self.assertIn("EXPORT_STL", result)
        self.assertIn("EXPORT_STEP", result)
        self.assertIn("EXPORT_IGES", result)

    def test_export_file(self):
        self.mod.export_file("/tmp/out.stl", "EXPORT_STL", set_index=0)
        self.fake_vsp.ExportFile.assert_called()

    def test_export_stl(self):
        self.mod.export_stl("/tmp/out.stl")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_obj(self):
        self.mod.export_obj("/tmp/out.obj")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_step(self):
        self.mod.export_step("/tmp/out.stp")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_iges(self):
        self.mod.export_iges("/tmp/out.igs")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_gmsh(self):
        self.mod.export_gmsh("/tmp/out.msh")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_dxf(self):
        self.mod.export_dxf("/tmp/out.dxf")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_svg(self):
        self.mod.export_svg("/tmp/out.svg")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_x3d(self):
        self.mod.export_x3d("/tmp/out.x3d")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_plot3d(self):
        self.mod.export_plot3d("/tmp/out.p3d")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_cart3d(self):
        self.mod.export_cart3d("/tmp/out.tri")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_nascart(self):
        self.mod.export_nascart("/tmp/out.dat")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_vspgeom(self):
        self.mod.export_vspgeom("/tmp/out.vspgeom")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_bem(self):
        self.mod.export_bem("/tmp/out.bem", "prop_geom_id")
        self.fake_vsp.SetBEMPropID.assert_called_once_with("prop_geom_id")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_selig_airfoil(self):
        self.mod.export_selig_airfoil("/tmp/out.dat")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_bezier_airfoil(self):
        self.mod.export_bezier_airfoil("/tmp/out.bz")
        self.fake_vsp.ExportFile.assert_called()

    def test_export_xsec(self):
        self.mod.export_xsec("/tmp/out.hrm")
        self.fake_vsp.ExportFile.assert_called()

    # ------------------------------------------------------------------
    # Computation-based exports
    # ------------------------------------------------------------------

    def test_compute_comp_geom(self):
        result = self.mod.compute_comp_geom("/tmp/comp", csv=True, txt=False)
        self.fake_vsp.ComputeCompGeom.assert_called()
        self.assertIsInstance(result, str)

    def test_compute_degen_geom(self):
        result = self.mod.compute_degen_geom("/tmp/degen", csv=True)
        self.fake_vsp.ComputeDegenGeom.assert_called()
        self.assertIn("complete", result.lower())

    def test_compute_cfd_mesh(self):
        result = self.mod.compute_cfd_mesh("/tmp/cfd", stl=True)
        self.fake_vsp.ComputeCFDMesh.assert_called()
        self.assertIn("complete", result.lower())

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def test_import_stl(self):
        result = self.mod.import_stl("/tmp/mesh.stl")
        self.fake_vsp.ImportFile.assert_called()
        self.assertEqual(result, "imported_geom_id")

    def test_import_v2(self):
        self.assertEqual(self.mod.import_v2("/tmp/old.vsp"), "imported_geom_id")

    def test_import_bem(self):
        self.assertEqual(
            self.mod.import_bem("/tmp/prop.bem"), "imported_geom_id"
        )

    def test_import_file_by_type_name(self):
        result = self.mod.import_file("/tmp/mesh.stl", "IMPORT_STL")
        self.fake_vsp.ImportFile.assert_called()
        self.assertEqual(result, "imported_geom_id")


if __name__ == "__main__":
    unittest.main()
