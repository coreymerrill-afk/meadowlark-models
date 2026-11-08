# V1 geometry audit — Corey was right
Coordinates below refer to v1 script units, each equal to 100 mm. These are actual geometric faults, not labeling problems.

1. **Clean feed intersects the waste volume.** Waste cube bounds are x=[1.165,2.115], y=[-1.475,.475], z=[.4,1.3]. Blue B feed's horizontal segment is (-1,-1.25,.9) → (2.05,-1.25,.9): 88.5 mm of centerline lies inside the waste cube. Its following rising segment also begins inside waste. This directly makes clean water appear to feed waste. No physical segregation was checked.
2. **Drain rises into the tank instead of gravity draining.** D route ends (1.64,-.65,.7) → (1.64,-.65,1.35), a 65 mm uphill leg, without a drain pump. Waste tank top is z=1.3; no inlet/coupling is modeled.
3. **No actual chamber drain opening.** D starts (.6,.3,1.12) inside the solid vessel floor disk (z=1.09–1.21), with no hole. The actuator cube happens to intersect the brown line; it is not a valve with defined input/output ports.
4. **Heater feed enters partway along a channel.** B ends at the second serpentine vertex (1.96,-.72,1.8), not its first (1.33,-.72,1.8). A 63 mm dead leg remains, with no defined inlet bore.
5. **Pump/tank ports are implicit penetrations.** Clean output starts inside a solid tank cube and both pump connections terminate inside a featureless cylinder. No explicit isolation, check provision, flowmeter or tank port exists.
6. **Circulation strainer isn't attached to a chamber hole.** Suction starts (.95,.85,1.5), radius 105.5 mm from vessel axis, outside its 102 mm outer radius; neither wall port nor broad removable strainer is modeled. Decorative guard bars don't establish a fluid intake. Pump connections again terminate inside a cylinder.
7. **Salt route climbs 65 mm**, with no modeled auger mechanism or visible bore; filled hopper/cone solids and a line are not a mechanically legible gravity chute.
8. **Fill/steam/lift interfaces aren't resolved.** No maximum waterline establishes an air gap, no lid penetration accepts hot fill or salt, and the lift tower doesn't demonstrate full clearing travel. Electronics have no checked steam separation.
9. **Exploded view destroys connectivity.** Tank, heater, salt and waste are translated independently while their pipes remain fixed; apparent endpoints cease to match assemblies.

Root cause: exterior-first primitive composition, route polylines authored separately from component ports, no explicit topology, and no collision/endpoint/gradient checks. V2 is port/topology-first, with hydraulics kept assembled even in the service-exploded view.
