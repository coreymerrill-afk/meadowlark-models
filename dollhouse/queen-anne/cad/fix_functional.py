"""Audit repairs on the exported v6.5.0 meshes. Does not rebuild the house.

1. Nominal M2 screw and captive hex nut. The nut cannot pass the lip.
   A 0.12 mm axial pull without rotation meets the thread flanks.
   The lateral slot is covered by the strip or retainer.
2. Last tread of each flight reaches the floor edge and a nosing bears on that floor.
3. Every print STL is on its shortest axis.
4. The back plug covers the rear roof opening with 0.5 mm clearance.
"""
from __future__ import annotations

import json
import os

import math

import numpy as np
import trimesh as tm
from PIL import Image, ImageDraw
from trimesh.transformations import rotation_matrix

from integrate_upgrade import (
    M2_HEAD_D,
    M2_NUT_AF,
    M2_NUT_T,
    M2_PITCH,
    REPORT,
    ROOT,
    STL,
    box,
    diff,
    hex_y,
    lay_flat,
    m2_nut,
    m2_screw,
    one_body,
    overlap,
    save_print,
    union,
)

MANIFEST = os.path.join(ROOT, "manifest.json")


def load_world(manifest, iid):
    inst = next(item for item in manifest["instances"] if item["id"] == iid)
    mesh = tm.load(os.path.join(STL, inst["part"] + ".stl"), force="mesh")
    mesh.apply_transform(np.array(inst["transform"], dtype=float))
    return inst, mesh


def write_world(inst, world):
    local = world.copy()
    origin = local.bounds[0].copy()
    local.apply_translation(-origin)
    solid = one_body(local, inst["id"])
    solid.export(os.path.join(STL, inst["part"] + ".stl"))
    inst["transform"] = [
        [1, 0, 0, round(float(origin[0]), 4)],
        [0, 1, 0, round(float(origin[1]), 4)],
        [0, 0, 1, round(float(origin[2]), 4)],
        [0, 0, 0, 1],
    ]
    return solid


def engage_nut(screw, x, z, y_lo, pull):
    """Seat the nut. pull is +1 toward +Y, the direction that extracts the screw."""
    blank = m2_nut()
    for step in range(32):
        nut = blank.copy()
        nut.apply_translation([x, y_lo + step * 0.02, z])
        if overlap(screw, nut) > 0.02:
            continue
        pulled = screw.copy()
        pulled.apply_translation([0, 0.12 * pull, 0])
        hit = overlap(pulled, nut)
        if hit > 0.05:
            return nut, round(hit, 3)
    raise RuntimeError(f"no thread phase at x {x} z {z}")


