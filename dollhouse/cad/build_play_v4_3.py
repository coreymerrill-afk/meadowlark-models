"""Play kit v4.3 Grand accents — Whimsy musts as REQUIRED printable parts.
All mates: Ø5.9 peg → Ø6.3 socket, pitch 31.75, spans ≤127 mm.
  Vertical: tower_stub / chimney_ridge / finial_ridge / clock_shaft
  Façade:   porch_post / porch_beam / porch_roof_slice
  Roof break: gable_end / dormer_play / mansard_break / cupola_play
Also: regenerate garden_gate_play_v4 with degenerate tris cleaned.
"""
import os, sys, numpy as np, trimesh as T
from trimesh.creation import cone, icosphere
import build_play_v4_1 as P
from build_v0 import bx, cyl, U, D_, OUT, SOCK_D, OFF, PITCH, S, LC
SD = 5.5
PEG_D, PEG_H = 5.9, 5.0

def peg(x, y, z=0):
    return cyl(PEG_D, PEG_H, x, y, z - PEG_H)

def lift(m):
    m = m.copy(); m.apply_translation([0, 0, -m.bounds[0][2]]); return m

def clean(m):
    m = m.copy(); m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices(); return m

def sock(x, y, z_top, depth=SD):
    return cyl(SOCK_D, depth + 0.01, x, y, z_top - depth)

def ok(m, name):
    e = m.extents
    fit = e[0] <= 330 and e[1] <= 320 and e[2] <= 325 and m.volume > 0
    print(f"{name:34s} {e[0]:6.1f}x{e[1]:6.1f}x{e[2]:6.1f} wt={m.is_watertight} vol={m.volume:8.0f} degen={int((m.area_faces<1e-9).sum())} {'OK' if fit else 'CHECK'}", flush=True)
    return fit

# ---------- vertical accents ----------
def tower_stub():
    """Short octagonal tower stub. Bottom peg → corner_post / floor socket; top Ø6.3 for finial/stack.
    Footprint ≤127. Mate: single center peg (use at corner post top via dowel, or floor OFF,OFF)."""
    R, h = 22.0, 70.0
    body = cyl(R * 2, h, 0, 0, 0, sec=8)
    belt = cyl(R * 2 + 4, 4, 0, 0, h * 0.55, sec=8)
    cap = cyl(R * 2 + 2, 5, 0, 0, h, sec=8)
    # arched window recesses (don't punch through — keep clear-play, shallow)
    cuts = []
    for a in (0, np.pi / 2, np.pi, 3 * np.pi / 2):
        x, y = np.cos(a) * (R - 2), np.sin(a) * (R - 2)
        cuts.append(bx(x - 6, y - 6, 18, x + 6, y + 6, 42))
    m = D_(U([body, belt, cap, peg(0, 0)]), cuts) if False else U([body, belt, cap, peg(0, 0)])
    # shallow niches as additive frames instead of through-cuts (stronger)
    frames = []
    for a in (0, np.pi / 2, np.pi, 3 * np.pi / 2):
        fx, fy = np.cos(a) * (R + 1.5), np.sin(a) * (R + 1.5)
        frames.append(bx(fx - 5, fy - 1.5, 20, fx + 5, fy + 1.5, 40) if abs(np.cos(a)) > 0.5
                      else bx(fx - 1.5, fy - 5, 20, fx + 1.5, fy + 5, 40))
    m = U([m] + frames)
    m = D_(m, [sock(0, 0, h + 5)])
    return lift(clean(m))

def chimney_ridge():
    """Brick chimney for roof_panel_lift ridge Ø6.3 sockets. Single peg — seats any ridge sock.
    Mate note: peg → roof_panel_lift_v4 ridge socket (xs at OFF+n*PITCH)."""
    w, d, h = 28.0, 22.0, 64.0
    body = bx(-w / 2, -d / 2, 0, w / 2, d / 2, h)
    cap = bx(-w / 2 - 2, -d / 2 - 2, h, w / 2 + 2, d / 2 + 2, h + 5)
    pot = cyl(10, 10, 0, 0, h + 5, sec=16)
    bands = [bx(-w / 2 - 0.4, -d / 2 - 0.4, z, w / 2 + 0.4, d / 2 + 0.4, z + 1.2) for z in (12, 28, 44)]
    # flue bore (shallow, open top)
    flue = cyl(7, 20, 0, 0, h - 5)
    m = D_(U([body, cap, pot, peg(0, 0)] + bands), [flue])
    return lift(clean(m))

