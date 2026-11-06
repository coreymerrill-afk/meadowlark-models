# Hand-Cranked Marble Factory

> **Unprinted prototype.** The default circuit is a computationally coherent loop: lift → downhill straights and swept right-hand corners → inlet → lift. Headings are continuous, the sampled ball-centre path has no uphill, the chute nest volume is 0 mm³, synchronized 3D carry vs the moving wheel/housing cleared, and all 32 unique parts sliced. Physical rolling and snap-fit remain untested. Not a certified toy.

Version 1.0.0. Built 2026-11-05T21:52:52-07:00 (America/Denver).

A colorful, snap-together marble run for a 10-year-old: a big hand crank lifts 35 mm printed balls in a paddle wheel, then gravity returns them through modular V-tracks and three swept R=80 corners, back into the inlet.

**This is an unprinted prototype.** Every clearance and motion check in this kit is computational. Print the fit coupon and the lift-only test before committing to the full set. Physical fit (especially the wheel-to-guide gap, chute nest, snap clip, and printed friction) is unproven until you try it.

**Not a certified toy.** Balls are 35 mm (larger than the common small-parts gauge) but this design is **not** safety-certified. The front plate has 6 mm viewing slots and the inlet is a 59 mm tunnel, but the 35 mm inlet must stay large enough for the ball, so fingers can still reach the wheel. Pinch risk remains. Adult supervision required. Not for children under 3. No certification is claimed.

## What you got on the H3C order (context)

The machine is a Bambu Lab H3C Full Combo (AMS 3H expected from the bundle listing) with a 0.4 mm × 7 hotend kit. Every part here is meant to print in PLA with a 0.4 mm nozzle, one color per part — no material mixing required. Re-slice in Bambu Studio with the official H3C profile; included slice reports used a generic 0.4 mm / 0.20 mm PLA profile and are **not** ready to send to the H3C.

## Default playable loop

Switch, merge, and spinner modules are **not** on this circuit. Their STLs are optional extras (see below) and do not have a verified layout of their own.

`J0 (−80, 0)` — chute nest — `S160` → `J1 (−240, 0)` — `corner R` → `J2 (−320, 80)` — `S160` → `J3 (−320, 240)` — `corner R` → `J4 (−240, 320)` — `S160` → `J5 (−80, 320)` — `S80` → `J6 (0, 320)` — `corner R` → `J7 (80, 240)` — `S160` → `J11 (80, 80)` — `inlet` → lift sump.

Track drop is 20 mm per 160 mm (7.13°). Inlet drop is 8.2 mm over 58.7 mm (7.96°). See `reports/VALIDATION.md` for the exact tests.

## How the lift works

1. **Pickup.** Balls roll down the inlet chute into a sump at the bottom of the wheel (ball-centre radius 90.5 mm against the outer guide).
2. **Retention.** A paddle (6 on the wheel, 60° apart, 8 mm thick) sweeps the ball up the rising side. The hub (r = 70) and concentric guide (inner r = 108) keep the ball in a pocket; the 2D quasi-static model shows the ball stays in contact with one paddle and never pinches against a second paddle (second-nearest gap ≥ 31 mm).
3. **Release.** Near 97° past the +x axis the pocket opens into a 7° descending chute. The ball rolls off the paddle onto the chute and through a short roofed section (keeps it from hopping out at the top).
4. **Return.** The chute ends in a low keel that sits in the first-track V floor, below the ball, with a short root into the chute floor on the lift side of J0 (so the housing stays one piece). From there the ball only goes downhill: 20 mm drop per 160 mm (7.13°) on the straights and matching swept corners, then 8.2 mm over 58.7 mm (7.96°) on the inlet.

A gravity pawl behind the wheel clicks over each paddle going forward and locks against a stop if the crank is released backward, so a ball on the rising side cannot slam the crank around.

## Modular track

Joints are two half-disc pegs that share a stand socket (0.5 mm radial clearance). Stands drop into the tiled base (dovetail tiles, 9 sockets each). You can unplug modules and rearrange them; an extra unused left corner is included for experiments. Keep a continuous downhill — default modules drop 20 mm over 160 mm (10 mm over 80 mm).

## Optional extras (not on the default loop)

These parts slice cleanly and are in the ZIP, but they are **not** placed in the assembled 3MF and they do **not** have a verified alternate circuit:

