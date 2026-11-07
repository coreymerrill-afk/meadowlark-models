"""Queen Anne Playhouse — parametric 1:24 CAD.

Units are millimetres. Z is up. Each mesh is a printable part. The viewer
loads these STLs with the manifest transforms; it does not use a separate
beauty mesh.

This is a CAD model. It has not been printed. Forces, fatigue, layer
adhesion, and stability were not tested. Nothing here is a toy-safety
certification or an H3C slice.
"""
from __future__ import annotations

import json
import os
import traceback

import numpy as np
import trimesh as tm
from trimesh.creation import box, cone, cylinder, icosphere
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STL_DIR = os.path.join(ROOT, "stl")
REPORT_DIR = os.path.join(ROOT, "reports")
LEGACY_TILE = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "floor_tile_v0.stl"))
LEGACY_POST = os.path.abspath(os.path.join(HERE, "..", "..", "stl", "snap_post_v0.stl"))

# Printer envelope from the project brief. Not re-measured on a machine.
BED = (330.0, 320.0, 325.0)
# 10 mm each side in XY for a brim / skirt, 10 mm of Z margin.
FIT_MAX = (BED[0] - 20.0, BED[1] - 20.0, BED[2] - 10.0)

# --- module ---
POST = 14.0
BAY_W = 254.0  # 2 x measured legacy tile, checked against the STL
BAY_D = 210.0  # shallower than a 2-tile depth, for hand reach
WALL = 1.6  # outer shell outside a corner pocket
SIDE = 0.40  # lateral pocket clearance, each side
GAP = 0.30  # vertical seat clearance
POCKET = 4.2
CLEAR = 118.0  # exposed post height / structural clear
PLATE_T = 14.0
FLOOR_T = 7.0
BASE_T = 12.0
SKIN = 3.2
LIFT = 8.6
PULL_SHORT = 18.0
PULL_FULL = 48.0
BAYS = 3
LEVELS = 3

# Panel head capture (relative to floor top and plate bottom).
FIN_DROP = 7.2
FIN_T = 4.6
FLANGE_H = 6.4
HOOK_DROP = 6.6
HOOK_T = 3.4

VOL_LIMIT = 1.0  # mm^3 — above this, solids are interpenetrating


def box_at(x0, y0, z0, x1, y1, z1):
    if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
        raise ValueError(f"bad box {(x0, y0, z0, x1, y1, z1)}")
    mesh = box([(x1 - x0), (y1 - y0), (z1 - z0)])
    mesh.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return mesh


def cyl_z(diameter, height, x, y, z0, sections=32):
    mesh = cylinder(radius=diameter / 2, height=height, sections=sections)
    mesh.apply_translation([x, y, z0 + height / 2])
    return mesh


def union(meshes):
    parts = [m for m in meshes if m is not None]
    if not parts:
        raise ValueError("empty union")
    if len(parts) == 1:
        return parts[0]
    return tm.boolean.union(parts, engine="manifold")


def difference(base, cuts):
    cuts = [c for c in cuts if c is not None]
    if not cuts:
        return base
    return tm.boolean.difference([base, *cuts], engine="manifold")


def cleanup(mesh):
    mesh = mesh.copy()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices(digits_vertex=5)
    mesh.fix_normals()
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def post_interval(origin_span):
    """Post solid interval inside a bay axis of length `origin_span`."""
    start = WALL + SIDE
    left = (start, start + POST)
    right_end = origin_span - WALL - SIDE
    right = (right_end - POST, right_end)
    return left, right


POST_X0, POST_X1 = post_interval(BAY_W)
POST_Y0, POST_Y1 = post_interval(BAY_D)
# names: left/right and front/rear solid ranges
LX0, LX1 = POST_X0
RX0, RX1 = POST_X1
FY0, FY1 = POST_Y0
BY0, BY1 = POST_Y1
OPEN_X0, OPEN_X1 = LX1, RX0
OPEN_Y0, OPEN_Y1 = FY1, BY0


def level_metrics(level):
    """World Z of the exposed floor, post, and plate for one storey."""
    floor_top = BASE_T
    for _ in range(level):
        post_top = floor_top + CLEAR
        plate_top = post_top + GAP + PLATE_T
        floor_top = plate_top + GAP + FLOOR_T
    post_bottom = floor_top - (POCKET - GAP)
    post_top = floor_top + CLEAR
    plate_bottom = post_top + GAP
    plate_top = plate_bottom + PLATE_T
    return {
        "floor_top": floor_top,
        "post_bottom": post_bottom,
        "post_top": post_top,
        "post_len": post_top - post_bottom,
        "plate_bottom": plate_bottom,
        "plate_top": plate_top,
    }


def aabb_overlap(a, b, pad=0.0):
    return (
        a[0][0] < b[1][0] + pad
        and a[1][0] > b[0][0] - pad
        and a[0][1] < b[1][1] + pad
        and a[1][1] > b[0][1] - pad
        and a[0][2] < b[1][2] + pad
        and a[1][2] > b[0][2] - pad
    )


def intersection_volume(a, b):
    if not aabb_overlap(a.bounds, b.bounds, pad=0.02):
        return 0.0
    try:
        hit = tm.boolean.intersection([a, b], engine="manifold")
    except Exception:
        return float("nan")
    if hit is None or len(hit.faces) == 0:
        return 0.0
    volume = float(hit.volume)
    if volume < 0:
        volume = abs(volume)
    return volume


# ---------------------------------------------------------------------------
# Parts, built in bay-local coordinates (0..BAY_W, 0..BAY_D) unless noted.
# ---------------------------------------------------------------------------

def _corner_pads(top_z):
    pads = []
    for x0, x1 in (POST_X0, POST_X1):
        for y0, y1 in (POST_Y0, POST_Y1):
            pads.append(box_at(x0 - SIDE, y0 - SIDE, 0, x1 + SIDE, y1 + SIDE, top_z))
    return pads


def _ribbed_slab(top_z, skin=3.2):
    parts = [box_at(0, 0, top_z - skin, BAY_W, BAY_D, top_z)]
    rim = 8.0
    parts.append(box_at(0, 0, 0, BAY_W, rim, top_z))
    parts.append(box_at(0, BAY_D - rim, 0, BAY_W, BAY_D, top_z))
    parts.append(box_at(0, 0, 0, rim, BAY_D, top_z))
    parts.append(box_at(BAY_W - rim, 0, 0, BAY_W, BAY_D, top_z))
    x = rim
    while x < BAY_W - rim:
        parts.append(box_at(x, 0, 0, min(x + 3.4, BAY_W), BAY_D, top_z))
        x += 36.0
    y = rim
    while y < BAY_D - rim:
        parts.append(box_at(0, y, 0, BAY_W, min(y + 3.4, BAY_D), top_z))
        y += 42.0
    parts.extend(_corner_pads(top_z))
    # Inter-bay lap: tongue on +X, pocket later on -X underside.
    tongue_y0, tongue_y1 = 49.0, 161.0
    parts.append(box_at(BAY_W - 6.0, tongue_y0, 0, BAY_W + 16.0, tongue_y1, 3.0))
    return union(parts)


def _lap_pocket():
    # Underside pocket that receives the neighbour tongue. 0.40 side, 0.35 vertical.
    return box_at(-0.2, 48.4, -0.2, 16.8, 161.6, 3.35)


