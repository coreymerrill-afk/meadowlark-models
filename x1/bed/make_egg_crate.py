#!/usr/bin/env python3
"""
Egg-crate (interlocking slotted blade) steel bed generator for the ACMER X1 Ultra.

Outputs (next to this script):
  egg_crate_bed.dxf            one BLADE + one CROSS-RIB (parts, layers CUT / LABELS, mm)
  nest_one_panel_4x8.dxf       all parts of ONE panel nested on a 1220 x 2440 mm sheet
  nest_full_bed_60x120.dxf     all parts of the whole bed on 1524 x 3048 mm (60x120 in) sheet(s)
  nest_full_bed_4x8.dxf        whole bed on 1220 x 2440 sheets (sheet 1, 2 ... stacked in one file)
  egg_crate_assembly.png       1600 px wide picture of the assembled grid
  egg_crate_drawing.pdf        2-page drawing
Usage:  python make_egg_crate.py [--material 1/8in|11ga]
Edit the PARAMETERS block below after measuring the machine.
"""
import math, sys, os, argparse
import numpy as np
import ezdxf
from ezdxf import units
import shapely.geometry as sg
from shapely.strtree import STRtree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MPoly, Rectangle
import mapbox_earcut

# ============================ PARAMETERS (mm) ============================
MATERIAL        = "1/8in"      # "1/8in" (3.18 mm plate) or "11ga" (3.04 mm sheet)
THICKNESS_MM    = {"1/8in": 3.18, "11ga": 3.04}
SLOT_CLEARANCE  = 0.2          # slot width = thickness + this (rounded UP to 0.05 mm)
SLOT_WIDTH_OVERRIDE = None     # set a number to force slot width (e.g. 3.5 if vendor wants looser)
SLOT_DEPTH_EXTRA = 0.0         # exact half-height laps; width clearance is separate from kerf

PANEL_L         = 1200.0       # panel length  (direction the long blades run)
PANEL_W         = 1200.0       # panel width   (across the blades; length of cross-ribs)
N_PANELS        = 2            # panels end to end along the machine's long axis (2 x 1200 = 2400)

BLADE_H         = 38.0         # blade height INCLUDING tooth tips (1.5 in)
BLADE_PITCH     = 50.0         # blade centre-to-centre (2 in)
RIB_PITCH_MAX   = 200.0        # max spacing between cross-ribs along the blades (150-250 sensible)
RIB_END_INSET   = 50.0         # first/last rib centre distance from blade end
SERRATED        = True         # serrated (triangle teeth) blade tops; ribs are always straight
NOTCH_W         = 120.0        # airflow vent cut in the bottom edge of each blade, centred between ribs
NOTCH_H         = 20.0         # vent height (blade bottom edge)
TOOTH_PITCH     = 12.0
TOOTH_H         = 4.0
# cross-rib height; None = valley height of the blade teeth (BLADE_H - TOOTH_H) so only tips touch work
RIB_H           = None

# nesting
SHEET_4X8       = (1220.0, 2440.0)      # width, length
SHEET_60X120    = (1524.0, 3048.0)
NEST_MARGIN     = 8.0
NEST_GAP        = 4.0
STEEL_DENSITY   = 7.85e-6               # kg / mm^3

# machine reference (for drawings only)
WORK_AREA       = (2450.0, 1250.0)      # ACMER X1 Ultra work area (X long, Y short)
EST_OPENING     = (2530.0, 1470.0)      # ESTIMATE - not published, measure it
OUT_DIR         = os.path.dirname(os.path.abspath(__file__))
# =========================================================================


def ceil_to(x, step):
    return math.ceil(round(x / step, 6)) * step


class Cfg:
    pass


def build_cfg(material=None):
    c = Cfg()
    c.material = material or MATERIAL
    c.t = THICKNESS_MM[c.material]
    c.slot = SLOT_WIDTH_OVERRIDE or round(ceil_to(c.t + SLOT_CLEARANCE, 0.05), 3)
    c.L, c.W, c.n_panels = PANEL_L, PANEL_W, N_PANELS
    c.H = BLADE_H
    c.serrated = SERRATED
    c.tooth_p, c.tooth_h = TOOTH_PITCH, (TOOTH_H if SERRATED else 0.0)
    c.Hv = c.H - c.tooth_h                       # blade height at tooth valleys
    c.RH = RIB_H if RIB_H else c.Hv              # rib height
    c.pitch = BLADE_PITCH
    c.n_blades = int(math.floor(c.W / c.pitch + 1e-9))
    first = (c.W - (c.n_blades - 1) * c.pitch) / 2.0
    c.blade_y = [first + i * c.pitch for i in range(c.n_blades)]       # blade centre lines across panel width
    span = c.L - 2 * RIB_END_INSET
    c.n_ribs = int(math.ceil(span / RIB_PITCH_MAX - 1e-9)) + 1
    c.rib_pitch = span / (c.n_ribs - 1)
    c.rib_x = [RIB_END_INSET + j * c.rib_pitch for j in range(c.n_ribs)]  # rib centre lines along panel length
    # half-slots: both cut to half the RIB height (+ extra); blade slot from bottom, rib slot from top
    c.dr = c.RH / 2.0 + SLOT_DEPTH_EXTRA        # rib slot depth (from top)
    c.db = c.RH / 2.0 + SLOT_DEPTH_EXTRA        # blade slot depth (from bottom)
    assert c.db + 8 <= c.Hv, "blade slots too deep for blade height"
    assert c.pitch - c.slot > 10 and c.rib_pitch - c.slot > 10
    c.sheet = SHEET_4X8
    return c


# ----------------------------- part geometry ------------------------------
def blade_poly(c):
    s = c.slot
    pts = [(0.0, NOTCH_H), (25.0, NOTCH_H), (25.0, 0.0)]
    for i, x in enumerate(c.rib_x):
        pts += [(x - s / 2, 0.0), (x - s / 2, c.db), (x + s / 2, c.db), (x + s / 2, 0.0)]
        if i + 1 < len(c.rib_x):  # vent between this rib and the next
            mid = (x + c.rib_x[i + 1]) / 2.0
            x0 = mid - NOTCH_W / 2; x1 = mid + NOTCH_W / 2
            pts += [(x0, 0.0), (x0, NOTCH_H), (x1, NOTCH_H), (x1, 0.0)]
    pts += [(c.L - 25.0, 0.0), (c.L - 25.0, NOTCH_H), (c.L, NOTCH_H)]
    if c.serrated:
        n = int(round(c.L / c.tooth_p)); p = c.L / n
        pts.append((c.L, c.Hv))
        for k in range(n, 0, -1):
            pts += [((k - 0.5) * p, c.H), ((k - 1) * p, c.Hv)]
    else:
        pts += [(c.L, c.H), (0.0, c.H)]
    return pts


