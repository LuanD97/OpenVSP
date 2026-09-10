"""Tests for MCP point cloud and Fit Model tools."""

from __future__ import annotations

import pathlib
import sys
import unittest
from unittest.mock import ANY, MagicMock

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _load_submodule, _make_fake_vsp

_SUBMODULE = str(pathlib.Path(__file__).parent.parent / "mcp" / "_fitmodel.py")


class _FitModelTestBase(unittest.TestCase):
    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mod = _load_submodule(self.fake_vsp, _SUBMODULE)

    def tearDown(self):
        sys.modules.pop("openvsp", None)


# ---------------------------------------------------------------------------
# Phase 2: Foundational helpers
# ---------------------------------------------------------------------------


class TestErrorCapture(_FitModelTestBase):
    def test_error_pushed_during_call_is_returned(self):
        def fn(vsp):
            vsp.ErrorMgrSingleton.getInstance().push(22, "boom")
            return "ok"

        result, errors = self.mod._capture(fn)
        self.assertEqual(result, "ok")
        self.assertEqual(errors, [{"code": 22, "message": "boom"}])

    def test_error_pushed_before_call_is_not_returned(self):
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()
        em.push(1, "earlier")

        def fn(vsp):
            return "ok"

        result, errors = self.mod._capture(fn)
        self.assertEqual(result, "ok")
        self.assertEqual(errors, [])
        # The earlier error is still on the queue.
        self.assertEqual(em.GetNumTotalErrors(), 1)

    def test_silence_errors_called(self):
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()
        self.mod._capture(lambda vsp: None)
        self.assertTrue(em.silenced)

    def test_exception_becomes_error_dict(self):
        def fn(vsp):
            raise ValueError("bad input")

        result = self.mod._error(str(ValueError("bad input")))
        self.assertEqual(result, {"error": "bad input"})


class TestFitTypeParsing(_FitModelTestBase):
    def test_free_variants(self):
        for value in ("free", "FREE", "Free"):
            code, reason = self.mod._parse_fit_type(value)
            self.assertIsNone(reason)
            self.assertEqual(code, self.fake_vsp.FIT_FREE)

    def test_fixed_variants(self):
        for value in ("fixed", "FIXED", "Fixed"):
            code, reason = self.mod._parse_fit_type(value)
            self.assertIsNone(reason)
            self.assertEqual(code, self.fake_vsp.FIT_FIXED)

    def test_other_rejected(self):
        code, reason = self.mod._parse_fit_type("other")
        self.assertIsNone(code)
        self.assertIsNotNone(reason)

    def test_int_round_trip(self):
        self.assertEqual(self.mod._fit_type_name(0), "FIXED")
        self.assertEqual(self.mod._fit_type_name(1), "FREE")


