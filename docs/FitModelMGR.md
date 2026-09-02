# FitModelMgr: How Fit Model Optimization Works

## Scope

This document explains the core Fit Model optimizer implemented by:

See also:

- `docs/FitModelAPI.md` for the proposed public API surface around `FitModelMgr`
- `docs/PointCloudSegmentationPlan.md` for the recommended pre-fit target-generation workflow

- `src/geom_core/FitModelMgr.h`
- `src/geom_core/FitModelMgr.cpp`

It focuses on:

- how the least-squares problem is constructed
- what “constraints” mean in this context
- how target points relate to surface $(u,w)$ coordinates
- how optimization variables are assembled
- how residuals and Jacobians are computed

It does **not** describe GUI workflows (`FitModelScreen`) except where needed to understand data flow.

## High-level idea

Fit Model minimizes geometric mismatch between:

- a set of **fixed 3D target points** $\{\mathbf{p}_i\}$ (typically from a point cloud)
- the corresponding **matched points on OpenVSP surfaces** $\{\mathbf{s}_i(u_i,w_i)\}$

Each target point stores:

- target 3D coordinate $\mathbf{p}_i$ (`TargetPt::m_Pt`)
- target geometry ID (`TargetPt::m_MatchGeom`)
- surface parameters $(u_i, w_i)$ in normalized $[0,1]$ coordinates (`TargetPt::m_UW`)
- whether $u_i$ is **fixed** or **free** (`TargetPt::m_UType`)
- whether $w_i$ is **fixed** or **free** (`TargetPt::m_WType`)

The optimizer adjusts:

- selected OpenVSP parameters (“fit variables”, `FitModelMgrSingleton::m_VarVec`)
- optionally some of the $(u_i,w_i)$ values (when marked FREE)

so that matched surface points land as close as possible to the target 3D points.

## What “constraints” mean here

Fit Model uses nonlinear least squares. “Constraints” are implemented as **residual equations**.

For each target point $i$:

- define model point on surface: $\mathbf{s}_i(u_i,w_i)$
- define residual vector: $\mathbf{r}_i = \mathbf{s}_i(u_i,w_i) - \mathbf{p}_i$

This yields **3 scalar residuals per target**:

$$
\mathbf{r}_i =
\begin{bmatrix}
 r_{ix}\\
 r_{iy}\\
 r_{iz}
\end{bmatrix}
$$

The overall least-squares objective is:

$$
\min_{\mathbf{x}} \; \frac{1}{2}\sum_{i=1}^{N} \|\mathbf{r}_i(\mathbf{x})\|^2
$$

where $\mathbf{x}$ is the vector of optimization variables (OpenVSP parms and optional free $(u,w)$ components).

There are no explicit inequality constraints; bounds are enforced indirectly via:

- OpenVSP `Parm` min/max bounds for design variables
- clamping/wrapping $u,w$ to $[0,1]$ during optimization updates

## Core data flow

The Fit Model manager has two lists:

1. Fit variables (`m_VarVec`): vector of `ParmID` strings.
2. Target points (`m_TargetPts`): vector of `TargetPt*`.

Before optimization, `BuildPtrVec()` resolves:

- `Parm*` pointers for each `ParmID` (stored in `m_ParmPtrVec`)
- `Geom*` pointers for each target geometry (stored in `m_TargetGeomPtrVec`)
- surface periodicity flags (`TargetPt::m_UClosed`, `TargetPt::m_WClosed`) derived from `VspSurf::IsClosedU/W()`

These caches avoid repeated lookups inside the inner solver loop.

## UW coordinates and “nearest point” mapping

### What are $(u,w)$

OpenVSP surfaces are evaluated using normalized parameters $(u,w) \in [0,1]^2$.

In code, the matched 3D point is computed as:

- `const VspSurf* s = matchgeom->GetSurfPtr(0);`
- `vec3d ps = s->CompPnt01( u, w );`

So, each target point ultimately measures distance to surface 0 of its target geom.

### Finding nearest $(u,w)$ (search)

When you only have a 3D point $\mathbf{p}$ and a surface $\mathbf{s}(u,w)$, you need an initial guess for $(u,w)$.

`TargetPt::SearchUW(Geom* matchgeom)` performs this initial mapping. Behavior depends on fixed/free flags:

#### Case A: $u$ FREE, $w$ FREE