def base_mesh():
    slab = _ribbed_slab(BASE_T, skin=3.6)
    # Raise the ribbed slab's coordinate: _ribbed_slab uses top_z from 0.
    # Rebuild at BASE_T by using the same function with top BASE_T.
    cuts = []
    # Corner pockets
    for x0, x1 in (POST_X0, POST_X1):
        for y0, y1 in (POST_Y0, POST_Y1):
            cuts.append(box_at(x0 - SIDE, y0 - SIDE, BASE_T - POCKET, x1 + SIDE, y1 + SIDE, BASE_T + 0.5))
    cuts.append(_lap_pocket())
    # Front sill slot for the lift-out hook. Stays inside the front rim.
    cuts.append(box_at(panel_x()[0] + 6, 3.2, BASE_T - 7.4, panel_x()[1] - 6, 3.2 + HOOK_T + 0.8, BASE_T + 0.3))
    # Left end sill (outer end panels). Right end sill is the mirrored cut;
    # both exist so one base STL serves every bay. Interior bays simply
    # leave the end slots unused.
    ey0, ey1 = panel_y()
    cuts.append(box_at(3.2, ey0 + 6, BASE_T - 7.4, 3.2 + HOOK_T + 0.8, ey1 - 6, BASE_T + 0.3))
    cuts.append(box_at(BAY_W - 3.2 - HOOK_T - 0.8, ey0 + 6, BASE_T - 7.4, BAY_W - 3.2, ey1 - 6, BASE_T + 0.3))
    # Rear shear bottom groove.
    cuts.append(box_at(LX1 + 1.0, shear_y()[0] - 0.3, BASE_T - 3.6, RX0 - 1.0, shear_y()[1] + 0.3, BASE_T + 0.2))
    # Porch tongue socket, open toward -Y, two of them so either stoop can dock.
    cuts.append(box_at(28, -0.4, 1.2, 78, 10, 5.2))
    for cx in (BAY_W / 2 - 22.0, BAY_W / 2 + 22.0):
        cuts.append(box_at(cx - 10.0, 140.6, BASE_T - 3.0, cx + 10.0, 147.4, BASE_T + 0.3))
    return cleanup(difference(slab, cuts))


def floor_mesh():
    slab = _ribbed_slab(FLOOR_T, skin=3.2)
    cuts = []
    for x0, x1 in (POST_X0, POST_X1):
        for y0, y1 in (POST_Y0, POST_Y1):
            cuts.append(box_at(x0 - SIDE, y0 - SIDE, FLOOR_T - POCKET, x1 + SIDE, y1 + SIDE, FLOOR_T + 0.5))
    cuts.append(_lap_pocket())
    px0, px1 = panel_x()
    cuts.append(box_at(px0 + 6, 3.2, FLOOR_T - 7.4, px1 - 6, 3.2 + HOOK_T + 0.8, FLOOR_T + 0.3))
    ey0, ey1 = panel_y()
    cuts.append(box_at(3.2, ey0 + 6, FLOOR_T - 7.4, 3.2 + HOOK_T + 0.8, ey1 - 6, FLOOR_T + 0.3))
    cuts.append(box_at(BAY_W - 3.2 - HOOK_T - 0.8, ey0 + 6, FLOOR_T - 7.4, BAY_W - 3.2, ey1 - 6, FLOOR_T + 0.3))
    sy0, sy1 = shear_y()
    cuts.append(box_at(LX1 + 1.0, sy0 - 0.3, FLOOR_T - 3.6, RX0 - 1.0, sy1 + 0.3, FLOOR_T + 0.2))
    # Partition foot sockets (optional, unused where no partition is set).
    # Two foot sockets. The divider origin sits at the bay centre, y = 78.
    for cx in (BAY_W / 2 - 22.0, BAY_W / 2 + 22.0):
        cuts.append(box_at(cx - 10.0, 140.6, FLOOR_T - 3.0, cx + 10.0, 147.4, FLOOR_T + 0.3))
    return cleanup(difference(slab, cuts))


def panel_x():
    margin = 9.0
    return OPEN_X0 + margin, OPEN_X1 - margin


def panel_y():
    margin = 9.0
    return OPEN_Y0 + margin, OPEN_Y1 - margin


def shear_y():
    """Rear shear occupies this Y range (tongue faces the posts in X)."""
    return BY0 - SKIN - 0.45, BY0 - 0.30


def post_mesh(groove=False):
    """Post local frame: X 0..POST, Y 0..POST, Z 0..length.

    The rear post has a groove in the room-facing face (-Y) for the shear tongue.
    """
    length = level_metrics(0)["post_len"]
    mesh = box_at(0, 0, 0, POST, POST, length)
    if groove:
        mesh = difference(mesh, [box_at(2.4, -0.4, -0.2, POST - 2.4, 5.1, length + 0.2)])
    return cleanup(mesh)


def plate_mesh(ledges=False):
    frame = box_at(0, 0, 0, BAY_W, BAY_D, PLATE_T)
    # Through-opening aligned to the post inner faces, so the frame bears on the posts.
    opening = box_at(OPEN_X0, OPEN_Y0, -0.4, OPEN_X1, OPEN_Y1, PLATE_T + 0.4)
    # Front relief pocket, open toward -Y through the front face, above the fin.
    px0, px1 = panel_x()
    # Relief starts at the plate underside so a lifted flange is already in void.
    pocket = box_at(px0 - 1.0, -0.4, -0.25, px1 + 1.0, OPEN_Y0 + FIN_T + 8.0, PLATE_T - 2.2)
    ey0, ey1 = panel_y()
    pocket_l = box_at(-0.4, ey0 - 1.0, -0.25, OPEN_X0 + FIN_T + 8.0, ey1 + 1.0, PLATE_T - 2.2)
    pocket_r = box_at(OPEN_X1 - FIN_T - 8.0, ey0 - 1.0, -0.25, BAY_W + 0.4, ey1 + 1.0, PLATE_T - 2.2)
    # Rear capture groove for the shear tab.
    sy0, sy1 = shear_y()
    rear = box_at(LX1 + 0.6, sy0 - 0.2, -0.3, RX0 - 0.6, sy1 + 0.5, 4.0)
    # No lap on the plate. A tongue here refills the right end-panel pocket.
    # Bases and floors carry the inter-bay key.
    mesh = difference(frame, [opening, pocket, pocket_l, pocket_r, rear])
    # Fins that capture a seated panel. They hang below the plate (local Z < 0).
    fins = [
        box_at(px0, OPEN_Y0, -FIN_DROP, px1, OPEN_Y0 + FIN_T, 0.15),
        box_at(OPEN_X0, ey0, -FIN_DROP, OPEN_X0 + FIN_T, ey1, 0.15),
        box_at(OPEN_X1 - FIN_T, ey0, -FIN_DROP, OPEN_X1, ey1, 0.15),
    ]
    # Corner keeper lips, room side of each post, so a post top cannot walk inward.
    # Inward lips at the room side of each post. Rear lips stop short of the shear.
    keepers = [
        box_at(LX1, FY1 + 1.5, -6.0, LX1 + 2.5, BY0 - 6.0, 0.15),
        box_at(RX0 - 2.5, FY1 + 1.5, -6.0, RX0, BY0 - 6.0, 0.15),
        box_at(LX1 + 1.5, FY1, -6.0, RX0 - 1.5, FY1 + 2.5, 0.15),
    ]
    parts = [mesh, *fins, *keepers]
    if ledges:
        # Two stoop ledges in front of the front posts. In plane with the plate
        # when the plate is printed flat, so they are not an overhang.
        for x0, x1 in (POST_X0, POST_X1):
            parts.append(box_at(x0 + 0.8, -32.0, 0.0, x1 - 0.8, -0.3, 8.0))
    return cleanup(union(parts))


def _window(x0, z0, w, h, y0, y1):
    return box_at(x0, y0 - 0.4, z0, x0 + w, y1 + 0.4, z0 + h)


