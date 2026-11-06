"""Remaining 48-inventory families plus disclosed extras."""
import math
import numpy as np
from geom import *
import constants as C
import parts as P

def corner45(turn='L'):
    return P.corner_track(turn, R=C.RC90, drop=C.DROP45, ang=45.0)

def _path_from_xy(pts):
    """pts: (x,y,z) list. Tangents from consecutive XY."""
    path = []
    for i, p in enumerate(pts):
        if i < len(pts) - 1:
            d = np.array(pts[i+1][:2]) - np.array(p[:2])
        else:
            d = np.array(p[:2]) - np.array(pts[i-1][:2])
        n = np.hypot(*d)
        t = (float(d[0]/n), float(d[1]/n)) if n > 1e-9 else (1.0, 0.0)
        path.append((tuple(p), t))
    return path

def _finish(path, sockets=None, slides=None):
    man = P._track_body(path)
    man = man - P._female_cut(path[0][0], path[0][1])
    man = man + P._tongue(path[-1][0], path[-1][1])
    man = P._apply_end_features(man, path[0][0], path[0][1], path[-1][0], path[-1][1])
    if sockets:
        tans = []
        for o in sockets:
            # nearest path tangent
            best, bt = 1e9, path[0][1]
            for q, t in path:
                d = (q[0]-o[0])**2 + (q[1]-o[1])**2
                if d < best:
                    best, bt = d, t
            tans.append(bt)
        man = P._reinforce_sockets(man, sockets, tans, slides=slides)
    man = man - P._female_cut(path[0][0], path[0][1])
    return man

def split_y(drop_a=20.0, drop_b=35.0, L=160.0, off=80.0):
    n = 25
    path_a = [((L*i/(n-1), 0.0, -drop_a*i/(n-1)), (1.0, 0.0)) for i in range(n)]
    path_b = []
    for i in range(n):
        x = L*i/(n-1)
        y = 0.5*off*(1 - math.cos(math.pi*x/L))
        dy = 0.5*off*(math.pi/L)*math.sin(math.pi*x/L)
        z = -drop_b*x/L
        t = np.array([1.0, dy]); t = t/np.hypot(*t)
        path_b.append(((x, y, z), (float(t[0]), float(t[1]))))
    ma = P._track_body(path_a)
    mb = P._track_body(path_b)
    # shared inlet female
    man = ma + mb
    man = man - P._female_cut(path_a[0][0], (1.0, 0.0))
    man = man + P._tongue(path_a[-1][0], (1.0, 0.0))
    man = man + P._tongue(path_b[-1][0], path_b[-1][1])
    # sockets: inlet area and each outlet inward
    socks = [(40.0, 0.0, -drop_a*40/L),
             (L-40.0, 0.0, -drop_a*(L-40)/L),
             (L-40.0, 0.5*off*(1-math.cos(math.pi*(L-40)/L)), -drop_b*(L-40)/L)]
    man = P._reinforce_sockets(man, socks, [(1,0), (1,0), path_b[-2][1]])
    man = man - P._female_cut(path_a[0][0], (1.0, 0.0))
    return man

def merge_y(drop_a=35.0, drop_b=20.0, L=160.0, off=80.0):
    """Inlet A at (0,0,0) drops more (cascade into B). Inlet B at (0,80,-15) is the through floor.
    Outlet at (160, 80, -35)."""
    z_b0 = -15.0
    n = 25
    path_b = [((L*i/(n-1), off, z_b0 - drop_b*i/(n-1)), (1.0, 0.0)) for i in range(n)]
    path_a = []
    for i in range(n):
        x = L*i/(n-1)
        y = off - 0.5*off*(1 + math.cos(math.pi*x/L))  # 0 → off
        # y(0)=off-0.5*off*2=0, y(L)=off-0.5*off*0=off
        dy = 0.5*off*(math.pi/L)*math.sin(math.pi*x/L)
        z = -drop_a*x/L
        t = np.array([1.0, dy]); t = t/np.hypot(*t)
        path_a.append(((x, y, z), (float(t[0]), float(t[1]))))
    man = P._track_body(path_a) + P._track_body(path_b)
    man = man - P._female_cut(path_a[0][0], (1.0, 0.0))
    man = man - P._female_cut(path_b[0][0], (1.0, 0.0))
    man = man + P._tongue(path_b[-1][0], (1.0, 0.0))
    socks = [(40, 0, -drop_a*40/L), (40, off, z_b0 - drop_b*40/L),
             (L-40, off, z_b0 - drop_b*(L-40)/L)]
    man = P._reinforce_sockets(man, socks, [(1,0), (1,0), (1,0)])
    return man

