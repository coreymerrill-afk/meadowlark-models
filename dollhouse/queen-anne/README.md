# Queen Anne Playhouse — v5.0.0

A 1:24 house drawn from the approved picture at `concept/approved-direction.jpg`. That picture is the visual direction. It is not a measured survey and it is not a render of this CAD.

The closed house is about as wide as the spire is tall. An octagonal turret stands on the left. A street gable, in sage, sits in front of the slate slopes, with a scalloped base board, rake bargeboards, and an owl in the opening. The porch wraps the turret and runs across the ground floor: turned columns, cyma brackets, a spindle rail, and steps. Shingles are individual scallops. Clapboard, belt courses, casings, and flower boxes are in the meshes.

v4 is in `archive/v4.0.0/`. It was a narrow stack with a flat porch and bar roofs.

## How it is played

The side walls are the everyday opening. They are the full depth of the rooms and pull straight off. There is no sill hook and no slide channel. The porch stays, and so does the ground-floor street wall, because a straight pull of that wall would have to pass through the porch. The upper front, above the porch roof, pulls straight off. The turret drum stays: a wrapped octagon cannot slide off its floors. The joint between turret and main block is a hairline.

Two stair flights are in the mesh, with treads, risers, and a spindle rail. The lower flight climbs from the entry to the first floor. The upper flight climbs from that floor to the attic. The wells are open.

## Lighting

Ten fixtures: eight ceiling pucks and two porch lanterns, on the fixed frame or the porch, not on a magnetic wall. The 6 × 6 × 3 mm cavity is a reservation. At a 20 mA planning figure the house is 0.20 A. That current was not measured. No fuse is nominated from the sum. The 24-LED / 0.48 A research scenario is not this house. Nominal 5 V USB, no mains.

## Ornament

Balusters, bargeboard piercings, blossoms, and scallop edges are thin. A 0.2 mm nozzle is the setting for that ornament. Structural walls are not held to that same minimum. None of it is claimed durable or safe.

## Checked

`python3 cad/build_queen_anne_v5.py` writes the STLs. Each part is one solid and fits the 310 × 300 × 315 mm allowance. The audit found no resting overlap above 2 mm³, a bearing probe under each roof, and open stair wells. The headroom probe clears 72 mm. The viewer loads these STLs.

## Not checked

No print, no slicer, no strength test, no tip-over test, no magnet pull test, no electrical test. Roofs are gravity seated. Magnetic support is unverified. Not a toy-safety certification.

Departures from the picture are in `manifest.json` under `departures_from_concept`.
