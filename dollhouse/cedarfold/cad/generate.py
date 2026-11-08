#!/usr/bin/env python3
"""Cedarfold Playhouse — original 1:24 folding cottage.

This is the geometry source. It writes print STLs, assembly STLs, a placed GLB,
validation reports, and preview renders. Style is a warm open-front cottage.
It is not a copy of a purchased plan.

Local wing frame, millimeters:
  +X away from the hinge, +Y toward the play front, +Z up.
  The hinge axis is the local Z axis through the origin.
The hearth wing is mirrored to world -X. The garden wing stays on world +X.
Open is this pose. Closed folds only the garden wing −180° about Z.
"""

from __future__ import annotations

import json
import math
import os
import struct
import zipfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
M = m3d.Manifold

# --- scale and printer -------------------------------------------------------
VERSION = "1.0.0"
SCALE = "1:24"
NOZZLE_MM = 0.4
BED_NOMINAL = (330.0, 320.0, 325.0)
BED_MARGIN = (310.0, 300.0, 315.0)  # X, Y, Z after the print pose

# --- hinge -------------------------------------------------------------------
HINGE_Z0 = 8.0
PITCH = 14.0
KNUCKLE_LEN = 13.50  # 0.50 mm axial gap
PIN_R = 2.0
BORE_SEG = 32
# Vertex radius is larger than the flat radius so the 32-gon flats clear the pin.
BORE_FLAT_R = 2.35
BORE_R = BORE_FLAT_R / math.cos(math.pi / BORE_SEG)
KNUCKLE_R = 5.20
SHROUD_IN = 5.55
SHROUD_OUT = 6.30
BODY_X = 7.2  # structural body stays at local x >= BODY_X

# Module splits sit on knuckle boundaries.
Z_BASE = HINGE_Z0 + 2 * PITCH  # 36, L1 walking surface
Z_L2 = HINGE_Z0 + 9 * PITCH  # 134
Z_L3 = HINGE_Z0 + 16 * PITCH  # 232
Z_HINGE_TOP = HINGE_Z0 + 20 * PITCH  # 288
RISE = Z_L2 - Z_BASE  # 98
N_RISERS = 12
TREAD = 7.5
RUN = N_RISERS * TREAD  # 90
STAIR_W = 42.0
LAND_D = 44.0

# --- plan --------------------------------------------------------------------
WALL = 3.2
POST = 14.0
BACK_Y0 = 3.2
BACK_Y1 = BACK_Y0 + WALL
HALL_Y0 = BACK_Y1
HALL_Y1 = HALL_Y0 + LAND_D
FLIGHT_Y0 = HALL_Y1
FLIGHT_Y1 = FLIGHT_Y0 + RUN
FRONT_STAND = 16.0
FRONT_Y0 = FLIGHT_Y1 + FRONT_STAND
FRONT_Y1 = FRONT_Y0 + WALL

INNER_X0 = BODY_X
INNER_X1 = BODY_X + WALL
STAIR1_X0 = INNER_X1 - 0.6
STAIR1_X1 = STAIR1_X0 + STAIR_W
STAIR2_X0 = STAIR1_X1 + 6.0
STAIR2_X1 = STAIR2_X0 + STAIR_W
FURN_X0 = STAIR2_X1 + 6.0
OUTER_X0 = FURN_X0 + 78.0
OUTER_X1 = OUTER_X0 + WALL

FLOOR_T = 3.6
SKIN = 1.15
ATTIC_CLEAR = 84.0
ATTIC_WALL_Z = Z_L3 + ATTIC_CLEAR
PEAK_Z = ATTIC_WALL_Z + 36.0

# Drawer rail (design values checked again on the meshes).
CAV_X0, CAV_X1 = 32.0, 170.0
CAV_Y0, CAV_Y1 = 24.0, FRONT_Y0 - 1.0
CAV_Z0, CAV_Z1 = 8.2, 31.2
DRAWER_Z0, DRAWER_Z1 = 9.0, 26.4
RELIEF_Z = 31.4
SLAB_Z0 = 32.4
GROOVE_Z0, GROOVE_Z1 = 15.6, 19.2
GROOVE_BACK = 4.0
RUN_Z0, RUN_Z1 = 16.35, 18.45
RUN_STICK = 3.35
LOW_Y0, LOW_Y1 = 40.0, 116.0
NOTCH_Y0, NOTCH_Y1 = 116.0, 156.0
RUN_CLOSED_Y0, RUN_CLOSED_Y1 = 72.0, 104.0
DRAWER_TRAVEL = NOTCH_Y1 - RUN_CLOSED_Y1 - 0.45  # stop remains 0.45 mm past full travel
PANEL_Y0, PANEL_Y1 = 152.0, 170.0
PANEL_CLOSED_FRONT = PANEL_Y1

TENON = 7.6
TENON_LEN = 3.5
SOCKET = 8.6  # 0.50 mm per side
SOCKET_DEPTH = 4.6  # tenon stops 1.1 mm above the socket floor

WOOD = "#c4a06a"
WOOD_DARK = "#8d6844"
CREAM = "#f4ecdf"
DRAWER_C = "#8d877c"
TERR = "#b76e58"
SAGE = "#7f947c"
ROOF_C = "#9a7548"
METAL = "#8e99a4"
ACCENT = "#c9845a"


def knuckle_span(index: int) -> tuple[float, float]:
    z0 = HINGE_Z0 + index * PITCH
    return z0, z0 + KNUCKLE_LEN


def owned_knuckles(z0: float, z1: float, parity: int) -> list[int]:
    found = []
    index = 0
    while True:
        a, b = knuckle_span(index)
        if a >= z1 - 1e-6:
            break
        if index % 2 == parity and a >= z0 - 1e-6 and b <= z1 + 1e-6:
            found.append(index)
        index += 1
        if index > 40:
            raise RuntimeError("knuckle search ran away")
    return found


def box(x: float, y: float, z: float, dx: float, dy: float, dz: float):
    if min(dx, dy, dz) <= 0:
        raise ValueError(f"bad box {(x, y, z, dx, dy, dz)}")
    return M.cube((float(dx), float(dy), float(dz))).translate((float(x), float(y), float(z)))


def cyl_z(x: float, y: float, z: float, radius: float, height: float, n: int = 24):
    return M.cylinder(float(height), float(radius), float(radius), int(n)).translate(
        (float(x), float(y), float(z))
    )


def cyl_x(x: float, y: float, z: float, radius: float, height: float, n: int = 18):
    """Cylinder along X, centered on (x, y, z)."""
    return (
        M.cylinder(float(height), float(radius), float(radius), int(n))
        .rotate((0.0, 90.0, 0.0))
        .translate((float(x) - float(height) / 2.0, float(y), float(z)))
    )


def snap_solid(solid, step: float = 0.01):
    """Snap to a 0.01 mm grid so the float32 STL stays a single watertight body.

    The move is much smaller than the 0.4 mm nozzle and smaller than the design gaps.
    """
    verts, tris = mesh_arrays(solid)
    snapped = np.round(verts / step) * step
    unique, inverse = np.unique(np.round(snapped, 6), axis=0, return_inverse=True)
    mapped = inverse[tris]
    keep = (mapped[:, 0] != mapped[:, 1]) & (mapped[:, 1] != mapped[:, 2]) & (mapped[:, 2] != mapped[:, 0])
    mesh = m3d.Mesh(
        np.ascontiguousarray(unique, dtype=np.float64),
        np.ascontiguousarray(mapped[keep], dtype=np.uint32),
    )
    cleaned = M(mesh)
    if cleaned.status() != m3d.Error.NoError or cleaned.is_empty() or len(cleaned.decompose()) != 1:
        raise RuntimeError(f"snap failed: {cleaned.status()} pieces {len(cleaned.decompose())}")
    return cleaned


def union(parts: list):
    parts = [p for p in parts if p is not None]
    if not parts:
        raise RuntimeError("nothing to union")
    if len(parts) == 1:
        return parts[0]
    return M.batch_boolean(parts, m3d.OpType.Add)


class Builder:
    def __init__(self, label: str):
        self.label = label
        self.plus: list = []
        self.minus: list = []

    def add(self, solid) -> None:
        self.plus.append(solid)

    def cut(self, solid) -> None:
        self.minus.append(solid)

    def build(self):
        solid = union(self.plus)
        if self.minus:
            solid = solid - union(self.minus)
        if solid.status() != m3d.Error.NoError:
            raise RuntimeError(f"{self.label} status {solid.status()}")
        if solid.is_empty() or solid.volume() < 1.0:
            raise RuntimeError(f"{self.label} volume {solid.volume()}")
        pieces = solid.decompose()
        if len(pieces) != 1:
            vols = sorted((round(p.volume(), 1) for p in pieces), reverse=True)
            raise RuntimeError(f"{self.label} has {len(pieces)} bodies, volumes {vols[:8]}")
        return snap_solid(solid)


def add_corner_posts(b: Builder, z0: float, z1: float) -> None:
    h = z1 - z0
    for x, y in (
        (INNER_X0, BACK_Y0),
        (OUTER_X1 - POST, BACK_Y0),
        (INNER_X0, FRONT_Y1 - POST),
        (OUTER_X1 - POST, FRONT_Y1 - POST),
    ):
        b.add(box(x, y, z0, POST, POST, h))


def post_centers() -> list[tuple[float, float]]:
    return [
        (INNER_X0 + POST / 2, BACK_Y0 + POST / 2),
        (OUTER_X1 - POST / 2, BACK_Y0 + POST / 2),
        (INNER_X0 + POST / 2, FRONT_Y1 - POST / 2),
        (OUTER_X1 - POST / 2, FRONT_Y1 - POST / 2),
    ]


def add_tenons(b: Builder, z_top: float) -> None:
    """Keys pointing down from a module bottom at z_top. They overlap the module by 0.4."""
    for x, y in post_centers():
        b.add(box(x - TENON / 2, y - TENON / 2, z_top - TENON_LEN, TENON, TENON, TENON_LEN + 0.4))


def cut_sockets(b: Builder, z_top: float) -> None:
    for x, y in post_centers():
        b.cut(
            box(
                x - SOCKET / 2,
                y - SOCKET / 2,
                z_top - SOCKET_DEPTH,
                SOCKET,
                SOCKET,
                SOCKET_DEPTH + 0.4,
            )
        )


def add_walls(b: Builder, z0: float, z1: float, front_h: float, front_open: bool) -> None:
    h = z1 - z0
    b.add(box(INNER_X0, BACK_Y0, z0, WALL, FRONT_Y1 - BACK_Y0, h))
    b.add(box(OUTER_X0, BACK_Y0, z0, WALL, FRONT_Y1 - BACK_Y0, h))
    b.add(box(INNER_X0, BACK_Y0, z0, OUTER_X1 - INNER_X0, WALL, h))
    if front_open:
        b.add(box(INNER_X0, FRONT_Y0, z0, OUTER_X1 - INNER_X0, WALL, front_h))
        # Railing posts and handrail above the sill, still open for play.
        rail_z = z0 + front_h
        rail_top = z0 + min(h, front_h + 18.0)
        y = FRONT_Y0
        x = INNER_X0 + 4.0
        while x < OUTER_X1 - 6.0:
            b.add(box(x, y, z0 + front_h - 1.0, 3.2, WALL, rail_top - (z0 + front_h - 1.0)))
            x += 16.0
        b.add(box(INNER_X0, y, rail_top - 2.4, OUTER_X1 - INNER_X0, WALL, 2.4))
    else:
        b.add(box(INNER_X0, FRONT_Y0, z0, OUTER_X1 - INNER_X0, WALL, h))
    add_corner_posts(b, z0, z1)


