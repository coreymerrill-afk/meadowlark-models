"""Queen Anne Playhouse v3. Units mm. Z up. One house.

v2 is archived. It read as three stacks, the bay sat beside the house, the
stair stopped short of the upper floors, and the panels hung on hooks.

This file is one plan. Rooms share floors and doorways. Two stair flights
reach the tower loft through real floor openings. Front and end facades pull
straight off on nominal 5 x 2.8 mm magnets. The capture bar closes a magnet
channel. It does not fasten the panel. The house frame may use joinery.

Lighting reservations follow the November 6 research note. They are not a
measured LED fit and not a finished circuit.
"""
from __future__ import annotations

import json
import os

import numpy as np
import trimesh as tm
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STL_DIR = os.path.join(ROOT, "stl")
REPORT_DIR = os.path.join(ROOT, "reports")
LEGACY_TILE = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "floor_tile_v0.stl"))
LEGACY_POST = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "snap_post_v0.stl"))

BED = (330.0, 320.0, 325.0)
FIT_MAX = (BED[0] - 20.0, BED[1] - 20.0, BED[2] - 10.0)
VOL_LIMIT = 1.0

BASE_TOP = 16.0
F2F = 116.0
FLOOR_T = 6.0
PLATE_T = 14.0
GAP = 0.45
CLEAR = F2F - FLOOR_T - GAP - PLATE_T  # 95.55, walking surface to plate underside
POST = 14.0
WALL = 8.0
POCKET = 3.6
SEAT = 0.50
PANEL_T = 3.4
PULL = 46.0

# Nominal magnet. Not a measured fit. Holding force is not calculated.
MAGNET_D = 5.0
MAGNET_T = 2.8
MAGNET_STATUS = "NOMINAL_NOT_FIT_APPROVED"
CLEAR_RADIAL = 0.25
CLEAR_AXIAL = 0.20
SKIN = 1.2
POCKET_D = MAGNET_D + 2 * CLEAR_RADIAL
POCKET_DEPTH = MAGNET_T + CLEAR_AXIAL

# Lighting reservations. Provisional. Not a fit test and not a buy list.
LED_CAVITY = (6.0, 6.0, 3.0)  # NOT fit-validated. Nano/Chip envelope is unknown.
CEILING_OD = 12.0
CEILING_DEPTH = 7.0
SCONCE = (8.0, 8.0, 12.0)
FEED_D = 2.0  # bare leads only
CHANNEL = (4.0, 3.0)
RISER = (14.0, 10.0)  # larger than the 12 x 8 minimum; this spine carries every circuit
CONNECTOR = (30.0, 20.0, 12.0)
RESISTOR = (25.0, 12.0, 8.0)
BAY_CLEAR = (150.0, 90.0, 30.0)
DIFFUSER_T = 1.0
AIR_GAP = 1.0

T_X0, T_X1 = 0.0, 200.0
H_X0, H_X1 = 200.8, 350.0
L_X0, L_X1 = 350.8, 540.0
Y0, Y1 = 0.0, 210.0
PORCH_Y0 = -52.0
BAY_X0, BAY_X1, BAY_Y0 = 424.0, 522.0, -38.0

L1 = BASE_TOP
L2 = BASE_TOP + F2F
L3 = BASE_TOP + 2 * F2F
RISES = 14
RISE = F2F / RISES
TREAD = 11.0
RUN = (RISES - 1) * TREAD  # 143
STAIR_W = 42.0
HEADROOM = 78.0

# Flight 1 climbs +Y in the tower, against the hall wall, ground to storey 2.
S1 = {"x0": 148.0, "x1": 188.0, "y0": 22.0, "y1": 22.0 + RUN, "z": L1, "up": 1}
# Flight 2 climbs -Y, storey 2 to the loft, beside flight 1.
S2 = {"x0": 100.0, "x1": 142.0, "y0": 172.0 - RUN, "y1": 172.0, "z": L2, "up": -1}
# Floor and plate wells. Larger than the flight so the last riser meets the edge
# and the walking line has the storey clear height overhead.
WELL1 = (146.0, 18.0, 192.0, 170.0)
WELL2 = (96.0, 24.0, 146.0, 176.0)


def box_at(x0, y0, z0, x1, y1, z1):
    if min(x1 - x0, y1 - y0, z1 - z0) <= 0.05:
        raise ValueError((round(x0, 2), round(y0, 2), round(z0, 2), round(x1, 2), round(y1, 2), round(z1, 2)))
    mesh = box((x1 - x0, y1 - y0, z1 - z0))
    mesh.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return mesh


def cyl_along(axis, diameter, length, center, sections=20):
    mesh = cylinder(radius=diameter / 2, height=length, sections=sections)
    if axis == "x":
        mesh.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
    elif axis == "y":
        mesh.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    elif axis != "z":
        raise ValueError(axis)
    mesh.apply_translation(tuple(center))
    return mesh


def union(meshes):
    parts = [m for m in meshes if m is not None]
    if not parts:
        raise ValueError("empty union")
    if len(parts) == 1:
        return parts[0]
    acc = parts[0]
    step = 12
    for index in range(1, len(parts), step):
        acc = tm.boolean.union([acc, *parts[index:index + step]], engine="manifold")
    return acc


def difference(base, cuts):
    cuts = [c for c in cuts if c is not None]
    if not cuts:
        return base
    acc = base
    step = 10
    for index in range(0, len(cuts), step):
        acc = tm.boolean.difference([acc, *cuts[index:index + step]], engine="manifold")
    return acc


def cleanup(mesh, name):
    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    if mesh.volume < 0:
        mesh.invert()
    positive = [part for part in mesh.split(only_watertight=False) if part.volume > VOL_LIMIT]
    if (not mesh.is_watertight) or mesh.volume <= 0 or len(positive) != 1:
        detail = [(round(part.volume), [round(float(v), 1) for v in part.bounds[:, 2]]) for part in positive[:6]]
        raise RuntimeError(f"{name} positive={len(positive)} watertight={mesh.is_watertight} vol={mesh.volume:.1f} {detail}")
    return mesh


def plate_zs(floor_top):
    plate_bottom = floor_top + CLEAR
    plate_top = plate_bottom + PLATE_T
    return plate_bottom, plate_top


def courses(x0, y0, z0, x1, y1, z1, axis, pitch=7.2, thick=1.15, band=1.5):
    ribs = []
    if axis == "y":
        z = z0 + 2.0
        while z < z1 - 2.4:
            ribs.append(box_at(x0, y0, z, x1, y1, min(z + band, z1)))
            z += pitch
    elif axis == "x":
        z = z0 + 2.0
        while z < z1 - 2.4:
            ribs.append(box_at(x0, y0, z, x1, y1, min(z + band, z1)))
            z += pitch
    else:
        raise ValueError(axis)
    return ribs


def brick_skirt(x0, y0, x1, y1, z1, faces):
    bands = []
    z = 1.4
    while z < z1 - 2.5:
        if "s" in faces:
            bands.append(box_at(x0 + 4, y0 - 1.05, z, x1 - 4, y0 + 0.35, z + 2.6))
        if "n" in faces:
            bands.append(box_at(x0 + 4, y1 - 0.35, z, x1 - 4, y1 + 1.05, z + 2.6))
        if "w" in faces:
            bands.append(box_at(x0 - 1.05, y0 + 4, z, x0 + 0.35, y1 - 4, z + 2.6))
        if "e" in faces:
            bands.append(box_at(x1 - 0.35, y0 + 4, z, x1 + 1.05, y1 - 4, z + 2.6))
        z += 6.4
    return bands


def window_cut(face, x, y, z, w, h, depth):
    """Through opening. `face` is the wall normal pointing outdoors."""
    # The outdoor side reaches past the siding ribs so the pane stays a real hole.
    if face == "-y":
        return box_at(x, y - 6.0, z, x + w, y + depth + 1.0, z + h)
    if face == "+y":
        return box_at(x, y - depth - 1.0, z, x + w, y + 6.0, z + h)
    if face == "-x":
        return box_at(x - 6.0, y, z, x + depth + 1.0, y + w, z + h)
    if face == "+x":
        return box_at(x - depth - 1.0, y, z, x + 6.0, y + w, z + h)
    raise ValueError(face)


def window_trim(face, x, y, z, w, h, outward):
    """Sash parts proud of the outer face. Meeting rail and jambs bridge the hole."""
    casing = 3.2
    proud = 2.2
    sill_p = 3.6
    parts = []
    rail_z = z + h * 0.48
    if face in ("-y", "+y"):
        y_out = y - outward if face == "-y" else y
        y_far = y if face == "-y" else y + outward
        # Overlap the wall by 1.2 and project outward.
        y0 = min(y_out, y_far) - (proud if face == "-y" else 0.0)
        y1 = max(y_out, y_far) + (proud if face == "+y" else 0.0)
        if face == "-y":
            y0, y1 = y - proud, y + 1.3
        else:
            y0, y1 = y - 1.3, y + proud
        parts.append(box_at(x - 1.2, y0, z - sill_p, x + w + 1.2, y1, z + 1.2))
        parts.append(box_at(x - 1.2, y0, z + h - 1.0, x + w + 1.2, y1, z + h + casing))
        parts.append(box_at(x - casing, y0, z - 0.4, x + 1.2, y1, z + h + 0.4))
        parts.append(box_at(x + w - 1.2, y0, z - 0.4, x + w + casing, y1, z + h + 0.4))
        parts.append(box_at(x - 0.4, y0, rail_z, x + w + 0.4, y1, rail_z + 2.6))
        if w > 60:
            parts.append(box_at(x + w / 2 - 1.3, y0, z, x + w / 2 + 1.3, y1, z + h))
    else:
        if face == "-x":
            x0, x1 = x - proud, x + 1.3
        else:
            x0, x1 = x - 1.3, x + proud
        parts.append(box_at(x0, y - 1.2, z - sill_p, x1, y + w + 1.2, z + 1.2))
        parts.append(box_at(x0, y - 1.2, z + h - 1.0, x1, y + w + 1.2, z + h + casing))
        parts.append(box_at(x0, y - casing, z - 0.4, x1, y + 1.2, z + h + 0.4))
        parts.append(box_at(x0, y + w - 1.2, z - 0.4, x1, y + w + casing, z + h + 0.4))
        parts.append(box_at(x0, y - 0.4, rail_z, x1, y + w + 0.4, rail_z + 2.6))
    return parts


def siding_on(face, x0, y0, z0, x1, y1, z1):
    ribs = []
    z = z0 + 3.0
    while z < z1 - 3.0:
        if face == "-y":
            ribs.append(box_at(x0 + 1.5, y0 - 1.15, z, x1 - 1.5, y0 + 0.7, z + 1.35))
        elif face == "+x":
            ribs.append(box_at(x1 - 0.7, y0 + 1.5, z, x1 + 1.15, y1 - 1.5, z + 1.35))
        elif face == "-x":
            ribs.append(box_at(x0 - 1.15, y0 + 1.5, z, x0 + 0.7, y1 - 1.5, z + 1.35))
        elif face == "+y":
            ribs.append(box_at(x0 + 1.5, y1 - 0.7, z, x1 - 1.5, y1 + 1.15, z + 1.35))
        z += 7.0
    return ribs


