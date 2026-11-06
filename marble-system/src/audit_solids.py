"""Standalone solids audit after the geom-fix pass.

Does not shrink the 35 mm ball. Reports raw intersection volumes.
Distinguishes designed snap preload (force unknown) from load-geometry clashes.
"""
import json, math, sys, subprocess
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / 'reports'
REP.mkdir(exist_ok=True)
TMP = Path('/tmp/v2_solids_audit')
TMP.mkdir(exist_ok=True)

def isect_vol(a, b):
    if a is None or b is None:
        return 0.0
    try:
        i = a ^ b
        if i.is_empty():
            return 0.0
        return max(0.0, float(i.volume()))
    except Exception:
        return -1.0

def isect_bbox(a, b):
    try:
        i = a ^ b
        if i.is_empty():
            return None
        mesh = i.to_mesh()
        V = np.asarray(mesh.vert_properties)[:, :3]
        if len(V) == 0:
            return None
        return dict(min=V.min(0).round(2).tolist(), max=V.max(0).round(2).tolist(),
                    center=((V.min(0)+V.max(0))/2).round(2).tolist())
    except Exception:
        return None

def export_v1_housings():
    v1 = Path(__file__).resolve().parents[2] / "marble-factory" / "src"
    script = f'''
import sys
sys.path.insert(0, {str(v1)!r})
from geom import to_trimesh
import lift as L
hb = L.housing_back()
hf = L.housing_front()
to_trimesh(hb).export("/tmp/v2_solids_audit/v1_housing_back.stl")
to_trimesh(hf).export("/tmp/v2_solids_audit/v1_housing_front.stl")
print("VOL", float(hb.volume()), float(hf.volume()))
print("INLET_CZ", L.INLET_CZ, "H_AXLE", L.H_AXLE, "CHUTE_END", L.CHUTE_END_X)
print("INLET_NOSE_BOTTOM", L.inlet_nose_bottom())
print("RB", L.RB, "RG", L.RG, "PLATE_IN", L.PLATE_IN)
'''
    p = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
    print(p.stdout)
    if p.returncode != 0:
        print(p.stderr)
        raise RuntimeError('v1 housing export failed')
    return p.stdout

def load_stl_as_manifold(path):
    import trimesh
    from geom import mesh_to_manifold
    tm = trimesh.load(str(path), force='mesh')
    return mesh_to_manifold(tm.vertices, tm.faces)

def place_lift(man, axle_xy, H_AXLE=136.0):
    return man.translate([axle_xy[0], axle_xy[1], H_AXLE])

def ball_at(x, y, z, seg=32):
    from geom import M
    return M.sphere(17.5, seg).translate([x, y, z])

def classify(vol, designed_snap=False):
    if vol < 0:
        return 'boolean_error'
    if designed_snap:
        return 'designed_snap_preload_force_unknown'
    if vol <= 5.0:
        return 'numeric_or_empty'
    if vol <= 50.0:
        return 'small_contact_or_tessellation'
    if vol <= 200.0:
        return 'material_nibble'
    return 'CRITICAL_CLASH'

def _summarize_samples(rows):
    by = {}
    for r in rows:
        by.setdefault(r['piece'], []).append(r)
    per = {}
    worst = dict(isect_mm3=-1)
    for k, rs in by.items():
        vols = [r['isect_mm3'] for r in rs if r['isect_mm3'] >= 0]
        top = sorted(rs, key=lambda r: r['isect_mm3'], reverse=True)[:3]
        per[k] = dict(n=len(rs), max=max(vols) if vols else None,
                      mean=round(sum(vols)/len(vols), 2) if vols else None,
                      n_over_50=sum(1 for v in vols if v > 50),
                      n_over_200=sum(1 for v in vols if v > 200),
                      top=top)
        for r in rs:
            if r['isect_mm3'] > worst.get('isect_mm3', -1):
                worst = r
    return per, worst

