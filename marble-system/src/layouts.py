"""Layout A is the assembleable default on the 18x24 board, lift at (460, 100).
Layout B is a design study only: the 80 mm helix does not clear the lift.

Each is an alternative assembly (not installed at once). The v1 lift sits in
standard orientation (chute toward -X, inlet from +Y) via lift_mount_plate.
Supports with H < 70 use disclosed low_mount extras, not the 24 ball-jointed posts.
"""
import math
import numpy as np
from geom import *
import constants as C
import parts as P
import catalog as Cat

WF = C.WATERFALL
STV = C.SOCKET_TO_V

def _rot(man, deg):
    return man if abs(deg) < 1e-9 else man.rotate([0, 0, deg])

def place(man, xy, heading, z):
    return _rot(man, heading).translate([xy[0], xy[1], z])

def pick_class(H):
    for kind, spec in C.CLASSES.items():
        if spec['Hmin'] - 1e-6 <= H <= spec['Hmax'] + 1e-6:
            return kind
    return None

def snap5(v):
    return 5.0 * round(v / 5.0)

def support_record(x, y, V):
    Hraw = V - STV
    if Hraw < 70 - 0.6:
        return dict(x=x, y=y, kind='low_mount', H=None, Hraw=round(Hraw, 2),
                    V=round(V, 2), extra=True)
    H = snap5(Hraw)
    # keep inside a real class window after snapping
    kind = pick_class(H)
    if kind is None:
        # nudge toward the nearest window
        if H < 70:
            return dict(x=x, y=y, kind='low_mount', H=None, Hraw=round(Hraw, 2),
                        V=round(V, 2), extra=True)
        if H > 230:
            H = 230.0
        kind = pick_class(H) or pick_class(H - 5) or pick_class(H + 5)
    spec = C.CLASSES[kind]
    z_bottom = H - spec['Hmin']
    overlap = spec['Ls'] - z_bottom
    return dict(x=x, y=y, kind=kind, H=H, Hraw=round(Hraw, 2), V=round(V, 2),
                z_bottom=z_bottom, overlap=overlap, extra=False)

WELLS = set(C.all_wells())

def nearest_well(x, y, max_d=0.15):
    if (round(x, 4), round(y, 4)) in {(round(a, 4), round(b, 4)) for a, b in WELLS}:
        return (float(x), float(y))
    best, bd = None, 1e9
    for a, b in WELLS:
        d = (a - x) ** 2 + (b - y) ** 2
        if d < bd:
            best, bd = (a, b), d
    if math.sqrt(bd) <= max_d:
        return best
    return None

def capture_well(x, y, heading_deg, slide_plus, slide_minus):
    """First well whose plan distance to the socket stadium axis is <= BJ_R+0.3."""
    t = np.array([math.cos(math.radians(heading_deg)), math.sin(math.radians(heading_deg))])
    reach = C.BJ_R + 0.30
    hit = []
    for wx, wy in WELLS:
        d = np.array([wx - x, wy - y])
        along = float(d @ t)
        lat = float(np.hypot(*(d - along * t)))
        if -slide_minus - 1e-6 <= along <= slide_plus + 1e-6 and lat <= reach + 1e-6:
            hit.append((lat, along, (wx, wy)))
    hit.sort()
    return hit[0][2] if hit else None


# ---------------------------------------------------------------------------
# Shared lift geometry (standard v1 orientation)
# ---------------------------------------------------------------------------
def lift_frame(axle):
    ax, ay = axle
    return dict(
        axle=(ax, ay),
        pegs=((ax - 80.0, ay), (ax + 80.0, ay)),
        J0=(ax - 160.0, ay),
        J11=(ax, ay + 80.0),
        inlet_xy=(ax, ay + 21.3),
        heading_out=180.0,
        heading_in=270.0,
    )


def _chain_z(start_V, drops):
    """Return (origin_z, end_V) for each piece given successive drops.
    origin_z = previous_end - WATERFALL; end_V = origin_z - drop."""
    prev_end = start_V
    out = []
    for d in drops:
        z0 = prev_end - WF
        end = z0 - d
        out.append((z0, end))
        prev_end = end
    return out


def _drop_posts_in_tracks(inst, pieces):
    """Skip a post whose shaft meets a track solid by more than a kiss.
    The well can sit 20 mm off a socket centre at the end of an S80 slide."""
    kept = []
    for rec in inst:
        if rec.get('kind') == 'low_mount' or 'post' not in rec:
            kept.append(rec)
            continue
        clash = False
        for piece in pieces:
            try:
                hit = rec['post'] ^ piece['solid']
            except Exception:
                clash = True
                break
            if (not hit.is_empty()) and float(hit.volume()) > 8.0:
                clash = True
                break
        if clash:
            continue
        kept.append(rec)
    return kept


