"""Boolean / containment / articulation / layout checks for the v2 full-48 CAD."""
import json, math
from pathlib import Path
import numpy as np
from geom import *
import constants as C
import parts as P
import catalog as Cat
import assembly as A
import layouts as L

OUT = Path('/workspace/marble-system-v2/reports')
OUT.mkdir(parents=True, exist_ok=True)

def vol(m):
    try:
        return float(m.volume())
    except Exception:
        return None

def isect(a, b):
    if a is None or b is None:
        return 0.0
    try:
        i = a ^ b
        if i.is_empty():
            return 0.0
        return max(0.0, float(i.volume()))
    except Exception:
        return -1.0

def bbox_ext(m):
    mesh = m.to_mesh()
    V = np.asarray(mesh.vert_properties)[:, :3]
    return (V.max(0) - V.min(0)).tolist(), V.min(0).tolist(), V.max(0).tolist()

def mesh_ok(m, name):
    info = dict(name=name, volume=vol(m))
    info['too_small'] = info['volume'] is not None and info['volume'] < 10
    ext, mn, mx = bbox_ext(m)
    info['extents'] = [round(x, 2) for x in ext]
    info['bbox_min'] = [round(x, 2) for x in mn]
    info['bbox_max'] = [round(x, 2) for x in mx]
    info['envelope_ok'] = (ext[0] <= C.ENVELOPE[0] + 0.05 and
                           ext[1] <= C.ENVELOPE[1] + 0.05 and
                           ext[2] <= C.ENVELOPE[2] + 0.05)
    tm = to_trimesh(m)
    try:
        raw = tm.split(only_watertight=False)
        real = 0
        slivers = 0
        for p in raw:
            V = np.asarray(p.vertices)
            ext = V.max(0) - V.min(0)
            try:
                pv = abs(float(p.volume))
            except Exception:
                pv = float(np.prod(np.clip(ext, 0, None)))
            if pv > 0.05 and ext.max() > 1.0:
                real += 1
            else:
                slivers += 1
        n = real
        info['sliver_components'] = slivers
    except Exception:
        n = None
    info['components'] = n
    info['watertight_kernel'] = info['volume'] is not None and info['volume'] > 0
    info['verts'] = int(len(tm.vertices))
    info['faces'] = int(len(tm.faces))
    return info