def layout_A_ball_path(C):
    """Ball-centre samples. Through a joint the sphere rides the sending V
    (V-tongue) until s exceeds TONGUE; ADAPT_IN then holds that height for
    TONGUE+2 mm before dropping (matches the solid). Height is V+VH, no shrink."""
    VH, WF, ZV0 = C.VH, C.WATERFALL, C.V1_ZV_J0
    samples = []

    def add_straight(name, origin, hdg, z0, L, drop, ds=8.0, prev_endV=None, z_fn=None):
        ca, sa = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
        s = 0.0
        while s <= L + 1e-6:
            x = origin[0] + ca * s
            y = origin[1] + sa * s
            if z_fn is not None:
                V = z0 + z_fn(s)
            elif prev_endV is not None and s <= C.TONGUE + 0.6:
                V = prev_endV
            else:
                V = z0 - drop * s / L
            near = (s < 16) or (s > L - 16)
            samples.append(dict(piece=name, s=round(s, 2), xyz=(x, y, V + VH),
                                V=V, near_joint=near))
            s += 3.0 if near else ds

    def add_corner(name, origin, hdg, z0, drop, turn='R', n=36, prev_endV=None):
        sgn = -1 if turn == 'R' else 1
        R = C.RC90
        ca0, sa0 = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
        for i in range(n):
            a = math.radians(90 * i / (n - 1))
            arc = R * a
            lx, ly = R * math.sin(a), sgn * R * (1 - math.cos(a))
            x = origin[0] + ca0 * lx - sa0 * ly
            y = origin[1] + sa0 * lx + ca0 * ly
            if prev_endV is not None and arc <= C.TONGUE + 0.6:
                V = prev_endV
            else:
                V = z0 - drop * i / (n - 1)
            near = i < 4 or i > n - 5
            samples.append(dict(piece=name, s=round(arc, 2), xyz=(x, y, V + VH),
                                V=V, near_joint=near))

    seq = [
        ('S160_1', (300.0, 100.0), 180.0, C.DROP160, 160.0, 'S'),
        ('CR1', (140.0, 100.0), 180.0, C.DROP90, None, 'CR'),
        ('S160_2', (60.0, 180.0), 90.0, C.DROP160, 160.0, 'S'),
        ('CR2', (60.0, 340.0), 90.0, C.DROP90, None, 'CR'),
        ('S160_3', (140.0, 420.0), 0.0, C.DROP160, 160.0, 'S'),
        ('S80_1', (300.0, 420.0), 0.0, C.DROP80, 80.0, 'S'),
        ('CR3', (380.0, 420.0), 0.0, C.DROP90, None, 'CR'),
        ('S160_4', (460.0, 340.0), 270.0, C.DROP160, 160.0, 'S'),
    ]
    prev_end = ZV0
    zs = []
    for i, (name, o, h, drop, L, kind) in enumerate(seq):
        z0 = ZV0 if i == 0 else prev_end - WF
        prevV = None if i == 0 else prev_end
        if kind == 'S':
            add_straight(name, o, h, z0, L, drop, prev_endV=prevV)
        else:
            add_corner(name, o, h, z0, drop, 'R', prev_endV=prevV)
        prev_end = z0 - drop
        zs.append((name, z0, prev_end))

    adapt_z = prev_end - WF
    adapt_drop = adapt_z - C.V1_INLET_ZV_END
    hold = C.TONGUE + 2.0
    L_in = C.V1_INLET_L
    def z_fn(s):
        return 0.0 if s <= hold else -adapt_drop * (s - hold) / (L_in - hold)
    add_straight('ADAPT_IN', (460.0, 180.0), 270.0, adapt_z, L_in, adapt_drop,
                 ds=5.0, prev_endV=prev_end, z_fn=z_fn)
    return samples, zs, adapt_z, adapt_drop