# ===========================================================================
# Layout A — simple loop
# ===========================================================================
def layout_A():
    axle = (460.0, 100.0)
    L = lift_frame(axle)
    J0, J11 = L['J0'], L['J11']
    ZV0 = C.V1_ZV_J0  # 180.96
    # pieces after ADAPT_OUT, origins at these joints, start heading, kind, drop
    # A1 S160 (300,100) -X → (140,100)
    # A2 CR R (140,100) -X → (60,180) +Y
    # A3 S160 (60,180) +Y → (60,340)
    # A4 CR R (60,340) +Y → (140,420) +X
    # A5 S160 (140,420) +X → (300,420)
    # A6 S80  (300,420) +X → (380,420)
    # A7 CR R (380,420) +X → (460,340) -Y
    # A8 S160 (460,340) -Y → (460,180)
    # A9 ADAPT_IN
    seq = [
        dict(name='S160_1', kind='S160', origin=(300.0, 100.0), hdg=180.0, drop=C.DROP160,
             end=(140.0, 100.0)),
        dict(name='CR1', kind='CR90', origin=(140.0, 100.0), hdg=180.0, drop=C.DROP90,
             end=(60.0, 180.0)),
        dict(name='S160_2', kind='S160', origin=(60.0, 180.0), hdg=90.0, drop=C.DROP160,
             end=(60.0, 340.0)),
        dict(name='CR2', kind='CR90', origin=(60.0, 340.0), hdg=90.0, drop=C.DROP90,
             end=(140.0, 420.0)),
        dict(name='S160_3', kind='S160', origin=(140.0, 420.0), hdg=0.0, drop=C.DROP160,
             end=(300.0, 420.0)),
        dict(name='S80_1', kind='S80', origin=(300.0, 420.0), hdg=0.0, drop=C.DROP80,
             end=(380.0, 420.0)),
        dict(name='CR3', kind='CR90', origin=(380.0, 420.0), hdg=0.0, drop=C.DROP90,
             end=(460.0, 340.0)),
        dict(name='S160_4', kind='S160', origin=(460.0, 340.0), hdg=270.0, drop=C.DROP160,
             end=(460.0, 180.0)),
    ]
    # first piece origin z = ZV0 (no waterfall before the first rail; ADAPT_OUT mates at J0)
    zs = []
    prev_end = ZV0
    for i, p in enumerate(seq):
        z0 = ZV0 if i == 0 else prev_end - WF
        endV = z0 - p['drop']
        zs.append((z0, endV))
        prev_end = endV
        p['z0'] = z0
        p['endV'] = endV
    j11_V = seq[-1]['endV']
    adapt_z = j11_V - WF
    adapt_drop = adapt_z - C.V1_INLET_ZV_END
    assert adapt_drop > 1.0, adapt_drop

    pieces = []
    builders = {
        'S160': lambda: P.straight_track_r(C.S160, C.DROP160),
        'S80': lambda: P.straight_track_r(C.S80, C.DROP80),
        'S40': lambda: P.straight_track_r(C.S40, C.DROP40),
        'CR90': lambda: P.corner_track('R'),
        'CL90': lambda: P.corner_track('L'),
        'HX360R': lambda: Cat.helix_360(turn='R'),
        'ADAPT_OUT': Cat.adapt_out,
        'ADAPT_IN': lambda d=adapt_drop: Cat.adapt_in(d),
    }
    # ADAPT_OUT is a thin keel liner placed AT J0, heading downstream (180).
    # It lives in the 12 mm wiped nest (into the first track), not in the chute.
    pieces.append(dict(name='ADAPT_OUT', kind='ADAPT_OUT', origin=J0, hdg=180.0,
                       z0=ZV0, solid=place(Cat.adapt_out(), J0, 180.0, ZV0)))
    for p in seq:
        man = builders[p['kind']]()
        p['solid'] = place(man, p['origin'], p['hdg'], p['z0'])
        pieces.append(p)
    pieces.append(dict(
        name='ADAPT_IN', kind='ADAPT_IN', origin=J11, hdg=270.0, z0=adapt_z,
        drop=adapt_drop, solid=place(Cat.adapt_in(adapt_drop), J11, 270.0, adapt_z)))

    # sockets / supports
    # For each rail, evaluate designed stations in world XY + V
    supports = []
    seen = set()

    def add_sup(xy, V, heading=0.0):
        key = (round(xy[0], 1), round(xy[1], 1))
        if key in seen:
            return
        rec = support_record(xy[0], xy[1], V)
        well = nearest_well(xy[0], xy[1], max_d=0.2)
        rec['well'] = well
        rec['has_well'] = well is not None
        rec['heading'] = heading
        if well is None:
            rec['skipped'] = 'no well at socket (seam/edge/joiner omit)'
        seen.add(key)
        supports.append(rec)

    # explicit stations (world) with V and optional slide capture
    def station_straight(origin, hdg, z0, L, drop, ss):
        t = np.array([math.cos(math.radians(hdg)), math.sin(math.radians(hdg))])
        for s in ss:
            xy = (origin[0] + t[0] * s, origin[1] + t[1] * s)
            V = z0 - drop * s / L
            well = capture_well(xy[0], xy[1], hdg, C.SLIDE, C.SLIDE)
            if well:
                add_sup(well, V, hdg)
            else:
                add_sup(xy, V, hdg)

    def station_corner(origin, hdg, z0, drop, turn='R'):
        # sockets at start (inward +s) and end (inward -s)
        s = 1 if turn == 'L' else -1
        t0 = np.array([math.cos(math.radians(hdg)), math.sin(math.radians(hdg))])
        # start
        well = capture_well(origin[0], origin[1], hdg, C.SLIDE, 0.0)
        add_sup(well if well else origin, z0, hdg)
        # end
        end = (origin[0] + C.RC90 * (t0[0] + s * (-t0[1] if False else 0)),)
        # R90 displacement: local (80, -80) rotated by hdg
        ca, sa = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
        loc = (C.RC90, s * C.RC90)  # L: (80,80), R: (80,-80)
        end_xy = (origin[0] + ca * loc[0] - sa * loc[1],
                  origin[1] + sa * loc[0] + ca * loc[1])
        end_hdg = hdg + s * 90.0
        well = capture_well(end_xy[0], end_xy[1], end_hdg, 0.0, C.SLIDE)
        add_sup(well if well else end_xy, z0 - drop, end_hdg)

    for p in seq:
        if p['kind'] in ('S160', 'S80', 'S40'):
            Llen = {'S160': C.S160, 'S80': C.S80, 'S40': C.S40}[p['kind']]
            ss = P._socket_stations_straight(Llen)
            station_straight(p['origin'], p['hdg'], p['z0'], Llen, p['drop'], ss)
        elif p['kind'] == 'CR90':
            station_corner(p['origin'], p['hdg'], p['z0'], p['drop'], 'R')

    # instantiate solids for supports that have wells
    inst = []
    for rec in supports:
        if not rec.get('has_well'):
            continue
        x, y = rec['well']
        if rec['kind'] == 'low_mount':
            hdg = rec.get('heading', 0.0)
            inst.append(dict(rec, H_ball=rec['Hraw'], heading=hdg,
                             solid=Cat.low_mount(rec['Hraw'], hdg).translate([x, y, 0])))
        else:
            inst.append(dict(rec, **_support_solids(x, y, rec['kind'], rec['H'])))
    inst = _drop_posts_in_tracks(inst, pieces)

    plate = Cat.lift_mount_plate().translate([axle[0], axle[1], 0])
    tiles = [P.tile(ix, iy).translate([ix * C.TILE_PX, iy * C.TILE_PY, 0])
             for ix in (0, 1) for iy in (0, 1)]

    return dict(
        name='A_simple_loop',
        description='Translated v1-style downhill loop on the 18x24 board. Lift axle at (460, 100).',
        lift=L,
        ZV0=ZV0,
        J0=J0, J11=J11,
        adapt_in_drop=adapt_drop,
        adapt_in_slope_deg=math.degrees(math.atan(adapt_drop / C.V1_INLET_L)),
        pieces=pieces,
        supports=supports,
        support_instances=inst,
        lift_mount_plate=plate,
        tiles=tiles,
        seq_meta=[{k: p[k] for k in p if k != 'solid'} for p in pieces],
    )