def add_siding(b: Builder, z0: float, z1: float) -> None:
    z = z0 + 8.0
    while z < z1 - 6.0:
        # Overlap 0.3 mm into the outer face so the rib is one solid with the wall.
        b.add(box(OUTER_X1 - 0.3, BACK_Y0 + 1.0, z, 0.9, FRONT_Y1 - BACK_Y0 - 2.0, 2.0))
        b.add(box(INNER_X0 + 1.0, BACK_Y0 - 0.6, z, OUTER_X1 - INNER_X0 - 2.0, 0.9, 2.0))
        z += 14.0


def add_wainscot(b: Builder, z_floor: float) -> None:
    z = z_floor + 0.2
    h = 26.0
    t = 0.8
    b.add(box(INNER_X1 - 0.2, HALL_Y1, z, t, FRONT_Y0 - HALL_Y1, h))
    b.add(box(OUTER_X0 - t + 0.2, BACK_Y1, z, t, FRONT_Y0 - BACK_Y1, h))
    b.add(box(INNER_X1, BACK_Y1 - 0.2, z, OUTER_X0 - INNER_X1, t, h))


def add_cornice(b: Builder, z_ceil: float) -> None:
    """Raised band plus a bead row. The beads are the lace, above the keys."""
    t = 2.2
    z = z_ceil - t
    b.add(box(INNER_X1 - 0.2, BACK_Y1, z, t, FRONT_Y0 - BACK_Y1, t))
    b.add(box(OUTER_X0 - t + 0.2, BACK_Y1, z, t, FRONT_Y0 - BACK_Y1, t))
    b.add(box(INNER_X1, BACK_Y1 - 0.2, z, OUTER_X0 - INNER_X1, t, t))
    y = BACK_Y1 + 6.0
    while y < FRONT_Y0 - 4.0:
        b.add(cyl_z(INNER_X1 + 0.4, y, z - 0.2, 1.35, 2.4, 10))
        b.add(cyl_z(OUTER_X0 - 0.4, y, z - 0.2, 1.35, 2.4, 10))
        y += 9.0
    x = INNER_X1 + 8.0
    while x < OUTER_X0 - 4.0:
        b.add(cyl_z(x, BACK_Y1 + 0.4, z - 0.2, 1.35, 2.4, 10))
        x += 9.0


def extrude_xz(polygon: list[tuple[float, float]], y0: float, y1: float):
    """Polygon in the XZ plane, extruded along Y from y0 to y1."""
    return extrude_xz_cs(m3d.CrossSection([polygon]), y0, y1)


def extrude_xz_cs(section, y0: float, y1: float):
    depth = y1 - y0
    solid = M.extrude(section, depth).rotate((90.0, 0.0, 0.0))
    return solid.translate((0.0, y0 + depth, 0.0))


def extrude_yz(polygon: list[tuple[float, float]], x0: float, x1: float):
    """Polygon in the YZ plane, extruded along X from x0 to x1."""
    solid = M.extrude(m3d.CrossSection([polygon]), x1 - x0)
    return solid.transform([[0.0, 0.0, 1.0, x0], [1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]])


def cyl_y(x: float, y: float, z: float, radius: float, height: float, n: int = 18):
    """Cylinder along +Y, starting at y."""
    return (
        M.cylinder(float(height), float(radius), float(radius), int(n))
        .rotate((-90.0, 0.0, 0.0))
        .translate((float(x), float(y), float(z)))
    )


def add_window(b: Builder, *, x0, x1, y0, y1, z0, z1, trim: float = 2.6) -> None:
    """Opening through a back wall. y0–y1 is the thin wall; the hole is in X and Z."""
    frame = 3.2
    b.add(box(x0 - frame, y0 - 1.05, z0 - frame, (x1 - x0) + 2 * frame, 1.45, (z1 - z0) + 2 * frame))
    b.cut(box(x0, y0 - 1.4, z0, x1 - x0, (y1 - y0) + 2.8, z1 - z0))
    b.add(box(x0 - 1.4, y0 - 1.7, z0 - 2.4, (x1 - x0) + 2.8, (y1 - y0) + 3.4, 2.6))


def add_window_x(b: Builder, *, x, y0, y1, z0, z1, outward: float) -> None:
    """Window through a wall of constant X. outward +1 grows trim toward +X."""
    trim = 2.6
    frame = 3.0
    wall_pad = 1.6
    b.add(box(x - (0.4 if outward < 0 else -0.9), y0 - frame, z0 - frame, 1.3, (y1 - y0) + 2 * frame, (z1 - z0) + 2 * frame))
    b.cut(box(x - wall_pad, y0, z0, WALL + 2 * wall_pad, y1 - y0, z1 - z0))
    # Sill.
    b.add(box(x - 0.4, y0 - 1.2, z0 - 2.4, WALL + 2.2, (y1 - y0) + 2.4, 2.6))


def floor_with_well(z: float, thickness: float, well: tuple[float, float, float, float] | None):
    slab = box(INNER_X0, BACK_Y0, z, OUTER_X1 - INNER_X0, FRONT_Y1 - BACK_Y0, thickness)
    if well:
        x0, x1, y0, y1 = well
        slab = slab - box(x0, y0, z - 0.3, x1 - x0, y1 - y0, thickness + 0.6)
    return slab


def cut_planks(b: Builder, z_top: float, skip: tuple[float, float, float, float] | None) -> None:
    """Shallow grooves in a finish floor. They do not pass through the skin."""
    y = HALL_Y0 + 4.0
    while y < FRONT_Y0 - 4.0:
        groove = box(FURN_X0, y, z_top - 0.38, OUTER_X0 - FURN_X0 - 2.0, 0.7, 0.5)
        b.cut(groove)
        y += 8.0


def stair_mass(x0: float, x1: float, z_low: float, z_high: float):
    """Solid stair. Low end at the front (large Y), high end at the hall."""
    rise = (z_high - z_low) / N_RISERS
    run = (FLIGHT_Y1 - FLIGHT_Y0) / N_RISERS
    steps = []
    for i in range(N_RISERS):
        y_front = FLIGHT_Y1 - i * run
        y_back = FLIGHT_Y1 - (i + 1) * run
        z_hi = z_low + (i + 1) * rise
        steps.append(box(x0, y_back - 0.45, z_low, x1 - x0, (y_front - y_back) + 0.45, z_hi - z_low))
    return union(steps)


def add_hinge_hardware(b: Builder, z0: float, z1: float, parity: int, pin_seat: bool) -> None:
    for index in owned_knuckles(z0, z1, parity):
        a, c = knuckle_span(index)
        b.add(cyl_z(0.0, 0.0, a, KNUCKLE_R, c - a, 28))
        # Bridge into the inner wall. Stays at local +X, so the two wings' bridges never meet.
        # Stay at y >= -1 so a 180° fold cannot swing this bridge into the other wing.
        b.add(box(0.8, -1.0, a, BODY_X + 1.2, 9.0, c - a))
        shroud = cyl_z(0.0, 0.0, a, SHROUD_OUT, c - a, 28) - cyl_z(0.0, 0.0, a - 0.2, SHROUD_IN, c - a + 0.4, 28)
        # Keep the rear half, which is the side away from the rooms.
        shroud = shroud ^ box(-8.0, -8.0, a - 0.1, 16.0, 8.2, c - a + 0.2)
        b.add(shroud)
        b.cut(cyl_z(0.0, 0.0, a - 0.15, BORE_R, c - a + 0.3, BORE_SEG))
    if pin_seat:
        # Closed bottom of the bore. The pin rests here. It is not a friction fit.
        b.add(cyl_z(0.0, 0.0, HINGE_Z0 - 2.2, KNUCKLE_R, 2.2, 28))
        b.add(box(0.8, -1.0, HINGE_Z0 - 2.2, BODY_X + 1.2, 9.0, 2.2))


def add_channel(b: Builder, z_floor: float, z_ceil: float) -> None:
    """Open 5 V race on the back wall. A groove, not a wire and not a closed tunnel."""
    z = z_floor + 52.0
    if z > z_ceil - 10.0:
        return
    # Clear of the corner posts. Open through the room face of the back wall.
    b.cut(box(FURN_X0, BACK_Y1 - 1.6, z_floor + 12.0, 8.0, 2.4, z - z_floor - 6.0))
    b.cut(box(FURN_X0, BACK_Y1 - 1.6, z, OUTER_X0 - FURN_X0 - 8.0, 2.4, 5.0))


def loop_pocket(b: Builder) -> None:
    """Slack-loop seat on the rear of the base, next to the hinge, not on the swinging front."""
    b.cut(box(BODY_X, 0.4, 10.0, 10.0, 2.6, 16.0))
    b.cut(cyl_z(BODY_X + 8.0, 2.0, 12.0, 6.5, 12.0, 20))


# --- furniture, fused to the module so each STL stays one body ---------------
def add_kitchen(b: Builder, z: float) -> None:
    counter_h = 30.0
    b.add(box(FURN_X0 + 8.0, HALL_Y0 + 2.0, z, OUTER_X0 - (FURN_X0 + 8.0) + 0.5, 78.0, counter_h))
    # Sink basin, floor of the basin left in.
    b.cut(box(OUTER_X0 - 32.0, HALL_Y0 + 36.0, z + counter_h - 7.0, 20.0, 26.0, 9.0))
    b.add(cyl_z(OUTER_X0 - 22.0, HALL_Y0 + 18.0, z + counter_h - 1.0, 1.4, 14.0, 12))
    b.add(box(OUTER_X0 - 26.0, HALL_Y0 + 16.0, z + counter_h + 11.0, 12.0, 6.0, 2.2))
    # Stove, four coils and an oven band.
    sx, sy = FURN_X0 + 14.0, HALL_Y0 + 6.0
    b.add(box(sx, sy, z, 36.0, 32.0, counter_h))
    for i in range(2):
        for j in range(2):
            b.add(cyl_z(sx + 10 + i * 16, sy + 9 + j * 14, z + counter_h - 0.4, 5.2, 1.5, 14))
    b.add(box(sx + 4.0, sy + 2.0, z + 4.0, 28.0, 1.2, 16.0))
    # Upper cabinet on the outer wall.
    b.add(box(OUTER_X0 - 18.0, HALL_Y0 + 8.0, z + 62.0, 18.4, 52.0, 28.0))
    # Door recess, open on the room face of the cabinet.
    b.cut(box(OUTER_X0 - 18.4, HALL_Y0 + 14.0, z + 68.0, 8.0, 40.0, 16.0))
    # Table and two stools, fused through the finish floor.
    b.add(box(FURN_X0 + 6.0, FLIGHT_Y0 + 8.0, z, 28.0, 22.0, 2.0))
    for dx, dy in ((2, 2), (22, 2), (2, 16), (22, 16)):
        b.add(box(FURN_X0 + 6.0 + dx, FLIGHT_Y0 + 8.0 + dy, z, 3.0, 3.0, 20.0))
    b.add(box(FURN_X0 + 4.0, FLIGHT_Y0 + 6.0, z + 20.0, 32.0, 26.0, 2.4))
    b.add(cyl_z(FURN_X0 + 20.0, FLIGHT_Y0 + 18.0, z + 22.2, 1.2, 10.0, 10))
    b.add(cyl_z(FURN_X0 + 20.0, FLIGHT_Y0 + 18.0, z + 32.0, 4.5, 3.2, 12))