def layout_B_ball_path(C, layB):
    VH, WF = C.VH, C.WATERFALL
    samples = []
    pcs = {p['name']: p for p in layB['pieces']}

    def add_helix(p, prev_endV):
        R = 90.0
        drop = p['drop']
        n = 48
        ca, sa = math.cos(math.radians(p['hdg'])), math.sin(math.radians(p['hdg']))
        ox, oy = p['origin']
        for i in range(n):
            a = 2 * math.pi * i / (n - 1)
            arc = R * a
            lx = R * math.sin(a)
            ly = -R * (1.0 - math.cos(a))
            x = ox + ca * lx - sa * ly
            y = oy + sa * lx + ca * ly
            if prev_endV is not None and arc <= C.TONGUE + 0.6:
                V = prev_endV
            else:
                V = p['z0'] - drop * i / (n - 1)
            samples.append(dict(piece='HX1', s=round(arc, 2), xyz=(x, y, V + VH),
                                V=V, near_joint=(i < 3 or i > n - 4)))
        endV = p['z0'] - drop
        for s in np.linspace(0, 40, 6):
            x = ox + ca * float(s)
            y = oy + sa * float(s)
            samples.append(dict(piece='HX1_stub', s=round(float(s), 2),
                                xyz=(x, y, endV + VH), V=endV, near_joint=True))

    prev_end = C.V1_ZV_J0
    started = False
    after = []
    for p in layB['pieces']:
        if p['name'] in ('ADAPT_OUT', 'ADAPT_IN'):
            continue
        if p['kind'] == 'HX360R':
            add_helix(p, None if not started else prev_end)
            prev_end = p['z0'] - p['drop']
            started = True
            continue
        after.append((p, None if not started else prev_end))
        prev_end = p['z0'] - p['drop']
        started = True
    saved_after = after
    def add_straight(name, origin, hdg, z0, L, drop, prev_endV):
        ca, sa = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
        s = 0.0
        while s <= L + 1e-6:
            V = prev_endV if (prev_endV is not None and s <= C.TONGUE + 0.6) else z0 - drop * s / L
            samples.append(dict(piece=name, s=round(s, 2),
                                xyz=(origin[0] + ca * s, origin[1] + sa * s, V + VH),
                                V=V, near_joint=(s < 16 or s > L - 16)))
            s += 3.0 if (s < 16 or s > L - 16) else 8.0
    def add_corner(name, origin, hdg, z0, drop, prev_endV):
        R = C.RC90
        ca0, sa0 = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
        n = 28
        for i in range(n):
            a = math.radians(90 * i / (n - 1))
            arc = R * a
            lx, ly = R * math.sin(a), -R * (1 - math.cos(a))
            x = origin[0] + ca0 * lx - sa0 * ly
            y = origin[1] + sa0 * lx + ca0 * ly
            V = prev_endV if (prev_endV is not None and arc <= C.TONGUE + 0.6) else z0 - drop * i / (n - 1)
            samples.append(dict(piece=name, s=round(arc, 2), xyz=(x, y, V + VH),
                                V=V, near_joint=(i < 3 or i > n - 4)))
    for p, held in saved_after:
        Llen = {'S160': 160.0, 'S80': 80.0, 'S40': 40.0}.get(p['kind'])
        if Llen:
            add_straight(p['name'], p['origin'], p['hdg'], p['z0'], Llen, p['drop'], held)
        else:
            add_corner(p['name'], p['origin'], p['hdg'], p['z0'], p['drop'], held)
    ai = pcs['ADAPT_IN']
    hold = C.TONGUE + 2.0
    L_in = C.V1_INLET_L
    drop = ai['drop']
    def z_fn(s):
        return 0.0 if s <= hold else -drop * (s - hold) / (L_in - hold)
    ca, sa = math.cos(math.radians(ai['hdg'])), math.sin(math.radians(ai['hdg']))
    s = 0.0
    while s <= L_in + 1e-6:
        V = ai['z0'] + z_fn(s)
        samples.append(dict(piece='ADAPT_IN', s=round(s, 2),
                            xyz=(ai['origin'][0] + ca * s, ai['origin'][1] + sa * s, V + C.VH),
                            V=V, near_joint=True))
        s += 5.0
    return samples


def sweep_samples(samples, route, tag=''):
    rows = []
    for i, sm in enumerate(samples):
        x, y, z = sm['xyz']
        v = isect_vol(ball_at(x, y, z), route)
        row = dict(i=i, piece=sm['piece'], s=sm['s'],
                   xyz=[round(x, 2), round(y, 2), round(z, 2)],
                   V=round(sm['V'], 2), near_joint=sm['near_joint'],
                   isect_mm3=round(v, 2) if v >= 0 else v,
                   class_=classify(v))
        rows.append(row)
        if i % 20 == 0:
            print(f"  {tag}sample {i}/{len(samples)} {sm['piece']} -> {v:.2f}", flush=True)
    return rows


