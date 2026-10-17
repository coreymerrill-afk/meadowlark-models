# Nightstand - one 4x8 sheet of 3/4 in plywood, laser cut

Designed for the ACMER X1 Ultra 120 W diode (kerf ~0.25 mm, spot 0.2 x 0.25 mm). Everything is flat 3/4 in ply, through-tab joints, **glued, with screws as the clamps** while the glue cures.

Rev 2 (furniture rules): **raised on feet** so robot vacuums can clean under it, and an **optional French cleat** so it can move from floor-standing to wall-hung.

## Files
| File | What |
|---|---|
| `nightstand-nest-1220x2440.dxf` | all parts nested on a 1220 x 2440 mm sheet, 6 mm spacing, mm units. Layers `CUT` (everything to cut) and `LABELS` (part names + sheet outline, reference only: set to non-output) |
| `nightstand-assembly.png` | exploded + assembled isometric, joint callouts A-J, pilot hole positions |
| `nightstand-clearance-cleat.png` | side view: floor clearance and the floor-standing vs wall-hung (cleat) positions |
| `parts.json` | web export for the 3D viewer, same schema as the kitchen cart's (name, group, optional, size, 3D origin + axes, outline) |
| `nightstand-nest-layout.png` | the nested sheet with every part labelled |
| `model.py` | the design (thickness is a parameter), `make_nest.py`, `render.py`, `export_json.py`, `verify.py`, `run_checks.py`, `gen_readme.py` regenerate everything. `checks.txt` = last verification output |

Change thickness: `NS_THICKNESS=17.6 /workspace/venv-egg/bin/python make_nest.py && ... render.py && ... gen_readme.py` (slot width = thickness + 0.1 mm). Screw lengths and the 1-1/4 in runner/face screws work for ply 17.0-19.5 mm; thinner than 17 needs shorter runner/face screws.

## Size
Overall **560 W x 400 D x 600 H mm** (22 x 15.75 x 23.6 in). Top 560 x 400 overhangs the carcass by 20 mm on the front, back and both sides. Carcass 520 W x 360 D. The sides stand on the floor on two 70 mm feet each (a 220 x 86 mm notch between them), the bottom shelf is at 100-118 mm, so there is **86 mm clear under the sides and 100 mm under the shelf**, open front and back and between the feet, enough for a typical robot vacuum (check yours: most are 76-92 mm tall). Cubby above the shelf 292 mm clear to the drawer runners, drawer on top. Drawer opening is inset: box 481 W x 300 D x 130 H, face 481 x 140.

## Parts (15 parts = 13 core + 2 optional cleat layers, + 2 optional test coupons, thickness 18 mm)
| # | Part | Qty | Size mm | Notes |
|---|---|---|---|---|
| 1 | TOP | 1 | 560 x 400 | overhangs sides 20 mm all round; 4 slots for side tabs; 4 pilots (4 screw heads show on top: fill + paint) |
| 2 | SIDE-L | 1 | 360 x 600 | identical to SIDE-R; 2 top tabs, 2 shelf slots, 3 back slots, 5 pilots, **foot notch** 220 x 86 under the shelf (two 70 mm feet) |
| 3 | SIDE-R | 1 | 360 x 600 | identical to SIDE-L |
| 4 | SHELF | 1 | 520 x 342 | tabs both ends; 2 pilots from underside into back edge |
| 5 | BACK | 1 | 520 x 464 | 3 tabs per end; sits on shelf, under top; 4 pilots for the cleat screws |
| 6 | RUNNER-L | 1 | 304 x 20 | strip, 2 pilots |
| 7 | RUNNER-R | 1 | 304 x 20 | strip, 2 pilots |
| 8 | DRW-SIDE-L | 1 | 300 x 130 | finger notches at both ends, 2 bottom slots, 3 pilots |
| 9 | DRW-SIDE-R | 1 | 300 x 130 | identical to DRW-SIDE-L |
| 10 | DRW-FRONT | 1 | 481 x 130 | finger ends; 90x22 pull slot; 3 pilots (1 bottom, 2 face) |
| 11 | DRW-BACK | 1 | 481 x 130 | finger ends; 1 pilot (bottom) |
| 12 | DRW-BOTTOM | 1 | 481 x 264 | 2 tabs per side |
| 13 | DRW-FACE | 1 | 481 x 140 | inset face 481x140; 90x22 pull slot, no holes on show side |
| 14 | CLEAT-BACKER-A | 1 | 464 x 80 | *optional* wall-mount layer 1; 4 pilots |
| 15 | CLEAT-BACKER-B | 1 | 464 x 80 | *optional* wall-mount layer 2 (glued to A) |
| 16-17 | TEST-SLOT / TEST-TAB | 1+1 | 80 x 60 / 80 x 58 | optional fit-test coupons (30 mm tab in a 30.1 x 18.1 slot). Cut these first |

Sheet use: parts cover 49% of the sheet; everything fits in a 2440 x 986 mm area, leaving about 234 mm across the 1220 mm width free (room for scrap tests). Long axis of every part runs along the 2440 mm direction (sheet grain).

