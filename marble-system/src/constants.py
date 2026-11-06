"""Locked v2 interface constants — 18x24 base, global 40 mm lattice, honest height classes."""
import math

RB = 17.5
VH = RB * math.sqrt(2)
V_ANG = 45.0

BJ_R = 8.0
BJ_D = 16.0
WALL_ABOVE_BALL = 3.0
SOCKET_TO_V = BJ_R + WALL_ABOVE_BALL          # 11.0
SOCKET_TO_RAIL = SOCKET_TO_V + VH             # 35.7487

# Exact 18 x 24 in base: four 9 x 12 in tiles. Global 40 mm wells, omit seam/edge hits.
P = 40.0
TILE_PX = 304.8                               # printed along H3C 330
TILE_PY = 228.6                               # printed along H3C 320
TILE_H = 12.0
MALE = 8.0
BODY_X = TILE_PX - MALE                       # 296.8
BODY_Y = TILE_PY - MALE                       # 220.6
ASSEMBLED = (2 * TILE_PX, 2 * TILE_PY)        # 609.6 x 457.2
ASSEMBLED_IN = (24.0, 18.0)
WELL = 22.4
WELL_DEPTH = 10.0
EMBED = 9.0
WELL_HALF = WELL / 2
SEAM_X = TILE_PX
SEAM_Y = TILE_PY
GRID_ORIGIN = 20.0
JOINER_KEEP = 12.0
EDGE_KEEP = 14.0

CAP_TO_CENTER = 10.0
CLASSES = {
    'short':  dict(Ls=50.0, Lpost=60.0, Omin=20.0, Hmin=70.0,  Hmax=100.0, qty=8),
    'medium': dict(Ls=80.0, Lpost=90.0, Omin=25.0, Hmin=100.0, Hmax=155.0, qty=10),
    'tall':   dict(Ls=125.0, Lpost=135.0, Omin=40.0, Hmin=145.0, Hmax=230.0, qty=6),
}
POST = 16.0
POST_CLR = 0.20
SLEEVE_OUTER = 22.0
SLEEVE_INNER = POST + 2 * POST_CLR
FLANGE = 30.0
FLANGE_T = 3.5
RACK_PITCH = 5.0
RACK_DEPTH = 3.0
RACK_SLOT_H = 2.8

TW = 64.0
BOT = 4.0
RIM = 18.0
VT = 30.0
TONGUE = 10.0
TONGUE_CLR = 0.40          # rest-state clearance, per side
WATERFALL = 0.50
SLIDE = 20.0
SLIDE_45 = 32.0            # 45° pieces need longer inward reach
S160, S80, S40 = 160.0, 80.0, 40.0
RC90 = 80.0
DROP160, DROP90, DROP80, DROP40, DROP45 = 20.0, 15.0, 10.0, 5.0, 10.0

# v1 lift numbers (for adapters / placement)
V1_H_AXLE = 136.0
V1_ZV_J0 = 180.96
V1_INLET_ZV_END = 22.75
V1_INLET_L = 58.7

BOM48 = [
    ('S160', 8), ('S80', 6), ('S40', 4),
    ('CR90', 5), ('CL90', 5), ('CR45', 2), ('CL45', 2),
    ('SPLIT_Y', 2), ('MERGE_Y', 2), ('FUNNEL', 2),
    ('HX360', 2), ('DROP40', 2), ('SPAN240', 2),
    ('TUN160', 1), ('SWITCH', 1), ('ADAPT_OUT', 1), ('ADAPT_IN', 1),
]

# Extras not in the 48 and not in the 24 support structures
EXTRAS = {
    'switch_gate': 1,
    'low_mount': 6,
    'lift_mount_plate': 1,
}

ENVELOPE = (330.0, 320.0, 325.0)

def global_well_candidates():
    xs, ys = [], []
    x = GRID_ORIGIN
    while x <= ASSEMBLED[0] - GRID_ORIGIN + 0.01:
        xs.append(round(x, 4)); x += P
    y = GRID_ORIGIN
    while y <= ASSEMBLED[1] - GRID_ORIGIN + 0.01:
        ys.append(round(y, 4)); y += P
    return xs, ys

def well_ok(x, y):
    """True if a 22.4 mm well centered at (x,y) stays clear of edges, seams, joiners."""
    hx = WELL_HALF
    # outer board edges
    if x - hx < EDGE_KEEP or x + hx > ASSEMBLED[0] - EDGE_KEEP:
        return False
    if y - hx < EDGE_KEEP or y + hx > ASSEMBLED[1] - EDGE_KEEP:
        return False
    # seams (the mid-board tile joints)
    if abs(x - SEAM_X) < hx + 2.0:
        return False
    if abs(y - SEAM_Y) < hx + 2.0:
        return False
    # joiner bands on each tile (males/females occupy 8 mm + margin at every tile edge)
    for x0 in (0.0, TILE_PX):
        if x0 <= x <= x0 + TILE_PX:
            loc = x - x0
            if loc < JOINER_KEEP or loc > TILE_PX - JOINER_KEEP:
                return False
    for y0 in (0.0, TILE_PY):
        if y0 <= y <= y0 + TILE_PY:
            loc = y - y0
            if loc < JOINER_KEEP or loc > TILE_PY - JOINER_KEEP:
                return False
    return True

def all_wells():
    xs, ys = global_well_candidates()
    return [(x, y) for x in xs for y in ys if well_ok(x, y)]

def wells_on_tile(ix, iy):
    x0, y0 = ix * TILE_PX, iy * TILE_PY
    out = []
    for x, y in all_wells():
        if x0 - 0.1 <= x <= x0 + TILE_PX + 0.1 and y0 - 0.1 <= y <= y0 + TILE_PY + 0.1:
            out.append((x, y))
    return out
