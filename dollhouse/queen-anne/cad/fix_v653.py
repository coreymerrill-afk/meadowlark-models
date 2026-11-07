"""v6.5.3 fastener lengths only. Does not rebuild the house.

Back screws become nominal M2x3 (under-head 3.0 mm). The nut stays.
Jamb screws become nominal M2x8 (under-head 8.0 mm). Each jamb nut moves
about 1 mm toward the head, on a whole number of 0.4 mm pitches when that
keeps the thread phase, and the blind bore is extended so the tip and the
nut both have empty hole past them. Magnet seats and the far skin stay closed.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import trimesh as tm
from PIL import Image, ImageDraw

from fix_functional import load_world, write_world
from integrate_upgrade import (
    REPORT,
    ROOT,
    STL,
    box,
    cyl_y,
    diff,
    hex_y,
    lay_flat,
    one_body,
    overlap,
    union,
)

MANIFEST = os.path.join(ROOT, "manifest.json")
HEAD_H = 1.6
NUT_T = 1.6
PITCH = 0.4
METAL = {
    "qa65_adult_screw_back_l",
    "qa65_adult_screw_back_r",
    "qa65_adult_screw_jl1",
    "qa65_adult_screw_jl2",
    "qa65_adult_screw_jr1",
    "qa65_adult_screw_jr2",
    "qa65_m2_nut",
}
JAMBS = (
    ("adult-screw-jl1", "nut-jl1", "walls-l1", "retainer-jl1"),
    ("adult-screw-jl2", "nut-jl2", "walls-l2", "retainer-jl2"),
    ("adult-screw-jr1", "nut-jr1", "side", "retainer-jr1"),
    ("adult-screw-jr2", "nut-jr2", "side", "retainer-jr2"),
)


def contains_at(mesh, x, y, z):
    return bool(mesh.contains([[x, y, z]])[0])


def ring(mesh, x, y, z, radius, count=8):
    pts = []
    for i in range(count):
        ang = i * 2 * math.pi / count
        pts.append([x + radius * math.cos(ang), y, z + radius * math.sin(ang)])
    return mesh.contains(pts)


def extreme_y(mesh, x, z, radius, y0, y1, want_min):
    ys = np.arange(y0, y1 + 1e-9, 0.05)
    found = []
    for i in range(8):
        ang = i * 2 * math.pi / 8
        pts = np.column_stack(
            [
                np.full(len(ys), x + radius * math.cos(ang)),
                ys,
                np.full(len(ys), z + radius * math.sin(ang)),
            ]
        )
        inside = mesh.contains(pts)
        if inside.any():
            hit = ys[inside]
            found.append(float(hit.min() if want_min else hit.max()))
    if not found:
        raise RuntimeError(f"no metal at r={radius} near {(x, z)}")
    return min(found) if want_min else max(found)


def first_solid(mesh, x, z, y_from, direction):
    y = y_from
    for _ in range(400):
        y += direction * 0.05
        if contains_at(mesh, x, y, z):
            return y
    raise RuntimeError(f"no solid from {y_from} along {direction}")


def interval_overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def draw_section(meshes, origin, normal, span, path, title, colors):
    image = Image.new("RGB", (980, 640), (244, 241, 234))
    draw = ImageDraw.Draw(image)
    draw.text((16, 12), title, fill=(20, 24, 28))
    a0, a1, b0, b1, px0, py0, px1, py1 = span
    axis = int(np.argmax(np.abs(normal)))
    for mesh, color in zip(meshes, colors):
        path3d = mesh.section(plane_origin=origin, plane_normal=normal)
        if path3d is None:
            continue
        for poly in path3d.discrete:
            pts = []
            for point in poly:
                if axis == 0:
                    u, v = point[1], point[2]
                else:
                    u, v = point[0], point[1]
                px = px0 + (u - a0) / (a1 - a0) * (px1 - px0)
                py = py0 + (b1 - v) / (b1 - b0) * (py1 - py0)
                pts.append((px, py))
            if len(pts) > 1:
                draw.line(pts, fill=color, width=2)
    image.save(path)


def magnet_points():
    pts = []
    for x in (226.0, 228.0, 230.0, 493.0, 495.0, 497.0):
        for z in (44.0, 68.0, 90.0, 142.0, 166.0, 188.0):
            for dz in (-1.5, 0.0, 1.5):
                for y in np.arange(294.5, 301.51, 0.7):
                    pts.append([x, y, z + dz])
    return np.array(pts)


def magnet_state(mesh, pts):
    """1 solid, 0 void, -1 on a face. A nudged wall face is not a new opening."""
    base = mesh.contains(pts)
    plus = pts.copy()
    plus[:, 1] += 0.35
    minus = pts.copy()
    minus[:, 1] -= 0.35
    above = mesh.contains(plus)
    below = mesh.contains(minus)
    state = []
    for i in range(len(pts)):
        if base[i] and above[i] and below[i]:
            state.append(1)
        elif (not base[i]) and (not above[i]) and (not below[i]):
            state.append(0)
        else:
            state.append(-1)
    return state


MAGNET_PTS = magnet_points()


def magnets_hold(before, after):
    opened = 0
    filled = 0
    for old, new in zip(before, after):
        if old == 1 and new == 0:
            opened += 1
        elif old == 0 and new == 1:
            filled += 1
    return opened == 0 and filled == 0


def phase_ok(screw, nut):
    """Seated overlap stays clear. A 0.12 mm axial shift, either way, meets the flanks."""
    if overlap(screw, nut) > 0.05:
        return False, 0.0
    best = 0.0
    for sign in (1.0, -1.0):
        pulled = screw.copy()
        pulled.apply_translation([0, 0.12 * sign, 0])
        best = max(best, overlap(pulled, nut))
    return best > 0.05, round(best, 3)


def seated_shift(screw, nut, underhead, new_tip):
    """Pick a shift near 1 mm whose thread phase still clears, then flanks on a 0.12 mm pull."""
    old = nut
    # Whole pitches preserve the ridge phase. Try those first, then a 0.02 mm search.
    preferred = [1.2, 0.8, 1.6, 2.0, 0.4]
    tried = []
    for shift in preferred + [round(1.0 + 0.02 * k, 2) for k in range(-15, 16)]:
        if shift < 0.7 or shift > 1.8 or shift in tried:
            continue
        tried.append(shift)
        near = float(old.bounds[0, 1]) - shift
        far = float(old.bounds[1, 1]) - shift
        if near < underhead + 0.8 or far > new_tip - 0.45:
            continue
        trial = old.copy()
        trial.apply_translation([0, -shift, 0])
        ok, hit = phase_ok(screw, trial)
        if ok:
            return shift, trial, hit
    raise RuntimeError("no thread phase for the moved jamb nut")


def fix_back(manifest, rear, screw_id, nut_id):
    inst, screw = load_world(manifest, screw_id)
    _n, nut = load_world(manifest, nut_id)
    center = screw.bounds.mean(axis=0)
    x, z = float(center[0]), float(center[2])
    y_lo, y_hi = float(screw.bounds[0, 1]) - 0.3, float(screw.bounds[1, 1]) + 0.3
    head = extreme_y(screw, x, z, 1.5, y_lo, y_hi, want_min=False)
    tip = extreme_y(screw, x, z, 0.4, y_lo, y_hi, want_min=True)
    under = head - HEAD_H
    new_tip = under - 3.0
    if new_tip <= tip:
        raise RuntimeError(f"{screw_id} M2x3 tip {new_tip} is not shorter than {tip}")
    trimmed = diff(screw, [box(x - 4, tip - 1, z - 4, x + 4, new_tip, z + 4)], screw_id)
    head2 = extreme_y(trimmed, x, z, 1.5, new_tip, head + 0.3, want_min=False)
    tip2 = extreme_y(trimmed, x, z, 0.4, new_tip - 0.2, head, want_min=True)
    under_len = (head2 - tip2) - HEAD_H
    nut_near = float(nut.bounds[1, 1])
    nut_far = float(nut.bounds[0, 1])
    engagement = interval_overlap(tip2, under, nut_far, nut_near)
    bore = first_solid(rear, x, z, tip2, -1)
    clearance = tip2 - bore
    ok, hit = phase_ok(trimmed, nut)
    if not ok:
        raise RuntimeError(f"{screw_id} lost thread engagement")
    if under_len < 2.9 or under_len > 3.15:
        raise RuntimeError(f"{screw_id} under-head {under_len} is not M2x3")
    if engagement < NUT_T - 0.08:
        raise RuntimeError(f"{screw_id} nut engagement {engagement}")
    if clearance <= 0 or contains_at(rear, x, tip2, z):
        raise RuntimeError(f"{screw_id} bottoms, clearance {clearance}")
    if overlap(trimmed, rear) > 0.05:
        raise RuntimeError(f"{screw_id} intersects the back")
    return {
        "inst": inst,
        "mesh": trimmed,
        "row": {
            "station": screw_id,
            "catalog": "M2x3",
            "under_head_mm": round(under_len, 2),
            "overall_mm": round(head2 - tip2, 2),
            "head_outer_y": round(head2, 2),
            "under_head_y": round(head2 - HEAD_H, 2),
            "tip_y": round(tip2, 2),
            "nut_y": [round(nut_far, 2), round(nut_near, 2)],
            "nominal_engagement_mm": round(engagement, 2),
            "full_nut": engagement >= NUT_T - 0.08,
            "tip_past_nut_mm": round(nut_far - tip2, 2),
            "bore_end_y": round(bore, 2),
            "tip_clearance_mm": round(clearance, 2),
            "bottoms": False,
            "pull_0_12mm_flank_mm3": hit,
            "nut_moved_mm": 0,
        },
    }


def fix_jamb(manifest, hosts, covers, screw_id, nut_id, host_id, cover_id, before_mag):
    inst, screw = load_world(manifest, screw_id)
    nut_inst, nut = load_world(manifest, nut_id)
    cover_inst, cover = covers[cover_id][0], covers[cover_id][1]
    host = hosts[host_id][1]
    center = screw.bounds.mean(axis=0)
    x, z = float(center[0]), float(center[2])
    y_lo, y_hi = float(screw.bounds[0, 1]) - 0.3, float(screw.bounds[1, 1]) + 1.2
    head = extreme_y(screw, x, z, 1.5, y_lo, y_hi, want_min=True)
    tip = extreme_y(screw, x, z, 0.4, y_lo, y_hi, want_min=False)
    under = head + HEAD_H
    new_tip = under + 8.0
    shift, moved, hit = seated_shift(screw, nut, under, new_tip)
    nut_near = float(moved.bounds[0, 1])
    nut_far = float(moved.bounds[1, 1])
    engagement = interval_overlap(under, new_tip, nut_near, nut_far)
    if engagement < NUT_T - 0.08:
        raise RuntimeError(f"{screw_id} engagement {engagement}")
    bore_now = first_solid(host, x, z, tip - 0.2, +1)
    y = bore_now
    while contains_at(host, x, y, z) and y < bore_now + 30:
        y += 0.05
    outer = y
    skin_left = outer - (new_tip + 0.6)
    if skin_left < 2.0:
        raise RuntimeError(f"{screw_id} only {skin_left:.2f} mm of skin if the bore is deepened")
    bore_end = new_tip + 0.6
    if bore_end < nut_far + 0.55:
        bore_end = nut_far + 0.55
    pocket = hex_y(
        x,
        nut_near - 0.2,
        nut_far + 0.2,
        z,
        (4.0 + 0.4) / math.sqrt(3),
    )
    slot_x0, slot_x1 = (x + 1.6, x + 5.2) if x < 400 else (x - 5.2, x - 1.6)
    slot = box(slot_x0, nut_near + 0.15, z - 0.95, slot_x1, nut_far - 0.15, z + 0.95)
    pilot = cyl_y(x, bore_now - 0.4, bore_end, z, 1.2)
    cut = diff(host, [pocket, slot, pilot], f"{host_id} {screw_id}")
    drop = float(host.volume - cut.volume)
    if drop < 0.5 or drop > 80:
        raise RuntimeError(f"{screw_id} removed {drop:.1f} mm3")
    if not magnets_hold(before_mag[host_id], magnet_state(cut, MAGNET_PTS)):
        raise RuntimeError(f"{screw_id} changed a magnet seat")
    extended = union(
        [screw, cyl_y(x, tip - 0.2, new_tip, z, 0.7)],
        screw_id + " tip",
    )
    head2 = extreme_y(extended, x, z, 1.5, head - 0.2, under, want_min=True)
    tip2 = extreme_y(extended, x, z, 0.4, tip - 0.2, new_tip + 0.3, want_min=False)
    under_len = (tip2 - head2) - HEAD_H
    bore2 = first_solid(cut, x, z, tip2 - 0.3, +1)
    clearance = bore2 - tip2
    past_nut = bore2 - nut_far
    if under_len < 7.9 or under_len > 8.15:
        raise RuntimeError(f"{screw_id} under-head {under_len} is not M2x8")
    if clearance < 0.5 or past_nut < 0.5:
        raise RuntimeError(f"{screw_id} clearance tip {clearance} past nut {past_nut}")
    if contains_at(cut, x, tip2, z) or contains_at(cut, x, bore2 - 0.05, z):
        raise RuntimeError(f"{screw_id} tip is in solid")
    # Far skin still closed, and the magnet-side sample above was unchanged.
    if not contains_at(cut, x, outer - 0.4, z):
        raise RuntimeError(f"{screw_id} opened the far skin")
    # The stile is open on the slot side, so the lip is a crescent, not a full ring.
    # The axis stays a 2.5 mm hole. Plastic just outside that hole, toward the head, stops the nut.
    lip_y = nut_near - 0.45
    if contains_at(cut, x, lip_y, z):
        raise RuntimeError(f"{screw_id} lip hole is closed")
    bearing = int(ring(cut, x, lip_y, z, 1.7).sum())
    if bearing < 3:
        raise RuntimeError(f"{screw_id} lip is open ({bearing} bearing samples)")
    if int(ring(cut, x, (nut_near + nut_far) / 2, z, 1.7).sum()) > 2:
        raise RuntimeError(f"{screw_id} nut pocket is closed")
    if overlap(moved, cut) > 0.05 or overlap(extended, cut) > 0.05:
        raise RuntimeError(f"{screw_id} fastener intersects the host")
    ok, hit2 = phase_ok(extended, moved)
    if not ok:
        raise RuntimeError(f"{screw_id} extended screw lost the thread")
    # Probe just inside the slot mouth. The point has to be in the retainer, not on its face.
    mouth_x = (slot_x1 - 0.35) if x < 400 else (slot_x0 + 0.35)
    mouth = np.array([[mouth_x, (nut_near + nut_far) / 2, z]])
    ear_added = False
    if not bool(cover.contains(mouth)[0]):
        outside = mouth_x + (0.8 if x < 400 else -0.8)
        ear = box(
            min(outside, x),
            min(float(cover.bounds[0, 1]), nut_near - 0.2),
            z - 2.2,
            max(outside, x),
            max(float(cover.bounds[1, 1]), nut_far + 0.2),
            z + 2.2,
        )
        cover = union([cover, ear], cover_id + " slot cover")
        ear_added = True
        if not bool(cover.contains(mouth)[0]):
            raise RuntimeError(f"{screw_id} side slot is not covered")
    hosts[host_id][1] = cut
    covers[cover_id] = (cover_inst, cover, True if ear_added else covers[cover_id][2])
    nut_inst["transform"][1][3] = round(float(nut_inst["transform"][1][3]) - shift, 4)
    return {
        "inst": inst,
        "mesh": extended,
        "x": x,
        "z": z,
        "row": {
            "station": screw_id,
            "host": host_id,
            "catalog": "M2x8",
            "under_head_mm": round(under_len, 2),
            "overall_mm": round(tip2 - head2, 2),
            "head_outer_y": round(head2, 2),
            "under_head_y": round(head2 + HEAD_H, 2),
            "tip_y": round(tip2, 2),
            "nut_y": [round(nut_near, 2), round(nut_far, 2)],
            "nut_moved_toward_head_mm": round(shift, 2),
            "nominal_engagement_mm": round(engagement, 2),
            "full_nut": True,
            "tip_past_nut_mm": round(tip2 - nut_far, 2),
            "bore_end_y": round(bore2, 2),
            "tip_clearance_mm": round(clearance, 2),
            "bore_past_nut_mm": round(past_nut, 2),
            "skin_after_bore_mm": round(outer - bore2, 2),
            "side_slot_covered": True,
            "cover_extended": ear_added,
            "pull_0_12mm_flank_mm3": hit2,
            "lip_hole_mm": 2.5,
            "bottoms": False,
        },
    }


def refresh_print(part_id, poses):
    local = tm.load(os.path.join(STL, part_id + ".stl"), force="mesh")
    flat = lay_flat(local)
    os.makedirs(os.path.join(STL, "print"), exist_ok=True)
    flat.export(os.path.join(STL, "print", part_id + ".stl"))
    extents = [round(float(v), 2) for v in flat.extents]
    key = part_id + ".stl"
    old = poses["parts"][key]["print_extents_mm"]
    if max(abs(a - b) for a, b in zip(extents, old)) > 2.0:
        raise RuntimeError(f"{part_id} print extents changed {old} -> {extents}")
    poses["parts"][key]["print_extents_mm"] = extents
    poses["parts"][key]["margin_to_310x300x315_mm"] = [
        round(310 - extents[0], 1),
        round(300 - extents[1], 1),
        round(315 - extents[2], 1),
    ]
    if min(poses["parts"][key]["margin_to_310x300x315_mm"]) < 0:
        raise RuntimeError(f"{part_id} no longer fits the bed")


def update_part(manifest, part_id, mesh):
    for item in manifest["parts"]:
        if item["id"] == part_id:
            item["triangles"] = int(len(mesh.faces))
            item["volume_mm3"] = round(float(mesh.volume), 1)
            item["bbox_mm"] = [round(float(v), 2) for v in mesh.extents]
            item["watertight"] = True
            item["bodies"] = 1
            return
    raise RuntimeError(part_id)


def main():
    manifest = json.load(open(MANIFEST, encoding="utf8"))
    if manifest.get("version") != "6.5.2":
        raise SystemExit("refusing to run: version is " + str(manifest.get("version")))
    _rear_inst, rear = load_world(manifest, "rear")
    hosts = {}
    before_mag = {}
    for iid in ("walls-l1", "walls-l2", "side"):
        inst, mesh = load_world(manifest, iid)
        hosts[iid] = [inst, mesh]
        before_mag[iid] = magnet_state(mesh, MAGNET_PTS)
    covers = {}
    for _s, _n, _h, cover_id in JAMBS:
        if cover_id not in covers:
            inst, mesh = load_world(manifest, cover_id)
            covers[cover_id] = [inst, mesh, False]

    backs = [
        fix_back(manifest, rear, "adult-screw-back-l", "nut-back-l"),
        fix_back(manifest, rear, "adult-screw-back-r", "nut-back-r"),
    ]
    jambs = []
    section = None
    for screw_id, nut_id, host_id, cover_id in JAMBS:
        row = fix_jamb(manifest, hosts, covers, screw_id, nut_id, host_id, cover_id, before_mag)
        jambs.append(row)
        if screw_id == "adult-screw-jl1":
            section = row
        # The magnet signature must still match the original after every cut on this host.
        if not magnets_hold(before_mag[host_id], magnet_state(hosts[host_id][1], MAGNET_PTS)):
            raise RuntimeError(host_id + " magnet seats changed")

    poses = json.load(open(os.path.join(REPORT, "print-orientations.json"), encoding="utf8"))
    for item in backs + jambs:
        solid = write_world(item["inst"], item["mesh"])
        update_part(manifest, item["inst"]["part"], solid)
        note_len = "M2x3" if "back" in item["inst"]["id"] else "M2x8"
        under = item["row"]["under_head_mm"]
        for part in manifest["parts"]:
            if part["id"] == item["inst"]["part"]:
                part["print"] = False
                part["reference_only"] = True
                part["note"] = (
                    f"REFERENCE ONLY. Not a printed part. Nominal ISO 1580 {note_len}, "
                    f"under-head {under} mm, head 3.8 x 1.6 mm, pitch 0.4 mm. "
                    "Not measured. Not a safety certification."
                )
    for host_id, (inst, mesh) in hosts.items():
        solid = write_world(inst, mesh)
        update_part(manifest, inst["part"], solid)
        refresh_print(inst["part"], poses)
    for cover_id, (inst, mesh, changed) in covers.items():
        if not changed:
            continue
        solid = write_world(inst, mesh)
        update_part(manifest, inst["part"], solid)
        refresh_print(inst["part"], poses)

    for name in METAL:
        print_path = os.path.join(STL, "print", name + ".stl")
        if os.path.exists(print_path):
            raise RuntimeError(name + " is in the print set")

    rows = [item["row"] for item in backs + jambs]
    bom_path = os.path.join(REPORT, "print-bom.json")
    bom = json.load(open(bom_path, encoding="utf8"))
    bom["purchased_hardware"][0]["drawn_overall_length_mm"] = {"back": 4.6, "jamb": 9.6}
    bom["purchased_hardware"][0]["drawn_under_head_length_mm"] = {"back": 3.0, "jamb": 8.0}
    bom["purchased_hardware"][0]["catalog_callout"] = (
        "2 x M2x3 on the back and 4 x M2x8 on the jambs. "
        "Those are under-head lengths. Head drawn 3.8 mm diameter by 1.6 mm, flat driver slot. "
        "Not printed. Not a measured fit and not certified."
    )
    bom["purchased_hardware"][0]["stations"] = rows
    bom["head_driver_pocket"] = (
        "Nominal pan head 3.8 x 1.6 mm and a flat driver slot. "
        "The recess is a design allowance for that head. Unprinted. Not certified."
    )
    bom["retention_physically_verified"] = False
    bom["zero_intersection_is_thread_proof"] = False
    bom["version"] = "6.5.3"
    with open(bom_path, "w", encoding="utf8") as handle:
        json.dump(bom, handle, indent=2)
        handle.write("\n")

    fastener = json.load(open(os.path.join(REPORT, "fastener.json"), encoding="utf8"))
    by_id = {row["station"]: row for row in rows}
    for station in fastener["stations"]:
        row = by_id[station["screw"]]
        station["catalog"] = row["catalog"]
        station["under_head_mm"] = row["under_head_mm"]
        station["nominal_engagement_mm"] = row["nominal_engagement_mm"]
        station["tip_clearance_mm"] = row["tip_clearance_mm"]
        station["pull_0_12mm_flank_mm3"] = row["pull_0_12mm_flank_mm3"]
        station["measured"] = False
    fastener["length_note"] = (
        "Back catalog length is M2x3. Jamb catalog length is M2x8. "
        "Engagement is the overlap of the under-head interval and the nut interval. "
        "It is not a mesh-collision proxy. Not physically tested."
    )
    fastener["safety_certification"] = False
    with open(os.path.join(REPORT, "fastener.json"), "w", encoding="utf8") as handle:
        json.dump(fastener, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(REPORT, "fastener-length.json"), "w", encoding="utf8") as handle:
        json.dump({"version": "6.5.3", "stations": rows}, handle, indent=2)
        handle.write("\n")

    with open(os.path.join(REPORT, "print-orientations.json"), "w", encoding="utf8") as handle:
        json.dump(poses, handle, indent=2)
        handle.write("\n")

    manifest["version"] = "6.5.3"
    with open(MANIFEST, "w", encoding="utf8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    # Reload the saved jl1 station so the section is the file on disk.
    _i, host = load_world(manifest, "walls-l1")
    _s, screw = load_world(manifest, "adult-screw-jl1")
    _n, nut = load_world(manifest, "nut-jl1")
    jl1 = next(item["row"] for item in jambs if item["row"]["station"] == "adult-screw-jl1")
    title = (
        f"Jamb jl1 axial section. M2x8 under-head {jl1['under_head_mm']} mm. "
        f"Nut engagement {jl1['nominal_engagement_mm']} mm. "
        f"Bore past the tip {jl1['tip_clearance_mm']} mm. Not a physical test."
    )
    draw_section(
        [host, screw, nut],
        [section["x"], 280, section["z"]],
        [1, 0, 0],
        (272, 290, 28, 44, 70, 40, 920, 600),
        os.path.join(REPORT, "jamb-axial-section.png"),
        title,
        [(28, 64, 58), (40, 70, 140), (120, 90, 40)],
    )
    check = os.path.join(ROOT, "check.mjs")
    text = open(check, encoding="utf8").read().replace("=== '6.5.2'", "=== '6.5.3'", 1)
    open(check, "w", encoding="utf8").write(text)
    readme = os.path.join(ROOT, "README.md")
    body = open(readme, encoding="utf8").read()
    body = body.replace("v6.5.2", "v6.5.3", 1)
    body = body.replace(
        "The drawn under-head lengths are 3.5 mm on the back and 7.7 mm on the jambs, so they are not catalog M2×5 or M2×10 screws.",
        "The back screws are nominal M2×3 and the jamb screws are nominal M2×8. Both figures are under-head lengths. The head is drawn 3.8 × 1.6 mm.",
    )
    open(readme, "w", encoding="utf8").write(body)
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
