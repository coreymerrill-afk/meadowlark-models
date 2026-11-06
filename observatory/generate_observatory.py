#!/usr/bin/env python3
"""H3C Celestial Observatory generator.

Mechanical print-test model for a Bambu Lab H3C Full Combo, 0.4 mm nozzles,
PLA first. Clearances are CAD targets. Nothing here has been printed or measured.

v1.1 corrects the v1.0 assembly:
- The deck was a plate on a 34 mm column and read as a floating disk on a shaft.
  The tower is now a drum the deck actually sits on.
- Inlay pockets were cut above the base solid, so the inlays had no seat.
- The retainer sat on the full axle diameter instead of in its groove.
- Hinge pins and the telescope trunnion did not share an axis, and a -35 deg
  rotation was about the tube origin rather than the cradle.
- The dome shell closed over the telescope and the orrery arm passed through it.
  The slit is a real shutter opening, and the orrery spins on a shoulder above
  the crown.
- TPU feet were flipped so the stems pointed away from their pockets.
"""

from __future__ import annotations

import json
import math
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
STL_DIR = ROOT / "stl"
RENDER_DIR = ROOT / "renders"
SEGMENTS = 64

# --- size, millimeters -------------------------------------------------------
BASE_OD = 160.0
BASE_H = 10.0
PLINTH_H = 3.0
PLINTH_R = 58.0

TOWER_OD = 96.0
TOWER_H = 46.0
PEG_H = 6.5
PEG_R = 9.0
PEG_RADIAL_CLEAR = 0.20
SOCKET_EXTRA = 0.55

SHELF_H = 4.0
SHELF_R = 56.0
BEARING_GAP = 0.12  # deck floats this far above the shelf; invisible, not a stick

PLATFORM_OD = 124.0
PLATFORM_H = 6.0
EAR_INNER = 9.0
EAR_OUTER = 15.0
EAR_X = 4.5
HINGE_ABOVE_DECK = 18.0
CRADLE_X = 24.0

DOME_R = 50.0
DOME_T = 2.0
SKIRT_T = 2.2
SKIRT_H = 1.8
GROOVE_DEPTH = 2.4
GROOVE_RADIAL_CLEAR = 0.30
DOME_AXIAL_GAP = 0.35
SLIT_W = 52.0
APEX_HOLE_R = 6.6

AXLE_D = 8.0
SPIN_CLEAR_D = 0.50
AXLE_HOLE_D = AXLE_D + SPIN_CLEAR_D  # 8.5
BASE_AXLE_HOLE_D = 8.8
ORRERY_HOLE_D = 8.8
FLANGE_H = 2.6
FLANGE_R = 7.2
WELL_EXTRA_R = 0.25
WELL_EXTRA_D = 0.35

HINGE_PIN_D = 4.0
HINGE_HOLE_D = 4.30
PIN_HEAD_H = 1.6
PIN_ENGAGE = 6.0
PIN_HEAD_GAP = 0.20

INLAY_R = 6.2
INLAY_GAP = 0.20
INLAY_T = 1.0
INLAY_POCKET_D = 1.25
INLAY_RING_R = 65.5

FOOT_STEM_D = 11.5
FOOT_POCKET_D = 12.0
FOOT_POCKET_DEPTH = 3.2
FOOT_PAD_H = 3.0
FOOT_AXIAL_GAP = 0.30
FOOT_RING_R = 52.0

RETAINER_INNER_R = 3.20
GROOVE_ROOT_R = 3.00
GROOVE_H = 1.8
CLIP_H = 1.4
CLIP_SIDE_GAP = 0.20

ORRERY_HUB_H = 4.2
CROWN_GAP = 3.2
HUB_TO_CLIP = 0.50

HOME_ELEV_DEG = 32.0
ELEV_MIN = 24.0
ELEV_MAX = 46.0

VERSION = "1.2.0"


def set_quality() -> None:
    mf.set_circular_segments(SEGMENTS)


def cylinder(h: float, r: float, r2: float | None = None, center: bool = False) -> mf.Manifold:
    return mf.Manifold.cylinder(h, r, r if r2 is None else r2, SEGMENTS, center)


def cube(x: float, y: float, z: float, center: bool = False) -> mf.Manifold:
    return mf.Manifold.cube([x, y, z], center)


def to_trimesh(solid: mf.Manifold, name: str) -> trimesh.Trimesh:
    if solid.is_empty():
        raise RuntimeError(f"empty solid: {name}")
    mesh = solid.to_mesh()
    verts = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    faces = np.asarray(mesh.tri_verts, dtype=np.int64)
    # process=True welds vertices and can open a manifold mesh. Trust the boolean.
    tm = trimesh.Trimesh(vertices=verts.copy(), faces=faces.copy(), process=False)
    tm.remove_unreferenced_vertices()
    tm.metadata["name"] = name
    if solid.status() != mf.Error.NoError:
        raise RuntimeError(f"{name} manifold status {solid.status()}")
    if abs(float(solid.volume())) < 1.0:
        raise RuntimeError(f"{name} has no volume")
    if not tm.is_watertight or not tm.is_winding_consistent:
        raise RuntimeError(f"{name} mesh is not a closed oriented shell")
    if tm.bounds[0][2] < -0.05:
        raise RuntimeError(f"{name} extends below the bed (z {tm.bounds[0][2]:.3f}); STL is not print-oriented")
    return tm


def euler(deg: Sequence[float]) -> np.ndarray:
    """Intrinsic XYZ, matching THREE r149 Quaternion.setFromEuler('XYZ')."""
    rx, ry, rz = [math.radians(a) for a in deg]
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    rxm = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    rym = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rzm = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rzm @ rym @ rxm


def matrix(translation: Sequence[float], rotation_deg: Sequence[float]) -> List[List[float]]:
    m = np.eye(4)
    m[:3, :3] = euler(rotation_deg)
    m[:3, 3] = translation
    return np.round(m, 6).tolist()


