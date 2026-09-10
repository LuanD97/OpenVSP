---

description: "Task list for Fit Model Tools for Agents"
---

# Tasks: Fit Model Tools for Agents

**Input**: Design documents from `/specs/001-fitmodel-mcp-tools/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/mcp-tools.md](contracts/mcp-tools.md),
[quickstart.md](quickstart.md)

**Tests**: REQUIRED. Constitution Principle IV requires test-first development: write the tests
for a slice, confirm they fail, then implement. Each phase lists its tests before its
implementation tasks.

**Organization**: Tasks are grouped by user story (US1–US4 from spec.md) so each story can be
built and validated on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US4 from spec.md. Setup, Foundational and Polish tasks have no story label
- `R#` refers to research.md decisions. "Contract" means contracts/mcp-tools.md

## Path Conventions

These abbreviations are used throughout. Paths are relative to the repository root.

- `MCP/` = `src/python_api/packages/openvsp/openvsp/mcp/`
- `UT/` = `src/python_api/packages/openvsp/openvsp/tests/` (fake-`vsp` unit tests)
- `RT` = `src/test/py/tests/test_FitModel_MCP.py` (real-binding tests)
- `PY` = `~/build/projects/openvsp/vsp/venv/bin/python`
- **Sync before running `RT`**: from the repository root,
  `cmake -E copy_directory src/python_api/packages/ ~/build/projects/openvsp/vsp/python_pseudo/`.
  The venv imports `openvsp` from a *copy* in `python_pseudo/`. Where tasks below say
  `copy_package`, use this command instead: the build tree's `copy_package` target copies from the
  main checkout, not this worktree (see quickstart.md).

## Conventions every task must follow (constitution Principle I, plan.md)

- Match `MCP/_geometry.py`:
  - module docstring and `from __future__ import annotations`
  - `from openvsp.mcp._core import _vsp, mcp`
  - `# ===` banner sections
  - `@mcp.tool()` on every tool, with a docstring that has an `Args:` block
- Every tool returns `dict[str, Any]`, never raises, and returns `{"error": ...}` on failure (R3).
- Every tool that calls the engine does so through the R2 error-capture helper (T008).
- Unit tests use `unittest.TestCase` with `_make_fake_vsp()`/`_load_submodule()`, in the style of
  `UT/test_mcp_geometry.py`. Real-binding tests are plain pytest functions, in the style of
  `src/test/py/tests/test_FitModel_Optimize.py`. They compare `ErrorMgr` counts, never assert zero.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm a green baseline and create empty files so later phases have somewhere to go.

- [X] T001 Confirm the baseline is green before changing anything:
  - run `PY -m pytest src/python_api/packages/openvsp/openvsp/tests -q`, expecting all existing
    MCP tests to pass
  - run `PY -m pytest src/test/py/tests -q -k FitModel`, expecting all seven `test_FitModel_*.py`
    to pass

  Record any pre-existing failures in the task notes. Don't fix them here.
- [X] T002 [P] Create `MCP/_fitmodel.py` containing:
  - the module docstring `"""Point cloud access and Fit Model (point-cloud-to-parametric fitting) MCP tools."""`
  - `from __future__ import annotations`
  - imports for `json`, `math`, `xml.etree.ElementTree as ET`, `from typing import Any`, and
    `from openvsp.mcp._core import _vsp, mcp`
  - empty `# ===` banner sections, in order: Helpers, Point cloud, Setup state, Variables,
    Targets, Solving, Persistence

  Add no tools yet.
- [X] T003 [P] Create `UT/test_mcp_fitmodel.py`:
  - the module docstring `"""Tests for MCP point cloud and Fit Model tools."""`
  - the same header as `UT/test_mcp_geometry.py`: the `sys.path` insert, the import of
    `_load_submodule`/`_make_fake_vsp`, and `_SUBMODULE` pointing at `mcp/_fitmodel.py`
  - a base class `_FitModelTestBase(unittest.TestCase)` whose `setUp` builds
    `self.fake_vsp`/`self.mod` and whose `tearDown` pops `sys.modules["openvsp"]`
- [X] T004 [P] Create `RT` (`src/test/py/tests/test_FitModel_MCP.py`):
  - docstring `"""Real-binding tests for the Fit Model MCP tools."""`
  - `import openvsp as vsp`, `import pytest`, `from openvsp.mcp import _fitmodel as fm`
  - helper `_sample_to_pts(geom_id, nu, nw, path)`, which writes `CompPnt01(geom_id, 0, (i+0.5)/nu, (j+0.5)/nw)`
    points as `x y z` lines and returns the list of `(x, y, z)`
  - fixture `pod_case(tmp_path)`, which:
    1. clears the model and fit (`ClearVSPModel`, `ResetFitModel`)
    2. adds a POD and sets `Length=7.5`, `FineRatio=9.0` (Design group), then `Update`
    3. samples 12×6 points to `tmp_path/"pod.pts"`
    4. perturbs the POD to `4.0`/`15.0`, then `Update`
    5. returns a dict with `geom_id`, `length_id`, `fine_id`, `pts_path` and `points`
  - fixture `err_baseline`, which returns `ErrorMgrSingleton.getInstance().GetNumTotalErrors()`
