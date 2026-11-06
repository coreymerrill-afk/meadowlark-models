"""Export print-oriented STLs, manifest, assembly JSON, colored 3MF, README, ZIP."""
import json, math, os, sys, zipfile, hashlib
from datetime import datetime
from pathlib import Path
import numpy as np
import trimesh
import assembly as A
from assembly import apply
from geom import to_trimesh

ROOT = Path('/workspace/marble-factory')
STL = ROOT / 'stl'
OUT = ROOT / 'kit'
RENDER = ROOT / 'renders'
for d in (STL, OUT, RENDER):
    d.mkdir(parents=True, exist_ok=True)

VERSION = '1.0.0'
QTY_PRINT = {
    'track_corner_left': 1,
    'track_switch_Y': 1,
    'track_spinner': 1,
    'track_merge_Y': 1,
    'switch_gate': 1,
    'spinner_rotor': 1,
    'spinner_post': 2,
    'spinner_retainer': 1,
    'lift_test_base': 1,
    'fit_coupon': 1,
}


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def export_stl(name, man):
    tm = to_trimesh(man)
    path = STL / f'{name}.stl'
    tm.export(str(path), file_type='stl')
    bb = tm.bounds
    ext = (bb[1] - bb[0]).tolist()
    return dict(path=str(path), verts=int(len(tm.vertices)), faces=int(len(tm.faces)),
                volume_mm3=float(tm.volume), watertight=bool(tm.is_watertight),
                bbox_min=bb[0].tolist(), bbox_max=bb[1].tolist(), extents_mm=ext,
                euler=int(tm.euler_number) if hasattr(tm, 'euler_number') else None)