## Joints (all tabs go through and end flush; every slot = tab + 0.1 mm each way, i.e. width 18.1 for 18 ply)
A. **Top <-> sides**: each side has two 100 mm tabs through 4 slots in the top (100.1 x 18.1); one screw between the tabs on each side.
B. **Shelf <-> sides**: shelf ends have two 80 mm tabs each, through side slots, flush outside.
C. **Back <-> sides**: back panel has three 80 mm tabs per end through side slots; back sits on the shelf and under the top.
D. **Runners**: 304 x 20 strips on the inside of each side at 410-430 mm height, 2 screws from outside. The drawer sides ride on top.
E. **Drawer box corners**: 5 x 26 mm finger joints (simple box joint). 1 screw through each side into the front/back edge.
F. **Drawer bottom**: 2 through-tabs (60 mm) per side + screws.
G. **Drawer face**: inset 481 x 140, glued and screwed from inside the box front.
H. **Pull**: a 90 x 22 mm slot cut through the box front and the face at the same height (finger pull).
I. **Feet (robot-vacuum clearance)**: each side runs to the floor but has a 220 x 86 mm notch cut from the bottom edge, leaving a 70 mm foot at the front and at the back. The bottom shelf is at 100 mm, so the web of side above the notch is 14 mm. Nothing extra to buy or glue: the feet are part of the side panel. Stick a felt or rubber dot under each foot if your floor is hard.
J. **Cleat backer (optional, wall mount)**: see below.

## French cleat wall mount (optional)
A nightstand is light, so unlike the kitchen cart this is a realistic way to hold it: **14.9 kg empty (15.7 kg with the cleat layers)**. Plan for 10 kg of contents or less in the drawer and cubby, about **26 kg (57 lb) total**, well inside the 150 lb the cleat seller claims. Wall-hung, the whole floor underneath is free.
* **CLEAT-BACKER-A + -B** (two 464 x 80 mm layers, both in the nest): glue A flat to the rear face of the BACK panel. It sits in the 18 mm pocket behind the back, flush with the rear edge of the sides. Glue B on top of A. Drive **4 x #8 x 1-3/4 in** from inside the nightstand through the back and A into B (pilots are in the back and A; B is solid on its rear face). Do this **before the drawer goes in** (the screws are at 520 mm high, behind the drawer). Two layers because the top overhangs the sides by 20 mm: the cleat face has to stand proud of that edge or the nightstand cannot sit against the wall.
* Hardware (not cut): **Uniclife 24 in aluminum French cleat, 2 pairs, seller-claimed 150 lb**, the same one as the kitchen cart: https://www.amazon.com/Uniclife-Aluminum-Hardware-Mounting-Interlocking/dp/B0FSPKRQDC . One pair is enough here (the second pair of the pack is the one for the cart). Hacksaw the cart half to about **440 mm** so it fits the backer, and the wall half to about **500 mm** so it is hidden behind the top and still lands on **two studs** (16 in = 406 mm centres, about 47 mm to spare each end). Screw the cart half to layer B with 4 short screws that stay inside B (#8 x 3/4 in; the 3/4 in tip stays inside the 18 mm layer B once it clears the 2-3 mm aluminum). Mount the wall half into the studs, not the drywall anchors.
* **Where**: the backer is centred 520 mm above the bottom of the feet. Mount the wall half so the nightstand hangs at the height you want: for the top of the nightstand level with your mattress, remember the top is 600 mm above the feet and the feet hang above the floor by whatever you choose (e.g. 120 mm lift = top at 720 mm, 28 in). Mark it with the nightstand held up, then check with a level before drilling.
* A French cleat engages by lifting, so you lift the nightstand straight up to take it off and straight down onto the wall bar to hang it. To switch back to floor-standing, lift it off and set it on its feet: the wall bar can stay on the wall and the cart half can stay on the backer, neither affects floor use.
* With the backer, depth against the wall is about 404 mm (the Z-bar pair stands the nightstand 6 mm off the wall at layer B). The top edge sits about 4 mm off the wall.

