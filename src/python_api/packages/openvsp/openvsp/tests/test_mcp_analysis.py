"""Tests for MCP analysis, results, and mass properties tools."""

from __future__ import annotations

import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(pathlib.Path(__file__).parent.parent / "mcp" / "_analysis.py")


class TestMCPAnalysis(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def test_list_analysis(self):
        result = self.mod.list_analysis()
        self.assertIn("CompGeom", result)
        self.assertIn("VSPAEROSweep", result)

    def test_get_analysis_doc(self):
        self.assertIsInstance(self.mod.get_analysis_doc("CompGeom"), str)

    def test_get_analysis_input_names(self):
        self.assertIn("Set", self.mod.get_analysis_input_names("CompGeom"))

    def test_get_analysis_input_doc(self):
        self.assertIsInstance(
            self.mod.get_analysis_input_doc("CompGeom", "Set"), str
        )

    def test_exec_analysis(self):
        result = self.mod.exec_analysis("CompGeom")
        self.fake_vsp.ExecAnalysis.assert_called_once_with("CompGeom")
        self.assertEqual(result, "results_abc123")

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def test_get_all_results_names(self):
        self.assertIn("CompGeom", self.mod.get_all_results_names())

    def test_get_all_data_names(self):
        self.assertIn(
            "Total_Wet_Area", self.mod.get_all_data_names("results_abc123")
        )

    # ------------------------------------------------------------------
    # Mass properties
    # ------------------------------------------------------------------

    def test_compute_mass_props(self):
        result = self.mod.compute_mass_props(set_index=0, num_slices=20, idir=0)
        self.fake_vsp.ComputeMassProps.assert_called_once_with(0, 20, 0)
        self.assertEqual(result, "mass_results_id")

    # ------------------------------------------------------------------
    # Analysis (extended)
    # ------------------------------------------------------------------

    def test_get_num_analysis(self):
        result = self.mod.get_num_analysis()
        self.fake_vsp.GetNumAnalysis.assert_called_once()
        self.assertEqual(result, "5")

    def test_set_analysis_input_defaults(self):
        result = self.mod.set_analysis_input_defaults("VSPAEROSweep")
        self.fake_vsp.SetAnalysisInputDefaults.assert_called_once_with(
            "VSPAEROSweep"
        )
        self.assertIn("VSPAEROSweep", result)

    def test_set_int_analysis_input(self):
        result = self.mod.set_int_analysis_input(
            "VSPAEROSweep", "Symmetry", [1]
        )
        self.fake_vsp.SetIntAnalysisInput.assert_called_once_with(
            "VSPAEROSweep", "Symmetry", [1], 0
        )
        self.assertIn("Symmetry", result)

    def test_set_double_analysis_input(self):
        result = self.mod.set_double_analysis_input(
            "VSPAEROSweep", "Sref", [100.0]
        )
        self.fake_vsp.SetDoubleAnalysisInput.assert_called_once_with(
            "VSPAEROSweep", "Sref", [100.0], 0
        )
        self.assertIn("Sref", result)

    def test_set_string_analysis_input(self):
        result = self.mod.set_string_analysis_input(
            "VSPAEROSweep", "Mode", ["panel"]
        )
        self.fake_vsp.SetStringAnalysisInput.assert_called_once_with(
            "VSPAEROSweep", "Mode", ["panel"], 0
        )
        self.assertIn("Mode", result)

    def test_get_int_analysis_input(self):
        result = self.mod.get_int_analysis_input("VSPAEROSweep", "Symmetry")
        self.fake_vsp.GetIntAnalysisInput.assert_called_once_with(
            "VSPAEROSweep", "Symmetry", 0
        )
        self.assertEqual(result, [1])

    def test_get_double_analysis_input(self):
        result = self.mod.get_double_analysis_input("VSPAEROSweep", "Sref")
        self.fake_vsp.GetDoubleAnalysisInput.assert_called_once_with(
            "VSPAEROSweep", "Sref", 0
        )
        self.assertEqual(result, [1.0])

    def test_get_string_analysis_input(self):
        result = self.mod.get_string_analysis_input("VSPAEROSweep", "Mode")
        self.fake_vsp.GetStringAnalysisInput.assert_called_once_with(
            "VSPAEROSweep", "Mode", 0
        )
        self.assertEqual(result, ["str1"])

    def test_get_results_name(self):
        result = self.mod.get_results_name("results_abc123")
        self.fake_vsp.GetResultsName.assert_called_once_with("results_abc123")
        self.assertEqual(result, "VSPAEROSweep")

    def test_get_results_type(self):
        result = self.mod.get_results_type("results_abc123", "CL")
        self.fake_vsp.GetResultsType.assert_called_once_with(
            "results_abc123", "CL"
        )
        self.assertEqual(result, "1")

    def test_list_results_names(self):
        result = self.mod.list_results_names()
        self.assertIn("CompGeom", result)


if __name__ == "__main__":
    unittest.main()