- [X] T005 Register the module in `MCP/__init__.py` by adding `_fitmodel,` to the side-effect
  import tuple after `_fea,`. Depends on T002.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared helpers every tool relies on: error capture, input parsing and
validation, variable/target description, the dangling-reference check, and the all-or-nothing
target batch. Also the test-harness support for them.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 [P] Extend `UT/_mcp_test_utils.py`:
  - **Fake error queue.** Add a `_FakeErrorMgr` class holding a list of `(code, message)`:
    - `GetNumTotalErrors()`
    - `PopLastError()`: returns an object with `GetErrorCode()`/`GetErrorString()` and pops the
      newest entry
    - `SilenceErrors()`: records `self.silenced = True`
    - `push(code, message)`: a test helper

    In `_make_fake_vsp()`, set `vsp.ErrorMgrSingleton.getInstance.return_value = _FakeErrorMgr()`.
  - **Constants and defaults.** Set `vsp.FIT_FIXED = 0` and `vsp.FIT_FREE = 1`, placed after the
    constant loops so those loops don't overwrite them. Add default return values:

    | Function | Default |
    |----------|---------|
    | `ValidParm` | `True` |
    | `GetFitModelVarIDs` | `()` |
    | `GetNumFitModelVars` | `0` |
    | `GetNumFitModelTargetPts` | `0` |
    | `AddFitModelVar` | `True` |
    | `AddFitModelTargetPt` | `0` |
    | `UpdateFitModelDistance` | `0.0` |
    | `GetFitModelDistance` | `0.0` |
    | `OptimizeFitModel` | `2` |
    | `SaveFitModel` | `True` |
    | `LoadFitModel` | `0` |
    | `GetParmGroupName` | `"Design"` |
    | `GetPtCloudPnts` | `()` |

  - **Server loader.** Add `"_fitmodel"` to the `submodules` list in `_load_full_server`.

  Confirm the existing suite still passes: `PY -m pytest UT -q`.
- [X] T007 Write failing unit tests for the Phase 2 helpers in `UT/test_mcp_fitmodel.py`. Call the
  private helpers directly as `self.mod._name`.
  - `TestErrorCapture`:
    - an error pushed during the wrapped call is returned in `vsp_errors` as `{code, message}`
    - an error pushed *before* the call is not returned and is still on the queue afterwards
    - `SilenceErrors` was called
    - an exception raised inside the call becomes `{"error": str(exc)}`
  - `TestFitTypeParsing`:
    - `"free"`, `"FREE"`, `"Fixed"` map to 1/0
    - `"other"` is rejected with a reason
    - ints 0/1 are converted back to `"FIXED"`/`"FREE"`
  - `TestValidateTargetSpec`:
    - a missing `x`/`y`/`z`/`geom_id`, a non-finite coordinate, `u=1.5`, `w=-0.1`, a bad type
      string, or a `geom_id` not in the model each give a reason string naming the field
    - defaults are u=w=0.5, FREE/FREE
  - `TestVarDescription`:
    - a parm found only through `GetGeomParmIDs` of geom `g2` (an XSec-owned parm) reports
      `geom_id="g2"`
    - `ValidParm=False` gives `valid: False, value: None`
  - `TestDanglingCheck`:
    - a target whose `GetFitModelTargetGeomID` is not in `FindGeoms()` is listed by index
    - a var failing `ValidParm` is listed by ID
  - `TestTargetBatch`:
    - success returns `first_index`/`last_index`/`count`
    - a Python-invalid entry means no `AddFitModelTargetPt` calls and `invalid` holds every bad
      position
    - an engine rejection (`AddFitModelTargetPt` returns -1 and pushes an error) on entry 2 of 3
      means the other added targets are deleted highest index first with
      `DeleteFitModelTargetPt`, and the result lists position 2 with the engine message
    - more than 10,000 entries is rejected before any engine call
- [X] T008 Implement the error-capture helpers in `MCP/_fitmodel.py` (R2):
  - `_capture(fn) -> tuple[Any, list[dict]]`, which does the following in order:
    1. gets `vsp = _vsp()` and `em = vsp.ErrorMgrSingleton.getInstance()`
    2. calls `em.SilenceErrors()`
    3. records `base = em.GetNumTotalErrors()`
    4. runs `result = fn(vsp)`
    5. pops `max(0, em.GetNumTotalErrors() - base)` errors with `PopLastError()`, oldest first in
       the returned list
    6. returns `(result, errors)`
  - `_error(message, **extra) -> dict`, which returns `{"error": message, **extra}`
  - `_engine_failed(errors, context) -> dict | None`, which returns an `_error` joining the messages,
    with `vsp_errors=errors`, when `errors` is non-empty

  Run `TestErrorCapture` and confirm it passes.
