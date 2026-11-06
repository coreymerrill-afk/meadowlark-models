# Marble System v2 — catalog plus one cleared default route

**Do not print the full kit.** Layout A clears a full 35 mm ball in computation: worst sample 1.01 mm³ against the tracks and both v1 housings, and no sample above 5 mm³. Consecutive Layout A rest joints are 0 mm³. Layout B is a **design study, not a working route**: the 80 mm helix does not cross itself, but the placed coil meets the lift housing by about 10,230 mm³. This is not a finished 48-piece play kit. Snap force, creep, fatigue, and rolling were not tested. The kit ZIP is not a print release.

Version **0.5-layoutA**. Computational prototype of a modular gravity marble run that
reuses the v1 hand-cranked paddle-wheel lift. **Not printed. Not certified. Not
kid-proof.** Treat every snap, slope, and load number as untested until a
physical kit exists.

v1 in `marble-factory` is **untouched**.

## What you get

- Four **exact 9×12 in** tiles (`228.6 × 304.8 mm`) that assemble to **18×24 in
  (457.2 × 609.6 mm)**. Printed with the 304.8 mm side along the H3C 330 mm
  axis (25.2 mm leftover).
- A **global 40 mm well lattice** that is allowed to cross tile boundaries that
  are *not* integer multiples of 40 mm. Wells that hit a seam, outer edge, or
  joiner band are omitted. **Actual site count: 117** (not 192).
  Per tile: tile_00 = 24, tile_10 = 28, tile_01 = 30,
  tile_11 = 35. Four distinct / mirrored well patterns.
- **48 track pieces** (source of truth below) plus **24 support structures**
  (8 short / 10 medium / 6 tall) counted separately, plus disclosed extras.
- Layout A is the default route and uses 9 posts (≤ 24). Layout B is a design study, not a second complete example.
  Not all 48 pieces are installed at once.

## 48-count track inventory

| id | qty | role |
|----|----:|------|
| S160 | 8 | 160 mm straight, drop 20 mm (7.13°) |
| S80 | 6 | 80 mm straight, drop 10 mm |
| S40 | 4 | 40 mm straight, drop 5 mm |
| CR90 / CL90 | 5 + 5 | R80 90° corners, drop 15 mm |
| CR45 / CL45 | 2 + 2 | R80 45° corners, drop 10 mm, 32 mm inward slide |
| SPLIT_Y | 2 | 160 mm Y-fork, A drop 20 / B drop 35 |
| MERGE_Y | 2 | two inlets, one downhill outlet |
| FUNNEL | 2 | wide basin, gravity floor, standard V exit |
| HX360 | 2 | descending 360° helix, coil Ø 244 mm, drop 80 mm, printed as **one piece** |
| DROP40 | 2 | 40 mm catch-bowl drop |
| SPAN240 | 2 | 240 mm straight, drop 30 mm |
| TUN160 | 1 | S160 with a roof |
| SWITCH | 1 | Y-fork plus a pocket for the removable gate |
| ADAPT_OUT | 1 | mates the published v1 chute keel, presents a standard male |
| ADAPT_IN | 1 | low direct-rail ramp into the v1 inlet (~31 mm class), **no ball stack**, always downhill |
| **sum** | **48** | |

## Support structures (separate bill)

24 structures × (sleeve + post + lock clip + ball cap) = 96 interface parts.

| class | qty | sleeve Ls | post | H window | overlap at max | below tile at min |
|-------|----:|----------:|-----:|----------:|---------------:|------------------:|
| short | 8 | 50 | 60 | 70–100 | 20 | 0 |
| medium | 10 | 80 | 90 | 100–155 | 25 | 0 |
| tall | 6 | 125 | 135 | 145–230 | 40 | 0 |

H is the ball-centre height above the tile = V-vertex − 11 mm. Rolling height
is H + `socket_to_rail` (35.75 mm). A short post at H = 70 puts the marble
centre at about 106 mm — there is no honest 50 mm minimum on these ball-jointed
posts. Rails that run lower use the disclosed `low_mount` extra (yoke, no ball).

Spares included in the print list: +8 lock clips (3 short / 3 medium / 2 tall)
and +8 ball caps. Replaceable wear parts; PETG recommended for clips.

## Extras (outside the 48 and the 24)

| extra | qty | why |
|-------|----:|-----|
| switch_gate | 1 | removable wall that blocks SWITCH path B |
| low_mount | 6 | well pin + yoke for rails below H = 70 mm |
| lift_mount_plate | 1 | two r=10.2 sockets 160 mm apart for the v1 housing pegs; square pins into the new wells (v1 teardrop pegs will not sit in a 22.4 mm square well) |
| fit_coupon | 1 | one-piece witness of well / rack / tongue / ball cup |

## Interface (locked)

- Grid pitch 40 mm. Track length 160 = 4P, corner R 80 = 2P, so 90° joints land
  on lattice points. 45° ends do **not**; they are supported off-grid by a 32 mm
  inward sliding socket. From a start at the origin heading +X, the CR45 end
  stadium captures well (40, 0) at **4.85 mm** lateral (inside the 8.3 mm ball
  radius).
- `socket_to_rail` = 8 + 3 + 17.5√2 = **35.75 mm**. The old 22 mm placeholder
  would bury the marble in the support ball.
- Ball joint: roll locked by an XZ meridian fin in an along-track slot; pitch
  ±15°; yaw via the cap turning on the round post pin (the square post itself
  does not yaw). Slide ±20 mm along-track (±32 mm on 45° pieces). This is **not**
  a free ball.
