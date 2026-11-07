"""Queen Anne v5. Units mm. Z up. Front is -Y.

Proportion, taken from the approved picture before any ornament:
the composition is broad. The turret is a large octagon, about a
quarter of the width, and its spire clears the main ridge. The porch
is deep and wraps that octagon. The street gable is a real cross-gable,
not one slab. Ornament is revolved or extruded, and the shingles are
individual scallops.

v4 is archived. It was a narrow stack with a flat porch and bar roofs.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import trimesh as tm
import manifold3d as md
from shapely.geometry import Point, Polygon, box as sbox, LineString
from shapely.geometry.polygon import orient as orient_poly
from shapely.ops import unary_union
from PIL import Image, ImageDraw
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STL = os.path.join(ROOT, "stl")
REPORT = os.path.join(ROOT, "reports")
LEGACY_TILE = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "floor_tile_v0.stl"))
LEGACY_POST = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "snap_post_v0.stl"))

BED = (330.0, 320.0, 325.0)
FIT = (310.0, 300.0, 315.0)

# Measured on the approved picture, then drawn:
# the closed house is about as wide as the spire is tall.
# The spire clears the main ridge by about a sixth of the height.
# The turret is about a quarter of that width, on the left.
# The porch is the ground storey and wraps the octagon.
# Rightmost turret vertex is TX + TR*cos(22.5) ≈ 209.6, so the
# main block starts just past it. The hairline between them is a
# real part joint, not a buried intersection.
TX, TY, TR = 156.0, 126.0, 58.0
MX0, MX1 = 211.0, 508.0
MY0, MY1 = 116.0, 296.0
PORCH_FRONT = 18.0
BASE = 16.0
F2F = 98.0
FLOOR_T = 6.0
PLATE = 10.0
GAP = 0.4
CLEAR = F2F - FLOOR_T - GAP - PLATE
L1, L2, L3 = BASE, BASE + F2F, BASE + 2 * F2F
EAVE = L3 + 12.0
RIDGE = EAVE + 128.0
CONE_H = 112.0

RISES = 13
RISE = F2F / RISES
TREAD = 10.0
RUN = (RISES - 1) * TREAD
HEAD = 72.0

S1 = dict(x0=424.0, x1=470.0, y0=136.0, y1=136.0 + RUN, z=L1, up=1)
S2 = dict(x0=366.0, x1=412.0, y0=248.0 - RUN, y1=248.0, z=L2, up=-1)

MAG_D, MAG_T = 5.0, 2.8
# Design allowances for a nominal disc. Not a measured fit.
# 0.30 mm on each side of the diameter, 0.40 mm along the 2.8 mm thickness.
# 1.4 mm of solid stays on the mating face so the disc cannot enter the closure gap.
SKIN, RAD, AX = 1.4, 0.30, 0.40
POD_D = MAG_D + 2 * RAD
POD_H = MAG_T + AX
PULL = 70.0
FIT_GAP = 0.45
JAMB_BACK = MY1 - 1.0

SAGE, IVORY, WINE = "#6f917c", "#f4ecdc", "#8d3038"
SLATE, BRICK = "#2a3642", "#8b4e3c"
WOOD, WOOD_D, PLASTER, BRASS = "#c4894e", "#6a432c", "#f6efe4", "#e6c98a"


def box_at(a, b, c, d, e, f):
    if min(d - a, e - b, f - c) <= 0.05:
        return None
    m = box((d - a, e - b, f - c))
    m.apply_translation(((a + d) / 2, (b + e) / 2, (c + f) / 2))
    return m


def move(mesh, x, y, z):
    out = mesh.copy()
    out.apply_translation((x, y, z))
    return out


def _xform(mesh, origin, x_axis, y_axis, z_axis):
    M = np.eye(4)
    M[0:3, 0] = np.asarray(x_axis, float)
    M[0:3, 1] = np.asarray(y_axis, float)
    M[0:3, 2] = np.asarray(z_axis, float)
    M[0:3, 3] = np.asarray(origin, float)
    out = mesh.copy()
    out.apply_transform(M)
    return out


def union(meshes):
    parts = [m for m in meshes if m is not None]
    if not parts:
        raise ValueError("empty union")
    acc = parts[0]
    for i in range(1, len(parts), 20):
        acc = tm.boolean.union([acc, *parts[i:i + 20]], engine="manifold")
    return acc


def difference(base, cuts):
    cuts = [c for c in cuts if c is not None]
    acc = base
    for i in range(0, len(cuts), 12):
        acc = tm.boolean.difference([acc, *cuts[i:i + 12]], engine="manifold")
    return acc


def cleanup(mesh, name):
    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    if mesh.volume < 0:
        mesh.invert()
    good = [p for p in mesh.split(only_watertight=False) if p.volume > 1.0]
    if (not mesh.is_watertight) or len(good) != 1:
        raise RuntimeError(f"{name} bodies={len(good)} watertight={mesh.is_watertight} vol={mesh.volume:.0f}")
    return mesh


def hull(pts):
    return tm.convex.convex_hull(np.asarray(pts, float))


def octagon(cx, cy, radius):
    return [(cx + radius * math.cos(math.radians(22.5 + i * 45)),
             cy + radius * math.sin(math.radians(22.5 + i * 45))) for i in range(8)]


def prism(pts, z0, z1):
    return hull([(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts])


def revolve(profile, sections=16):
    mesh = tm.creation.revolve(np.asarray(profile, float), sections=sections)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def extrude(poly, depth):
    mesh = tm.creation.extrude_polygon(poly, depth)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def spindle(h=26.0):
    return revolve([
        [0, 0], [2.15, 0], [2.35, 1.2], [1.35, 3.2], [1.25, h * 0.38],
        [2.55, h * 0.52], [1.25, h * 0.68], [1.45, h - 2.4], [2.25, h - 0.8],
        [2.15, h], [0, h],
    ], 24)


def column(h):
    return revolve([
        [0, 0], [6.4, 0], [7.6, 2.2], [7.2, 5], [5.4, 8], [4.6, 14],
        [4.35, h - 16], [5.1, h - 10], [7.4, h - 5],         [7.8, h - 1.5], [6.8, h], [0, h],
    ], 28)


def bracket_mesh():
    """Cyma porch bracket. The spandrel opening goes through the plate."""
    pts = [(0, 0), (0, 20), (3.6, 20), (3.6, 15.5)]
    for i in range(8):
        t = i / 7
        pts.append((3.6 + 13 * (t ** 1.35), 15.2 - 12.4 * math.sin(t * math.pi / 2)))
    pts += [(16.2, 1.6), (16.2, 0)]
    plate = Polygon(pts)
    opening = Polygon([(6.0, 2.2), (6.0, 7.0), (8.4, 5.4), (11.0, 3.5), (13.0, 2.4), (10.8, 2.2)])
    shape = plate.difference(opening)
    if shape.geom_type != "Polygon" or len(shape.interiors) != 1:
        raise RuntimeError(f"bracket opening failed {shape.geom_type}")
    return extrude(shape, 4.2)


def fish_tile():
    """One fish-scale. The round nose is the exposed butt."""
    body = sbox(-2.7, 0.2, 2.7, 4.8)
    nose = Point(0, 0.2).buffer(2.55, resolution=6)
    shape = body.union(nose).intersection(sbox(-2.9, -0.15, 2.9, 5.4))
    return extrude(shape, 1.05)


def scallop():
    """Main-roof shingle. Subtle relief, not a spike."""
    body = sbox(-3.4, 0, 3.4, 4.2)
    nose = Point(0, 4.0).buffer(3.2, resolution=5)
    shape = body.union(nose).intersection(sbox(-3.7, 0, 3.7, 7.0))
    return extrude(shape, 0.55)


def tiny_scallop():
    """Cone shingle. Small enough to read as slate, not armour."""
    body = sbox(-1.55, 0, 1.55, 1.9)
    nose = Point(0, 1.85).buffer(1.45, resolution=4)
    shape = body.union(nose).intersection(sbox(-1.7, 0, 1.7, 3.2))
    return extrude(shape, 0.38)


def bargeboard(length=168.0):
    """Connected verge. Scroll openings, not a row of drilled holes."""
    bar = sbox(0, 1.6, length, 18)
    holes = []
    x = 12.0
    while x < length - 18:
        holes.append(Polygon([
            (x, 6.4), (x + 3.4, 12.2), (x + 8.0, 10.6), (x + 6.4, 7.2), (x + 2.2, 6.6),
        ]).buffer(0.65))
        x += 16.5
    bites = [Point(float(v), 1.6).buffer(3.2, resolution=6) for v in np.arange(8, length - 4, 14)]
    shape = bar.difference(unary_union(holes + bites))
    if shape.geom_type != "Polygon":
        raise RuntimeError(f"verge split into {shape.geom_type}")
    return extrude(shape, 2.4)


def rake_board(x0, z0, x1, z1, y, into):
    """Scalloped barge along a gable rake. `into` is +1 or -1, toward the triangle."""
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)
    board = bargeboard(max(24.0, length - 10))
    board.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    board.apply_translation(-board.bounds[0])
    board.apply_transform(rotation_matrix(-math.atan2(dz, dx), [0, 1, 0]))
    board.apply_translation((x0 + into * dz / length * 7, y, z0 + into * -dx / length * 7))
    return board


SCALLOP = None
TINY = None
FISH = None
BRACKET = None
SPINDLE = None


def cached():
    global SCALLOP, TINY, FISH, BRACKET, SPINDLE
    if SCALLOP is None:
        SCALLOP = cleanup(scallop(), "scallop")
        TINY = cleanup(tiny_scallop(), "tiny")
        FISH = cleanup(fish_tile(), "fish")
        BRACKET = cleanup(bracket_mesh(), "bracket")
        SPINDLE = cleanup(spindle(), "spindle")


def plate_top(floor):
    return floor + CLEAR + PLATE


def slope_frame(y0, z0, y1, z1):
    slope = np.array([0.0, y1 - y0, z1 - z0], float)
    slope /= np.linalg.norm(slope)
    normal = np.cross(np.array([1.0, 0.0, 0.0]), slope)
    normal /= np.linalg.norm(normal)
    return slope, normal


def slope_slab(x0, x1, y0, z0, y1, z1, thick=5.5):
    slope, normal = slope_frame(y0, z0, y1, z1)
    inn = -normal * thick
    return hull([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z1), (x0, y1, z1),
        (x0, y0, z0) + inn, (x1, y0, z0) + inn, (x1, y1, z1) + inn, (x0, y1, z1) + inn,
    ])


def shingle_field(x0, x1, y0, z0, y1, z1, kind="scallop", skip=None):
    """Staggered shingles embedded in the slope. Fish scales point downhill."""
    cached()
    slope, normal = slope_frame(y0, z0, y1, z1)
    length = float(np.linalg.norm([0, y1 - y0, z1 - z0]))
    across = np.array([1.0, 0.0, 0.0])
    fish = kind == "fish"
    tile = FISH if fish else SCALLOP
    along = slope
    embed = 0.40 if fish else 0.22
    pitch_x = 9.0 if fish else 7.2
    pitch_s = 4.4 if fish else 4.6
    pieces = []
    course = 0
    s = 2.0
    while s < length - 8:
        x = x0 + 2 + ((pitch_x * 0.5) if course % 2 else 0)
        while x < x1 - 6:
            origin = np.array([x, y0, z0], float) + slope * s - normal * embed
            if skip is not None and skip(origin):
                x += pitch_x
                continue
            pieces.append(_xform(tile, origin, across, along, normal))
            x += pitch_x
        s += pitch_s
        course += 1
    return pieces


def clapboard(x0, y0, z0, x1, y1, z1, face):
    ribs = []
    z = z0 + 1.0
    while z < z1 - 2.2:
        z2 = min(z + 2.15, z1)
        if face == "-y":
            ribs.append(box_at(x0, y0 - 0.9, z, x1, y0 + 0.85, z2))
        elif face == "+x":
            ribs.append(box_at(x1 - 0.85, y0, z, x1 + 0.9, y1, z2))
        elif face == "+y":
            ribs.append(box_at(x0, y1 - 0.85, z, x1, y1 + 0.9, z2))
        z += 4.05
    return [r for r in ribs if r]


def brick_skin(x0, y0, x1, y1, z1):
    bands = []
    z = 1.2
    while z < z1 - 2:
        bands += [
            box_at(x0 + 2, y0 - 1.15, z, x1 - 2, y0 + 0.4, z + 2.3),
            box_at(x0 + 2, y1 - 0.4, z, x1 - 2, y1 + 1.15, z + 2.3),
            box_at(x1 - 0.4, y0 + 2, z, x1 + 1.15, y1 - 2, z + 2.3),
            box_at(x0 - 1.15, y0 + 2, z, x0 + 0.4, y1 - 2, z + 2.3),
        ]
        z += 4.8
    return [b for b in bands if b]


def plate_xz(poly, y_face, depth):
    """Extrude a profile drawn in XZ. Thickness grows toward -Y from y_face."""
    poly = orient_poly(poly, 1)
    if poly.geom_type != "Polygon":
        raise RuntimeError(f"profile is {poly.geom_type}")
    contours = [np.array(poly.exterior.coords)[:-1], *[np.array(ring.coords)[:-1] for ring in poly.interiors]]
    raw = md.CrossSection(contours).extrude(depth).to_mesh()
    mesh = tm.Trimesh(np.asarray(raw.vert_properties)[:, :3], np.asarray(raw.tri_verts), process=True)
    verts = np.array(mesh.vertices)
    mesh.vertices = np.column_stack([verts[:, 0], y_face - verts[:, 2], verts[:, 1]])
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def arch_band(x, z, w, rise, width):
    t = np.linspace(math.pi, 0.0, 40)
    cx = x + w / 2.0
    arc = np.column_stack([cx + (w * 0.52) * np.cos(t), z + rise * np.sin(t)])
    return LineString(arc).buffer(width / 2.0, cap_style=2)


def pediment(x, y, z, w, kind="arch"):
    """Curved hood. kind=fan adds pierced lights and a short spindle rail."""
    rise = max(8.0, min(14.0, w * 0.28))
    parts = [
        plate_xz(arch_band(x, z, w, rise, 2.8), y + 0.2, 3.4),
        plate_xz(arch_band(x + 1.4, z + 1.6, w - 2.8, rise * 0.62, 1.35), y - 2.2, 1.7),
    ]
    if kind == "fan" and w >= 28:
        t = np.linspace(math.pi, 0.0, 42)
        cx = x + w / 2.0
        outer = np.column_stack([cx + (w * 0.46) * np.cos(t), z + 1.2 + rise * 0.78 * np.sin(t)])
        fan = Polygon([(x + 1.5, z + 1.2), (x + w - 1.5, z + 1.2), *outer.tolist()]).buffer(0)
        holes = []
        for frac in (-0.64, -0.32, 0.0, 0.32, 0.64):
            px = cx + frac * w * 0.34
            span = max(0.08, 1.0 - (frac * 1.2) ** 2)
            top = z + 2.4 + rise * 0.62 * math.sqrt(span)
            holes.append(LineString([(px, z + 3.4), (cx * 0.82 + px * 0.18, top)]).buffer(0.85))
        fan = fan.difference(unary_union(holes))
        if fan.geom_type != "Polygon":
            raise RuntimeError(f"fan hood split {fan.geom_type}")
        parts.append(plate_xz(fan, y - 0.4, 2.2))
        rail = z + rise + 1.2
        parts.append(box_at(x - 1, y - 2.8, rail, x + w + 1, y + 0.8, rail + 2.0))
        parts.append(box_at(x - 3, y - 4.2, rail + 8.2, x + w + 3, y + 0.6, rail + 10.6))
        for px in np.linspace(x + 2.5, x + w - 2.5, 7):
            sp = spindle(7.6)
            sp.apply_translation((float(px), y - 1.2, rail + 1.0))
            parts.append(sp)
    return parts


def window_pack(face, x, y, z, w, h, hood="arch"):
    """Layered casing, sill, and a curved hood. The pane is a hole already cut in the wall.
    The front lip is added after that cut, so the cutter cannot erase it.
    hood=fan is the one ornate street window. hood=plain is a side window with no crown.
    """
    parts = []
    if face == "-y":
        parts += [
            box_at(x - 3.2, y - 3.0, z - 3.4, x + w + 3.2, y + 0.8, z + 1.4),
            box_at(x - 3.4, y - 2.6, z + h - 1.2, x + w + 3.4, y + 0.8, z + h + 3.2),
            box_at(x - 3.2, y - 2.6, z, x + 1.5, y + 0.8, z + h),
            box_at(x + w - 1.5, y - 2.6, z, x + w + 3.2, y + 0.8, z + h),
            box_at(x - 5.4, y - 4.6, z - 5.2, x + w + 5.4, y - 1.2, z - 2.0),
            box_at(x - 5.2, y - 3.8, z - 1.2, x - 2.2, y + 0.2, z + h + 1.4),
            box_at(x + w + 2.2, y - 3.8, z - 1.2, x + w + 5.2, y + 0.2, z + h + 1.4),
            box_at(x - 4.6, y - 3.4, z + h + 1.0, x + w + 4.6, y + 0.2, z + h + 3.6),
            # Front stop. It overlaps the opening and is not in the wall cutter.
            box_at(x, y - 0.9, z, x + 1.15, y + 0.55, z + h),
            box_at(x + w - 1.15, y - 0.9, z, x + w, y + 0.55, z + h),
            box_at(x, y - 0.9, z + h - 1.15, x + w, y + 0.55, z + h),
            box_at(x, y - 0.9, z, x + w, y + 0.55, z + 1.15),
        ]
        if hood != "fan":
            parts += [
                box_at(x, y - 2.2, z + h * 0.47, x + w, y + 0.6, z + h * 0.47 + 1.8),
                box_at(x + w * 0.47, y - 2.0, z + 1.4, x + w * 0.53, y + 0.5, z + h * 0.47),
                box_at(x + w * 0.47, y - 2.0, z + h * 0.47 + 1.8, x + w * 0.53, y + 0.5, z + h - 1.2),
            ]
        if hood != "plain":
            parts += pediment(x - 2, y, z + h + 2.4, w + 4, "fan" if hood == "fan" else "arch")
    elif face == "+x":
        parts += [
            box_at(x - 0.8, y - 3.2, z - 3.4, x + 3.0, y + w + 3.2, z + 1.4),
            box_at(x - 0.8, y - 3.4, z + h - 1.2, x + 3.0, y + w + 3.4, z + h + 2.4),
            box_at(x - 0.8, y - 3.2, z, x + 3.0, y + 1.5, z + h),
            box_at(x - 0.8, y + w - 1.5, z, x + 3.0, y + w + 3.2, z + h),
            box_at(x - 0.6, y, z + h * 0.47, x + 2.4, y + w, z + h * 0.47 + 1.8),
            box_at(x - 1.6, y - 4.6, z - 5.0, x + 1.2, y + w + 4.6, z - 2.2),
            box_at(x - 1.4, y - 4.4, z - 1, x + 1.0, y - 2.0, z + h),
            box_at(x - 1.4, y + w + 2.0, z - 1, x + 1.0, y + w + 4.4, z + h),
        ]
    return [p for p in parts if p is not None]


def flower_box(x, y, z, w=28):
    parts = [box_at(x, y - 8, z, x + w, y - 1.2, z + 7)]
    for i in range(4):
        parts.append(tm.creation.icosphere(subdivisions=1, radius=2.1))
        parts[-1].apply_translation((x + 4 + i * 6.5, y - 4.6, z + 8))
    return parts


def owl():
    body = revolve([[0, 0], [4.2, 0], [4.6, 2], [3.2, 7], [3.8, 10], [2.4, 13], [0, 13]], 12)
    ear = box_at(-1.2, -1, 11.5, 1.2, 1, 15)
    return union([body, ear, move(ear, 2.4, 0, 0)])


CATALOG, INSTANCES, FIXTURES = {}, [], []


def add_part(name, mesh, note):
    ext = [round(float(v), 2) for v in (mesh.bounds[1] - mesh.bounds[0])]
    if any(ext[i] > FIT[i] + 0.3 for i in range(3)):
        raise RuntimeError(f"{name} too big {ext}")
    CATALOG[name] = {"mesh": mesh, "note": note, "extents": ext, "triangles": int(len(mesh.faces)), "volume": round(float(mesh.volume), 1)}
    print(name, ext, flush=True)


def publish(name, world, note, iid, role, color, motion=None, explode=None, extra=None):
    local = world.copy()
    origin = local.bounds[0].copy()
    local.apply_translation(-origin)
    add_part(name, local, note)
    INSTANCES.append({
        "id": iid, "part": name, "role": role, "color": color, "motion": motion,
        "explode_mm": explode or [0, 0, 0], "world": world,
        "place": [float(v) for v in origin], "extra": extra or {},
    })


def build():
    cached()
    foundations()
    floors()
    fixed_walls()
    facades()
    roofs()
    porch()
    stairs()
    ornament()
    rooms()
    service()


def foundations():
    main = union([
        box_at(MX0, PORCH_FRONT, 3, MX1, MY1, BASE),
        box_at(MX0 + 0.8, PORCH_FRONT - 3, BASE - 5.5, MX1 + 3, MY1 + 3, BASE - 1.4),
        box_at(394, 290, 8, 410, 301.7, 15.4),
        *brick_skin(MX0 + 2.2, PORCH_FRONT, MX1, MY1, BASE),
    ])
    deck = []
    y = PORCH_FRONT + 4
    while y < MY0 - 4:
        deck.append(box_at(MX0 + 8, y, BASE - 0.6, 400, y + 3.2, BASE - 0.15))
        y += 7
    chase = [
        box_at(221.4, 278.4, 14.0, 224.6, 281.6, 16.3),
        box_at(221.4, 278.4, 10.4, 402, 281.6, 13.2),
        box_at(396.2, 278.4, 10.4, 403.6, 301.9, 13.2),
    ]
    publish("qa5_foundation_v5", cleanup(difference(union([main, *deck]), chase), "foundation"),
            "Brick base, porch deck, and a covered chase to the service bay. The chase is a void in this solid.",
            "foundation", "structure", BRICK)
    turret = union([
        prism(octagon(TX, TY, TR + 42), 0, BASE),
        prism(octagon(TX, TY, TR + 48), BASE - 5.5, BASE - 1.4),
    ])
    turret = cleanup(difference(turret, [box_at(MX0 - 0.6, -20, -4, 900, 700, BASE + 8)]), "turret base")
    publish("qa5_foundation_turret_v5", turret, "Octagonal brick pier under the turret.", "turret-base", "structure", BRICK, explode=[-18, -8, 0])


def floors():
    def slab(z, well):
        mesh = box_at(MX0 + 6, MY0 + 6, z - FLOOR_T, MX1 - 14, MY1 - 6, z)
        ribs = []
        y = MY0 + 14
        while y < MY1 - 12:
            ribs.append(box_at(MX0 + 16, y, z - 0.55, MX1 - 20, y + 1.3, z + 0.15))
            y += 9
        mesh = union([mesh, *ribs])
        bore = cylinder(radius=1.55, height=FLOOR_T + 1.2, sections=12)
        bore.apply_translation((223, 280, z - FLOOR_T / 2))
        return cleanup(difference(mesh, [box_at(*well), bore]), "floor")
    well1 = (S1["x0"] - 4, S1["y0"] - 4, L2 - FLOOR_T - 1, S1["x1"] + 4, S1["y1"] + 8, L2 + 1)
    well2 = (S2["x0"] - 4, S2["y0"] - 6, L3 - FLOOR_T - 1, S2["x1"] + 4, S2["y1"] + 6, L3 + 1)
    publish("qa5_floor_l2_v5", slab(L2, well1), "First floor. Opening is the lower stair.", "floor-l2", "floor", WOOD, explode=[0, 0, 10])
    publish("qa5_floor_l3_v5", slab(L3, well2), "Attic floor. Opening is the upper stair.", "floor-l3", "floor", WOOD, explode=[0, 0, 18])
    disc = cleanup(prism(octagon(TX, TY, TR - 16), 0, FLOOR_T), "turret floor")
    disc = cleanup(difference(disc, [box_at(MX0 - 0.6, -10, -2, 900, 500, 20)]), "turret floor cut")
    for iid, z, exp in (("turret-floor-l2", L2 - FLOOR_T, 10), ("turret-floor-l3", L3 - FLOOR_T, 18)):
        world = move(disc, 0, 0, z)
        if iid.endswith("l2"):
            publish("qa5_floor_turret_v5", world, "Turret floor, outside the main slab.", iid, "floor", WOOD, explode=[-8, 0, exp])
        else:
            INSTANCES.append({"id": iid, "part": "qa5_floor_turret_v5", "role": "floor", "color": WOOD,
                              "motion": None, "explode_mm": [-8, 0, exp], "world": world,
                              "place": [float(v) for v in world.bounds[0]], "extra": {}})


def fixed_walls():
    def shell(floor, name):
        z0, z1 = floor + 0.4, plate_top(floor)
        zp = floor + CLEAR
        parts = [
            # Ceiling plate reaches the rear edge so the roof bears with the back off.
            box_at(MX0 + 4, MY0 + 8, zp, MX1 - 16, MY1 - 3, z1),
            box_at(MX0 + 12, MY0 + 4, zp - 9, MX1 - 12, MY0 + 14, z1),
            # Hall wall stops short of the rear opening.
            box_at(348, MY0 + 16, z0, 356, MY1 - 28, z1),
            # Left rear jamb. The right jamb is the side wall's return.
            box_at(MX0 + 6, MY1 - 18, z0, MX0 + 18, MY1 - 1.0, z1),
        ]
        parts.append(box_at(336, 208, floor + 40, 360, 226, floor + 56))
        parts.append(box_at(336, 238, floor + 42, 360, 256, floor + 56))
        cuts = [box_at(344, 148, z0, 362, 196, floor + 76)]
        for zc in (floor + 28, floor + 52, floor + 74):
            # Opens on the room face of the jamb. Skin of SKIN stays on the mating face.
            cuts.append(along_y(MX0 + 17, JAMB_BACK - SKIN, MY1 - 18.6, zc, POD_D / 2))
            cuts.append(along_y(MX0 + 17, MY1 - 20.4, MY1 - 18.2, zc, 4.3))
        if name == "l1":
            cuts.append(box_at(S1["x0"] - 6, S1["y0"] - 6, zp - 1, S1["x1"] + 6, S1["y1"] + 10, z1 + 1))
        else:
            cuts.append(box_at(S2["x0"] - 6, S2["y0"] - 8, zp - 1, S2["x1"] + 6, S2["y1"] + 8, z1 + 1))
        # Chase inside the plate, then down the left jamb. Opens on the jamb underside.
        mid = zp + PLATE * 0.5
        spots = [(280, 175), (390, 155)] if name == "l1" else [(290, 185), (470, 160), (400, 270)]
        for x, y in spots:
            bore = cylinder(radius=1.45, height=5.4, sections=12)
            bore.apply_translation((x, y, zp + 2.4))
            cuts.append(bore)
            cuts.append(box_at(x - 1.3, min(y, 280), mid - 1.3, x + 1.3, max(y, 280), mid + 1.3))
        cuts.append(box_at(221.7, 278.7, mid - 1.3, max(s[0] for s in spots) + 1.3, 281.3, mid + 1.3))
        drop = cylinder(radius=1.45, height=mid - (floor + 0.15), sections=12)
        drop.apply_translation((223, 280, (mid + floor + 0.15) / 2))
        cuts.append(drop)
        # Shelf and locating pin are part of this solid. They overlap the jamb.
        # Bottom ledge only on the ground storey. The panel is one piece from that floor up,
        # so a ledge at the upper floor would sit inside the panel.
        if name == "l1":
            parts.append(union([
                box_at(MX0 + 7, JAMB_BACK - 4, floor + 0.15, MX0 + 17, JAMB_BACK + 0.3, floor + 6),
                box_at(MX0 + 7, JAMB_BACK - 1, floor + 0.15, MX0 + 17, JAMB_BACK + 5.5, floor + FIT_GAP),
            ]))
        pin = cylinder(radius=1.35, height=10, sections=16)
        pin.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        pin.apply_translation((MX0 + 12, JAMB_BACK + 1.5, floor + 36))
        parts.append(pin)
        return cleanup(difference(union(parts), cuts), name)
    publish("qa5_walls_l1_v5", shell(L1, "l1"),
            "Fixed ceiling, hall wall, and the left rear jamb. The rear opening is clear.",
            "walls-l1", "structure", PLASTER)
    publish("qa5_walls_l2_v5", shell(L2, "l2"),
            "Fixed ceiling and hall wall of the first floor. The back is not this part.",
            "walls-l2", "structure", PLASTER, explode=[0, 12, 8])
    knee_z = EAVE - GAP
    knee = union([
        box_at(MX0 + 16, MY0 + 4, L3 + 0.5, MX1 - 10, MY0 + 10, knee_z),
        # Side pads only, so the attic center is open from the rear above the back wall.
        box_at(MX0 + 16, MY1 - 14, L3 + 0.5, MX0 + 52, MY1 - 4, knee_z),
        box_at(MX1 - 56, MY1 - 14, L3 + 0.5, MX1 - 16, MY1 - 4, knee_z),
        box_at(MX0 + 10, MY0 + 6, L3 + 0.5, MX0 + 22, MY1 - 6, knee_z),
        box_at(MX1 - 18, MY0 + 6, L3 + 0.5, MX1 - 8, MY1 - 6, knee_z),
    ])
    publish("qa5_attic_frame_v5", cleanup(knee, "knee"), "Eave plates the roof sits on.", "attic-frame", "structure", PLASTER, explode=[0, 0, 16], extra={"plate_top": knee_z})
    lights(L1, [("parlor", 280, 175), ("entry", 390, 155), ("kitchen", 492, 240)])
    lights(L2, [("bedroom", 290, 185), ("bath", 470, 160), ("landing", 400, 270)])
    lights(L3, [("attic", 400, 190), ("turret", TX, TY)])


def lights(floor, spots):
    void = cylinder(radius=2.6, height=3.2, sections=12)
    void.apply_translation((0, 0, 1.6))
    feed = cylinder(radius=1.15, height=4.4, sections=12)
    feed.apply_translation((0, 0, 4.6))
    slot = box_at(-3, -0.5, -0.2, -0.6, 0.5, 1.3)
    housing = cleanup(difference(revolve([
        [0, 0], [6.2, 0], [6.2, 1.0], [4.6, 2.6], [2.4, 6.4], [0, 6.4],
    ], 16), [void, feed, slot, move(slot, 4.2, 0, 0)]), "puck")
    name = "qa5_puck_v5"
    if name not in CATALOG:
        local = housing.copy()
        origin = local.bounds[0].copy()
        local.apply_translation(-origin)
        add_part(name, local, "Ceiling puck. Cavity opens down. A 2.3 mm feed leaves the top. The diode is not measured.")
    top = floor + CLEAR - 0.30
    storey = 1 if floor == L1 else (2 if floor == L2 else 3)
    for room, x, y in spots:
        world = move(housing, x, y, top - float(housing.bounds[1][2]))
        INSTANCES.append({
            "id": f"{room}-light", "part": name, "role": "light", "color": BRASS,
            "motion": None, "explode_mm": [0, 0, 12], "world": world,
            "place": [float(v) for v in world.bounds[0]], "extra": {},
        })
        FIXTURES.append({"id": f"{room}-light", "kind": "ceiling", "room": room, "x": x, "y": y,
                         "z": top - 7, "storey": storey, "circuit": room})


def facade(bounds, face, windows, flowers=False):
    x0, y0, z0, x1, y1, z1 = bounds
    if face == "-y":
        body = [box_at(x0, y1 - 3.4, z0, x1, y1, z1),
                box_at(x0, y1 - 7.5, z0, x0 + 12, y1, z1),
                box_at(x1 - 12, y1 - 7.5, z0, x1, y1, z1)]
        skin = clapboard(x0 + 8, y1 - 3.4, z0, x1 - 8, y1, z1, "-y")
        # layered cornice
        corn = [
            box_at(x0 - 1, y1 - 6, z1 - 8, x1 + 1, y1 + 1.2, z1 - 5),
            box_at(x0 - 2, y1 - 8, z1 - 5.2, x1 + 2, y1 + 2.4, z1 - 2.4),
            box_at(x0 - 1, y1 - 5, z1 - 2.6, x1 + 1, y1 + 0.8, z1),
        ]
        cuts, trim = [], []
        for win in windows:
            cuts.append(box_at(win["x"], y1 - 8, win["z"], win["x"] + win["w"], y1 + 2, win["z"] + win["h"]))
            if win.get("hood") == "fan":
                cuts += screw_sockets(win["x"], y1 - 3.4, win["z"], win["w"], win["h"])
            trim += window_pack("-y", win["x"], y1 - 3.4, win["z"], win["w"], win["h"], win.get("hood", "arch"))
            if flowers:
                trim += flower_box(win["x"] + 2, y1 - 3.4, win["z"] - 12, win["w"] - 4)
        if z1 > L3:
            for px in (230, 303, 379, 448):
                socket = cylinder(radius=2.1, height=10, sections=12)
                socket.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
                socket.apply_translation((px, y1 - 3.8, L3 - 4))
                cuts.append(socket)
        mesh = union([difference(union(body + skin + corn), cuts), *trim])
    else:
        body = [box_at(x1 - 3.4, y0, z0, x1, y1, z1),
                box_at(x1 - 7.5, y0, z0, x1, y0 + 12, z1),
                box_at(x1 - 7.5, y1 - 12, z0, x1, y1, z1)]
        skin = clapboard(x1 - 3.4, y0 + 8, z0, x1, y1 - 8, z1, "+x")
        corn = [
            box_at(x1 - 6, y0 - 1, z1 - 8, x1 + 1.2, y1 + 1, z1 - 5),
            box_at(x1 - 8, y0 - 2, z1 - 5.2, x1 + 2.4, y1 + 2, z1 - 2.4),
        ]
        cuts, trim = [], []
        for win in windows:
            cuts.append(box_at(x1 - 8, win["y"], win["z"], x1 + 2, win["y"] + win["w"], win["z"] + win["h"]))
            trim += window_pack("+x", x1 - 3.4, win["y"], win["z"], win["w"], win["h"])
        mesh = union([difference(union(body + skin + corn), cuts), *trim])
    return cleanup(mesh, face)


def along_y(x, y_a, y_b, z, radius, sections=20):
    """Cylinder spanning y_a to y_b. Used for pockets that must break a face."""
    c = cylinder(radius=radius, height=abs(y_b - y_a), sections=sections)
    c.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    c.apply_translation((x, (y_a + y_b) / 2.0, z))
    return c


def mag_slots(origin, into, zs):
    ax, ay = into
    cuts = []
    for zc in zs:
        c = cylinder(radius=POD_D / 2, height=POD_H + 0.15, sections=14)
        c.apply_transform(rotation_matrix(math.pi / 2, [0, 1, 0] if abs(ax) > 0.5 else [1, 0, 0]))
        c.apply_translation((origin[0] + ax * (SKIN + POD_H / 2), origin[1] + ay * (SKIN + POD_H / 2), zc))
        cuts.append(c)
    z0, z1 = min(zs) - 4, max(zs) + 12
    if abs(ax) > 0.5:
        a = origin[0] + ax * SKIN
        b = origin[0] + ax * (SKIN + POD_H)
        cuts.append(box_at(min(a, b), origin[1] - 3.2, z0, max(a, b), origin[1] + 3.2, z1))
    else:
        a = origin[1] + ay * SKIN
        b = origin[1] + ay * (SKIN + POD_H)
        cuts.append(box_at(origin[0] - 3.2, min(a, b), z0, origin[0] + 3.2, max(a, b), z1))
    return cuts


def screw_sockets(x, y, z, w, h):
    """Blind holes in the street wall for the headed pins. Axis is Y."""
    cuts = []
    for cx in (x - 1.0, x + w + 1.0):
        hole = cylinder(radius=1.05, height=5.2, sections=12)
        hole.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        hole.apply_translation((cx, y + 2.6, z + h * 0.5))
        cuts.append(hole)
    return cuts


def publish_capture(x, y, z, w, h, tag):
    """Separate sash, two keepers, two headed pins. The head, not peg friction, stops withdrawal."""
    def frame_box():
        outer = box_at(x + 1.7, y + 0.95, z + 1.7, x + w - 1.7, y + 3.45, z + h - 1.7)
        inner = box_at(x + 3.7, y + 0.4, z + 3.7, x + w - 3.7, y + 4.0, z + h - 3.7)
        rails = [
            box_at(x + 3.5, y + 0.95, z + h * 0.48, x + w - 3.5, y + 3.45, z + h * 0.48 + 2.2),
            box_at(x + w * 0.33, y + 0.95, z + 3.5, x + w * 0.33 + 1.4, y + 3.45, z + h * 0.48),
            box_at(x + w * 0.66, y + 0.95, z + 3.5, x + w * 0.66 + 1.4, y + 3.45, z + h - 3.5),
        ]
        return cleanup(union([difference(outer, [inner]), *rails]), "sash " + tag)

    def keeper(side):
        cx = x - 1.0 if side < 0 else x + w + 1.0
        body = box_at(cx - 2.2, y + 4.7, z + 8, cx + 2.2, y + 6.5, z + h - 8)
        lip_x0, lip_x1 = (cx, x + 3.4) if side < 0 else (x + w - 3.4, cx)
        lip = box_at(lip_x0, y + 3.85, z + 8, lip_x1, y + 4.95, z + h - 8)
        hole = cylinder(radius=1.35, height=5.4, sections=16)
        hole.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        hole.apply_translation((cx, y + 4.5, z + h * 0.5))
        return cleanup(difference(union([body, lip]), [hole]), "keeper " + tag)

    def pin(cx):
        shaft = cylinder(radius=0.75, height=5.6, sections=12)
        shaft.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        shaft.apply_translation((cx, y + 4.3, z + h * 0.5))
        head = cylinder(radius=1.85, height=1.15, sections=14)
        head.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        head.apply_translation((cx, y + 7.35, z + h * 0.5))
        return cleanup(union([shaft, head]), "pin " + tag)

    publish(f"qa5_sash_{tag}_v5", frame_box(),
            "Removable sash. 0.4 mm behind the front stop. Clear lights, no glass.",
            f"sash-{tag}", "sash", IVORY, explode=[0, -12, 0])
    for side, name in ((-1, "l"), (1, "r")):
        publish(f"qa5_keeper_{tag}_{name}_v5", keeper(side),
                "Room-side keeper. The lip captures the sash. Pull the pin, then this bar, then the sash.",
                f"keeper-{tag}-{name}", "fastener", WOOD_D, explode=[0, 16, 0])
        publish(f"qa5_pin_{tag}_{name}_v5", pin(x - 1.0 if side < 0 else x + w + 1.0),
                "Headed pin. The head is larger than the keeper hole. Friction of the shaft is not the lock. Untested.",
                f"pin-{tag}-{name}", "fastener", BRASS, explode=[0, 24, 0])


def ground_front():
    """Fixed street wall behind the porch. A straight pull would hit the porch,
    so everyday play is the side wall. The door sits in the opening."""
    x0, x1 = MX0 + 2.4, MX1 - 12
    y1 = MY0 - 0.4
    z0, z1 = L1 + 1.0, L2 - 0.2
    body = [
        box_at(x0, y1 - 3.6, z0, x1, y1, z1),
        box_at(x0, y1 - 8, z0, x0 + 14, y1, z1),
        box_at(x1 - 14, y1 - 8, z0, x1, y1, z1),
    ]
    skin = clapboard(x0 + 10, y1 - 3.6, z0 + 2, x1 - 10, y1, z1 - 8, "-y")
    belt = [
        box_at(x0 + 0.4, y1 - 5.2, z1 - 9, x1 - 0.4, y1 + 1.4, z1 - 6.2),
        box_at(x0 + 0.2, y1 - 6.4, z1 - 6.4, x1 - 0.2, y1 + 2.2, z1 - 3.2),
        box_at(x0, y1 - 4.2, z1 - 3.4, x1, y1 + 0.8, z1),
    ]
    # Projecting bay, welded to the street wall. Clears the porch posts.
    bay = box_at(432, y1 - 16, L1 + 16, 488, y1 + 0.6, L1 + 84)
    body.append(bay)
    wins = [{"x": 248, "z": L1 + 24, "w": 34, "h": 60, "hood": "arch"}]
    door = {"x": 368, "z": L1 + 1.2, "w": 34, "h": 76}
    cuts, trim = [], []
    for win in wins:
        cuts.append(box_at(win["x"], y1 - 10, win["z"], win["x"] + win["w"], y1 + 2, win["z"] + win["h"]))
        trim += window_pack("-y", win["x"], y1 - 3.6, win["z"], win["w"], win["h"], win.get("hood", "arch"))
        trim += flower_box(win["x"] + 1, y1 - 3.6, win["z"] - 11, win["w"] - 2)
    cuts.append(box_at(door["x"], y1 - 10, door["z"], door["x"] + door["w"], y1 + 2, door["z"] + door["h"]))
    trim += [
        box_at(door["x"] - 4, y1 - 5.4, door["z"] - 1, door["x"] + door["w"] + 4, y1 + 0.6, door["z"] + 2.2),
        box_at(door["x"] - 3.4, y1 - 4.6, door["z"], door["x"] - 0.4, y1 + 0.4, door["z"] + door["h"] + 2),
        box_at(door["x"] + door["w"] + 0.4, y1 - 4.6, door["z"], door["x"] + door["w"] + 3.4, y1 + 0.4, door["z"] + door["h"] + 2),
        box_at(door["x"] - 6, y1 - 6, door["z"] + door["h"], door["x"] + door["w"] + 6, y1 + 0.8, door["z"] + door["h"] + 4),
    ]
    trim += pediment(door["x"] - 4, y1 - 1, door["z"] + door["h"] + 3.5, door["w"] + 8, "arch")
    # baseboard on the room side of the street wall
    trim.append(box_at(x0 + 6, y1 - 0.6, z0 + 0.4, x1 - 6, y1 + 2.6, z0 + 7.5))
    cuts.append(box_at(442, y1 - 20, L1 + 30, 478, y1 + 2, L1 + 76))
    trim += window_pack("-y", 442, y1 - 16, L1 + 30, 36, 46, "arch")
    mesh = cleanup(union([difference(union(body + skin + belt), cuts), *trim]), "ground front")
    publish("qa5_front_ground_v5", mesh,
            "Ground floor street wall. Fixed, because the porch is in front of it. Flower boxes and the door casing are in the mesh.",
            "front-ground", "structure", SAGE)
    leaf = union([
        box_at(door["x"] + 2.2, y1 - 2.2, door["z"] + 3.4, door["x"] + door["w"] - 2.2, y1 - 1.0, door["z"] + door["h"] - 2.4),
        box_at(door["x"] + 5, y1 - 3.0, door["z"] + 10, door["x"] + door["w"] - 5, y1 - 1.4, door["z"] + 36),
        box_at(door["x"] + 5, y1 - 3.0, door["z"] + 42, door["x"] + door["w"] - 5, y1 - 1.4, door["z"] + 68),
        box_at(door["x"] + door["w"] - 8, y1 - 3.4, door["z"] + 40, door["x"] + door["w"] - 5, y1 - 1.6, door["z"] + 46),
    ])
    publish("qa5_door_v5", cleanup(leaf, "door"),
            "Burgundy door, seated in the opening with clearance. It is not a magnet panel.",
            "door", "trim", WINE)


def facades():
    ground_front()
    # Upper street wall is fixed. The 0.65 mm seam is the belt at the floor line.
    z0, z1 = L2 + 0.45, L3 + 10
    wins = [{"x": x, "z": L2 + 16, "w": 34, "h": 64, "hood": "fan" if x == 324 else "arch"} for x in (248, 324, 400, 462)]
    front = facade((MX0 + 4, MY0 - 4.4, z0, MX1 - 12, MY0 - 0.35, z1), "-y", wins, flowers=True)
    publish("qa5_front_upper_v5", front,
            "Upper street wall. Fixed. Big sash openings. It does not pull off.",
            "front-upper", "structure", SAGE)
    publish_capture(324, MY0 - 3.75, L2 + 16, 34, 64, "upper")
    wins = [{"y": y, "z": z, "w": 34, "h": 50} for z in (L1 + 26, L2 + 22) for y in (148, 220)]
    side = facade((MX1 - 6.0, MY0 + 0.9, L1 + 1.2, MX1 + 0.35, MY1 - 12, plate_top(L2) - 1.2), "+x", wins)
    jamb = box_at(MX1 - 11, MY1 - 20, L1 + 1.0, MX1 - 1.2, JAMB_BACK, plate_top(L2) - 1.0)
    shelf = union([
        box_at(MX1 - 12, JAMB_BACK - 4, L1 + 0.15, MX1 - 3, JAMB_BACK + 0.3, L1 + 6),
        box_at(MX1 - 12, JAMB_BACK - 1, L1 + 0.15, MX1 - 3, JAMB_BACK + 5.5, L1 + FIT_GAP),
    ])
    pin = cylinder(radius=1.35, height=10, sections=16)
    pin.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    pin.apply_translation((MX1 - 8, JAMB_BACK + 1.5, L1 + 36))
    pin2 = cylinder(radius=1.35, height=10, sections=16)
    pin2.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    pin2.apply_translation((MX1 - 8, JAMB_BACK + 1.5, L2 + 36))
    bores = []
    for zc in (L1 + 28, L1 + 52, L1 + 74, L2 + 28, L2 + 52, L2 + 74):
        bores.append(along_y(MX1 - 13, JAMB_BACK - SKIN, MY1 - 12.6, zc, POD_D / 2))
        bores.append(along_y(MX1 - 13, MY1 - 15.2, MY1 - 12.2, zc, 4.3))
    side = cleanup(difference(union([side, jamb, shelf, pin, pin2]), bores), "side")
    publish("qa5_side_v5", side,
            "Right wall, fixed. The rear return is the right jamb. It does not pull off.",
            "side", "structure", SAGE)
    rear_closure()


def rear_closure():
    """The only wall that comes off. One print. Seats 0.45 mm behind the jambs."""
    x0, x1 = MX0 + 8.0, MX1 - 4.0
    y0 = JAMB_BACK + FIT_GAP
    y1 = y0 + 4.6
    z0 = L1 + FIT_GAP
    z1 = plate_top(L2) - FIT_GAP
    body = [
        box_at(x0, y0, z0, x1, y1, z1),
        box_at(x0, y0, z0, x0 + 12, y1 + 0.8, z1),
        box_at(x1 - 12, y0, z0, x1, y1 + 0.8, z1),
    ]
    skin = clapboard(x0 + 14, y0, z0 + 6, x1 - 14, y1, z1 - 6, "+y")
    wins = []
    for z in (L1 + 28, L2 + 24):
        wins.append({"x": x0 + 36, "z": z, "w": 42, "h": 50})
        wins.append({"x": x0 + 150, "z": z, "w": 42, "h": 50})
    cuts, trim = [], []
    for win in wins:
        cuts.append(box_at(win["x"], y0 - 2, win["z"], win["x"] + win["w"], y1 + 3, win["z"] + win["h"]))
        trim += [
            box_at(win["x"] - 3.2, y0 + 1.2, win["z"] - 3.4, win["x"] + win["w"] + 3.2, y1 + 2.2, win["z"] + 1.4),
            box_at(win["x"] - 3.2, y0 + 1.2, win["z"] + win["h"] - 1.2, win["x"] + win["w"] + 3.2, y1 + 2.4, win["z"] + win["h"] + 3.2),
            box_at(win["x"] - 3.4, y0 + 1.2, win["z"], win["x"] + 1.6, y1 + 2.0, win["z"] + win["h"]),
            box_at(win["x"] + win["w"] - 1.6, y0 + 1.2, win["z"], win["x"] + win["w"] + 3.4, y1 + 2.0, win["z"] + win["h"]),
            box_at(win["x"] + win["w"] * 0.46, y0 + 1.4, win["z"] - 0.4, win["x"] + win["w"] * 0.54, y1 + 1.6, win["z"] + win["h"] + 0.6),
        ]
    zs = [L1 + 28, L1 + 52, L1 + 74, L2 + 28, L2 + 52, L2 + 74]
    for sx in (MX0 + 17, MX1 - 13):
        for zc in zs:
            # Skin on the mating face, mouth through the outside of the stile.
            cuts.append(along_y(sx, y0 + SKIN, y1 + 1.5, zc, POD_D / 2))
            cuts.append(along_y(sx, y1 + 0.6, y1 + 2.2, zc, 4.3))
    for sx, zc in ((MX0 + 12, L1 + 36), (MX0 + 12, L2 + 36), (MX1 - 8, L1 + 36), (MX1 - 8, L2 + 36)):
        socket = cylinder(radius=1.75, height=9, sections=16)
        socket.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        socket.apply_translation((sx, y0 + 3.4, zc))
        cuts.append(socket)
    mesh = cleanup(union([difference(union(body + skin), cuts), *trim]), "rear")
    publish("qa5_rear_v5", mesh,
            "Full back, one print, 0.45 mm off the jambs. Magnet mouths open through the stile. Nominal 5.0 x 2.8 mm discs, seat depth 3.2 mm. Not a brace.",
            "rear", "back", SAGE, {"group": "back", "pull": [0, PULL, 0]}, [0, 56, 0],
            {"fit_gap_mm": FIT_GAP, "jamb_back_y": JAMB_BACK,
             "magnet_seat_depth_mm": POD_H, "magnet_diameter_mm": POD_D, "mating_skin_mm": SKIN})
    magnet_caps(y0, y1)


def magnet_caps(y0, y1):
    """Caps cover the open mouths. Bosses stop short of the 3.2 mm disc seat. Clearance, not a tested snap."""
    zs = [L1 + 28, L1 + 52, L1 + 74, L2 + 28, L2 + 52, L2 + 74]
    def cap(x, zs_here, y_boss0, y_boss1, y_plate0, y_plate1, tag):
        bosses = [along_y(x, y_boss0, y_boss1, z, 2.05) for z in zs_here]
        heads = [along_y(x, y_plate0, y_plate1, z, 3.05) for z in zs_here]
        ya, yb = min(y_plate0, y_plate1), max(y_plate0, y_plate1)
        spine = box_at(x - 1.1, ya + 0.25, min(zs_here) - 1, x + 1.1, yb - 0.25, max(zs_here) + 1)
        publish(f"qa5_cap_{tag}_v5", cleanup(union([spine, *heads, *bosses]), "cap " + tag),
                "Covers magnet mouths. The boss leaves the 3.2 mm seat clear. Pull the cap straight off to remove a disc. Untested.",
                f"cap-{tag}", "fastener", IVORY, explode=[0, 14, 0])
    # Panel caps sit outside the stile. Disc zone ends at y1.
    cap(MX0 + 17, zs, y1 + 0.25, y1 + 1.15, y1 + 0.95, y1 + 1.85, "back-l")
    cap(MX1 - 13, zs, y1 + 0.25, y1 + 1.15, y1 + 0.95, y1 + 1.85, "back-r")
    # Jamb caps sit on the room face. Disc zone begins 3.2 mm before the skin.
    disc = JAMB_BACK - SKIN - POD_H
    mouth = MY1 - 18
    def one(x, z, y_boss0, y_boss1, y_plate0, y_plate1, tag):
        boss = along_y(x, y_boss0, y_boss1, z, 2.05)
        head = along_y(x, y_plate0, y_plate1, z, 3.05)
        publish(f"qa5_cap_{tag}_v5", cleanup(union([head, boss]), "cap " + tag),
                "One magnet cap. Boss stops at the 3.2 mm seat. Clearance fit, untested.",
                f"cap-{tag}", "fastener", IVORY, explode=[0, 10, 0])
    for floor, side in ((L1, "a"), (L2, "b")):
        for i, z in enumerate((floor + 28, floor + 52, floor + 74)):
            one(MX0 + 17, z, disc - 0.2, mouth - 1.3, mouth - 2.15, mouth - 1.05, f"jl{side}{i}")
            one(MX1 - 13, z, disc - 0.2, MY1 - 13.6, MY1 - 14.9, MY1 - 13.3, f"jr{side}{i}")


def cone_courses():
    """Small slate courses on the cone flats. Proud a fraction of a millimetre."""
    cached()
    pieces = []
    base_z = plate_top(L3) + GAP
    i = 0
    z = base_z + 3
    while z < base_z + CONE_H * 0.86:
        t = (z - base_z) / CONE_H
        vert = (TR - 4) * (1.0 - t)
        ap = vert * math.cos(math.pi / 8)
        flat = 2 * vert * math.sin(math.pi / 8)
        step = 3.4
        count = max(1, int(flat / step))
        for k in range(8):
            ang = math.radians(45 + k * 45)
            normal = np.array([math.cos(ang), math.sin(ang), 0.0])
            tangent = np.array([-math.sin(ang), math.cos(ang), 0.0])
            for j in range(count):
                off = (j - (count - 1) / 2.0) * step + (step * 0.5 if i % 2 else 0.0)
                if abs(off) > flat / 2 - 1.4:
                    continue
                origin = np.array([TX, TY, z]) + normal * (ap - 0.16) + tangent * off
                up = np.cross(normal, tangent)
                pieces.append(_xform(TINY, origin, tangent, up, normal))
        z += 2.6
        i += 1
    return pieces


def on_facet(angle, radius, z, sx, sy, sz, dt=0.0, dz=0.0):
    a = math.radians(angle)
    n = np.array([math.cos(a), math.sin(a), 0.0])
    t = np.array([-math.sin(a), math.cos(a), 0.0])
    origin = np.array([TX, TY, z]) + n * radius + t * dt + np.array([0.0, 0.0, dz])
    return _xform(box((sx, sy, sz)), origin, t, n, np.array([0.0, 0.0, 1.0]))


APO = TR * math.cos(math.pi / 8)


def facet_trim(angle, z, w, h):
    """Casing and pediment on one turret flat. The flat sits at the apothem, not the vertex radius."""
    sill = on_facet(angle, APO - 0.3, z - 2.2, w + 8, 3.6, 3.8)
    head = on_facet(angle, APO - 0.3, z + h + 0.7, w + 8, 3.6, 3.6)
    left = on_facet(angle, APO - 0.3, z + h / 2, 3.2, 3.4, h + 2, dt=-(w / 2 + 1.2))
    right = on_facet(angle, APO - 0.3, z + h / 2, 3.2, 3.4, h + 2, dt=(w / 2 + 1.2))
    a = math.radians(angle)
    n = np.array([math.cos(a), math.sin(a), 0.0])
    t = np.array([-math.sin(a), math.cos(a), 0.0])
    peak = hull([
        (-w / 2 - 2, 0.8, 0), (w / 2 + 2, 0.8, 0), (0, 0.8, 9),
        (-w / 2 - 2, -2.2, 0), (w / 2 + 2, -2.2, 0), (0, -2.2, 9),
    ])
    origin = np.array([TX, TY, z + h + 2.0]) + n * APO
    ped = _xform(peak, origin, t, n, np.array([0.0, 0.0, 1.0]))
    return [sill, head, left, right, ped]


def facet_hole(angle, z, w, h):
    return on_facet(angle, APO - 2.0, z + h / 2, w, 16, h)


def roofs():
    # The street gable is the front of the attic. The main slope sits
    # behind it, so the triangle reads instead of a roof slab.
    y_r = (MY0 + MY1) / 2
    z_r = RIDGE
    y_e, z_e = MY0 + 1.0, EAVE + 8
    gx0, gx1 = 292.0, 468.0
    gy0, gz0, gz1 = MY0 - 42, L3 + 4, RIDGE + 24
    xmid = (gx0 + gx1) / 2
    front = slope_slab(MX0 + 6, MX1 - 8, y_e, z_e, y_r - 3.0, z_r)
    shingles = shingle_field(MX0 + 14, MX1 - 16, y_e, z_e, y_r - 3.0, z_r, "fish")
    # Cheeks of the gable, running back into the main slope so they are one roof.
    left = hull([
        (gx0 + 2, gy0 + 6.2, gz0 + 4), (gx0 + 2, 150, z_e + 18),
        (xmid - 1, gy0 + 6.2, gz1 - 6), (xmid - 1, 150, z_r - 4),
        (gx0 + 8, gy0 + 10, gz0), (gx0 + 8, 146, z_e + 12),
        (xmid - 4, gy0 + 10, gz1 - 14), (xmid - 4, 146, z_r - 12),
    ])
    right = hull([
        (gx1 - 2, gy0 + 6.2, gz0 + 4), (gx1 - 2, 150, z_e + 18),
        (xmid + 1, gy0 + 6.2, gz1 - 6), (xmid + 1, 150, z_r - 4),
        (gx1 - 8, gy0 + 10, gz0), (gx1 - 8, 146, z_e + 12),
        (xmid + 4, gy0 + 10, gz1 - 14), (xmid + 4, 146, z_r - 12),
    ])
    def z_at(y):
        t = (y - y_e) / (y_r - y_e)
        return z_e + t * (z_r - z_e)
    zc = z_at(MY0 + 8)
    fascia = box_at(MX0 + 12, y_e - 1.2, z_e - 7, MX1 - 14, y_e + 3.5, z_e + 1.2)
    ridge = box_at(MX0 + 24, y_r - 16, z_r - 8, gx0 - 6, y_r - 3.4, z_r + 2.4)
    crest = [fascia, ridge, box_at(MX0 + 20, MY0 + 4, zc - 2.4, gx0 - 8, MY0 + 10, zc + 2.2)]
    cx = MX0 + 40
    while cx < gx0 - 20:
        crest.append(move(spindle(18), cx, y_r - 8, z_r - 2))
        cx += 16
    crest.append(box_at(MX0 + 36, y_r - 12, z_r + 14, gx0 - 16, y_r - 6, z_r + 17))
    # Small dormer on the slope left of the street gable. Its base enters the slab.
    zd = z_at(150)
    dormer = [
        box_at(230, 144, zd - 8, 276, 176, zd + 26),
        hull([
            (228, 146, zd + 18), (278, 146, zd + 18), (253, 146, zd + 40),
            (228, 174, zd + 16), (278, 174, zd + 16), (253, 174, zd + 36),
        ]),
    ]
    dormer_win = box_at(244, 138, zd + 2, 262, 152, zd + 20)
    front_roof = cleanup(difference(union([front, left, right, *crest, *shingles, *dormer]), [dormer_win]), "front roof")
    publish("qa5_roof_front_v5", front_roof,
            "Front slope and the gable cheeks. Fish-scale courses overlap and the noses stay proud.",
            "roof-front", "roof", SLATE, {"group": "roof", "lift": [0, 0, 48], "park": [0, -40, 28]},
            [0, -24, 50], {"plate_top": EAVE - GAP, "seat_z": EAVE})
    face = hull([
        (gx0 + 4, gy0, gz0), (gx1 - 4, gy0, gz0), (xmid, gy0, gz1),
        (gx0 + 4, gy0 + 5.2, gz0), (gx1 - 4, gy0 + 5.2, gz0), (xmid, gy0 + 5.2, gz1),
    ])
    opening = box_at(xmid - 15, gy0 - 3, gz0 + 28, xmid + 15, gy0 + 8, gz0 + 86)
    face = difference(face, [opening])
    gx, gz = xmid, gz0
    gable_trim = [
        plate_xz(arch_band(gx - 22, gz + 74, 44, 16, 3.2), gy0 + 1.6, 3.0),
        box_at(gx - 18, gy0 - 1.2, gz + 70, gx + 18, gy0 + 2.2, gz + 76),
        box_at(gx - 1.2, gy0 - 0.8, gz + 30, gx + 1.2, gy0 + 2.0, gz + 84),
        box_at(gx - 14, gy0 - 0.8, gz + 50, gx + 14, gy0 + 2.0, gz + 53.2),
        box_at(gx - 20, gy0 - 1.4, gz + 22, gx + 20, gy0 + 2.4, gz + 28),
    ]
    for px in np.linspace(gx0 + 36, gx1 - 36, 7):
        gable_trim.append(box_at(px - 3.2, gy0 - 7, gz0 - 10, px + 3.2, gy0 + 2.2, gz0 + 4))
        gable_trim.append(box_at(px - 4.6, gy0 - 4, gz0 - 2, px + 4.6, gy0 + 1.6, gz0 + 3))
    finial = revolve([[0, 0], [5.2, 0], [3.6, 4], [1.3, 16], [0.45, 26], [0, 28]], 16)
    finial.apply_translation((xmid, gy0 + 2.2, gz1 - 10))
    gable_trim.append(finial)
    board = bargeboard(gx1 - gx0 - 20)
    board.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    board.apply_translation(-board.bounds[0])
    board.apply_translation((gx0 + 10, gy0 - 0.4, gz0 - 1))
    bird = move(owl(), xmid, gy0 + 1.4, gz0 + 26)
    left_rake = rake_board(gx0 + 10, gz0 + 8, xmid - 6, gz1 - 10, gy0 - 0.8, 1)
    right_rake = rake_board(gx1 - 10, gz0 + 8, xmid + 6, gz1 - 10, gy0 - 0.8, -1)
    publish("qa5_gable_v5", cleanup(union([face, *gable_trim, board, bird, left_rake, right_rake]), "gable"),
            "Street gable. Arched attic sash, scroll verge, owl. The piercings go through.",
            "gable", "structure", SAGE, {"group": "roof", "lift": [0, 0, 48], "park": [0, -46, 24]},
            [0, -30, 40])
    rear = slope_slab(MX0 + 8, MX1 - 8, MY1 + 14, EAVE - 16, y_r + 3.0, RIDGE)
    def skip_chimney(origin):
        return 442.0 < origin[0] < 492.0 and 206.0 < origin[1] < 252.0
    rear_sh = shingle_field(MX0 + 8, MX1 - 8, MY1 + 14, EAVE - 16, y_r + 3.0, RIDGE, "fish", skip_chimney)
    bricks = []
    bz = RIDGE - 36
    while bz < RIDGE + 18:
        bricks += [
            box_at(448, 214, bz, 484, 218.2, bz + 2.4),
            box_at(448, 242, bz, 484, 246.2, bz + 2.4),
            box_at(448, 218, bz, 452.2, 242, bz + 2.4),
            box_at(479.8, 218, bz, 484, 242, bz + 2.4),
        ]
        bz += 5.0
    chim = union([
        box_at(450, 216, RIDGE - 40, 482, 244, RIDGE + 24),
        box_at(444, 210, RIDGE + 22, 488, 250, RIDGE + 32),
        box_at(456, 222, RIDGE + 30, 468, 236, RIDGE + 52),
        box_at(470, 224, RIDGE + 30, 482, 238, RIDGE + 46),
        *bricks,
    ])
    # Wide center opening so the attic floor and the upper stair are visible from the rear.
    soffit = box_at(324, MY1 - 12, 120, 470, MY1 + 42, L3 + 40)
    rear_roof = cleanup(difference(union([rear, chim, *rear_sh]), [soffit]), "rear roof")
    publish("qa5_roof_rear_v5", rear_roof, "Rear slope, fish-scale courses, chimney. Center soffit is open over the attic.",
            "roof-rear", "roof", SLATE, {"group": "roof", "lift": [0, 0, 48], "park": [0, 28, 28]},
            [0, 20, 50], {"plate_top": EAVE - GAP, "seat_z": EAVE})
    cone = revolve([[0, 0], [TR - 4, 0], [1.8, CONE_H], [0, CONE_H]], 8)
    cone = move(cone, TX, TY, plate_top(L3) + GAP)
    cone.apply_transform(rotation_matrix(math.radians(22.5), [0, 0, 1], [TX, TY, plate_top(L3)]))
    cap = cleanup(prism(octagon(TX, TY, TR - 16), plate_top(L3) - 4, plate_top(L3) + 0.15), "cap")
    publish("qa5_turret_cap_v5", cap, "Plate under the cone.", "turret-cap", "structure", PLASTER, explode=[-8, 0, 20])
    scales = cone_courses()
    tip = revolve([[0, 0], [4.4, 0], [2.6, 6], [0.7, 18], [0, 22]], 16)
    tip.apply_translation((TX, TY, plate_top(L3) + GAP + CONE_H - 4))
    publish("qa5_roof_turret_v5", cleanup(union([cone, tip, *scales]), "cone"),
            "Octagonal cone with a course of scallops on each flat.", "roof-turret", "roof", SLATE,
            {"group": "roof", "lift": [0, 0, 56], "park": [-28, -20, 24]}, [-12, -16, 40],
            {"plate_top": plate_top(L3), "seat_z": plate_top(L3) + GAP})
    def turret_shell(z0, z1, wins, name):
        shell = prism(octagon(TX, TY, TR), z0, z1)
        holes = [prism(octagon(TX, TY, TR - 4.6), z0 - 1, z1 + 1), box_at(MX0 - 0.35, 0, z0 - 1, 900, 500, z1 + 1)]
        holes += [facet_hole(ang, z, 20, 42) for ang, z in wins]
        bands = []
        # Belts skip the flat against the house, so the cut there is not a shaved sliver.
        width = 2 * TR * math.sin(math.pi / 8) + 1.2
        def add_belt(z_a, z_b, proud):
            for ang in (45, 90, 135, 180, 225, 270, 315):
                bands.append(on_facet(ang, APO - 0.2, (z_a + z_b) / 2, width, proud + 1.4, z_b - z_a))
        # Three molded belts, not a stack of hairline rings.
        add_belt(z0 + 6, z0 + 12, 1.5)
        add_belt(z0 + 10.2, z0 + 13.0, 0.7)
        add_belt(z1 - 14, z1 - 6, 1.6)
        add_belt(z1 - 8.5, z1 - 5.2, 0.7)
        trim = []
        for ang, wz in wins:
            trim += facet_trim(ang, wz, 20, 42)
        mesh = difference(union([shell, *bands]), holes)
        return cleanup(union([mesh, *trim]), name)

    street = (180, 225, 270, 315)
    publish("qa5_turret_loft_v5", turret_shell(L3 + 0.2, plate_top(L3) + 0.1, [(a, L3 + 18) for a in street], "loft"),
            "Turret loft, with cased windows on the street flats.", "turret-loft", "structure", SAGE, explode=[-10, -6, 16])
    lower_wins = [(a, L1 + 30) for a in street] + [(a, L2 + 18) for a in street]
    publish("qa5_turret_v5", turret_shell(L1 + 0.6, L3 - 0.2, lower_wins, "turret"),
            "Octagonal turret, two storeys, clapboard, belt courses, and cased windows.",
            "turret", "structure", SAGE, explode=[-14, -10, 0])


def standing_bracket():
    raw = bracket_mesh()
    raw.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    raw.apply_translation((-float(raw.bounds[0][0]), -float(raw.bounds[0][1]), -float(raw.bounds[0][2])))
    return raw


def seg_bar(p, q, z0, z1, half=1.8):
    d = np.array(q, float) - np.array(p, float)
    n = np.array([-d[1], d[0]], float)
    n = n / np.linalg.norm(n) * half
    a, b = np.array(p, float), np.array(q, float)
    return hull([
        (a[0] + n[0], a[1] + n[1], z0), (a[0] - n[0], a[1] - n[1], z0),
        (b[0] + n[0], b[1] + n[1], z0), (b[0] - n[0], b[1] - n[1], z0),
        (a[0] + n[0], a[1] + n[1], z1), (a[0] - n[0], a[1] - n[1], z1),
        (b[0] + n[0], b[1] + n[1], z1), (b[0] - n[0], b[1] - n[1], z1),
    ])


def rail_run(p, q, z=None):
    z = BASE + 3 if z is None else z
    bits = [seg_bar(p, q, z, z + 3.4), seg_bar(p, q, z + 22, z + 26)]
    a, b = np.array(p, float), np.array(q, float)
    length = float(np.linalg.norm(b - a))
    step = 11.0
    n = max(1, int(length / step))
    for i in range(1, n):
        t = i / n
        pos = a + (b - a) * t
        bits.append(move(SPINDLE, float(pos[0]), float(pos[1]), z + 1.2))
    return bits


def ang_out(x, y):
    return math.degrees(math.atan2(y - TY, x - TX))


def place_bracket(x, y, z, degrees):
    raw = standing_bracket()
    raw.apply_transform(rotation_matrix(math.radians(degrees), [0, 0, 1]))
    raw.apply_translation((x, y, z))
    return raw


def porch():
    cached()
    z_beam = L2 - 18
    col_h = (z_beam + 5) - BASE
    # Posts outside the turret, on the street side of the octagon.
    ring = []
    for ang in (200, 245, 290):
        a = math.radians(ang)
        ring.append((TX + 84 * math.cos(a), TY + 84 * math.sin(a)))
    front_posts = [(250, 36), (330, 32), (410, 32), (488, 36)]
    parts = []
    for x, y in ring:
        parts.append(move(column(col_h), x, y, BASE + 1.1))
        parts.append(place_bracket(x, y, z_beam - 16, ang_out(x, y)))
    for i in range(len(ring) - 1):
        parts += rail_run(ring[i], ring[i + 1])
        parts.append(seg_bar(ring[i], ring[i + 1], z_beam, z_beam + 7, half=4.2))
    # Close the ring visually toward the front run with a beam to the corner.
    corner = (232, 78)
    parts.append(move(column(col_h), *corner, BASE + 1.1))
    parts.append(place_bracket(*corner, z_beam - 16, -90))
    parts += rail_run(ring[-1], corner)
    parts.append(seg_bar(ring[-1], corner, z_beam, z_beam + 7, half=4.2))
    publish("qa5_porch_turret_v5", cleanup(union(parts), "porch turret"),
            "Octagonal corner porch. Turned columns, cyma brackets, spindle rail. It stays during play.",
            "porch-turret", "porch", IVORY, explode=[-16, -10, 0])
    parts = []
    for x, y in front_posts:
        parts.append(move(column(col_h), x, y, BASE + 1.1))
        parts.append(place_bracket(x, y, z_beam - 16, -90))
    parts += rail_run(front_posts[0], front_posts[-1])
    parts.append(box_at(front_posts[0][0] - 4, 24, z_beam, front_posts[-1][0] + 6, 48, z_beam + 8))
    parts.append(box_at(front_posts[0][0] - 2, 18, z_beam + 1, front_posts[-1][0] + 4, 30, z_beam + 6))
    dx = front_posts[0][0] + 14
    while dx < front_posts[-1][0] - 10:
        parts.append(box_at(dx, 30, z_beam - 4.2, dx + 3.4, 44, z_beam + 1.6))
        dx += 9.0
    # Steps reach the middle post so the flight is one solid with the porch.
    parts += [
        box_at(378, 2, BASE + 0.4, 442, 14, BASE + 6),
        box_at(382, 8, BASE + 6, 438, 20, BASE + 11),
        box_at(386, 14, BASE + 11, 434, 40, BASE + 17),
    ]
    publish("qa5_porch_front_v5", cleanup(union(parts), "porch front"),
            "Front porch across the main block, with the steps. It stays during play.",
            "porch-front", "porch", IVORY, explode=[0, -18, 0])
    # Two porch roofs, each on its own beam, seated with a gap.
    proof = slope_slab(246, 500, 26, z_beam + 16, 96, z_beam + 28)
    proof_sh = shingle_field(258, 488, 32, z_beam + 18, 90, z_beam + 26)
    publish("qa5_porch_roof_v5", cleanup(union([proof, *proof_sh]), "porch roof"),
            "Front porch roof with scalloped shingles. Bears on the beam.",
            "porch-roof", "roof", SLATE, {"group": "roof", "lift": [0, 0, 40]},
            [0, -20, 24], {"plate_top": z_beam + 8, "seat_z": z_beam + 8 + GAP})
    z0 = z_beam + 7 + GAP
    outer = octagon(TX, TY, 94)
    inner = octagon(TX, TY, 64)
    skirt = hull([*( (*p, z0) for p in outer ), *( (*p, z0 + 4.5) for p in outer ), *( (*p, z0 + 16) for p in inner )])
    skirt = difference(skirt, [
        prism(octagon(TX, TY, TR + 1.4), z0 - 2, z0 + 22),
        box_at(MX0 - 0.4, 60, z_beam, 900, 400, z_beam + 46),
    ])
    publish("qa5_porch_skirt_v5", cleanup(skirt, "skirt"),
            "Faceted roof around the turret porch.",
            "porch-skirt", "roof", SLATE, {"group": "roof", "lift": [0, 0, 40]},
            [-12, -8, 20], {"plate_top": z_beam + 7, "seat_z": z_beam + 7 + GAP})
    # Two lanterns on the fixed porch, beside the door posts.
    lantern = cleanup(union([
        box_at(0, 0, 2, 8, 8, 14),
        box_at(1.4, -1.2, 4, 6.6, 1.2, 11),
        revolve([[0, 0], [5, 0], [1.2, 3], [0, 3]], 8),
    ]), "lantern")
    name = "qa5_lantern_v5"
    local = lantern.copy()
    o = local.bounds[0].copy()
    local.apply_translation(-o)
    add_part(name, local, "Porch lantern on a fixed post. Not on a magnetic wall.")
    for iid, x, y in (("lantern-a", 292, 34), ("lantern-b", 472, 34)):
        world = move(lantern, x, y, BASE + 48)
        INSTANCES.append({"id": iid, "part": name, "role": "light", "color": BRASS, "motion": None,
                          "explode_mm": [0, -8, 6], "world": world, "place": [float(v) for v in world.bounds[0]], "extra": {}})
        FIXTURES.append({"id": iid, "kind": "lantern", "room": "porch", "x": x, "y": y, "z": BASE + 52, "storey": 1, "circuit": "exterior"})


def stair_flight(spec, open_positive_x=True):
    x0, x1 = spec["x0"], spec["x1"]
    y0, y1 = spec["y0"], spec["y1"]
    z0 = spec["z"] + 1.4
    parts = []
    # Sloped stringers, thin, so the profile reads as a stair.
    def stringer(x):
        z_land = z0 + F2F
        return hull([
            (x, y0, z0 + 2), (x + 4.5, y0, z0 + 2),
            (x, y1, z_land - 4), (x + 4.5, y1, z_land - 4),
            (x, y0, z0 + 16), (x + 4.5, y0, z0 + 16),
            (x, y1, z_land + 8), (x + 4.5, y1, z_land + 8),
        ])
    parts += [stringer(x0), stringer(x1 - 4.5)]
    for i in range(RISES - 1):
        z = z0 + (i + 1) * RISE
        if spec["up"] > 0:
            yb = y0 + (i + 1) * TREAD
            ya = yb - TREAD - 1.2
        else:
            ya = y1 - (i + 1) * TREAD
            yb = ya + TREAD + 1.2
        parts.append(box_at(x0 + 0.4, ya, z - 2.4, x1 - 0.4, yb, z))
        parts.append(box_at(x0 + 1.2, yb - 1.6, z - RISE, x1 - 1.2, yb, z))
        parts.append(move(SPINDLE, x1 - 2.4, (ya + yb) / 2, z - 2.0))
    rail_z0 = z0 + 26
    rail_z1 = z0 + F2F + 6
    parts.append(hull([
        (x1 - 4.2, y0 + 2, rail_z0), (x1 - 0.8, y0 + 2, rail_z0),
        (x1 - 4.2, y1 - 2, rail_z1), (x1 - 0.8, y1 - 2, rail_z1),
        (x1 - 4.2, y0 + 2, rail_z0 + 8), (x1 - 0.8, y0 + 2, rail_z0 + 8),
        (x1 - 4.2, y1 - 2, rail_z1 + 8), (x1 - 0.8, y1 - 2, rail_z1 + 8),
    ]))
    parts.append(move(revolve([[0, 0], [3.6, 0], [4.2, 3], [2.6, 8], [2.4, 70], [3.4, 78], [0, 80]], 10), x0 + 2.2, y0 + 6, z0))
    return union(parts)


def stairs():
    cached()
    publish("qa5_stair_lower_v5", cleanup(stair_flight(S1), "lower"),
            "Open stair, entry to the first floor, with a spindle rail.", "stair-lower", "stair", WOOD_D, explode=[20, 0, 6])
    publish("qa5_stair_upper_v5", cleanup(stair_flight(S2), "upper"),
            "Open stair, first floor to the attic, with a spindle rail.", "stair-upper", "stair", WOOD_D, explode=[16, 0, 14])


def ornament():
    """Fitted trim. Separate solids, 0.4 mm off the siding, not fused into it."""
    length = (MX1 - 16) - (MX0 + 10)
    courses = [
        (0, -2.4, 0, 2.0),
        (1.6, -4.8, -0.4, 4.2),
        (3.8, -7.6, 0.2, 6.8),
        (6.2, -10.6, 1.0, 9.4),
        (8.8, -13.0, 2.2, 11.4),
    ]
    layers = [box_at(0, y0, z0, length, y1, z1) for z0, y0, y1, z1 in courses]
    bar = cleanup(union(layers), "cornice")
    pegs = []
    for px in (230, 303, 379, 448):
        peg = cylinder(radius=1.15, height=7.4, sections=12)
        peg.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        peg.apply_translation((px - (MX0 + 10), 3.4, 4.0))
        pegs.append(peg)
    bar = cleanup(union([bar, *pegs]), "cornice")
    # Back of the moulding is local y = 0. Siding stands just behind that.
    publish("qa5_cornice_v5", move(bar, MX0 + 10, MY0 - 11.0, L3 - 8),
            "Layered crown. Four pegs enter the sockets in the upper wall. Radial clearance is 0.45 mm. Untested.",
            "cornice", "trim", IVORY)
    w = 48.0
    crown = cleanup(union([
        box_at(0, -3.2, 0, w, 0, 2.6),
        hull([
            (1, 0, 2.2), (w - 1, 0, 2.2), (w / 2, 0, 12),
            (1, -2.6, 2.2), (w - 1, -2.6, 2.2), (w / 2, -2.6, 12),
        ]),
        box_at(w * 0.2, -2.2, 4.5, w * 0.8, -0.4, 6.2),
    ]), "crown")
    for i, x in enumerate((248, 324, 400, 462)):
        world = move(crown, x - 7, MY0 - 9.6, L2 + 78)
        if i == 0:
            publish("qa5_crown_v5", world, "Window crown. One print, placed over each upper sash.",
                    "crown-0", "trim", IVORY)
        else:
            INSTANCES.append({
                "id": f"crown-{i}", "part": "qa5_crown_v5", "role": "trim", "color": IVORY,
                "motion": None, "explode_mm": [0, -6, 4], "world": world,
                "place": [float(v) for v in world.bounds[0]], "extra": {},
            })


def rooms():
    def bed():
        posts = []
        for px, py in ((6, 10), (42, 10), (6, 70), (42, 70)):
            posts.append(move(revolve([
                [0, 0], [2.3, 0], [2.7, 2], [1.7, 8], [1.55, 30], [2.3, 36], [1.4, 38], [0, 38],
            ], 10), px, py, 0))
        crest = plate_xz(arch_band(4, 30, 40, 12, 3.2), 74, 6)
        return cleanup(union([
            box_at(4, 6, 8, 44, 72, 14),
            box_at(2, 64, 12, 46, 78, 34),
            crest,
            box_at(8, 58, 14, 22, 70, 20),
            box_at(26, 58, 14, 40, 70, 20),
            *posts,
        ]), "bed")
    def basin():
        bowl = cylinder(radius=5.5, height=3.2, sections=16)
        bowl.apply_translation((7, 7, 18))
        return cleanup(union([
            box_at(4, 4, 0, 10, 10, 17),
            bowl,
            box_at(2, 2, 16.2, 12, 12, 18.2),
        ]), "basin")

    def cabinet():
        body = union([
            box_at(0, 0, 0, 60, 18, 34),
            box_at(2, -0.8, 4, 28, 1.2, 30),
            box_at(32, -0.8, 4, 58, 1.2, 30),
            box_at(0, 6, 30, 60, 16, 36),
            box_at(40, 2, 34, 58, 14, 50),
        ])
        sink = cylinder(radius=5.2, height=8, sections=16)
        sink.apply_translation((18, 9, 34))
        return cleanup(difference(body, [sink]), "cabinet")
    def table():
        return cleanup(union([
            box_at(0, 0, 18, 40, 24, 20),
            move(revolve([[0, 0], [1.6, 0], [1.6, 18], [0, 18]], 8), 4, 4, 0),
            move(revolve([[0, 0], [1.6, 0], [1.6, 18], [0, 18]], 8), 36, 4, 0),
            move(revolve([[0, 0], [1.6, 0], [1.6, 18], [0, 18]], 8), 4, 20, 0),
            move(revolve([[0, 0], [1.6, 0], [1.6, 18], [0, 18]], 8), 36, 20, 0),
        ]), "table")
    def rug(w, d):
        return cleanup(box_at(0, 0, 0, w, d, 0.8), "rug")
    def sofa():
        parts = [box_at(3, 2, 0, 59, 22, 5)]
        parts.append(hull([
            (8, 3, 4.6), (54, 3, 4.6), (54, 16, 4.6), (8, 16, 4.6),
            (10, 4, 12), (31, 4, 13.2), (52, 4, 12), (52, 15, 10.4), (10, 15, 10.4),
        ]))
        for x in (0.0, 56.0):
            parts.append(box_at(x, 1, 4, x + 6, 20, 15))
            roll = cylinder(radius=3.1, height=12, sections=14)
            roll.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
            roll.apply_translation((x + 3, 6, 15))
            parts.append(roll)
        for t in np.linspace(0, 1, 6):
            px = 6 + t * 50
            parts.append(box_at(px - 5, 15.5, 8, px + 5, 22, 28))
        crest = cylinder(radius=1.8, height=50, sections=12)
        crest.apply_transform(rotation_matrix(math.pi / 2, [0, 1, 0]))
        crest.apply_translation((31, 20.5, 28))
        parts.append(crest)
        return cleanup(union(parts), "sofa")
    def chair():
        legs = []
        for px, py in ((-8.2, -6.6), (8.2, -6.6), (-8.2, 6.6), (8.2, 6.6)):
            legs.append(move(revolve([
                [0, 0], [1.55, 0], [1.05, 1.2], [1.45, 2.4], [0.75, 8], [1.35, 11],
                [0.7, 14], [1.15, 16.5], [0, 16.5],
            ], 12), px, py, 0))
        seat = hull([
            (-9.5, -8, 16.2), (9.5, -8, 16.2), (9.5, 7.2, 16.2), (-9.5, 7.2, 16.2),
            (-8.6, -7, 19.4), (8.6, -7, 19.4), (8.2, 6.4, 18.6), (-8.2, 6.4, 18.6),
            (0, 0, 20.4),
        ])
        t = np.linspace(0, 2 * math.pi, 48)
        oval = Polygon(np.column_stack([7.4 * np.cos(t), 30 + 9.2 * np.sin(t)]))
        inner = Polygon(np.column_stack([5.6 * np.cos(t), 30 + 7.2 * np.sin(t)]))
        back = plate_xz(oval.difference(inner), 8.2, 2.6)
        cameo = plate_xz(inner.buffer(0.2), 7.6, 1.4)
        posts = [
            move(revolve([[0, 0], [1.15, 0], [0.85, 4], [1.2, 10], [0.7, 18], [1.05, 22], [0, 22]], 10), -8.2, 6.6, 16),
            move(revolve([[0, 0], [1.15, 0], [0.85, 4], [1.2, 10], [0.7, 18], [1.05, 22], [0, 22]], 10), 8.2, 6.6, 16),
        ]
        rail = cylinder(radius=0.7, height=16.4, sections=10)
        rail.apply_transform(rotation_matrix(math.pi / 2, [0, 1, 0]))
        rail.apply_translation((0, -6.6, 7))
        return cleanup(union([
            *legs, seat, back, cameo, *posts, rail,
            box_at(-9, -7.4, 13.5, 9, -6.4, 17.2),
            box_at(-9, 6.2, 13.5, 9, 7.4, 17.2),
        ]), "chair")
    pieces = [
        ("qa5_bed_v5", bed(), "Bed with pillows.", "bed", (236, 168, L2 + 0.6)),
        ("qa5_stand_v5", cleanup(union([
            box_at(0, 0, 0, 16, 14, 16),
            box_at(1.2, -0.6, 3, 14.6, 1.2, 13),
        ]), "stand"), "Nightstand beside the bed.", "stand", (292, 196, L2 + 0.6)),
        ("qa5_bedrug_v5", rug(40, 22), "Rug at the foot of the bed.", "bedrug", (242, 146, L2 + 0.4)),
        ("qa5_cabinet_v5", cabinet(), "Kitchen cabinets and sink.", "cabinet", (430, 258, L1 + 0.5)),
        ("qa5_table_v5", table(), "Parlor table.", "table", (250, 168, L1 + 1.4)),
        ("qa5_rug_v5", rug(54, 38), "Parlor rug.", "rug", (242, 158, L1 + 0.3)),
        ("qa5_sofa_v5", sofa(), "Parlor sofa.", "sofa", (230, 220, L1 + 0.5)),
        ("qa5_chair_v5", chair(), "Parlor chair.", "chair", (320, 175, L1 + 0.5)),
        ("qa5_trunk_v5", cleanup(box_at(0, 0, 0, 36, 18, 14), "trunk"), "Attic trunk.", "trunk", (300, 200, L3 + 0.8)),
        ("qa5_tub_v5", cleanup(union([
            box_at(0, 0, 0, 32, 16, 12),
            box_at(2, 2, 8, 30, 14, 14),
        ]), "tub"), "Bath tub.", "tub", (456, 132, L2 + 0.6)),
        ("qa5_basin_v5", basin(), "Bath basin on a pedestal.", "basin", (478, 188, L2 + 0.6)),
        ("qa5_cot_v5", cleanup(union([
            box_at(2, 2, 6, 34, 18, 12),
            box_at(0, 14, 8, 36, 20, 22),
        ]), "cot"), "Attic cot, on the open side of the attic.", "cot", (340, 160, L3 + 0.8)),
    ]
    for name, mesh, note, iid, at in pieces:
        color = WINE if iid in ("rug", "bedrug") else WOOD
        publish(name, move(mesh, *at), note, iid, "furniture", color, explode=[0, 0, 8])


def service():
    shell = box_at(0, 0, 0, 158, 100, 40)
    void = box_at(4, 6, 6, 154, 92, 36)
    mouth = box_at(8, 90, 8, 150, 102, 34)
    port = box_at(36, -0.2, 10.4, 48, 8, 13.2)
    bay = cleanup(difference(shell, [void, mouth, port]), "bay")
    publish("qa5_service_v5", move(bay, 360, MY1 + 6, 0),
            "Adult bay behind the house. A port on this face meets the foundation chase. 0.3 mm gap. Not a play door.",
            "service", "service", "#3c4650", explode=[0, 24, 0])
    # Coupon uses the same seat as the house: skin 1.4, depth 3.2, mouth open.
    frame = box_at(0, 0, 0, 28, 8, 22)
    frame = cleanup(difference(frame, [along_y(14, SKIN, 8.6, 11, POD_D / 2)]), "coupon frame")
    panel = box_at(6, 8.8, 4, 22, 14, 18)
    panel = cleanup(union([panel, along_y(14, SKIN + POD_H + 0.08, 9.1, 11, 2.45)]), "coupon cap")
    publish("qa5_coupon_frame_v5", move(frame, 2200, 0, 0),
            "Magnet coupon block. Mouth is open. Seat is 3.2 mm deep for a nominal 2.8 mm disc, with 1.4 mm skin. Not a measured fit.",
            "coupon-frame", "coupon", PLASTER)
    publish("qa5_coupon_panel_v5", move(panel, 2200, 0, 0),
            "Coupon cap. Boss stops at the disc seat. Same clearance as the house caps.",
            "coupon-panel", "coupon", IVORY, {"group": "coupon", "pull": [0, 16, 0]})
    bar = cleanup(union([box_at(0.2, 0.2, 0, POD_H - 0.2, 6.0, 24), box_at(0.6, -1.1, 2, POD_H - 0.5, 7.4, 20)]), "bar")
    publish("qa5_retainer_v5", move(bar, 2260, 0, 10), "Capture bar for the magnet. It does not fasten the wall.", "retainer", "coupon", "#777777")
    w = box_at(0, 0, 0, 40, 18, 5)
    c1 = cylinder(radius=(MAG_D + 0.4) / 2, height=1.4, sections=14)
    c1.apply_translation((12, 9, 4.3))
    c2 = cylinder(radius=(MAG_D + 0.4) / 2, height=1.4, sections=14)
    c2.apply_translation((28, 9, 4.3))
    wells = cleanup(difference(w, [c1, c2]), "wells")
    publish("qa5_polarity_v5", move(wells, 2320, 0, 0), "Polarity aid. Shallow wells. Do not leave discs in it.", "polarity", "coupon", "#ddd8cc")


def overlap(a, b):
    return not (a.bounds[1][0] < b.bounds[0][0] or a.bounds[0][0] > b.bounds[1][0]
                or a.bounds[1][1] < b.bounds[0][1] or a.bounds[0][1] > b.bounds[1][1]
                or a.bounds[1][2] < b.bounds[0][2] or a.bounds[0][2] > b.bounds[1][2])


def ivol(a, b):
    hit = tm.boolean.intersection([a, b], engine="manifold")
    if hit is None or hit.is_empty:
        return 0.0
    v = float(hit.volume)
    return v if v > 0 else 0.0


def audits():
    fails = []
    house = [i for i in INSTANCES if i["role"] != "coupon"]
    worst, pair, n = 0.0, None, 0
    for i in range(len(house)):
        for j in range(i + 1, len(house)):
            if not overlap(house[i]["world"], house[j]["world"]):
                continue
            n += 1
            v = ivol(house[i]["world"], house[j]["world"])
            if v > worst:
                worst, pair = v, (house[i]["id"], house[j]["id"], round(v, 1))
            if v > 2.0:
                fails.append({"pair": [house[i]["id"], house[j]["id"]], "mm3": round(v, 1)})
                print("clash", house[i]["id"], house[j]["id"], round(v, 1), flush=True)
    roofs = []
    for item in house:
        if item["role"] != "roof":
            continue
        plate = item["extra"]["plate_top"]
        foot = item["world"].bounds
        probe = box_at(foot[0, 0] + 10, foot[0, 1] + 6, plate - 0.35, foot[1, 0] - 10, foot[1, 1] - 6, plate + 0.05)
        best, who = 0.0, None
        for other in house:
            if other["role"] not in ("structure", "porch"):
                continue
            if overlap(probe, other["world"]):
                v = ivol(probe, other["world"])
                if v > best:
                    best, who = v, other["id"]
        roofs.append({"id": item["id"], "bodies": 1, "seat_gap_mm": round(item["extra"]["seat_z"] - plate, 3), "bearing_probe_mm3": round(best, 1), "bearer": who})
        if best < 40:
            fails.append({"roof": item["id"], "bearing": round(best, 1)})
    stairs = []
    for spec, iid, target in ((S1, "stair-lower", L2), (S2, "stair-upper", L3)):
        mesh = next(i["world"] for i in house if i["id"] == iid)
        top = float(mesh.bounds[1][2])
        if spec["up"] > 0:
            well = box_at(spec["x0"] + 6, spec["y0"] + 12, target - 1, spec["x1"] - 6, spec["y1"] - 6, target + 1)
        else:
            well = box_at(spec["x0"] + 6, spec["y0"] + 8, target - 1, spec["x1"] - 6, spec["y1"] - 10, target + 1)
        blocked = 0
        for item in house:
            if item["role"] == "floor" and overlap(well, item["world"]):
                blocked = max(blocked, ivol(well, item["world"]))
        clear = HEAD
        for i in range(1, RISES - 1, 3):
            z = spec["z"] + (i + 1) * RISE
            y = spec["y0"] + i * TREAD if spec["up"] > 0 else spec["y1"] - i * TREAD
            x = (spec["x0"] + spec["x1"]) / 2
            ceiling = min(z + 6 + HEAD, target - 1)
            if ceiling <= z + 10:
                continue
            probe = box_at(x - 3, y - 3, z + 6, x + 3, y + 3, ceiling)
            for item in house:
                if item["id"] == iid or item["role"] not in ("structure", "floor", "roof"):
                    continue
                if overlap(probe, item["world"]) and ivol(probe, item["world"]) > 0.5:
                    clear = 0
                    print("head", iid, item["id"], i, flush=True)
                    break
        row = {"id": iid, "top_z": round(top, 2), "target": target, "top_gap_mm": round(target - top, 2),
               "well_blocked_mm3": round(blocked, 2), "headroom_sample_mm": clear}
        stairs.append(row)
        if blocked > 2:
            fails.append({"well": iid})
        if clear < HEAD:
            fails.append({"headroom": iid})
    seats = []
    hosts = [i for i in house if i["role"] in ("structure", "roof", "porch", "back", "floor")]
    for item in house:
        if item["role"] != "trim":
            continue
        nearest = 99.0
        for host in hosts:
            gap = 0.0
            for axis in range(3):
                if item["world"].bounds[1][axis] < host["world"].bounds[0][axis]:
                    gap = max(gap, float(host["world"].bounds[0][axis] - item["world"].bounds[1][axis]))
                elif host["world"].bounds[1][axis] < item["world"].bounds[0][axis]:
                    gap = max(gap, float(item["world"].bounds[0][axis] - host["world"].bounds[1][axis]))
            nearest = min(nearest, gap)
        seats.append({"id": item["id"], "seat_gap_mm": round(nearest, 3)})
        if nearest > 1.2:
            fails.append({"floating_trim": item["id"], "mm": round(nearest, 2)})
    print("seats", seats, flush=True)
    rear = next(i for i in INSTANCES if i["id"] == "rear")
    rb = rear["world"].bounds
    gap = float(rb[0][1] - JAMB_BACK)
    touch = 0.0
    for other in house:
        if other["id"] not in ("walls-l1", "walls-l2", "side", "attic-frame"):
            continue
        if overlap(rear["world"], other["world"]):
            touch += ivol(rear["world"], other["world"])
    rear_fit = {"gap_y_mm": round(gap, 3), "target_gap_mm": FIT_GAP,
                "intersection_mm3": round(touch, 3),
                "panel_bbox_mm": [round(float(v), 1) for v in (rb[1] - rb[0])],
                "closed_transform": "identity placement of the STL; this gap is the closed position"}
    print("rear fit", rear_fit, flush=True)
    if not (0.25 <= gap <= 0.8):
        fails.append({"rear_gap_mm": round(gap, 3)})
    if touch > 2:
        fails.append({"rear_intersection_mm3": round(touch, 2)})
    print("rest", n, pair, "roofs", roofs, "stairs", stairs, flush=True)
    return {"ok": not fails, "failures": fails[:16], "rest_pairs": n, "worst_mm3": round(worst, 2),
            "worst_pair": pair, "roofs": roofs, "stairs": stairs, "rear_fit": rear_fit, "trim_seats": seats}


def write_all(report):
    os.makedirs(STL, exist_ok=True)
    os.makedirs(REPORT, exist_ok=True)
    keep = set(CATALOG)
    for name in os.listdir(STL):
        if name.endswith(".stl") and name[:-4] not in keep:
            os.remove(os.path.join(STL, name))
    for name, info in CATALOG.items():
        info["mesh"].export(os.path.join(STL, name + ".stl"))
    bad = []
    for name, info in CATALOG.items():
        mesh = tm.load(os.path.join(STL, name + ".stl"), force="mesh")
        counts = np.bincount(mesh.edges_unique_inverse)
        nbad = int(np.sum(counts != 2))
        comps = len(mesh.split(only_watertight=False))
        parts = mesh.split(only_watertight=False)
        positive = [p for p in parts if p.volume > 1.0]
        negative = [p for p in parts if p.volume < -1.0]
        info["reloaded"] = {
            "watertight": bool(mesh.is_watertight),
            "winding": bool(mesh.is_winding_consistent),
            "components": comps,
            "positive_bodies": len(positive),
            "negative_bodies": len(negative),
            "nonmanifold_edges": nbad,
            "volume": round(float(mesh.volume), 1),
        }
        if len(positive) != 1 or negative or nbad or not mesh.is_watertight:
            bad.append(name)
            print("topology", name, info["reloaded"], flush=True)
    if bad:
        raise RuntimeError("reloaded STL is not one clean solid: " + ", ".join(bad))
    house = [i for i in INSTANCES if i["role"] != "coupon"]
    mins = np.min([i["world"].bounds[0] for i in house], axis=0)
    maxs = np.max([i["world"].bounds[1] for i in house], axis=0)
    cx, cy = (mins[0] + maxs[0]) / 2, (mins[1] + maxs[1]) / 2
    cz = (mins[2] + maxs[2]) * 0.42
    bom = {}
    instances = []
    for item in INSTANCES:
        bom[item["part"]] = bom.get(item["part"], 0) + 1
        p = item["place"]
        instances.append({
            "id": item["id"], "part": item["part"], "role": item["role"], "color": item["color"],
            "motion": item["motion"], "explode_mm": item["explode_mm"],
            "transform": [[1, 0, 0, round(p[0], 3)], [0, 1, 0, round(p[1], 3)], [0, 0, 1, round(p[2], 3)], [0, 0, 0, 1]],
        })
    count = len(FIXTURES)
    manifest = {
        "name": "Queen Anne Playhouse",
        "version": "6.4.0",
        "prior_version": "archive/v4.0.0",
        "scale": "1:24",
        "description": "Solid Queen Anne. Front and sides stay on. The full back is the one magnetic closure.",
        "concept_image": "concept/approved-direction.jpg",
        "concept_note": "Approved picture. Not this CAD and not a measured survey.",
        "units": "mm", "up_axis": "Z",
        "printer_nominal_bed_mm": list(BED), "fit_envelope_mm": list(FIT),
        "assembled_size_mm": {
            "x": round(float(maxs[0] - mins[0]), 1), "y": round(float(maxs[1] - mins[1]), 1), "z": round(float(maxs[2] - mins[2]), 1),
            "min_mm": [round(float(v), 1) for v in mins], "max_mm": [round(float(v), 1) for v in maxs],
        },
        "proportion_note": "Assembly is wider than the v4 stack. Turret across the flats is about 148 mm. Porch depth is about 86 mm. Main ridge is below the turret spire.",
        "rooms": [
            {"id": "parlor", "storey": 1, "note": "Left, open to the turret."},
            {"id": "entry", "storey": 1, "note": "Door and the foot of the lower stair."},
            {"id": "kitchen", "storey": 1, "note": "Right, cabinets on the rear wall."},
            {"id": "bedroom", "storey": 2, "note": "First floor, left of the stair."},
            {"id": "bath", "storey": 2, "note": "First floor, right."},
            {"id": "landing", "storey": 2, "note": "Lower flight arrives. Upper flight leaves."},
            {"id": "attic", "storey": 3, "note": "Under the cross-gable."},
            {"id": "turret", "storey": 3, "note": "Same level as the attic."},
        ],
        "plan": {"storeys": [
            {"storey": 1, "floor_z": L1, "rooms": [
                {"id": "p", "name": "Parlor", "x0": 250, "y0": 120, "x1": 390, "y1": 240},
                {"id": "t", "name": "Turret", "x0": 100, "y0": 60, "x1": 240, "y1": 200},
                {"id": "e", "name": "Entry", "x0": 390, "y0": 120, "x1": 450, "y1": 200},
                {"id": "k", "name": "Kitchen", "x0": 450, "y0": 140, "x1": 530, "y1": 290},
                {"id": "porch", "name": "Porch", "x0": 120, "y0": 22, "x1": 520, "y1": 100},
            ], "doors": [{"id": "hall", "x0": 400, "y0": 150, "x1": 414, "y1": 198}],
             "stairs": [{"id": "lower", "x0": S1["x0"], "y0": S1["y0"], "x1": S1["x1"], "y1": S1["y1"]}],
             "lights": [f for f in FIXTURES if f["storey"] == 1]},
            {"storey": 2, "floor_z": L2, "rooms": [
                {"id": "b", "name": "Bedroom", "x0": 250, "y0": 120, "x1": 400, "y1": 250},
                {"id": "bath", "name": "Bath", "x0": 460, "y0": 120, "x1": 530, "y1": 200},
                {"id": "land", "name": "Landing", "x0": 400, "y0": 220, "x1": 500, "y1": 290},
            ], "doors": [], "stairs": [
                {"id": "upper", "x0": S2["x0"], "y0": S2["y0"], "x1": S2["x1"], "y1": S2["y1"]},
                {"id": "well", "x0": S1["x0"], "y0": S1["y0"], "x1": S1["x1"], "y1": S1["y1"]},
            ], "lights": [f for f in FIXTURES if f["storey"] == 2]},
            {"storey": 3, "floor_z": L3, "rooms": [
                {"id": "a", "name": "Attic", "x0": 260, "y0": 130, "x1": 520, "y1": 280},
                {"id": "tl", "name": "Turret loft", "x0": 110, "y0": 60, "x1": 240, "y1": 200},
            ], "doors": [], "stairs": [{"id": "well", "x0": S2["x0"], "y0": S2["y0"], "x1": S2["x1"], "y1": S2["y1"]}],
             "lights": [f for f in FIXTURES if f["storey"] == 3]},
        ]},
        "magnet": {
            "status": "NOMINAL_NOT_FIT_APPROVED", "nominal_mm": [MAG_D, MAG_T],
            "radial_clearance_per_side_mm": RAD, "axial_clearance_mm": AX,
            "pocket_diameter_mm": round(POD_D, 2), "pocket_depth_mm": round(POD_H, 2),
            "mating_skin_mm": SKIN, "holding_force_calculated": False, "h3c_pause_profile": False,
            "retention": "magnetic_only_straight_pull",
            "capture_bar": "closes the magnet only",
        },
        "lighting": {
            "architecture": "External regulated nominal 5V USB, pre-resistored 5-12V warm-white branches.",
            "cavity_status": "PROVISIONAL_NOT_FIT_VALIDATED",
            "cavity_mm": [6, 6, 3], "fixture_count": count,
            "research_scenario_leds": 24, "research_scenario_budget_A": 0.48,
            "house_budget_A_at_20mA": round(count * 0.02, 3), "budget_is_measured": False,
            "protection_finalized": False, "electrically_tested": False, "mains_inside": False,
            "fuse_nominated": False,
            "protection_note": "No fuse is selected. Do not size one from the 20 mA sum.",
            "fixtures": FIXTURES,
            "fragile_ornament": "Balusters, bargeboard piercings, flower blossoms, and scallop edges are thin. A 0.2 mm nozzle is the ornament setting. They are not claimed durable or safe.",
        },
        "departures_from_concept": [
            "The picture is a render, not a survey. The broad front, turret, porch, and street gable follow it. Mouldings are thicker than the render's hairlines.",
            "Play access is the full back, one wall, pulled straight off. The front and both sides stay. The picture's open view is a side cutaway; this house opens at the back.",
            "The back seats 0.45 mm off the jambs. That gap is the fit, not a missing wall. Magnets do not hold the house up. The back is not a brace.",
            "The rear wall's measured bbox fits one print. It is not a 460 mm slab.",
            "Colors in the viewer are the intended palette. One printed part is one material until it is painted.",
            "Balusters, bargeboard piercings, blossoms, and scallop edges are thin. A 0.2 mm nozzle is the ornament setting. They are not claimed durable.",
        ],
        "magnet_install_steps": [
            "Print the coupon first. Its bore is the same cross-section as the house seats.",
            "A nominal 5.0 x 2.8 mm disc drops in the open mouth. The seat is 5.6 mm across and 3.2 mm deep. Those are design allowances of 0.30 mm radial and 0.40 mm axial, not a measured fit.",
            "1.4 mm of plastic stays between the disc and the mating face. The cap boss stops at the seat and does not pinch the disc.",
            "The cap pulls straight off. It does not fasten the back to the jamb. Holding force is untested.",
            "The back pulls straight off toward the rear. Pins and the bottom ledge locate it. The front, sides, porch, and roofs stay.",
        ],
        "limits": [
            "Not printed. No strength, tip-over, magnet, or electrical test.",
            "Roofs are gravity seated, not locked. They bear on the fixed shell with the back off.",
            "The back is a closure, not a structural brace. Magnets are not the house's support.",
            "Thin ornament can break. That is not a safety claim.",
            "A 0.2 mm nozzle is a machine some printers can take. It is not confirmed for this house. Nozzle diameter, layer height, and extrusion width are different numbers.",
            "Not a toy-safety certification.",
        ],
        "cameras": {
            "closed": {"position": [60, -420, 200], "target": [330, 170, 180]},
            "front": {"position": [360, -460, 180], "target": [360, 160, 180]},
            "rear": {"position": [370, 640, 160], "target": [370, 280, 130]},
            "open": {"position": [400, 780, 190], "target": [390, 220, 230]},
            "stairs": {"position": [470, 640, 210], "target": [400, 190, 210]},
            "attic": {"position": [470, 360, 250], "target": [360, 185, 226]},
            "detail": {"position": [390, -40, 340], "target": [380, 70, 310]},
            "attachment": {"position": [640, 480, 110], "target": [420, 280, 90]},
            "plan": {"position": [cx, cy, maxs[2] + 280], "target": [cx, cy, 80]},
            "lighting": {"position": [cx + 40, mins[1] - 80, 160], "target": [cx, cy, 90]},
            "explode": {"position": [cx - 80, mins[1] - 200, cz + 80], "target": [cx, cy, cz]},
        },
        "legacy_interface": legacy_interface(),
        "validation": {
            "printed": False, "measured": False, "physically_verified": False, "forces_tested": False,
            "h3c_sliced": False, "h3c_pause_profile": False, "electrically_tested": False,
            "protection_finalized": False, "led_fit_validated": False, "cad_validated": report["ok"],
        },
        "parts": [{"id": n, "file": f"stl/{n}.stl", "note": i["note"], "triangles": i["triangles"], "volume_mm3": i["reloaded"]["volume"],
                   "watertight": i["reloaded"]["watertight"], "bodies": i["reloaded"]["components"],
                   "nonmanifold_edges": i["reloaded"]["nonmanifold_edges"],
                   "bbox_mm": i["extents"], "fits_brim_allowance": True} for n, i in CATALOG.items()],
        "bom": [{"part": n, "file": f"stl/{n}.stl", "qty": q, **({"print_qty": 26, "note": "One bar per rear pocket and matching jamb pocket, plus the coupon. The bar closes the magnet only."} if n == "qa5_retainer_v5" else {})} for n, q in sorted(bom.items())],
        "instances": instances,
    }
    # cameras used python lists of numpy floats
    for cam in manifest["cameras"].values():
        cam["position"] = [round(float(v), 1) for v in cam["position"]]
        cam["target"] = [round(float(v), 1) for v in cam["target"]]
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf8") as h:
        json.dump(manifest, h, indent=2)
        h.write("\n")
    report.update({"triangles": sum(i["triangles"] for i in CATALOG.values()), "instance_count": len(instances),
                   "fixture_count": count, "assembly_mm": manifest["assembled_size_mm"]})
    with open(os.path.join(REPORT, "validation.json"), "w", encoding="utf8") as h:
        json.dump(report, h, indent=2)
        h.write("\n")
    return manifest


def legacy_interface():
    tile = tm.load(LEGACY_TILE)
    post = tm.load(LEGACY_POST)
    peg = post.copy()
    peg.apply_transform(rotation_matrix(math.pi, [1, 0, 0]))
    peg.apply_translation((15.875, 15.875, 11.0))
    hit = tm.boolean.intersection([tile, peg], engine="manifold")
    vol = 0.0 if hit is None or hit.is_empty else max(0.0, float(hit.volume))
    return {"tile_bbox_mm": [round(float(v), 3) for v in tile.extents], "seated_peg_mm3": round(vol, 3),
            "snap_compatible": False, "note": "Measured on floor_tile_v0. This house does not use that socket."}


def lay_on_bed(mesh):
    """Put the shortest bounding axis on Z and the part's minimum corner at the origin."""
    out = mesh.copy()
    axis = int(np.argmin(out.extents))
    if axis == 0:
        out.apply_transform(rotation_matrix(-math.pi / 2, [0, 1, 0]))
    elif axis == 1:
        out.apply_transform(rotation_matrix(-math.pi / 2, [1, 0, 0]))
    out.apply_translation(-out.bounds[0])
    return out