def rib_poly(c):
    s = c.slot
    pts = [(0.0, 0.0)]
    # Rectangular vents between blades; never intersect the upper half-lap slots.
    for a, b in zip(c.blade_y, c.blade_y[1:]):
        mid = (a + b) / 2
        pts += [(mid - 15, 0), (mid - 15, 12), (mid + 15, 12), (mid + 15, 0)]
    pts += [(c.W, 0.0), (c.W, c.RH)]
    for y in reversed(c.blade_y):
        pts += [(y + s / 2, c.RH), (y + s / 2, c.RH - c.dr), (y - s / 2, c.RH - c.dr), (y - s / 2, c.RH)]
    pts.append((0.0, c.RH))
    return pts


def dedupe(pts):
    out = []
    for p in pts:
        if not out or (abs(p[0] - out[-1][0]) > 1e-9 or abs(p[1] - out[-1][1]) > 1e-9):
            out.append(p)
    if abs(out[0][0] - out[-1][0]) < 1e-9 and abs(out[0][1] - out[-1][1]) < 1e-9:
        out.pop()
    return out


def part_list(c, panels=1):
    """list of (name, polygon points) for `panels` panels."""
    parts = []
    for p in range(panels):
        for i in range(c.n_blades):
            parts.append((f"BLADE P{p+1}-{i+1:02d}", "BLADE", dedupe(blade_poly(c))))
        for j in range(c.n_ribs):
            parts.append((f"RIB P{p+1}-{j+1}", "RIB", dedupe(rib_poly(c))))
    return parts


def area(pts):
    return sg.Polygon(pts).area


# ------------------------------- verification ------------------------------
def verify(c, log):
    t, s = c.t, c.slot
    B = sg.Polygon(dedupe(blade_poly(c))); R = sg.Polygon(dedupe(rib_poly(c)))
    assert B.is_valid and R.is_valid
    # (a) slot positions read back from the actual polygons
    bp = dedupe(blade_poly(c)); rp = dedupe(rib_poly(c))
    bslots = sorted({round((x1 + x2) / 2, 3) for (x1, y1), (x2, y2) in zip(bp, bp[1:] + bp[:1])
                     if abs(y1 - c.db) < 1e-9 and abs(y2 - c.db) < 1e-9 and abs(abs(x2 - x1) - s) < 1e-6})
    rslots = sorted({round((x1 + x2) / 2, 3) for (x1, y1), (x2, y2) in zip(rp, rp[1:] + rp[:1])
                     if abs(y1 - (c.RH - c.dr)) < 1e-9 and abs(y2 - (c.RH - c.dr)) < 1e-9 and abs(abs(x2 - x1) - s) < 1e-6})
    assert bslots == sorted(round(x, 3) for x in c.rib_x), "blade slot positions != rib positions"
    assert rslots == sorted(round(y, 3) for y in c.blade_y), "rib slot positions != blade positions"
    # (b) every crossing (blade i x rib j): rib centre-line x_j lies in blade slot, blade centre y_i in rib slot,
    #     and the solid steel of the two parts does not overlap in Z
    n_cross = 0; min_gap = 1e9
    for yi in c.blade_y:
        for xj in c.rib_x:
            strip_b = B.intersection(sg.box(xj - t / 2, -1, xj + t / 2, c.H + 1))   # blade material in rib thickness
            strip_r = R.intersection(sg.box(yi - t / 2, -1, yi + t / 2, c.RH + 1))  # rib material in blade thickness
            blade_min_z = strip_b.bounds[1]; rib_max_z = strip_r.bounds[3]
            assert blade_min_z >= rib_max_z - 1e-9, f"overlap at blade {yi} rib {xj}"
            min_gap = min(min_gap, blade_min_z - rib_max_z)
            n_cross += 1
    # blade/rib not crossing: blades are in disjoint y bands and ribs in disjoint x bands
    assert c.pitch > t and c.rib_pitch > t
    # tops: rib top is at or below blade valleys
    assert c.RH <= c.Hv + 1e-9
    log.append(f"verify: {c.n_blades} blades x {c.n_ribs} ribs = {n_cross} crossings per panel; "
               f"blade slot centres == rib positions, rib slot centres == blade positions; "
               f"vertical clearance at every crossing = {min_gap:.2f} mm (>=0, no overlap)")
    return n_cross