def _support_solids(x, y, kind, H):
    spec = C.CLASSES[kind]
    z_bottom = H - spec['Hmin']
    return dict(
        sleeve=P.sleeve(kind).translate([x, y, 0]),
        post=P.post(kind).translate([x, y, z_bottom]),
        clip=P.lock_clip(kind).translate([x, y, 0]),
        cap=P.ball_cap().translate([x, y, z_bottom + spec['Lpost']]),
        z_bottom=z_bottom, overlap=spec['Ls'] - z_bottom,
    )


# ===========================================================================
# Layout B — helix feature
# ===========================================================================
def layout_B():
    """Design study, not a working route.

    The catalog helix is a real 80 mm pitch so a full turn does not cross
    itself. Placed beside the lift on this 18x24 board, that coil occupies
    the housing. This layout is kept so the collision can be inspected.
    It is not a complete example.
    """
    axle = (420.0, 100.0)
    L = lift_frame(axle)
    J0, J11 = L['J0'], L['J11']
    ZV0 = C.V1_ZV_J0
    seq = [
        dict(name='HX1', kind='HX360R', origin=(260.0, 100.0), hdg=180.0, drop=80.0,
             end=(220.0, 100.0)),
        dict(name='CR1', kind='CR90', origin=(220.0, 100.0), hdg=180.0, drop=C.DROP90,
             end=(140.0, 180.0)),
        dict(name='CR2', kind='CR90', origin=(140.0, 180.0), hdg=90.0, drop=C.DROP90,
             end=(220.0, 260.0)),
        dict(name='S80_1', kind='S80', origin=(220.0, 260.0), hdg=0.0, drop=C.DROP80,
             end=(300.0, 260.0)),
        dict(name='S40_1', kind='S40', origin=(300.0, 260.0), hdg=0.0, drop=C.DROP40,
             end=(340.0, 260.0)),
        dict(name='CR3', kind='CR90', origin=(340.0, 260.0), hdg=0.0, drop=C.DROP90,
             end=(420.0, 180.0)),
    ]
    prev_end = ZV0
    for i, pce in enumerate(seq):
        z0 = ZV0 if i == 0 else prev_end - WF
        endV = z0 - pce['drop']
        pce['z0'] = z0
        pce['endV'] = endV
        prev_end = endV
    j11_V = seq[-1]['endV']
    adapt_z = j11_V - WF
    adapt_drop = adapt_z - C.V1_INLET_ZV_END
    assert adapt_drop > 1.0, (adapt_drop, adapt_z)

    pieces = []
    pieces.append(dict(name='ADAPT_OUT', kind='ADAPT_OUT', origin=J0, hdg=180.0,
                       z0=ZV0, solid=place(Cat.adapt_out(), J0, 180.0, ZV0)))
    builders = {
        'S160': lambda: P.straight_track_r(C.S160, C.DROP160),
        'S80': lambda: P.straight_track_r(C.S80, C.DROP80),
        'S40': lambda: P.straight_track_r(C.S40, C.DROP40),
        'CR90': lambda: P.corner_track('R'),
        'HX360R': lambda: Cat.helix_360(turn='R'),
    }
    for pce in seq:
        pce['solid'] = place(builders[pce['kind']](), pce['origin'], pce['hdg'], pce['z0'])
        pieces.append(pce)
    pieces.append(dict(
        name='ADAPT_IN', kind='ADAPT_IN', origin=J11, hdg=270.0, z0=adapt_z,
        drop=adapt_drop, solid=place(Cat.adapt_in(adapt_drop), J11, 270.0, adapt_z)))

    supports = []
    seen = set()

    def add_sup(xy, V, heading=0.0):
        key = (round(xy[0], 1), round(xy[1], 1))
        if key in seen:
            return
        rec = support_record(xy[0], xy[1], V)
        well = nearest_well(xy[0], xy[1], max_d=0.2)
        rec['well'] = well
        rec['has_well'] = well is not None
        rec['heading'] = heading
        if well is None:
            rec['skipped'] = 'no well at socket (seam/edge/joiner omit)'
        seen.add(key)
        supports.append(rec)

    def station_straight(origin, hdg, z0, Llen, drop, ss):
        t = np.array([math.cos(math.radians(hdg)), math.sin(math.radians(hdg))])
        for s in ss:
            xy = (origin[0] + t[0] * s, origin[1] + t[1] * s)
            V = z0 - drop * s / Llen
            well = capture_well(xy[0], xy[1], hdg, C.SLIDE, C.SLIDE)
            if well:
                add_sup(well, V, hdg)
            else:
                add_sup(xy, V, hdg)

    def station_corner(origin, hdg, z0, drop, turn='R'):
        s = -1 if turn == 'R' else 1
        ca, sa = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
        well = capture_well(origin[0], origin[1], hdg, C.SLIDE, 0.0)
        add_sup(well if well else origin, z0, hdg)
        loc = (C.RC90, s * C.RC90)
        end_xy = (origin[0] + ca * loc[0] - sa * loc[1],
                  origin[1] + sa * loc[0] + ca * loc[1])
        end_hdg = hdg + s * 90.0
        well = capture_well(end_xy[0], end_xy[1], end_hdg, 0.0, C.SLIDE)
        add_sup(well if well else end_xy, z0 - drop, end_hdg)

    add_sup((260.0, 100.0), ZV0, 180.0)
    add_sup((220.0, 100.0), seq[0]['endV'], 180.0)
    add_sup((180.0, 140.0), ZV0 - 80.0 * 56.0 / 360.0, 180.0 - 56.0)
    add_sup((340.0, 140.0), ZV0 - 80.0 * 298.0 / 360.0, 180.0 - 298.0)
    for rec in supports:
        if rec.get('well') in ((180.0, 140.0), (340.0, 140.0)):
            rec['kind'] = 'low_mount'
            rec['H'] = None
            rec['extra'] = True
            rec['note'] = 'exact-height keyed extra; Hraw not on 5 mm rack'
    for pce in seq:
        if pce['kind'] in ('S160', 'S80', 'S40'):
            Llen = {'S160': 160.0, 'S80': 80.0, 'S40': 40.0}[pce['kind']]
            station_straight(pce['origin'], pce['hdg'], pce['z0'], Llen, pce['drop'],
                             P._socket_stations_straight(Llen))
        elif pce['kind'] == 'CR90':
            station_corner(pce['origin'], pce['hdg'], pce['z0'], pce['drop'], 'R')

    inst = []
    for rec in supports:
        if not rec.get('has_well'):
            continue
        x, y = rec['well']
        if rec['kind'] == 'low_mount':
            hdg = rec.get('heading', 0.0)
            inst.append(dict(rec, H_ball=rec['Hraw'], heading=hdg,
                             solid=Cat.low_mount(rec['Hraw'], hdg).translate([x, y, 0])))
        else:
            inst.append(dict(rec, **_support_solids(x, y, rec['kind'], rec['H'])))
    inst = _drop_posts_in_tracks(inst, pieces)

    plate = Cat.lift_mount_plate().translate([axle[0], axle[1], 0])
    tiles = [P.tile(ix, iy).translate([ix * C.TILE_PX, iy * C.TILE_PY, 0])
             for ix in (0, 1) for iy in (0, 1)]

    return dict(
        name='B_helix',
        status='design_study',
        description='Design study only. The 80 mm helix does not clear the lift on this board. Not a working route.',
        lift=L,
        ZV0=ZV0,
        J0=J0, J11=J11,
        adapt_in_drop=adapt_drop,
        adapt_in_slope_deg=math.degrees(math.atan(adapt_drop / C.V1_INLET_L)),
        pieces=pieces,
        supports=supports,
        support_instances=inst,
        lift_mount_plate=plate,
        tiles=tiles,
        seq_meta=[{k: pce[k] for k in pce if k != 'solid'} for pce in pieces],
    )


