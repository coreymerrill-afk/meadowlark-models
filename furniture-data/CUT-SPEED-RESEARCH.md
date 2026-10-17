# Cutting speed on 18 mm (3/4 in) plywood: research and the model behind the machine times

Researched 2026-10-17. Everything below is a desk estimate. Nobody has published a verified 18 mm plywood cut for the ACMER X1 Ultra, and none of this was measured on Corey's machine. One timed test cut on scrap replaces all of it.

## What ACMER says about the X1 Ultra
- 120 W diode, plywood "up to 28 mm", 40 mm only for paulownia (soft, balsa-like) wood. Pass count and feed for plywood are not published. [Hackster](https://www.hackster.io/news/acmer-s-massive-new-laser-cnc-can-cut-an-entire-sheet-of-plywood-b1a9dd8e1123), [GizmoCrowd Kickstarter review](https://www.gizmocrowd.com/post/acmer-x1-laser-engraver-review)
- Claims "3-4x faster than a 40 W laser and 2x faster than an 80 W laser" in ACMER's own tests; 30,000 mm/min is the maximum motion speed, not a cutting speed. [ACMER X1 page](https://x1.acmerlaser.com/), [Laserbuying review](https://www.laserbuying.com/blogs/articles/acmer-x1-review-the-3-in-1-workshop-machine-makers-have-been-waiting-for)
- ACMER's own settings page has no X1 table and no 18 mm entry; it only says test each batch and use more passes when speed alone is not enough. [ACMER material settings](https://acmerlaser.com/pages/material-setting)
- Caution: some sellers say "120 W" diode labels mean electrical input, with far less optical power. ACMER and the reviews above present 120 W as laser output. Unverified either way.

## Diode data points for thick plywood / wood (effective rate = speed / passes)
| Machine | Material | Speed, passes | Effective | Source |
|---|---|---|---|---|
| Sculpfun SF-A9 40 W optical | 18 mm rubberwood with glue joints | 300 mm/min, 95 %, 4 passes | 75 mm/min | [r/lasercutting](https://www.reddit.com/r/lasercutting/comments/1l1tkbt/cut_plywood_18mm_with_diode_laser/) |
| 40 W optical diode | 18 mm birch ply | 2 passes, "excessive charring", speed not given | n/a | [r/hobbycnc](https://www.reddit.com/r/hobbycnc/comments/1l1t26d/diode_laser_for_cut_18mm_plywood/) |
| Atomstack A70 Max, about 70 W | 3/4 in | "more than 4 passes at 700 mm/min" | under 175 mm/min | [r/lasercutting](https://www.reddit.com/r/lasercutting/comments/1l1tkbt/cut_plywood_18mm_with_diode_laser/) |
| Atomstack A70 Pro | 18 mm pine board (softer than ply) | 600 mm/min, 3 passes | 200 mm/min | [Hobby Laser Cutters review](https://hobbylasercutters.com/atomstack-a70-pro/) |
| Atomstack A70 Pro | 10 mm poplar plywood | 300 mm/min, 1 pass | 300 mm/min (10 mm) | same review |
| Low-power NEJE module | 18 mm plywood | 120 mm/min, 8 passes | 15 mm/min | [NEJE wiki](https://neje.wiki/doku.php?id=m_db) |
| Sculpfun S30-class | 10 mm plywood | 180 mm/min, up to 12 passes (S30) / 300 mm/min, 2 passes (S30 Pro Max) | 15-150 mm/min | [Sculpfun](https://www.sculpfun.com/pages/machine-details) |

Scaling to the X1 Ultra's 120 W using ACMER's claim: 75 mm/min (40 W) x 3-4 = 225-300 mm/min; 200 mm/min (A70 Pro) x 1.8-2 = 360-400 mm/min. If the real optical power is lower than claimed, 120-150 mm/min.

## What the 4 W IR module does
It is a 1064 nm marking module for metal, ceramic and coated surfaces. It cannot even cut metal sheet, so it is unsuitable for cutting 18 mm plywood. [Laserbuying](https://www.laserbuying.com/blogs/articles/acmer-x1-review-the-3-in-1-workshop-machine-makers-have-been-waiting-for) (the conclusion for plywood is mine, from that spec and the wavelength).

## Commercial scale-up reference
- **3-6 kW fiber lasers (what Madam Metalworks runs) are not a wood tool.** Wood absorbs the 1 micron wavelength poorly; expect poor cuts and fire risk. Use CO2 for plywood. [OneLaser](https://www.1laser.com/blogs/topic/laser-cutting-plywood)
- Smaller CO2 (100-150 W), manufacturer table for 18 mm plywood: 1-2 mm/s = 60-120 mm/min, and rated "not rated" below 100 W. [OneLaser settings table](https://www.1laser.com/blogs/topic/laser-cutting-plywood). Generic CO2 guide: 18 mm birch 2-5 mm/s, 3-5 passes. [Hflaser](https://www.hflaser.com/laser-cutting-wood-best-practices-for-mdf-plywood-and-hardwood.html)
- 300 W CO2: plywood to 20 mm at 8-12 mm/s = 480-720 mm/min (vendor figure; its own list calls 18 mm "rapid cutting for flat-pack furniture"). [Redsail](https://www.redsaillaser.com/archives/4204.html)
- 500-600 W CO2 tubes: 18 mm die-board (plywood) at 9-12 mm/s = 540-720 mm/min. [SLW laser tubes](https://www.slw-laser.com/laser-tube/slw-300w-co2-laser-tube-cutting-plywood-18mm.html)
- Reality check: a sourced 300-600 W CO2 flatbed cuts about 480-720 mm/min in ONE pass, roughly 2x the diode typical case, not 10-20x. A 10-20x factor is only plausible by combining faster cutting, much faster rapids, no multi-pass, and auto loading, and I found no source for it on 18 mm plywood. For real volume a nesting CNC router is the usual commercial tool; that was not researched here.

## Rates used in the plan.json model
| Case | Passes x speed | Effective rate | Basis |
|---|---|---|---|
| Slow | 5 x 600 mm/min | 120 mm/min | "120 W" behaves like a 60-70 W optical diode (A70 Max data) |
| Typical | 4 x 1200 mm/min | 300 mm/min | ACMER 3-4x claim on the 40 W data point |
| Best | 2 x 1200 mm/min | 600 mm/min | Close to ACMER's single-pass marketing; unverified |
| Commercial CO2 (sourced) | 1 x 600 mm/min | 600 mm/min | 300-600 W CO2 vendor figures, 60 m/min rapids, 5 min/sheet, $8/h operating cost (assumed) |
| What-if 10x / 20x | n/a | n/a | Corey's what-if on the diode typical cut + travel time; assumption, not sourced |

Machine time per unit = path / effective rate + rapid travel (nearest-neighbour hop between the contours in the DXFs, repeated every pass, at 10,000 mm/min plus 0.3 s per contour per pass) + 15 min per sheet for loading, focusing, the fit-test coupon and unloading (5 min for commercial). Path lengths and contour counts come from each design's DXFs (`plan.json` -> `profit.cut_path_m`, `profit.contours`, `profit.rapid_travel_m`). Wear/electricity is $1.70 per machine hour on the diode (assumption), $8 on the commercial machine.

The old estimate (100-200 mm/min single pass, 150 headline) is not used. It sits near the slow case. Corey's "under an hour" instinct only matches the best case for the smaller pieces.

## Still unverified
1. Real X1 Ultra pass count and feed on 18 mm plywood (and whether "120 W" is optical power). Do a timed test cut on scrap.
2. Edge char and glue-line behavior at that many passes; thick plywood may need the CNC for clean edges.
3. Rapid travel actually reaching 10,000 mm/min and the 15 min per sheet setup.
4. Commercial CO2 numbers are vendor claims; the 10x / 20x cases are assumptions.
5. Plywood grade (birch vs basic, void-free vs not) changes the speed a lot.
