# Queen Anne Playhouse — v3.0.0

One 1:24 house. The parlor, entry, and living room share the ground floor. A porch is the front of the entry, and the bay is the living room pushed forward. Stairs in the tower climb to a landing, then to the loft. v1 and v2 are in `archive/`.

Facades pull straight off. There is no sill hook, side groove, or slide-then-lift. Each stile has three nominal 5.0 × 2.8 mm magnet pairs. A capture bar closes the magnet channel. It does not fasten the panel. Holding force was not calculated. The coupon is the pull test.

The frame may use posts, plates, and laps. Roofs sit on their own plates with a 0.45 mm seat gap. They are not locked against a lift.

## Rooms

| Storey | Rooms |
| --- | --- |
| Ground | Parlor, entry, living room with bay, porch |
| Second | Tower bedroom, upper hall, living bedroom |
| Loft | Tower third floor, reached by the upper flight |

Doorways connect parlor to entry, entry to living, the landing to the upper hall, and the upper hall to the bedroom. Clear samples in those openings do not intersect the walls. Each stair well is open, the last riser stops 0.45 mm below the floor, and an 78 mm headroom sample along both flights is clear.

## Lighting reservations

This is not a buy list and not a finished circuit. The November 6, 2026 research note is the source. Prices and stock were a snapshot. Nothing here was purchased.

Recommended path: a regulated external nominal 5 V USB supply, then parallel warm-white **5–12 V DC** Evan Designs Chip/Nano LEDs, each with the resistor the maker supplies. Not the 3 V variant. No mains wiring inside the house. A regulated 12 V adapter is an alternative and needs protection rated for 12 V. An AA pack plus a boost converter is optional and is not the default; it is not modeled. No coin cells, loose lithium cells, or charging.

This house has **17** fixtures: a ceiling puck and a sconce in each of seven rooms, plus two porch lanterns and one entry lantern. The research scenario of 24 LEDs at 20 mA (0.48 A) is not this count. Seventeen times 20 mA is 0.34 A, and 20 mA is a planning figure. Current at 5 V was not measured.

| Reservation | Size |
| --- | --- |
| Ceiling housing | 12 mm diameter × 7 mm deep |
| Exterior housing | 8 × 8 × 12 mm |
| LED cavity | 6 × 6 × 3 mm, provisional, not fit-validated |
| Bare-lead feed | 2 mm diameter. A resistor or a plug does not pass |
| Plate channel | 4 × 3 mm, open upward in the fixed plate |
| Rear chase | 14 × 10 mm, added behind the rear wall. Corner posts are not hollowed |
| Connector pocket | 30 × 20 × 12 mm |
| Resistor pocket | 25 × 12 × 8 mm, in the channel, not inside the lamp |
| Adult service bay | 150 × 90 × 30 mm clear, behind the hall |

The harness stays on the fixed frame. Roofs have no lamps. Pulling a panel does not leave a wire hanging. Room circuits, the exterior group, and a master switch are planned in the adult bay. Covers are large service parts, not coin-sized lenses.

Protection is not selected. Littelfuse 1206L050 is a 6 V, 0.5 A hold candidate only. It is not sole protection for the unknown fine LED leads, and its resistance can drop a 5 V bus. A current-limited bench test is still required. Adafruit 501 is an out-of-stock voltage example, not a kit to order.

Research notes, not purchase approval:

- Evan Designs Chip/Nano/Pico LEDs: https://evandesigns.com/products/chip-nano-pico-leds
- Evan Designs LED sizes: https://evandesigns.com/pages/information-about-led-sizes
- Evan Designs regulated 12 V adapter: https://evandesigns.com/products/regulated-12-volt-dc-output-adapter-transformer
- Adafruit 501, 1620, 2697, 373, 1863, 261, 6180, 771, 1903: https://www.adafruit.com/
- JST PH: https://www.jst-mfg.com/product/index.php?series=199
- Littelfuse 1206L050: https://www.littelfuse.com/products/fuses-overcurrent-protection/polyswitch-resettable-pptc-devices/surface-mount-polyswitch-resettable-pptc-devices/1206l/1206l050

## What was checked

`python3 cad/build_queen_anne_v3.py` from `dollhouse/queen-anne` rebuilds the STLs, `manifest.json`, and `reports/validation.json`.

The CAD check found no resting overlap, a bearing probe under every roof, clear stair wells and 78 mm headroom samples, open doorways, clear window panes with sills, empty LED cavities, and fixture bodies joined to the frame. A straight pull of every panel at 0, 10, 22, and 40 mm did not hit the fixed house. Part bounding boxes fit 310 × 300 × 315 mm.

## What was not checked

No slicer run, no print, no H3C test, no strength test, no magnet pull test, no electrical test. Zero overlap is not a proof that a roof or a panel stays put. The 5 × 2.8 mm pocket is nominal. The 6 × 6 × 3 mm cavity is a reservation. This is not a toy-safety certification and not an electrical approval.

Regenerate with `python3 cad/build_queen_anne_v3.py`.