- `track_switch_Y` + `switch_gate` and `track_merge_Y` still use an older internal 12 mm A-drop. They are **not** drop-in compatible with the 7.13° default loop.
- `track_spinner` uses the same 20 mm / 160 mm drop as a straight, so it can physically substitute a `S160`, but the rotor / posts / retainer were not given a verified layout with the rest of the factory.

Do not treat these as a second finished factory.

## First print (do this first)

1. `fit_coupon` — every repeating interface (pegs, sockets, hexes, clip groove, gate/retainer holes).
2. The lift-only set listed in `manifest.json` → `first_print`, on `lift_test_base` instead of the full tile grid: both housings, two wheel halves, axle, crank, clip, pawl, `stand_J11_h025`, inlet, 1–2 balls.
3. Confirm: axle turns smoothly, pawl clicks, a ball is picked up and released onto the chute, clip stays put, crank does not collide with the inlet.
4. Only then print the six tiles, nine stands, four `S160`, one `S80`, three right corners, and the remaining balls.

## Suggested colors (one spool per part type)

- Blue PLA: straight tracks, inlet
- Green PLA: corners
- Pink PLA: optional switch and merge
- Orange PLA: optional spinner track/posts, clip
- Red PLA: wheel halves, balls, optional spinner rotor
- Yellow PLA: crank, optional switch gate and retainer
- Dark grey PLA: housing back, pawl
- Cyan PLA: housing front
- White/natural: axle
- Light grey: stands and tiles

## Parts

| Part | Qty | Color | Size (mm) | Supports | Notes |
|---|---:|---|---|---|---|
| `track_straight_160` | 4 | #2E86DE | 160.0 × 76.0 × 70.0 | no | track module — print rim-down (upside down) |
| `track_straight_80` | 1 | #2E86DE | 80.0 × 76.0 × 60.0 | no | track module — print rim-down (upside down) |
| `track_corner_right` | 3 | #10AC84 | 118.0 × 118.0 × 70.0 | no | track module — print rim-down (upside down) |
| `track_corner_left` | 1 | #10AC84 | 118.0 × 118.0 × 70.0 | no | track module — print rim-down (upside down) |
| `track_switch_Y` | 1 | #F368E0 | 240.0 × 156.0 × 102.0 | no | track module — print rim-down (upside down) |
| `track_spinner` | 1 | #FF9F43 | 160.0 × 76.0 × 70.0 | no | track module — print rim-down (upside down) |
| `track_merge_Y` | 1 | #F368E0 | 160.0 × 156.0 × 102.0 | no | track module — print rim-down (upside down) |
| `lift_inlet_chute` | 1 | #54A0FF | 58.7 × 76.0 × 50.0 | no | track module — print rim-down (upside down) |
| `switch_gate` | 1 | #FECA57 | 120.0 × 132.0 × 76.2 | no | OPTIONAL extra — not in the default loop. Drop-gate for track_switch_Y. |
| `spinner_rotor` | 1 | #FF6B6B | 60.0 × 60.0 × 63.0 | no + brim | OPTIONAL extra — 4-paddle rotor (use with track_spinner as a S160 substitute). |
| `spinner_post` | 2 | #FF9F43 | 14.0 × 10.0 × 45.2 | no | OPTIONAL extra — U-slot post (print 2, second mirrored 180°). |
| `spinner_retainer` | 1 | #FECA57 | 16.0 × 70.0 × 35.4 | no | OPTIONAL extra — retainer arch that clears the paddle disc. |
| `stand_J0_h175` | 1 | #8395A7 | 40.0 × 40.0 × 184.5 | no + brim | stand, cap top 175.0 mm above tile |
| `stand_J1_h155` | 1 | #8395A7 | 40.0 × 40.0 × 164.5 | no + brim | stand, cap top 155.0 mm above tile |
| `stand_J2_h135` | 1 | #8395A7 | 40.0 × 40.0 × 144.5 | no + brim | stand, cap top 135.0 mm above tile |
| `stand_J3_h115` | 1 | #8395A7 | 40.0 × 40.0 × 124.5 | no + brim | stand, cap top 115.0 mm above tile |
| `stand_J4_h095` | 1 | #8395A7 | 40.0 × 40.0 × 104.5 | no + brim | stand, cap top 95.0 mm above tile |
| `stand_J5_h075` | 1 | #8395A7 | 40.0 × 40.0 × 84.5 | no + brim | stand, cap top 75.0 mm above tile |
| `stand_J6_h065` | 1 | #8395A7 | 40.0 × 40.0 × 74.5 | no + brim | stand, cap top 65.0 mm above tile |
| `stand_J7_h045` | 1 | #8395A7 | 40.0 × 40.0 × 54.5 | no + brim | stand, cap top 45.0 mm above tile |
| `stand_J11_h025` | 1 | #8395A7 | 40.0 × 40.0 × 34.5 | no + brim | stand, cap top 25.0 mm above tile |
| `base_tile` | 6 | #C8D6E5 | 250.0 × 250.0 × 12.0 | no | 240 mm lattice tile with dovetails and 9 stand sockets |
| `lift_housing_back` | 1 | #576574 | 294.0 × 267.5 × 52.0 | no | back plate + guide + exit chute + roof + pawl pin; plate face on bed |
| `lift_housing_front` | 1 | #48DBFB | 265.6 × 258.0 × 5.0 | no | front plate with viewing slots and inlet port; outer face on bed |
| `lift_wheel_half` | 2 | #EE5253 | 210.0 × 185.9 × 19.0 | no | paddle-wheel half; split face on bed (print 2) |
| `lift_axle` | 1 | #F5F6FA | 32.0 × 32.0 × 81.5 | no + brim | hex axle; print standing on the head (no supports) |
| `lift_crank` | 1 | #FECA57 | 81.0 × 26.0 × 48.5 | no | crank arm + knob; arm face on bed, knob stands up |
| `lift_clip` | 1 | #FF9F43 | 30.0 × 34.0 × 4.0 | no + brim | snap U-clip on the axle groove (front) |
| `lift_pawl` | 1 | #222F3E | 51.8 × 18.4 × 39.0 | no | gravity anti-reverse pawl; print on its flat side |
| `ball_35` | 6 | #FF4757 | 35.0 × 35.0 × 34.5 | yes | 35 mm ball with 0.5 mm bed flat; supports required (or print as two hemispheres) |
| `lift_test_base` | 1 | #C8D6E5 | 220.0 × 120.0 × 12.0 | no | first-print frame: sockets for the two housing pegs and the inlet stand |
| `fit_coupon` | 1 | #A3CB38 | 96.0 × 76.0 × 17.6 | no | first-print fit coupon: pegs, sockets, hexes, clip groove, spinner slot |