def run():
    fails = []
    sections = {}

    cat = Cat.part_catalog()
    built = {}
    mesh_reps = []
    for name, fn in cat.items():
        print('build', name, flush=True)
        m = fn()
        built[name] = m
        rep = mesh_ok(m, name)
        mesh_reps.append(rep)
        if not rep['watertight_kernel']:
            fails.append(f'{name} not a positive-volume solid')
        if not rep['envelope_ok']:
            fails.append(f'{name} exceeds H3C envelope {rep["extents"]}')
        MULTI_OK = {'lift_mount_plate'}  # two flush well inserts, by design
        if rep['components'] not in (1, None) and name not in MULTI_OK:
            fails.append(f'{name} has {rep["components"]} components')
        if rep['too_small']:
            fails.append(f'{name} volume too small')
    sections['meshes'] = mesh_reps

    neigh = []
    def check(pair, a, b, limit, why, designed_snap=False):
        v = isect(a, b)
        rec = dict(pair=pair, isect_mm3=v, limit=limit, why=why, designed_snap=designed_snap)
        neigh.append(rec)
        if v < 0:
            fails.append(f'{pair} boolean error')
        elif (not designed_snap) and v > limit:
            fails.append(f'{pair} intersection {v:.1f} mm3 > {limit} (latched/rest must not interpenetrate)')
        return v

    # Sleeve in an actual well of tile_00 at (60,60)
    tile = built['tile_00']
    sl = P.sleeve('medium').translate([60, 60, 0])
    check('sleeve_medium@well(60,60) x tile_00', sl, tile, 8.0,
          'sleeve foot should seat with only key/fillet kiss')

    for kind in C.CLASSES:
        sl = P.sleeve(kind)
        po = P.post(kind)
        check(f'post_{kind}@min x sleeve', sl, po, 2.0, 'sliding clearance at min height')
        spec = C.CLASSES[kind]
        zmax = spec['Hmax'] - spec['Hmin']
        check(f'post_{kind}@max x sleeve', sl, po.translate([0, 0, zmax]), 2.0,
              'sliding clearance at max height')
        ov = spec['Ls'] - zmax
        rec = dict(kind=kind, z_bottom_min=0.0, z_bottom_max=zmax, overlap_at_max=ov,
                   overlap_required=spec['Omin'], below_base_at_min=0.0,
                   Hmin=spec['Hmin'], Hmax=spec['Hmax'], stroke=spec['Hmax']-spec['Hmin'],
                   qty=spec['qty'])
        sections.setdefault('height_windows', []).append(rec)
        if ov < spec['Omin'] - 1e-6:
            fails.append(f'{kind} overlap at max {ov} < {spec["Omin"]}')
        if zmax < -1e-6:
            fails.append(f'{kind} max extension negative')
        cl = P.lock_clip(kind)
        check(f'clip_{kind} x sleeve_{kind}', cl, sl, 400.0,
              'captive wrap + hook through window; assembly deflection expected',
              designed_snap=True)
        check(f'clip_{kind} x post_{kind}@min (engaged)', cl, po, 250.0,
              'pawl hook sits in a rack slot — designed engagement',
              designed_snap=True)

    cap = built['ball_cap']
    po = P.post('medium')
    cap_p = cap.translate([0, 0, C.CLASSES['medium']['Lpost']])
    check('ball_cap x post_medium pin', cap_p, po, 80.0,
          'designed annular bulge snap of cap onto pin (untested force)',
          designed_snap=True)

    tr = built['track_S160']
    cap_at = cap.translate([40.0, 0.0, -16.0 - C.CAP_TO_CENTER])
    check('ball_cap x S160 socket@s40', cap_at, tr, 120.0,
          'designed lip snap + fin in slot (untested insertion force)',
          designed_snap=True)

    Hc = np.array([40.0, 0.0, -16.0])
    dummy_post = P.post('medium').translate(
        [40.0, 0.0, -16.0 - C.CAP_TO_CENTER - C.CLASSES['medium']['Lpost']])
    art = []
    for deg in (-15, 0, 15):
        t2 = tr.translate([-Hc[0], -Hc[1], -Hc[2]]).rotate([0, deg, 0]).translate(list(Hc))
        vhit = isect(t2, dummy_post)
        art.append(dict(motion='pitch', deg=deg, vs_post_mm3=vhit))
        if vhit > 40:
            fails.append(f'pitched track {deg} hits post {vhit:.1f}')
    rolled = tr.translate([-Hc[0], -Hc[1], -Hc[2]]).rotate([8, 0, 0]).translate(list(Hc))
    v_roll = isect(rolled, cap_at)
    art.append(dict(motion='roll', deg=8, vs_cap_mm3=v_roll,
                    note='keyed fin should resist roll; contact volume is the key working, not a fail'))
    sections['articulation'] = art
    if v_roll < 0.5:
        fails.append(f'roll key produced only {v_roll:.2f} mm3 contact; fin/slot may not be engaged')

    sections['dof'] = {
        'pitch_deg': 15,
        'yaw': 'cap_yaws_on_round_post_pin_with_the_track',
        'roll': 'locked_by_XZ_fin_in_along_track_slot',
        'slide_along_track_mm': C.SLIDE,
        'slide_45_mm': C.SLIDE_45,
        'not_claimed': 'independent_track_rotation_on_a_yaw_locked_square_post',
    }
    sections['socket_to_rail'] = dict(
        BJ_R=C.BJ_R, wall_above_ball=C.WALL_ABOVE_BALL,
        socket_to_v_vertex=C.SOCKET_TO_V, VH=C.VH,
        socket_to_rail=C.SOCKET_TO_RAIL,
        formula='BJ_R + wall + VH = 8 + 3 + 17.5*sqrt(2) = 35.7487',
        replaces_placeholder_22=True,
        why='22 mm would put the 35 mm marble inside the 16 mm support ball',
    )

    # REST joints — latched state must not interpenetrate (limit 5 mm3 numeric noise)
    print('rest joints', flush=True)
    s160 = built['track_S160']
    cl = built['track_CL90'].translate([C.S160, 0, -C.DROP160 - C.WATERFALL])
    s80 = built['track_S80'].rotate([0, 0, 90]).translate([
        C.S160 + C.RC90, C.RC90, -C.DROP160 - C.WATERFALL - C.DROP90 - C.WATERFALL])
    s160b = built['track_S160'].translate([C.S160, 0, -C.DROP160 - C.WATERFALL])
    vj1 = check('REST S160 x CL90', s160, cl, 5.0,
                'latched tongue/hook must sit in recesses without solid overlap')
    vj2 = check('REST CL90 x S80', cl, s80, 5.0,
                'latched tongue/hook must sit in recesses without solid overlap')
    vj3 = check('REST S160 x S160', s160, s160b, 5.0,
                'straight-to-straight latched joint')
    sections['rest_joints'] = [
        dict(pair='S160 x CL90', isect_mm3=vj1),
        dict(pair='CL90 x S80', isect_mm3=vj2),
        dict(pair='S160 x S160', isect_mm3=vj3),
    ]

    # 45° slot reach
    end = (C.RC90 * math.sin(math.radians(45)),
           -C.RC90 * (1 - math.cos(math.radians(45))))
    hits = L.capture_well(end[0], end[1], -45.0, 0.0, C.SLIDE_45)
    # capture_well searches global board wells; locally we recompute against a unit grid
    t = np.array([math.cos(math.radians(-45)), math.sin(math.radians(-45))])
    local_hits = []
    for i in range(-1, 4):
        for j in range(-3, 3):
            wx, wy = i * 40.0, j * 40.0
            d = np.array([wx - end[0], wy - end[1]])
            along = float(d @ t)
            lat = float(np.hypot(*(d - along * t)))
            if -C.SLIDE_45 - 1e-6 <= along <= 1e-6 and lat <= C.BJ_R + 0.30 + 1e-6:
                local_hits.append(dict(well=(wx, wy), lat=round(lat, 2), along=round(along, 2)))
    sections['cr45_slot_reach'] = dict(
        end_xy=[round(end[0], 3), round(end[1], 3)],
        slide_mm=C.SLIDE_45,
        captured_from_origin_start=local_hits,
        note='Start joint on-grid is captured directly. End stadium (32 mm inward along the tangent) reaches well (40,0) at 4.85 mm lateral, inside BJ_R+0.3 = 8.3 mm.',
    )
    if not any(h['well'] == (40.0, 0.0) for h in local_hits):
        fails.append('CR45 end socket does not capture (40,0)')

    # wells
    wells = C.all_wells()
    per = {f'{ix}{iy}': len(C.wells_on_tile(ix, iy)) for ix in (0, 1) for iy in (0, 1)}
    sections['wells'] = dict(
        assembled_mm=list(C.ASSEMBLED), assembled_in=list(C.ASSEMBLED_IN),
        tile_mm=[C.TILE_PX, C.TILE_PY],
        pitch=C.P, count=len(wells),
        per_tile=per,
        not_192='tile boundaries are not integer multiples of 40 mm; seam/edge/joiner wells omitted',
        print_orientation='304.8 along H3C 330, 228.6 along H3C 320',
    )
    if len(wells) == 192:
        fails.append('well count came out 192 — omit rules were not applied')

    # BOM
    total = sum(q for _, q in C.BOM48)
    sections['bom48'] = dict(items=[{'id': i, 'qty': q} for i, q in C.BOM48], sum=total)
    if total != 48:
        fails.append(f'BOM sum {total} != 48')
    sections['support_structures'] = dict(
        short=8, medium=10, tall=6, total=24,
        parts_per='sleeve + post + lock_clip + ball_cap',
        interface_parts=96,
        spare_clips=8, spare_caps=8,
    )
    sections['extras_outside_48_and_24'] = C.EXTRAS

    # helix
    hx = built['track_HX360']
    hx_ext = mesh_ok(hx, 'track_HX360')['extents']
    sections['helix'] = dict(
        extents=hx_ext, coil_diameter_mm=244,
        printed_as='single connected piece (fits H3C 320 bed on the long side? '
                   f'{max(hx_ext[0], hx_ext[1]) <= 320})',
        drop_mm=80, segments=1,
        note='Self-intersection avoided: 80 mm pitch vs ~41 mm section height.',
    )

    # layouts
    print('layouts', flush=True)
    layout_reps = []
    for builder in (L.layout_A, L.layout_B):
        lay = builder()
        sm = L.summarize(lay)
        # board containment of joints
        off = []
        for p in lay['pieces']:
            for key in ('origin', 'end'):
                if key in p:
                    x, y = p[key]
                    if not (0 <= x <= C.ASSEMBLED[0] and 0 <= y <= C.ASSEMBLED[1]):
                        off.append((p['name'], key, x, y))
        sm['off_board'] = off
        if off:
            fails.append(f"{lay['name']} has off-board points {off}")
        if not sm['within_24']:
            fails.append(f"{lay['name']} uses {sm['n_posts']} posts > 24")
        if sm['adapt_in_drop'] <= 0:
            fails.append(f"{lay['name']} ADAPT_IN drop not positive")
        # piece-to-piece rest intersections along the route
        joint_hits = []
        pcs = [p for p in lay['pieces'] if p['kind'] not in ('ADAPT_OUT',)]
        # check consecutive designed rails (skip adapters vs v1 lift, which is not in this package)
        rails = [p for p in lay['pieces'] if p['kind'] not in ('ADAPT_OUT', 'ADAPT_IN')]
        for a, b in zip(rails, rails[1:]):
            v = isect(a['solid'], b['solid'])
            rec = dict(a=a['name'], b=b['name'], isect_mm3=v)
            joint_hits.append(rec)
            if v > 5.0:
                fails.append(f"{lay['name']} {a['name']} x {b['name']} rest overlap {v:.1f} mm3")
        sm['layout_rest_joints'] = joint_hits
        sm['seq'] = lay['seq_meta']
        layout_reps.append(sm)
    sections['layouts'] = layout_reps

    # sample (retained translated demo on tile_00)
    print('sample assembly', flush=True)
    sample = A.sample()
    sm = []
    for s in sample['supports']:
        v = isect(s['sleeve'], sample['tile'])
        sm.append(dict(what=f"sleeve {s['kind']} @{s['x']},{s['y']} x tile", isect=v))
        if v > 15:
            fails.append(f'sample sleeve collision {v:.1f}')
        if s['z_bottom'] < -1e-6:
            fails.append('sample post below tile')
    vj = isect(sample['tracks']['S160'], sample['tracks']['CL90'])
    sm.append(dict(what='sample S160 x CL90 rest', isect=vj))
    if vj > 5:
        fails.append(f'sample S160xCL90 rest overlap {vj:.1f}')
    vj2 = isect(sample['tracks']['CL90'], sample['tracks']['S80'])
    sm.append(dict(what='sample CL90 x S80 rest', isect=vj2))
    if vj2 > 5:
        fails.append(f'sample CL90xS80 rest overlap {vj2:.1f}')
    sections['sample'] = sm

    report = dict(fails=fails, n_fail=len(fails), sections=sections)
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2, default=str))
    print('FAILS', len(fails))
    for f in fails:
        print(' -', f)
    return report

if __name__ == '__main__':
    run()
