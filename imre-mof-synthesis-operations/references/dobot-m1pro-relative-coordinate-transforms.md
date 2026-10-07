# Dobot M1 Pro relative XY moves and R-frame transforms

Use this reference when an operator requests a relative Cartesian move, especially wording such as “in this R-coordinate direction,” “tool-local X-/Y-,” or “30 mm diagonally.”

## Resolve the frame and distance convention

Before motion, distinguish these independent choices:

1. **Base/robot frame** — requested `ΔX, ΔY` are added directly to the measured controller pose.
2. **Tool/local frame at R** — rotate the requested local vector into the base frame before calculating the target.
3. **Per-axis amount** — “X−30 and Y−30” means a 42.426 mm diagonal.
4. **Total diagonal distance** — “30 mm toward X−/Y−” means local components `(-30/√2, -30/√2)`.

If wording materially leaves these choices ambiguous, ask the operator to choose rather than silently selecting a convention. Preserve `Z` and `R` unless explicitly changed.

## Forward transform: local to base

For controller pose `(X0, Y0, R)` and local displacement `(dxL, dyL)`, with `R` in degrees:

```text
dxB = cos(R)·dxL − sin(R)·dyL
dyB = sin(R)·dxL + cos(R)·dyL
X1  = X0 + dxB
Y1  = Y0 + dyB
R1  = R
```

For a total distance `d` along a normalized local direction `(ux, uy)`:

```text
n   = √(ux² + uy²)
dxL = d·ux/n
dyL = d·uy/n
```

Do the calculation with a deterministic math tool and retain full precision in the protocol target; round only for the operator-facing summary.

## Inverse transform: observed base displacement to local R frame

Given measured start and end poses:

```text
dxB = X1 − X0
dyB = Y1 − Y0

dxL =  cos(R)·dxB + sin(R)·dyB
dyL = −sin(R)·dxB + cos(R)·dyB
```

Also calculate rather than assume:

```text
distance       = √(dxB² + dyB²)
base heading   = atan2(dyB, dxB)
heading offset = base heading − R
```

Do not describe an observed displacement as exactly 30 mm merely because that was the intended nominal move. Report the measured/calculated distance and any discrepancy.

## Safe execution pattern

1. Obtain a fresh edge-mediated pose; never calculate a relative target from retained PUDA state alone.
2. Confirm `idle`, healthy edge, empty pending/ack-pending consumers, and a fresh overhead safety frame. Use the wrist view as additional local evidence when moving near labware.
3. Calculate the absolute target and pass it through the driver workspace validator before dispatch.
4. Record the frame convention and transform in the one-command protocol description.
5. Use `safe_move` and remember it may lift to travel Z, translate/rotate, then descend rather than tracing a direct low-Z line.
6. Independently query the resulting pose and verify state, edge health, queues, and post-motion images.
7. When asked to “move back,” restore the exact independently verified prior pose, not a rounded inverse or a newly recomputed approximation.

## Worked calibration example

From `(239.5, -77.5, R=-43.5°)`, an observed endpoint `(267.5, -90.5, R=-43.5°)` has:

```text
base delta      = (+28, -13) mm
actual distance = 30.870698 mm
base heading    = -24.904769°
local R delta   = (+29.259092, +9.844061) mm
R change        = 0°
heading offset  = +18.595231° relative to R
```

The exact directional representation is therefore:

```text
X1 = X0 + 30.870698·cos(R + 18.595231°)
Y1 = Y0 + 30.870698·sin(R + 18.595231°)
R1 = R
```

This is a worked transform/calibration example, not a reusable absolute target.

## Operator-confirmed R-relative calibrated vector

A later operator-confirmed transform established this reference displacement:

```text
reference pose: Rref = -17.049999°
base vector at Rref: vref = (+30.5, +1.0) mm
magnitude: 30.516389 mm
```

To apply **this calibrated transformation** at a different current orientation `Rcur`, rotate the complete reference vector by the orientation difference; do not replace it with a pure `30·(cos Rcur, sin Rcur)` vector:

```text
θ   = Rcur − Rref
dxB = cos(θ)·30.5 − sin(θ)·1.0
dyB = sin(θ)·30.5 + cos(θ)·1.0
X1  = X0 + dxB
Y1  = Y0 + dyB
R1  = Rcur
```

