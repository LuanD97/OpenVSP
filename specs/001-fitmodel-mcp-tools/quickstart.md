# Quickstart: Validating the Fit Model Tools

**Feature**: [spec.md](spec.md) | **Contract**: [contracts/mcp-tools.md](contracts/mcp-tools.md)

This is a run guide for proving the feature works. It lists what to run and what to expect, but
contains no implementation.

## Prerequisites

- OpenVSP built with the Python API. The build tree is `~/build/projects/openvsp/vsp`.
- The build-tree venv is `~/build/projects/openvsp/vsp/venv`. It contains the compiled `openvsp`
  (3.51.3, with the Fit Model API), `mcp` 1.x, numpy < 2, and pytest. Use this interpreter, not
  system Python.
- Commands below run from the repository root, with `PY=~/build/projects/openvsp/vsp/venv/bin/python`.

> **The venv imports `openvsp` from a copy.** The package lives in
> `~/build/projects/openvsp/vsp/python_pseudo/`, which is a **copy** of
> `src/python_api/packages/` and not a link to it. After editing `openvsp/mcp/_fitmodel.py`, sync
> the copy before running anything that imports `openvsp.mcp` for real. From the repository root:
>
> ```bash
> cmake -E copy_directory src/python_api/packages/ ~/build/projects/openvsp/vsp/python_pseudo/
> ```
>
> **Do not use `--target copy_package` from this worktree.** That build tree was configured from
> the main checkout (`~/Documents/repos/OpenVSP`, see `VSP_SOURCE_DIR` in its `CMakeCache.txt`),
> so `copy_package` copies *that* checkout's packages and silently reverts these tools. The C++
> is identical between the two, so only the Python copy needs this manual step. It becomes
> unnecessary once the build tree's source checkout contains this work.
>
> The fake-`vsp` unit tests (step 1) load modules by path from the source tree, so they don't need
> this step.

## 1. Unit tests (fake `vsp`, no compiled bindings needed)

```bash
$PY -m pytest src/python_api/packages/openvsp/openvsp/tests/test_mcp_fitmodel.py \
              src/python_api/packages/openvsp/openvsp/tests/test_mcp_server.py -q
```

**Expected**:
- All pass.
- `test_mcp_server.py` sees at least 208 tools (185 existing plus 23 new), including every name in
  the contract.
- Error-capture tests show that only errors raised during the call are reported, and that earlier
  errors are left on the queue.
- Batch tests show that a rejected entry leaves the setup unchanged.

## 2. Real-binding tests

```bash
cmake -E copy_directory src/python_api/packages/ ~/build/projects/openvsp/vsp/python_pseudo/
$PY -m pytest src/test/py/tests/test_FitModel_MCP.py -q
```

**Expected**:

| Scenario | Proves | Pass condition |
|----------|--------|----------------|
| POD, truth `Length 7.5 / FineRatio 9.0`, start `4.0 / 15.0`, 72 targets, `fit_model_to_convergence()` | SC-001, US2 | Both values within 0.1%, `stop_reason == "converged"`, `rms_final` ≈ 0, in no more than 10 passes |
| Same setup with `max_passes=1` | US2 scenario 2 | `passes == 1`, `stop_reason == "pass_limit"` |
| Single `optimize_fit_model()` from the far start | FR-010, R12 | `rms_after < rms_before`, `info` in 1–4, and values *not* yet within 0.1% (shows the loop is needed) |
| Fuselage and wing sampled to a cloud, then perturbed, then fitted | SC-006 | `rms_final ≤ 0.1 × rms_initial` |
| Cloud file of 100,000 points, `get_point_cloud_summary`, `get_point_cloud_points(count=5000)` | FR-002, FR-003, SC-004 | Summary has no coordinates, and at most 1,000 points are returned with `next_start` set |
| `add_fit_model_targets_from_cloud` with a box and `stride=10` | FR-012, US3 scenario 3 | `count` equals the number of in-box points ÷ 10 (rounded up), and the result has no coordinates |
| `save_fit_model` → `reset_fit_model` → `load_fit_model` | FR-013, US4 | Variables and every target field round-trip |
| `load_fit_model(append=True)` on an existing setup | US4 scenario 3 | Counts add up |
| Load into a model missing the saved parms | R14 | Error result lists `missing_parm_ids` |
| Target u = 1.5, target on a `BLANK` geom, bad index, duplicate variable | Edge cases, FR-016 | Each gives an error result naming the input, and the setup is unchanged |
| Delete a target's geom, then `optimize_fit_model` | R10 | Error lists `dangling_target_indices`, and the engine is not called |
| Missing `.pts` file | R8 | Error names the file, and no component is left behind |

## 3. Full CTest run

```bash
cd src/test/py && $PY -m pytest . -q
```

This is what the `PyTest` CTest target runs, pointed at this worktree. `ctest -R PyTest` in
`~/build/projects/openvsp/vsp` runs the main checkout's copy of `src/test/py` instead, so it only
covers this feature once that checkout contains it.

**Expected**: every test passes except two that already fail without this feature,
`test_FourViewScreenShot` and `test_RoutingGeom`. Both assert that the process-global error queue
is empty, and the existing `test_FitModel_Vars.py` deliberately leaves errors on it. None of the
seven `test_FitModel_*.py` files or `test_FitModel_MCP.py` may fail.

## 4. End-to-end through a real agent (manual)

1. Register the server with an MCP client, using the venv's entry point
   `~/build/projects/openvsp/vsp/venv/bin/openvsp-mcp` (stdio).
2. Make a reference cloud by sampling a known model's surface to a `.pts` file (one `x y z` per
   line), then perturb that model's parameters and save it.
3. Ask the agent to: open the perturbed model, import the cloud, summarise it, choose fit
   variables, create targets from the cloud by region, fit to convergence, and save the result.

**Expected**:
- The fit uses no more than 10 tool calls, not counting geometry building (SC-002).
- The saved model reopens with the original parameter values (US1 scenario 5).
- The client log shows no protocol errors caused by stray `Error Code: …` lines, even when a
  deliberately bad call is included. That verifies the stdout guarantee (research R2).
