"""Slice 3 FitModel target-point tests.

These tests lock down the behavior of the FitModel target-point public API:
- add/delete/get/set target points headlessly (no GUI selection state)
- validate inputs and report failures via ErrorMgr

Note: ErrorMgr is process-global and can retain expected errors from other tests,
so the lifecycle test checks that no *new* errors were emitted (baseline compare).
"""

import math

import openvsp as vsp
import pytest


def testFitModel_TargetPtLifecycle():
    """Happy-path lifecycle: add -> read back -> update -> delete."""

    errorMgr = vsp.ErrorMgrSingleton.getInstance()
    start_errors = errorMgr.GetNumTotalErrors()

    # Reset vehicle + fit model state.
    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    # POD is a supported target geometry type.
    geom_id = vsp.AddGeom("POD", "")

    # Add a single target point. (This should not implicitly run SearchUW.)
    target_pt = vsp.vec3d(1.0, 2.0, 3.0)
    target_index = vsp.AddFitModelTargetPt(
        target_pt, geom_id, 0.25, vsp.FIT_FIXED, 0.75, vsp.FIT_FREE
    )

    assert target_index == 0
    assert vsp.GetNumFitModelTargetPts() == 1

    stored_pt = vsp.GetFitModelTargetPt(target_index)
    assert stored_pt.x() == pytest.approx(1.0)
    assert stored_pt.y() == pytest.approx(2.0)
    assert stored_pt.z() == pytest.approx(3.0)
    assert vsp.GetFitModelTargetGeomID(target_index) == geom_id

    stored_uw = vsp.GetFitModelTargetUW(target_index)
    assert stored_uw.x() == pytest.approx(0.25)
    assert stored_uw.y() == pytest.approx(0.75)
    assert vsp.GetFitModelTargetUType(target_index) == vsp.FIT_FIXED
    assert vsp.GetFitModelTargetWType(target_index) == vsp.FIT_FREE

    updated_pt = vsp.vec3d(-1.0, -2.0, -3.0)
    vsp.SetFitModelTargetPt(
        target_index, updated_pt, geom_id, 0.5, vsp.FIT_FREE, 0.1, vsp.FIT_FIXED
    )

    stored_pt = vsp.GetFitModelTargetPt(target_index)
    assert stored_pt.x() == pytest.approx(-1.0)
    assert stored_pt.y() == pytest.approx(-2.0)
    assert stored_pt.z() == pytest.approx(-3.0)

    stored_uw = vsp.GetFitModelTargetUW(target_index)
    assert stored_uw.x() == pytest.approx(0.5)
    assert stored_uw.y() == pytest.approx(0.1)
    assert vsp.GetFitModelTargetUType(target_index) == vsp.FIT_FREE
    assert vsp.GetFitModelTargetWType(target_index) == vsp.FIT_FIXED

    vsp.DeleteFitModelTargetPt(target_index)
    assert vsp.GetNumFitModelTargetPts() == 0

    assert errorMgr.GetNumTotalErrors() == start_errors


def testFitModel_TargetPtInvalidInputs():
    """Validation tests (negative cases) + ErrorMgr code checks."""

    errorMgr = vsp.ErrorMgrSingleton.getInstance()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    pod_id = vsp.AddGeom("POD", "")
    blank_id = vsp.AddGeom("BLANK", "")

    pt = vsp.vec3d(0.0, 0.0, 0.0)

    assert vsp.AddFitModelTargetPt(pt, "bad_geom_id") == -1
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_PTR

    assert vsp.AddFitModelTargetPt(pt, blank_id) == -1
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_TYPE

    assert vsp.AddFitModelTargetPt(pt, pod_id, 0.5, 99, 0.5, vsp.FIT_FREE) == -1
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_TYPE

    assert vsp.AddFitModelTargetPt(vsp.vec3d(math.nan, 0.0, 0.0), pod_id) == -1
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_INPUT_VAL

    assert (
        vsp.AddFitModelTargetPt(pt, pod_id, math.inf, vsp.FIT_FREE, 0.5, vsp.FIT_FREE)
        == -1
    )
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_INPUT_VAL

    assert vsp.GetNumFitModelTargetPts() == 0

    # Out-of-range operations should report index errors.
    vsp.DeleteFitModelTargetPt(0)
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INDEX_OUT_RANGE

    vsp.GetFitModelTargetPt(0)
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INDEX_OUT_RANGE

    vsp.SetFitModelTargetPt(0, pt, pod_id, 0.5, vsp.FIT_FREE, 0.5, vsp.FIT_FREE)
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INDEX_OUT_RANGE

    assert vsp.GetNumFitModelTargetPts() == 0


if __name__ == "__main__":
    testFitModel_TargetPtLifecycle()
    testFitModel_TargetPtInvalidInputs()