# --------------------------------- nesting ----------------------------------
def nest(parts, sheet, margin=NEST_MARGIN, gap=NEST_GAP):
    """shelf nest, parts laid along sheet length (long dimension), 2+ columns. returns list of sheets
    each = list of (name, kind, pts_translated)."""
    sw, sl = sheet
    items = []
    for name, kind, pts in parts:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        items.append((name, kind, pts, max(xs) - min(xs), max(ys) - min(ys)))
    # group: blades first then ribs (each full-length, same width)
    items.sort(key=lambda it: (it[1] != "BLADE", it[0]))
    w = items[0][3]
    ncol = int((sl - 2 * margin + gap) // (w + gap))
    sheets = []; cur = []; y = margin; i = 0
    while i < len(items):
        row = items[i:i + ncol]
        if row[0][1] != row[-1][1]:        # keep blades/ribs in separate rows
            row = [r for r in row if r[1] == row[0][1]]
        h = max(r[4] for r in row)
        if y + h > sw - margin + 1e-9:
            sheets.append(cur); cur = []; y = margin
        for k, r in enumerate(row):
            dx = margin + k * (w + gap); dy = y
            cur.append((r[0], r[1], [(px + dx, py + dy) for px, py in r[2]]))
        y += h + gap
        i += len(row)
    if cur:
        sheets.append(cur)
    return sheets, ncol


def check_nest(sheets, sheet, margin=NEST_MARGIN, gap=NEST_GAP):
    sw, sl = sheet
    for si, sh in enumerate(sheets):
        polys = [sg.Polygon(p) for _, _, p in sh]
        for pg in polys:
            b = pg.bounds
            assert b[0] >= margin - 1e-6 and b[1] >= margin - 1e-6 and b[2] <= sl - margin + 1e-6 and b[3] <= sw - margin + 1e-6, "part outside sheet margin"
        tree = STRtree(polys)
        for a, pg in enumerate(polys):
            for bidx in tree.query(pg.buffer(gap)):
                if bidx > a:
                    d = pg.distance(polys[bidx])
                    assert d >= gap - 1e-6, f"parts too close on sheet {si+1}: {sh[a][0]} / {sh[bidx][0]} dist {d:.2f}"
    return True


# ----------------------------------- DXF -----------------------------------
def new_doc():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = units.MM
    doc.header["$MEASUREMENT"] = 1
    doc.layers.add("CUT", color=1)
    doc.layers.add("LABELS", color=3)
    return doc


def add_poly(msp, pts, layer="CUT", dx=0.0, dy=0.0):
    msp.add_lwpolyline([(x + dx, y + dy) for x, y in pts], close=True, dxfattribs={"layer": layer})


def label(msp, text, x, y, h=6.0):
    msp.add_text(text, height=h, dxfattribs={"layer": "LABELS", "insert": (x, y)})


def write_parts_dxf(c, path):
    doc = new_doc(); msp = doc.modelspace()
    B = dedupe(blade_poly(c)); R = dedupe(rib_poly(c))
    nb = c.n_blades * c.n_panels; nr = c.n_ribs * c.n_panels
    label(msp, "ACMER X1 ULTRA EGG-CRATE BED - units mm - CUT layer = cut, LABELS layer = notes (do not cut)", 0, 160, 8)
    label(msp, f"Material: mild steel {c.material} ({c.t} mm). Slot width {c.slot} mm (kerf to be compensated by vendor). "
               f"Dimensions to be confirmed after measuring machine inside opening.", 0, 145, 6)
    # BLADE
    label(msp, f"PART A  BLADE  qty {nb} ({c.n_blades}/panel x {c.n_panels} panels)  {c.L:g} x {c.H:g} x {c.t} mm  "
               f"slots {c.slot} x {c.db:.2f} deep cut from BOTTOM (flat edge); serrated top" if c.serrated else
          f"PART A  BLADE  qty {nb}  {c.L:g} x {c.H:g} x {c.t} mm  slots {c.slot} x {c.db:.2f} from BOTTOM", 0, 100, 6)
    label(msp, "Slot centres from left end (mm): " + ", ".join(f"{x:.2f}" for x in c.rib_x), 0, 88, 5)
    add_poly(msp, B, dx=0, dy=40)
    # RIB
    label(msp, f"PART B  CROSS-RIB  qty {nr} ({c.n_ribs}/panel x {c.n_panels} panels)  {c.W:g} x {c.RH:g} x {c.t} mm  "
               f"slots {c.slot} x {c.dr:.2f} deep cut from TOP, straight edges", 0, 20, 6)
    label(msp, "Slot centres from left end (mm): " + ", ".join(f"{y:.2f}" for y in c.blade_y), 0, 8, 5)
    add_poly(msp, R, dx=0, dy=-40)
    label(msp, "Assembly: lay ribs flat-side-down on bench, drop blades in from above (rib slots open up, blade slots open down). No bolts or welds.", 0, -70, 5)
    doc.saveas(path)


def write_nest_dxf(c, sheets, sheet, path, title):
    doc = new_doc(); doc.layers.add("SHEET", color=8)
    msp = doc.modelspace(); sw, sl = sheet
    y0 = 0.0
    for si, sh in enumerate(sheets):
        oy = si * (sw + 150)
        msp.add_lwpolyline([(0, oy), (sl, oy), (sl, oy + sw), (0, oy + sw)], close=True, dxfattribs={"layer": "SHEET"})
        label(msp, f"{title} - sheet {si+1}/{len(sheets)} - {sl:g} x {sw:g} mm - material {c.material} - SHEET layer is reference only", 0, oy + sw + 12, 8)
        for name, kind, pts in sh:
            add_poly(msp, pts, dy=oy)
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            label(msp, name, min(xs) + 20, oy + min(ys) + c.db + 3.0, 5.0)
    doc.saveas(path)


def dxf_report(path, layers=("CUT", "LABELS")):
    d = ezdxf.readfile(path)
    msp = d.modelspace()
    cnt = {}
    for e in msp:
        cnt[(e.dxf.layer, e.dxftype())] = cnt.get((e.dxf.layer, e.dxftype()), 0) + 1
    return d.units, cnt


# ------------------------------- 3D rendering --------------------------------
def tri_prism(poly2d, to3d, thick):
    """extruded mesh from 2D polygon (shapely polygon). to3d(x, y, q) -> world, q=0 / thick."""
    tris = []; groups = []
    gid = 0
    def add_poly_prism(pg):
        nonlocal gid
        ext = list(pg.exterior.coords)[:-1]
        rings = [len(ext)]; verts = list(ext)
        for r in pg.interiors:
            v = list(r.coords)[:-1]; verts += v; rings.append(len(verts))
        idx = mapbox_earcut.triangulate_float64(np.array(verts, dtype=np.float64), np.array(rings, dtype=np.uint32))
        for q in (0.0, thick):
            for a, b, cc in idx.reshape(-1, 3):
                tris.append([to3d(*verts[a], q), to3d(*verts[b], q), to3d(*verts[cc], q)]); groups.append(gid)
            gid += 1
        for ring in [ext] + [list(r.coords)[:-1] for r in pg.interiors]:
            n = len(ring)
            for k in range(n):
                p0, p1 = ring[k], ring[(k + 1) % n]
                a = to3d(*p0, 0); b = to3d(*p1, 0); cc = to3d(*p1, thick); d = to3d(*p0, thick)
                tris.append([a, b, cc]); groups.append(gid)
                tris.append([a, cc, d]); groups.append(gid)
                gid += 1
    geoms = [poly2d] if poly2d.geom_type == "Polygon" else [g for g in poly2d.geoms if g.geom_type == "Polygon"]
    for g in geoms:
        add_poly_prism(g)
    return np.array(tris, dtype=float), np.array(groups)


class Camera:
    def __init__(self, az_deg=-32, el_deg=32):
        self.az = math.radians(az_deg); self.el = math.radians(el_deg)
    def project(self, P):
        P = np.asarray(P, float)
        x1 = P[..., 0] * math.cos(self.az) - P[..., 1] * math.sin(self.az)
        y1 = P[..., 0] * math.sin(self.az) + P[..., 1] * math.cos(self.az)
        z1 = P[..., 2]
        u = x1
        v = z1 * math.cos(self.el) + y1 * math.sin(self.el)
        w = -y1 * math.cos(self.el) + z1 * math.sin(self.el)
        return u, v, w
    def to_cam(self):
        # world-space unit vector pointing at the camera
        ca, sa, ce, se = math.cos(self.az), math.sin(self.az), math.cos(self.el), math.sin(self.el)
        # y1 = X sa + Y ca ; camera dir in rotated frame (0,-ce,se) -> world
        v = np.array([0, -ce, se])
        return np.array([ v[0]*ca + v[1]*sa, -v[0]*sa + v[1]*ca, v[2] ])


def render_scene(meshes, cam, size, ss=3, margin=0.06):
    """meshes: list of (tris Nx3x3, groups, base_rgb). returns RGB float image (h,w,3) and projector fn."""
    Wp, Hp = size[0] * ss, size[1] * ss
    allv = np.concatenate([m[0].reshape(-1, 3) for m in meshes])
    u, v, _ = cam.project(allv)
    sc = min(Wp * (1 - 2 * margin) / (u.max() - u.min()), Hp * (1 - 2 * margin) / (v.max() - v.min()))
    ox = (Wp - sc * (u.max() + u.min())) / 2; oy = (Hp + sc * (v.max() + v.min())) / 2
    def proj(P):
        uu, vv, ww = cam.project(P)
        return ox + sc * uu, oy - sc * vv, ww
    zbuf = np.full((Hp, Wp), -1e18); img = np.ones((Hp, Wp, 3)); ids = np.full((Hp, Wp), -1, dtype=np.int64)
    light = np.array([-0.45, -0.55, 0.75]); light /= np.linalg.norm(light)
    tocam = cam.to_cam()
    gbase = 0
    for tris, groups, rgb in meshes:
        px, py, pw = proj(tris)
        for t in range(len(tris)):
            tri = tris[t]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0]); nn = np.linalg.norm(n)
            if nn < 1e-12:
                continue
            n /= nn
            if n @ tocam < 0: n = -n
            shade = 0.50 + 0.50 * max(0.0, n @ light) ** 0.9
            col = np.array(rgb) * shade
            xs, ys, ws = px[t], py[t], pw[t]
            x0 = max(int(math.floor(xs.min())), 0); x1 = min(int(math.ceil(xs.max())), Wp - 1)
            y0 = max(int(math.floor(ys.min())), 0); y1 = min(int(math.ceil(ys.max())), Hp - 1)
            if x1 < x0 or y1 < y0: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(d) < 1e-9: continue
            l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
            l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
            l2 = 1 - l0 - l1
            m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            wv = l0 * ws[0] + l1 * ws[1] + l2 * ws[2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            upd = m & (wv > sub)
            sub[upd] = wv[upd]
            img[y0:y1 + 1, x0:x1 + 1][upd] = col
            ids[y0:y1 + 1, x0:x1 + 1][upd] = gbase + groups[t]
        gbase += groups.max() + 1
    # outlines where face group changes
    edge = np.zeros_like(ids, bool)
    edge[:, 1:] |= ids[:, 1:] != ids[:, :-1]; edge[1:, :] |= ids[1:, :] != ids[:-1, :]
    from numpy.lib.stride_tricks import sliding_window_view
    img[edge] = img[edge] * 0.35
    img = img.reshape(size[1], ss, size[0], ss, 3).mean(axis=(1, 3))
    def proj_out(P):
        a, b, _ = proj(P)
        return a / ss, b / ss
    return np.clip(img, 0, 1), proj_out


def build_section_meshes(c, xmax=470.0, ymax=262.0):
    t = c.t
    B = sg.Polygon(dedupe(blade_poly(c))).intersection(sg.box(0, -1, xmax, c.H + 1))
    R = sg.Polygon(dedupe(rib_poly(c))).intersection(sg.box(0, -1, ymax, c.RH + 1))
    bm = []; rm = []
    for yc in c.blade_y:
        if yc + t / 2 > ymax: continue
        tr, gr = tri_prism(B, lambda x, y, q, yc=yc: (x, yc - t / 2 + q, y), t); bm.append((tr, gr))
    for xc in c.rib_x:
        if xc + t / 2 > xmax: continue
        tr, gr = tri_prism(R, lambda x, y, q, xc=xc: (xc - t / 2 + q, x, y), t); rm.append((tr, gr))
    meshes = []
    for tr, gr in bm: meshes.append((tr, gr, (0.52, 0.60, 0.70)))
    for tr, gr in rm: meshes.append((tr, gr, (0.86, 0.56, 0.26)))
    return meshes


# ------------------------------- drawing helpers -------------------------------
def dim_line(ax, p1, p2, text, off=0.0, horizontal=True, fs=8, color="k", ext=True):
    (x1, y1), (x2, y2) = p1, p2
    if horizontal:
        yy = y1 + off
        if ext and off != 0:
            ax.plot([x1, x1], [y1, yy + np.sign(off) * 1], color=color, lw=0.5)
            ax.plot([x2, x2], [y2, yy + np.sign(off) * 1], color=color, lw=0.5)
        ax.annotate("", xy=(x1, yy), xytext=(x2, yy), arrowprops=dict(arrowstyle="<->", lw=0.8, color=color, shrinkA=0, shrinkB=0))
        ax.text((x1 + x2) / 2, yy, text, ha="center", va="bottom", fontsize=fs, color=color,
                bbox=dict(fc="white", ec="none", pad=0.6))
    else:
        xx = x1 + off
        if ext and off != 0:
            ax.plot([x1, xx + np.sign(off) * 1], [y1, y1], color=color, lw=0.5)
            ax.plot([x2, xx + np.sign(off) * 1], [y2, y2], color=color, lw=0.5)
        ax.annotate("", xy=(xx, y1), xytext=(xx, y2), arrowprops=dict(arrowstyle="<->", lw=0.8, color=color, shrinkA=0, shrinkB=0))
        ax.text(xx, (y1 + y2) / 2, text, ha="right" if off < 0 else "left", va="center", fontsize=fs, color=color, rotation=0,
                bbox=dict(fc="white", ec="none", pad=0.6))


def draw_poly(ax, pts, fc="#c9d3df", ec="k", lw=0.8, dx=0, dy=0, **kw):
    ax.add_patch(MPoly([(x + dx, y + dy) for x, y in pts], closed=True, fc=fc, ec=ec, lw=lw, **kw))


STEEL = "#b9c6d6"; RIBC = "#f0c08e"


def sheet_text(ax, lines, x=0.0, y=1.0, fs=9, dy=0.075, bold_first=True):
    for i, ln in enumerate(lines):
        ax.text(x, y - i * dy, ln, transform=ax.transAxes, fontsize=fs, va="top",
                fontweight="bold" if (i == 0 and bold_first) else "normal", wrap=False)


def stats(c):
    Ab = area(dedupe(blade_poly(c))); Ar = area(dedupe(rib_poly(c)))
    wb = Ab * c.t * STEEL_DENSITY; wr = Ar * c.t * STEEL_DENSITY
    per_panel = c.n_blades * wb + c.n_ribs * wr
    return dict(Ab=Ab, Ar=Ar, wb=wb, wr=wr, per_panel=per_panel, total=per_panel * c.n_panels,
                sheet_wt=SHEET_4X8[0] * SHEET_4X8[1] * c.t * STEEL_DENSITY,
                cut_len_blade=sg.Polygon(dedupe(blade_poly(c))).length, cut_len_rib=sg.Polygon(dedupe(rib_poly(c))).length)


# ------------------------------------ PNG ------------------------------------
def make_png(c, path, st):
    cam = Camera(-26, 40)
    meshes = build_section_meshes(c, xmax=470.0, ymax=212.0)
    IW, IH = 1000, 640
    img, proj = render_scene(meshes, cam, (IW, IH), ss=3)
    fig = plt.figure(figsize=(16, 12), dpi=100, facecolor="white")
    fig.text(0.5, 0.975, "Egg-crate steel bed for the X1 Ultra - how the grid goes together", ha="center", va="top", fontsize=17, fontweight="bold")
    fig.text(0.5, 0.955, f"Mild steel {c.material} ({c.t} mm), laser cut, interlocking slots - no bolts, no welding.  Dimensions to be confirmed after measuring the machine's inside opening.",
             ha="center", va="top", fontsize=10.5, color="#444")
    # --- iso
    ax = fig.add_axes([0.02, 0.43, 0.62, 0.47]); ax.imshow(img, extent=[0, IW, IH, 0]); ax.set_xlim(0, IW); ax.set_ylim(IH, 0); ax.axis("off")
    ax.set_title("Cut-away corner of one panel (real geometry: 4 blades x 3 ribs)", fontsize=11, loc="left")
    def pt(x, y, z): a, b = proj([[x, y, z]]); return float(a[0]), float(b[0])
    t = c.t
    def callout(tx, ty, px, py, text, color="k"):
        ax.annotate(text, xy=(px, py), xytext=(tx, ty), fontsize=10.5, color=color, ha="center",
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1), bbox=dict(fc="white", ec=color, lw=0.8, pad=3))
    yb = c.blade_y[2]
    callout(130, 72, *pt(150, yb, c.H), "BLADE - long, on edge\nserrated top, only tips touch work", "#1f4e79")
    callout(800, 70, *pt(c.rib_x[1], 230, c.RH), "CROSS-RIB - keeps blades straight\nand evenly spaced", "#a1581a")
    callout(850, 590, *pt(c.rib_x[2], c.blade_y[3], c.db * 0.9), "Interlocking slot: blade is notched\nfrom below, rib from above, each\nhalf-way through. They just drop together.", "#333")
    callout(85, 500, *pt(0, c.blade_y[0] - t / 2, 0), "Flat bottom edge sits on the\nmachine's bed", "#333")
    # --- side view & slot detail
    ax2 = fig.add_axes([0.67, 0.50, 0.31, 0.40]); ax2.set_aspect("equal"); ax2.axis("off")
    ax2.set_title("Side view of one blade (zoom)", fontsize=11, loc="left")
    x0 = c.rib_x[1] - 42; x1 = c.rib_x[1] + 42
    P = sg.Polygon(dedupe(blade_poly(c))).intersection(sg.box(x0, -1, x1, c.H + 1))
    for g in ([P] if P.geom_type == "Polygon" else P.geoms):
        draw_poly(ax2, list(g.exterior.coords), fc=STEEL)
    xc = c.rib_x[1]
    # rib shown in section (hatched) as it passes through slot
    ax2.add_patch(Rectangle((xc - c.t / 2, 0), c.t, c.RH - c.dr, fc=RIBC, ec="#a1581a", lw=0.8))
    dim_line(ax2, (x0 - 4, 0), (x0 - 4, c.H), f"{c.H:g} mm\nblade height", off=-3, horizontal=False, fs=9)
    dim_line(ax2, (x1 + 2, c.Hv), (x1 + 2, c.H), f"{c.tooth_h:g} mm\ntooth", off=10, horizontal=False, fs=8.5)
    dim_line(ax2, (xc + c.slot / 2, 0), (xc + c.slot / 2, c.db), f"slot depth\n{c.db:.1f} mm", off=14, horizontal=False, fs=8.5)
    dim_line(ax2, (xc - c.slot / 2, c.db + 1), (xc + c.slot / 2, c.db + 1), "", off=0)
    ax2.text(xc, c.db + 7, f"slot width {c.slot} mm", ha="center", fontsize=8.5, bbox=dict(fc="white", ec="none", pad=0.5))
    dim_line(ax2, (x0, c.Hv), (x0 + c.tooth_p, c.Hv), "", off=0)
    ax2.text(x0 + c.tooth_p / 2, c.H + 8, f"tooth pitch {c.tooth_p:g} mm", ha="center", fontsize=8.5)
    ax2.text(xc, -12, "rib passes through here (orange = rib steel)", ha="center", fontsize=8.5, color="#a1581a")
    ax2.set_xlim(x0 - 28, x1 + 30); ax2.set_ylim(-18, c.H + 16)
    ax3 = fig.add_axes([0.67, 0.43, 0.31, 0.05]); ax3.axis("off")
    ax3.text(0, 0.5, f"Blade: {c.t} mm thick.  Slot = thickness + {SLOT_CLEARANCE} mm clearance.", fontsize=9.5, va="center")
    # --- plan view
    ax4 = fig.add_axes([0.04, 0.05, 0.64, 0.34]); ax4.set_aspect("equal"); ax4.axis("off")
    ax4.set_title(f"Top view - whole bed: {c.n_panels} panels, {c.L*c.n_panels:g} x {c.W:g} mm (dashed = ACMER work area {WORK_AREA[0]:g} x {WORK_AREA[1]:g}, centred)", fontsize=10.5, loc="left")
    wa = Rectangle(((c.L * c.n_panels - WORK_AREA[0]) / 2, (c.W - WORK_AREA[1]) / 2), WORK_AREA[0], WORK_AREA[1], fill=False, ec="#c0392b", ls="--", lw=1.1)
    ax4.add_patch(wa)
    for p in range(c.n_panels):
        ox = p * c.L
        ax4.add_patch(Rectangle((ox, 0), c.L, c.W, fc="#eef2f7", ec="k", lw=1.0))
        for y in c.blade_y: ax4.plot([ox, ox + c.L], [y, y], color="#4a6a8a", lw=0.9)
        for x in c.rib_x: ax4.plot([ox + x, ox + x], [0, c.W], color="#d9822b", lw=2.0)
        ax4.text(ox + c.L / 2, c.W / 2, f"PANEL {p+1}", ha="center", va="center", fontsize=13, fontweight="bold", color="#33445a",
                 bbox=dict(fc="white", ec="none", alpha=0.85, pad=2))
    dim_line(ax4, (0, c.W), (c.L, c.W), f"{c.L:g} mm (blade length)", off=40, fs=9)
    dim_line(ax4, (0, 0), (0, c.W), f"{c.W:g} mm\n(rib length)", off=-40, horizontal=False, fs=9)
    dim_line(ax4, (c.rib_x[0], 0), (c.rib_x[1], 0), f"rib spacing {c.rib_pitch:.1f}", off=-45, fs=8.5)
    dim_line(ax4, (c.L*c.n_panels, c.blade_y[0]), (c.L*c.n_panels, c.blade_y[1]), f"blade pitch {c.pitch:g}", off=40, horizontal=False, fs=8.5)
    ax4.set_xlim(-190, c.L * c.n_panels + 420); ax4.set_ylim(-190, c.W + 120)
    # --- legend / quantities
    ax5 = fig.add_axes([0.70, 0.04, 0.29, 0.36]); ax5.axis("off")
    nb = c.n_blades * c.n_panels; nr = c.n_ribs * c.n_panels
    lines = ["Parts for the whole bed",
             f"Blades:     {nb} pcs  ({c.n_blades} per panel)  {c.L:g} x {c.H:g} mm",
             f"Cross-ribs: {nr} pcs  ({c.n_ribs} per panel)  {c.W:g} x {c.RH:g} mm",
             f"Steel: {c.material}, {c.t} mm thick",
             f"Weight: {st['per_panel']:.1f} kg per panel, {st['total']:.1f} kg for the bed",
             f"Height: {c.H:g} mm ({c.H/25.4:.2f} in) - work rests on the",
             "  blade tips only; everything below is open air",
             "",
             "Colour key (top view):",
             "  blue line = blade     orange bar = cross-rib",
             "",
             "Sizes are estimates until the machine's",
             "inside opening is measured (not published;",
             f"estimated about {EST_OPENING[0]:g} x {EST_OPENING[1]:g} mm)."]
    sheet_text(ax5, lines, fs=10, dy=0.075)
    fig.savefig(path, dpi=100, facecolor="white")
    plt.close(fig)
    return img