def magnet_slot_cuts(axis, origin, along0, along1, z_centers):
    """Chambers and a top-entry slot. The slot stops shy of the mating face.

    `origin` is the mating-skin outer face centerline point (x, y).
    `axis` is the pull axis, pointing from the frame toward the outdoors
    for a panel, and from the outdoors into the wall for a frame.
    The slot opens upward only. Nothing projects past the mating face.
    """
    cuts = []
    depth = POCKET_DEPTH
    sign = 1.0 if axis[0] > 0 or axis[1] > 0 else -1.0
    # axis is a tuple (dx, dy) of the direction INTO the part, away from the mate face.
    ax, ay = axis
    for zc in z_centers:
        center = (origin[0] + ax * (SKIN + depth / 2), origin[1] + ay * (SKIN + depth / 2), zc)
        direction = "x" if abs(ax) > 0.5 else "y"
        cuts.append(cyl_along(direction, POCKET_D, depth + 0.2, center))
    z0 = min(z_centers) - 6.0
    z1 = max(z_centers) + 16.0
    # Slot cross-section is 7.2 along the mate plane and `depth` deep, inset by the skin.
    if abs(ax) > 0.5:
        x_near = origin[0] + ax * SKIN
        x_far = origin[0] + ax * (SKIN + depth)
        cuts.append(box_at(min(x_near, x_far), origin[1] - 3.6, z0, max(x_near, x_far), origin[1] + 3.6, z1))
        # Dovetail undercut, still inside the part, still shy of the mate face.
        cuts.append(box_at(
            min(x_near, x_far) - (1.5 if ax < 0 else 0),
            origin[1] - 5.2,
            z0 + 3,
            max(x_near, x_far) + (1.5 if ax > 0 else 0),
            origin[1] + 5.2,
            z1 - 4,
        ))
    else:
        y_near = origin[1] + ay * SKIN
        y_far = origin[1] + ay * (SKIN + depth)
        cuts.append(box_at(origin[0] - 3.6, min(y_near, y_far), z0, origin[0] + 3.6, max(y_near, y_far), z1))
        cuts.append(box_at(
            origin[0] - 5.2,
            min(y_near, y_far) - (1.5 if ay < 0 else 0),
            z0 + 3,
            origin[0] + 5.2,
            max(y_near, y_far) + (1.5 if ay > 0 else 0),
            z1 - 4,
        ))
    return cuts, sign


def retainer_mesh():
    """Bar that closes a magnet slot. The ear stays inside the slot.

    It does not reach the mating face, so it cannot hook the panel to the frame.
    """
    bar = box_at(0.15, 0.2, 0.0, POCKET_DEPTH - 0.25, 6.6, 28.0)
    ear = box_at(0.7, -1.3, 3.0, POCKET_DEPTH - 0.7, 8.1, 24.0)
    return cleanup(union([bar, ear]), "retainer")


def ceiling_parts(cx, cy, z_plate_bottom):
    """Rigid puck under the plate. Diffuser is tied to the rim. Cavity is empty."""
    z1 = z_plate_bottom
    z0 = z1 - CEILING_DEPTH
    shell = cyl_along("z", CEILING_OD, CEILING_DEPTH, (cx, cy, (z0 + z1) / 2))
    # Overlap the plate by 1.6 so the puck is one body with the frame.
    neck = cyl_along("z", 6.0, 3.2, (cx, cy, z1 - 0.4))
    # Baffle ring, opaque, between cavity and the printed ceiling.
    return [shell, neck]


def ceiling_cuts(cx, cy, z_plate_bottom):
    z1 = z_plate_bottom
    z0 = z1 - CEILING_DEPTH
    # Leave a 1 mm diffuser at the bottom, tied by a rim, with two light slots.
    cavity_z0 = z0 + DIFFUSER_T + AIR_GAP
    cavity = box_at(cx - 3, cy - 3, cavity_z0, cx + 3, cy + 3, cavity_z0 + LED_CAVITY[2])
    air = box_at(cx - 4.2, cy - 4.2, z0 + DIFFUSER_T, cx + 4.2, cy + 4.2, cavity_z0 + 0.05)
    slot_a = box_at(cx - 3.4, cy - 0.7, z0 - 0.4, cx - 0.6, cy + 0.7, z0 + DIFFUSER_T + 0.3)
    slot_b = box_at(cx + 0.6, cy - 0.7, z0 - 0.4, cx + 3.4, cy + 0.7, z0 + DIFFUSER_T + 0.3)
    feed = cyl_along("z", FEED_D, 8.0, (cx, cy, z1 - 1.0))
    return [cavity, air, slot_a, slot_b, feed]


def sconce_parts(x0, y0, z0, face):
    w, d, h = SCONCE
    if face == "+y":
        body = box_at(x0, y0 - 1.4, z0, x0 + w, y0 + d, z0 + h)
    elif face == "-y":
        body = box_at(x0, y0 - d, z0, x0 + w, y0 + 1.4, z0 + h)
    elif face == "+x":
        body = box_at(x0 - 1.4, y0, z0, x0 + d, y0 + w, z0 + h)
    elif face == "-x":
        body = box_at(x0 - d, y0, z0, x0 + 1.4, y0 + w, z0 + h)
    else:
        raise ValueError(face)
    return [body]


def sconce_cuts(x0, y0, z0, face):
    w, d, h = SCONCE
    # Cavity sits just behind the outdoor/room diffuser. Feed leaves the back into the wall.
    if face == "-y":
        cavity = box_at(x0 + 1.0, y0 - d + DIFFUSER_T + AIR_GAP, z0 + 4.0, x0 + 1.0 + 6, y0 - d + DIFFUSER_T + AIR_GAP + 3, z0 + 4 + 6)
        air = box_at(x0 + 0.6, y0 - d + DIFFUSER_T, z0 + 3.2, x0 + w - 0.6, y0 - d + DIFFUSER_T + AIR_GAP + 0.05, z0 + h - 2.4)
        slot = box_at(x0 + 1.5, y0 - d - 0.3, z0 + 5.5, x0 + w - 1.5, y0 - d + DIFFUSER_T + 0.2, z0 + 7.2)
        feed = cyl_along("y", FEED_D, 6.0, (x0 + w / 2, y0 - 1.5, z0 + h / 2))
    elif face == "+y":
        cavity = box_at(x0 + 1.0, y0 + DIFFUSER_T + AIR_GAP, z0 + 4.0, x0 + 7.0, y0 + DIFFUSER_T + AIR_GAP + 3.0, z0 + 10.0)
        air = box_at(x0 + 0.6, y0 + DIFFUSER_T, z0 + 3.2, x0 + w - 0.6, y0 + DIFFUSER_T + AIR_GAP + 0.05, z0 + h - 2.4)
        slot = box_at(x0 + 1.5, y0 + DIFFUSER_T - 0.2, z0 + 5.5, x0 + w - 1.5, y0 + d + 0.3, z0 + 7.2)
        feed = cyl_along("y", FEED_D, 6.0, (x0 + w / 2, y0 + d - 1.0, z0 + h / 2))
    else:
        raise ValueError(face)
    return [cavity, air, slot, feed]


def lantern_parts(x, y, z, face):
    return sconce_parts(x, y, z, face)


def channel_groove(x0, y0, z_top, x1, y1):
    """4 x 3 covered channel in the top of a plate. Open upward."""
    return box_at(x0, y0, z_top - CHANNEL[1], x1, y1, z_top + 0.4)


def resistor_pocket(x0, y0, z_top):
    return box_at(x0, y0, z_top - RESISTOR[2], x0 + RESISTOR[0], y0 + RESISTOR[1], z_top + 0.5)


def connector_pocket(x0, y0, z0, face):
    """30 x 20 x 12, opening rearward out of a pilaster. Not inside a post."""
    if face == "+y":
        return box_at(x0, y0 - 0.4, z0, x0 + CONNECTOR[0], y0 + CONNECTOR[2], z0 + CONNECTOR[1])
    raise ValueError(face)


def stair_solid(spec):
    """Solid stepped flight. The last riser stops short of the upper floor.

    No full-height stringer: that box would run through the landing.
    """
    x0, x1 = spec["x0"], spec["x1"]
    z0 = spec["z"] + 0.95
    parts = []
    for i in range(RISES):
        z1 = spec["z"] + (i + 1) * RISE
        last = i == RISES - 1
        if spec["up"] > 0:
            y_b = spec["y0"] + i * TREAD + (2.4 if last else 3.2)
            y_a = spec["y0"]
        else:
            y_a = spec["y1"] - i * TREAD - (2.4 if last else 3.2)
            y_b = spec["y1"]
        parts.append(box_at(x0, y_a, z0, x1, y_b, z1 - (0.45 if last else 0.0)))
    return union(parts)


def gable_roof(x0, y0, x1, y1, z_seat, rise, steps=6):
    depth = y1 - y0
    parts = []
    for i in range(steps):
        inset = (depth * 0.42) * (i / steps)
        z0 = z_seat + rise * i / steps
        z1 = z_seat + rise * (i + 1) / steps + 1.6
        parts.append(box_at(x0, y0 + inset, z0, x1, y1 - inset, z1))
    return union(parts)


def hip_roof(x0, y0, x1, y1, z_seat, rise, steps=7, finial=True):
    parts = []
    for i in range(steps):
        tx = (x1 - x0) * 0.40 * (i / steps)
        ty = (y1 - y0) * 0.40 * (i / steps)
        z0 = z_seat + rise * i / steps
        z1 = z_seat + rise * (i + 1) / steps + 1.3
        parts.append(box_at(x0 + tx, y0 + ty, z0, x1 - tx, y1 - ty, z1))
    if finial:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        parts.append(cyl_along("z", 8.0, 16.0, (cx, cy, z_seat + rise + 6)))
    return union(parts)


def flat_roof(x0, y0, x1, y1, z_seat, thick=6.0):
    slab = box_at(x0, y0, z_seat, x1, y1, z_seat + thick)
    fascia = box_at(x0 - 1.2, y0 - 1.2, z_seat + 1.0, x1 + 1.2, y0 + 3.0, z_seat + thick + 2.0)
    return union([slab, fascia])


def panel_mesh(bounds, face, windows, z_centers, door=False):
    x0, y0, z0, x1, y1, z1 = bounds
    if face == "-y":
        body = box_at(x0, y1 - PANEL_T, z0, x1, y1, z1)
        stile_a = box_at(x0, y1 - 6.4, z0, x0 + 16, y1, z1)
        stile_b = box_at(x1 - 16, y1 - 6.4, z0, x1, y1, z1)
        rail_b = box_at(x0, y1 - 6.4, z0, x1, y1, z0 + 8)
        rail_t = box_at(x0, y1 - 6.4, z1 - 8, x1, y1, z1)
        skin = siding_on(face, x0, y1 - PANEL_T, z0, x1, y1, z1)
        cuts = []
        trim = []
        for win in windows:
            cuts.append(window_cut(face, win["x"], y1 - PANEL_T, win["z"], win["w"], win["h"], 8))
            trim.extend(window_trim(face, win["x"], y1 - PANEL_T, win["z"], win["w"], win["h"], 2.2))
        if door:
            cuts.append(window_cut(face, (x0 + x1) / 2 - 16, y1 - PANEL_T, z0 - 0.2, 32, 40, 8))
            trim.extend(window_trim(face, (x0 + x1) / 2 - 16, y1 - PANEL_T, z0 + 2, 32, 36, 2.2))
        # Mating face is y1. Into the panel is -Y. The slot does not cross that face.
        for sx in (x0 + 8, x1 - 8):
            slot, _sign = magnet_slot_cuts((0, -1), (sx, y1), 0, 0, z_centers)
            cuts.extend(slot)
        mesh = union([difference(union([body, stile_a, stile_b, rail_b, rail_t, *skin]), cuts), *trim])
    elif face == "-x":
        body = box_at(x0, y0, z0, x0 + PANEL_T, y1, z1)
        stile_a = box_at(x0, y0, z0, x0 + 6.4, y0 + 16, z1)
        stile_b = box_at(x0, y1 - 16, z0, x0 + 6.4, y1, z1)
        rail_b = box_at(x0, y0, z0, x0 + 6.4, y1, z0 + 8)
        rail_t = box_at(x0, y0, z1 - 8, x0 + 6.4, y1, z1)
        skin = siding_on(face, x0, y0, z0, x0 + PANEL_T, y1, z1)
        cuts = []
        trim = []
        for win in windows:
            cuts.append(window_cut(face, x0, win["y"], win["z"], win["w"], win["h"], 8))
            trim.extend(window_trim(face, x0, win["y"], win["z"], win["w"], win["h"], 2.2))
        for sy in (y0 + 8, y1 - 8):
            slot, _sign = magnet_slot_cuts((1, 0), (x0, sy), 0, 0, z_centers)
            cuts.extend(slot)
        mesh = union([difference(union([body, stile_a, stile_b, rail_b, rail_t, *skin]), cuts), *trim])
    elif face == "+x":
        body = box_at(x1 - PANEL_T, y0, z0, x1, y1, z1)
        stile_a = box_at(x1 - 6.4, y0, z0, x1, y0 + 16, z1)
        stile_b = box_at(x1 - 6.4, y1 - 16, z0, x1, y1, z1)
        rail_b = box_at(x1 - 6.4, y0, z0, x1, y1, z0 + 8)
        rail_t = box_at(x1 - 6.4, y0, z1 - 8, x1, y1, z1)
        skin = siding_on(face, x1 - PANEL_T, y0, z0, x1, y1, z1)
        cuts = []
        trim = []
        for win in windows:
            cuts.append(window_cut(face, x1, win["y"], win["z"], win["w"], win["h"], 8))
            trim.extend(window_trim(face, x1 - PANEL_T, win["y"], win["z"], win["w"], win["h"], 2.2))
        for sy in (y0 + 8, y1 - 8):
            slot, _sign = magnet_slot_cuts((-1, 0), (x1, sy), 0, 0, z_centers)
            cuts.extend(slot)
        mesh = union([difference(union([body, stile_a, stile_b, rail_b, rail_t, *skin]), cuts), *trim])
    else:
        raise ValueError(face)
    return cleanup(mesh, f"panel {face}")


