# Research: Fit Model Tools for Agents

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-09-10

All findings below were measured against the real bindings in the build-tree venv
(`~/build/projects/openvsp/vsp/venv`, OpenVSP 3.51.3, `mcp` 1.29.1, numpy 1.26.4, Python 3.12)
unless marked otherwise. No NEEDS CLARIFICATION items remained after this phase.

## R1. Where the tools live

- **Decision**: One new module, `openvsp/mcp/_fitmodel.py`, registered in `openvsp/mcp/__init__.py`
  next to the existing eight tool modules. It holds both point-cloud and Fit Model tools, split into
  `# ====` banner sections.
- **Rationale**: Existing modules are organised by domain (`_geometry`, `_fea`, `_xsec`, …). The
  point-cloud tools only exist to feed Fit Model, and region selection (FR-012) spans both.
  Keeping them together keeps the fork addition self-contained (Principle V).
- **Alternatives considered**: A separate `_pointcloud.py` module. Rejected because it would split one
  workflow across two modules and double the registration edits for little gain. Adding the tools
  to `_io.py` was rejected because it already runs to 670 lines and covers file formats, not fitting.

## R2. Reporting engine errors (FR-015)

- **Finding**: Fit Model calls never raise. They return a sentinel (`False`, `-1`, `0`, `""`) and push
  `(code, message)` onto the process-global `ErrorMgrSingleton`, for example
  `(22, "AddFitModelVar::Parm already added …")`. None of the existing MCP tools read that queue.
- **Finding**: `ErrorMgr` also `printf`s every error to **file descriptor 1** (`m_PrintErrors = true`
  by default, `APIErrorMgr.cpp:115`). On the stdio transport, stdout carries the JSON-RPC stream, so
  any engine error corrupts the protocol. `SilenceErrors()` stops the printing, and errors still
  queue (verified).
- **Decision**: A private helper in `_fitmodel.py` wraps every engine call sequence:
  1. Call `SilenceErrors()`. This is idempotent and cheap.
  2. Record `GetNumTotalErrors()` as the baseline.
  3. Run the calls.
  4. Pop exactly `(count − baseline)` errors with `PopLastError()`. Those are this call's errors.
     Errors left over from earlier calls stay on the queue and are never attributed to this call.
  5. If any were popped, return `{"error": "<joined messages>", "vsp_errors": [{code, message}, …]}`.
- **Rationale**: Uses the counting approach the codebase already relies on (see
  `FitModelAPI_Handover.md` gotcha 1 and `gen_unit_test.py`), and it's the only way to satisfy
  FR-015 without C++ changes.
- **Alternatives considered**: Draining the whole queue before every call. Rejected because it
  discards other tools' errors that an agent or test may still want to read.
  Silencing only in `main()`. Not enough on its own, since tests and examples import tools without
  `main()`. See R16 for the server-wide follow-up.

## R3. Result shape

- **Decision**: Every new tool returns `dict[str, Any]`, with `{"error": str, …}` on failure and
  plain JSON-safe data (floats, ints, strings, lists) on success. vec3d values are returned as
  `[x, y, z]` lists and vec2d values as `[u, w]`.
- **Rationale**: Matches the existing dict-returning tools (`get_vsp_version`, `_surface.py`) and
  Principle III ("return an error value that matches the tool's existing return type"). A dict lets
  structured detail such as `vsp_errors` or `invalid` entries sit alongside the message.
- **Alternatives considered**: `str` results like `"Error: …"`, as in `_io.py`. Rejected because
  optimize and fit results are structured, and agents parse dicts reliably.

## R4. Target fixed/free representation

- **Decision**: Tools accept and return `"FREE"` / `"FIXED"` (case-insensitive on input), mapped to
  `vsp.FIT_FREE` (1) / `vsp.FIT_FIXED` (0).
- **Rationale**: Agents misuse raw integer enums. The existing `import_file` tool already takes
  constant names as strings.

## R5. u/w range validation

- **Finding**: `AddFitModelTargetPt(pt, geom, u=1.5)` and `SetFitModelTargetPt(…, u=2.0, w=-1.0)`
  are both accepted without error. The engine checks only that values are finite and that the type
  is valid.
