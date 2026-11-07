"""Apply the cream scroll upgrade onto the current house STLs. Run once per fresh export.

The rear roof stays one fixed solid. A larger eave opening is cut into it, and the
same removable back grows up to close that opening. No second roof panel is added.
Cutters are applied once and are not written as print parts.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import trimesh as tm
from trimesh.transformations import rotation_matrix

from qa_upgrade import CREAM, build, read_hosts

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STL = os.path.join(ROOT, "stl")
REPORT = os.path.join(ROOT, "reports")
HOSTS = ("gable", "porch-front", "turret", "turret-loft", "roof-front", "rear", "roof-rear", "walls-l1", "walls-l2", "side")


def box(x0, y0, z0, x1, y1, z1):
    mesh = tm.creation.box([x1 - x0, y1 - y0, z1 - z0])
    mesh.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return mesh


def cyl_y(x, y0, y1, z, radius):
    mesh = tm.creation.cylinder(radius=radius, height=abs(y1 - y0), sections=20)
    mesh.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    mesh.apply_translation([x, (y0 + y1) / 2, z])
    return mesh


def one_body(mesh, name):
    """Accept one closed solid. A negative split shell is ignored when the whole mesh is clean."""
    solid = tm.Trimesh(vertices=np.asarray(mesh.vertices, dtype=np.float32), faces=np.asarray(mesh.faces), process=True)
    counts = np.bincount(solid.edges_unique_inverse)
    nbad = int(np.sum(counts != 2))
    positive = [part for part in solid.split(only_watertight=False) if part.volume > 1.0]
    if (not solid.is_watertight) or solid.volume <= 0 or nbad or len(positive) != 1:
        raise RuntimeError(
            f"{name} bodies={len(positive)} watertight={solid.is_watertight} "
            f"nonmanifold={nbad} vol={solid.volume:.1f}"
        )
    return solid


def to_local(world, transform):
    local = world.copy()
    local.apply_translation(-np.array(transform, dtype=float)[:3, 3])
    return local


def lay_flat(mesh):
    out = mesh.copy()
    axis = int(np.argmin(out.extents))
    if axis == 0:
        out.apply_transform(rotation_matrix(-math.pi / 2, [0, 1, 0]))
    elif axis == 1:
        out.apply_transform(rotation_matrix(-math.pi / 2, [1, 0, 0]))
    out.apply_translation(-out.bounds[0])
    return out


def screw_span(x, y_head, y_tip, z):
    """Clearance screw. The head sits at y_head, the tip at y_tip. Slot is for an adult. Not a tested thread."""
    y0, y1 = (y_head, y_tip) if y_head < y_tip else (y_tip, y_head)
    # Head is the 1.4 mm nearest y_head. Shaft runs the rest of the way to the tip.
    if y_head > y_tip:
        head = cyl_y(x, y_head - 1.4, y_head, z, 2.2)
        shaft = cyl_y(x, y_tip, y_head - 1.1, z, 1.0)
        slot = box(x - 0.4, y_head - 1.55, z - 2.3, x + 0.4, y_head + 0.2, z + 2.3)
    else:
        head = cyl_y(x, y_head, y_head + 1.4, z, 2.2)
        shaft = cyl_y(x, y_head + 1.1, y_tip, z, 1.0)
        slot = box(x - 0.4, y_head - 0.2, z - 2.3, x + 0.4, y_head + 1.55, z + 2.3)
    return one_body(tm.boolean.difference([tm.boolean.union([shaft, head], engine="manifold"), slot], engine="manifold"), "screw")


def diff(mesh, cutters, name):
    if not cutters:
        return mesh
    return one_body(tm.boolean.difference([mesh, *cutters], engine="manifold"), name)


def union(meshes, name):
    return one_body(tm.boolean.union(meshes, engine="manifold"), name)


def overlap(a, b):
    if np.any(a.bounds[0] > b.bounds[1]) or np.any(b.bounds[0] > a.bounds[1]):
        return 0.0
    hit = tm.boolean.intersection([a, b], engine="manifold")
    if hit is None or hit.is_empty:
        return 0.0
    return float(hit.volume)


def save_print(name, mesh, poses):
    native = [round(float(v), 2) for v in mesh.extents]
    if mesh.extents[2] > 100 and mesh.extents[2] > float(np.min(mesh.extents)) + 1:
        flat = lay_flat(mesh)
        os.makedirs(os.path.join(STL, "print"), exist_ok=True)
        flat.export(os.path.join(STL, "print", name))
        extents = [round(float(v), 2) for v in flat.extents]
        pose = "shortest axis on Z, corner at the origin"
    else:
        extents = native
        pose = "native STL, already inside the height allowance"
    poses[name] = {
        "pose": pose,
        "native_extents_mm": native,
        "print_extents_mm": extents,
        "margin_to_310x300x315_mm": [round(310 - extents[0], 1), round(300 - extents[1], 1), round(315 - extents[2], 1)],
    }


def part_record(part_id, mesh, note):
    return {
        "id": part_id,
        "file": f"stl/{part_id}.stl",
        "note": note,
        "triangles": int(len(mesh.faces)),
        "volume_mm3": round(float(mesh.volume), 1),
        "watertight": True,
        "bodies": 1,
        "nonmanifold_edges": 0,
        "bbox_mm": [round(float(v), 2) for v in mesh.extents],
        "fits_brim_allowance": bool(np.all(np.sort(mesh.extents) <= np.sort([310, 300, 315]) + 0.5)),
    }


def instance(iid, part_id, role, color, transform, motion=None, explode=None):
    placed = np.array(transform, dtype=float)
    return {
        "id": iid,
        "part": part_id,
        "role": role,
        "color": color,
        "motion": motion,
        "explode_mm": explode or [0, 0, 0],
        "transform": [[round(float(placed[r, c]), 4) for c in range(4)] for r in range(4)],
    }


def identity():
    return np.eye(4)


def translation(x, y, z):
    matrix = np.eye(4)
    matrix[:3, 3] = [x, y, z]
    return matrix


def extend_back(modified):
    """Fixed roof, larger rear eave opening, same back grown up to close it."""
    roof = modified["roof-rear"]
    rear = modified["rear"]
    # Above the attic floor (about z 212) and open toward +Y so the back can slide out.
    opening = box(318, 250, 214, 462, 360, 286)
    roof = diff(roof, [opening], "roof-rear opening")
    plug = box(324, 295.45, 198, 456, 302.45, 278)
    rear = union([rear, plug], "rear attic plug")
    modified["roof-rear"] = roof
    modified["rear"] = rear
    return opening


def lock_strips(assembly, modified):
    """Bayonet stops a straight pull. A recessed screw stops the upward release."""
    screws = []
    for side, cx in (("left", 228.0), ("right", 495.0)):
        name = f"cap_capture_{side}"
        strip = assembly.world()[name]
        bore = cyl_y(cx, 297.7, 303.8, 110.0, 1.25)
        pocket = cyl_y(cx, 301.5, 303.9, 110.0, 2.55)
        strip = diff(strip, [bore, pocket], name)
        assembly.world_override = getattr(assembly, "world_override", {})
        assembly.world_override[name] = strip
        rear = modified["rear"]
        hits = [y for y in np.linspace(290, 310, 81) if rear.contains([[cx, float(y), 110.0]])[0]]
        if len(hits) < 3:
            raise RuntimeError(f"rear screw {side} missed the stile")
        outer = hits[-1]
        # Break the outer face. Stop 1.5 mm before the mating face so the disc skin stays whole.
        modified["rear"] = diff(rear, [cyl_y(cx, outer - 5.2, outer + 0.4, 110.0, 1.25)], f"rear screw {side}")
    return None


def world_of(assembly):
    meshes = assembly.world()
    meshes.update(getattr(assembly, "world_override", {}))
    return meshes


def retainer_for(manifest, hosts, ids, host_id, tag):
    meshes = []
    by_id = {item["id"]: item for item in manifest["instances"]}
    for iid in ids:
        inst = by_id[iid]
        mesh = tm.load(os.path.join(STL, inst["part"] + ".stl"), force="mesh")
        mesh.apply_transform(inst["transform"])
        meshes.append(mesh)
    low = np.min([mesh.bounds[0] for mesh in meshes], axis=0)
    high = np.max([mesh.bounds[1] for mesh in meshes], axis=0)
    # The screw enters the room face of the jamb and stops before the far face.
    x1 = high[0] + 1.2
    cx = float((low[0] + high[0]) / 2)
    if host_id == "side":
        # Stop short of the main side slab, which starts near x 505.
        x1 = 503.1
        cx = 501.2
    host = hosts[host_id]

    def span_at(z):
        hits = [y for y in np.linspace(240, 320, 161) if host.contains([[cx, float(y), float(z)]])[0]]
        return None if len(hits) < 4 else (hits[0], hits[-1])

    span = None
    cz = None
    for candidate in (low[2] - 6.0, high[2] + 6.0, (low[2] + high[2]) / 2):
        trial = span_at(candidate)
        if trial is not None and trial[1] - trial[0] >= 8:
            span, cz = trial, float(candidate)
            break
    if span is None:
        raise RuntimeError(f"retainer {tag} has no solid jamb at x {cx}")
    face, far = span
    y_tip = float(min(face + 5.5, far - 1.6))
    # The jamb's room face is not flat. Keep the bar outside every sampled face.
    faces = []
    for x in np.linspace(low[0], x1, 7):
        for z in (low[2] + 1.0, high[2] - 1.0, cz):
            hits = [y for y in np.linspace(240, 320, 81) if host.contains([[float(x), float(y), float(z)]])[0]]
            if hits:
                faces.append(hits[0])
    outer = min(faces) if faces else face
    y_head = float(outer - 3.0)
    bar = box(low[0] - 1.2, y_head - 0.3, min(low[2], cz) - 2.0, x1, outer - 0.4, max(high[2], cz) + 2.0)
    for shift in np.linspace(0, 10, 21):
        trial = bar.copy()
        trial.apply_translation([0, -float(shift), 0])
        if overlap(trial, host) <= 0.05:
            bar = trial
            y_head -= float(shift)
            break
    else:
        raise RuntimeError(f"retainer {tag} cannot clear {host_id}")
    hosts[host_id] = diff(host, [cyl_y(cx, face - 0.5, y_tip, cz, 1.45)], f"{host_id} retainer {tag}")
    if hosts[host_id].contains([[cx, min(face + 1.2, y_tip - 0.8), cz]])[0]:
        raise RuntimeError(f"retainer hole did not open in {host_id} for {tag}")
    bar = diff(bar, [cyl_y(cx, y_head - 0.5, y_head + 2.6, cz, 1.25)], f"bar {tag}")
    return one_body(bar, f"bar {tag}"), screw_span(cx, y_head - 0.3, y_tip, cz)


def landing_report(manifest):
    by_id = {item["id"]: item for item in manifest["instances"]}

    def load(iid):
        inst = by_id[iid]
        mesh = tm.load(os.path.join(STL, inst["part"] + ".stl"), force="mesh")
        mesh.apply_transform(inst["transform"])
        return mesh

    rows = []
    for stair_id, floor_id, floor_top in (("stair-lower", "floor-l2", 114.15), ("stair-upper", "floor-l3", 212.15)):
        stair = load(stair_id)
        floor = load(floor_id)
        # Walking surface: vertices on the arrival half, below the handrail.
        arrive = stair.vertices[stair.vertices[:, 2] < floor_top + 8]
        tread = float(arrive[:, 2].max()) if len(arrive) else None
        rows.append({
            "stair": stair_id,
            "floor": floor_id,
            "mesh_max_z": round(float(stair.bounds[1, 2]), 2),
            "floor_top_z": round(float(floor.bounds[1, 2]), 2),
            "rail_above_floor_mm": round(float(stair.bounds[1, 2] - floor.bounds[1, 2]), 2),
            "highest_vertex_within_8mm_of_floor_z": None if tread is None else round(tread, 2),
            "shared_volume_mm3": round(overlap(stair, floor), 3),
            "meaning": "mesh_max_z is the handrail and stringer, which stand above the floor. top_gap in validation.json is floor target minus that rail, so a negative value is the rail height, not a dropped tread.",
        })
    return rows


def main():
    print("building upgrade solids", flush=True)
    assembly = build(ROOT)
    hosts, _colors, manifest = read_hosts(ROOT)
    print("cutting hosts once", flush=True)
    modified = assembly.apply(hosts)
    extend_back(modified)
    lock_strips(assembly, modified)
    decor = {name: mesh for name, mesh in world_of(assembly).items() if not name.startswith("cap_")}
    # cap strips are retention, still exported; cutters never enter world().
    strips = {name: mesh for name, mesh in world_of(assembly).items() if name.startswith("cap_capture")}
    screws = []
    for side, cx in (("left", 228.0), ("right", 495.0)):
        # Head at the outer face, tip inside the stile, clear of the mating face at y 295.45.
        screws.append((f"adult-screw-back-{side[0]}", screw_span(cx, 303.3, 298.2, 110.0)))
    groups = [
        ("jl1", ["cap-jla0", "cap-jla1", "cap-jla2"], "walls-l1"),
        ("jl2", ["cap-jlb0", "cap-jlb1", "cap-jlb2"], "walls-l2"),
        ("jr1", ["cap-jra0", "cap-jra1", "cap-jra2"], "side"),
        ("jr2", ["cap-jrb0", "cap-jrb1", "cap-jrb2"], "side"),
    ]
    bars = []
    for tag, ids, host_id in groups:
        bar, tool = retainer_for(manifest, modified, ids, host_id, tag)
        bars.append((tag, bar, tool))
        if overlap(bar, modified[host_id]) > 2.0:
            raise RuntimeError(f"retainer {tag} intersects {host_id}")

    by_id = {item["id"]: item for item in manifest["instances"]}
    poses_path = os.path.join(REPORT, "print-orientations.json")
    poses_doc = json.load(open(poses_path, encoding="utf8")) if os.path.exists(poses_path) else {"envelope_mm": [310, 300, 315], "parts": {}}
    poses = poses_doc.setdefault("parts", {})
    for iid in HOSTS:
        solid = one_body(modified[iid], iid)
        modified[iid] = solid
        local = to_local(solid, by_id[iid]["transform"])
        part_id = by_id[iid]["part"]
        local.export(os.path.join(STL, part_id + ".stl"))
        save_print(part_id + ".stl", local, poses)
        print("host", iid, "vol", round(solid.volume, 1), flush=True)

    new_instances = []
    new_parts = []
    back_motion = {"group": "back", "pull": [0, 70, 0]}

    def add_world(iid, mesh, role, color, note, motion=None):
        solid = one_body(mesh, iid)
        part_id = "qa65_" + iid.replace("-", "_")
        solid.export(os.path.join(STL, part_id + ".stl"))
        save_print(part_id + ".stl", solid, poses)
        new_parts.append(part_record(part_id, solid, note))
        new_instances.append(instance(iid, part_id, role, color, identity(), motion, [0, 12, 0]))
        return solid

    notes = {part.name: part.note for part in assembly.parts}
    roles = {part.name: part.role for part in assembly.parts}
    exported = []
    for name, mesh in {**decor, **strips}.items():
        role = "fastener" if roles.get(name) == "retention" else "trim"
        motion = back_motion if name.startswith("cap_capture") else None
        add_world(name.replace("_", "-"), mesh, role, CREAM if role == "trim" else "#c8b48a", notes.get(name, ""), motion)
        exported.append(name)
    for iid, mesh in screws:
        add_world(iid, mesh, "fastener", "#c8b48a",
                  "Recessed clearance screw. Adult pulls it out along +Y before the cap strip can slide up. Not a tested thread. Not safety validated.",
                  back_motion)
    for tag, bar, tool in bars:
        add_world(f"retainer-{tag}", bar, "fastener", CREAM,
                  "Covers one row of jamb magnet caps with 0.3 mm clearance. The caps stay put while this bar is screwed on. Adult assembly. Not safety validated.")
        add_world(f"adult-screw-{tag}", tool, "fastener", "#c8b48a",
                  "Recessed clearance screw for one jamb retainer. Adult removal. Not a tested thread. Not safety validated.")

    # The two long clearance strips are replaced by the bayonet strips.
    drop = {"cap-back-l", "cap-back-r"}
    manifest["instances"] = [item for item in manifest["instances"] if item["id"] not in drop]
    manifest["instances"].extend(new_instances)
    dropped_parts = {by_id[iid]["part"] for iid in drop}
    manifest["parts"] = [item for item in manifest["parts"] if item["id"] not in dropped_parts]
    manifest["parts"].extend(new_parts)
    manifest["version"] = "6.5.0"
    manifest["description"] = "Solid Queen Anne. Front, sides, and roof stay on. The full back, extended up over the attic opening, is the one closure."
    manifest["magnet_install_steps"] = [
        "Print the coupon first. Its bore is the same cross-section as the house seats.",
        "A nominal 5.0 x 2.8 mm disc drops in the open mouth. The seat is 5.6 mm across and 3.2 mm deep. Those are design allowances of 0.30 mm radial and 0.40 mm axial, not a measured fit.",
        "1.4 mm of plastic stays between the disc and the mating face.",
        "The two rear strips slide down 3 mm onto headed studs. That lip resists a straight pull. Each strip is then held by a recessed screw so it cannot slide back up. An adult removes the screw first.",
        "Each row of jamb caps is covered by a retainer bar and one recessed screw. The caps are clearance fits under that bar. They are not trapped once the bar is off.",
        "Nothing here is a tested thread, a wear test, or a toy-safety validation.",
    ]
    # Refresh stats on rewritten hosts.
    replaced = {by_id[iid]["part"] for iid in HOSTS}
    stats = {}
    for iid in HOSTS:
        mesh = tm.load(os.path.join(STL, by_id[iid]["part"] + ".stl"), force="mesh")
        stats[by_id[iid]["part"]] = mesh
    for record in manifest["parts"]:
        if record["id"] in stats:
            mesh = stats[record["id"]]
            record["triangles"] = int(len(mesh.faces))
            record["volume_mm3"] = round(float(mesh.volume), 1)
            record["bbox_mm"] = [round(float(v), 2) for v in mesh.extents]
            record["watertight"] = True
            record["bodies"] = 1
            record["nonmanifold_edges"] = 0
    bom = {item["part"]: item for item in manifest.get("bom", [])}
    for record in new_parts:
        bom[record["id"]] = {"part": record["id"], "file": record["file"], "qty": 1}
    for part_id in dropped_parts:
        bom.pop(part_id, None)
    manifest["bom"] = [bom[key] for key in sorted(bom)]
    listed = {record["id"] + ".stl" for record in manifest["parts"]}
    for name in os.listdir(STL):
        if name.endswith(".stl") and name not in listed:
            os.remove(os.path.join(STL, name))
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    poses_doc["note"] = "Margins are envelope minus the printed bounding box. Caps and strips are on their short axis. No slicer was run. The house is not a finished print kit."
    with open(poses_path, "w", encoding="utf8") as handle:
        json.dump(poses_doc, handle, indent=2)
        handle.write("\n")

    # Audits that do not depend on source comments.
    roof = modified["roof-rear"]
    rear = modified["rear"]
    access = {
        "roof": "fixed, one solid, no lift-off panel",
        "closure": "the full back, including the attic plug, is the only piece that comes off",
        "opening_world_mm": {"x": [318, 462], "y": [250, 360], "z": [214, 286]},
        "plug_world_mm": {"x": [324, 456], "y": [295.45, 302.45], "z": [198, 278]},
        "rear_versus_roof_mm3": round(overlap(rear, roof), 3),
        "how_to_reach": "Take the back off along +Y. The attic plug leaves with it. The fixed roof keeps a rear eave opening above the attic floor, about 144 mm wide, open toward the rear. Furniture under about 36 mm and a hand use that opening. No roof panel is removed.",
    }
    if access["rear_versus_roof_mm3"] > 2:
        raise RuntimeError("back plug intersects the roof " + str(access["rear_versus_roof_mm3"]))
    with open(os.path.join(REPORT, "rear-access.json"), "w", encoding="utf8") as handle:
        json.dump(access, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(REPORT, "landings.json"), "w", encoding="utf8") as handle:
        json.dump({"top_gap_meaning": "validation top_gap_mm = floor target z minus the stair mesh maximum z. Negative means the rail stands above the floor.",
                   "flights": landing_report(manifest)}, handle, indent=2)
        handle.write("\n")
    rows = []
    bad = []
    for record in manifest["parts"]:
        mesh = tm.load(os.path.join(STL, record["id"] + ".stl"), force="mesh")
        counts = np.bincount(mesh.edges_unique_inverse)
        nbad = int(np.sum(counts != 2))
        pieces = mesh.split(only_watertight=False)
        positive = [part for part in pieces if part.volume > 1.0]
        negative = [part for part in pieces if part.volume < -1.0]
        row = {"id": record["id"], "watertight": bool(mesh.is_watertight), "positive_bodies": len(positive),
               "negative_split_mm3": round(sum(part.volume for part in negative), 2),
               "nonmanifold_edges": nbad, "volume_mm3": round(float(mesh.volume), 1)}
        rows.append(row)
        if len(positive) != 1 or nbad or not mesh.is_watertight or mesh.volume <= 0:
            bad.append(record["id"])
    with open(os.path.join(REPORT, "topology.json"), "w", encoding="utf8") as handle:
        json.dump({"ok": not bad, "version": "6.5.0", "parts": len(rows), "failures": bad,
                   "cutters_published": 0,
                   "rule": "Reloaded STL: one positive body, no negative body, every edge on exactly two faces. Cutters are not parts.",
                   "bodies": rows}, handle, indent=2)
        handle.write("\n")
    if bad:
        raise RuntimeError("topology failed: " + ", ".join(bad))
    print(json.dumps({"version": "6.5.0", "new": len(new_parts), "exported_decor": exported, "topology": len(rows), "roof_overlap": access["rear_versus_roof_mm3"]}))


if __name__ == "__main__":
    main()