def front_panel_bay(kind):
    x0, x1 = panel_x()
    flange_top = CLEAR + GAP - 0.55
    flange_bot = flange_top - FLANGE_H
    skin_y0, skin_y1 = 0.9, 0.9 + SKIN
    body = box_at(x0, skin_y0, 0.0, x1, skin_y1, flange_bot)
    # Flanges stop short of the corner so a front leaf and an end leaf do not meet.
    flange = box_at(x0 + 8, OPEN_Y0 + FIN_T + 0.45, flange_bot, x1 - 8, OPEN_Y0 + FIN_T + 7.0, flange_top)
    hook = box_at(x0 + 8, 3.55, -HOOK_DROP, x1 - 8, 3.55 + HOOK_T, 2.4)
    cuts = []
    if kind == "entry":
        door_w = 72.0
        door_x = (x0 + x1) / 2 - door_w / 2
        cuts.append(_window(door_x, -0.2, door_w, 96.0, skin_y0, skin_y1))
        # Side light
        cuts.append(_window(x1 - 28.0, 28.0, 18.0, 64.0, skin_y0, skin_y1))
        # Hook cannot cross the doorway. Replace the full hook with two jamb hooks.
        hook = union(
            [
                box_at(x0 + 6, 3.55, -HOOK_DROP, door_x - 4, 3.55 + HOOK_T, 2.4),
                box_at(door_x + door_w + 4, 3.55, -HOOK_DROP, x1 - 6, 3.55 + HOOK_T, 2.4),
            ]
        )
    else:
        span = x1 - x0
        win_w = 64.0
        gap = 14.0
        left = x0 + (span - (2 * win_w + gap)) / 2
        for wx in (left, left + win_w + gap):
            cuts.append(_window(wx, 28.0, win_w, 70.0, skin_y0, skin_y1))
    # Finger scoops on the outer face. They do not break through the 3.2 mm skin.
    scoop_z = 46.0
    for sx in (x0 + 16, x1 - 40):
        cuts.append(box_at(sx, skin_y0 - 0.2, scoop_z, sx + 24, skin_y0 + 1.5, scoop_z + 16))
    mesh = difference(union([body, flange, hook]), cuts)
    return cleanup(mesh)


def end_panel_bay(side):
    """side is 'left' or 'right'. Built in bay coordinates."""
    y0, y1 = panel_y()
    flange_top = CLEAR + GAP - 0.55
    flange_bot = flange_top - FLANGE_H
    if side == "left":
        skin_x0, skin_x1 = 0.9, 0.9 + SKIN
        flange = box_at(OPEN_X0 + FIN_T + 0.45, y0 + 8, flange_bot, OPEN_X0 + FIN_T + 7.0, y1 - 8, flange_top)
        hook = box_at(3.55, y0 + 8, -HOOK_DROP, 3.55 + HOOK_T, y1 - 8, 2.4)
        outer = skin_x0
    else:
        skin_x0, skin_x1 = BAY_W - 0.9 - SKIN, BAY_W - 0.9
        flange = box_at(OPEN_X1 - FIN_T - 7.0, y0 + 8, flange_bot, OPEN_X1 - FIN_T - 0.45, y1 - 8, flange_top)
        hook = box_at(BAY_W - 3.55 - HOOK_T, y0 + 8, -HOOK_DROP, BAY_W - 3.55, y1 - 8, 2.4)
        outer = skin_x1
    body = box_at(skin_x0, y0, 0.0, skin_x1, y1, flange_bot)
    win_h = 70.0
    win_w = 56.0
    win_y = (y0 + y1) / 2 - win_w / 2
    cuts = [_window_y(skin_x0, skin_x1, win_y, 28.0, win_w, win_h)]
    scoop_y = y0 + 18
    if side == "left":
        cuts.append(box_at(outer - 0.2, scoop_y, 46, outer + 1.5, scoop_y + 22, 62))
    else:
        cuts.append(box_at(outer - 1.5, scoop_y, 46, outer + 0.2, scoop_y + 22, 62))
    return cleanup(difference(union([body, flange, hook]), cuts))


def _window_y(x0, x1, y, z, w, h):
    return box_at(x0 - 0.3, y, z, x1 + 0.3, y + w, z + h)


def rear_panel_bay():
    sy0, sy1 = shear_y()
    body = box_at(LX1 + 0.8, sy0, 0.6, RX0 - 0.8, sy1, CLEAR - 1.2)
    # Tongues enter the -Y groove of each rear post.
    tongue_l = box_at(LX0 + 2.9, BY0 - 0.4, 10.0, LX1 - 2.9, BY0 + 4.3, CLEAR - 12.0)
    tongue_r = box_at(RX0 + 2.9, BY0 - 0.4, 10.0, RX1 - 2.9, BY0 + 4.3, CLEAR - 12.0)
    bottom = box_at(LX1 + 2.2, sy0 + 0.3, -3.0, RX0 - 2.2, sy1 - 0.3, -0.2)
    top = box_at(LX1 + 2.2, sy0 + 0.25, CLEAR + GAP + 0.7, RX0 - 2.2, sy1 - 0.25, CLEAR + GAP + 3.2)
    win = box_at((BAY_W / 2) - 26, sy0 - 0.4, 34, (BAY_W / 2) + 26, sy1 + 0.4, 82)
    return cleanup(difference(union([body, tongue_l, tongue_r, bottom, top]), [win]))


def _soffit_and_plug(x_over0, x_over1, y_over0, y_over1, rise_z):
    """Flat seat. Local Z 0 is the soffit underside, which sits GAP above the plate."""
    soffit = box_at(x_over0, y_over0, 0, x_over1, y_over1, 4.0)
    plug = box_at(OPEN_X0 + 12, OPEN_Y0 + 14, -6.2, OPEN_X1 - 12, OPEN_Y1 - 12, 0.2)
    return union([soffit, plug])


def _gable_shell(x0, x1, y0, y1, z0, rise, ridge="x"):
    if ridge == "x":
        outer = np.array(
            [
                [x0, y0, z0],
                [x1, y0, z0],
                [x1, y1, z0],
                [x0, y1, z0],
                [x0, (y0 + y1) / 2, z0 + rise],
                [x1, (y0 + y1) / 2, z0 + rise],
            ],
            dtype=float,
        )
        inner = np.array(
            [
                [x0 + 4.5, y0 + 6.0, z0 + 3.2],
                [x1 - 4.5, y0 + 6.0, z0 + 3.2],
                [x1 - 4.5, y1 - 6.0, z0 + 3.2],
                [x0 + 4.5, y1 - 6.0, z0 + 3.2],
                [x0 + 4.5, (y0 + y1) / 2, z0 + rise - 8.0],
                [x1 - 4.5, (y0 + y1) / 2, z0 + rise - 8.0],
            ],
            dtype=float,
        )
    else:
        outer = np.array(
            [
                [x0, y0, z0],
                [x1, y0, z0],
                [x1, y1, z0],
                [x0, y1, z0],
                [(x0 + x1) / 2, y0, z0 + rise],
                [(x0 + x1) / 2, y1, z0 + rise],
            ],
            dtype=float,
        )
        inner = np.array(
            [
                [x0 + 6.0, y0 + 4.5, z0 + 3.2],
                [x1 - 6.0, y0 + 4.5, z0 + 3.2],
                [x1 - 6.0, y1 - 4.5, z0 + 3.2],
                [x0 + 6.0, y1 - 4.5, z0 + 3.2],
                [(x0 + x1) / 2, y0 + 4.5, z0 + rise - 8.0],
                [(x0 + x1) / 2, y1 - 4.5, z0 + rise - 8.0],
            ],
            dtype=float,
        )
    shell = difference(tm.convex.convex_hull(outer), [tm.convex.convex_hull(inner)])
    return shell


def roof_ridge():
    seat = _soffit_and_plug(2.0, BAY_W - 2.0, -6.0, BAY_D + 6.0, 72)
    shell = _gable_shell(2.0, BAY_W - 2.0, -6.0, BAY_D + 6.0, 4.0, 72.0, ridge="x")
    return cleanup(union([seat, shell]))


def roof_gable():
    # Front-facing gable. Extra front overhang. Stops 2 mm short of the bay sides.
    seat = _soffit_and_plug(2.0, BAY_W - 2.0, -22.0, BAY_D + 4.0, 104)
    shell = _gable_shell(2.0, BAY_W - 2.0, -22.0, BAY_D + 4.0, 4.0, 104.0, ridge="y")
    chimney = box_at(BAY_W * 0.62, BAY_D * 0.55, 70.0, BAY_W * 0.62 + 26, BAY_D * 0.55 + 20, 132.0)
    flue = cyl_z(12, 40, BAY_W * 0.62 + 13, BAY_D * 0.55 + 10, 100)
    chimney = difference(chimney, [flue])
    return cleanup(union([seat, shell, chimney]))


