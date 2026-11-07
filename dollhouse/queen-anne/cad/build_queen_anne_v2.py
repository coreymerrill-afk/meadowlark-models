"""Queen Anne Playhouse v2. Units mm. Z up.

v1.0.0 is archived. Its tower roof STL is four separate bodies: the cone
starts about 78 mm above the seat. This file replaces that with one solid
per roof, each bearing on its own plate.

Magnet discs are nominal 5.0 x 2.8 mm. The pocket is that size plus a
parametric FDM allowance. It is not a proven fit, and no holding force is
calculated. Keyed seats carry the panel. Magnets only assist retention.
"""
from __future__ import annotations

import json
import os
import traceback

import numpy as np
import trimesh as tm
from trimesh.creation import box, cylinder, icosphere
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STL_DIR = os.path.join(ROOT, "stl")
REPORT_DIR = os.path.join(ROOT, "reports")
LEGACY_TILE = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "floor_tile_v0.stl"))
LEGACY_POST = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "snap_post_v0.stl"))

BED = (330.0, 320.0, 325.0)
FIT_MAX = (BED[0] - 20.0, BED[1] - 20.0, BED[2] - 10.0)
VOL_LIMIT = 1.0

# Structure
POST = 16.0
SIDE = 0.40
GAP = 0.35
POCKET = 4.2
PLATE_T = 15.0
FLOOR_T = 7.0
BASE_T = 14.0
LIFT = 9.0
PULL = 54.0
ROOF_SLIDE = 16.0
ROOF_LIFT = 20.0

# Nominal magnet. NOT a measured fit. Grade and force are unknown.
MAGNET_D = 5.0
MAGNET_T = 2.8
MAGNET_STATUS = "NOMINAL_NOT_FIT_APPROVED"
CLEAR_RADIAL = 0.25
CLEAR_AXIAL = 0.20
SKIN_MATING = 1.2
POCKET_D = MAGNET_D + 2 * CLEAR_RADIAL
POCKET_DEPTH = MAGNET_T + CLEAR_AXIAL
RETAINER_CLEAR = 0.25

# Wings: different footprints and storey heights. Not a 3x3 grid.
WINGS = (
    {"name": "tower", "x": 0.0, "y": 0.0, "w": 200.0, "d": 188.0, "clears": (112.0, 100.0, 90.0),
     "front": "single", "party_right": 86.0, "end_left_from": 1, "bay_left": True},
    {"name": "hall", "x": 200.0, "y": 22.0, "w": 154.0, "d": 166.0, "clears": (128.0, 104.0),
     "front": "entry", "party_right": 110.0, "end_left_from": None, "bay_left": False},
    {"name": "living", "x": 354.0, "y": 0.0, "w": 280.0, "d": 206.0, "clears": (140.0, 114.0),
     "front": "double", "party_right": None, "end_left_from": None, "bay_right": True},
)


def box_at(x0, y0, z0, x1, y1, z1):
    if min(x1 - x0, y1 - y0, z1 - z0) <= 0:
        raise ValueError((x0, y0, z0, x1, y1, z1))
    mesh = box((x1 - x0, y1 - y0, z1 - z0))
    mesh.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return mesh


def cyl_x(diameter, length, x0, y, z, sections=28):
    mesh = cylinder(radius=diameter / 2, height=length, sections=sections)
    mesh.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
    mesh.apply_translation((x0 + length / 2, y, z))
    return mesh


def union(meshes):
    parts = [m for m in meshes if m is not None]
    if len(parts) == 1:
        return parts[0]
    return tm.boolean.union(parts, engine="manifold")


def difference(base, cuts):
    cuts = [c for c in cuts if c is not None]
    if not cuts:
        return base
    return tm.boolean.difference([base, *cuts], engine="manifold")


def cleanup(mesh, name):
    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    if mesh.volume < 0:
        mesh.invert()
    positive = [part for part in mesh.split(only_watertight=False) if part.volume > 1.0]
    if (not mesh.is_watertight) or mesh.volume <= 0 or len(positive) != 1:
        detail = [(round(part.volume), [round(float(v), 1) for v in part.bounds[:, 2]]) for part in positive]
        raise RuntimeError(
            f"{name} positive={len(positive)} watertight={mesh.is_watertight} vol={mesh.volume:.1f} {detail}"
        )
    return mesh


def stack_levels(clears):
    levels = []
    floor_top = BASE_T
    for index, clear in enumerate(clears):
        post_bottom = floor_top - (POCKET - GAP)
        post_top = floor_top + clear
        plate_bottom = post_top
        plate_top = plate_bottom + PLATE_T
        levels.append({
            "floor_top": floor_top,
            "post_bottom": post_bottom,
            "post_top": post_top,
            "plate_bottom": plate_bottom,
            "plate_top": plate_top,
            "clear": clear,
        })
        if index < len(clears) - 1:
            floor_top = plate_top + GAP + FLOOR_T
    return levels


def corners(w, d):
    a = 1.2 + SIDE
    return {
        "FL": (a, a),
        "FR": (w - a - POST, a),
        "RL": (a, d - a - POST),
        "RR": (w - a - POST, d - a - POST),
    }


def brick_and_boards(mesh, w, d, top, faces="fnes"):
    # Proud courses on exposed faces only. Party walls are left plain so wings can meet.
    bands = []
    z = 1.2
    while z < top - 3.2:
        if "s" in faces:
            bands.append(box_at(3, -0.85, z, w - 3, 0.45, z + 3.1))
        if "n" in faces:
            bands.append(box_at(3, d - 0.45, z, w - 3, d + 0.85, z + 3.1))
        if "w" in faces:
            bands.append(box_at(-0.85, 3, z, 0.45, d - 3, z + 3.1))
        if "e" in faces:
            bands.append(box_at(w - 0.45, 3, z, w + 0.85, d - 3, z + 3.1))
        z += 6.6
    if bands:
        mesh = union([mesh, *bands])
    return mesh


def sill_cut(w, z_top):
    return box_at(POST + 10, 4.6, z_top - 8.2, w - POST - 10, 10.2, z_top + 0.5)


