# Marble Factory — Slice Validation Report

**When:** 2026-11-05 America/Denver
**Slicer:** Official PrusaSlicer 2.7.4 via xvfb-run + /workspace/tools/sysroot, same pattern as observatory-slice-validation.
**Profile:** Generic 0.4 mm / 0.20 mm PLA. **Not** an official H3C profile. Re-slice in Bambu Studio before printing.

- Unique STLs: **32**
- Non-empty G-code with extrusions: **32/32**
- Failures: **0**

| Part | Settings | Filament mm | Moves | Z range | Supports | Warnings | Verdict |
|------|----------|-------------|------:|---------|----------|----------|---------|
| `ball_35` | `generic_0.4_pla_0.20_supports.ini` | 3406.15 | 122280 | 0.2–34.4 | yes | — | PASS |
| `base_tile` | `generic_0.4_pla_0.20.ini` | 50640.37 | 702175 | 0.2–12.0 | no | — | PASS |
| `fit_coupon` | `generic_0.4_pla_0.20.ini` | 8942.76 | 115334 | 0.2–17.6 | no | — | PASS |
| `lift_axle` | `generic_0.4_pla_0.20_brim.ini` | 3926.17 | 88085 | 0.2–81.4 | no | floating islands/bridges mentioned | PASS |
| `lift_clip` | `generic_0.4_pla_0.20_brim.ini` | 918.77 | 10918 | 0.2–5.0 | no | — | PASS |
| `lift_crank` | `generic_0.4_pla_0.20.ini` | 5135.0 | 145844 | 0.2–48.4 | no | floating islands/bridges mentioned | PASS |
| `lift_housing_back` | `generic_0.4_pla_0.20.ini` | 120200.32 | 1547196 | 0.2–52.0 | no | — | PASS |
| `lift_housing_front` | `generic_0.4_pla_0.20.ini` | 51052.12 | 513686 | 0.2–5.0 | no | — | PASS |
| `lift_inlet_chute` | `generic_0.4_pla_0.20.ini` | 16587.54 | 287648 | 0.2–50.0 | no | — | PASS |
| `lift_pawl` | `generic_0.4_pla_0.20.ini` | 4488.69 | 160139 | 0.2–39.0 | no | — | PASS |
| `lift_test_base` | `generic_0.4_pla_0.20.ini` | 20469.49 | 323111 | 0.2–12.0 | no | — | PASS |
| `lift_wheel_half` | `generic_0.4_pla_0.20.ini` | 33978.09 | 783148 | 0.2–19.0 | no | — | PASS |
| `spinner_post` | `generic_0.4_pla_0.20.ini` | 1228.85 | 13437 | 0.2–45.2 | no | — | PASS |
| `spinner_retainer` | `generic_0.4_pla_0.20.ini` | 3038.83 | 35227 | 0.2–35.4 | no | floating islands/bridges mentioned | PASS |
| `spinner_rotor` | `generic_0.4_pla_0.20_brim.ini` | 4197.83 | 109130 | 0.2–63.0 | no | floating islands/bridges mentioned | PASS |
| `stand_J0_h175` | `generic_0.4_pla_0.20_brim.ini` | 17244.36 | 512289 | 0.2–184.4 | no | — | PASS |
| `stand_J11_h025` | `generic_0.4_pla_0.20_brim.ini` | 4194.19 | 100823 | 0.2–34.4 | no | — | PASS |
| `stand_J1_h155` | `generic_0.4_pla_0.20_brim.ini` | 15492.44 | 457139 | 0.2–164.4 | no | — | PASS |
| `stand_J2_h135` | `generic_0.4_pla_0.20_brim.ini` | 13757.71 | 402276 | 0.2–144.4 | no | — | PASS |
| `stand_J3_h115` | `generic_0.4_pla_0.20_brim.ini` | 12019.38 | 348083 | 0.2–124.4 | no | — | PASS |
| `stand_J4_h095` | `generic_0.4_pla_0.20_brim.ini` | 10277.25 | 292918 | 0.2–104.4 | no | — | PASS |
| `stand_J5_h075` | `generic_0.4_pla_0.20_brim.ini` | 8534.55 | 237891 | 0.2–84.4 | no | — | PASS |
| `stand_J6_h065` | `generic_0.4_pla_0.20_brim.ini` | 7666.9 | 210444 | 0.2–74.4 | no | — | PASS |
| `stand_J7_h045` | `generic_0.4_pla_0.20_brim.ini` | 5929.74 | 156004 | 0.2–54.4 | no | — | PASS |
| `switch_gate` | `generic_0.4_pla_0.20.ini` | 25535.59 | 218171 | 0.2–76.0 | no | — | PASS |
| `track_corner_left` | `generic_0.4_pla_0.20.ini` | 36235.6 | 724472 | 0.2–70.0 | no | — | PASS |
| `track_corner_right` | `generic_0.4_pla_0.20.ini` | 36216.57 | 766606 | 0.2–70.0 | no | floating islands/bridges mentioned | PASS |
| `track_merge_Y` | `generic_0.4_pla_0.20.ini` | 81614.95 | 1263576 | 0.2–102.0 | no | — | PASS |
| `track_spinner` | `generic_0.4_pla_0.20.ini` | 52528.06 | 649623 | 0.2–70.0 | no | — | PASS |
| `track_straight_160` | `generic_0.4_pla_0.20.ini` | 45299.33 | 496499 | 0.2–70.0 | no | — | PASS |
| `track_straight_80` | `generic_0.4_pla_0.20.ini` | 22828.85 | 274126 | 0.2–60.0 | no | — | PASS |
| `track_switch_Y` | `generic_0.4_pla_0.20.ini` | 134218.39 | 1777392 | 0.2–102.0 | no | — | PASS |

No empty-first-layer failures. `ball_35` requires supports. Axle, crank, rotor, retainer, and `track_corner_right` warned about floating bridges/loose extrusions but still produced full toolpaths.