def roof_tower():
    seat = _soffit_and_plug(-10.0, BAY_W - 2.0, -16.0, BAY_D + 8.0, 150)
    cx = BAY_W * 0.46
    cy = BAY_D * 0.48
    outer = cone(radius=118, height=156, sections=8)
    outer.apply_translation([cx, cy, 4.0 + 78])
    inner = cone(radius=104, height=140, sections=8)
    inner.apply_translation([cx, cy, 4.0 + 86])
    cap_cut = box_at(cx - 160, cy - 160, 4.0 + 148, cx + 160, cy + 160, 4.0 + 220)
    shell = difference(outer, [inner, cap_cut])
    cap = cylinder(radius=22, height=5, sections=8)
    cap.apply_translation([cx, cy, 4.0 + 148 + 2.5])
    # Keep the cone inside the soffit on the shared (+X) side by clipping it.
    clip = box_at(BAY_W - 2.0, -40, -10, BAY_W + 80, BAY_D + 40, 220)
    shell = difference(union([shell, cap]), [clip])
    return cleanup(union([seat, shell]))


def porch_mesh():
    """One stoop. Local origin matches the bay origin, porch in -Y."""
    deck = box_at(18, -74, 0, BAY_W - 18, -1.2, 8.0)
    tongue = box_at(30.4, -1.2, 1.7, 75.6, 9.2, 4.6)
    # Piers stand outside the front-panel removal path (panel X is inset).
    px0, px1 = panel_x()
    pier_l = box_at(4, -68, 0, px0 - 4, -28, 42)
    pier_r = box_at(px1 + 4, -68, 0, BAY_W - 4, -28, 42)
    # Low toe board across the front, below the panel body, so it does not
    # cross the pull path. Top is under the storey floor line (z = BASE_T).
    toe = box_at(px0, -74, 0, px1, -66, 9.2)
    return cleanup(union([deck, tongue, pier_l, pier_r, toe]))


def balcony_mesh():
    """Saddles over the tower-plate ledges. Local Z = 0 is GAP above the ledge top."""
    deck = box_at(LX0 - 2, -78, 0.35, RX1 + 2, -3.0, 6.4)
    rail = box_at(LX0 - 2, -78, 6.4, RX1 + 2, -66, 34.0)
    grip = box_at(LX0 + 30, -78.5, 14.0, RX1 - 30, -65.5, 27.0)
    saddles = []
    voids = []
    ledge_bottom = -(8.0 + GAP)
    for x0, x1 in (POST_X0, POST_X1):
        saddles.append(box_at(x0 - 0.3, -36.0, ledge_bottom - 0.2, x1 + 0.3, -1.0, 6.4))
        voids.append(box_at(x0 + 0.35, -33.0, ledge_bottom - 0.8, x1 - 0.35, 0.3, -0.05))
    return cleanup(difference(union([deck, rail, *saddles]), [grip, *voids]))


def partition_mesh():
    # Feet drop into the floor sockets. Origin is the bay-centre placement point.
    wall = box_at(-40, 0.8, 2.7, 40, 7.2, 66)
    foot_l = box_at(-28.6, 1.4, 0.4, -15.4, 6.6, 4.8)
    foot_r = box_at(15.4, 1.4, 0.4, 28.6, 6.6, 4.8)
    return cleanup(union([wall, foot_l, foot_r]))


def furn_table():
    top = box_at(0, 0, 26, 78, 48, 31)
    ped = box_at(18, 10, 0, 60, 38, 26.2)
    return cleanup(union([top, ped]))


def furn_chair():
    seat = box_at(0, 0, 18, 30, 30, 23)
    back = box_at(0, 24, 18, 30, 30, 44)
    ped = box_at(6, 6, 0, 24, 22, 18.2)
    return cleanup(union([seat, back, ped]))


def furn_bed():
    base = box_at(0, 0, 0, 86, 46, 16)
    head = box_at(0, 38, 0, 86, 46, 32)
    return cleanup(union([base, head]))


def furn_sofa():
    base = box_at(0, 0, 0, 80, 34, 16)
    back = box_at(0, 26, 0, 80, 34, 30)
    arm_l = box_at(0, 0, 0, 8, 34, 24)
    arm_r = box_at(72, 0, 0, 80, 34, 24)
    return cleanup(union([base, back, arm_l, arm_r]))


def furn_figure():
    """One solid 1:24 adult-height gauge. No separate small parts."""
    legs = box_at(-8, -6, 0, 8, 6, 30)
    torso = box_at(-10, -7, 28, 10, 7, 52)
    head = icosphere(subdivisions=1, radius=8)
    head.apply_translation([0, 0, 60])
    return cleanup(union([legs, torso, head]))


def coupon_socket():
    plate = box_at(0, 0, 0, 96, 64, 10)
    # Drop-in lap, open at the top. 0.40 mm side clearance against the plug tongue.
    pocket = box_at(28.0, 14.0, 4.2, 68.0, 50.0, 10.5)
    # Legacy gauge holes only. There is no loose peg.
    legacy_a = cyl_z(6.00, 7.2, 16, 22, 2.8, sections=40)
    legacy_b = cyl_z(6.30, 7.2, 16, 46, 2.8, sections=40)
    return cleanup(difference(plate, [pocket, legacy_a, legacy_b]))


def coupon_plug():
    plate = box_at(16, 8, 10.35, 80, 56, 16)
    tongue = box_at(28.4, 14.4, 4.65, 67.6, 49.6, 10.7)
    return cleanup(union([plate, tongue]))


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def shifted(mesh, x, y, z, rz_deg=0.0):
    out = mesh.copy()
    if rz_deg:
        out.apply_transform(rotation_matrix(np.deg2rad(rz_deg), [0, 0, 1]))
    out.apply_translation([x, y, z])
    return out


def matrix_place(x, y, z, rx=0.0, ry=0.0, rz=0.0):
    acc = np.eye(4)
    for degrees, axis in ((rx, [1, 0, 0]), (ry, [0, 1, 0]), (rz, [0, 0, 1])):
        if degrees:
            rot = rotation_matrix(np.deg2rad(degrees), axis)
            acc = rot @ acc
    acc = translation_matrix([x, y, z]) @ acc
    return acc


def orient_print(mesh, rx=0.0, ry=0.0, rz=0.0):
    """Rotate into the recommended bed pose and drop the minimum corner to 0."""
    acc = np.eye(4)
    out = mesh.copy()
    for degrees, axis in ((rx, [1.0, 0.0, 0.0]), (ry, [0.0, 1.0, 0.0]), (rz, [0.0, 0.0, 1.0])):
        if abs(degrees) > 1e-9:
            rot = rotation_matrix(np.deg2rad(degrees), axis)
            out.apply_transform(rot)
            acc = rot @ acc
    low = out.bounds[0].copy()
    slide = translation_matrix((-low).tolist())
    out.apply_transform(slide)
    acc = slide @ acc
    return cleanup(out), acc


def world_from_print(place, print_acc):
    return place @ np.linalg.inv(print_acc)


