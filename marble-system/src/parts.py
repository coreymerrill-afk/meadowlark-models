"""Generate v2 interface solids in the assembly frame (tile top z=0)."""
import math
import numpy as np
from geom import *
import constants as C

def _key():
    # 2 mm key rib so sleeve only seats one way (points +Y)
    return box(-2.0, 2.0, C.SLEEVE_OUTER/2 - 0.2, C.SLEEVE_OUTER/2 + 2.0, -C.EMBED, C.FLANGE_T)

def tile(ix=0, iy=0):
    """One quadrant of the 18x24 board. Wells are a global 40 mm lattice,
    omitting any that hit seams, outer edges, or joiner bands. Local origin
    is the tile's pitch corner (top z=0)."""
    mx, my, m = C.BODY_X, C.BODY_Y, C.MALE
    body = box(0, mx, 0, my, -C.TILE_H, 0)
    male_x = box(mx - 0.1, mx + m, 40, my - 40, -8.0, -1.0)
    male_y = box(40, mx - 40, my - 0.1, my + m, -8.0, -1.0)
    fem_x = box(-0.2, m + 0.3, 40 - 0.3, my - 40 + 0.3, -8.3, -0.7)
    fem_y = box(40 - 0.3, mx - 40 + 0.3, -0.2, m + 0.3, -8.3, -0.7)
    man = body + male_x + male_y - fem_x - fem_y
    for y in (70.0, my - 70.0):
        man = man - box(mx - 14, mx + 1, y - 7, y + 7, -7.0, -1.0)
    for x in (70.0, mx - 70.0):
        man = man - box(x - 7, x + 7, my - 14, my + 1, -7.0, -1.0)
    x0, y0 = ix * C.TILE_PX, iy * C.TILE_PY
    w = C.WELL / 2
    for gx, gy in C.wells_on_tile(ix, iy):
        x, y = gx - x0, gy - y0
        well = box(x - w, x + w, y - w, y + w, -C.WELL_DEPTH, 0.2)
        key = box(x - 2.3, x + 2.3, y + w - 0.2, y + w + 2.3, -C.WELL_DEPTH, 0.2)
        man = man - well - key
    return man

def tile_latch():
    # Sliding bar that drops into the edge slots of two neighboring tiles.
    bar = box(0, 28, -6, 6, 0, 5)
    hook = box(20, 28, -6, 6, 0, 9)
    return bar + hook

def sleeve(kind):
    spec = C.CLASSES[kind]
    Ls, out, inn = spec['Ls'], C.SLEEVE_OUTER, C.SLEEVE_INNER
    o2, i2 = out / 2, inn / 2
    outer = box(-o2, o2, -o2, o2, -C.EMBED, Ls)
    inner = box(-i2, i2, -i2, i2, -0.2, Ls + 1)
    flange = box(-C.FLANGE/2, C.FLANGE/2, -C.FLANGE/2, C.FLANGE/2, 0, C.FLANGE_T)
    man = outer + flange + _key() - inner
    # pawl window on +X near top (load-bearing hook comes through here)
    pz = Ls - 12.0
    man = man - box(i2 - 0.2, o2 + 8, -6.0, 6.0, pz - 5.0, pz + 5.0)
    # captive rails for the clip (wrap grooves on ±Y of the +X face)
    rail_z0, rail_z1 = pz - 8.0, pz + 8.0
    man = man - box(o2 - 1.2, o2 + 0.2, -o2 - 0.2, -o2 + 1.4, rail_z0, rail_z1)
    man = man - box(o2 - 1.2, o2 + 0.2, o2 - 1.4, o2 + 0.2, rail_z0, rail_z1)
    return man

def post(kind):
    spec = C.CLASSES[kind]
    Lp, Ls = spec['Lpost'], spec['Ls']
    p2 = C.POST / 2
    man = box(-p2, p2, -p2, p2, 0, Lp)
    # cap pin (round) on top — cap yaws here
    pin = cyl(4.0, 6.5, 0, 0, Lp - 0.2)
    bulge = cyl(4.45, 1.6, 0, 0, Lp + 3.2)
    man = man + pin + bulge
    # rack slots on +X face, aligned so pawl at (Ls-12) engages when z_bottom = 5*k
    # slot centre in post-local z = (Ls-12) - 5*k, k = 0 .. n
    n = int(round((spec['Hmax'] - spec['Hmin']) / C.RACK_PITCH))
    pz0 = Ls - 12.0
    for k in range(n + 1):
        zs = pz0 - k * C.RACK_PITCH
        if zs < 8 or zs > Lp - 8:
            continue
        h = C.RACK_SLOT_H / 2
        slot = box(p2 - C.RACK_DEPTH, p2 + 0.2, -5.5, 5.5, zs - h, zs + h)
        man = man - slot
    return man

