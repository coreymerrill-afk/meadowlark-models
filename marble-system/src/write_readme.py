"""Write README.md and INTERFACE_CAD.md from live constants + reports."""
import json
from pathlib import Path
import constants as C

ROOT = Path('/workspace/marble-system-v2')
KIT = ROOT / 'kit'
REP = ROOT / 'reports'

def main():
    wells = C.all_wells()
    per = {f'{ix}{iy}': len(C.wells_on_tile(ix, iy)) for ix in (0, 1) for iy in (0, 1)}
    val = json.loads((REP / 'validation.json').read_text()) if (REP / 'validation.json').exists() else {}
    man = json.loads((KIT / 'manifest.json').read_text()) if (KIT / 'manifest.json').exists() else {}
    slc = {}
    sp = ROOT / 'slice' / 'slice_report.json'
    if sp.exists():
        rows = json.loads(sp.read_text())
        slc = dict(n=len(rows), pass_n=sum(1 for r in rows if r.get('ok')))

    nfail = val.get('n_fail', '?')
    layouts = val.get('sections', {}).get('layouts', man.get('layouts', []))

    def lay_md(s):
        if not s:
            return '_not yet run_'
        posts = s.get('posts', [])
        lows = s.get('low_mounts', [])
        lines = [
            f"- **{s.get('name')}**: {s.get('n_track_pieces')} track pieces, "
            f"{s.get('n_posts')} ball-joint posts (≤24), {s.get('n_low_mounts')} low_mount extras.",
            f"- ADAPT_IN drop {s.get('adapt_in_drop')} mm over {C.V1_INLET_L} mm "
            f"({s.get('adapt_in_slope_deg')}° downhill).",
            f"- Lift axle {s.get('lift', {}).get('axle')}, pegs {s.get('lift', {}).get('pegs')}.",
            f"- Posts: " + ', '.join(f"({p['x']:.0f},{p['y']:.0f}) {p['kind']} H={p['H']}" for p in posts),
            f"- Low mounts (disclosed extras, H < 70): " + (', '.join(f"({p['x']:.0f},{p['y']:.0f}) Hraw={p['Hraw']}" for p in lows) or 'none'),
        ]
        return '\n'.join(lines)

    readme = f"""# Marble System v2 — full 48-piece CAD (prototype)

Version **0.3-full48**. Computational prototype of a modular gravity marble run that
reuses the v1 hand-cranked paddle-wheel lift. **Not printed. Not certified. Not
kid-proof.** Treat every snap, slope, and load number as untested until a
physical kit exists.

v1 in `/workspace/marble-factory` is **untouched**.

## What you get

- Four **exact 9×12 in** tiles (`228.6 × 304.8 mm`) that assemble to **18×24 in
  (457.2 × 609.6 mm)**. Printed with the 304.8 mm side along the H3C 330 mm
  axis (25.2 mm leftover).
- A **global 40 mm well lattice** that is allowed to cross tile boundaries that
  are *not* integer multiples of 40 mm. Wells that hit a seam, outer edge, or
  joiner band are omitted. **Actual site count: {len(wells)}** (not 192).
  Per tile: tile_00 = {per['00']}, tile_10 = {per['10']}, tile_01 = {per['01']},
  tile_11 = {per['11']}. Four distinct / mirrored well patterns.
- **48 track pieces** (source of truth below) plus **24 support structures**
  (8 short / 10 medium / 6 tall) counted separately, plus disclosed extras.
- Two complete example layouts on the same board, each using ≤ 24 posts.
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
{lay_md(layouts[0] if layouts else None)}

The two skipped sockets at y = 220 sit on the omitted seam row; neighboring
supports still carry those S160s (160 mm span).

### Layout B — helix
{lay_md(layouts[1] if len(layouts) > 1 else None)}

The helix is a single connected printable guide (actual bbox about 244 × 252 ×
116 mm, under the 320 mm bed). It is supported at its entry and exit balls; sag
of a 244 mm spiral on two posts is **untested**. The 80 mm pitch clears the
~41 mm section height, so the coil does not self-intersect.

## Validation

Report: `reports/validation.json`. This run: **{nfail} fail(s)**.

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

Slice report: `slice/SLICE_REPORT.md` ({slc.get('pass_n', '?')}/{slc.get('n', '?')} PASS).

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

Generated {man.get('generated', '(run export to stamp a time)')} America/Denver.
"""
    (ROOT / 'README.md').write_text(readme)
    (KIT / 'README.md').write_text(readme)

    cad = f"""# v2 CAD interface notes (0.3-full48)

See `README.md` for the kit-facing description. This file records the geometry
locks used by the generators.

- Tile pitch {C.TILE_PX} × {C.TILE_PY} mm, assembled {C.ASSEMBLED[0]} × {C.ASSEMBLED[1]} mm.
- Wells: global origin {C.GRID_ORIGIN}, pitch {C.P}, well {C.WELL} mm square,
  depth {C.WELL_DEPTH}, omitted if they intersect seams at x={C.SEAM_X} /
  y={C.SEAM_Y}, outer edges (keep {C.EDGE_KEEP} mm) or joiner bands (keep
  {C.JOINER_KEEP} mm). Count {len(wells)}.
- SOCKET_TO_V = {C.SOCKET_TO_V}, SOCKET_TO_RAIL = {C.SOCKET_TO_RAIL:.4f}.
- SLIDE = {C.SLIDE}, SLIDE_45 = {C.SLIDE_45}, TONGUE = {C.TONGUE},
  TONGUE_CLR = {C.TONGUE_CLR}, WATERFALL = {C.WATERFALL}.
- Classes: {C.CLASSES}
- BOM48 sum {sum(q for _,q in C.BOM48)}; extras {C.EXTRAS}.

Sample support XY from CAD 0.2 — (60,60), (140,60), (260,140), (260,180) —
remain valid wells on tile_00 after the tile size reverted from 320×240 to
304.8×228.6.
"""
    (ROOT / 'INTERFACE_CAD.md').write_text(cad)

    # machine-readable interface
    iface = dict(
        version='0.3-full48',
        assembled_mm=list(C.ASSEMBLED),
        assembled_in=list(C.ASSEMBLED_IN),
        tile_mm=[C.TILE_PX, C.TILE_PY],
        pitch_mm=C.P,
        well_count=len(wells),
        wells_per_tile=per,
        socket_to_rail=C.SOCKET_TO_RAIL,
        classes=C.CLASSES,
        bom48=[{'id': i, 'qty': q} for i, q in C.BOM48],
        extras=C.EXTRAS,
        slide=C.SLIDE, slide_45=C.SLIDE_45,
        tongue_clearance=C.TONGUE_CLR, waterfall=C.WATERFALL,
    )
    (ROOT / 'interface_v2.json').write_text(json.dumps(iface, indent=2))
    print('wrote README, INTERFACE_CAD, interface_v2.json')

if __name__ == '__main__':
    main()
