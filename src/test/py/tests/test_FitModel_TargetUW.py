"""Slice 4 FitModel target UW search/refine smoke tests.

Goal: lock down public API calls exist, run headlessly, report errors via ErrorMgr.

Note: ErrorMgr is process-global; tests compare against baseline error count.
"""

import math

import openvsp as vsp
import pytest


def testFitModel_TargetUW_SearchAndRefineSmoke():
    errorMgr = vsp.ErrorMgrSingleton.getInstance()
    start_errors = errorMgr.GetNumTotalErrors()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    geom_id = vsp.AddGeom("POD", "")

    idx = vsp.AddFitModelTargetPt(
        vsp.vec3d(1.0, 2.0, 3.0), geom_id, 0.25, vsp.FIT_FREE, 0.75, vsp.FIT_FREE
    )
    assert idx == 0

    vsp.SearchFitModelTargetUW()
    assert errorMgr.GetNumTotalErrors() == start_errors

    uw = vsp.GetFitModelTargetUW(idx)
    assert math.isfinite(uw.x())
    assert math.isfinite(uw.y())

    vsp.RefineFitModelTargetUW()
    assert errorMgr.GetNumTotalErrors() == start_errors

    uw = vsp.GetFitModelTargetUW(idx)
    assert math.isfinite(uw.x())
    assert math.isfinite(uw.y())


def testFitModel_TargetUW_EmptyGuards():
    errorMgr = vsp.ErrorMgrSingleton.getInstance()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    vsp.SearchFitModelTargetUW()
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_INPUT_VAL

    vsp.RefineFitModelTargetUW()
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_INPUT_VAL


if __name__ == "__main__":
    testFitModel_TargetUW_SearchAndRefineSmoke()
    testFitModel_TargetUW_EmptyGuards()