def finial_ridge():
    """Ball-and-spire finial. Peg → any ridge Ø6.3 or tower_stub / corner-post top socket."""
    m = [cyl(10, 4, 0, 0, 0), cyl(7, 6, 0, 0, 4),
         T.primitives.Sphere(radius=6).apply_translation([0, 0, 16]) if False else None]
    ball = icosphere(subdivisions=2, radius=6); ball.apply_translation([0, 0, 16])
    tip = cone(radius=3.2, height=18); tip.apply_translation([0, 0, 22])
    collar = cyl(9, 3, 0, 0, 22)
    m = U([cyl(10, 4, 0, 0, 0), cyl(7, 6, 0, 0, 4), ball, collar, tip, peg(0, 0)])
    # LED tip bore optional
    m = D_(m, [cyl(LC, 25, 0, 0, 30)])
    return lift(clean(m))

def clock_shaft():
    """Square clocktower shaft for Cogsworth. Bottom peg → corner_post top / floor; top sock for finial.
    Face ≤127. Mate: center peg."""
    s, h = 48.0, 110.0
    body = bx(-s / 2, -s / 2, 0, s / 2, s / 2, h)
    belt = bx(-s / 2 - 2, -s / 2 - 2, h * 0.62, s / 2 + 2, s / 2 + 2, h * 0.62 + 5)
    cap = bx(-s / 2 - 1, -s / 2 - 1, h, s / 2 + 1, s / 2 + 1, h + 6)
    # clock face discs (additive relief, four sides)
    faces = []
    for a, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        faces.append(cyl(22, 2.5, dx * (s / 2 + 1), dy * (s / 2 + 1), h * 0.72, ax=('x' if dx else 'y'), sec=24))
        # hub
        faces.append(cyl(4, 3.5, dx * (s / 2 + 2), dy * (s / 2 + 2), h * 0.72, ax=('x' if dx else 'y'), sec=12))
    m = U([body, belt, cap, peg(0, 0)] + faces)
    m = D_(m, [sock(0, 0, h + 6)])
    return lift(clean(m))

# ---------- porch / street façade ----------
def porch_post():
    """Porch column. Peg → floor_tile / lawn / path Ø6.3 socket (same as outdoor).
    Top has Ø6.3 sock for porch_beam / porch_roof_slice peg. Height ~88 mm (wall plate)."""
    h = 88.0
    col = cyl(10, h, 0, 0, 0, sec=20)
    base = cyl(16, 5, 0, 0, 0, sec=20)
    capital = cyl(14, 5, 0, 0, h, sec=20)
    m = U([col, base, capital, peg(0, 0)])
    m = D_(m, [sock(0, 0, h + 5)])
    return lift(clean(m))

def porch_beam():
    """Beam spanning 4×pitch = 127 mm (two porch posts on adjacent tile sockets).
    Underside pegs at 0 and 127 match porch_post top socks / tile pitch.
    Mate: pegs → porch_post top sockets."""
    L, w, t = 127.0, 14.0, 10.0
    beam = bx(0, -w / 2, PEG_H, L, w / 2, PEG_H + t)
    # decorative underside notch
    crown = bx(-2, -w / 2 - 1, PEG_H + t, L + 2, w / 2 + 1, PEG_H + t + 4)
    pegs = [peg(0, 0), peg(L, 0)]
    return lift(clean(U([beam, crown] + pegs)))

def porch_roof_slice():
    """Shed porch roof slice, 127 deep span × 70. Underside pegs at beam posts (0 & 127).
    Lip at rear seats visually on wall; does not cover windows (depth 70 toward street).
    Mate: pegs → porch_post top or porch_beam (if beam has socks — posts preferred)."""
    L, depth, thick = 127.0, 70.0, 3.5
    # sloped slab via extrusion of box then we just use flat shed with riser at back
    panel = bx(0, 0, 8, L, depth, 8 + thick)  # flat shed, rear elevated feel via lip
    riser = bx(0, depth - 6, 0, L, depth, 8 + thick)  # back wall seat
    lip = bx(-2, -2, 8 + thick, L + 2, 4, 8 + thick + 3)
    pegs = [peg(0, 12), peg(L, 12)]
    return lift(clean(U([panel, riser, lip] + pegs)))