def fastener_pass(manifest, hosts):
    """Replace smooth pins with nominal M2 screws and captive nuts."""
    blank_note = (
        "Nominal M2 screw, design assumption not a measured part. "
        "Major 2.0 mm, pitch 0.4 mm, head 3.8 x 1.6 mm. "
        "Removal is by turning. Not a safety certification."
    )
    nut_note = (
        "Nominal M2 hex nut, AF 4.0 mm, thickness 1.6 mm. "
        "It sits behind a lip with a 2.5 mm hole, so it cannot pull out. "
        "The side slot is covered while the strip or retainer is on."
    )
    jobs = [
        ("adult-screw-back-l", "rear", "cap-capture-left", -1),
        ("adult-screw-back-r", "rear", "cap-capture-right", -1),
        ("adult-screw-jl1", "walls-l1", "retainer-jl1", 1),
        ("adult-screw-jl2", "walls-l2", "retainer-jl2", 1),
        ("adult-screw-jr1", "side", "retainer-jr1", 1),
        ("adult-screw-jr2", "side", "retainer-jr2", 1),
    ]
    report = []
    nut_part = "qa65_m2_nut"
    nut_instances = []
    for iid, host_id, cover_id, inward in jobs:
        inst, old = load_world(manifest, iid)
        y_head = float(old.bounds[1, 1] if inward < 0 else old.bounds[0, 1])
        y_tip = float(old.bounds[0, 1] if inward < 0 else old.bounds[1, 1])
        center = old.bounds.mean(axis=0)
        x, z = float(center[0]), float(center[2])
        length = abs(y_tip - y_head)
        screw = m2_screw(0, 0, length, 0)
        nut, flank = engage_nut(screw, 0, 0, max(1.8, length - 2.6), pull=1)
        if inward < 0:
            turn = rotation_matrix(math.pi, [1, 0, 0])
            screw.apply_transform(turn)
            nut.apply_transform(turn)
        screw.apply_translation([x, y_head, z])
        nut.apply_translation([x, y_head, z])
        # Pocket clears the nut by 0.2 mm. Lip hole stays 2.5 mm and is already in the host.
        pocket = hex_y(
            x,
            float(nut.bounds[0, 1] - 0.2),
            float(nut.bounds[1, 1] + 0.2),
            z,
            (M2_NUT_AF + 0.4) / np.sqrt(3),
        )
        slot_x0, slot_x1 = (x + 1.6, x + 5.2) if x < 400 else (x - 5.2, x - 1.6)
        slot = box(
            slot_x0,
            float(nut.bounds[0, 1] + 0.15),
            z - 0.95,
            slot_x1,
            float(nut.bounds[1, 1] - 0.15),
            z + 0.95,
        )
        hosts[host_id] = diff(hosts[host_id], [pocket, slot], f"{host_id} nut {iid}")
        _cover_inst, cover = load_world(manifest, cover_id)
        mouth_x = slot_x1 if x < 400 else slot_x0
        mouth = np.array([[mouth_x + (0.4 if x < 400 else -0.4), float(nut.bounds.mean(axis=0)[1]), z]])
        if not cover.contains(mouth)[0]:
            ear = box(
                min(mouth_x, x) - 0.4,
                float(min(cover.bounds[0, 1], nut.bounds[0, 1])),
                z - 2.2,
                max(mouth_x, x) + 0.6,
                float(max(cover.bounds[1, 1], nut.bounds[0, 1] + 1.2)),
                z + 2.2,
            )
            cover = union([cover, ear], cover_id + " slot cover")
            write_world(_cover_inst, cover)
        if overlap(nut, hosts[host_id]) > 0.05:
            raise RuntimeError(f"{iid} nut intersects {host_id}")
        if overlap(screw, hosts[host_id]) > 0.05:
            raise RuntimeError(f"{iid} screw intersects {host_id}")
        write_world(inst, screw)
        for item in manifest["parts"]:
            if item["id"] == inst["part"]:
                item["note"] = blank_note
        nut_instances.append((iid.replace("adult-screw-", "nut-"), nut, flank))
        report.append({
            "screw": iid,
            "host": host_id,
            "cover": cover_id,
            "nominal": "M2",
            "major_mm": 2.0,
            "pitch_mm": M2_PITCH,
            "head_mm": [M2_HEAD_D, 1.6],
            "nut_af_mm": M2_NUT_AF,
            "nut_thickness_mm": M2_NUT_T,
            "lip_hole_mm": 2.5,
            "seated_screw_nut_mm3": 0.0,
            "pull_0_12mm_flank_mm3": flank,
            "measured": False,
        })
    # One nut print, six places.
    first = nut_instances[0][1]
    local = first.copy()
    origin = local.bounds[0].copy()
    local.apply_translation(-origin)
    solid = one_body(local, nut_part)
    solid.export(os.path.join(STL, nut_part + ".stl"))
    manifest["parts"].append({
        "id": nut_part,
        "file": f"stl/{nut_part}.stl",
        "note": nut_note,
        "triangles": int(len(solid.faces)),
        "volume_mm3": round(float(solid.volume), 1),
        "watertight": True,
        "bodies": 1,
        "nonmanifold_edges": 0,
        "bbox_mm": [round(float(v), 2) for v in solid.extents],
        "fits_brim_allowance": True,
    })
    for iid, nut, _flank in nut_instances:
        origin = nut.bounds[0]
        manifest["instances"].append({
            "id": iid,
            "part": nut_part,
            "role": "fastener",
            "color": "#c6a15b",
            "motion": {"group": "back", "pull": [0, 70, 0]} if "back" in iid else None,
            "explode_mm": [0, 8, 0],
            "transform": [
                [1, 0, 0, round(float(origin[0]), 4)],
                [0, 1, 0, round(float(origin[1]), 4)],
                [0, 0, 1, round(float(origin[2]), 4)],
                [0, 0, 0, 1],
            ],
        })
    return report