def lock_clip(kind='medium'):
    """Replaceable PETG pawl. Modelled around a sleeve at the origin, +X window.
    Printed separately lying on its side. Load on the hook seats it; squeeze tab retracts it.
    Unload-to-release: hook top face is square (needs the post to be lifted ~1 mm before it withdraws)."""
    spec = C.CLASSES[kind]
    Ls = spec['Ls']
    pz = Ls - 12.0
    o2 = C.SLEEVE_OUTER / 2
    # body outside the sleeve
    body = box(o2 - 0.4, o2 + 8.0, -9.0, 9.0, pz - 9.0, pz + 9.0)
    # squeeze tab
    tab = box(o2 + 6.0, o2 + 16.0, -7.0, 7.0, pz - 5.0, pz + 5.0)
    # hook through the window — square load face (bottom of hook)
    hook = box(C.SLEEVE_INNER/2 - 3.2, o2 + 1.0, -4.5, 4.5, pz - 1.4, pz + 1.2)
    # captive ears that wrap into the sleeve rails
    ear1 = box(o2 - 1.4, o2 + 2.0, -o2 - 0.1, -6.5, pz - 7.5, pz + 7.5)
    ear2 = box(o2 - 1.4, o2 + 2.0, 6.5, o2 + 0.1, pz - 7.5, pz + 7.5)
    return body + tab + hook + ear1 + ear2

def ball_cap():
    """16 mm sphere + neck onto the post pin + meridian fin (XZ plane) to key roll.
    Cap yaws on the round pin so heading is free; fin locks roll to the track slot."""
    ball = M.sphere(C.BJ_R, 28)
    # move so ball centre is at z = CAP_TO_CENTER above a post-top at 0,
    # but we model cap with post-top at z=0, ball centre at z=10
    ball = ball.translate([0, 0, C.CAP_TO_CENTER])
    neck = cyl(3.6, C.CAP_TO_CENTER - C.BJ_R + 2.0, 0, 0, 0)
    # socket for the post pin (clearance + designed bulge snap)
    hole = cyl(4.15, 8.0, 0, 0, -0.2)
    # meridian fin in XZ (thin in Y): protrudes 2.4 mm, spans upper/mid sphere so ±15° pitch stays keyed
    fin = box(-7.2, 7.2, -0.9, 0.9, C.CAP_TO_CENTER - 3.0, C.CAP_TO_CENTER + C.BJ_R + 2.4)
    cap = ball + neck + fin - hole
    return cap

def _track_body(path):
    """Sweep a V-channel body along path of (origin, tangent_xy). origin z is V-vertex."""
    w2 = C.TW / 2
    loop_body = [(-w2, -C.BOT), (w2, -C.BOT), (w2, C.RIM), (-w2, C.RIM)]
    # V cut: open upward
    vt = C.VT
    loop_cut = [(0, -0.2), (vt, vt - 0.2), (vt, C.RIM + 8), (-vt, C.RIM + 8), (-vt, vt - 0.2)]
    samples_b = []
    samples_c = []
    for (o, t) in path:
        samples_b.append((o, t, loop_body))
        samples_c.append((o, t, loop_cut))
    body = sweep(samples_b)
    cut = sweep(samples_c)
    return body - cut

def _extend_path(path, e):
    (p0, t0) = path[0]
    (p1, t1) = path[-1]
    t0 = np.array(t0, float); t0 = t0 / np.hypot(*t0)
    t1 = np.array(t1, float); t1 = t1 / np.hypot(*t1)
    a = (tuple(np.array(p0) - np.array([t0[0], t0[1], 0]) * e), tuple(t0))
    b = (tuple(np.array(p1) + np.array([t1[0], t1[1], 0]) * e), tuple(t1))
    return [a] + list(path) + [b]

