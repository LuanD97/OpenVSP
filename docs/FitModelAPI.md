# Fit Model API Proposal

## Purpose

Expose `FitModelMgr` through OpenVSP public C++, AngelScript, and generated Python APIs so point-cloud-to-parametric-geometry fitting can run headlessly.

See also:

- `docs/FitModelMGR.md` for how the existing optimizer works internally
- `docs/PointCloudSegmentationPlan.md` for the recommended pre-fit point-cloud workflow

Current Fit Model implementation is functional but mostly GUI-driven:

- `src/geom_core/FitModelMgr.h`
- `src/geom_core/FitModelMgr.cpp`
- `src/gui_and_draw/FitModelScreen.cpp`

Point-cloud access is already public through `ImportFile(..., IMPORT_PTS, ...)`, `GetPtCloudPnts`, `CreatePtCloudGeom`, `CreateConvexHull`, and `ProjectPtCloudPts`. Missing layer is direct creation of fit targets, fit-variable management, and optimizer execution.

## Design Goals

1. Support headless fitting without GUI selection state.
2. Accept arbitrary target coordinates, including externally segmented or synthesized landmarks.
3. Preserve existing Fit Model behavior and `.fit` format.
4. Follow existing `VSP_Geom_API` validation and `ErrorMgr` conventions.
5. Keep first API small while allowing future target weights, robust losses, and solver controls.
6. Expose identical capability through C++, AngelScript, and Python bindings.
7. Implement the feature using test-driven development so API behavior is locked down before wrapper and binding work lands.

## Development Process Requirement

This feature should be implemented with test-driven development.

Recommended rule:

1. write or extend failing tests for one API slice
2. implement the smallest code change needed to pass
3. refactor only after tests are green
4. then move to the next API slice

Suggested slice order for TDD (live status):

- [x] 1) state reset and clear operations
- [x] 2) variable add/delete/get APIs
- [x] 3) target add/delete/get/set APIs
- [x] 4) `SearchFitModelTargetUW` and `RefineFitModelTargetUW`
- [x] 5) `UpdateFitModelDistance` and `GetFitModelDistance`
- [ ] 6) `OptimizeFitModel`
- [ ] 7) save/load wrappers
- [ ] 8) AngelScript/Python binding smoke tests

## Non-Goals for Initial API

- Exposing point visibility, point picking, or GUI selection operations.
- Replacing `cminpack` or changing Fit Model optimization math.
- Automatically segmenting aircraft point clouds inside OpenVSP.
- Supporting target surfaces other than surface index zero. Current `TargetPt` implementation uses `GetSurfPtr(0)`.
- Adding target weights or robust loss functions in first patch.

## Proposed Public API

### Target type enum

Add public enum values in `src/geom_api/APIDefines.h`:

```cpp
enum FIT_TARGET_TYPE
{
    FIT_FIXED = 0,
    FIT_FREE = 1
};
```

Values intentionally match `TargetPt::FIXED` and `TargetPt::FREE`.

### State management

```cpp
extern void ResetFitModel();
extern void ClearFitModelVars();
extern void ClearFitModelTargetPts();
```

Behavior:

- `ResetFitModel()` calls `FitModelMgr.Renew()`.
- Clear operations only clear specified collection.
- All successful calls finish with `ErrorMgr.NoError()`.

### Fit variables

```cpp
extern bool AddFitModelVar( const std::string & parm_id );
extern void DeleteFitModelVar( const std::string & parm_id );
extern int GetNumFitModelVars();
extern std::vector<std::string> GetFitModelVarIDs();
```

Behavior:

- `AddFitModelVar` validates parameter ID through `ParmMgr.FindParm`.
- Duplicate parameter IDs return `false` and report an API error.
- `DeleteFitModelVar` validates membership before deletion.
- Getter order matches `FitModelMgr.GetVarVec()`, currently sorted by parameter name.

### Target points

Minimal useful creation API:

```cpp
extern int AddFitModelTargetPt(
    const vec3d & target_pt,
    const std::string & target_geom_id,
    double u = 0.5,
    int u_type = FIT_FREE,
    double w = 0.5,
    int w_type = FIT_FREE );
```

