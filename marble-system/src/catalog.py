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
    centers = [(p[0], p[1], p[2] + C.VH) for p, _t in path_a + path_b]
    return P.carve_balls(man, centers)

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
    # Both inlets fall toward the shared exit. Path A starts higher and path B
    # starts already lower; neither rises.
    centers = [(p[0], p[1], p[2] + C.VH) for p, _t in path_a + path_b]
    return P.carve_balls(man, centers)

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
    """One-turn helix. Pitch is 80 mm so the ~40 mm section does not meet the
    next pass. A shorter pitch self-crosses the rail. Coil radius 90 mm."""
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
    socks = [path[0][0], path[-1][0]]
    tans = [h0, h1]
    sls = [(0.0, C.SLIDE), (C.SLIDE, 0.0)]
    # Mid-coil sockets beside the R=90 coil. Layout B's study places
    # local (80, -40) on well (180, 140) and (-80, -40) on (340, 140).
    if turn == "R":
        targets = [(80.0, -40.0), (-80.0, -40.0)]
    else:
        targets = [(80.0, 40.0), (-80.0, 40.0)]
    for tx, ty in targets:
        best_i = min(range(n), key=lambda i: (path[i][0][0] - tx) ** 2 + (path[i][0][1] - ty) ** 2)
        (_px, _py, pz), t = path[best_i]
        socks.append((tx, ty, pz))
        tans.append(t)
        sls.append((C.SLIDE, C.SLIDE))
    man = P._reinforce_sockets(man, socks, tans, slides=sls)
    man = man - P._female_cut(path[0][0], h0)
    return man

def drop40(L=80.0, drop=40.0):
    """Guided 40 mm descent. One continuous V, steeper through the middle,
    with side walls. The ball path is the centreline — there is no unguided
    bowl and no connector block in that path."""
    n = 24
    def z_at(s):
        # Ease in, steep middle, ease out. Monotone down.
        u = s / L
        return -drop * (u * u * (3 - 2 * u)) - 2.0 * u
    pts = []
    for i in range(n):
        s = L * i / (n - 1)
        pts.append(((s, 0.0, z_at(s)), (1.0, 0.0)))
    man = P._track_body(pts)
    man = man - P._female_cut(pts[0][0], (1.0, 0.0))
    man = man + P._tongue(pts[-1][0], (1.0, 0.0))
    # Walls outside the ball so the descent stays a channel.
    walls = []
    for i in range(n - 1):
        s0 = L * i / (n - 1)
        s1 = L * (i + 1) / (n - 1)
        z0, z1 = z_at(s0), z_at(s1)
        for sg in (+1, -1):
            walls.append(box(s0, s1, sg * 22, sg * 34, min(z0, z1) - C.BOT, max(z0, z1) + C.RIM))
    man = man + union(walls)
    man = P._reinforce_sockets(man, [(L - 28.0, 0.0, z_at(L - 28.0))], [(1.0, 0.0)])
    centers = [(s, 0.0, z_at(s) + C.VH) for s in np.linspace(0, L, 28)]
    return P.carve_balls(man, centers)

def tun160():
    man = P.straight_track_r(C.S160, C.DROP160)
    # Side walls stay outside the ball (|y|>=20 > RB=17.5) and join the
    # sloped body along the whole length; roof is above ball top (VH+RB≈42.25).
    left = box(12, 148, -32, -20, -24, 56)
    right = box(12, 148, 20, 32, -24, 56)
    roof = box(12, 148, -32, 32, 44, 56)
    return man + left + right + roof

def switch_y():
    """Y-fork plus a divider slot and two detent grooves.
    The slot sits between the branches after they have separated past a
    35 mm sphere (around x=110). Gate down crosses branch B. Gate up
    is the same shoe raised clear of both balls."""
    man = split_y()
    # Divider pocket. Branch A ball stays inside |y|<18. Branch B centre
    # near x=110 is about y=62, so its ball starts near y=44.
    # The tower is the detent post. It stands above the rail so the raised
    # gate still has a groove to sit in.
    tower = box(106, 118, 18.0, 22.0, 0, 36)
    man = man + tower
    slot = box(96, 128, 22, 40, -8, 40)
    # Grooves in the wall on the A side of the slot (y just under 22).
    groove_down = box(106, 118, 20.6, 23.0, 3.4, 6.2)
    groove_up = box(106, 118, 20.6, 23.0, 25.4, 28.2)
    return man - slot - groove_down - groove_up

def switch_gate():
    """Shoe in the divider slot, rib in the down groove, blade across B."""
    shoe = box(100, 124, 24, 38, 0, 10)
    # Rib is 0.4 mm taller than the groove on each side and 0.6 mm into
    # the wall, so the seated pose is a designed snap, not a free rattle.
    rib = box(108, 116, 20.8, 22.4, 3.0, 6.6)
    blade = box(104, 120, 42, 80, 1, 16)
    return shoe + rib + blade

def pose_switch_gate(mode):
    """'down' blocks branch B. 'up' parks the blade above both balls."""
    gate = switch_gate()
    if mode == 'down':
        return gate
    if mode == 'up':
        return gate.translate([0, 0, 22])
    raise ValueError(mode)

