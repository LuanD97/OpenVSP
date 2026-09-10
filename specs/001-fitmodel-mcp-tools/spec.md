# Feature Specification: Fit Model Tools for Agents

**Feature Branch**: `001-fitmodel-mcp-tools` (no branch created; work is on `speckit-init`)

**Created**: 2026-09-10

**Status**: Draft

**Input**: User description: "I want to expose the new FitModelMgr API to the MCP tool surface such
that an agent can use it to fully manipulate the FitModel functionality against an imported point
cloud to generate a parametric aircraft geometry."

## Clarifications

### Session 2026-09-10

- Q: Should the converged-fit tool be part of this repository's tool surface, or stay reserved
  for the separate semantic-layer (OOVSP) server? → A: This repository, alongside the one-for-one
  Fit Model tools. OOVSP may reuse it later.
- Q: How are targets chosen from an imported cloud? → A: Both. The agent can send explicit
  coordinates in a batch, and it can ask the server to select cloud points by region with
  optional subsampling, so coordinates never pass through the agent.

## User Scenarios & Testing *(mandatory)*

The actor throughout is an **AI agent** driving OpenVSP through its agent tool surface (the tool
server agents connect to), on behalf of an engineer who has a scanned aircraft and wants an
editable parametric model of it. Today the agent can import a point cloud and build geometry, but
it cannot touch Fit Model at all, so it has no way to tune a model to the cloud.

### User Story 1 - Refine a parametric model against an imported point cloud (Priority: P1)

The agent has already built a coarse parametric model (for example a fuselage and a wing) using
the existing geometry tools. It imports the scan, chooses which model parameters may change, adds
target points from the scan and assigns each to the component it should constrain, finds where
each target lands on its component's surface, measures the fit error, runs the optimizer, reads
back the new parameter values and error, and saves the fitted model.

**Why this priority**: This is the whole feature in its minimum form. Every Fit Model operation
is reachable, and an agent can turn a scan into a fitted parametric model with no GUI.

**Independent Test**: Build a single body of known length and fineness ratio, sample its surface
to a point cloud file, perturb both parameters, then use only the agent tools to import the
cloud, set up the fit, and optimize. The recovered values must match the originals.

**Acceptance Scenarios**:

1. **Given** an empty model and a point cloud file, **When** the agent imports it, **Then** it
   receives the new point cloud component's identifier and point count, without the points
   themselves being returned.
2. **Given** a model with a fuselage component, **When** the agent adds the fuselage length as a
   fit variable, **Then** listing fit variables shows it with its name, group, owning component,
   and current value.
3. **Given** fit variables and a batch of target points assigned to the fuselage, **When** the
   agent runs the correspondence search and then asks for the fit error, **Then** it receives a
   finite error value greater than zero for a perturbed model.
4. **Given** a configured fit, **When** the agent runs an optimization pass, **Then** it receives
   the solver outcome in plain language, the fit error before and after, and each fit variable's
   new value.
5. **Given** a fitted model, **When** the agent saves the model with the existing save tool,
   **Then** reopening that file reproduces the fitted parameter values.

---

### User Story 2 - Fit to convergence in one request (Priority: P2)

One optimization pass keeps the target-to-surface matches fixed. When the model starts far from
the scan, those matches go stale as parameters move, and the result stops short of the answer.
The agent asks for a converged fit in a single request. The system repeats the match-then-optimize
cycle until the error stops improving or a pass limit is reached, and reports the error after each
pass, how many passes ran, and why it stopped.

**Why this priority**: Without it, an agent that runs one optimization pass gets a plausible but
wrong answer and has no signal that it is wrong. A measured case in this repository recovered the
exact parameters only after five cycles, whereas one cycle stopped well short.

**Independent Test**: Use the same perturbed body as User Story 1, starting far from the truth
(for example, length 4.0 vs 7.5 and fineness ratio 15.0 vs 9.0). One request must recover the
true values and return an error history that ends at or near zero.

**Scope note**: In scope for this repository (see Clarifications and FR-011).

**Acceptance Scenarios**:

1. **Given** a configured fit far from the solution, **When** the agent requests a converged fit,
   **Then** the result includes one error value per pass, the number of passes, the stop reason
   (converged, pass limit, or no improvement), and the final variable values.
2. **Given** a pass limit of 1, **When** the agent requests a converged fit, **Then** exactly one
   cycle runs and the stop reason is "pass limit".

---

### User Story 3 - Choose targets from the cloud without moving every point (Priority: P3)

Scans have tens of thousands to millions of points, far more than an agent can read or send back.
The agent needs to inspect the cloud at a coarse level (count, extent, a sample), then turn a chosen
subset into targets for a named component.

**Why this priority**: User Story 1 works when the agent already has sparse, component-labelled
targets, for example from external segmentation. This story lets it work from the raw cloud.

**Independent Test**: Import a cloud of at least 100,000 points and confirm that the summary and
any sample stay within the response size limit. Then create targets for one component from a
chosen subset and confirm the target count and coordinates match that subset.

**Scope note**: Both target sources are in scope: explicit coordinates and server-side region
selection (see Clarifications and FR-012).

