# Marble Factory — Mechanical & Mesh Validation

**When:** 2026-11-05 America/Denver  
**Status:** Unprinted prototype. Computational checks only. Physical rolling and snap-fit remain untested.

## Default route (the playable circuit)

Lift chute (J0) → S160 → CR → S160 → CR → S160 → S80 → CR → S160 → inlet → lift sump.

Joints: J0(−80,0) → J1(−240,0) → J2(−320,80) → J3(−320,240) → J4(−240,320) → J5(−80,320) → J6(0,320) → J7(80,240) → J11(80,80) → inlet.

Every joint preserves heading or turns 90° with a swept R=80 corner. There are no sharp 90° V-channel kinks. Track slope is 20 mm drop per 160 mm (7.13°), chosen so the nest slope matches the 7° exit chute and J11 lands 8.2 mm above the inlet end (7.96° inlet).

Switch, merge, and spinner modules are **not** in this circuit. Their STLs are included as optional extras without a verified layout of their own.

## Checks that passed (exact)

- **Mesh quality:** 32/32 unique parts are single-component, positive-volume, kernel-watertight Manifold solids. Print envelopes ≤ 330×320×325 mm (largest: `lift_housing_back` 294×267.5×52 mm).
- **Heading continuity:** 8/8 default joints match outgoing heading of the previous module to incoming heading of the next.
- **Slopes:** default-loop ball-centre path, 247 samples, drop 158.2 mm, **0 uphill** samples (>0.15 mm). Lift 2D log: 406 steps, second-nearest paddle gap ≥ 31.05 mm, paddles cleared at wheel angle 88°.
- **Chute nest:** `track_straight_160[0] × lift_housing_back` intersection = **0.0 mm³**. The nest is a low keel in the V floor (below the ball) with a clearance fit, rooted into the chute on the lift side of J0 so the housing stays one piece.
- **Inlet × front plate** and **inlet × last return straight** and **inlet × crank** (catalogued pose and 15° crank sweep through 360°): 0 mm³.
- **Shaft seating:** axle × both journals, both wheel hexes, and crank (0°/60° hex) = 0 mm³.
- **Wheel motion:** both halves vs housing back, housing front, and pawl at 20° steps through 360° = **0 mm³** at every step.
- **Synchronized 3D carry:** ball placed at each selected 2D-sim centre with the wheel rotated to the **same** angle `w`. 165 samples (every ~3° on the carry, every ~0.5–1° near pickup w∈[−115,−75] and release w∈[70,100]). Ball radius used: 17.15 mm (0.35 mm shrink so tangent V/paddle contact is not counted as a collision). **max vs housing = 0.0 mm³; max vs wheel = 0.0 mm³.** This does **not** by itself prove the paddle pushes the ball — the 2D contact model does — it proves the shrinking ball does not bury itself in the hub, guide, or a second paddle at those poses.
- **Default-loop ball clearance:** 87 samples along the 247-point path (including junction endpoints) vs every placed track, inlet, and housing solid. Hits above 20 mm³: **0**.
- **Slicing:** 32/32 unique STLs produced non-empty PrusaSlicer 2.7.4 toolpaths on the generic 0.4/0.20 PLA profile.

## What this still does not prove

- Physical rolling, friction, and printed snap-fit (0.5 mm peg/socket, 0.2 mm/flat hex, clip).
- That a real ball is *driven* rather than merely cleared (3D test used a shrunken sphere; 2D sim is the pickup/push evidence).
- Child safety. Viewing slots are 6 mm wide. The inlet must stay 35 mm+ to pass the ball, so fingers can enter; the inlet chute is a 59 mm tunnel, not a certified guard. Pinch risk remains at the wheel. Not a certified toy.
- Optional switch / spinner / merge as a working alternate circuit — they were not given a verified layout.

## First print

`fit_coupon`, then the lift-only set on `lift_test_base` (both housings, two wheel halves, axle, crank, clip, pawl, `stand_J11_h025`, inlet, 1–2 balls). Confirm pickup, carry, release, pawl, and clip before printing the tile grid and tracks.

## Final kernel mesh stats (Manifold, no vertex-weld)

