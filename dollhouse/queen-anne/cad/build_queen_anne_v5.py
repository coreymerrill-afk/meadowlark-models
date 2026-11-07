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
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union
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
SKIN, RAD, AX = 1.2, 0.25, 0.20
POD_D = MAG_D + 2 * RAD
POD_H = MAG_T + AX
PULL = 58.0

SAGE, IVORY, WINE = "#8aa396", "#f6f1e7", "#8d3038"
SLATE, BRICK = "#3d4b57", "#7a4338"
WOOD, WOOD_D, PLASTER, BRASS = "#c9a36e", "#6d4b32", "#f4ecdf", "#e7d7b4"


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
    ], 12)


def column(h):
    return revolve([
        [0, 0], [6.4, 0], [7.6, 2.2], [7.2, 5], [5.4, 8], [4.6, 14],
        [4.35, h - 16], [5.1, h - 10], [7.4, h - 5], [7.8, h - 1.5], [6.8, h], [0, h],
    ], 16)


def bracket_mesh():
    # A cyma curve, extruded. This is the carved bracket, not an L of boxes.
    pts = [(0, 0), (0, 20), (3.6, 20), (3.6, 15.5)]
    for i in range(8):
        t = i / 7
        pts.append((3.6 + 13 * (t ** 1.35), 15.2 - 12.4 * math.sin(t * math.pi / 2)))
    pts += [(16.2, 1.6), (16.2, 0)]
    return extrude(Polygon(pts), 4.2)


def scallop():
    # One shingle. The nose is a real scallop, thick enough to read
    # in a full-house view and still a 0.2 mm nozzle ornament.
    body = sbox(-5.4, 0, 5.4, 7.4)
    nose = Point(0, 7.0).buffer(5.2, resolution=6)
    shape = body.union(nose).intersection(sbox(-5.8, 0, 5.8, 12.4))
    return extrude(shape, 1.7)


def bargeboard(length=168.0):
    bar = sbox(0, 0, length, 16)
    bites = [Point(x, 0).buffer(6.2, resolution=6) for x in np.arange(10, length - 4, 14)]
    pierced = [Point(x, 9).buffer(2.3, resolution=6) for x in np.arange(18, length - 8, 16)]
    shape = bar.difference(unary_union(bites + pierced))
    return extrude(shape, 3.0)


SCALLOP = None
BRACKET = None
SPINDLE = None


def cached():
    global SCALLOP, BRACKET, SPINDLE
    if SCALLOP is None:
        SCALLOP = cleanup(scallop(), "scallop")
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


def shingle_field(x0, x1, y0, z0, y1, z1):
    """Individual staggered scallops lying on the slope, embedded into it."""
    cached()
    slope, normal = slope_frame(y0, z0, y1, z1)
    length = float(np.linalg.norm([0, y1 - y0, z1 - z0]))
    across = np.array([1.0, 0.0, 0.0])
    pieces = []
    course = 0
    s = 1.5
    while s < length - 8:
        x = x0 + 2 + (4.6 if course % 2 else 0)
        while x < x1 - 8:
            origin = np.array([x, y0, z0], float) + slope * s - normal * 0.5
            pieces.append(_xform(SCALLOP, origin, across, slope, normal))
            x += 11.2
        s += 7.0
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


def pediment(x, y, z, w):
    peak = z + 8
    return [
        hull([(x, y, z), (x + w, y, z), (x + w / 2, y, peak), (x, y - 2.4, z), (x + w, y - 2.4, z), (x + w / 2, y - 2.4, peak)]),
        box_at(x - 1.5, y - 2.8, z - 1.4, x + w + 1.5, y + 0.6, z + 1.2),
    ]