Return target index on success, `-1` on failure.

Additional management and inspection:

```cpp
extern void DeleteFitModelTargetPt( int target_index );
extern int GetNumFitModelTargetPts();
extern vec3d GetFitModelTargetPt( int target_index );
extern std::string GetFitModelTargetGeomID( int target_index );
extern vec2d GetFitModelTargetUW( int target_index );
extern int GetFitModelTargetUType( int target_index );
extern int GetFitModelTargetWType( int target_index );

extern void SetFitModelTargetPt(
    int target_index,
    const vec3d & target_pt,
    const std::string & target_geom_id,
    double u,
    int u_type,
    double w,
    int w_type );
```

Validation:

- Target geometry ID must resolve to a `Geom`.
- Reject unsupported target types using same exclusions as `FitModelScreen`: mesh, human, point cloud, wire frame, blank, hinge, and NGon geometry.
- `u_type` and `w_type` must be `FIT_FIXED` or `FIT_FREE`.
- Initial `u` and `w` must be finite.
- Clamp non-periodic coordinates to `[0, 1]`; wrap periodic coordinates consistently with optimizer behavior. Alternatively, reject out-of-range values in first patch and document requirement. Rejection is safer and easier to reason about.
- Index getters/setters must report `VSP_INDEX_OUT_RANGE`.

`AddFitModelTargetPt` should create `TargetPt` directly. It should not depend on `PtCloudGeom::m_Selected`, Fit Model screen visibility, or vehicle selection flags.

Suggested implementation sequence:

1. Validate inputs.
2. Allocate `TargetPt`.
3. Set target coordinate, target geometry ID, initial `UW`, and fixed/free types.
4. Call `SearchUW` only through explicit `SearchFitModelTargetUW()`; do not hide expensive nearest-point work inside target creation.
5. Add target through `FitModelMgr.AddTargetPt()`.
6. Return new target index.

Keeping search explicit lets callers add a batch of targets, then run one clearly visible search phase.

### Solver operations

```cpp
extern void SearchFitModelTargetUW();
extern void RefineFitModelTargetUW();
extern double UpdateFitModelDistance();
extern double GetFitModelDistance();
extern int OptimizeFitModel();
```

Behavior:

- `SearchFitModelTargetUW` calls `FitModelMgr.SearchTargetUW()`.
- `RefineFitModelTargetUW` calls `FitModelMgr.RefineTargetUW()`.
- `UpdateFitModelDistance` calls `FitModelMgr.UpdateDist()` and returns resulting RMS distance.
- `GetFitModelDistance` returns cached metric without recomputation.
- `OptimizeFitModel` validates problem dimensions before calling `FitModelMgr.Optimize()`.
- After optimization, call `UpdateFitModelDistance()` so cached metric matches optimized geometry.

Precondition checks for `OptimizeFitModel`:

- At least one target point.
- At least one fit variable or free target `U/W` coordinate.
- Number of residual conditions must be adequate for solver: `3 * target_count >= optimization_variable_count`.
- Every parameter ID and target geometry ID remains valid.
- All selected parameters are active and finite.

Return existing `lmder1` info code for compatibility. Invalid API-level preconditions should report through `ErrorMgr` and return `0`, matching current invalid-input result.

### Persistence

```cpp
extern bool SaveFitModel( const std::string & file_name );
extern int LoadFitModel( const std::string & file_name, bool clear_existing = true );
```

Implementation can set existing manager file-name fields and call `Save()` or `Load()`.

Important semantic decision: current `FitModelMgr::Load()` appends targets and variables. Public API should default to clearing existing state first. `clear_existing = false` preserves append behavior when explicitly requested.

## Required Internal Improvements

Public wrappers can call existing methods, but several small manager additions make API behavior safe and clean.

### Delete target by index

Current manager only exposes `DelCurrTargetPt()`, which depends on mutable GUI-oriented current index. Add:

```cpp
bool DelTargetPt( int index );
```

`DelCurrTargetPt()` may delegate to it.

### Update target by index

Either expose controlled setters through manager or implement API wrapper using `GetTargetPt(index)`. Manager method preferred:

```cpp
bool SetTargetPt(
    int index,
    const vec3d & pt,
    const std::string & geom_id,
    const vec2d & uw,
    int u_type,
    int w_type );
```

This centralizes validation and avoids public API code mutating internals piecemeal.

### Empty-target distance guard

Current `FitModelMgr::UpdateDist()` divides by `npt`. Add empty-target handling:

```cpp
if ( npt == 0 )
{
    m_DistMetric = 0.0;
    return;
}
```

### Optimizer allocation and dimension guards

Current `Optimize()` allocates arrays from target and variable counts before checking validity. Add guards before allocation and `lmder1` call.

### Load transaction behavior

Current `Load()` can partially append state before later failure. Longer-term improvement: parse into temporary target/variable collections, validate, then commit. Initial API may document current behavior, but transactional load is preferable.

## API Wrapper Placement

### `src/geom_api/VSP_Geom_API.h`

Add documented declarations under a new Doxygen group, preferably `FitModel`, near point-cloud geometry functions or analysis/optimization APIs.

Every function should include:

- C++ example
- Python example
- parameter contracts
- return/error semantics
- related-function links

### `src/geom_api/VSP_Geom_API.cpp`

Add:

```cpp
#include "FitModelMgr.h"
#include "ParmMgr.h"
```

Implement wrappers in namespace `vsp`, following patterns used by `GetPtCloudPnts`, `CreatePtCloudGeom`, and `ProjectPtCloudPts`.

Validation helpers may reduce duplication:

```cpp
static TargetPt* FindFitTargetForOp( int index, const char* operation );
static Geom* FindFitTargetGeomForOp( const std::string& geom_id, const char* operation );
static bool IsValidFitTargetType( int type );
```

Keep helpers file-local unless useful elsewhere.

### `src/geom_core/ScriptMgr.cpp`

Register scalar/string functions directly with `asFUNCTION`.

Examples:

```cpp
r = se->RegisterGlobalFunction(
    "bool AddFitModelVar( const string & in parm_id )",
    asFUNCTION( vsp::AddFitModelVar ), asCALL_CDECL );
assert( r >= 0 );

r = se->RegisterGlobalFunction(
    "int AddFitModelTargetPt( const vec3d & in target_pt, const string & in target_geom_id, double u = 0.5, int u_type = FIT_FREE, double w = 0.5, int w_type = FIT_FREE )",
    asFUNCTION( vsp::AddFitModelTargetPt ), asCALL_CDECL );
assert( r >= 0 );
```

Vector return types may need `ScriptMgrSingleton` adapter methods, following `GetPtCloudPnts()` for array conversion.

Register enum values near other API enum registration:

```cpp
r = se->RegisterEnum( "FIT_TARGET_TYPE" );
assert( r >= 0 );
r = se->RegisterEnumValue( "FIT_TARGET_TYPE", "FIT_FIXED", FIT_FIXED );
assert( r >= 0 );
r = se->RegisterEnumValue( "FIT_TARGET_TYPE", "FIT_FREE", FIT_FREE );
assert( r >= 0 );
```

## Suggested Python Workflow

```python
import openvsp as vsp

vsp.ClearVSPModel()

cloud_id = vsp.ImportFile("aircraft.pts", vsp.IMPORT_PTS, "")
cloud_points = vsp.GetPtCloudPnts(cloud_id)

# External code segments/downsamples cloud and builds initial geometry.
fuselage_id = vsp.AddGeom("FUSELAGE")
wing_id = vsp.AddGeom("WING")

# Configure coarse model using SetParmVal/GetXSec APIs.
# ...

vsp.ResetFitModel()

vsp.AddFitModelVar(vsp.FindParm(fuselage_id, "Length", "Design"))
vsp.AddFitModelVar(vsp.FindParm(wing_id, "TotalSpan", "WingGeom"))

for point in fuselage_targets:
    vsp.AddFitModelTargetPt(point, fuselage_id)

for point in wing_targets:
    vsp.AddFitModelTargetPt(point, wing_id)

vsp.SearchFitModelTargetUW()
vsp.RefineFitModelTargetUW()
before = vsp.UpdateFitModelDistance()
info = vsp.OptimizeFitModel()
after = vsp.GetFitModelDistance()

vsp.WriteVSPFile("fitted_aircraft.vsp3", vsp.SET_ALL)
```

