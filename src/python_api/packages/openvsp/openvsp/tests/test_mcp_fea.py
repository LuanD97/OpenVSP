"""Tests for MCP FEA Mesh and Structural Parts tools."""
from __future__ import annotations

import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(pathlib.Path(__file__).parent.parent / "mcp" / "_fea.py")


class TestMCPFEA(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)

    # ------------------------------------------------------------------
    # FEA
    # ------------------------------------------------------------------

    def test_num_fea_structures(self):
        self.assertEqual(self.mod.num_fea_structures(), 2)

    def test_get_fea_struct_id_vec(self):
        result = self.mod.get_fea_struct_id_vec()
        self.assertIn("fea_s1", result)

    def test_add_fea_struct(self):
        result = self.mod.add_fea_struct("geom1")
        self.fake_vsp.AddFeaStruct.assert_called_once_with("geom1", True, 0)
        self.assertEqual(result, 0)

    def test_delete_fea_struct(self):
        result = self.mod.delete_fea_struct("geom1", 0)
        self.fake_vsp.DeleteFeaStruct.assert_called_once_with("geom1", 0)
        self.assertIn("geom1", result)

    def test_get_fea_struct_id(self):
        result = self.mod.get_fea_struct_id("geom1", 0)
        self.assertEqual(result, "fea_s1")

    def test_get_fea_struct_name(self):
        self.assertEqual(self.mod.get_fea_struct_name("geom1", 0), "WingStruct")

    def test_set_fea_struct_name(self):
        result = self.mod.set_fea_struct_name("geom1", 0, "WingBox")
        self.assertIn("WingBox", result)

    def test_num_fea_parts(self):
        self.assertEqual(self.mod.num_fea_parts("fea_s1"), 3)

    def test_get_fea_part_id_vec(self):
        result = self.mod.get_fea_part_id_vec("fea_s1")
        self.assertEqual(result, ["fp1", "fp2", "fp3"])

    def test_add_fea_part(self):
        result = self.mod.add_fea_part("geom1", 0, "FEA_RIB")
        self.fake_vsp.AddFeaPart.assert_called_once()
        self.assertEqual(result, "fp_new")

    def test_delete_fea_part(self):
        result = self.mod.delete_fea_part("geom1", 0, "fp1")
        self.fake_vsp.DeleteFeaPart.assert_called_once_with("geom1", 0, "fp1")

    def test_get_fea_part_name(self):
        self.assertEqual(self.mod.get_fea_part_name("fp1"), "Rib_1")

    def test_set_fea_part_name(self):
        result = self.mod.set_fea_part_name("fp1", "FrontRib")
        self.assertIn("FrontRib", result)

    def test_get_fea_part_type_returns_name(self):
        self.fake_vsp.GetFeaPartType.return_value = 1  # FEA_RIB
        result = self.mod.get_fea_part_type("fp1")
        self.assertEqual(result, "FEA_RIB")

    def test_num_fea_sub_surfs(self):
        self.assertEqual(self.mod.num_fea_sub_surfs("fea_s1"), 1)

    def test_get_fea_sub_surf_id_vec(self):
        result = self.mod.get_fea_sub_surf_id_vec("fea_s1")
        self.assertEqual(result, ["fss1"])

    def test_add_fea_sub_surf(self):
        result = self.mod.add_fea_sub_surf("geom1", 0, "SS_LINE")
        self.fake_vsp.AddFeaSubSurf.assert_called_once()
        self.assertEqual(result, "fss_new")

    def test_delete_fea_sub_surf(self):
        result = self.mod.delete_fea_sub_surf("geom1", 0, "fss1")
        self.fake_vsp.DeleteFeaSubSurf.assert_called_once_with("geom1", 0, "fss1")

    def test_add_fea_material(self):
        result = self.mod.add_fea_material()
        self.fake_vsp.AddFeaMaterial.assert_called_once()
        self.assertEqual(result, "mat1")

    def test_add_fea_property(self):
        result = self.mod.add_fea_property(0)
        self.fake_vsp.AddFeaProperty.assert_called_once_with(0)
        self.assertEqual(result, "prop1")

    def test_compute_fea_mesh(self):
        result = self.mod.compute_fea_mesh("fea_s1")
        self.fake_vsp.ComputeFeaMesh.assert_called_once_with("fea_s1", 0)
        self.assertIn("complete", result.lower())

    def test_set_fea_part_perpendicular_spar_id(self):
        result = self.mod.set_fea_part_perpendicular_spar_id("fp1", "fp2")
        self.fake_vsp.SetFeaPartPerpendicularSparID.assert_called_once_with("fp1", "fp2")

    def test_get_fea_part_perpendicular_spar_id(self):
        result = self.mod.get_fea_part_perpendicular_spar_id("fp1")
        self.assertEqual(result, "fp2")


if __name__ == "__main__":
    unittest.main()
