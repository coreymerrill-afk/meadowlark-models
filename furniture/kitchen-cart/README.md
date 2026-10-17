# Rolling kitchen cart - 18 mm (3/4 in) plywood, laser cut from ONE 4 x 8 ft sheet

Same style and tooling as the nightstand: parametric `model.py`, through-tab + slot joints (slot = tab + 0.1 mm), finger joints on the drawer, 3.0 mm pilot holes for #8 screws, DXF in mm with `CUT` and `LABELS` layers. Made for the ACMER X1 Ultra (kerf ~0.25 mm).

## Files
| File | What |
|---|---|
| `kitchen-cart-nest-1220x2440.dxf` | all 29 parts + 2 fit-test coupons on one 1220 x 2440 mm sheet, 6 mm spacing. Layers `CUT` (cut) and `LABELS` (names + sheet outline, reference only: set to non-output) |
| `cart-assembly.png` | exploded + assembled isometric, shelf-slot layout, caster foot detail |
| `cart-nest-layout.png` | the nested sheet, every part labelled (optional parts are the lighter colours) |
| `parts.json` | web export for the 3D viewer: name, width, height, thickness, 3D origin + axes (u, v, n), centre, outline (see its `note`) |
| `model.py`, `make_nest.py`, `render.py`, `export_json.py`, `verify.py`, `run_checks.py` | regenerate everything. `checks.txt` = the verification output |

Change thickness: `KC_THICKNESS=17.6 python make_nest.py && python render.py && python export_json.py` (slot = thickness + 0.1). Screw lengths work for ply 17-19.5 mm.

## Size and height budget
**600 W x 450 D x 900 H mm** (23.6 x 17.7 x 35.4 in), worktop at exactly 900 mm. A 22 mm rail lip runs along the back and both sides (front open, so you can slide things on); lip top is at 922 mm.

Why not three bays of 300 / 300 / 250? Those add up to 850 mm. With four panels (72 mm) and the casters + feet (138 mm) that makes a 1,060 mm (42 in) cart, well above counter height. So at 900 mm the default is **two shelf levels + a drawer**, and the slot rows let you re-split it:

| Layout (rows of the 50 mm slot grid) | Bay 1 clear | Bay 2 clear | Bay 3 / drawer |
|---|---|---|---|
| **As drawn:** shelf on row 5, optional drawer on row 10 | **310** | **227** (shelf to drawer face) | drawer box 112 inside |
| Same, no drawer | 310 | 398 (stand mixer fits) | - |
| Shelf on row 6, no drawer | 360 | 348 | - |
| Two shelves, rows 3 and 8 (cut 1 more SHELF + 2 LEDGER) | 210 | 232 | 248 |

Vertical stack from the floor: casters 102 mm, two 18 mm foot layers (to 138), base 18 (top at 156), sides 726 mm tall, top 18 mm (bottom at 882, top at 900).

## Parts (29 parts: 19 core + 10 optional, plus 2 optional test coupons; all 18 mm)
| # | Part | Qty | Size mm (outline incl. tabs) | Notes |
|---|---|---|---|---|
| 1 | BASE | 1 | 600 x 450 | 4 slots for side tabs, 12 pilots |
| 2 | TOP | 1 | 600 x 450 | 4 slots for side tabs, 13 pilots (9 rail screws from below, 4 from above: fill + paint) |
| 3-4 | SIDE-L / SIDE-R | 2 | 420 x 744 | 2 tabs top, 2 tabs bottom, 3 back slots, **13 slot rows x 2** at 50 mm pitch (the shelf-slot grid) |
| 5 | BACK | 1 | 570 x 726 | 3 tabs per end; inset 18 mm from the rear edge of the sides |
| 6-8 | RAIL-L / RAIL-R / RAIL-B | 3 | 450 x 22, 450 x 22, 564 x 22 | lip around the worktop, glued + screwed up from the underside of the top |
| 9-10 | LEDGER-SH5-L / -R | 2 | 48 x 365 | shelf supports: 30 mm ledge + 2 tabs (80 mm) through the side slots |
| 11 | SHELF | 1 | 532 x 381 | loose, sits on the 2 ledgers |
| 12-19 | FOOT-A1..4, FOOT-B1..4 | 8 | 100 x 75 | caster blocks, A+B glued = 36 mm. A: four 8.5 mm bolt holes. B: four hex nut pockets |
| *opt* 20-21 | LEDGER-DR-L / -R | 2 | 48 x 365 | same ledger, in row 10, carries the drawer |
| *opt* 22-23 | DRW-SIDE-L / -R | 2 | 350 x 130 | nightstand design |
| *opt* 24-25 | DRW-FRONT / DRW-BACK | 2 | 531 x 130 | finger ends; front has a 90 x 22 pull slot |
| *opt* 26 | DRW-BOTTOM | 1 | 531 x 314 | 2 tabs per side |
| *opt* 27 | DRW-FACE | 1 | 531 x 150 | inset face, flush with the sides' front edge, pull slot |
| *opt* 28-29 | CLEAT-BACKER-A / -B | 2 | 514 x 80 | French-cleat mounting plate, two layers glued (see below) |
| *opt* | TEST-SLOT / TEST-TAB | 1+1 | 80 x 60 / 80 x 58 | fit coupons: **cut first** |

