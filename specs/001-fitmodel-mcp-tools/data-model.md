# Data Model: Fit Model Tools for Agents

**Feature**: [spec.md](spec.md) | **Research**: [research.md](research.md)

These are the shapes exchanged between the agent and the tools. The state they describe (point
clouds, variables, targets, cached distance) lives entirely in the OpenVSP engine. The tools keep
no state of their own between calls.

All coordinates and distances are in model units. All results are JSON-safe.

## Point Cloud

A `PtCloud` component created by import.

| Field | Type | Notes |
|-------|------|-------|
| `geom_id` | string | Component ID returned by the engine |
| `num_points` | int | ≥ 1. An import that yields 0 points is an error (R8) |
| `bbox_min`, `bbox_max` | `[x, y, z]` | Summary only |
| `centroid` | `[x, y, z]` | Summary only |

**Validation**: Any tool taking `cloud_id` fails if the geom does not exist or its type is not
`PtCloud`.

## Fit Variable

A model parameter the optimizer may change.

| Field | Type | Notes |
|-------|------|-------|
| `parm_id` | string | Valid only within the session |
| `name` | string | e.g. `Length` |
| `group` | string | e.g. `Design`, `XSec` |
| `geom_id` | string \| null | Owning component found by scanning (R9). `null` if not found |
| `geom_name` | string \| null | |
| `value` | float \| null | `null` when `valid` is false |
| `valid` | bool | False when the parm no longer exists (orphaned) |

**Validation (add)**: the parm must pass `ValidParm` and must not already be a variable. A batch
is all-or-nothing.

**Order**: the engine's order (sorted by parameter name).

## Target Point

A coordinate the fitted surface of one component should pass through.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `index` | int | assigned | Position in the setup. Deleting a target shifts later indices down by one |
| `point` | `[x, y, z]` | required | Finite |
| `geom_id` | string | required | Must exist and be a fittable type (the engine decides; R6) |
| `u`, `w` | float | 0.5 | Within `[0, 1]` (R5), finite |
| `u_type`, `w_type` | `"FREE"` \| `"FIXED"` | `"FREE"` | Case-insensitive on input |

**Input form (batch entry)**: `{"x", "y", "z", "geom_id", "u"?, "w"?, "u_type"?, "w_type"?}`.

**Update**: every field is optional. Omitted fields keep their current values.

## Region Selection

Input to the tool that creates targets from cloud points.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `cloud_id` | string | required | A `PtCloud` component |
| `geom_id` | string | required | Component the targets constrain |
| `bbox_min`, `bbox_max` | `[x, y, z]` | required | Inclusive. `bbox_min ≤ bbox_max` on every axis |
| `stride` | int | 1 | ≥ 1. Keep every Nth match, in cloud order |
| `u_type`, `w_type` | `"FREE"` \| `"FIXED"` | `"FREE"` | u and w start at 0.5 |

**Validation**: 1 ≤ selected ≤ 10,000, otherwise an error with `matched` and `selected` counts.

## Fit Setup

The engine's current variables and targets as a whole. It is saved to or loaded from a `.fit`
file in the existing format.

| Operation | Effect |
|-----------|--------|
| reset | Clears variables, targets and the cached distance |
| clear vars / clear targets | Clears only that collection |
| load (`append=false`, the default) | Replaces the setup |
| load (`append=true`) | Adds to the setup |

**Load result extras**: `missing_parm_ids` (variables in the file that are not in the model),
`dangling_target_indices` (targets whose `geom_id` is not in the model). If either is non-empty,
the result is an error result (R14).

## Distance Result

| Field | Type | Notes |
|-------|------|-------|
| `rms` | float | ≥ 0. Exactly 0 when there are no targets (R11) |
| `num_targets` | int | |

## Optimize Result (single pass)

| Field | Type | Notes |
|-------|------|-------|
| `info` | int | MINPACK code 0–7 (R12) |
| `info_meaning` | string | Plain-language text from the R12 table |
| `rms_before`, `rms_after` | float | |
| `vars` | list of Fit Variable | Values after the pass |

## Fit Run (converged fit)

| Field | Type | Notes |
|-------|------|-------|
| `passes` | int | 1 … `max_passes` |
| `stop_reason` | `"converged"` \| `"no_improvement"` \| `"pass_limit"` \| `"error"` | |
| `rms_history` | list of `{pass, rms_before, rms_after, info}` | One entry per completed pass |
| `rms_initial`, `rms_final` | float | |
| `vars` | list of Fit Variable | Final values |
| `error`, `vsp_errors` | | Present only when `stop_reason == "error"` |

**Inputs**: `max_passes` (int, 1–100, default 10), `tolerance` (float > 0, default 1e-6),
`refine` (bool, default true).

### Loop states

```text
start ──► pre-check (R10) ──fail──► error (no passes run)
              │ ok
              ▼
   ┌──► pass k: search → [refine] → rms_before → optimize → rms_after
   │          │
   │          ├─ engine error ─────────────────────────────► stop: error
   │          ├─ rms_after == 0 or 0 ≤ rel_impr < tol ──────► stop: converged
   │          ├─ rms_after > prev_rms ──────────────────────► stop: no_improvement
   │          ├─ k == max_passes ───────────────────────────► stop: pass_limit
   └──────────┘ otherwise, k += 1
```

`rel_impr = (prev_rms − rms_after) / prev_rms`. `prev_rms` is the previous pass's `rms_after`,
or `rms_before` for pass 1.

## Error Result

Returned by any tool in place of its success shape.

| Field | Type | Notes |
|-------|------|-------|
| `error` | string | Names the failing input (index, parm ID, geom ID, file) and the reason (FR-016) |
| `vsp_errors` | list of `{code, message}` | Engine errors raised during this call only (R2) |
| `invalid` | list of `{position, reason}` | Batch tools: every rejected entry |
| *(tool-specific)* | | e.g. `matched`, `missing_parm_ids`, `dangling_target_indices`, partial `rms_history` |
