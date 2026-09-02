import openvsp as vsp
import pytest


def testFitModel_ResetAndClearState():
    errorMgr = vsp.ErrorMgrSingleton.getInstance()

    # Start from a known clean model state.
    vsp.ClearVSPModel()

    geom_id = vsp.AddGeom("POD", "")
    parm_id = vsp.FindParm(geom_id, "Length", "Design")

    assert vsp.AddFitModelVar(parm_id) is True

    # Clear variables only.
    vsp.ClearFitModelVars()
    assert vsp.GetNumFitModelVars() == 0

    # Clearing targets on an empty state should be a no-op.
    vsp.ClearFitModelTargetPts()
    assert vsp.GetNumFitModelTargetPts() == 0

    # Reset should clear both collections.
    assert vsp.AddFitModelVar(parm_id) is True
    vsp.ResetFitModel()
    assert vsp.GetNumFitModelVars() == 0
    assert vsp.GetNumFitModelTargetPts() == 0

    # Check for errors
    assert errorMgr.GetNumTotalErrors() == 0


if __name__ == "__main__":
    testFitModel_ResetAndClearState()