- **Decision**: The tool layer rejects u or w outside `[0, 1]` before calling the engine.
- **Rationale**: FR-006 and the spec's edge cases require it, and `docs/FitModelAPI.md` already
  recommended rejection. This is input validation, not fitting logic, so it complies with
  Principle II.
- **Follow-up (out of scope)**: Move the range check into `AddFitModelTargetPt`/`SetFitModelTargetPt`
  in C++ so every binding gets it.

## R6. All-or-nothing target batches (FR-006, FR-012)

- **Decision**: The batch is applied in two phases.
  1. **Pre-validate in Python** everything that is cheap and has a single right answer: required
     keys, finite numbers, u/w range, fixed/free strings, target geom exists in `FindGeoms()`, and
     the batch is within the cap.
  2. **Add through the engine** one target at a time, capturing any rejection per entry (for
     example an unsupported component type). If any entry fails, delete every target this call
     added, highest index first, so the setup is unchanged. Then return all invalid entries by
     position.
- **Rationale**: The engine is the authority on which component types are fittable
  (`IsSupportedFitTargetGeom`). Copying its exclusion list into Python would duplicate logic that
  can drift (Principle II). Rolling back keeps the batch atomic without that copy.
- **Alternatives considered**: Copying the exclusion list (mesh, human, point cloud, wire, blank,
  hinge, n-gon) into Python was rejected for the drift risk above. Stopping at the first engine
  failure was rejected because the spec requires *every* invalid entry to be reported.
- **Cap**: 10,000 targets per request, for both explicit and region-selected batches. The response
  returns `first_index`/`last_index`/`count`. Indices are contiguous and follow input order.

## R7. Region selection from a cloud (FR-012)

- **Decision**: Read the cloud once with `GetPtCloudPnts(cloud_id)`, keep points inside an
  inclusive axis-aligned box, keep every `stride`-th match in cloud order, then feed the result to
  the R6 batch path with the given geom and fixed/free types. Plain Python, no numpy.
- **Measured**: For a 200,000-point cloud, `ImportFile` took 0.50 s, `GetPtCloudPnts` 0.08 s (it
  returns a tuple of vec3d), and reading `.x()` on every point 0.04 s. Filtering 1,000,000 points
  should take about 1 s.
- **Measured (T040, 1,000,000-point cloud, uniform random in the unit cube)**: import (not counted
  against the goal) 3.05 s; `get_point_cloud_summary` 1.75 s; `add_fit_model_targets_from_cloud`
  with a box selecting 7,943 points (under the 10,000 cap), stride 1, 1.76 s. Both under the 2 s
  goal.
- **Rationale**: This only filters input points, with no surface evaluation, projection or
  fitting. It is the "choosing which cloud points become targets" carve-out in FR-017 and complies
  with Principle II. numpy would be faster but adds nothing at this scale.
- **Errors**: No matches, or none left after the stride, is an error that names the box. More
  matches than the cap is an error that reports the matched count (spec edge cases).
- **Alternatives considered**: `ProjectPtCloudPts`. It projects points onto a surface, which is a
  different operation, and it modifies the cloud.

## R8. Point cloud access without flooding the agent (FR-001–FR-003)

- **Decision**:
  - `import_point_cloud` returns `{geom_id, num_points}`.
  - `get_point_cloud_summary` computes the count, bounding box and centroid from one pass over the
    points.
  - `get_point_cloud_points(start, count, stride)` returns at most 1,000 points, with `total` and
    `next_start` (`null` when done).
- **Finding**: `ImportFile` on a missing file returns `"NONE"`, reports **no** error, and leaves no
  component behind. `GetPtCloudPnts` on a geom that isn't a cloud returns an empty tuple plus error
  `(2, "… is not a point cloud")`.
- **Decision**: The import tool treats `"NONE"` or an empty cloud as an error naming the file. If
  the cloud is empty it deletes the component it created.

## R9. Fit variables and their owners (FR-005)