## Screws and hardware
* Pilot holes: **3.0 mm** (under the #8 thread of ~4.2 mm). Total 30 screws.
* **#8 x 1-1/2 in: 20** (top 4, shelf-to-back 2, sides 6, drawer corners 4, drawer bottom 4)
* **#8 x 1-1/4 in: 6** (runners 4, drawer face 2) - shorter on purpose, they go through 18 mm into another 18 mm part and must not poke out
* **#8 x 1-3/4 in: 4** (cleat backer, only if you build the wall mount)
* **Glue + screws**: wood glue (Titebond II or III) on every tab, slot and finger face, then the screws as clamps. The glue is the joint; the screws hold it tight while it cures (1 hour before handling, 24 hours before loading) and stay in as reinforcement. A tab-and-slot joint has a lot of glue area, so a glued joint is stronger than the plywood around it; screws alone would work loose over time. Scrape or sand the charred laser faces in the tabs and slots first: carbon glues badly. Do not glue the drawer into the carcass (it rides on the runners). Fill the 4 top screw holes and sand before painting.
* Optional: 2 felt/UHMW strips on the runner tops, a knob if you do not like the slot pull.

Screw positions: cleat = 4 through the back into the backer (only if built); top = 1 per side between the tabs + 2 into the back top edge; shelf = 2 up into the back bottom edge; each side = 1 into shelf edge, 2 into the back edge, 2 into the runner; drawer = 1 per corner (4), 1 per side into the bottom (2), 1 each through box front and back into the bottom edge (2), 2 from inside box front into the face.

## Assembly order
1. Lay SIDE-L flat, glue the back and shelf tabs into its slots, then fit SIDE-R on the other ends (tap with a mallet and a scrap block). Screw from outside.
2. Screw the runners on (both sides) with the carcass on its back; both must be level with each other (410-430 mm above the floor).
3. Lay the top upside down, stand the carcass on it so the side tabs enter the top slots, glue, then drive the 4 top screws (2 into the side edges, 2 into the back edge). Check the 4 feet touch the floor (a shim or a sanded foot if the floor is not flat).
4. Optional cleat, **now, before the drawer**: glue backer A to the back's rear face, glue B on A, and drive the 4 x #8 x 1-3/4 from inside the carcass; clamp or weight it till the glue sets. Then fit the Z-bar to B.
5. Drawer: glue the finger joints and bottom tabs, check it is square, drive all box screws (the two bottom screws through the front go in now, before the face). Then glue and screw the face from inside with the box sitting in the opening on 2 mm shims for an even gap.

## Cutting notes (ACMER X1 Ultra, 120 W diode)
* ACMER's published capacity is plywood up to **28 mm in one pass** at 120 W. They publish **no feed rate for 18 mm ply**. I could not find one, so the numbers here are only starting guesses; set your own from the test below.
* **Test on scrap first**: cut the TEST-SLOT / TEST-TAB coupons and a row of 3 mm holes. The tab must slide through with finger pressure and be flush. If it is loose, the cut is wider (kerf) than drawn; if tight, widen the clearance or use LightBurn's Kerf Offset.
* Starting guess: 120 W mode, full power, **100-200 mm/min**, one pass, air assist on high; go slower or run a second pass if the cut does not clear. Edges will be dark and slightly tapered (wider on the top face); you paint, so sand/prime.
* Rough machine time: about 25.9 m of cut path -> roughly 2-4 hours at 100-200 mm/min (estimate, plus moves). Stay with the machine the whole time: cutting 18 mm ply can flare up.
* Hold the sheet flat. A warped sheet changes focus; weigh or clamp it; cut on the egg-crate bed so the beam passes clear below the sheet (burn-through will mark the bed).
* **Kerf**: the drawn slots are tab + 0.1 mm and kerf compensation is *noted, not applied*. A 0.25 mm kerf removes ~0.125 mm per side, so uncompensated cut slots come out about 0.25 mm wider than drawn and tabs about 0.25 mm narrower (total gap near 0.6 mm, partly closed by edge char/taper). For a tighter fit use LightBurn's Kerf Offset (0.125 mm: inside-out for outlines, outside-in for holes) or lower the clearance. Decide from the coupons. Pilot holes are 3.0 mm drawn (cut ~3.25 mm); check a screw bites in your scrap, redraw 2.8 if not. Laser holes taper over 18 mm; screw from the wider (top) side where you can.
* **Order of operations**: (1) coupons, (2) all 3 mm pilot holes and slots/obround pulls (inner features), (3) small parts: runners, drawer sides, front/back/face, (4) the large outlines last (SIDE, TOP, BACK, SHELF). In LightBurn use "Cut Inner Shapes First". The DXF has no hold-down tabs, so each part drops free when its outline finishes; for the big parts add 2-3 micro-joints in LightBurn or pin them, then snap and sand them off.
* Dry-fit everything before glue. Wipe resin and char out of the slots with a rag; a small chisel or file only if the coupon needed it.

## What was checked (see `checks.txt`)
* 15 parts, tabs/slots: 18 tab-slot pairs; each slot = tab length + 0.1 mm by 18 + 0.1 mm = 18.1 mm; every tab is exactly 18 mm long (flush through). Cleat backer parts and the foot notch added in rev 2. DXF read-back shows slots of these sizes: {(100.1, 18.1): 4, (80.1, 18.1): 10, (60.1, 18.1): 4, (30.1, 18.1): 1}
* 3D overlap test of all parts in the assembled position: **0 overlaps** (and the test does catch an undersized slot), re-run after the rev 2 changes.
* Every screw path (30) stays inside its parts, the tip is >= 1 mm inside the mating part (no poke-through).
* Nest: no overlaps, min spacing 6.0 mm, all geometry within 2440 x 1220 mm (6 mm border), used 986 mm of the 1220 mm width.