def _translation(instance):
    return [float(instance["transform"][0][3]), float(instance["transform"][1][3]), float(instance["transform"][2][3])]


def write_review_exports(manifest=None):
    """Print poses, magnet centers, a real stile section, and a reloaded-STL topology count.

    Reads the STLs already on disk. It does not rebuild the house.
    """
    if manifest is None:
        with open(os.path.join(ROOT, "manifest.json"), encoding="utf8") as handle:
            manifest = json.load(handle)
    os.makedirs(os.path.join(STL, "print"), exist_ok=True)
    os.makedirs(REPORT, exist_ok=True)
    poses = {}
    for part in manifest["parts"]:
        name = part["id"] + ".stl"
        mesh = tm.load(os.path.join(STL, name), force="mesh")
        native = [round(float(v), 2) for v in mesh.extents]
        shortest = float(np.min(mesh.extents))
        if mesh.extents[2] > max(shortest * 1.05, shortest + 1.0) and mesh.extents[2] > 100.0:
            flat = lay_on_bed(mesh)
            flat.export(os.path.join(STL, "print", name))
            extents = [round(float(v), 2) for v in flat.extents]
            poses[name] = {
                "pose": "shortest axis on Z, corner at the origin",
                "native_extents_mm": native,
                "print_extents_mm": extents,
                "margin_to_310x300x315_mm": [round(310 - extents[0], 1), round(300 - extents[1], 1), round(315 - extents[2], 1)],
            }
        else:
            poses[name] = {
                "pose": "native STL, shortest axis already on Z" if mesh.extents[2] <= shortest + 1.0 else "native STL, already inside the height allowance",
                "native_extents_mm": native,
                "print_extents_mm": native,
                "margin_to_310x300x315_mm": [round(310 - native[0], 1), round(300 - native[1], 1), round(315 - native[2], 1)],
            }
    with open(os.path.join(REPORT, "print-orientations.json"), "w", encoding="utf8") as handle:
        json.dump({"envelope_mm": [310, 300, 315], "parts": poses,
                   "note": "Margins are envelope minus the printed bounding box. A positive margin is unused bed. No slicer was run."},
                  handle, indent=2)
        handle.write("\n")

    by_id = {item["id"]: item for item in manifest["instances"]}
    rear_t = _translation(by_id["rear"])
    jamb_host = {"l1": _translation(by_id["walls-l1"]), "l2": _translation(by_id["walls-l2"]), "side": _translation(by_id["side"])}
    cap_t = {"qa5_cap_back-l_v5": _translation(by_id["cap-back-l"]), "qa5_cap_back-r_v5": _translation(by_id["cap-back-r"])}
    zs = [L1 + 28, L1 + 52, L1 + 74, L2 + 28, L2 + 52, L2 + 74]
    xs = [(MX0 + 17, "qa5_cap_back-l_v5", "l1"), (MX1 - 13, "qa5_cap_back-r_v5", "side")]
    rear = tm.load(os.path.join(STL, "qa5_rear_v5.stl"), force="mesh")
    stations = []
    n = 0
    for x, cap_name, right_host in xs:
        for zc in zs:
            n += 1
            host_key = right_host if x > 400 else ("l1" if zc < L2 else "l2")
            world = [x, round(JAMB_BACK + FIT_GAP + SKIN + POD_H / 2, 2), zc]
            local = [round(world[i] - rear_t[i], 2) for i in range(3)]
            skin = [local[0], round(SKIN / 2, 2), local[2]]
            if rear.contains([local])[0]:
                raise RuntimeError(f"station {n} disc center is solid in qa5_rear_v5 at {local}")
            if not rear.contains([skin])[0]:
                raise RuntimeError(f"station {n} skin is void in qa5_rear_v5 at {skin}")
            jt = jamb_host[host_key]
            jamb_world = [x, round(JAMB_BACK - SKIN - POD_H / 2, 2), zc]
            stations.append({
                "station": n,
                "panel": {
                    "host": "qa5_rear_v5",
                    "center_mm": world,
                    "center_in_stl_mm": local,
                    "axis": [0, 1, 0],
                    "mouth_opens": "+Y",
                    "diameter_mm": round(POD_D, 2),
                    "depth_mm": round(POD_H, 2),
                    "skin_mm": SKIN,
                    "mating_face_y": round(JAMB_BACK + FIT_GAP, 2),
                    "disc_zone_y": [round(JAMB_BACK + FIT_GAP + SKIN, 2), round(JAMB_BACK + FIT_GAP + SKIN + POD_H, 2)],
                    "cap": cap_name,
                    "cap_retention": "Head sits in the counterbore. Boss stops at the disc zone. Clearance fit. Not printed.",
                },
                "jamb": {
                    "host": {"l1": "qa5_walls_l1_v5", "l2": "qa5_walls_l2_v5", "side": "qa5_side_v5"}[host_key],
                    "center_mm": jamb_world,
                    "center_in_stl_mm": [round(jamb_world[i] - jt[i], 2) for i in range(3)],
                    "axis": [0, -1, 0],
                    "mouth_opens": "-Y",
                    "diameter_mm": round(POD_D, 2),
                    "depth_mm": round(POD_H, 2),
                    "skin_mm": SKIN,
                },
            })
    magnets = {
        "nominal_disc_mm": [MAG_D, MAG_T],
        "allowance": "0.30 mm each side of the diameter, 0.40 mm along the 2.8 mm thickness. Design numbers, not a measured fit.",
        "coordinates": "center_mm is the assembled house, Z up. center_in_stl_mm is that point in the host STL, whose manifest transform is a translation.",
        "stations": stations,
        "section": "Cut qa5_rear_v5 at local x = 9, which is assembled x = 228. The disc zone is assembled y 296.85 to 300.05.",
    }
    with open(os.path.join(REPORT, "magnets.json"), "w", encoding="utf8") as handle:
        json.dump(magnets, handle, indent=2)
        handle.write("\n")

    crop = box_at(3.0, -0.2, 21.0, 15.0, 7.6, 34.0)
    seat = tm.boolean.intersection([rear, crop], engine="manifold")
    if seat is None or seat.is_empty or seat.volume < 10:
        raise RuntimeError("magnet cutaway missed the rear stile")
    cap = tm.load(os.path.join(STL, "qa5_cap_back-l_v5.stl"), force="mesh")
    cap.apply_translation(cap_t["qa5_cap_back-l_v5"])
    cap.apply_translation([-rear_t[0], -rear_t[1], -rear_t[2]])
    cap.apply_translation([-crop.bounds[0][0], -crop.bounds[0][1], -crop.bounds[0][2]])
    seat.apply_translation(-crop.bounds[0])
    seat.export(os.path.join(REPORT, "magnet-cutaway-seat.stl"))
    cap.export(os.path.join(REPORT, "magnet-cutaway-cap.stl"))
    _section_png(rear, cap_t, rear_t, os.path.join(REPORT, "magnet-section.png"))

    rows = []
    bad = []
    for part in manifest["parts"]:
        mesh = tm.load(os.path.join(STL, part["id"] + ".stl"), force="mesh")
        counts = np.bincount(mesh.edges_unique_inverse)
        nbad = int(np.sum(counts != 2))
        pieces = mesh.split(only_watertight=False)
        positive = [p for p in pieces if p.volume > 1.0]
        negative = [p for p in pieces if p.volume < -1.0]
        row = {"id": part["id"], "watertight": bool(mesh.is_watertight), "positive_bodies": len(positive),
               "negative_bodies": len(negative), "nonmanifold_edges": nbad, "volume_mm3": round(float(mesh.volume), 1)}
        rows.append(row)
        if len(positive) != 1 or negative or nbad or not mesh.is_watertight or mesh.volume <= 0:
            bad.append(part["id"])
    with open(os.path.join(REPORT, "topology.json"), "w", encoding="utf8") as handle:
        json.dump({"ok": not bad, "parts": len(rows), "failures": bad,
                   "rule": "Reloaded STL: one positive body, no negative body, every edge on exactly two faces.",
                   "bodies": rows}, handle, indent=2)
        handle.write("\n")
    if bad:
        raise RuntimeError("reloaded STL is not one clean solid: " + ", ".join(bad))
    manifest.setdefault("cameras", {})["attic"] = {"position": [470.0, 360.0, 250.0], "target": [360.0, 185.0, 226.0]}
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"print_poses": sum(1 for p in poses.values() if p["pose"].startswith("shortest")),
                      "stations": len(stations), "topology": len(rows)}))