# ---------- roofs-on silhouette breaks ----------
def gable_end():
    """Triangular gable-end panel, width 127. Bottom pegs into two floor/tile socks at OFF spacing
    along the open gable line — OR seat on wall-top lip as a freestanding end (pegs into post tops).
    Does not cover windows. Mate: pegs at x=0 and x=127 → porch_post / corner / floor sockets."""
    W, rise, thick = 127.0, 58.0, 4.0
    # triangle prism via convex hull of points
    pts = np.array([
        [0, 0, 0], [W, 0, 0], [W, thick, 0], [0, thick, 0],
        [W / 2, 0, rise], [W / 2, thick, rise]
    ], dtype=float)
    tri = T.Trimesh(vertices=pts, faces=[
        [0, 1, 4], [1, 2, 4], [2, 5, 4], [0, 4, 5], [0, 5, 3], [2, 3, 5],
        [0, 3, 1], [1, 3, 2]
    ]).convex_hull
    # bargeboards
    left = bx(-2, -1, 0, 4, thick + 1, 4)
    right = bx(W - 4, -1, 0, W + 2, thick + 1, 4)
    # ridge sock for finial
    m = U([tri, left, right, peg(0, thick / 2), peg(W, thick / 2)])
    # add a small top platform with sock at apex for finial_ridge
    plat = bx(W / 2 - 8, -1, rise - 2, W / 2 + 8, thick + 1, rise + 4)
    m = U([m, plat])
    m = D_(m, [sock(W / 2, thick / 2, rise + 4)])
    return lift(clean(m))

def dormer_play():
    """Play dormer — seats on roof_panel_lift ridge via 1 peg. Clear window opening (no glass required).
    Mate: peg → ridge Ø6.3. Lift-compatible (comes off with roof)."""
    w, d, h = 40.0, 36.0, 38.0
    body = bx(-w / 2, 0, PEG_H, w / 2, d, PEG_H + h)
    # clear window aperture
    cut = bx(-12, d - 6, PEG_H + 10, 12, d + 1, PEG_H + 30)
    # mini gable roof
    roof_pts = np.array([
        [-w / 2 - 3, -1, PEG_H + h], [w / 2 + 3, -1, PEG_H + h],
        [w / 2 + 3, d + 4, PEG_H + h], [-w / 2 - 3, d + 4, PEG_H + h],
        [0, -1, PEG_H + h + 22], [0, d + 4, PEG_H + h + 22]
    ], dtype=float)
    roof = T.Trimesh(vertices=roof_pts, faces=[[0,1,4],[1,2,5],[1,5,4],[0,4,5],[0,5,3],[2,3,5],[0,3,1],[1,3,2]]).convex_hull
    sill = bx(-14, d - 4, PEG_H + 8, 14, d + 2, PEG_H + 10)
    m = D_(U([body, roof, sill, peg(0, d / 2)]), [cut])
    return lift(clean(m))

def mansard_break():
    """Mansard silhouette panel — 127 wide × 70 tall, fish-scale bands. Top/bottom pegs for ridge /
    wall-cap mates. Mate: bottom pegs → ridge socks at 0 and 127 (4×pitch); top socks for finial."""
    L, h, thick = 127.0, 70.0, 4.0
    panel = bx(0, 0, PEG_H, L, thick, PEG_H + h)
    tiles = []
    for r, y in enumerate(np.arange(PEG_H + 6, PEG_H + h - 8, 8)):
        off = 0 if r % 2 else 5
        for x in np.arange(6 + off, L - 4, 10):
            tiles.append(cyl(8.5, 1.2, x, thick - 0.2, y, ax='y', sec=12))
    band = [bx(0, 0, PEG_H + h - 5, L, thick + 1, PEG_H + h),
            bx(0, 0, PEG_H, L, thick + 1, PEG_H + 5)]
    pegs = [peg(0, thick / 2), peg(L, thick / 2)]
    m = U([panel] + tiles + band + pegs)
    # top socks for finial / cresting
    m = D_(m, [sock(L / 2, thick / 2, PEG_H + h)])
    return lift(clean(m))