def window_pack(face, x, y, z, w, h):
    """Layered casing, sill, hood, muntins. The pane itself is a hole in the wall."""
    parts = []
    if face == "-y":
        parts += [
            box_at(x - 3.2, y - 3.0, z - 3.4, x + w + 3.2, y + 0.8, z + 1.4),
            box_at(x - 3.4, y - 2.6, z + h - 1.2, x + w + 3.4, y + 0.8, z + h + 3.2),
            box_at(x - 3.2, y - 2.6, z, x + 1.5, y + 0.8, z + h),
            box_at(x + w - 1.5, y - 2.6, z, x + w + 3.2, y + 0.8, z + h),
            box_at(x, y - 2.2, z + h * 0.47, x + w, y + 0.6, z + h * 0.47 + 1.8),
            box_at(x + w * 0.47, y - 2.0, z + 1.4, x + w * 0.53, y + 0.5, z + h * 0.47),
            box_at(x + w * 0.47, y - 2.0, z + h * 0.47 + 1.8, x + w * 0.53, y + 0.5, z + h - 1.2),
        ]
        parts += pediment(x - 2, y, z + h + 3.0, w + 4)
    elif face == "+x":
        parts += [
            box_at(x - 0.8, y - 3.2, z - 3.4, x + 3.0, y + w + 3.2, z + 1.4),
            box_at(x - 0.8, y - 3.4, z + h - 1.2, x + 3.0, y + w + 3.4, z + h + 2.4),
            box_at(x - 0.8, y - 3.2, z, x + 3.0, y + 1.5, z + h),
            box_at(x - 0.8, y + w - 1.5, z, x + 3.0, y + w + 3.2, z + h),
            box_at(x - 0.6, y, z + h * 0.47, x + 2.4, y + w, z + h * 0.47 + 1.8),
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
    rooms()
    service()


def foundations():
    main = union([
        box_at(MX0, PORCH_FRONT, 3, MX1, MY1, BASE),
        box_at(MX0 + 0.8, PORCH_FRONT - 3, BASE - 5.5, MX1 + 3, MY1 + 3, BASE - 1.4),
        *brick_skin(MX0 + 2.2, PORCH_FRONT, MX1, MY1, BASE),
    ])
    deck = []
    y = PORCH_FRONT + 4
    while y < MY0 - 4:
        deck.append(box_at(MX0 + 8, y, BASE - 0.6, 400, y + 3.2, BASE - 0.15))
        y += 7
    publish("qa5_foundation_v5", cleanup(union([main, *deck]), "foundation"),
            "Brick base and the wood porch deck. Courses are in the mesh.", "foundation", "structure", BRICK)
    turret = union([
        prism(octagon(TX, TY, TR + 42), 0, BASE),
        prism(octagon(TX, TY, TR + 48), BASE - 5.5, BASE - 1.4),
    ])
    turret = cleanup(difference(turret, [box_at(MX0 - 0.6, -20, -4, 900, 700, BASE + 8)]), "turret base")
    publish("qa5_foundation_turret_v5", turret, "Octagonal brick pier under the turret.", "turret-base", "structure", BRICK, explode=[-18, -8, 0])


def floors():
    def slab(z, well):
        mesh = box_at(MX0 + 6, MY0 + 6, z - FLOOR_T, MX1 - 6, MY1 - 6, z)
        ribs = []
        y = MY0 + 14
        while y < MY1 - 12:
            ribs.append(box_at(MX0 + 16, y, z - 0.55, MX1 - 16, y + 1.3, z + 0.15))
            y += 9
        mesh = union([mesh, *ribs])
        return cleanup(difference(mesh, [box_at(*well)]), "floor")
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
            box_at(MX0 + 8, MY1 - 8, z0, MX1 - 8, MY1, z1),
            box_at(MX0 + 4, MY0 + 8, zp, MX1 - 8, MY1 - 6, z1),
            box_at(MX0 + 12, MY0 + 4, zp - 9, MX1 - 12, MY0 + 12, z1),
            box_at(348, MY0 + 16, z0, 356, MY1 - 6, z1),
        ]
        # wainscot on the rear wall
        parts.append(box_at(MX0 + 14, MY1 - 9.2, z0 + 2, MX1 - 14, MY1 - 7.4, z0 + 36))
        cuts = [box_at(344, 148, z0, 362, 196, floor + 76)]
        if name == "l1":
            cuts.append(box_at(S1["x0"] - 6, S1["y0"] - 6, zp - 1, S1["x1"] + 6, S1["y1"] + 10, z1 + 1))
        else:
            cuts.append(box_at(S2["x0"] - 6, S2["y0"] - 8, zp - 1, S2["x1"] + 6, S2["y1"] + 8, z1 + 1))
        cuts.append(box_at(470, MY1 - 12, floor + 30, 510, MY1 + 2, floor + 78))
        return cleanup(union([difference(union(parts), cuts), *window_pack("+y", 470, MY1, floor + 30, 40, 48)]), name)
    publish("qa5_walls_l1_v5", shell(L1, "l1"), "Fixed rear wall, hall partition, and ceiling plate.", "walls-l1", "structure", PLASTER)
    publish("qa5_walls_l2_v5", shell(L2, "l2"), "Fixed rear wall and ceiling of the first floor.", "walls-l2", "structure", PLASTER, explode=[0, 12, 8])
    knee_z = EAVE - GAP
    knee = union([
        box_at(MX0 + 16, MY0 + 4, L3 + 0.5, MX1 - 10, MY0 + 10, knee_z),
        box_at(MX0 + 16, MY1 - 16, L3 + 0.5, MX1 - 10, MY1 - 6, knee_z),
        box_at(MX0 + 10, MY0 + 6, L3 + 0.5, MX0 + 22, MY1 - 6, knee_z),
        box_at(MX1 - 18, MY0 + 6, L3 + 0.5, MX1 - 8, MY1 - 6, knee_z),
    ])
    publish("qa5_attic_frame_v5", cleanup(knee, "knee"), "Eave plates the roof sits on.", "attic-frame", "structure", PLASTER, explode=[0, 0, 16], extra={"plate_top": knee_z})
    lights(L1, [("parlor", 280, 175), ("entry", 390, 155), ("kitchen", 492, 240)])
    lights(L2, [("bedroom", 290, 185), ("bath", 470, 160), ("landing", 400, 270)])
    lights(L3, [("attic", 400, 190), ("turret", TX, TY)])


