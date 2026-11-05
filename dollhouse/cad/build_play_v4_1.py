"""Play kit v4.1 Physical — Structure critic TWEAKs on v4 play parts.
Same snap system as v0: Ø5.9 pegs into Ø6.3 sockets on 31.75 grid. Z=0 bed.

TWEAKs (Dollhouse · Structure pass 1):
  1. shed_shell_v4 — front lintel + two posts under roof leading edge (open-front kept)
  2. wall_panel_clear_window_v4 — taller sill, mid rail, jamb thickeners ≥12 mm
  3. garden_gate_play_v4 — deeper header + pier cap beam
KEEP parts regenerated unchanged from build_play_v4.
"""
import os, sys, numpy as np, trimesh as T
from build_v0 import bx, cyl, U, D_, OUT, LC, SOCK_D, OFF, PITCH, S, floor_tile, H as TILE_H, RIB_H, DECK
import build_wall_v0 as W0
import build_corner_post_v0 as CP

def peg(x, y, z=0):
    return cyl(5.9, 5.0, x, y, z - 5.0)

def lift(m):
    m = m.copy()
    m.apply_translation([0, 0, -m.bounds[0][2]])
    return m

def ok_bounds(m, name):
    e = m.extents
    fit = e[0] <= 330 and e[1] <= 320 and e[2] <= 325
    print(f"{name:34s} {e[0]:6.1f}x{e[1]:6.1f}x{e[2]:6.1f} wt={m.is_watertight} vol={m.volume:8.0f} {'OK' if fit and m.volume > 0 else 'CHECK'}", flush=True)
    return fit

# ---------- play structure ----------
def wall_clear_window():
    """Short wall with large clear opening. v4.1: taller sill, mid rail, jambs ≥12 mm thick."""
    w = W0.wall('blank')
    m = T.boolean.intersection([w, bx(CP.E, -50, -50, S, 50, 300)], engine='manifold')
    m.apply_translation([-CP.E, 0, 0])
    L = S - CP.E  # 107.125
    # taller sill: aperture starts at 36 (was 28); slightly shorter opening
    z0, zh, hw = 36.0, 48.0, 32.0  # ~64 wide × 48 tall; jambs ~(L-64)/2 ≈ 21.5
    cuts = [bx(L / 2 - hw, -6, z0, L / 2 + hw, 6, z0 + zh)]
    m = D_(m, cuts)
    # sill shelf (taller / deeper)
    sill = bx(L / 2 - hw - 2, -W0.TH / 2 - 3, z0 - 4, L / 2 + hw + 2, W0.TH / 2 + 1, z0)
    # mid rail across opening (keeps clear-glass intent, stops tall jamb flex)
    mid_z = z0 + zh / 2
    mid = bx(L / 2 - hw - 1, -W0.TH / 2 - 1, mid_z - 2.5, L / 2 + hw + 1, W0.TH / 2 + 1, mid_z + 2.5)
    # jamb thickeners: local wall depth ≥12 mm at left/right jambs
    jam_w = 12.0
    left = bx(L / 2 - hw - jam_w, -6, W0.PL_H, L / 2 - hw, 6, z0 + zh + 4)
    right = bx(L / 2 + hw, -6, W0.PL_H, L / 2 + hw + jam_w, 6, z0 + zh + 4)
    return lift(U([m, sill, mid, left, right]))

def wall_wide_door():
    """Short wall with wide doorway ≥28 mm clear (unchanged KEEP)."""
    w = W0.wall('blank')
    m = T.boolean.intersection([w, bx(CP.E, -50, -50, S, 50, 300)], engine='manifold')
    m.apply_translation([-CP.E, 0, 0])
    L = S - CP.E
    half = 17.0
    cuts = [bx(L / 2 - half, -6, W0.PL_H, L / 2 + half, 6, W0.PL_H + 78)]
    return lift(D_(m, cuts))

def roof_panel_lift(L=S * 2, depth=80, thick=3.5):
    panel = bx(0, 0, 0, L, depth, thick)
    rib = bx(0, depth / 2 - 2, thick, L, depth / 2 + 2, thick + 4)
    lip = bx(0, 0, thick, L, 4, thick + 3)
    pegs = [peg(x, y) for x in (OFF, L / 2, L - OFF) for y in (10, depth - 10)]
    return lift(U([panel, rib, lip] + pegs))

