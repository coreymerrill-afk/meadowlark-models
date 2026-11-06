"""Sample on-grid subsection: S160 + CL90 + S80 on one tile, four supports."""
import math
import numpy as np
from geom import *
import constants as C
import parts as P

# Joints on the 40 mm lattice (first socket of the tile is at 20,20)
J0 = (20.0, 60.0)
J1 = (180.0, 60.0)     # +160 X
J2 = (260.0, 140.0)    # CL90: +80 X, +80 Y
J3 = (260.0, 220.0)    # +80 Y

# Module-math V-vertex at J0 so socket Hs land on 5 mm clicks
# H(s) = V(s) - SOCKET_TO_V; first S160 socket at s=40, drop 5 → H = z_v0 - 5 - 11
ZV0 = 146.0            # → H=130 at (60,60)

SUPPORTS = [
    # x, y, kind, H
    (60.0,  60.0, 'medium', 130.0),
    (140.0, 60.0, 'medium', 120.0),
    (260.0, 140.0, 'medium', 100.0),
    (260.0, 180.0, 'short',   95.0),
]

def _rotz(man, deg):
    return man.rotate([0, 0, deg])

def placed_tile():
    return P.tile()

def placed_support(x, y, kind, H):
    spec = C.CLASSES[kind]
    z_bottom = H - spec['Hmin']
    assert z_bottom >= -1e-6, (kind, H, z_bottom)
    assert spec['Hmin'] - 1e-6 <= H <= spec['Hmax'] + 1e-6
    overlap = spec['Ls'] - z_bottom
    assert overlap >= spec['Omin'] - 1e-6
    sl = P.sleeve(kind).translate([x, y, 0])
    po = P.post(kind).translate([x, y, z_bottom])
    cl = P.lock_clip(kind).translate([x, y, 0])
    cap = P.ball_cap().translate([x, y, z_bottom + spec['Lpost']])
    return dict(sleeve=sl, post=po, clip=cl, cap=cap,
                x=x, y=y, kind=kind, H=H, z_bottom=z_bottom, overlap=overlap)

def placed_tracks():
    s160 = P.straight_track_r(C.S160, C.DROP160).translate([J0[0], J0[1], ZV0])
    # waterfall 0.5 mm at J1
    cl = P.corner_track('L').translate([J1[0], J1[1], ZV0 - C.DROP160 - C.WATERFALL])
    s80 = _rotz(P.straight_track_r(C.S80, C.DROP80), 90).translate(
        [J2[0], J2[1], ZV0 - C.DROP160 - C.WATERFALL - C.DROP90 - C.WATERFALL])
    return dict(S160=s160, CL90=cl, S80=s80)

def sample():
    supports = [placed_support(*s) for s in SUPPORTS]
    return dict(tile=placed_tile(), supports=supports, tracks=placed_tracks())