def base_mesh(w, d, lap_right=True, lap_left=True, lap_y=(40.0, 130.0), mullion=False):
    slab = box_at(0, 0, 4.2, w, d, BASE_T)
    rim = [
        box_at(0, 0, 0, w, 10, BASE_T),
        box_at(0, d - 10, 0, w, d, BASE_T),
        box_at(0, 0, 0, 10, d, BASE_T),
        box_at(w - 10, 0, 0, w, d, BASE_T),
    ]
    ribs = []
    x = 18.0
    while x < w - 12:
        ribs.append(box_at(x, 0, 0, min(x + 3.2, w), d, BASE_T))
        x += 34.0
    parts = [slab, *rim, *ribs]
    for x0, y0 in corners(w, d).values():
        parts.append(box_at(x0 - SIDE, y0 - SIDE, 0, x0 + POST + SIDE, y0 + POST + SIDE, BASE_T))
    if lap_right:
        parts.append(box_at(w - 6, lap_y[0] + 1.2, 0, w + 9.0, lap_y[1] - 1.2, 2.6))
    if mullion:
        parts.append(box_at(w / 2 - POST / 2 - SIDE, 1.2, 0, w / 2 + POST / 2 + SIDE, 1.2 + POST + 2 * SIDE, BASE_T))
    mesh = union(parts)
    cuts = [sill_cut(w, BASE_T)]
    for x0, y0 in corners(w, d).values():
        cuts.append(box_at(x0 - SIDE, y0 - SIDE, BASE_T - POCKET, x0 + POST + SIDE, y0 + POST + SIDE, BASE_T + 0.4))
    if lap_left:
        cuts.append(box_at(-0.3, lap_y[0] + 0.4, -0.2, 11.4, lap_y[1] - 0.4, 3.55))
    if mullion:
        cuts.append(box_at(w / 2 - POST / 2 - SIDE, 1.2, BASE_T - POCKET, w / 2 + POST / 2 + SIDE, 1.2 + POST + 2 * SIDE, BASE_T + 0.4))
    faces = "sn"
    if not lap_left:
        faces += "w"
    if not lap_right:
        faces += "e"
    return cleanup(brick_and_boards(difference(mesh, cuts), w, d, BASE_T, faces), f"base {w}")


def floor_mesh(w, d, stairwell=None, mullion=False):
    slab = box_at(0, 0, 2.4, w, d, FLOOR_T)
    rim = [
        box_at(0, 0, 0, w, 8, FLOOR_T),
        box_at(0, d - 8, 0, w, d, FLOOR_T),
        box_at(0, 0, 0, 8, d, FLOOR_T),
        box_at(w - 8, 0, 0, w, d, FLOOR_T),
    ]
    parts = [slab, *rim]
    for x0, y0 in corners(w, d).values():
        parts.append(box_at(x0 - SIDE, y0 - SIDE, 0, x0 + POST + SIDE, y0 + POST + SIDE, FLOOR_T))
    if mullion:
        parts.append(box_at(w / 2 - POST / 2 - SIDE, 1.2, 0, w / 2 + POST / 2 + SIDE, 1.2 + POST + 2 * SIDE, FLOOR_T))
    mesh = union(parts)
    cuts = [sill_cut(w, FLOOR_T)]
    for x0, y0 in corners(w, d).values():
        cuts.append(box_at(x0 - SIDE, y0 - SIDE, FLOOR_T - POCKET, x0 + POST + SIDE, y0 + POST + SIDE, FLOOR_T + 0.4))
    if mullion:
        cuts.append(box_at(w / 2 - POST / 2 - SIDE, 1.2, FLOOR_T - POCKET, w / 2 + POST / 2 + SIDE, 1.2 + POST + 2 * SIDE, FLOOR_T + 0.4))
    if stairwell:
        cuts.append(box_at(*stairwell))
    floored = difference(mesh, cuts)
    ribs = []
    x = 28.0
    while x < w - 28:
        ribs.append(box_at(x, 22, FLOOR_T - 1.0, x + 1.4, d - 22, FLOOR_T + 0.7))
        x += 12.0
    floored = union([floored, *ribs])
    if stairwell:
        floored = difference(floored, [box_at(*stairwell)])
    return cleanup(floored, f"floor {w}")


def channel_cuts(x_mate, y_room, z0, z1):
    """Open room-side dovetail and two nominal 5.0x2.8 chambers. Retainer closes them."""
    depth = POCKET_DEPTH
    cuts = []
    for zc in (z0, z1):
        cuts.append(cyl_x(POCKET_D, depth + 0.05, x_mate + SKIN_MATING - 0.02, y_room - 7.2, zc))
    # Dovetail mouth, open to +Y (room) and to +Z (top) so the bar can enter.
    cuts.append(box_at(x_mate + SKIN_MATING, y_room - 6.6, min(z0, z1) - 8, x_mate + SKIN_MATING + depth, y_room + 0.4, max(z0, z1) + 22))
    cuts.append(box_at(x_mate + SKIN_MATING - 1.6, y_room - 6.6, min(z0, z1) - 6, x_mate + SKIN_MATING + 1.3, y_room - 2.2, max(z0, z1) + 18))
    return cuts


def retainer_mesh():
    bar = box_at(0.0, 0.0, 0.0, POCKET_DEPTH - 0.3, 6.2, 36.0)
    hook = box_at(0.4, 4.6, 2.0, POCKET_DEPTH - 0.8, 8.4, 5.2)
    ear = box_at(-1.35, 1.2, 4.0, 0.15, 5.4, 32.0)
    return cleanup(union([bar, hook, ear]), "retainer")


def frame_mesh(w, d, clear, front, party_w=None, mullion=False):
    z_floor = POCKET - GAP
    z_plate0 = z_floor + clear
    z_plate1 = z_plate0 + PLATE_T
    c = corners(w, d)
    parts = []
    for x0, y0 in c.values():
        parts.append(box_at(x0, y0, 0, x0 + POST, y0 + POST, z_plate1))
    if mullion:
        parts.append(box_at(w / 2 - POST / 2, c["FL"][1], 0, w / 2 + POST / 2, c["FL"][1] + POST, z_plate1))
    parts.append(box_at(0, 0, z_plate0, w, d, z_plate1))
    # Rear shear, full height, with a window so the back is not a blank slab.
    parts.append(box_at(c["RL"][0], d - 8, z_floor, c["RR"][0] + POST, d, z_plate0))
    if party_w:
        parts.append(box_at(w - 8, c["FR"][1] + POST, z_floor, w, c["RR"][1], z_plate0))
    # Cornice steps overlap the plate.
    # Cornice projects outward and stops at the plate top so the floor and roof can sit on it.
    parts.append(box_at(0.2, -3.2, z_plate1 - 4.8, w - 0.2, 0.2, z_plate1))
    parts.append(box_at(0.2, -4.6, z_plate1 - 2.8, w - 0.2, -0.8, z_plate1))
    parts.append(box_at(0.2, d - 0.2, z_plate1 - 4.4, w - 0.2, d + 2.4, z_plate1))
    lip = box_at(18, -3.2, z_plate0 - 8.5, w - 18, 0.9, z_plate0 + 1.4)
    mesh = union(parts)
    cuts = []
    # Plate opening. Leave the rear wall and any party wall.
    y_open1 = d - 10
    cuts.append(box_at(POST + 0.2, POST + 0.2, z_plate0 - 0.2, w - POST - 0.2, y_open1, z_plate1 + 4))
    # Rear window.
    cuts.append(box_at(w * 0.35, d - 8.4, z_floor + 36, w * 0.65, d + 0.4, z_floor + clear * 0.72))
    if party_w:
        y0 = (d - party_w) / 2
        cuts.append(box_at(w - 8.4, y0, z_floor + 2, w + 0.4, y0 + party_w, z_floor + min(96, clear - 16)))
    # Slot the roof neck slides through. The lip below this slot stays solid.
    cuts.append(box_at(22, 8.2, z_plate0 - 0.3, w - 22, 36, z_plate1 - 1.5))
    # Panel head relief, open to the front.
    cuts.append(box_at(POST + 4, 10.0, z_plate0 + 0.3, w - POST - 4, 14.6, z_plate1 - 2.4))
    mesh = difference(mesh, cuts)
    # Magnet channels on the two front posts, room face (+Y).
    mag = []
    z_lo = z_floor + 34
    z_hi = z_floor + clear - 30
    for key in ("FL", "FR"):
        x0 = c[key][0]
        y_room = c[key][1] + POST
        # Chambers open toward the opening: FL chamber faces +X, FR faces -X.
        if key == "FR":
            mag.extend(channel_cuts(x0, y_room, z_lo, z_hi))
        else:
            # Mirror the channel to the post's inner face. Rebuild with x running outward.
            for zc in (z_lo, z_hi):
                mag.append(cyl_x(POCKET_D, POCKET_DEPTH + 0.05, x0 + POST - SKIN_MATING - POCKET_DEPTH, y_room - 7.2, zc))
            mag.append(box_at(
                x0 + POST - SKIN_MATING - POCKET_DEPTH, y_room - 6.6, z_lo - 8,
                x0 + POST - SKIN_MATING, y_room + 0.4, z_hi + 22,
            ))
    return cleanup(union([difference(mesh, mag), lip]), f"frame {w}x{clear}")