def lights(floor, spots):
    void = cylinder(radius=2.6, height=2.6, sections=12)
    void.apply_translation((0, 0, 2.0))
    slot = box_at(-3, -0.5, -0.2, -0.6, 0.5, 1.3)
    housing = cleanup(difference(revolve([
        [0, 0], [6.2, 0], [6.2, 1.0], [4.6, 2.6], [2.4, 6.4], [0, 6.4],
    ], 16), [void, slot, move(slot, 4.2, 0, 0)]), "puck")
    name = "qa5_puck_v5"
    if name not in CATALOG:
        local = housing.copy()
        origin = local.bounds[0].copy()
        local.apply_translation(-origin)
        add_part(name, local, "Ceiling puck on the fixed plate. 6 mm cavity is provisional, not a measured LED.")
    top = floor + CLEAR - 0.45
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
            trim += window_pack("-y", win["x"], y1 - 3.4, win["z"], win["w"], win["h"])
            if flowers:
                trim += flower_box(win["x"] + 2, y1 - 3.4, win["z"] - 12, win["w"] - 4)
        zc = [z0 + (z1 - z0) * t for t in (0.25, 0.55, 0.82)]
        for sx in (x0 + 6, x1 - 6):
            cuts += mag_slots((sx, y1), (0, -1), zc)
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
        zc = [z0 + (z1 - z0) * t for t in (0.25, 0.55, 0.82)]
        for sy in (y0 + 6, y1 - 6):
            cuts += mag_slots((x1, sy), (-1, 0), zc)
        mesh = union([difference(union(body + skin + corn), cuts), *trim])
    return cleanup(mesh, face)


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