- [X] T009 Implement the parsing and validation helpers in `MCP/_fitmodel.py`:
  - `_parse_fit_type(value) -> tuple[int | None, str | None]` (case-insensitive `"FREE"`/`"FIXED"`, R4)
  - `_fit_type_name(int) -> str`
  - `_vec3_list(v) -> list[float]`
  - `_finite(*vals) -> bool`
  - `_validate_target_spec(spec, position, geom_ids) -> tuple[dict | None, str | None]`, which
    returns a normalised `{point, geom_id, u, w, u_type, w_type}` or a reason, applying the
    data-model Target Point rules including the u/w range `[0, 1]` (R5)

  Run `TestFitTypeParsing` and `TestValidateTargetSpec` and confirm they pass.
- [X] T010 Implement the description helpers in `MCP/_fitmodel.py`:
  - `_parm_geom_map(vsp) -> dict[str, str]`, which scans `GetGeomParmIDs(g)` for every
    `g` in `FindGeoms()` (R9)
  - `_describe_var(vsp, parm_id, geom_map) -> dict` (Fit Variable shape: `valid` from
    `ValidParm`, and name/group/value only when valid)
  - `_list_vars(vsp) -> list[dict]` (engine order, from `GetFitModelVarIDs()`)
  - `_describe_target(vsp, index) -> dict` (Target Point shape, with `u_type`/`w_type` as strings)
  - `_dangling(vsp) -> tuple[list[int], list[str]]` (R10)

  Run `TestVarDescription` and `TestDanglingCheck` and confirm they pass.
- [X] T011 Implement `_add_target_batch(vsp, specs) -> dict` in `MCP/_fitmodel.py` (R6):
  1. Reject more than `_MAX_BATCH = 10000` specs.
  2. Validate every spec with `_validate_target_spec` against `set(FindGeoms())`. Collect all
     reasons as `invalid: [{position, reason}]`, and return an error without touching the engine
     if any fail.
  3. Add each spec with `AddFitModelTargetPt(vsp.vec3d(*point), geom_id, u, u_type, w, w_type)`,
     capturing engine errors per entry.
  4. If any entry fails, delete the added indices highest first and return an error with every
     failing position.
  5. On success return `{count, first_index, last_index, num_targets}`.

  Run `TestTargetBatch` and confirm it passes.

**Checkpoint**: `PY -m pytest UT/test_mcp_fitmodel.py -q` passes all helper tests. User stories can
now begin.

---

## Phase 3: User Story 1 - Refine a parametric model against an imported point cloud (Priority: P1) 🎯 MVP

**Goal**: An agent can import a cloud, set up fit variables and targets, run correspondence,
measure the fit error, optimize, and read back the results using only these tools. The model is
then saved with the existing `write_vsp_file`.

**Independent Test**: Use `pod_case` in `RT`. Import the sampled cloud, add both variables, add the
72 sampled points as targets, search/refine, measure the distance (> 0), optimize once, and confirm
the distance fell and the values moved toward 7.5/9.0. Save, reopen, and confirm the values persist.

### Tests for User Story 1 ⚠️ Write first and confirm they fail

- [X] T012 [P] [US1] Add failing unit tests to `UT/test_mcp_fitmodel.py`:
  - `TestImportPointCloud`:
    - success gives `{geom_id, num_points}`
    - `ImportFile` returning `"NONE"` gives an error naming the file
    - zero points gives an error and `DeleteGeom` is called on the new ID
  - `TestSetupState`: `reset_fit_model`/`clear_fit_model_vars`/`clear_fit_model_targets` call
    the right engine function and return counts
  - `TestAddVars`:
    - a list of two gives `added: 2` and `vars`
    - an ID failing `ValidParm`, or a duplicate (within the list or already in
      `GetFitModelVarIDs`), gives `invalid` and no `AddFitModelVar` calls
    - an engine rejection on the 2nd entry means the 1st is rolled back with `DeleteFitModelVar`
    - an empty list or more than 1000 entries is rejected
  - `TestListVars`: shape and count
  - `TestAddTargets`: delegates to the batch (success and invalid shapes pass through)
  - `TestSolving`:
    - search/refine/optimize with a dangling target return an error listing
      `dangling_target_indices` and do not call the engine function
    - `update_fit_model_distance` with 0 targets returns `rms: 0.0` without calling
      `UpdateFitModelDistance` (R11)
    - `get_fit_model_distance` returns the cached value
    - `optimize_fit_model` returns `info`, `info_meaning` (e.g. 2 → the R12 text), `rms_before`,
      `rms_after`, `vars`
    - an engine error pushed during optimize turns into an error with `vsp_errors`
