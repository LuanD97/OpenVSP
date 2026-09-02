# Point Cloud Segmentation Plan Before Fit Model API

## Purpose

This document lays out a practical external workflow for preparing an aircraft point cloud **before** sending targets into the proposed Fit Model API described in `docs/FitModelAPI.md`.

See also:

- `docs/FitModelAPI.md` for the proposed external API used after segmentation
- `docs/FitModelMGR.md` for the internal optimizer behavior that the generated targets will drive

Goal:

- start with raw or semi-raw aircraft scan data
- clean and segment the cloud outside OpenVSP
- extract structured geometric information
- generate a stable, sparse, component-aware target set for `FitModelMgr`

The main idea is simple:

**do not send raw scan points directly into Fit Model**.

Instead:

1. preprocess and align the scan
2. segment the cloud into aircraft components
3. extract section-based landmarks and contours
4. convert those into a sparse set of fit targets and initial model parameters
5. use the Fit Model API only for final parametric refinement

## Why segmentation is needed

Fit Model minimizes point-to-surface residuals. It does not:

- infer aircraft topology from an unstructured cloud
- know which points belong to fuselage vs wing vs tail
- know where to place section breaks
- know which points should constrain planform vs local airfoil vs fuselage thickness
- apply robust priors against scan noise, occlusion, or asymmetric damage

If a raw cloud is used directly, typical failure modes are:

- wrong correspondences
- too many noisy targets
- overfitting local scan defects
- underconstrained global shape
- solver drift via free $(u,w)$ instead of actual geometry improvement

Segmentation fixes this by converting a raw geometric observation into a set of **meaningful constraints**.

## Desired end state

External pipeline should produce three outputs:

### 1. Clean aligned cloud
A cloud in a consistent aircraft body coordinate frame:

- $x$: longitudinal axis
- $y$: spanwise axis
- $z$: vertical axis

### 2. Structured component data
For example:

- fuselage centerline and cross-sections
- wing left/right section slices
- horizontal tail sections
- vertical tail sections
- nacelle or pod centerlines and section radii
- key landmarks such as nose tip, wing root, wing tip, tail root, tail tip

### 3. Fit-ready targets
A sparse target set for the Fit Model API, where each target point already knows which component it is intended to constrain.

Example target record:

```json
{
  "xyz": [12.4, 8.1, 1.7],
  "component": "wing_left",
  "target_geom": "wing_main",
  "role": "section_contour",
  "station": 0.62,
  "u_type": "free",
  "w_type": "free"
}
```

## Recommended external tooling

Python stack is likely best for iteration speed.

Suggested tools:

- `Open3D` for point-cloud IO, filtering, normals, downsampling, clustering
- `NumPy` for array work
- `SciPy` for optimization, interpolation, smoothing
- `scikit-learn` for PCA, clustering, nearest-neighbor work
- `PyVista` or `trimesh` for mesh and visualization helpers

Optional:

- `PCL` if existing codebase already uses it
- `CGAL` if strong geometry processing is needed
- `networkx` for graph-based segmentation/proximity grouping

## Pipeline overview

A robust pipeline has six stages:

1. ingest and cleanup
2. registration and axis normalization
3. coarse component segmentation
4. section extraction and landmark generation
5. initial OpenVSP model parameter estimation
6. target generation for Fit Model API

## Stage 1: ingest and cleanup

### Inputs

Potential input sources:

- LiDAR point cloud
- photogrammetry reconstruction
- mesh converted to point sample
- `.ply`, `.las`, `.xyz`, `.obj`, `.stl`, or custom source

### Operations

Recommended first-pass cleanup:

1. remove obvious environment geometry
   - floor
   - tripod
   - hangar walls
   - support rigs
2. unify units
   - meters strongly preferred
3. remove duplicate points
4. apply voxel downsampling
5. estimate normals
6. remove isolated outliers
   - statistical outlier filter
   - radius outlier filter

### Suggested output

- `cloud_clean.ply`
- `cloud_clean_downsampled.ply`

### Notes

Keep both:

- a medium-density cloud for segmentation
- a lower-density cloud for iterative experiments

Do not downsample so hard that section contours collapse.

## Stage 2: registration and axis normalization

This stage puts the aircraft into a stable body frame.

### Objectives

Determine:

- longitudinal direction
- span direction
- vertical direction
- approximate symmetry plane

### Methods

