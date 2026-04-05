"""Tests for MCP parasite drag, PCurve, Advanced Links, and CFD Mesh tools."""

from __future__ import annotations

import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(pathlib.Path(__file__).parent.parent / "mcp" / "_misc.py")


class TestMCPMisc(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)

    # ------------------------------------------------------------------
    # Parasite drag
    # ------------------------------------------------------------------

    def test_add_excrescence(self):
        result = self.mod.add_excrescence("Antenna", 0, 5.0)
        self.fake_vsp.AddExcrescence.assert_called_once_with("Antenna", 0, 5.0)
        self.assertIn("Antenna", result)

    def test_delete_excrescence(self):
        result = self.mod.delete_excrescence(0)
        self.fake_vsp.DeleteExcrescence.assert_called_once_with(0)
        self.assertIn("0", result)

    def test_update_parasite_drag(self):
        result = self.mod.update_parasite_drag()
        self.fake_vsp.UpdateParasiteDrag.assert_called_once()
        self.assertIn("updated", result.lower())

    # ------------------------------------------------------------------
    # PCurve
    # ------------------------------------------------------------------

    def test_set_pcurve(self):
        result = self.mod.set_pcurve("prop1", 0, [0.0, 1.0], [1.0, 0.5], 2)
        self.fake_vsp.SetPCurve.assert_called_once_with(
            "prop1", 0, [0.0, 1.0], [1.0, 0.5], 2
        )
        self.assertIn("0", result)

    def test_pcurve_get_tvec(self):
        result = self.mod.pcurve_get_tvec("prop1", 0)
        self.assertEqual(result, [0.0, 0.5, 1.0])

    def test_pcurve_get_val_vec(self):
        result = self.mod.pcurve_get_val_vec("prop1", 1)
        self.assertEqual(result, [1.0, 0.8, 0.5])

    def test_pcurve_get_type(self):
        self.assertEqual(self.mod.pcurve_get_type("prop1", 0), 2)

    def test_pcurve_convert_to(self):
        result = self.mod.pcurve_convert_to("prop1", 0, 1)
        self.fake_vsp.PCurveConvertTo.assert_called_once_with("prop1", 0, 1)
        self.assertIn("1", result)

    def test_pcurve_delete_pt(self):
        result = self.mod.pcurve_delete_pt("prop1", 0, 1)
        self.fake_vsp.PCurveDeletePt.assert_called_once_with("prop1", 0, 1)

    def test_pcurve_split(self):
        result = self.mod.pcurve_split("prop1", 0, 0.5)
        self.fake_vsp.PCurveSplit.assert_called_once_with("prop1", 0, 0.5)
        self.assertEqual(result, 2)

    def test_approximate_all_propeller_pcurves(self):
        result = self.mod.approximate_all_propeller_pcurves("prop1")
        self.fake_vsp.ApproximateAllPropellerPCurves.assert_called_once_with(
            "prop1"
        )
        self.assertIn("prop1", result)

    def test_set_pcurve_length_mismatch(self):
        result = self.mod.set_pcurve("prop1", 0, [0.0, 1.0], [1.0], 2)
        self.assertIn("Error", result)
        self.fake_vsp.SetPCurve.assert_not_called()

    # ------------------------------------------------------------------
    # Advanced Links
    # ------------------------------------------------------------------

    def test_get_adv_link_names(self):
        result = self.mod.get_adv_link_names()
        self.fake_vsp.GetAdvLinkNames.assert_called_once()
        self.assertEqual(result, ["Link1"])

    def test_add_adv_link(self):
        result = self.mod.add_adv_link("MyLink")
        self.fake_vsp.AddAdvLink.assert_called_once_with("MyLink")
        self.assertIn("MyLink", result)

    def test_del_adv_link(self):
        result = self.mod.del_adv_link(0)
        self.fake_vsp.DelAdvLink.assert_called_once_with(0)
        self.assertIn("0", result)

    def test_del_all_adv_links(self):
        result = self.mod.del_all_adv_links()
        self.fake_vsp.DelAllAdvLinks.assert_called_once()
        self.assertIn("all", result.lower())

    def test_add_adv_link_input(self):
        result = self.mod.add_adv_link_input(0, "parm1", "len")
        self.fake_vsp.AddAdvLinkInput.assert_called_once_with(0, "parm1", "len")
        self.assertIn("len", result)

    def test_add_adv_link_output(self):
        result = self.mod.add_adv_link_output(0, "parm2", "x")
        self.fake_vsp.AddAdvLinkOutput.assert_called_once_with(0, "parm2", "x")
        self.assertIn("x", result)

    def test_del_adv_link_input(self):
        result = self.mod.del_adv_link_input(0, "len")
        self.fake_vsp.DelAdvLinkInput.assert_called_once_with(0, "len")
        self.assertIn("len", result)

    def test_del_adv_link_output(self):
        result = self.mod.del_adv_link_output(0, "x")
        self.fake_vsp.DelAdvLinkOutput.assert_called_once_with(0, "x")
        self.assertIn("x", result)

    def test_get_adv_link_input_names(self):
        result = self.mod.get_adv_link_input_names(0)
        self.fake_vsp.GetAdvLinkInputNames.assert_called_once_with(0)
        self.assertEqual(result, ["len"])

    def test_get_adv_link_output_names(self):
        result = self.mod.get_adv_link_output_names(0)
        self.fake_vsp.GetAdvLinkOutputNames.assert_called_once_with(0)
        self.assertEqual(result, ["x"])

    def test_get_adv_link_input_parms(self):
        result = self.mod.get_adv_link_input_parms(0)
        self.fake_vsp.GetAdvLinkInputParms.assert_called_once_with(0)
        self.assertEqual(result, ["parm1"])

    def test_get_adv_link_output_parms(self):
        result = self.mod.get_adv_link_output_parms(0)
        self.fake_vsp.GetAdvLinkOutputParms.assert_called_once_with(0)
        self.assertEqual(result, ["parm2"])

    def test_set_adv_link_code(self):
        result = self.mod.set_adv_link_code(0, "x = 10.0 - len;")
        self.fake_vsp.SetAdvLinkCode.assert_called_once_with(
            0, "x = 10.0 - len;"
        )
        self.assertIn("0", result)

    def test_get_adv_link_code(self):
        result = self.mod.get_adv_link_code(0)
        self.fake_vsp.GetAdvLinkCode.assert_called_once_with(0)
        self.assertEqual(result, "x = 10.0 - len;")

    def test_build_adv_link_script(self):
        result = self.mod.build_adv_link_script(0)
        self.fake_vsp.BuildAdvLinkScript.assert_called_once_with(0)
        self.assertIn("True", result)

    def test_validate_adv_link_parms(self):
        result = self.mod.validate_adv_link_parms(0)
        self.fake_vsp.ValidateAdvLinkParms.assert_called_once_with(0)
        self.assertIn("True", result)

    def test_search_replace_adv_link_code(self):
        result = self.mod.search_replace_adv_link_code(0, "10.0", "20.0")
        self.fake_vsp.SearchReplaceAdvLinkCode.assert_called_once_with(
            0, "10.0", "20.0"
        )
        self.assertIn("0", result)

    # ------------------------------------------------------------------
    # CFD (low-level)
    # ------------------------------------------------------------------

    def test_set_cfd_mesh_val(self):
        result = self.mod.set_cfd_mesh_val(1, 0.5)
        self.fake_vsp.SetCFDMeshVal.assert_called_once_with(1, 0.5)
        self.assertIn("0.5", result)

    def test_delete_all_cfd_sources(self):
        result = self.mod.delete_all_cfd_sources()
        self.fake_vsp.DeleteAllCFDSources.assert_called_once()
        self.assertIn("Deleted", result)

    def test_set_cfd_wake_flag(self):
        result = self.mod.set_cfd_wake_flag("geom1", True)
        self.fake_vsp.SetCFDWakeFlag.assert_called_once_with("geom1", True)
        self.assertIn("geom1", result)

    def test_add_cfd_source(self):
        result = self.mod.add_cfd_source(0, "geom1", 0, 0.5, 0.1, 0.5, 0.5)
        self.fake_vsp.AddCFDSource.assert_called_once_with(
            0, "geom1", 0, 0.5, 0.1, 0.5, 0.5
        )
        self.assertIn("geom1", result)


if __name__ == "__main__":
    unittest.main()