- [X] T013 [P] [US1] Add failing real-binding tests to `RT`:
  - `test_import_point_cloud`: `num_points == 72`
  - `test_import_missing_file_reports_error`: error names the file, and the `FindGeoms()` count
    is unchanged
  - `test_add_and_list_vars`: names `Length`/`FineRatio`, group `Design`, `geom_id` is the POD
  - `test_duplicate_and_bogus_var_rejected_atomically`: `num_vars` is unchanged after a failing
    batch
  - `test_targets_search_distance`: `rms > 0` after search
  - `test_target_out_of_range_uw_and_blank_geom_rejected`: `u=1.5` is rejected, a `BLANK` geom is
    rejected with the engine message, and the target count is unchanged
  - `test_single_optimize_improves_but_stops_short`: `rms_after < rms_before`, `info` in 1–4, and
    at least one of Length/FineRatio *not* within 0.1% of the truth
  - `test_deleted_geom_reports_dangling`: `DeleteGeom` the POD, then `optimize_fit_model` gives an
    error with `dangling_target_indices`
  - `test_saved_model_keeps_fitted_values`: `vsp.WriteVSPFile` to `tmp_path`, `ClearVSPModel`,
    `ReadVSPFile`, and the values match the post-optimize values

  Each test ends with the error count equal to `err_baseline`.

### Implementation for User Story 1

- [X] T014 [US1] Implement `import_point_cloud(file_name: str)` in the Point cloud section of
  `MCP/_fitmodel.py`:
  1. Call `ImportFile(file_name, vsp.IMPORT_PTS, "")` via `_capture`.
  2. Treat `"NONE"` or an empty ID as an error naming the file.
  3. Get the count with `len(GetPtCloudPnts(id))`. If it is 0, call `DeleteGeom(id)` and return an
     error.
  4. Otherwise return `{geom_id, num_points}`.

  The docstring states the file format (plain text, one `x y z` per line, model units) and that it
  is step 1 of the workflow.
- [X] T015 [US1] Implement `reset_fit_model()`, `clear_fit_model_vars()` and
  `clear_fit_model_targets()` in the Setup state section of `MCP/_fitmodel.py`. Each returns
  `{num_vars, num_targets}` from `GetNumFitModelVars`/`GetNumFitModelTargetPts` after the call.
- [X] T016 [US1] Implement `add_fit_model_vars(parm_ids: list[str])` (1–1000, all-or-nothing:
  `ValidParm` and duplicate pre-check, then `AddFitModelVar` each, rolling back with
  `DeleteFitModelVar` on an engine rejection; R9) and `list_fit_model_vars()` (`{num_vars, vars}`
  via `_list_vars`) in the Variables section of `MCP/_fitmodel.py`.
- [X] T017 [US1] Implement `add_fit_model_targets(targets: list[dict])` in the Targets section of
  `MCP/_fitmodel.py`. It is a thin wrapper over `_add_target_batch`. The docstring gives the entry
  schema `{x, y, z, geom_id, u?, w?, u_type?, w_type?}`, the defaults, the 10,000 cap, and the note
  that the search step (not this call) matches targets to the surface.
- [X] T018 [US1] Implement the following in the Solving section of `MCP/_fitmodel.py`:
  - `search_fit_model_target_uw()` and `refine_fit_model_target_uw()`: run the `_dangling`
    pre-check, call the engine, return `{num_targets}`
  - `update_fit_model_distance()`: 0 targets gives `{rms: 0.0, num_targets: 0}` with no engine
    call; otherwise `_dangling`, then `UpdateFitModelDistance`
  - `get_fit_model_distance()`: cached value
- [X] T019 [US1] Implement `optimize_fit_model()` in the Solving section of `MCP/_fitmodel.py`:
  - add a module-level `_INFO_MEANINGS` dict for codes 0–7 with the exact R12 texts
  - run `_dangling` first, then `rms_before = UpdateFitModelDistance()`, `info =
    OptimizeFitModel()`, `rms_after = GetFitModelDistance()`
  - return `{info, info_meaning, rms_before, rms_after, vars}`
  - the docstring warns: "One pass solves against frozen target-to-surface matches and can stop
    short when the model starts far from the scan. Prefer fit_model_to_convergence." (FR-018)
- [X] T020 [US1] Run `PY -m pytest UT/test_mcp_fitmodel.py -q`, then `copy_package` and
  `PY -m pytest RT -q -k "not convergence and not cloud_summary and not from_cloud and not fit_file"`.
  All US1 tests must pass.

**Checkpoint**: The MVP is complete. An agent can fit a model to a cloud with one-for-one tools.

---

## Phase 4: User Story 2 - Fit to convergence in one request (Priority: P2)

**Goal**: One tool call repeats search/refine/optimize until the fit error stops improving and
reports each pass (FR-011, R13).