def add_bedroom(b: Builder, z: float) -> None:
    # Bed against the outer wall.
    b.add(box(FURN_X0 + 4.0, HALL_Y1 + 4.0, z, OUTER_X0 - FURN_X0 - 2.0, 64.0, 8.0))
    b.add(box(FURN_X0 + 6.0, HALL_Y1 + 8.0, z + 8.0, OUTER_X0 - FURN_X0 - 8.0, 56.0, 6.0))
    b.add(box(OUTER_X0 - 16.0, HALL_Y1 + 6.0, z + 8.0, 16.5, 60.0, 16.0))  # headboard into the wall
    b.add(box(FURN_X0 + 8.0, HALL_Y1 + 46.0, z + 14.0, 24.0, 14.0, 4.0))  # pillow
    # Nightstand and lamp.
    b.add(box(FURN_X0 + 2.0, HALL_Y0 + 4.0, z, 22.0, 18.0, 16.0))
    b.add(cyl_z(FURN_X0 + 13.0, HALL_Y0 + 13.0, z + 16.0, 1.3, 12.0, 10))
    b.add(cyl_z(FURN_X0 + 13.0, HALL_Y0 + 13.0, z + 27.5, 5.0, 4.0, 12))
    # Rug border, a raised edge fused to the skin.
    b.add(box(FURN_X0 + 2.0, FLIGHT_Y0 + 2.0, z, 4.0, 36.0, 0.9))
    b.add(box(FURN_X0 + 2.0, FLIGHT_Y0 + 2.0, z, 40.0, 4.0, 0.9))


def add_parlor(b: Builder, z: float) -> None:
    # Sofa against the back wall.
    b.add(box(FURN_X0, BACK_Y1 - 0.4, z, OUTER_X0 - FURN_X0, 28.0, 12.0))
    b.add(box(FURN_X0 + 2.0, BACK_Y1, z + 12.0, OUTER_X0 - FURN_X0 - 4.0, 8.0, 14.0))
    b.add(box(FURN_X0, BACK_Y1 + 6.0, z + 8.0, 4.0, 20.0, 10.0))
    b.add(box(OUTER_X0 - 4.5, BACK_Y1 + 6.0, z + 8.0, 4.5, 20.0, 10.0))
    # Table.
    b.add(box(FURN_X0 + 18.0, HALL_Y1 + 6.0, z, 3.0, 3.0, 18.0))
    b.add(box(FURN_X0 + 40.0, HALL_Y1 + 6.0, z, 3.0, 3.0, 18.0))
    b.add(box(FURN_X0 + 18.0, HALL_Y1 + 24.0, z, 3.0, 3.0, 18.0))
    b.add(box(FURN_X0 + 40.0, HALL_Y1 + 24.0, z, 3.0, 3.0, 18.0))
    b.add(box(FURN_X0 + 14.0, HALL_Y1 + 2.0, z + 18.0, 32.0, 28.0, 2.4))
    # Floor lamp in the corner, fused to the skin and the wall.
    b.add(cyl_z(OUTER_X0 - 8.0, FRONT_Y0 - 16.0, z, 3.2, 2.0, 12))
    b.add(cyl_z(OUTER_X0 - 8.0, FRONT_Y0 - 16.0, z, 1.2, 48.0, 10))
    b.add(cyl_z(OUTER_X0 - 8.0, FRONT_Y0 - 16.0, z + 48.0, 5.5, 6.0, 14))


def add_bath(b: Builder, z: float) -> None:
    # Tub against the outer wall, hollow.
    b.add(box(OUTER_X0 - 36.0, HALL_Y1 + 2.0, z, 36.4, 62.0, 18.0))
    b.cut(box(OUTER_X0 - 32.0, HALL_Y1 + 6.0, z + 6.0, 24.0, 54.0, 14.0))
    # Basin.
    b.add(box(FURN_X0 + 4.0, HALL_Y0 + 2.0, z, 12.0, 12.0, 16.0))
    b.add(cyl_z(FURN_X0 + 14.0, HALL_Y0 + 14.0, z + 16.0, 8.0, 5.0, 16))
    b.cut(cyl_z(FURN_X0 + 14.0, HALL_Y0 + 14.0, z + 18.0, 5.5, 4.0, 14))
    b.add(cyl_z(FURN_X0 + 14.0, HALL_Y0 + 8.0, z + 20.0, 1.0, 8.0, 8))
    # Toilet.
    b.add(box(FURN_X0 + 2.0, FRONT_Y0 - 36.0, z, 22.0, 28.0, 14.0))
    b.add(box(FURN_X0 + 2.0, FRONT_Y0 - 16.0, z + 14.0, 18.0, 12.0, 12.0))
    # Tile grooves in a tall wainscot on the outer wall. Stay clear of the corner posts
    # so the grooves open into the room instead of becoming enclosed voids.
    b.add(box(OUTER_X0 - 1.2, BACK_Y0 + POST, z, 1.5, FRONT_Y1 - BACK_Y0 - 2 * POST, 42.0))
    yy = BACK_Y0 + POST + 2.0
    while yy < FRONT_Y1 - POST - 4.0:
        b.cut(box(OUTER_X0 - 2.6, yy, z + 6.0, 2.4, 0.8, 30.0))
        yy += 6.0


def add_attic_room(b: Builder, z: float) -> None:
    b.add(box(FURN_X0 + 6.0, FLIGHT_Y0 + 8.0, z, 48.0, 36.0, 7.0))
    b.add(box(FURN_X0 + 6.0, FLIGHT_Y0 + 8.0, z + 7.0, 48.0, 8.0, 10.0))
    b.add(box(FURN_X0 + 10.0, FLIGHT_Y0 + 28.0, z + 7.0, 16.0, 10.0, 3.0))
    # Trunk.
    b.add(box(FURN_X0 + 8.0, HALL_Y0 + 4.0, z, 30.0, 16.0, 12.0))
    b.add(box(FURN_X0 + 8.0, HALL_Y0 + 4.0, z + 11.2, 30.0, 16.0, 1.4))


def add_terrace(b: Builder, z: float) -> None:
    b.add(box(FURN_X0 + 8.0, FLIGHT_Y1 - 10.0, z, 28.0, 18.0, 12.0))  # planter
    b.add(box(FURN_X0 + 12.0, FLIGHT_Y1 - 6.0, z + 12.0, 20.0, 12.0, 6.0))
    b.cut(box(FURN_X0 + 14.0, FLIGHT_Y1 - 4.0, z + 14.0, 16.0, 8.0, 6.0))
    b.add(box(OUTER_X0 - 28.0, HALL_Y1 + 8.0, z, 22.0, 16.0, 14.0))  # bench base
    b.add(box(OUTER_X0 - 30.0, HALL_Y1 + 6.0, z + 14.0, 26.0, 20.0, 2.2))


def add_gable_roof(b: Builder, wall_top: float) -> None:
    """Ridge runs front to back. The hinge-side eave is flush. The outer eave overhangs.

    The back wall carries the gable. The play front stays open under the roof.
    """
    peak_x = (INNER_X1 + OUTER_X0) * 0.5
    z_eave = wall_top - 1.4
    z_peak = PEAK_Z
    # CCW in the XZ plane. The attic is the region under the slopes.
    outer = [(INNER_X0, z_eave), (OUTER_X1 + 7.0, z_eave), (peak_x, z_peak)]
    inner = [(INNER_X0 + 14.0, z_eave + 3.4), (OUTER_X1 - 6.0, z_eave + 3.4), (peak_x, z_peak - 6.0)]
    shell = m3d.CrossSection([outer]) - m3d.CrossSection([inner])
    if shell.is_empty():
        raise RuntimeError("gable roof profile is empty")
    # Inset from the back face so the roof does not share that exterior plane.
    b.add(extrude_xz_cs(shell, BACK_Y0 + 0.35, FRONT_Y1 + 6.0))
    b.add(box(INNER_X0, BACK_Y0 + 0.35, z_eave - 0.6, WALL + 1.6, FRONT_Y0 - BACK_Y0 - 0.35, 2.4))
    b.add(box(OUTER_X0 - 1.0, BACK_Y0 + 0.35, z_eave - 0.6, WALL + 8.0, FRONT_Y0 - BACK_Y0 - 0.35, 2.4))
    b.add(extrude_xz(
        [(INNER_X0, z_eave - 0.6), (OUTER_X1, z_eave - 0.6), (peak_x, z_peak + 0.4)],
        BACK_Y0 + 0.35,
        BACK_Y1 - 0.15,
    ))
    # Round window through the back gable only. Kept clear of the roof shell.
    b.cut(cyl_y(peak_x, BACK_Y0 - 1.5, z_eave + 10.0, 5.5, WALL + 4.0, 18))


def add_terrace_roof(b: Builder, wall_top: float) -> None:
    """Shed over the rear half. The front of this storey is the open terrace."""
    y_cut = FLIGHT_Y0 + 16.0
    z_hi = wall_top - 6.0
    z_lo = Z_L3 + 46.0
    # CCW in the YZ plane. Inset from the back face and from the outer wall faces.
    outer = [(BACK_Y0 + 0.4, z_hi - 4.6), (y_cut + 8.0, z_lo - 4.0), (y_cut + 8.0, z_lo), (BACK_Y0 + 0.4, z_hi)]
    b.add(extrude_yz(outer, INNER_X0 + 0.45, OUTER_X1 - 0.45))


def add_balcony(b: Builder, z: float) -> None:
    """Outer-wall balcony on the hearth attic. Floor ties into the wall."""
    y0 = HALL_Y1 + 6.0
    y1 = y0 + 62.0
    b.add(box(OUTER_X1 - 0.8, y0, z, 30.0, y1 - y0, 3.2))
    # Rails.
    b.add(box(OUTER_X1 + 26.0, y0, z, 2.4, y1 - y0, 18.0))
    b.add(box(OUTER_X0, y0, z, 32.0, 2.4, 18.0))
    b.add(box(OUTER_X0, y1 - 2.4, z, 32.0, 2.4, 18.0))
    b.add(box(OUTER_X1 + 24.0, y0, z + 16.0, 4.0, y1 - y0, 2.2))
    # Door through the outer wall.
    b.cut(box(OUTER_X0 - 1.0, y0 + 12.0, z, WALL + 2.4, 32.0, 58.0))
    b.add(box(OUTER_X0 - 0.4, y0 + 8.0, z, 1.4, 4.0, 62.0))
    b.add(box(OUTER_X0 - 0.4, y0 + 44.0, z, 1.4, 4.0, 62.0))
    b.add(box(OUTER_X0 - 0.4, y0 + 8.0, z + 58.0, 1.4, 40.0, 4.0))


