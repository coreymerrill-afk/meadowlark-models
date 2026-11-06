# v2 slice report — previous meshes only

This report is the older generic PrusaSlicer 2.7.4 run (0.4 mm / 0.20 mm PLA). **Not** an official H3C profile. It does **not** cover the STLs regenerated for the Layout A clearance. PrusaSlicer was not available when those meshes were written, so they were not re-sliced. Do not print from this report.

- Brim profile: posts, caps, clips, latches, low_mount, switch_gate, fit_coupon.
- Supports profile: helix, drop40, split, merge, switch, funnel, both adapters.
- Everything else: plain generic PLA.

- Unique STLs: 36
- PASS: 36/36

| Part | Settings | Filament mm | Moves | Verdict | Warnings |
|------|----------|-------------|------:|---------|----------|
| `ADAPT_IN` | `generic_0.4_pla_0.20_supports.ini` | 13034.46 | 193998 | PASS | — |
| `ADAPT_OUT` | `generic_0.4_pla_0.20_supports.ini` | 6597.47 | 101090 | PASS | — |
| `ball_cap` | `generic_0.4_pla_0.20_brim.ini` | 562.59 | 16409 | PASS | floating islands/bridges mentioned |
| `fit_coupon` | `generic_0.4_pla_0.20_brim.ini` | 12170.15 | 124163 | PASS | floating islands/bridges mentioned |
| `lift_mount_plate` | `generic_0.4_pla_0.20.ini` | 16897.16 | 216821 | PASS | floating islands/bridges mentioned |
| `lock_clip_medium` | `generic_0.4_pla_0.20_brim.ini` | 1025.89 | 12272 | PASS | floating islands/bridges mentioned |
| `lock_clip_short` | `generic_0.4_pla_0.20_brim.ini` | 1025.89 | 12272 | PASS | floating islands/bridges mentioned |
| `lock_clip_tall` | `generic_0.4_pla_0.20_brim.ini` | 1025.89 | 12272 | PASS | floating islands/bridges mentioned |
| `low_mount` | `generic_0.4_pla_0.20_brim.ini` | 4618.89 | 45375 | PASS | floating islands/bridges mentioned |
| `post_medium` | `generic_0.4_pla_0.20_brim.ini` | 4652.41 | 67312 | PASS | — |
| `post_short` | `generic_0.4_pla_0.20_brim.ini` | 3167.03 | 46362 | PASS | — |
| `post_tall` | `generic_0.4_pla_0.20_brim.ini` | 6835.06 | 98220 | PASS | — |
| `sleeve_medium` | `generic_0.4_pla_0.20.ini` | 8287.67 | 87947 | PASS | floating islands/bridges mentioned |
| `sleeve_short` | `generic_0.4_pla_0.20.ini` | 5619.17 | 61565 | PASS | floating islands/bridges mentioned |
| `sleeve_tall` | `generic_0.4_pla_0.20.ini` | 12289.39 | 128047 | PASS | floating islands/bridges mentioned |
| `switch_gate` | `generic_0.4_pla_0.20_brim.ini` | 3486.01 | 51916 | PASS | floating islands/bridges mentioned |
| `tile_00` | `generic_0.4_pla_0.20.ini` | 104774.71 | 1517118 | PASS | floating islands/bridges mentioned |
| `tile_01` | `generic_0.4_pla_0.20.ini` | 106106.86 | 1463411 | PASS | floating islands/bridges mentioned |
| `tile_10` | `generic_0.4_pla_0.20.ini` | 105395.6 | 1481761 | PASS | floating islands/bridges mentioned |
| `tile_11` | `generic_0.4_pla_0.20.ini` | 106832.84 | 1419716 | PASS | floating islands/bridges mentioned |
| `tile_latch` | `generic_0.4_pla_0.20_brim.ini` | 635.63 | 6051 | PASS | — |
| `track_CL45` | `generic_0.4_pla_0.20.ini` | 13666.82 | 253465 | PASS | — |
| `track_CL90` | `generic_0.4_pla_0.20.ini` | 22402.58 | 454520 | PASS | floating islands/bridges mentioned |
| `track_CR45` | `generic_0.4_pla_0.20.ini` | 13678.96 | 257801 | PASS | floating islands/bridges mentioned |
| `track_CR90` | `generic_0.4_pla_0.20.ini` | 22354.86 | 444285 | PASS | floating islands/bridges mentioned |
| `track_DROP40` | `generic_0.4_pla_0.20_supports.ini` | 30625.76 | 530600 | PASS | — |
| `track_FUNNEL` | `generic_0.4_pla_0.20_supports.ini` | 35121.73 | 616430 | PASS | — |
| `track_HX360` | `generic_0.4_pla_0.20_supports.ini` | 213619.28 | 2520274 | PASS | — |
| `track_MERGE_Y` | `generic_0.4_pla_0.20_supports.ini` | 74506.8 | 1067007 | PASS | — |
| `track_S160` | `generic_0.4_pla_0.20.ini` | 28464.35 | 455496 | PASS | — |
| `track_S40` | `generic_0.4_pla_0.20.ini` | 8333.37 | 116729 | PASS | — |
| `track_S80` | `generic_0.4_pla_0.20.ini` | 16110.01 | 239914 | PASS | — |
| `track_SPAN240` | `generic_0.4_pla_0.20.ini` | 41317.98 | 670204 | PASS | — |
| `track_SPLIT_Y` | `generic_0.4_pla_0.20_supports.ini` | 74959.62 | 1122306 | PASS | — |
| `track_SWITCH` | `generic_0.4_pla_0.20_supports.ini` | 74340.93 | 1086912 | PASS | — |
| `track_TUN160` | `generic_0.4_pla_0.20.ini` | 39600.21 | 660770 | PASS | — |
