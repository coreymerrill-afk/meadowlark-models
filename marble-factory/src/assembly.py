"""Canonical layout, part catalogue (print-orientation STLs), assembly transforms."""
import numpy as np, math
from geom import *
import tracks as T, lift as L

LIFT_POS = np.array([80.0, 0.0, L.H_AXLE])

def Tm(R=None, t=(0, 0, 0)):
    m = np.eye(4)
    if R is not None:
        m[:3, :3] = R
    m[:3, 3] = t
    return m

def Rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def Rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def Ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def apply(man, m4):
    return man.transform(m4[:3])

# Nest match: tongue tip (v=1.2 above chute vertex line) equals first-track V vertex.
NEST_X = L.CHUTE_END_X + 12.0  # -160
TONGUE_TIP = 1.2
ZV_J0 = float(L.H_AXLE + L.chute_center_z(NEST_X) - T.VH + TONGUE_TIP)

# Default playable route: lift chute -> straights and RIGHT corners only -> inlet.
# Every joint preserves heading (straights) or turns 90° with a swept R=80 corner.
# Switch / spinner / merge are optional extras and are NOT in this circuit.
ROUTE = [
    ('S160', 'J0', 'J1', 180),
    ('CR',   'J1', 'J2', 180),
    ('S160', 'J2', 'J3', 90),
    ('CR',   'J3', 'J4', 90),
    ('S160', 'J4', 'J5', 0),
    ('S80',  'J5', 'J6', 0),
    ('CR',   'J6', 'J7', 0),
    ('S160', 'J7', 'J11', 270),
    ('IN',   'J11', None, 270),
]
XY = {
    'J0': (-80.0, 0.0), 'J1': (-240.0, 0.0), 'J2': (-320.0, 80.0), 'J3': (-320.0, 240.0),
    'J4': (-240.0, 320.0), 'J5': (-80.0, 320.0), 'J6': (0.0, 320.0),
    'J7': (80.0, 240.0), 'J11': (80.0, 80.0),
}
# 20 mm drop / 160 mm run = 7.13° (matches the 7° exit chute over the nest).
DROPS_A = {'S160': 20.0, 'CR': 20.0, 'CL': 20.0, 'SW': T.SW_DA, 'SP': 20.0, 'MG': T.MG_DA, 'S80': 10.0}
DROPS_B = {'SW': T.SW_DB_OUT}
END_HEADING = {'S160': lambda h: h, 'S80': lambda h: h, 'IN': lambda h: h,
               'CR': lambda h: (h - 90) % 360, 'CL': lambda h: (h + 90) % 360,
               'SP': lambda h: h, 'SW': lambda h: h, 'MG': lambda h: h}


def joint_heights():
    z = {'J0': ZV_J0}
    for mod, a, b, h in ROUTE:
        if mod == 'IN':
            continue
        za = z[a] if isinstance(a, str) else z[a[0]]
        if isinstance(b, tuple):
            z[b[0]] = za - DROPS_A[mod]
            z[b[1]] = za - DROPS_B[mod]
        else:
            z[b] = za - DROPS_A[mod]
    return z


ZV = joint_heights()
INLET_END_Y = L.PLATE_IN + 0.3
INLET_L = XY['J11'][1] - INLET_END_Y
INLET_ZV_END = L.H_AXLE + L.INLET_CZ - T.VH
INLET_DROP = ZV['J11'] - INLET_ZV_END

FLIP = Tm(Rx(180))
CAT = {}


def reg(name, builder, print_from_model, color, supports=False, brim=False, desc=''):
    CAT[name] = dict(builder=builder, P=print_from_model, color=color,
                     supports=supports, brim=brim, desc=desc, inst=[])


def to_bed(man, R4):
    f = apply(man, R4)
    bb = f.bounding_box()
    return Tm(None, (-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2])) @ R4


def flip_to_bed(man):
    return to_bed(man, FLIP)