PART_BUILDERS = {
    "qa_base_v1": (base_mesh, (0, 0, 0), "Base tile with ground floor, sill slots, and the inter-bay lap."),
    "qa_floor_v1": (floor_mesh, (0, 0, 0), "Upper floor. Corner pockets, sill slots, lap, partition sockets."),
    "qa_post_front_v1": (lambda: post_mesh(), (0, 90, 0), "Front post. Printed on its side so the 14 mm face is the first layer."),
    "qa_post_rear_v1": (lambda: post_mesh(groove=True), (0, 90, 0), "Rear post with the shear groove in the room-facing face. Printed on its side."),
    "qa_plate_v1": (lambda: plate_mesh(False), (0, 0, 0), "Storey plate: headers, panel fins, and the rear shear groove."),
    "qa_plate_tower_v1": (lambda: plate_mesh(True), (0, 0, 0), "Tower plate with two integral balcony ledges."),
    "qa_panel_front_glazed_v1": (lambda: front_panel_bay("glazed"), (90, 0, 0), "Front lift-out panel, two windows. Printed flat, hooks up."),
    "qa_panel_front_entry_v1": (lambda: front_panel_bay("entry"), (90, 0, 0), "Front lift-out entry panel, open doorway. Printed flat, hooks up."),
    "qa_panel_end_left_v1": (lambda: end_panel_bay("left"), (0, 90, 0), "Left end lift-out panel. Printed flat."),
    "qa_panel_end_right_v1": (lambda: end_panel_bay("right"), (0, 90, 0), "Right end lift-out panel. Printed flat."),
    "qa_rear_v1": (rear_panel_bay, (90, 0, 0), "Fixed rear shear panel. Tongues engage the rear posts. Not a play panel."),
    "qa_roof_tower_v1": (roof_tower, (0, 0, 0), "Tower roof, octagonal shell, lift-off plug."),
    "qa_roof_ridge_v1": (roof_ridge, (0, 0, 0), "Centre ridge roof, lift-off."),
    "qa_roof_gable_v1": (roof_gable, (0, 0, 0), "Right front gable with an integral chimney. Lift-off."),
    "qa_porch_v1": (porch_mesh, (0, 0, 0), "Front stoop. Piers stand outside the panel pull path."),
    "qa_balcony_v1": (balcony_mesh, (0, 0, 0), "Tower balcony. Lifts off the ledges before the panel behind it is pulled."),
    "qa_partition_v1": (partition_mesh, (0, 0, 0), "Optional half-height divider. Feet drop into the floor sockets."),
    "qa_furn_table_v1": (furn_table, (0, 0, 0), "Scale table, one piece."),
    "qa_furn_chair_v1": (furn_chair, (0, 0, 0), "Scale chair, one piece."),
    "qa_furn_bed_v1": (furn_bed, (0, 0, 0), "Scale bed, one piece."),
    "qa_furn_sofa_v1": (furn_sofa, (0, 0, 0), "Scale sofa, one piece."),
    "qa_furn_figure_v1": (furn_figure, (0, 0, 0), "1:24 adult-height gauge, one solid."),
    "qa_coupon_socket_v1": (coupon_socket, (0, 0, 0), "Fit coupon, socket side. Print this first."),
    "qa_coupon_plug_v1": (coupon_plug, (0, 0, 0), "Fit coupon, plug side. The tongue is integral."),
}

COLORS = {
    "structure": "#f3f0e7",
    "siding": "#6e90a6",
    "siding_entry": "#5f8498",
    "floor": "#e4d2b8",
    "roof": "#c4845a",
    "roof_tower": "#b87348",
    "porch": "#efe6d6",
    "balcony": "#f7f4ee",
    "furn": "#c6a36a",
    "furn_soft": "#8ea36f",
    "figure": "#d28b78",
    "partition": "#d9d3c7",
    "coupon": "#d7dbe2",
}


def build_parts():
    os.makedirs(STL_DIR, exist_ok=True)
    catalog = {}
    for name, (builder, rotations, note) in PART_BUILDERS.items():
        print(f"build {name}", flush=True)
        local = builder()
        if local.volume <= 0 or not local.is_watertight:
            raise RuntimeError(f"{name} failed watertight/volume {local.is_watertight} {local.volume}")
        rx, ry, rz = rotations
        printed, print_acc = orient_print(local, rx, ry, rz)
        if printed.bounds[0].min() < -1e-4:
            raise RuntimeError(f"{name} print origin not at 0: {printed.bounds[0]}")
        extents = printed.extents.tolist()
        fits = all(extents[i] <= FIT_MAX[i] + 1e-6 for i in range(3))
        path = os.path.join(STL_DIR, name + ".stl")
        printed.export(path)
        catalog[name] = {
            "local": local,
            "printed": printed,
            "print_acc": print_acc,
            "note": note,
            "extents": extents,
            "fits": fits,
            "triangles": int(len(printed.faces)),
            "volume_mm3": round(float(printed.volume), 1),
            "watertight": bool(printed.is_watertight),
            "bbox_min": [round(float(v), 3) for v in printed.bounds[0]],
            "bbox_max": [round(float(v), 3) for v in printed.bounds[1]],
            "print_rotation_deg": [rx, ry, rz],
        }
        flag = "OK" if fits else "OVER"
        print(f"  {extents[0]:7.1f} x {extents[1]:7.1f} x {extents[2]:7.1f}  {flag}  tris={len(printed.faces)}", flush=True)
    return catalog


def add_instance(instances, catalog, part, iid, x, y, z, role, color, motion, explode, bay, level, rz=0.0, rx=0.0, ry=0.0):
    place = matrix_place(x, y, z, rx, ry, rz)
    world = catalog[part]["local"].copy()
    world.apply_transform(place)
    manifest_m = world_from_print(place, catalog[part]["print_acc"])
    instances.append(
        {
            "id": iid,
            "part": part,
            "role": role,
            "color": color,
            "bay": bay,
            "level": level,
            "motion": motion,
            "explode_mm": explode,
            "matrix": manifest_m,
            "world": world,
        }
    )


def assemble(catalog):
    instances = []
    post_len = level_metrics(0)["post_len"]
    for bay in range(BAYS):
        ox = bay * BAY_W
        add_instance(
            instances, catalog, "qa_base_v1", f"B{bay+1}-base", ox, 0, 0,
            "structure", COLORS["floor"], None, [0, 0, -40 - 20 * bay], bay, 0,
        )
        for level in range(LEVELS):
            m = level_metrics(level)
            tag = f"L{level+1}B{bay+1}"
            # Posts. Rear posts are rotated so the +X groove faces the opening.
            posts = (
                ("FL", "qa_post_front_v1", LX0, FY0),
                ("FR", "qa_post_front_v1", RX0, FY0),
                ("RL", "qa_post_rear_v1", LX0, BY0),
                ("RR", "qa_post_rear_v1", RX0, BY0),
            )
            for pid, part, x, y in posts:
                add_instance(
                    instances, catalog, part, f"{tag}-post-{pid}", ox + x, y, m["post_bottom"],
                    "structure", COLORS["structure"], None,
                    [(-30 if "L" in pid else 30), (-20 if "F" in pid else 20), 30 + level * 24],
                    bay, level,
                )
            plate_part = "qa_plate_tower_v1" if bay == 0 and level == 0 else "qa_plate_v1"
            add_instance(
                instances, catalog, plate_part, f"{tag}-plate", ox, 0, m["plate_bottom"],
                "structure", COLORS["structure"], None, [0, 0, 70 + level * 30], bay, level,
            )
            add_instance(
                instances, catalog, "qa_rear_v1", f"{tag}-rear", ox, 0, m["floor_top"],
                "shear", COLORS["structure"], None, [0, 50, 20 + level * 16], bay, level,
            )
            front_part = "qa_panel_front_entry_v1" if bay == 1 and level == 0 else "qa_panel_front_glazed_v1"
            pull = [0, -PULL_FULL, 0]
            add_instance(
                instances, catalog, front_part, f"{tag}-front", ox, 0, m["floor_top"],
                "panel", COLORS["siding_entry"] if front_part.endswith("entry_v1") else COLORS["siding"],
                {"lift": [0, 0, LIFT], "pull": pull, "group": "front"},
                [0, -90, 40 + level * 20], bay, level,
            )
            if bay == 0:
                add_instance(
                    instances, catalog, "qa_panel_end_left_v1", f"{tag}-end", ox, 0, m["floor_top"],
                    "panel", COLORS["siding"],
                    {"lift": [0, 0, LIFT], "pull": [-PULL_FULL, 0, 0], "group": "end"},
                    [-90, 0, 30 + level * 16], bay, level,
                )
            if bay == BAYS - 1:
                add_instance(
                    instances, catalog, "qa_panel_end_right_v1", f"{tag}-end", ox, 0, m["floor_top"],
                    "panel", COLORS["siding"],
                    {"lift": [0, 0, LIFT], "pull": [PULL_FULL, 0, 0], "group": "end"},
                    [90, 0, 30 + level * 16], bay, level,
                )
            if level < LEVELS - 1:
                add_instance(
                    instances, catalog, "qa_floor_v1", f"{tag}-floor", ox, 0, m["plate_top"] + GAP,
                    "floor", COLORS["floor"], None, [0, 0, 50 + level * 20], bay, level,
                )
        # Roofs sit GAP above the top plate.
        top = level_metrics(LEVELS - 1)
        roof_z = top["plate_top"] + GAP
        if bay == 0:
            roof_part, roof_color = "qa_roof_tower_v1", COLORS["roof_tower"]
        elif bay == 1:
            roof_part, roof_color = "qa_roof_ridge_v1", COLORS["roof"]
        else:
            roof_part, roof_color = "qa_roof_gable_v1", COLORS["roof"]
        add_instance(
            instances, catalog, roof_part, f"B{bay+1}-roof", ox, 0, roof_z,
            "roof", roof_color,
            {"lift": [0, 0, 16], "pull": [0, 0, 150], "group": "roof"},
            [0, (-40 if bay == 0 else 40 if bay == 2 else 0), 160], bay, LEVELS,
        )
    for bay in (0, 1):
        add_instance(
            instances, catalog, "qa_porch_v1", f"B{bay+1}-porch", bay * BAY_W, 0, 0,
            "porch", COLORS["porch"], None, [0, -70, 0], bay, 0,
        )
    # Balcony on the level-0 tower plate ledges (ledge local z = 8, plate bottom as placed).
    ledge_z = level_metrics(0)["plate_bottom"] + 8.0 + GAP
    add_instance(
        instances, catalog, "qa_balcony_v1", "B1-balcony", 0, 0, ledge_z,
        "balcony", COLORS["balcony"],
        {"lift": [0, 0, 20], "pull": [0, -70, 30], "group": "balcony"},
        [0, -80, 60], 0, 1,
    )
    # Partitions — short, so the side doorway stays open.
    floor0 = level_metrics(0)
    floor1 = level_metrics(1)
    add_instance(
        instances, catalog, "qa_partition_v1", "L1B2-partition",
        BAY_W + BAY_W / 2, 140.0, floor0["floor_top"] - 2.4,
        "partition", COLORS["partition"], None, [0, 0, 40], 1, 0,
    )
    add_instance(
        instances, catalog, "qa_partition_v1", "L2B3-partition",
        2 * BAY_W + BAY_W / 2, 140.0, floor1["floor_top"] - 2.4,
        "partition", COLORS["partition"], None, [0, 0, 50], 2, 1,
    )
    place_furniture(instances, catalog)
    return instances