## Assembly (no glue, no electronics, no screws)

1. Dovetail the six base tiles into a 720 × 480 mm lattice (3 × 2). The verified joints and the two housing pegs at (0, 0) and (160, 0) all land on this grid.
2. Drop each stand into its marked socket (heights are in the part name, e.g. `stand_J0_h175`).
3. Snap track modules onto the stands, starting at J0 (beside the lift) and working downhill: `S160`, right corner, `S160`, right corner, `S160`, `S80`, right corner, `S160`. Half-pegs from neighboring modules share a socket and form a full disc.
4. Seat the lift housing back (teardrop pegs) in the two sockets at world (0, 0) and (160, 0). Slide the pawl onto its pin. The chute keel should sit in the first-track V floor without forcing the walls.
5. Place the two wheel halves in the pocket (hexes aligned). Fit the front plate onto the three alignment pins plus the pawl and stop pins.
6. Insert the axle from the **back**, tip-first toward the front: it passes through the back journal, both wheel hexes, and the front journal. The head stays behind the back plate.
7. Press the crank onto the front hex and snap the U-clip into the groove beyond the crank.
8. Snap the inlet chute onto J11; its nose should line up with the front-plate inlet. Drop in up to six balls and turn the crank so the top of the crank moves toward the inlet side (CCW viewed from the front).

If a joint feels tight, scrape the pegs lightly; if it’s loose, a sliver of tape on a peg is enough for a prototype. Do not force the axle — the hexes are 0.2 mm per flat oversized.

## Files

- `stl/` — one watertight STL per unique part, already in print orientation
- `manifest.json` — quantities, colors, bounding boxes, clearances, joint heights
- `assembly.json` — 4×4 transforms from each print-oriented STL into the assembled world frame
- `marble_factory_assembly.3mf` — colored assembled preview of the default loop (not a ready-to-print plate)
- `SUPPORT_NOTES.md` — per-part brim/support flags
- `reports/VALIDATION.md` — exact computational tests (do not inflate beyond what was checked)
- `slice/SLICE_REPORT.md` — generic-profile slice check of all 32 unique STLs
- `renders/` — top-view route, assembly steps, lift mechanism

Print envelope used for checks: 330 × 320 × 325 mm (H3C). Largest part is `lift_housing_back` at 294.0 × 267.5 × 52.0 mm.