**Independent Test**: `pod_case` from the far start (4.0/15.0). `fit_model_to_convergence()`
recovers 7.5/9.0 to within 0.1%, with `stop_reason == "converged"`. With `max_passes=1` it
returns `stop_reason == "pass_limit"`.

### Tests for User Story 2 ⚠️ Write first and confirm they fail

- [X] T021 [P] [US2] Add failing `TestFitToConvergence` unit tests to `UT/test_mcp_fitmodel.py`.
  Drive the engine with `side_effect` lists on `UpdateFitModelDistance`/`GetFitModelDistance`.
  - `converged` when `rms_after` hits 0
  - `converged` when the relative improvement is below `tolerance`
  - `no_improvement` when `rms_after` exceeds the previous value; the result is kept and
    `DeleteFitModelVar`/reset are not called
  - `pass_limit` with `max_passes=1`: exactly one `OptimizeFitModel` call
  - `error` when an engine error is pushed during pass 2: the history holds pass 1 plus
    `vsp_errors`
  - `refine=False` means no `RefineFitModelTargetUW` call
  - the dangling pre-check means no passes run
  - `max_passes` 0 or 101, or `tolerance <= 0`, is rejected
  - the `rms_history` entries are `{pass, rms_before, rms_after, info}`, and `rms_initial`,
    `rms_final` and `vars` are present
- [X] T022 [P] [US2] Add failing real-binding tests to `RT`:
  - `test_convergence_recovers_pod` (SC-001): import, add both vars, add targets from the sampled
    points, then `fit_model_to_convergence()`. Expect Length/FineRatio within 0.1% of 7.5/9.0,
    `stop_reason == "converged"`, `passes <= 10`, and `rms_final < 1e-6`.
  - `test_convergence_pass_limit`: `max_passes=1` gives `passes == 1` and
    `stop_reason == "pass_limit"`.
  - `test_convergence_fuselage_and_wing` (SC-006):
    1. build a FUSELAGE plus WING at their default positions
    2. sample each surface (for example 10×8 points each) as targets for its own component
    3. perturb fuselage `Length` (Design) and wing `Span` of `XSec_1` by +20%
    4. add both as variables and run the fit
    5. expect `rms_final <= 0.1 * rms_initial`

    If a chosen parm is inactive under the wing's default driver group, `OptimizeFitModel` reports
    "Inactive Parm". In that case choose an active parm and note it in the test.

### Implementation for User Story 2

- [X] T023 [US2] Implement `fit_model_to_convergence(max_passes: int = 10, tolerance: float = 1e-6, refine: bool = True)`
  in the Solving section of `MCP/_fitmodel.py`, exactly as the R13 / data-model "Loop states"
  diagram describes.
  - **Input checks**: `max_passes` must be 1–100 and `tolerance` > 0. Then run `_dangling`.
  - **Each pass**, inside one `_capture`: `SearchFitModelTargetUW`, then `RefineFitModelTargetUW`
    (if `refine`), then `rms_before = UpdateFitModelDistance()`, then `info = OptimizeFitModel()`,
    then `rms_after = GetFitModelDistance()`.
  - **Stop checks** after each pass, in this order: `error`, then `converged` (`rms_after == 0` or
    `0 <= rel_impr < tolerance`), then `no_improvement` (`rms_after > prev_rms`), then
    `pass_limit`.
  - **Return** `{passes, stop_reason, rms_history, rms_initial, rms_final, vars}`.
  - **Docstring** marks this as the recommended fitting tool and explains why several passes are
    needed.
- [X] T024 [US2] Run `PY -m pytest UT/test_mcp_fitmodel.py -q -k Convergence`, then `copy_package`
  and `PY -m pytest RT -q -k convergence`. All must pass. Record the pass count and timing of
  `test_convergence_recovers_pod` in the task notes (the plan target is 1 s or less).

  **Result**: 10/10 unit tests pass, 3/3 real-binding convergence tests pass.
  `test_convergence_recovers_pod` (SC-001): 5 passes, `rms_final` ≈ 1.1e-16, 0.31 s
  (well under the 1 s target). Length/FineRatio recovered to 7.5/9.0 within 0.1%.

**Checkpoint**: US1 and US2 both work. Agents get a correct fit in one call.

---

## Phase 5: User Story 3 - Choose targets from the cloud without moving every point (Priority: P3)

**Goal**: An agent can see a cloud's summary, page through its points within the response cap,
and turn every point inside a box into targets on the server, so no coordinates pass through the
agent (FR-002, FR-003, FR-012; R7, R8).

**Independent Test**: Import a 100,000-point cloud. The summary holds no coordinates, and
`get_point_cloud_points(count=5000)` returns at most 1,000. `add_fit_model_targets_from_cloud`
with a box and `stride=10` creates `ceil(in_box / 10)` targets and returns no coordinates.

### Tests for User Story 3 ⚠️ Write first and confirm they fail