def base_mesh(x0, y0, x1, y1, pockets, extra, faces):
    slab = box_at(x0, y0, 4.0, x1, y1, BASE_TOP)
    rim = [
        box_at(x0, y0, 0, x1, y0 + 8, BASE_TOP),
        box_at(x0, y1 - 8, 0, x1, y1, BASE_TOP),
        box_at(x0, y0, 0, x0 + 8, y1, BASE_TOP),
        box_at(x1 - 8, y0, 0, x1, y1, BASE_TOP),
    ]
    parts = [slab, *rim, *extra, *brick_skirt(x0, y0, x1, y1, BASE_TOP, faces)]
    mesh = union(parts)
    cuts = []
    for px, py in pockets:
        cuts.append(box_at(px - 0.45, py - 0.45, BASE_TOP - POCKET, px + POST + 0.45, py + POST + 0.45, BASE_TOP + 0.3))
    return cleanup(difference(mesh, cuts), "base")


def floor_mesh(x0, y0, x1, y1, z_top, opening, pockets):
    z0 = z_top - FLOOR_T
    slab = box_at(x0, y0, z0 + 1.5, x1, y1, z_top)
    rim = [
        box_at(x0, y0, z0, x1, y0 + 7, z_top),
        box_at(x0, y1 - 7, z0, x1, y1, z_top),
        box_at(x0, y0, z0, x0 + 7, y1, z_top),
        box_at(x1 - 7, y0, z0, x1, y1, z_top),
    ]
    mesh = union([slab, *rim])
    cuts = []
    if opening:
        cuts.append(box_at(*opening))
    for px, py in pockets:
        cuts.append(box_at(px - 0.45, py - 0.45, z_top - POCKET, px + POST + 0.45, py + POST + 0.45, z_top + 0.3))
    mesh = difference(mesh, cuts)
    ribs = []
    x = x0 + 16
    while x < x1 - 16:
        ribs.append(box_at(x, y0 + 12, z_top - 1.0, x + 1.3, y1 - 12, z_top + 0.55))
        x += 14
    mesh = union([mesh, *ribs])
    if opening:
        mesh = difference(mesh, [box_at(*opening)])
    return cleanup(mesh, "floor")


def posts_of(x0, y0, x1, y1):
    # Outer faces are the building faces, so a panel can sit flat against them.
    return {
        "FL": (x0, y0),
        "FR": (x1 - POST, y0),
        "RL": (x0, y1 - POST),
        "RR": (x1 - POST, y1 - POST),
    }


def frame_mesh(spec):
    x0, y0, x1, y1 = spec["x0"], spec["y0"], spec["x1"], spec["y1"]
    z_floor = spec["floor"]
    z_pb, z_pt = plate_zs(z_floor)
    c = posts_of(x0, y0, x1, y1)
    parts = []
    for px, py in c.values():
        parts.append(box_at(px, py, z_floor - (POCKET - GAP), px + POST, py + POST, z_pt))
    # Plate. Leave the rear pilaster and the walls welded in.
    parts.append(box_at(x0 + 2, y0 + 2, z_pb, x1 - 2, y1 - 2, z_pt))
    # Rear wall.
    parts.append(box_at(x0 + 4, y1 - WALL, z_floor + 0.25, x1 - 4, y1, z_pb + 1.5))
    # Party wall, if any.
    if spec.get("party") == "+x":
        parts.append(box_at(x1 - WALL, y0 + POST + 2, z_floor + 0.25, x1, y1 - POST - 2, z_pb + 1.5))
    if spec.get("side") == "-x":
        parts.append(box_at(x0, y0 + POST + 2, z_floor + 0.25, x0 + WALL, y1 - POST - 2, z_pb + 1.5))
    if spec.get("side") == "+x":
        parts.append(box_at(x1 - WALL, y0 + POST + 2, z_floor + 0.25, x1, y1 - POST - 2, z_pb + 1.5))
    # Front head beam. Flat face at y0. No lip below it.
    parts.append(box_at(c["FL"][0] + POST - 1, y0, z_pb - 12, c["FR"][0] + 1, y0 + WALL, z_pb + 1.5))
    # Rear pilaster, added outside the corner posts and overlapped into the rear wall.
    px0 = spec["pilaster_x"]
    parts.append(box_at(px0, y1 - 2.0, z_floor + 0.3, px0 + 44, y1 + 16, z_pt))
    # Cornice on the free front, stopping at the plate top so the roof can sit.
    parts.append(box_at(x0 + 6, y0 - 3.0, z_pt - 5.5, x1 - 6, y0 + 0.8, z_pt - 0.4))
    extras = spec.get("solids") or []
    parts.extend(extras)
    mesh = union(parts)
    cuts = []
    # Rear window.
    for win in spec.get("rear_windows") or []:
        cuts.append(window_cut("+y", win["x"], y1, win["z"], win["w"], win["h"], WALL))
    # Doors through the party wall.
    for door in spec.get("doors") or []:
        cuts.append(box_at(door[0], door[1], door[2], door[3], door[4], door[5]))
    # Side windows if the side wall is fixed.
    for win in spec.get("side_windows") or []:
        face = win["face"]
        if face == "-x":
            cuts.append(window_cut(face, x0, win["y"], win["z"], win["w"], win["h"], WALL))
        elif face == "+x":
            cuts.append(window_cut(face, x1, win["y"], win["z"], win["w"], win["h"], WALL))
    # Plate service channel, resistor pocket, feed, fixtures.
    for cut in spec.get("cuts") or []:
        cuts.append(cut)
    # Pilaster chase, open to the rear, larger than 12 x 8. Does not enter the corner posts.
    cuts.append(box_at(px0 + 8, y1 + 4, z_floor + 2, px0 + 8 + RISER[0], y1 + 16.4, z_pt - 2))
    # Connector pocket opening rearward at this storey.
    cuts.append(box_at(px0 + 6, y1 + 16 - CONNECTOR[2], z_pb - 4, px0 + 6 + CONNECTOR[0], y1 + 16.5, z_pb - 4 + CONNECTOR[1]))
    mesh = difference(mesh, cuts)
    trim = []
    for win in spec.get("rear_windows") or []:
        trim.extend(window_trim("+y", win["x"], y1, win["z"], win["w"], win["h"], 2.0))
    for win in spec.get("side_windows") or []:
        face = win["face"]
        x_face = x0 if face == "-x" else x1
        trim.extend(window_trim(face, x_face, win["y"], win["z"], win["w"], win["h"], 2.0))
    for win in spec.get("bay_windows") or []:
        trim.extend(window_trim(win["face"], win["x"], win["y"], win["z"], win["w"], win["h"], 2.0))
    # Door casing on the party wall, proud into the room, not filling the hole.
    for door in spec.get("door_trim") or []:
        trim.extend(door)
    if trim:
        mesh = union([mesh, *trim])
    return cleanup(mesh, spec["name"])


def simple_chair():
    seat = box_at(0, 0, 8, 16, 16, 11)
    back = box_at(0, 12, 8, 16, 15, 28)
    legs = [box_at(1, 1, 0, 3, 3, 9), box_at(13, 1, 0, 15, 3, 9), box_at(1, 13, 0, 3, 15, 9), box_at(13, 13, 0, 15, 15, 9)]
    return cleanup(union([seat, back, *legs]), "chair")


def simple_table():
    top = box_at(0, 0, 16, 36, 22, 18.5)
    legs = [box_at(2, 2, 0, 5, 5, 17), box_at(31, 2, 0, 34, 5, 17), box_at(2, 17, 0, 5, 20, 17), box_at(31, 17, 0, 34, 20, 17)]
    return cleanup(union([top, *legs]), "table")


def simple_sofa():
    base = box_at(0, 0, 4, 48, 20, 12)
    back = box_at(0, 14, 8, 48, 20, 26)
    arm_l = box_at(0, 0, 8, 5, 16, 20)
    arm_r = box_at(43, 0, 8, 48, 16, 20)
    return cleanup(union([base, back, arm_l, arm_r]), "sofa")


def simple_bed():
    frame = box_at(0, 0, 2, 40, 72, 10)
    head = box_at(0, 64, 6, 40, 72, 28)
    return cleanup(union([frame, head]), "bed")


def simple_figure():
    foot = box_at(3, 3, 0, 9, 9, 4)
    leg = box_at(4, 4, 3, 8, 8, 16)
    body = box_at(2.5, 3, 15, 9.5, 9, 31)
    head = cyl_along("z", 6.5, 7.0, (6, 6, 33))
    return cleanup(union([foot, leg, body, head]), "figure")


def coupon_pair():
    """Same slot cutter as the house, on a straight-pull pair. No sill hook."""
    frame = box_at(0, 0, 0, 36, 16, 70)
    panel = box_at(4, -6.4, 4, 32, -0.5, 64)
    zc = [18, 34, 50]
    cuts = []
    for sx in (10, 26):
        slot, _s = magnet_slot_cuts((0, 1), (sx, 0), 0, 0, zc)
        cuts.extend(slot)
    frame = cleanup(difference(frame, cuts), "coupon frame")
    cuts = []
    for sx in (10, 26):
        slot, _s = magnet_slot_cuts((0, -1), (sx, -0.5), 0, 0, [c - 4 for c in (22, 38, 54)])
        # coupon panel local z is shifted; chambers are cut in its own coordinates below
        cuts.extend(slot)
    # Rebuild panel cuts in the panel's coordinates directly.
    panel_body = box_at(0, 0, 0, 28, 6.4, 60)
    pcuts = []
    for sx in (6, 22):
        slot, _s = magnet_slot_cuts((0, -1), (sx, 6.4), 0, 0, [16, 32, 48])
        pcuts.extend(slot)
    panel = cleanup(difference(panel_body, pcuts), "coupon panel")
    return frame, panel


def polarity_fixture():
    """Shallow wells. Discs are not enclosed and must be removed."""
    bed = box_at(0, 0, 0, 40, 24, 6)
    well_a = cyl_along("z", MAGNET_D + 0.4, 1.2, (12, 12, 5.6))
    well_b = cyl_along("z", MAGNET_D + 0.4, 1.2, (28, 12, 5.6))
    gap = box_at(16, 4, 5.2, 24, 20, 6.4)
    return cleanup(difference(bed, [well_a, well_b, gap]), "polarity")


def fixture_section():
    """Printable slice of the ceiling puck: cavity, air gap, captive diffuser, 2 mm feed, 4x3 channel."""
    plate = box_at(0, 0, 7, 36, 28, 7 + PLATE_T)
    puck = cyl_along("z", CEILING_OD, CEILING_DEPTH, (18, 14, 7 - CEILING_DEPTH / 2))
    neck = cyl_along("z", 6.0, 3.0, (18, 14, 7 - 0.2))
    mesh = union([plate, puck, neck])
    cuts = ceiling_cuts(18, 14, 7)
    cuts.append(channel_groove(4, 12, 7 + PLATE_T, 32, 16))
    cuts.append(resistor_pocket(6, 4, 7 + PLATE_T))
    # Cut the front off so the cavity, feed, and channel are visible in one solid.
    # A viewing notch, not a second body: it stays tied at the back.
    cuts.append(box_at(-1, -1, 0, 18, 14, 20))
    return cleanup(difference(mesh, cuts), "fixture section")