def _section_png(rear, cap_t, rear_t, path):
    local_x = (MX0 + 17) - rear_t[0]
    section = rear.section(plane_origin=[local_x, 0, 0], plane_normal=[1, 0, 0])
    if section is None:
        raise RuntimeError("rear stile section is empty")
    cap = tm.load(os.path.join(STL, "qa5_cap_back-l_v5.stl"), force="mesh")
    cap_local_x = (MX0 + 17) - cap_t["qa5_cap_back-l_v5"][0]
    cap_section = cap.section(plane_origin=[cap_local_x, 0, 0], plane_normal=[1, 0, 0])
    width, height = 980, 1280
    image = Image.new("RGB", (width, height), (244, 241, 234))
    draw = ImageDraw.Draw(image)
    draw.text((24, 18), "Rear stile, assembled x = 228. Y is enlarged. Actual mesh section.", fill=(20, 24, 28))
    draw.text((24, 44), "Nominal disc 5.0 x 2.8 mm. Seat 5.6 dia x 3.2 deep. Skin 1.4. Design allowance, not a measured fit.", fill=(20, 24, 28))

    def strokes(path3d, origin, color, span):
        if path3d is None:
            return
        y0, y1, z0, z1, px0, py0, px1, py1 = span
        for poly in path3d.discrete:
            pts = []
            for x, y, z in poly:
                wy, wz = y + origin[1], z + origin[2]
                px = px0 + (wy - y0) / (y1 - y0) * (px1 - px0)
                py = py0 + (z1 - wz) / (z1 - z0) * (py1 - py0)
                pts.append((px, py))
            if len(pts) > 1:
                draw.line(pts, fill=color, width=2)

    full = (294.5, 304.0, 10.0, 210.0, 70, 110, 430, 1220)
    strokes(section, rear_t, (28, 64, 58), full)
    strokes(cap_section, cap_t["qa5_cap_back-l_v5"], (140, 48, 48), full)
    zoom = (294.8, 303.2, 36.0, 52.0, 500, 160, 940, 1180)
    draw.rectangle((490, 140, 950, 1200), outline=(180, 176, 168))
    draw.text((500, 120), "Station 1, z = 44", fill=(20, 24, 28))
    strokes(section, rear_t, (28, 64, 58), zoom)
    strokes(cap_section, cap_t["qa5_cap_back-l_v5"], (140, 48, 48), zoom)
    seat_y = JAMB_BACK + FIT_GAP + SKIN + POD_H / 2
    for zc in (L1 + 28, L1 + 52, L1 + 74, L2 + 28, L2 + 52, L2 + 74):
        px = full[4] + (seat_y - full[0]) / (full[1] - full[0]) * (full[6] - full[4])
        py = full[5] + (full[3] - zc) / (full[3] - full[2]) * (full[7] - full[5])
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), outline=(140, 48, 48))
        draw.text((24, py - 8), f"z {zc:.0f}", fill=(40, 44, 48))
    draw.text((500, 90), "Green: stile. Red: cap. Ring: disc center.", fill=(40, 44, 48))
    image.save(path)


def main():
    build()
    report = audits()
    manifest = write_all(report)
    write_review_exports(manifest)
    print(json.dumps({"ok": report["ok"], "parts": len(manifest["parts"]), "fixtures": report["fixture_count"],
                      "size": manifest["assembled_size_mm"], "fails": report["failures"][:6]}))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
