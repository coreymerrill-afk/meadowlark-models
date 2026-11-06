# Solids audit — Layout A clearance, Layout B design study

Full 35 mm sphere, radius 17.5 mm, no shrink. Volumes are manifold intersections. This is computational clearance, not a certification. Snap force, creep, fatigue, and rolling were not tested.

## Layout A — default route

- 250 ball samples along the loop, including the waterfall hold at each joint and the inlet adapter, tested against the union of the track solids and both v1 housings.
- Worst sample: **1.01 mm³** at CR3, arc 14.36 mm. No sample above 5 mm³.
- Consecutive rest joints, including S160_4 × ADAPT_IN: **0 mm³**.
- ADAPT_OUT × housing back: **1.49 mm³** (numeric sliver). ADAPT_OUT × housing front and × the first straight: 0. ADAPT_IN × both housings: 0.
- Posts whose shaft met a track by more than 8 mm³ are omitted. Nine posts remain, inside the 24.
- The north rim of CR2, S160_3, and S80_1 reaches about y = 459.6 mm. The tile ends at 457.2 mm, so that rim overhangs by about 2.4 mm. The ball centreline stays on the board.

## Layout B — design study, not a working route

The catalog helix stays at radius 90 mm and pitch 80 mm. A column that contains both an upper and a lower pass has at least **22 mm** of vertical air, so the rail does not cross itself. A 25 mm pitch was not used: the section would meet the next pass.

Placed on the 18×24 board beside the lift (axle 420, 100):

- Helix solid × v1 housings: **10,230 mm³**.
- 35 mm ball on that route, including the other track solids and the housings: worst **5,109 mm³** on the helix. Seven samples above 5 mm³.

That layout is kept so the collision can be inspected. It is not a complete example and it is not a route to print.

## Catalog centrelines

Same 35 mm sphere, local frame, no shrink. Worst sample:

| Family | mm³ |
|--------|----:|
| Straights, corners, funnel, helix, DROP40, tunnel, both adapters | 0.00 |
| SPLIT_Y branch A / SWITCH branch A | 0.17 |
| MERGE_Y inlet B | 0.26 |
| MERGE_Y inlet A | 1.93 |
| SPLIT_Y branch B / SWITCH branch B, gate up | 3.55 |

DROP40 is one guided V. There is no bowl and no connector block on the ball path. Both merge inlets fall toward the shared exit.

Switch gate, two poses: down meets the branch B ball by about 5,985 mm³ and misses branch A. Up misses both balls. Each detent overlaps the divider tower by **7.68 mm³**. That overlap is a designed snap. The force is unknown.

## Not claimed

- The 48-piece inventory is not a finished play kit. Layout B does not clear the lift.
- The full-kit ZIP and the Layout A 3MF are not a print release.
- Changed STLs were not re-sliced. The older generic PrusaSlicer 2.7.4 report does not cover these meshes and is not an H3C result.
- v1 `marble-factory` is unchanged.