- Track joints: male tongue + side hooks into a female pocket and recesses.
  Assembly deflection of the hooks is intended. **Latched rest state does not
  interpenetrate** (validated S160×CL90, CL90×S80, S160×S160 = 0 mm³).
- Each joint also drops an extra 0.5 mm waterfall so the receiving floor is
  downhill of the arriving tongue.
- Positive 5 mm detent pawl above the tile. Unload-to-release (the hook face
  is square). Squeeze the clip to retract after lifting the post ~1 mm.

## Two example layouts

Both fit the 18×24 board, use the v1 lift in standard orientation (chute toward
−X, inlet from +Y), and stay downhill with a 35 mm ball. They are alternative
assemblies — do not install both at once. The lift sits on `lift_mount_plate`
on two wells; the plate is one extra, not one of the 24.

### Layout A — simple loop
- **A_simple_loop**: 10 track pieces, 10 ball-joint posts (≤24), 3 low_mount extras.
- ADAPT_IN drop 19.21 mm over 58.7 mm (18.12° downhill).
- Lift axle [460.0, 100.0], pegs [[380.0, 100.0], [540.0, 100.0]].
- Posts: (260,100) tall H=165.0, (180,100) medium H=155.0, (140,100) medium H=150.0, (60,180) medium H=135.0, (60,300) medium H=120.0, (60,340) medium H=115.0, (140,420) short H=100.0, (180,420) short H=95.0, (260,420) short H=85.0, (340,420) short H=75.0
- Low mounts (disclosed extras, H < 70): (380,420) Hraw=66.96, (460,340) Hraw=51.96, (460,300) Hraw=46.46

The two skipped sockets at y = 220 sit on the omitted seam row; neighboring
supports still carry those S160s (160 mm span).

### Layout B — design study, not a working route
- **B_helix**: the coil is the catalog helix (radius 90 mm, pitch 80 mm). Placed on this board it meets the lift. Do not treat it as an example to assemble.
- ADAPT_IN drop 15.21 mm over 58.7 mm (14.53° downhill).
- Lift axle [420.0, 100.0], pegs [[340.0, 100.0], [500.0, 100.0]].
- Posts: (260,100) tall H=170.0, (220,100) short H=90.0, (140,180) short H=75.0
- Low mounts (disclosed extras, H < 70): (220,260) Hraw=58.96, (260,260) Hraw=50.96, (340,260) Hraw=45.46, (420,180) Hraw=27.46

The helix part itself is one piece. At the 80 mm pitch the vertical air between passes is about 22 mm, so the rail does not cross itself. A shorter pitch was rejected because the section would meet the next pass. Sag between the coil sockets is untested. The assembled study meets the lift by about 10,230 mm³.

## Validation

Report: `reports/SOLIDS_AUDIT.md`. Layout A’s 35 mm sweep is the clearance that matters. An older “0 fail” count is not that sweep. No G-code is included.

Checks included: single-body watertight solids inside the 330×320×325 envelope;
sleeve/post sliding clearance; height-window overlap and no below-tile
protrusion; rest-state joint clearance (not “0 fails” if solids overlap);
pitch ±15° vs the post; roll-key contact of the fin; 45° slot well capture;
BOM sum = 48; well count ≠ 192; both layouts on-board with ≤ 24 posts and a
positive ADAPT_IN slope; consecutive rail rest mates.

Designed snaps (clip ears, cap bulge, socket lip) are labelled `designed_snap`
and are **not** treated as rest-state passes. Insertion forces are untested.

Ball-path assumption, stated honestly: a 35 mm sphere centre is taken to follow
the V-vertex + `VH` (17.5√2 mm) along each piece’s centreline. That is a
geometric clearance model, not a rolling-resistance or bounce simulation.
Carry through the v1 lift is the existing v1 synchronized 3D carry, unchanged.

## Slicing

Official PrusaSlicer 2.7.4, **generic** 0.4 mm / 0.20 mm PLA profiles. **Not**
an official H3C / Bambu profile. Re-slice in Bambu Studio on the H3C before
printing.

- Brim: posts, caps, clips, latches, low_mount, switch_gate, fit_coupon.
- Supports profile: helix, drop bowl, split/merge/switch, funnel, both adapters.
- Everything else: plain generic PLA.

Slice report: `slice/SLICE_REPORT.md` (36/36 PASS).

Suggested materials: PLA or PETG for tiles and tracks; **PETG for lock clips**
(repeated flex). 0.4 mm nozzle, 0.20 mm layer.

## What is untested

- Snap insertion and release forces, and whether a loaded track drops when the
  clip is squeezed.
- Creep of the pawl or cap bulge (the design uses a positive detent *because*
  friction pretension creeps).
- Physical rolling of a 35 mm ball, including the 14–18° ADAPT_IN ramps and
  the 80 mm helix.
- Helix sag on two end supports; joint durability; tile warp on the H3C.
- Child-safety / pinch at the lift (v1 already documents an open housing).
- Fatigue, UV, impact, certification of any kind.

The published 0-fail report does not boolean ADAPT_OUT or ADAPT_IN against the v1 lift solids, and it does not sweep a 35 mm ball solid along the route. Clip, cap, and socket overlaps are designed snaps. Helix sag on two end posts is untested.

Print the `fit_coupon` and one short support first. Do not hand this to a child
as a finished toy.

## File map

```
marble-system-v2/
  src/           Python generators (constants, parts, catalog, layouts, …)
  stl/           one STL per unique item, print-oriented
  kit/           manifest.json, assembly.json, layout A 3MF, this README
  renders/       board plan, height windows, support section, two 3D previews
  reports/       validation.json
  slice/         SLICE_REPORT.md only — generic G-code is not included
```

Generated 2026-11-05T23:54:42-07:00 America/Denver.
