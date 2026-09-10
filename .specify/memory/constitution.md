<!--
Sync Impact Report
==================
Version change: (unversioned template) → 1.0.0
Rationale: initial ratification; every placeholder filled for the first time.

Principles defined:
- [PRINCIPLE_1_NAME] → I. Follow Established Conventions (NON-NEGOTIABLE)
- [PRINCIPLE_2_NAME] → II. One Headless API, Every Binding
- [PRINCIPLE_3_NAME] → III. API Contract and Error Reporting
- [PRINCIPLE_4_NAME] → IV. Test-Backed Changes
- [PRINCIPLE_5_NAME] → V. Upstream Compatibility and Minimal Divergence

Sections added:
- Technology and Build Constraints (was [SECTION_2_NAME])
- Development Workflow (was [SECTION_3_NAME])
- Governance (filled)

Sections removed: none

Templates (read the constitution at runtime; not modified by this command):
- .specify/templates/plan-template.md — its "Constitution Check" gate evaluates Principles I–V
- .specify/templates/spec-template.md — no change required
- .specify/templates/tasks-template.md — Principle IV implies test tasks come first

Deferred TODOs: none
-->

# OpenVSP Constitution

## Core Principles

### I. Follow Established Conventions (NON-NEGOTIABLE)

New and modified code MUST match the conventions already established in this repository and
in the file being edited. When a convention is unclear, the surrounding code is the reference.
Contributors MUST NOT introduce new styles, patterns, or tooling.

- C++ MUST follow `vsp.astylerc`: Allman braces (`--style=break`), padded operators and
  parentheses (`Foo( a, b )`), braces on every control block, 4-space indentation with no tabs,
  and LF line endings.
- C++ naming MUST follow the existing idiom: `CamelCase` classes and free functions, `m_`
  prefixed members (`m_GeomID`), and `...Mgr` singletons for managers (`FitModelMgr`, `ParmMgr`).
- New C++ source files MUST carry the NOSA 1.3 license banner used by existing files.
- Public API headers MUST fully qualify standard types (`std::string`, `std::vector`) and
  MUST NOT contain `using` directives, because older SWIG builds cannot resolve them.
- Python MUST match the idioms of its package. For example, `openvsp/mcp/` modules use
  `from __future__ import annotations`, docstrings on every tool, `# ====` section banners,
  and the shared `_vsp()` import helper.
- Changes MUST NOT reformat, rename, or restructure code outside the scope of the change.

Rationale: OpenVSP is a large, long-lived codebase with many contributors. Following its
conventions keeps diffs reviewable and keeps this fork mergeable with upstream.

### II. One Headless API, Every Binding

Every user-facing capability MUST be reachable through the public API without GUI state.

- The C++ entry point MUST be declared in `src/geom_api/VSP_Geom_API.h` and implemented in
  `src/geom_api/VSP_Geom_API.cpp` within `namespace vsp`, delegating to the owning `...Mgr`
  in `src/geom_core/`.
- The same function MUST be registered with AngelScript in `src/geom_core/ScriptMgr.cpp`
  under the same name and signature.
- The Python binding MUST come from the SWIG generation in `src/geom_api/*.i`. Hand-written
  Python equivalents of API functions are prohibited.
- Functionality that exists only behind GUI buttons or screens (`src/gui_and_draw/`) MUST be
  moved into, or exposed through, the relevant manager before it is exposed as API.
- MCP tools in `openvsp/mcp/` MUST be thin wrappers over the Python API. They MUST NOT
  reimplement geometry or analysis logic.

Rationale: the C++, AngelScript, Python, and MCP interfaces MUST expose identical behaviour so
that scripts, batch runs, and agents get the same results as the GUI.

### III. API Contract and Error Reporting

- Every API function MUST validate its inputs (IDs, indices, ranges) before acting. On failure
  it MUST call `ErrorMgr.AddError( <APIDefines error code>, "FunctionName::message" )` and
  return. On success it MUST call `ErrorMgr.NoError()`.
- Error codes and enums MUST come from `src/geom_api/APIDefines.h`. New codes or enum values
  MUST be added there with a Doxygen `/*!< ... */` description.
- Every public declaration MUST have a Doxygen block with `\ingroup`, a summary, and
  `\param [in]`/`\param [out]` and `\return` tags where they apply.
- Non-trivial functions SHOULD include example code in both the AngelScript
  (`\forcpponly` / `\code{.cpp}`) and Python (`\beginPythonOnly` / `\code{.py}`) forms. These
  examples MUST be self-checking (increment `__failure` or `assert`) and MUST leave no API
  errors on the queue, because `src/python_api/gen_unit_test.py` turns them into tests.
- MCP tools MUST catch exceptions and return an error value (`{"error": ...}` or
  `"Error: ..."`) that matches the tool's existing return type, instead of raising.

Rationale: API callers have no GUI feedback. A consistent error queue and executable
documentation are the only reliable way for them to find out that a call failed.

### IV. Test-Backed Changes

