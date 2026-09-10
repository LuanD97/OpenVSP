"""Real-binding tests for the Fit Model MCP tools."""

import openvsp as vsp
import pytest

from openvsp.mcp import _fitmodel as fm


def _sample_to_pts(geom_id, nu, nw, path):
    """Sample a regular (nu x nw) grid of surface points and write them as a .pts file.

    Returns the list of (x, y, z) points, in the same order they were written.
    """
    points = []
    with open(path, "w", encoding="utf-8") as f:
        for i in range(nu):
            for j in range(nw):
                u = (i + 0.5) / nu
                w = (j + 0.5) / nw
                pt = vsp.CompPnt01(geom_id, 0, u, w)
                x, y, z = pt.x(), pt.y(), pt.z()
                f.write(f"{x} {y} {z}\n")
                points.append((x, y, z))
    return points


@pytest.fixture
def pod_case(tmp_path):
    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    geom_id = vsp.AddGeom("POD", "")
    length_id = vsp.FindParm(geom_id, "Length", "Design")
    fine_id = vsp.FindParm(geom_id, "FineRatio", "Design")

    vsp.SetParmVal(length_id, 7.5)
    vsp.SetParmVal(fine_id, 9.0)
    vsp.Update()

    pts_path = tmp_path / "pod.pts"
    points = _sample_to_pts(geom_id, 12, 6, pts_path)

    vsp.SetParmVal(length_id, 4.0)
    vsp.SetParmVal(fine_id, 15.0)
    vsp.Update()

    return {
        "geom_id": geom_id,
        "length_id": length_id,
        "fine_id": fine_id,
        "pts_path": str(pts_path),
        "points": points,
    }


@pytest.fixture
def err_baseline():
    return vsp.ErrorMgrSingleton.getInstance().GetNumTotalErrors()


# ---------------------------------------------------------------------------
# User Story 1
# ---------------------------------------------------------------------------


def test_import_point_cloud(pod_case, err_baseline):
    result = fm.import_point_cloud(pod_case["pts_path"])
    assert result["num_points"] == 72
    assert vsp.ErrorMgrSingleton.getInstance().GetNumTotalErrors() == err_baseline


def test_import_missing_file_reports_error(err_baseline):
    vsp.ClearVSPModel()
    before = len(vsp.FindGeoms())
    result = fm.import_point_cloud("/tmp/does_not_exist_fitmodel_mcp.pts")
    assert "error" in result
    assert "does_not_exist_fitmodel_mcp.pts" in result["error"]
    assert len(vsp.FindGeoms()) == before
    assert vsp.ErrorMgrSingleton.getInstance().GetNumTotalErrors() == err_baseline


def test_add_and_list_vars(pod_case, err_baseline):
    result = fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    assert result["added"] == 2
    names = {v["name"] for v in result["vars"]}
    assert names == {"Length", "FineRatio"}
    for v in result["vars"]:
        assert v["group"] == "Design"
        assert v["geom_id"] == pod_case["geom_id"]
    assert vsp.ErrorMgrSingleton.getInstance().GetNumTotalErrors() == err_baseline


def test_duplicate_and_bogus_var_rejected_atomically(pod_case, err_baseline):
    fm.add_fit_model_vars([pod_case["length_id"]])
    before = vsp.GetNumFitModelVars()
    result = fm.add_fit_model_vars([pod_case["fine_id"], pod_case["length_id"]])
    assert "error" in result
    assert vsp.GetNumFitModelVars() == before