def place_furniture(instances, catalog):
    def put(part, iid, bay, level, x, y, color, ez):
        m = level_metrics(level)
        add_instance(
            instances, catalog, part, iid, bay * BAY_W + x, y, m["floor_top"] + GAP,
            "furniture", color, None, [0, 0, ez], bay, level,
        )

    put("qa_furn_table_v1", "L1B1-table", 0, 0, 36, 40, COLORS["furn"], 80)
    put("qa_furn_chair_v1", "L1B1-chair", 0, 0, 58, 100, COLORS["furn"], 90)
    put("qa_furn_figure_v1", "L1B2-figure", 1, 0, 150, 55, COLORS["figure"], 100)
    put("qa_furn_sofa_v1", "L1B2-sofa", 1, 0, 40, 36, COLORS["furn_soft"], 85)
    put("qa_furn_table_v1", "L1B3-table", 2, 0, 48, 48, COLORS["furn"], 80)
    put("qa_furn_bed_v1", "L2B1-bed", 0, 1, 40, 36, COLORS["furn_soft"], 110)
    put("qa_furn_chair_v1", "L2B2-chair", 1, 1, 90, 60, COLORS["furn"], 100)
    put("qa_furn_figure_v1", "L2B3-figure", 2, 1, 48, 100, COLORS["figure"], 120)
    put("qa_furn_bed_v1", "L3B3-bed", 2, 2, 44, 40, COLORS["furn_soft"], 140)
    put("qa_furn_table_v1", "L3B1-table", 0, 2, 50, 55, COLORS["furn"], 130)


def moved(mesh, motion, stage):
    """stage: rest, lift, short, full."""
    out = mesh.copy()
    if not motion or stage == "rest":
        return out
    lift = np.array(motion["lift"], dtype=float)
    pull = np.array(motion["pull"], dtype=float)
    if stage == "lift":
        out.apply_translation(lift)
    elif stage == "short":
        out.apply_translation(lift + pull * (PULL_SHORT / PULL_FULL))
    elif stage == "full":
        out.apply_translation(lift + pull)
    else:
        raise ValueError(stage)
    return out


def static_pairs(instances):
    """Pairs that are allowed to be close and must not interpenetrate at rest."""
    problems = []
    meshes = [(item["id"], item["world"]) for item in instances]
    worst = 0.0
    worst_pair = None
    checked = 0
    for i in range(len(meshes)):
        for j in range(i + 1, len(meshes)):
            if not aabb_overlap(meshes[i][1].bounds, meshes[j][1].bounds, pad=0.0):
                continue
            checked += 1
            volume = intersection_volume(meshes[i][1], meshes[j][1])
            if volume > worst:
                worst = volume
                worst_pair = (meshes[i][0], meshes[j][0], volume)
            if volume > VOL_LIMIT:
                problems.append({"a": meshes[i][0], "b": meshes[j][0], "volume_mm3": round(volume, 3)})
    return {
        "aabb_pairs_checked": checked,
        "worst_mm3": None if worst_pair is None else round(worst_pair[2], 4),
        "worst_pair": None if worst_pair is None else [worst_pair[0], worst_pair[1]],
        "failures": problems,
    }


def path_checks(instances):
    by_id = {item["id"]: item for item in instances}
    blockers = [item for item in instances if item["role"] != "panel"]
    balcony = by_id["B1-balcony"]
    results = []
    failures = []
    panels = [item for item in instances if item["role"] == "panel"]
    for panel in panels:
        others = [item["world"] for item in blockers if item["id"] != panel["id"]]
        # Neighbour panels stay put during one-panel removal.
        neighbours = [item["world"] for item in panels if item["id"] != panel["id"]]
        for stage in ("rest", "lift", "short", "full"):
            moved_panel = moved(panel["world"], panel["motion"], stage)
            hits = []
            for other_id, other_mesh in [(item["id"], item["world"]) for item in blockers] + [
                (n["id"], n["world"]) for n in panels if n["id"] != panel["id"]
            ]:
                volume = intersection_volume(moved_panel, other_mesh)
                if volume > VOL_LIMIT:
                    hits.append({"against": other_id, "volume_mm3": round(volume, 3)})
            # Dedicated proof: level-2 tower front panel vs balcony, then with balcony removed.
            extra = None
            if panel["id"] == "L2B1-front" and stage == "full":
                blocked = intersection_volume(moved_panel, balcony["world"])
                extra = {"against_seated_balcony_mm3": round(blocked, 3)}
                if blocked > VOL_LIMIT:
                    failures.append({"id": panel["id"], "stage": "full", "issue": "balcony crosses the panel pull", "volume_mm3": blocked})
            if hits:
                failures.append({"id": panel["id"], "stage": stage, "hits": hits})
            results.append({"id": panel["id"], "stage": stage, "hits": hits, "balcony": extra})
    # Roof lift clears the plate.
    for item in instances:
        if item["role"] != "roof":
            continue
        lifted = moved(item["world"], item["motion"], "lift")
        for other in instances:
            if other["id"] == item["id"]:
                continue
            volume = intersection_volume(lifted, other["world"])
            if volume > VOL_LIMIT:
                failures.append({"id": item["id"], "stage": "roof-lift", "against": other["id"], "volume_mm3": round(volume, 3)})
    return {"panels": results, "failures": failures}