def main():
    A.build_catalogue()
    manifest = dict(
        name='Hand-Cranked Marble Factory',
        version=VERSION,
        generated=datetime.now().astimezone().isoformat(timespec='seconds'),
        timezone='America/Denver',
        printer='Bambu Lab H3C (generic 0.4 mm / 0.20 mm PLA validation — not an official H3C profile)',
        ball_diameter_mm=35.0,
        disclaimer=(
            'Unprinted prototype. Geometry, clearance and slicer checks are computational only. '
            'Physical fit of moving parts and rolling behavior are unproven until printed and tested. '
            'Not a certified toy. 35 mm printed balls are large, but this kit is not evaluated or '
            'certified for child safety (pinch points at the lift and spinner remain; adult supervision '
            'required). Not intended for children under 3.'
        ),
        mechanism=dict(
            elevator='6-paddle wheel, R_hub=70, R_paddle=105, guided by a concentric outer wall R=108 '
                     'from -120° to +98°. Pickup in a bottom sump; a paddle sweeps the ball up between '
                     'hub and guide; at the 97° tangent the ball rolls onto a 7° descending chute that '
                     'nests into the first track.',
            anti_reverse='Gravity pawl on a pin at 116 mm / 185°; forward (CCW) lifts the pawl, reverse '
                         'drives the tip into a stop post.',
            switch='Removable bridge-gate over a 45° drop shelf. Gate in: ball stays on path A (-12 mm). '
                   'Gate out: ball rolls off the shelf and drops 40 mm into path B.',
            spinner='Overhead 4-paddle rotor on integral stubs that drop into open U-slots; a retainer '
                    'bar captures the stubs. Balls push the paddles as they roll under (H=36, Rp=30).',
        ),
        clearances_mm=dict(
            track_peg_r=9.7, stand_socket_r=10.2, peg_socket_radial=0.5,
            stand_peg_r=9.7, tile_socket_r=10.2,
            wheel_hex_af=16.0, wheel_hex_hole_af=16.4,
            crank_hex_af=13.0, crank_hex_hole_af=13.4,
            axle_jBack_r=11.0, housing_back_hole_r=11.4,
            axle_jFront_r=8.75, housing_front_hole_r=9.15,
            clip_groove_r=4.75, clip_seat_r=4.95, clip_throat=8.9,
            spinner_stub_r=4.0, spinner_slot_halfwidth=4.4,
            guide_radial_on_ball='RG-RH-2*RB = 108-70-35 = 3 mm total (ball sits on hub, ~3 mm to guide)',
            chute_slope_deg=7.0, track_slope_deg=round(math.degrees(math.atan(20 / 160)), 2),
            track_slope_note='20 mm drop per 160 mm on the default loop. The 12 mm figure belongs to the older switch/merge extras, not this circuit.',
            inlet_slope_deg=round(math.degrees(math.atan(A.INLET_DROP / A.INLET_L)), 2),
        ),
        layout=dict(joints={k: dict(xy=list(v), zv=round(A.ZV[k], 3),
                                    stand_cap=round(A.ZV[k] - 6.0, 3))
                            for k, v in A.XY.items()},
                    lift_origin=A.LIFT_POS.tolist(),
                    nest_x_lift_local=A.NEST_X,
                    inlet_length=A.INLET_L, inlet_drop=A.INLET_DROP,
                    tiles=[[x0, y0] for x0 in (-360, -120, 120) for y0 in (-40, 200)]),
        parts=[],
        moving_pivots=[],
        first_print=['fit_coupon', 'lift_test_base', 'lift_housing_back', 'lift_housing_front',
                     'lift_wheel_half', 'lift_axle', 'lift_crank', 'lift_clip', 'lift_pawl',
                     'stand_J11_h025', 'lift_inlet_chute', 'ball_35'],
    )
    assembly = dict(version=VERSION, units='mm', instances=[])
    scene_geo = {}

    print('exporting STLs ...')
    for name, meta in A.CAT.items():
        qty = max(len(meta['inst']), QTY_PRINT.get(name, 0))
        if qty == 0:
            continue
        man = A.print_mesh(name)
        info = export_stl(name, man)
        info.update(dict(
            name=name, qty=qty, color=meta['color'], supports=meta['supports'],
            brim=meta['brim'] or name.startswith('stand_') or name in (
                'spinner_rotor', 'lift_axle', 'lift_clip'),
            desc=meta['desc'],
        ))
        # recommend brim on tall stands and small-footprint parts
        if name.startswith('stand_') or name in ('spinner_rotor', 'lift_clip', 'lift_axle'):
            info['brim'] = True
        manifest['parts'].append(info)
        print(f'  {name:28s} qty={qty}  {info["extents_mm"][0]:6.1f}x{info["extents_mm"][1]:5.1f}x{info["extents_mm"][2]:5.1f}  wt={info["watertight"]}')

        Pinv = np.linalg.inv(meta['P'])
        for k, inst in enumerate(meta['inst']):
            M = inst['M']
            if M is None:
                continue
            W = M @ Pinv  # print -> world
            assembly['instances'].append(dict(
                part=name, index=k, at=inst.get('at'),
                transform=W.tolist(),
                color=meta['color'],
            ))
            tm = trimesh.load(str(STL / f'{name}.stl'))
            tm.apply_transform(W)
            rgba = list(hex_rgb(meta['color'])) + [255]
            tm.visual.face_colors = rgba
            scene_geo[f'{name}_{k}'] = tm

    # place 6 balls along the loop for the preview 3MF (not a motion claim)
    ball = trimesh.load(str(STL / 'ball_35.stl'))
    preview_centers = []
    try:
        loop, _segs = A.default_ball_path()
        pick = np.linspace(0, len(loop) - 1, 6).astype(int)
        preview_centers = [loop[i] for i in pick]
    except Exception as e:
        print('ball path preview failed:', e)
        preview_centers = [(80, 0, 50)] * 6
    Pball = A.CAT['ball_35']['P']
    for i, c in enumerate(preview_centers):
        W = np.eye(4)
        # print ball has its flat near min-z; center of sphere in print frame
        pb = apply(A.model_of('ball_35'), Pball)
        bb = pb.bounding_box()
        # sphere centre in print frame is close to (0,0,17) after to_bed
        print_center = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2 + 0.25])
        W[:3, 3] = np.array(c) - print_center
        tm = ball.copy()
        tm.apply_transform(W)
        tm.visual.face_colors = [255, 71, 87, 255]
        scene_geo[f'ball_preview_{i}'] = tm
        assembly['instances'].append(dict(part='ball_35', index=i, at='preview',
                                          transform=W.tolist(), color='#FF4757'))

    manifest['moving_pivots'] = [
        dict(name='lift_wheel', origin=A.LIFT_POS.tolist(), axis=[0, 1, 0],
             motion='child turns crank CCW (viewed from +y); wheel lifts balls on rising side (+x)'),
        dict(name='lift_crank', origin=(A.LIFT_POS + np.array([0, (29.5 + 39.5) / 2, 0])).tolist(),
             axis=[0, 1, 0], motion='fixed to axle'),
        dict(name='lift_pawl', origin=(A.LIFT_POS + np.array([L_Q()[0], 0, L_Q()[1]])).tolist(),
             axis=[0, 1, 0], motion='gravity returns to rest; forward paddles push it CW out of the way'),
    ]
    manifest['ball_center_paths_note'] = (
        'Default-loop ball-centre path from assembly.default_ball_path() and the lift 2D log '
        'are in reports/ball_paths.json. Track slope is 20 mm drop per 160 mm (7.13°), matching '
        'the 7° exit chute; inlet is about 8°.'
    )

    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    (OUT / 'assembly.json').write_text(json.dumps(assembly, indent=2))

    print('writing 3MF ...')
    scene = trimesh.Scene(scene_geo)
    scene.export(str(OUT / 'marble_factory_assembly.3mf'))

    readme = build_readme(manifest)
    (OUT / 'README.md').write_text(readme)
    (ROOT / 'README.md').write_text(readme)

    zip_path = ROOT / 'marble-factory-kit.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(STL.glob('*.stl')):
            z.write(p, arcname=f'stl/{p.name}')
        z.write(OUT / 'manifest.json', arcname='manifest.json')
        z.write(OUT / 'assembly.json', arcname='assembly.json')
        z.write(OUT / 'README.md', arcname='README.md')
        z.write(OUT / 'marble_factory_assembly.3mf', arcname='marble_factory_assembly.3mf')
        notes = OUT / 'SUPPORT_NOTES.md'
        notes.write_text(support_notes(manifest))
        z.write(notes, arcname='SUPPORT_NOTES.md')
    print('ZIP', zip_path, zip_path.stat().st_size)
    return manifest