- **Finding**: `GetParmContainer` returns the Geom ID for Geom parms but the **XSec ID** for XSec
  parms (e.g. wing section `Span`), and `GetGeomName(xsec_id)` then reports an error.
  `GetContainerName` returns `"XSec"`, which says nothing about the owner. Scanning
  `GetGeomParmIDs(g)` over `FindGeoms()` does find the owning wing.
- **Finding**: `GetFitModelVarIDs()` returns a tuple, and variable IDs survive component deletion as
  orphans. `ValidParm(id)` detects this without pushing an error.
- **Decision**:
  - `list_fit_model_vars` builds a parm→geom map once per call by scanning `GetGeomParmIDs`.
  - Each entry reports `parm_id, name, group, geom_id, geom_name, value, valid`.
  - Orphaned variables are listed with `valid: false` and no value.
- **Decision**: `add_fit_model_vars(parm_ids)` takes a list, to meet the SC-002 call budget. It is
  all-or-nothing: `ValidParm` and duplicate checks run first, then the engine adds each one, and any
  engine rejection rolls back the ones added.

## R10. Dangling references before solving

- **Finding**: After `DeleteGeom` on a target's component, `SearchFitModelTargetUW` silently removes
  the targets. The later calls then report "No target points", and nothing says which targets went
  or why.
- **Decision**: `search_…`, `refine_…`, `update_fit_model_distance`, `optimize_fit_model` and
  `fit_model_to_convergence` first check that every target's geom is in `FindGeoms()` and every
  variable passes `ValidParm`. If any fail, they return an error listing the dangling target
  indices and orphaned variable IDs, **without** calling the engine.
- **Rationale**: Meets the spec edge case ("reports the dangling targets by index instead of failing
  silently"). The pre-check is read-only validation.

## R11. Distance with zero targets

- **Finding**: `UpdateFitModelDistance()` with no targets returns `0.0` **and** pushes
  `(22, "No target points")`. So FR-015 (surface every error) conflicts with the spec edge case
  ("returns 0 rather than failing").
- **Decision**: With zero targets, `update_fit_model_distance` returns `{rms: 0.0, num_targets: 0}`
  without calling the engine. `get_fit_model_distance` reads the cached value, which pushes no
  error. That satisfies both requirements.

## R12. Single optimize pass (FR-010)

- **Decision**: `optimize_fit_model` runs `UpdateFitModelDistance` (the "before" value), then
  `OptimizeFitModel`, then `GetFitModelDistance` (the "after" value). It returns `info`, its meaning,
  `rms_before`, `rms_after`, and the R9 variable listing. The description warns that one pass
  solves against frozen correspondence (FR-018).
- **Info meanings** (MINPACK `lmder1`, called at `FitModelMgr.cpp:1004`). Engine guards return 0.

| info | meaning |
|------|---------|
| 0 | Improper input, or rejected by an engine precondition (see `vsp_errors`) |
| 1 | Converged: relative reduction in the sum of squares is within tolerance |
| 2 | Converged: relative change in the parameters is within tolerance |
| 3 | Converged: both 1 and 2 |
| 4 | Residuals are orthogonal to the Jacobian columns (stationary point) |
| 5 | Stopped: function evaluation limit reached |
| 6 | Stopped: tolerance too small, no further reduction in the sum of squares possible |
| 7 | Stopped: tolerance too small, no further improvement in the parameters possible |

## R13. Converged fit (FR-011)

- **Measured**: POD, with truth `Length=7.5, FineRatio=9.0`, starting from `4.0/15.0`, 72
  surface-sampled targets, all u/w free:

| pass | rms_before | rms_after | info |
|------|------------|-----------|------|
| 1 | 1.56495 | 0.13610 | 2 |
| 2 | 0.05021 | 0.00000 | 2 |
| 3 | 0.00000 | 0.00000 | 2 |

  Recovered `7.5000 / 9.0000` exactly in 0.29 s total. Pass 1 alone stops short, which confirms the
  need for the loop.
- **Decision**: Each pass runs `SearchFitModelTargetUW` → (`RefineFitModelTargetUW` if
  `refine=True`, the default) → `rms_before = UpdateFitModelDistance` → `OptimizeFitModel` →
  `rms_after = GetFitModelDistance`. The loop stops when the first of these applies:
  - `converged`: `rms_after == 0`, or `0 ≤ (prev_rms − rms_after) / prev_rms < tolerance`, where
    `prev_rms` is the previous pass's `rms_after` (or pass 1's `rms_before`).
  - `no_improvement`: `rms_after > prev_rms`. The engine's result is kept and reported, not reverted.
  - `pass_limit`: `max_passes` reached (default 10).
  - `error`: the engine reports an error during a pass. Partial history is included.

  Defaults are `tolerance = 1e-6` and `max_passes = 10`, with `max_passes` limited to 1–100.
