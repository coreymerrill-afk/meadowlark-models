"""Play-first kit v4 (1:24, H3C): clear windows, lift-off roof, open-face rail, Lego outdoor modules.
Same snap system as v0: Ø5.9 pegs into Ø6.3 sockets on 31.75 grid, Ø3.2 light races. Z=0 bed."""
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
    """Short wall (107.125) with a large clear opening (no muntins): ~70×55 aperture, sill at 28 mm."""
    w = W0.wall('blank')
    # trim like short_wall_v0c: keep x in [E, 127]
    m = T.boolean.intersection([w, bx(CP.E, -50, -50, S, 50, 300)], engine='manifold')
    m.apply_translation([-CP.E, 0, 0])
    L = S - CP.E  # 107.125
    z0, zh, hw = 28.0, 55.0, 35.0
    cuts = [bx(L / 2 - hw, -6, z0, L / 2 + hw, 6, z0 + zh)]
    m = D_(m, cuts)
    sill = bx(L / 2 - hw - 2, -W0.TH / 2 - 2, z0 - 2.5, L / 2 + hw + 2, W0.TH / 2, z0)
    return lift(U([m, sill]))

def wall_wide_door():
    """Short wall (107.125) with wide doorway ≥28 mm clear (34 mm opening from plinth)."""
    w = W0.wall('blank')
    m = T.boolean.intersection([w, bx(CP.E, -50, -50, S, 50, 300)], engine='manifold')
    m.apply_translation([-CP.E, 0, 0])
    L = S - CP.E
    half = 17.0
    cuts = [bx(L / 2 - half, -6, W0.PL_H, L / 2 + half, 6, W0.PL_H + 78)]
    return lift(D_(m, cuts))

def roof_panel_lift(L=S * 2, depth=80, thick=3.5):
    """Lift-off roof panel (prints flat): shallow pitch board with underside Ø5.9 pegs
    that drop into wall-top / ridge sockets. Kid lifts whole panel to reach rooms."""
    # Print flat on bed: L × depth × thick, pegs point +Z then we flip? Keep pegs below Z=0 then lift.
    panel = bx(0, 0, 0, L, depth, thick)
    # shallow ridge rib for stiffness
    rib = bx(0, depth / 2 - 2, thick, L, depth / 2 + 2, thick + 4)
    # edge lip (finger grip)
    lip = bx(0, 0, thick, L, 4, thick + 3)
    # underside pegs at OFF, L/2, L-OFF along length; near front + back
    pegs = [peg(x, y) for x in (OFF, L / 2, L - OFF) for y in (10, depth - 10)]
    m = U([panel, rib, lip] + pegs)
    return lift(m)

def open_face_rail(L=S, h=18):
    """Low open-back furniture rail: kid sees whole room; furniture doesn't roll off.
    Pegs into a floor-tile edge socket row."""
    posts = []
    xs = [OFF + i * PITCH for i in range(4) if OFF + i * PITCH <= L]
    for x in xs:
        posts.append(cyl(4.5, h, x, 0, 0, sec=16))
        posts.append(peg(x, 0))
    rail = bx(4, -2.5, h - 3, L - 4, 2.5, h)
    # open — no solid wall panel
    return lift(U(posts + [rail]))

# ---------- outdoor Lego modules ----------
def lawn_tile():
    """Yard tile: same snap/light interfaces as floor_tile_v0, shallow grass grooves on deck."""
    t = floor_tile()
    # shallow parallel grooves on deck top (decorative only)
    grooves = []
    for y in np.arange(8, S - 6, 7):
        grooves.append(bx(6, y - 0.4, TILE_H - 0.6, S - 6, y + 0.4, TILE_H + 0.01))
    return D_(t, grooves)

def path_tile():
    """Paver path tile: same sockets; checker/paver recess pattern on deck."""
    t = floor_tile()
    cuts = []
    for i in range(4):
        for j in range(4):
            x0, y0 = 6 + i * 29, 6 + j * 29
            cuts.append(bx(x0, y0, TILE_H - 0.8, x0 + 26, y0 + 26, TILE_H + 0.01))
    return D_(t, cuts)

def garden_bed():
    """Raised garden bed ~100×50×18 with hollow soil well; 2 pegs on 31.75 pitch."""
    outer = bx(0, 0, 0, 100, 50, 18)
    well = bx(4, 4, 4, 96, 46, 19)
    m = D_(outer, [well])
    return lift(U([m, peg(OFF, 25), peg(OFF + PITCH, 25)]))

def fence_straight():
    """Fence segment spanning one tile edge (~127): open pickets, 2 pegs at edge sockets."""
    L, h = S, 42.0
    m = [bx(0, -2, 0, L, 2, 4), bx(0, -2, h - 4, L, 2, h)]  # rails
    for x in np.arange(8, L - 4, 10):
        m.append(bx(x - 1.2, -1.5, 4, x + 1.2, 1.5, h - 4))
    # open — large gaps between pickets (see-through)
    m += [peg(OFF, 0), peg(S - OFF, 0)]
    return lift(U(m))