def _tongue(path_end, heading):
    """Male tongue continuing the V at the downstream end."""
    t = np.array(heading, float); t = t / np.hypot(*t)
    o = np.array(path_end, float)
    pts = []
    for s in (0.0, C.TONGUE):
        pts.append((tuple(o + np.array([t[0], t[1], 0]) * s), (t[0], t[1])))
    w2 = 18.0
    tw = 18.0 - C.TONGUE_CLR
    loop = [(-tw, -C.BOT + 0.6), (tw, -C.BOT + 0.6), (tw, 7.2), (-tw, 7.2)]
    return sweep([(p, th, loop) for p, th in pts])

def _female_cut(path_start, heading):
    """Pocket at the upstream end plus a 0.5 mm waterfall (deeper receiving floor)."""
    t = np.array(heading, float); t = t / np.hypot(*t)
    o = np.array(path_start, float)
    pts = []
    for s in (-2.0, C.TONGUE + 1.2):
        pts.append((tuple(o + np.array([t[0], t[1], 0.0]) * s), (t[0], t[1])))
    # Simple rectangular pocket that definitely removes receiving material.
    w2 = 34.0
    loop = [(-w2, -C.BOT - C.WATERFALL - 0.4), (w2, -C.BOT - C.WATERFALL - 0.4),
            (w2, C.RIM + 2.0), (-w2, C.RIM + 2.0)]
    return sweep([(p, th, loop) for p, th in pts])


def _oriented_box(origin, heading, s0, s1, u0, u1, v0, v1):
    t = np.array(heading, float); t = t / np.hypot(*t[:2])
    ang = math.degrees(math.atan2(t[1], t[0]))
    o = np.array(origin, float)
    return box(s0, s1, u0, u1, v0, v1).rotate([0, 0, ang]).translate([o[0], o[1], o[2]])

def _apply_end_features(man, start, start_h, end, end_h):
    """Male hooks at downstream end; matching recesses at upstream end.
    Rest-state: hooks are smaller than recesses (unloaded, no interpenetration).
    Lead-ins on the catch provide assembly deflection only."""
    clr = 0.45
    for side in (+1, -1):
        u0, u1 = (28.4, 39.6) if side > 0 else (-39.6, -28.4)
        hook = _oriented_box(end, end_h, -2.5, 9.4, u0, u1, -1.6, 8.6)
        catch = _oriented_box(end, end_h, 7.2, 11.4, u0, u1, -1.6, 3.6)
        man = man + hook + catch
    for side in (+1, -1):
        u0, u1 = (27.5, 40.5) if side > 0 else (-40.5, -27.5)
        rec = _oriented_box(start, start_h, -3.2, 11.6, u0, u1, -2.4, 4.4)
        man = man - rec
    return man

def _hooks_at(origin, heading, sign=+1):
    """Large dual squeeze hooks at a joint. sign=+1 on male (end), -1 unused."""
    t = np.array(heading, float); t = t / np.hypot(*t)
    u = np.array([-t[1], t[0], 0.0])
    o = np.array(origin, float)
    hooks = []
    for side in (+1, -1):
        # hook body to the side of the track
        c = o + u * side * (C.TW/2 + 4.0) + np.array([t[0], t[1], 0]) * (4.0 if sign > 0 else -4.0)
        hx, hy = c[0], c[1]
        hz = o[2] - C.BOT
        bar = box(hx - 5, hx + 5, hy - 5, hy + 5, hz, hz + 10)
        # rough hook — oriented later via a larger box along -t for catch
        hooks.append(bar)
    return union(hooks) if hooks else None

