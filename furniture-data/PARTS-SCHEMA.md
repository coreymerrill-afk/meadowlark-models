# parts.json schema (furniture-v2)

Written by `export_parts_json()` in `_lib/fp.py`. One file per design: `<slug>/parts.json`. Units mm.

Top level: `units`, `frame`, `thickness` (18.0), `overall {width, depth, height}`, `note`, `parts[]`.

World frame: x = width (left to right), y = depth (front 0 to back), z = up (floor 0). For a Three.js y-up scene use `(x, z, -y)`.

## Each entry in `parts[]`

| Field | Type | Meaning |
|---|---|---|
| `name`, `group`, `optional`, `thickness`, `sheet` | string / string / bool / number / int | Part name, group (carcass, drawer, cleat, ...), option flag, ply thickness, nest sheet number (matches `plan.json`) |
| `width`, `height` | number | Body size (no tabs), local a and b |
| `bbox` | `[a_min, b_min, a_max, b_max]` | Full outline extent incl. tabs, local coordinates |
| `origin`, `u`, `v`, `n` | 3-vectors | Plate frame. 3D point = `origin + a*u + b*v + w*n`, with `w` from 0 to `thickness` |
| `center` | 3-vector | Mid-thickness centre of the bbox, world coordinates |
| **`outline`** | `[[a,b], ...]` | **Exterior ring only**, local (a,b), closed (first point repeated at the end). Tabs are part of it. It has NO holes in it. |
| **`holes`** | `[ [[a,b], ...], ... ]` | **List of interior rings**, one per cut-out: joint slots (tab + 0.1 mm), screw pilots (3 mm, 32-gon), pin holes, vents, handle slots, logo cut-outs. Same local (a,b) coordinates as `outline` and as the DXF CUT layer. Rings are open (last point is NOT repeated). |
| `hole_count` | int | `len(holes)` (this used to be the value of `holes` before 2026-10-17) |

## Rendering rule

Part solid = `outline` minus every ring in `holes`, extruded `thickness` along `n`.

Three.js: `shape = new THREE.Shape(outlinePoints)`; for each ring `shape.holes.push(new THREE.Path(ringPoints))`. THREE wants the holes wound opposite to the outline: after `ShapeUtils.isClockWise`, reverse the hole if it has the same winding as the outline. Then `ExtrudeGeometry(shape, {depth: thickness, bevelEnabled: false})`. The existing `furniture/viewer.js` `panelGeometry()` only reads `outline`, which is why slots did not show on exploded side panels.

## Slot / tab rule (what the checker tests)

Every tab protruding from part A passes through a rectangular slot ring in the mating part B: slot = tab + 0.1 mm in length and width (18.1 mm wide for 18 mm ply), tab flush with the far face of B. `check_parts_json.py` verifies this from parts.json alone (no model code):

1. No two parts' solids (outline minus holes) overlap in 3D. A tab with no slot would overlap.
2. Every 18.1 mm-wide rectangular hole is filled by another part's tab. A slot with no tab is reported.

The kitchen cart's side panels carry 13 slot rows at 50 mm pitch on purpose (adjustable shelf and drawer positions). Unoccupied rows are reported as "intentionally spare".