MODS = {
    'S160': lambda: T.mod_straight(160, 20)[0],
    'S80': lambda: T.mod_straight(80, 10)[0],
    'CR': lambda: T.mod_corner('R', 20)[0],
    'CL': lambda: T.mod_corner('L', 20)[0],
    'SW': lambda: T.mod_switch()[0],
    'SP': lambda: T.mod_spinner(20)[0],
    'MG': lambda: T.mod_merge()[0],
    'IN': lambda: T.mod_inlet(INLET_L, INLET_DROP)[0],
}
NAMES = {
    'S160': 'track_straight_160', 'S80': 'track_straight_80',
    'CR': 'track_corner_right', 'CL': 'track_corner_left',
    'SW': 'track_switch_Y', 'SP': 'track_spinner', 'MG': 'track_merge_Y',
    'IN': 'lift_inlet_chute',
}
COL = {
    'S160': '#2E86DE', 'S80': '#2E86DE', 'CR': '#10AC84', 'CL': '#10AC84',
    'SW': '#F368E0', 'SP': '#FF9F43', 'MG': '#F368E0', 'IN': '#54A0FF',
}


def roty_xz(om):
    c, s = math.cos(math.radians(om)), math.sin(math.radians(om))
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def build_catalogue(wheel_omega=0.0, crank_angle=0.0, pawl_phi=0.0, gate_on=True):
    CAT.clear()
    for k, f in MODS.items():
        man = f()
        reg(NAMES[k], (lambda man=man: man), flip_to_bed(man), COL[k],
            desc='track module — print rim-down (upside down)')
    for mod, a, b, h in ROUTE:
        ja = a if isinstance(a, str) else a[0]
        x, y = XY[ja]
        A = Tm(None, (x, y, ZV[ja])) @ Tm(Rz(h))
        CAT[NAMES[mod]]['inst'].append(dict(at=ja, M=A))

    # Optional extras: catalogued and printable, NOT placed on the default loop.
    gate = T.gate_bridge()
    reg('switch_gate', lambda: gate, to_bed(gate, Tm(Rx(180))), '#FECA57',
        desc='OPTIONAL extra — not in the default loop. Drop-gate for track_switch_Y.')
    rot = T.spinner_rotor()
    reg('spinner_rotor', lambda: rot, to_bed(rot, Tm(Rx(-90))), '#FF6B6B',
        desc='OPTIONAL extra — 4-paddle rotor (use with track_spinner as a S160 substitute).')
    post = T.spinner_post(side=+1)
    reg('spinner_post', lambda: post, to_bed(post, Tm()), '#FF9F43',
        desc='OPTIONAL extra — U-slot post (print 2, second mirrored 180°).')
    ret = T.spinner_retainer()
    reg('spinner_retainer', lambda: ret, to_bed(ret, FLIP), '#FECA57',
        desc='OPTIONAL extra — retainer arch that clears the paddle disc.')

    # stands
    for j, (x, y) in XY.items():
        cap = ZV[j] - T.BOT
        nm = 'stand_%s_h%03d' % (j, round(cap))
        st = T.stand(cap)
        reg(nm, (lambda st=st: st), to_bed(st, FLIP), '#8395A7',
            desc='stand, cap top %.1f mm above tile' % cap)
        CAT[nm]['inst'].append(dict(at=j, M=Tm(None, (x, y, 0))))

    # tiles 3x2 covering sockets x=-320..320, y=0..400
    tile = T.base_tile()
    reg('base_tile', lambda: tile, Tm(None, (0, 0, T.TILE_H)), '#C8D6E5',
        desc='240 mm lattice tile with dovetails and 9 stand sockets')
    for i, x0 in enumerate((-360.0, -120.0, 120.0)):
        for jj, y0 in enumerate((-40.0, 200.0)):
            CAT['base_tile']['inst'].append(dict(at='tile%d%d' % (i, jj), M=Tm(None, (x0, y0, 0))))

    # lift
    LP = Tm(None, LIFT_POS)
    hb = L.housing_back()
    reg('lift_housing_back', lambda: hb, to_bed(hb, Tm(Rx(90))), '#576574',
        desc='back plate + guide + exit chute + roof + pawl pin; plate face on bed')
    CAT['lift_housing_back']['inst'].append(dict(at='lift', M=LP))
    hf = L.housing_front()
    reg('lift_housing_front', lambda: hf, to_bed(hf, Tm(Rx(-90))), '#48DBFB',
        desc='front plate with viewing slots and inlet port; outer face on bed')
    CAT['lift_housing_front']['inst'].append(dict(at='lift', M=LP))
    wh = L.wheel_half()
    reg('lift_wheel_half', lambda: wh, Tm(), '#EE5253',
        desc='paddle-wheel half; split face on bed (print 2)')
    for Mx in L.wheel_assembly_transforms(wheel_omega):
        m4 = np.eye(4)
        m4[:3] = Mx
        CAT['lift_wheel_half']['inst'].append(dict(at='lift', M=LP @ m4))
    axl = L.axle()
    # print standing on the head
    reg('lift_axle', lambda: axl, to_bed(axl, Tm(Rx(-90))), '#F5F6FA',
        desc='hex axle; print standing on the head (no supports)')
    CAT['lift_axle']['inst'].append(dict(at='lift', M=LP))
    cr = L.crank(0.0)
    reg('lift_crank', lambda: cr, to_bed(cr, Tm(Rx(-90))), '#FECA57',
        desc='crank arm + knob; arm face on bed, knob stands up')
    CAT['lift_crank']['inst'].append(dict(at='lift', M=LP @ Tm(roty_xz(crank_angle))))
    cl = L.clip()
    reg('lift_clip', lambda: cl, Tm(), '#FF9F43', desc='snap U-clip on the axle groove (front)')
    # clip modelled in XY, thickness +z; map to XZ plane at groove, opening toward -z
    CAT['lift_clip']['inst'].append(dict(
        at='lift',
        M=LP @ Tm(None, (0.0, (L.AX['groove'][0] + L.AX['groove'][1]) / 2, 0.0))
          @ Tm(Rx(90)) @ Tm(None, (0.0, -4.0, -2.0))))
    pw = L.pawl(0.0)
    reg('lift_pawl', lambda: pw, to_bed(pw, Tm(Rx(90))), '#222F3E',
        desc='gravity anti-reverse pawl; print on its flat side')
    CAT['lift_pawl']['inst'].append(dict(at='lift', M=LP @ Tm(roty_xz(pawl_phi)) if False else LP))
    # pawl rotation is about Q, not the wheel axis — keep rest pose here; motion tested separately

    b = L.ball()
    reg('ball_35', lambda: b, to_bed(b, Tm()), '#FF4757', supports=True,
        desc='35 mm ball with 0.5 mm bed flat; supports required (or print as two hemispheres)')
    for k in range(6):
        CAT['ball_35']['inst'].append(dict(at='queue', M=None))

    # test / diagnostic
    tb = L.lift_test_base()
    reg('lift_test_base', lambda: tb, Tm(None, (0, 0, 12)), '#C8D6E5',
        desc='first-print frame: sockets for the two housing pegs and the inlet stand')
    # not placed in the full assembly (tiles replace it)
    coupon = make_coupon()
    reg('fit_coupon', lambda: coupon, Tm(), '#A3CB38',
        desc='first-print fit coupon: pegs, sockets, hexes, clip groove, spinner slot')

    return CAT