def open_face_rail(L=S, h=18):
    posts = []
    xs = [OFF + i * PITCH for i in range(4) if OFF + i * PITCH <= L]
    for x in xs:
        posts.append(cyl(4.5, h, x, 0, 0, sec=16))
        posts.append(peg(x, 0))
    rail = bx(4, -2.5, h - 3, L - 4, 2.5, h)
    return lift(U(posts + [rail]))

# ---------- outdoor Lego modules ----------
def lawn_tile():
    t = floor_tile()
    grooves = []
    for y in np.arange(8, S - 6, 7):
        grooves.append(bx(6, y - 0.4, TILE_H - 0.6, S - 6, y + 0.4, TILE_H + 0.01))
    return D_(t, grooves)

def path_tile():
    t = floor_tile()
    cuts = []
    for i in range(4):
        for j in range(4):
            x0, y0 = 6 + i * 29, 6 + j * 29
            cuts.append(bx(x0, y0, TILE_H - 0.8, x0 + 26, y0 + 26, TILE_H + 0.01))
    return D_(t, cuts)

def garden_bed():
    outer = bx(0, 0, 0, 100, 50, 18)
    well = bx(4, 4, 4, 96, 46, 19)
    m = D_(outer, [well])
    return lift(U([m, peg(OFF, 25), peg(OFF + PITCH, 25)]))

def fence_straight():
    L, h = S, 42.0
    m = [bx(0, -2, 0, L, 2, 4), bx(0, -2, h - 4, L, 2, h)]
    for x in np.arange(8, L - 4, 10):
        m.append(bx(x - 1.2, -1.5, 4, x + 1.2, 1.5, h - 4))
    m += [peg(OFF, 0), peg(S - OFF, 0)]
    return lift(U(m))