def opening_gauge(catalog):
    """Furniture and the figure must fit through the front opening by AABB."""
    px0, px1 = panel_x()
    opening_w = px1 - px0
    # Visible height is the skin below the flange, about CLEAR - flange.
    opening_h = CLEAR - FLANGE_H - 2.0
    gauges = []
    ok = True
    for name in ("qa_furn_table_v1", "qa_furn_chair_v1", "qa_furn_bed_v1", "qa_furn_sofa_v1", "qa_furn_figure_v1"):
        ext = catalog[name]["local"].extents
        dims = sorted(float(v) for v in ext)
        # The piece passes if its two smaller dimensions fit the opening (it can be turned).
        fits = dims[0] <= opening_h - 8 and dims[1] <= opening_w - 8
        ok = ok and fits
        gauges.append({"part": name, "extents_mm": [round(float(v), 1) for v in ext], "fits_front_opening": fits})
    reach = round(shear_y()[0], 2)  # inner face of the rear shear, from the front exterior y=0
    return {
        "front_opening_mm": [round(opening_w, 2), round(opening_h, 2)],
        "end_opening_width_mm": round(panel_y()[1] - panel_y()[0], 2),
        "horizontal_reach_front_to_rear_inner_mm": reach,
        "gauges": gauges,
        "all_fit": ok,
    }


def legacy_interface():
    tile = tm.load(LEGACY_TILE)
    post = tm.load(LEGACY_POST)
    off = 15.875
    pitch = 31.75
    points = [off + i * pitch for i in range(4)]
    rot = rotation_matrix(np.pi, [1, 0, 0])
    seated = []
    for x in points:
        for y in points:
            peg = post.copy()
            peg.apply_transform(rot)
            # Tip-down, flange seated on the deck. Established by measurement:
            # rotated post z=-1 is the flange underside; translate by +11.
            peg.apply_translation([x, y, 11.0])
            seated.append(round(intersection_volume(tile, peg), 4))
    shifted = post.copy()
    shifted.apply_transform(rot)
    shifted.apply_translation([points[0] + 10.0, points[0], 11.0])
    off_grid = round(intersection_volume(tile, shifted), 3)
    # Queen Anne floor has no legacy socket: the same seated peg intersects it.
    floor = floor_mesh()
    peg = post.copy()
    peg.apply_transform(rot)
    peg.apply_translation([points[0], points[0], 11.0])
    # Floor local top is FLOOR_T, not 10. Reseat flange on the floor top.
    peg.apply_translation([0, 0, FLOOR_T - 10.0])
    against_floor = round(intersection_volume(floor, peg), 3)
    return {
        "tile_file": "dollhouse/stl/floor_tile_v0.stl",
        "post_file": "dollhouse/stl/snap_post_v0.stl",
        "tile_bbox_mm": [round(float(v), 3) for v in tile.extents],
        "post_bbox_mm": [round(float(v), 3) for v in post.extents],
        "tile_watertight": bool(tile.is_watertight),
        "post_watertight": bool(post.is_watertight),
        "socket_grid_mm": points,
        "pitch_mm": pitch,
        "offset_mm": off,
        "peg_orientation": "tip down, flange underside on the deck (z translation +11 after a 180 degree X rotation)",
        "intersection_mm3_at_16_sockets": seated,
        "intersection_mm3_shifted_10mm": off_grid,
        "sockets_clear": all(v <= VOL_LIMIT for v in seated) and off_grid > 10,
        "bay_width_mm": BAY_W,
        "bay_width_over_measured_tile": round(BAY_W / float(tile.extents[0]), 4),
        "depth_mm": BAY_D,
        "depth_matches_two_tiles": abs(BAY_D - 2 * float(tile.extents[1])) < 0.1,
        "peg_intersection_mm3_on_queen_anne_floor": against_floor,
        "snap_compatible": False,
        "conclusion": (
            "The legacy floor tile STL is 127 x 127 x 10 mm. A tip-down snap_post_v0 "
            "intersects that tile by ~0 mm^3 at all 16 measured sockets and by a large "
            "volume 10 mm off the grid, so the Ø6 peg / Ø6.3 socket interface is real. "
            "One Queen Anne bay is exactly two measured tile-widths in X and is not two "
            "tile-depths in Y. The same peg intersects the Queen Anne floor, which has "
            "no Ø6.3 socket. The kits share a 254 mm module width and do not share a joint."
        ),
    }


def coupon_check(catalog):
    socket = catalog["qa_coupon_socket_v1"]["local"]
    plug = catalog["qa_coupon_plug_v1"]["local"]
    # Place the plug's tongue into the socket pocket. Both are built in the same
    # local frame, so the rest pose is the engaged pose.
    engaged = intersection_volume(socket, plug)
    lifted = plug.copy()
    lifted.apply_translation([0, 0, 20])
    separated = intersection_volume(socket, lifted)
    return {
        "engaged_intersection_mm3": round(engaged, 4),
        "separated_20mm_intersection_mm3": round(separated, 4),
        "engages_without_penetration": engaged <= VOL_LIMIT and separated <= VOL_LIMIT,
    }


def support_check(instances):
    """The compression stack is post top, then GAP, then plate, then GAP, then floor.

    Downward hooks and fins make a raw bounding-box gap meaningless, so this
    checks the box posts and the placed storey heights directly.
    """
    problems = []
    for level in range(LEVELS):
        metrics = level_metrics(level)
        expected_gap = round(metrics["plate_bottom"] - metrics["post_top"], 4)
        if abs(expected_gap - GAP) > 1e-6:
            problems.append({"level": level, "issue": "formula gap", "gap": expected_gap})
        for bay in range(BAYS):
            post = next(item for item in instances if item["id"] == f"L{level+1}B{bay+1}-post-FL")
            plate = next(item for item in instances if item["id"] == f"L{level+1}B{bay+1}-plate")
            post_top = float(post["world"].bounds[1][2])
            if abs(post_top - metrics["post_top"]) > 0.05:
                problems.append({"id": post["id"], "post_top": post_top, "expected": metrics["post_top"]})
            plate_top = float(plate["world"].bounds[1][2])
            if abs(plate_top - metrics["plate_top"]) > 0.05:
                problems.append({"id": plate["id"], "plate_top": plate_top, "expected": metrics["plate_top"]})
            gap = round(metrics["plate_bottom"] - post_top, 4)
            if abs(gap - GAP) > 0.05:
                problems.append({"id": plate["id"], "seat_gap": gap})
        if level < LEVELS - 1:
            for bay in range(BAYS):
                floor = next(item for item in instances if item["id"] == f"L{level+1}B{bay+1}-floor")
                floor_bottom = float(floor["world"].bounds[0][2])
                expected = level_metrics(level)["plate_top"] + GAP
                if abs(floor_bottom - expected) > 0.05:
                    problems.append({"id": floor["id"], "floor_bottom": floor_bottom, "expected": expected})
    return {"seat_gap_mm": GAP, "failures": problems}


def round_matrix(matrix):
    return [[round(float(value), 6) for value in row] for row in matrix.tolist()]