def make_coupon():
    """A 90×70×14 plate carrying every repeating interface at final sizes."""
    plate = box(0, 96, 0, 72, 0, 3.2)
    bits = [plate]
    # stand peg (as on a stand)
    bits.append(cyl(9.7, 9.5, 16, 16, 3.2))
    # tile / stand socket (hole through)
    bits.append(cyl(20, 3.2, 42, 16, 0) - cyl(10.2, 5, 42, 16, -1))
    # track half-disc peg standing up
    half = box(58, 80, 6, 26, 3.2, 13.2)
    bits.append(cyl(9.7, 10, 70, 16, 3.2) ^ half)
    # hex 16.4 (wheel) and hex 13.4 (crank) holes
    bits.append(box(6, 30, 34, 66, 0, 8) - poly_extrude([(16 + x, 50 + y) for x, y in hexagon(16.4)], 10, -1))
    bits.append(box(34, 56, 34, 66, 0, 8) - poly_extrude([(45 + x, 50 + y) for x, y in hexagon(13.4)], 10, -1))
    # journal holes
    bits.append(box(60, 92, 34, 54, 0, 6) - cyl(11.4, 8, 70, 44, -1) - cyl(9.15, 8, 84, 44, -1))
    # clip-groove pin + a printed clip nestled beside it
    pin = cyl(4.75, 14, 16, 60, 3.2)
    groove = cyl(4.75, 4.4, 16, 60, 3.2 + 5)  # leave as body; actually cut a groove
    pin = pin - (cyl(8, 4.4, 16, 60, 3.2 + 5) - cyl(4.75, 4.4, 16, 60, 3.2 + 5))
    # wait that adds nothing... cut an annular groove: pin minus (outer-inner ring)
    # pin already r=4.75; groove should locally be r=4.75 still? Real groove r=4.75 over 4.4 mm.
    # The clip seats on r=4.75. No extra cut needed; the pin IS the groove diameter.
    # Add larger shoulders each side:
    pin = union([cyl(6.5, 5, 16, 60, 3.2), cyl(4.75, 4.4, 16, 60, 8.2), cyl(6.5, 5, 16, 60, 12.6)])
    bits.append(pin)
    clip = L.clip().rotate([90, 0, 0]).translate([40, 70, 3.2])
    # don't union clip — keep coupon as one plate; instead add a 4.3 mm gate hole and 3.2 mm retainer hole
    bits.append(box(56, 92, 56, 70, 0, 6) - cyl(4.3, 8, 66, 63, -1) - cyl(3.2, 8, 80, 63, -1))
    return union(bits)