def cupola_play():
    """Octagon cupola for widow's walk / ranch. v4.3.1: pegs at ±2·PITCH (span 127) on a
    base sill → roof_panel_lift_v4 ridge socks at x=15.875 & 142.875 (centre over 79.375).
    Top sock for finial. Lift-compatible. Mate: pegs → roof_panel_lift ridge."""
    R, h = 20.0, 42.0
    body = cyl(R * 2, h, 0, 0, PEG_H, sec=8)
    roof = cyl(R * 2 + 6, 4, 0, 0, PEG_H + h, sec=8)
    spire = cyl(8, 18, 0, 0, PEG_H + h + 4, sec=8)
    ball = cyl(12, 8, 0, 0, PEG_H + h + 20, sec=16)
    tip = cyl(4, 12, 0, 0, PEG_H + h + 28, sec=12)
    collar = cyl(R * 2 + 3, 3, 0, 0, PEG_H + h - 1, sec=8)
    frames = []
    for k in range(8):
        a = k * np.pi / 4 + np.pi / 8
        fx, fy = np.cos(a) * (R + 1), np.sin(a) * (R + 1)
        frames.append(bx(fx - 3, fy - 1.2, PEG_H + 10, fx + 3, fy + 1.2, PEG_H + 28)
                      if abs(np.cos(a)) > abs(np.sin(a))
                      else bx(fx - 1.2, fy - 3, PEG_H + 10, fx + 1.2, fy + 3, PEG_H + 28))
    pegs = [peg(-2 * PITCH, 0), peg(2 * PITCH, 0)]
    sill = bx(-2 * PITCH - 7, -7, 0, 2 * PITCH + 7, 7, PEG_H + 2)
    m = U([sill, body, roof, spire, ball, tip, collar] + frames + pegs)
    m = D_(m, [sock(0, 0, PEG_H + h + 40)])
    return lift(clean(m))

# ---------- gate cleanup (Print Fit should) ----------
def garden_gate_play():
    """v4.2 gate geometry (peg span 127) with degenerate faces scrubbed."""
    W, pw, h = 145.0, 18.0, 75.0
    parts = []
    for x in (0, W - pw):
        parts += [bx(x, 0, 0, x + pw, 18, h), bx(x - 1, -1, 0, x + pw + 1, 19, 6),
                  peg(x + pw / 2, 9), bx(x - 2, -2, h, x + pw + 2, 20, h + 6)]
    parts.append(bx(-2, 2, h - 2, W + 2, 16, h + 8))
    gw = (W - 2 * pw - 4) / 2
    for k in range(2):
        x0 = pw + 2 + k * (gw + 2)
        parts += [bx(x0, 5, 8, x0 + gw, 13, 14), bx(x0, 5, h - 18, x0 + gw, 13, h - 4),
                  bx(x0, 5, 8, x0 + 4, 13, h - 4), bx(x0 + gw - 4, 5, 8, x0 + gw, 13, h - 4),
                  bx(x0, 5, h / 2 - 2, x0 + gw, 13, h / 2 + 2)]
    parts.append(bx(W / 2 - 4, 3, h / 2 - 3, W / 2 + 4, 14, h / 2 + 3))
    return clean(lift(U(parts)))

PARTS = {
    'tower_stub_v43': tower_stub,
    'chimney_ridge_v43': chimney_ridge,
    'finial_ridge_v43': finial_ridge,
    'clock_shaft_v43': clock_shaft,
    'porch_post_v43': porch_post,
    'porch_beam_v43': porch_beam,
    'porch_roof_slice_v43': porch_roof_slice,
    'gable_end_v43': gable_end,
    'dormer_play_v43': dormer_play,
    'mansard_break_v43': mansard_break,
    'cupola_play_v43': cupola_play,
    'garden_gate_play_v4': garden_gate_play,
}

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    bad = []
    for n, f in PARTS.items():
        if len(sys.argv) > 1 and n not in sys.argv[1:]:
            continue
        try:
            m = f()
            if not ok(m, n):
                bad.append(n)
            m.export(os.path.join(OUT, n + '.stl'))
        except Exception as ex:
            import traceback; traceback.print_exc()
            print(n, 'ERR', repr(ex)[:300], flush=True); bad.append(n)
    print('bad:', bad)