def ground_front():
    """Fixed street wall behind the porch. A straight pull would hit the porch,
    so everyday play is the side wall. The door sits in the opening."""
    x0, x1 = MX0 + 2.4, MX1 - 1.2
    y1 = MY0 - 0.4
    z0, z1 = L1 + 1.0, L2 - 1.2
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
    wins = [{"x": 250, "z": L1 + 28, "w": 30, "h": 56}, {"x": 455, "z": L1 + 28, "w": 30, "h": 56}]
    door = {"x": 368, "z": L1 + 1.2, "w": 34, "h": 76}
    cuts, trim = [], []
    for win in wins:
        cuts.append(box_at(win["x"], y1 - 10, win["z"], win["x"] + win["w"], y1 + 2, win["z"] + win["h"]))
        trim += window_pack("-y", win["x"], y1 - 3.6, win["z"], win["w"], win["h"])
        trim += flower_box(win["x"] + 1, y1 - 3.6, win["z"] - 11, win["w"] - 2)
    cuts.append(box_at(door["x"], y1 - 10, door["z"], door["x"] + door["w"], y1 + 2, door["z"] + door["h"]))
    trim += [
        box_at(door["x"] - 4, y1 - 5.4, door["z"] - 1, door["x"] + door["w"] + 4, y1 + 0.6, door["z"] + 2.2),
        box_at(door["x"] - 3.4, y1 - 4.6, door["z"], door["x"] - 0.4, y1 + 0.4, door["z"] + door["h"] + 2),
        box_at(door["x"] + door["w"] + 0.4, y1 - 4.6, door["z"], door["x"] + door["w"] + 3.4, y1 + 0.4, door["z"] + door["h"] + 2),
        box_at(door["x"] - 6, y1 - 6, door["z"] + door["h"], door["x"] + door["w"] + 6, y1 + 0.8, door["z"] + door["h"] + 4),
    ]
    trim += pediment(door["x"] - 4, y1 - 1, door["z"] + door["h"] + 3.5, door["w"] + 8)
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
    # Upper front, full width, above the porch roof so it can pull straight off.
    z0, z1 = L2 + 6, L3 + 10
    wins = [{"x": x, "z": L2 + 22, "w": 28, "h": 54} for x in (252, 332, 414, 468)]
    front = facade((MX0 + 4, MY0 - 4.4, z0, MX1 - 0.8, MY0 - 0.35, z1), "-y", wins, flowers=True)
    publish("qa5_facade_front_v5", front, "Full-width upper front. Straight pull. Flower boxes are part of the shell.",
            "front-upper", "facade", SAGE, {"group": "front", "pull": [0, -PULL, 0]}, [0, -40, 8])
    for i, floor in enumerate((L1, L2)):
        z0, z1 = floor + 3, floor + CLEAR - 2
        wins = [{"y": y, "z": floor + 24, "w": 32, "h": 54} for y in (150, 230)]
        side = facade((MX1 + 0.5, MY0 + 6, z0, MX1 + 0.5 + 3.6, MY1 - 8, z1), "+x", wins)
        publish(f"qa5_facade_side_l{i+1}_v5", side, "Full-depth side wall. This is the play opening. Straight pull.",
                f"side-l{i+1}", "facade", SAGE, {"group": "end", "pull": [PULL, 0, 0]}, [36, 0, 6])