def adapt_out():
    """Thin retaining liner around the v1 exit keel, in the 12 mm wiped nest
    (local +X = downstream into the first track). The keel itself follows the
    chute's 7° slope (chute_center_z - VH), so this collar is swept on the
    same slope. Cavity is an offset of the published keel hexagon
    [(0,1.3),(4.2,5.8),(2.2,5.8),(0,3.5),(-2.2,5.8),(-4.2,5.8)]. Outer stays
    inside the V (v >= |u|) and below the ball (v <= 6.4 < VH-RB = 7.25).
    Place at J0 with the outgoing heading. This is the 48th inventory part."""
    slope = math.tan(math.radians(7.0))
    # v1 chute V-vertex at J0 is chute_center_z(-160)-VH+H_AXLE = 179.763,
    # while the first-track V (V1_ZV_J0) is 180.96. The keel is modelled in
    # the chute-V frame, so the collar (placed at track V) shifts down by
    # that 1.197 mm and then follows the 7° chute slope.
    chute_shift = -1.197
    # Offset keel hexagon. Cavity tips sit above the outer so the subtract
    # opens the top (no paper-thin roof).
    outer = [(0.0, 0.30), (5.35, 6.4), (2.15, 6.4), (0.0, 2.25),
             (-2.15, 6.4), (-5.35, 6.4)]
    cavity = [(0.0, 0.85), (4.70, 6.55), (2.20, 6.55), (0.0, 3.05),
              (-2.20, 6.55), (-4.70, 6.55)]
    x0, x1 = 0.5, 12.0
    def samples(loop):
        return [((x, 0.0, chute_shift - slope * x), (1.0, 0.0), loop) for x in (x0, x1)]
    from geom import sweep
    return sweep(samples(outer)) - sweep(samples(cavity))

def _slim_v(path, w2=23.5):
    """Narrow V-channel that can enter the v1 front-plate hole (±24.5 mm)."""
    vt = min(C.VT, w2 - 0.5)
    loop_body = [(-w2, -C.BOT), (w2, -C.BOT), (w2, C.RIM), (-w2, C.RIM)]
    loop_cut = [(0, -0.2), (vt, vt - 0.2), (vt, C.RIM + 8), (-vt, C.RIM + 8), (-vt, vt - 0.2)]
    samples_b = [(o, t, loop_body) for o, t in path]
    samples_c = [(o, t, loop_cut) for o, t in path]
    from geom import sweep
    return sweep(samples_b) - sweep(samples_c)

def adapt_in(drop=None):
    """Low ramp from a standard female (no ball stack) down to the v1 front-plate inlet.
    Wide V stops short of the plate; a 47 mm throat continues to the inner face
    (not past it). No solid nose block in the ball path. Always downhill."""
    L = C.V1_INLET_L
    drop = 23.2 if drop is None else drop
    if drop < 1.0:
        raise ValueError('ADAPT_IN needs a positive drop')
    # plate outer is ~5.3 mm before L (5 mm plate + 0.3). Stop the 64 mm body 8 mm early.
    L_wide = L - 8.0
    # Hold V through the incoming tongue + female pocket so the 35 mm ball,
    # which spans the joint, rides the V-tongue instead of dropping into it.
    hold = C.TONGUE + 2.0
    def z_at(s):
        if s <= hold:
            return 0.0
        return -drop * (s - hold) / (L - hold)
    n = 16
    path = [((L_wide * i / (n - 1), 0.0, z_at(L_wide * i / (n - 1))), (1.0, 0.0))
            for i in range(n)]
    man = P._track_body(path)
    man = man - P._female_cut(path[0][0], (1.0, 0.0))
    throat = [((L_wide, 0.0, z_at(L_wide)), (1.0, 0.0)), ((L, 0.0, z_at(L)), (1.0, 0.0))]
    man = man + _slim_v(throat, w2=23.5)
    centers = [(s, 0.0, z_at(s) + C.VH) for s in np.linspace(0, L, 20)]
    return P.carve_balls(man, centers)

def low_mount(H_ball=55.0, heading=0.0):
    """Fixed well-anchored post with an integrated keyed ball that seats in a
    low rail's existing socket (Hraw < 70, below the short-class window).
    Same BJ_R / CAP_TO_CENTER stack as ball_cap, so the rail V is at the
    designed height and the hanging socket boss is the mating feature — a
    yoke at the rail underside would collide with that boss. Extra, not one
    of the 24 sleeve/post structures. Print one per needed height. heading
    aligns the roll-key fin with the track (cardinal in the example layouts)."""
    H = float(H_ball)
    post_top = H - C.CAP_TO_CENTER
    if post_top < 6.0:
        raise ValueError(f'low_mount H_ball={H} too short for the cap stack')
    pin = box(-8, 8, -8, 8, -C.EMBED, 4)
    post = box(-8, 8, -8, 8, 0, post_top)
    ball = M.sphere(C.BJ_R, 28).translate([0, 0, H])
    neck = cyl(3.6, C.CAP_TO_CENTER - C.BJ_R + 2.0, 0, 0, post_top)
    fin = box(-7.2, 7.2, -0.9, 0.9, H - 3.0, H + C.BJ_R + 2.4)
    man = pin + post + ball + fin + neck
    if abs(heading) > 1e-9:
        man = man.rotate([0, 0, heading])
    return man

def lift_mount_plate():
    """Two flush well inserts (not an above-tile bar). The v1 housing foot sits on
    the tile at z=0; a raised plate would collide with that foot. Each insert fills
    a 22.4 mm well and provides a r=10.2 hole for the teardrop peg (9.7 mm)."""
    def insert(x):
        body = box(x - 11.0, x + 11.0, -11.0, 11.0, -C.EMBED, 0.0)
        hole = cyl(10.2, C.EMBED + 2.0, x, 0.0, -C.EMBED - 1.0)
        return body - hole
    return insert(-80.0) + insert(80.0)

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
