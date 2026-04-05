"""Tests for MCP surface query and geometry interrogation tools."""

from __future__ import annotations

import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(pathlib.Path(__file__).parent.parent / "mcp" / "_surface.py")


class TestMCPSurface(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)

    # ------------------------------------------------------------------
    # Surface query
    # ------------------------------------------------------------------

    def test_get_geom_bbox_min(self):
        result = self.mod.get_geom_bbox_min("geom1")
        self.assertAlmostEqual(result["x"], -1.0)
        self.assertAlmostEqual(result["y"], -5.0)
        self.assertAlmostEqual(result["z"], 0.0)

    def test_get_geom_bbox_max(self):
        result = self.mod.get_geom_bbox_max("geom1")
        self.assertAlmostEqual(result["x"], 1.0)
        self.assertAlmostEqual(result["y"], 5.0)
        self.assertAlmostEqual(result["z"], 2.0)

    def test_comp_pnt01(self):
        result = self.mod.comp_pnt01("geom1", 0, 0.5, 0.5)
        self.fake_vsp.CompPnt01.assert_called_once_with("geom1", 0, 0.5, 0.5)
        self.assertIn("x", result)
        self.assertIn("y", result)
        self.assertIn("z", result)

    def test_comp_norm01(self):
        result = self.mod.comp_norm01("geom1", 0, 0.5, 0.5)
        self.assertAlmostEqual(result["z"], 1.0)

    def test_comp_tan_u01(self):
        result = self.mod.comp_tan_u01("geom1", 0, 0.5, 0.5)
        self.assertAlmostEqual(result["x"], 1.0)

    def test_comp_tan_w01(self):
        result = self.mod.comp_tan_w01("geom1", 0, 0.5, 0.5)
        self.assertAlmostEqual(result["y"], 1.0)

    def test_proj_pnt01(self):
        result = self.mod.proj_pnt01("geom1", 0, 0.5, 2.0, 1.0)
        self.fake_vsp.ProjPnt01.assert_called_once()
        self.assertIn("dist", result)
        self.assertIn("u", result)
        self.assertIn("w", result)
        self.assertAlmostEqual(result["dist"], 0.02)


if __name__ == "__main__":
    unittest.main()
