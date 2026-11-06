"""Mesh quality, static/motion interference, ball-path slope and clearance, shaft seating."""
import json, math, sys
from pathlib import Path
import numpy as np
import manifold3d as m3
from geom import to_trimesh
import assembly as A
from assembly import apply
import lift as L
import tracks as T
import lift2d

ROOT = Path('/workspace/marble-factory')
REP = ROOT / 'reports'
REP.mkdir(exist_ok=True)
M = m3.Manifold


def vol_isect(a, b):
    if a.is_empty() or b.is_empty():
        return 0.0
    i = a ^ b
    return 0.0 if i.is_empty() else float(i.volume())


def world_part(name, k=0):
    meta = A.CAT[name]
    man = meta['builder']()
    M4 = meta['inst'][k]['M']
    return apply(man, M4)


def report_mesh_quality():
    rows = []
    fails = []
    for name, meta in A.CAT.items():
        man = A.print_mesh(name)
        tm = to_trimesh(man)
        bb = tm.bounds
        ext = bb[1] - bb[0]
        comps = len(man.decompose())
        row = dict(name=name, verts=len(tm.vertices), faces=len(tm.faces),
                   volume=float(tm.volume), watertight=bool(tm.is_watertight),
                   components=comps, extents=ext.tolist(),
                   too_big=bool(ext[0] > 330 or ext[1] > 320 or ext[2] > 325),
                   genus=int(man.genus()) if hasattr(man, 'genus') else None)
        if not row['watertight']:
            fails.append(f'{name} not watertight')
        if comps != 1:
            fails.append(f'{name} has {comps} components')
        if row['too_big']:
            fails.append(f'{name} exceeds bed ({ext})')
        if tm.volume <= 0:
            fails.append(f'{name} non-positive volume')
        rows.append(row)
    return rows, fails


def shaft_seating():
    """Journals should sit inside holes with clearance (intersection volume ~ 0).
    Hex drives should also not interpenetrate."""
    notes = []
    fails = []
    hb = world_part('lift_housing_back')
    hf = world_part('lift_housing_front')
    ax = world_part('lift_axle')
    v_back = vol_isect(ax, hb)
    v_front = vol_isect(ax, hf)
    notes.append(dict(pair='axle×housing_back', isect_mm3=v_back,
                      expect='~0 (0.4 mm radial clearance on jBack)'))
    notes.append(dict(pair='axle×housing_front', isect_mm3=v_front,
                      expect='~0 (0.4 mm radial clearance on jFront)'))
    if v_back > 50:
        fails.append(f'axle intersects housing back by {v_back:.1f} mm³')
    if v_front > 50:
        fails.append(f'axle intersects housing front by {v_front:.1f} mm³')
    # wheel hex vs axle
    for k in range(2):
        w = world_part('lift_wheel_half', k)
        vi = vol_isect(ax, w)
        notes.append(dict(pair=f'axle×wheel_half[{k}]', isect_mm3=vi, expect='~0 (0.2 mm/flat hex clearance)'))
        if vi > 50:
            fails.append(f'axle intersects wheel half {k} by {vi:.1f} mm³')
    # crank vs axle — hex should clear; crank body should not hit housing
    cr = world_part('lift_crank')
    vi = vol_isect(ax, cr)
    notes.append(dict(pair='axle×crank', isect_mm3=vi, expect='~0 (0.2 mm/flat)'))
    if vi > 50:
        fails.append(f'axle intersects crank by {vi:.1f} mm³')
    vf = vol_isect(cr, hf)
    notes.append(dict(pair='crank×housing_front', isect_mm3=vf, expect='0 (3.5 mm axial gap)'))
    if vf > 1:
        fails.append(f'crank intersects front plate by {vf:.1f} mm³')
    # pawl vs pin: pawl hole r=5.4, pin r=5.0
    pw = world_part('lift_pawl')
    vi = vol_isect(pw, hb)
    notes.append(dict(pair='pawl×housing_back (includes pin)', isect_mm3=vi,
                      expect='small or 0; pin clearance 0.4 mm radial'))
    if vi > 200:
        fails.append(f'pawl intersects housing/pin by {vi:.1f} mm³')
    return notes, fails