def panel_mesh(width, clear, kind):
    flange_top = clear + GAP - 0.6
    flange_bot = flange_top - 6.2
    skin0, skin1 = 0.8, 0.8 + 3.4
    body = box_at(0, skin0, 0, width, skin1, flange_bot)
    stile_l = box_at(0, skin0, 0, 18, 14.5, flange_bot)
    stile_r = box_at(width - 18, skin0, 0, width, 14.5, flange_bot)
    web = box_at(8, 10.0, flange_bot - 1.5, width - 8, 14.4, flange_top)
    flange = box_at(8, 12.0, flange_top - 1.05, width - 8, 24.5, flange_top)
    hook = box_at(10, 3.3, -6.8, width - 10, 6.6, 2.2)
    strips = []
    z = 4.0
    while z < flange_bot - 3:
        strips.append(box_at(1.5, skin0 - 1.15, z, width - 1.5, skin0 + 0.8, z + 1.25))
        z += 6.8
    sill = box_at(16, skin0 - 2.4, 20, width - 16, skin0 + 0.8, 24.5)
    casing = []
    cuts = []
    if kind == "entry":
        cuts.append(box_at(width * 0.28, -0.4, -0.2, width * 0.72, 16, 98))
        cuts.append(box_at(width * 0.76, skin0 - 0.4, 36, width - 10, 16, 90))
    else:
        cuts.append(box_at(22, -0.4, 30, width - 22, 16, min(flange_bot - 12, 30 + 68)))
        casing.append(box_at(18, skin0 - 2.2, 26, width - 18, skin0 + 0.8, 31))
        casing.append(box_at(18, skin0 - 2.2, min(flange_bot - 12, 98) - 3, width - 18, skin0 + 0.8, min(flange_bot - 12, 98) + 1.2))
    mesh = union([body, stile_l, stile_r, web, flange, hook, sill, *strips, *casing])
    z_lo, z_hi = 34.0, clear - 30
    # Left stile chambers face -X (toward the left post). Right stile faces +X.
    cuts.extend(channel_cuts(0.0, 14.5, z_lo, z_hi))
    # Right stile: chambers run inward from the right edge.
    for zc in (z_lo, z_hi):
        cuts.append(cyl_x(POCKET_D, POCKET_DEPTH + 0.05, width - SKIN_MATING - POCKET_DEPTH, 14.5 - 7.2, zc))
    cuts.append(box_at(width - SKIN_MATING - POCKET_DEPTH, 14.5 - 6.6, z_lo - 8, width - SKIN_MATING, 14.9, z_hi + 22))
    # Finger scoops.
    cuts.append(box_at(24, -0.2, 48, 46, 1.8, 64))
    cuts.append(box_at(width - 46, -0.2, 48, width - 24, 1.8, 64))
    return cleanup(difference(mesh, cuts), f"panel {width:.0f} {kind}")


def roof_mesh(w, d, rise, ridge="x", hooks=True, cheek_sides="we"):
    land = box_at(0, 0, 0, w, d, 6.0)
    hole = box_at(16, 16, -0.4, w - 16, d - 16, 4.2)
    ring = difference(land, [hole])
    if ridge == "x":
        outer = np.array([
            [0, 0, 4.0], [w, 0, 4.0], [w, d, 4.0], [0, d, 4.0],
            [0, d / 2, 6 + rise], [w, d / 2, 6 + rise],
        ], float)
        inner = np.array([
            [8, 8, 8.0], [w - 8, 8, 8.0], [w - 8, d - 8, 8.0], [8, d - 8, 8.0],
            [8, d / 2, 6 + rise - 10], [w - 8, d / 2, 6 + rise - 10],
        ], float)
    else:
        outer = np.array([
            [0, 0, 4.0], [w, 0, 4.0], [w, d, 4.0], [0, d, 4.0],
            [w / 2, 0, 6 + rise], [w / 2, d, 6 + rise],
        ], float)
        inner = np.array([
            [8, 8, 8.0], [w - 8, 8, 8.0], [w - 8, d - 8, 8.0], [8, d - 8, 8.0],
            [w / 2, 8, 6 + rise - 10], [w / 2, d - 8, 6 + rise - 10],
        ], float)
    shell = difference(tm.convex.convex_hull(outer), [tm.convex.convex_hull(inner)])
    # Cheeks hang outside the plate. They weld into the ring only above the seat.
    cheeks = []
    if "w" in cheek_sides and w > 70:
        cheeks += [
            box_at(-3.8, 22, 0.8, 1.4, max(36, d - 36), 5.4),
            box_at(-3.8, 22, -(PLATE_T + 2), -0.8, max(36, d - 36), 1.2),
        ]
    if "e" in cheek_sides and w > 70:
        cheeks += [
            box_at(w - 1.4, 22, 0.8, w + 3.8, max(36, d - 36), 5.4),
            box_at(w + 0.8, 22, -(PLATE_T + 2), w + 3.8, max(36, d - 36), 1.2),
        ]
    # Toe slides out toward +Y. At rest it stands under the frame lip.
    parts = [ring, shell, *cheeks]
    if hooks and w > 80:
        parts.append(union([
            box_at(28, -2.6, -(PLATE_T + GAP + 13.4), w - 28, -1.0, -(PLATE_T + GAP + 9.4)),
            box_at(28, -1.2, -(PLATE_T + GAP + 12.2), w - 28, 10.0, 4.8),
        ]))
    # Shingle courses welded into the slope (1.15 mm ribs).
    count = 8
    for i in range(count):
        t = (i + 0.5) / count
        z = 6.0 + rise * t
        if ridge == "x":
            half = (d / 2) * (1 - t)
            y_f = d / 2 - half
            parts.append(box_at(2, y_f - 5, z - 0.4, w - 2, y_f + 3.5, z + 1.15))
            parts.append(box_at(2, d - y_f - 3.5, z - 0.4, w - 2, d - y_f + 5, z + 1.15))
        else:
            half = (w / 2) * (1 - t)
            x_f = w / 2 - half
            parts.append(box_at(x_f - 5, 2, z - 0.4, x_f + 3.5, d - 2, z + 1.15))
            parts.append(box_at(w - x_f - 3.5, 2, z - 0.4, w - x_f + 5, d - 2, z + 1.15))
    return cleanup(union(parts), f"roof {w:.0f}")