Net mass (600 kg/m3 ply assumed): 19.2 kg core, **25.3 kg with drawer + cleat backer**, plus casters (~2-3 kg).

## Joints (every slot = tab + 0.1 mm each way: 18.1 wide; all tabs are 18 mm long, flush through)
* **Sides <-> base and top**: each side has two 100 mm tabs top and bottom through slots in the top and base. The side's end edge sits ON the base, so the load goes straight down into the base and feet (not through the glue).
* **Back <-> sides**: three 80 mm tabs per end through side slots. The back stands on the base and runs up under the top.
* **Ledgers <-> sides** (the modular part): see below.
* **Rails**: strips on edge along the top edge, glued and screwed up from below.
* **Drawer**: as the nightstand: 5-finger box joints, bottom with 2 through-tabs per side, inset face glued + screwed from inside the box front, 90 x 22 pull slot.

## Modular shelf slots (SHELF-SLOT LAYOUT panel in `cart-assembly.png`)
Each side has **13 rows of two 80 x 18.1 slots, 50 mm pitch** (row k underside = 42 + 50k mm above the base top). Shelves are NOT glued into the carcass. Each level is two LEDGER strips whose tabs pass through a row of slots, with a loose SHELF resting on them. The shelf pins the ledgers, so:
1. lift the shelf out, 2. pull both ledgers inward out of their slots, 3. push them into another row, 4. drop the shelf back. Nothing is glued, so the carcass is never redone.
A drawer uses the **same ledgers**: the box rides on top of them, face flush with the front. Any row from 0 to 10 works for a drawer (row 10 is the highest where the face still clears the top; keep the face 5 mm clear of any shelf above). The ledger starts 18 mm behind the front edge so a face can sit in front of it.
Unused rows are open slits (about 80 x 18 mm); leave them, or glue in spare tab off-cuts and paint if you want a plain side. Optional: 1 screw (#8 x 1-1/4) up through each ledger into the shelf locks it; the pilots are cut for it.

## Casters and feet (mounting pattern in the CASTER FOOT panel)
**HOLKIE 3 in swivel plate casters, set of 4, total-lock (pedal brake locks wheel and swivel), 1,000 lb set rating:** https://www.amazon.com/Locking-Swivel-Casters-Heavy-Duty-Plate/dp/B085ZNL3KW (listing price about $25, 4.7 stars). Maker page with the dimensions: https://holkie.com/products/3-inch-plate-casters-with-brake-black . Pick the variant with a brake on all four.
* Maker specs used: top plate 94 x 63.5 mm, **hole pattern 73.2 x 44.5 mm (2.88 x 1.75 in)**, slots 12 x 7.9 mm, overall height 100 mm (listing says 4 in, I used 102).
* Each caster bolts to a **foot**: FOOT-A (4 x 8.5 mm holes) with FOOT-B glued on top (4 hex nut pockets, 13.4 mm across flats). Hardware: **16 x M8 x 30 bolts, 16 nuts, 16 washers** (the set ships 16 x M8 x 25 + nuts; 25 mm is only flush with the nut here, so use 30 mm). Feet sit at the four corners: caster stance 490 x 360 mm.
* The foot is fixed to the base with glue and **2 x #8 x 1-3/4** from the top of the base (2 screws per foot, 8 total).

## Robot-vacuum clearance
Underside of the base is **138 mm** above the floor (casters 102 + foot 36), well over the 60-80 mm you asked for. It's open from the front and back: **370 mm** clear between the left and right casters even allowing for wheel swing, so a 340 mm robot passes straight under. The sides are open only between the front and back feet (about 250 mm), so robots will not enter from the side. To cut the gap to about 100 mm, glue FOOT-A directly under the base and drop FOOT-B (the nuts then need T-nuts or lag screws instead of the pockets).

## French cleat wall mount (optional)
**Plausible only for parking an empty cart, not for hanging a loaded one.** The empty cart is about 25 kg (55 lb) and a loaded one 60 kg+, which is more than a drywall/stud cleat wants to see, and the casters (not the wall) are the working support. Also a laser cannot cut the 45 degree bevel, so the cleat itself has to be bought.
* **CLEAT-BACKER-A + -B** (two 514 x 80 mm layers, in the nest): glue A flat to the rear face of the BACK panel (it fills the 18 mm recess behind the back) and B on top of A, with 4 x #8 x 1-3/4 from inside the cart through the back and A into B. Two layers because the top and base overhang the back by 15 mm: the cleat face has to stand proud of that or the cart cannot get close enough to the wall. Cart-side aluminum cleat screws to B.
* Hardware: **Uniclife 24 in aluminum French cleat, 2 pairs, seller-claimed 150 lb:** https://www.amazon.com/Uniclife-Aluminum-Hardware-Mounting-Interlocking/dp/B0FSPKRQDC . Hacksaw one pair to about 500 mm so it fits the backer; mount the wall half into **two studs** (16 in centres), not the supplied drywall anchors.
* Position the wall cleat so the cart hangs with the casters about 5 mm off the floor. To park: empty the cart, lift about 15 mm, hook on, lock the casters. To roll: lift off. A French cleat engages by lifting, so the cart cannot lock onto it just by rolling.
* With the backer, the cart is 453 mm deep and the top/base edge clears the wall by about 9 mm (cleat standoff about 6 mm).

## Glue + screws
Glue is the joint; **the screws are clamps while the glue cures** and then stay in as reinforcement. Use a PVA wood glue (Titebond II, or **Titebond III** for the kitchen: water resistant, indirect food contact OK). Scrape or lightly sand the charred laser faces in every tab and slot first: carbon glues badly. Spread glue on both tab sides and finger faces, assemble, drive the screws right away, wipe squeeze-out, and leave 1 hour before handling and 24 hours before loading. Do NOT glue the ledgers or the shelves (they must stay removable). Seal all wood with a water-resistant finish (the shelf tops and the worktop especially).

## Screws (pilots 3.0 mm drawn; #8 thread is about 4.2 mm)
* **#8 x 1-1/2 in: 20** (top to sides 2, top to back 2, base to sides 2, base to back 2, sides to back 4; drawer corners 4, drawer bottom 4)
* **#8 x 1-1/4 in: 13** (rails 9, shelf lock 2, drawer face 2): shorter on purpose so the tips stay inside the part
* **#8 x 1-3/4 in: 12** (feet 8, cleat backer 4)
* Core cart without drawer or cleat: 12 + 11 + 8 = 31 screws.
* M8 x 30 bolts / nuts / washers x 16 for the casters.
Positions: top: 1 per side between the tabs, 2 into the back top edge; rails: 3 per side rail and 3 on the back rail, up from below; base: 1 per side and 2 into the back, up from below (reach under the cart, 138 mm of room); sides: 2 each from outside into the back panel edge.

## Assembly order
1. Cut the coupons, then the sheet. Dry-fit everything. Clean the char out of the slots and off the tab faces.
2. **Feet:** bolt a caster to each FOOT-A (bolts up through the plate, nut on top, tighten with a socket). Glue FOOT-B over it, nuts inside the pockets, clamp. Do all 4.
3. Lay the BASE top-up on the bench, glue and set the 4 feet under it, drive the 8 foot screws down through the base (the 2 rear screws per foot are behind the back panel position).
4. Stand SIDE-L and SIDE-R on the base: glue the 4 bottom tabs into the base slots, glue the BACK tabs into both sides. Ratchet-strap the carcass tight across the front. Drive the side-to-back screws from outside, then roll the cart on its side and drive the base screws up from below.
5. Glue the 4 top tabs into the TOP slots and set it down; drive the 4 top screws (2 into the sides, 2 into the back).
6. Glue the 3 rails on the TOP, drive the 9 screws up from below.
7. Drop the ledgers into the chosen row, drop the shelf in. Drawer module: assemble as the nightstand (finger joints, bottom, check square, box screws, then the face from inside with 2 mm shims) and set it on the row-10 ledgers.
8. Optional: backer + cleat. Fill and sand the 4 top screw holes, finish, lock the casters.

## Load rating (estimates, not tested)
* Casters: 1,000 lb set rating (seller). I would plan for half of it, **about 220 kg (500 lb)**, a ceiling nobody will reach.
* Shelf: span between ledgers 474 mm, 18 mm ply (assumed E = 5 GPa): 25 kg spread out deflects about 0.35 mm, bending stress is about 1.3 MPa at 50 kg, so strength is not the limit. Planning load **30 kg (66 lb) per shelf, 25 kg on the worktop, 5 kg in the drawer**, **about 80 kg (175 lb) total**.
* Stability is the real limit, not strength. Caster stance is 490 x 360 mm, empty centre of gravity about 560 mm up. With 15 kg each on the base, shelf and worktop (70 kg total, centre of gravity about 535 mm) the cart tips at about 18 degrees front-to-back, and a locked cart tips from a horizontal push of about 14 kgf (30 lbf) at the worktop. Keep heavy things low (mixer on the base level), don't lean on it at the top edge, keep drawer contents under 5 kg and don't pull it out with the casters unlocked.

## Cutting notes (ACMER X1 Ultra, 120 W diode)
* ACMER publishes 28 mm plywood in one pass for this machine but **no feed rate for 18 mm**. 100-200 mm/min is a starting guess from the nightstand notes. **Cut the TEST coupons on scrap first** and adjust. The tab must slide through with finger pressure and be flush. Kerf comp is noted, not applied (see the nightstand README for the Kerf Offset steps).
* Cut path is **50.1 m**, so roughly **4-8 hours** at 100-200 mm/min (estimate). Never leave the machine running unattended: 18 mm ply can flare.
* The nest uses 2433 x 1178 mm of the sheet (6 mm border). Real US 4 x 8 ply is 1219 x 2438 mm, which leaves only about 5 mm on the long side, so trim/check the sheet and lay it dead flat. Parts are 79% of the sheet area. All long axes run along the 2440 mm direction except the small parts and the drawer bottom/face.
* Order of operations: coupons, then every pilot hole and slot, then the small parts (feet, ledgers, rails, drawer), then the large outlines last (SIDE, BASE, TOP, BACK, SHELF). "Cut inner shapes first" in LightBurn. Add 2-3 micro-joints on the big parts so they don't drop and shift.
* Edges are dark and a bit tapered; wipe the slots clean before glue. Screw from the wider (top) face where you can.

## What was checked (`checks.txt`)
* 26 tab/slot pairs in the assembled model: every slot = tab + 0.1 mm, every tab exactly 18 mm (flush through).
* 3D overlap test of all 29 parts in assembled position: **0 overlaps** (negative control with a 0.4 mm undersized slot: 16 overlaps, so the test works).
* All 45 screw paths stay inside their parts, tips >= 1 mm inside the mate.
* Nest: 0 overlaps, 6.0 mm minimum spacing, inside the sheet; DXF read-back: extent 6-2433 x 6-1178 mm, 0 overlapping outlines, slot sizes as expected.

## Not verified
* Caster plate hole pattern and bolt size for the exact Amazon listing (taken from the maker's page; the Amazon text I could fetch was for a sibling listing of the same casters). Measure the casters when they arrive; the 8.5 mm holes assume M8 and the slots are only 7.9 mm wide.
* Cut speed and fit for 18 mm ply on this laser, wood actual thickness (set `KC_THICKNESS` to your measured value).
* Load and tip numbers are hand estimates, not tests. Cleat rating is the seller's claim.
