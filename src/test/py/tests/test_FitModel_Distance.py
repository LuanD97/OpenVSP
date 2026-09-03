"""Slice 5 FitModel distance metric tests."""

import math

import openvsp as vsp
import pytest


def testFitModel_Distance_ComputesExpectedPointResidual():
    errorMgr = vsp.ErrorMgrSingleton.getInstance()
    start_errors = errorMgr.GetNumTotalErrors()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    geom_id = vsp.AddGeom("POD", "")

    u = 0.3
    w = 0.4
    surf_pt = vsp.CompPnt01(geom_id, 0, u, w)

    target_pt = vsp.vec3d(surf_pt.x(), surf_pt.y() + 3.0, surf_pt.z() + 4.0)

    idx = vsp.AddFitModelTargetPt(target_pt, geom_id, u, vsp.FIT_FIXED, w, vsp.FIT_FIXED)
    assert idx == 0

    dist = vsp.UpdateFitModelDistance()
    assert dist == pytest.approx(5.0)
    assert vsp.GetFitModelDistance() == pytest.approx(5.0)
    assert errorMgr.GetNumTotalErrors() == start_errors


def testFitModel_Distance_EmptyGuardAndCachedValue():
    errorMgr = vsp.ErrorMgrSingleton.getInstance()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    assert vsp.GetFitModelDistance() == pytest.approx(0.0)

    dist = vsp.UpdateFitModelDistance()
    assert dist == pytest.approx(0.0)
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_INVALID_INPUT_VAL

    assert math.isfinite(vsp.GetFitModelDistance())
    assert vsp.GetFitModelDistance() == pytest.approx(0.0)


if __name__ == "__main__":
    testFitModel_Distance_ComputesExpectedPointResidual()
    testFitModel_Distance_EmptyGuardAndCachedValue()