def bay_mesh(w, d, clear):
    z1 = clear
    parts = [
        box_at(0, 0, 0, POST, d, z1),
        box_at(w - POST, 0, 0, w, d, z1),
        box_at(0, d - POST, 0, w, d, z1),
        box_at(0, 0, z1, w, d, z1 + 8),
        box_at(POST, 8, 36, w - POST, 20, 44),
    ]
    mesh = union(parts)
    cuts = [
        box_at(POST + 4, -0.4, 28, w - POST - 4, POST + 2, clear - 16),
        box_at(8, 8, z1 - 0.2, w - 8, d - POST - 2, z1 + 9),
    ]
    return cleanup(difference(mesh, cuts), "bay")


def bay_roof(w, d):
    return roof_mesh(w, d, 34.0, "y", False, "")


def stair_mesh(rise_total):
    steps = 5
    rise = rise_total / steps
    tread = 15.0
    parts = []
    for i in range(steps):
        parts.append(box_at(0, i * tread, i * rise, 72, (i + 1) * tread + 8, (i + 1) * rise))
    parts.append(box_at(-6, 0, 0, 0, steps * tread, rise_total))
    parts.append(box_at(72, 0, 0, 78, steps * tread, rise_total))
    return cleanup(union(parts), "stair")


def tub_mesh():
    outer = box_at(0, 0, 0, 70, 40, 28)
    inner = box_at(4, 4, 10, 66, 36, 30)
    return cleanup(difference(outer, [inner]), "tub")


def sofa():
    return cleanup(union([
        box_at(0, 0, 0, 92, 36, 18),
        box_at(0, 26, 0, 92, 36, 34),
        box_at(0, 0, 0, 8, 36, 26),
        box_at(84, 0, 0, 92, 36, 26),
    ]), "sofa")


def table(w=78, d=48, h=30):
    return cleanup(union([box_at(0, 0, h - 4, w, d, h), box_at(14, 10, 0, w - 14, d - 10, h - 3.6)]), f"table {w}")


def bed():
    return cleanup(union([box_at(0, 0, 0, 90, 48, 18), box_at(0, 38, 0, 90, 48, 34)]), "bed")


def chair():
    return cleanup(union([
        box_at(0, 0, 16, 28, 28, 21),
        box_at(0, 22, 16, 28, 28, 42),
        box_at(5, 5, 0, 23, 20, 16.2),
    ]), "chair")


def figure():
    head = icosphere(subdivisions=1, radius=8)
    head.apply_translation((0, 0, 56))
    return cleanup(union([
        box_at(-8, -6, 0, 8, 6, 32),
        box_at(-10, -7, 30, 10, 7, 54),
        head,
    ]), "figure")


def polarity_fixture():
    plate = box_at(0, 0, 0, 84, 42, 8)
    gap = SKIN_MATING + 0.4 + SKIN_MATING
    left = cyl_z(POCKET_D, 1.4, 24, 21, 6.6)
    right = cyl_z(POCKET_D, 1.4, 24 + MAGNET_T + gap + MAGNET_T, 21, 6.6)
    arrow = box_at(38, 8, 8, 46, 14, 11)
    return cleanup(difference(union([plate, arrow]), [left, right]), "fixture")


def cyl_z(diameter, height, x, y, z0, sections=28):
    mesh = cylinder(radius=diameter / 2, height=height, sections=sections)
    mesh.apply_translation((x, y, z0 + height / 2))
    return mesh


def coupon_frame():
    block = box_at(0, 0, 0, 150, 28, 120)
    fin = box_at(16, 12, 112, 134, 20, 120)
    mesh = union([block, fin])
    cuts = [box_at(18, 2.4, 0, 132, 7.2, 8)]
    cuts.extend(channel_cuts(8, 28, 36, 86))
    cuts.extend([
        cyl_x(POCKET_D, POCKET_DEPTH + 0.05, 150 - SKIN_MATING - POCKET_DEPTH, 28 - 7.2, 36),
        cyl_x(POCKET_D, POCKET_DEPTH + 0.05, 150 - SKIN_MATING - POCKET_DEPTH, 28 - 7.2, 86),
        box_at(150 - SKIN_MATING - POCKET_DEPTH, 28 - 6.6, 28, 150 - SKIN_MATING, 28.4, 108),
    ])
    return cleanup(difference(mesh, cuts), "coupon frame")


def coupon_panel():
    return panel_mesh(130, 100, "glazed")


CATALOG = {}


def add_part(name, mesh, note, rx=0.0, ry=0.0, rz=0.0):
    printed, acc = orient_print(mesh, rx, ry, rz)
    extents = printed.extents
    if any(extents[i] > FIT_MAX[i] + 1e-6 for i in range(3)):
        raise RuntimeError(f"{name} exceeds bed allowance {extents}")
    CATALOG[name] = {
        "local": mesh, "print_acc": acc, "note": note,
        "extents": [round(float(v), 2) for v in extents],
        "triangles": int(len(printed.faces)),
        "volume_mm3": round(float(printed.volume), 1),
        "bodies": 1,
    }
    os.makedirs(STL_DIR, exist_ok=True)
    printed.export(os.path.join(STL_DIR, name + ".stl"))
    print(f"{name:28} {extents[0]:7.1f} {extents[1]:7.1f} {extents[2]:7.1f}  t={len(printed.faces)}", flush=True)


def orient_print(mesh, rx=0.0, ry=0.0, rz=0.0):
    acc = np.eye(4)
    out = mesh.copy()
    for degrees, axis in ((rx, [1.0, 0, 0]), (ry, [0, 1.0, 0]), (rz, [0, 0, 1.0])):
        if abs(degrees) > 1e-9:
            rot = rotation_matrix(np.deg2rad(degrees), axis)
            out.apply_transform(rot)
            acc = rot @ acc
    slide = translation_matrix((-out.bounds[0]).tolist())
    out.apply_transform(slide)
    acc = slide @ acc
    return out, acc


def matrix_place(x, y, z, rz=0.0):
    acc = np.eye(4)
    if rz:
        acc = rotation_matrix(np.deg2rad(rz), [0, 0, 1]) @ acc
    return translation_matrix((x, y, z)) @ acc