def service_cabinet():
    """Adult bay. Clear volume 150 x 90 x 30. Cover is a separate part."""
    outer = box_at(0, 0, 0, 158, 102, 42)
    void = box_at(4, 6, 6, 4 + BAY_CLEAR[0], 6 + BAY_CLEAR[1], 6 + BAY_CLEAR[2])
    # Rear opening for the cover, and a house-side inlet for the riser jumper.
    mouth = box_at(6, 96, 8, 152, 103, 36)
    inlet = box_at(20, -0.4, 8, 20 + RISER[0] + 4, 8, 8 + RISER[1] + 4)
    mesh = difference(outer, [void, mouth, inlet])
    return cleanup(mesh, "service")


def service_cover():
    door = box_at(0, 0, 0, 142, 6, 26)
    tongue_l = box_at(-1.6, 1.2, 2, 0.4, 4.6, 24)
    tongue_r = box_at(141.6, 1.2, 2, 143.6, 4.6, 24)
    return cleanup(union([door, tongue_l, tongue_r]), "service cover")


CATALOG = {}
INSTANCES = []
WINDOWS = []
FIXTURES = []


def add_part(name, mesh, note):
    extents = [round(float(v), 2) for v in mesh.extents]
    if any(extents[i] > FIT_MAX[i] + 0.2 for i in range(3)):
        raise RuntimeError(f"{name} exceeds fit envelope {extents} > {FIT_MAX}")
    CATALOG[name] = {
        "mesh": mesh,
        "note": note,
        "triangles": int(len(mesh.faces)),
        "volume_mm3": round(float(mesh.volume), 1),
        "extents": extents,
    }
    print(f"part {name} {extents} tri {len(mesh.faces)}", flush=True)


def add_instance(part, iid, role, color, motion, explode, world, extra=None):
    INSTANCES.append({
        "id": iid,
        "part": part,
        "role": role,
        "color": color,
        "motion": motion,
        "explode_mm": explode,
        "world": world,
        "extra": extra or {},
    })


def shift_to_origin(mesh):
    local = mesh.copy()
    origin = local.bounds[0].copy()
    local.apply_translation(-origin)
    return local, [float(v) for v in origin]


def build():
    # --- bases ---
    tower_pockets = list(posts_of(T_X0, Y0, T_X1, Y1).values())
    hall_pockets = list(posts_of(H_X0, Y0, H_X1, Y1).values())
    living_pockets = list(posts_of(L_X0, Y0, L_X1, Y1).values())
    porch_deck_h = box_at(H_X0, PORCH_Y0, 4.0, H_X1, Y0 + 2, BASE_TOP)
    porch_deck_l = box_at(L_X0, PORCH_Y0, 4.0, 412, Y0 + 2, BASE_TOP)
    bay_slab = box_at(BAY_X0, BAY_Y0, 4.0, BAY_X1, Y0 + 2, BASE_TOP)
    apron_t = box_at(30, Y1 - 2, 0, 180, Y1 + 16, 15.5)
    apron_h = box_at(H_X0 + 16, Y1 - 2, 0, H_X1 - 16, Y1 + 16, 15.5)
    apron_l = box_at(L_X0 + 16, Y1 - 2, 0, L_X1 - 30, Y1 + 16, 15.5)
    groove_z0, groove_z1 = 3.0, 3.0 + RISER[1]
    # Horizontal collector, open rearward, avoiding corner posts.
    def apron_groove(x0, x1):
        return box_at(x0, Y1 + 5, groove_z0, x1, Y1 + 16.6, groove_z1)

    tower_base = base_mesh(T_X0, Y0, T_X1, Y1, tower_pockets, [apron_t], "wsn")
    tower_base = cleanup(difference(tower_base, [apron_groove(40, 170)]), "tower base groove")
    hall_base = base_mesh(H_X0, Y0, H_X1, Y1, hall_pockets, [porch_deck_h, apron_h], "sn")
    hall_base = cleanup(difference(hall_base, [apron_groove(H_X0 + 24, H_X1 - 24)]), "hall base groove")
    living_base = base_mesh(L_X0, Y0, L_X1, Y1, living_pockets, [porch_deck_l, bay_slab, apron_l], "sne")
    living_base = cleanup(difference(living_base, [apron_groove(L_X0 + 24, L_X1 - 40)]), "living base groove")
    add_part("qa3_base_tower_v3", *shift_keep(tower_base, "Tower base, brick courses, rear service apron."))
    place_last("qa3_base_tower_v3", "tower-base", "structure", "#8d5a45", [0, 0, 0])
    add_part("qa3_base_hall_v3", *shift_keep(hall_base, "Entry base. The porch deck is this slab, not a second building."))
    place_last("qa3_base_hall_v3", "hall-base", "structure", "#8d5a45", [0, 0, 0])
    add_part("qa3_base_living_v3", *shift_keep(living_base, "Living-room base, continuous with the bay floor."))
    place_last("qa3_base_living_v3", "living-base", "structure", "#8d5a45", [0, 0, 0])

    # floors
    # Wells cover the whole flight so the upper steps are not capped by the floor.
    open1 = (WELL1[0], WELL1[1], L2 - FLOOR_T - 0.4, WELL1[2], WELL1[3], L2 + 0.8)
    open2 = (WELL2[0], WELL2[1], L3 - FLOOR_T - 0.4, WELL2[2], WELL2[3], L3 + 0.8)
    fl_t2 = floor_mesh(T_X0, Y0, T_X1, Y1, L2, open1, tower_pockets)
    fl_t3 = floor_mesh(T_X0, Y0, T_X1, Y1, L3, open2, tower_pockets)
    fl_h = floor_mesh(H_X0, Y0, H_X1, Y1, L2, None, hall_pockets)
    fl_l = floor_mesh(L_X0, Y0, L_X1, Y1, L2, None, living_pockets)
    add_part("qa3_floor_tower_l2_v3", *shift_keep(fl_t2, "Tower second floor. Opening is the lower stair."))
    place_last("qa3_floor_tower_l2_v3", "tower-floor-l2", "structure", "#c4a574", [0, 0, 8])
    add_part("qa3_floor_tower_l3_v3", *shift_keep(fl_t3, "Loft floor. Opening is the upper stair."))
    place_last("qa3_floor_tower_l3_v3", "tower-floor-l3", "structure", "#c4a574", [0, 0, 16])
    add_part("qa3_floor_hall_v3", *shift_keep(fl_h, "Upper hall floor. Reached through the tower landing door."))
    place_last("qa3_floor_hall_v3", "hall-floor", "structure", "#c4a574", [0, 0, 8])
    add_part("qa3_floor_living_v3", *shift_keep(fl_l, "Living-bedroom floor."))
    place_last("qa3_floor_living_v3", "living-floor", "structure", "#c4a574", [0, 0, 8])

    stairs_l = cleanup(stair_solid(S1), "stair lower")
    stairs_u = cleanup(stair_solid(S2), "stair upper")
    add_part("qa3_stair_lower_v3", *shift_keep(stairs_l, "Fourteen rises from the parlor floor to the second-floor landing."))
    place_last("qa3_stair_lower_v3", "stair-lower", "stair", "#8a6a3b", [0, 0, 6])
    add_part("qa3_stair_upper_v3", *shift_keep(stairs_u, "Fourteen rises from that landing to the tower loft."))
    place_last("qa3_stair_upper_v3", "stair-upper", "stair", "#8a6a3b", [0, 0, 14])

    # frames and fixtures are built per storey
    build_frames()
    build_panels()
    build_roofs()
    build_service()
    build_small()
    place_furniture()


def shift_keep(mesh, note):
    """Return (local mesh, note) while stashing the world mesh on the catalog via a side channel.

    add_part only sees the local mesh. The world mesh is recovered by the translation
    stored in ORIGINS.
    """
    local, origin = shift_to_origin(mesh)
    ORIGINS.append(origin)
    WORLD.append(mesh)
    return local, note


ORIGINS = []
WORLD = []


def take_world():
    return WORLD[-1], ORIGINS[-1]


def place_last(part, iid, role, color, explode):
    world, origin = take_world()
    add_instance(part, iid, role, color, None, explode, world, {"origin": origin})