def fence_corner():
    """90° corner fence, pegs on both legs."""
    arm = lambda: U([bx(0, -2, 0, 64, 2, 4), bx(0, -2, 38, 64, 2, 42)]
                    + [bx(x - 1.2, -1.5, 4, x + 1.2, 1.5, 38) for x in np.arange(8, 60, 10)])
    a = arm()
    b = arm()
    b.apply_transform(T.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    post = cyl(6, 42, 0, 0, 0, sec=16)
    m = U([a, b, post, peg(OFF, 0), peg(0, OFF)])
    return lift(m)

def garden_gate_play():
    """Clear play gate: two open frames + simple latch bar; stone-ish piers with pegs.
    Intentionally NOT ornate — kid sees through and can 'open' play space."""
    W, pier_w, h = 140.0, 18.0, 70.0
    parts = []
    for x in (0, W - pier_w):
        parts += [bx(x, 0, 0, x + pier_w, 18, h), bx(x - 1, -1, 0, x + pier_w + 1, 19, 6)]
        parts.append(peg(x + pier_w / 2, 9))
    # two open leaf frames (see-through rectangles)
    gw = (W - 2 * pier_w - 4) / 2
    for k in range(2):
        x0 = pier_w + 2 + k * (gw + 2)
        # frame only
        parts += [
            bx(x0, 6, 8, x0 + gw, 10, 12),
            bx(x0, 6, h - 14, x0 + gw, 10, h - 10),
            bx(x0, 6, 8, x0 + 3, 10, h - 10),
            bx(x0 + gw - 3, 6, 8, x0 + gw, 10, h - 10),
        ]
        # single mid bar (not dense)
        parts.append(bx(x0, 6, h / 2 - 1.5, x0 + gw, 10, h / 2 + 1.5))
    # latch stub
    parts.append(bx(W / 2 - 4, 4, h / 2 - 3, W / 2 + 4, 12, h / 2 + 3))
    return lift(U(parts))

def sandbox():
    """Sandbox / play pad: 100×100 tray, 12 mm walls, 4 corner pegs."""
    outer = bx(0, 0, 0, 100, 100, 14)
    well = bx(4, 4, 3, 96, 96, 15)
    m = D_(outer, [well])
    pegs = [peg(x, y) for x in (OFF, OFF + 2 * PITCH) for y in (OFF, OFF + 2 * PITCH)]
    return lift(U([m] + pegs))

def planter_stub():
    """Tree/planter stub: pot + short trunk; 1 centre peg."""
    pot = D_(cyl(28, 16, 0, 0, 0, sec=32), [cyl(22, 12, 0, 0, 5, sec=32)])
    trunk = cyl(8, 36, 0, 0, 16, sec=16)
    canopy_stub = cyl(18, 8, 0, 0, 48, sec=16)  # stub only — kid can add foliage or leave bare
    return lift(U([pot, trunk, canopy_stub, peg(0, 0)]))

def bench_play():
    """Garden bench with 2 pegs."""
    seat = bx(0, 0, 14, 50, 16, 17)
    back = bx(0, 12, 17, 50, 16, 32)
    legs = [bx(x, y, 0, x + 4, y + 4, 14) for x in (2, 44) for y in (2, 10)]
    return lift(U([seat, back] + legs + [peg(OFF, 8), peg(OFF + PITCH, 8)]))

def shed_shell():
    """Open-front shed / outdoor playhouse shell on one tile footprint.
    Walls on 3 sides, open +Y face, pitched roof, pegs into floor/lawn tile."""
    W, D, H = 120.0, 100.0, 90.0
    th = 4.0
    # floor plate
    floor = bx(0, 0, 0, W, D, 3)
    # three walls (N, E, W) — open south (+Y in our build: open at y=D)
    back = bx(0, 0, 3, W, th, H)           # -Y back
    left = bx(0, 0, 3, th, D, H)
    right = bx(W - th, 0, 3, W, D, H)
    # large clear window openings on back + sides (see-through)
    cuts = [
        bx(W / 2 - 28, -1, 28, W / 2 + 28, th + 1, 70),
        bx(-1, D / 2 - 22, 28, th + 1, D / 2 + 22, 65),
        bx(W - th - 1, D / 2 - 22, 28, W + 1, D / 2 + 22, 65),
    ]
    walls = D_(U([back, left, right]), cuts)
    # simple gable roof (two slabs)
    roof_l = bx(-4, -4, H - 2, W / 2 + 2, D + 4, H + 2)
    roof_r = bx(W / 2 - 2, -4, H - 2, W + 4, D + 4, H + 2)
    # ridge lift via wedges approximated as thicker centre
    ridge = bx(W / 2 - 4, -4, H, W / 2 + 4, D + 4, H + 18)
    pegs = [peg(x, y) for x in (OFF, W - OFF) for y in (OFF, D - OFF) if x < W and y < D]
    # ensure pegs land in range
    pegs = [peg(OFF, OFF), peg(OFF + 2 * PITCH, OFF), peg(OFF, OFF + 2 * PITCH), peg(OFF + 2 * PITCH, OFF + 2 * PITCH)]
    m = U([floor, walls, roof_l, roof_r, ridge] + pegs)
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

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    bad = []
    for n, f in PARTS.items():
        if len(sys.argv) > 1 and n not in sys.argv[1:]:
            continue
        try:
            m = f()
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