def wheel_motion(step=15):
    """Boolean wheel (both halves) against housing, pawl, chute through one revolution."""
    notes = []
    fails = []
    hb = world_part('lift_housing_back')
    hf = world_part('lift_housing_front')
    pw = world_part('lift_pawl')
    wh = A.CAT['lift_wheel_half']['builder']()
    LP = A.Tm(None, A.LIFT_POS)
    for om in range(0, 360, step):
        acc = None
        for Mx in L.wheel_assembly_transforms(om):
            m4 = np.eye(4)
            m4[:3] = Mx
            w = apply(wh, LP @ m4)
            acc = w if acc is None else acc + w
        hits = {
            'back': vol_isect(acc, hb),
            'front': vol_isect(acc, hf),
            'pawl': vol_isect(acc, pw),
        }
        notes.append(dict(omega=om, **hits))
        for k, v in hits.items():
            if v > 80:
                fails.append(f'wheel@{om}° intersects {k} by {v:.1f} mm³')
    return notes, fails


def static_neighbors():
    """Selected assembly pairs that must not collide (beyond advertised clearances)."""
    pairs = [
        ('lift_inlet_chute', 0, 'lift_housing_front', 0, 25, 'inlet vs front plate / baffle'),
        ('lift_inlet_chute', 0, 'lift_crank', 0, 1, 'inlet vs crank at catalogued angle'),
        ('track_straight_160', 0, 'lift_housing_back', 0, 2, 'chute tongue must sit in the first-track V, not the walls'),
        ('lift_inlet_chute', 0, 'track_straight_160', 3, 25, 'inlet vs last return straight at J11'),
    ]
    notes, fails = [], []
    cache = {}

    def get(n, k):
        key = (n, k)
        if key not in cache:
            cache[key] = world_part(n, k)
        return cache[key]

    for a, ia, b, ib, lim, why in pairs:
        try:
            va = vol_isect(get(a, ia), get(b, ib))
        except Exception as e:
            notes.append(dict(pair=f'{a}[{ia}]×{b}[{ib}]', error=str(e), why=why))
            fails.append(f'{a}×{b} boolean failed: {e}')
            continue
        notes.append(dict(pair=f'{a}[{ia}]×{b}[{ib}]', isect_mm3=va, limit=lim, why=why))
        if va > lim:
            fails.append(f'{a}[{ia}]×{b}[{ib}] intersects by {va:.1f} mm³ (limit {lim}); {why}')
    return notes, fails


def heading_continuity():
    notes, fails = [], []
    for i, (mod, a, b, h) in enumerate(A.ROUTE):
        if i == 0:
            continue
        prev = A.ROUTE[i - 1]
        prev_out = A.END_HEADING[prev[0]](prev[3])
        ok = abs((prev_out - h + 180) % 360 - 180) < 0.5
        notes.append(dict(from_mod=prev[0], to_mod=mod, prev_out=prev_out, this_in=h, ok=ok))
        if not ok:
            fails.append(f'heading break {prev[0]} out {prev_out} -> {mod} in {h}')
    return notes, fails