def build_frames():
    # Shared fixture plan. Coordinates are the housing origins.
    # Each ceiling light sits on a fixed plate. Channels run in that plate to the pilaster.
    specs = []
    # Tower storeys
    for index, floor in enumerate((L1, L2, L3)):
        z_pb, z_pt = plate_zs(floor)
        cx, cy = 70.0, 100.0
        solids = ceiling_parts(cx, cy, z_pb)
        cuts = ceiling_cuts(cx, cy, z_pb)
        cuts.append(channel_groove(cx - 2, cy, z_pt, cx + 2, Y1 - 6))
        cuts.append(channel_groove(40, Y1 - 18, z_pt, 168, Y1 - 14))
        cuts.append(resistor_pocket(46, Y1 - 36, z_pt))
        rear = [{"x": 78, "z": floor + 28, "w": 36, "h": 52}]
        doors = []
        door_trim = []
        if index < 2:
            dy0 = 48 if index == 0 else 148
            dy1 = dy0 + 46
            doors.append((T_X1 - WALL - 0.4, dy0, floor + 1.5, T_X1 + 0.3, dy1, floor + 84))
        if index == 0:
            cuts.append(box_at(WELL1[0], WELL1[1], z_pb - 1.0, WELL1[2], WELL1[3], z_pt + 1.0))
        elif index == 1:
            cuts.append(box_at(WELL2[0], WELL2[1], z_pb - 1.0, WELL2[2], WELL2[3], z_pt + 1.0))
        side = None
        side_windows = []
        # sconce on rear wall, room side, wired into the rear channel
        solids.extend(sconce_parts(48, Y1 - WALL, floor + 48, "-y"))
        cuts.extend(sconce_cuts(48, Y1 - WALL, floor + 48, "-y"))
        specs.append({
            "name": f"tower-l{index+1}",
            "part": f"qa3_frame_tower_l{index+1}_v3",
            "x0": T_X0, "y0": Y0, "x1": T_X1, "y1": Y1, "floor": floor,
            "party": "+x" if True else None,
            "side": side,
            "pilaster_x": 148.0,
            "rear_windows": rear,
            "doors": doors,
            "side_windows": side_windows,
            "solids": solids,
            "cuts": cuts,
            "note": f"Tower frame, storey {index+1}. Ceiling puck and rear sconce are part of this solid.",
        })
        FIXTURES.append({"id": f"tower-l{index+1}-ceiling", "kind": "ceiling", "room": ["parlor", "tower-bedroom", "loft"][index], "x": cx, "y": cy, "z": z_pb - CEILING_DEPTH, "storey": index + 1, "circuit": ["parlor", "tower-bedroom", "loft"][index]})
        FIXTURES.append({"id": f"tower-l{index+1}-sconce", "kind": "sconce", "room": ["parlor", "tower-bedroom", "loft"][index], "x": 52, "y": Y1 - WALL - 4, "z": floor + 48, "storey": index + 1, "circuit": ["parlor", "tower-bedroom", "loft"][index], "cavity": (52, Y1 - WALL - 8.5, floor + 55), "shell": (49.2, Y1 - WALL - 0.5, floor + 50.5)})
        WINDOWS.append({"part_hint": f"tower-l{index+1}", "face": "+y", "x": 78, "y": Y1, "z": floor + 28, "w": 36, "h": 52})

    # Hall
    for index, floor in enumerate((L1, L2)):
        z_pb, z_pt = plate_zs(floor)
        cx, cy = 275.0, 90.0
        solids = ceiling_parts(cx, cy, z_pb)
        cuts = ceiling_cuts(cx, cy, z_pb)
        cuts.append(channel_groove(cx - 2, cy, z_pt, cx + 2, Y1 - 6))
        cuts.append(resistor_pocket(H_X0 + 30, Y1 - 40, z_pt))
        doors = []
        dy0 = 44 if index == 0 else 148
        dy1 = dy0 + 46
        doors.append((H_X1 - WALL - 0.4, dy0, floor + 1.5, H_X1 + 0.3, dy1, floor + 84))
        solids.extend(sconce_parts(240, Y1 - WALL, floor + 46, "-y"))
        cuts.extend(sconce_cuts(240, Y1 - WALL, floor + 46, "-y"))
        porch_solids = []
        if index == 0:
            # Porch posts and beam. Lantern pad is added material on the post, not a cut through it.
            porch_solids.append(box_at(214, -46, L1 + 0.3, 228, -32, z_pt))
            porch_solids.append(box_at(214, -48, z_pt - 10, H_X1, 2.0, z_pt))
            porch_solids.extend(lantern_parts(216, -46, floor + 62, "-y"))
            cuts.extend(sconce_cuts(216, -46, floor + 62, "-y"))
            # Entry lantern on the fixed jamb, outside the panel's x range.
            porch_solids.extend(lantern_parts(H_X0 + 2, 0.0, floor + 58, "-y"))
            cuts.extend(sconce_cuts(H_X0 + 2, 0.0, floor + 58, "-y"))
            FIXTURES.append({"id": "porch-lantern-w", "kind": "lantern", "room": "porch", "x": 220, "y": -54, "z": floor + 68, "storey": 1, "circuit": "exterior", "cavity": (220, -54.5, floor + 69), "shell": (217.2, -46.5, floor + 64.5)})
            FIXTURES.append({"id": "entry-lantern", "kind": "lantern", "room": "entry", "x": H_X0 + 6, "y": -6, "z": floor + 64, "storey": 1, "circuit": "exterior", "cavity": (H_X0 + 6, -8.5, floor + 65), "shell": (H_X0 + 3.2, -0.5, floor + 60.5)})
        specs.append({
            "name": f"hall-l{index+1}",
            "part": f"qa3_frame_hall_l{index+1}_v3",
            "x0": H_X0, "y0": Y0, "x1": H_X1, "y1": Y1, "floor": floor,
            "party": "+x",
            "pilaster_x": H_X0 + 40,
            "rear_windows": [{"x": 250, "z": floor + 30, "w": 40, "h": 48}],
            "doors": doors,
            "solids": solids + porch_solids,
            "cuts": cuts,
            "note": f"Hall frame, storey {index+1}. Porch posts, when present, are this solid.",
        })
        FIXTURES.append({"id": f"hall-l{index+1}-ceiling", "kind": "ceiling", "room": ["entry", "upper-hall"][index], "x": cx, "y": cy, "z": z_pb - 7, "storey": index + 1, "circuit": ["entry", "upper-hall"][index]})
        FIXTURES.append({"id": f"hall-l{index+1}-sconce", "kind": "sconce", "room": ["entry", "upper-hall"][index], "x": 244, "y": Y1 - 12, "z": floor + 46, "storey": index + 1, "circuit": ["entry", "upper-hall"][index], "cavity": (244, Y1 - WALL - 8.5, floor + 53), "shell": (241.2, Y1 - WALL - 0.5, floor + 48.5)})

    # Living
    for index, floor in enumerate((L1, L2)):
        z_pb, z_pt = plate_zs(floor)
        cx, cy = 450.0, 110.0
        solids = ceiling_parts(cx, cy, z_pb)
        cuts = ceiling_cuts(cx, cy, z_pb)
        cuts.append(channel_groove(cx - 2, 40, z_pt, cx + 2, Y1 - 6))
        cuts.append(resistor_pocket(L_X0 + 24, Y1 - 42, z_pt))
        solids.extend(sconce_parts(400, Y1 - WALL, floor + 50, "-y"))
        cuts.extend(sconce_cuts(400, Y1 - WALL, floor + 50, "-y"))
        side_windows = []
        extra = []
        if index == 0:
            # Bay walls, same frame as the living room. Windows cut below.
            extra.append(box_at(BAY_X0, BAY_Y0, L1 + 0.25, BAY_X0 + WALL, 2.0, z_pt))
            extra.append(box_at(BAY_X1 - WALL, BAY_Y0, L1 + 0.25, BAY_X1, 2.0, z_pt))
            # Head only. The sash panel is the bay front, so there is no wall behind it.
            extra.append(box_at(BAY_X0, BAY_Y0, z_pt - 8, BAY_X1, BAY_Y0 + WALL, z_pt))
            extra.append(box_at(BAY_X0 + WALL, BAY_Y0, z_pt - 4, BAY_X1 - WALL, -8.0, z_pt))
            extra.append(box_at(386, -46, L1 + 0.3, 400, -32, z_pt))
            extra.append(box_at(L_X0, -48, z_pt - 10, 408, 2.0, z_pt))
            extra.extend(lantern_parts(388, -46, floor + 62, "-y"))
            cuts.extend(sconce_cuts(388, -46, floor + 62, "-y"))
            cuts.append(window_cut("-x", BAY_X0, BAY_Y0 + 8, floor + 26, 22, 48, WALL))
            cuts.append(window_cut("+x", BAY_X1, BAY_Y0 + 8, floor + 26, 22, 48, WALL))
            FIXTURES.append({"id": "porch-lantern-e", "kind": "lantern", "room": "porch", "x": 392, "y": -54, "z": floor + 68, "storey": 1, "circuit": "exterior", "cavity": (392, -54.5, floor + 69), "shell": (389.2, -46.5, floor + 64.5)})
            WINDOWS.append({"part_hint": "living-bay", "face": "-y", "x": BAY_X0 + 10, "y": BAY_Y0, "z": floor + 26, "w": 70, "h": 52})
        specs.append({
            "name": f"living-l{index+1}",
            "part": f"qa3_frame_living_l{index+1}_v3",
            "x0": L_X0, "y0": Y0, "x1": L_X1, "y1": Y1, "floor": floor,
            "party": None,
            "side": None,
            "pilaster_x": L_X0 + 36,
            "rear_windows": [{"x": 430, "z": floor + 30, "w": 46, "h": 50}],
            "side_windows": side_windows,
            "doors": [],
            "solids": solids + extra,
            "cuts": cuts,
            "bay_windows": [
                {"face": "-x", "x": BAY_X0, "y": BAY_Y0 + 8, "z": floor + 26, "w": 22, "h": 48},
                {"face": "+x", "x": BAY_X1, "y": BAY_Y0 + 8, "z": floor + 26, "w": 22, "h": 48},
            ] if index == 0 else [],
            "note": f"Living frame, storey {index+1}. The bay walls are this solid.",
        })
        FIXTURES.append({"id": f"living-l{index+1}-ceiling", "kind": "ceiling", "room": ["living", "living-bedroom"][index], "x": cx, "y": cy, "z": z_pb - 7, "storey": index + 1, "circuit": ["living", "living-bedroom"][index]})
        FIXTURES.append({"id": f"living-l{index+1}-sconce", "kind": "sconce", "room": ["living", "living-bedroom"][index], "x": 404, "y": Y1 - 12, "z": floor + 50, "storey": index + 1, "circuit": ["living", "living-bedroom"][index], "cavity": (404, Y1 - WALL - 8.5, floor + 57), "shell": (401.2, Y1 - WALL - 0.5, floor + 52.5)})

    for spec in specs:
        mesh = frame_mesh(spec)
        add_part(spec["part"], *shift_keep(mesh, spec["note"]))
        world, origin = take_world()
        add_instance(
            spec["part"], spec["name"] + "-frame", "structure", "#d9c7a4",
            None, [0, 0, 18 if "l2" in spec["name"] else (36 if "l3" in spec["name"] else 0)],
            world, {"storey": spec["floor"], "plate_top": plate_zs(spec["floor"])[1]},
        )


def build_panels():
    def zs(floor):
        z_pb, _pt = plate_zs(floor)
        return floor + 6.0, z_pb - 2.0

    def centers(z0, z1):
        span = z1 - z0
        return [z0 + span * 0.28, z0 + span * 0.52, z0 + span * 0.76]

    jobs = []
    for index, floor in enumerate((L1, L2, L3)):
        z0, z1 = zs(floor)
        win = [{"x": 62, "z": floor + 24, "w": 36, "h": 58}]
        if index == 0:
            win = [{"x": 48, "z": floor + 22, "w": 34, "h": 56}, {"x": 110, "z": floor + 22, "w": 34, "h": 56}]
        jobs.append({
            "part": f"qa3_panel_tower_l{index+1}_front_v3",
            "id": f"tower-l{index+1}-front",
            "bounds": (22, -0.5 - PANEL_T, z0, 178, -0.5, z1),
            "face": "-y",
            "windows": win,
            "pull": [0, -PULL, 0],
            "note": f"Tower front, storey {index+1}. Straight pull. Magnets only.",
        })
        jobs.append({
            "part": f"qa3_panel_tower_l{index+1}_west_v3",
            "id": f"tower-l{index+1}-west",
            "bounds": (-0.5 - PANEL_T, 28, z0, -0.5, 176, z1),
            "face": "-x",
            "windows": [{"y": 70, "z": floor + 24, "w": 36, "h": 56}],
            "pull": [-PULL, 0, 0],
            "note": f"Tower west wall, storey {index+1}. Straight pull. Magnets only.",
        })
    for index, floor in enumerate((L1, L2)):
        z0, z1 = zs(floor)
        jobs.append({
            "part": f"qa3_panel_hall_l{index+1}_front_v3",
            "id": f"hall-l{index+1}-front",
            "bounds": (232, -0.5 - PANEL_T, z0, 332, -0.5, z1),
            "face": "-y",
            "windows": [] if index == 0 else [{"x": 258, "z": floor + 24, "w": 40, "h": 56}],
            "door": index == 0,
            "pull": [0, -PULL, 0],
            "note": "Entry door panel." if index == 0 else "Upper hall front. Straight pull. Magnets only.",
        })
    z0, z1 = zs(L2)
    jobs.append({
        "part": "qa3_panel_living_l2_front_v3",
        "id": "living-l2-front",
        "bounds": (372, -0.5 - PANEL_T, z0, 520, -0.5, z1),
        "face": "-y",
        "windows": [{"x": 400, "z": L2 + 24, "w": 36, "h": 54}, {"x": 456, "z": L2 + 24, "w": 36, "h": 54}],
        "pull": [0, -PULL, 0],
        "note": "Living bedroom front. Straight pull. Magnets only.",
    })
    z0, z1 = zs(L1)
    jobs.append({
        "part": "qa3_panel_bay_front_v3",
        "id": "bay-front",
        "bounds": (BAY_X0 + 6, BAY_Y0 - 0.5 - PANEL_T, z0, BAY_X1 - 6, BAY_Y0 - 0.5, z1),
        "face": "-y",
        "windows": [{"x": BAY_X0 + 18, "z": L1 + 24, "w": 64, "h": 52}],
        "pull": [0, -PULL, 0],
        "note": "Bay window sash. It is the living-room front, and it pulls straight off.",
    })
    for index, floor in enumerate((L1, L2)):
        z0, z1 = zs(floor)
        jobs.append({
            "part": f"qa3_panel_living_l{index+1}_east_v3",
            "id": f"living-l{index+1}-east",
            "bounds": (L_X1 + 0.5, 30, z0, L_X1 + 0.5 + PANEL_T, 170, z1),
            "face": "+x",
            "windows": [{"y": 78, "z": floor + 24, "w": 34, "h": 52}],
            "pull": [PULL, 0, 0],
            "note": f"Living east wall, storey {index+1}. Straight pull. Magnets only.",
        })

    for job in jobs:
        z0 = job["bounds"][2]
        z1 = job["bounds"][5]
        mesh = panel_mesh(job["bounds"], job["face"], job["windows"], centers(z0, z1), job.get("door", False))
        add_part(job["part"], *shift_keep(mesh, job["note"]))
        world, _origin = take_world()
        group = "end" if job["face"] in ("-x", "+x") else "front"
        add_instance(
            job["part"], job["id"], "panel", "#f3ead8",
            {"group": group, "pull": job["pull"]},
            [job["pull"][0] * 0.6, job["pull"][1] * 0.6, 12],
            world,
            {"face": job["face"]},
        )


