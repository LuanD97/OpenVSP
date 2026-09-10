# Contract: Fit Model MCP Tools

**Module**: `openvsp/mcp/_fitmodel.py` | **Shapes**: [data-model.md](../data-model.md)

The tool names, parameters and result shapes below are the public contract for agents. Every
tool returns a `dict`. Failures return an **Error Result** (`{"error": …, "vsp_errors": […], …}`)
and never raise. "Engine" means the OpenVSP Python API. Each row notes the engine calls a tool
makes and the checks it adds on top, with the research decision behind them.

Recommended order, which is also stated in the tool descriptions (FR-018):
`import_point_cloud` → `get_point_cloud_summary` → build/adjust geometry with the existing tools →
`reset_fit_model` → `add_fit_model_vars` → `add_fit_model_targets` /
`add_fit_model_targets_from_cloud` → `fit_model_to_convergence` → `write_vsp_file`.

## Point cloud

| Tool | Parameters | Success result | Engine calls / added checks |
|------|------------|----------------|-----------------------------|
| `import_point_cloud` | `file_name: str` (absolute path; plain text, one `x y z` per line) | `{geom_id, num_points}` | `ImportFile(…, IMPORT_PTS, "")`. `"NONE"` or 0 points is an error naming the file, and an empty component is deleted (R8) |
| `get_point_cloud_summary` | `cloud_id: str` | `{geom_id, num_points, bbox_min, bbox_max, centroid}` | `GetPtCloudPnts`. Must be a `PtCloud` |
| `get_point_cloud_points` | `cloud_id: str`, `start: int = 0`, `count: int = 1000`, `stride: int = 1` | `{total, start, stride, returned, next_start, points: [[x,y,z],…]}` | `count` limited to 1–1000, `stride ≥ 1`, `start` in range. `next_start` is `null` when done |

## Setup state

| Tool | Parameters | Success result | Engine calls |
|------|------------|----------------|--------------|
| `reset_fit_model` | none | `{num_vars: 0, num_targets: 0}` | `ResetFitModel` |
| `clear_fit_model_vars` | none | `{num_vars: 0, num_targets}` | `ClearFitModelVars` |
| `clear_fit_model_targets` | none | `{num_vars, num_targets: 0}` | `ClearFitModelTargetPts` |

## Variables

| Tool | Parameters | Success result | Engine calls / added checks |
|------|------------|----------------|-----------------------------|
| `add_fit_model_vars` | `parm_ids: list[str]` (1–1000) | `{added: n, vars: [Fit Variable…]}` | `ValidParm` plus duplicate pre-check, then `AddFitModelVar` each. All-or-nothing with rollback. `invalid` lists every bad entry (R9) |
| `delete_fit_model_var` | `parm_id: str` | `{num_vars}` | `DeleteFitModelVar` |
| `list_fit_model_vars` | none | `{num_vars, vars: [Fit Variable…]}` | `GetFitModelVarIDs`, `ValidParm`, `GetParmName/GroupName/Val`, geom scan (R9) |

## Targets

| Tool | Parameters | Success result | Engine calls / added checks |
|------|------------|----------------|-----------------------------|
| `add_fit_model_targets` | `targets: list[{x, y, z, geom_id, u?, w?, u_type?, w_type?}]` (1–10,000) | `{count, first_index, last_index, num_targets}` | Python pre-validation (finite, u/w in [0,1], type strings, geom exists), then `AddFitModelTargetPt` each. All-or-nothing with rollback. `invalid: [{position, reason}]` (R5, R6) |
| `add_fit_model_targets_from_cloud` | `cloud_id: str`, `geom_id: str`, `bbox_min: [x,y,z]`, `bbox_max: [x,y,z]`, `stride: int = 1`, `u_type: str = "FREE"`, `w_type: str = "FREE"` | `{matched, count, first_index, last_index, num_targets}`, with no coordinates | `GetPtCloudPnts`, inclusive box filter, stride, then the batch path above. 0 selected, or more than 10,000, is an error with counts (R7) |
| `get_fit_model_target` | `index: int` | Target Point | `GetFitModelTargetPt/GeomID/UW/UType/WType` |
| `list_fit_model_targets` | `start: int = 0`, `count: int = 1000` | `{total, start, returned, next_start, targets: [Target Point…]}` | as above, paged. `count` limited to 1–1000 |
| `update_fit_model_target` | `index: int`, plus optional `x, y, z, geom_id, u, w, u_type, w_type` | Target Point (after the update) | Read current values, merge, validate as for add, then `SetFitModelTargetPt` |
| `delete_fit_model_target` | `index: int` | `{num_targets}` | `DeleteFitModelTargetPt`. Later indices shift down by one (stated in the description) |