def track_slopes():
    notes, fails = [], []
    pts, segs = A.default_ball_path()
    dumped = dict(default_loop=pts, segments=[{k: (v if k != 'pts' else v) for k, v in seg.items()} for seg in segs])
    zs = [p[2] for p in pts]
    uphill = []
    for i in range(1, len(zs)):
        dz = zs[i] - zs[i - 1]
        if dz > 0.15:
            uphill.append(dict(i=i, dz=dz, a=pts[i - 1], b=pts[i]))
    notes.append(dict(path='default_loop', n=len(pts), z0=zs[0], z1=zs[-1],
                      drop=zs[0] - zs[-1], uphill_samples=len(uphill)))
    if uphill:
        fails.append(f'default_loop has {len(uphill)} uphill samples, first dz={uphill[0]["dz"]:.3f}')
        notes[-1]['first_uphill'] = uphill[0]
    p, log, rel = lift2d.full_eval(lift2d.P)
    lift_pts = [[A.LIFT_POS[0] + s['x'], A.LIFT_POS[1], A.LIFT_POS[2] + s['z']] for s in log]
    dumped['lift'] = lift_pts
    dumped['lift_log'] = log
    notes.append(dict(path='lift', n=len(lift_pts), cleared_paddles_at_w=rel,
                      zmin=min(s['z'] for s in log), zmax=max(s['z'] for s in log),
                      min_second_paddle_gap=min(s['g2'] for s in log)))
    (REP / 'ball_paths.json').write_text(json.dumps(dumped, default=float))
    return notes, fails, dumped


def _wheel_at(wh, LP, om):
    acc = None
    for Mx in L.wheel_assembly_transforms(om):
        m4 = np.eye(4)
        m4[:3] = Mx
        w = apply(wh, LP @ m4)
        acc = w if acc is None else acc + w
    return acc


def sync_carry(log):
    """Ball at the 2D-sim centre vs housing + wheel at the SAME wheel angle."""
    notes, fails = [], []
    hb = world_part('lift_housing_back')
    hf = world_part('lift_housing_front')
    housing = hb + hf
    wh = A.CAT['lift_wheel_half']['builder']()
    LP = A.Tm(None, A.LIFT_POS)
    # Fine near pickup (w -115..-75) and release (70..100); every ~3° elsewhere.
    picks = []
    for i, s in enumerate(log):
        w = s['w']
        if w <= -75 or w >= 70 or (i % 6 == 0):
            picks.append(s)
    house_hits, deep_wheel = [], []
    max_h = 0.0
    max_w = 0.0
    for s in picks:
        c = [A.LIFT_POS[0] + s['x'], A.LIFT_POS[1], A.LIFT_POS[2] + s['z']]
        ball = M.sphere(L.RB - 0.35, 36).translate(c)
        vh = vol_isect(ball, housing)
        vw = vol_isect(ball, _wheel_at(wh, LP, s['w']))
        max_h = max(max_h, vh)
        max_w = max(max_w, vw)
        rec = dict(w=s['w'], center=c, vs_housing=vh, vs_wheel=vw)
        if vh > 25:
            house_hits.append(rec)
        if vw > 450:
            deep_wheel.append(rec)
    notes.append(dict(samples=len(picks), max_vs_housing=max_h, max_vs_wheel=max_w,
                      housing_hits=len(house_hits), deep_wheel_hits=len(deep_wheel),
                      note='vs_wheel includes intended driving-paddle contact; >450 mm3 is treated as burial'))
    if house_hits:
        fails.append(f'sync carry: ball vs housing at {len(house_hits)} samples, e.g. {house_hits[0]}')
        notes[-1]['house_examples'] = house_hits[:6]
    if deep_wheel:
        fails.append(f'sync carry: ball buried in wheel (>450 mm3) at {len(deep_wheel)} samples, e.g. {deep_wheel[0]}')
        notes[-1]['wheel_examples'] = deep_wheel[:6]
    return notes, fails


