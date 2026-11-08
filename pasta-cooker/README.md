# Published copy

Viewer route: `/pasta-cooker/`. This page replaces the rejected v1 geometry. The note below is the Blender 4.2.9 v2 handoff. Its line that no website change was performed described the asset drop before this page. No hydraulic, thermal, or safety validation was added with the page. About 15 minutes dry-to-cooked remains unvalidated.

# PASTA / 02 — topology-first replacement concept

**UNBUILT / NOT FABRICATION-READY. The approximately 15-minute dry-to-cooked goal is not validated.**

## What was actually wrong
Corey's objection was justified. V1's clean feed actually penetrated the waste solid; its drain had an unpumped 65 mm uphill leg and no chamber-floor opening. The heater inlet joined the wrong vertex, circulation ports were implied rather than modeled, and exploded module translations disconnected pipes. See `AUDIT-V1.md` for coordinates, dimensions and exact causes. This is not repaired by labels: v2 uses new geometry and a new port-defined plumbing graph. V1 is untouched.

## Read the replacement
- `pasta-cooker-v2-exterior.blend` / `.glb`: exterior guards built around the routes; paths deliberately exposed rather than buried in an opaque decorative box.
- `pasta-cooker-v2-cutaway.blend` / `.glb`: front tank/chamber/waste walls, lid and dry exterior guards removed. Actual sloped floor opening, strainer, waterline, waste headspace and receiving connection can be inspected.
- `pasta-cooker-v2-exploded.blend` / `.glb`: service/lift view. Basket/carriage raised 190 mm, lid removed vertically/aside. **No plumbed module is displaced**, so tank/heater/valve/waste connections remain real and consistent. This intentionally avoids v1's disconnected “explosion.”
- `exterior.png`, `cutaway.png`, `exploded.png`: annotated actual Blender renders; flow-arrow meshes lie on actual route segments.
- `plumbing-graph.png`: graph with same-chamber aliases clearly identified; schematic, not physical layout.
- `connection-manifest.json`: authored node ports, component internals, all routed edge control points, units/radii, intended free-fall transfers.
- `topology-checks.json`: endpoint, tangent, gravity, selected spatial/clearance test results. `view-topology-checks.json` separately compares actual curve endpoints with actual port-collar world positions in every saved state. `CHECK-SUMMARY.json` provides the lean result.
- `generate.py`: complete procedural Blender source; `presentation.py`: annotated renders/graph source.

All dimensions in manifest/script are millimetres; Blender and GLB are metres. Overall chassis about 660 x 480 mm, with lift mast reaching approximately 715 mm. This is a deliberately larger proof-of-layout concept, not an optimized compact countertop package.

## Actual circuits and interfaces
**Clean feed:** hollow removable unsalted tank side bore → isolation/check cartridge provision → metering pump → flowmeter → isolated heater channel (ceramic separator and dry back enclosure) → elevated nozzle. The hot nozzle ends at z480; max chamber waterline is z420. Dotted beads are free-falling water, not a pipe bridging the air gap. Clean routes stay left; no clean line enters, traverses or connects to waste.

**Chamber circulation:** broad open bar-screen cartridge lies inside the vessel, outside the basket's radial envelope. Its hood connects to a bored wall port, a service union, a heat-compatible pump placeholder, a separate return wall port, and a tee feeding broad outlets into the same chamber. Only the tee is a branch. Screen spacing, pump compatibility, flow, anti-sticking, service seals and starch performance are unvalidated. Service union is accessible after isolation/cooling; removal sequence needs engineering. No pasta is intended to enter pump, but screening is not proven.

**Drain:** sloped chamber floor converges to a genuine open off-axis low point at z235. Pipe meets top of NC valve vertically at z215; output z185; downstream route stays level/downhill to a vertical removable receiving coupling at z135. A receiving stub extends to z120 inside waste headspace; maxfill is z95. Waste reservoir lies below the entire floor, not beside/above it. Valve body has a bore and an explicitly **closed default gate**, with actuator/stem beside its bore. This is not a claim that drain control has been engineered. Waste has its own vent, an inlet coupling and a local drip tray. Tube elbows meet bores axially instead of ending obliquely on a tank lid.