def _socket_cut(origin, tangent, slide_neg=None, slide_pos=None):
    """Elongated spherical socket + fin slot. slide_neg/slide_pos are travel along ±tangent
    so an end socket can be limited to grow inward and not invade the next piece."""
    if slide_neg is None: slide_neg = C.SLIDE
    if slide_pos is None: slide_pos = C.SLIDE
    t = np.array(tangent, float); t = t / np.hypot(*t[:2] if len(t) > 2 else t)
    if len(t) == 2:
        t = np.array([t[0], t[1], 0.0])
    o = np.array(origin, float)
    Hc = o - np.array([0, 0, C.SOCKET_TO_V])
    sph_r = C.BJ_R + 0.30
    s1 = M.sphere(sph_r, 24).translate(list(Hc - t * slide_neg))
    s2 = M.sphere(sph_r, 24).translate(list(Hc + t * slide_pos))
    ang = math.degrees(math.atan2(t[1], t[0]))
    mid = box(-slide_neg, slide_pos, -sph_r, sph_r, -sph_r, sph_r).rotate([0, 0, ang]).translate(list(Hc))
    cavity = s1 + s2 + mid
    lip_z = Hc[2] - 3.0
    above = cavity ^ box(-400, 400, -400, 400, lip_z, 400)
    throat = []
    for ds in (-slide_neg, slide_pos):
        pnt = Hc + t * ds
        throat.append(cyl(7.15, 12.0, pnt[0], pnt[1], lip_z - 12.0))
    throat.append(box(-slide_neg, slide_pos, -7.15, 7.15, -16, 0).rotate([0, 0, ang]).translate([Hc[0], Hc[1], lip_z]))
    fin = box(-slide_neg - 6, slide_pos + 6, -1.15, 1.15, -4.0, C.BJ_R + 3.5)
    fin = fin.rotate([0, 0, ang]).translate(list(Hc))
    return above + union(throat) + fin

def _socket_stations_straight(L):
    """Socket stations along a straight.
    S40: mid (slide ±20 covers both joints).
    S80: at 20 and 60 so ±20 slide reaches both joints — needed when the
    geometric mid sits on a seam with no well.
    Longer: at 40 and L-40 (160 mm span between supports is acceptable)."""
    if L <= C.P + 1:
        return [L / 2]
    if L <= C.S80 + 1:
        return [C.P / 2, L - C.P / 2]
    return [C.P, L - C.P]

def straight_track(L, drop):
    n = max(2, int(L / 20) + 1)
    path = []
    for i in range(n):
        s = L * i / (n - 1)
        path.append(((s, 0.0, -drop * s / L), (1.0, 0.0)))
    man = _track_body(_extend_path(path, 1.0))
    man = man - _female_cut(path[0][0], (1.0, 0.0))
    man = man + _tongue(path[-1][0], (1.0, 0.0))
    # hooks at male end (large side catches)
    end = np.array(path[-1][0])
    for sy in (+1, -1):
        hx, hy = end[0] + 3.0, sy * (C.TW/2 + 5.0)
        hook = box(hx - 2, hx + 8, hy - 4.5, hy + 4.5, end[2] - 2.0, end[2] + 9.0)
        catch = box(hx + 6, hx + 11, hy - 4.5, hy + 4.5, end[2] - 2.0, end[2] + 4.0)
        man = man + hook + catch
    # matching recesses at female end
    st = np.array(path[0][0])
    for sy in (+1, -1):
        hx, hy = st[0] - 1.0, sy * (C.TW/2 + 5.0)
        rec = box(hx - 1, hx + 10, hy - 5.0, hy + 5.0, st[2] - 2.4, st[2] + 4.4)
        man = man - rec
    for s in _socket_stations_straight(L):
        o = (s, 0.0, -drop * s / L)
        man = man - _socket_cut(o, (1.0, 0.0))
        # local boss around socket so the lip has material (union a block, then recut)
    return man

def _reinforce_sockets(man, stations, tangents, slides=None):
    for i, (o, t) in enumerate(zip(stations, tangents)):
        sn, sp = (C.SLIDE, C.SLIDE) if not slides else slides[i]
        t = np.array(t, float); t = t / np.hypot(*t[:2])
        ang = math.degrees(math.atan2(t[1], t[0]))
        # Extra pad only on end-limited sockets (one side zero) and only inward.
        # Mid-span sockets (both sides open) must not grow past the slide, or an
        # S80 station at s=20 would invade the previous piece by ~8 mm.
        if sn > 0 and sp > 0:
            pad_n = pad_p = 0.0
        else:
            pad_n = 8.0 if sn else 0.0
            pad_p = 8.0 if sp else 0.0
        boss = box(-sn - pad_n, sp + pad_p, -14.0, 14.0, -C.SOCKET_TO_V - 8, -0.2)
        boss = boss.rotate([0, 0, ang]).translate([o[0], o[1], o[2]])
        man = man + boss
        man = man - _socket_cut(o, (t[0], t[1]), sn, sp)
    return man