def ry(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


# --- parts -------------------------------------------------------------------

def build_base() -> mf.Manifold:
    body = cylinder(BASE_H, BASE_OD / 2)
    rim = cylinder(2.0, BASE_OD / 2) - cylinder(2.0, BASE_OD / 2 - 6.5)
    body = body + rim.translate([0, 0, BASE_H])
    plinth = cylinder(PLINTH_H, PLINTH_R).translate([0, 0, BASE_H])
    body = body + plinth

    seat = BASE_H + PLINTH_H
    socket = cylinder(PEG_H + SOCKET_EXTRA, PEG_R + PEG_RADIAL_CLEAR)
    key = cube(5.6, 3.4, PEG_H + SOCKET_EXTRA).translate([-2.8, PEG_R - 0.4, 0])
    body = body - (socket + key).translate([0, 0, seat - (PEG_H + SOCKET_EXTRA)])

    well = cylinder(FLANGE_H + WELL_EXTRA_D, FLANGE_R + WELL_EXTRA_R)
    shaft = cylinder(seat + 2.0, BASE_AXLE_HOLE_D / 2)
    body = body - well - shaft

    pocket_r = INLAY_R + INLAY_GAP
    for i in range(8):
        ang = i * (math.tau / 8) + math.pi / 8
        x, y = INLAY_RING_R * math.cos(ang), INLAY_RING_R * math.sin(ang)
        pocket = cylinder(INLAY_POCKET_D + 0.2, pocket_r).translate([x, y, BASE_H - INLAY_POCKET_D])
        body = body - pocket

    for i in range(4):
        ang = i * (math.pi / 2) + math.pi / 4
        x, y = FOOT_RING_R * math.cos(ang), FOOT_RING_R * math.sin(ang)
        body = body - cylinder(FOOT_POCKET_DEPTH, FOOT_POCKET_D / 2).translate([x, y, 0])

    for i in range(36):
        ang = i * 10.0
        tick = cube(8.0, 0.7, 0.45).translate([BASE_OD / 2 - 11.0, -0.35, BASE_H - 0.45])
        body = body - tick.rotate([0, 0, ang])
    return body


def build_tower() -> mf.Manifold:
    body = cylinder(TOWER_H, TOWER_OD / 2 - 0.6)
    for i in range(18):
        ang = i * (math.tau / 18)
        x = (TOWER_OD / 2 + 0.15) * math.cos(ang)
        y = (TOWER_OD / 2 + 0.15) * math.sin(ang)
        flute = cylinder(TOWER_H - 8.0, 2.3).translate([x, y, 4.0])
        body = body - flute
    body = body ^ cylinder(TOWER_H, TOWER_OD / 2)

    peg = cylinder(PEG_H, PEG_R).translate([0, 0, -PEG_H])
    key = cube(5.0, 3.0, PEG_H).translate([-2.5, PEG_R - 0.2, -PEG_H])
    body = body + peg + key

    # 45° underside so the wider shelf prints peg-down without support.
    rise = SHELF_R - (TOWER_OD / 2)
    chamfer = cylinder(rise, TOWER_OD / 2, SHELF_R).translate([0, 0, TOWER_H - rise])
    shelf = cylinder(SHELF_H, SHELF_R).translate([0, 0, TOWER_H])
    body = body + chamfer + shelf

    for i in range(4):
        panel = cube(16.0, 2.2, 20.0, center=True).translate([0, TOWER_OD / 2 - 1.3, TOWER_H * 0.48])
        panel = panel.rotate([0, 0, 45 + i * 90])
        body = body - panel

    bore = cylinder(TOWER_H + SHELF_H + PEG_H + 4, AXLE_HOLE_D / 2).translate([0, 0, -PEG_H - 2])
    # Peg tip on the bed. Assembly translation shifts this back onto the plinth.
    return (body - bore).translate([0, 0, PEG_H])


def build_platform(hinge_local_z: float) -> mf.Manifold:
    deck = cylinder(PLATFORM_H, PLATFORM_OD / 2)
    deck = deck - cylinder(PLATFORM_H + 2, AXLE_HOLE_D / 2).translate([0, 0, -1])

    groove_outer = DOME_R + GROOVE_RADIAL_CLEAR
    groove_inner = DOME_R - SKIRT_T - GROOVE_RADIAL_CLEAR
    groove = cylinder(GROOVE_DEPTH, groove_outer) - cylinder(GROOVE_DEPTH, groove_inner)
    deck = deck - groove.translate([0, 0, PLATFORM_H - GROOVE_DEPTH])

    ring = cylinder(1.3, 18.0) - cylinder(1.3, AXLE_HOLE_D / 2 + 0.4)
    deck = deck + ring.translate([0, 0, PLATFORM_H])

    for side in (-1, 1):
        y = side * (EAR_INNER + EAR_OUTER) / 2
        ear = cube(EAR_X * 2, EAR_OUTER - EAR_INNER, HINGE_ABOVE_DECK + 6, center=True)
        ear = ear.translate([CRADLE_X, y, PLATFORM_H + (HINGE_ABOVE_DECK + 6) / 2])
        deck = deck + ear

    hole = cylinder(EAR_OUTER * 2 + 8, HINGE_HOLE_D / 2, center=True).rotate([90, 0, 0])
    deck = deck - hole.translate([CRADLE_X, 0, hinge_local_z])

    for i in range(8):
        spoke = cube(26.0, 1.6, 0.5).translate([16.0, -0.8, PLATFORM_H - 0.5]).rotate([0, 0, i * 45.0])
        deck = deck - spoke
    return deck


def build_dome() -> mf.Manifold:
    """One shell. The skirt overlaps the hemisphere so the union is a single solid."""
    ball = mf.Manifold.sphere(DOME_R, SEGMENTS)
    hemi = ball - cube(DOME_R * 4, DOME_R * 4, DOME_R * 2, center=True).translate([0, 0, -DOME_R])
    skirt = cylinder(SKIRT_H + 1.2, DOME_R) - cylinder(SKIRT_H + 1.2, DOME_R - SKIRT_T)
    outer = (hemi + skirt.translate([0, 0, -SKIRT_H])).translate([0, 0, SKIRT_H])
    inner = mf.Manifold.sphere(DOME_R - DOME_T, SEGMENTS).translate([0, 0, SKIRT_H])
    inner_skirt = cylinder(SKIRT_H + 0.5, DOME_R - SKIRT_T).translate([0, 0, -0.2])
    shell = outer - inner - inner_skirt
    # Shutter on +X only. Starts above the skirt so the ring stays whole.
    slit = cube(DOME_R + 6, SLIT_W, DOME_R + 8, center=False).translate([6.0, -SLIT_W / 2, SKIRT_H + 4.0])
    crown = cylinder(DOME_R, APEX_HOLE_R).translate([0, 0, SKIRT_H + DOME_R * 0.35])
    return shell - slit - crown


def build_telescope() -> Tuple[mf.Manifold, float]:
    """Tube stands on the eyepiece. Returns the solid and the trunnion Z."""
    ep_len, tube_len, flare = 9.0, 40.0, 7.0
    trunnion_z = 15.0
    od, id_ = 16.0, 10.5
    tube = cylinder(ep_len, 5.6) - cylinder(ep_len, 3.4)
    main = cylinder(tube_len, od / 2) - cylinder(tube_len, id_ / 2)
    tube = tube + main.translate([0, 0, ep_len])
    for z in (ep_len + 6, ep_len + 18, ep_len + 30, ep_len + 40):
        ring = (cylinder(1.5, od / 2 + 0.9) - cylinder(1.5, od / 2 - 0.15)).translate([0, 0, z])
        tube = tube + ring
    flare_m = cylinder(flare, od / 2, od / 2 + 2.4).translate([0, 0, ep_len + tube_len])
    flare_m = flare_m - cylinder(flare, id_ / 2 - 0.2).translate([0, 0, ep_len + tube_len])
    tube = tube + flare_m

    boss_outer = EAR_INNER - 1.0
    boss_inner = 6.0
    boss_len = boss_outer - boss_inner
    for side in (-1, 1):
        boss = cylinder(boss_len, 5.2, center=True).rotate([90, 0, 0])
        center_y = side * (boss_inner + boss_outer) / 2
        tube = tube + boss.translate([0, center_y, trunnion_z])
    hole = cylinder(EAR_INNER * 2 + 4, HINGE_HOLE_D / 2, center=True).rotate([90, 0, 0])
    tube = tube - hole.translate([0, 0, trunnion_z])
    return tube, trunnion_z


def build_hinge_pin() -> mf.Manifold:
    span = PIN_HEAD_H + (EAR_OUTER - EAR_INNER) + (EAR_INNER - (EAR_INNER - 1.0)) + PIN_ENGAGE
    # head + ear thickness + 1 mm ear-to-boss gap + engagement
    shaft_len = (EAR_OUTER - EAR_INNER) + 1.0 + PIN_ENGAGE
    head = cylinder(PIN_HEAD_H, 3.3)
    shaft = cylinder(shaft_len, HINGE_PIN_D / 2).translate([0, 0, PIN_HEAD_H])
    tip = cylinder(1.1, HINGE_PIN_D / 2, HINGE_PIN_D / 2 - 0.45).translate([0, 0, PIN_HEAD_H + shaft_len])
    return head + shaft + tip


def build_axle(groove_z: float, tip_z: float) -> mf.Manifold:
    flange = cylinder(FLANGE_H, FLANGE_R)
    shaft = cylinder(tip_z - FLANGE_H, AXLE_D / 2).translate([0, 0, FLANGE_H])
    pin = flange + shaft
    tool = cylinder(GROOVE_H, AXLE_D / 2 + 0.2) - cylinder(GROOVE_H, GROOVE_ROOT_R)
    pin = pin - tool.translate([0, 0, groove_z])
    # Tip above the groove, small enough for the clip to slide down onto it.
    tip_start = groove_z + GROOVE_H
    tip = cylinder(tip_z - tip_start, GROOVE_ROOT_R - 0.25, 2.4).translate([0, 0, tip_start])
    return pin + tip


def build_retainer() -> mf.Manifold:
    ring = cylinder(CLIP_H, 5.5) - cylinder(CLIP_H, RETAINER_INNER_R)
    # Tab overlaps the ring so the clip is one body. Opening is on the other side.
    tab = cube(4.6, 2.6, CLIP_H).translate([3.6, -1.3, 0])
    opening = cube(6.2, 6.8, CLIP_H + 0.4).translate([-8.2, -3.4, -0.2])
    return ring + tab - opening


def build_orrery() -> mf.Manifold:
    hub = cylinder(ORRERY_HUB_H, 11.0) - cylinder(ORRERY_HUB_H, ORRERY_HOLE_D / 2)
    arm_a = cube(36.0, 6.0, 3.2).translate([6.0, -3.0, 0.0])
    arm_b = cube(32.0, 5.2, 3.2).translate([-36.0, -2.6, 0.0])
    # Posts are buried in the arms. A post that only touches a face splits into two bodies.
    post_a = cylinder(5.2, 2.00).translate([38.0, 0.0, 2.0])
    post_b = cylinder(5.0, 1.90).translate([-28.0, 0.0, 2.0])
    return hub + arm_a + arm_b + post_a + post_b


def build_planet(radius: float, ring: bool) -> mf.Manifold:
    planet = mf.Manifold.sphere(radius, 48).translate([0, 0, radius])
    hole = cylinder(max(radius * 0.72, 3.6), 2.55).translate([0, 0, 0.0])
    planet = planet - hole
    if ring:
        band = (cylinder(1.4, radius + 2.6) - cylinder(1.4, radius * 0.72)).translate([0, 0, radius - 0.7])
        planet = planet + band
    return planet


def build_inlay(kind: str) -> mf.Manifold:
    r = INLAY_R
    if kind == "star":
        coords = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.42
            coords.append([rad * math.cos(ang), rad * math.sin(ang)])
        cs = mf.CrossSection([np.array(coords, dtype=np.float64)])
    elif kind == "hex":
        a = np.linspace(0, math.tau, 6, endpoint=False) + math.pi / 6
        cs = mf.CrossSection([np.column_stack([r * np.cos(a), r * np.sin(a)])])
    elif kind == "diamond":
        poly = np.array([[0, r], [-r * 0.72, 0], [0, -r], [r * 0.72, 0]], dtype=np.float64)
        cs = mf.CrossSection([poly])
        if cs.area() <= 0:
            cs = mf.CrossSection([poly[::-1].copy()])
    elif kind == "crescent":
        cs = mf.CrossSection.circle(r, 48) - mf.CrossSection.circle(r * 0.78, 48).translate([r * 0.38, 0])
    else:
        cs = mf.CrossSection.circle(r, 48)
    return mf.Manifold.extrude(cs, INLAY_T)


def build_coupon() -> mf.Manifold:
    """One first plate: axle and hinge ladders, a real bridge, and a snap-off 8 mm pin."""
    plate = cube(86.0, 46.0, 3.0).translate([-8.0, -8.0, 0])
    # Ø4 hinge ladder (fit_pin). Left to right: 4.00, 4.20, 4.30, 4.50, 4.80
    for i, d in enumerate((4.00, 4.20, 4.30, 4.50, 4.80)):
        plate = plate - cylinder(4.0, d / 2).translate([4.0 + i * 12.0, 30.0, -0.5])
    # Ø8 axle ladder: 8.30, 8.50, 8.70, 9.00
    for i, d in enumerate((8.30, 8.50, 8.70, 9.00)):
        plate = plate - cylinder(4.0, d / 2).translate([8.0 + i * 16.0, 14.0, -0.5])
    # Bridge: 14 mm span, 1.6 mm thick, printed in the air between two piers.
    for x in (58.0, 74.0):
        plate = plate + cube(5.0, 10.0, 8.0).translate([x, 4.0, 3.0])
    plate = plate + cube(21.0, 8.0, 1.6).translate([56.0, 5.0, 11.0])
    # Snap-off Ø8 pin stands beside the plate. The tab overlaps both solids.
    pin = cylinder(14.0, 4.0).translate([88.0, 20.0, 0.0])
    tab = cube(18.0, 1.6, 1.4).translate([68.0, 19.2, 0.0])
    return plate + pin + tab


def build_fit_pin() -> mf.Manifold:
    return cylinder(16.0, HINGE_PIN_D / 2) + cylinder(1.4, 3.1)


def build_foot() -> mf.Manifold:
    pad = cylinder(FOOT_PAD_H, 9.0)
    stem_h = FOOT_POCKET_DEPTH - FOOT_AXIAL_GAP
    stem = cylinder(stem_h, FOOT_STEM_D / 2).translate([0, 0, FOOT_PAD_H])
    return pad + stem


# --- assembly math -----------------------------------------------------------

def stack() -> Dict[str, float]:
    seat = BASE_H + PLINTH_H
    tower_z = seat + BEARING_GAP
    shelf_top = tower_z + TOWER_H + SHELF_H
    platform_z = shelf_top + BEARING_GAP
    platform_top = platform_z + PLATFORM_H
    hinge_z = platform_top + HINGE_ABOVE_DECK
    groove_floor = platform_top - GROOVE_DEPTH
    dome_z = groove_floor + DOME_AXIAL_GAP
    crown_z = dome_z + SKIRT_H + DOME_R
    shoulder_z = crown_z + CROWN_GAP
    orrery_z = shoulder_z
    groove_z = orrery_z + ORRERY_HUB_H + HUB_TO_CLIP
    tip_z = groove_z + GROOVE_H + 3.2
    return {
        "seat": seat,
        "tower_z": tower_z,
        "platform_z": platform_z,
        "platform_top": platform_top,
        "hinge_z": hinge_z,
        "dome_z": dome_z,
        "crown_z": crown_z,
        "orrery_z": orrery_z,
        "groove_z": groove_z,
        "tip_z": tip_z,
    }


def elevation_rotation(elev_deg: float) -> float:
    """STL +Z is vertical. This Y rotation lays the tube at elev_deg above +X."""
    return 90.0 - elev_deg


def probe_elevation_sign() -> int:
    phi = elevation_rotation(HOME_ELEV_DEG)
    base = ry(phi) @ np.array([0.0, 0.0, 1.0])
    bumped = ry(-4.0) @ base
    e0 = math.degrees(math.atan2(base[2], base[0]))
    e1 = math.degrees(math.atan2(bumped[2], bumped[0]))
    return -1 if e1 > e0 else 1


# --- validate ----------------------------------------------------------------

def apply_matrix(tm: trimesh.Trimesh, mat: np.ndarray) -> trimesh.Trimesh:
    out = tm.copy()
    out.apply_transform(mat)
    return out


def intersection_mm3(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    """Solid intersection volume. This is the audit's boolean, not a vertex sample."""
    gap = max(float(np.max(a.bounds[0] - b.bounds[1])), float(np.max(b.bounds[0] - a.bounds[1])))
    if gap > 0.2:
        return 0.0
    hit = trimesh.boolean.intersection([a, b], engine="manifold")
    if hit is None or hit.is_empty or len(hit.faces) == 0:
        return 0.0
    return abs(float(hit.volume))


def check_assembly(meshes: Dict[str, trimesh.Trimesh], instances: List[dict], s: Dict[str, float]) -> List[str]:
    issues: List[str] = []
    placed: List[Tuple[str, trimesh.Trimesh]] = []
    for inst in instances:
        if inst.get("scene") == "bench":
            continue
        mat = np.array(inst["transform"], dtype=np.float64)
        placed.append((inst["id"], apply_matrix(meshes[inst["part_id"]], mat)))

    # Trunnion must land on the hinge.
    tel = next(i for i in instances if i["part_id"] == "telescope_tube")
    local = np.array([0.0, 0.0, tel["trunnion_z"], 1.0])
    world = np.array(tel["transform"], dtype=np.float64) @ local
    hinge = np.array([CRADLE_X, 0.0, s["hinge_z"]])
    if np.linalg.norm(world[:3] - hinge) > 1e-3:
        issues.append(f"telescope trunnion is {np.linalg.norm(world[:3] - hinge):.3f} mm off the cradle axis")

    by_name = {name: mesh for name, mesh in placed}

    def mesh(name: str) -> trimesh.Trimesh:
        return by_name[name]

    for i, (na, a) in enumerate(placed):
        for nb, b in placed[i + 1 :]:
            volume = intersection_mm3(a, b)
            if volume > 1.0:
                issues.append(f"solid intersection {na} ∩ {nb} = {volume:.1f} mm³")

    retainer = mesh("retainer_clip")
    groove_lo, groove_hi = s["groove_z"], s["groove_z"] + GROOVE_H
    overlap = min(retainer.bounds[1][2], groove_hi) - max(retainer.bounds[0][2], groove_lo)
    if overlap < 0.8:
        issues.append(f"retainer overlaps the axle groove by {overlap:.2f} mm")

    for inst in instances:
        if not str(inst["id"]).startswith("tpu_foot"):
            continue
        foot = mesh(inst["id"])
        if foot.bounds[1][2] < 1.0 or foot.bounds[0][2] > -1.0:
            issues.append(f"{inst['id']} is not seated in a pocket (z {foot.bounds[:, 2].tolist()})")
        clash = intersection_mm3(foot, mesh("base"))
        if clash > 1.0:
            issues.append(f"{inst['id']} ∩ base = {clash:.1f} mm³")

    def spun(name: str, origin, axis, deg) -> trimesh.Trimesh:
        out = mesh(name).copy()
        out.apply_transform(trimesh.transformations.rotation_matrix(math.radians(deg), axis, origin))
        return out

    for yaw in (0, 90, 180, 270):
        volume = intersection_mm3(spun("dome", [0, 0, 0], [0, 0, 1], yaw), mesh("rotating_platform"))
        if volume > 1.0:
            issues.append(f"dome yaw {yaw}° ∩ deck = {volume:.1f} mm³")
        volume = intersection_mm3(spun("orrery_arm", [0, 0, 0], [0, 0, 1], yaw), mesh("dome"))
        if volume > 1.0:
            issues.append(f"orrery yaw {yaw}° ∩ dome = {volume:.1f} mm³")

    sign = probe_elevation_sign()
    base_mat = np.array(tel["transform"], dtype=np.float64)
    hinge_p = np.array([CRADLE_X, 0.0, s["hinge_z"]])
    for elev in (ELEV_MIN, HOME_ELEV_DEG, ELEV_MAX):
        delta = (elev - HOME_ELEV_DEG) * sign
        swing = np.eye(4)
        swing[:3, :3] = ry(delta)
        swing[:3, 3] = hinge_p - ry(delta) @ hinge_p
        posed = apply_matrix(meshes["telescope_tube"], swing @ base_mat)
        for other in ("rotating_platform", "tower", "axle_pin", "dome"):
            volume = intersection_mm3(posed, mesh(other))
            if volume > 1.0:
                issues.append(f"telescope at {elev:.0f}° ∩ {other} = {volume:.1f} mm³")
    return issues


# --- preview -----------------------------------------------------------------

def render_preview(meshes: Dict[str, trimesh.Trimesh], instances: List[dict], path: Path, title: str, azim: float) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(10, 10), facecolor="#10151d")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#10151d")
    for inst in instances:
        if inst.get("scene") == "bench":
            continue
        tm = meshes[inst["part_id"]]
        mat = np.array(inst["transform"], dtype=np.float64)
        homo = np.hstack([tm.vertices, np.ones((len(tm.vertices), 1))])
        verts = (mat @ homo.T).T[:, :3]
        faces = tm.faces
        step = max(1, len(faces) // 3500)
        polys = verts[faces[::step]]
        rgb = tm.visual.face_colors[0, :3] / 255.0
        coll = Poly3DCollection(polys, alpha=0.96, linewidths=0.02)
        coll.set_facecolor((*rgb, 0.96))
        coll.set_edgecolor((0.02, 0.03, 0.05, 0.12))
        ax.add_collection3d(coll)
    ax.set_box_aspect((1, 1, 0.8))
    ax.set_xlim(-90, 90)
    ax.set_ylim(-90, 90)
    ax.set_zlim(-8, 150)
    ax.axis("off")
    ax.view_init(elev=18, azim=azim)
    fig.suptitle(title, color="white", fontsize=13, y=0.96)
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)


def write_readme(path: Path, s: Dict[str, float], issues: List[str]) -> None:
    status = "CAD checks passed" if not issues else "CAD checks reported issues"
    path.write_text(
        f"""# H3C Celestial Observatory — v{VERSION}

Print-test model for a **Bambu Lab H3C Full Combo** with **0.4 mm** nozzles only
(the machine's 0.4 mm PrintTools, plus seven extra 0.4 mm hotends). PLA first.
Optional feet are black TPU 75A and are not required for the mechanism.

**{status}. Not printed. Not measured.** Clearances below are design targets
from this CAD file, not caliper readings and not a finished-print result.

All 19 unique STLs generated toolpaths in PrusaSlicer 2.7.4 using generic 0.4 mm / 0.20 mm PLA, supported where needed; not official H3C profile, not physically tested; re-slice in Bambu Studio H3C profile; assembly 3MF not plate. Generic G-code from that check is not included.

## Print the coupon first

`stl/fit_coupon.stl` is the first plate. It is one body:

- Ø4.0 hole ladder, left to right: 4.00, 4.20, 4.30, 4.50, 4.80 mm. The separate `fit_pin` is Ø4.0.
- Ø8.0 hole ladder, left to right: 8.30, 8.50, 8.70, 9.00 mm. A snap-off Ø8.0 pin is on the same plate.
- A 14 mm bridge, 1.6 mm thick, between two piers.
- The hinge design target is the 4.30 mm hole. The axle design target is the 8.50 mm hole.
  If those are tight or sloppy, stop before printing the observatory. This page cannot see that result.

## Mechanism

The tower is an 84 mm drum. The deck sits on a shelf on that drum (0.12 mm CAD gap),
and the 8 mm axle only registers the spin. It is not the structure.

1. Drop the axle flange into the underside well.
2. Press the tower peg into the base. The shoulder seats on the plinth; the peg does not bottom out.
3. Set the deck on the tower shelf. It should turn on the axle.
4. Set the dome skirt in the deck groove. It turns on its own. The shutter opening faces +X.
5. Sit the telescope in the cradle and slide a hinge pin in from each side, head outward.
6. The axle continues through a loose hole in the crown. Sit the orrery on the axle shoulder above the dome.
7. Slide the retainer down the tip into the groove. It should not clamp the arm.
8. Press inlays into the eight base pockets. Feet are optional.

Home telescope elevation is {HOME_ELEV_DEG:.0f}° above the deck, toward +X.
The CAD range that stays clear of the dome and the deck is {ELEV_MIN:.0f}° to {ELEV_MAX:.0f}°.

All 19 unique STLs generated toolpaths in PrusaSlicer 2.7.4 using generic 0.4 mm / 0.20 mm PLA, supported where needed; not official H3C profile, not physically tested; re-slice in Bambu Studio H3C profile; assembly 3MF not plate. Generic G-code from that check is not included.

Supports from that slice: dome and telescope require supports. **planet_ringed requires supports** — brim alone fails with no extrusions in the first layer. planet_large uses a brim and no supports. Tower uses a brim and still warned of floating bridge anchors and long bridging extrusions. axle_pin, fit_pin, and hinge_pin want a brim (low bed adhesion). Leave supports off the coupon. The optional foot was path-checked with PLA, not a TPU profile.

## Files

| File | What it is |
|------|------------|
| `stl/*.stl` | One watertight mesh per part, bed on Z = 0. Not a toolpath. |
| `h3c_celestial_observatory_stls.zip` | Those STLs. Toolpaths were checked in PrusaSlicer; this zip is meshes, not G-code. |
| `h3c_celestial_observatory.3mf` | Colored assembly scene (face colors). **Not** a Bambu plate and **not** sliced as a plate. |
| `manifest.json` | Quantities, colors, 4×4 assembly transforms, pivots. |
| `generate_observatory.py` | This source. |

## Clearances (design targets, unverified on a machine)

| Interface | Target |
|-----------|--------|
| Axle 8.0 in tower and deck bores | 8.5 mm (0.50 mm diametral) |
| Axle in the orrery | 8.8 mm |
| Axle through the base and the dome crown | loose, not a bearing |
| Hinge pin 4.0 | 4.30 mm holes |
| Dome skirt in the groove | 0.30 mm radial each side, 0.35 mm above the groove floor |
| Inlay in its pocket | 0.20 mm lateral each side |
| Tower peg | 0.20 mm radial, does not bottom out |
| Retainer on the groove root | 0.20 mm radial |
| Deck above the shelf | 0.12 mm |
| Assembled envelope | under 220 mm. Stack height is about {s['tip_z']:.0f} mm plus the feet below the base. |

Regenerate with `python3 generate_observatory.py` from this directory
(`manifold3d`, `trimesh`, `numpy`, `scipy`, `rtree`, `pillow`, `matplotlib`).
""",
        encoding="utf-8",
    )


@dataclass
class PartSpec:
    id: str
    filename: str
    quantity: int
    material: str
    color_name: str
    color_hex: str
    print_notes: str
    tests: List[str]
    bbox_mm: List[float] = field(default_factory=list)
    volume_mm3: float = 0.0
    watertight: bool = False
    triangle_count: int = 0


def main() -> None:
    set_quality()
    STL_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    s = stack()
    sign = probe_elevation_sign()
    phi = elevation_rotation(HOME_ELEV_DEG)
    trunnion_holder = {}

    colors = {
        "base": ("PLA", "Navy", "#243656"),
        "tower": ("PLA", "Ivory", "#f3ead7"),
        "axle_pin": ("PLA", "Brass", "#e6c36a"),
        "retainer_clip": ("PLA", "Brass", "#f0d48a"),
        "rotating_platform": ("PLA", "Sandstone", "#c4a574"),
        "dome": ("PLA", "Cyan", "#2ec4e6"),
        "telescope_tube": ("PLA", "Gold", "#f0b429"),
        "hinge_pin": ("PLA", "Ivory", "#f7f1e4"),
        "orrery_arm": ("PLA", "Magenta", "#e23b8c"),
        "planet_large": ("PLA", "Amber", "#ffd166"),
        "planet_ringed": ("PLA", "Rose", "#ff8ad4"),
        "inlay_star": ("PLA", "Cyan", "#2ec4e6"),
        "inlay_crescent": ("PLA", "Magenta", "#e23b8c"),
        "inlay_hex": ("PLA", "Yellow", "#f0b429"),
        "inlay_diamond": ("PLA", "White", "#f7f4ef"),
        "inlay_circle": ("PLA", "Black", "#1a1a1a"),
        "fit_coupon": ("PLA", "White", "#f7f4ef"),
        "fit_pin": ("PLA", "White", "#f7f4ef"),
        "tpu_foot": ("TPU 75A", "Black", "#161616"),
    }
    quantity = {
        "base": 1, "tower": 1, "axle_pin": 1, "retainer_clip": 1, "rotating_platform": 1,
        "dome": 1, "telescope_tube": 1, "hinge_pin": 2, "orrery_arm": 1, "planet_large": 1,
        "planet_ringed": 1, "inlay_star": 2, "inlay_crescent": 2, "inlay_hex": 2,
        "inlay_diamond": 1, "inlay_circle": 1, "fit_coupon": 1, "fit_pin": 2, "tpu_foot": 4,
    }
    notes = {
        "base": "Flat on the bottom. Pockets and the axle well are in the solid.",
        "tower": "Peg down. Use a brim. PrusaSlicer 2.7.4 still warned of floating bridge anchors and long bridging extrusions on the shelf. Re-check them in the H3C profile.",
        "axle_pin": "Standing on the flange. Brim recommended (low bed adhesion in the generic PLA slice).",
        "retainer_clip": "Flat, one piece. Slide it down the tip into the groove. Print a spare.",
        "rotating_platform": "Flat on the bottom. Ear holes are a sideways bridge. No supports.",
        "dome": "Skirt on the bed. Tree supports inside the shell. The shutter and crown hole are overhangs.",
        "telescope_tube": "Eyepiece on the bed. Support the sideways bosses. Rings are small overhangs.",
        "hinge_pin": "Head down. Print a spare. Brim recommended (low bed adhesion).",
        "orrery_arm": "Flat on the bed. Hub, arms, and posts are one body. No supports.",
        "planet_large": "Socket rim on the bed. Brim, no supports, in the generic PLA slice.",
        "planet_ringed": "Socket rim on the bed. The ring is joined to the sphere. Supports are required. Brim alone fails: PrusaSlicer 2.7.4 reported no extrusions in the first layer.",
        "inlay_star": "Flat. One color.",
        "inlay_crescent": "Flat. One color.",
        "inlay_hex": "Flat. One color.",
        "inlay_diamond": "Flat. One color.",
        "inlay_circle": "Flat. One color.",
        "fit_coupon": "Print this plate first, flat, supports off. The bridge is the test. The Ø8 pin stands beside the plate.",
        "fit_pin": "Standing. Ø4.0 mate for the coupon. Brim recommended (low bed adhesion).",
        "tpu_foot": "Pad down. Optional. The generic slice used a PLA profile only, not a TPU profile.",
    }
    tests = {
        "base": ["large flat", "inlay pockets", "foot pockets", "keyed socket"],
        "tower": ["flutes", "window recesses", "keyed peg", "axle bore"],
        "axle_pin": ["cylinder", "flange", "retainer groove"],
        "retainer_clip": ["clip clearance"],
        "rotating_platform": ["spin bore", "dome groove", "hinge bridge"],
        "dome": ["thin shell", "shutter opening", "skirt"],
        "telescope_tube": ["thin wall", "barrel rings", "trunnion"],
        "hinge_pin": ["pin diameter"],
        "orrery_arm": ["arms", "posts"],
        "planet_large": ["sphere", "socket"],
        "planet_ringed": ["ring"],
        "inlay_star": ["press-fit shape"],
        "inlay_crescent": ["press-fit shape"],
        "inlay_hex": ["press-fit shape"],
        "inlay_diamond": ["press-fit shape"],
        "inlay_circle": ["press-fit shape"],
        "fit_coupon": ["first plate", "bridge", "clearance ladder"],
        "fit_pin": ["coupon mate"],
        "tpu_foot": ["optional soft foot"],
    }

    builders = {
        "base": build_base,
        "tower": build_tower,
        "axle_pin": lambda: build_axle(s["groove_z"], s["tip_z"]),
        "retainer_clip": build_retainer,
        "rotating_platform": lambda: build_platform(s["hinge_z"] - s["platform_z"]),
        "dome": build_dome,
        "hinge_pin": build_hinge_pin,
        "orrery_arm": build_orrery,
        "planet_large": lambda: build_planet(6.2, False),
        "planet_ringed": lambda: build_planet(4.6, True),
        "inlay_star": lambda: build_inlay("star"),
        "inlay_crescent": lambda: build_inlay("crescent"),
        "inlay_hex": lambda: build_inlay("hex"),
        "inlay_diamond": lambda: build_inlay("diamond"),
        "inlay_circle": lambda: build_inlay("circle"),
        "fit_coupon": build_coupon,
        "fit_pin": build_fit_pin,
        "tpu_foot": build_foot,
    }

    print("Building telescope…")
    tel_solid, trunnion_z = build_telescope()
    trunnion_holder["z"] = trunnion_z

    meshes: Dict[str, trimesh.Trimesh] = {}
    specs: List[PartSpec] = []
    bed_shift: Dict[str, float] = {}
    file_issues: List[str] = []
    print("Building parts…")
    solids = {"telescope_tube": tel_solid}
    for pid, builder in builders.items():
        print(f"  {pid}")
        solids[pid] = builder()

    order = [
        "base", "tower", "axle_pin", "retainer_clip", "rotating_platform", "dome",
        "telescope_tube", "hinge_pin", "orrery_arm", "planet_large", "planet_ringed",
        "inlay_star", "inlay_crescent", "inlay_hex", "inlay_diamond", "inlay_circle",
        "fit_coupon", "fit_pin", "tpu_foot",
    ]
    for pid in order:
        preview = solids[pid].to_mesh()
        min_z = float(np.asarray(preview.vert_properties)[:, 2].min())
        if abs(min_z) > 0.02:
            solids[pid] = solids[pid].translate([0, 0, -min_z])
            bed_shift[pid] = min_z
        else:
            bed_shift[pid] = 0.0
        tm = to_trimesh(solids[pid], pid)
        hex_color = colors[pid][2].lstrip("#")
        rgb = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
        tm.visual.face_colors = np.tile(np.array(rgb + [255], dtype=np.uint8), (len(tm.faces), 1))
        tm.export(STL_DIR / f"{pid}.stl")
        meshes[pid] = tm
        welded = trimesh.load(STL_DIR / f"{pid}.stl", force="mesh", process=False)
        welded.merge_vertices()
        welded.update_faces(welded.unique_faces() & welded.nondegenerate_faces())
        welded.remove_unreferenced_vertices()
        welded.fix_normals()
        n_bodies = len(welded.split(only_watertight=False))
        if not welded.is_watertight or not welded.is_winding_consistent or welded.volume <= 0 or n_bodies != 1:
            file_issues.append(
                f"{pid}: file is not one watertight body (watertight={welded.is_watertight}, bodies={n_bodies}, volume={welded.volume:.1f})"
            )
        if welded.bounds[0][2] < -0.05 or welded.bounds[0][2] > 0.05:
            file_issues.append(f"{pid}: bed face is at z={welded.bounds[0][2]:.3f}, not 0")
        ext = tm.extents.tolist()
        specs.append(
            PartSpec(
                id=pid,
                filename=f"stl/{pid}.stl",
                quantity=quantity[pid],
                material=colors[pid][0],
                color_name=colors[pid][1],
                color_hex=colors[pid][2],
                print_notes=notes[pid],
                tests=tests[pid],
                bbox_mm=[round(v, 3) for v in ext],
                volume_mm3=round(float(tm.volume), 1),
                watertight=bool(tm.is_watertight),
                triangle_count=int(len(tm.faces)),
            )
        )

    instances: List[dict] = []

    def add(pid: str, translation, rotation=(0, 0, 0), *, scene="assembly", explode=(0, 0, 0), extra=None, iid=None):
        shift = bed_shift.get(pid, 0.0)
        translation = (translation[0], translation[1], translation[2] + shift)
        inst = {
            "id": iid or pid,
            "part_id": pid,
            "scene": scene,
            "transform": matrix(translation, rotation),
            "translation_mm": [round(float(v), 4) for v in translation],
            "rotation_deg_xyz": [round(float(v), 4) for v in rotation],
            "explode_mm": [round(float(v), 3) for v in explode],
        }
        if extra:
            inst.update(extra)
        instances.append(inst)

    add("base", (0, 0, 0), explode=(0, 0, 0))
    add("tower", (0, 0, s["tower_z"] - PEG_H), explode=(0, 0, 18))
    add("axle_pin", (0, 0, 0), explode=(28, 0, 30))
    add("rotating_platform", (0, 0, s["platform_z"]), explode=(0, 0, 36))
    add("dome", (0, 0, s["dome_z"]), explode=(0, 0, 62))

    rot_y = phi
    local_h = np.array([0.0, 0.0, trunnion_z])
    trans = np.array([CRADLE_X, 0.0, s["hinge_z"]]) - ry(rot_y) @ local_h
    add(
        "telescope_tube",
        trans,
        (0.0, rot_y, 0.0),
        explode=(36, 0, 8),
        extra={"trunnion_z": trunnion_z},
    )

    # Rx(+90) sends local +Z toward -Y. Head stays outboard of +Y.
    y_pos = EAR_OUTER + PIN_HEAD_GAP + PIN_HEAD_H
    add("hinge_pin", (CRADLE_X, y_pos, s["hinge_z"]), (90, 0, 0), explode=(0, 24, 36), iid="hinge_pin_a")
    add("hinge_pin", (CRADLE_X, -y_pos, s["hinge_z"]), (-90, 0, 0), explode=(0, -24, 36), iid="hinge_pin_b")

    add("orrery_arm", (0, 0, s["orrery_z"]), explode=(0, 0, 78))
    add("planet_large", (38, 0, s["orrery_z"] + ORRERY_HUB_H + 0.45), explode=(16, 0, 86))
    add("planet_ringed", (-28, 0, s["orrery_z"] + ORRERY_HUB_H + 0.45), explode=(-16, 0, 84))
    add("retainer_clip", (0, 0, s["groove_z"] + CLIP_SIDE_GAP), explode=(0, 0, 96))

    kinds = [
        "inlay_star", "inlay_crescent", "inlay_hex", "inlay_diamond",
        "inlay_circle", "inlay_star", "inlay_crescent", "inlay_hex",
    ]
    for i, kind in enumerate(kinds):
        ang = i * (math.tau / 8) + math.pi / 8
        x, y = INLAY_RING_R * math.cos(ang), INLAY_RING_R * math.sin(ang)
        radial = np.array([x, y, 0.0])
        radial = radial / np.linalg.norm(radial) * 14.0
        add(kind, (x, y, BASE_H - INLAY_POCKET_D + 0.08), explode=(radial[0], radial[1], 10), iid=f"{kind}_{i}")

    for i in range(4):
        ang = i * (math.pi / 2) + math.pi / 4
        x, y = FOOT_RING_R * math.cos(ang), FOOT_RING_R * math.sin(ang)
        add("tpu_foot", (x, y, -FOOT_PAD_H), explode=(0, 0, -12), iid=f"tpu_foot_{i}")

    add("fit_coupon", (0, 0, 0), scene="bench", iid="fit_coupon")
    add("fit_pin", (0, 0, 0), scene="bench", iid="fit_pin_a")
    add("fit_pin", (0, 0, 0), scene="bench", iid="fit_pin_b")

    print("Checking assembly…")
    issues = file_issues + check_assembly(meshes, instances, s)

    assembly_ids = [inst["id"] for inst in instances if inst["scene"] == "assembly"]
    pts = []
    for inst in instances:
        if inst["scene"] != "assembly":
            continue
        tm = meshes[inst["part_id"]]
        homo = np.hstack([tm.vertices, np.ones((len(tm.vertices), 1))])
        world = (np.array(inst["transform"]) @ homo.T).T[:, :3]
        pts.append(world)
    all_pts = np.vstack(pts)
    lo, hi = all_pts.min(0), all_pts.max(0)
    size = hi - lo
    if np.any(size >= 220):
        issues.append(f"assembled envelope {size.tolist()} is not under 220 mm")

    zip_path = ROOT / "h3c_celestial_observatory_stls.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for stl in sorted(STL_DIR.glob("*.stl")):
            zf.write(stl, arcname=stl.name)

    scene = trimesh.Scene()
    for inst in instances:
        if inst["scene"] != "assembly":
            continue
        geom = meshes[inst["part_id"]].copy()
        scene.add_geometry(geom, node_name=inst["id"], geom_name=inst["id"], transform=np.array(inst["transform"]))
    scene.export(ROOT / "h3c_celestial_observatory.3mf")

    print("Rendering…")
    render_preview(meshes, instances, RENDER_DIR / "preview.png", "H3C Celestial Observatory — CAD, unprinted", 38)
    render_preview(meshes, instances, RENDER_DIR / "preview_alt.png", "H3C Celestial Observatory — other side", 200)

    pivots = [
        {
            "id": "platform_yaw",
            "label": "Deck",
            "type": "revolute",
            "axis": [0, 0, 1],
            "origin_mm": [0, 0, s["platform_z"]],
            "home_deg": 0,
            "limits_deg": [-180, 180],
            "delta_sign": 1,
            "instance_ids": ["rotating_platform", "telescope_tube", "hinge_pin_a", "hinge_pin_b"],
            "actuation": "manual",
        },
        {
            "id": "dome_yaw",
            "label": "Dome",
            "type": "revolute",
            "axis": [0, 0, 1],
            "origin_mm": [0, 0, s["dome_z"]],
            "home_deg": 0,
            "limits_deg": [-180, 180],
            "delta_sign": 1,
            "instance_ids": ["dome"],
            "actuation": "manual",
        },
        {
            "id": "telescope_altitude",
            "label": "Telescope",
            "type": "revolute",
            "axis": [0, 1, 0],
            "origin_mm": [CRADLE_X, 0, s["hinge_z"]],
            "home_deg": HOME_ELEV_DEG,
            "limits_deg": [ELEV_MIN, ELEV_MAX],
            "delta_sign": sign,
            "instance_ids": ["telescope_tube"],
            "actuation": "manual",
            "units": "degrees above the deck, toward +X",
        },
        {
            "id": "orrery_yaw",
            "label": "Orrery",
            "type": "revolute",
            "axis": [0, 0, 1],
            "origin_mm": [0, 0, s["orrery_z"]],
            "home_deg": 0,
            "limits_deg": [-180, 180],
            "delta_sign": 1,
            "instance_ids": ["orrery_arm", "planet_large", "planet_ringed"],
            "actuation": "manual",
        },
    ]

    manifest = {
        "name": "H3C Celestial Observatory",
        "slug": "h3c-celestial-observatory",
        "version": VERSION,
        "units": "mm",
        "up_axis": "Z",
        "rotation_order": "XYZ",
        "description": (
            "Compact mechanical observatory and orrery for a first H3C print: "
            "a drum tower, a deck that turns, a dome in a groove, a tilting telescope "
            "in the shutter opening, and an orrery on the crown."
        ),
        "target_printer": {
            "model": "Bambu Lab H3C Full Combo",
            "nozzle_mm": 0.4,
            "extra_hotends": "seven additional 0.4 mm hotends",
            "bed_mm": [330, 320, 325],
            "bed_source": "https://bambulab.com/en-us/h3c/specs",
            "material_first": "PLA",
            "notes": "0.4 mm only. Do not assign a 0.2, 0.6, or 0.8 mm nozzle. Stock Bambu PLA preset. No custom temperature is published because this has not been printed.",
        },
        "assembled_size_mm": {
            "x": round(float(size[0]), 2),
            "y": round(float(size[1]), 2),
            "z": round(float(size[2]), 2),
            "min_mm": [round(float(v), 2) for v in lo],
            "max_mm": [round(float(v), 2) for v in hi],
            "limit": 220,
            "includes_feet": True,
            "includes_coupon": False,
        },
        "clearances": {
            "units": "mm",
            "note": "CAD design targets. Not physically verified.",
            "axle_diameter": AXLE_D,
            "spin_bore_diameter": AXLE_HOLE_D,
            "orrery_bore_diameter": ORRERY_HOLE_D,
            "hinge_pin_diameter": HINGE_PIN_D,
            "hinge_hole_diameter": HINGE_HOLE_D,
            "dome_skirt_radial_clearance_per_side": GROOVE_RADIAL_CLEAR,
            "dome_skirt_axial_gap": DOME_AXIAL_GAP,
            "inlay_lateral_gap_per_side": INLAY_GAP,
            "deck_above_shelf": BEARING_GAP,
            "retainer_radial_gap": round(RETAINER_INNER_R - GROOVE_ROOT_R, 3),
        },
        "pivots": pivots,
        "assembly_instances": instances,
        "assembly_steps": [
            "Print fit_coupon.stl and learn the Ø4 and Ø8 ladders before any observatory part.",
            "Print the axle, tower, deck, dome, telescope, hinge pins, orrery, and retainer in PLA on a 0.4 mm nozzle.",
            "Seat the axle flange in the base, then the tower peg. The drum carries the deck; the axle only centers it.",
            "Set the deck on the shelf and the dome skirt in the groove. Each should turn by hand.",
            "Cradle the telescope and insert both hinge pins from the outside.",
            "Set the orrery on the shoulder above the crown and slide the retainer into the groove.",
            "Press the eight inlays. Feet are optional TPU.",
        ],
        "parts": [asdict(p) for p in specs],
        "artifacts": {
            "generator": "generate_observatory.py",
            "stl_dir": "stl/",
            "stl_zip": "h3c_celestial_observatory_stls.zip",
            "stl_zip_kind": "individual-part-stls",
            "scene_3mf": "h3c_celestial_observatory.3mf",
            "scene_3mf_kind": "colored-assembly-scene",
            "scene_3mf_note": "Named parts with face colors in assembled position. Not a Bambu Studio plate layout and not sliced as a plate.",
            "preview": "renders/preview.png",
            "preview_alt": "renders/preview_alt.png",
            "readme": "README.md",
            "coupon_stl": "stl/fit_coupon.stl",
        },
        "slice": {
            "sliced": True,
            "slicer": "PrusaSlicer 2.7.4",
            "profile": "Generic FFF 330×320 mm bed, 0.4 mm nozzle, 0.20 mm layers, PLA",
            "parts_with_toolpaths": "19/19",
            "official_h3c_profile": False,
            "physically_tested": False,
            "assembly_3mf_is_plate": False,
            "gcode_distributed": False,
            "summary": (
                "All 19 unique STLs generated toolpaths in PrusaSlicer 2.7.4 using generic "
                "0.4 mm / 0.20 mm PLA, supported where needed; not official H3C profile, not "
                "physically tested; re-slice in Bambu Studio H3C profile; assembly 3MF not plate."
            ),
            "supports_required": ["dome", "telescope_tube", "planet_ringed"],
            "brim_recommended": ["axle_pin", "fit_pin", "hinge_pin", "tower", "planet_large"],
            "planet_ringed": "Brim-only fails with no extrusions in the first layer. Supports required.",
            "tower": "Brim used. Warnings: floating bridge anchors and long bridging extrusions.",
            "tpu_foot": "Path-checked with the PLA profile only, not a TPU profile.",
        },
        "validation": {
            "cad_validated": len(issues) == 0,
            "watertight_checked": True,
            "intersection_checked": True,
            "pivot_alignment_checked": True,
            "print_orientation": "Each STL has its bed face at Z = 0. Assembly poses are only in assembly_instances[].transform.",
            "issues": issues,
            "physically_verified": False,
            "measured": False,
            "printed": False,
            "physically_untested": [
                "H3C shrinkage and hole size with the actual PLA",
                "Whether the design clearances spin freely, stick, or rattle",
                "Dome support scars",
                "PLA-on-PLA wear",
                "TPU 75A feed path",
            ],
        },
        "coupon": {
            "id": "fit_coupon",
            "stl": "stl/fit_coupon.stl",
            "title": "First plate — bridge and fit ladders",
            "purpose": "Print this before the observatory. It is the only part on the first plate.",
            "steps": [
                "Slice only fit_coupon.stl in Bambu Studio with the stock PLA preset and a 0.4 mm PrintTool.",
                "Leave every observatory part off this plate. Do not load a 0.2, 0.6, or 0.8 mm nozzle for it.",
                "The bridge is the 14 mm span on the piers. The holes are ladders, not a passed test.",
                "Try the snap-off Ø8 pin in 8.30, 8.50, 8.70, and 9.00. Try fit_pin (Ø4) in 4.00, 4.20, 4.30, 4.50, and 4.80.",
                "The deck bore is designed for 8.50 and the hinge for 4.30. If those two are wrong for your filament, stop and do not force the assembly.",
            ],
            "checks": [
                {"title": "Ø8.50 hole vs snap-off pin", "result": "not-run"},
                {"title": "Ø4.30 hole vs fit_pin", "result": "not-run"},
                {"title": "14 mm bridge completed", "result": "not-run"},
            ],
        },
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_readme(ROOT / "README.md", s, issues)
    print(f"Envelope mm: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f}")
    print(f"Unique parts: {len(specs)}  instances: {len(assembly_ids)} assembly + bench")
    if issues:
        print("ISSUES")
        for issue in issues:
            print(" !", issue)
        raise SystemExit(1)
    print("CAD checks passed. Unprinted. Not measured.")


if __name__ == "__main__":
    main()
