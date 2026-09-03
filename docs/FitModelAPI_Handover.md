# FitModel API – Agent Handover (next slices)

## Current status (as of 2026-09-03)

Slices completed and green:
- Slice 1: state reset/clear API
- Slice 2: variable lifecycle API
- Slice 3: target point lifecycle API (add/delete/get/set + FIT_TARGET_TYPE enum)

Pytests passing:
- `src/test/py/tests/test_FitModel_State.py`
- `src/test/py/tests/test_FitModel_Vars.py`
- `src/test/py/tests/test_FitModel_TargetPts.py`

## How to build + run tests (important)

This repo’s python tests must be run using the **build-tree venv**, not system python.

- Source tree: `/home/luan/src/OpenVSP`
- Build tree: `/home/luan/build/openvsp/vsp`
- Pytest: `/home/luan/build/openvsp/vsp/venv/bin/pytest`

From the source root:
- Run a single test:
  - `/home/luan/build/openvsp/vsp/venv/bin/pytest src/test/py/tests/test_FitModel_TargetPts.py -q`
- Run all FitModel tests:
  - `/home/luan/build/openvsp/vsp/venv/bin/pytest src/test/py/tests/test_FitModel_State.py src/test/py/tests/test_FitModel_Vars.py src/test/py/tests/test_FitModel_TargetPts.py -q`

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
  - Helper validation functions were added near `FindGeomForOp`.

Core manager:
- `src/geom_core/FitModelMgr.h/.cpp`
  - Added index-based helpers:
    - `bool DelTargetPt( int index );`
    - `bool SetTargetPt( int index, ... );`

AngelScript bindings:
- `src/geom_core/ScriptMgr.h/.cpp`
  - Registered:
    - `FIT_TARGET_TYPE` enum values
    - all FitModel slice 1/2/3 functions
    - `vec2d` AngelScript value type (needed because target UW getter returns `vec2d`)

Tests:
- `src/test/py/tests/test_FitModel_Vars.py`
- `src/test/py/tests/test_FitModel_TargetPts.py`

## Known nuances / gotchas

1) `ErrorMgrSingleton` is process-global
- Some tests intentionally generate errors and leave them in the global error stack.
- `test_FitModel_TargetPts.py::testFitModel_TargetPtLifecycle` uses a baseline error-count check (no *new* errors) instead of asserting 0.

2) Python wrappers for `array<string>`
- `GetFitModelVarIDs()` returns a sequence that is not always a python `list`; tests use `list(vsp.GetFitModelVarIDs())`.

3) Target creation intentionally does NOT auto-search UW
- Per `docs/FitModelAPI.md`, `AddFitModelTargetPt` only stores pt + initial UW/types; it does not call `SearchUW`.

## What to do next (Slice 4)

### Slice 4 APIs to implement
From `docs/FitModelAPI.md`:
- `SearchFitModelTargetUW()`
- `RefineFitModelTargetUW()`

Expected behavior:
- wrappers should call:
  - `FitModelMgr.SearchTargetUW()`
  - `FitModelMgr.RefineTargetUW()`
- should follow ErrorMgr patterns: validate preconditions, then `ErrorMgr.NoError()` on success.

Suggested tests to add:
- Create a POD (or other supported geom)
- Add at least 1 target point with arbitrary initial UW
- Call `SearchFitModelTargetUW()`
  - Assert no errors
  - Optionally assert the stored UW changed (only if deterministic enough)
- Call `RefineFitModelTargetUW()`
  - Assert no errors

(If UW changes are not deterministic/reliable across versions, just assert it runs, and maybe assert UW remains finite.)

### Slice 5+
Slice 5: `UpdateFitModelDistance` + `GetFitModelDistance`
- Add empty-target guard in manager (`UpdateDist` division by zero) per proposal.

Slice 6: `OptimizeFitModel`
- Needs dimension/precondition guards before allocation + `lmder1` call.
- Add a smoke test that distance decreases.

Slice 7: save/load wrappers
- Decide default `clear_existing=true` behavior.

Slice 8: binding smoke tests
- Minimal AngelScript script that calls new APIs.

## Quick verification commands

After implementing new slices:
1) rebuild:
- `cd /home/luan/build/openvsp/vsp && cmake --build . -- -j2`

2) run FitModel tests:
- `/home/luan/build/openvsp/vsp/venv/bin/pytest src/test/py/tests/test_FitModel_State.py src/test/py/tests/test_FitModel_Vars.py src/test/py/tests/test_FitModel_TargetPts.py -q`

(Plus any new tests you add for slices 4+.)