- **Rationale**: This is the same loop that recovered the exact answer in the probe. It only
  sequences existing engine calls, so it complies with Principle II.

## R14. Loading a fit setup (FR-013)

- **Finding**: `LoadFitModel` into a model that no longer has the saved parms returns `0` (success),
  **silently drops** the variables, and keeps targets whose `MatchGeom` no longer exists. A missing
  file gives `(7, "Can't Read File …")`. libxml2 also writes an `I/O warning` to stderr, which is
  harmless because stderr isn't the protocol channel.
- **Decision**: `load_fit_model(file_name, append=False)` calls `LoadFitModel(file, not append)`.
  It then reports unresolved references:
  - Missing variables are found by reading `Variable/ParmID` from the `.fit` XML with
    `xml.etree.ElementTree` and diffing against `GetFitModelVarIDs()`.
  - Dangling targets are found with the R10 check.
  - If anything is unresolved, the result is `{"error": …, "missing_parm_ids": […],
    "dangling_target_indices": […], "num_vars", "num_targets"}`, and the message states that the
    setup was loaded without them.
- **Rationale**: The spec requires each unresolved reference to be reported. Reading IDs from a
  simple XML file is reporting, not re-implementing the loader.
- **Alternatives considered**: Fixing `FitModelMgr::Load` in C++ to report unknown parms. This is
  the better long-term fix and is recorded as a follow-up. It is out of scope because the spec
  treats the C++ API as complete.
- **Format** (verified): `<Vsp_FitModel><Version>1</Version><TargetPt>…<MatchGeom>…</MatchGeom>
  …</TargetPt><Variable><ParmID>…</ParmID></Variable></Vsp_FitModel>`.

## R15. Testing strategy (Principle IV)

- **Decision**: Two layers, both written before the code (test-first):
  1. **Unit** tests: `openvsp/tests/test_mcp_fitmodel.py`, using the fake-`vsp` harness.
     `_make_fake_vsp()` gains Fit Model return values and a small **stateful** fake `ErrorMgr`
     queue, so error capture, rollback and stop reasons can be tested without `_vsp`.
     `_load_full_server` adds `_fitmodel` to its list, and `test_mcp_server.py` checks that the new
     tools are registered.
  2. **Real-binding** tests: `src/test/py/tests/test_FitModel_MCP.py`, run by the existing `PyTest`
     CTest target. They call the tool functions directly against the compiled bindings, covering
     the SC-001 POD recovery, the SC-006 fuselage+wing fit, region selection, save/load round trip,
     and the probe-found gaps (R5, R8, R10, R11, R14).
- **Rationale**: Follows the constitution's test locations, and the ErrorMgr "compare counts" rule
  from the handover doc.

## R16. Engine gaps recorded as follow-ups (not in this feature)

| Gap | Where | Handled here by |
|-----|-------|-----------------|
| u/w outside [0, 1] accepted | `AddFitModelTargetPt`, `SetFitModelTargetPt` | R5 tool-side check |
| Unknown parms silently dropped on load | `FitModelMgr::Load` | R14 post-load diff |
| Targets on deleted geoms silently removed by search | `FitModelMgr::SearchTargetUW` | R10 pre-check |
| Errors `printf` to stdout, corrupting the stdio transport | `APIErrorMgr.cpp:115` | R2 `SilenceErrors()` on first Fit Model tool use. **A server-wide call in `main()` is recommended so the other 185 tools are covered too.** |
| `import_file` returns `"NONE"` as success | `_io.py` | R8 for the new tool only |
