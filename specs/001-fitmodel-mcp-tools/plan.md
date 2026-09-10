# Implementation Plan: Fit Model Tools for Agents

**Branch**: `001-fitmodel-mcp-tools` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-fitmodel-mcp-tools/spec.md`

## Summary

Expose the finished headless Fit Model API, plus the point-cloud access it needs, as 23 MCP tools
in one new module, `openvsp/mcp/_fitmodel.py`. The tools are thin Python wrappers over the
existing `openvsp` bindings, with no C++ changes. They add only:

- sequencing: the fit-to-convergence loop, which probes showed is required, because one optimize
  pass stops at RMS 0.136 while four passes recover the truth exactly
- validation: u/w range checks, dangling references, and atomic batches with rollback
- region-based selection of cloud points
- reporting: every engine `ErrorMgr` error is surfaced, and printing to stdout is silenced so it
  cannot corrupt the stdio transport

Details are in [research.md](research.md), shapes in [data-model.md](data-model.md), and the
agent-facing contract in [contracts/mcp-tools.md](contracts/mcp-tools.md).

## Technical Context

**Language/Version**: Python 3.11 and 3.13 (CI matrix); the local build venv is 3.12

**Primary Dependencies**: `mcp` 1.x (`FastMCP`, pinned `<2`), the OpenVSP SWIG bindings
(`openvsp`, 3.51.3 with the Fit Model API), and the standard library (`xml.etree`, `math`). No new
dependencies.

**Storage**: Files only. `.pts` point clouds in, `.fit` setups in and out, both in existing
formats. `.vsp3` is saved through the existing tool.

**Testing**: pytest (the unittest-style MCP tests run under it). Fake-`vsp` unit tests in
`openvsp/tests/`, and real-binding tests in `src/test/py/tests/` run by the `PyTest` CTest target.

**Target Platform**: Headless OpenVSP Python API on Linux, Windows and macOS. MCP over stdio or SSE.

**Project Type**: Additive tool module in an existing library's MCP server

**Performance Goals**:
- Summarise or select from a 1,000,000-point cloud in 2 s or less. Measured: 200k points import in
  0.50 s and are read in 0.12 s.
- A single-component converged fit of 72 targets in 1 s or less. Measured: 0.29 s.

**Constraints**:
- No response contains more than 1,000 points or targets.
- Batches are capped at 10,000 targets.
- Nothing is written to stdout except by the MCP transport.
- Tools keep no state; all state lives in the engine.

**Scale/Scope**: 23 new tools (the server goes from 185 to 208). About 700 lines in the module,
matching the size of the existing modules, and about 600 lines of tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Pre-research | Post-design |
|-----------|------|--------------|-------------|
| I. Conventions | New module copies the `_geometry.py` idioms: `from __future__ import annotations`, `# ====` sections, a docstring on every tool, `_vsp()` from `_core`, try/except returning an error | Pass | Pass. Contract uses snake_case names like the existing tools, dict results like `_surface.py`, and no restyling of other files |
| II. One headless API | MCP tools are thin wrappers and must not reimplement geometry or analysis logic | Pass, with a note | Pass. Every surface evaluation, correspondence search, distance and optimization is an engine call. Tool code only (a) validates inputs, (b) sequences calls (the R13 loop), (c) filters existing cloud coordinates by a box (R7, the FR-017 carve-out), and (d) reads `ParmID`s from a `.fit` file for reporting (R14). None of this computes geometry |
| III. Errors | Tools catch exceptions and return an error value, and engine failures are never silent | Pass | Pass. The R2 helper surfaces only this call's `ErrorMgr` entries and silences stdout printing. Error results name the input at fault (FR-016) |
| IV. Tests | Test-first. MCP tests use the fake-`vsp` harness, API tests go in `src/test/py/tests/`, and CTest passes | Pass | Pass. R15: unit tests in `test_mcp_fitmodel.py` (the harness gains Fit Model mocks and a stateful ErrorMgr fake), real-binding tests in `test_FitModel_MCP.py`, registration asserted in `test_mcp_server.py` |
| V. Upstream compatibility | Additive only, no C++ or dependency changes | Pass | Pass. One new module, one import line, and edits to the test harness and docs. Engine gaps found during research are recorded as follow-ups (research R16), not patched here |

No violations, so Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-fitmodel-mcp-tools/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0: decisions R1–R16 with measurements
├── data-model.md        # Phase 1: result and input shapes, fit-loop states
├── quickstart.md        # Phase 1: how to validate the feature
├── contracts/
│   └── mcp-tools.md     # Phase 1: 23-tool agent contract and FR coverage
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks), not created here
```

### Source Code (repository root)

```text
src/python_api/packages/openvsp/openvsp/
├── mcp/
│   ├── __init__.py              # EDIT: add _fitmodel to the side-effect import list
│   └── _fitmodel.py             # NEW: 23 tools plus private helpers (error capture,
│                                #      validation, parm→geom map, dangling check)
├── tests/
│   ├── _mcp_test_utils.py       # EDIT: Fit Model/PtCloud mocks, stateful fake ErrorMgr,
│   │                            #       _fitmodel in _load_full_server
│   ├── test_mcp_fitmodel.py     # NEW: fake-vsp unit tests, one class per contract section
│   └── test_mcp_server.py       # EDIT: assert the new tool names are registered
└── index.rst                    # EDIT: add point cloud fitting to the "server exposes tools for" list

src/test/py/tests/
└── test_FitModel_MCP.py         # NEW: real-binding tests (SC-001 POD recovery, SC-006
                                 #      fuselage+wing, region selection, save/load, R5/R8/R10/R11/R14)

docs/
└── FitModelAPI.md               # EDIT: short "MCP tools" status note pointing at the contract
```

**Structure Decision**: This is an addition to the existing MCP package. It follows the layout of
the eight current tool modules and their paired `test_mcp_*.py` files. Real-binding coverage goes
next to the existing `test_FitModel_*.py` suite so the `PyTest` CTest target picks it up with no
CMake changes.

## Complexity Tracking

No Constitution Check violations, so nothing to justify.

## Follow-ups outside this feature

The engine gaps in research R16 are all worked around here. Of those, the one-line `SilenceErrors()`
call in `openvsp/mcp/__init__.py:main()` has the highest value, because without it any of the
other 185 tools can corrupt the stdio stream the first time the engine reports an error. It is a
separate change, better made as its own commit.