#### PCA-based rough orientation

Use principal components for a first guess:

- largest variance axis often approximates fuselage length
- second axis often approximates span
- third axis often approximates thickness/height

This is useful but not always enough because:

- swept wings distort PCA
- asymmetric scan coverage can bias axes
- gear or support structures can pollute modes

#### Symmetry-plane estimation

For conventional aircraft, find approximate mirror plane.

Possible methods:

- search candidate planes that maximize mirrored point overlap
- minimize point-to-mirrored-cloud distance
- estimate via RANSAC + symmetry objective

This step is important because many downstream features assume left/right symmetry.

#### Ground-plane removal if present

If the aircraft was scanned in scene, detect and remove floor plane first.

### Expected output

- rigid transform from raw cloud to aircraft body frame
- symmetry plane estimate
- aligned cloud `cloud_body_frame.ply`

## Stage 3: coarse component segmentation

Segment major aircraft components before any parametric fitting.

Minimum useful component labels:

- fuselage
- wing_left
- wing_right
- htail_left
- htail_right
- vtail
- nacelle_* or pod_*
- other / unknown

### Strategy

Use a hybrid of:

- geometry
- orientation
- connectivity
- symmetry
- spatial priors

### Recommended sequence

#### 3.1 Detect fuselage candidate

Fuselage often has:

- longest longitudinal extent
- high continuity along body axis
- approximately elliptical cross-sections in normal slices
- lower span-to-length ratio than wings

Heuristics:

- slice cloud normal to longitudinal axis
- look for sequence of slices with compact near-elliptic contours
- track centroid continuity across slices

#### 3.2 Detect planar lifting surfaces

Wings and tails often show:

- large local planarity
- strong principal in-plane directions
- small thickness relative to chord/span

Useful features:

- local surface normals
- curvature
- local PCA eigenvalue ratios
- distance from symmetry plane
- attachment region relative to fuselage

#### 3.3 Split wing from tail

Use longitudinal location:

- main wing near mid-body
- horizontal tail aft
- vertical tail aft and vertical

#### 3.4 Detect nacelles and pods

Look for:

- compact cylindrical or capsule-like clusters
- attached below or beside wing/fuselage
- local circular cross-sections

### Candidate algorithms

- DBSCAN for disconnected or weakly connected clusters
- region growing on normals
- graph segmentation using adjacency + normal compatibility
- RANSAC-like primitive hints for cylinders or planar sheets

### Output schema

Recommended file:

- `segments/labels.parquet` or `segments/labels.csv`

Fields:

- point index
- xyz
- normal
- segment id
- component label
- confidence

## Stage 4: section extraction and landmark generation

This is the most important stage for OpenVSP fitting.

Raw segments are still too dense and too unstructured. Convert each component into section-based descriptors.

## Fuselage extraction plan

### Objectives

Extract:

- fuselage centerline
- fuselage stations along $x$
- cross-section contours per station
- width and height per station
- optional ellipse or superellipse fit per section

### Procedure

1. determine fuselage centerline seed from slice centroids
2. smooth centerline using spline fit
3. reslice fuselage normal to centerline direction
4. fit contour or ellipse in each slice
5. reject bad slices with too few points or heavy occlusion

### Outputs

- `fuselage/centerline.csv`
- `fuselage/sections/section_###.csv`
- `fuselage/section_summary.csv`

Section summary fields:

- station
- center x,y,z
- width
- height
- area
- contour quality
- slice point count

### OpenVSP handoff use

Use section summaries to initialize:

- fuselage length
- fuselage xsec locations
- width and height distribution
- nose/tail taper trend

Use section contour points as fit targets later.

## Wing extraction plan

### Objectives

Extract:

- root and tip region
- span axis
- left/right separation
- section slices along span
- leading edge curve
- trailing edge curve
- chord length and twist by station
- approximate airfoil section contour

### Procedure

1. isolate left and right wing clouds
2. estimate span direction in each half
3. define span stations from root to tip
4. slice with planes normal to local span direction
5. in each slice:
   - project points to section plane
   - fit 2D contour
   - detect LE and TE as extrema
   - estimate chord line
   - estimate section twist and thickness
6. smooth LE/TE and twist distributions across stations

### Outputs

- `wing_left/sections/*.csv`
- `wing_right/sections/*.csv`
- `wing_left/station_summary.csv`
- `wing_right/station_summary.csv`
- `wing_left/leading_edge.csv`
- `wing_left/trailing_edge.csv`
- same for right wing

