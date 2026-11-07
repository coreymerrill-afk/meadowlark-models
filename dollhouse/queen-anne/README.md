# Queen Anne Playhouse — v1.0.0

A separate 1:24 house for the Meadowlark dollhouse showcase. It is not Bramble Cottage and not one of the other five play-kit manors.

The public Real Good Toys Queen Anne kit is 1:12. This model keeps the asymmetric tower, the front gable, and the layered porch, with flatter trim and openings sized for hands. It does not reuse that kit's dimensions.

**CAD checks passed. Not printed. Not measured. Not sliced.** Forces, fatigue, layer adhesion, and tip-over were not tested. This is not a toy-safety certification and not an H3C print test.

The viewer at `/dollhouse/queen-anne/` loads these STLs. There is no separate beauty mesh.

## Size

Assembly bounds from the placed meshes: **788 × 297 × 662 mm**. Three bays, three storeys. A bay is **254 mm wide × 210 mm deep**. Clear storey height is **118 mm**. Front opening in the panel is **204 × 110 mm**. Reach from the front face to the inner face of the rear shear is **190 mm**.

Those are CAD numbers. They are not a hand-clearance trial.

## What carries the house

Posts, plates, floors, and the rear shear carry the load. Front panels, end panels, roofs, the porch, the balcony, partitions, and furniture do not.

- Posts drop into corner pockets with **0.40 mm** side clearance and a **0.30 mm** seat gap.
- Each plate sits **0.30 mm** above the posts. The next floor sits **0.30 mm** above the plate.
- The rear shear's tongues sit in the rear-post grooves, with a tab in the floor and a tab in the plate.
- Bases and upper floors key to the next bay with a **16 mm** underside lap. Measured rest intersection of every contacting pair is **0 mm³**.
- Interior sides between bays are open above the corner posts. A doll does not have to pass through another room's furniture to reach the next bay.

## Panels and roofs

Panels are lift-out. No hinges, magnets, or loose pins.

1. Lift **8.6 mm**. That clears the lower hook and the head fin.
2. Pull out along the wall normal, **48 mm**.

The CAD sweep (rest, lift, 18 mm, and 48 mm) does not intersect the frame, the neighbour panels, the porch, or the balcony. The balcony rail sits beyond that pull. Roofs lift off a plug in the plate opening; a **16 mm** lift clears the plate in the same check.

Square edges and the lift gap were not tried with fingers.

## Legacy 127 mm grid

Checked against the meshes, not against the arithmetic:

| Check | Result |
| --- | --- |
| `floor_tile_v0.stl` | 127.0 × 127.0 × 10.0 mm, watertight |
| `snap_post_v0.stl` | 9 × 9 × 9 mm, watertight |
| Tip-down peg in all 16 sockets | **0 mm³** intersection |
| Same peg shifted 10 mm | **113 mm³** intersection |
| Bay width ÷ measured tile | **2.0** |
| Bay depth vs two tiles | **No.** Depth is 210 mm |
| Same peg on a Queen Anne floor | **86 mm³** intersection. There is no Ø6.3 socket |

The kits share a 254 mm module width. They do not share a joint.

## Print the coupon, then one bay

Largest part box is inside **310 × 300 × 315 mm**, which leaves 10 mm on each side of a 330 × 320 mm bed and 10 mm under a 325 mm height. That is a bounding-box allowance for a brim. No slicer ran. Nothing here was printed on an H3C.

1. `qa_coupon_socket_v1` and `qa_coupon_plug_v1`. The tongue drops into the pocket (engaged intersection **0 mm³**). Two holes, Ø6.0 and Ø6.3, are a size gauge. There is no loose peg.
2. One ground bay: base, two front posts, two rear posts, plate, rear shear, one front panel, one end panel.
3. The other bays, the upper floors, roofs, porch, balcony, partitions, and furniture only after that bay seats.

Posts are exported lying on the 14 mm face. Panels are exported with the skin's features facing up. Roofs sit on their soffit. Every STL has its minimum corner at the origin. See `manifest.json` for each bbox.

## Files

| File | What it is |
| --- | --- |
| `cad/build_queen_anne.py` | Parametric source. Regenerates the STLs, the manifest, and `reports/validation.json`. |
| `stl/*.stl` | One watertight mesh per part. Not a toolpath. |
| `manifest.json` | BOM, colours, and the 4×4 placement of every instance. |
| `reports/validation.json` | The CAD checks named above. |

Regenerate with `python3 cad/build_queen_anne.py` from `dollhouse/queen-anne` (`trimesh`, `manifold3d`, `numpy`, `scipy`).