**Salt/steam/lift:** dry salt cartridge and metering gate have a genuinely downhill chute into the chamber annulus; clean upstream water remains unsalted. Salt fill outlet, hot fill outlet and rim-supported steam standpipe are outside the basket's full radial lift sweep, including port collars. Basket bottom rises from z280 to z470, clearing z455 vessel rim by 15 mm and remaining directly over chamber. No lateral discharge position is shown. Lid has actual separate apertures around fixed nozzles/standpipe; the steam pickup is a rim-supported headspace standpipe, NOT attached to the removable lid. Steam exits rear-left, away from the rear-right segregated dry bay. Neither steam routing nor bay barrier proves safe condensation/ingress performance.

## Tests — narrow, explicit scope
The generator tests actual Blender curve endpoint coordinates against named port coordinates with <0.01 mm tolerance, and checks endpoint tangents against declared component bore axes. It also checks:
- nonascending drain centerline, including valve and receiving stub;
- tube-radius-padded sampling against unrelated clean-tank, waste and dry-bay AABBs;
- exact segment-to-segment centerline distances minus tube radii between distinct hydraulic circuits;
- basket lift height and radial nozzle/steam collar clearance;
- geometric air gap and waste maxfill/headspace relationships.

Ports deliberately connect to component bores; internal pump/check/meter mechanisms are abstracted, not simulated. Selected clearance checks are **not** a complete solid interference, swept-volume, tolerance, structural or manufacturability analysis. Same-circuit self-clearance, hidden wiring, thermal expansion, screen fouling, all couplers and full service disassembly require further engineering. Named assemblies and ports are preserved in editable Blender files. Curves/meshes are real geometry, not images posing as a model.

## Before a physical design
Need food-contact material selection, water/electric separation and fault testing, leak containment, dry-fire/overtemperature and flow protection, power arbitration, pressure/scale analysis, safe venting/condensate handling, guarded/interlocked hot lift motion, verified drain temperature/overflow/full-waste shutdown, anti-siphon/backflow compliance, cleanable dead-leg-free details and starch/descaling tests. Waste maxfill is a geometric line only, not a sensor. No emergency overflow pipe is silently added: fail-closed feed plus independent high-level/waste-full detection and a safe containment/overflow strategy remain engineering requirements.

Channel-plus-vessel heating versus vessel-only remains unresolved: two heaters must share the available household power, not invent extra power. Channels can stage hot fill but add scale/flow/service faults; vessel-only reduces those passages but heats the vessel/water mass directly. No validated thermal advantage, cook time, efficiency, hydraulic performance or electrical safety is asserted.

## Provenance and reproduction
Local Blender 4.2.9 LTS / bpy / Cycles CPU, 24 samples. Pillow 13.0.0 annotates Blender renders and draws the clearly separate graph. No Meshy/Shapecast, paid generation, purchase, credentials, external uploads, repo edits or deployment.

Run `blender -b -t 6 --python generate.py`, then `python3 presentation.py`. `build.log` records execution. `pasta-cooker-v2-assets.zip` contains handoff assets, code, graph, manifest/checks and documentation; raw renders/logs remain alongside but need not be carried to the website.

**Website readiness:** static GLBs/posters for a replacement handoff only. No website change, upload, browser integration or live verification performed. Keep the conceptual disclaimer wherever displayed.

Final generator checks: 38 authored endpoint checks, 31 bore-axis tangent checks, 134 distinct-circuit segment clearance checks, no sampled unrelated tank/waste/dry-bay collisions; monotone gravity drain, 60 mm air gap, 15 mm basket-over-rim lift clearance. Minimum nozzle/steam collar-to-basket radial clearance is 5.247 mm nominal, without tolerance allowance. These checks do not certify safety or manufacturability.

`validate_saved.py` independently reopens all three final .blend files and compares actual routed endpoints to actual port-collar world positions; `final-saved-geometry-checks.json` records the final saved-state evidence. Minor rear cradle radial ties were added to connect the structural uprights to the support ring; they are included in the canonical generator.

The waterline is a geometric upper limit, not a validated portion recipe or water-volume/thermal budget. Salt bridging/moisture sealing, condensate management and all real component ratings remain unengineered.