def build_roofs():
    _pb, tower_plate = plate_zs(L3)
    _pb2, main_plate = plate_zs(L2)
    _pb1, porch_plate = plate_zs(L1)
    tower = hip_roof(T_X0 - 6, Y0 - 8, T_X1 + 4, Y1 + 6, tower_plate + GAP, 78, 7)
    hall = gable_roof(H_X0 + 2, Y0 - 10, H_X1 - 1.2, Y1 + 8, main_plate + GAP, 62, 6)
    living = gable_roof(L_X0 + 1.2, Y0 - 10, L_X1 + 8, Y1 + 8, main_plate + GAP, 62, 6)
    # Chimney is part of the living roof solid.
    living = cleanup(union([living, box_at(470, 150, main_plate + GAP + 40, 496, 176, main_plate + GAP + 92)]), "living roof chimney")
    porch = flat_roof(210, PORCH_Y0, 406, -8, porch_plate + GAP, 6)
    bay = hip_roof(BAY_X0 + 1, BAY_Y0 + 1, BAY_X1 - 1, -9.0, porch_plate + GAP, 6, 3, finial=False)
    roofs = [
        ("qa3_roof_tower_v3", tower, "tower-roof", tower_plate, "Tower roof. One solid. Bears on the loft plate."),
        ("qa3_roof_hall_v3", hall, "hall-roof", main_plate, "Hall roof. Same eave and ridge as the living roof."),
        ("qa3_roof_living_v3", living, "living-roof", main_plate, "Living roof, chimney included. Seats on the living plate only."),
        ("qa3_roof_porch_v3", porch, "porch-roof", porch_plate, "Porch roof. Bears on the porch beam, which is part of the ground frames."),
        ("qa3_roof_bay_v3", bay, "bay-roof", porch_plate, "Bay rooflet. Bears on the bay walls, which are part of the living frame."),
    ]
    for part, mesh, iid, plate, note in roofs:
        add_part(part, *shift_keep(mesh, note))
        world, _o = take_world()
        add_instance(
            part, iid, "roof", "#5d6a72",
            {"group": "roof", "lift": [0, 0, 70], "park": [0, -80, 160]},
            [0, -30, 80],
            world,
            {"plate_top": plate, "seat_z": plate + GAP},
        )


def build_service():
    cabinet = service_cabinet()
    cover = service_cover()
    add_part("qa3_service_cabinet_v3", *shift_keep(cabinet, "Adult service bay. Clear volume 150 x 90 x 30. Separated from the play floors."))
    world, _o = take_world()
    placed = world.copy()
    # world mesh is already in its build coordinates (origin at 0). Place it.
    # service_cabinet is built at local 0. Shift the instance.
    ox, oy, oz = H_X0 + 8, Y1 + 18, 0.0
    placed.apply_translation((ox, oy, oz))
    INSTANCES.append({
        "id": "service-bay",
        "part": "qa3_service_cabinet_v3",
        "role": "service",
        "color": "#3e4752",
        "motion": None,
        "explode_mm": [0, 40, 0],
        "world": placed,
        "extra": {"origin": [ox, oy, oz]},
        "place": [ox, oy, oz],
    })
    add_part("qa3_service_cover_v3", *shift_keep(cover, "Service-bay cover. Adult lifts it. Tongues keep it from falling into the play rooms."))
    cworld, _o = take_world()
    cplaced = cworld.copy()
    cplaced.apply_translation((ox + 8, oy + 94, 8))
    INSTANCES.append({
        "id": "service-cover",
        "part": "qa3_service_cover_v3",
        "role": "service",
        "color": "#5c6770",
        "motion": {"group": "service", "pull": [0, 30, 0]},
        "explode_mm": [0, 70, 0],
        "world": cplaced,
        "extra": {},
        "place": [ox + 8, oy + 94, 8],
    })


def build_small():
    frame, panel = coupon_pair()
    add_part("qa3_coupon_frame_v3", *shift_keep(frame, "Straight-pull coupon, frame half. Same slot as the house. No hook."))
    fworld, _ = take_world()
    add_part("qa3_coupon_panel_v3", *shift_keep(panel, "Straight-pull coupon, panel half. Flat back. Magnets only."))
    pworld, _ = take_world()
    add_part("qa3_retainer_v3", *shift_keep(retainer_mesh(), "Magnet capture bar. Encapsulates the disc. Does not fasten the panel."))
    rworld, _ = take_world()
    add_part("qa3_polarity_v3", *shift_keep(polarity_fixture(), "Polarity aid. Shallow wells. Do not leave discs in it."))
    wworld, _ = take_world()
    add_part("qa3_fixture_section_v3", *shift_keep(fixture_section(), "Ceiling-fixture cross section. Cavity is provisional, not a measured LED."))
    sworld, _ = take_world()
    # Park coupons off the house, excluded from assembly bounds.
    samples = [
        ("qa3_coupon_frame_v3", "coupon-frame", fworld, (620, 0, 0), "coupon", "#c4b49a"),
        ("qa3_coupon_panel_v3", "coupon-panel", pworld, (624, -8, 4), "coupon", "#f3ead8"),
        ("qa3_retainer_v3", "coupon-retainer-frame", rworld, (628, 2, 20), "coupon", "#888888"),
        ("qa3_retainer_v3", "coupon-retainer-panel", rworld, (630, -6, 24), "coupon", "#888888"),
        ("qa3_polarity_v3", "polarity", wworld, (680, 0, 0), "coupon", "#dddddd"),
        ("qa3_fixture_section_v3", "fixture-section", sworld, (760, 0, 0), "sample", "#e6d7b0"),
    ]
    for part, iid, base, shift, role, color in samples:
        world = base.copy()
        world.apply_translation(shift)
        INSTANCES.append({
            "id": iid, "part": part, "role": role, "color": color,
            "motion": {"group": "coupon", "pull": [0, -20, 0]} if "panel" in iid else None,
            "explode_mm": [0, -20, 10],
            "world": world, "extra": {}, "place": list(shift),
        })


def place_furniture():
    chair = simple_chair()
    table = simple_table()
    sofa = simple_sofa()
    bed = simple_bed()
    figure = simple_figure()
    add_part("qa3_chair_v3", *shift_keep(chair, "Chair."))
    add_part("qa3_table_v3", *shift_keep(table, "Table."))
    add_part("qa3_sofa_v3", *shift_keep(sofa, "Sofa."))
    add_part("qa3_bed_v3", *shift_keep(bed, "Bed."))
    add_part("qa3_figure_v3", *shift_keep(figure, "1:24 figure, one solid."))
    items = [
        ("qa3_chair_v3", "parlor-chair", chair, (28, 36, L1 + 0.7), "#8d5a45"),
        ("qa3_table_v3", "parlor-table", table, (70, 70, L1 + 0.7), "#a67c52"),
        ("qa3_figure_v3", "entry-figure", figure, (250, 48, L1 + 0.7), "#c4554a"),
        ("qa3_sofa_v3", "living-sofa", sofa, (400, 70, L1 + 0.7), "#6e4c6a"),
        ("qa3_bed_v3", "tower-bed", bed, (22, 36, L2 + 0.8), "#d7d0c4"),
        ("qa3_bed_v3", "living-bed", bed, (390, 40, L2 + 0.8), "#d7d0c4"),
        ("qa3_chair_v3", "loft-chair", chair, (24, 40, L3 + 0.8), "#8d5a45"),
    ]
    for part, iid, base, shift, color in items:
        world = base.copy()
        world.apply_translation(shift)
        INSTANCES.append({
            "id": iid, "part": part, "role": "furniture", "color": color,
            "motion": None, "explode_mm": [0, 0, 24],
            "world": world, "extra": {}, "place": list(shift),
        })


def place_of(item):
    if "place" in item:
        return item["place"]
    # Structure, floors, panels, roofs were shifted to origin. Recover translation from world bounds min
    # ONLY if the local mesh origin is the min corner. It is.
    return [float(v) for v in item["world"].bounds[0]]


def matrix_at(origin):
    return [
        [1, 0, 0, round(origin[0], 4)],
        [0, 1, 0, round(origin[1], 4)],
        [0, 0, 1, round(origin[2], 4)],
        [0, 0, 0, 1],
    ]


def intersection_volume(a, b):
    hit = tm.boolean.intersection([a, b], engine="manifold")
    if hit is None or hit.is_empty:
        return 0.0
    volume = float(hit.volume)
    return volume if volume > 0 else 0.0


def bbox_overlap(a, b, pad=0.0):
    return not (
        a.bounds[1][0] < b.bounds[0][0] - pad
        or a.bounds[0][0] > b.bounds[1][0] + pad
        or a.bounds[1][1] < b.bounds[0][1] - pad
        or a.bounds[0][1] > b.bounds[1][1] + pad
        or a.bounds[1][2] < b.bounds[0][2] - pad
        or a.bounds[0][2] > b.bounds[1][2] + pad
    )


def moved(mesh, vector):
    copy = mesh.copy()
    copy.apply_translation(vector)
    return copy