Parameter names above are illustrative; production scripts should verify actual parameter IDs from created geometry.

## Tests

Add API tests near existing geometry API tests.

### Basic target lifecycle

1. Add POD or fuselage geometry.
2. Add target point.
3. Verify target count and getters.
4. Update target.
5. Delete target.
6. Verify count returns to zero.

### Invalid target inputs

Test:

- nonexistent geometry ID
- point-cloud target geometry
- invalid U/W type
- out-of-range target index
- non-finite coordinate
- non-finite U/W

Each must add expected `ErrorMgr` error and avoid state mutation.

### Variable lifecycle

Test:

- valid parameter add
- duplicate add
- invalid parameter ID
- delete existing
- delete missing
- clear all

### Solver smoke test

1. Create a simple POD with intentionally wrong length/fineness.
2. Generate target points from a second reference POD or known surface coordinates.
3. Add fitting parameters.
4. Add target points.
5. Search/refine U/W.
6. Optimize.
7. Assert final RMS distance is lower than initial RMS distance.
8. Assert solver info code indicates termination rather than invalid input.

### Persistence

1. Build fit state.
2. Save `.fit`.
3. Reset manager.
4. Load `.fit`.
5. Verify target and variable counts plus values.

### Binding smoke test

Run equivalent AngelScript/Python API test to prove registration and generated wrapper behavior.

## Error Semantics

Recommended mapping:

- invalid geometry/parameter ID -> `VSP_INVALID_PTR`
- wrong target geometry type -> `VSP_INVALID_TYPE`
- invalid fixed/free value -> `VSP_INVALID_TYPE`
- invalid target index -> `VSP_INDEX_OUT_RANGE`
- invalid numeric value or solver dimensions -> `VSP_INVALID_INPUT_VAL`
- duplicate variable -> `VSP_INVALID_INPUT_VAL`
- file operation failure -> existing file-related error code where available

Functions returning values should return neutral failure values:

- index: `-1`
- count: `0`
- distance: `0.0` or `NaN`; `0.0` matches existing style but can mask errors, so callers must inspect `ErrorMgr`
- bool: `false`
- optimizer info: `0`

## Naming Rationale

Use `FitModel` in every public symbol. Avoid generic names such as `AddFitVar` that may collide with future optimization systems.

Recommended names:

- `AddFitModelVar`
- `AddFitModelTargetPt`
- `OptimizeFitModel`

These map clearly to GUI utility name and `FitModelMgr` implementation.

## Future Extensions

Potential second phase:

- target weights
- component/group weights
- robust losses such as Huber or Cauchy
- parameter scaling
- lower/upper bounds separate from `Parm` bounds
- target surface index
- target normal constraints
- point-to-plane residuals
- per-target enable/disable
- solver tolerance and iteration controls
- progress/cancellation callbacks
- fit result struct containing status, iterations, initial RMS, final RMS, and message
- bulk target insertion to reduce Python binding overhead

Possible bulk API:

```cpp
extern int AddFitModelTargetPts(
    const std::vector<vec3d> & target_pts,
    const std::string & target_geom_id,
    int u_type = FIT_FREE,
    int w_type = FIT_FREE );
```

Bulk insertion should wait until scalar API behavior and tests stabilize.

## Recommended Implementation Order

1. Add manager safety guards for empty targets and invalid optimizer dimensions.
2. Add target deletion/update by index.
3. Add public enum.
4. Add state and variable wrappers.
5. Add target wrappers.
6. Add solver wrappers.
7. Register AngelScript bindings.
8. Add C++ and script tests.
9. Add persistence wrappers.
10. Add bulk target API only if profiling shows binding overhead matters.

## Acceptance Criteria

Implementation is complete when a headless script can:

1. Import or otherwise obtain point-cloud coordinates.
2. Create parametric OpenVSP geometry.
3. Register geometry parameters as fit variables.
4. Add externally selected target coordinates without GUI interaction.
5. Search/refine target surface coordinates.
6. Run optimizer.
7. observe reduced RMS distance.
8. Save resulting `.vsp3` and optional `.fit` files.