def build_base(parity: int, pin_seat: bool):
    b = Builder(f"base-{parity}")
    # Bottom plate, walls, top slab.
    b.add(box(INNER_X0, BACK_Y0, 0.0, OUTER_X1 - INNER_X0, FRONT_Y1 - BACK_Y0, 6.0))
    b.add(box(INNER_X0, BACK_Y0, 0.0, WALL, FRONT_Y1 - BACK_Y0, Z_BASE))
    b.add(box(OUTER_X0, BACK_Y0, 0.0, WALL, FRONT_Y1 - BACK_Y0, Z_BASE))
    b.add(box(INNER_X0, BACK_Y0, 0.0, OUTER_X1 - INNER_X0, WALL, Z_BASE))
    b.add(box(INNER_X0, FRONT_Y0, 0.0, OUTER_X1 - INNER_X0, WALL, Z_BASE))
    b.add(box(INNER_X0, BACK_Y0, SLAB_Z0, OUTER_X1 - INNER_X0, FRONT_Y1 - BACK_Y0, Z_BASE - SLAB_Z0))
    add_corner_posts(b, 0.0, Z_BASE)
    # Cheeks beside the drawer. The grooves are cut into these, so the runners are captured.
    b.add(box(CAV_X0 - 8.0, CAV_Y0, 6.0, 8.0, FRONT_Y0 - CAV_Y0, SLAB_Z0 - 6.0))
    b.add(box(CAV_X1, CAV_Y0, 6.0, 8.0, FRONT_Y0 - CAV_Y0, SLAB_Z0 - 6.0))
    add_siding(b, 6.0, Z_BASE - 2.0)
    add_hinge_hardware(b, 0.0, Z_BASE, parity, pin_seat)
    cut_sockets(b, Z_BASE)
    # Drawer cavity, rails, and the lift relief over the extended position.
    b.cut(box(CAV_X0, CAV_Y0, CAV_Z0, CAV_X1 - CAV_X0, CAV_Y1 - CAV_Y0, CAV_Z1 - CAV_Z0))
    # Grooves. Low ceiling, then a taller notch at the front of the groove.
    b.cut(box(CAV_X0 - GROOVE_BACK, LOW_Y0, GROOVE_Z0, GROOVE_BACK + 0.6, LOW_Y1 - LOW_Y0, GROOVE_Z1 - GROOVE_Z0))
    b.cut(box(CAV_X1 - 0.6, LOW_Y0, GROOVE_Z0, GROOVE_BACK + 0.6, LOW_Y1 - LOW_Y0, GROOVE_Z1 - GROOVE_Z0))
    b.cut(box(CAV_X0 - GROOVE_BACK, NOTCH_Y0, GROOVE_Z0, GROOVE_BACK + 0.6, NOTCH_Y1 - NOTCH_Y0, RELIEF_Z - GROOVE_Z0))
    b.cut(box(CAV_X1 - 0.6, NOTCH_Y0, GROOVE_Z0, GROOVE_BACK + 0.6, NOTCH_Y1 - NOTCH_Y0, RELIEF_Z - GROOVE_Z0))
    # Front opening the drawer face passes through. Overlaps the cavity so no lip remains.
    b.cut(
        box(
            CAV_X0 - 1.0,
            CAV_Y1 - 2.0,
            CAV_Z0 - 0.6,
            CAV_X1 - CAV_X0 + 2.0,
            FRONT_Y1 - CAV_Y1 + 4.0,
            RELIEF_Z - CAV_Z0 + 1.0,
        )
    )
    loop_pocket(b)
    add_casters_cuts(b)
    # Plank grooves on the structural top, shallow.
    y = HALL_Y0 + 3.0
    while y < FRONT_Y0 - 4.0:
        b.cut(box(STAIR2_X1 + 2.0, y, Z_BASE - 0.42, OUTER_X0 - STAIR2_X1 - 6.0, 0.65, 0.55))
        y += 8.0
    return b.build()


def caster_centers() -> list[tuple[float, float, str]]:
    return [
        (26.0, 28.0, "brake"),
        (OUTER_X0 - 8.0, 28.0, "brake"),
        (26.0, FRONT_Y0 - 22.0, "free"),
        (OUTER_X0 - 8.0, FRONT_Y0 - 22.0, "free"),
    ]


def add_casters_cuts(b: Builder) -> None:
    for x, y, _kind in caster_centers():
        b.cut(box(x - 15.0, y - 15.0, 0.0, 30.0, 30.0, 2.35))
        for dx in (-9.0, 9.0):
            for dy in (-9.0, 9.0):
                b.cut(cyl_z(x + dx, y + dy, 0.0, 2.15, 6.2, 14))


def build_drawer():
    b = Builder("drawer")
    # Body and a front panel that stays in the front opening when closed.
    b.add(box(CAV_X0 + 0.55, 46.0, DRAWER_Z0, CAV_X1 - CAV_X0 - 1.1, PANEL_Y0 - 46.0 + 6.0, DRAWER_Z1 - DRAWER_Z0))
    b.add(
        box(
            CAV_X0 + 2.0,
            PANEL_Y0,
            DRAWER_Z0 + 0.4,
            CAV_X1 - CAV_X0 - 4.0,
            PANEL_Y1 - PANEL_Y0,
            DRAWER_Z1 - DRAWER_Z0 - 0.6,
        )
    )
    # Finger pull.
    b.add(box(CAV_X0 + 28.0, PANEL_Y1 - 2.4, 14.0, CAV_X1 - CAV_X0 - 56.0, 6.0, 8.0))
    # Runners. Closed position is the mesh position.
    ry0, ry1 = RUN_CLOSED_Y0, RUN_CLOSED_Y1
    b.add(box(CAV_X0 + 0.55 - RUN_STICK, ry0, RUN_Z0, RUN_STICK + 0.4, ry1 - ry0, RUN_Z1 - RUN_Z0))
    b.add(box(CAV_X1 - 0.55 - 0.4, ry0, RUN_Z0, RUN_STICK + 0.4, ry1 - ry0, RUN_Z1 - RUN_Z0))
    # Interior partitions so it does not read as an empty trough only.
    b.add(box(CAV_X0 + 8.0, 80.0, CAV_Z0 + 0.7, 1.4, 40.0, 8.0))
    return b.build()


def build_ground(parity: int, furn):
    # Dedicated function so the slab logic stays obvious.
    z0, z1 = Z_BASE, Z_L2
    b = Builder(f"ground-{parity}")
    add_walls(b, z0, z1, front_h=20.0, front_open=True)
    add_siding(b, z0 + 4.0, z1 - 8.0)
    add_tenons(b, z0)
    b.add(floor_with_well(z0, SKIN, None))
    cut_planks(b, z0 + SKIN, None)
    b.add(stair_mass(STAIR1_X0, STAIR1_X1, z0, z1))
    b.add(floor_with_well(z1 - FLOOR_T, FLOOR_T, (STAIR1_X0 - 0.3, STAIR1_X1 + 0.3, FLIGHT_Y0, FLIGHT_Y1 + 0.2)))
    cut_sockets(b, z1)
    add_wainscot(b, z0)
    add_cornice(b, z1 - FLOOR_T)
    add_channel(b, z0, z1)
    add_hinge_hardware(b, z0, z1, parity, False)
    add_window_x(b, x=OUTER_X0, y0=FLIGHT_Y0 + 6.0, y1=FLIGHT_Y0 + 34.0, z0=z0 + 24.0, z1=z0 + 60.0, outward=1)
    add_window(b, x0=FURN_X0 + 10.0, x1=FURN_X0 + 40.0, y0=BACK_Y0 - 0.5, y1=BACK_Y1 + 1.0, z0=z0 + 28.0, z1=z0 + 56.0)
    furn(b, z0)
    return b.build()


def build_upper(parity: int, furn):
    z0, z1 = Z_L2, Z_L3
    b = Builder(f"upper-{parity}")
    add_walls(b, z0, z1, front_h=22.0, front_open=True)
    add_siding(b, z0 + 4.0, z1 - 8.0)
    add_tenons(b, z0)
    b.add(floor_with_well(z0, SKIN, (STAIR1_X0 - 0.3, STAIR1_X1 + 0.3, FLIGHT_Y0, FLIGHT_Y1 + 0.2)))
    cut_planks(b, z0 + SKIN, None)
    b.add(stair_mass(STAIR2_X0, STAIR2_X1, z0, z1))
    b.add(floor_with_well(z1 - FLOOR_T, FLOOR_T, (STAIR2_X0 - 0.3, STAIR2_X1 + 0.3, FLIGHT_Y0, FLIGHT_Y1 + 0.2)))
    cut_sockets(b, z1)
    add_wainscot(b, z0)
    add_cornice(b, z1 - FLOOR_T)
    add_channel(b, z0, z1)
    add_hinge_hardware(b, z0, z1, parity, False)
    add_window_x(b, x=OUTER_X0, y0=HALL_Y1 + 4.0, y1=HALL_Y1 + 30.0, z0=z0 + 22.0, z1=z0 + 52.0, outward=1)
    add_window(b, x0=FURN_X0 + 8.0, x1=FURN_X0 + 36.0, y0=BACK_Y0 - 0.5, y1=BACK_Y1 + 1.0, z0=z0 + 26.0, z1=z0 + 50.0)
    furn(b, z0)
    return b.build()