def audits():
    failures = []
    house = [item for item in INSTANCES if item["role"] not in ("coupon", "sample")]
    worst = 0.0
    worst_pair = None
    checked = 0
    for i in range(len(house)):
        for j in range(i + 1, len(house)):
            if not bbox_overlap(house[i]["world"], house[j]["world"]):
                continue
            checked += 1
            volume = intersection_volume(house[i]["world"], house[j]["world"])
            if volume > worst:
                worst = volume
                worst_pair = (house[i]["id"], house[j]["id"], round(volume, 2))
            if volume > 0.5:
                failures.append({"pair": [house[i]["id"], house[j]["id"]], "mm3": round(volume, 2)})
                print(f" clash {house[i]['id']} x {house[j]['id']} {volume:.1f}", flush=True)
    print(f"rest pairs {checked} worst {worst_pair}", flush=True)

    roofs = []
    for item in house:
        if item["role"] != "roof":
            continue
        plate_top = item["extra"]["plate_top"]
        seat = item["extra"]["seat_z"]
        footprint = item["world"].bounds
        probe = box_at(
            footprint[0][0] + 6, footprint[0][1] + 6, plate_top - 0.25,
            footprint[1][0] - 6, footprint[1][1] - 6, plate_top,
        )
        bearing = 0.0
        bearer = None
        for other in house:
            if other["role"] != "structure":
                continue
            if not bbox_overlap(probe, other["world"]):
                continue
            volume = intersection_volume(probe, other["world"])
            if volume > bearing:
                bearing = volume
                bearer = other["id"]
        lifted = moved(item["world"], item["motion"]["lift"])
        lift_hit = 0.0
        for other in house:
            if other["id"] == item["id"] or other["role"] == "roof":
                continue
            if not bbox_overlap(lifted, other["world"]):
                continue
            lift_hit = max(lift_hit, intersection_volume(lifted, other["world"]))
        row = {
            "id": item["id"],
            "bodies": 1,
            "seat_gap_mm": round(seat - plate_top, 3),
            "bearing_probe_mm3": round(bearing, 1),
            "bearer": bearer,
            "straight_lift_mm3": round(lift_hit, 2),
        }
        roofs.append(row)
        if bearing < 80:
            failures.append({"roof": item["id"], "bearing_mm3": round(bearing, 1), "bearer": bearer})
        if lift_hit > 0.5:
            failures.append({"roof_lift": item["id"], "mm3": round(lift_hit, 2)})
    print("roofs", roofs, flush=True)

    sweeps = []
    fixed = [item for item in house if item["role"] != "panel"]
    for item in house:
        if item["role"] != "panel":
            continue
        pull = item["motion"]["pull"]
        if item["motion"].get("slide") or item["motion"].get("lift"):
            failures.append({"panel_motion": item["id"], "detail": "slide or lift is not allowed"})
        for distance in (0.0, 10.0, 22.0, 40.0):
            scale = distance / PULL
            shifted = moved(item["world"], [pull[0] * scale, pull[1] * scale, pull[2] * scale])
            hit = 0.0
            for other in fixed:
                if not bbox_overlap(shifted, other["world"]):
                    continue
                hit = max(hit, intersection_volume(shifted, other["world"]))
            if hit > 0.5:
                failures.append({"sweep": item["id"], "mm": distance, "mm3": round(hit, 2)})
                print(f" sweep {item['id']} {distance} {hit:.1f}", flush=True)
        sweeps.append({"id": item["id"], "pull": pull, "slide": None, "lift": None})

    # Stair probes.
    stair_rows = []
    floors = [item for item in house if "floor" in item["part"] or item["part"].startswith("qa3_base")]
    overhead = [item for item in house if item["role"] in ("structure", "roof") or "floor" in item["part"]]
    for spec, iid, target in ((S1, "stair-lower", L2), (S2, "stair-upper", L3)):
        mesh = next(item["world"] for item in house if item["id"] == iid)
        top = float(mesh.bounds[1][2])
        bottom = float(mesh.bounds[0][2])
        # Opening probe: a box in the well at the upper floor must miss that floor.
        if spec["up"] > 0:
            well = box_at(spec["x0"] + 4, spec["y0"] + 20, target - 2, spec["x1"] - 4, spec["y1"] - 20, target + 1)
        else:
            well = box_at(spec["x0"] + 4, spec["y0"] + 10, target - 2, spec["x1"] - 4, spec["y1"] - 16, target + 1)
        blocked = 0.0
        for item in house:
            if "floor_tower" not in item["part"]:
                continue
            if abs(item["world"].bounds[0][2] - (target - FLOOR_T)) > 3:
                continue
            blocked = max(blocked, intersection_volume(well, item["world"]))
        # Headroom samples along the walking line.
        tight = 999.0
        for i in range(0, RISES - 1, 2):
            z_step = spec["z"] + (i + 1) * RISE
            if spec["up"] > 0:
                y = spec["y0"] + i * TREAD + 4
            else:
                y = spec["y1"] - i * TREAD - 4
            x = (spec["x0"] + spec["x1"]) / 2
            probe = box_at(x - 2, y - 2, z_step + 2, x + 2, y + 2, z_step + 2 + HEADROOM)
            clear = True
            for item in overhead:
                if not bbox_overlap(probe, item["world"]):
                    continue
                if intersection_volume(probe, item["world"]) > 0.2:
                    clear = False
                    break
            if not clear:
                # Measure how far up is actually clear by shrinking.
                for height in (70, 60, 50, 40):
                    probe = box_at(x - 2, y - 2, z_step + 2, x + 2, y + 2, z_step + 2 + height)
                    blocked_h = False
                    for item in overhead:
                        if bbox_overlap(probe, item["world"]) and intersection_volume(probe, item["world"]) > 0.2:
                            blocked_h = True
                            break
                    if not blocked_h:
                        tight = min(tight, height)
                        break
                else:
                    tight = min(tight, 0)
            else:
                tight = min(tight, HEADROOM)
        row = {
            "id": iid,
            "bottom_z": round(bottom, 2),
            "top_z": round(top, 2),
            "target_floor_z": target,
            "top_gap_mm": round(target - top, 2),
            "well_blocked_mm3": round(blocked, 2),
            "headroom_sample_mm": None if tight > 900 else tight,
        }
        stair_rows.append(row)
        if blocked > 0.5:
            failures.append({"stair_well": iid, "mm3": round(blocked, 2)})
        if top > target - 0.2 or target - top > 2.0:
            failures.append({"stair_top": iid, "gap": round(target - top, 2)})
        if bottom < spec["z"] - 0.2:
            failures.append({"stair_bottom": iid, "z": bottom})
        if row["headroom_sample_mm"] is not None and row["headroom_sample_mm"] < HEADROOM:
            failures.append({"headroom": iid, "mm": row["headroom_sample_mm"]})
    print("stairs", stair_rows, flush=True)

    # Doorway probes. A box in each opening must miss structure.
    doors = [
        ("parlor-entry", box_at(T_X1 - 6, 56, L1 + 20, H_X0 + 4, 86, L1 + 68)),
        ("entry-living", box_at(H_X1 - 6, 52, L1 + 20, L_X0 + 4, 82, L1 + 68)),
        ("landing-hall", box_at(T_X1 - 6, 156, L2 + 20, H_X0 + 4, 186, L2 + 68)),
        ("hall-bedroom", box_at(H_X1 - 6, 156, L2 + 20, L_X0 + 4, 186, L2 + 68)),
    ]
    door_rows = []
    for name, probe in doors:
        hit = 0.0
        for item in house:
            if item["role"] not in ("structure",) and "floor" not in item["part"] and "base" not in item["part"]:
                continue
            if not bbox_overlap(probe, item["world"]):
                continue
            hit = max(hit, intersection_volume(probe, item["world"]))
        door_rows.append({"id": name, "blocked_mm3": round(hit, 2)})
        if hit > 0.5:
            failures.append({"door": name, "mm3": round(hit, 2)})
            print(f" door {name} {hit:.1f}", flush=True)

    # Fixture: housing material exists, cavity probe is empty, feed probe is empty.
    fixture_rows = []
    for fix in FIXTURES:
        host = None
        for item in house:
            if item["role"] != "structure":
                continue
            if fix["z"] + 2 < item["world"].bounds[0][2] or fix["z"] > item["world"].bounds[1][2] + 2:
                continue
            if item["world"].bounds[0][0] - 2 <= fix["x"] <= item["world"].bounds[1][0] + 2:
                host = item
                break
        if "cavity" in fix:
            cx, cy, cz = fix["cavity"]
            sx, sy, sz = fix["shell"]
            cavity = box_at(cx - 0.6, cy - 0.5, cz - 0.6, cx + 0.6, cy + 0.5, cz + 0.6)
            shell = box_at(sx - 0.35, sy - 0.35, sz - 0.35, sx + 0.35, sy + 0.35, sz + 0.35)
        else:
            cavity = box_at(fix["x"] - 1.2, fix["y"] - 1.2, fix["z"] + 2.2, fix["x"] + 1.2, fix["y"] + 1.2, fix["z"] + 3.6)
            shell = box_at(fix["x"] - 0.4, fix["y"] - 0.4, fix["z"] + 0.3, fix["x"] + 0.4, fix["y"] + 0.4, fix["z"] + 1.2)
        empty = None
        solid = None
        if host is not None:
            empty = round(intersection_volume(cavity, host["world"]), 2)
            solid = round(intersection_volume(shell, host["world"]), 2)
            if empty > 0.4:
                failures.append({"cavity": fix["id"], "mm3": empty})
            if solid < 0.2:
                failures.append({"fixture_body": fix["id"], "shell_mm3": solid})
        else:
            failures.append({"fixture_host": fix["id"]})
        fixture_rows.append({"id": fix["id"], "host": None if host is None else host["id"], "cavity_mm3": empty, "shell_mm3": solid})
    print("fixtures", fixture_rows, flush=True)

    windows = []
    samples = [
        ("tower-l1-front", box_at(58, -8, L1 + 32, 68, 1, L1 + 42), box_at(46, -7, L1 + 18, 84, 1, L1 + 23)),
        ("bay-front", box_at(BAY_X0 + 26, BAY_Y0 - 8, L1 + 32, BAY_X0 + 40, BAY_Y0 + 2, L1 + 42), box_at(BAY_X0 + 16, BAY_Y0 - 8, L1 + 20, BAY_X0 + 80, BAY_Y0 + 2, L1 + 25)),
        ("hall-l1-front", box_at(274, -8, L1 + 30, 290, 1, L1 + 38), box_at(250, -7, L1 + 8, 310, 1, L1 + 16)),
    ]
    for iid, hole, sill in samples:
        host = next(item["world"] for item in house if item["id"] == iid)
        open_mm3 = round(intersection_volume(hole, host), 2)
        sill_mm3 = round(intersection_volume(sill, host), 2)
        windows.append({"id": iid, "hole_mm3": open_mm3, "sill_mm3": sill_mm3})
        if open_mm3 > 0.5:
            failures.append({"window_hole": iid, "mm3": open_mm3})
        if sill_mm3 < 1.0:
            failures.append({"window_sill": iid, "mm3": sill_mm3})
    print("windows", windows, flush=True)

    # Nominal disc in the coupon panel chamber.
    panel = CATALOG["qa3_coupon_panel_v3"]["mesh"]
    disc = cyl_along("y", MAGNET_D, MAGNET_T, (6, 6.4 - SKIN - POCKET_DEPTH / 2, 16))
    fit = intersection_volume(panel, disc)
    over = intersection_volume(panel, cyl_along("y", MAGNET_D + 1.0, MAGNET_T, (6, 6.4 - SKIN - 1.0, 16)))
    magnet = {
        "status": MAGNET_STATUS,
        "nominal_mm": [MAGNET_D, MAGNET_T],
        "radial_clearance_per_side_mm": CLEAR_RADIAL,
        "axial_clearance_mm": CLEAR_AXIAL,
        "pocket_diameter_mm": round(POCKET_D, 2),
        "pocket_depth_mm": round(POCKET_DEPTH, 2),
        "mating_skin_mm": SKIN,
        "seat_gap_mm": SEAT,
        "nominal_disc_intersection_mm3": round(fit, 3),
        "one_mm_oversize_intersection_mm3": round(over, 3),
        "holding_force_calculated": False,
        "h3c_pause_profile": False,
        "pairs_per_panel": 6,
        "retention": "magnetic_only_straight_pull",
        "capture_bar": "encapsulates the magnet only; it is not a panel hook, sill, or latch",
    }
    if fit > 0.05:
        failures.append({"magnet_fit": fit})
    if over < 1.0:
        failures.append({"magnet_oversize": over})

    return {
        "ok": not failures,
        "failures": failures[:24],
        "rest_pairs": checked,
        "worst_mm3": round(worst, 3),
        "worst_pair": worst_pair,
        "roofs": roofs,
        "stairs": stair_rows,
        "doors": door_rows,
        "panel_sweeps": sweeps,
        "windows": windows,
        "fixtures": fixture_rows,
        "magnet": magnet,
    }


def legacy_interface():
    tile = tm.load(LEGACY_TILE)
    post = tm.load(LEGACY_POST)
    peg = post.copy()
    peg.apply_transform(rotation_matrix(np.pi, [1, 0, 0]))
    peg.apply_translation((15.875, 15.875, 11.0))
    seated = intersection_volume(tile, peg)
    return {
        "tile_bbox_mm": [round(float(v), 3) for v in tile.extents],
        "seated_peg_mm3": round(seated, 3),
        "snap_compatible": False,
        "note": "Measured on floor_tile_v0 and snap_post_v0. This house does not use that socket.",
    }