# ------------------------------------ PDF ------------------------------------
def make_pdf(c, path, st, png_path, nest_info, log):
    with PdfPages(path) as pdf:
        # ---------------- page 1 : assembly ----------------
        fig = plt.figure(figsize=(17, 11), facecolor="white")
        fig.text(0.03, 0.96, "EGG-CRATE STEEL BED - ACMER X1 Ultra - assembly (page 1 of 2)", fontsize=16, fontweight="bold", va="top")
        fig.text(0.03, 0.93, f"Units: mm.  Material: mild steel {c.material} ({c.t} mm).  Laser cut, interlocking half-depth slots.  Dimensions to be confirmed after measuring machine inside opening.",
                 fontsize=10, va="top", color="#444")
        im = plt.imread(png_path)
        axi = fig.add_axes([0.02, 0.49, 0.50, 0.40]); axi.imshow(im[int(0.11 * im.shape[0]):int(0.575 * im.shape[0]), int(0.02 * im.shape[1]):int(0.645 * im.shape[1])]); axi.axis("off")
        # plan
        ax = fig.add_axes([0.03, 0.06, 0.60, 0.40]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("TOP VIEW - whole bed (2 panels, end to end)", fontsize=11, loc="left", fontweight="bold")
        for p in range(c.n_panels):
            ox = p * c.L
            ax.add_patch(Rectangle((ox, 0), c.L, c.W, fc="#eef2f7", ec="k", lw=1.0))
            for y in c.blade_y: ax.plot([ox, ox + c.L], [y, y], color="#4a6a8a", lw=0.7)
            for x in c.rib_x: ax.plot([ox + x, ox + x], [0, c.W], color="#d9822b", lw=1.8)
        dim_line(ax, (0, c.W), (c.L, c.W), f"{c.L:g}", off=45, fs=9)
        dim_line(ax, (c.L, c.W), (2 * c.L, c.W), f"{c.L:g}", off=45, fs=9)
        dim_line(ax, (0, c.W), (2 * c.L, c.W), f"{2*c.L:g} overall", off=120, fs=9)
        dim_line(ax, (0, 0), (0, c.W), f"{c.W:g}", off=-50, horizontal=False, fs=9)
        for j in range(c.n_ribs - 1):
            dim_line(ax, (c.rib_x[j], 0), (c.rib_x[j + 1], 0), f"{c.rib_pitch:.1f}", off=-60, fs=7.5)
        dim_line(ax, (0, 0), (c.rib_x[0], 0), f"{RIB_END_INSET:g}", off=-130, fs=7.5)
        dim_line(ax, (c.L, c.blade_y[0]), (c.L, c.blade_y[1]), f"{c.pitch:g}", off=40, horizontal=False, fs=7.5)
        ax.text(c.L * 0.5, c.W * 0.5, "24 blades @ 50 pitch" if c.n_blades == 24 else f"{c.n_blades} blades @ {c.pitch:g} pitch", ha="center", fontsize=10, bbox=dict(fc="white", ec="none", alpha=.85))
        ax.text(c.L * 1.5, c.W * 0.5, f"{c.n_ribs} cross-ribs per panel", ha="center", fontsize=10, bbox=dict(fc="white", ec="none", alpha=.85))
        ax.text(c.L, -230, "Panel 1 / Panel 2 butt together at the seam (blades line up end to end).  Ribs run across the blades.", ha="center", fontsize=8.5)
        ax.set_xlim(-130, 2 * c.L + 80); ax.set_ylim(-260, c.W + 190)
        # end elevation + crossing detail
        ax = fig.add_axes([0.54, 0.52, 0.44, 0.40]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("SIDE VIEW (looking along the blades) - 5 blades shown", fontsize=11, loc="left", fontweight="bold")
        ax.add_patch(Rectangle((-12, -3), 5 * c.pitch + 6, 3, fc="#555", ec="none"))
        ax.text(2.5 * c.pitch - 6, -9, "machine bed / base plate", ha="center", fontsize=8.5)
        for i in range(5):
            xc0 = i * c.pitch + c.pitch / 2 - 12
            tp = []
            n = 4
            # triangle teeth profile seen end-on is just a rectangle at tip height - show tips as a thin lighter strip
            ax.add_patch(Rectangle((xc0 - c.t / 2, 0), c.t, c.Hv, fc=STEEL, ec="k", lw=0.7))
            ax.add_patch(Rectangle((xc0 - c.t / 2, c.Hv), c.t, c.tooth_h, fc="#e6edf5", ec="k", lw=0.5, ls=":"))
        xs = [i * c.pitch + c.pitch / 2 - 12 for i in range(5)]
        ax.add_patch(Rectangle((xs[0] - 15, 0), xs[-1] - xs[0] + 30, c.RH - c.dr, fc=RIBC, ec="#a1581a", lw=0.6, alpha=0.8, zorder=0))
        dim_line(ax, (xs[0], c.H), (xs[1], c.H), f"pitch {c.pitch:g}", off=9, fs=9)
        dim_line(ax, (xs[0] - c.t / 2 - 2, 0), (xs[0] - c.t / 2 - 2, c.H), f"{c.H:g}\nblade", off=-6, horizontal=False, fs=9)
        dim_line(ax, (xs[4] + 8, 0), (xs[4] + 8, c.RH), f"{c.RH:g}\nrib", off=18, horizontal=False, fs=9)
        ax.text(xs[2], c.H + 24, f"blade thickness {c.t} mm;  dotted = tooth tips ({c.tooth_h:g} mm above rib)", ha="center", fontsize=8.5)
        ax.text(xs[2], -24, "orange = cross-rib behind the blades (it sits in the blade slots)", ha="center", fontsize=8.5, color="#a1581a")
        ax.set_xlim(xs[0] - 40, xs[4] + 50); ax.set_ylim(-30, c.H + 36)
        # table
        ax = fig.add_axes([0.54, 0.06, 0.44, 0.42]); ax.axis("off")
        nb = c.n_blades * c.n_panels; nr = c.n_ribs * c.n_panels
        lines = ["QUANTITIES & NOTES",
                 f"A  BLADE        qty {nb}  ({c.n_blades}/panel)   {c.L:g} x {c.H:g} x {c.t}   {st['wb']:.2f} kg each",
                 f"B  CROSS-RIB   qty {nr}  ({c.n_ribs}/panel)   {c.W:g} x {c.RH:g} x {c.t}   {st['wr']:.2f} kg each",
                 f"Total steel: {st['total']:.0f} kg ({st['total']*2.2046:.0f} lb); {st['per_panel']:.0f} kg per panel.",
                 f"Sheet: one {SHEET_4X8[0]:g} x {SHEET_4X8[1]:g} mm (4x8 ft) sheet of {c.material} weighs {st['sheet_wt']:.0f} kg.",
                 f"Nesting: {nest_info}",
                 "",
                 "ASSEMBLY: ribs flat on the bench with slots up; drop blades in with slots down. No bolts or welds. "
                 f"Lifts out as two panels of about {st['per_panel']:.0f} kg each (two-person lift).",
                 "",
                 "USE: diode laser (cuts drop through the grid); 4 W IR (blade tips are the only contact, flat and level); "
                 "CNC uses a separate lift-out spoilboard.",
                 "",
                 "TO CONFIRM: panel size 1200 x 1200 was chosen to fit a 4x8 sheet and the work area. "
                 f"The machine's inside opening is not published (estimated {EST_OPENING[0]:g} x {EST_OPENING[1]:g} mm) and ACMER's "
                 "'44 mm' cover-to-surface figure is unexplained. Measure before ordering."]
        import textwrap
        wl = []
        for ln in lines:
            wl += textwrap.wrap(ln, 82, subsequent_indent="   ") or [""]
        sheet_text(ax, wl, fs=9.2, dy=0.055)
        pdf.savefig(fig); plt.close(fig)

        # ---------------- page 2 : part drawings ----------------
        fig = plt.figure(figsize=(17, 11), facecolor="white")
        fig.text(0.03, 0.97, "EGG-CRATE STEEL BED - part drawings (page 2 of 2)", fontsize=16, fontweight="bold", va="top")
        fig.text(0.03, 0.94, "Units mm. CUT geometry = finished part outline (vendor to apply kerf compensation). Not to scale where labelled 'detail'.", fontsize=10, va="top", color="#444")
        B = dedupe(blade_poly(c)); R = dedupe(rib_poly(c))
        # blade full
        ax = fig.add_axes([0.03, 0.75, 0.94, 0.17]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"PART A - BLADE  (qty {c.n_blades*c.n_panels}) - {c.L:g} x {c.H:g} x {c.t}  - slots cut from the FLAT BOTTOM edge, teeth on top", fontsize=10.5, loc="left", fontweight="bold")
        draw_poly(ax, B, fc=STEEL, lw=0.5)
        dim_line(ax, (0, c.H), (c.L, c.H), f"{c.L:g}", off=20, fs=9)
        for j in range(c.n_ribs - 1):
            dim_line(ax, (c.rib_x[j], 0), (c.rib_x[j + 1], 0), f"{c.rib_pitch:.1f}", off=-14, fs=7.5)
        dim_line(ax, (0, 0), (c.rib_x[0], 0), f"{RIB_END_INSET:g}", off=-14, fs=7.5)
        dim_line(ax, (c.rib_x[-1], 0), (c.L, 0), f"{RIB_END_INSET:g}", off=-14, fs=7.5)
        ax.text(c.L / 2, -34, f"{c.n_ribs} slots per blade, centres at " + ", ".join(f"{x:.1f}" for x in c.rib_x), ha="center", fontsize=8)
        ax.set_xlim(-60, c.L + 40); ax.set_ylim(-45, c.H + 30)
        # rib full
        ax = fig.add_axes([0.03, 0.57, 0.94, 0.17]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"PART B - CROSS-RIB  (qty {c.n_ribs*c.n_panels}) - {c.W:g} x {c.RH:g} x {c.t}  - slots cut from the TOP edge, straight edges", fontsize=10.5, loc="left", fontweight="bold")
        draw_poly(ax, R, fc=RIBC, lw=0.5)
        dim_line(ax, (0, c.RH), (c.W, c.RH), f"{c.W:g}", off=20, fs=9)
        for i in range(0, 6):
            dim_line(ax, (c.blade_y[i], 0), (c.blade_y[i + 1], 0), f"{c.pitch:g}", off=-12, fs=7)
        dim_line(ax, (0, 0), (c.blade_y[0], 0), f"{c.blade_y[0]:g}", off=-26, fs=7)
        ax.text(c.W / 2, -42, f"{c.n_blades} slots per rib, {c.pitch:g} pitch, first centre {c.blade_y[0]:g} from each end", ha="center", fontsize=8)
        ax.set_xlim(-60, c.W + 40); ax.set_ylim(-52, c.RH + 30)
        # details
        def clip(pts, xa, xb, ya=-1, yb=100):
            return sg.Polygon(pts).intersection(sg.box(xa, ya, xb, yb))
        # blade slot detail
        ax = fig.add_axes([0.03, 0.10, 0.30, 0.42]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("DETAIL 1 - blade slot (from bottom)", fontsize=10.5, loc="left", fontweight="bold")
        xc = c.rib_x[1]; g = clip(B, xc - 22, xc + 22)
        for gg in ([g] if g.geom_type == "Polygon" else g.geoms): draw_poly(ax, list(gg.exterior.coords), fc=STEEL)
        dim_line(ax, (xc - c.slot / 2, c.db), (xc + c.slot / 2, c.db), f"{c.slot} wide", off=5, fs=9)
        dim_line(ax, (xc + c.slot / 2, 0), (xc + c.slot / 2, c.db), f"{c.db:.2f} deep", off=9, horizontal=False, fs=9)
        dim_line(ax, (xc - 22, 0), (xc - 22, c.H), f"{c.H:g}", off=-3, horizontal=False, fs=9)
        dim_line(ax, (xc - 22, c.Hv), (xc - 22, c.H), "", off=0)
        ax.text(xc, -6, f"slot = {c.t} + {SLOT_CLEARANCE} mm clearance, kerf to be adjusted by vendor", ha="center", fontsize=8)
        ax.text(xc, c.H + 6, "teeth: see detail 3", ha="center", fontsize=8)
        ax.set_xlim(xc - 30, xc + 30); ax.set_ylim(-10, c.H + 14)
        # rib slot detail
        ax = fig.add_axes([0.35, 0.10, 0.30, 0.42]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("DETAIL 2 - rib slot (from top)", fontsize=10.5, loc="left", fontweight="bold")
        yc = c.blade_y[2]; g = clip(R, yc - 22, yc + 22)
        for gg in ([g] if g.geom_type == "Polygon" else g.geoms): draw_poly(ax, list(gg.exterior.coords), fc=RIBC)
        dim_line(ax, (yc - c.slot / 2, c.RH - c.dr), (yc + c.slot / 2, c.RH - c.dr), f"{c.slot} wide", off=-8, fs=9)
        dim_line(ax, (yc + c.slot / 2, c.RH - c.dr), (yc + c.slot / 2, c.RH), f"{c.dr:.2f} deep", off=9, horizontal=False, fs=9)
        dim_line(ax, (yc - 22, 0), (yc - 22, c.RH), f"{c.RH:g}", off=-3, horizontal=False, fs=9)
        ax.text(yc, -6, f"remaining web under slot {c.RH - c.dr:.2f}", ha="center", fontsize=8)
        ax.set_xlim(yc - 30, yc + 30); ax.set_ylim(-10, c.H + 14)
        # teeth detail
        ax = fig.add_axes([0.67, 0.30, 0.30, 0.22]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("DETAIL 3 - serrated top (blades only)", fontsize=10.5, loc="left", fontweight="bold")
        g = clip(B, 0, 40, c.Hv - 14, c.H + 1)
        for gg in ([g] if g.geom_type == "Polygon" else g.geoms): draw_poly(ax, list(gg.exterior.coords), fc=STEEL)
        dim_line(ax, (0, c.H), (c.L / round(c.L / c.tooth_p), c.H), f"{c.tooth_p:g} pitch", off=5, fs=9)
        dim_line(ax, (40, c.Hv), (40, c.H), f"{c.tooth_h:g} high", off=-1, horizontal=False, fs=9)
        ax.text(20, c.Hv - 12, "tips are sharp: deburr / handle with gloves\n(optional 0.5 mm flat on tips)", ha="center", fontsize=8)
        ax.set_xlim(-6, 55); ax.set_ylim(c.Hv - 17, c.H + 9)
        # notes
        ax = fig.add_axes([0.67, 0.06, 0.31, 0.22]); ax.axis("off")
        lines = ["NOTES",
                 f"1. Material: mild steel (A36 / equivalent), {c.material} = {c.t} mm. 11 ga ({THICKNESS_MM['11ga']} mm) also OK;",
                 "   if 11 ga, slot width becomes 3.25 mm (regenerate with --material 11ga).",
                 "2. Slot width = thickness + 0.2 mm. Vendor to compensate kerf; widen to 3.5 if tight.",
                 "3. Tolerances: slot width +0.15/-0.05, slot position +/-0.2, length +/-0.5.",
                 "4. Deburr all edges, remove dross; leave bare steel (light oil). If coated, add",
                 "   coating thickness to slot width.",
                 f"5. Qty: {c.n_blades*c.n_panels} x A, {c.n_ribs*c.n_panels} x B.   Two panels of {c.L:g} x {c.W:g}.",
                 "6. Dimensions to be confirmed after measuring the machine inside opening."]
        sheet_text(ax, lines, fs=8.6, dy=0.105)
        for lx, ly in [(0.03, 0.065)]:
            pass
        ax = fig.add_axes([0.03, 0.02, 0.62, 0.06]); ax.axis("off")
        ax.text(0, 0.9, "ASSEMBLY CHECK (computed): " + log[0], fontsize=8.3, va="top", wrap=True)
        pdf.savefig(fig); plt.close(fig)


# ------------------------------------ main ------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--material", default=None, choices=list(THICKNESS_MM))
    ap.add_argument("--out", default=OUT_DIR)
    a = ap.parse_args()
    c = build_cfg(a.material)
    out = a.out; os.makedirs(out, exist_ok=True)
    log = []
    verify(c, log)
    st = stats(c)

    write_parts_dxf(c, os.path.join(out, "egg_crate_bed.dxf"))

    # nest: one panel on 4x8
    parts1 = part_list(c, 1)
    sh1, ncol = nest(parts1, SHEET_4X8)
    check_nest(sh1, SHEET_4X8)
    write_nest_dxf(c, sh1, SHEET_4X8, os.path.join(out, "nest_one_panel_4x8.dxf"), "ONE PANEL")
    # whole bed on 4x8 (may need >1 sheet) and on 60x120
    partsN = part_list(c, c.n_panels)
    shN, _ = nest(partsN, SHEET_4X8); check_nest(shN, SHEET_4X8)
    write_nest_dxf(c, shN, SHEET_4X8, os.path.join(out, "nest_full_bed_4x8.dxf"), "FULL BED on 4x8")
    shL, _ = nest(partsN, SHEET_60X120); check_nest(shL, SHEET_60X120)
    write_nest_dxf(c, shL, SHEET_60X120, os.path.join(out, "nest_full_bed_60x120.dxf"), "FULL BED on 60x120")
    # extent used on 1-panel nest
    ext = max(max(p[1] for p in pts) for _, _, pts in sh1[0]) + NEST_MARGIN
    nest_info = (f"one panel ({len(parts1)} parts) fits on ONE 4x8 sheet in {ext:.0f} of {SHEET_4X8[0]:g} mm width; "
                 f"whole bed ({len(partsN)} parts) needs {len(shN)} 4x8 sheets (2nd sheet {len(shN[1]) if len(shN)>1 else 0} parts) or {len(shL)} sheet of 60x120.")
    log.append(nest_info)

    png = os.path.join(out, "egg_crate_assembly.png")
    make_png(c, png, st)
    make_pdf(c, os.path.join(out, "egg_crate_drawing.pdf"), st, png, nest_info, log)

    # --- re-read DXFs
    for f in ["egg_crate_bed.dxf", "nest_one_panel_4x8.dxf", "nest_full_bed_4x8.dxf", "nest_full_bed_60x120.dxf"]:
        u, cnt = dxf_report(os.path.join(out, f))
        log.append(f"{f}: units={u} (4=mm) entities={cnt}")

    print("CONFIG: material", c.material, "t", c.t, "slot", c.slot, "blade_h", c.H, "rib_h", c.RH, "pitch", c.pitch,
          "n_blades", c.n_blades, "n_ribs", c.n_ribs, "rib_pitch", round(c.rib_pitch, 2), "db/dr", c.db)
    print(f"WEIGHT: blade {st['wb']:.3f} kg, rib {st['wr']:.3f} kg, panel {st['per_panel']:.1f} kg, bed {st['total']:.1f} kg, 4x8 sheet {st['sheet_wt']:.1f} kg")
    print(f"CUT LENGTH: blade {st['cut_len_blade']:.0f} mm, rib {st['cut_len_rib']:.0f} mm; per panel "
          f"{(c.n_blades*st['cut_len_blade']+c.n_ribs*st['cut_len_rib'])/1000:.1f} m")
    print(f"NEST 1 panel 4x8: sheets={len(sh1)} columns={ncol} parts={len(sh1[0])}")
    print(f"NEST full 4x8: sheets={len(shN)} parts per sheet={[len(s) for s in shN]}")
    print(f"NEST full 60x120: sheets={len(shL)} parts per sheet={[len(s) for s in shL]}")
    for l in log: print(l)


if __name__ == "__main__":
    main()
