"""Queen Anne v4. Units mm. Z up. Front is -Y.

The approved picture is the aesthetic direction, not a measured survey.
This file builds a printable house in that direction: octagonal turret,
conical roof, pitched cross-gable, wraparound porch, clapboard, slate
courses, masonry base, and two real stair flights.

v3 is archived. It read as stacked blocks.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import trimesh as tm
from trimesh.creation import box, cone, cylinder
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STL_DIR = os.path.join(ROOT, "stl")
REPORT_DIR = os.path.join(ROOT, "reports")
LEGACY_TILE = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "floor_tile_v0.stl"))
LEGACY_POST = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "snap_post_v0.stl"))

BED = (330.0, 320.0, 325.0)
FIT_MAX = (310.0, 300.0, 315.0)
VOL = 1.0

# Main block. The turret and porch project beyond it.
MX0, MX1 = 168.0, 418.0
MY0, MY1 = 36.0, 228.0
TCX, TCY, TR = 132.0, 92.0, 62.0

BASE = 18.0
F2F = 114.0
FLOOR_T = 6.0
PLATE_T = 11.0
GAP = 0.45
CLEAR = F2F - FLOOR_T - GAP - PLATE_T
L1, L2, L3 = BASE, BASE + F2F, BASE + 2 * F2F

RISES = 14
RISE = F2F / RISES
TREAD = 9.2
RUN = (RISES - 1) * TREAD
STAIR_W = 46.0
HEADROOM = 76.0

# Flight 1 climbs toward the back. Flight 2 returns toward the turret.
S1 = {"x0": 300.0, "x1": 346.0, "y0": 58.0, "y1": 58.0 + RUN, "z": L1, "up": 1}
S2 = {"x0": 220.0, "x1": 266.0, "y0": 56.0, "y1": 56.0 + RUN, "z": L2, "up": 1}
WELL1 = (296.0, 52.0, 352.0, 58.0 + RUN + 6.0)
WELL2 = (214.0, 50.0, 272.0, 56.0 + RUN + 8.0)

MAGNET_D, MAGNET_T = 5.0, 2.8
CLEAR_RADIAL, CLEAR_AXIAL, SKIN = 0.25, 0.20, 1.2
POCKET_D = MAGNET_D + 2 * CLEAR_RADIAL
POCKET_DEPTH = MAGNET_T + CLEAR_AXIAL
PULL = 64.0

LED_CAVITY = (6.0, 6.0, 3.0)
CEILING_OD, CEILING_DEPTH = 12.0, 7.0
SCONCE = (8.0, 8.0, 12.0)
FEED_D = 2.0
CHANNEL = (4.0, 3.0)
RISER = (14.0, 10.0)
BAY_CLEAR = (150.0, 90.0, 30.0)

SAGE = "#8ea396"
IVORY = "#f3eee4"
BURGUNDY = "#7c2f38"
SLATE = "#4c5660"
BRICK = "#8a4b3c"
WOOD = "#c49a6c"
WOOD_DARK = "#8d5e3c"
PLASTER = "#f0e6d4"
BRASS = "#e6d7b8"


def box_at(x0, y0, z0, x1, y1, z1):
    if min(x1 - x0, y1 - y0, z1 - z0) <= 0.04:
        return None
    mesh = box((x1 - x0, y1 - y0, z1 - z0))
    mesh.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return mesh


def cyl_z(radius, height, x, y, z0, sections=12):
    mesh = cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation((x, y, z0 + height / 2))
    return mesh


def cone_at(radius, height, x, y, z0, sections=8):
    mesh = cone(radius=radius, height=height, sections=sections)
    mesh.apply_translation((x, y, z0))
    return mesh


def lathe(profile, sections=10):
    """profile is (z, radius) from bottom to top. Closed solid."""
    rings = [(z, max(r, 0.35)) for z, r in profile]
    verts = []
    for z, r in rings:
        for i in range(sections):
            a = 2 * math.pi * i / sections
            verts.append((r * math.cos(a), r * math.sin(a), z))
    n = sections
    faces = []
    for k in range(len(rings) - 1):
        for i in range(n):
            a = k * n + i
            b = k * n + (i + 1) % n
            c = (k + 1) * n + i
            d = (k + 1) * n + (i + 1) % n
            faces += [[a, c, b], [b, c, d]]
    base = len(verts)
    verts.append((0, 0, rings[0][0]))
    verts.append((0, 0, rings[-1][0]))
    for i in range(n):
        faces.append([base, (i + 1) % n, i])
        faces.append([base + 1, (len(rings) - 1) * n + i, (len(rings) - 1) * n + (i + 1) % n])
    mesh = tm.Trimesh(vertices=np.array(verts, float), faces=np.array(faces), process=True)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def move(mesh, x, y, z):
    out = mesh.copy()
    out.apply_translation((x, y, z))
    return out


def spin_z(mesh, degrees, origin):
    out = mesh.copy()
    out.apply_translation((-origin[0], -origin[1], 0))
    out.apply_transform(rotation_matrix(math.radians(degrees), [0, 0, 1]))
    out.apply_translation((origin[0], origin[1], 0))
    return out


def union(meshes):
    parts = [m for m in meshes if m is not None]
    if not parts:
        raise ValueError("empty union")
    acc = parts[0]
    for index in range(1, len(parts), 16):
        acc = tm.boolean.union([acc, *parts[index:index + 16]], engine="manifold")
    return acc


def difference(base, cuts):
    cuts = [c for c in cuts if c is not None]
    if not cuts:
        return base
    acc = base
    for index in range(0, len(cuts), 12):
        acc = tm.boolean.difference([acc, *cuts[index:index + 12]], engine="manifold")
    return acc


def cleanup(mesh, name):
    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    if mesh.volume < 0:
        mesh.invert()
    positive = [part for part in mesh.split(only_watertight=False) if part.volume > VOL]
    if (not mesh.is_watertight) or mesh.volume <= 0 or len(positive) != 1:
        detail = [(round(part.volume), [round(float(v), 1) for v in part.bounds[0]]) for part in positive[:4]]
        raise RuntimeError(f"{name} positive={len(positive)} watertight={mesh.is_watertight} vol={mesh.volume:.0f} {detail}")
    return mesh


def hull(points):
    return tm.convex.convex_hull(np.array(points, float))


def octagon(cx, cy, radius):
    pts = []
    for i in range(8):
        a = math.radians(22.5 + i * 45.0)
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return pts


def prism(pts, z0, z1):
    return hull([(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts])


def plate_top(floor):
    return floor + CLEAR + PLATE_T


def courses(x0, y0, z0, x1, y1, z1, axis, pitch=5.2, band=3.4, proud=1.05):
    ribs = []
    z = z0 + 1.2
    while z < z1 - 2.0:
        z2 = min(z + band, z1 - 0.4)
        if axis == "-y":
            ribs.append(box_at(x0, y0 - proud, z, x1, y0 + 0.8, z2))
        elif axis == "+y":
            ribs.append(box_at(x0, y1 - 0.8, z, x1, y1 + proud, z2))
        elif axis == "+x":
            ribs.append(box_at(x1 - 0.8, y0, z, x1 + proud, y1, z2))
        elif axis == "-x":
            ribs.append(box_at(x0 - proud, y0, z, x0 + 0.8, y1, z2))
        z += pitch
    return [r for r in ribs if r is not None]


def brick_courses(x0, y0, x1, y1, z1, faces):
    bands = []
    z = 1.5
    while z < z1 - 2.2:
        if "s" in faces:
            bands.append(box_at(x0 + 3, y0 - 1.1, z, x1 - 3, y0 + 0.45, z + 2.5))
        if "n" in faces:
            bands.append(box_at(x0 + 3, y1 - 0.45, z, x1 - 3, y1 + 1.1, z + 2.5))
        if "e" in faces:
            bands.append(box_at(x1 - 0.45, y0 + 3, z, x1 + 1.1, y1 - 3, z + 2.5))
        if "w" in faces:
            bands.append(box_at(x0 - 1.1, y0 + 3, z, x0 + 0.45, y1 - 3, z + 2.5))
        z += 5.6
    return [b for b in bands if b is not None]


def window_hole(face, x, y, z, w, h, depth=10):
    if face == "-y":
        return box_at(x, y - 8, z, x + w, y + depth, z + h)
    if face == "+x":
        return box_at(x - depth, y, z, x + 8, y + w, z + h)
    if face == "+y":
        return box_at(x, y - depth, z, x + w, y + 8, z + h)
    raise ValueError(face)


def sash(face, x, y, z, w, h):
    """Ivory-thick sash built into a shell: sill, hood, jambs, meeting rail, muntins."""
    parts = []
    rail = z + h * 0.46
    if face == "-y":
        y0, y1 = y - 2.4, y + 1.1
        parts += [
            box_at(x - 2, y0, z - 3.2, x + w + 2, y1, z + 1.3),
            box_at(x - 2, y0, z + h - 1.1, x + w + 2, y1, z + h + 2.6),
            box_at(x - 2.4, y0, z, x + 1.3, y1, z + h),
            box_at(x + w - 1.3, y0, z, x + w + 2.4, y1, z + h),
            box_at(x, y0, rail, x + w, y1, rail + 2.2),
            box_at(x + w * 0.48, y0, z + 1.2, x + w * 0.52, y1, rail),
            box_at(x + w * 0.48, y0, rail + 2.2, x + w * 0.52, y1, z + h - 1.2),
        ]
    elif face == "+x":
        x0, x1 = x - 1.1, x + 2.4
        parts += [
            box_at(x0, y - 2, z - 3.2, x1, y + w + 2, z + 1.3),
            box_at(x0, y - 2, z + h - 1.1, x1, y + w + 2, z + h + 2.6),
            box_at(x0, y - 2.4, z, x1, y + 1.3, z + h),
            box_at(x0, y + w - 1.3, z, x1, y + w + 2.4, z + h),
            box_at(x0, y, rail, x1, y + w, rail + 2.2),
            box_at(x0, y + w * 0.48, z + 1.2, x1, y + w * 0.52, rail),
            box_at(x0, y + w * 0.48, rail + 2.2, x1, y + w * 0.52, z + h - 1.2),
        ]
    return [p for p in parts if p is not None]


def magnet_cuts(origin, into, z_centers):
    """Chambers and a top slot. `into` points into the part, away from the mating face."""
    ax, ay = into
    cuts = []
    for zc in z_centers:
        center = (origin[0] + ax * (SKIN + POCKET_DEPTH / 2), origin[1] + ay * (SKIN + POCKET_DEPTH / 2), zc)
        axis = "x" if abs(ax) > 0.5 else "y"
        mesh = cylinder(radius=POCKET_D / 2, height=POCKET_DEPTH + 0.15, sections=16)
        if axis == "x":
            mesh.apply_transform(rotation_matrix(math.pi / 2, [0, 1, 0]))
        else:
            mesh.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        mesh.apply_translation(center)
        cuts.append(mesh)
    z0, z1 = min(z_centers) - 5, max(z_centers) + 14
    if abs(ax) > 0.5:
        xa = origin[0] + ax * SKIN
        xb = origin[0] + ax * (SKIN + POCKET_DEPTH)
        cuts.append(box_at(min(xa, xb), origin[1] - 3.4, z0, max(xa, xb), origin[1] + 3.4, z1))
    else:
        ya = origin[1] + ay * SKIN
        yb = origin[1] + ay * (SKIN + POCKET_DEPTH)
        cuts.append(box_at(origin[0] - 3.4, min(ya, yb), z0, origin[0] + 3.4, max(ya, yb), z1))
    return cuts


def gable_roof(x0, y0, x1, y1, z_eave, z_ridge):
    ymid = (y0 + y1) / 2.0
    outer = hull([
        (x0, y0, z_eave), (x1, y0, z_eave), (x1, y1, z_eave), (x0, y1, z_eave),
        (x0, ymid, z_ridge), (x1, ymid, z_ridge),
    ])
    inner = hull([
        (x0 + 12, y0 + 14, z_eave - 6), (x1 - 12, y0 + 14, z_eave - 6),
        (x1 - 12, y1 - 14, z_eave - 6), (x0 + 12, y1 - 14, z_eave - 6),
        (x0 + 12, ymid, z_ridge - 14), (x1 - 12, ymid, z_ridge - 14),
    ])
    body = difference(outer, [inner])
    shingles = []
    for y_a, y_b in ((y0, ymid), (ymid, y1)):
        span = abs(y_b - y_a)
        steps = 12
        for i in range(steps):
            t0 = i / steps
            t1 = (i + 0.72) / steps
            ya = y_a + (y_b - y_a) * t0
            yb = y_a + (y_b - y_a) * t1
            za = z_eave + (z_ridge - z_eave) * (abs(ya - y_a) / span)
            zb = z_eave + (z_ridge - z_eave) * (abs(yb - y_a) / span)
            shingles.append(box_at(x0 + 3, min(ya, yb), max(za, zb) - 4.0, x1 - 3, max(ya, yb), max(za, zb) + 1.15))
    acc = body
    for shingle in shingles:
        if shingle is None:
            continue
        trial = union([acc, shingle])
        positive = [part for part in trial.split(only_watertight=False) if part.volume > VOL]
        if trial.is_watertight and len(positive) == 1:
            acc = trial
    return acc


def cross_gable(x0, y0, x1, y1, z_eave, z_ridge):
    xmid = (x0 + x1) / 2.0
    body = hull([
        (x0, y0, z_eave), (x1, y0, z_eave), (x1, y1, z_eave), (x0, y1, z_eave),
        (xmid, y0, z_ridge), (xmid, y1, z_ridge),
    ])
    return body


def spindle(height=28.0):
    radii = (2.6, 1.7, 1.5, 2.8, 1.5, 1.7, 2.6)
    step = height / len(radii)
    parts = []
    for i, radius in enumerate(radii):
        z0 = i * step - 0.4
        parts.append(cyl_z(radius, step + 0.8, 0, 0, max(z0, 0), 8))
    return union(parts)


def column(height):
    specs = [(0, 8.2, 6), (4, 6.4, height - 28), (height - 26, 5.4, 14), (height - 14, 8.4, 14)]
    parts = []
    for z0, radius, h in specs:
        parts.append(cyl_z(radius, h + 1.2, 0, 0, z0, 10))
    return union(parts)


def bracket():
    return union([
        box_at(0, 0, 0, 3.4, 4.2, 18),
        box_at(0, 0, 14.2, 3.4, 16, 18),
        box_at(0, 2.2, 6, 3.4, 6.4, 15.2),
        box_at(0, 5.2, 9.2, 3.4, 9.6, 15.4),
        box_at(0, 8.4, 11.6, 3.4, 13.2, 15.6),
        cyl_z(2.2, 3.4, 1.7, 14.2, 13.2, 8),
    ])


def porch_rail(x0, x1, y, z, along="x"):
    parts = []
    if along == "x":
        parts.append(box_at(x0, y, z + 24, x1, y + 3.2, z + 28))
        parts.append(box_at(x0, y, z, x1, y + 3.2, z + 3.2))
        x = x0 + 8
        while x < x1 - 6:
            parts.append(move(spindle(22), x, y + 1.6, z + 2.4))
            x += 12
    else:
        parts.append(box_at(x0, y, z + 24, x0 + 3.2, x1, z + 28))
        parts.append(box_at(x0, y, z, x0 + 3.2, x1, z + 3.2))
        yy = y + 8
        while yy < x1 - 6:
            parts.append(move(spindle(22), x0 + 1.6, yy, z + 2.4))
            yy += 12
    return union(parts)


def stair_flight(spec):
    x0, x1 = spec["x0"], spec["x1"]
    z_base = spec["z"] + 0.9
    parts = []
    for i in range(RISES):
        last = i == RISES - 1
        z1 = spec["z"] + (i + 1) * RISE - (0.45 if last else 0.0)
        if spec["up"] > 0:
            y_b = spec["y0"] + i * TREAD + (2.6 if last else 3.4)
            y_a = spec["y0"]
        else:
            y_a = spec["y1"] - i * TREAD - (2.6 if last else 3.4)
            y_b = spec["y1"]
        parts.append(box_at(x0 + 3, y_a, z_base, x1 - 3, y_b, z1))
    # Newels and a sloped handrail the open side can see.
    parts.append(cyl_z(3.4, F2F - 12, x0 + 4, spec["y0"] + 4, spec["z"], 8))
    parts.append(box_at(x1 - 6, spec["y0"] + 12, spec["z"] + 48, x1 - 2.6, spec["y1"] - 8, spec["z"] + F2F - 2))
    return union(parts)


def ceiling_puck(cx, cy, z_plate_bottom):
    shell = cyl_z(CEILING_OD / 2, CEILING_DEPTH, cx, cy, z_plate_bottom - CEILING_DEPTH, 16)
    neck = cyl_z(3.2, 3.0, cx, cy, z_plate_bottom - 1.6, 12)
    return [shell, neck]


def ceiling_voids(cx, cy, z_plate_bottom):
    z0 = z_plate_bottom - CEILING_DEPTH
    cavity_z = z0 + 2.0
    return [
        box_at(cx - 3, cy - 3, cavity_z, cx + 3, cy + 3, cavity_z + 3),
        box_at(cx - 4, cy - 4, z0 + 1.0, cx + 4, cy + 4, cavity_z + 0.05),
        box_at(cx - 3.2, cy - 0.6, z0 - 0.4, cx - 0.7, cy + 0.6, z0 + 1.25),
        box_at(cx + 0.7, cy - 0.6, z0 - 0.4, cx + 3.2, cy + 0.6, z0 + 1.25),
        cyl_z(FEED_D / 2, 8, cx, cy, z_plate_bottom - 2.5, 10),
    ]


def gable_fret(x_face, y0, y1, z0, z_peak, y_peak):
    """Barge and a pierced gable panel, thickness toward +X or -X depending on sign later."""
    panel = hull([
        (0, y0, z0), (3.2, y0, z0), (0, y1, z0), (3.2, y1, z0),
        (0, y_peak, z_peak), (3.2, y_peak, z_peak),
    ])
    cuts = []
    y = y0 + 14
    while y < y1 - 14:
        z = z0 + 8 + (z_peak - z0) * (1 - abs(y - y_peak) / max(1, (y1 - y0) / 2)) * 0.45
        cuts.append(cyl_z(3.2, 6, 1.6, y, z, 8))
        y += 16
    # Crescent discovery, raised by leaving a moon of material: cut a full disc then we add a crescent back.
    return difference(panel, cuts)


def owl(x, y, z):
    body = cyl_z(4.2, 6.5, x, y, z, 10)
    head = cyl_z(3.4, 4.5, x, y, z + 5.5, 10)
    ear_l = box_at(x - 2.4, y - 1.2, z + 8.5, x - 0.4, y + 1.2, z + 11.5)
    ear_r = box_at(x + 0.4, y - 1.2, z + 8.5, x + 2.4, y + 1.2, z + 11.5)
    return union([body, head, ear_l, ear_r])


CATALOG = {}
INSTANCES = []
FIXTURES = []


def add_part(name, mesh, note):
    extents = [round(float(v), 2) for v in (mesh.bounds[1] - mesh.bounds[0])]
    if any(extents[i] > FIT_MAX[i] + 0.4 for i in range(3)):
        raise RuntimeError(f"{name} exceeds bed allowance {extents}")
    CATALOG[name] = {"mesh": mesh, "note": note, "extents": extents, "triangles": int(len(mesh.faces)), "volume": round(float(mesh.volume), 1)}
    print(f"part {name} {extents}", flush=True)


def shift(mesh):
    local = mesh.copy()
    origin = local.bounds[0].copy()
    local.apply_translation(-origin)
    return local, [float(v) for v in origin]


def publish(name, mesh, note, iid, role, color, motion=None, explode=None, extra=None):
    local, origin = shift(mesh)
    add_part(name, local, note)
    INSTANCES.append({
        "id": iid, "part": name, "role": role, "color": color,
        "motion": motion, "explode_mm": explode or [0, 0, 0],
        "world": mesh, "place": origin, "extra": extra or {},
    })


def build():
    build_foundations()
    build_floors()
    build_fixed_walls()
    build_facades()
    build_roofs()
    build_porch()
    build_stairs()
    build_furniture()
    build_service_and_coupons()


def build_foundations():
    main = box_at(MX0, MY0, 4, MX1, MY1, BASE)
    main = union([main, box_at(MX0, MY0 - 58, 4, 360, MY0 + 2, BASE), *brick_courses(MX0, MY0 - 58, MX1, MY1, BASE, "sne")])
    # Water table
    main = union([main, box_at(MX0 - 2, MY0 - 60, BASE - 4, MX1 + 2, MY1 + 2, BASE - 1.2)])
    publish("qa4_foundation_main_v4", cleanup(main, "foundation"), "Masonry base and porch deck. Brick courses are in the mesh.", "foundation", "structure", BRICK, explode=[0, 0, 0])
    pts = octagon(TCX, TCY, TR + 6)
    turret = union([prism(pts, 0, BASE), prism(octagon(TCX, TCY, TR + 10), BASE - 4, BASE - 1.2)])
    turret = cleanup(difference(turret, [box_at(MX0 - 4, -40, -2, 700, 500, BASE + 8)]), "turret base")
    publish("qa4_foundation_turret_v4", cleanup(turret, "turret base"), "Octagonal masonry base of the turret.", "turret-base", "structure", BRICK, explode=[-20, -10, 0])


def floor_slab(z_top, opening):
    slab = box_at(MX0 + 4, MY0 + 4, z_top - FLOOR_T, MX1 - 4, MY1 - 4, z_top)
    ribs = []
    y = MY0 + 16
    while y < MY1 - 16:
        ribs.append(box_at(MX0 + 18, y, z_top - 0.7, MX1 - 18, y + 1.5, z_top + 0.05))
        y += 12
    mesh = union([slab, *[r for r in ribs if r]])
    if opening:
        mesh = difference(mesh, [box_at(*opening)])
    return mesh


def build_floors():
    open2 = (WELL1[0], WELL1[1], L2 - FLOOR_T - 0.3, WELL1[2], WELL1[3], L2 + 0.8)
    open3 = (WELL2[0], WELL2[1], L3 - FLOOR_T - 0.3, WELL2[2], WELL2[3], L3 + 0.8)
    publish("qa4_floor_l2_v4", cleanup(floor_slab(L2, open2), "floor l2"), "First floor. The opening is the lower stair.", "floor-l2", "floor", WOOD, explode=[0, 0, 12])
    publish("qa4_floor_l3_v4", cleanup(floor_slab(L3, open3), "floor l3"), "Attic floor. The opening is the upper stair.", "floor-l3", "floor", WOOD, explode=[0, 0, 24])
    lobe = difference(prism(octagon(TCX, TCY, TR - 10), 0, FLOOR_T), [box_at(MX0 + 1.2, -20, -2, 500, 400, 20)])
    lobe = cleanup(lobe, "turret floor")
    publish("qa4_floor_turret_v4", lobe, "Turret floor disc, used on the first floor and the loft.", "turret-floor-l2", "floor", WOOD, explode=[-12, 0, 12])
    INSTANCES[-1]["world"] = move(lobe, 0, 0, L2 - FLOOR_T)
    INSTANCES[-1]["place"] = [float(v) for v in INSTANCES[-1]["world"].bounds[0]]
    world3 = move(lobe, 0, 0, L3 - FLOOR_T)
    INSTANCES.append({
        "id": "turret-floor-l3", "part": "qa4_floor_turret_v4", "role": "floor", "color": WOOD,
        "motion": None, "explode_mm": [-12, 0, 24], "world": world3,
        "place": [float(v) for v in world3.bounds[0]], "extra": {},
    })


def fixed_shell(floor, storey_name):
    """Rear wall, partitions, and ceiling plate. Front and the play side stay open."""
    z0 = floor + 0.35
    z_plate = floor + CLEAR
    z1 = plate_top(floor)
    parts = []
    # Rear wall
    parts.append(box_at(MX0 + 6, MY1 - 8, z0, MX1 - 6, MY1, z1))
    # Left return only behind the turret joint, a short shear wall
    parts.append(box_at(MX0, MY0 + 70, z0, MX0 + 8, MY1 - 8, z1))
    # Ceiling plate, open at the stair well later
    parts.append(box_at(MX0 + 8, MY0 + 8, z_plate, MX1 - 8, MY1 - 8, z1))
    # Front header, inset so a facade can pass outside it
    parts.append(box_at(MX0 + 10, MY0 + 2, z_plate - 8, MX1 - 10, MY0 + 10, z1))
    # Kitchen partition with a door
    parts.append(box_at(356, MY0 + 24, z0, 364, MY1 - 4, z1))
    cuts = [box_at(350, 90, z0, 370, 142, floor + 80)]
    # Rear window
    cuts.append(window_hole("+y", 250, MY1, floor + 28, 36, 52, 12))
    # Stair well through this storey's plate
    if storey_name == "l1":
        cuts.append(box_at(WELL1[0], WELL1[1], z_plate - 1, WELL1[2], WELL1[3], z1 + 1))
    if storey_name == "l2":
        cuts.append(box_at(WELL2[0], WELL2[1], z_plate - 1, WELL2[2], WELL2[3], z1 + 1))
    # Service chase added outside the rear wall, not through a corner post
    parts.append(box_at(360, MY1 - 2, z0, 400, MY1 + 16, z1))
    cuts.append(box_at(368, MY1 + 4, z0 + 2, 368 + RISER[0], MY1 + 17, z1 - 2))
    mesh = difference(union(parts), cuts)
    trim = sash("+y", 250, MY1, floor + 28, 36, 52)
    return union([mesh, *trim])


def build_fixed_walls():
    for floor, name, iid in ((L1, "l1", "walls-l1"), (L2, "l2", "walls-l2")):
        mesh = cleanup(fixed_shell(floor, name), name)
        publish(f"qa4_walls_{name}_v4", mesh, "Fixed rear wall, partition, and ceiling plate. Facades are separate.", iid, "structure", PLASTER, explode=[0, 20, 8 if name == "l2" else 0], extra={"plate_top": plate_top(floor)})
    # Attic knee and ridge beam so the roof has a seat that does not depend on a facade
    z_eave = L3 + 6
    knee = union([
        box_at(200, MY0 + 6, L3 + 0.4, MX1 - 10, MY0 + 14, z_eave),
        box_at(200, MY1 - 14, L3 + 0.4, MX1 - 10, MY1 - 4, z_eave),
        box_at(200, MY0 + 6, L3 + 0.4, 214, MY1 - 4, z_eave),
        box_at(MX1 - 18, MY0 + 6, L3 + 0.4, MX1 - 8, MY1 - 4, z_eave),
    ])
    publish("qa4_attic_frame_v4", cleanup(knee, "attic"), "Knee walls. The main roof sits on them.", "attic-frame", "structure", PLASTER, explode=[0, 0, 30], extra={"plate_top": z_eave})
    cap = cleanup(prism(octagon(TCX, TCY, TR - 14), 0, 4.0), "turret cap")
    world = move(cap, 0, 0, plate_top(L3) - 4)
    publish("qa4_turret_cap_v4", cap, "Plate under the turret cone.", "turret-cap", "structure", PLASTER, explode=[-10, 0, 30])
    INSTANCES[-1]["world"] = world
    INSTANCES[-1]["place"] = [float(v) for v in world.bounds[0]]
    # Lights in the fixed plates
    add_lights()


def add_lights():
    """Record fixtures. Voids are cut into the plates by a second pass below."""
    plan = [
        ("parlor-ceiling", "ceiling", "parlor", 230, 100, L1, "parlor"),
        ("entry-ceiling", "ceiling", "entry", 250, 78, L1, "entry"),
        ("kitchen-ceiling", "ceiling", "kitchen", 386, 150, L1, "kitchen"),
        ("bedroom-ceiling", "ceiling", "bedroom", 190, 90, L2, "bedroom"),
        ("bath-ceiling", "ceiling", "bath", 380, 70, L2, "bath"),
        ("landing-ceiling", "ceiling", "landing", 300, 180, L2, "landing"),
        ("attic-ceiling", "ceiling", "attic", 300, 120, L3, "attic"),
        ("turret-ceiling", "ceiling", "turret", TCX, TCY, L3, "turret"),
    ]
    # Applied as geometry in the plates via small added pucks unioned, voids differenced.
    # Done here by rebuilding is too late; fixtures are separate ivory/brass parts
    # seated 0.3 mm under the plate so they stay on the fixed frame.
    for fid, kind, room, x, y, floor, circuit in plan:
        z = floor + CLEAR - 0.3
        puck = cleanup(union(ceiling_puck(0, 0, CEILING_DEPTH)), fid)
        # local puck hangs below z=0
        world = move(puck, x, y, z - CEILING_DEPTH)
        # The helper built a puck whose shell occupies z=0..7 in local after cleanup shift? 
        # ceiling_puck uses z_plate_bottom as the top. We published via cleanup which does not shift.
        FIXTURES.append({"id": fid, "kind": kind, "room": room, "x": x, "y": y, "z": z - CEILING_DEPTH, "storey": 1 if floor == L1 else (2 if floor == L2 else 3), "circuit": circuit})
    # One shared puck mesh instanced
    puck = cleanup(union(ceiling_puck(0, 0, CEILING_DEPTH) + [
        # medallion
        cyl_z(9, 1.4, 0, 0, CEILING_DEPTH - 1.2, 16),
    ]), "puck")
    local, _ = shift(puck)
    add_part("qa4_ceiling_puck_v4", local, "Rigid ceiling puck. 6 x 6 x 3 cavity is provisional, not a measured LED.")
    # voids must exist in the puck. Rebuild with voids.
    solid = union(ceiling_puck(0, 0, CEILING_DEPTH) + [cyl_z(9, 1.4, 0, 0, CEILING_DEPTH - 1.2, 16)])
    solid = cleanup(difference(solid, ceiling_voids(0, 0, CEILING_DEPTH)), "puck voids")
    CATALOG["qa4_ceiling_puck_v4"]["mesh"] = shift(solid)[0]
    CATALOG["qa4_ceiling_puck_v4"]["triangles"] = int(len(solid.faces))
    CATALOG["qa4_ceiling_puck_v4"]["volume"] = round(float(solid.volume), 1)
    for fix in FIXTURES:
        if fix["kind"] != "ceiling":
            continue
        floor = {1: L1, 2: L2, 3: L3}[fix["storey"]]
        top = floor + CLEAR - 1.8
        cx = (solid.bounds[0][0] + solid.bounds[1][0]) / 2
        cy = (solid.bounds[0][1] + solid.bounds[1][1]) / 2
        world = move(solid, fix["x"] - cx, fix["y"] - cy, top - float(solid.bounds[1][2]))
        INSTANCES.append({
            "id": fix["id"], "part": "qa4_ceiling_puck_v4", "role": "light", "color": BRASS,
            "motion": None, "explode_mm": [0, 0, 18], "world": world,
            "place": [float(v) for v in world.bounds[0]],
            "extra": {},
        })


def facade_wall(bounds, face, windows, door=False):
    x0, y0, z0, x1, y1, z1 = bounds
    if face == "-y":
        body = box_at(x0, y1 - 3.6, z0, x1, y1, z1)
        stile_l = box_at(x0, y1 - 8, z0, x0 + 14, y1, z1)
        stile_r = box_at(x1 - 14, y1 - 8, z0, x1, y1, z1)
        skin = courses(x0 + 10, y1 - 3.6, z0, x1 - 10, y1, z1, "-y")
        cuts, trim = [], []
        for win in windows:
            cuts.append(window_hole(face, win["x"], y1 - 3.6, win["z"], win["w"], win["h"]))
            trim += sash(face, win["x"], y1 - 3.6, win["z"], win["w"], win["h"])
        if door:
            cuts.append(window_hole(face, (x0 + x1) / 2 - 16, y1 - 3.6, z0 - 0.2, 32, 52))
            trim += sash(face, (x0 + x1) / 2 - 16, y1 - 3.6, z0 + 36, 32, 28)
        zc = [z0 + (z1 - z0) * t for t in (0.28, 0.55, 0.8)]
        for sx in (x0 + 7, x1 - 7):
            cuts += magnet_cuts((sx, y1), (0, -1), zc)
        mesh = union([difference(union([body, stile_l, stile_r, *skin]), cuts), *trim])
    elif face == "+x":
        body = box_at(x1 - 3.6, y0, z0, x1, y1, z1)
        stile_a = box_at(x1 - 8, y0, z0, x1, y0 + 14, z1)
        stile_b = box_at(x1 - 8, y1 - 14, z0, x1, y1, z1)
        skin = courses(x1 - 3.6, y0 + 10, z0, x1, y1 - 10, z1, "+x")
        cuts, trim = [], []
        for win in windows:
            cuts.append(window_hole(face, x1, win["y"], win["z"], win["w"], win["h"]))
            trim += sash(face, x1 - 3.6, win["y"], win["z"], win["w"], win["h"])
        zc = [z0 + (z1 - z0) * t for t in (0.28, 0.55, 0.8)]
        for sy in (y0 + 7, y1 - 7):
            cuts += magnet_cuts((x1, sy), (-1, 0), zc)
        mesh = union([difference(union([body, stile_a, stile_b, *skin]), cuts), *trim])
    else:
        raise ValueError(face)
    return cleanup(mesh, face)


def build_facades():
    def span(floor):
        z0 = floor + 2
        z1 = floor + CLEAR - 1
        return z0, z1
    jobs = []
    for index, floor in enumerate((L1, L2)):
        z0, z1 = span(floor)
        win_y = floor + 24
        jobs.append((f"qa4_facade_front_l{index+1}_v4", f"front-l{index+1}", (200, -0.45 - 3.6, z0, MX1 - 2, -0.45, z1), "-y",
                     [{"x": 230, "z": win_y, "w": 34, "h": 58}, {"x": 300, "z": win_y, "w": 34, "h": 58}, {"x": 360, "z": win_y, "w": 34, "h": 58}],
                     index == 0, [0, -PULL, 0]))
        jobs.append((f"qa4_facade_side_l{index+1}_v4", f"side-l{index+1}", (MX1 + 0.45, MY0 + 8, z0, MX1 + 0.45 + 3.6, MY1 - 8, z1), "+x",
                     [{"y": 70, "z": win_y, "w": 34, "h": 56}, {"y": 140, "z": win_y, "w": 34, "h": 56}],
                     False, [PULL, 0, 0]))
    z0, z1 = span(L3)
    # Attic front is the decorated gable wall, full width to the corners.
    jobs.append(("qa4_facade_front_l3_v4", "front-l3", (210, -0.45 - 3.6, z0, 390, -0.45, z0 + 70), "-y",
                 [{"x": 280, "z": L3 + 16, "w": 30, "h": 40}], False, [0, -PULL, 0]))
    for part, iid, bounds, face, windows, door, pull in jobs:
        mesh = facade_wall(bounds, face, windows, door)
        group = "end" if face == "+x" else "front"
        publish(part, mesh, "Full-width facade shell. Straight pull. Magnets only.", iid, "facade", SAGE,
                {"group": group, "pull": pull}, [pull[0] * 0.7, pull[1] * 0.7, 10])
    build_turret_shell()


def build_turret_shell():
    """Three front facets of the octagon, stacked as one shell per storey is heavy; one shell for the exposed drum."""
    pts = octagon(TCX, TCY, TR)
    inner = octagon(TCX, TCY, TR - 4.2)
    outer = prism(pts, L1 + 1, plate_top(L2) - 2)
    hole = prism(inner, L1 - 1, plate_top(L2))
    # Keep only the street-facing half by cutting away +Y and the house overlap.
    shell = difference(outer, [hole, box_at(TCX - 10, TCY + 8, L1 - 2, TCX + TR + 8, TCY + TR + 8, plate_top(L2))])
    # Windows on two front flats. Approximate with boxes in world axes.
    cuts = []
    for z in (L1 + 26, L2 + 26):
        cuts.append(box_at(TCX - 16, TCY - TR - 2, z, TCX + 16, TCY - TR + 10, z + 48))
        cuts.append(box_at(TCX - TR - 2, TCY - 20, z, TCX - TR + 12, TCY + 16, z + 46))
    shell = difference(shell, cuts)
    # Clapboard rings
    rings = []
    z = L1 + 4
    while z < plate_top(L2) - 8:
        rings.append(prism(octagon(TCX, TCY, TR + 0.9), z, z + 2.4))
        z += 5.4
    shell = difference(union([shell, *rings]), [prism(octagon(TCX, TCY, TR - 1.2), L1, plate_top(L2)), *cuts, box_at(MX0 - 1.0, -40, L1 - 4, 700, 500, plate_top(L2) + 4)])
    publish("qa4_turret_shell_v4", cleanup(shell, "turret shell"), "Street facets of the turret through the first floor.", "turret-shell", "structure", SAGE, explode=[-16, -10, 0])
    upper = prism(octagon(TCX, TCY, TR), L3 + 0.8, plate_top(L3) - 1.0)
    upper = difference(upper, [
        prism(octagon(TCX, TCY, TR - 4.2), L3 - 1, plate_top(L3)),
        box_at(TCX - 14, TCY - TR - 1, L3 + 16, TCX + 14, TCY - TR + 8, L3 + 52),
        box_at(MX0 - 1, -40, L3 - 2, 700, 500, plate_top(L3)),
    ])
    publish("qa4_turret_loft_v4", cleanup(upper, "turret loft"), "Turret loft drum under the cone.", "turret-loft", "structure", SAGE, explode=[-16, -8, 20])


def build_roofs():
    eave = L3 + 6 + GAP
    ridge = L3 + 148
    main = gable_roof(206, MY0 - 8, MX1 + 8, MY1 + 6, eave, ridge)
    front = cross_gable(250, MY0 - 22, 360, MY0 + 18, eave + 2, eave + 48)
    chim = box_at(304, 116, ridge - 46, 330, 148, ridge + 16)
    chim = union([chim, box_at(302, 114, ridge + 12, 332, 150, ridge + 20)])
    roof = cleanup(union([main, front, chim]), "main roof")
    publish("qa4_roof_main_v4", roof, "Main roof and street cross-gable, one shell, shingle courses in the mesh.", "roof-main", "roof", SLATE,
            {"group": "roof", "lift": [0, 0, 90], "park": [0, -40, 150]}, [0, -20, 80],
            {"plate_top": eave - GAP, "seat_z": eave})
    # The published seat is the eave; bearing probe uses plate_top. Set plate to the attic frame top.
    INSTANCES[-1]["extra"]["plate_top"] = L3 + 6
    INSTANCES[-1]["extra"]["seat_z"] = L3 + 6 + GAP
    cone_h = 118
    cone_z = plate_top(L3) 
    # Turret third storey drum then cone
    drum = None
    rings = [cone_at(TR - 4, cone_h, TCX, TCY, cone_z, 8)]
    for i in range(12):
        z = cone_z + 6 + i * 8
        if z > cone_z + cone_h - 10:
            break
        r = (TR - 2) * (1 - (z - cone_z) / cone_h)
        rings.append(cyl_z(r + 1.3, 2.0, TCX, TCY, z, 8))
    turret_roof = cleanup(union(rings), "turret roof")
    publish("qa4_roof_turret_v4", turret_roof, "Octagonal drum and conical roof. Shingle rings are in the mesh.", "roof-turret", "roof", SLATE,
            {"group": "roof", "lift": [0, 0, 100], "park": [-30, -80, 160]}, [-20, -30, 90],
            {"plate_top": plate_top(L3), "seat_z": plate_top(L3) + GAP})
    # seat gap: cone starts at plate_top, should be plate_top+GAP. Shift world up by GAP.
    item = INSTANCES[-1]
    item["world"].apply_translation((0, 0, GAP))
    item["place"][2] += GAP
    item["extra"]["seat_z"] = plate_top(L3) + GAP


def build_porch():
    z_beam = L1 + CLEAR - 6
    posts = []
    for x, y in ((150, -32), (250, -32), (340, -32)):
        posts.append(move(column(z_beam - BASE - 1), x, y, BASE + 0.5))
        posts.append(move(bracket(), x - 6, y - 4, z_beam - 16))
    beam = box_at(130, -42, z_beam, 360, -18, z_beam + 8)
    rail_f = porch_rail(160, 320, -36, BASE + 0.6)
    steps = union([
        box_at(268, -70, 0.4, 324, -46, 6),
        box_at(272, -58, 6, 320, -44, 12),
        box_at(276, -50, 12, 316, -30, BASE + 8),
    ])
    porch = cleanup(union(posts + [beam, rail_f, steps]), "porch")
    publish("qa4_porch_v4", porch, "Wraparound porch: turned posts, brackets, balusters, and steps. Lifts off before the front wall is pulled.", "porch", "porch", IVORY,
            {"group": "porch", "lift": [0, 0, 130], "park": [0, -90, 40]}, [0, -40, 20])
    # Porch roof, slate, bears on the beam
    proof = box_at(70, -34, z_beam + 8 + GAP, 360, 2, z_beam + 14)
    fascia = box_at(66, -38, z_beam + 10, 364, -28, z_beam + 18)
    # shingle laps
    laps = []
    y = -34
    while y < 0:
        laps.append(box_at(72, y, z_beam + 12, 356, y + 7, z_beam + 15.2))
        y += 6.5
    side = None
    publish("qa4_porch_roof_v4", cleanup(union([proof, fascia, *laps]), "porch roof"), "Porch roof. Bears on the porch beam.", "porch-roof", "roof", SLATE,
            {"group": "roof", "lift": [0, 0, 80], "park": [0, -70, 70]}, [0, -30, 40],
            {"plate_top": z_beam + 8, "seat_z": z_beam + 8 + GAP})
    # Door, burgundy, on the front facade plane but its own part so the color is right. Same pull.
    door = union([
        box_at(294, -11.2, L1 + 3, 314, -7.6, L1 + 74),
        box_at(297, -12.0, L1 + 10, 311, -10.6, L1 + 32),
        box_at(297, -12.0, L1 + 40, 311, -10.6, L1 + 66),
    ])
    publish("qa4_door_v4", cleanup(door, "door"), "Front door. Pulls with the ground-floor facade. No hook.", "door", "facade", BURGUNDY,
            {"group": "front", "pull": [0, -PULL, 0]}, [0, -70, 6])
    # Entry lanterns on porch posts (fixed to the porch, so they lift with it). Two of them.
    lantern = cleanup(union([
        box_at(0, 0, 0, 8, 8, 12),
        box_at(1.2, -0.6, 2, 6.8, 1.2, 9),
    ]), "lantern")
    local, _ = shift(lantern)
    add_part("qa4_lantern_v4", local, "Porch lantern. 8 x 8 x 12 housing. Cavity is provisional.")
    for iid, x, y in (("lantern-w", 146, -52), ("lantern-e", 336, -52)):
        world = move(lantern, x, y, BASE + 62)
        INSTANCES.append({
            "id": iid, "part": "qa4_lantern_v4", "role": "light", "color": BRASS,
            "motion": {"group": "porch", "lift": [0, 0, 130]}, "explode_mm": [0, -20, 10],
            "world": world, "place": [float(v) for v in world.bounds[0]], "extra": {},
        })
        FIXTURES.append({"id": iid, "kind": "lantern", "room": "porch", "x": x + 4, "y": y + 4, "z": BASE + 66, "storey": 1, "circuit": "exterior"})


def build_stairs():
    publish("qa4_stair_lower_v4", cleanup(stair_flight(S1), "stair lower"), "Ground to the first floor. Fourteen rises, open to the side.", "stair-lower", "stair", WOOD_DARK, explode=[30, 0, 8])
    publish("qa4_stair_upper_v4", cleanup(stair_flight(S2), "stair upper"), "First floor to the attic and turret landing.", "stair-upper", "stair", WOOD_DARK, explode=[20, 0, 20])


def build_furniture():
    def bed():
        return cleanup(union([box_at(0, 0, 2, 42, 74, 12), box_at(0, 62, 8, 42, 74, 32), box_at(2, 4, 12, 40, 64, 16)]), "bed")
    def table():
        return cleanup(union([box_at(0, 0, 16, 36, 22, 18), box_at(2, 2, 0, 5, 5, 16), box_at(31, 2, 0, 34, 5, 16), box_at(2, 17, 0, 5, 20, 16), box_at(31, 17, 0, 34, 20, 16)]), "table")
    def counter():
        return cleanup(union([box_at(0, 0, 0, 46, 16, 28), box_at(4, 2, 28, 22, 14, 34)]), "counter")
    def tub():
        return cleanup(difference(box_at(0, 0, 0, 36, 22, 16), [box_at(3, 3, 6, 33, 19, 17)]), "tub")
    pieces = [
        ("qa4_bed_v4", bed(), "Bed.", "bed", (176, 80, L2 + 0.9)),
        ("qa4_table_v4", table(), "Parlor table.", "table", (200, 70, L1 + 0.8)),
        ("qa4_counter_v4", counter(), "Kitchen counter.", "counter", (368, 176, L1 + 0.8)),
        ("qa4_tub_v4", tub(), "Bath.", "tub", (372, 44, L2 + 0.9)),
    ]
    for name, mesh, note, iid, shift_by in pieces:
        publish(name, move(mesh, *shift_by), note, iid, "furniture", WOOD, explode=[0, 0, 16])


def retainer():
    bar = box_at(0.2, 0.2, 0, POCKET_DEPTH - 0.2, 6.2, 26)
    ear = box_at(0.8, -1.2, 3, POCKET_DEPTH - 0.6, 7.6, 22)
    return cleanup(union([bar, ear]), "retainer")


def coupon():
    frame = box_at(0, 0, 0, 40, 14, 72)
    cuts = []
    for zc in (20, 36, 52):
        cuts += magnet_cuts((12, 0), (0, 1), [zc])
        cuts += magnet_cuts((28, 0), (0, 1), [zc])
    frame = cleanup(difference(frame, cuts), "coupon frame")
    panel = box_at(6, -8, 6, 34, -0.4, 66)
    cuts = []
    for zc in (26, 42, 58):
        cuts += magnet_cuts((12, -0.4), (0, -1), [zc])
        cuts += magnet_cuts((28, -0.4), (0, -1), [zc])
    panel = cleanup(difference(panel, cuts), "coupon panel")
    return frame, panel


def polarity():
    bed = box_at(0, 0, 0, 42, 22, 6)
    return cleanup(difference(bed, [
        cyl_z((MAGNET_D + 0.4) / 2, 1.2, 12, 11, 4.9, 16),
        cyl_z((MAGNET_D + 0.4) / 2, 1.2, 30, 11, 4.9, 16),
    ]), "polarity")


def build_service_and_coupons():
    outer = box_at(0, 0, 0, 158, 104, 44)
    void = box_at(4, 8, 6, 154, 98, 36)
    mouth = box_at(8, 96, 8, 150, 106, 34)
    inlet = box_at(18, -0.4, 8, 40, 10, 24)
    cabinet = cleanup(difference(outer, [void, mouth, inlet]), "service")
    publish("qa4_service_bay_v4", move(cabinet, 250, MY1 + 20, 0), "Adult service bay behind the house. Clear volume 150 x 90 x 30.", "service-bay", "service", "#3d4650", explode=[0, 36, 0])
    frame, panel = coupon()
    publish("qa4_coupon_frame_v4", frame, "Straight-pull coupon, frame half. Same slot cutter. No hook.", "coupon-frame", "coupon", PLASTER, explode=[0, 0, 0])
    # place coupons off the house
    INSTANCES[-1]["world"] = move(frame, 620, 0, 0)
    INSTANCES[-1]["place"] = [620, 0, 0]
    publish("qa4_coupon_panel_v4", panel, "Straight-pull coupon, panel half.", "coupon-panel", "coupon", SAGE, {"group": "coupon", "pull": [0, -24, 0]})
    INSTANCES[-1]["world"] = move(panel, 626, -8, 6)
    INSTANCES[-1]["place"] = [626 + panel.bounds[0][0], -8 + panel.bounds[0][1], 6 + panel.bounds[0][2]]
    publish("qa4_retainer_v4", retainer(), "Magnet capture bar. It closes the disc. It does not fasten the facade.", "retainer", "coupon", "#777777")
    INSTANCES[-1]["world"] = move(retainer(), 640, 4, 20)
    INSTANCES[-1]["place"] = [float(v) for v in INSTANCES[-1]["world"].bounds[0]]
    publish("qa4_polarity_v4", polarity(), "Polarity aid. Shallow wells only. Do not leave discs in it.", "polarity", "coupon", "#dddddd")
    INSTANCES[-1]["world"] = move(polarity(), 680, 0, 0)
    INSTANCES[-1]["place"] = [680, 0, 0]
    # Gable owl, fixed on the attic frame side, a small discovery
    bird = cleanup(owl(0, 0, 0), "owl")
    publish("qa4_owl_v4", move(bird, 300, 8, L3 + 118), "Small owl under the front gable. Fixed trim, not a loose piece.", "owl", "trim", WOOD_DARK, explode=[0, -16, 10])
    crescent = cleanup(difference(cyl_z(7, 2.2, 0, 0, 0, 16), [cyl_z(5, 4, 2.2, 0, -1, 14)]), "crescent")
    publish("qa4_crescent_v4", move(crescent, TCX - 20, TCY - TR - 6, L2 + 20), "Crescent on the turret drum.", "crescent", "trim", IVORY, explode=[0, -12, 8])


def intersection_volume(a, b):
    hit = tm.boolean.intersection([a, b], engine="manifold")
    if hit is None or hit.is_empty:
        return 0.0
    volume = float(hit.volume)
    return volume if volume > 0 else 0.0


def overlaps(a, b):
    return not (
        a.bounds[1][0] < b.bounds[0][0] or a.bounds[0][0] > b.bounds[1][0]
        or a.bounds[1][1] < b.bounds[0][1] or a.bounds[0][1] > b.bounds[1][1]
        or a.bounds[1][2] < b.bounds[0][2] or a.bounds[0][2] > b.bounds[1][2]
    )


def moved(mesh, vector):
    copy = mesh.copy()
    copy.apply_translation(vector)
    return copy


def audits():
    failures = []
    house = [i for i in INSTANCES if i["role"] not in ("coupon",)]
    worst = 0.0
    worst_pair = None
    checked = 0
    for i in range(len(house)):
        for j in range(i + 1, len(house)):
            if not overlaps(house[i]["world"], house[j]["world"]):
                continue
            checked += 1
            volume = intersection_volume(house[i]["world"], house[j]["world"])
            if volume > worst:
                worst = volume
                worst_pair = (house[i]["id"], house[j]["id"], round(volume, 1))
            if volume > 1.0:
                failures.append({"pair": [house[i]["id"], house[j]["id"]], "mm3": round(volume, 1)})
                print(f" clash {house[i]['id']} {house[j]['id']} {volume:.1f}", flush=True)
    print("rest", checked, worst_pair, flush=True)
    roofs = []
    for item in house:
        if item["role"] != "roof":
            continue
        plate = item["extra"].get("plate_top")
        seat = item["extra"].get("seat_z")
        foot = item["world"].bounds
        probe = box_at(foot[0][0] + 8, foot[0][1] + 8, plate - 0.3, foot[1][0] - 8, foot[1][1] - 8, plate + 0.05)
        bearing, bearer = 0.0, None
        for other in house:
            if other["role"] not in ("structure", "porch"):
                continue
            if overlaps(probe, other["world"]):
                volume = intersection_volume(probe, other["world"])
                if volume > bearing:
                    bearing, bearer = volume, other["id"]
        roofs.append({"id": item["id"], "bodies": 1, "seat_gap_mm": None if seat is None else round(seat - plate, 3), "bearing_probe_mm3": round(bearing, 1), "bearer": bearer})
        if bearing < 80:
            failures.append({"roof": item["id"], "bearing": round(bearing, 1)})
    print("roofs", roofs, flush=True)
    # Straight pulls against parts that stay (roofs and porch lift off first).
    fixed_roles = {"structure", "floor", "furniture", "service", "trim", "light", "stair"}
    for item in house:
        if item["role"] != "facade":
            continue
        pull = item["motion"]["pull"]
        if item["motion"].get("slide") or item["motion"].get("lift"):
            failures.append({"motion": item["id"]})
        for dist in (0, 12, 28, 48):
            shifted = moved(item["world"], [pull[0] * dist / PULL, pull[1] * dist / PULL, 0])
            for other in house:
                if other["role"] not in fixed_roles:
                    continue
                if other.get("motion") and (other["motion"].get("lift") or other["motion"].get("pull")):
                    continue
                if overlaps(shifted, other["world"]):
                    volume = intersection_volume(shifted, other["world"])
                    if volume > 1.0:
                        failures.append({"sweep": item["id"], "mm": dist, "hit": other["id"], "mm3": round(volume, 1)})
                        print(f" sweep {item['id']} {dist} {other['id']} {volume:.1f}", flush=True)
    stairs = []
    overhead_roles = {"structure", "floor", "roof"}
    for spec, iid, target in ((S1, "stair-lower", L2), (S2, "stair-upper", L3)):
        mesh = next(i["world"] for i in house if i["id"] == iid)
        top = float(mesh.bounds[1][2])
        if spec["up"] > 0:
            well = box_at(spec["x0"] + 6, spec["y0"] + 16, target - 1, spec["x1"] - 6, spec["y1"] - 10, target + 1)
        else:
            well = box_at(spec["x0"] + 6, spec["y0"] + 10, target - 1, spec["x1"] - 6, spec["y1"] - 14, target + 1)
        blocked = 0
        for item in house:
            if "floor" in item["id"] and overlaps(well, item["world"]):
                blocked = max(blocked, intersection_volume(well, item["world"]))
        tight = HEADROOM
        for i in range(0, RISES - 1, 3):
            z_step = spec["z"] + (i + 1) * RISE
            y = spec["y0"] + i * TREAD + 5 if spec["up"] > 0 else spec["y1"] - i * TREAD - 5
            x = (spec["x0"] + spec["x1"]) / 2
            ceiling = min(z_step + 4 + HEADROOM, target - 2)
            if ceiling <= z_step + 8:
                continue
            probe = box_at(x - 2, y - 2, z_step + 4, x + 2, y + 2, ceiling)
            for item in house:
                if item["role"] not in overhead_roles or item["id"] == iid:
                    continue
                if overlaps(probe, item["world"]) and intersection_volume(probe, item["world"]) > 0.4:
                    if iid == "stair-upper" and tight == HEADROOM:
                        print(" headroom hit", item["id"], "step", i, flush=True)
                    tight = min(tight, 0)
                    break
        row = {"id": iid, "top_z": round(top, 2), "target": target, "top_gap_mm": round(target - top, 2), "well_blocked_mm3": round(blocked, 2), "headroom_sample_mm": tight}
        stairs.append(row)
        if blocked > 1:
            failures.append({"well": iid, "mm3": round(blocked, 1)})
        if target - top > 3 or top > target - 0.1:
            failures.append({"stair_top": iid, "gap": round(target - top, 2)})
        if tight < HEADROOM:
            failures.append({"headroom": iid})
    print("stairs", stairs, flush=True)
    return {"ok": not failures, "failures": failures[:20], "rest_pairs": checked, "worst_mm3": round(worst, 2), "worst_pair": worst_pair, "roofs": roofs, "stairs": stairs}


def legacy_interface():
    tile = tm.load(LEGACY_TILE)
    post = tm.load(LEGACY_POST)
    peg = post.copy()
    peg.apply_transform(rotation_matrix(math.pi, [1, 0, 0]))
    peg.apply_translation((15.875, 15.875, 11.0))
    return {
        "tile_bbox_mm": [round(float(v), 3) for v in tile.extents],
        "seated_peg_mm3": round(intersection_volume(tile, peg), 3),
        "snap_compatible": False,
        "note": "Measured on floor_tile_v0. This house does not use that socket.",
    }


def write_outputs(report, legacy):
    os.makedirs(STL_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    for name in os.listdir(STL_DIR):
        if name.endswith(".stl") and not name.startswith("qa4_"):
            os.remove(os.path.join(STL_DIR, name))
    for info in CATALOG.values():
        pass
    for name, info in CATALOG.items():
        info["mesh"].export(os.path.join(STL_DIR, name + ".stl"))
    house = [i for i in INSTANCES if i["role"] != "coupon"]
    mins = np.min([i["world"].bounds[0] for i in house], axis=0)
    maxs = np.max([i["world"].bounds[1] for i in house], axis=0)
    bom = {}
    instances = []
    for item in INSTANCES:
        bom[item["part"]] = bom.get(item["part"], 0) + 1
        instances.append({
            "id": item["id"], "part": item["part"], "role": item["role"], "color": item["color"],
            "motion": item["motion"], "explode_mm": item["explode_mm"],
            "transform": [[1, 0, 0, round(item["place"][0], 3)], [0, 1, 0, round(item["place"][1], 3)], [0, 0, 1, round(item["place"][2], 3)], [0, 0, 0, 1]],
        })
    facade_count = len([i for i in INSTANCES if i["role"] == "facade"])
    retainer_qty = facade_count * 4 + 2
    bom_rows = []
    for name, qty in sorted(bom.items()):
        row = {"part": name, "file": f"stl/{name}.stl", "qty": qty}
        if name == "qa4_retainer_v4":
            row["print_qty"] = retainer_qty
            row["note"] = "Shown once on the coupon. Print one more for every stile, shell and frame."
        bom_rows.append(row)
    count = len(FIXTURES)
    manifest = {
        "name": "Queen Anne Playhouse",
        "version": "4.0.0",
        "prior_version": "archive/v3.0.0",
        "also_archived": ["archive/v1.0.0", "archive/v2.0.0", "archive/v3.0.0"],
        "scale": "1:24",
        "description": "Octagonal turret, cross-gable, wraparound porch. Concept picture is the direction, not the CAD.",
        "concept_image": "concept/approved-direction.jpg",
        "concept_note": "Approved visual direction. Not engineered geometry and not a photograph of this CAD.",
        "units": "mm",
        "up_axis": "Z",
        "printer_nominal_bed_mm": list(BED),
        "fit_envelope_mm": list(FIT_MAX),
        "assembled_size_mm": {"x": round(float(maxs[0] - mins[0]), 1), "y": round(float(maxs[1] - mins[1]), 1), "z": round(float(maxs[2] - mins[2]), 1), "min_mm": [round(float(v), 1) for v in mins], "max_mm": [round(float(v), 1) for v in maxs]},
        "rooms": [
            {"id": "parlor", "storey": 1, "note": "Front-left, open to the turret alcove."},
            {"id": "entry", "storey": 1, "note": "Hall at the burgundy door. The lower stair leaves from here."},
            {"id": "kitchen", "storey": 1, "note": "Right of the entry, with the counter on the rear wall."},
            {"id": "bedroom", "storey": 2, "note": "First floor, left of the stair."},
            {"id": "bath", "storey": 2, "note": "First floor, right front."},
            {"id": "landing", "storey": 2, "note": "The lower flight arrives here. The upper flight leaves toward the turret."},
            {"id": "attic", "storey": 3, "note": "Under the cross-gable."},
            {"id": "turret", "storey": 3, "note": "Same floor as the attic, through the turret opening."},
        ],
        "plan": {"storeys": [
            {"storey": 1, "floor_z": L1, "rooms": [
                {"id": "parlor", "name": "Parlor", "x0": 170, "y0": 40, "x1": 280, "y1": 160},
                {"id": "turret", "name": "Turret", "x0": 80, "y0": 40, "x1": 168, "y1": 150},
                {"id": "entry", "name": "Entry", "x0": 280, "y0": 40, "x1": 340, "y1": 120},
                {"id": "kitchen", "name": "Kitchen", "x0": 344, "y0": 40, "x1": 410, "y1": 210},
                {"id": "porch", "name": "Porch", "x0": 70, "y0": -50, "x1": 360, "y1": 30},
            ], "doors": [{"id": "entry-kitchen", "x0": 328, "y0": 78, "x1": 344, "y1": 132}], "stairs": [{"id": "lower", "x0": WELL1[0], "y0": WELL1[1], "x1": WELL1[2], "y1": WELL1[3]}], "lights": [f for f in FIXTURES if f["storey"] == 1]},
            {"storey": 2, "floor_z": L2, "rooms": [
                {"id": "bedroom", "name": "Bedroom", "x0": 170, "y0": 40, "x1": 300, "y1": 200},
                {"id": "bath", "name": "Bath", "x0": 340, "y0": 40, "x1": 410, "y1": 120},
                {"id": "landing", "name": "Landing", "x0": 250, "y0": 180, "x1": 340, "y1": 220},
            ], "doors": [], "stairs": [{"id": "upper", "x0": WELL2[0], "y0": WELL2[1], "x1": WELL2[2], "y1": WELL2[3]}, {"id": "lower-well", "x0": WELL1[0], "y0": WELL1[1], "x1": WELL1[2], "y1": WELL1[3]}], "lights": [f for f in FIXTURES if f["storey"] == 2]},
            {"storey": 3, "floor_z": L3, "rooms": [
                {"id": "attic", "name": "Attic", "x0": 190, "y0": 50, "x1": 400, "y1": 200},
                {"id": "turret", "name": "Turret loft", "x0": 80, "y0": 40, "x1": 180, "y1": 150},
            ], "doors": [], "stairs": [{"id": "upper-well", "x0": WELL2[0], "y0": WELL2[1], "x1": WELL2[2], "y1": WELL2[3]}], "lights": [f for f in FIXTURES if f["storey"] == 3]},
        ]},
        "magnet": {
            "status": "NOMINAL_NOT_FIT_APPROVED",
            "nominal_mm": [MAGNET_D, MAGNET_T],
            "radial_clearance_per_side_mm": CLEAR_RADIAL,
            "axial_clearance_mm": CLEAR_AXIAL,
            "pocket_diameter_mm": round(POCKET_D, 2),
            "pocket_depth_mm": round(POCKET_DEPTH, 2),
            "mating_skin_mm": SKIN,
            "holding_force_calculated": False,
            "h3c_pause_profile": False,
            "retention": "magnetic_only_straight_pull",
            "capture_bar": "encapsulates the magnet only",
        },
        "lighting": {
            "architecture": "External regulated nominal 5V USB. Parallel warm-white 5-12V DC Chip/Nano LEDs, each with its own resistor.",
            "cavity_mm": list(LED_CAVITY),
            "cavity_status": "PROVISIONAL_NOT_FIT_VALIDATED",
            "ceiling_housing_mm": [CEILING_OD, CEILING_DEPTH],
            "exterior_housing_mm": list(SCONCE),
            "feedthrough_diameter_mm": FEED_D,
            "local_channel_mm": list(CHANNEL),
            "riser_clear_mm": list(RISER),
            "service_bay_clear_mm": list(BAY_CLEAR),
            "fixture_count": count,
            "research_scenario_leds": 24,
            "research_scenario_budget_A": 0.48,
            "house_budget_A_at_20mA": round(count * 0.02, 3),
            "budget_is_measured": False,
            "protection_finalized": False,
            "electrically_tested": False,
            "mains_inside": False,
            "fuse_nominated": False,
            "protection_note": "No fuse is selected. A 6V 0.5A PPTC is not sole protection and is not nominated from the LED count.",
            "fixtures": FIXTURES,
            "route": [
                "Puck or lantern on the fixed plate or the porch, never on a magnetic facade",
                "2 mm feed for bare leads only",
                "Resistor stays in the cornice pocket, not in the lamp",
                "Rear chase outside the corner posts, down to the adult bay",
            ],
            "supply_example": "Adafruit 501 is an out-of-stock example, not a kit to buy.",
        },
        "departures_from_concept": [
            "The picture is a render, not a measured drawing. Massing is matched; moulding profiles are thickened to about 1.2 mm so an FDM nozzle can make them.",
            "The pictured cutaway does not show a complete path onto the turret loft. This model adds a second flight from the first-floor landing to that floor.",
            "The porch stands in front of the ground-floor wall, so the porch lifts off before that wall is pulled straight out. The pull itself has no hook and no slide.",
            "Viewer colors are the intended sage, ivory, burgundy, and slate. A single printed part is one material until it is painted.",
            "Interior furnishings are a few wood pieces, not the fully dressed rooms in the picture.",
        ],
        "magnet_install_steps": [
            "Print the coupon and seat the discs before the house. The slot is the same cutter as the facade stiles.",
            "An adult inserts a nominal 5.0 x 2.8 mm disc, then slides the capture bar in from the top of the stile.",
            "The bar closes the magnet. It does not catch the frame. Holding force was not measured.",
            "Polarity: use the shallow fixture, then take the discs out.",
            "Lift the porch off before pulling the front wall. Side walls pull straight out with the porch still down.",
        ],
        "limits": [
            "Not printed. No slicer run, no strength test, no tip-over test, no magnet pull test, no electrical test.",
            "Roof uplift is not locked. Porch and roofs are gravity seated.",
            "Magnetic support of the facades is unverified.",
            "LED cavity and 5 V current are unknown. No fuse was chosen from the milliamp sum.",
            "Not a toy-safety certification.",
        ],
        "cameras": {
            "closed": {"position": [820, -680, 360], "target": [230, 80, 190]},
            "open": {"position": [720, 20, 220], "target": [280, 130, 150]},
            "stairs": {"position": [240, 48, 70], "target": [320, 150, 100]},
        },
        "legacy_interface": legacy,
        "validation": {
            "printed": False, "measured": False, "physically_verified": False, "forces_tested": False,
            "h3c_sliced": False, "h3c_pause_profile": False, "electrically_tested": False,
            "protection_finalized": False, "led_fit_validated": False, "cad_validated": report["ok"],
        },
        "parts": [{"id": name, "file": f"stl/{name}.stl", "note": info["note"], "triangles": info["triangles"], "volume_mm3": info["volume"], "watertight": True, "bodies": 1, "bbox_mm": info["extents"], "fits_brim_allowance": True} for name, info in CATALOG.items()],
        "bom": bom_rows,
        "instances": instances,
    }
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    report["triangles"] = sum(info["triangles"] for info in CATALOG.values())
    report["instance_count"] = len(instances)
    report["fixture_count"] = count
    report["assembly_mm"] = manifest["assembled_size_mm"]
    with open(os.path.join(REPORT_DIR, "validation.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    return manifest


def main():
    build()
    print("audit", len(INSTANCES), flush=True)
    report = audits()
    legacy = legacy_interface()
    manifest = write_outputs(report, legacy)
    print(json.dumps({"ok": report["ok"], "failures": report["failures"][:8], "parts": len(manifest["parts"]), "instances": len(manifest["instances"]), "fixtures": report["fixture_count"]}, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