def cone_courses():
    """Scallops on the cone flats. Origin is inside the flat so the nose crosses it."""
    cached()
    pieces = []
    base_z = plate_top(L3) + GAP
    for i in range(9):
        z = base_z + 4 + i * 11
        t = (z - base_z) / CONE_H
        if t > 0.84:
            break
        vert = (TR - 4) * (1.0 - t)
        ap = vert * math.cos(math.pi / 8)
        flat = 2 * vert * math.sin(math.pi / 8)
        count = 3 if flat > 30 else 2
        for k in range(8):
            ang = math.radians(45 + k * 45)
            normal = np.array([math.cos(ang), math.sin(ang), 0.0])
            tangent = np.array([-math.sin(ang), math.cos(ang), 0.0])
            for j in range(count):
                off = (j - (count - 1) / 2.0) * 10.5 + (5.2 if i % 2 else 0.0)
                if abs(off) > flat / 2 - 5:
                    continue
                origin = np.array([TX, TY, z]) + normal * (ap - 0.55) + tangent * off
                up = np.cross(normal, tangent)
                pieces.append(_xform(SCALLOP, origin, tangent, up, normal))
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
    head = on_facet(angle, APO - 0.3, z + h + 1.6, w + 8, 3.4, 3.2)
    left = on_facet(angle, APO - 0.3, z + h / 2, 3.2, 3.4, h + 2, dt=-(w / 2 + 1.2))
    right = on_facet(angle, APO - 0.3, z + h / 2, 3.2, 3.4, h + 2, dt=(w / 2 + 1.2))
    a = math.radians(angle)
    n = np.array([math.cos(a), math.sin(a), 0.0])
    t = np.array([-math.sin(a), math.cos(a), 0.0])
    peak = hull([
        (-w / 2 - 2, 0.8, 0), (w / 2 + 2, 0.8, 0), (0, 0.8, 9),
        (-w / 2 - 2, -2.2, 0), (w / 2 + 2, -2.2, 0), (0, -2.2, 9),
    ])
    origin = np.array([TX, TY, z + h + 3.2]) + n * APO
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
    shingles = shingle_field(MX0 + 14, MX1 - 16, y_e + 3, z_e + 3, y_r - 12, z_r - 8)
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
    crest = [box_at(MX0 + 20, MY0 + 4, zc - 2.4, gx0 - 8, MY0 + 10, zc + 2.2)]
    cx = MX0 + 28
    while cx < gx0 - 14:
        crest.append(move(SPINDLE, cx, MY0 + 7, zc - 1.6))
        cx += 12
    front_roof = cleanup(union([front, left, right, *crest, *shingles]), "front roof")
    publish("qa5_roof_front_v5", front_roof,
            "Front slope and the gable cheeks, with individual scalloped shingles.",
            "roof-front", "roof", SLATE, {"group": "roof", "lift": [0, 0, 48], "park": [0, -40, 28]},
            [0, -24, 50], {"plate_top": EAVE - GAP, "seat_z": EAVE})
    face = hull([
        (gx0 + 4, gy0, gz0), (gx1 - 4, gy0, gz0), (xmid, gy0, gz1),
        (gx0 + 4, gy0 + 5.2, gz0), (gx1 - 4, gy0 + 5.2, gz0), (xmid, gy0 + 5.2, gz1),
    ])
    opening = box_at(xmid - 15, gy0 - 3, gz0 + 28, xmid + 15, gy0 + 8, gz0 + 86)
    face = difference(face, [opening])
    board = bargeboard(gx1 - gx0 - 20)
    board.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    board.apply_translation(-board.bounds[0])
    board.apply_translation((gx0 + 10, gy0 - 0.4, gz0 - 1))
    bird = move(owl(), xmid, gy0 + 1.4, gz0 + 26)
    publish("qa5_gable_v5", cleanup(union([face, board, bird]), "gable"),
            "Street gable wall, scalloped bargeboard, and the owl. Sage, in front of the slate slope.",
            "gable", "structure", SAGE, {"group": "roof", "lift": [0, 0, 48], "park": [0, -46, 24]},
            [0, -30, 40])
    rear = slope_slab(MX0 + 8, MX1 - 8, MY1 + 14, EAVE - 16, y_r + 3.0, RIDGE)
    rear_sh = shingle_field(MX0 + 16, MX1 - 16, MY1 + 8, EAVE - 12, y_r + 8, RIDGE - 10)
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
        box_at(447, 213, RIDGE + 18, 485, 247, RIDGE + 28),
        *bricks,
    ])
    rear_roof = cleanup(union([rear, chim, *rear_sh]), "rear roof")
    publish("qa5_roof_rear_v5", rear_roof, "Rear slope, scalloped shingles, and the brick chimney.",
            "roof-rear", "roof", SLATE, {"group": "roof", "lift": [0, 0, 48], "park": [0, 28, 28]},
            [0, 20, 50], {"plate_top": EAVE - GAP, "seat_z": EAVE})
    cone = revolve([[0, 0], [TR - 4, 0], [1.8, CONE_H], [0, CONE_H]], 8)
    cone = move(cone, TX, TY, plate_top(L3) + GAP)
    cone.apply_transform(rotation_matrix(math.radians(22.5), [0, 0, 1], [TX, TY, plate_top(L3)]))
    cap = cleanup(prism(octagon(TX, TY, TR - 16), plate_top(L3) - 4, plate_top(L3) + 0.15), "cap")
    publish("qa5_turret_cap_v5", cap, "Plate under the cone.", "turret-cap", "structure", PLASTER, explode=[-8, 0, 20])
    scales = cone_courses()
    publish("qa5_roof_turret_v5", cleanup(union([cone, *scales]), "cone"),
            "Octagonal cone with a course of scallops on each flat.", "roof-turret", "roof", SLATE,
            {"group": "roof", "lift": [0, 0, 56], "park": [-28, -20, 24]}, [-12, -16, 40],
            {"plate_top": plate_top(L3), "seat_z": plate_top(L3) + GAP})
    def turret_shell(z0, z1, wins, name):
        shell = prism(octagon(TX, TY, TR), z0, z1)
        holes = [prism(octagon(TX, TY, TR - 4.6), z0 - 1, z1 + 1), box_at(MX0 - 0.35, 0, z0 - 1, 900, 500, z1 + 1)]
        holes += [facet_hole(ang, z, 16, 34) for ang, z in wins]
        bands = []
        z = z0 + 5
        while z < z1 - 6:
            bands.append(prism(octagon(TX, TY, TR + 0.85), z, z + 1.35))
            z += 4.1
        for belt in (z0 + 2, z1 - 7):
            bands.append(prism(octagon(TX, TY, TR + 1.8), belt, belt + 3.6))
        trim = []
        for ang, wz in wins:
            trim += facet_trim(ang, wz, 16, 34)
        mesh = difference(union([shell, *bands]), holes)
        return cleanup(union([mesh, *trim]), name)

    street = (180, 225, 270, 315)
    publish("qa5_turret_loft_v5", turret_shell(L3 + 0.6, plate_top(L3) + 0.1, [(a, L3 + 18) for a in street], "loft"),
            "Turret loft, with cased windows on the street flats.", "turret-loft", "structure", SAGE, explode=[-10, -6, 16])
    lower_wins = [(a, L1 + 30) for a in street] + [(a, L2 + 18) for a in street]
    publish("qa5_turret_v5", turret_shell(L1 + 0.6, plate_top(L2) - 0.4, lower_wins, "turret"),
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


def rooms():
    def bed():
        return cleanup(union([
            box_at(0, 0, 8, 48, 78, 16),
            box_at(0, 66, 10, 48, 80, 36),
            box_at(4, 8, 16, 44, 70, 20),
            box_at(6, 58, 20, 22, 68, 26),
            box_at(26, 58, 20, 42, 68, 26),
        ]), "bed")
    def cabinet():
        return cleanup(union([
            box_at(0, 0, 0, 64, 18, 32),
            box_at(2, -0.8, 4, 30, 1.2, 28),
            box_at(34, -0.8, 4, 62, 1.2, 28),
            box_at(0, 8, 28, 64, 16, 52),
            box_at(0, 0, 48, 64, 14, 78),
            box_at(8, 2, 32, 28, 16, 36),
        ]), "cabinet")
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
        return cleanup(union([
            box_at(0, 0, 6, 62, 22, 16),
            box_at(0, 14, 12, 62, 24, 32),
            box_at(0, 0, 10, 6, 22, 26),
            box_at(56, 0, 10, 62, 22, 26),
            box_at(8, 2, 16, 28, 16, 20),
            box_at(34, 2, 16, 54, 16, 20),
        ]), "sofa")
    def chair():
        return cleanup(union([
            box_at(0, 0, 6, 20, 20, 14),
            box_at(0, 12, 10, 20, 20, 30),
            move(revolve([[0, 0], [1.5, 0], [1.5, 8], [0, 8]], 8), 3, 3, 0),
            move(revolve([[0, 0], [1.5, 0], [1.5, 8], [0, 8]], 8), 16, 3, 0),
        ]), "chair")
    pieces = [
        ("qa5_bed_v5", bed(), "Bed with pillows.", "bed", (236, 168, L2 + 0.6)),
        ("qa5_cabinet_v5", cabinet(), "Kitchen cabinets and sink.", "cabinet", (430, 258, L1 + 0.5)),
        ("qa5_table_v5", table(), "Parlor table.", "table", (250, 168, L1 + 1.4)),
        ("qa5_rug_v5", rug(54, 38), "Parlor rug.", "rug", (242, 158, L1 + 0.3)),
        ("qa5_sofa_v5", sofa(), "Parlor sofa.", "sofa", (230, 220, L1 + 0.5)),
        ("qa5_chair_v5", chair(), "Parlor chair.", "chair", (320, 175, L1 + 0.5)),
        ("qa5_trunk_v5", cleanup(box_at(0, 0, 0, 36, 18, 14), "trunk"), "Attic trunk.", "trunk", (320, 214, L3 + 0.8)),
    ]
    for name, mesh, note, iid, at in pieces:
        color = WINE if iid == "rug" else WOOD
        publish(name, move(mesh, *at), note, iid, "furniture", color, explode=[0, 0, 8])


def service():
    shell = box_at(0, 0, 0, 158, 100, 40)
    void = box_at(4, 6, 6, 154, 92, 36)
    mouth = box_at(8, 90, 8, 150, 102, 34)
    bay = cleanup(difference(shell, [void, mouth]), "bay")
    publish("qa5_service_v5", move(bay, 360, MY1 + 6, 0),
            "Adult bay behind the house. 150 x 90 x 30 clear. Not a play door.",
            "service", "service", "#3c4650", explode=[0, 24, 0])
    frame = box_at(0, 0, 0, 36, 12, 64)
    cuts = mag_slots((10, 0), (0, 1), [18, 32, 46]) + mag_slots((26, 0), (0, 1), [18, 32, 46])
    frame = cleanup(difference(frame, cuts), "coupon frame")
    panel = box_at(4, -7, 4, 32, -0.4, 58)
    cuts = mag_slots((10, -0.4), (0, -1), [22, 36, 50]) + mag_slots((26, -0.4), (0, -1), [22, 36, 50])
    panel = cleanup(difference(panel, cuts), "coupon panel")
    publish("qa5_coupon_frame_v5", move(frame, 2200, 0, 0), "Straight-pull coupon, frame half.", "coupon-frame", "coupon", PLASTER)
    publish("qa5_coupon_panel_v5", move(panel, 2204, -8, 4), "Straight-pull coupon, panel half.", "coupon-panel", "coupon", SAGE,
            {"group": "coupon", "pull": [0, -20, 0]})
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
    print("rest", n, pair, "roofs", roofs, "stairs", stairs, flush=True)
    return {"ok": not fails, "failures": fails[:16], "rest_pairs": n, "worst_mm3": round(worst, 2),
            "worst_pair": pair, "roofs": roofs, "stairs": stairs}


def write_all(report):
    os.makedirs(STL, exist_ok=True)
    os.makedirs(REPORT, exist_ok=True)
    for name in os.listdir(STL):
        if name.endswith(".stl") and not name.startswith("qa5_"):
            os.remove(os.path.join(STL, name))
    for name, info in CATALOG.items():
        info["mesh"].export(os.path.join(STL, name + ".stl"))
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
    n_facade = len([i for i in INSTANCES if i["role"] == "facade"])
    count = len(FIXTURES)
    manifest = {
        "name": "Queen Anne Playhouse",
        "version": "5.0.0",
        "prior_version": "archive/v4.0.0",
        "scale": "1:24",
        "description": "Broad Queen Anne: large octagonal turret, street cross-gable, deep wraparound porch.",
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
            "The picture is a render, not a survey. Width, turret, porch depth, and the street gable follow it. Mouldings are thicker than the render's hairlines.",
            "The street gable is a separate sage wall in front of the slate slopes, with a hairline gap so the two parts do not occupy the same volume.",
            "Routine play is the side wall, pulled straight off. The porch and the ground-floor street wall stay.",
            "The turret drum is fixed. A wrapped octagon cannot slide off its floors in a straight line. The joint to the main block is a hairline, not a buried intersection.",
            "Colors in the viewer are the intended palette. One printed part is one material until it is painted.",
            "Balusters, bargeboard piercings, blossoms, and scallop edges are thin. A 0.2 mm nozzle is the ornament setting. They are not claimed durable.",
        ],
        "magnet_install_steps": [
            "Print the coupon first. The slot matches the facade stiles.",
            "An adult seats a nominal 5.0 x 2.8 mm disc and slides the capture bar in from the top.",
            "The bar closes the magnet. It does not catch the frame. Holding force is untested.",
            "The side walls are the everyday opening. They pull straight out. The porch does not have to come off.",
        ],
        "limits": [
            "Not printed. No strength, tip-over, magnet, or electrical test.",
            "Roofs are gravity seated, not locked.",
            "Thin ornament can break. That is not a safety claim.",
            "Not a toy-safety certification.",
        ],
        "cameras": {
            "closed": {"position": [-80, -620, 250], "target": [280, 150, 145]},
            "front": {"position": [300, -760, 190], "target": [310, 150, 130]},
            "open": {"position": [920, 180, 200], "target": [360, 190, 130]},
            "stairs": {"position": [820, 210, 140], "target": [420, 190, 110]},
            "detail": {"position": [250, -30, 55], "target": [370, 55, 40]},
            "attachment": {"position": [760, 180, 70], "target": [500, 200, 55]},
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
        "parts": [{"id": n, "file": f"stl/{n}.stl", "note": i["note"], "triangles": i["triangles"], "volume_mm3": i["volume"],
                   "watertight": True, "bodies": 1, "bbox_mm": i["extents"], "fits_brim_allowance": True} for n, i in CATALOG.items()],
        "bom": [{"part": n, "file": f"stl/{n}.stl", "qty": q, **({"print_qty": n_facade * 4 + 2, "note": "One bar per stile, plus the coupon."} if n == "qa5_retainer_v5" else {})} for n, q in sorted(bom.items())],
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


def main():
    build()
    report = audits()
    manifest = write_all(report)
    print(json.dumps({"ok": report["ok"], "parts": len(manifest["parts"]), "fixtures": report["fixture_count"],
                      "size": manifest["assembled_size_mm"], "fails": report["failures"][:6]}))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