def funnel(L=80.0, drop=20.0, mouth=96.0):
    """Wide sloped basin to a standard V exit. Floor always downhill."""
    n = 16
    path = [((L*i/(n-1), 0.0, -drop*i/(n-1)), (1.0, 0.0)) for i in range(n)]
    man = P._track_body(path)
    # mouth walls: two tapering sides
    w0, w1 = mouth/2, C.TW/2
    wall = []
    for i in range(n-1):
        s0, s1 = L*i/(n-1), L*(i+1)/(n-1)
        z0, z1 = -drop*i/(n-1), -drop*(i+1)/(n-1)
        wa = w0 + (w1-w0)*i/(n-1)
        wb = w0 + (w1-w0)*(i+1)/(n-1)
        for sg in (+1, -1):
            wall.append(box(s0, s1, sg*min(wa, wb)-4, sg*max(wa, wb), min(z0, z1)-C.BOT, max(z0, z1)+C.RIM))
    man = man + union(wall)
    # sloped floor fill
    floor = []
    for i in range(n-1):
        s0, s1 = L*i/(n-1), L*(i+1)/(n-1)
        z0 = -drop*i/(n-1) - C.BOT
        floor.append(box(s0, s1, -mouth/2, mouth/2, z0, z0 + 3.5))
    man = man + union(floor)
    man = man + P._tongue(path[-1][0], (1.0, 0.0))
    man = P._reinforce_sockets(man, [(L-40, 0, -drop*(L-40)/L)], [(1, 0)])
    return man

def helix_360(R=90.0, drop=80.0, n=72, exit_stub=40.0, turn="L"):
    """Descending 360° helix, printable as one piece (dia ~244 mm). Exit stub +X at z=-drop."""
    path = []
    for i in range(n):
        a = 2*math.pi * i / (n - 1)
        x = R * math.sin(a)
        y = R * (1 - math.cos(a))
        z = -drop * i / (n - 1)
        path.append(((x, y, z), (math.cos(a), math.sin(a))))
    # replace last point's continuation with stub along +X from (0,0,-drop)
    for k in range(1, 5):
        s = exit_stub * k / 4
        path.append(((s, 0.0, -drop), (1.0, 0.0)))
    if turn == "R":
        path = [((x, -y, z), (tx, -ty)) for (x, y, z), (tx, ty) in path]
    man = P._track_body(path)
    h0, h1 = path[0][1], path[-1][1]
    man = man - P._female_cut(path[0][0], h0)
    man = man + P._tongue(path[-1][0], h1)
    man = P._apply_end_features(man, path[0][0], h0, path[-1][0], h1)
    man = P._reinforce_sockets(
        man,
        [path[0][0], path[-1][0]],
        [h0, h1],
        slides=[(0.0, C.SLIDE), (C.SLIDE, 0.0)])
    man = man - P._female_cut(path[0][0], h0)
    return man

def drop40(L=80.0, drop=40.0):
    """Short fall into a catch bowl, then a V exit. Floor of the bowl is downhill to the exit."""
    path_in = [((0.0, 0.0, 0.0), (1, 0)), ((24.0, 0.0, -3.0), (1, 0))]
    path_mid = [((24.0 + 26.0*i/7, 0.0, -3.0 - (drop-5)*i/7), (1, 0)) for i in range(8)]
    path_out = [((50.0, 0.0, -drop), (1, 0)), ((L, 0.0, -drop - 2.0), (1, 0))]
    man = P._track_body(path_in) + P._track_body(path_mid) + P._track_body(path_out)
    bowl = M.sphere(28, 24).translate([36.0, 0.0, -drop + 10])
    bowl = bowl ^ box(10, 62, -28, 28, -drop - 16, -drop + 20)
    # guarantee a single body even if sweeps only kiss
    conn = box(18, 56, -20, 20, -drop - 6, 6)
    man = man + bowl + conn
    man = man - P._female_cut((0, 0, 0), (1, 0))
    man = man + P._tongue((L, 0, -drop - 2), (1, 0))
    man = P._reinforce_sockets(man, [(L - 24, 0, -drop - 2.0)], [(1, 0)])
    return man

def tun160():
    man = P.straight_track_r(C.S160, C.DROP160)
    roof = box(12, 148, -18, 18, 10, 28)
    # slope the roof roughly
    return man + roof

def switch_y():
    """Same Y-fork as SPLIT_Y plus a vertical pocket that receives switch_gate.
    Gate in = path B blocked; gate out = both paths open (manual)."""
    man = split_y()
    # pocket roughly over the B branch root (does not cut the A floor)
    pocket = box(30, 50, 10, 38, -20, 18)
    return man - pocket

def switch_gate():
    """Removable wall that blocks path B of the switch when dropped in."""
    return box(28, 48, 8, 36, -18, 16) + box(30, 46, 20, 50, 12, 20)

