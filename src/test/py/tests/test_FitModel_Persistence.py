"""Slice 7 FitModel persistence tests."""

from pathlib import Path

import openvsp as vsp
import pytest


def testFitModel_Persistence_SaveLoadRoundTrip(tmp_path):
    errorMgr = vsp.ErrorMgrSingleton.getInstance()
    start_errors = errorMgr.GetNumTotalErrors()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    geom_id = vsp.AddGeom("POD", "")
    length_id = vsp.FindParm(geom_id, "Length", "Design")
    fine_ratio_id = vsp.FindParm(geom_id, "FineRatio", "Design")

    assert vsp.AddFitModelVar(length_id) is True
    assert vsp.AddFitModelVar(fine_ratio_id) is True

    target_pt = vsp.vec3d(1.25, -2.5, 3.75)
    idx = vsp.AddFitModelTargetPt(
        target_pt, geom_id, 0.2, vsp.FIT_FIXED, 0.8, vsp.FIT_FREE
    )
    assert idx == 0

    fit_file = tmp_path / "roundtrip.fit"
    assert vsp.SaveFitModel(str(fit_file)) is True
    assert fit_file.exists()

    vsp.ResetFitModel()
    assert vsp.GetNumFitModelVars() == 0
    assert vsp.GetNumFitModelTargetPts() == 0

    assert vsp.LoadFitModel(str(fit_file)) == 0
    assert vsp.GetNumFitModelVars() == 2
    assert list(vsp.GetFitModelVarIDs()) == [fine_ratio_id, length_id]
    assert vsp.GetNumFitModelTargetPts() == 1
    assert vsp.GetFitModelTargetGeomID(0) == geom_id

    stored_pt = vsp.GetFitModelTargetPt(0)
    assert stored_pt.x() == pytest.approx(1.25)
    assert stored_pt.y() == pytest.approx(-2.5)
    assert stored_pt.z() == pytest.approx(3.75)

    stored_uw = vsp.GetFitModelTargetUW(0)
    assert stored_uw.x() == pytest.approx(0.2)
    assert stored_uw.y() == pytest.approx(0.8)
    assert vsp.GetFitModelTargetUType(0) == vsp.FIT_FIXED
    assert vsp.GetFitModelTargetWType(0) == vsp.FIT_FREE
    assert errorMgr.GetNumTotalErrors() == start_errors


def testFitModel_Persistence_LoadAppendAndErrors(tmp_path):
    errorMgr = vsp.ErrorMgrSingleton.getInstance()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    geom_id = vsp.AddGeom("POD", "")
    length_id = vsp.FindParm(geom_id, "Length", "Design")

    assert vsp.AddFitModelVar(length_id) is True
    idx = vsp.AddFitModelTargetPt(
        vsp.vec3d(0.0, 1.0, 2.0), geom_id, 0.3, vsp.FIT_FREE, 0.4, vsp.FIT_FIXED
    )
    assert idx == 0

    fit_file = tmp_path / "append.fit"
    assert vsp.SaveFitModel(str(fit_file)) is True

    assert vsp.LoadFitModel(str(fit_file), False) == 0
    assert vsp.GetNumFitModelVars() == 1
    assert list(vsp.GetFitModelVarIDs()) == [length_id]
    assert vsp.GetNumFitModelTargetPts() == 2

    missing_file = tmp_path / "missing.fit"
    assert vsp.LoadFitModel(str(missing_file)) == 1
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_FILE_DOES_NOT_EXIST

    bad_file = tmp_path / "bad.fit"
    Path(bad_file).write_text("not xml", encoding="utf-8")
    assert vsp.LoadFitModel(str(bad_file)) != 0
    assert errorMgr.PopLastError().GetErrorCode() == vsp.VSP_WRONG_FILE_TYPE


if __name__ == "__main__":
    testFitModel_Persistence_SaveLoadRoundTrip(Path("."))
    testFitModel_Persistence_LoadAppendAndErrors(Path("."))
