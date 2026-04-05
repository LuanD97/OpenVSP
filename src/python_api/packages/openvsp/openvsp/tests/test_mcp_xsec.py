"""Tests for MCP XSec, Airfoil, and Sub-Surface tools."""

from __future__ import annotations

import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(pathlib.Path(__file__).parent.parent / "mcp" / "_xsec.py")


class TestMCPXSec(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)

    # ------------------------------------------------------------------
    # XSec / Airfoil
    # ------------------------------------------------------------------

    def test_get_num_xsec_surfs(self):
        self.assertEqual(self.mod.get_num_xsec_surfs("geom1"), 1)
        self.fake_vsp.GetNumXSecSurfs.assert_called_once_with("geom1")

    def test_get_xsec_surf(self):
        result = self.mod.get_xsec_surf("geom1", 0)
        self.fake_vsp.GetXSecSurf.assert_called_once_with("geom1", 0)
        self.assertEqual(result, "xsec_surf_1")

    def test_get_num_xsec(self):
        self.assertEqual(self.mod.get_num_xsec("xsec_surf_1"), 4)

    def test_get_xsec(self):
        result = self.mod.get_xsec("xsec_surf_1", 2)
        self.fake_vsp.GetXSec.assert_called_with("xsec_surf_1", 2)
        self.assertEqual(result, "xsec_id_1")

    def test_cut_xsec(self):
        result = self.mod.cut_xsec("geom1", 1)
        self.fake_vsp.CutXSec.assert_called_once_with("geom1", 1)
        self.assertIn("1", result)

    def test_copy_xsec(self):
        self.mod.copy_xsec("geom1", 0)
        self.fake_vsp.CopyXSec.assert_called_once_with("geom1", 0)

    def test_paste_xsec(self):
        result = self.mod.paste_xsec("geom1", 2)
        self.fake_vsp.PasteXSec.assert_called_once_with("geom1", 2)
        self.assertIn("2", result)

    def test_change_xsec_shape(self):
        result = self.mod.change_xsec_shape("xsec_surf_1", 1, "XS_CIRCLE")
        self.fake_vsp.ChangeXSecShape.assert_called_once()
        self.assertIn("XS_CIRCLE", result)

    def test_get_xsec_shape_returns_name(self):
        self.fake_vsp.GetXSecShape.return_value = 7
        result = self.mod.get_xsec_shape("xsec_id_1")
        self.assertEqual(result, "XS_FOUR_SERIES")

    def test_get_xsec_width(self):
        self.assertAlmostEqual(self.mod.get_xsec_width("xsec_id_1"), 1.5)

    def test_get_xsec_height(self):
        self.assertAlmostEqual(self.mod.get_xsec_height("xsec_id_1"), 0.5)

    def test_set_xsec_width(self):
        result = self.mod.set_xsec_width("xsec_id_1", 2.0)
        self.fake_vsp.SetXSecWidth.assert_called_once_with("xsec_id_1", 2.0)
        self.assertIn("2.0", result)

    def test_set_xsec_height(self):
        result = self.mod.set_xsec_height("xsec_id_1", 0.8)
        self.fake_vsp.SetXSecHeight.assert_called_once_with("xsec_id_1", 0.8)

    def test_set_xsec_width_height(self):
        result = self.mod.set_xsec_width_height("xsec_id_1", 2.0, 0.8)
        self.fake_vsp.SetXSecWidthHeight.assert_called_once_with(
            "xsec_id_1", 2.0, 0.8
        )

    def test_set_xsec_tan_angles(self):
        result = self.mod.set_xsec_tan_angles(
            "xsec_id_1", "XSEC_BOTH_SIDES", 90.0
        )
        self.fake_vsp.SetXSecTanAngles.assert_called_once()
        self.assertIn("XSEC_BOTH_SIDES", result)

    def test_read_file_airfoil(self):
        result = self.mod.read_file_airfoil("xsec_id_1", "/tmp/naca2412.dat")
        self.fake_vsp.ReadFileAirfoil.assert_called_once_with(
            "xsec_id_1", "/tmp/naca2412.dat"
        )
        self.assertIn("naca2412", result)

    # ------------------------------------------------------------------
    # Sub-surfaces
    # ------------------------------------------------------------------

    def test_add_sub_surf(self):
        result = self.mod.add_sub_surf("geom1", "SS_CONTROL")
        self.fake_vsp.AddSubSurf.assert_called_once()
        self.assertEqual(result, "ss_id_1")

    def test_delete_sub_surf(self):
        result = self.mod.delete_sub_surf("ss_id_1")
        self.fake_vsp.DeleteSubSurf.assert_called_once_with("ss_id_1")
        self.assertIn("ss_id_1", result)

    def test_get_sub_surf_by_index(self):
        result = self.mod.get_sub_surf_by_index("geom1", 0)
        self.fake_vsp.GetSubSurf.assert_called_with("geom1", 0)
        self.assertEqual(result, "ss_id_1")

    def test_get_sub_surf_by_name(self):
        self.fake_vsp.GetSubSurf.return_value = ["ss_id_1"]
        result = self.mod.get_sub_surf_by_name("geom1", "Aileron")
        self.assertIsInstance(result, list)

    def test_get_sub_surf_id_vec(self):
        result = self.mod.get_sub_surf_id_vec("geom1")
        self.assertEqual(result, ["ss_id_1", "ss_id_2"])

    def test_get_all_sub_surf_ids(self):
        result = self.mod.get_all_sub_surf_ids()
        self.assertIn("ss_id_1", result)

    def test_get_num_sub_surf(self):
        self.assertEqual(self.mod.get_num_sub_surf("geom1"), 2)

    def test_get_sub_surf_type_returns_name(self):
        self.fake_vsp.GetSubSurfType.return_value = 3  # SS_CONTROL
        result = self.mod.get_sub_surf_type("ss_id_1")
        self.assertEqual(result, "SS_CONTROL")

    def test_get_sub_surf_name(self):
        self.assertEqual(self.mod.get_sub_surf_name("ss_id_1"), "Aileron")

    def test_set_sub_surf_name(self):
        result = self.mod.set_sub_surf_name("ss_id_1", "Flap")
        self.fake_vsp.SetSubSurfName.assert_called_once_with("ss_id_1", "Flap")
        self.assertIn("Flap", result)

    def test_get_sub_surf_index(self):
        self.assertEqual(self.mod.get_sub_surf_index("ss_id_1"), 1)

    def test_get_sub_surf_parm_ids(self):
        result = self.mod.get_sub_surf_parm_ids("ss_id_1")
        self.assertEqual(result, ["sp1", "sp2"])


if __name__ == "__main__":
    unittest.main()