def build_attic(parity: int, terrace: bool):
    z0 = Z_L3
    z1 = ATTIC_WALL_Z
    b = Builder(f"attic-{parity}")
    # Rear and side walls. Front is a railing. Terrace wing steps the side walls down.
    if terrace:
        y_split = FLIGHT_Y0 + 16.0
        b.add(box(INNER_X0, BACK_Y0, z0, WALL, FRONT_Y1 - BACK_Y0, 28.0))
        b.add(box(OUTER_X0, BACK_Y0, z0, WALL, FRONT_Y1 - BACK_Y0, 28.0))
        b.add(box(INNER_X0, BACK_Y0, z0, WALL, y_split - BACK_Y0, z1 - z0))
        b.add(box(OUTER_X0, BACK_Y0, z0, WALL, y_split - BACK_Y0, z1 - z0))
        b.add(box(INNER_X0, BACK_Y0, z0, OUTER_X1 - INNER_X0, WALL, z1 - z0))
        b.add(box(INNER_X0, FRONT_Y0, z0, OUTER_X1 - INNER_X0, WALL, 24.0))
        x = INNER_X0 + 4.0
        while x < OUTER_X1 - 6.0:
            b.add(box(x, FRONT_Y0, z0 + 20.0, 3.2, WALL, 16.0))
            x += 16.0
        b.add(box(INNER_X0, FRONT_Y0, z0 + 34.0, OUTER_X1 - INNER_X0, WALL, 2.4))
        add_corner_posts(b, z0, z0 + 28.0)
        b.add(box(INNER_X0, BACK_Y0, z0, POST, POST, z1 - z0))
        b.add(box(OUTER_X1 - POST, BACK_Y0, z0, POST, POST, z1 - z0))
    else:
        add_walls(b, z0, z1, front_h=18.0, front_open=True)
    add_siding(b, z0 + 4.0, z0 + 70.0)
    add_tenons(b, z0)
    b.add(floor_with_well(z0, SKIN, (STAIR2_X0 - 0.3, STAIR2_X1 + 0.3, FLIGHT_Y0, FLIGHT_Y1 + 0.2)))
    cut_planks(b, z0 + SKIN, None)
    add_wainscot(b, z0)
    add_hinge_hardware(b, z0, min(z1, Z_HINGE_TOP), parity, False)
    add_channel(b, z0, z0 + 70.0)
    if terrace:
        add_terrace_roof(b, ATTIC_WALL_Z)
        add_terrace(b, z0)
        add_window_x(b, x=OUTER_X0, y0=HALL_Y0 + 8.0, y1=HALL_Y0 + 30.0, z0=z0 + 20.0, z1=z0 + 46.0, outward=1)
    else:
        add_gable_roof(b, ATTIC_WALL_Z)
        add_balcony(b, z0)
        add_attic_room(b, z0)
        add_window(b, x0=FURN_X0 + 12.0, x1=FURN_X0 + 36.0, y0=BACK_Y0 - 0.5, y1=BACK_Y1 + 1.0, z0=z0 + 22.0, z1=z0 + 44.0)
    return b.build()


def build_cap():
    b = Builder("cap")
    b.add(cyl_z(0.0, 0.0, Z_HINGE_TOP + 0.8, 7.2, 8.0, 28))
    b.add(box(0.6, -4.0, Z_HINGE_TOP + 0.8, 6.0, 8.0, 3.0))  # lug so it is not a lone disc in the viewer
    b.cut(cyl_z(0.0, 0.0, Z_HINGE_TOP + 0.4, PIN_R + 0.25, 9.2, BORE_SEG))
    # Cross hole for a Ø2 spring pin. The steel rod is assumed drilled; that hole is not in a print part.
    b.cut(cyl_x(0.0, 0.0, Z_HINGE_TOP + 5.2, 1.15, 18.0, 14))
    return b.build()


def build_coupons():
    a = Builder("coupon-a")
    a.add(box(0.0, 0.0, 0.0, 28.0, 18.0, 8.0))
    a.add(cyl_z(28.0, 9.0, 0.0, 6.0, 8.0, 24))
    a.cut(cyl_z(28.0, 9.0, -0.2, BORE_R, 8.4, BORE_SEG))
    b = Builder("coupon-b")
    b.add(box(8.0, 0.0, 8.6, 28.0, 18.0, 8.0))
    b.add(cyl_z(8.0, 9.0, 8.6, 6.0, 8.0, 24))
    b.cut(cyl_z(8.0, 9.0, 8.4, BORE_R, 8.4, BORE_SEG))
    rail = Builder("coupon-rail")
    rail.add(box(0.0, 0.0, 0.0, 22.0, 48.0, 16.0))
    rail.cut(box(0.0, 4.0, 6.0, 5.0, 36.0, 3.4))
    rider = Builder("coupon-rider")
    rider.add(box(4.6, 8.0, 7.2, 12.0, 18.0, 6.0))
    rider.add(box(1.2, 12.0, 6.7, 4.2, 12.0, 2.0))
    return {
        "cf_coupon_hinge_a": a.build(),
        "cf_coupon_hinge_b": b.build(),
        "cf_coupon_drawer_rail": rail.build(),
        "cf_coupon_drawer_rider": rider.build(),
    }


def build_caster_mesh():
    """Nominal small plate caster. Not a measured commercial part and not a print."""
    plate = box(-13.0, -13.0, 0.25, 26.0, 26.0, 1.9)
    stem = cyl_z(0.0, 0.0, -14.0, 3.4, 14.5, 16)
    wheel = cyl_x(0.0, 0.0, -16.5, 12.5, 8.0, 24)
    horn_l = box(-6.2, -2.4, -20.0, 3.8, 4.8, 16.0)
    horn_r = box(2.4, -2.4, -20.0, 3.8, 4.8, 16.0)
    return snap_solid(union([plate, stem, wheel, horn_l, horn_r]))


def build_pin():
    return snap_solid(cyl_z(0.0, 0.0, HINGE_Z0 + 0.05, PIN_R, (Z_HINGE_TOP + 6.4) - (HINGE_Z0 + 0.05), 24))


def build_spring_pin():
    return snap_solid(cyl_x(0.0, 0.0, Z_HINGE_TOP + 5.2, 1.0, 16.0, 12))


def place(solid, wing: str):
    if wing == "hearth":
        return solid.mirror((1.0, 0.0, 0.0))
    return solid


def mesh_arrays(solid):
    mesh = solid.to_mesh()
    verts = np.asarray(mesh.vert_properties[:, :3], dtype=np.float64)
    tris = np.asarray(mesh.tri_verts, dtype=np.int64)
    return verts, tris


def write_stl(path: Path, solid) -> None:
    verts, tris = mesh_arrays(solid)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        header = b"Cedarfold prototype CAD solid. Design allowance, not a measured print."
        fh.write(header[:80].ljust(80, b"\0"))
        fh.write(struct.pack("<I", len(tris)))
        for tri in tris:
            p = verts[tri]
            n = np.cross(p[1] - p[0], p[2] - p[0])
            norm = np.linalg.norm(n)
            if norm > 0:
                n = n / norm
            fh.write(struct.pack("<3f", *n.astype(np.float32)))
            for point in p:
                fh.write(struct.pack("<3f", *point.astype(np.float32)))
            fh.write(struct.pack("<H", 0))


def reload_stl(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, file_type="stl", force="mesh")
    if not isinstance(loaded, trimesh.Trimesh):
        raise RuntimeError(f"{path.name} did not reload as one mesh")
    return loaded


def orient_on_bed(solid, kind: str):
    """Broad back on the bed.

    Assembly +Z (lace, cornice) maps to print +Y.
    Assembly -Z (keys) maps to print -Y.
    Assembly back (-Y) maps to print -Z.
    This is not the shortest-axis-on-Z pose.
    """
    if kind == "cap":
        # Lay the short cylinder on its side so print Z is the diameter, not the short axis.
        linear = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=float)
        note = "Cap lies on its side. Print Z is the diameter, not the short axis."
    elif kind == "coupon":
        linear = np.eye(3)
        note = "Coupon already has its broad face toward -Z in its own frame. Translated onto the origin."
    else:
        # Columns are images of the basis: X -> -X, Y -> Z, Z -> Y.
        linear = np.array([[-1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]], dtype=float)
        note = (
            "Broad back on the bed. Assembly up (lace, cornice) points to print +Y, "
            "so the keys sit below the lace on the plate. Not shortest-axis-on-Z."
        )
    src = solid
    # Apply linear transform about the origin, then drop the min corner to 0.
    affine = np.column_stack([linear, np.zeros(3)])
    turned = src.transform(affine.tolist())
    bounds = turned.bounding_box()
    mins = (bounds[0], bounds[1], bounds[2])
    shifted = turned.translate((-mins[0], -mins[1], -mins[2]))
    return shifted, note, linear, mins


def aabb(solid) -> tuple[float, float, float, float, float, float]:
    b = solid.bounding_box()
    return tuple(float(v) for v in b)


def size_of(bounds) -> tuple[float, float, float]:
    return (bounds[3] - bounds[0], bounds[4] - bounds[1], bounds[5] - bounds[2])


def rotate_z(solid, degrees: float):
    return solid.rotate((0.0, 0.0, float(degrees)))


def gap_report(a, b) -> dict:
    inter = a ^ b
    vol = float(inter.volume()) if not inter.is_empty() else 0.0
    gap = float(a.min_gap(b, 8.0))
    return {"intersection_mm3": round(vol, 3), "min_gap_mm": round(gap, 3)}


def probe_inside(solid, x: float, y: float, z: float, span: float = 1.2) -> bool:
    sample = box(x - span / 2, y - span / 2, z - span / 2, span, span, span)
    hit = solid ^ sample
    return (not hit.is_empty()) and hit.volume() > span**3 * 0.25