- Calls `VspSurf::FindNearest01( u, w, pt )` to find the nearest point on the surface in $(u,w)$.
- Compares the new nearest distance to the current stored $(u,w)$ distance; if the new one is worse, it keeps the old.

This is important for stability when a target is near multiple local minima (e.g., near seams on closed surfaces).

#### Case B: $u$ FREE, $w$ FIXED

- Holds $w$ constant.
- Builds a constant-$w$ curve: `s->GetW01ConstCurve( c, w )`.
- Finds nearest along the curve: `c.FindNearest01(u, pt)`.

#### Case C: $u$ FIXED, $w$ FREE

- Holds $u$ constant.
- Builds constant-$u$ curve: `s->GetU01ConstCurve( c, u )`.
- Finds nearest along the curve: `c.FindNearest01(w, pt)`.

#### Case D: $u$ FIXED, $w$ FIXED

No search; stored values are used.

### Refining $(u,w)$ (local improvement)

`TargetPt::RefineUW(Geom* matchgeom)` is similar but uses the current $(u,w)$ as a starting point:

- For FREE/FREE: `s->FindNearest01( u, w, pt, u0, w0 )`
- For FREE/FIXED and FIXED/FREE: passes starting guess to `VspCurve::FindNearest01(...)`

This is typically used after the geometry has changed due to parameter updates.

### Why Fit Model keeps $(u,w)$ in the optimization

A target point needs to “know” where it lies on the surface. But geometry changes during optimization.

Fit Model offers two strategies:

1. **Keep $(u,w)$ fixed** (treat mapping as part of the correspondence definition).
2. **Allow $(u,w)$ to vary** as part of optimization to improve correspondence.

Allowing $(u,w)$ to be free makes each target point act more like a “closest point” constraint during fitting.

That can improve robustness when initial $(u,w)$ guesses are poor, but it also increases degrees of freedom and can lead to sliding along a surface if fit variables are insufficient.

## Building the optimization variable vector

The solver variable vector $\mathbf{x}$ is assembled in a fixed order.

### Variable count

`UpdateNumOptVars()` computes:

$$
N_{\text{opt}} = N_{\text{parms}} + \sum_{i=1}^{N_{\text{targets}}} [u_i\text{ free}] + [w_i\text{ free}]
$$

This count is stored as `m_NumOptVars`.

### Packing order: `ParmToX(double* x)`

Variables are packed as:

1. All design variables (parms) in `m_VarVec` order.
2. For each target point in `m_TargetPts` order:
   - append $u_i$ if FREE
   - append $w_i$ if FREE

### Unpacking order: `XtoParm(const double* x)`

Unpacking uses the same order:

1. Set each `Parm*` to its corresponding entry.
2. For each target point:
   - overwrite $u_i$ if FREE
   - overwrite $w_i$ if FREE

After updating a FREE $u$ or $w$, it is normalized with:

- `Clamp01( value, periodicFlag )`

`Clamp01` behavior:

- if periodic (closed surface direction): wraps with `x - floor(x)`
- else clamps to `[0,1]`

This is the core “bound handling” for $(u,w)$.

## Residual computation (metrics)

The solver uses the callback `fcn(...)` which delegates to either:

- `FitModelMgr.CalcMetrics(x, fvec)` for residuals
- `FitModelMgr.CalcMetricDeriv(x, fvec, fjac)` for Jacobian

### Residual definition

`CalcMetrics` does:

1. Apply $\mathbf{x}$ to parms and target $(u,w)$ via `XtoParm(x)`.
2. Update vehicle geometry: `VehicleMgr.GetVehicle()->Update(false)`.
3. For each target point $i$:
   - compute $\Delta_i = \mathbf{s}_i(u_i,w_i) - \mathbf{p}_i$ via `TargetPt::CalcDelta(Geom*)`
   - store into residual vector `y` as:
     - `y[3*i + 0] = Δx`
     - `y[3*i + 1] = Δy`
     - `y[3*i + 2] = Δz`

So the residual vector length is:

$$
M = 3\,N_{\text{targets}}
$$

### Distance metric shown in GUI

`UpdateDist()` computes RMS distance:

$$
\text{DistMetric} = \sqrt{\frac{1}{N}\sum_i \|\Delta_i\|^2}
$$

This is not the optimized objective itself (which is sum of squares), but it is directly related and is easier to interpret.

## Jacobian (derivative) computation

The Jacobian is an $M \times N$ matrix where:

- $M = 3 N_{\text{targets}}$
- $N = N_{\text{opt}}$

`CalcMetricDeriv` builds it in two parts.

### Part 1: derivatives w.r.t. design variables (finite difference)

For each parm variable $x_j$ (only the design-variable subset, not free $u,w$):

- compute step size:
  - `eps = sqrt(machine_precision)`
  - `dx = eps * abs(x0)` or `dx = eps` if `x0==0`
- perturb only that variable: `xp[j] = x0 + dx`
- compute new residuals `fprm = f(xp)`
- finite-difference column:

$$
\frac{\partial f}{\partial x_j} \approx \frac{f(x + dx\,e_j) - f(x)}{dx}
$$

This yields an approximate derivative of each residual component with respect to each design variable.

After finite differences, geometry is restored to original $x$:

- `XtoParm(x)`
- `VehicleMgr.GetVehicle()->Update(false)`

### Part 2: derivatives w.r.t. free $(u,w)$ (analytic)

For free $(u,w)$ variables, it uses surface tangents:

- $\partial \mathbf{s}/\partial u$ via `VspSurf::CompTanU01(u,w)`
- $\partial \mathbf{s}/\partial w$ via `VspSurf::CompTanW01(u,w)`

Code paths:

- `TargetPt::CalcDerivU(Geom*)` returns $\partial \mathbf{s}/\partial u$
- `TargetPt::CalcDerivW(Geom*)` returns $\partial \mathbf{s}/\partial w$

Then it fills the Jacobian columns for free $u_i$ and/or $w_i$:

- if $u_i$ FREE, Jacobian column = tangent in $u$ direction
- if $w_i$ FREE, Jacobian column = tangent in $w$ direction

This makes the $u,w$ part of the Jacobian exact (given the surface evaluation), while design-variable part is approximate.

## Solving the nonlinear least squares problem

`FitModelMgrSingleton::Optimize()` sets up `cminpack`’s Levenberg–Marquardt solver `lmder1`.

Dimensions:

- $m = 3\,N_{\text{targets}}$
- $n = N_{\text{opt}}$

Arrays allocated:

- `x[n]`: current variable values
- `y[m]`: residuals
- `fjac[m*n]`: Jacobian
- `ipvt[n]`, `wa[lwa]`: solver work arrays

Tolerance:

- `tol = sqrt(machine_precision)`

Call:

- `info = lmder1( fcn, nullptr, m, n, x, y, fjac, ldfjac, tol, ipvt, wa, lwa );`

After solver:

- apply final `x` back to geometry: `XtoParm(x)`
- force surface update: `VehicleMgr.GetVehicle()->ForceUpdate( GeomBase::SURF )`

The return value `info` comes from `cminpack` and indicates convergence status or invalid input.

## Practical notes and gotchas

### Surface index hard-coded to zero

Target matching uses `matchgeom->GetSurfPtr(0)` everywhere. Multi-surface geoms are treated as if surface 0 is the only surface.

### Correspondence can drift if $(u,w)$ are free

If you free $u$ and/or $w$ for many targets but have too few design variables, the solver can reduce distance by sliding target correspondences along the surface rather than changing geometry.

Mitigations:

- keep one parameter fixed where appropriate (station constraints)
- use fewer FREE targets
- fit in stages (coarse to fine)

### Updating $(u,w)$ outside optimization

The explicit `SearchTargetUW()` and `RefineTargetUW()` steps re-establish correspondence as geometry changes. Many workflows do:

1. set initial model
2. `SearchTargetUW()`
3. run `Optimize()`
4. `RefineTargetUW()`
5. run `Optimize()` again

### Empty-target edge case

`UpdateDist()` divides by target count. If `N_targets==0` this must be guarded to avoid divide-by-zero.

### Parameter scaling and conditioning

Design-variable derivatives are computed by finite differences using `dx = eps * |x0|`.

If parameters have very different magnitudes, solver conditioning can be poor.

Mitigations (future):

- explicit parameter scaling
- normalize variables (solve in scaled space)
- adjust finite-difference step per parameter

## Glossary

- **target point**: fixed 3D point you want the model to match
- **matched point**: point on OpenVSP surface at stored $(u,w)$
- **residual**: difference vector between matched point and target point
- **design variable**: OpenVSP `Parm` chosen to be adjusted
- **free $(u,w)$**: surface parameters included as optimization variables
- **closed/periodic direction**: surface parameter where 0 and 1 represent the same location