def ball_clearance(dumped):
    """Ball along the default loop vs every placed track/inlet/housing (not a parked wheel)."""
    notes, fails = [], []
    solids = []
    for name, meta in A.CAT.items():
        if name.startswith('stand_') or name in ('base_tile', 'ball_35', 'lift_axle', 'lift_crank',
                                                 'lift_clip', 'lift_pawl', 'lift_wheel_half'):
            continue
        for k, inst in enumerate(meta['inst']):
            if inst.get('M') is None:
                continue
            if name.startswith('track_') or name in ('lift_inlet_chute', 'lift_housing_back', 'lift_housing_front'):
                solids.append((name, k, world_part(name, k)))
    pts = dumped['default_loop']
    # denser at segment starts (junctions): take every 3rd plus first/last of each segment
    idxs = set(range(0, len(pts), 3))
    off = 0
    for seg in dumped['segments']:
        n = len(seg['pts'])
        idxs.add(off)
        idxs.add(off + n - 1)
        if n > 2:
            idxs.add(off + 1)
            idxs.add(off + n - 2)
        off += n - (1 if off else 0)
    # fix index mapping: default_ball_path drops duplicate joints so segment lengths overlap
    idxs = sorted(i for i in range(len(pts)) if i % 3 == 0 or i < 4 or i > len(pts) - 5)
    # also explicitly test joint XY locations
    hits = []
    for i in idxs:
        c = pts[i]
        ball = M.sphere(L.RB - 0.35, 36).translate(list(c))
        for name, k, sol in solids:
            v = vol_isect(ball, sol)
            if v > 20:
                hits.append(dict(i=i, center=c, solid=f'{name}[{k}]', mm3=v))
    notes.append(dict(path='default_loop', samples=len(idxs), hits=len(hits),
                      worst=max((h['mm3'] for h in hits), default=0)))
    if hits:
        fails.append(f'default_loop: ball intersects solids at {len(hits)} samples, worst {hits[0]}')
        notes[-1]['examples'] = hits[:10]
    return notes, fails


def crank_sweep():
    """Crank body vs inlet over 360°."""
    inlet = world_part('lift_inlet_chute')
    cr0 = A.CAT['lift_crank']['builder']()  # angle 0
    LP = A.Tm(None, A.LIFT_POS)
    notes, fails = [], []
    for om in range(0, 360, 15):
        cr = apply(cr0, LP @ A.Tm(A.roty_xz(om)))
        v = vol_isect(cr, inlet)
        notes.append(dict(angle=om, isect=v))
        if v > 1:
            fails.append(f'crank@{om}° hits inlet by {v:.1f} mm³')
    return notes, fails


def main():
    A.build_catalogue()
    out = dict(fails=[], sections={})
    print('mesh quality...')
    rows, f = report_mesh_quality()
    out['sections']['meshes'] = rows
    out['fails'] += f
    print('  fails', f)

    print('shaft seating...')
    n, f = shaft_seating()
    out['sections']['shafts'] = n
    out['fails'] += f
    print('  fails', f)

    print('static neighbors...')
    n, f = static_neighbors()
    out['sections']['neighbors'] = n
    out['fails'] += f
    print('  fails', f)

    print('wheel motion...')
    n, f = wheel_motion(20)
    out['sections']['wheel_motion'] = n
    out['fails'] += f
    print('  fails', f)

    print('crank sweep...')
    n, f = crank_sweep()
    out['sections']['crank_sweep'] = n
    out['fails'] += f
    print('  fails', f)

    print('heading continuity...')
    n, f = heading_continuity()
    out['sections']['headings'] = n
    out['fails'] += f
    print('  fails', f)

    print('slopes...')
    n, f, dumped = track_slopes()
    out['sections']['slopes'] = n
    out['fails'] += f
    print('  fails', f)

    print('sync 3D carry...')
    n, f = sync_carry(dumped['lift_log'])
    out['sections']['sync_carry'] = n
    out['fails'] += f
    print('  fails', f)

    print('ball clearance on default loop...')
    n, f = ball_clearance(dumped)
    out['sections']['ball_clearance'] = n
    out['fails'] += f
    print('  fails', f)

    (REP / 'validation.json').write_text(json.dumps(out, indent=2, default=float))
    print('TOTAL FAILS', len(out['fails']))
    for x in out['fails']:
        print(' -', x)
    return out


if __name__ == '__main__':
    main()
