"""v6.5.2 corrections only. No new ornament.

Full-width upper landing, lace printed on its flat back, metal kept out of the print set.
"""
from __future__ import annotations

import json
import os

import numpy as np
import trimesh as tm
from PIL import Image, ImageDraw
from trimesh.transformations import rotation_matrix

from integrate_upgrade import REPORT, ROOT, STL, box, one_body, overlap, union

MANIFEST = os.path.join(ROOT, "manifest.json")
METAL = {
    "qa65_adult_screw_back_l",
    "qa65_adult_screw_back_r",
    "qa65_adult_screw_jl1",
    "qa65_adult_screw_jl2",
    "qa65_adult_screw_jr1",
    "qa65_adult_screw_jr2",
    "qa65_m2_nut",
}
LACE = [
    "qa65_gable_verge_left",
    "qa65_gable_verge_right",
    "qa65_porch_frieze_1",
    "qa65_porch_frieze_2",
    "qa65_porch_frieze_3",
]


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


def back_on_bed(mesh):
    """Put the broad plate on z=0 and the key tabs on the top. Origin x=y=z=0."""
    out = mesh.copy()
    out.apply_transform(rotation_matrix(np.pi, [1, 0, 0], out.bounds.mean(axis=0)))
    z = out.vertices[:, 2]
    bins = np.arange(float(z.min()) - 0.05, float(z.max()) + 0.3, 0.15)
    hist, edges = np.histogram(z, bins)
    face_z = None
    for index, count in enumerate(hist):
        if count > 80:
            face_z = 0.5 * (edges[index] + edges[index + 1])
            break
    if face_z is None:
        raise RuntimeError("no plate face")
    out.apply_translation([-out.bounds[0, 0], -out.bounds[0, 1], -face_z])
    below = out.vertices[:, 2] < -0.05
    if int(below.sum()) > 30:
        raise RuntimeError("plate is not the low face")
    if below.any():
        out.vertices[below, 2] = 0.0
    out.apply_translation([0, 0, -float(out.bounds[0, 2])])
    out.apply_translation([-out.bounds[0, 0], -out.bounds[0, 1], 0])
    return out


def bed_contact(mesh):
    low = mesh.vertices[mesh.vertices[:, 2] < 0.35]
    span = low[:, :2].max(axis=0) - low[:, :2].min(axis=0)
    section = mesh.section(plane_origin=[0, 0, 0.2], plane_normal=[0, 0, 1])
    loops = 0 if section is None else len(section.discrete)
    counts = np.bincount(mesh.edges_unique_inverse)
    return {
        "origin_z": round(float(mesh.bounds[0, 2]), 4),
        "extents_mm": [round(float(v), 2) for v in mesh.extents],
        "h3c_margin_mm": [
            round(310 - float(mesh.extents[0]), 1),
            round(300 - float(mesh.extents[1]), 1),
            round(315 - float(mesh.extents[2]), 1),
        ],
        "vertices_below_0_35mm": int(len(low)),
        "bed_span_mm": [round(float(v), 1) for v in span],
        "loops_at_z_0_2": loops,
        "watertight": bool(mesh.is_watertight),
        "nonmanifold_edges": int(np.sum(counts != 2)),
    }