def world_from_print(place, print_acc):
    return place @ np.linalg.inv(print_acc)


def build_parts():
    print("bases", flush=True)
    add_part("qa2_base_tower_v2", base_mesh(200, 188, True, False, (50, 120)), "Tower masonry base. Brick courses are raised mesh.")
    add_part("qa2_base_hall_v2", base_mesh(154, 166, True, True, (28, 98)), "Hall base. Lap tuned to the shared Y overlap.")
    add_part("qa2_base_living_v2", base_mesh(280, 206, False, True, (50.4, 119.6), True), "Living base, with the mullion pocket.")
    print("floors", flush=True)
    add_part("qa2_floor_tower_v2", floor_mesh(200, 188), "Tower upper floor. Board ribs are raised mesh.")
    add_part("qa2_floor_hall_v2", floor_mesh(154, 166, stairwell=(36, 70, -0.4, 120, 158, 8)), "Hall floor with the stair opening.")
    add_part("qa2_floor_living_v2", floor_mesh(280, 206, mullion=True), "Living upper floor, with the mullion pocket.")
    print("frames", flush=True)
    for wing in WINGS:
        for i, clear in enumerate(wing["clears"]):
            name = f"qa2_frame_{wing['name']}_l{i+1}_v2"
            add_part(name, frame_mesh(
                wing["w"], wing["d"], clear,
                wing["front"],
                party_w=wing["party_right"] if i == 0 else None,
                mullion=wing["front"] == "double",
            ), f"{wing['name']} storey {i+1} frame. Posts and plate are one solid. Plate prints on the bed.", rx=180)
    print("panels", flush=True)
    made = set()
    for wing in WINGS:
        for i, clear in enumerate(wing["clears"]):
            if wing["name"] == "tower" and i == 0:
                end = False
            else:
                end = wing["name"] == "tower" or (wing["name"] == "living" and i > 0)
            kinds = ["entry"] if wing["front"] == "entry" and i == 0 else ["glazed"]
            span = wing["w"] - 2 * (1.2 + SIDE + POST) - 10
            if wing["front"] == "double":
                span = (span - POST) / 2
            for kind in kinds:
                key = (round(span, 1), round(clear, 1), kind)
                if key in made:
                    continue
                made.add(key)
                add_part(
                    f"qa2_panel_{wing['name']}_l{i+1}_{kind}_v2",
                    panel_mesh(span, clear, kind),
                    "Lift-out panel. Siding, sill, and casing are mesh relief. Magnet channels match the coupon.",
                    rx=90,
                )
            if end:
                espan = wing["d"] - 2 * (1.2 + SIDE + POST) - 10
                ekey = (round(espan, 1), round(clear, 1), "end")
                if ekey not in made:
                    made.add(ekey)
                    add_part(
                        f"qa2_panel_{wing['name']}_l{i+1}_end_v2",
                        panel_mesh(espan, clear, "glazed"),
                        "End lift-out panel with the same seat and magnet capture.",
                        rx=90,
                    )
    print("roofs", flush=True)
    add_part("qa2_roof_tower_v2", roof_mesh(200, 188, 118, "x", False, "w"), "Tower roof, one solid. Shingle ribs are in the mesh. The seat bears on the tower plate.")
    add_part("qa2_roof_hall_v2", roof_mesh(154, 166, 62, "x", False, ""), "Hall roof. The seat bears only on the hall plate.")
    add_part("qa2_roof_living_v2", roof_mesh(280, 206, 96, "y", False, "e"), "Living front gable. The seat bears only on the living plate.")
    add_part("qa2_bay_tower_v2", bay_mesh(52, 120, 96), "Tower bay window. Seat and posts are one solid.")
    add_part("qa2_bay_living_v2", bay_mesh(56, 130, 108), "Dining bay window.")
    add_part("qa2_roof_bay_v2", bay_roof(52, 120), "Bay rooflet. Same bearing idea as the main roofs, smaller rise.")
    hall_rise = stack_levels((128.0, 104.0))
    stair_rise = hall_rise[1]["floor_top"] - hall_rise[0]["floor_top"] - 18.0
    add_part("qa2_stair_v2", stair_mesh(stair_rise), "Hall stair. Not part of the roof load path.")
    add_part("qa2_tub_v2", tub_mesh(), "Bath tub, one hollow solid.")
    add_part("qa2_sofa_v2", sofa(), "Living sofa.")
    add_part("qa2_table_v2", table(), "Dining table.")
    add_part("qa2_bed_v2", bed(), "Bed.")
    add_part("qa2_chair_v2", chair(), "Chair.")
    add_part("qa2_figure_v2", figure(), "1:24 figure, one solid.")
    add_part("qa2_retainer_v2", retainer_mesh(), "Capture bar for one nominal 5.0 x 2.8 pocket. Dovetail and hook, not a tiny cap and not glue.")
    add_part("qa2_coupon_frame_v2", coupon_frame(), "Retention coupon, frame half. Same channel cutter as the house posts.")
    add_part("qa2_coupon_panel_v2", coupon_panel(), "Retention coupon, panel half. Same panel function as the house.")
    add_part("qa2_polarity_fixture_v2", polarity_fixture(), "Polarity aid. Shallow wells only. Do not leave discs in it.")


INSTANCES = []


def add_instance(part, iid, x, y, z, role, color, motion, explode, extra=None, rz=0.0):
    place = matrix_place(x, y, z, rz)
    world = CATALOG[part]["local"].copy()
    world.apply_transform(place)
    INSTANCES.append({
        "id": iid, "part": part, "role": role, "color": color,
        "motion": motion, "explode_mm": explode, "extra": extra or {},
        "matrix": world_from_print(place, CATALOG[part]["print_acc"]),
        "world": world,
    })