- [X] T025 [P] [US3] Add failing unit tests to `UT/test_mcp_fitmodel.py`:
  - `TestCloudSummary`:
    - count, bbox and centroid are computed from mock vec3d points
    - a geom whose `GetGeomTypeName` is not `"PtCloud"` gives an error naming it
  - `TestCloudPoints`:
    - `count` is clamped to 1000
    - `next_start` advances, and is `None` at the end
    - `stride` works
    - a `start` outside `[0, total)` gives an error
  - `TestTargetsFromCloud`:
    - the box is inclusive on the boundary
    - `stride=2` keeps every 2nd match in cloud order
    - 0 matches gives an error with `bbox_min`/`bbox_max` in the message
    - more than 10,000 selected gives an error with `matched` and `selected`
    - `bbox_min > bbox_max` on any axis is rejected
    - the batch rollback path applies
    - the success result has `matched`, `count`, `first_index`, `last_index`, `num_targets`, and
      no point lists
- [X] T026 [P] [US3] Add failing real-binding tests to `RT`:
  - `test_cloud_summary_and_paging` (SC-004):
    1. write 100,000 random points in the unit cube to `tmp_path`, then import them
    2. summary `num_points == 100000`, `0 <= bbox <= 1`, and no point lists
    3. `get_point_cloud_points(count=5000)` gives `returned == 1000` and `next_start == 1000`
  - `test_targets_from_cloud_box_and_stride`:
    1. use the `pod_case` cloud
    2. compute the in-box count in the test from `fixture["points"]`
    3. `add_fit_model_targets_from_cloud(..., stride=10)` gives `count == ceil(in_box/10)`
    4. `GetFitModelTargetPt(first_index)` equals the first in-box point
  - `test_targets_from_cloud_empty_box`: error, and the target count is unchanged

### Implementation for User Story 3

- [X] T027 [US3] Implement the following in the Point cloud section of `MCP/_fitmodel.py`:
  - `_cloud_points(vsp, cloud_id)`: checks `GetGeomTypeName == "PtCloud"` and returns the list of
    `(x, y, z)` from `GetPtCloudPnts`
  - `get_point_cloud_summary(cloud_id)`: returns `{geom_id, num_points, bbox_min, bbox_max, centroid}`
    from one pass
  - `get_point_cloud_points(cloud_id, start=0, count=1000, stride=1)`: returns
    `{total, start, stride, returned, next_start, points}`, with `count` clamped to 1–1000
- [X] T028 [US3] Implement `add_fit_model_targets_from_cloud(cloud_id, geom_id, bbox_min, bbox_max, stride=1, u_type="FREE", w_type="FREE")`
  in the Targets section of `MCP/_fitmodel.py`:
  1. Validate the box and stride.
  2. Filter with `_cloud_points`, inclusive on every axis, then take every `stride`-th match.
  3. Check that the selection is between 1 and 10,000.
  4. Build specs and pass them to `_add_target_batch`.
  5. Return the batch result plus `matched`.

  The docstring explains that this selects existing cloud points and does no projection (R7).
- [X] T029 [US3] Run `PY -m pytest UT/test_mcp_fitmodel.py -q -k "Cloud"`, then `copy_package` and
  `PY -m pytest RT -q -k "cloud"`. All must pass.

**Checkpoint**: Agents can work from a raw cloud without transferring its coordinates.

---

## Phase 6: User Story 4 - Inspect, edit, save, and resume a fit setup (Priority: P4)

**Goal**: An agent can review and edit individual targets and variables, and save or load the setup
in the existing `.fit` format, with unresolved references reported (FR-007, FR-013; R14).

**Independent Test**: Configure 50 targets, update target 10, and confirm the others are unchanged.
Save, reset and load, and confirm every variable and target field round-trips. Append-load and
confirm the counts add up. Load into a fresh model and get `missing_parm_ids`.

### Tests for User Story 4 ⚠️ Write first and confirm they fail

- [X] T030 [P] [US4] Add failing unit tests to `UT/test_mcp_fitmodel.py`:
  - `TestTargetAccess`:
    - `get_fit_model_target` shape
    - out-of-range index gives an error naming the index and the valid range
    - `list_fit_model_targets` paging clamps `count` to 1000
  - `TestUpdateTarget`:
    - only `geom_id` given keeps the current point/u/w/types (read back through the mocked
      getters)
    - `u=2.0` is rejected before `SetFitModelTargetPt`
    - success returns the updated target
  - `TestDeleteTarget` and `TestDeleteVar`: return counts, and engine errors pass through
  - `TestSaveLoad`:
    - `SaveFitModel` returning `False` gives an error
    - `load_fit_model(f)` calls `LoadFitModel(f, True)`, and `append=True` calls
      `LoadFitModel(f, False)`
    - write a temporary `.fit` XML with two `<Variable><ParmID>` entries while
      `GetFitModelVarIDs` returns only one: the error lists the missing one in `missing_parm_ids`
    - a dangling target after load gives `dangling_target_indices`
    - an engine missing-file error gives `vsp_errors`