def straight_track_r(L, drop):
    n = max(2, int(L / 20) + 1)
    path = [((L * i / (n - 1), 0.0, -drop * i / (n - 1)), (1.0, 0.0)) for i in range(n)]
    man = _track_body(path)
    man = man - _female_cut(path[0][0], (1.0, 0.0))
    man = man + _tongue(path[-1][0], (1.0, 0.0))
    man = _apply_end_features(man, path[0][0], (1.0, 0.0), path[-1][0], (1.0, 0.0))
    stations = [(s, 0.0, -drop * s / L) for s in _socket_stations_straight(L)]
    man = _reinforce_sockets(man, stations, [(1.0, 0.0)] * len(stations))
    man = man - _female_cut(path[0][0], (1.0, 0.0))
    return man

def corner_track(turn='L', R=None, drop=None, ang=90.0):
    R = C.RC90 if R is None else R
    drop = C.DROP90 if drop is None else drop
    s = 1 if turn == 'L' else -1
    n = 25
    path = []
    for i in range(n):
        a = math.radians(ang * i / (n - 1))
        x = R * math.sin(a)
        y = s * R * (1 - math.cos(a))
        t = (math.cos(a), s * math.sin(a))
        path.append(((x, y, -drop * i / (n - 1)), t))
    man = _track_body(path)
    man = man - _female_cut(path[0][0], path[0][1])
    man = man + _tongue(path[-1][0], path[-1][1])
    man = _apply_end_features(man, path[0][0], path[0][1], path[-1][0], path[-1][1])
    stations = [path[0][0], path[-1][0]]
    tangents = [path[0][1], path[-1][1]]
    sl = C.SLIDE_45 if ang < 89.0 else C.SLIDE
    # grow sliding sockets only inward so bosses do not invade the next piece
    man = _reinforce_sockets(man, stations, tangents, slides=[(0.0, sl), (sl, 0.0)])
    man = man - _female_cut(path[0][0], path[0][1])
    return man

def fit_coupon():
    """One-piece coupon of every repeating interface."""
    plate = box(0, 120, 0, 80, 0, 4)
    # well sample
    w = C.WELL / 2
    plate = plate - box(20 - w, 20 + w, 20 - w, 20 + w, 4 - C.WELL_DEPTH, 4.2)
    plate = plate - box(20 - 2.3, 20 + 2.3, 20 + w - 0.2, 20 + w + 2.3, 4 - C.WELL_DEPTH, 4.2)
    # rack sample (3 slots)
    rack = box(50, 66, 10, 26, 4, 30)
    for k in range(3):
        zs = 10 + k * 5
        rack = rack - box(66 - 3.0, 66.2, 12, 24, 4 + zs - 1.4, 4 + zs + 1.4)
    # tongue / female witness blocks
    male = box(80, 80 + C.TONGUE, 15, 45, 4, 12)
    fem = box(96, 116, 14.6, 45.4, 3.5, 12.2)
    fem = fem - box(96, 96 + C.TONGUE + 0.8, 15.2, 44.8, 3.7, 11.5)
    # ball seat cup
    cup = cyl(14, 10, 30, 55, 4) - M.sphere(C.BJ_R + 0.3, 20).translate([30, 55, 4 + 8])
    return plate + rack + male + fem + cup

def part_catalog():
    """Build every unique interface solid (design frame)."""
    return {
        'base_tile': tile,
        'tile_latch': tile_latch,
        'sleeve_short': lambda: sleeve('short'),
        'sleeve_medium': lambda: sleeve('medium'),
        'sleeve_tall': lambda: sleeve('tall'),
        'post_short': lambda: post('short'),
        'post_medium': lambda: post('medium'),
        'post_tall': lambda: post('tall'),
        'lock_clip_short': lambda: lock_clip('short'),
        'lock_clip_medium': lambda: lock_clip('medium'),
        'lock_clip_tall': lambda: lock_clip('tall'),
        'ball_cap': ball_cap,
        'track_S160': lambda: straight_track_r(C.S160, C.DROP160),
        'track_S80': lambda: straight_track_r(C.S80, C.DROP80),
        'track_CR90': lambda: corner_track('R'),
        'track_CL90': lambda: corner_track('L'),
        'fit_coupon': fit_coupon,
    }