## Solving

| Tool | Parameters | Success result | Engine calls / added checks |
|------|------------|----------------|-----------------------------|
| `search_fit_model_target_uw` | none | `{num_targets}` | Dangling pre-check (R10), then `SearchFitModelTargetUW` |
| `refine_fit_model_target_uw` | none | `{num_targets}` | R10, then `RefineFitModelTargetUW` |
| `update_fit_model_distance` | none | `{rms, num_targets}` | 0 targets gives `rms: 0.0` without an engine call (R11). Otherwise R10, then `UpdateFitModelDistance` |
| `get_fit_model_distance` | none | `{rms, num_targets}` | `GetFitModelDistance` (cached, no recompute) |
| `optimize_fit_model` | none | Optimize Result | R10, then `UpdateFitModelDistance` → `OptimizeFitModel` → `GetFitModelDistance`. The description warns that one pass can stop short far from the solution (R12) |
| `fit_model_to_convergence` | `max_passes: int = 10` (1–100), `tolerance: float = 1e-6` (> 0), `refine: bool = True` | Fit Run | R10, then the loop in R13 / data-model "Loop states" |

## Persistence

| Tool | Parameters | Success result | Engine calls / added checks |
|------|------------|----------------|-----------------------------|
| `save_fit_model` | `file_name: str` | `{file_name, num_vars, num_targets}` | `SaveFitModel`. `False` is an error |
| `load_fit_model` | `file_name: str`, `append: bool = False` | `{num_vars, num_targets}` | `LoadFitModel(file, not append)`, then the `.fit` ParmID diff and dangling-target check. Anything unresolved is an Error Result with `missing_parm_ids` / `dangling_target_indices` (R14) |

## Guarantees across all tools

1. **No silent engine errors**: any engine error raised during the call turns the result into an
   Error Result with `vsp_errors`. Errors from earlier calls are left alone (R2).
2. **No stdout pollution**: engine error printing is silenced before the first engine call (R2).
3. **Bounded responses**: no result contains more than 1,000 points or targets (SC-004).
4. **Atomic batches**: `add_fit_model_vars`, `add_fit_model_targets` and
   `add_fit_model_targets_from_cloud` either apply fully or leave the setup unchanged.
5. **Parity**: results equal those from the same engine call sequence made directly (FR-017).
6. **Headless**: no tool touches the GUI (FR-019).

## FR coverage

| FR | Tools |
|----|-------|
| FR-001–003 | `import_point_cloud`, `get_point_cloud_summary`, `get_point_cloud_points` |
| FR-004 | `reset_fit_model`, `clear_fit_model_vars`, `clear_fit_model_targets` |
| FR-005 | `add_fit_model_vars`, `delete_fit_model_var`, `list_fit_model_vars` |
| FR-006, FR-007 | `add_fit_model_targets`, `get_/list_/update_/delete_fit_model_target(s)` |
| FR-008, FR-009 | `search_/refine_fit_model_target_uw`, `update_/get_fit_model_distance` |
| FR-010, FR-011 | `optimize_fit_model`, `fit_model_to_convergence` |
| FR-012 | `add_fit_model_targets_from_cloud` |
| FR-013 | `save_fit_model`, `load_fit_model` |
| FR-014 | existing `write_vsp_file` (no new tool) |
| FR-015–020 | the cross-tool guarantees above |