def upper_landing(manifest):
    inst, stair = load_world(manifest, "stair-upper")
    _f, floor = load_world(manifest, "floor-l3")
    # Full walking width is about x 366-412. The well is open there down to y~123.
    # Side strips sit on the floor. The center deck is the walking surface.
    deck = box(362.4, 123.0, 205.0, 415.6, 150.0, 213.5)
    left = box(354.0, 123.0, 212.32, 366.0, 150.0, 213.5)
    right = box(412.0, 123.0, 212.32, 424.0, 150.0, 213.5)
    merged = union([stair, deck, left, right], "upper full landing")
    vol = overlap(merged, floor)
    if vol > 0.5:
        raise RuntimeError(f"upper landing intersects floor {vol:.2f}")
    write_world(inst, merged)
    with open(MANIFEST, "w", encoding="utf8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return center_probe(manifest)


def center_probe(manifest):
    _i, stair = load_world(manifest, "stair-upper")
    x = 389.0
    section = stair.section(plane_origin=[x, 160, 180], plane_normal=[1, 0, 0])
    ys, zs = [], []
    for poly in section.discrete:
        for point in poly:
            ys.append(point[1])
            zs.append(point[2])
    ys, zs = np.array(ys), np.array(zs)
    walk = (ys < 150) & (zs > 208)
    return {
        "probe_x_mm": x,
        "walking_width_mm": 48,
        "y_min_of_landing_mm": round(float(ys[walk].min()), 2),
        "z_max_of_landing_mm": round(float(zs[walk].max()), 2),
        "floor_top_z": 212.15,
        "opening_y_mm": 123,
        "reaches_opening": bool(ys[walk].min() <= 124),
        "center_has_floor_height_surface": bool(zs[walk].max() >= 212),
    }


def draw_section(meshes, origin, normal, span, path, title, colors):
    image = Image.new("RGB", (980, 640), (244, 241, 234))
    draw = ImageDraw.Draw(image)
    draw.text((16, 12), title, fill=(20, 24, 28))
    a0, a1, b0, b1, px0, py0, px1, py1 = span
    # span axes: for normal X, plot Y and Z. For normal Z, plot X and Y.
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
                    px = px0 + (u - a0) / (a1 - a0) * (px1 - px0)
                    py = py0 + (b1 - v) / (b1 - b0) * (py1 - py0)
                else:
                    u, v = point[0], point[1]
                    px = px0 + (u - a0) / (a1 - a0) * (px1 - px0)
                    py = py0 + (b1 - v) / (b1 - b0) * (py1 - py0)
                pts.append((px, py))
            if len(pts) > 1:
                draw.line(pts, fill=color, width=2)
    image.save(path)


def pocket_wall(manifest):
    _i, rear = load_world(manifest, "rear")
    # Nut center from the placed nut.
    _n, nut = load_world(manifest, "nut-back-l")
    center = nut.bounds.mean(axis=0)
    # Walk +X and -X from just outside the nut until the solid ends.
    walls = []
    for sign in (1, -1):
        x = float(center[0])
        while rear.contains([[x, float(center[1]), float(center[2])]])[0] and abs(x - center[0]) < 20:
            x += sign * 0.2
        walls.append(round(abs(x - float(center[0])) - M2_AF_HALF(), 2))
    return walls


def M2_AF_HALF():
    return 2.0


def main():
    manifest = json.load(open(MANIFEST, encoding="utf8"))
    probe = upper_landing(manifest)
    if not probe["center_has_floor_height_surface"] or not probe["reaches_opening"]:
        raise RuntimeError("upper center landing failed " + str(probe))

    lace_report = {}
    for part_id in LACE:
        mesh = tm.load(os.path.join(STL, "print", part_id + ".stl"), force="mesh")
        flipped = one_body(back_on_bed(mesh), part_id + " bed")
        info = bed_contact(flipped)
        if info["origin_z"] != 0 or info["vertices_below_0_35mm"] < 100 or min(info["bed_span_mm"]) < 20:
            raise RuntimeError(part_id + " bed contact " + str(info))
        if min(info["h3c_margin_mm"]) < 0 or info["nonmanifold_edges"]:
            raise RuntimeError(part_id + " print unfit " + str(info))
        flipped.export(os.path.join(STL, "print", part_id + ".stl"))
        lace_report[part_id] = info

    poses_path = os.path.join(REPORT, "print-orientations.json")
    poses = json.load(open(poses_path, encoding="utf8"))
    for part_id, info in lace_report.items():
        poses["parts"][part_id + ".stl"] = {
            "pose": "flat back on the bed, key tabs up, origin z=0",
            "native_extents_mm": info["extents_mm"],
            "print_extents_mm": info["extents_mm"],
            "margin_to_310x300x315_mm": info["h3c_margin_mm"],
            "origin_z": 0,
        }
    for part_id in METAL:
        poses["parts"].pop(part_id + ".stl", None)
        print_path = os.path.join(STL, "print", part_id + ".stl")
        if os.path.exists(print_path):
            os.remove(print_path)
    poses["excluded_not_printed"] = sorted(METAL)
    poses["note"] = (
        "Metal reference screws and the nut are not in this print set. "
        "Verge and frieze prints sit on the flat back. No slicer was run."
    )
    with open(poses_path, "w", encoding="utf8") as handle:
        json.dump(poses, handle, indent=2)
        handle.write("\n")

    for item in manifest["parts"]:
        if item["id"] in METAL:
            item["print"] = False
            item["reference_only"] = True
            item["note"] = "REFERENCE ONLY. Not a printed part. " + item.get("note", "")
    manifest["bom"] = [row for row in manifest.get("bom", []) if row["part"] not in METAL]
    manifest["version"] = "6.5.2"
    purchased = {
        "not_printed": sorted(METAL),
        "print_part_count": sum(1 for item in manifest["parts"] if item["id"] not in METAL),
        "print_instance_count": sum(1 for item in manifest["instances"] if item["part"] not in METAL),
        "purchased_hardware": [
            {
                "item": "slotted pan head machine screw",
                "standard_assumption": "ISO 1580 form, ISO 965 M2 pitch 0.4 mm. Driver is a flat screwdriver in the drawn slot.",
                "count_back": 2,
                "count_jamb": 4,
                "drawn_overall_length_mm": {"back": 5.1, "jamb": 9.3},
                "drawn_head_height_mm": 1.6,
                "drawn_under_head_length_mm": {"back": 3.5, "jamb": 7.7},
                "catalog_callout": "None. M2x3, M2x4, M2x6, M2x8 and M2x10 are under-head lengths and do not equal 3.5 or 7.7. The drawing is not labeled as those parts.",
                "fit_assumption": "Shank major drawn 2.0 mm through a 2.5 mm lip hole. Not measured.",
            },
            {
                "item": "hex nut",
                "standard_assumption": "ISO 4032 M2. Across flats 4.0 mm, thickness 1.6 mm, pitch 0.4 mm. The mesh across corners is 4.62 mm, which is that hex.",
                "count": 6,
                "fit_assumption": "0.2 mm pocket clearance around the nut. The lip hole is 2.5 mm, smaller than the nut, so the nut cannot pull out.",
            },
        ],
        "retention_physically_verified": False,
        "zero_intersection_is_thread_proof": False,
    }
    with open(os.path.join(REPORT, "print-bom.json"), "w", encoding="utf8") as handle:
        json.dump(purchased, handle, indent=2)
        handle.write("\n")
    with open(MANIFEST, "w", encoding="utf8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    _s, stair = load_world(manifest, "stair-upper")
    draw_section(
        [stair],
        [389, 160, 180],
        [1, 0, 0],
        (110, 170, 190, 220, 70, 40, 920, 600),
        os.path.join(REPORT, "stair-upper-center-section.png"),
        "Upper stair at x=389, the center of the walking width. Landing reaches y=123 and z=213.5.",
        [(140, 48, 48)],
    )
    # Bed-contact plan views, five parts.
    sheet = Image.new("RGB", (1100, 780), (244, 241, 234))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 10), "Print bed contact at z=0.2 mm. Back is on the bed. Keys are up.", fill=(20, 24, 28))
    for index, part_id in enumerate(LACE):
        mesh = tm.load(os.path.join(STL, "print", part_id + ".stl"), force="mesh")
        section = mesh.section(plane_origin=[0, 0, 0.2], plane_normal=[0, 0, 1])
        ox, oy = 20 + (index % 3) * 360, 40 + (index // 3) * 360
        draw.text((ox, oy), part_id.replace("qa65_", ""), fill=(20, 24, 28))
        if section is None:
            continue
        ext = mesh.extents
        for poly in section.discrete:
            pts = []
            for point in poly:
                px = ox + 10 + point[0] / max(ext[0], 1) * 300
                py = oy + 320 - point[1] / max(ext[1], 1) * 280
                pts.append((px, py))
            if len(pts) > 1:
                draw.line(pts, fill=(28, 64, 58), width=1)
    sheet.save(os.path.join(REPORT, "bed-contact-section.png"))

    rear_i, rear = load_world(manifest, "rear")
    screw = load_world(manifest, "adult-screw-back-l")[1]
    nut = load_world(manifest, "nut-back-l")[1]
    strip = load_world(manifest, "cap-capture-left")[1]
    z = float(nut.bounds.mean(axis=0)[2])
    draw_section(
        [rear, strip, screw, nut],
        [228, 300, z],
        [0, 0, 1],
        (210, 250, 290, 310, 80, 40, 920, 600),
        os.path.join(REPORT, "fastener-slot-section.png"),
        "Plan at the back-left nut. Green stile, red strip covers the side slot, blue screw, brown nut. Slot is under the strip.",
        [(28, 64, 58), (140, 48, 48), (40, 70, 140), (120, 90, 40)],
    )
    # Pocket wall: from nut center sideways until the rear solid ends.
    center = nut.bounds.mean(axis=0)
    walls = []
    for sign in (1.0, -1.0):
        x = float(center[0])
        seen = False
        for _step in range(80):
            x += sign * 0.15
            inside = bool(rear.contains([[x, float(center[1]), float(center[2])]])[0])
            if inside:
                seen = True
            elif seen:
                break
        walls.append(round(abs(x - float(center[0])), 2))
    with open(os.path.join(REPORT, "print-bom.json"), "w", encoding="utf8") as handle:
        purchased["pocket_wall_from_nut_center_mm"] = {"minus_x": walls[1] if False else walls[0], "plus_x": walls[1] if len(walls) > 1 else None}
        purchased["pocket_wall_note"] = "Distance from the nut center to where the stile solid ends. The nut across-flats is 4.0 mm, so the wall outside the flats is this distance minus 2.0 mm. Not a measured print."
        json.dump(purchased, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"version": "6.5.2", "probe": probe if False else center_probe(manifest), "lace_loops": {k: v["loops_at_z_0_2"] for k, v in lace_report.items()}, "walls": walls}))


if __name__ == "__main__":
    main()