def family_sweeps(C, Cat, P):
    """Guided 35 mm motions on every catalog track family in local frame."""
    out = []
    VH = C.VH

    def run(name, solid, samples, note=''):
        rows = []
        worst = 0.0
        loc = None
        for sm in samples:
            x, y, z = sm
            v = isect_vol(ball_at(x, y, z, seg=24), solid)
            rows.append((sm, v))
            if v > worst:
                worst, loc = v, sm
        out.append(dict(family=name, n=len(samples), max_mm3=round(worst, 2),
                        worst_xyz=[round(c, 2) for c in loc] if loc else None,
                        class_=classify(worst), note=note,
                        n_over_50=sum(1 for _, v in rows if v > 50),
                        n_over_200=sum(1 for _, v in rows if v > 200)))
        print(f"  family {name:16s} max={worst:8.2f}  {classify(worst)}  {note}", flush=True)

    for name, L, drop in (('S160', C.S160, C.DROP160), ('S80', C.S80, C.DROP80),
                          ('S40', C.S40, C.DROP40), ('SPAN240', 240.0, 30.0)):
        man = P.straight_track_r(L, drop)
        samp = [(s, 0.0, -drop * s / L + VH) for s in np.linspace(0, L, max(8, int(L / 16) + 1))]
        run(name, man, samp)

    for name, turn, ang, drop in (('CR90', 'R', 90.0, C.DROP90), ('CL90', 'L', 90.0, C.DROP90),
                                  ('CR45', 'R', 45.0, C.DROP45), ('CL45', 'L', 45.0, C.DROP45)):
        man = P.corner_track(turn, R=C.RC90, drop=drop, ang=ang)
        sgn = 1 if turn == 'L' else -1
        n = 20 if ang > 50 else 12
        samp = []
        for i in range(n):
            a = math.radians(ang * i / (n - 1))
            x = C.RC90 * math.sin(a)
            y = sgn * C.RC90 * (1 - math.cos(a))
            V = -drop * i / (n - 1)
            samp.append((x, y, V + VH))
        run(name, man, samp)

    # SPLIT_Y / SWITCH both branches
    def split_samples(drop_a=20.0, drop_b=35.0, L=160.0, off=80.0, n=16):
        a, b = [], []
        for i in range(n):
            x = L * i / (n - 1)
            a.append((x, 0.0, -drop_a * i / (n - 1) + VH))
            y = 0.5 * off * (1 - math.cos(math.pi * x / L))
            b.append((x, y, -drop_b * i / (n - 1) + VH))
        return a, b
    sa, sb = split_samples()
    run('SPLIT_Y_A', Cat.split_y(), sa, 'branch A')
    run('SPLIT_Y_B', Cat.split_y(), sb, 'branch B')
    run('SWITCH_A', Cat.switch_y(), sa, 'manual switch, gate out (both open); gate itself experimental')
    run('SWITCH_B', Cat.switch_y(), sb, 'manual switch branch B, gate out')
    sw = Cat.switch_y()
    down = Cat.pose_switch_gate('down')
    up = Cat.pose_switch_gate('up')
    def _max_ball(solid, samples):
        worst = 0.0
        for sm in samples:
            worst = max(worst, isect_vol(ball_at(*sm, seg=24), solid))
        return worst
    gate_note = dict(
        family='SWITCH_GATE',
        down_blocks_B_mm3=round(_max_ball(down, sb), 2),
        down_hits_A_mm3=round(_max_ball(down, sa), 2),
        up_hits_B_mm3=round(_max_ball(up, sb), 2),
        up_hits_A_mm3=round(_max_ball(up, sa), 2),
        detent_down_mm3=round(isect_vol(down, sw), 2),
        detent_up_mm3=round(isect_vol(up, sw), 2),
        note='down must meet the B ball and miss the A ball; up must miss both. Detent volumes are designed snap preload.',
    )
    gate_note['class_'] = (
        'designed_snap_preload_force_unknown'
        if gate_note['down_blocks_B_mm3'] > 200
        and gate_note['down_hits_A_mm3'] <= 5
        and gate_note['up_hits_B_mm3'] <= 5
        and gate_note['up_hits_A_mm3'] <= 5
        else 'CRITICAL_CLASH'
    )
    out.append(gate_note)
    print('  family SWITCH_GATE', gate_note['class_'],
          'B', gate_note['down_blocks_B_mm3'], 'A', gate_note['down_hits_A_mm3'],
          'upB', gate_note['up_hits_B_mm3'], 'detent', gate_note['detent_down_mm3'], flush=True)

    # MERGE_Y — both inlets fall to the shared exit. Sample those centrelines.
    try:
        L, off, drop_a, drop_b, z_b0 = 160.0, 80.0, 35.0, 20.0, -15.0
        ma, mb = [], []
        for i in range(16):
            x = L * i / 15
            y = off - 0.5 * off * (1 + math.cos(math.pi * x / L))
            ma.append((x, y, -drop_a * x / L + VH))
            mb.append((x, off, z_b0 - drop_b * i / 15 + VH))
        my = Cat.merge_y()
        run('MERGE_Y_A', my, ma, 'inlet A falls to the shared exit')
        run('MERGE_Y_B', my, mb, 'inlet B already lower, still downhill')
    except Exception as e:
        out.append(dict(family='MERGE_Y', error=str(e), note='experimental'))

    # FUNNEL centreline
    try:
        fun = Cat.funnel()
        samp = [(s, 0.0, -20.0 * s / 80.0 + VH) for s in np.linspace(0, 80, 10)]
        run('FUNNEL', fun, samp, 'simple gravity mouth; not a certified catch')
    except Exception as e:
        out.append(dict(family='FUNNEL', error=str(e), note='experimental'))

    # helix local
    hx = Cat.helix_360(turn='R')
    samp = []
    n = 36
    R, drop = 90.0, 80.0
    for i in range(n):
        a = 2 * math.pi * i / (n - 1)
        x = R * math.sin(a)
        y = -R * (1 - math.cos(a))
        samp.append((x, y, -drop * i / (n - 1) + VH))
    for s in np.linspace(0, 40, 5):
        samp.append((s, 0.0, -drop + VH))
    run('HX360R', hx, samp, 'one-piece descending helix')

    # DROP40: one continuous guided V (smoothstep plus a 2 mm exit ease).
    d40 = Cat.drop40()
    def drop_z(s, L=80.0, fall=40.0):
        u = s / L
        return -fall * (u * u * (3 - 2 * u)) - 2.0 * u
    run('DROP40', d40,
        [(s, 0.0, drop_z(s) + VH) for s in np.linspace(0, 80, 20)],
        'continuous guided descent, no bowl')

    run('TUN160', Cat.tun160(),
        [(s, 0.0, -C.DROP160 * s / C.S160 + VH) for s in np.linspace(0, C.S160, 10)],
        'roofed S160; roof is above the ball')

    # ADAPT_IN default
    drop = 23.2
    L = C.V1_INLET_L
    hold = C.TONGUE + 2.0
    def zloc(s):
        return 0.0 if s <= hold else -drop * (s - hold) / (L - hold)
    run('ADAPT_IN', Cat.adapt_in(drop),
        [(s, 0.0, zloc(s) + VH) for s in np.linspace(0, L, 14)],
        'hold through tongue then drop to v1 inlet')

    # ADAPT_OUT: ball along first 12 mm at local V=0 (track V); collar is below ball
    run('ADAPT_OUT', Cat.adapt_out(),
        [(s, 0.0, VH) for s in np.linspace(0.5, 12, 6)],
        'collar lives below ball bottom (v<=6.4 < VH-RB=7.25)')

    return out