def model_of(name):
    return CAT[name]['builder']()


def print_mesh(name):
    return apply(model_of(name), CAT[name]['P'])


def world_from_print(name, k):
    M_ = CAT[name]['inst'][k]['M']
    if M_ is None:
        return None
    return M_ @ np.linalg.inv(CAT[name]['P'])



def module_local_path(mod):
    if mod == 'S160': return T.straight(160, 20, n=21)
    if mod == 'S80': return T.straight(80, 10, n=11)
    if mod == 'CR': return T.arc(80, 'R', 20)
    if mod == 'CL': return T.arc(80, 'L', 20)
    if mod == 'IN': return T.straight(INLET_L, INLET_DROP, n=13)
    if mod == 'SP': return T.straight(160, 20, n=21)
    raise KeyError(mod)

def default_ball_path():
    """World-frame ball-centre polyline for the default route (continuous heading)."""
    pts = []
    segs = []
    for mod, a, b, h in ROUTE:
        ja = a if isinstance(a, str) else a[0]
        M = Tm(None, (XY[ja][0], XY[ja][1], ZV[ja])) @ Tm(Rz(h))
        local = module_local_path(mod)
        seg = []
        for p, t in local:
            w = (M @ np.array([p[0], p[1], p[2] + T.VH, 1.0]))[:3]
            seg.append(w.tolist())
        segs.append(dict(mod=mod, start=ja, end=b, heading=h, pts=seg))
        if pts and seg:
            # drop duplicate joint vertex
            pts += seg[1:]
        else:
            pts += seg
    return pts, segs

