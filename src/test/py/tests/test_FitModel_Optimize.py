"""Slice 6 FitModel optimize tests."""

import openvsp as vsp
import pytest


def testFitModel_Optimize_ReducesDistance_ForSingleParm():
    errorMgr = vsp.ErrorMgrSingleton.getInstance()
    start_errors = errorMgr.GetNumTotalErrors()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    geom_id = vsp.AddGeom("POD", "")
    length_id = vsp.FindParm(geom_id, "Length", "Design")
    assert len(length_id) > 0

    baseline_length = vsp.GetParmVal(length_id)
    target_length = baseline_length * 1.5

    u = 0.35
    w = 0.6
    target_pt = vsp.CompPnt01(geom_id, 0, u, w)

    vsp.SetParmVal(length_id, target_length)
    vsp.Update()
    target_pt = vsp.CompPnt01(geom_id, 0, u, w)

    vsp.SetParmVal(length_id, baseline_length)
    vsp.Update()

    assert vsp.AddFitModelVar(length_id) is True
    idx = vsp.AddFitModelTargetPt(target_pt, geom_id, u, vsp.FIT_FIXED, w, vsp.FIT_FIXED)
    assert idx == 0

    before = vsp.UpdateFitModelDistance()
    assert before > 0.0

    info = vsp.OptimizeFitModel()
    after = vsp.GetFitModelDistance()

    assert info > 0
    assert after < before
    assert after == pytest.approx(0.0, abs=1e-6)
    assert vsp.GetParmVal(length_id) == pytest.approx(target_length, rel=1e-6, abs=1e-6)
    assert errorMgr.GetNumTotalErrors() == start_errors


def testFitModel_Optimize_Guards():
    errorMgr = vsp.ErrorMgrSingleton.getInstance()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    assert vsp.OptimizeFitModel() == 0
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_INPUT_VAL

    geom_id = vsp.AddGeom("POD", "")
    target_pt = vsp.CompPnt01(geom_id, 0, 0.25, 0.75)

    idx = vsp.AddFitModelTargetPt(target_pt, geom_id, 0.25, vsp.FIT_FIXED, 0.75, vsp.FIT_FIXED)
    assert idx == 0

    assert vsp.OptimizeFitModel() == 0
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_INPUT_VAL

    vsp.ResetFitModel()

    length_id = vsp.FindParm(geom_id, "Length", "Design")
    fine_ratio_id = vsp.FindParm(geom_id, "FineRatio", "Design")
    assert vsp.AddFitModelVar(length_id) is True
    assert vsp.AddFitModelVar(fine_ratio_id) is True

    idx = vsp.AddFitModelTargetPt(target_pt, geom_id, 0.25, vsp.FIT_FREE, 0.75, vsp.FIT_FREE)
    assert idx == 0

    assert vsp.OptimizeFitModel() == 0
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_INPUT_VAL


if __name__ == "__main__":
    testFitModel_Optimize_ReducesDistance_ForSingleParm()
    testFitModel_Optimize_Guards()