**Acceptance Scenarios**:

1. **Given** an imported cloud of 100,000 points, **When** the agent asks for a summary, **Then**
   it receives the point count, bounding box, and centroid, and no coordinates.
2. **Given** an imported cloud, **When** the agent requests points, **Then** no more than the
   response cap is returned, together with the total count and whether the result was truncated.
3. **Given** an imported cloud and a fuselage component, **When** the agent asks for targets
   from the cloud points inside a bounding box, keeping every 10th point, and assigns them to
   the fuselage, **Then** it receives the number of targets created and their index range, and
   no coordinates. Each new target is a cloud point inside the box assigned to the fuselage.

---

### User Story 4 - Inspect, edit, save, and resume a fit setup (Priority: P4)

The agent reviews the current fit setup, corrects individual targets (wrong component, wrong
fixed/free choice, bad coordinate), removes variables that should not move, and saves the setup
to a file so the fit can resume in a later session.

**Why this priority**: Staged fitting (component by component, then coupled) needs targeted edits
and resumable state, but a first fit can be done without them.

**Independent Test**: Configure a fit, save it, reset, and load it back. The variable list and
every target's coordinate, component, u/w values, and fixed/free types must match the saved
state.

**Acceptance Scenarios**:

1. **Given** a fit with 50 targets, **When** the agent updates target 10's component and
   fixed/free types, **Then** reading target 10 shows the new values and the other targets are
   unchanged.
2. **Given** a saved fit setup file and a model with an existing setup, **When** the agent loads
   the file with default options, **Then** the existing setup is replaced, not appended to.
3. **Given** the same situation, **When** the agent loads with append requested, **Then** the
   loaded variables and targets are added to the existing ones.

---

### Edge Cases

- **Point cloud file missing, unreadable, or with no valid points**: the import reports an error
  naming the file. No empty component is left behind.
- **Parameter identifier that does not exist, or is already a fit variable**: the add reports
  which identifier failed and why.
- **Removing a parameter that is not a fit variable**: an error is reported and nothing changes.
- **Target assigned to a component that cannot be fitted** (mesh, human, point cloud, wireframe,
  blank, hinge, n-gon): rejected with the component's type named.
- **Target index out of range** on read, update, or delete: an error names the index and the
  valid range.
- **Non-finite coordinates, u/w outside 0–1, or a fixed/free value that is neither**: rejected
  before any change is made.
- **One invalid target in a batch**: the whole batch is rejected and the response lists every
  invalid entry by position, so the setup is never left half-applied.
- **Optimizing with no targets, no free quantities, or fewer equations than unknowns** (three per
  target versus the number of variables plus free u/w coordinates): rejected before the solver
  runs, with the counts reported.
- **Fit error requested with no targets**: returns 0 rather than failing.
- **Error rises after an optimization pass**: reported as-is, with before and after values, and
  never hidden.
- **Parameter identifiers change between sessions** after a model is reloaded: listing variables
  always includes each variable's name, group, and component, so the agent can re-resolve them.
- **Fit setup file references parameters or components missing from the current model**: the
  load reports each unresolved reference.
- **Targets referencing a deleted component**: optimizing or searching reports the dangling
  targets by index instead of failing silently.
- **Geometry engine reports an error without raising one** (its normal behaviour): the tool
  returns an error result rather than a success.
- **Region selection matches no cloud points**, or the subsampling leaves none: reported as an
  error naming the region, and no targets are created.
- **Region selection would create more targets than the per-request cap**: rejected with the
  matched count, so the agent can narrow the region or increase the subsampling step.

## Requirements *(mandatory)*

### Functional Requirements

**Point cloud access**

- **FR-001**: Agents MUST be able to import a point cloud from a plain-text file with one
  whitespace-separated `x y z` point per line, and receive the new component's identifier and
  point count.
- **FR-002**: Agents MUST be able to get a summary of an imported cloud (point count, bounding
  box, centroid) that contains no individual coordinates.
- **FR-003**: Agents MUST be able to retrieve cloud points in bounded pages. Each response returns
  at most 1,000 points, and reports the total count and whether more remain.

**Fit setup: variables**

- **FR-004**: Agents MUST be able to reset the entire fit setup, clear only the variables, or
  clear only the targets.
- **FR-005**: Agents MUST be able to add and remove fit variables by parameter, and list them.
  Each listed variable MUST include its identifier, name, group, owning component, and current
  value.

**Fit setup: targets**

- **FR-006**: Agents MUST be able to add target points in a single batch. Each target carries a
  coordinate, the component it constrains, optional initial u and w (default 0.5), and a
  fixed/free choice for each (default free). The batch is validated in full before anything is
  applied. On success the new target indices are returned in input order. On failure nothing is
  applied and every invalid entry is reported by position.
- **FR-007**: Agents MUST be able to read, update, and delete an individual target by index, and
  list targets in bounded pages of at most 1,000.

**Fitting**

- **FR-008**: Agents MUST be able to run the correspondence search and the correspondence
  refinement that match each target to a location on its component's surface.
- **FR-009**: Agents MUST be able to compute the current fit error (RMS target-to-surface
  distance), and also to read the last computed value without recomputing it.