| Part | Qty | Faces | Verts | Volume cm³ | Watertight | Extents mm |
|------|----:|------:|------:|-----------:|:----------:|------------|
| `track_straight_160` | 4 | 978 | 491 | 206.31 | yes | 160.0 × 76.0 × 70.0 |
| `track_straight_80` | 1 | 962 | 483 | 103.30 | yes | 80.0 × 76.0 × 60.0 |
| `track_corner_right` | 3 | 4452 | 2228 | 162.15 | yes | 118.0 × 118.0 × 70.0 |
| `track_corner_left` | 1 | 4448 | 2226 | 162.24 | yes | 118.0 × 118.0 × 70.0 |
| `track_switch_Y` | 1 | 5954 | 2977 | 609.16 | yes | 240.0 × 156.0 × 102.0 |
| `track_spinner` | 1 | 1438 | 721 | 258.78 | yes | 160.0 × 76.0 × 70.0 |
| `track_merge_Y` | 1 | 6690 | 3347 | 375.18 | yes | 160.0 × 156.0 × 102.0 |
| `lift_inlet_chute` | 1 | 346 | 175 | 109.93 | yes | 58.7 × 76.0 × 50.0 |
| `switch_gate` | 1 | 2124 | 1064 | 97.37 | yes | 120.0 × 132.0 × 76.2 |
| `spinner_rotor` | 1 | 940 | 472 | 20.87 | yes | 60.0 × 60.0 × 63.0 |
| `spinner_post` | 2 | 152 | 78 | 4.80 | yes | 14.0 × 10.0 × 45.2 |
| `spinner_retainer` | 1 | 116 | 60 | 12.12 | yes | 16.0 × 70.0 × 35.4 |
| `stand_J0_h175` | 1 | 1276 | 640 | 127.51 | yes | 40.0 × 40.0 × 184.5 |
| `stand_J1_h155` | 1 | 1276 | 640 | 113.39 | yes | 40.0 × 40.0 × 164.5 |
| `stand_J2_h135` | 1 | 1276 | 640 | 99.28 | yes | 40.0 × 40.0 × 144.5 |
| `stand_J3_h115` | 1 | 1276 | 640 | 85.16 | yes | 40.0 × 40.0 × 124.5 |
| `stand_J4_h095` | 1 | 1276 | 640 | 71.05 | yes | 40.0 × 40.0 × 104.5 |
| `stand_J5_h075` | 1 | 1276 | 640 | 56.93 | yes | 40.0 × 40.0 × 84.5 |
| `stand_J6_h065` | 1 | 1276 | 640 | 49.88 | yes | 40.0 × 40.0 × 74.5 |
| `stand_J7_h045` | 1 | 1276 | 640 | 35.76 | yes | 40.0 × 40.0 × 54.5 |
| `stand_J11_h025` | 1 | 1276 | 640 | 21.65 | yes | 40.0 × 40.0 × 34.5 |
| `base_tile` | 6 | 5392 | 2666 | 202.03 | yes | 250.0 × 250.0 × 12.0 |
| `lift_housing_back` | 1 | 4450 | 2225 | 633.72 | yes | 294.0 × 267.5 × 52.0 |
| `lift_housing_front` | 1 | 4772 | 2358 | 243.09 | yes | 265.6 × 258.0 × 5.0 |
| `lift_wheel_half` | 2 | 2446 | 1211 | 260.65 | yes | 210.0 × 185.9 × 19.0 |
| `lift_axle` | 1 | 1628 | 816 | 20.87 | yes | 32.0 × 32.0 × 81.5 |
| `lift_crank` | 1 | 780 | 390 | 30.70 | yes | 81.0 × 26.0 × 48.5 |
| `lift_clip` | 1 | 272 | 138 | 2.73 | yes | 30.0 × 34.0 × 4.0 |
| `lift_pawl` | 1 | 1096 | 548 | 19.72 | yes | 51.8 × 18.4 × 39.0 |
| `ball_35` | 6 | 8158 | 4081 | 22.40 | yes | 35.0 × 35.0 × 34.5 |
| `lift_test_base` | 1 | 798 | 401 | 134.21 | yes | 220.0 × 120.0 × 12.0 |
| `fit_coupon` | 1 | 2236 | 1120 | 35.84 | yes | 96.0 × 76.0 × 17.6 |

- Unique parts: **32**  | printed qty: **49**
- Unique faces / verts: **72112** / **36036**
- Printed faces / verts: **154298** / **76989**
- Printed solid volume: **6719.6 cm³** (plastic estimate before infill; not a filament-use figure)
- All 32 unique parts: single component, kernel-watertight, inside the 330 × 320 × 325 mm envelope.
- Raw `trimesh.load(..., process=False)` can report non-watertight because vertices are intentionally not welded; the kernel/manifold result above is the quality check that was used.
