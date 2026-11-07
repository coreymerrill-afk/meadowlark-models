# Queen Anne Playhouse — v6.0.0

A 1:24 house drawn from the approved picture at `concept/approved-direction.jpg`. That picture is the visual direction. It is not a measured survey and it is not a render of this CAD. The picture's open view is a side cutaway. This house opens at the back.

The closed house is about as wide as the spire is tall. An octagonal turret stands on the left. A street gable, in sage, sits in front of the slate slopes, with rake bargeboards and an owl. The porch wraps the turret. Shingles are thin scallops in the mesh. The front and the right side are solid walls with clear sash openings.

v4 is in `archive/v4.0.0/`. v5 put a removable shell on every room. Those shells sat off the house. They are gone.

## How it is played

One wall comes off: the full back. It is one print, 285 × 7 × 189 mm, under the 310 × 300 × 315 mm allowance. Closed, its inner face is 0.45 mm behind the jambs and it does not occupy their volume. It pulls straight off on nominal 5.0 × 2.8 mm discs. There is no sill hook. The front, sides, porch, floors, and roofs stay. The back is not a brace, and the magnets are not what holds the house up. The roof bears on the fixed plates with the back off.

Two stair flights have treads, risers, and a spindle rail. The lower flight climbs from the entry to the first floor. The upper flight climbs from that floor to the attic. The wells are open. The hall wall stops short of the rear opening.

## Lighting

Ten fixtures: eight ceiling pucks and two porch lanterns, on the fixed frame or the porch, not on a magnetic wall. The 6 × 6 × 3 mm cavity is a reservation. At a 20 mA planning figure the house is 0.20 A. That current was not measured. No fuse is nominated from the sum. The 24-LED / 0.48 A research scenario is not this house. Nominal 5 V USB, no mains.

## Ornament

Balusters, bargeboard piercings, blossoms, and scallop edges are thin. A 0.2 mm nozzle is the setting for that ornament. Structural walls are not held to that same minimum. None of it is claimed durable or safe.

## Checked

`python3 cad/build_queen_anne_v5.py` writes the STLs. Each part is one solid and fits the 310 × 300 × 315 mm allowance. The audit found no resting overlap above 2 mm³, a bearing probe under each roof, and open stair wells. The headroom probe clears 72 mm. The viewer loads these STLs.

## Not checked

No print, no slicer, no strength test, no tip-over test, no magnet pull test, no electrical test. Roofs are gravity seated. Magnetic support is unverified. Not a toy-safety certification.

Departures from the picture are in `manifest.json` under `departures_from_concept`.