def insertion_paths(C, P):
    rows = []
    sleeve = P.sleeve('medium')
    Lp = C.CLASSES['medium']['Lpost']
    for dz in (30.0, 15.0, 5.0, 0.0):
        post = P.post('medium').translate([0, 0, dz])
        v = isect_vol(post, sleeve)
        rows.append(dict(pair='post_into_sleeve', offset_mm=dz, isect_mm3=round(v, 2),
                         class_=classify(v), note='lowering post; seated at dz=0'))
    clip = P.lock_clip('medium')
    for dx in (14.0, 8.0, 3.0, 0.0):
        v = isect_vol(clip.translate([dx, 0, 0]), sleeve)
        rows.append(dict(pair='clip_into_window', offset_mm=dx, isect_mm3=round(v, 2),
                         class_=classify(v, designed_snap=(dx == 0.0 and v > 5)),
                         note='seated clip ears are a designed snap; force unknown'))
    post = P.post('medium')
    for dz in (12.0, 6.0, 2.0, 0.0):
        cap = P.ball_cap().translate([0, 0, Lp + dz])
        v = isect_vol(cap, post)
        rows.append(dict(pair='cap_onto_pin', offset_mm=dz, isect_mm3=round(v, 2),
                         class_=classify(v, designed_snap=(dz == 0.0)),
                         note='seated pin bulge is a designed snap (~12 mm3); force unknown'))
    for r in rows:
        print(f"  insert {r['pair']:20s} off={r['offset_mm']:5.1f}  {r['isect_mm3']:8.2f}  {r['class_']}", flush=True)
    return rows


def rec_pair(pairs, name, a, b, designed_snap=False, note=''):
    v = isect_vol(a, b)
    bb = isect_bbox(a, b) if v > 0.01 else None
    row = dict(pair=name, isect_mm3=round(v, 2) if v >= 0 else v,
               class_=classify(v, designed_snap), designed_snap=designed_snap,
               bbox=bb, note=note)
    pairs.append(row)
    print(f"  {name:48s} {v:10.2f}  {row['class_']}", flush=True)
    return v