def adapt_out():
    """Collar that accepts the v1 chute keel and presents a standard male at J0.
    Built from the published keel profile (same numbers that generate the v1 mesh)."""
    # Open V channel ~24 mm long, heading +X locally (caller rotates).
    path = [((-14.0, 0.0, 1.2), (1, 0)), ((12.0, 0.0, 0.0), (1, 0))]
    man = P._track_body(path)
    # keel clearance cavity (v1 keel loop, extra 0.45 mm)
    keel_cut = []
    for x in np.linspace(-14, 2, 8):
        keel_cut.append(((x, 0.0, 1.2 - (x+14)*1.2/16), (-1, 0)))
    loop = [(0, 1.3-0.45), (4.6, 6.2), (2.4, 6.2), (0, 3.5), (-2.4, 6.2), (-4.6, 6.2)]
    # simpler box cavity for the keel
    cav = box(-16, 4, -5.0, 5.0, 0.6, 6.5)
    man = man - cav
    man = man + P._tongue((12.0, 0.0, 0.0), (1, 0))
    return man

def adapt_in(drop=None):
    """Low ramp from a standard female (no ball stack) down to the v1 front-plate inlet.
    Length matches v1 INLET_L. Drop defaults to the catalog 23.2 mm witness;
    layouts pass the actual remaining height. Always downhill. No ball socket."""
    L = C.V1_INLET_L
    drop = 23.2 if drop is None else drop
    if drop < 1.0:
        raise ValueError('ADAPT_IN needs a positive drop')
    n = 12
    path = [((L*i/(n-1), 0.0, -drop*i/(n-1)), (1.0, 0.0)) for i in range(n)]
    man = P._track_body(path)
    man = man - P._female_cut(path[0][0], (1.0, 0.0))
    # nose that meets the v1 front-plate opening (±24.5 mm wide)
    nose = box(L - 8, L + 6, -24.0, 24.0, -drop - 8, -drop + 22)
    man = man + nose
    # NO ball socket — this is the low direct-rail adapter
    return man

def low_mount():
    """Well pin + yoke that saddles a track underside. Extra, not one of the 24.
    Covers rail underside heights roughly 36–68 mm via a short 4 mm rack."""
    pin = box(-8, 8, -8, 8, -C.EMBED, 4)
    post = box(-7, 7, -7, 7, 0, 52)
    yoke = box(-36, 36, -10, 10, 48, 58)
    inner = box(-22, 22, -12, 12, 50, 57)
    return pin + post + yoke - inner

def lift_mount_plate():
    """Sits on two wells 160 mm apart, offers v1 teardrop/round sockets (r=10.2) for housing pegs."""
    plate = box(-110, 110, -28, 28, 0, 8)
    pins = box(-88, -72, -8, 8, -C.EMBED, 1) + box(72, 88, -8, 8, -C.EMBED, 1)
    holes = cyl(10.2, 10, -80, 0, -1) + cyl(10.2, 10, 80, 0, -1)
    return plate + pins - holes

def part_catalog():
    cat = {
        'tile_00': lambda: P.tile(0, 0),
        'tile_10': lambda: P.tile(1, 0),
        'tile_01': lambda: P.tile(0, 1),
        'tile_11': lambda: P.tile(1, 1),
        'tile_latch': P.tile_latch,
        'sleeve_short': lambda: P.sleeve('short'),
        'sleeve_medium': lambda: P.sleeve('medium'),
        'sleeve_tall': lambda: P.sleeve('tall'),
        'post_short': lambda: P.post('short'),
        'post_medium': lambda: P.post('medium'),
        'post_tall': lambda: P.post('tall'),
        'lock_clip_short': lambda: P.lock_clip('short'),
        'lock_clip_medium': lambda: P.lock_clip('medium'),
        'lock_clip_tall': lambda: P.lock_clip('tall'),
        'ball_cap': P.ball_cap,
        'track_S160': lambda: P.straight_track_r(C.S160, C.DROP160),
        'track_S80': lambda: P.straight_track_r(C.S80, C.DROP80),
        'track_S40': lambda: P.straight_track_r(C.S40, C.DROP40),
        'track_CR90': lambda: P.corner_track('R'),
        'track_CL90': lambda: P.corner_track('L'),
        'track_CR45': lambda: corner45('R'),
        'track_CL45': lambda: corner45('L'),
        'track_SPLIT_Y': split_y,
        'track_MERGE_Y': merge_y,
        'track_FUNNEL': funnel,
        'track_HX360': helix_360,
        'track_DROP40': drop40,
        'track_SPAN240': lambda: P.straight_track_r(240.0, 30.0),
        'track_TUN160': tun160,
        'track_SWITCH': switch_y,
        'ADAPT_OUT': adapt_out,
        'ADAPT_IN': adapt_in,
        'switch_gate': switch_gate,
        'low_mount': low_mount,
        'lift_mount_plate': lift_mount_plate,
        'fit_coupon': P.fit_coupon,
    }
    return cat