- [X] T031 [P] [US4] Add failing real-binding tests to `RT`:
  - `test_update_target_leaves_others` (50 targets, update index 10's geom and types)
  - `test_fit_file_round_trip`: `save_fit_model` to `tmp_path`, `reset_fit_model`,
    `load_fit_model`; variables and every target's point/geom/u/w/types match
  - `test_fit_file_append`: counts double
  - `test_fit_file_into_model_missing_parms`: save, `ClearVSPModel`, load. The result has an
    error with `missing_parm_ids` equal to the saved variable IDs
  - `test_delete_var_and_target`

### Implementation for User Story 4

- [X] T032 [US4] Implement `get_fit_model_target(index)`, `list_fit_model_targets(start=0, count=1000)`,
  `update_fit_model_target(index, x=None, y=None, z=None, geom_id=None, u=None, w=None, u_type=None, w_type=None)`
  and `delete_fit_model_target(index)` in the Targets section of `MCP/_fitmodel.py`:
  - **Update** reads the current values with `_describe_target`, merges in the given fields,
    validates with `_validate_target_spec`, and then calls `SetFitModelTargetPt`.
  - **Delete**: the docstring says that later indices shift down by one.
- [X] T033 [US4] Implement `delete_fit_model_var(parm_id)`, returning `{num_vars}`, in the Variables
  section of `MCP/_fitmodel.py`.
- [X] T034 [US4] Implement the following in the Persistence section of `MCP/_fitmodel.py` (R14):
  - `_fit_file_parm_ids(path) -> list[str]`: reads `Variable/ParmID` with `ET.parse`, and returns
    `[]` on a parse error
  - `save_fit_model(file_name)`: returns `{file_name, num_vars, num_targets}`
  - `load_fit_model(file_name, append=False)`:
    1. `LoadFitModel(file_name, not append)`
    2. `missing = [p for p in _fit_file_parm_ids(file_name) if p not in GetFitModelVarIDs()]`
    3. dangling targets via `_dangling`
    4. if either list is non-empty, return an error with `missing_parm_ids`,
       `dangling_target_indices`, `num_vars` and `num_targets`, whose message says the setup was
       loaded without them
- [X] T035 [US4] Run `PY -m pytest UT/test_mcp_fitmodel.py -q`, then `copy_package` and
  `PY -m pytest RT -q`. The full RT file must pass.

**Checkpoint**: All four stories are complete. The spec's 23 tools are in place.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Registration coverage, documentation, and end-to-end validation against the success
criteria.

- [X] T036 Update `UT/test_mcp_server.py`:
  - raise the threshold to `assertGreaterEqual(len(tool_names), 208)`
  - add a test that asserts all 23 contract tool names are registered: `import_point_cloud`,
    `get_point_cloud_summary`, `get_point_cloud_points`, `reset_fit_model`, `clear_fit_model_vars`,
    `clear_fit_model_targets`, `add_fit_model_vars`, `delete_fit_model_var`, `list_fit_model_vars`,
    `add_fit_model_targets`, `add_fit_model_targets_from_cloud`, `get_fit_model_target`,
    `list_fit_model_targets`, `update_fit_model_target`, `delete_fit_model_target`,
    `search_fit_model_target_uw`, `refine_fit_model_target_uw`, `update_fit_model_distance`,
    `get_fit_model_distance`, `optimize_fit_model`, `fit_model_to_convergence`, `save_fit_model`,
    `load_fit_model`
- [X] T037 [P] Review every tool docstring in `MCP/_fitmodel.py` against FR-018. Each must give
  its purpose, `Args:` with units (model units), where it fits in the contract's recommended order,
  and its limits (response caps, the 10,000 batch cap, the index shift on delete, the optimize
  warning). Fix any gaps.
- [X] T038 [P] Update `src/python_api/packages/openvsp/openvsp/index.rst`. In the MCP Server
  "The server exposes tools for:" list, add the bullets "Importing point clouds and inspecting them
  in bounded pages" and "Fitting model parameters to point cloud targets with Fit Model, including a
  fit-to-convergence tool".
- [X] T039 [P] Update `docs/FitModelAPI.md`. Under "Current status", add a short "MCP tools"
  paragraph: the functions are exposed as agent tools in `openvsp/mcp/_fitmodel.py`; the contract
  is at `specs/001-fitmodel-mcp-tools/contracts/mcp-tools.md`; and the engine gaps are listed in
  research R16.
- [X] T040 Measure performance against the plan's goals with a one-off script in the session
  scratchpad, not the repo:
  - a 1,000,000-point `.pts`: time `get_point_cloud_summary` and
    `add_fit_model_targets_from_cloud` with a box selecting ≤ 10,000
  - record both timings in research.md R7 (the goal is 2 s or less excluding import)
- [X] T041 Run the full validation from quickstart.md sections 1–3:
  - the unit suite
  - `copy_package`, then `RT`
  - `cd ~/build/projects/openvsp/vsp && ctest -R PyTest --output-on-failure`

  All must pass, with no regressions in the seven existing `test_FitModel_*.py` files or in the
  existing MCP tests.
- [ ] T042 Carry out quickstart.md section 4, the end-to-end agent run through
  `~/build/projects/openvsp/vsp/venv/bin/openvsp-mcp`. Confirm and record:
  - SC-002: 10 or fewer tool calls from import to save, not counting geometry building
  - the saved model reopens with the recovered values
  - no stdio protocol errors after a deliberately bad call (R2)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 first. T002, T003 and T004 can run in parallel. T005 needs T002.
- **Foundational (Phase 2)**: needs Phase 1. T006 can run in parallel with T007, since they are
  different files. T008 → T009 → T010 → T011 run in order (same file; T011 uses T008–T010).
  **Blocks all stories.**
- **US1 (Phase 3)**: needs Phase 2.
- **US2 (Phase 4)**: needs Phase 2. Its tests set up targets through the engine or `_add_target_batch`,
  so it does not need US1's tools. Its real-binding test calls `add_fit_model_targets` for
  convenience; if US2 is done before US1, use `vsp.AddFitModelTargetPt` directly.
- **US3 (Phase 5)**: needs Phase 2 (`_add_target_batch`). Independent of US1 and US2.
- **US4 (Phase 6)**: needs Phase 2. Independent of the other stories.
- **Polish (Phase 7)**: T036 needs all story phases. T037–T039 can run in parallel with each other
  (different files) once the stories are done. T040 → T041 → T042 last.

### Within Each User Story

1. Test tasks, `[P]` between the unit file and `RT` (different files). Run them and **confirm they
   fail**.
2. Implementation tasks in listed order (all edit `MCP/_fitmodel.py`, so none are `[P]`).
3. The checkpoint run task.

### Parallel Opportunities

- Phase 1: T002, T003, T004.
- Phase 2: T006 alongside T007.
- Each story: its unit-test task alongside its `RT` task (T012/T013, T021/T022, T025/T026, T030/T031).
- After Phase 2, different stories can be developed at the same time only if the edits to
  `MCP/_fitmodel.py` and `UT/test_mcp_fitmodel.py` are coordinated. Each story keeps to its own
  banner section and test classes to keep merges trivial.
- Phase 7: T037, T038, T039.

---

## Parallel Example: User Story 1

```bash
# Write both US1 test sets together (different files), then confirm both fail:
Task: "T012 [US1] unit tests in src/python_api/packages/openvsp/openvsp/tests/test_mcp_fitmodel.py"
Task: "T013 [US1] real-binding tests in src/test/py/tests/test_FitModel_MCP.py"

# Then implement in order (same file):
T014 import_point_cloud → T015 setup state → T016 variables → T017 targets → T018 solving → T019 optimize
```

## Parallel Example: Setup

```bash
Task: "T002 Create src/python_api/packages/openvsp/openvsp/mcp/_fitmodel.py skeleton"
Task: "T003 Create src/python_api/packages/openvsp/openvsp/tests/test_mcp_fitmodel.py skeleton"
Task: "T004 Create src/test/py/tests/test_FitModel_MCP.py skeleton and fixtures"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup, then Phase 2 Foundational (error capture, validation, batch).
2. Phase 3 US1. **Stop and validate** with T020: an agent can fit a model with one-for-one tools.
3. Commit, following the constitution's commit conventions (imperative subject, body explaining
   why, no attribution trailers).

### Incremental Delivery

1. MVP (US1), then commit.
2. US2 `fit_model_to_convergence`, then commit. Highest value after the MVP, since it makes fits
   correct by default.
3. US3 cloud summary, paging and region selection, then commit.
4. US4 target editing and `.fit` persistence, then commit.
5. Polish (registration test, docs, measurements, end-to-end), then commit.

### Out of scope (do not do in this feature)

The following are recorded in research R16:
- C++ fixes for the engine gaps
- the server-wide `SilenceErrors()` in `MCP/__init__.py:main()`
- the `"NONE"` handling in the existing `import_file`

Propose them as separate changes after this feature lands.

---

## Notes

- `[P]` means different files and no dependency on an incomplete task. Two tasks editing
  `MCP/_fitmodel.py` are never `[P]`.
- The `ErrorMgr` queue is process-global. Real-binding tests compare error counts with
  `err_baseline` and never assert zero (FitModelAPI_Handover.md gotcha 1).
- `GetFitModelVarIDs()` returns a tuple, so wrap it in `list()` before comparing.
- Remember the manual sync (see Path Conventions) before every `RT` run, or the tests will
  exercise stale code.