class TestValidateTargetSpec(_FitModelTestBase):
    def setUp(self):
        super().setUp()
        self.geom_ids = {"g1"}

    def test_missing_field(self):
        for field in ("x", "y", "z", "geom_id"):
            spec = {"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "g1"}
            del spec[field]
            normalised, reason = self.mod._validate_target_spec(
                spec, 0, self.geom_ids
            )
            self.assertIsNone(normalised)
            self.assertIn(field, reason)

    def test_non_finite_coordinate(self):
        spec = {"x": float("nan"), "y": 0.0, "z": 0.0, "geom_id": "g1"}
        normalised, reason = self.mod._validate_target_spec(spec, 0, self.geom_ids)
        self.assertIsNone(normalised)
        self.assertIn("x", reason)

    def test_non_numeric_coordinate(self):
        spec = {"x": "abc", "y": 0.0, "z": 0.0, "geom_id": "g1"}
        normalised, reason = self.mod._validate_target_spec(spec, 0, self.geom_ids)
        self.assertIsNone(normalised)
        self.assertIn("x", reason)

    def test_non_numeric_u(self):
        spec = {"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "g1", "u": "abc"}
        normalised, reason = self.mod._validate_target_spec(spec, 0, self.geom_ids)
        self.assertIsNone(normalised)
        self.assertIn("u", reason)

    def test_u_out_of_range(self):
        spec = {"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "g1", "u": 1.5}
        normalised, reason = self.mod._validate_target_spec(spec, 0, self.geom_ids)
        self.assertIsNone(normalised)
        self.assertIn("u", reason)

    def test_w_out_of_range(self):
        spec = {"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "g1", "w": -0.1}
        normalised, reason = self.mod._validate_target_spec(spec, 0, self.geom_ids)
        self.assertIsNone(normalised)
        self.assertIn("w", reason)

    def test_bad_type_string(self):
        spec = {"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "g1", "u_type": "nope"}
        normalised, reason = self.mod._validate_target_spec(spec, 0, self.geom_ids)
        self.assertIsNone(normalised)
        self.assertIn("u_type", reason)

    def test_geom_id_not_in_model(self):
        spec = {"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "bogus"}
        normalised, reason = self.mod._validate_target_spec(spec, 0, self.geom_ids)
        self.assertIsNone(normalised)
        self.assertIn("geom_id", reason)

    def test_defaults(self):
        spec = {"x": 1.0, "y": 2.0, "z": 3.0, "geom_id": "g1"}
        normalised, reason = self.mod._validate_target_spec(spec, 0, self.geom_ids)
        self.assertIsNone(reason)
        self.assertEqual(normalised["point"], [1.0, 2.0, 3.0])
        self.assertEqual(normalised["u"], 0.5)
        self.assertEqual(normalised["w"], 0.5)
        self.assertEqual(normalised["u_type"], self.fake_vsp.FIT_FREE)
        self.assertEqual(normalised["w_type"], self.fake_vsp.FIT_FREE)


class TestVarDescription(_FitModelTestBase):
    def test_var_found_through_xsec_owned_parm(self):
        self.fake_vsp.FindGeoms.return_value = ["g1", "g2"]
        self.fake_vsp.GetGeomParmIDs.side_effect = lambda g: {
            "g1": ["p1"],
            "g2": ["p2"],
        }[g]
        parm_map = self.mod._parm_geom_map(self.fake_vsp)
        self.assertEqual(parm_map["p2"], "g2")

        info = self.mod._describe_var(self.fake_vsp, "p2", parm_map)
        self.assertEqual(info["geom_id"], "g2")

    def test_invalid_parm_reports_no_value(self):
        self.fake_vsp.ValidParm.return_value = False
        info = self.mod._describe_var(self.fake_vsp, "p1", {})
        self.assertFalse(info["valid"])
        self.assertIsNone(info["value"])


class TestDanglingCheck(_FitModelTestBase):
    def test_target_with_missing_geom_listed_by_index(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "missing_geom"
        self.fake_vsp.FindGeoms.return_value = []
        self.fake_vsp.GetFitModelVarIDs.return_value = ()

        dangling_targets, dangling_vars = self.mod._dangling(self.fake_vsp)
        self.assertEqual(dangling_targets, [0])
        self.assertEqual(dangling_vars, [])

    def test_var_failing_valid_parm_listed_by_id(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 0
        self.fake_vsp.GetFitModelVarIDs.return_value = ("p1",)
        self.fake_vsp.ValidParm.return_value = False

        dangling_targets, dangling_vars = self.mod._dangling(self.fake_vsp)
        self.assertEqual(dangling_targets, [])
        self.assertEqual(dangling_vars, ["p1"])


class TestTargetBatch(_FitModelTestBase):
    def _spec(self, geom_id="g1"):
        return {"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": geom_id}

    def test_success(self):
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        self.fake_vsp.AddFitModelTargetPt.side_effect = [0, 1]
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 2

        result = self.mod._add_target_batch(self.fake_vsp, [self._spec(), self._spec()])
        self.assertEqual(result["first_index"], 0)
        self.assertEqual(result["last_index"], 1)
        self.assertEqual(result["count"], 2)

    def test_python_invalid_entry_makes_no_engine_calls(self):
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        specs = [self._spec(), {"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "bogus"}]
        result = self.mod._add_target_batch(self.fake_vsp, specs)
        self.assertIn("invalid", result)
        self.assertEqual([e["position"] for e in result["invalid"]], [1])
        self.fake_vsp.AddFitModelTargetPt.assert_not_called()

    def test_engine_rejection_rolls_back_highest_first(self):
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()

        def add_side_effect(*args, **kwargs):
            call_index = self.fake_vsp.AddFitModelTargetPt.call_count - 1
            if call_index == 1:
                em.push(2, "engine rejected")
                return -1
            return call_index

        self.fake_vsp.AddFitModelTargetPt.side_effect = add_side_effect
        specs = [self._spec(), self._spec(), self._spec()]
        result = self.mod._add_target_batch(self.fake_vsp, specs)

        self.assertIn("error", result)
        self.assertEqual([e["position"] for e in result["invalid"]], [1])
        # The batch keeps going after a rejection, so entries 0 and 2 were both
        # added and both are rolled back, highest index first.
        delete_calls = [
            call.args[0] for call in self.fake_vsp.DeleteFitModelTargetPt.call_args_list
        ]
        self.assertEqual(delete_calls, [2, 0])

    def test_every_engine_rejection_reported(self):
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()

        def add_side_effect(*args, **kwargs):
            call_index = self.fake_vsp.AddFitModelTargetPt.call_count - 1
            if call_index in (1, 2):
                em.push(2, f"engine rejected {call_index}")
                return -1
            return call_index

        self.fake_vsp.AddFitModelTargetPt.side_effect = add_side_effect
        specs = [self._spec() for _ in range(4)]
        result = self.mod._add_target_batch(self.fake_vsp, specs)

        self.assertIn("error", result)
        self.assertEqual([e["position"] for e in result["invalid"]], [1, 2])
        self.assertIn("engine rejected 2", result["invalid"][1]["reason"])
        delete_calls = [
            call.args[0] for call in self.fake_vsp.DeleteFitModelTargetPt.call_args_list
        ]
        self.assertEqual(delete_calls, [3, 0])

    def test_empty_batch_rejected(self):
        result = self.mod._add_target_batch(self.fake_vsp, [])
        self.assertIn("error", result)
        self.assertIn("empty", result["error"])
        self.fake_vsp.AddFitModelTargetPt.assert_not_called()

    def test_over_cap_rejected_before_engine_call(self):
        specs = [self._spec() for _ in range(self.mod._MAX_BATCH + 1)]
        result = self.mod._add_target_batch(self.fake_vsp, specs)
        self.assertIn("error", result)
        self.fake_vsp.AddFitModelTargetPt.assert_not_called()


# ---------------------------------------------------------------------------
# Phase 3: User Story 1
# ---------------------------------------------------------------------------


class TestImportPointCloud(_FitModelTestBase):
    def test_success(self):
        self.fake_vsp.ImportFile.return_value = "cloud1"
        self.fake_vsp.GetPtCloudPnts.return_value = ((0.0, 0.0, 0.0),) * 5
        result = self.mod.import_point_cloud("/tmp/cloud.pts")
        self.assertEqual(result, {"geom_id": "cloud1", "num_points": 5})

    def test_none_id_is_error(self):
        self.fake_vsp.ImportFile.return_value = "NONE"
        result = self.mod.import_point_cloud("/tmp/missing.pts")
        self.assertIn("error", result)
        self.assertIn("/tmp/missing.pts", result["error"])

    def test_zero_points_deletes_and_errors(self):
        self.fake_vsp.ImportFile.return_value = "cloud1"
        self.fake_vsp.GetPtCloudPnts.return_value = ()
        result = self.mod.import_point_cloud("/tmp/empty.pts")
        self.assertIn("error", result)
        self.fake_vsp.DeleteGeom.assert_called_once_with("cloud1")


class TestSetupState(_FitModelTestBase):
    def test_reset_fit_model(self):
        self.fake_vsp.GetNumFitModelVars.return_value = 0
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 0
        result = self.mod.reset_fit_model()
        self.fake_vsp.ResetFitModel.assert_called_once()
        self.assertEqual(result, {"num_vars": 0, "num_targets": 0})

    def test_clear_fit_model_vars(self):
        self.fake_vsp.GetNumFitModelVars.return_value = 0
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 3
        result = self.mod.clear_fit_model_vars()
        self.fake_vsp.ClearFitModelVars.assert_called_once()
        self.assertEqual(result, {"num_vars": 0, "num_targets": 3})

    def test_clear_fit_model_targets(self):
        self.fake_vsp.GetNumFitModelVars.return_value = 2
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 0
        result = self.mod.clear_fit_model_targets()
        self.fake_vsp.ClearFitModelTargetPts.assert_called_once()
        self.assertEqual(result, {"num_vars": 2, "num_targets": 0})


class TestAddVars(_FitModelTestBase):
    def test_two_vars_added(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        self.fake_vsp.ValidParm.return_value = True
        result = self.mod.add_fit_model_vars(["p1", "p2"])
        self.assertEqual(result["added"], 2)
        self.assertIn("vars", result)

    def test_invalid_parm_rejected_no_engine_calls(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ()

        def valid(parm_id):
            return parm_id != "p1"

        self.fake_vsp.ValidParm.side_effect = valid
        result = self.mod.add_fit_model_vars(["p1", "p2"])
        self.assertIn("invalid", result)
        self.fake_vsp.AddFitModelVar.assert_not_called()

    def test_duplicate_within_list_rejected(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        self.fake_vsp.ValidParm.return_value = True
        result = self.mod.add_fit_model_vars(["p1", "p1"])
        self.assertIn("invalid", result)
        self.fake_vsp.AddFitModelVar.assert_not_called()

    def test_duplicate_already_added_rejected(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ("p1",)
        self.fake_vsp.ValidParm.return_value = True
        result = self.mod.add_fit_model_vars(["p1"])
        self.assertIn("invalid", result)
        self.fake_vsp.AddFitModelVar.assert_not_called()

    def test_engine_rejection_rolls_back(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        self.fake_vsp.ValidParm.return_value = True
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()

        def add_side_effect(parm_id):
            if parm_id == "p2":
                em.push(22, "rejected")
                return False
            return True

        self.fake_vsp.AddFitModelVar.side_effect = add_side_effect
        result = self.mod.add_fit_model_vars(["p1", "p2"])
        self.assertIn("error", result)
        self.fake_vsp.DeleteFitModelVar.assert_called_once_with("p1")

    def test_empty_list_rejected(self):
        result = self.mod.add_fit_model_vars([])
        self.assertIn("error", result)

    def test_over_cap_rejected(self):
        result = self.mod.add_fit_model_vars([f"p{i}" for i in range(1001)])
        self.assertIn("error", result)


class TestListVars(_FitModelTestBase):
    def test_shape_and_count(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ("p1", "p2")
        self.fake_vsp.ValidParm.return_value = True
        result = self.mod.list_fit_model_vars()
        self.assertEqual(result["num_vars"], 2)
        self.assertEqual(len(result["vars"]), 2)


class TestAddTargets(_FitModelTestBase):
    def test_delegates_to_batch_success(self):
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        self.fake_vsp.AddFitModelTargetPt.return_value = 0
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        result = self.mod.add_fit_model_targets(
            [{"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "g1"}]
        )
        self.assertEqual(result["count"], 1)

    def test_delegates_to_batch_invalid(self):
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        result = self.mod.add_fit_model_targets(
            [{"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": "bogus"}]
        )
        self.assertIn("invalid", result)


class TestSolving(_FitModelTestBase):
    def test_search_with_dangling_target_errors_without_engine_call(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "missing"
        self.fake_vsp.FindGeoms.return_value = []
        result = self.mod.search_fit_model_target_uw()
        self.assertIn("error", result)
        self.assertIn("dangling_target_indices", result)
        self.fake_vsp.SearchFitModelTargetUW.assert_not_called()

    def test_refine_with_dangling_target_errors_without_engine_call(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "missing"
        self.fake_vsp.FindGeoms.return_value = []
        result = self.mod.refine_fit_model_target_uw()
        self.assertIn("error", result)
        self.assertIn("dangling_target_indices", result)
        self.fake_vsp.RefineFitModelTargetUW.assert_not_called()

    def test_optimize_with_dangling_target_errors_without_engine_call(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "missing"
        self.fake_vsp.FindGeoms.return_value = []
        result = self.mod.optimize_fit_model()
        self.assertIn("error", result)
        self.assertIn("dangling_target_indices", result)
        self.fake_vsp.OptimizeFitModel.assert_not_called()

    def test_update_distance_zero_targets_skips_engine(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 0
        result = self.mod.update_fit_model_distance()
        self.assertEqual(result, {"rms": 0.0, "num_targets": 0})
        self.fake_vsp.UpdateFitModelDistance.assert_not_called()

    def test_get_fit_model_distance_cached(self):
        self.fake_vsp.GetFitModelDistance.return_value = 3.5
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 2
        result = self.mod.get_fit_model_distance()
        self.assertEqual(result["rms"], 3.5)
        self.fake_vsp.UpdateFitModelDistance.assert_not_called()

    def test_optimize_returns_full_shape(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "g1"
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        self.fake_vsp.UpdateFitModelDistance.return_value = 1.0
        self.fake_vsp.GetFitModelDistance.return_value = 0.1
        self.fake_vsp.OptimizeFitModel.return_value = 2
        result = self.mod.optimize_fit_model()
        self.assertEqual(result["info"], 2)
        self.assertIn("info_meaning", result)
        self.assertEqual(result["rms_before"], 1.0)
        self.assertEqual(result["rms_after"], 0.1)
        self.assertIn("vars", result)

    def test_optimize_engine_error_becomes_error_result(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "g1"
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()

        def optimize_side_effect():
            em.push(22, "no optimization variables")
            return 0

        self.fake_vsp.OptimizeFitModel.side_effect = optimize_side_effect
        result = self.mod.optimize_fit_model()
        self.assertIn("error", result)
        self.assertIn("vsp_errors", result)


# ---------------------------------------------------------------------------
# Phase 4: User Story 2
# ---------------------------------------------------------------------------


class TestFitToConvergence(_FitModelTestBase):
    def _make_ok_engine(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "g1"
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        self.fake_vsp.GetFitModelVarIDs.return_value = ()

    def test_converged_when_rms_hits_zero(self):
        self._make_ok_engine()
        self.fake_vsp.UpdateFitModelDistance.side_effect = [1.0]
        self.fake_vsp.GetFitModelDistance.side_effect = [0.0]
        result = self.mod.fit_model_to_convergence()
        self.assertEqual(result["stop_reason"], "converged")
        self.assertEqual(result["passes"], 1)

    def test_converged_when_relative_improvement_below_tolerance(self):
        self._make_ok_engine()
        self.fake_vsp.UpdateFitModelDistance.side_effect = [1.0]
        self.fake_vsp.GetFitModelDistance.side_effect = [0.9999999]
        result = self.mod.fit_model_to_convergence(tolerance=1e-3)
        self.assertEqual(result["stop_reason"], "converged")

    def test_no_improvement_keeps_result(self):
        self._make_ok_engine()
        self.fake_vsp.UpdateFitModelDistance.side_effect = [1.0]
        self.fake_vsp.GetFitModelDistance.side_effect = [2.0]
        result = self.mod.fit_model_to_convergence()
        self.assertEqual(result["stop_reason"], "no_improvement")
        self.assertEqual(result["passes"], 1)
        self.fake_vsp.DeleteFitModelVar.assert_not_called()
        self.fake_vsp.ResetFitModel.assert_not_called()

    def test_pass_limit_one_optimize_call(self):
        self._make_ok_engine()
        self.fake_vsp.UpdateFitModelDistance.side_effect = [1.0] * 5
        self.fake_vsp.GetFitModelDistance.side_effect = [0.5] * 5
        result = self.mod.fit_model_to_convergence(max_passes=1, tolerance=1e-9)
        self.assertEqual(result["stop_reason"], "pass_limit")
        self.assertEqual(self.fake_vsp.OptimizeFitModel.call_count, 1)

    def test_error_during_pass_two_keeps_pass_one_history(self):
        self._make_ok_engine()
        self.fake_vsp.UpdateFitModelDistance.side_effect = [1.0, 0.5]
        self.fake_vsp.GetFitModelDistance.side_effect = [0.5, 0.5]
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()
        call_count = {"n": 0}

        def optimize_side_effect():
            call_count["n"] += 1
            if call_count["n"] == 2:
                em.push(22, "engine failure")
            return 2

        self.fake_vsp.OptimizeFitModel.side_effect = optimize_side_effect
        result = self.mod.fit_model_to_convergence(max_passes=5, tolerance=1e-9)
        self.assertEqual(result["stop_reason"], "error")
        self.assertEqual(len(result["rms_history"]), 1)
        self.assertIn("vsp_errors", result)

    def test_refine_false_skips_refine_call(self):
        self._make_ok_engine()
        self.fake_vsp.UpdateFitModelDistance.side_effect = [1.0]
        self.fake_vsp.GetFitModelDistance.side_effect = [0.0]
        self.mod.fit_model_to_convergence(refine=False)
        self.fake_vsp.RefineFitModelTargetUW.assert_not_called()

    def test_dangling_precheck_runs_no_passes(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "missing"
        self.fake_vsp.FindGeoms.return_value = []
        result = self.mod.fit_model_to_convergence()
        self.assertIn("error", result)
        self.fake_vsp.SearchFitModelTargetUW.assert_not_called()
        self.fake_vsp.OptimizeFitModel.assert_not_called()

    def test_bad_max_passes_rejected(self):
        for bad in (0, 101):
            result = self.mod.fit_model_to_convergence(max_passes=bad)
            self.assertIn("error", result)

    def test_bad_tolerance_rejected(self):
        result = self.mod.fit_model_to_convergence(tolerance=0)
        self.assertIn("error", result)

    def test_history_and_summary_fields(self):
        self._make_ok_engine()
        self.fake_vsp.UpdateFitModelDistance.side_effect = [1.0]
        self.fake_vsp.GetFitModelDistance.side_effect = [0.0]
        result = self.mod.fit_model_to_convergence()
        self.assertEqual(
            set(result["rms_history"][0].keys()), {"pass", "rms_before", "rms_after", "info"}
        )
        self.assertIn("rms_initial", result)
        self.assertIn("rms_final", result)
        self.assertIn("vars", result)


# ---------------------------------------------------------------------------
# Phase 5: User Story 3
# ---------------------------------------------------------------------------


def _mock_vec3d(x, y, z):
    v = MagicMock()
    v.x.return_value = x
    v.y.return_value = y
    v.z.return_value = z
    return v


class TestCloudSummary(_FitModelTestBase):
    def test_count_bbox_centroid(self):
        self.fake_vsp.GetGeomTypeName.return_value = "PtCloud"
        self.fake_vsp.GetPtCloudPnts.return_value = [
            _mock_vec3d(0.0, 0.0, 0.0),
            _mock_vec3d(2.0, 4.0, 6.0),
        ]
        result = self.mod.get_point_cloud_summary("cloud1")
        self.assertEqual(result["num_points"], 2)
        self.assertEqual(result["bbox_min"], [0.0, 0.0, 0.0])
        self.assertEqual(result["bbox_max"], [2.0, 4.0, 6.0])
        self.assertEqual(result["centroid"], [1.0, 2.0, 3.0])

    def test_non_ptcloud_geom_errors(self):
        self.fake_vsp.GetGeomTypeName.return_value = "Pod"
        result = self.mod.get_point_cloud_summary("geom1")
        self.assertIn("error", result)
        self.assertIn("geom1", result["error"])


class TestCloudPoints(_FitModelTestBase):
    def setUp(self):
        super().setUp()
        self.fake_vsp.GetGeomTypeName.return_value = "PtCloud"
        self.fake_vsp.GetPtCloudPnts.return_value = [
            _mock_vec3d(float(i), 0.0, 0.0) for i in range(10)
        ]

    def test_count_clamped_to_1000(self):
        result = self.mod.get_point_cloud_points("cloud1", count=5000)
        self.assertLessEqual(result["returned"], 1000)

    def test_next_start_advances_and_none_at_end(self):
        result = self.mod.get_point_cloud_points("cloud1", start=0, count=5)
        self.assertEqual(result["next_start"], 5)
        result2 = self.mod.get_point_cloud_points("cloud1", start=5, count=5)
        self.assertIsNone(result2["next_start"])

    def test_stride(self):
        result = self.mod.get_point_cloud_points("cloud1", start=0, count=10, stride=2)
        self.assertEqual(result["returned"], 5)
        self.assertEqual([p[0] for p in result["points"]], [0.0, 2.0, 4.0, 6.0, 8.0])

    def test_start_out_of_range_errors(self):
        result = self.mod.get_point_cloud_points("cloud1", start=100)
        self.assertIn("error", result)


class TestTargetsFromCloud(_FitModelTestBase):
    def setUp(self):
        super().setUp()
        self.fake_vsp.GetGeomTypeName.return_value = "PtCloud"
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        self.fake_vsp.GetPtCloudPnts.return_value = [
            _mock_vec3d(0.0, 0.0, 0.0),
            _mock_vec3d(1.0, 1.0, 1.0),
            _mock_vec3d(5.0, 5.0, 5.0),  # outside the box
        ]

    def test_box_inclusive_on_boundary(self):
        self.fake_vsp.AddFitModelTargetPt.side_effect = [0, 1]
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 2
        result = self.mod.add_fit_model_targets_from_cloud(
            "cloud1", "g1", [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]
        )
        self.assertEqual(result["matched"], 2)

    def test_stride_keeps_every_nth_in_order(self):
        self.fake_vsp.GetPtCloudPnts.return_value = [
            _mock_vec3d(float(i), 0.0, 0.0) for i in range(6)
        ]
        self.fake_vsp.AddFitModelTargetPt.side_effect = [0, 1, 2]
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 3
        result = self.mod.add_fit_model_targets_from_cloud(
            "cloud1", "g1", [0.0, 0.0, 0.0], [5.0, 0.0, 0.0], stride=2
        )
        self.assertEqual(result["count"], 3)

    def test_zero_matches_errors_with_bbox_in_message(self):
        result = self.mod.add_fit_model_targets_from_cloud(
            "cloud1", "g1", [100.0, 100.0, 100.0], [200.0, 200.0, 200.0]
        )
        self.assertIn("error", result)
        self.assertIn("100.0", result["error"])

    def test_over_cap_selected_errors_with_counts(self):
        self.fake_vsp.GetPtCloudPnts.return_value = [
            _mock_vec3d(0.0, 0.0, 0.0) for _ in range(10001)
        ]
        result = self.mod.add_fit_model_targets_from_cloud(
            "cloud1", "g1", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        )
        self.assertIn("error", result)
        self.assertEqual(result["matched"], 10001)
        self.assertEqual(result["selected"], 10001)

    def test_bbox_min_greater_than_max_rejected(self):
        result = self.mod.add_fit_model_targets_from_cloud(
            "cloud1", "g1", [1.0, 0.0, 0.0], [0.0, 1.0, 1.0]
        )
        self.assertIn("error", result)

    def test_bad_geom_id_is_one_error_not_per_point(self):
        result = self.mod.add_fit_model_targets_from_cloud(
            "cloud1", "bogus", [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]
        )
        self.assertIn("error", result)
        self.assertIn("bogus", result["error"])
        self.assertNotIn("invalid", result)
        self.fake_vsp.AddFitModelTargetPt.assert_not_called()

    def test_bad_fit_type_is_one_error_not_per_point(self):
        for kwargs in ({"u_type": "nope"}, {"w_type": "nope"}):
            result = self.mod.add_fit_model_targets_from_cloud(
                "cloud1", "g1", [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], **kwargs
            )
            self.assertIn("error", result)
            self.assertIn(next(iter(kwargs)), result["error"])
            self.assertNotIn("invalid", result)
        self.fake_vsp.AddFitModelTargetPt.assert_not_called()

    def test_rollback_path_applies(self):
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()

        def add_side_effect(*args, **kwargs):
            call_index = self.fake_vsp.AddFitModelTargetPt.call_count - 1
            if call_index == 1:
                em.push(2, "engine rejected")
                return -1
            return call_index

        self.fake_vsp.AddFitModelTargetPt.side_effect = add_side_effect
        result = self.mod.add_fit_model_targets_from_cloud(
            "cloud1", "g1", [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]
        )
        self.assertIn("error", result)
        self.fake_vsp.DeleteFitModelTargetPt.assert_called_once_with(0)

    def test_success_shape_has_no_point_lists(self):
        self.fake_vsp.AddFitModelTargetPt.side_effect = [0, 1]
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 2
        result = self.mod.add_fit_model_targets_from_cloud(
            "cloud1", "g1", [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]
        )
        for key in ("matched", "count", "first_index", "last_index", "num_targets"):
            self.assertIn(key, result)
        self.assertNotIn("points", result)
        self.assertNotIn("point", result)


# ---------------------------------------------------------------------------
# Phase 6: User Story 4
# ---------------------------------------------------------------------------


class TestTargetAccess(_FitModelTestBase):
    def test_get_fit_model_target_shape(self):
        self.fake_vsp.GetFitModelTargetPt.return_value = _mock_vec3d(1.0, 2.0, 3.0)
        self.fake_vsp.GetFitModelTargetUW.return_value = _mock_vec3d(0.25, 0.75, 0.0)
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "g1"
        self.fake_vsp.GetFitModelTargetUType.return_value = self.fake_vsp.FIT_FIXED
        self.fake_vsp.GetFitModelTargetWType.return_value = self.fake_vsp.FIT_FREE
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1

        result = self.mod.get_fit_model_target(0)
        self.assertEqual(result["point"], [1.0, 2.0, 3.0])
        self.assertEqual(result["geom_id"], "g1")
        self.assertEqual(result["u"], 0.25)
        self.assertEqual(result["w"], 0.75)
        self.assertEqual(result["u_type"], "FIXED")
        self.assertEqual(result["w_type"], "FREE")

    def test_out_of_range_index_errors(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 3
        result = self.mod.get_fit_model_target(5)
        self.assertIn("error", result)
        self.assertIn("5", result["error"])
        self.assertIn("3", result["error"])

    def test_list_targets_paging_clamps_count(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 2000
        self.fake_vsp.GetFitModelTargetPt.return_value = _mock_vec3d(0.0, 0.0, 0.0)
        self.fake_vsp.GetFitModelTargetUW.return_value = _mock_vec3d(0.5, 0.5, 0.0)
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "g1"
        self.fake_vsp.GetFitModelTargetUType.return_value = self.fake_vsp.FIT_FREE
        self.fake_vsp.GetFitModelTargetWType.return_value = self.fake_vsp.FIT_FREE

        result = self.mod.list_fit_model_targets(start=0, count=5000)
        self.assertEqual(result["returned"], 1000)

    def test_list_targets_negative_start_errors(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 3
        result = self.mod.list_fit_model_targets(start=-1)
        self.assertIn("error", result)
        self.fake_vsp.GetFitModelTargetPt.assert_not_called()

    def test_add_targets_empty_list_rejected(self):
        result = self.mod.add_fit_model_targets([])
        self.assertIn("error", result)
        self.assertNotIn("list index", result["error"])


class TestUpdateTarget(_FitModelTestBase):
    def setUp(self):
        super().setUp()
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.FindGeoms.return_value = ["g1"]
        self.fake_vsp.GetFitModelTargetPt.return_value = _mock_vec3d(1.0, 2.0, 3.0)
        self.fake_vsp.GetFitModelTargetUW.return_value = _mock_vec3d(0.25, 0.75, 0.0)
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "g1"
        self.fake_vsp.GetFitModelTargetUType.return_value = self.fake_vsp.FIT_FIXED
        self.fake_vsp.GetFitModelTargetWType.return_value = self.fake_vsp.FIT_FREE

    def test_only_geom_id_keeps_other_fields(self):
        result = self.mod.update_fit_model_target(0, geom_id="g1")
        self.fake_vsp.SetFitModelTargetPt.assert_called_once_with(
            0, ANY, "g1", 0.25, self.fake_vsp.FIT_FIXED, 0.75, self.fake_vsp.FIT_FREE
        )

    def test_u_out_of_range_rejected_before_engine_call(self):
        result = self.mod.update_fit_model_target(0, u=2.0)
        self.assertIn("error", result)
        self.fake_vsp.SetFitModelTargetPt.assert_not_called()

    def test_success_returns_updated_target(self):
        result = self.mod.update_fit_model_target(0, x=9.0)
        self.assertEqual(result["point"][0], 9.0)


class TestDeleteTarget(_FitModelTestBase):
    def test_returns_count(self):
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 4
        result = self.mod.delete_fit_model_target(0)
        self.fake_vsp.DeleteFitModelTargetPt.assert_called_once_with(0)
        self.assertEqual(result["num_targets"], 4)

    def test_engine_error_passes_through(self):
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()

        def delete_side_effect(idx):
            em.push(13, "Target Index Out Of Range")

        self.fake_vsp.DeleteFitModelTargetPt.side_effect = delete_side_effect
        result = self.mod.delete_fit_model_target(99)
        self.assertIn("error", result)


class TestDeleteVar(_FitModelTestBase):
    def test_returns_count(self):
        self.fake_vsp.GetNumFitModelVars.return_value = 1
        result = self.mod.delete_fit_model_var("p1")
        self.fake_vsp.DeleteFitModelVar.assert_called_once_with("p1")
        self.assertEqual(result["num_vars"], 1)

    def test_engine_error_passes_through(self):
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()

        def delete_side_effect(parm_id):
            em.push(22, "Parm not in Fit Model")

        self.fake_vsp.DeleteFitModelVar.side_effect = delete_side_effect
        result = self.mod.delete_fit_model_var("bogus")
        self.assertIn("error", result)


class TestSaveLoad(_FitModelTestBase):
    def test_save_false_is_error(self):
        self.fake_vsp.SaveFitModel.return_value = False
        result = self.mod.save_fit_model("/tmp/out.fit")
        self.assertIn("error", result)

    def test_save_success_shape(self):
        self.fake_vsp.SaveFitModel.return_value = True
        self.fake_vsp.GetNumFitModelVars.return_value = 2
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 5
        result = self.mod.save_fit_model("/tmp/out.fit")
        self.assertEqual(result, {"file_name": "/tmp/out.fit", "num_vars": 2, "num_targets": 5})

    def test_load_calls_load_fit_model_replace(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 0
        self.mod.load_fit_model("/tmp/in.fit")
        self.fake_vsp.LoadFitModel.assert_called_once_with("/tmp/in.fit", True)

    def test_load_append_calls_load_fit_model_no_clear(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 0
        self.mod.load_fit_model("/tmp/in.fit", append=True)
        self.fake_vsp.LoadFitModel.assert_called_once_with("/tmp/in.fit", False)

    def test_missing_parm_ids_reported(self):
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fit", delete=False) as f:
            f.write(
                "<Vsp_FitModel><Variable><ParmID>p1</ParmID></Variable>"
                "<Variable><ParmID>p2</ParmID></Variable></Vsp_FitModel>"
            )
            fit_path = f.name
        try:
            self.fake_vsp.GetFitModelVarIDs.return_value = ("p1",)
            self.fake_vsp.GetNumFitModelTargetPts.return_value = 0
            result = self.mod.load_fit_model(fit_path)
            self.assertIn("error", result)
            self.assertEqual(result["missing_parm_ids"], ["p2"])
        finally:
            import os

            os.unlink(fit_path)

    def test_dangling_target_after_load_reported(self):
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 1
        self.fake_vsp.GetFitModelTargetGeomID.return_value = "missing"
        self.fake_vsp.FindGeoms.return_value = []
        result = self.mod.load_fit_model("/tmp/nonexistent_but_mocked.fit")
        self.assertIn("error", result)
        self.assertIn("dangling_target_indices", result)

    def test_engine_missing_file_error_reported(self):
        em = self.fake_vsp.ErrorMgrSingleton.getInstance()

        def load_side_effect(file_name, clear_existing):
            em.push(7, "Can't Read File")
            return 1

        self.fake_vsp.LoadFitModel.side_effect = load_side_effect
        self.fake_vsp.GetFitModelVarIDs.return_value = ()
        self.fake_vsp.GetNumFitModelTargetPts.return_value = 0
        result = self.mod.load_fit_model("/tmp/does_not_exist.fit")
        self.assertIn("error", result)
        self.assertIn("vsp_errors", result)


if __name__ == "__main__":
    unittest.main()