def fence_corner():
    arm = lambda: U([bx(0, -2, 0, 64, 2, 4), bx(0, -2, 38, 64, 2, 42)]
                    + [bx(x - 1.2, -1.5, 4, x + 1.2, 1.5, 38) for x in np.arange(8, 60, 10)])
    a = arm()
    b = arm()
    b.apply_transform(T.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    post = cyl(6, 42, 0, 0, 0, sec=16)
    m = U([a, b, post, peg(OFF, 0), peg(0, OFF)])
    return lift(m)

def garden_gate_play():
    """Clear play gate. v4.1: deeper header + pier cap beam so open frames don't twist."""
    W, pier_w, h = 140.0, 18.0, 75.0  # slightly taller for deeper header stack
    parts = []
    for x in (0, W - pier_w):
        parts += [bx(x, 0, 0, x + pier_w, 18, h), bx(x - 1, -1, 0, x + pier_w + 1, 19, 6)]
        parts.append(peg(x + pier_w / 2, 9))
        # pier cap plate
        parts.append(bx(x - 2, -2, h, x + pier_w + 2, 20, h + 6))
    # continuous pier-cap beam across full width (ties piers, deep header)
    parts.append(bx(-2, 2, h - 2, W + 2, 16, h + 8))
    gw = (W - 2 * pier_w - 4) / 2
    for k in range(2):
        x0 = pier_w + 2 + k * (gw + 2)
        # deeper leaf frames: thicker members + deeper header bar (~12 mm tall, 8 mm deep)
        parts += [
            bx(x0, 5, 8, x0 + gw, 13, 14),                 # bottom rail
            bx(x0, 5, h - 18, x0 + gw, 13, h - 4),         # deep header (14 mm tall)
            bx(x0, 5, 8, x0 + 4, 13, h - 4),               # stile L (4 mm)
            bx(x0 + gw - 4, 5, 8, x0 + gw, 13, h - 4),     # stile R
            bx(x0, 5, h / 2 - 2, x0 + gw, 13, h / 2 + 2), # mid bar
        ]
    parts.append(bx(W / 2 - 4, 3, h / 2 - 3, W / 2 + 4, 14, h / 2 + 3))
    return lift(U(parts))

def sandbox():
    outer = bx(0, 0, 0, 100, 100, 14)
    well = bx(4, 4, 3, 96, 96, 15)
    m = D_(outer, [well])
    pegs = [peg(x, y) for x in (OFF, OFF + 2 * PITCH) for y in (OFF, OFF + 2 * PITCH)]
    return lift(U([m] + pegs))

def planter_stub():
    pot = D_(cyl(28, 16, 0, 0, 0, sec=32), [cyl(22, 12, 0, 0, 5, sec=32)])
    trunk = cyl(8, 36, 0, 0, 16, sec=16)
    canopy_stub = cyl(18, 8, 0, 0, 48, sec=16)
    return lift(U([pot, trunk, canopy_stub, peg(0, 0)]))

def bench_play():
    seat = bx(0, 0, 14, 50, 16, 17)
    back = bx(0, 12, 17, 50, 16, 32)
    legs = [bx(x, y, 0, x + 4, y + 4, 14) for x in (2, 44) for y in (2, 10)]
    return lift(U([seat, back] + legs + [peg(OFF, 8), peg(OFF + PITCH, 8)]))

def shed_shell():
    """Open-front shed. v4.1: two front posts + continuous lintel under roof leading edge."""
    W, D, H = 120.0, 100.0, 90.0
    th = 4.0
    floor = bx(0, 0, 0, W, D, 3)
    back = bx(0, 0, 3, W, th, H)
    left = bx(0, 0, 3, th, D, H)
    right = bx(W - th, 0, 3, W, D, H)
    cuts = [
        bx(W / 2 - 28, -1, 28, W / 2 + 28, th + 1, 70),
        bx(-1, D / 2 - 22, 28, th + 1, D / 2 + 22, 65),
        bx(W - th - 1, D / 2 - 22, 28, W + 1, D / 2 + 22, 65),
    ]
    walls = D_(U([back, left, right]), cuts)
    # front posts under roof edge (open face at +Y = D)
    post_w = 8.0
    front_posts = [
        bx(th, D - post_w, 3, th + post_w, D, H),
        bx(W - th - post_w, D - post_w, 3, W - th, D, H),
    ]
    # continuous front lintel / header under roof leading edge
    lintel = bx(th, D - post_w - 2, H - 10, W - th, D + 2, H + 2)
    roof_l = bx(-4, -4, H - 2, W / 2 + 2, D + 4, H + 2)
    roof_r = bx(W / 2 - 2, -4, H - 2, W + 4, D + 4, H + 2)
    ridge = bx(W / 2 - 4, -4, H, W / 2 + 4, D + 4, H + 18)
    pegs = [peg(OFF, OFF), peg(OFF + 2 * PITCH, OFF), peg(OFF, OFF + 2 * PITCH), peg(OFF + 2 * PITCH, OFF + 2 * PITCH)]
    m = U([floor, walls] + front_posts + [lintel, roof_l, roof_r, ridge] + pegs)
    return lift(m)

PARTS = {
    'wall_panel_clear_window_v4': wall_clear_window,
    'wall_panel_wide_door_v4': wall_wide_door,
    'roof_panel_lift_v4': roof_panel_lift,
    'open_face_rail_v4': open_face_rail,
    'lawn_tile_v4': lawn_tile,
    'path_tile_v4': path_tile,
    'garden_bed_v4': garden_bed,
    'fence_straight_v4': fence_straight,
    'fence_corner_v4': fence_corner,
    'garden_gate_play_v4': garden_gate_play,
    'sandbox_v4': sandbox,
    'planter_stub_v4': planter_stub,
    'bench_play_v4': bench_play,
    'shed_shell_v4': shed_shell,
}

# Parts that changed in v4.1 (regenerate these by default)
TWEAKED = ('shed_shell_v4', 'wall_panel_clear_window_v4', 'garden_gate_play_v4')

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    bad = []
    only = sys.argv[1:] or list(TWEAKED)
    for n in only:
        if n not in PARTS:
            print('unknown', n); bad.append(n); continue
        try:
            m = PARTS[n]()
            m = lift(m)
            ok = ok_bounds(m, n) and m.is_watertight
            m.export(os.path.join(OUT, n + '.stl'))
            if not ok:
                bad.append(n)
        except Exception as ex:
            import traceback
            print(n, 'ERR', repr(ex)[:400], flush=True)
            traceback.print_exc()
            bad.append(n)
    print('bad:', bad)
