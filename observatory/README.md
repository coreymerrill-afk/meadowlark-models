# H3C Celestial Observatory — v1.2.0

Print-test model for a **Bambu Lab H3C Full Combo** with **0.4 mm** nozzles only
(the machine's 0.4 mm PrintTools, plus seven extra 0.4 mm hotends). PLA first.
Optional feet are black TPU 75A and are not required for the mechanism.

**CAD checks passed. Not printed. Not measured.** Clearances below are design targets
from this CAD file, not caliper readings and not a finished-print result.

## Print the coupon first

`stl/fit_coupon.stl` is the first plate. It is one body:

- Ø4.0 hole ladder, left to right: 4.00, 4.20, 4.30, 4.50, 4.80 mm. The separate `fit_pin` is Ø4.0.
- Ø8.0 hole ladder, left to right: 8.30, 8.50, 8.70, 9.00 mm. A snap-off Ø8.0 pin is on the same plate.
- A 14 mm bridge, 1.6 mm thick, between two piers.
- The hinge design target is the 4.30 mm hole. The axle design target is the 8.50 mm hole.
  If those are tight or sloppy, stop before printing the observatory. This page cannot see that result.

## Mechanism

The tower is an 84 mm drum. The deck sits on a shelf on that drum (0.12 mm CAD gap),
and the 8 mm axle only registers the spin. It is not the structure.

1. Drop the axle flange into the underside well.
2. Press the tower peg into the base. The shoulder seats on the plinth; the peg does not bottom out.
3. Set the deck on the tower shelf. It should turn on the axle.
4. Set the dome skirt in the deck groove. It turns on its own. The shutter opening faces +X.
5. Sit the telescope in the cradle and slide a hinge pin in from each side, head outward.
6. The axle continues through a loose hole in the crown. Sit the orrery on the axle shoulder above the dome.
7. Slide the retainer down the tip into the groove. It should not clamp the arm.
8. Press inlays into the eight base pockets. Feet are optional.

Home telescope elevation is 32° above the deck, toward +X.
The CAD range that stays clear of the dome and the deck is 24° to 46°.

Supports, for a 0.4 mm nozzle and 0.20 mm layers: dome wants tree supports inside the shell.
Telescope bosses want support. Everything else is meant to print without supports.
Leave supports off for the coupon so the bridge is actually a bridge. This has not been sliced.

## Files

| File | What it is |
|------|------------|
| `stl/*.stl` | One watertight mesh per part, bed on Z = 0. Not a toolpath. |
| `h3c_celestial_observatory_stls.zip` | Those STLs. Not sliced. |
| `h3c_celestial_observatory.3mf` | Colored assembly scene (face colors). **Not** a Bambu plate layout and **not** presliced. |
| `manifest.json` | Quantities, colors, 4×4 assembly transforms, pivots. |
| `generate_observatory.py` | This source. |

## Clearances (design targets, unverified on a machine)

| Interface | Target |
|-----------|--------|
| Axle 8.0 in tower and deck bores | 8.5 mm (0.50 mm diametral) |
| Axle in the orrery | 8.8 mm |
| Axle through the base and the dome crown | loose, not a bearing |
| Hinge pin 4.0 | 4.30 mm holes |
| Dome skirt in the groove | 0.30 mm radial each side, 0.35 mm above the groove floor |
| Inlay in its pocket | 0.20 mm lateral each side |
| Tower peg | 0.20 mm radial, does not bottom out |
| Retainer on the groove root | 0.20 mm radial |
| Deck above the shelf | 0.12 mm |
| Assembled envelope | under 220 mm. Stack height is about 132 mm plus the feet below the base. |

Regenerate with `python3 generate_observatory.py` from this directory
(`manifold3d`, `trimesh`, `numpy`, `scipy`, `rtree`, `pillow`, `matplotlib`).