def L_Q():
    import lift as L
    return L.Qpt()


def T_ax():
    import tracks as T
    return T.spinner_axis_local()


def _spinner_axis():
    M = A.CAT['track_spinner']['inst'][0]['M']
    # local +y (track left) is the rotor axis
    v = M[:3, :3] @ np.array([0.0, 1.0, 0.0])
    return v.tolist()


def support_notes(manifest):
    lines = ['# Support & print notes\n',
             'Generic 0.4 mm nozzle, 0.20 mm layer, PLA. Re-slice in Bambu Studio with the official H3C profile before printing. '
             'Do not use the validation G-code on the machine.\n']
    for p in manifest['parts']:
        flag = []
        if p['supports']:
            flag.append('SUPPORTS REQUIRED')
        if p.get('brim'):
            flag.append('brim recommended')
        extra = ('; '.join(flag) + ' — ') if flag else ''
        lines.append(f"- `{p['name']}` x{p['qty']}: {extra}{p['desc']}\n")
    lines.append('\n## Track orientation\n')
    lines.append('Tracks print rim-down. The V-floor is two 45° faces (printable without supports). Underside pockets open toward the top of the print.\n')
    lines.append('\n## Balls\n')
    lines.append('A full 35 mm sphere with a 0.5 mm bed flat needs supports (or print two hemispheres and glue — this kit does not include hemisphere STLs). '
                 'First-layer contact is only the 0.5 mm flat plus whatever the support raft provides.\n')
    return ''.join(lines)


def build_readme(manifest):
    parts_tbl = ['| Part | Qty | Color | Size (mm) | Supports | Notes |',
                 '|---|---:|---|---|---|---|']
    for p in manifest['parts']:
        e = p['extents_mm']
        parts_tbl.append(
            f"| `{p['name']}` | {p['qty']} | {p['color']} | {e[0]:.1f} × {e[1]:.1f} × {e[2]:.1f} | "
            f"{'yes' if p['supports'] else 'no'}{' + brim' if p.get('brim') else ''} | {p['desc']} |")
    return f"""# Hand-Cranked Marble Factory

> **Unprinted prototype.** The default circuit is a computationally coherent loop: lift → downhill straights and swept right-hand corners → inlet → lift. Headings are continuous, the sampled ball-centre path has no uphill, the chute nest volume is 0 mm³, synchronized 3D carry vs the moving wheel/housing cleared, and all 32 unique parts sliced. Physical rolling and snap-fit remain untested. Not a certified toy.

Version {VERSION}. Built {manifest['generated']} ({manifest['timezone']}).

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

{chr(10).join(parts_tbl)}

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
"""


if __name__ == '__main__':
    main()