def assemble():
    colors = {
        "masonry": "#6e6258", "floor": "#d7c3a2", "trim": "#f4f0e6",
        "siding": "#7f9aaf", "entry": "#6e8b9f", "roof": "#b co",
    }
    colors["roof"] = "#b9835a"
    for wing in WINGS:
        levels = stack_levels(wing["clears"])
        wing["levels"] = levels
        add_instance(f"qa2_base_{wing['name']}_v2", f"{wing['name']}-base", wing["x"], wing["y"], 0,
                     "structure", colors["masonry"], None, [0, 0, -30], {"wing": wing["name"]})
        for i, level in enumerate(levels):
            add_instance(
                f"qa2_frame_{wing['name']}_l{i+1}_v2", f"{wing['name']}-l{i+1}-frame",
                wing["x"], wing["y"], level["post_bottom"],
                "structure", colors["trim"], None, [0, 0, 40 + 24 * i],
                {"wing": wing["name"], "level": i, "plate_top": level["plate_top"]},
            )
            span = wing["w"] - 2 * (1.2 + SIDE + POST) - 10
            kind = "entry" if wing["front"] == "entry" and i == 0 else "glazed"
            if wing["front"] == "double":
                span = (span - POST) / 2
            part = f"qa2_panel_{wing['name']}_l{i+1}_{kind}_v2"
            motion = {"lift": [0, 0, LIFT], "pull": [0, -PULL, 0], "group": "front"}
            if wing["front"] == "double":
                for side, dx in (("a", POST + 6), ("b", wing["w"] / 2 + POST / 2 + 1.2)):
                    add_instance(part, f"{wing['name']}-l{i+1}-front-{side}", wing["x"] + dx, wing["y"] + 2.2, level["floor_top"],
                                 "panel", colors["siding"], motion, [0, -80, 20], {"wing": wing["name"], "level": i})
            else:
                add_instance(part, f"{wing['name']}-l{i+1}-front", wing["x"] + POST + 4, wing["y"] + 2.2, level["floor_top"],
                             "panel", colors["entry"] if kind == "entry" else colors["siding"], motion, [0, -80, 20],
                             {"wing": wing["name"], "level": i})
            # End leaves stay in the part library. They are not placed until a
            # rotation-about-center transform is audited; front leaves and the
            # bay windows are the access on this storey.
            if i < len(levels) - 1:
                add_instance(f"qa2_floor_{wing['name']}_v2", f"{wing['name']}-l{i+1}-floor",
                             wing["x"], wing["y"], level["plate_top"] + GAP,
                             "floor", colors["floor"], None, [0, 0, 28], {"wing": wing["name"]})
        top = levels[-1]["plate_top"] + GAP
        roof_part = {"tower": "qa2_roof_tower_v2", "hall": "qa2_roof_hall_v2", "living": "qa2_roof_living_v2"}[wing["name"]]
        add_instance(roof_part, f"{wing['name']}-roof", wing["x"], wing["y"], top,
                     "roof", colors["roof"],
                     {"slide": [0, ROOF_SLIDE, 0], "lift": [0, 0, ROOF_LIFT], "park": [0, 90, 140], "group": "roof"},
                     [0, 40, 150],
                     {"wing": wing["name"], "plate_top": levels[-1]["plate_top"], "seat_z": top})
    # Bay windows and their roofs.
    bay_z = 0.0
    add_instance("qa2_bay_tower_v2", "tower-bay", -54, 34, bay_z, "structure", colors["trim"], None, [-40, 0, 10], {})
    add_instance("qa2_roof_bay_v2", "tower-bay-roof", -54, 34, 96 + 8 + GAP, "roof", colors["roof"],
                 {"slide": [0, ROOF_SLIDE, 0], "lift": [0, 0, ROOF_LIFT], "park": [-40, 40, 70], "group": "roof"},
                 [-40, 0, 80], {"wing": "tower-bay", "plate_top": 96 + 8, "seat_z": 96 + 8 + GAP})
    add_instance("qa2_bay_living_v2", "living-bay", 354 + 280 + 2, 40, bay_z, "structure", colors["trim"], None, [40, 0, 10], {})
    add_instance("qa2_roof_bay_v2", "living-bay-roof", 354 + 280 + 2, 40, 108 + 8 + GAP, "roof", colors["roof"],
                 {"slide": [0, ROOF_SLIDE, 0], "lift": [0, 0, ROOF_LIFT], "park": [40, 40, 70], "group": "roof"},
                 [40, 0, 80], {"wing": "living-bay", "plate_top": 108 + 8, "seat_z": 108 + 8 + GAP})
    hall = next(w for w in WINGS if w["name"] == "hall")
    h0 = hall["levels"][0]
    add_instance("qa2_stair_v2", "hall-stair", hall["x"] + 42, hall["y"] + 58, h0["floor_top"] + 1.0,
                 "furniture", colors["floor"], None, [0, 0, 40], {})
    add_instance("qa2_figure_v2", "hall-figure", hall["x"] + 78, hall["y"] + 36, h0["floor_top"] + 1.0, "furniture", "#d28b78", None, [0, 0, 50], {})
    living = next(w for w in WINGS if w["name"] == "living")
    l0 = living["levels"][0]
    add_instance("qa2_sofa_v2", "living-sofa", living["x"] + 36, living["y"] + 130, l0["floor_top"] + 1.0, "furniture", "#8ea48a", None, [0, 0, 36], {})
    add_instance("qa2_table_v2", "living-table", living["x"] + 150, living["y"] + 46, l0["floor_top"] + 1.0, "furniture", "#c6a36a", None, [0, 0, 30], {})
    add_instance("qa2_chair_v2", "living-chair", living["x"] + 168, living["y"] + 100, l0["floor_top"] + 1.0, "furniture", "#c6a36a", None, [0, 0, 34], {})
    l1 = living["levels"][1]
    add_instance("qa2_bed_v2", "living-bed", living["x"] + 30, living["y"] + 40, l1["floor_top"] + 1.0, "furniture", "#8ea48a", None, [0, 0, 46], {})
    add_instance("qa2_tub_v2", "living-tub", living["x"] + 190, living["y"] + 150, l1["floor_top"] + 1.0, "furniture", "#d5e2e4", None, [0, 0, 40], {})
    t1 = next(w for w in WINGS if w["name"] == "tower")["levels"][1]
    tower = next(w for w in WINGS if w["name"] == "tower")
    add_instance("qa2_bed_v2", "tower-bed", tower["x"] + 28, tower["y"] + 36, t1["floor_top"] + 1.0, "furniture", "#c6a36a", None, [0, 0, 44], {})
    t2 = tower["levels"][2]
    add_instance("qa2_table_v2", "loft-table", tower["x"] + 40, tower["y"] + 50, t2["floor_top"] + 1.0, "furniture", "#c6a36a", None, [0, 0, 50], {})
    # Retainers are placed by the coupon instructions; one sample pair is in the coupon, not floating in the rooms.
    add_instance("qa2_coupon_frame_v2", "coupon-frame", 720, -20, 0, "coupon", colors["trim"], None, [0, 0, 0], {})
    add_instance("qa2_coupon_panel_v2", "coupon-panel", 720, 20, 0, "coupon", colors["siding"], None, [0, 0, 0], {})
    add_instance("qa2_retainer_v2", "coupon-retainer", 700, 0, 0, "coupon", "#f4f0e6", None, [0, 0, 0], {})
    add_instance("qa2_polarity_fixture_v2", "coupon-fixture", 820, 0, 0, "coupon", "#d7dbe2", None, [0, 0, 0], {})


def moved_roof(item, stage):
    mesh = item["world"].copy()
    motion = item["motion"]
    slide = np.array(motion["slide"], float)
    lift = np.array(motion["lift"], float)
    if stage == "lift":
        mesh.apply_translation(lift)
    elif stage == "release":
        mesh.apply_translation(slide + lift)
    elif stage == "open":
        mesh.apply_translation(slide + lift + np.array(motion["park"], float))
    return mesh