def render_png(path: Path, solids: list[tuple[object, tuple[int, int, int]]], eye, target, size=560) -> None:
    """Z-buffer of the actual triangles. Lambert shade, no texture stand-in."""
    eye = np.asarray(eye, dtype=float)
    target = np.asarray(target, dtype=float)
    forward = target - eye
    forward = forward / np.linalg.norm(forward)
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-6:
        up = np.array([0.0, 1.0, 0.0])
        right = np.cross(forward, up)
    right = right / np.linalg.norm(right)
    cup = np.cross(right, forward)
    light = np.array([-0.35, -0.55, 0.76])
    light = light / np.linalg.norm(light)
    w = h = size
    zbuf = np.full((h, w), np.inf, dtype=np.float32)
    img = np.zeros((h, w, 3), dtype=np.float32)
    img[:] = np.array([0.125, 0.105, 0.09], dtype=np.float32)
    focal = size * 1.15
    for solid, color in solids:
        verts, tris = mesh_arrays(solid)
        if len(tris) == 0:
            continue
        cam = np.stack(
            [
                (verts - eye) @ right,
                (verts - eye) @ cup,
                (verts - eye) @ forward,
            ],
            axis=1,
        )
        rgb = np.array(color, dtype=np.float32) / 255.0
        for tri in tris:
            p = cam[tri]
            if np.min(p[:, 2]) <= 1.0:
                continue
            n = np.cross(p[1] - p[0], p[2] - p[0])
            if n[2] <= 0:
                continue  # back face in this camera (forward is +Z)
            nn = np.linalg.norm(n)
            if nn < 1e-9:
                continue
            n = n / nn
            shade = 0.28 + 0.72 * max(0.0, float(np.dot(n, light)))
            sx = focal * (p[:, 0] / p[:, 2]) + w * 0.5
            sy = h * 0.5 - focal * (p[:, 1] / p[:, 2])
            minx = max(int(np.floor(np.min(sx))), 0)
            maxx = min(int(np.ceil(np.max(sx))), w - 1)
            miny = max(int(np.floor(np.min(sy))), 0)
            maxy = min(int(np.ceil(np.max(sy))), h - 1)
            if maxx <= minx or maxy <= miny:
                continue
            span = (maxx - minx + 1) * (maxy - miny + 1)
            stride = 1 if span < 90000 else 2 if span < 280000 else 3
            xs = np.arange(minx, maxx + 1, stride, dtype=np.float32)
            ys = np.arange(miny, maxy + 1, stride, dtype=np.float32)
            gx, gy = np.meshgrid(xs, ys)
            x0, y0s = sx[0], sy[0]
            x1, y1s = sx[1], sy[1]
            x2, y2s = sx[2], sy[2]
            den = (y1s - y2s) * (x0 - x2) + (x2 - x1) * (y0s - y2s)
            if abs(den) < 1e-6:
                continue
            w0 = ((y1s - y2s) * (gx - x2) + (x2 - x1) * (gy - y2s)) / den
            w1 = ((y2s - y0s) * (gx - x2) + (x0 - x2) * (gy - y2s)) / den
            w2 = 1.0 - w0 - w1
            mask = (w0 >= -0.002) & (w1 >= -0.002) & (w2 >= -0.002)
            if not np.any(mask):
                continue
            zz = w0 * p[0, 2] + w1 * p[1, 2] + w2 * p[2, 2]
            xi = np.rint(gx).astype(np.int32)
            yi = np.rint(gy).astype(np.int32)
            current = zbuf[yi, xi]
            update = mask & (zz < current)
            if not np.any(update):
                continue
            zbuf[yi[update], xi[update]] = zz[update]
            img[yi[update], xi[update]] = rgb * shade
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img * 255.0, 0, 255).astype(np.uint8), "RGB").save(path)


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def write_plans(path_open: Path, path_closed: Path) -> None:
    def svg(folded: bool) -> str:
        # Schematic of the walking floors, not a render.
        scale = 2.15
        def X(v):
            return 40 + v * scale
        def Y(v):
            return 40 + v * scale
        w = 40 + 460 * scale
        h = 40 + (420 if folded else 280) * scale
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">',
            '<rect width="100%" height="100%" fill="#f6f0e6"/>',
            '<g font-family="Georgia, serif" fill="#3a2c22">',
        ]
        def wing(ox, oy, label, flip_y=False):
            def P(x, y):
                yy = FRONT_Y1 - y if flip_y else y
                return X(ox + x), Y(oy + yy)
            x0, y0 = P(INNER_X0, BACK_Y0)
            x1, y1 = P(OUTER_X1, FRONT_Y1)
            parts.append(
                f'<rect x="{min(x0,x1):.1f}" y="{min(y0,y1):.1f}" width="{abs(x1-x0):.1f}" height="{abs(y1-y0):.1f}" fill="#e7d3b0" stroke="#6b4b2e" stroke-width="2"/>'
            )
            # Hall
            hx0, hy0 = P(INNER_X0, HALL_Y0)
            hx1, hy1 = P(OUTER_X1, HALL_Y1)
            parts.append(
                f'<rect x="{min(hx0,hx1):.1f}" y="{min(hy0,hy1):.1f}" width="{abs(hx1-hx0):.1f}" height="{abs(hy1-hy0):.1f}" fill="#f3e6cf" stroke="#6b4b2e" stroke-width="1"/>'
            )
            # Stairs
            for x_a, x_b, name in (
                (STAIR1_X0, STAIR1_X1, "Stair to next floor"),
                (STAIR2_X0, STAIR2_X1, "Stair above"),
            ):
                sx0, sy0 = P(x_a, FLIGHT_Y0)
                sx1, sy1 = P(x_b, FLIGHT_Y1)
                parts.append(
                    f'<rect x="{min(sx0,sx1):.1f}" y="{min(sy0,sy1):.1f}" width="{abs(sx1-sx0):.1f}" height="{abs(sy1-sy0):.1f}" fill="#d7b896" stroke="#6b4b2e"/>'
                )
            lx, ly = P((INNER_X0 + OUTER_X1) / 2, FRONT_Y1 * 0.55)
            parts.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="16">{label}</text>')
            parts.append(
                f'<text x="{P(INNER_X0 + 8, HALL_Y0 + 18)[0]:.0f}" y="{P(INNER_X0 + 8, HALL_Y0 + 18)[1]:.0f}" font-size="12">Hall / landing {LAND_D:.0f} mm deep</text>'
            )
        if not folded:
            wing(20, 20, "Hearth")
            wing(20 + OUTER_X1 + 16, 20, "Garden")
            parts.append(
                f'<text x="40" y="28" font-size="18">Open — wings side by side, fronts toward the bottom of this drawing</text>'
            )
        else:
            wing(80, 20, "Hearth (fixed)")
            wing(80, 20 + FRONT_Y1 + 18, "Garden folded behind", flip_y=True)
            parts.append(
                f'<text x="40" y="28" font-size="18">Closed — garden wing folded 180° behind the hearth wing</text>'
            )
        parts.append("</g></svg>")
        return "".join(parts)

    path_open.write_text(svg(False))
    path_closed.write_text(svg(True))


