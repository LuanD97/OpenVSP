"""Tests for MCP geometry, model I/O, and parameter tools."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(pathlib.Path(__file__).parent.parent / "mcp" / "_geometry.py")


class TestMCPGeometry(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)

    # ------------------------------------------------------------------
    # Version
    # ------------------------------------------------------------------

    def test_get_vsp_version(self):
        result = self.mod.get_vsp_version()
        self.assertEqual(result["version"], "3.49.0")
        self.assertEqual(result["major"], 3)
        self.assertEqual(result["minor"], 49)
        self.assertEqual(result["change"], 0)

    # ------------------------------------------------------------------
    # Model I/O
    # ------------------------------------------------------------------

    def test_clear_model(self):
        result = self.mod.clear_model()
        self.fake_vsp.ClearVSPModel.assert_called_once()
        self.assertIn("cleared", result.lower())

    def test_read_vsp_file(self):
        result = self.mod.read_vsp_file("/tmp/test.vsp3")
        self.fake_vsp.ReadVSPFile.assert_called_once_with("/tmp/test.vsp3")
        self.assertIn("test.vsp3", result)

    def test_write_vsp_file(self):
        result = self.mod.write_vsp_file("/tmp/out.vsp3", set_index=1)
        self.fake_vsp.WriteVSPFile.assert_called_once_with("/tmp/out.vsp3", 1)
        self.assertIn("out.vsp3", result)

    def test_get_vsp_filename(self):
        self.assertEqual(self.mod.get_vsp_filename(), "model.vsp3")

    # ------------------------------------------------------------------
    # Geometry types
    # ------------------------------------------------------------------

    def test_get_geom_types(self):
        result = self.mod.get_geom_types()
        self.assertIn("WING", result)
        self.assertIn("FUSELAGE", result)

    # ------------------------------------------------------------------
    # Geometry management
    # ------------------------------------------------------------------

    def test_find_geoms(self):
        self.assertEqual(self.mod.find_geoms(), ["geom1", "geom2"])

    def test_find_geoms_with_name(self):
        result = self.mod.find_geoms_with_name("Wing")
        self.fake_vsp.FindGeomsWithName.assert_called_once_with("Wing")
        self.assertEqual(result, ["geom1"])

    def test_find_geom(self):
        result = self.mod.find_geom("Wing", index=0)
        self.fake_vsp.FindGeom.assert_called_once_with("Wing", 0)
        self.assertEqual(result, "geom1")

    def test_add_geom(self):
        result = self.mod.add_geom("WING", parent_id="")
        self.fake_vsp.AddGeom.assert_called_once_with("WING", "")
        self.assertEqual(result, "new_geom_id")

    def test_delete_geom(self):
        result = self.mod.delete_geom("geom1")
        self.fake_vsp.DeleteGeom.assert_called_once_with("geom1")
        self.assertIn("geom1", result)

    def test_get_geom_name(self):
        self.assertEqual(self.mod.get_geom_name("geom1"), "Wing")

    def test_set_geom_name(self):
        result = self.mod.set_geom_name("geom1", "MainWing")
        self.fake_vsp.SetGeomName.assert_called_once_with("geom1", "MainWing")
        self.assertIn("MainWing", result)

    def test_get_geom_type_name(self):
        self.assertEqual(self.mod.get_geom_type_name("geom1"), "Wing")

    def test_get_geom_parent(self):
        self.assertEqual(self.mod.get_geom_parent("geom1"), "")

    def test_get_geom_children(self):
        self.assertEqual(self.mod.get_geom_children("geom1"), ["child1"])

    def test_get_geom_parm_ids(self):
        self.assertEqual(
            self.mod.get_geom_parm_ids("geom1"), ["parm1", "parm2"]
        )

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------

    def test_find_parm(self):
        result = self.mod.find_parm("geom1", "Span", "WingGeom")
        self.fake_vsp.FindParm.assert_called_once_with(
            "geom1", "Span", "WingGeom"
        )
        self.assertEqual(result, "parm1")

    def test_get_parm_name(self):
        self.assertEqual(self.mod.get_parm_name("parm1"), "Span")

    def test_get_parm_val(self):
        self.assertAlmostEqual(self.mod.get_parm_val("parm1"), 10.0)

    def test_get_parm_val_by_name(self):
        result = self.mod.get_parm_val_by_name("geom1", "Span", "WingGeom")
        self.fake_vsp.GetParmVal.assert_called_with("geom1", "Span", "WingGeom")
        self.assertAlmostEqual(result, 10.0)

    def test_set_parm_val(self):
        self.mod.set_parm_val("parm1", 20.0)
        self.fake_vsp.SetParmVal.assert_called_with("parm1", 20.0)

    def test_set_parm_val_by_name(self):
        self.mod.set_parm_val_by_name("geom1", "Span", "WingGeom", 20.0)
        self.fake_vsp.SetParmVal.assert_called_with(
            "geom1", "Span", "WingGeom", 20.0
        )

    # ------------------------------------------------------------------
    # Model update & sets
    # ------------------------------------------------------------------

    def test_update_model(self):
        result = self.mod.update_model()
        self.fake_vsp.Update.assert_called_once()
        self.assertIn("updated", result.lower())

    def test_get_set_name(self):
        result = self.mod.get_set_name(0)
        self.fake_vsp.GetSetName.assert_called_once_with(0)
        self.assertEqual(result, "SET_ALL")

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def test_summarize_model(self):
        result = self.mod.summarize_model()
        self.assertIn("geom1", result)
        self.assertIn("geom2", result)

    def test_summarize_model_empty(self):
        self.fake_vsp.FindGeoms.return_value = []
        self.assertIn("empty", self.mod.summarize_model().lower())

    def test_get_geom_parameters(self):
        result = self.mod.get_geom_parameters("geom1")
        data = json.loads(result)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        self.assertIn("id", data[0])
        self.assertIn("name", data[0])
        self.assertIn("value", data[0])


if __name__ == "__main__":
    unittest.main()