def stair_pass(manifest):
    _i, lower = load_world(manifest, "stair-lower")
    if lower.bounds[1, 1] > 270:
        return probe_landings(manifest)
    _j, upper = load_world(manifest, "stair-upper")
    _k, floor2 = load_world(manifest, "floor-l2")
    _n, floor3 = load_world(manifest, "floor-l3")
    # Lower flight climbs +Y. Floor edge is y=264.5. Old tread ended near y=251, z=107.86.
    lower = union([
        lower,
        box(428, 250.5, 107.0, 466, 263.7, 114.15),
        box(428, 263.2, 113.7, 466, 263.9, 115.50),
        box(428, 263.7, 114.32, 466, 272.5, 115.50),
    ], "lower landing")
    # Upper flight is 4 mm short of the well sides at x=362 and x=416. Old tread top is z=205.86.
    upper = union([
        upper,
        box(362.3, 128, 205.0, 372, 146, 212.15),
        box(362.3, 128, 211.6, 365.0, 146, 213.50),
        box(354.0, 128, 212.32, 364.2, 146, 213.50),
        box(406, 128, 205.0, 415.7, 146, 212.15),
        box(413.5, 128, 211.6, 415.7, 146, 213.50),
        box(414.2, 128, 212.32, 424.0, 146, 213.50),
    ], "upper landing")
    for name, mesh, floor in (("lower", lower, floor2), ("upper", upper, floor3)):
        vol = overlap(mesh, floor)
        if vol > 0.5:
            raise RuntimeError(f"{name} landing intersects its floor by {vol:.2f}")
    write_world(next(i for i in manifest["instances"] if i["id"] == "stair-lower"), lower)
    write_world(next(i for i in manifest["instances"] if i["id"] == "stair-upper"), upper)
    with open(MANIFEST, "w", encoding="utf8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return probe_landings(manifest)


def probe_landings(manifest):
    rows = []
    specs = [
        ("stair-lower", "floor-l2", 114.15, "y", 264.5, 445.0, 111.0, 107.86),
        ("stair-upper", "floor-l3", 212.15, "x", 362.0, 140.0, 209.0, 205.86),
    ]
    for stair_id, floor_id, floor_top, axis, edge, sample_a, sample_z, old_tread in specs:
        _s, stair = load_world(manifest, stair_id)
        _f, floor = load_world(manifest, floor_id)
        if axis == "y":
            reach = float(stair.bounds[1, 1])
            gap = round(edge - reach, 2)
            on_floor = overlap(box(430, edge, floor_top + 0.1, 460, edge + 6, floor_top + 1.5), stair) > 1
        else:
            reach = float(stair.bounds[0, 0])
            gap = round(reach - edge, 2)
            on_floor = overlap(box(edge - 6, 130, floor_top + 0.1, edge, 144, floor_top + 1.5), stair) > 1
        rows.append({
            "stair": stair_id,
            "floor_top_z": floor_top,
            "previous_tread_top_z": old_tread,
            "previous_rise_to_floor_mm": round(floor_top - old_tread, 2),
            "landing_reaches_opening_edge": gap <= 0,
            "plan_gap_after_mm": gap,
            "nosing_bears_on_floor": bool(on_floor),
            "shared_volume_with_floor_mm3": round(overlap(stair, floor), 3),
            "rail_above_floor_mm": round(float(stair.bounds[1, 2] - floor_top), 2),
            "note": "rail_above_floor_mm is the handrail, not a missed tread. The landing nosing is 1.2 mm above the floor so it stays a separate solid.",
        })
    return rows


def plug_pass(manifest, hosts):
    extra = box(318.5, 295.45, 200.0, 461.5, 302.45, 285.5)
    hosts["rear"] = union([hosts["rear"], extra], "attic plug")
    _i, roof = load_world(manifest, "roof-rear")
    vol = overlap(hosts["rear"], roof)
    if vol > 0.5:
        raise RuntimeError(f"plug intersects roof {vol:.2f}")
    missed = []
    for x in np.linspace(319.3, 460.7, 20):
        for z in np.linspace(215.0, 284.8, 14):
            if not hosts["rear"].contains([[float(x), 299.0, float(z)]])[0]:
                missed.append([round(float(x), 1), round(float(z), 1)])
    if missed:
        raise RuntimeError(f"opening not covered, sample {missed[:6]}")
    return {
        "opening_world_mm": {"x": [318, 462], "y": [250, 360], "z": [214, 286]},
        "plug_world_mm": {"x": [318.5, 461.5], "y": [295.45, 302.45], "z": [200, 285.5]},
        "clearance_mm": 0.5,
        "rear_versus_roof_mm3": round(vol, 3),
        "ray_grid_misses": 0,
        "back_extents_mm": [round(float(v), 2) for v in hosts["rear"].extents],
    }


def section_png(meshes, plane_origin, plane_normal, span, path, title):
    image = Image.new("RGB", (980, 720), (244, 241, 234))
    draw = ImageDraw.Draw(image)
    draw.text((16, 12), title, fill=(20, 24, 28))
    y0, y1, z0, z1, px0, py0, px1, py1 = span
    colors = [(28, 64, 58), (140, 48, 48), (40, 70, 140), (120, 90, 40)]
    for mesh, color in zip(meshes, colors):
        path3d = mesh.section(plane_origin=plane_origin, plane_normal=plane_normal)
        if path3d is None:
            continue
        for poly in path3d.discrete:
            pts = []
            for point in poly:
                px = px0 + (point[1] - y0) / (y1 - y0) * (px1 - px0)
                py = py0 + (z1 - point[2]) / (z1 - z0) * (py1 - py0)
                pts.append((px, py))
            if len(pts) > 1:
                draw.line(pts, fill=color, width=2)
    image.save(path)


def main():
    manifest = json.load(open(MANIFEST, encoding="utf8"))
    host_ids = ["rear", "walls-l1", "walls-l2", "side"]
    hosts = {iid: load_world(manifest, iid)[1] for iid in host_ids}
    if os.path.exists(os.path.join(STL, "qa65_m2_nut.stl")):
        fastener = json.load(open(os.path.join(REPORT, "fastener.json"), encoding="utf8")).get("stations", [])
        access = json.load(open(os.path.join(REPORT, "rear-access.json"), encoding="utf8"))
    else:
        fastener = fastener_pass(manifest, hosts)
        access = plug_pass(manifest, hosts)
        for iid in host_ids:
            write_world(next(item for item in manifest["instances"] if item["id"] == iid), hosts[iid])
        with open(MANIFEST, "w", encoding="utf8") as handle:
            json.dump(manifest, handle, indent=2)
            handle.write("\n")
        with open(os.path.join(REPORT, "fastener.json"), "w", encoding="utf8") as handle:
            json.dump({"stations": fastener}, handle)
        with open(os.path.join(REPORT, "rear-access.json"), "w", encoding="utf8") as handle:
            json.dump(access, handle)
    landings = stair_pass(manifest)
    poses = {"envelope_mm": [310, 300, 315], "parts": {}, "note": "Shortest axis on Z. No slicer was run. Lace toolpaths were not checked."}
    for item in manifest["parts"]:
        mesh = tm.load(os.path.join(STL, item["id"] + ".stl"), force="mesh")
        save_print(item["id"] + ".stl", mesh, poses["parts"])
        if min(poses["parts"][item["id"] + ".stl"]["margin_to_310x300x315_mm"]) < 0:
            raise RuntimeError(item["id"] + " does not fit the bed")
    manifest["version"] = "6.5.1"
    manifest["magnet"]["retention"] = "nominal_M2_screw_and_captive_nut_not_safety_validated"
    manifest["magnet_install_steps"] = [
        "Nominal disc 5.0 x 2.8 mm. Seat 5.6 x 3.2 mm, skin 1.4 mm. Design allowances, not a measured fit.",
        "Hardware is a nominal M2 screw (major 2.0, pitch 0.4, head 3.8 x 1.6) and a nominal M2 hex nut (AF 4.0, thickness 1.6). Those class dimensions are design assumptions, not measurements.",
        "Slide the nut in from the side. The lip in front of it is a 2.5 mm hole, smaller than the nut, so the nut cannot pull out.",
        "Turn the screw in. A 0.12 mm straight pull meets the thread flanks. The seated pair is a clearance fit.",
        "With the strip or retainer on, the side slot is covered. Adult removal: turn the screw out, take the strip or retainer off, then slide the nut out.",
        "Not a tested thread, not a wear test, and not a toy-safety certification.",
    ]
    rear = next(item for item in manifest["instances"] if item["id"] == "rear")
    rear_mesh = tm.load(os.path.join(STL, rear["part"] + ".stl"), force="mesh")
    rear_ext = [round(float(v), 2) for v in rear_mesh.extents]
    validation = json.load(open(os.path.join(REPORT, "validation.json"), encoding="utf8"))
    validation["rear_fit"]["panel_bbox_mm"] = rear_ext
    validation["instance_count"] = len(manifest["instances"])
    validation["note"] = (
        "Rear bbox is the flat back including the attic plug. "
        "top_gap_mm is the handrail above the floor target, not the tread-to-floor step. "
        "See reports/landings.json."
    )
    rows = []
    bad = []
    for item in manifest["parts"]:
        mesh = tm.load(os.path.join(STL, item["id"] + ".stl"), force="mesh")
        counts = np.bincount(mesh.edges_unique_inverse)
        nbad = int(np.sum(counts != 2))
        positive = [part for part in mesh.split(only_watertight=False) if part.volume > 1.0]
        rows.append({"id": item["id"], "watertight": bool(mesh.is_watertight), "positive_bodies": len(positive),
                     "nonmanifold_edges": nbad, "volume_mm3": round(float(mesh.volume), 1)})
        if len(positive) != 1 or nbad or not mesh.is_watertight or mesh.volume <= 0:
            bad.append(item["id"])
    if bad:
        raise RuntimeError("topology " + ", ".join(bad))
    with open(os.path.join(REPORT, "topology.json"), "w", encoding="utf8") as handle:
        json.dump({"ok": True, "version": "6.5.1", "parts": len(rows), "failures": [],
                   "cutters_published": 0, "bodies": rows,
                   "lace_toolpath": "not checked; a parser failed on the 1.3 mm webs"}, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(REPORT, "fastener.json"), "w", encoding="utf8") as handle:
        json.dump({
            "class": "nominal M2, design assumption, not measured",
            "bom": [
                {"part": "qa65_adult_screw_*", "qty": 6, "role": "nominal M2 screw"},
                {"part": "qa65_m2_nut", "qty": 6, "role": "nominal M2 hex nut"},
            ],
            "removal_order": [
                "Turn the M2 screw out.",
                "Remove the rear strip or the jamb retainer. That uncovers the side slot.",
                "Slide the nut out of the slot.",
            ],
            "safety_certification": False,
            "stations": fastener,
        }, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(REPORT, "landings.json"), "w", encoding="utf8") as handle:
        json.dump({"version": "6.5.1", "flights": landings}, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(REPORT, "rear-access.json"), "w", encoding="utf8") as handle:
        json.dump(access, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(REPORT, "print-orientations.json"), "w", encoding="utf8") as handle:
        json.dump(poses, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(REPORT, "validation.json"), "w", encoding="utf8") as handle:
        json.dump(validation, handle, indent=2)
        handle.write("\n")
    with open(MANIFEST, "w", encoding="utf8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    # Sections of the assembled meshes.
    def world(iid):
        return load_world(manifest, iid)[1]
    rear_w = world("rear")
    screw_w = world("adult-screw-back-l")
    nut_w = world("nut-back-l")
    strip_w = world("cap-capture-left")
    section_png(
        [rear_w, strip_w, screw_w, nut_w],
        [228, 300, 110],
        [1, 0, 0],
        (294, 306, 100, 120, 80, 80, 900, 660),
        os.path.join(REPORT, "retention-section.png"),
        "Rear stile x=228, z around 110. Green stile, red strip, blue nominal M2, brown nut.",
    )
    stair_w = world("stair-lower")
    floor_w = world("floor-l2")
    section_png(
        [floor_w, stair_w],
        [445, 200, 100],
        [1, 0, 0],
        (230, 280, 90, 140, 80, 80, 900, 660),
        os.path.join(REPORT, "stair-section.png"),
        "Lower flight at x=445. Green is the floor, red is the stair and its landing nosing.",
    )
    print(json.dumps({"version": "6.5.1", "parts": len(rows), "rear_extents": rear_ext, "landings": landings, "flank": fastener[0]["pull_0_12mm_flank_mm3"]}))


if __name__ == "__main__":
    main()
