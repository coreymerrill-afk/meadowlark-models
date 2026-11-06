# Support & print notes
Generic 0.4 mm nozzle, 0.20 mm layer, PLA. Re-slice in Bambu Studio with the official H3C profile before printing. Do not use the validation G-code on the machine.
- `track_straight_160` x4: track module — print rim-down (upside down)
- `track_straight_80` x1: track module — print rim-down (upside down)
- `track_corner_right` x3: track module — print rim-down (upside down)
- `track_corner_left` x1: track module — print rim-down (upside down)
- `track_switch_Y` x1: track module — print rim-down (upside down)
- `track_spinner` x1: track module — print rim-down (upside down)
- `track_merge_Y` x1: track module — print rim-down (upside down)
- `lift_inlet_chute` x1: track module — print rim-down (upside down)
- `switch_gate` x1: OPTIONAL extra — not in the default loop. Drop-gate for track_switch_Y.
- `spinner_rotor` x1: brim recommended — OPTIONAL extra — 4-paddle rotor (use with track_spinner as a S160 substitute).
- `spinner_post` x2: OPTIONAL extra — U-slot post (print 2, second mirrored 180°).
- `spinner_retainer` x1: OPTIONAL extra — retainer arch that clears the paddle disc.
- `stand_J0_h175` x1: brim recommended — stand, cap top 175.0 mm above tile
- `stand_J1_h155` x1: brim recommended — stand, cap top 155.0 mm above tile
- `stand_J2_h135` x1: brim recommended — stand, cap top 135.0 mm above tile
- `stand_J3_h115` x1: brim recommended — stand, cap top 115.0 mm above tile
- `stand_J4_h095` x1: brim recommended — stand, cap top 95.0 mm above tile
- `stand_J5_h075` x1: brim recommended — stand, cap top 75.0 mm above tile
- `stand_J6_h065` x1: brim recommended — stand, cap top 65.0 mm above tile
- `stand_J7_h045` x1: brim recommended — stand, cap top 45.0 mm above tile
- `stand_J11_h025` x1: brim recommended — stand, cap top 25.0 mm above tile
- `base_tile` x6: 240 mm lattice tile with dovetails and 9 stand sockets
- `lift_housing_back` x1: back plate + guide + exit chute + roof + pawl pin; plate face on bed
- `lift_housing_front` x1: front plate with viewing slots and inlet port; outer face on bed
- `lift_wheel_half` x2: paddle-wheel half; split face on bed (print 2)
- `lift_axle` x1: brim recommended — hex axle; print standing on the head (no supports)
- `lift_crank` x1: crank arm + knob; arm face on bed, knob stands up
- `lift_clip` x1: brim recommended — snap U-clip on the axle groove (front)
- `lift_pawl` x1: gravity anti-reverse pawl; print on its flat side
- `ball_35` x6: SUPPORTS REQUIRED — 35 mm ball with 0.5 mm bed flat; supports required (or print as two hemispheres)
- `lift_test_base` x1: first-print frame: sockets for the two housing pegs and the inlet stand
- `fit_coupon` x1: first-print fit coupon: pegs, sockets, hexes, clip groove, spinner slot

## Track orientation
Tracks print rim-down. The V-floor is two 45° faces (printable without supports). Underside pockets open toward the top of the print.

## Balls
A full 35 mm sphere with a 0.5 mm bed flat needs supports (or print two hemispheres and glue — this kit does not include hemisphere STLs). First-layer contact is only the 0.5 mm flat plus whatever the support raft provides.