def test_targets_search_distance(pod_case, err_baseline):
    fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    targets = [
        {"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]}
        for (x, y, z) in pod_case["points"]
    ]
    add_result = fm.add_fit_model_targets(targets)
    assert add_result["count"] == 72

    fm.search_fit_model_target_uw()
    dist_result = fm.update_fit_model_distance()
    assert dist_result["rms"] > 0


def test_target_out_of_range_uw_and_blank_geom_rejected(pod_case, err_baseline):
    before = vsp.GetNumFitModelTargetPts()

    result = fm.add_fit_model_targets(
        [{"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": pod_case["geom_id"], "u": 1.5}]
    )
    assert "error" in result
    assert vsp.GetNumFitModelTargetPts() == before

    blank_id = vsp.AddGeom("BLANK", "")
    result = fm.add_fit_model_targets(
        [{"x": 0.0, "y": 0.0, "z": 0.0, "geom_id": blank_id}]
    )
    assert "error" in result
    assert vsp.GetNumFitModelTargetPts() == before


def test_single_optimize_improves_but_stops_short(pod_case, err_baseline):
    fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    targets = [
        {"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]}
        for (x, y, z) in pod_case["points"]
    ]
    fm.add_fit_model_targets(targets)
    fm.search_fit_model_target_uw()

    result = fm.optimize_fit_model()
    assert result["rms_after"] < result["rms_before"]
    assert 1 <= result["info"] <= 4

    length_val = vsp.GetParmVal(pod_case["length_id"])
    fine_val = vsp.GetParmVal(pod_case["fine_id"])
    length_close = abs(length_val - 7.5) <= 0.001 * 7.5
    fine_close = abs(fine_val - 9.0) <= 0.001 * 9.0
    assert not (length_close and fine_close)


def test_deleted_geom_reports_dangling(pod_case, err_baseline):
    fm.add_fit_model_vars([pod_case["length_id"]])
    fm.add_fit_model_targets(
        [{"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]} for (x, y, z) in pod_case["points"][:5]]
    )
    vsp.DeleteGeom(pod_case["geom_id"])

    result = fm.optimize_fit_model()
    assert "error" in result
    assert "dangling_target_indices" in result
    assert result["dangling_target_indices"] == list(range(5))


def test_saved_model_keeps_fitted_values(pod_case, err_baseline, tmp_path):
    fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    targets = [
        {"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]}
        for (x, y, z) in pod_case["points"]
    ]
    fm.add_fit_model_targets(targets)
    fm.search_fit_model_target_uw()
    fm.optimize_fit_model()

    length_val = vsp.GetParmVal(pod_case["length_id"])
    fine_val = vsp.GetParmVal(pod_case["fine_id"])

    out_file = tmp_path / "pod_fitted.vsp3"
    vsp.WriteVSPFile(str(out_file), 0)
    vsp.ClearVSPModel()
    vsp.ReadVSPFile(str(out_file))

    geom_id = vsp.FindGeoms()[0]
    length_id2 = vsp.FindParm(geom_id, "Length", "Design")
    fine_id2 = vsp.FindParm(geom_id, "FineRatio", "Design")
    assert vsp.GetParmVal(length_id2) == pytest.approx(length_val)
    assert vsp.GetParmVal(fine_id2) == pytest.approx(fine_val)


# ---------------------------------------------------------------------------
# User Story 2
# ---------------------------------------------------------------------------


def test_convergence_recovers_pod(pod_case, err_baseline):
    """SC-001."""
    fm.import_point_cloud(pod_case["pts_path"])  # not required for fitting itself
    fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    targets = [
        {"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]}
        for (x, y, z) in pod_case["points"]
    ]
    fm.add_fit_model_targets(targets)

    result = fm.fit_model_to_convergence()

    assert result["stop_reason"] == "converged"
    assert result["passes"] <= 10
    assert result["rms_final"] < 1e-6

    length_val = vsp.GetParmVal(pod_case["length_id"])
    fine_val = vsp.GetParmVal(pod_case["fine_id"])
    assert length_val == pytest.approx(7.5, rel=1e-3)
    assert fine_val == pytest.approx(9.0, rel=1e-3)


def test_convergence_pass_limit(pod_case, err_baseline):
    fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    targets = [
        {"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]}
        for (x, y, z) in pod_case["points"]
    ]
    fm.add_fit_model_targets(targets)

    result = fm.fit_model_to_convergence(max_passes=1)
    assert result["passes"] == 1
    assert result["stop_reason"] == "pass_limit"


def test_convergence_fuselage_and_wing(err_baseline, tmp_path):
    """SC-006."""
    vsp.ClearVSPModel()
    vsp.ResetFitModel()

    fuse_id = vsp.AddGeom("FUSELAGE", "")
    wing_id = vsp.AddGeom("WING", "")
    vsp.Update()

    fuse_length_id = vsp.FindParm(fuse_id, "Length", "Design")

    # Find an active parm on the wing's first XSec. Span may be inactive
    # under the default driver group (if so, "Inactive Parm" shows up in
    # optimize_fit_model's info/vsp_errors); Root Chord is active by default.
    xsec_surf = vsp.GetXSecSurf(wing_id, 0)
    xsec1 = vsp.GetXSec(xsec_surf, 1)
    span_id = vsp.FindParm(xsec1, "Root_Chord", "XSec")

    fuse_baseline = vsp.GetParmVal(fuse_length_id)
    wing_baseline = vsp.GetParmVal(span_id)

    fuse_pts_path = tmp_path / "fuse.pts"
    wing_pts_path = tmp_path / "wing.pts"
    fuse_points = _sample_to_pts(fuse_id, 10, 8, fuse_pts_path)
    wing_points = _sample_to_pts(wing_id, 10, 8, wing_pts_path)

    # Perturb both parms by +20% and refresh the geometry.
    vsp.SetParmVal(fuse_length_id, fuse_baseline * 1.2)
    vsp.SetParmVal(span_id, wing_baseline * 1.2)
    vsp.Update()

    assert vsp.AddFitModelVar(fuse_length_id) is True
    assert vsp.AddFitModelVar(span_id) is True

    for x, y, z in fuse_points:
        idx = vsp.AddFitModelTargetPt(vsp.vec3d(x, y, z), fuse_id)
        assert idx >= 0
    for x, y, z in wing_points:
        idx = vsp.AddFitModelTargetPt(vsp.vec3d(x, y, z), wing_id)
        assert idx >= 0

    rms_initial = vsp.UpdateFitModelDistance()
    result = fm.fit_model_to_convergence()

    assert result["rms_final"] <= 0.1 * rms_initial


# ---------------------------------------------------------------------------
# User Story 3
# ---------------------------------------------------------------------------


def test_cloud_summary_and_paging(err_baseline, tmp_path):
    """SC-004."""
    import random

    random.seed(0)
    pts_path = tmp_path / "big_cloud.pts"
    with open(pts_path, "w", encoding="utf-8") as f:
        for _ in range(100_000):
            f.write(f"{random.random()} {random.random()} {random.random()}\n")

    import_result = fm.import_point_cloud(str(pts_path))
    cloud_id = import_result["geom_id"]
    assert import_result["num_points"] == 100_000

    summary = fm.get_point_cloud_summary(cloud_id)
    assert summary["num_points"] == 100_000
    assert "points" not in summary
    for value in summary["bbox_min"] + summary["bbox_max"]:
        assert 0.0 <= value <= 1.0

    page = fm.get_point_cloud_points(cloud_id, count=5000)
    assert page["returned"] == 1000
    assert page["next_start"] == 1000


def test_targets_from_cloud_box_and_stride(pod_case, err_baseline):
    import math

    points = pod_case["points"]
    bbox_min = [-1000.0, -1000.0, -1000.0]
    bbox_max = [1000.0, 1000.0, 0.0]  # keep only points with z <= 0
    in_box = [p for p in points if p[2] <= 0.0]
    assert 0 < len(in_box) < len(points)

    cloud_result = fm.import_point_cloud(pod_case["pts_path"])
    cloud_id = cloud_result["geom_id"]

    result = fm.add_fit_model_targets_from_cloud(
        cloud_id, pod_case["geom_id"], bbox_min, bbox_max, stride=10
    )
    assert "error" not in result
    assert result["count"] == math.ceil(len(in_box) / 10)

    first_pt = vsp.GetFitModelTargetPt(result["first_index"])
    expected = in_box[0]
    assert first_pt.x() == pytest.approx(expected[0])
    assert first_pt.y() == pytest.approx(expected[1])
    assert first_pt.z() == pytest.approx(expected[2])


def test_targets_from_cloud_empty_box(pod_case, err_baseline):
    cloud_result = fm.import_point_cloud(pod_case["pts_path"])
    cloud_id = cloud_result["geom_id"]
    before = vsp.GetNumFitModelTargetPts()

    result = fm.add_fit_model_targets_from_cloud(
        cloud_id, pod_case["geom_id"], [1000.0, 1000.0, 1000.0], [2000.0, 2000.0, 2000.0]
    )
    assert "error" in result
    assert vsp.GetNumFitModelTargetPts() == before


# ---------------------------------------------------------------------------
# User Story 4
# ---------------------------------------------------------------------------


def test_update_target_leaves_others(pod_case, err_baseline):
    targets = [
        {"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]}
        for (x, y, z) in pod_case["points"][:50]
    ]
    fm.add_fit_model_targets(targets)

    other_before = fm.get_fit_model_target(5)
    blank_id = vsp.AddGeom("BLANK", "")
    vsp.DeleteGeom(blank_id)  # exercise a churned ID space, no-op otherwise

    result = fm.update_fit_model_target(10, geom_id=pod_case["geom_id"], u_type="FIXED", w_type="FIXED")
    assert "error" not in result
    assert result["u_type"] == "FIXED"
    assert result["w_type"] == "FIXED"

    other_after = fm.get_fit_model_target(5)
    assert other_after == other_before


def test_fit_file_round_trip(pod_case, err_baseline, tmp_path):
    fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    targets = [
        {"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"], "u_type": "FIXED"}
        for (x, y, z) in pod_case["points"][:10]
    ]
    fm.add_fit_model_targets(targets)

    before_vars = fm.list_fit_model_vars()
    before_targets = fm.list_fit_model_targets()

    fit_file = tmp_path / "roundtrip.fit"
    save_result = fm.save_fit_model(str(fit_file))
    assert "error" not in save_result

    fm.reset_fit_model()
    load_result = fm.load_fit_model(str(fit_file))
    assert "error" not in load_result

    after_vars = fm.list_fit_model_vars()
    after_targets = fm.list_fit_model_targets()

    assert {v["parm_id"] for v in after_vars["vars"]} == {v["parm_id"] for v in before_vars["vars"]}
    for b, a in zip(before_targets["targets"], after_targets["targets"]):
        assert a["point"] == pytest.approx(b["point"])
        assert a["geom_id"] == b["geom_id"]
        assert a["u"] == pytest.approx(b["u"])
        assert a["w"] == pytest.approx(b["w"])
        assert a["u_type"] == b["u_type"]
        assert a["w_type"] == b["w_type"]


def test_fit_file_append(pod_case, err_baseline, tmp_path):
    fm.add_fit_model_vars([pod_case["length_id"]])
    targets = [
        {"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]}
        for (x, y, z) in pod_case["points"][:5]
    ]
    fm.add_fit_model_targets(targets)

    fit_file = tmp_path / "append.fit"
    fm.save_fit_model(str(fit_file))

    before_vars = vsp.GetNumFitModelVars()
    before_targets = vsp.GetNumFitModelTargetPts()

    result = fm.load_fit_model(str(fit_file), append=True)
    assert "error" not in result
    assert result["num_vars"] == before_vars  # same var re-added is a duplicate, still 1
    assert result["num_targets"] == before_targets * 2


def test_fit_file_into_model_missing_parms(pod_case, err_baseline, tmp_path):
    fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    saved_var_ids = set(vsp.GetFitModelVarIDs())

    fit_file = tmp_path / "missing_parms.fit"
    fm.save_fit_model(str(fit_file))

    vsp.ClearVSPModel()
    result = fm.load_fit_model(str(fit_file))
    assert "error" in result
    assert set(result["missing_parm_ids"]) == saved_var_ids


def test_delete_var_and_target(pod_case, err_baseline):
    fm.add_fit_model_vars([pod_case["length_id"], pod_case["fine_id"]])
    fm.add_fit_model_targets(
        [{"x": x, "y": y, "z": z, "geom_id": pod_case["geom_id"]} for (x, y, z) in pod_case["points"][:3]]
    )

    del_var_result = fm.delete_fit_model_var(pod_case["length_id"])
    assert del_var_result["num_vars"] == 1

    del_target_result = fm.delete_fit_model_target(0)
    assert del_target_result["num_targets"] == 2
