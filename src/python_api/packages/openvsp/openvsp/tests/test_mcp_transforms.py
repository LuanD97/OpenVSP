"""Tests for MCP group/set transform, variable preset, and VSPAERO CS group tools."""

from __future__ import annotations

import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(
    pathlib.Path(__file__).parent.parent / "mcp" / "_transforms.py"
)


class TestMCPTransforms(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)

    # ------------------------------------------------------------------
    # Group transforms
    # ------------------------------------------------------------------

    def test_scale_set(self):
        result = self.mod.scale_set(0, 2.0)
        self.fake_vsp.ScaleSet.assert_called_once_with(0, 2.0)
        self.assertIn("2.0", result)

    def test_rotate_set(self):
        result = self.mod.rotate_set(0, 10.0, 0.0, 0.0)
        self.fake_vsp.RotateSet.assert_called_once_with(0, 10.0, 0.0, 0.0)

    def test_translate_set(self):
        result = self.mod.translate_set(0, 1.0, 2.0, 3.0)
        self.fake_vsp.vec3d.assert_called_once_with(1.0, 2.0, 3.0)
        self.fake_vsp.TranslateSet.assert_called_once()
        self.assertIn("1.0", result)

    # ------------------------------------------------------------------
    # Variable presets
    # ------------------------------------------------------------------

    def test_get_var_preset_groups(self):
        result = self.mod.get_var_preset_groups()
        self.assertEqual(result, ["grp1", "grp2"])

    def test_add_var_preset_group(self):
        result = self.mod.add_var_preset_group("Cruise")
        self.fake_vsp.AddVarPresetGroup.assert_called_once_with("Cruise")
        self.assertEqual(result, "grp_new")

    def test_delete_var_preset_group(self):
        result = self.mod.delete_var_preset_group("grp1")
        self.fake_vsp.DeleteVarPresetGroup.assert_called_once_with("grp1")
        self.assertIn("grp1", result)

    def test_get_var_preset_settings(self):
        result = self.mod.get_var_preset_settings("grp1")
        self.assertEqual(result, ["set1", "set2"])

    def test_add_var_preset_setting(self):
        result = self.mod.add_var_preset_setting("grp1", "High-Speed")
        self.fake_vsp.AddVarPresetSetting.assert_called_once_with(
            "grp1", "High-Speed"
        )
        self.assertEqual(result, "set_new")

    def test_delete_var_preset_setting(self):
        result = self.mod.delete_var_preset_setting("grp1", "set1")
        self.assertIn("set1", result)

    def test_get_var_preset_parm_ids(self):
        result = self.mod.get_var_preset_parm_ids("grp1")
        self.assertEqual(result, ["parm1", "parm2"])

    def test_add_var_preset_parm(self):
        result = self.mod.add_var_preset_parm("grp1", "parm3")
        self.fake_vsp.AddVarPresetParm.assert_called_once_with("grp1", "parm3")
        self.assertIn("parm3", result)

    def test_delete_var_preset_parm(self):
        result = self.mod.delete_var_preset_parm("grp1", "parm1")
        self.assertIn("parm1", result)

    def test_set_var_preset_parm_val(self):
        result = self.mod.set_var_preset_parm_val("grp1", "set1", "parm1", 3.5)
        self.fake_vsp.SetVarPresetParmVal.assert_called_once_with(
            "grp1", "set1", "parm1", 3.5
        )

    def test_get_var_preset_parm_val(self):
        result = self.mod.get_var_preset_parm_val("grp1", "set1", "parm1")
        self.assertAlmostEqual(result, 5.0)

    def test_save_var_preset_parm_vals(self):
        result = self.mod.save_var_preset_parm_vals("grp1", "set1")
        self.fake_vsp.SaveVarPresetParmVals.assert_called_once_with(
            "grp1", "set1"
        )
        self.assertIn("set1", result)

    def test_apply_var_preset_setting(self):
        result = self.mod.apply_var_preset_setting("grp1", "set1")
        self.fake_vsp.ApplyVarPresetSetting.assert_called_once_with(
            "grp1", "set1"
        )
        self.assertIn("set1", result)

    # ------------------------------------------------------------------
    # VSPAERO control surface groups
    # ------------------------------------------------------------------

    def test_get_num_control_surface_groups(self):
        self.assertEqual(self.mod.get_num_control_surface_groups(), 3)

    def test_create_vspaero_control_surface_group(self):
        result = self.mod.create_vspaero_control_surface_group()
        self.fake_vsp.CreateVSPAEROControlSurfaceGroup.assert_called_once()
        self.assertEqual(result, 3)

    def test_get_vspaero_control_group_name(self):
        result = self.mod.get_vspaero_control_group_name(0)
        self.fake_vsp.GetVSPAEROControlGroupName.assert_called_once_with(0)
        self.assertEqual(result, "Aileron_Group")

    def test_set_vspaero_control_group_name(self):
        result = self.mod.set_vspaero_control_group_name(0, "Elevator")
        self.fake_vsp.SetVSPAEROControlGroupName.assert_called_once_with(
            "Elevator", 0
        )
        self.assertIn("Elevator", result)

    def test_auto_group_vspaero_control_surfaces(self):
        result = self.mod.auto_group_vspaero_control_surfaces()
        self.fake_vsp.AutoGroupVSPAEROControlSurfaces.assert_called_once()
        self.assertIn("auto", result.lower())

    def test_add_all_to_vspaero_control_surface_group(self):
        result = self.mod.add_all_to_vspaero_control_surface_group(1)
        self.fake_vsp.AddAllToVSPAEROControlSurfaceGroup.assert_called_once_with(
            1
        )
        self.assertIn("1", result)

    def test_remove_all_from_vspaero_control_surface_group(self):
        result = self.mod.remove_all_from_vspaero_control_surface_group(1)
        self.fake_vsp.RemoveAllFromVSPAEROControlSurfaceGroup.assert_called_once_with(
            1
        )


if __name__ == "__main__":
    unittest.main()