### OpenVSP handoff use

Use summaries to initialize:

- span
- root chord
- tip chord
- sweep
- dihedral
- twist
- wing break positions for multi-section wing

Use section contour points and LE/TE points as fit targets.

## Horizontal tail extraction plan

Same pattern as wing, but aft and smaller.

Outputs:

- tail section slices
- tail LE/TE curves
- span/chord/twist summaries

These are useful for initializing a dedicated `WING` geom used as horizontal tail.

## Vertical tail extraction plan

Vertical tail behaves like a rotated lifting surface.

Extract:

- root and tip
- vertical span axis
- section slices in appropriate local plane
- LE/TE curves
- sweep and chord trends

Use for initializing a vertical `WING`-based tail or equivalent parametric setup.

## Nacelle / pod extraction plan

### Objectives

Extract:

- centerline
- radius or width/height profile
- inlet and outlet stations
- mounting position and axis

### Procedure

1. detect local cylindrical segment
2. fit centerline spline or axis line
3. slice normal to centerline
4. estimate radius or section profile

### OpenVSP handoff use

Initialize:

- `POD` or `FUSELAGE`-like body
- length
- diameter profile
- location and orientation

## Stage 5: initial OpenVSP model estimation

Before using Fit Model, create a coarse parametric aircraft model from extracted summaries.

This stage should not yet rely on point-to-surface fitting. It should be mostly deterministic.

### Fuselage initialization

From section summary:

- choose number of xsecs
- assign xsec positions
- set width/height trend
- choose cross-section type family

### Wing initialization

From wing station summary:

- choose one-, two-, or multi-section wing
- set span
- set sweep/dihedral/twist
- set root/tip chords
- place wing relative to fuselage

### Tail initialization

Same pattern.

### Nacelle initialization

From centerline and radius profile:

- choose pod or fuselage-like geom
- set length and diameter curve
- position and orient in aircraft frame

### Why this matters

Fit Model works best when starting close to the right topology and rough dimensions.

It should refine:

- chord
- twist
- thickness trends
- fuselage widths/heights
- relative placement

It should not be asked to discover:

- that a wing exists
- where the fuselage is
- how many sections are needed

## Stage 6: target generation for Fit Model API

Convert structured component outputs into sparse fit targets.

## Principles for target generation

### Use sparse, structured targets

Good targets:

- fuselage contour points at selected stations
- wing LE/TE points at selected span stations
- wing section contour points
- tail section contour points
- nacelle section contour points
- a few global landmarks

Bad targets:

- every raw point
- noisy underside points with poor coverage
- thick clusters around reflective scan artifacts

### Keep component association explicit

Each target should already know which OpenVSP geom it is intended to constrain.

Example mapping:

- fuselage contour targets -> fuselage geom
- main wing section targets -> main wing geom
- horizontal tail targets -> htail geom
- nacelle contour targets -> nacelle geom

### Use multiple target roles

Recommended role labels:

- `section_contour`
- `leading_edge`
- `trailing_edge`
- `tip`
- `root`
- `centerline`
- `landmark`

This helps debugging and future weighting.

## Suggested target densities

### Fuselage

- 20 to 50 stations
- 8 to 24 contour points per station

### Wing

- 10 to 30 span stations per side
- 8 to 20 contour points per station
- explicit LE and TE point at each station

### Tail

- fewer stations than wing
- same contour strategy

### Nacelles

- 10 to 20 stations
- 8 to 16 contour points per station

This usually yields hundreds to low thousands of total targets, which is far more manageable than millions of raw points.

## Guidance for U/W free vs fixed target design

This segmentation stage should also prepare intended correspondence strategy.

### Use both FREE when

- target point only needs nearest match on that surface
- local contour point is generic and does not correspond to a fixed station or seam

### Fix one coordinate when

- target should stay on a known station-like slice
- wing target belongs to a known span station
- fuselage target belongs to a known longitudinal station

### Fix both rarely

Only when correspondence is already known very confidently.

Over-fixing can make optimization brittle if initial model is not close enough.

## Proposed intermediate data products

A useful external directory layout:

```text
project/
  raw/
    aircraft_raw.ply
  clean/
    cloud_clean.ply
    cloud_body_frame.ply
  segments/
    labels.parquet
    components.json
  fuselage/
    centerline.csv
    section_summary.csv
    sections/
  wing_left/
    station_summary.csv
    leading_edge.csv
    trailing_edge.csv
    sections/
  wing_right/
    ...
  htail/
    ...
  vtail/
    ...
  nacelles/
    ...
  fit/
    initial_model.json
    fit_targets.json
    fit_vars.json
```

## Example `fit_targets.json` schema

```json
[
  {
    "xyz": [10.2, 0.0, 1.1],
    "component": "fuselage",
    "target_geom": "fuselage_main",
    "role": "section_contour",
    "station": 0.35,
    "u": 0.5,
    "u_type": "free",
    "w": 0.5,
    "w_type": "free",
    "confidence": 0.93
  }
]
```

Useful optional fields:

- `weight`
- `confidence`
- `symmetry_group`
- `source_section_id`
- `side`
- `notes`

## Quality control and diagnostics

Before Fit Model API is called, verify:

### Cloud-level checks

- units correct
- body axes reasonable
- symmetry plane plausible
- no large environmental junk remains

### Segment-level checks

- every major component present
- no obvious fuselage/wing cross-labeling
- left/right split plausible
- section extraction coverage adequate

### Target-level checks

- no huge target density imbalance by component
- target coordinates finite
- target count manageable
- target geom mapping complete

### Visualization requirement

Strongly recommended:

- color by segment
- overlay extracted centerlines and section planes
- preview sampled fit targets over cloud

This visualization loop will catch most pipeline mistakes earlier than the solver will.

## Failure modes and mitigations

## Failure mode: incomplete scan coverage

Examples:

- missing underside
- missing wing tip
- shadowed root sections

Mitigations:

- use symmetry assumptions
- mark low-confidence sections
- avoid oversampling missing regions
- use stronger initial parametric priors there

## Failure mode: asymmetry from real object or scan error

Examples:

- damaged wing
- sagged control surface
- scan registration drift

Mitigations:

- decide early whether target model should be symmetric or as-scanned
- if symmetric model desired, symmetrize before target generation
- if as-scanned desired, keep component-specific asymmetry but expect more fit variables

## Failure mode: noisy trailing edges and thin surfaces

Mitigations:

- smooth section contours
- use LE/TE centerlines rather than raw point extremes alone
- avoid over-weighting TE points

## Failure mode: topology ambiguity

Examples:

- wing-body fairing merged into fuselage cloud
- engine pylon blended into nacelle and wing

Mitigations:

- introduce `unknown` or `blend` labels during segmentation
- exclude ambiguous blend zones from first fit pass
- fit clean component cores first, then refine

## Recommended staged fitting workflow

Best practice after segmentation:

### Pass 1: coarse deterministic model build

- build fuselage, wing, tail, nacelles from extracted summaries
- no optimization yet or only minimal refinement

### Pass 2: component-local fit

- fit fuselage using fuselage-only targets and vars
- fit wing planform and section vars using wing-only targets
- fit tails similarly

### Pass 3: coupled global fit

- unlock component placement vars
- use combined sparse target set
- run full Fit Model solve

### Pass 4: optional densification

- add more contour targets only after coarse alignment is stable
- avoid jumping directly to dense target sets

## Suggested first implementation priority

If building this pipeline from scratch, do it in this order:

1. body-frame registration
2. fuselage segmentation and section extraction
3. wing left/right segmentation and section extraction
4. initial OpenVSP fuselage + wing model creation
5. sparse target generation
6. Fit Model API integration
7. tails and nacelles
8. denser section and contour refinement

This gives usable aircraft reconstruction sooner.

## Success criteria

Segmentation stage is successful when it produces:

1. a stable aligned aircraft cloud
2. major component labels with reasonable confidence
3. section summaries for fuselage and wing at minimum
4. a coarse OpenVSP model close enough to visualize plausibly
5. a sparse target set that reduces RMS after Fit Model optimization
6. repeatable results across similar scans

## Summary

Best workflow is:

- raw cloud -> clean cloud
- clean cloud -> aligned body frame
- aligned cloud -> labeled aircraft components
- labeled components -> section summaries and landmarks
- summaries -> initial OpenVSP model
- selected contour/landmark points -> Fit Model targets
- Fit Model -> final parametric refinement

That keeps the segmentation stage responsible for **topology and correspondence**, and Fit Model responsible for **continuous parametric refinement**.