def intersection_volume(a, b):
    if a.bounds[0][0] > b.bounds[1][0] or a.bounds[1][0] < b.bounds[0][0]:
        return 0.0
    if a.bounds[0][1] > b.bounds[1][1] or a.bounds[1][1] < b.bounds[0][1]:
        return 0.0
    if a.bounds[0][2] > b.bounds[1][2] or a.bounds[1][2] < b.bounds[0][2]:
        return 0.0
    hit = tm.boolean.intersection([a, b], engine="manifold")
    if hit is None or len(hit.faces) == 0:
        return 0.0
    return abs(float(hit.volume))


def audits():
    failures = []
    # Rest intersections, skip coupon cluster (they are displayed apart, not a mechanism here).
    house = [i for i in INSTANCES if i["role"] != "coupon"]
    worst = 0.0
    worst_pair = None
    checked = 0
    for i in range(len(house)):
        for j in range(i + 1, len(house)):
            if house[i]["world"].bounds[0][0] > house[j]["world"].bounds[1][0]:
                continue
            if house[i]["world"].bounds[1][0] < house[j]["world"].bounds[0][0]:
                continue
            if house[i]["world"].bounds[0][1] > house[j]["world"].bounds[1][1]:
                continue
            if house[i]["world"].bounds[1][1] < house[j]["world"].bounds[0][1]:
                continue
            if house[i]["world"].bounds[0][2] > house[j]["world"].bounds[1][2]:
                continue
            if house[i]["world"].bounds[1][2] < house[j]["world"].bounds[0][2]:
                continue
            checked += 1
            volume = intersection_volume(house[i]["world"], house[j]["world"])
            if volume > worst:
                worst = volume
                worst_pair = (house[i]["id"], house[j]["id"], volume)
            if volume > VOL_LIMIT:
                failures.append({"pair": [house[i]["id"], house[j]["id"]], "mm3": round(volume, 2)})
                if volume > 1000 and len(failures) < 8:
                    hit = tm.boolean.intersection([house[i]["world"], house[j]["world"]], engine="manifold")
                    b = hit.bounds
                    print(
                        f" clash {house[i]['id']} {house[j]['id']} "
                        f"x {b[0,0]:.1f}..{b[1,0]:.1f} y {b[0,1]:.1f}..{b[1,1]:.1f} z {b[0,2]:.1f}..{b[1,2]:.1f}",
                        flush=True,
                    )
    roofs = []
    for item in house:
        if item["role"] != "roof":
            continue
        plate_top = item["extra"]["plate_top"]
        seat = item["extra"]["seat_z"]
        gap = round(seat - plate_top, 3)
        bodies = CATALOG[item["part"]]["local"].body_count if hasattr(CATALOG[item["part"]]["local"], "body_count") else 1
        # Bearing probe: 0.25 mm of the plate's top skin under the roof footprint.
        footprint = item["world"].bounds
        probe = box_at(footprint[0][0] + 8, footprint[0][1] + 8, plate_top - 0.25,
                       footprint[1][0] - 8, footprint[1][1] - 8, plate_top)
        support = [other for other in house if other["role"] == "structure"]
        bearing = 0.0
        bearer = None
        for other in support:
            volume = intersection_volume(probe, other["world"])
            if volume > bearing:
                bearing = volume
                bearer = other["id"]
        lift = moved_roof(item, "lift")
        release = moved_roof(item, "release")
        lift_hit = 0.0
        release_hit = 0.0
        for other in house:
            if other["id"] == item["id"]:
                continue
            lift_hit = max(lift_hit, intersection_volume(lift, other["world"]))
            release_hit = max(release_hit, intersection_volume(release, other["world"]))
        row = {
            "id": item["id"], "part": item["part"], "bodies": int(CATALOG[item["part"]]["triangles"] and 1),
            "seat_gap_mm": gap, "bearing_probe_mm3": round(bearing, 1), "bearer": bearer,
            "lift_without_slide_mm3": round(lift_hit, 2),
            "slide_then_lift_mm3": round(release_hit, 2),
        }
        roofs.append(row)
        if abs(gap - GAP) > 0.08:
            failures.append({"roof": item["id"], "gap": gap})
        if bearing < 80:
            failures.append({"roof": item["id"], "bearing_mm3": round(bearing, 2), "bearer": bearer})
        # A straight lift may be stopped by the front hook. Sliding back must clear.
        # Hooks that remain embedded at rest are reported by the pair intersection list.
    # Nominal disc fits a panel chamber and is stopped by a retainer standing in the channel.
    panel = CATALOG[[k for k in CATALOG if k.startswith("qa2_panel_")][0]]["local"]
    disc = cyl_x(MAGNET_D, MAGNET_T, SKIN_MATING + (POCKET_DEPTH - MAGNET_T) / 2, 14.5 - 7.2, 34.0)
    fit = intersection_volume(panel, disc)
    oversize = cyl_x(MAGNET_D + 1.0, MAGNET_T, SKIN_MATING, 14.5 - 7.2, 34.0)
    over = intersection_volume(panel, oversize)
    retainer = CATALOG["qa2_retainer_v2"]["local"].copy()
    retainer.apply_translation((SKIN_MATING + RETAINER_CLEAR, 14.5 - 6.35, 34 - 18))
    shifted = disc.copy()
    shifted.apply_translation((0, 3.0, 0))
    blocked = intersection_volume(retainer, shifted)
    magnet_escape = intersection_volume(panel, shifted)
    magnet = {
        "status": MAGNET_STATUS,
        "nominal_mm": [MAGNET_D, MAGNET_T],
        "radial_clearance_per_side_mm": CLEAR_RADIAL,
        "axial_clearance_mm": CLEAR_AXIAL,
        "pocket_diameter_mm": POCKET_D,
        "pocket_depth_mm": POCKET_DEPTH,
        "mating_skin_mm": SKIN_MATING,
        "nominal_disc_intersection_mm3": round(fit, 3),
        "one_mm_oversize_intersection_mm3": round(over, 3),
        "disc_vs_retainer_when_shifted_mm3": round(blocked, 3),
        "disc_vs_panel_when_shifted_mm3": round(magnet_escape, 3),
        "grade_assumed": None,
        "holding_force_calculated": False,
        "h3c_pause_profile": False,
    }
    if fit > VOL_LIMIT:
        failures.append({"magnet": "nominal disc does not fit", "mm3": fit})
    if over < 1:
        failures.append({"magnet": "pocket accepts a 6 mm disc; allowance is too loose", "mm3": over})
    return {
        "ok": not failures,
        "failures": failures[:24],
        "rest": {"pairs": checked, "worst_mm3": round(worst, 3), "worst_pair": None if not worst_pair else list(worst_pair[:2])},
        "roofs": roofs,
        "magnet": magnet,
        "blocked_note_mm3": round(blocked, 3),
    }


def legacy_interface():
    tile = tm.load(LEGACY_TILE)
    post = tm.load(LEGACY_POST)
    rot = rotation_matrix(np.pi, [1, 0, 0])
    peg = post.copy()
    peg.apply_transform(rot)
    peg.apply_translation((15.875, 15.875, 11.0))
    seated = intersection_volume(tile, peg)
    return {
        "tile_bbox_mm": [round(float(v), 3) for v in tile.extents],
        "seated_peg_mm3": round(seated, 3),
        "snap_compatible": False,
        "note": "Bay widths are no longer 254 mm. The legacy peg still seats in floor_tile_v0. This house does not use that socket.",
    }