def main() -> None:
    print("Building Cedarfold solids…", flush=True)
    hearth = {
        "base": build_base(0, True),
        "drawer": build_drawer(),
        "ground": build_ground(0, add_kitchen),
        "upper": build_upper(0, add_bedroom),
        "attic": build_attic(0, terrace=False),
    }
    garden = {
        "base": build_base(1, False),
        "drawer": build_drawer(),
        "ground": build_ground(1, add_parlor),
        "upper": build_upper(1, add_bath),
        "attic": build_attic(1, terrace=True),
    }
    cap = build_cap()
    coupons = build_coupons()
    caster = build_caster_mesh()
    pin = build_pin()
    spring = build_spring_pin()
    print("Solids built", flush=True)

    catalog = []

    def add_part(part_id, name, role, color, solid, wing, kind, explode, print_part=True, drawer=False):
        world = place(solid, wing) if wing else solid
        catalog.append(
            {
                "id": part_id,
                "name": name,
                "role": role,
                "color": color,
                "solid": world,
                "wing": wing,
                "kind": kind,
                "explode": explode,
                "print": print_part,
                "drawer": drawer,
            }
        )

    add_part("cf_hearth_base", "Hearth base, drawer rails, and hinge seat", "base", WOOD_DARK, hearth["base"], "hearth", "shell", (0, -20, 0))
    add_part("cf_hearth_drawer", "Hearth drawer", "drawer", DRAWER_C, hearth["drawer"], "hearth", "shell", (0, 70, 0), drawer=True)
    add_part("cf_hearth_ground", "Hearth kitchen storey and lower stair", "storey", WOOD, hearth["ground"], "hearth", "shell", (0, 0, 28))
    add_part("cf_hearth_upper", "Hearth bedroom storey and upper stair", "storey", WOOD, hearth["upper"], "hearth", "shell", (0, 0, 64))
    add_part("cf_hearth_attic", "Hearth attic, gable roof, and balcony", "roof", ROOF_C, hearth["attic"], "hearth", "shell", (0, 0, 110))
    add_part("cf_garden_base", "Garden base and drawer rails", "base", WOOD_DARK, garden["base"], "garden", "shell", (0, -20, 0))
    add_part("cf_garden_drawer", "Garden drawer", "drawer", DRAWER_C, garden["drawer"], "garden", "shell", (0, 70, 0), drawer=True)
    add_part("cf_garden_ground", "Garden parlor storey and lower stair", "storey", CREAM, garden["ground"], "garden", "shell", (0, 0, 28))
    add_part("cf_garden_upper", "Garden bath storey and upper stair", "storey", CREAM, garden["upper"], "garden", "shell", (0, 0, 64))
    add_part("cf_garden_loft", "Garden terrace loft and shed roof", "roof", ROOF_C, garden["attic"], "garden", "shell", (0, 0, 110))
    add_part("cf_hinge_cap", "Hinge cap (spring-pin cross hole)", "hardware-plastic", ACCENT, cap, None, "cap", (20, -30, 40))
    for cid, solid in coupons.items():
        add_part(cid, cid.replace("_", " "), "coupon", SAGE, solid, None, "coupon", (0, 0, 0))
    add_part("cf_ref_pin", "Catalog Ø4 mm hinge rod — not printed", "catalog", METAL, pin, None, "ref", (0, 0, 0), print_part=False)
    add_part("cf_ref_spring_pin", "Catalog Ø2×16 mm spring pin — not printed", "catalog", METAL, spring, None, "ref", (0, 0, 0), print_part=False)

    # Caster instances are separate placed meshes so the GLB shows them, one reference file plus transforms.
    caster_instances = []
    for wing in ("hearth", "garden"):
        for index, (x, y, kind) in enumerate(caster_centers()):
            wx, wy = (-x, y) if wing == "hearth" else (x, y)
            caster_instances.append(
                {
                    "id": f"caster-{wing}-{index}",
                    "name": f"{wing.title()} caster ({kind}, catalog, not printed)",
                    "wing": wing,
                    "kind": kind,
                    "translate": (wx, wy, 0.0),
                }
            )

    print("Validating…", flush=True)
    failures = []

    def check(ok: bool, message: str) -> None:
        print(("  ok  " if ok else " FAIL ") + message, flush=True)
        if not ok:
            failures.append(message)

    # Stair and landing probes, hearth ground in world (mirrored X).
    def world_point(x, y, z, wing="hearth"):
        return (-x, y, z) if wing == "hearth" else (x, y, z)

    hg = place(hearth["ground"], "hearth")
    hu = place(hearth["upper"], "hearth")
    ha = place(hearth["attic"], "hearth")
    mid_i = N_RISERS // 2
    rise = RISE / N_RISERS
    run = RUN / N_RISERS
    tread_z = Z_BASE + (mid_i + 1) * rise
    tread_y = FLIGHT_Y1 - (mid_i + 0.5) * run
    stair_x = (STAIR1_X0 + STAIR1_X1) / 2
    land_x = stair_x
    land_y = (HALL_Y0 + HALL_Y1) / 2
    px, py, pz = world_point(land_x, land_y, Z_L2 - 1.2)
    check(probe_inside(hg, px, py, pz), "L2 landing solid is inside the hearth kitchen storey")
    wx, wy, wz = world_point(stair_x, (FLIGHT_Y0 + FLIGHT_Y1) / 2, Z_L2 - 1.2)
    check(not probe_inside(hg, wx, wy, wz), "L2 stairwell is open over the lower flight")
    tx, ty, tz = world_point(stair_x, tread_y, tread_z - 1.0)
    check(probe_inside(hg, tx, ty, tz), "A lower-stair tread is solid")
    ax, ay, az = world_point(stair_x, tread_y, tread_z + 12.0)
    check(not probe_inside(hg, ax, ay, az), "There is air above that tread")
    # L3 landing on the upper module.
    lx, ly, lz = world_point((STAIR2_X0 + STAIR2_X1) / 2, land_y, Z_L3 - 1.2)
    check(probe_inside(hu, lx, ly, lz), "L3 landing solid is inside the hearth bedroom storey")
    sx, sy, sz = world_point((STAIR2_X0 + STAIR2_X1) / 2, (FLIGHT_Y0 + FLIGHT_Y1) / 2, Z_L3 - 1.2)
    check(not probe_inside(hu, sx, sy, sz), "L3 stairwell is open over the upper flight")
    # Attic floor does not cover the upper stairwell.
    check(not probe_inside(ha, sx, sy, Z_L3 + 0.4), "Attic finish floor keeps the upper stairwell open")
    # Hall walking width is the generated landing depth.
    check(LAND_D + 1e-6 >= STAIR_W, f"Landing depth {LAND_D} mm covers the {STAIR_W} mm walking width")

    # Hardware envelope vs the other wing at every sampled angle.
    hearth_body = union([place(hearth[k], "hearth") for k in ("base", "ground", "upper", "attic")])
    garden_body = union([place(garden[k], "garden") for k in ("base", "ground", "upper", "attic")])
    motion = []
    for angle in (0, -20, -40, -60, -80, -100, -120, -140, -160, -180):
        spun = rotate_z(garden_body, angle)
        report = gap_report(hearth_body, spun)
        report["angle_deg"] = angle
        report["drawers"] = "closed"
        motion.append(report)
        check(report["intersection_mm3"] < 2.0, f"wing bodies clear at {angle}° ({report})")
    # Drawers fully out, both wings, at open and closed and one mid angle.
    hearth_drawer_out = place(hearth["drawer"], "hearth").translate((0.0, DRAWER_TRAVEL, 0.0))
    garden_drawer_local = place(garden["drawer"], "garden").translate((0.0, DRAWER_TRAVEL, 0.0))
    for angle in (0, -90, -180):
        spun_wing = rotate_z(garden_body, angle)
        spun_drawer = rotate_z(garden_drawer_local, angle)
        report = gap_report(union([hearth_body, hearth_drawer_out]), union([spun_wing, spun_drawer]))
        report["angle_deg"] = angle
        report["drawers"] = "full travel"
        motion.append(report)
        check(report["intersection_mm3"] < 2.0, f"wings plus extended drawers clear at {angle}° ({report})")

    # Drawer rail behavior on the hearth, which is the same rail design as the garden.
    base_w = place(hearth["base"], "hearth")
    drawer_w = place(hearth["drawer"], "hearth")

    def slide(solid, distance):
        return solid.translate((0.0, distance, 0.0))

    closed_gap = gap_report(base_w, drawer_w)
    open_gap = gap_report(base_w, slide(drawer_w, DRAWER_TRAVEL))
    check(closed_gap["intersection_mm3"] < 1.0 and closed_gap["min_gap_mm"] > 0.15, f"drawer closed clearance {closed_gap}")
    check(open_gap["intersection_mm3"] < 1.0 and open_gap["min_gap_mm"] > 0.15, f"drawer at travel clearance {open_gap}")
    past = gap_report(base_w, slide(drawer_w, DRAWER_TRAVEL + 3.0))
    check(past["intersection_mm3"] > 5.0, f"drawer past the stop hits the base {past}")
    lifted_closed = gap_report(base_w, drawer_w.translate((0.0, 0.0, 3.2)))
    lifted_open = gap_report(base_w, slide(drawer_w, DRAWER_TRAVEL).translate((0.0, 0.0, 3.2)))
    check(lifted_closed["intersection_mm3"] > 5.0, f"closed drawer cannot lift out {lifted_closed}")
    check(lifted_open["intersection_mm3"] < 1.0, f"fully extended drawer can lift out of the notch {lifted_open}")

    # Tenon engagement: nominal contact, and a 2 mm press creates a real intersection.
    ground_w = place(hearth["ground"], "hearth")
    stack = gap_report(base_w, ground_w)
    pressed = gap_report(base_w, ground_w.translate((0.0, 0.0, -2.0)))
    check(stack["intersection_mm3"] < 8.0, f"base and kitchen storey nominal stack {stack}")
    check(pressed["intersection_mm3"] > 50.0, f"pressing the storey 2 mm engages keys/bearing {pressed}")

    # Pin sits in the bore without intersecting the hearth hinge solids.
    pin_gap = gap_report(union([place(hearth["base"], "hearth"), place(hearth["ground"], "hearth"), place(hearth["upper"], "hearth"), place(hearth["attic"], "hearth")]), pin)
    check(pin_gap["intersection_mm3"] < 1.0 and pin_gap["min_gap_mm"] > 0.05, f"pin clearance to hearth plastic {pin_gap}")
    cap_gap = gap_report(cap, pin)
    check(cap_gap["intersection_mm3"] < 1.0 and cap_gap["min_gap_mm"] > 0.05, f"pin clearance to cap {cap_gap}")

    # Export.
    asm_dir = ROOT / "stl" / "assembly"
    print_dir = ROOT / "stl" / "print"
    ref_dir = ROOT / "stl" / "reference"
    for folder in (asm_dir, print_dir, ref_dir):
        folder.mkdir(parents=True, exist_ok=True)

    orientations = {}
    reloads = {}
    for part in catalog:
        asm_path = (asm_dir if part["print"] else ref_dir) / f"{part['id']}.stl"
        write_stl(asm_path, part["solid"])
        if not part["print"]:
            loaded = reload_stl(asm_path)
            reloads[part["id"]] = {
                "watertight": bool(loaded.is_watertight),
                "volume_mm3": round(float(loaded.volume), 1),
                "triangles": int(len(loaded.faces)),
            }
            check(loaded.is_watertight and loaded.volume > 0, f"reload {part['id']}")
            continue
        loaded = reload_stl(asm_path)
        reloads[part["id"]] = {
            "watertight": bool(loaded.is_watertight),
            "volume_mm3": round(float(loaded.volume), 1),
            "triangles": int(len(loaded.faces)),
            "assembly_file": f"stl/assembly/{part['id']}.stl",
        }
        check(loaded.is_watertight and loaded.volume > 0, f"reload assembly {part['id']}")
        oriented, note, linear, mins = orient_on_bed(part["solid"], part["kind"])
        print_path = print_dir / f"{part['id']}.stl"
        write_stl(print_path, oriented)
        printed = reload_stl(print_path)
        check(printed.is_watertight and printed.volume > 0 and abs(printed.volume - loaded.volume) / loaded.volume < 0.02, f"reload print {part['id']}")
        pb = aabb(oriented)
        extents = size_of(pb)
        margins = [round(BED_MARGIN[i] - extents[i], 2) for i in range(3)]
        native = size_of(aabb(part["solid"]))
        orientations[part["id"]] = {
            "pose": note,
            "assembly_extents_mm": [round(v, 2) for v in native],
            "print_extents_mm": [round(v, 2) for v in extents],
            "margin_to_310x300x315_mm": margins,
            "linear_assembly_to_print": linear.round(6).tolist(),
            "assembly_min_after_linear_mm": [round(float(v), 3) for v in mins],
        }
        check(all(m >= -0.05 for m in margins), f"{part['id']} print margin {margins} extents {extents}")
        shortest = min(native)
        # The print Z should not be that shortest axis unless the part is a coupon lying naturally.
        if part["kind"] == "shell":
            check(extents[2] > shortest + 1.0, f"{part['id']} print Z {extents[2]} is not the shortest assembly axis {shortest}")

    # Caster clearance to the hearth base in the open pose.
    caster_gaps = []
    for inst in caster_instances:
        if inst["wing"] != "hearth":
            continue
        placed = caster.translate(inst["translate"])
        caster_gaps.append(gap_report(base_w, placed))
    check(all(g["intersection_mm3"] < 1.0 and g["min_gap_mm"] > 0.1 for g in caster_gaps), f"caster pockets clear the reference casters {caster_gaps}")

    radial_flat = BORE_FLAT_R - PIN_R
    reports = ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "motion.json").write_text(json.dumps({"samples": motion, "drawer_travel_mm": DRAWER_TRAVEL}, indent=2))
    (reports / "print-orientations.json").write_text(json.dumps(orientations, indent=2))
    (reports / "reload.json").write_text(json.dumps(reloads, indent=2))

    # Manifest, BOM, GLB, previews, plans, zip.
    instances = []
    for part in catalog:
        instances.append(
            {
                "id": part["id"],
                "part": part["id"],
                "name": part["name"],
                "wing": part["wing"],
                "role": part["role"],
                "color": part["color"],
                "print": part["print"],
                "file": f"stl/assembly/{part['id']}.stl" if part["print"] else f"stl/reference/{part['id']}.stl",
                "explode_mm": list(part["explode"]),
                "drawer_travel_mm": DRAWER_TRAVEL if part["drawer"] else 0,
            }
        )
    for inst in caster_instances:
        instances.append(
            {
                "id": inst["id"],
                "part": "cf_ref_caster",
                "name": inst["name"],
                "wing": inst["wing"],
                "role": "catalog",
                "color": METAL,
                "print": False,
                "file": "stl/reference/cf_ref_caster.stl",
                "translate_mm": list(inst["translate"]),
                "explode_mm": [0, 0, -24],
                "drawer_travel_mm": 0,
                "brake": inst["kind"] == "brake",
            }
        )
    write_stl(ref_dir / "cf_ref_caster.stl", caster)
    caster_loaded = reload_stl(ref_dir / "cf_ref_caster.stl")
    check(caster_loaded.is_watertight, "reload caster reference")

    # Bounds of the open assembly including casters' wheels (about 30 mm below).
    all_bounds = [aabb(p["solid"]) for p in catalog if p["print"] or p["id"] == "cf_ref_pin"]
    min_corner = [min(b[i] for b in all_bounds) for i in range(3)]
    max_corner = [max(b[i + 3] for b in all_bounds) for i in range(3)]
    min_corner[2] = min(min_corner[2], -30.0)
    manifest = {
        "name": "Cedarfold Playhouse",
        "version": VERSION,
        "scale": SCALE,
        "status": "UNPRINTED PROTOTYPE",
        "units": "mm",
        "up_axis": "Z",
        "nozzle_basis_mm": NOZZLE_MM,
        "nozzle_0_2_mm": "not confirmed; this CAD is for a 0.4 mm nozzle",
        "printer_nominal_bed_mm": list(BED_NOMINAL),
        "fit_envelope_mm": list(BED_MARGIN),
        "hinge": {
            "axis": [0, 0, 1],
            "origin_mm": [0, 0, 0],
            "open_deg": 0,
            "closed_deg": -180,
            "moving_wing": "garden",
            "pin_diameter_mm": PIN_R * 2,
            "bore_flat_radius_mm": BORE_FLAT_R,
            "radial_clearance_to_flats_mm": round(radial_flat, 3),
            "axial_knuckle_gap_mm": round(PITCH - KNUCKLE_LEN, 3),
            "segments": BORE_SEG,
        },
        "drawer": {
            "travel_mm": DRAWER_TRAVEL,
            "axis_open_pose": [0, 1, 0],
            "capture": "Runners ride in side grooves. A front stop meets the runner at full travel. The front of the groove is taller, so the drawer lifts out only when it is fully extended.",
        },
        "stairs": {
            "walking_width_mm": STAIR_W,
            "risers_per_flight": N_RISERS,
            "rise_mm": round(RISE / N_RISERS, 3),
            "tread_mm": TREAD,
            "floor_to_floor_mm": RISE,
            "landing_depth_mm": LAND_D,
            "landing": "Back hall of each upper floor. The hall is the full room width and at least the stair width in the direction of travel. The flight opens through that floor; the landing is solid and continuous with the room floor.",
        },
        "keys": {
            "tenon_mm": [TENON, TENON, TENON_LEN],
            "socket_mm": [SOCKET, SOCKET, SOCKET_DEPTH],
            "side_clearance_mm": round((SOCKET - TENON) / 2, 3),
            "end_clearance_mm": round(SOCKET_DEPTH - TENON_LEN, 3),
            "magnets": "None. Stacking is the rectangular keys. Magnets are not the attachment.",
        },
        "lighting": {
            "voltage": "5 V provisional empty grooves",
            "section_mm": [5.0, 1.7],
            "loop": "Each base has a rear pocket beside the hinge for a slack loop. No wire is included. The groove is on the fixed stile, not a loose lead on the swinging front.",
        },
        "casters": {
            "count": 8,
            "brake_count": 4,
            "assumption": "Nominal 25 mm wheel plate caster, about 26 mm plate, 18 mm hole spacing, M4 screws. The mesh is a schematic, not a measured catalog part. Brake holding force was not tested.",
        },
        "open_size_mm": {
            "min_mm": [round(v, 1) for v in min_corner],
            "max_mm": [round(v, 1) for v in max_corner],
        },
        "rooms": [
            {"id": "hearth-kitchen", "storey": 1, "note": "Outer counter, sink, stove, table. Stair to the bedroom is on the inner side."},
            {"id": "hearth-bedroom", "storey": 2, "note": "Bed and lamp. Hall at the back is the landing."},
            {"id": "hearth-attic", "storey": 3, "note": "Gable attic, cot, balcony door on the outer wall."},
            {"id": "garden-parlor", "storey": 1, "note": "Sofa, table, floor lamp."},
            {"id": "garden-bath", "storey": 2, "note": "Tub, basin, toilet."},
            {"id": "garden-terrace", "storey": 3, "note": "Open front terrace under a rear shed roof."},
        ],
        "instances": instances,
        "limits": [
            "UNPRINTED PROTOTYPE. No physical print, fit, pinch, tip, drawer-ejection, or caster-brake test was run.",
            "Not a finished print kit and not a child-safe toy. Hinge pinch, tipping, a drawer coming free, and wheel locks are unproven.",
            "Clearances in this manifest are CAD design allowances.",
            "No slicer was run. Supports for the back-on-bed pose were not generated.",
            "Metal rod, spring pin, casters, and screws are catalog assumptions. They are not in the plastic zip.",
            "The 5 V lighting is an empty groove and a rear slack pocket. No wire, LED, or supply is specified as a tested circuit.",
            "0.4 mm nozzle basis. A 0.2 mm nozzle is not confirmed.",
            "Story joints are rectangular keys. There are no magnets.",
            "Queen Anne is a different model and is not changed by this one.",
        ],
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2))

    bom = {
        "version": VERSION,
        "plastic": [],
        "catalog_metal_and_hardware": [
            {"item": "Steel dowel pin", "nominal": "Ø4 mm × 286 mm", "qty": 1, "role": "Hinge pin. Rests on the printed seat. Retained by the spring pin through the cap. Not printed."},
            {"item": "Spring pin", "nominal": "Ø2 mm × 16 mm", "qty": 1, "role": "Cross pin through the printed cap. The rod is assumed drilled to suit. Not printed."},
            {"item": "Plate caster", "nominal": "25 mm wheel, ~26 mm plate, 18 mm hole pattern", "qty": 4, "role": "Free swivel. Schematic mesh only."},
            {"item": "Plate caster with brake", "nominal": "25 mm wheel, ~26 mm plate, brake", "qty": 4, "role": "The rear pair on each wing. Brake force was not tested."},
            {"item": "Pan head screw", "nominal": "M4 × 12 mm", "qty": 32, "role": "Caster plates, four screws each. Not printed."},
        ],
        "notes": [
            "Plastic is modeled as PLA. Suggested colors are warm wood, cream, and a muted drawer tone. The material is printed plastic, not wood.",
            "A 0.4 mm nozzle is the basis. Layer height is not a tested profile.",
            "Print the hinge coupon and the drawer coupon before the house.",
        ],
    }
    for part in catalog:
        if not part["print"]:
            continue
        bom["plastic"].append(
            {
                "id": part["id"],
                "name": part["name"],
                "qty": 1,
                "material": "PLA",
                "print_stl": f"stl/print/{part['id']}.stl",
                "assembly_stl": f"stl/assembly/{part['id']}.stl",
                "print_extents_mm": orientations[part["id"]]["print_extents_mm"],
                "margin_mm": orientations[part["id"]]["margin_to_310x300x315_mm"],
                "pose": orientations[part["id"]]["pose"],
            }
        )
    (reports / "print-bom.json").write_text(json.dumps(bom, indent=2))
    (reports / "clearances.json").write_text(
        json.dumps(
            {
                "hinge_radial_to_bore_flats_mm": round(radial_flat, 3),
                "hinge_axial_gap_mm": round(PITCH - KNUCKLE_LEN, 3),
                "key_side_mm": round((SOCKET - TENON) / 2, 3),
                "key_end_mm": round(SOCKET_DEPTH - TENON_LEN, 3),
                "drawer_closed": closed_gap,
                "drawer_open": open_gap,
                "drawer_past_stop": past,
                "drawer_lift_closed": lifted_closed,
                "drawer_lift_open": lifted_open,
                "stack_nominal": stack,
                "stack_pressed_2mm": pressed,
                "pin": pin_gap,
                "cap": cap_gap,
                "casters": caster_gaps,
                "source": "CAD design allowance. Not a physical measurement.",
            },
            indent=2,
        )
    )

    # GLB in the open pose.
    scene = trimesh.Scene()
    for part in catalog:
        verts, tris = mesh_arrays(part["solid"])
        mesh = trimesh.Trimesh(vertices=verts, faces=tris, process=False)
        color = hex_rgb(part["color"]) + (255,)
        mesh.visual.face_colors = color
        scene.add_geometry(mesh, node_name=part["id"], geom_name=part["id"])
    for inst in caster_instances:
        verts, tris = mesh_arrays(caster)
        mesh = trimesh.Trimesh(vertices=verts, faces=tris, process=False)
        mesh.visual.face_colors = hex_rgb(METAL) + (255,)
        mesh.apply_translation(inst["translate"])
        scene.add_geometry(mesh, node_name=inst["id"], geom_name=inst["id"])
    glb_path = ROOT / "assembly.glb"
    scene.export(glb_path)
    print(f"GLB {glb_path} ({glb_path.stat().st_size} bytes)", flush=True)

    write_plans(ROOT / "plan-open.svg", ROOT / "plan-closed.svg")

    # Previews from the actual meshes. Skip catalog metal so the plastic reads clearly.
    preview_solids = [(p["solid"], hex_rgb(p["color"])) for p in catalog if p["print"] and p["role"] != "coupon"]
    garden_ids = {"cf_garden_base", "cf_garden_drawer", "cf_garden_ground", "cf_garden_upper", "cf_garden_loft"}
    closed_solids = []
    half_solids = []
    drawers_solids = []
    for part in catalog:
        if not part["print"] or part["role"] == "coupon":
            continue
        color = hex_rgb(part["color"])
        solid = part["solid"]
        if part["id"] in garden_ids:
            closed_solids.append((rotate_z(solid, -180), color))
            half_solids.append((rotate_z(solid, -90), color))
        else:
            closed_solids.append((solid, color))
            half_solids.append((solid, color))
        if part["drawer"]:
            moved = solid.translate((0.0, DRAWER_TRAVEL, 0.0))
            if part["wing"] == "garden":
                drawers_solids.append((moved, color))
            else:
                drawers_solids.append((moved, color))
        else:
            drawers_solids.append((solid, color))
    center = np.array([(min_corner[i] + max_corner[i]) / 2 for i in range(3)])
    eye_34 = center + np.array([260.0, 460.0, 190.0])
    previews = ROOT / "previews"
    print("Rendering previews…", flush=True)
    if os.environ.get("CF_SKIP_RENDER") == "1":
        print("CF_SKIP_RENDER set, skipping PNGs", flush=True)
    else:
        render_png(previews / "open-three-quarter.png", preview_solids, eye_34, center + np.array([0, 0, 20]))
        render_png(previews / "closed-three-quarter.png", closed_solids, center + np.array([340.0, -420.0, 210.0]), center)
        render_png(previews / "half-fold.png", half_solids, center + np.array([460.0, 120.0, 200.0]), center)
        render_png(previews / "drawers-out.png", drawers_solids, center + np.array([40.0, 520.0, 80.0]), center + np.array([0, 20, -80]))
        # Interior: clip the hearth kitchen by removing the front band.
        clip = box(-OUTER_X1 - 5, -5, -5, OUTER_X1 + 40, FRONT_Y0 - 10, 400)
        interior = []
        for part in catalog:
            if part["wing"] == "hearth" and part["print"] and part["role"] != "coupon":
                interior.append((part["solid"] ^ clip, hex_rgb(part["color"])))
        render_png(previews / "hearth-interior.png", interior, np.array([-40.0, 340.0, 120.0]), np.array([-90.0, 80.0, 80.0]))
        # Hinge section: a thin world slice around x=0 of the bases.
        hinge_slice = box(-30, -20, 0, 60, 80, 80)
        hinge_solids = []
        for part in catalog:
            if part["id"] in {"cf_hearth_base", "cf_garden_base", "cf_ref_pin"}:
                hinge_solids.append((part["solid"] ^ hinge_slice, hex_rgb(part["color"])))
        render_png(previews / "hinge-bases.png", hinge_solids, np.array([40.0, -90.0, 70.0]), np.array([0.0, 10.0, 24.0]), size=640)
        print("Previews written", flush=True)

    zip_path = ROOT / "downloads" / f"cedarfold-v{VERSION}-plastic-print.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    note = ROOT / "downloads" / "PRINT.txt"
    note.write_text(
        "\n".join(
            [
                f"Cedarfold Playhouse v{VERSION}",
                "UNPRINTED PROTOTYPE. Plastic print STLs only.",
                "Not a toy-safety certification. Not a finished kit.",
                "No slicer was run. Clearances are CAD allowances.",
                "Orient each shell with the broad back on the bed.",
                "Keys sit below the lace (cornice) on the plate.",
                "Do not stand a shell on its shortest axis.",
                "Metal rod, spring pin, casters, and screws are not in this zip.",
                "Print cf_coupon_hinge_a/b and the drawer coupon before the house.",
                f"Drawer CAD travel {DRAWER_TRAVEL:.1f} mm.",
                f"Hinge pin Ø{PIN_R*2:.0f} mm, bore flat clearance {radial_flat:.2f} mm.",
            ]
        )
        + "\n"
    )
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(note, "PRINT.txt")
        zf.write(reports / "print-bom.json", "print-bom.json")
        for part in catalog:
            if part["print"]:
                zf.write(print_dir / f"{part['id']}.stl", f"stl/{part['id']}.stl")
    print(f"zip {zip_path} ({zip_path.stat().st_size} bytes)", flush=True)

    if failures:
        (reports / "failures.json").write_text(json.dumps(failures, indent=2))
        raise SystemExit(f"{len(failures)} checks failed:\n" + "\n".join(failures))
    (reports / "failures.json").write_text("[]\n")
    print("All checks passed.", flush=True)


if __name__ == "__main__":
    main()