def ball_center_paths():
    """World-frame polylines of the ball centre for each named path."""
    paths = {}
    # lift rise + exit (from 2d log, y=0)
    import lift2d
    p, log, rel = lift2d.full_eval(lift2d.P)
    lift_pts = []
    for s in log:
        lift_pts.append((LIFT_POS[0] + s['x'], LIFT_POS[1], LIFT_POS[2] + s['z']))
    paths['lift'] = lift_pts

    def xform_path(local_pts, M):
        out = []
        for x, y, zv in local_pts:
            # ball centre is VH above V vertex
            p4 = M @ np.array([x, y, zv + T.VH, 1.0])
            out.append(tuple(p4[:3]))
        return out

    def module_M(modname, idx=0):
        return CAT[NAMES[modname]]['inst'][idx]['M']

    # tracks along the default (gate-on, path A) loop
    seq = []
    # S160 J0 idx 0
    seq += xform_path([p for p, _ in T.straight(160, 12, n=17)], module_M('S160', 0))
    seq += xform_path([p for p, _ in T.arc(80, 'R', 12)], module_M('CR', 0))
    seq += xform_path([p for p, _ in T.straight(160, 12, n=17)], module_M('S160', 1))
    A, B = T.sw_B_path.__doc__ and (T.straight(T.SW_L, T.SW_DA, n=49), T.sw_B_path())
    seq += xform_path([p for p, _ in A], module_M('SW', 0))
    seq += xform_path([p for p, _ in T.straight(160, 12, n=33)], module_M('SP', 0))
    zB0 = -(T.SW_DB_OUT - T.SW_DA)
    a = T.straight(T.MG_L, T.MG_DA, n=33)
    seq += xform_path([p for p, _ in a], module_M('MG', 0))
    seq += xform_path([p for p, _ in T.arc(80, 'R', 12)], module_M('CR', 1))
    seq += xform_path([p for p, _ in T.arc(80, 'R', 12)], module_M('CR', 2))
    seq += xform_path([p for p, _ in T.straight(160, 12, n=17)], module_M('S160', 2))
    seq += xform_path([p for p, _ in T.straight(INLET_L, INLET_DROP, n=9)], module_M('IN', 0))
    paths['loop_A'] = seq

    seqB = []
    seqB += xform_path([p for p, _ in T.straight(160, 12, n=17)], module_M('S160', 0))
    seqB += xform_path([p for p, _ in T.arc(80, 'R', 12)], module_M('CR', 0))
    seqB += xform_path([p for p, _ in T.straight(160, 12, n=17)], module_M('S160', 1))
    seqB += xform_path([p for p, _ in B], module_M('SW', 0))
    seqB += xform_path([p for p, _ in T.straight(160, 12, n=17)], module_M('S160', 1 if False else 0))  # placeholder
    # S160 from J5b is instance index: S160 instances: 0=J0, 1=J2, 2=J9, and J5b is another...
    # ROUTE S160s: J0-J1 (0), J2-J3 (1), J5b-J6b (2), J9-J11 (3)  -- wait I only have 3 in ROUTE?
    # ROUTE: S160 J0, S160 J2, S160 J5b, S160 J9  = 4 instances!
    paths['loop_B_partial'] = seqB  # completed in validate after counting instances
    paths['_B_raw'] = B
    return paths


if __name__ == '__main__':
    build_catalogue()
    print('ZV', {k: round(v, 2) for k, v in ZV.items()})
    print('inlet L', round(INLET_L, 2), 'drop', round(INLET_DROP, 2),
          'slope_deg', round(math.degrees(math.atan(INLET_DROP / INLET_L)), 2))
    print('ZV_J0', round(ZV_J0, 3), 'INLET_ZV_END', round(INLET_ZV_END, 3))
    for n, c in CAT.items():
        print(n, 'qty', len(c['inst']))