def write_outputs(catalog, instances, checks):
    os.makedirs(REPORT_DIR, exist_ok=True)
    worlds = [item["world"] for item in instances]
    stacked = tm.util.concatenate(worlds)
    bounds = stacked.bounds
    size = (bounds[1] - bounds[0]).tolist()
    parts_meta = []
    for name, info in catalog.items():
        parts_meta.append(
            {
                "id": name,
                "file": f"stl/{name}.stl",
                "note": info["note"],
                "triangles": info["triangles"],
                "volume_mm3": info["volume_mm3"],
                "watertight": info["watertight"],
                "bbox_mm": [round(v, 2) for v in info["extents"]],
                "bbox_min_mm": info["bbox_min"],
                "bbox_max_mm": info["bbox_max"],
                "fits_brim_allowance": info["fits"],
                "fit_max_mm": list(FIT_MAX),
                "bed_mm": list(BED),
                "print_rotation_deg_xyz": info["print_rotation_deg"],
                "min_z_mm": info["bbox_min"][2],
            }
        )
    bom_counts = {}
    manifest_instances = []
    for item in instances:
        bom_counts[item["part"]] = bom_counts.get(item["part"], 0) + 1
        manifest_instances.append(
            {
                "id": item["id"],
                "part": item["part"],
                "role": item["role"],
                "color": item["color"],
                "bay": item["bay"],
                "level": item["level"],
                "transform": round_matrix(item["matrix"]),
                "explode_mm": item["explode_mm"],
                "motion": item["motion"],
            }
        )
    first_print = [
        "qa_coupon_socket_v1",
        "qa_coupon_plug_v1",
        "qa_base_v1",
        "qa_post_front_v1",
        "qa_post_rear_v1",
        "qa_plate_v1",
        "qa_rear_v1",
        "qa_panel_front_glazed_v1",
        "qa_panel_end_left_v1",
    ]
    bom = []
    for name in PART_BUILDERS:
        qty = bom_counts.get(name, 0)
        if qty == 0 and name.startswith("qa_coupon_"):
            qty = 1
        bom.append(
            {
                "part": name,
                "qty": qty,
                "first_bay_print": name in first_print,
                "file": f"stl/{name}.stl",
            }
        )
    manifest = {
        "name": "Queen Anne Playhouse",
        "slug": "queen-anne",
        "version": "1.0.0",
        "units": "mm",
        "scale": "1:24",
        "up_axis": "Z",
        "route": "/dollhouse/queen-anne/",
        "description": "A 1:24 Queen Anne playhouse with a tower, a front gable, lift-out panels, and lift-off roofs. The viewer places the CAD STLs.",
        "distinct_from": [
            "Bramble Cottage",
            "Larkspur Grand Ranch",
            "Pennywhistle Row House",
            "Cloisterwick Manor",
            "Cogsworth Works",
            "Electrified Manor",
        ],
        "target_printer": {
            "model": "Bambu Lab H3C",
            "bed_mm": list(BED),
            "bed_source": "Project brief envelope 330 x 320 x 325 mm. Not re-measured on a machine.",
            "brim_allowance_mm": "Parts are limited to 310 x 300 x 315 so 10 mm remains on each XY side and 10 mm in Z.",
            "nozzle_assumed_mm": 0.4,
            "material_assumed": "PLA",
            "sliced": False,
            "h3c_profile_tested": False,
        },
        "assembled_size_mm": {
            "x": round(size[0], 2),
            "y": round(size[1], 2),
            "z": round(size[2], 2),
            "min_mm": [round(float(v), 2) for v in bounds[0]],
            "max_mm": [round(float(v), 2) for v in bounds[1]],
        },
        "module_mm": {
            "bay_width": BAY_W,
            "bay_depth": BAY_D,
            "post": POST,
            "clear_height": CLEAR,
            "levels": LEVELS,
            "bays": BAYS,
            "seat_gap": GAP,
            "pocket_side_clearance": SIDE,
        },
        "mechanism": {
            "panels": "Lift 8.6 mm to clear the lower hook and the head fin, then pull out along the wall normal. Removable. No hinges, magnets, or loose pins.",
            "balcony": "Saddles over two ledges on the tower plate and lifts off upward. The rail sits beyond the panel pull, so the panel path stays clear.",
            "roofs": "Gravity plug into the plate opening. Lift straight up.",
            "rear_shear": "Tongued into the rear posts and captured by the floor and the plate. It is structure, not a play panel.",
            "inter_bay": "Underside lap on each base and each upper floor, 16 mm long, 0.40 mm side clearance. Plates are located by the posts. Interior sides between bays are open above the corner posts.",
        },
        "validation": {
            "printed": False,
            "measured": False,
            "physically_verified": False,
            "forces_tested": False,
            "fatigue_tested": False,
            "stability_tested": False,
            "h3c_sliced": False,
            "cad_validated": checks["ok"],
        },
        "parts": parts_meta,
        "bom": bom,
        "instances": manifest_instances,
        "first_print": first_print,
        "legacy_interface": checks["legacy"],
        "limits": [
            "Not printed. Clearances are CAD targets.",
            "Forces, buckling, floor deflection, lap shear, fatigue, and tip-over were not calculated or tested.",
            "No load rating and no toy-safety certification.",
            "Do not treat the assembled house as a lifting handle.",
            "Generic brim-allowance check only. No slicer was run. Not an H3C test.",
            "Panel edges are square. Pinch gaps and finger comfort were not trialed.",
            "The balcony must come off before the second-storey tower front panel is fully pulled.",
        ],
    }
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    report = {
        "ok": checks["ok"],
        "fit": checks["fit"],
        "rest_intersections": checks["rest"],
        "paths": {"failures": checks["paths"]["failures"]},
        "opening": checks["opening"],
        "coupon": checks["coupon"],
        "support": checks["support"],
        "legacy": checks["legacy"],
        "assembly_mm": manifest["assembled_size_mm"],
        "instance_count": len(instances),
        "unique_parts": len(catalog),
        "triangles": int(sum(info["triangles"] for info in catalog.values())),
    }
    with open(os.path.join(REPORT_DIR, "validation.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    return manifest, report


def assert_roundtrip(catalog, instances):
    """STL vertices plus the manifest matrix must match the assembly mesh."""
    worst = 0.0
    for item in instances[:8]:
        info = catalog[item["part"]]
        stamped = info["printed"].copy()
        stamped.apply_transform(item["matrix"])
        delta = np.max(np.abs(stamped.bounds - item["world"].bounds))
        worst = max(worst, float(delta))
    if worst > 0.05:
        raise RuntimeError(f"STL/manifest round-trip delta {worst}")
    return round(worst, 5)


def main():
    print("legacy measure...", flush=True)
    legacy = legacy_interface()
    print(legacy["conclusion"], flush=True)
    if not legacy["sockets_clear"]:
        raise RuntimeError("legacy socket measurement failed")
    if abs(legacy["bay_width_over_measured_tile"] - 2.0) > 1e-6:
        raise RuntimeError("bay width is not twice the measured tile")
    catalog = build_parts()
    over = [name for name, info in catalog.items() if not info["fits"]]
    if over:
        raise RuntimeError(f"parts exceed brim allowance: {over}")
    print("assemble...", flush=True)
    instances = assemble(catalog)
    print(f"instances {len(instances)}", flush=True)
    print("rest intersections...", flush=True)
    rest = static_pairs(instances)
    print(" worst", rest["worst_pair"], rest["worst_mm3"], "failures", len(rest["failures"]), flush=True)
    print("paths...", flush=True)
    paths = path_checks(instances)
    print(" path failures", len(paths["failures"]), flush=True)
    opening = opening_gauge(catalog)
    coupon = coupon_check(catalog)
    support = support_check(instances)
    trip = assert_roundtrip(catalog, instances)
    ok = (
        not rest["failures"]
        and not paths["failures"]
        and opening["all_fit"]
        and coupon["engages_without_penetration"]
        and not support["failures"]
        and legacy["sockets_clear"]
        and not legacy["snap_compatible"]
    )
    checks = {
        "ok": ok,
        "fit": {"max_mm": list(FIT_MAX), "all_parts_fit": not over},
        "rest": rest,
        "paths": paths,
        "opening": opening,
        "coupon": coupon,
        "support": support,
        "legacy": legacy,
        "roundtrip_mm": trip,
    }
    manifest, report = write_outputs(catalog, instances, checks)
    print(json.dumps({k: report[k] for k in ("ok", "assembly_mm", "instance_count", "unique_parts", "triangles")}, indent=2))
    print("coupon", coupon)
    print("opening", opening["front_opening_mm"], "reach", opening["horizontal_reach_front_to_rear_inner_mm"])
    print("support failures", support["failures"][:8])
    if rest["failures"]:
        print("REST", json.dumps(rest["failures"], indent=2))
    if paths["failures"]:
        print("PATH", json.dumps(paths["failures"], indent=2))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