def plan_document():
    def marks(storey):
        return [
            {"id": fix["id"], "kind": fix["kind"], "x": fix["x"], "y": fix["y"], "circuit": fix["circuit"]}
            for fix in FIXTURES if fix["storey"] == storey
        ]

    return {
        "storeys": [
            {
                "storey": 1,
                "floor_z": L1,
                "doors": [
                    {"id": "parlor-entry", "x0": 192, "y0": 48, "x1": 210, "y1": 94},
                    {"id": "entry-living", "x0": 342, "y0": 44, "x1": 360, "y1": 90},
                    {"id": "front-door", "x0": 266, "y0": -6, "x1": 298, "y1": 8},
                ],
                "stairs": [{"id": "lower-flight", "x0": WELL1[0], "y0": WELL1[1], "x1": WELL1[2], "y1": WELL1[3]}],
                "lights": marks(1),
                "rooms": [
                    {"id": "parlor", "name": "Parlor", "x0": 12, "y0": 16, "x1": 146, "y1": 190, "note": "Tower ground floor, west of the stair."},
                    {"id": "stair-hall", "name": "Stair", "x0": 150, "y0": 22, "x1": 192, "y1": 168, "note": "Lower flight. Continues to the landing, then to the loft."},
                    {"id": "entry", "name": "Entry", "x0": 214, "y0": 12, "x1": 336, "y1": 190, "note": "Front door on the porch. Doors to the parlor and the living room."},
                    {"id": "living", "name": "Living room", "x0": 364, "y0": 12, "x1": 526, "y1": 190, "note": "Includes the bay, which is this room pushed forward."},
                    {"id": "porch", "name": "Porch", "x0": 210, "y0": -52, "x1": 406, "y1": 0, "note": "Deck is the entry base. Not a shed."},
                    {"id": "bay", "name": "Bay", "x0": BAY_X0, "y0": BAY_Y0, "x1": BAY_X1, "y1": 0, "note": "Living-room window bay. Same floor, same frame."},
                ],
            },
            {
                "storey": 2,
                "floor_z": L2,
                "doors": [
                    {"id": "landing-hall", "x0": 192, "y0": 148, "x1": 210, "y1": 194},
                    {"id": "hall-bedroom", "x0": 342, "y0": 148, "x1": 360, "y1": 194},
                ],
                "stairs": [
                    {"id": "lower-well", "x0": WELL1[0], "y0": WELL1[1], "x1": WELL1[2], "y1": WELL1[3]},
                    {"id": "upper-flight", "x0": WELL2[0], "y0": WELL2[1], "x1": WELL2[2], "y1": WELL2[3]},
                ],
                "lights": marks(2),
                "rooms": [
                    {"id": "tower-bedroom", "name": "Tower bedroom", "x0": 12, "y0": 16, "x1": 146, "y1": 150, "note": "West of the stair opening."},
                    {"id": "landing", "name": "Landing", "x0": 16, "y0": 168, "x1": 192, "y1": 202, "note": "Arrives from below. Door to the upper hall. Second flight leaves toward the loft."},
                    {"id": "upper-hall", "name": "Upper hall", "x0": 214, "y0": 16, "x1": 336, "y1": 190, "note": "Corridor from the tower door to the living bedroom."},
                    {"id": "living-bedroom", "name": "Bedroom", "x0": 364, "y0": 16, "x1": 526, "y1": 190, "note": "Over the living room."},
                ],
            },
            {
                "storey": 3,
                "floor_z": L3,
                "doors": [],
                "stairs": [{"id": "upper-well", "x0": WELL2[0], "y0": WELL2[1], "x1": WELL2[2], "y1": WELL2[3]}],
                "lights": marks(3),
                "rooms": [
                    {"id": "loft", "name": "Tower loft", "x0": 12, "y0": 16, "x1": 96, "y1": 190, "note": "Reached only by the upper flight. The well beside it is that stair."},
                ],
            },
        ]
    }


def lighting_document(report):
    circuits = {}
    for fix in FIXTURES:
        circuits.setdefault(fix["circuit"], []).append(fix["id"])
    count = len(FIXTURES)
    return {
        "architecture": "External regulated nominal 5V USB. Parallel warm-white 5-12V DC Chip/Nano LEDs, each with its own supplied resistor.",
        "rejected": [
            "3V LED variant on this bus",
            "mains wiring inside the house",
            "one shared resistor for several bare LEDs",
            "coin cells, loose lithium cells, or charging in the house",
            "AA boost as the default supply",
        ],
        "alternatives": {
            "regulated_12V": "Possible with the same pre-resistored 5-12V LEDs. The 6V PPTC candidate is not usable on 12V. Not the default.",
            "aa_boost": "Optional later module, 3xAA plus a 5.2V boost, in its own bay. Not modeled. Not the default. No parallel connection with the USB supply.",
        },
        "cavity_mm": list(LED_CAVITY),
        "cavity_status": "PROVISIONAL_NOT_FIT_VALIDATED",
        "ceiling_housing_mm": [CEILING_OD, CEILING_DEPTH],
        "exterior_housing_mm": list(SCONCE),
        "diffuser_mm": DIFFUSER_T,
        "air_gap_mm": AIR_GAP,
        "feedthrough_diameter_mm": FEED_D,
        "feedthrough_note": "Smooth 2 mm feed for unconnectorized LED leads only. A resistor or a plug does not pass this hole.",
        "local_channel_mm": list(CHANNEL),
        "riser_clear_mm": list(RISER),
        "riser_minimum_from_research_mm": [12, 8],
        "riser_note": "The spine is added behind the rear wall. Corner posts are not hollowed out. 14 x 10 is this house's chase because every circuit drops here. 12 x 8 was the research minimum.",
        "connector_pocket_mm": list(CONNECTOR),
        "resistor_pocket_mm": list(RESISTOR),
        "service_bay_clear_mm": list(BAY_CLEAR),
        "optional_battery_bay": "Not in this cabinet. A separate 100 x 80 x 35 holder plus a 40 x 35 x 15 converter area would be a later module.",
        "fixture_count": count,
        "research_scenario_leds": 24,
        "research_scenario_budget_A": 0.48,
        "house_budget_A_at_20mA": round(count * 0.020, 3),
        "budget_is_measured": False,
        "protection_finalized": False,
        "electrically_tested": False,
        "mains_inside": False,
        "supply_example": "Adafruit 501 is an out-of-stock voltage example, not a kit to buy.",
        "protection_note": "Littelfuse 1206L050 (6V, 0.5A hold) is not selected. It is not sole protection for unknown fine LED wire, and its resistance can drop a 5V bus. A current-limited bench test is still required.",
        "circuits": [{"id": key, "fixtures": value, "switch": "adult service bay, one station per circuit, plus a master"} for key, value in circuits.items()],
        "fixtures": [
            {key: (list(value) if isinstance(value, tuple) else value) for key, value in fix.items()}
            for fix in FIXTURES
        ],
        "route": [
            "LED in the fixture cavity on a fixed plate, wall, or porch post",
            "2 mm feed, bare leads only, into the 4 x 3 plate channel",
            "resistor pocket 25 x 12 x 8 in that channel, not inside the lamp",
            "connector pocket 30 x 20 x 12 in the rear pilaster",
            "14 x 10 rear chase down the pilaster, outside the corner posts",
            "horizontal collector in the rear apron, across a 0.8 mm module joint with a short fixed jumper",
            "adult service bay in the cabinet behind the hall",
        ],
        "panel_rule": "No conductor is routed on a removable panel or a lift-off roof. Roofs have no LEDs and no disconnect. Pulling a panel leaves the harness on the frame.",
        "fixture_probe": report["fixtures"],
    }


def write_outputs(report, legacy):
    os.makedirs(STL_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    for name in os.listdir(STL_DIR):
        if name.endswith(".stl") and not name.startswith("qa3_"):
            os.remove(os.path.join(STL_DIR, name))
    origins = {}
    # CATALOG meshes are local. Instance worlds carry placement.
    for item in INSTANCES:
        if item["part"] not in origins:
            origins[item["part"]] = place_of(item)
    for name, info in CATALOG.items():
        path = os.path.join(STL_DIR, f"{name}.stl")
        info["mesh"].export(path)

    house = [item for item in INSTANCES if item["role"] not in ("coupon", "sample")]
    mins = np.min([item["world"].bounds[0] for item in house], axis=0)
    maxs = np.max([item["world"].bounds[1] for item in house], axis=0)
    size = maxs - mins

    panels = [item for item in INSTANCES if item["role"] == "panel"]
    retainer_qty = len(panels) * 4 + 2  # two stiles on the panel and two on the frame, plus the coupon pair
    parts = []
    for name, info in CATALOG.items():
        parts.append({
            "id": name,
            "file": f"stl/{name}.stl",
            "note": info["note"],
            "triangles": info["triangles"],
            "volume_mm3": info["volume_mm3"],
            "watertight": True,
            "bodies": 1,
            "bbox_mm": info["extents"],
            "fits_brim_allowance": True,
        })
    bom = {}
    instances = []
    for item in INSTANCES:
        bom[item["part"]] = bom.get(item["part"], 0) + 1
        origin = item.get("place") or place_of(item)
        instances.append({
            "id": item["id"],
            "part": item["part"],
            "role": item["role"],
            "color": item["color"],
            "motion": item["motion"],
            "explode_mm": item["explode_mm"],
            "transform": matrix_at(origin),
        })
    bom_rows = []
    for name, qty in sorted(bom.items()):
        row = {"part": name, "file": f"stl/{name}.stl", "qty": qty}
        if name == "qa3_retainer_v3":
            row["print_qty"] = retainer_qty
            row["note"] = "Two bars are shown on the coupon. Print one more for every stile, frame and panel."
        bom_rows.append(row)

    lighting = lighting_document(report)
    manifest = {
        "name": "Queen Anne Playhouse",
        "version": "3.0.0",
        "prior_version": "archive/v2.0.0",
        "also_archived": ["archive/v1.0.0", "archive/v2.0.0"],
        "scale": "1:24",
        "description": "One house: parlor, entry, living room with a bay, porch, two bedrooms, and a tower loft.",
        "units": "mm",
        "up_axis": "Z",
        "printer_nominal_bed_mm": list(BED),
        "fit_envelope_mm": list(FIT_MAX),
        "assembled_size_mm": {
            "x": round(float(size[0]), 1),
            "y": round(float(size[1]), 1),
            "z": round(float(size[2]), 1),
            "min_mm": [round(float(v), 1) for v in mins],
            "max_mm": [round(float(v), 1) for v in maxs],
        },
        "rooms": [
            {"id": "parlor", "storey": 1, "note": "Tower ground floor, west of the stair. Door to the entry."},
            {"id": "entry", "storey": 1, "note": "Front door under the porch. Doors to the parlor and the living room."},
            {"id": "living", "storey": 1, "note": "Living room. The bay is this room, not a shed."},
            {"id": "tower-bedroom", "storey": 2, "note": "West of the stair opening. Door from the landing to the upper hall."},
            {"id": "upper-hall", "storey": 2, "note": "Landing corridor between the tower and the bedroom."},
            {"id": "living-bedroom", "storey": 2, "note": "Over the living room."},
            {"id": "loft", "storey": 3, "note": "Tower third floor. The upper flight arrives here."},
        ],
        "plan": plan_document(),
        "stairs": report["stairs"],
        "magnet": report["magnet"],
        "lighting": lighting,
        "magnet_install_steps": [
            "Print the coupon pair and seat it before the house. The slot is the same cutter as the wall stiles.",
            "The panel pulls straight off. There is no sill hook, no side groove, and no slide-then-lift.",
            "An adult inserts a nominal 5.0 x 2.8 mm disc into each chamber, then slides the capture bar in from the top.",
            "The bar closes the magnet. It does not catch the frame. Six pairs hold each facade. That holding force is not calculated and has not been measured.",
            "Polarity: use the shallow fixture, then take the discs out. Do not leave loose discs in the house.",
            "No pause-print profile was made. If a bar cracks, the disc can be exposed. This is not a child-safety certification.",
        ],
        "limits": [
            "Not printed. No slicer run, no H3C test, no strength test, no fatigue test.",
            "Zero overlap is not a structural proof. Roof uplift is not locked.",
            "Magnet grade is unknown. Panel weight is carried by the magnets only, and that has not been pull-tested.",
            "LED cavity 6 x 6 x 3 mm is a reservation. Chip/Nano size, 5V current, and brightness are not known.",
            "Fixture count is this house, not the 24-LED research scenario. 20 mA is a planning figure, not a measurement.",
            "Protection is not selected. A 6V 0.5A PPTC is not sole protection and can drop a 5V bus.",
            "No mains in the house. USB 5V is the intended supply. The cited 5V adapter was out of stock and is not a buy list.",
            "Service covers are adult parts. Keep them captive in the grooves. No coin cells and no charging.",
        ],
        "legacy_interface": legacy,
        "validation": {
            "printed": False,
            "measured": False,
            "physically_verified": False,
            "forces_tested": False,
            "h3c_sliced": False,
            "h3c_pause_profile": False,
            "electrically_tested": False,
            "protection_finalized": False,
            "led_fit_validated": False,
            "cad_validated": report["ok"],
        },
        "parts": parts,
        "bom": bom_rows,
        "instances": instances,
    }
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    report["assembly_mm"] = manifest["assembled_size_mm"]
    report["instance_count"] = len(instances)
    report["triangles"] = sum(info["triangles"] for info in CATALOG.values())
    report["fixture_count"] = lighting["fixture_count"]
    report["lighting_budget_A"] = lighting["house_budget_A_at_20mA"]
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
    print(json.dumps({
        "ok": report["ok"],
        "failures": report["failures"][:8],
        "parts": len(manifest["parts"]),
        "instances": len(manifest["instances"]),
        "fixtures": report["fixture_count"],
        "triangles": report["triangles"],
    }, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