- **FR-010**: Agents MUST be able to run a single optimization pass. The result MUST include the
  solver outcome code and its plain-language meaning, the fit error before and after, and each
  fit variable's name and final value.
- **FR-011**: Agents MUST be able to request a converged fit that repeats correspondence search
  and optimization until the relative error improvement between passes drops below a tolerance
  (default 1e-6) or a pass limit (default 10) is reached. The result MUST include the error
  history, pass count, stop reason, and final variable values. This tool is part of this
  repository's tool surface, alongside the one-for-one operations.
- **FR-012**: Agents MUST be able to create targets for a named component from points already in
  an imported cloud, without sending coordinates. The agent names the cloud, the component, an
  axis-aligned bounding box, and an optional subsampling step (keep every Nth matching point,
  default 1). Initial u/w values and fixed/free choices follow the FR-006 defaults. The request
  is all or nothing and capped at 10,000 targets. The response reports the number of targets
  created and their index range, and contains no coordinates. This complements the explicit
  batch in FR-006; it does not replace it.

**Persistence**

- **FR-013**: Agents MUST be able to save the fit setup to a file and load it back, in the
  existing fit setup file format. Loading replaces the current setup by default and appends only
  when explicitly requested.
- **FR-014**: The fitted geometry MUST persist through the existing model save capability. No
  separate export path is added.

**Behaviour and reporting**

- **FR-015**: Every tool MUST return an error result whenever the geometry engine reports an
  error during that call, even if the engine raised no exception. Errors left over from earlier
  calls MUST NOT be attributed to the current one.
- **FR-016**: Every error result MUST name the specific input at fault (index, parameter,
  component, or file) and the reason.
- **FR-017**: Fit results obtained through the tools MUST match those obtained by performing the
  same sequence of operations through OpenVSP's existing scripting interfaces. The tools add no
  fitting behaviour of their own beyond sequencing, validation, reporting, and choosing which
  cloud points become targets (FR-012).
- **FR-018**: Every tool's description MUST state its purpose, inputs, units (model units), and
  where it fits in the recommended workflow order. The single optimization pass MUST warn that
  one pass can stop short when the model starts far from the scan.
- **FR-019**: All tools MUST work in a headless session with no GUI.
- **FR-020**: Every Fit Model operation available in OpenVSP's scripting interfaces (reset,
  clear, variable, target, search, refine, distance, optimize, save, and load) MUST be reachable
  through at least one agent tool.

### Key Entities

- **Point Cloud**: an imported set of 3D points held as a model component, with an identifier,
  point count, and extent.
- **Fit Variable**: a model parameter the optimizer may change, identified by parameter and
  described by name, group, owning component, and current value.
- **Target Point**: a 3D coordinate the fitted surface should pass through. It belongs to exactly
  one fittable component and has a surface location (u, w), each coordinate marked fixed or free.
- **Fit Setup**: the current collection of fit variables and target points, which can be saved
  to and loaded from a file.
- **Fit Error**: the RMS distance from targets to their matched surface locations, in model units.
- **Fit Run**: the record of one converged-fit request: error after each pass, pass count, stop
  reason, and final variable values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Starting from a single body with length and fineness ratio perturbed by at least
  40%, an agent using only the tools recovers both values to within 0.1% of the truth.
- **SC-002**: A single-component fit (import cloud, add variables, add targets, fit, save) takes
  no more than 10 tool calls, not counting the calls used to build the initial geometry.
- **SC-003**: 100% of the Fit Model operations in OpenVSP's scripting interfaces are reachable
  through the agent tools.
- **SC-004**: For clouds of up to 1,000,000 points, no single tool response contains more than
  1,000 points or targets.
- **SC-005**: Every edge case listed above produces an error result that names the offending
  input. No call succeeds silently while the engine reports an error.
- **SC-006**: On a two-component model (fuselage and wing) sampled to a cloud and then perturbed,
  the tool-driven fit reduces the fit error by at least 90% from its starting value.

## Assumptions

- The agent, or an external pipeline, builds the initial coarse model with the existing geometry
  tools, and does any segmentation of the scan outside OpenVSP, as described in
  `docs/PointCloudSegmentationPlan.md`. Automatic segmentation is out of scope.
- The headless Fit Model interface already added to OpenVSP (reset, variables, targets,
  search/refine, distance, optimize, save/load) is complete and is the only fitting engine used.
  No changes to fitting mathematics are in scope.
- Fit Model's existing limits carry over: targets fit only the first surface of a component, and
  there are no per-target weights, robust loss, or progress reporting during a solve.
- Coordinates and errors are in the model's own units. No unit conversion is performed.
- One model is active per tool-server session, and the fit setup belongs to that model.
- Parameter identifiers are valid only within a session. Addressing by semantic path (for example
  "wing.sweep") belongs to the separate semantic-layer project and is out of scope here.
- Live GUI visualization of the fit is out of scope. It remains possible through the existing
  graphics-enabled facade but is not required.
- Point cloud import supports only the existing plain-text `x y z` format. Other scan formats
  must be converted externally.
