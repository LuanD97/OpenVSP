import openvsp as vsp


def testFitModel_VarLifecycle():
    errorMgr = vsp.ErrorMgrSingleton.getInstance()

    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    geom_id = vsp.AddGeom("POD", "")
    length_id = vsp.FindParm(geom_id, "Length", "Design")
    fine_ratio_id = vsp.FindParm(geom_id, "FineRatio", "Design")

    assert len(length_id) > 0
    assert len(fine_ratio_id) > 0

    assert vsp.AddFitModelVar(length_id) is True
    assert vsp.GetNumFitModelVars() == 1
    assert list(vsp.GetFitModelVarIDs()) == [length_id]

    assert vsp.AddFitModelVar(fine_ratio_id) is True
    assert vsp.GetNumFitModelVars() == 2
    assert list(vsp.GetFitModelVarIDs()) == [fine_ratio_id, length_id]

    # Duplicate add should fail and keep state unchanged.
    assert vsp.AddFitModelVar(length_id) is False
    assert vsp.GetNumFitModelVars() == 2

    # Invalid parm should fail and keep state unchanged.
    assert vsp.AddFitModelVar("bad_parm_id") is False
    assert vsp.GetNumFitModelVars() == 2

    vsp.DeleteFitModelVar(length_id)
    assert vsp.GetNumFitModelVars() == 1
    assert list(vsp.GetFitModelVarIDs()) == [fine_ratio_id]

    # Deleting a missing var should be rejected and not mutate state.
    vsp.DeleteFitModelVar(length_id)
    assert vsp.GetNumFitModelVars() == 1
    assert list(vsp.GetFitModelVarIDs()) == [fine_ratio_id]

    vsp.ClearFitModelVars()
    assert vsp.GetNumFitModelVars() == 0
    assert list(vsp.GetFitModelVarIDs()) == []

    # Duplicate add, bad parm, and deleting missing var should have reported errors.
    assert errorMgr.GetNumTotalErrors() >= 3


if __name__ == "__main__":
    testFitModel_VarLifecycle()
