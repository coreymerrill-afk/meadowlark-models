"""Golden detail bay. Units mm. Z up. Not the whole house.

One parlor window, one pierced verge board, one curved bracket,
one shingle cartridge, and one furnished room. Parts are separate
closed solids. They are not fused into the Queen Anne shell.

A minimum web is a design number. It is untested until a coupon
is printed on the actual machine.
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
OUT = os.path.abspath(os.path.join(HERE, "..", "detail-proof"))
MODELS = os.path.join(OUT, "models")
EVID = os.path.join(OUT, "evidence")

BED = (330.0, 320.0, 325.0)
# Design webs. Not a measured minimum and not a durability claim.
WEB_MM = 1.6
PLATE_MM = 1.7
HOLE_D = 3.6


def box_at(a, b, c, d, e, f):
    if min(d - a, e - b, f - c) <= 0.05:
        return None
    mesh = box((d - a, e - b, f - c))
    mesh.apply_translation(((a + d) / 2, (b + e) / 2, (c + f) / 2))
    return mesh


def move(mesh, x, y, z):
    out = mesh.copy()
    out.apply_translation((x, y, z))
    return out


def union(meshes):
    parts = [m for m in meshes if m is not None]
    acc = parts[0]
    for i in range(1, len(parts), 16):
        acc = tm.boolean.union([acc, *parts[i:i + 16]], engine="manifold")
    return acc


def difference(base, cuts):
    cuts = [c for c in cuts if c is not None]
    acc = base
    for i in range(0, len(cuts), 10):
        acc = tm.boolean.difference([acc, *cuts[i:i + 10]], engine="manifold")
    return acc


def cleanup(mesh, name):
    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    if mesh.volume < 0:
        mesh.invert()
    good = [p for p in mesh.split(only_watertight=False) if abs(p.volume) > 1.0]
    if (not mesh.is_watertight) or len(good) != 1:
        raise RuntimeError(f"{name} bodies={len(good)} watertight={mesh.is_watertight} vol={mesh.volume:.1f}")
    return mesh


def extrude(poly, depth):
    mesh = tm.creation.extrude_polygon(poly, depth)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def revolve(profile, sections=16):
    mesh = tm.creation.revolve(np.asarray(profile, float), sections=sections)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def window_wall():
    """One solid: wall, layered casing, sill, and pediment. The sash opening is a real hole."""
    # Clear aperture 50 x 76 mm. At 1:24 that is 47.2 x 71.8 inches.
    x0, x1, z0, z1 = 30.0, 80.0, 36.0, 112.0
    wall = box_at(0, 0, 0, 110, 4.4, 148)
    casing = [
        box_at(x0 - 7, -3.4, z0 - 2, x0, 0.8, z1 + 4),
        box_at(x1, -3.4, z0 - 2, x1 + 7, 0.8, z1 + 4),
        box_at(x0 - 7, -3.6, z1, x1 + 7, 0.8, z1 + 6.5),
        box_at(x0 - 9, -4.6, z1 + 5.2, x1 + 9, 0.6, z1 + 8.4),
        # sill and drip
        box_at(x0 - 12, -9.5, z0 - 7.5, x1 + 12, 1.0, z0 - 3.2),
        box_at(x0 - 8, -6.2, z0 - 3.6, x1 + 8, 0.8, z0 + 1.2),
        # backband
        box_at(x0 - 10, -2.2, z0 - 5, x0 - 6.2, 0.5, z1 + 7),
        box_at(x1 + 6.2, -2.2, z0 - 5, x1 + 10, 0.5, z1 + 7),
    ]
    # Cyma pediment. The profile is the crown, not a flat triangle.
    ped = []
    peak_z = z1 + 28
    for i, (y_out, thick) in enumerate(((-1.2, 2.4), (-3.2, 1.8), (-5.0, 1.4))):
        shrink = i * 3.2
        ped.append(tm.convex.convex_hull(np.array([
            (x0 - 4 + shrink, 0.4, z1 + 7),
            (x1 + 4 - shrink, 0.4, z1 + 7),
            ((x0 + x1) / 2, 0.4, peak_z - i * 2.5),
            (x0 - 4 + shrink, y_out, z1 + 7),
            (x1 + 4 - shrink, y_out, z1 + 7),
            ((x0 + x1) / 2, y_out, peak_z - i * 2.5),
        ], float)))
    opening = box_at(x0, -12, z0, x1, 12, z1)
    # Room-side stop, so the sash has a shoulder. It must not close the hole.
    stop = [
        box_at(x0 - 1.2, 3.2, z0 - 1.2, x0 + 1.6, 5.2, z1 + 1.2),
        box_at(x1 - 1.6, 3.2, z0 - 1.2, x1 + 1.2, 5.2, z1 + 1.2),
        box_at(x0, 3.2, z1 - 1.4, x1, 5.2, z1 + 1.6),
        box_at(x0, 3.2, z0 - 1.6, x1, 5.2, z0 + 1.4),
    ]
    mesh = cleanup(difference(union([wall, *casing, *ped, *stop]), [opening]), "window wall")
    return mesh, {"clear_aperture_mm": [50.0, 76.0], "full_size_in": [round(50 * 24 / 25.4, 1), round(76 * 24 / 25.4, 1)]}


def sash():
    """Double-hung sash. Six clear openings. Sits in the hole with clearance, not in the wall."""
    # Wall opening is x 30..80, z 36..112. Sash is 0.6 mm inside that, in y 0.7..3.5.
    x0, x1, z0, z1 = 30.6, 79.4, 36.6, 111.4
    y0, y1 = 0.7, 3.5
    rail = 2.0
    bar = 1.5
    mid_z = (z0 + z1) / 2
    parts = [
        box_at(x0, y0, z0, x0 + rail, y1, z1),
        box_at(x1 - rail, y0, z0, x1, y1, z1),
        box_at(x0, y0, z0, x1, y1, z0 + rail),
        box_at(x0, y0, z1 - rail, x1, y1, z1),
        box_at(x0, y0, mid_z - bar / 2, x1, y1, mid_z + bar / 2),
    ]
    for frac in (1 / 3, 2 / 3):
        x = x0 + (x1 - x0) * frac
        parts.append(box_at(x - bar / 2, y0, z0, x + bar / 2, y1, z1))
    return cleanup(union(parts), "sash"), {
        "perimeter_clearance_mm": 0.6,
        "rail_mm": rail,
        "muntin_mm": bar,
        "panes": 6,
        "glass": "none; the panes are openings",
    }


def lace():
    """Verge board. The piercings go through. Nothing fills them."""
    length, height = 108.0, 26.0
    plate = sbox(0, 0, length, height)
    bites = [Point(float(x), 0).buffer(4.6, resolution=8) for x in np.arange(8, length - 4, 12)]
    holes = []
    for row, y, step, rad in ((0, 15.5, 9.0, HOLE_D / 2), (1, 8.2, 9.0, 1.45)):
        shift = 4.5 if row else 0.0
        for x in np.arange(10 + shift, length - 8, step):
            holes.append(Point(float(x), y).buffer(rad, resolution=10))
    shape = plate.difference(unary_union(bites + holes))
    if shape.geom_type != "Polygon":
        raise RuntimeError(f"lace split into {shape.geom_type}")
    # Designed web: centre spacing minus diameters, from the drawing, not a measurement of a print.
    web = round(9.0 - HOLE_D, 2)
    mesh = cleanup(extrude(shape, PLATE_MM), "lace")
    return mesh, {
        "plate_thickness_mm": PLATE_MM,
        "hole_diameter_mm": HOLE_D,
        "designed_web_mm": web,
        "web_status": "UNTESTED_UNTIL_PHYSICAL_COUPON",
        "interiors": len(shape.interiors),
        "piercings": "through; no backing",
    }


def bracket():
    """Cyma bracket. The opening follows the curve and goes through the plate."""
    pts = [(0, 0), (0, 28), (4.2, 28), (4.2, 22)]
    for i in range(10):
        t = i / 9
        pts.append((4.2 + 18 * (t ** 1.25), 21.5 - 17.5 * math.sin(t * math.pi / 2)))
    pts += [(22.5, 2.2), (22.5, 0)]
    plate = Polygon(pts)
    # Kept under the cyma and off the outer edge. The rim is drawn, not tested.
    opening = Polygon([
        (7.2, 3.0), (7.2, 10.2), (10.4, 7.6), (14.2, 4.8), (17.2, 3.2), (14.6, 3.0),
    ])
    shape = plate.difference(opening)
    if shape.geom_type != "Polygon" or len(shape.interiors) != 1:
        raise RuntimeError(f"bracket split {shape.geom_type}")
    web = round(float(plate.exterior.distance(opening)), 2)
    raw = extrude(shape, 4.2)
    raw.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    raw.apply_translation(-raw.bounds[0])
    return cleanup(raw, "bracket"), {
        "thickness_mm": 4.2,
        "opening": "through the spandrel, one connected plate",
        "designed_rim_mm": web,
        "web_status": "UNTESTED_UNTIL_PHYSICAL_COUPON",
    }


def shingle_cartridge():
    def one():
        body = sbox(-2.3, 0, 2.3, 2.6)
        nose = Point(0, 2.5).buffer(2.15, resolution=5)
        shape = body.union(nose).intersection(sbox(-2.5, 0, 2.5, 4.6))
        return cleanup(extrude(shape, 0.42), "tile")

    tile = one()
    length, rise = 64.0, 18.0
    slope = np.array([0.0, length, rise], float)
    slope /= np.linalg.norm(slope)
    normal = np.cross(np.array([1.0, 0.0, 0.0]), slope)
    normal /= np.linalg.norm(normal)
    slab = tm.convex.convex_hull(np.array([
        (0, 0, 0), (52, 0, 0), (52, length, rise), (0, length, rise),
        (0, 0, 0) - normal * 1.5, (52, 0, 0) - normal * 1.5,
        (52, length, rise) - normal * 1.5, (0, length, rise) - normal * 1.5,
    ], float))
    tiles = []
    dist = float(np.linalg.norm([0, length, rise]))
    course = 0
    s = 1.2
    while s < dist - 4.5:
        x = 3.0 + (2.5 if course % 2 else 0.0)
        while x < 47:
            piece = tile.copy()
            M = np.eye(4)
            M[0:3, 0] = [1.0, 0.0, 0.0]
            M[0:3, 1] = slope
            M[0:3, 2] = normal
            M[0:3, 3] = np.array([x, 0.0, 0.0]) + slope * s - normal * 0.18
            piece.apply_transform(M)
            tiles.append(piece)
            x += 5.1
        s += 3.3
        course += 1
    mesh = cleanup(union([slab, *tiles]), "shingles")
    return mesh, {
        "courses": course,
        "tile_thickness_mm": 0.42,
        "designed_relief_mm": 0.24,
        "relief_status": "MESH_DIMENSION_NOT_A_PRINT",
    }


def floor_and_skirt():
    """Boards are grooves in the slab. Baseboards stop for the door."""
    slab = box_at(0, 0, 0, 168, 128, 2.6)
    grooves = []
    x = 8.0
    while x < 164:
        grooves.append(box_at(x, 1.5, 2.15, x + 0.55, 126.5, 2.75))
        x += 8.0
    boards = difference(slab, grooves)
    skirts = [
        box_at(166, 0, 2.6, 168, 128, 9.2),
        box_at(2, 126, 2.6, 166, 128, 9.2),
        box_at(2, 0, 2.6, 96, 2.0, 9.2),
        box_at(136, 0, 2.6, 166, 2.0, 9.2),
    ]
    mesh = cleanup(union([boards, *skirts]), "floor")
    return mesh, {"door_gap_mm": [96, 136], "groove_depth_mm": 0.45, "board_pitch_mm": 8.0}


def door_frame():
    """Passage in the left wall. The opening is empty."""
    wall = box_at(0, 8, 2.6, 3.2, 52, 78)
    wall2 = box_at(0, 92, 2.6, 3.2, 120, 78)
    head = box_at(0, 8, 74, 3.2, 120, 82)
    return cleanup(union([wall, wall2, head]), "door frame"), {"clear_opening_mm": [40, 71.4]}


def sofa():
    """Rolled arms, a bowed back, and two seat cushions. Footprint stays inside the bay."""
    parts = [box_at(4, 2, 0, 62, 27, 5.0)]
    parts.append(tm.convex.convex_hull(np.array([
        (9, 4, 4.6), (57, 4, 4.6), (57, 20, 4.6), (9, 20, 4.6),
        (10, 5, 12.2), (31, 5, 13.4), (56, 5, 12.2),
        (56, 19, 10.6), (10, 19, 10.6),
    ], float)))
    parts.append(tm.convex.convex_hull(np.array([
        (10, 5.5, 12.0), (30, 5.5, 12.0), (30, 19, 12.0), (10, 19, 12.0),
        (11, 6.5, 15.6), (20, 7, 16.4), (29, 6.5, 15.6), (29, 18, 14.2), (11, 18, 14.2),
    ], float)))
    parts.append(tm.convex.convex_hull(np.array([
        (34, 5.5, 12.0), (56, 5.5, 12.0), (56, 19, 12.0), (34, 19, 12.0),
        (35, 6.5, 15.6), (45, 7, 16.4), (55, 6.5, 15.6), (55, 18, 14.2), (35, 18, 14.2),
    ], float)))
    for t in np.linspace(0, 1, 8):
        x = 8 + t * 50
        bow = math.sin(t * math.pi) * 2.4
        parts.append(box_at(x - 3.6, 19.2 + bow, 8, x + 3.6, 24.2 + bow, 29))
    crest = cylinder(radius=2.1, height=52, sections=14)
    crest.apply_transform(rotation_matrix(math.pi / 2, [0, 1, 0]))
    crest.apply_translation((34, 22.6, 29.2))
    parts.append(crest)
    for x in (0.0, 58.0):
        parts.append(box_at(x, 1, 4.5, x + 8, 26, 16))
        roll = cylinder(radius=4.0, height=12, sections=16)
        roll.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
        roll.apply_translation((x + 4, 7, 16))
        parts.append(roll)
    return cleanup(union(parts), "sofa"), {"full_size_note": "about a 6 foot sofa at 1:24"}


def chair():
    legs = []
    for x, y in ((2.4, 2.4), (16.4, 2.4), (2.4, 15.2), (16.4, 15.2)):
        legs.append(move(revolve([
            [0, 0], [1.55, 0], [1.05, 1.4], [1.4, 2.6], [0.8, 7.4], [1.25, 9.2], [0, 9.2],
        ], 10), x, y, 0))
    seat = tm.convex.convex_hull(np.array([
        (1.2, 1.2, 9.0), (18.6, 1.2, 9.0), (18.6, 15.5, 9.0), (1.2, 15.5, 9.0),
        (2.0, 2.0, 12.4), (18.0, 2.0, 12.4), (17.2, 14.6, 11.6), (2.6, 14.6, 11.6),
        (10, 8, 13.2),
    ], float))
    crest = tm.convex.convex_hull(np.array([
        (0.4, 14.2, 24), (19.6, 14.2, 24), (18.2, 18.6, 24), (1.8, 18.6, 24),
        (1.6, 14.6, 29.5), (18.4, 14.6, 29.5), (16.2, 17.4, 31.2), (3.8, 17.4, 31.2),
        (10, 16.2, 32.4),
    ], float))
    mesh = union([
        seat,
        box_at(0.6, 14.2, 11, 3.2, 17.4, 26),
        box_at(16.8, 14.2, 11, 19.4, 17.4, 26),
        box_at(8.6, 14.6, 12, 11.4, 16.8, 25),
        crest,
        *legs,
    ])
    return cleanup(mesh, "chair"), {"back": "crest rail and a centre splat"}


def table():
    legs = []
    for x, y in ((3, 3), (29, 3), (3, 17), (29, 17)):
        legs.append(move(revolve([
            [0, 0], [1.5, 0], [1.15, 3], [1.15, 16], [1.6, 18.2], [0, 18.2],
        ], 10), x, y, 0))
    top = box_at(0, 0, 18.0, 34, 22, 20.2)
    return cleanup(union([top, *legs]), "table"), {"top_height_mm": 20.2, "full_size_in": round(20.2 * 24 / 25.4, 1)}


def bookcase():
    parts = [
        box_at(0, 0, 0, 2.2, 12, 58),
        box_at(24, 0, 0, 26.2, 12, 58),
        box_at(0, 10, 0, 26.2, 12, 58),
        box_at(0, 0, 0, 26.2, 12, 2.2),
        box_at(0, 0, 55.5, 26.2, 12, 58),
    ]
    z = 16.0
    shelves = []
    while z < 52:
        parts.append(box_at(1.2, 1.0, z, 25, 11.2, z + 1.6))
        shelves.append(z + 1.6)
        z += 14
    parts.append(box_at(-0.8, -0.6, 55.2, 27.0, 12.6, 58.4))
    parts.append(tm.convex.convex_hull(np.array([
        (1, 0, 58.2), (25.2, 0, 58.2), (25.2, 12, 58.2), (1, 12, 58.2),
        (13.1, 2, 66.5), (13.1, 10, 66.5),
    ], float)))
    # Books sit on the shelves and enter them by 0.35 mm so they are one print.
    for top, widths in ((shelves[0], (3.2, 2.4, 3.6, 2.2)), (shelves[1], (2.6, 4.0, 2.8)), (shelves[2], (3.4, 2.2, 2.8, 3.0))):
        x = 3.0
        for width in widths:
            parts.append(box_at(x, 2.2, top - 0.35, x + width, 9.4, top + 8.5))
            x += width + 0.7
    return cleanup(union(parts), "bookcase"), {"shelves": 3, "front": "open", "books": "part of this solid"}


def stair_bit():
    """Five treads and a rail. A sample of the flight, not the house stair."""
    parts = []
    for i in range(4):
        parts.append(box_at(0, i * 9.0, i * 7.2, 32, i * 9.0 + 10.2, i * 7.2 + 7.6))
        parts.append(move(revolve([
            [0, 0], [1.15, 0], [1.35, 1], [0.85, 4], [1.25, 12], [0.7, 14], [0, 14],
        ], 8), 29.2, i * 9.0 + 5, i * 7.2 + 7.4))
    parts.append(tm.convex.convex_hull(np.array([
        (27.4, 2, 20), (31.2, 2, 20), (27.4, 32, 42), (31.2, 32, 42),
        (27.4, 2, 22.2), (31.2, 2, 22.2), (27.4, 32, 44.2), (31.2, 32, 44.2),
    ], float)))
    parts.append(move(revolve([[0, 0], [2.4, 0], [2.4, 46], [0, 46]], 10), 4, 2, 0))
    return cleanup(union(parts), "stair sample"), {
        "rises": 4,
        "rise_mm": 7.2,
        "rise_in_at_1_24": round(7.2 * 24 / 25.4, 2),
        "tread_mm": 9.0,
    }


def light():
    """Puck. Cavity opens downward. A 2 mm feed leaves the top. Both are voids."""
    body = cylinder(radius=7.2, height=8.0, sections=24)
    body.apply_translation((0, 0, 4.0))
    cavity = cylinder(radius=3.0, height=3.6, sections=20)
    cavity.apply_translation((0, 0, 1.5))
    feed = cylinder(radius=1.0, height=6.4, sections=12)
    feed.apply_translation((0, 0, 5.2))
    mesh = cleanup(difference(body, [cavity, feed]), "light")
    return mesh, {
        "cavity_diameter_mm": 6.0,
        "cavity_depth_mm": 3.0,
        "cavity_status": "PROVISIONAL_NOT_FIT_VALIDATED",
        "feedthrough_diameter_mm": 2.0,
        "feed_opens": "top of the puck",
        "wired_to_rear_closure": False,
    }


def analyze(mesh):
    ext = mesh.bounds[1] - mesh.bounds[0]
    fits = bool(np.all(np.sort(ext) <= np.sort(BED)))
    # Oriented-in-place fit, not every rotation. Record the given orientation.
    fits_given = bool(ext[0] <= BED[0] and ext[1] <= BED[1] and ext[2] <= BED[2])
    return {
        "watertight": bool(mesh.is_watertight),
        "bodies": len([p for p in mesh.split(only_watertight=False) if abs(p.volume) > 1]),
        "volume_mm3": round(float(mesh.volume), 1),
        "bounds_mm": [round(float(v), 2) for v in ext],
        "fits_330x320x325_in_this_orientation": fits_given,
        "fits_if_rotated_to_smallest_axes": fits,
    }


def section_png(mesh, origin, normal, path, title):
    from PIL import Image, ImageDraw
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    if sec is None:
        raise RuntimeError(f"no section {path}")
    planar, _ = sec.to_2D()
    polys = planar.polygons_full
    if not polys:
        raise RuntimeError(f"empty section {path}")
    all_pts = np.vstack([np.array(p.exterior.coords) for p in polys])
    minx, miny = all_pts.min(axis=0)
    maxx, maxy = all_pts.max(axis=0)
    span = max(maxx - minx, maxy - miny, 1)
    scale = 640 / span
    pad = 30

    def xy(pt):
        return (pad + (pt[0] - minx) * scale, pad + (maxy - pt[1]) * scale)

    w = int((maxx - minx) * scale + 2 * pad)
    h = int((maxy - miny) * scale + 2 * pad)
    img = Image.new("RGB", (max(w, 80), max(h, 80)), (244, 241, 234))
    draw = ImageDraw.Draw(img)
    for poly in polys:
        draw.polygon([xy(p) for p in poly.exterior.coords], fill=(47, 74, 63), outline=(20, 24, 28))
        for ring in poly.interiors:
            draw.polygon([xy(p) for p in ring.coords], fill=(244, 241, 234), outline=(20, 24, 28))
    img.save(path)
    return {"polygons": len(polys), "holes": sum(len(p.interiors) for p in polys), "file": os.path.basename(path), "plane": title}


def beam():
    """Joist the light sits under. One end meets the window wall. The post meets the floor."""
    return cleanup(union([
        box_at(24, 40, 146, 56, 118, 150),
        box_at(28, 114, 2.6, 36, 118, 150),
    ]), "beam"), {"light_seat": "underside at z 146, coplanar with the puck top. The post stands left of the casing."}


def build():
    os.makedirs(MODELS, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    wall, wall_meta = window_wall()
    sash_m, sash_meta = sash()
    lace_m, lace_meta = lace()
    bracket_m, bracket_meta = bracket()
    shingles, shingle_meta = shingle_cartridge()
    floor_m, floor_meta = floor_and_skirt()
    frame_m, frame_meta = door_frame()
    sofa_m, sofa_meta = sofa()
    chair_m, chair_meta = chair()
    table_m, table_meta = table()
    case_m, case_meta = bookcase()
    stair_m, stair_meta = stair_bit()
    light_m, light_meta = light()
    beam_m, beam_meta = beam()

    # Assembly. Room at the origin. Detail samples on a bench to the right,
    # so each motif can be inspected without being buried in the room.
    placed = [
        ("floor", floor_m, (0, 0, 0), floor_meta, "Floor boards and baseboards. Door gap is x 96 to 136."),
        ("door-frame", frame_m, (0, 0, 0), frame_meta, "Left-hand passage. The opening is empty."),
        ("window-wall", wall, (24, 118, 2.6), wall_meta, "Back wall of the bay. Sits on the floor. Coplanar, no shared volume."),
        ("sash", sash_m, (24, 118, 2.6), sash_meta, "In the opening, 0.6 mm clear of the reveal."),
        ("sofa", sofa_m, (8, 28, 2.6), sofa_meta, "Left side. Stops before the front door gap."),
        ("chair", chair_m, (108, 24, 2.6), chair_meta, "Right of the path, in front of the table."),
        ("table", table_m, (104, 52, 2.6), table_meta, "Centre-right."),
        ("bookcase", case_m, (8, 100, 2.6), case_meta, "Back-left. Open shelves."),
        ("stair-sample", stair_m, (132, 78, 2.6), stair_meta, "Back-right. Four rises. Clear of the window wall and the table."),
        ("light", light_m, (46, 78, 138), light_meta, "Top is coplanar with the joist underside. Cavity faces down."),
        ("beam", beam_m, (0, 0, 0), beam_meta, "Joist meets the window wall at y 118. Post meets the floor at z 2.6."),
        ("lace", lace_m, (196, 10, 2.6), lace_meta, "Bench. Through-pierced verge board."),
        ("bracket", bracket_m, (196, 50, 2.6), bracket_meta, "Bench. Cyma bracket, hole through the spandrel."),
        ("shingle-sample", shingles, (196, 80, 2.6), shingle_meta, "Bench. Shallow courses on one cartridge."),
    ]

    catalog = {}
    instances = []
    scene = tm.Scene()
    for iid, mesh, pos, meta, note in placed:
        world = move(mesh, *pos)
        info = analyze(world)
        info.update(meta)
        info["note"] = note
        info["placement_mm"] = list(pos)
        catalog[iid] = info
        world.export(os.path.join(MODELS, f"dp_{iid}.stl"))
        T = np.eye(4)
        T[0:3, 3] = pos
        # The exported STL is already in world position, so the GLB uses that mesh
        # and the JSON records the placement that produced it.
        scene.add_geometry(world, node_name=iid, geom_name=iid)
        instances.append({"id": iid, "file": f"models/dp_{iid}.stl", "placement_mm": list(pos), "note": note})
        print(iid, info["bounds_mm"], "bodies", info["bodies"], "watertight", info["watertight"], flush=True)

    # Sections. Holes must show up as interiors, not as surface colour.
    sections = [
        section_png(wall, [0, 2.2, 70], [0, 1, 0], os.path.join(EVID, "window-plan.png"),
                    "Horizontal cut through the window. The white region is the opening."),
        section_png(lace_m, [40, 12, PLATE_MM / 2], [0, 0, 1], os.path.join(EVID, "lace-plan.png"),
                    "Cut through the verge board. White disks are through-holes."),
        section_png(light_m, [0, 0, 4], [1, 0, 0], os.path.join(EVID, "light-section.png"),
                    "Vertical cut through the puck. Cavity below, feed through the top."),
        section_png(bracket_m, [10, 2.1, 12], [0, 1, 0], os.path.join(EVID, "bracket-section.png"),
                    "Cut through the bracket. The hole is open."),
    ]

    # Contacts: no two parts may share volume. Coplanar is allowed.
    clashes = []
    worlds = [(iid, move(mesh, *pos)) for iid, mesh, pos, meta, note in placed]
    for i in range(len(worlds)):
        for j in range(i + 1, len(worlds)):
            a, b = worlds[i][1], worlds[j][1]
            if np.any(a.bounds[1] < b.bounds[0]) or np.any(b.bounds[1] < a.bounds[0]):
                continue
            hit = tm.boolean.intersection([a, b], engine="manifold")
            vol = 0.0 if hit is None or hit.is_empty else max(0.0, float(hit.volume))
            if vol > 0.5:
                clashes.append({"pair": [worlds[i][0], worlds[j][0]], "mm3": round(vol, 2)})
                print("clash", worlds[i][0], worlds[j][0], round(vol, 2), flush=True)

    scene.export(os.path.join(OUT, "assembly.glb"))
    report = {
        "name": "Queen Anne detail proof",
        "what_this_is": "One window, one pierced verge, one bracket, one shingle cartridge, one furnished bay. Not the whole house.",
        "units": "mm",
        "scale": "1:24",
        "up": "Z",
        "bed_mm": list(BED),
        "slicer": None,
        "slicer_note": "No PrusaSlicer, Cura, or OrcaSlicer binary was on this machine. No toolpath was produced. A mesh section is not a slice.",
        "minimum_web": "No single thickness. Each part records the dimension drawn for it. None of those webs has a coupon.",
        "minimum_web_status": "UNTESTED_UNTIL_PHYSICAL_COUPON",
        "nozzle_assumption": "0.4 mm is the structural default. 0.2 mm is available for ornament. Neither was run.",
        "parts": catalog,
        "instances": instances,
        "sections": sections,
        "shared_volume_mm3": clashes,
        "shared_volume_ok": not clashes,
        "intentional_contacts": [
            "Window wall rests on the floor. Faces meet. Volume shared is zero.",
            "Sash is inside the opening with 0.6 mm clearance. It does not enter the wall.",
            "Furniture rests on the floor. Faces meet. Volume shared is zero.",
            "Lace, bracket, and the shingle cartridge are on the bench, not attached to the room.",
        ],
        "not_claimed": [
            "Not printed.",
            "Magnet fit, strength, and any web smaller than a tested coupon are unproven.",
            "The LED cavity is a reservation, not a measured diode.",
            "This bay is not the finished house.",
        ],
    }
    with open(os.path.join(OUT, "assembly.json"), "w", encoding="utf8") as handle:
        json.dump({"units": "mm", "up": "Z", "instances": instances}, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(EVID, "report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    if clashes:
        raise SystemExit(1)
    print("detail proof ok", len(catalog), "parts", flush=True)
    return report


if __name__ == "__main__":
    build()