- New API behaviour MUST be developed test-first: write a failing test for one slice of the
  feature, implement the smallest change that passes it, then refactor. This follows the
  precedent set by the Fit Model API work.
- Python API tests MUST live in `src/test/py/tests/` as `test_<Feature>_<Aspect>.py` and run
  under pytest. AngelScript coverage MUST live in `src/test/scripttest/` as
  `Test<Feature>.vspscript` and be registered with `ADD_TEST` in that directory's
  `CMakeLists.txt`.
- MCP tool changes MUST be covered in `openvsp/tests/test_mcp_*.py` using the fake-`vsp`
  harness in `_mcp_test_utils.py`, so the tests run without a compiled `_vsp`.
- Bug fixes MUST include a regression test that fails without the fix.
- Test data files MUST be referenced by relative path and copied next to the test with
  `CONFIGURE_FILE( ... COPYONLY )`, so tests do not depend on the directory they are
  launched from.
- `ctest` in the build tree MUST pass before a change is merged.

Rationale: much of the API was previously GUI-only and unchecked. The conversion of doc
examples into tests has already found real bugs, so tests are what show a change works.

### V. Upstream Compatibility and Minimal Divergence

This repository is a fork of NASA OpenVSP. Changes MUST stay mergeable with upstream and MUST
NOT break its users.

- Existing public API signatures, enum values, and file formats (`.vsp3`, `.fit`, `.des`) MUST
  NOT change incompatibly. API evolution MUST be additive.
- Bundled third-party code in `Libraries/` and `src/external/` MUST NOT be modified except to
  fix a build break, and any such change MUST say why in the commit message.
- Fork-specific work (for example the Fit Model API and the MCP server) MUST be kept in
  self-contained additions where possible, not threaded through unrelated upstream code.
- Dependency pins in `setup.py.in`, `requirements-dev.txt`, and `constraints.txt` MUST carry
  a comment explaining the constraint (for example `numpy<2` for the `_vsp` C-API and
  `mcp<2` for `FastMCP`).

Rationale: every unnecessary divergence makes the next upstream release harder to merge.

## Technology and Build Constraints

- Language standards: C++17 (`CMAKE_CXX_STANDARD 17`), CMake 3.24 or newer, and Python 3.11
  and 3.13 as exercised by the CI matrix.
- Build: two-stage CMake. `Libraries/` builds into `buildlibs/`, then `src/` builds into
  `build/` with `VSP_LIBRARY_PATH` pointing at `buildlibs/`. Build directories MUST NOT be
  committed.
- Portability: code MUST build on the CI matrix in `.github/workflows/build.yml` (Windows
  MSVC, Ubuntu GCC 13, macOS LLVM). Platform-specific code MUST be guarded the way existing
  code is (for example `#ifdef WIN32`).
- Headless targets (`vspscript`, the Python API) MUST build and run without graphics
  libraries. GUI-only dependencies MUST stay confined to GRAPHICS_ONLY targets.
- Python bindings are generated by SWIG. The `_vsp` extension targets the numpy 1.x C-API.
- License: NASA Open Source Agreement 1.3. New dependencies MUST be license-compatible and
  listed in `README.md` under the matching dependency category.

## Development Workflow

- Commit subjects MUST be in the imperative mood and sentence case, with no trailing period,
  describing the user-visible effect ("Expose Geom textures", "Fix crash in DeleteExcrescence
  with an out of range index"). Each commit SHOULD cover one logical change.
- Commit bodies MUST explain why the change was made and what evidence supports it
  (reproduction, failing test, affected platform), wrapped at about 72 columns. Newly
  exposed API functions SHOULD be listed in the body.
- Commits that expose API MUST include the header declaration, implementation, AngelScript
  registration, and tests together. They MUST NOT be split so that any binding lags behind.
- Design notes and proposals for multi-slice features MUST go in `docs/<Feature>.md` and be
  kept current with a status section as slices land.
- `CHANGELOG.md` is generated from release tag annotations by `changelog.sh` and MUST NOT be
  edited by hand.
- Local agent configuration (for example `AGENTS.md`), scratch models, and exported
  artifacts MUST NOT be committed.

## Governance

This constitution takes precedence over informal practice for all work in this repository.
Where it is silent, the established conventions of the surrounding code apply (Principle I).

- Amendments MUST be made by editing `.specify/memory/constitution.md` through
  `/speckit-constitution`, updating the Sync Impact Report, and committing with a message that
  states the version change.
- Versioning follows semantic versioning. MAJOR is for removing or redefining a principle.
  MINOR is for adding a principle or section, or materially expanding guidance. PATCH is for
  clarifications and wording fixes.
- Every `/speckit-plan` MUST pass its Constitution Check against Principles I–V before design
  begins, and again after design. Any justified violation MUST be recorded in the plan's
  Complexity Tracking table.
- Code review MUST confirm compliance, in particular convention conformance, binding parity,
  error reporting, and test coverage.

**Version**: 1.0.0 | **Ratified**: 2026-09-10 | **Last Amended**: 2026-09-10