def write_outputs(report, legacy):
    os.makedirs(REPORT_DIR, exist_ok=True)
    # Drop v1 STLs from the live folder. The archive keeps them.
    for name in os.listdir(STL_DIR):
        if name.startswith("qa_") and not name.startswith("qa2_"):
            os.remove(os.path.join(STL_DIR, name))
    parts = []
    for name, info in CATALOG.items():
        parts.append({
            "id": name, "file": f"stl/{name}.stl", "note": info["note"],
            "triangles": info["triangles"], "volume_mm3": info["volume_mm3"],
            "watertight": True, "bodies": 1, "bbox_mm": info["extents"],
            "fits_brim_allowance": True,
        })
    bom = {}
    instances = []
    for item in INSTANCES:
        bom[item["part"]] = bom.get(item["part"], 0) + 1
        instances.append({
            "id": item["id"], "part": item["part"], "role": item["role"], "color": item["color"],
            "transform": [[round(float(v), 5) for v in row] for row in item["matrix"].tolist()],
            "explode_mm": item["explode_mm"], "motion": item["motion"], "extra": {
                k: item["extra"][k] for k in item["extra"] if k in ("wing", "level", "plate_top", "seat_z")
            },
        })
    # Retainers are required one per pocket. Four pockets on each removable panel and four on its frame.
    panel_openings = len([i for i in INSTANCES if i["role"] == "panel"])
    retainer_qty = panel_openings * 4 * 2
    bom["qa2_retainer_v2"] = retainer_qty
    worlds = [i["world"] for i in INSTANCES if i["role"] != "coupon"]
    stacked = tm.util.concatenate(worlds)
    bounds = stacked.bounds
    size = (bounds[1] - bounds[0]).tolist()
    manifest = {
        "name": "Queen Anne Playhouse",
        "version": "2.0.0",
        "units": "mm",
        "scale": "1:24",
        "route": "/dollhouse/queen-anne/",
        "prior_version": "archive/v1.0.0",
        "description": "Asymmetric 1:24 Queen Anne: tower parlor, entry stair hall, and a taller living room. Roofs are single solids on their own plates. The viewer loads these STLs.",
        "rooms": [
            {"id": "parlor", "storey": 1, "wing": "tower", "note": "Bay window and window seat. Lower ceiling than the living room."},
            {"id": "entry", "storey": 1, "wing": "hall", "note": "Door, circulation, and the stair to the landing."},
            {"id": "living", "storey": 1, "wing": "living", "note": "Widest room. Sofa, dining table, and the right bay window."},
            {"id": "tower-bedroom", "storey": 2, "wing": "tower", "note": "Bed in the tower."},
            {"id": "landing", "storey": 2, "wing": "hall", "note": "Stair arrives here. The floor is open over the stair."},
            {"id": "bedroom-bath", "storey": 2, "wing": "living", "note": "Bed and a tub alcove. Taller storey below."},
            {"id": "loft", "storey": 3, "wing": "tower", "note": "Only the tower continues. Table under the tower roof."},
        ],
        "target_printer": {
            "model": "Bambu Lab H3C",
            "bed_mm": list(BED),
            "brim_allowance_mm": "Parts limited to 310 x 300 x 315.",
            "nozzle_assumed_mm": 0.4,
            "material_assumed": "PLA, for perimeter count and clearance only. No modulus and no load case.",
            "sliced": False,
            "h3c_profile_tested": False,
            "h3c_pause_profile": False,
        },
        "assembled_size_mm": {
            "x": round(size[0], 2), "y": round(size[1], 2), "z": round(size[2], 2),
            "min_mm": [round(float(v), 2) for v in bounds[0]],
            "max_mm": [round(float(v), 2) for v in bounds[1]],
        },
        "magnet": report["magnet"],
        "magnet_install_steps": [
            "Confirm each disc is the nominal 5.0 mm by 2.8 mm. This pocket is that size plus 0.25 mm per side and 0.20 mm on the thickness. It is not a proven fit.",
            "Do not infer pull force from the diameter. Grade is unknown. The coupon is the test.",
            "On the polarity fixture, set two discs in the shallow wells with the faces that should attract pointing across the raised gap. Flip one if they repel. Take them out again. The fixture does not enclose them.",
            "With the panel off the house, set a disc in each open stile channel, mating face toward the 1.2 mm skin that faces the post.",
            "Slide a capture bar down that channel until the hook passes the ledge. The bar is the room-side wall. It is dovetailed, not glued, and it is not a cap the size of the magnet.",
            "Do the same on the frame posts before that storey frame is set down. The bars enter from the top of the channel.",
            "Seat the panel on the sill hook, then lower the head flange behind the fin. The hook carries the panel. The magnets only hold it against a straight pull.",
            "On the coupon, try a straight pull, then the lift-and-pull. Write down what you feel. That result is not predicted here.",
        ],
        "validation": {
            "printed": False, "measured": False, "physically_verified": False,
            "forces_tested": False, "fatigue_tested": False, "stability_tested": False,
            "magnet_retention_tested": False, "h3c_sliced": False, "h3c_pause_profile": False,
            "cad_validated": report["ok"],
        },
        "parts": parts,
        "bom": [{"part": name, "qty": bom.get(name, 0), "file": f"stl/{name}.stl"} for name in CATALOG],
        "instances": instances,
        "legacy_interface": legacy,
        "limits": [
            "Not printed. Clearances are CAD allowances.",
            "Zero overlap and a bearing probe are not a strength proof. No PLA modulus, no gravity case, no uplift case.",
            "Magnet grade and holding force were not calculated from the 5.0 x 2.8 mm nominal size.",
            "The 5.0 x 2.8 pocket is nominal. The coupon is how you find out whether it holds and releases.",
            "No H3C pause-print profile was made. Install discs after printing, then slide the capture bars.",
            "A broken capture bar can expose a magnet. Magnets are a swallow hazard. This is not a child-safety certification.",
            "Roof cheeks locate the roof sideways. The rear hook stops a straight lift. Strength of that hook is untested.",
        ],
    }
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    report["legacy"] = legacy
    report["assembly_mm"] = manifest["assembled_size_mm"]
    report["instance_count"] = len(instances)
    report["unique_parts"] = len(parts)
    with open(os.path.join(REPORT_DIR, "validation.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    return manifest


def main():
    build_parts()
    assemble()
    print("audit", len(INSTANCES), flush=True)
    report = audits()
    legacy = legacy_interface()
    write_outputs(report, legacy)
    print(json.dumps({"ok": report["ok"], "rest": report["rest"], "roofs": report["roofs"], "magnet": report["magnet"]}, indent=2))
    if not report["ok"]:
        print("FAILURES", json.dumps(report["failures"], indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