Confirmed application at `Rcur=-77.43°`:

```text
θ          = -60.380001°
base delta = (+15.943805102, -26.020089909) mm
start      = (240.5, -77.5)
endpoint   = (256.443805102, -103.520089909)
```

The controller independently reported `(256.443817, -103.520088, Z=50, R=-77.43)`, within controller precision, and the operator explicitly confirmed the transformation as correct.

A second application at a substantially different orientation validated the same rotation rule:

```text
Rcur       = -139.169998°
θ          = -122.119999°
base delta = (-15.369737742, -26.363254005) mm
start      = (240.5, -77.5)
endpoint   = (225.130262258, -103.863254005)
```

The controller independently reported `(225.130264, -103.863251, Z=50, R=-139.169998)`, within controller precision. Because this transformed endpoint was above an occupied centrifuge, execution used a target-local staging check at `Z=100` before descending to `Z=50`. A later request to descend to `Z=25` required a separate full-pose operator clearance confirmation; correct XY transform math does not prove low-Z physical clearance.

Two positive-R applications confirmed that the same calibrated-vector rule remains valid across quadrants:

```text
Rcur       = +41.549999°
θ          = +58.599998°
base delta = (+15.037243901, +26.554308424) mm
start      = (240.5, -77.5)
endpoint   = (255.537243901, -50.945691576)
measured   = (255.537247, -50.945690, Z=50, R=41.549999)

Rcur       = +100.349998°
θ          = +117.399997°
base delta = (-14.923907427, +26.618170243) mm
start      = (240.5, -77.5)
endpoint   = (225.576092573, -50.881829757)
measured   = (225.576096, -50.881828, Z=50, R=100.349998)
```

For both applications, use the same operational pattern: independently verify the low-Z start pose, calculate with full precision, stage the transformed X/Y/R at `Z=100`, inspect fresh target-local wrist and overhead frames, then descend to `Z=50` and independently verify. Any later request to descend below the inspected `Z=50` endpoint is a **new low-clearance operation**, even when only Z changes. Obtain fresh pose/state/queue/camera evidence and separate operator confirmation when occupied-rotor clearance remains hidden. Preserve the measured X/Y/R exactly while lowering; do not recompute or round the transform endpoint.

## Radially normalizing transformed XY targets

When an operator asks to change an existing transformed endpoint set to an exact diagonal XY distance from a shared center while preserving each endpoint's direction, rescale each center-relative vector rather than recomputing from rounded angles:

```text
dx = X − Cx
dy = Y − Cy
s  = requested_radius / √(dx² + dy²)
dx_new = s·dx
dy_new = s·dy
X_new  = Cx + dx_new
Y_new  = Cy + dy_new
```

Use a deterministic math tool, preserve full source precision, and verify `√(dx_new² + dy_new²)` equals the requested radius within the chosen numerical tolerance. Report both the new deltas and absolute XY coordinates so the operator can audit the center convention.

If asked to plot the recalculated positions, produce an equal-aspect XY plot containing the shared center, the requested-radius circle, radial lines, holder labels, coordinates, axis units, and an explicit statement that numbering follows the source scan convention. Verify the rendered artifact for clipped or overlapping labels before delivery. For headless plotting, select a non-interactive renderer such as Matplotlib `Agg`; this is preferable to relying on a GUI backend.

Do not treat recalculated geometry as a new physical calibration or active robot target automatically. Keep it analysis-only until the operator explicitly authorizes registration or motion, and retain the original scan/calibration as provenance.

### Wording rule

- **“Use this transformation”** means rotate and preserve the calibrated vector above, including its measured `30.516389 mm` magnitude and `+1 mm` cross-axis component.
- **“Exactly 30 mm along current R”** means the pure normalized vector `(30 cos R, 30 sin R)`.
- **“Make these transformed XYs exactly 30 mm from center”** means radially normalize the existing center-relative vectors to 30 mm while preserving their individual directions.
- If the request combines incompatible conventions and the intended meaning is not established by the replied-to context, calculate the candidate endpoints and ask before motion. Once the operator has explicitly confirmed one convention for the active workflow, reuse it consistently.