def summarize(lay):
    posts = [s for s in lay['support_instances'] if s['kind'] != 'low_mount']
    lows = [s for s in lay['support_instances'] if s['kind'] == 'low_mount']
    kinds = {}
    for p in lay['pieces']:
        kinds[p['kind']] = kinds.get(p['kind'], 0) + 1
    skipped = [s for s in lay['supports'] if not s.get('has_well')]
    return dict(
        name=lay['name'],
        n_track_pieces=len(lay['pieces']),
        piece_kinds=kinds,
        n_posts=len(posts),
        n_low_mounts=len(lows),
        n_skipped_sockets=len(skipped),
        posts=[{k: p[k] for k in ('x', 'y', 'kind', 'H', 'Hraw', 'V', 'well') if k in p} for p in posts],
        low_mounts=[{k: p[k] for k in ('x', 'y', 'Hraw', 'V', 'well', 'heading', 'H_ball') if k in p} for p in lows],
        skipped=[{k: s[k] for k in ('x', 'y', 'Hraw', 'V', 'skipped') if k in s} for s in skipped],
        adapt_in_drop=round(lay['adapt_in_drop'], 2),
        adapt_in_slope_deg=round(lay['adapt_in_slope_deg'], 2),
        status=lay.get('status', 'default'),
        lift=lay['lift'],
        within_24=len(posts) <= 24,
    )
