# FitModel API – Agent Handover (next slices)

## Current status (as of 2026-09-03)

Slices completed and green:
- Slice 1: state reset/clear API
- Slice 2: variable lifecycle API
- Slice 3: target point lifecycle API (add/delete/get/set + FIT_TARGET_TYPE enum)
- Slice 4: target UW search/refine API
- Slice 5: distance metric API

Pytests passing:
- `src/test/py/tests/test_FitModel_State.py`
- `src/test/py/tests/test_FitModel_Vars.py`
- `src/test/py/tests/test_FitModel_TargetPts.py`
- `src/test/py/tests/test_FitModel_TargetUW.py`
- `src/test/py/tests/test_FitModel_Distance.py`

## How to build + run tests (important)

This repo’s python tests must be run using the **build-tree venv**, not system python.

- Source tree: `/home/luan/src/OpenVSP`
- Build tree: `/home/luan/build/openvsp/vsp`
- Pytest: `/home/luan/build/openvsp/vsp/venv/bin/pytest`

From the source root:
- Run a single test:
  - `/home/luan/build/openvsp/vsp/venv/bin/pytest src/test/py/tests/test_FitModel_TargetPts.py -q`
- Run all FitModel tests:
  - `/home/luan/build/openvsp/vsp/venv/bin/pytest src/test/py/tests/test_FitModel_State.py src/test/py/tests/test_FitModel_Vars.py src/test/py/tests/test_FitModel_TargetPts.py src/test/py/tests/test_FitModel_TargetUW.py src/test/py/tests/test_FitModel_Distance.py -q`

Rebuild (generates fresh python bindings into the venv editable package):
- Build from: `/home/luan/build/openvsp/vsp`

## Files changed so far (FitModel API work)

Public API:
- `src/geom_api/APIDefines.h`
  - Added `FIT_TARGET_TYPE { FIT_FIXED=0, FIT_FREE=1 }`
- `src/geom_api/VSP_Geom_API.h`
  - Added FitModel state/vars/targets declarations
- `src/geom_api/VSP_Geom_API.cpp`
  - Implemented:
    - Slice 1: `ResetFitModel`, `ClearFitModelVars`, `ClearFitModelTargetPts`
    - Slice 2: `AddFitModelVar`, `DeleteFitModelVar`, `GetNumFitModelVars`, `GetFitModelVarIDs`
    - Slice 3: `AddFitModelTargetPt`, `DeleteFitModelTargetPt`, `GetFitModelTargetPt`, `GetFitModelTargetGeomID`, `GetFitModelTargetUW`, `GetFitModelTargetUType`, `GetFitModelTargetWType`, `SetFitModelTargetPt`
    - Slice 4: `SearchFitModelTargetUW`, `RefineFitModelTargetUW`
    - Slice 5: `UpdateFitModelDistance`, `GetFitModelDistance`
  - Helper validation functions were added near `FindGeomForOp`.

Core manager:
- `src/geom_core/FitModelMgr.h/.cpp`
  - Added index-based helpers:
    - `bool DelTargetPt( int index );`
    - `bool SetTargetPt( int index, ... );`
  - Slice 5 safety fixes:
    - `FitModelMgrSingleton::UpdateDist()` empty-target guard (prevents div-by-zero)
    - reset cached `m_DistMetric` on `Wype()`

AngelScript bindings:
- `src/geom_core/ScriptMgr.h/.cpp`
  - Registered:
    - `FIT_TARGET_TYPE` enum values
    - all FitModel slice 1-5 functions
    - `vec2d` AngelScript value type (needed because target UW getter returns `vec2d`)

Tests:
- `src/test/py/tests/test_FitModel_Vars.py`
- `src/test/py/tests/test_FitModel_TargetPts.py`
- `src/test/py/tests/test_FitModel_TargetUW.py`
- `src/test/py/tests/test_FitModel_Distance.py`

## Known nuances / gotchas

1) `ErrorMgrSingleton` is process-global
- Some tests intentionally generate errors and leave them in the global error stack.
- `test_FitModel_TargetPts.py::testFitModel_TargetPtLifecycle` uses a baseline error-count check (no *new* errors) instead of asserting 0.

2) Python wrappers for `array<string>`
- `GetFitModelVarIDs()` returns a sequence that is not always a python `list`; tests use `list(vsp.GetFitModelVarIDs())`.

3) Target creation intentionally does NOT auto-search UW
- Per `docs/FitModelAPI.md`, `AddFitModelTargetPt` only stores pt + initial UW/types; it does not call `SearchUW`.

4) Optional GUI visualization requires graphics-enabled build
- The FitModel API is designed for headless use first.
- If the user wants live visualization while Python drives the API, OpenVSP must be built with graphics enabled (`VSP_NO_GRAPHICS=OFF`, FLTK available).
- Use facade mode with:
  - `openvsp_config.LOAD_GRAPHICS = True`
  - `openvsp_config.LOAD_FACADE = True`
- This should show model state changes in a facade-owned GUI while Python continues running.
- Do not assume per-iteration optimize animation; current solver path is blocking unless later instrumented.

## What to do next (Slice 6)

### Slice 6 APIs to implement
From `docs/FitModelAPI.md`:
- `OptimizeFitModel()`

Expected behavior:
- wrapper should call `FitModelMgr.Optimize()`
- add API-level precondition guards **before** allocation/`lmder1`:
  - `GetNumFitModelTargetPts() > 0`
  - at least 1 optimization DOF (fit var or free target U/W)
  - residual dimension adequate: `3 * target_count >= opt_var_count`
- return `lmder1` info code on success
- follow ErrorMgr patterns: `ErrorMgr.NoError()` on success, meaningful error code on invalid input.

Suggested tests to add:
- Build simple deterministic case with 1 geom (POD works):
  - create target point from known surface coordinate via `CompPnt01` + offset
  - set target UW fixed to keep problem stable
  - add 1 fit variable (e.g. POD length)
  - compute `before = UpdateFitModelDistance()`
  - `info = OptimizeFitModel()`
  - compute `after = UpdateFitModelDistance()`
  - assert `after < before` (allow tolerance)
- Add negative tests for precondition guards.
- Optional manual smoke check for GUI visualization path after graphics-enabled rebuild:
  - load with `LOAD_GRAPHICS = True` and `LOAD_FACADE = True`
  - `InitGUI()` / `StartGUI()`
  - run FitModel setup calls and confirm GUI reflects state changes

### Slice 7
`SaveFitModel` / `LoadFitModel` wrappers.

### Slice 8
Binding smoke tests (AngelScript script calling new APIs).

## Quick verification commands

After implementing new slices:
1) rebuild:
- `cd /home/luan/build/openvsp/vsp && cmake --build . -- -j2`

2) run FitModel tests:
- `/home/luan/build/openvsp/vsp/venv/bin/pytest src/test/py/tests/test_FitModel_State.py src/test/py/tests/test_FitModel_Vars.py src/test/py/tests/test_FitModel_TargetPts.py src/test/py/tests/test_FitModel_TargetUW.py src/test/py/tests/test_FitModel_Distance.py -q`

(Plus any new tests you add for slices 6+.)
