# Dollhouse Play-First Kit — v4.3 Grand (2026-11-05)

Corey’s brief: Grand v3 was “plenty pretty, maybe too pretty.” Designs are for **practical kid play** — see inside, reach inside, rearrange outdoors like Legos. Scale **1:24**. Snap system unchanged.

## Play rules (locked)

1. **See inside**  
   No dense muntins, stained-glass inserts, leaded panes, or ornament that blocks room view. Windows are large clear openings (or open frames). Each manor prefers an **open-back / open-side** so a kid sees every room at a glance after setup.

2. **Hand access**  
   Every room reachable without tools. Prefer: open back (or one fully open face), **lift-off roofs** as separate snap modules, removable wall panels on the snap-post grid, wide doorways between rooms. At 1:24, kid hands won’t fit through tiny windows — open faces + lift-off roofs are the real access path. Viewer **Play view** hides roofs + rear walls by default.

3. **Manipulate furniture**  
   Furniture/figures stay free-standing on floor tiles. Room footprints stay open; no fixed built-ins that block play. Doorways ≥ ~25–30 mm clear where possible.

4. **Lego-like outdoors**  
   Outdoor kit on the **same 127 mm tile / Ø6 snap grid**. Kids move lawn, path, beds, fence, gate, sandbox, planter, bench, shed like bricks.

5. **Tone down facade clutter**  
   Keep charming silhouettes (gable, porch, chimney). Porte-cochère, stained glass, dense cresting, weathervane are **optional kit parts**, not baked into room shells.

6. **Six layouts stay**  
   Bramble Cottage, Larkspur Grand Ranch, Pennywhistle Row House, Cloisterwick Manor, Cogsworth Works, Electrified Manor — rebuilt for open play. Wired-5 keeps light channels + magnetic service panel concept.

## Snap interfaces (unchanged)

| Interface | Spec |
|-----------|------|
| Floor / outdoor tile | 127 × 127 mm |
| Snap | Ø6 post / Ø6.3 socket, 31.75 mm pitch (4×4), OFF = 15.875 |
| Light race | Ø3.2 |
| Corner post + short walls | existing `corner_post_v0`, `wall_panel_*_short_v0c` |
| Bed | H3C 330 × 320 × 325 |

Outdoor modules use the same **Ø5.9 peg → Ø6.3 socket** as furniture so they sit on lawn/path/floor tiles. Fence/gate use pegs at tile-edge socket positions. Shed sits on 1–2 tiles with open front.

## Part list — play structure (`stl/*_v4` / `*_play`)

| STL | Role |
|-----|------|
| `wall_panel_clear_window_v4.stl` | Short-compatible clear window: large open aperture, sill, no muntins |
| `wall_panel_wide_door_v4.stl` | Wide doorway ≥ 28 mm clear (≈ 34 mm opening) |
| `roof_panel_lift_v4.stl` | Lift-off roof panel: underside pegs on 31.75 grid seat by **lip on wall tops**; **ridge Ø6.3 sockets** are for finial / chimney / cupola / dormer mates (not wall pegs) |
| `open_face_rail_v4.stl` | Low open-back rail (furniture stop, full sightline) |

Reuse unchanged: `floor_tile_v0`, `snap_post_v0`, `corner_post_v0`, `dowel_pin_v0`, wall shorts, wired_* for Electrified Manor.

## Part list — outdoor Lego modules

| STL | Footprint / pegs | Play use |
|-----|------------------|----------|
| `lawn_tile_v4.stl` | 127×127, same sockets as floor | Yard base |
| `path_tile_v4.stl` | 127×127, paver grooves | Walkway |
| `garden_bed_v4.stl` | ~100×50 raised bed, 2 pegs | Planting play |
| `fence_straight_v4.stl` | Spans one tile edge, 2 pegs | Yard edge |
| `fence_corner_v4.stl` | 90° corner, 2 pegs | Corner |
| `garden_gate_play_v4.stl` | Open double gate + piers, clear sight | Entry (not ornate-obstructed) |
| `sandbox_v4.stl` | ~100×100 tray, 4 corner pegs | Play pad |
| `planter_stub_v4.stl` | Round planter + trunk stub, 1 peg | Tree / plant |
| `bench_play_v4.stl` | Bench, 2 pegs | Sit / rest |
| `shed_shell_v4.stl` | Open-front shed ~127×100, pegs on floor | Outdoor playhouse shell |

v3 showpiece STLs (porte-cochère, stained inserts, weathervane, etc.) remain downloadable as **optional ornament**, demoted in the explorer.

## How outdoor modules snap

```
  [lawn_tile] [path_tile] [lawn_tile]
       ↑ peg into any tile socket (31.75 grid)
  fence_straight sits on edge sockets of a lawn/path tile
  garden_gate_play bridges a path gap between two piers
  shed_shell sits on one lawn/floor tile, open face toward play
  sandbox / garden_bed / bench / planter drop onto sockets like furniture
```

Kids rearrange the garden layer without tools; houses stay on structural floor tiles.

## Viewer (models.coreyhq.com/dollhouse)

- Banner / rev: **v4.3 Grand**
- **Play view** control: roofs OFF + rear walls OFF + clear (non-stained) windows — **default ON**
- Explode / night / turntable kept
- Kit tab: play outdoor + structure STLs first; v3 ornaments optional

## v4.3 Grand accents (REQUIRED play BOM)

All accents mate only Ø6.3 / 31.75; porch posts use the same floor/tile sockets as outdoor. Spans ≤127 mm. Do not cover clear windows or kill lift-off roofs.

| STL | Mate | Role |
|-----|------|------|
| `tower_stub_v43.stl` | Center peg → corner-post top / floor socket; top sock for finial | Vertical accent |
| `chimney_ridge_v43.stl` | Peg → `roof_panel_lift_v4` ridge Ø6.3 | Vertical / roofs-on |
| `finial_ridge_v43.stl` | Peg → ridge / tower / gable top sock | Vertical accent |
| `clock_shaft_v43.stl` | Peg → corner-post top; top sock for finial | Cogsworth vertical |
| `porch_post_v43.stl` | Peg → floor/lawn/path Ø6.3; top sock for beam | Street façade |
| `porch_beam_v43.stl` | Pegs at 0 & 127 → porch_post tops | Façade beam |
| `porch_roof_slice_v43.stl` | Pegs (y=12) → porch_post tops, not floor grid | Porch roof slice |
| `gable_end_v43.stl` | Pegs at 0 & 127; apex sock for finial | Roofs-on silhouette |
| `dormer_play_v43.stl` | Peg → ridge Ø6.3; clear window opening | Roofs-on break |
| `mansard_break_v43.stl` | Pegs at 0 & 127 → ridge; top sock | Mansard silhouette |
| `cupola_play_v43.stl` | Pegs ±63.5 (span 127) → ridge socks x=15.875/142.875; top Ø6.3 sock in Ø16 boss | Widow’s-walk cupola |

Per-manor required accents live in `grand.js` COREBOM (v4.3 Grand).

## Gaps left

- Physical Ø6.3 socket fit still pending H3C clearance-strip test
- 3MF plates after fit
- Corner-post top socket: shipped in v4.2 (`corner_post_v0` / wired)
