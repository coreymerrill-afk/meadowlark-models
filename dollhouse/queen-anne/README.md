# Queen Anne Playhouse — v4.0.0

A 1:24 house in the direction of the approved picture at `concept/approved-direction.jpg`. That picture is a visual target, not a measured drawing and not a render of this CAD.

The house has an octagonal turret with a conical roof, a pitched main roof with shingle courses, a wraparound porch with turned posts and balusters, clapboard on the facade shells, and a masonry base. v3 is in `archive/v3.0.0/` because it still read as stacked blocks.

## How it is played

The front shells and the side shells are the full width of those walls and pull straight off. There is no sill hook. The porch stands in front of the ground-floor wall, so the porch lifts off before that wall is pulled. The turret drum stays put: a wrapped tower cannot slide straight off its own floors. Side walls pull with the porch still down.

Two stair flights are in the mesh. The lower flight climbs from the entry to the first floor. The upper flight climbs from that floor to the attic. The turret loft is the same floor, reached across the turret opening.

## Lighting

Ten fixtures: eight ceiling pucks and two porch lanterns. They sit on the fixed frame or the porch, not on a magnetic facade. The 6 × 6 × 3 mm cavity is a reservation. At a 20 mA planning figure the house is 0.20 A. That current was not measured. No fuse is nominated from the sum. The 24-LED / 0.48 A research scenario is not this house. Nominal 5 V USB, no mains, no coin cells.

## Checked

`python3 cad/build_queen_anne_v4.py` writes the STLs. The audit found no resting overlap, a bearing probe under each roof, open stair wells, and 76 mm clearance from the steps up to the next floor. Straight pulls of the facade shells did not hit the parts that stay.

## Not checked

No print, no slicer, no strength test, no tip-over test, no magnet pull test, no electrical test. Roof and porch uplift are not locked. Magnetic support is unverified. Not a toy-safety certification.

Departures from the picture are listed in `manifest.json` under `departures_from_concept`.