def main():
    sys.path.insert(0, str(ROOT / 'src'))
    import constants as C
    import parts as P
    import catalog as Cat
    import layouts as Lyt

    report = dict(version='solids-audit-2-geomfix', notes=[])
    print('=== export v1 housings ===', flush=True)
    report['v1_export_log'] = export_v1_housings()
    hb0 = load_stl_as_manifold(TMP / 'v1_housing_back.stl')
    hf0 = load_stl_as_manifold(TMP / 'v1_housing_front.stl')

    print('=== build layout A ===', flush=True)
    layA = Lyt.layout_A()
    axle = layA['lift']['axle']
    hb = place_lift(hb0, axle)
    hf = place_lift(hf0, axle)
    housing = hb + hf
    pieces = {p['name']: p for p in layA['pieces']}

    pairs = []
    print('=== adapter vs v1 lift / first track ===', flush=True)
    rec_pair(pairs, 'ADAPT_OUT x housing_back', pieces['ADAPT_OUT']['solid'], hb,
             note='thin keel collar; must not eat chute walls')
    rec_pair(pairs, 'ADAPT_OUT x housing_front', pieces['ADAPT_OUT']['solid'], hf)
    rec_pair(pairs, 'ADAPT_OUT x S160_1', pieces['ADAPT_OUT']['solid'], pieces['S160_1']['solid'],
             note='collar inside first-track V')
    rec_pair(pairs, 'ADAPT_IN x housing_front', pieces['ADAPT_IN']['solid'], hf)
    rec_pair(pairs, 'ADAPT_IN x housing_back', pieces['ADAPT_IN']['solid'], hb)
    rec_pair(pairs, 'ADAPT_IN x S160_4', pieces['ADAPT_IN']['solid'], pieces['S160_4']['solid'],
             note='numeric coincident face historically ~7.5 mm3')
    rec_pair(pairs, 'S160_1 x housing_back (keel nest)', pieces['S160_1']['solid'], hb)
    rec_pair(pairs, 'lift_mount_plate x housing_back', layA['lift_mount_plate'], hb,
             designed_snap=True, note='teardrop pegs in r=10.2 holes')

    print('=== Layout A consecutive rest ===', flush=True)
    for a, b in zip(layA['pieces'], layA['pieces'][1:]):
        rec_pair(pairs, f"{a['name']} x {b['name']}", a['solid'], b['solid'], note='latched rest')

    print('=== Layout A 35 mm sweep (no shrink) ===', flush=True)
    samples, zs, adapt_z, adapt_drop = layout_A_ball_path(C)
    route = None
    for p in layA['pieces']:
        route = p['solid'] if route is None else (route + p['solid'])
    route_plus = route + housing
    ball_A = sweep_samples(samples, route_plus, tag='A ')
    per_A, worst_A = _summarize_samples(ball_A)
    print('A BALL WORST', worst_A, flush=True)

    print('=== Layout A seats / low_mounts ===', flush=True)
    seats = []
    for inst in layA['support_instances']:
        if inst['kind'] == 'low_mount':
            v_track = 0.0
            hit = None
            for p in layA['pieces']:
                vv = isect_vol(inst['solid'], p['solid'])
                if vv > v_track:
                    v_track, hit = vv, p['name']
            rec_s = dict(kind='low_mount', well=inst['well'], Hraw=inst.get('Hraw'),
                         heading=inst.get('heading'), H_ball=inst.get('H_ball'),
                         ball_x_track_mm3=round(v_track, 2), ball_x_track=hit,
                         class_=classify(v_track, designed_snap=True),
                         note='integrated keyed ball in existing socket; snap force unknown')
            seats.append(rec_s)
            print('  low_mount', rec_s, flush=True)
            continue
        kind, H = inst['kind'], inst['H']
        spec = C.CLASSES[kind]
        z_bottom = H - spec['Hmin']
        H_from_stack = z_bottom + spec['Lpost'] + C.CAP_TO_CENTER
        v_cap_post = isect_vol(inst['cap'], inst['post'])
        v_post_sleeve = isect_vol(inst['post'], inst['sleeve'])
        v_cap_track = 0.0
        hit_name = None
        v_post_track = 0.0
        post_hit = None
        for p in layA['pieces']:
            vv = isect_vol(inst['cap'], p['solid'])
            if vv > v_cap_track:
                v_cap_track, hit_name = vv, p['name']
            vp = isect_vol(inst['post'], p['solid'])
            if vp > v_post_track:
                v_post_track, post_hit = vp, p['name']
        rec_s = dict(
            well=inst['well'], kind=kind, H=H, Hraw=inst.get('Hraw'),
            z_bottom=z_bottom, H_from_stack=H_from_stack,
            stack_matches_H=abs(H_from_stack - H) < 0.05,
            cap_x_post_mm3=round(v_cap_post, 2),
            post_x_sleeve_mm3=round(v_post_sleeve, 2),
            cap_x_track_mm3=round(v_cap_track, 2), cap_x_track=hit_name,
            post_x_track_mm3=round(v_post_track, 2), post_x_track=post_hit,
            cap_x_post_class=classify(v_cap_post, designed_snap=True),
            cap_x_track_class=classify(v_cap_track, designed_snap=True),
            post_x_track_class=classify(v_post_track),
            note='cap/post bulge and cap/socket lip are designed snaps; post×track is load geometry',
        )
        seats.append(rec_s)
        print('  seat', rec_s, flush=True)

    print('=== build layout B ===', flush=True)
    layB = Lyt.layout_B()
    axleB = layB['lift']['axle']
    hbB = place_lift(hb0, axleB)
    hfB = place_lift(hf0, axleB)
    print('=== Layout B consecutive rest ===', flush=True)
    pairsB = []
    for a, b in zip(layB['pieces'], layB['pieces'][1:]):
        rec_pair(pairsB, f"{a['name']} x {b['name']}", a['solid'], b['solid'])
    rec_pair(pairsB, 'B ADAPT_OUT x housing_back',
             [p for p in layB['pieces'] if p['name'] == 'ADAPT_OUT'][0]['solid'], hbB)
    rec_pair(pairsB, 'B ADAPT_IN x housing_front',
             [p for p in layB['pieces'] if p['name'] == 'ADAPT_IN'][0]['solid'], hfB)
    rec_pair(pairsB, 'B lift_mount_plate x housing_back', layB['lift_mount_plate'], hbB,
             designed_snap=True)

    print('=== Layout B helix sockets vs posts ===', flush=True)
    hx_solid = [p for p in layB['pieces'] if p['name'] == 'HX1'][0]['solid']
    helix_seats = []
    for inst in layB['support_instances']:
        well = inst.get('well') or (inst['x'], inst['y'])
        if well in ((180.0, 140.0), (340.0, 140.0), (260.0, 100.0), (220.0, 100.0)):
            solid = inst['solid'] if inst['kind'] == 'low_mount' else inst['cap']
            v = isect_vol(solid, hx_solid)
            rec_h = dict(well=well, kind=inst['kind'], H=inst.get('H'), Hraw=inst.get('Hraw'),
                         cap_x_helix_mm3=round(v, 2),
                         class_=classify(v, designed_snap=True),
                         note='keyed ball in helix socket (56° or 298° or end)')
            helix_seats.append(rec_h)
            print('  helix seat', rec_h, flush=True)

    print('=== Layout B 35 mm sweep ===', flush=True)
    samplesB = layout_B_ball_path(C, layB)
    routeB = None
    for p in layB['pieces']:
        routeB = p['solid'] if routeB is None else (routeB + p['solid'])
    routeB = routeB + hbB + hfB
    ball_B = sweep_samples(samplesB, routeB, tag='B ')
    per_B, worst_B = _summarize_samples(ball_B)
    print('B BALL WORST', worst_B, flush=True)

    print('=== family ball paths ===', flush=True)
    families = family_sweeps(C, Cat, P)

    print('=== insertion paths ===', flush=True)
    inserts = insertion_paths(C, P)

    # helix remaining sag
    helix_note = (
        'HX360 stays at radius 90 mm and pitch 80 mm so one turn does not cross the rail. '
        'Layout B is a design study: that coil meets the lift housing on the 18×24 board. '
        'It is not a working route. Mid-span sag between the two coil sockets is untested.'
    )

    crit = [p for p in pairs + pairsB if p['class_'] == 'CRITICAL_CLASH']
    ball_crit = [r for r in ball_A + ball_B if r['class_'] == 'CRITICAL_CLASH']
    fam_crit = [f for f in families if f.get('class_') == 'CRITICAL_CLASH']

    def _mm(row):
        return row.get('isect_mm3', row.get('max_mm3', -1))

    remaining = [
        'Computational clearance only. Rolling, snap force, creep, fatigue, and printed fit were not tested. Not a certified toy.',
        'Cap×post pin bulge and cap×socket lip are designed snaps. Clip ears at the seated pose are a designed snap. Force is unknown.',
        helix_note,
        'FUNNEL centreline is a simple gravity mouth. It is not a tested catch.',
        'The v1 lift mechanism is unchanged and lives in marble-factory.',
    ]
    wa = _mm(worst_A)
    wb = _mm(worst_B)
    if wa > 5:
        remaining.append(
            f"Layout A 35 mm sweep is NOT clear: worst {wa} mm³ at {worst_A.get('piece')} s={worst_A.get('s')}."
        )
    else:
        remaining.append(
            f"Layout A 35 mm sweep worst is {wa} mm³ (full 17.5 mm radius, no shrink)."
        )
    if wb > 5:
        remaining.append(
            f"Layout B is experimental, not a complete example: 35 mm sweep worst {wb} mm³ at {worst_B.get('piece')}."
        )
    else:
        remaining.append(
            f"Layout B 35 mm sweep worst is {wb} mm³ against the placed route and lift. Mid-coil sag is still untested."
        )
    if fam_crit:
        names = ', '.join(f"{f['family']}={f.get('max_mm3')}" for f in fam_crit)
        remaining.append('Catalog families still above the critical threshold: ' + names + '.')
    else:
        remaining.append('Catalog family centreline sweeps have no sample classed CRITICAL_CLASH.')
    if crit:
        remaining.append(
            'Rest-solid pairs still classed CRITICAL_CLASH: '
            + ', '.join(f"{p['pair']}={p['isect_mm3']}" for p in crit) + '.'
        )

    report.update(dict(
        remaining_not_buildable_or_untested=remaining,
        adapter_and_route_pairs=pairs,
        layout_B_pairs=pairsB,
        ball_sweep_A=dict(n_samples=len(ball_A), shrink_mm=0.0,
                          contact_model='V+VH, tongue-hold at joints, ADAPT_IN hold then drop, no shrink',
                          worst=worst_A, per_piece=per_A,
                          clashes=[r for r in ball_A if r['isect_mm3'] > 20]),
        ball_sweep_B=dict(n_samples=len(ball_B), worst=worst_B, per_piece=per_B,
                          clashes=[r for r in ball_B if r['isect_mm3'] > 20]),
        seats_A=seats,
        helix_B_seats=helix_seats,
        helix_B_note=helix_note,
        families=families,
        insertion=inserts,
        layout_A_heights=dict(chain=zs, adapt_z=adapt_z, adapt_drop=adapt_drop,
                              adapt_slope_deg=layA['adapt_in_slope_deg']),
        critical=dict(adapter_or_route=crit, ball_samples=len(ball_crit),
                      family=fam_crit, ball_worst_A=worst_A, ball_worst_B=worst_B),
        bom48_note='ADAPT_OUT is a real thin keel collar (48th inventory part), not an omitted unusable body.',
        do_not_print=True,
    ))

    (REP / 'solids_audit.json').write_text(json.dumps(report, indent=2, default=str))
    lines = [
        '# Solids audit (geom-fix pass)',
        '',
        '**DO NOT PRINT v2 until the remaining issues below are acceptable.**',
        '35 mm ball is **not** shrunk. Designed snaps are reported separately from load geometry.',
        '',
        '## Remaining issues (not a 0-fail claim)',
        '',
    ]
    for item in remaining:
        lines.append(f'- {item}')
    lines += [
        '',
        '## Adapter and route booleans (Layout A)',
        '',
        '| pair | mm³ | class | note |',
        '|------|----:|-------|------|',
    ]
    for p in pairs:
        lines.append(f"| {p['pair']} | {p['isect_mm3']} | {p['class_']} | {p.get('note','')} |")
    lines += [
        '',
        '## Layout A ball sweep',
        '',
        f"- samples: {len(ball_A)}",
        f"- worst: {worst_A.get('isect_mm3')} mm³ at {worst_A.get('piece')} s={worst_A.get('s')} xyz={worst_A.get('xyz')} ({worst_A.get('class_')})",
        '',
        '| piece | n | max mm³ | mean | n>50 | n>200 |',
        '|-------|--:|--------:|-----:|-----:|------:|',
    ]
    for k, info in per_A.items():
        lines.append(f"| {k} | {info['n']} | {info['max']} | {info['mean']} | {info['n_over_50']} | {info['n_over_200']} |")
    lines += [
        '',
        '## Layout B ball sweep',
        '',
        f"- samples: {len(ball_B)}",
        f"- worst: {worst_B.get('isect_mm3')} mm³ at {worst_B.get('piece')} s={worst_B.get('s')} xyz={worst_B.get('xyz')} ({worst_B.get('class_')})",
        '',
        '| piece | n | max mm³ | mean | n>50 | n>200 |',
        '|-------|--:|--------:|-----:|-----:|------:|',
    ]
    for k, info in per_B.items():
        lines.append(f"| {k} | {info['n']} | {info['max']} | {info['mean']} | {info['n_over_50']} | {info['n_over_200']} |")
    lines += ['', '## Layout B helix seats', '']
    for h in helix_seats:
        lines.append(f"- well {h['well']} ({h['kind']}, Hraw={h.get('Hraw')}, H={h.get('H')}): "
                     f"{h['cap_x_helix_mm3']} mm³ ({h['class_']})")
    lines += ['', helix_note, '', '## Catalog family ball paths', '',
              '| family | max mm³ | class | note |',
              '|--------|--------:|-------|------|']
    for f in families:
        lines.append(f"| {f.get('family')} | {f.get('max_mm3', '-')} | {f.get('class_', f.get('error','-'))} | {f.get('note','')} |")
    lines += ['', '## Insertion paths (CAD)', '',
              '| pair | offset mm | mm³ | class |',
              '|------|----------:|----:|-------|']
    for r in inserts:
        lines.append(f"| {r['pair']} | {r['offset_mm']} | {r['isect_mm3']} | {r['class_']} |")
    lines += [
        '',
        '## Critical count',
        f"- adapter/route CRITICAL_CLASH rows: {len(crit)}",
        f"- ball CRITICAL_CLASH samples: {len(ball_crit)}",
        f"- family CRITICAL_CLASH: {len(fam_crit)}",
        '',
        'Not a certified play kit. Computational checks only.',
        '',
    ]
    (REP / 'SOLIDS_AUDIT.md').write_text('\n'.join(lines))
    print('WROTE reports/solids_audit.json and SOLIDS_AUDIT.md')
    print('CRITICAL adapter/route', len(crit), 'ball', len(ball_crit), 'family', len(fam_crit))
    return report

if __name__ == '__main__':
    main()
