# Published copy

Viewer route: `/pasta-cooker/`. The note below is the Blender 4.2.9 handoff, kept for the limits and the file list. Its closing line — target repo not verified, not integrated — described the asset drop before this page. It is not a performance claim. No validation was added with the page.

# PASTA / 01 — automatic pasta cooker concept

**CONCEPTUAL / UNBUILT. Roughly 15 minutes dry-to-cooked is an unvalidated design goal, NOT a performance promise.**

## Actual deliverables / provenance
Procedural editable Blender geometry generated locally with Blender **4.2.9 LTS**, built-in Python/bpy, Cycles CPU rendering (24 samples), built-in glTF exporter. PNG annotation uses Python Pillow 13.0.0. No Shapecast or Meshy was used: parent connector search found no matching connector. No paid generation, purchases, credentials, or external uploads. All geometry is newly created from primitives, mesh walls, curves and rings; no downloaded product meshes or reference-image tracing.

- `pasta-cooker-assembled.blend` and `.glb`: full exterior and internal components.
- `pasta-cooker-cutaway.blend` and `.glb`: casing and lid hidden, sectioned vessel wall shows basket and plumbing.
- `pasta-cooker-exploded.blend` and `.glb`: selected modules translated apart, plumbing stays in assembled reference position (not a connected working configuration).
- `exterior.png`, `cutaway.png`, `exploded.png`: annotated actual Blender renders.
- `*-raw.png`: original renders; `*-anchors.json`: camera-projected annotation points.
- `generate.py`: complete modeling/render/export source. `annotate.py`: annotation source.
- `build.log`: execution evidence.

Reproduce: `blender -b -t 6 --python generate.py` then `python3 annotate.py`.

## Architecture and path reading
Nominal exterior envelope about **480 x 360 x 410 mm**, indicative only; Blender coordinates and GLB are meters. Individual named geometry remains editable; mesh basket ribs/hoops visually represent perforations, not manufacturable screen sizing.

1. Blue removable clean-water tank -> metering pump -> blue cold-feed pipe -> orange serpentine flow-through heated channel -> elevated rim outlet/air-gap concept into vessel. This is the actual depicted geometric route; metering sensors, valve internals and backflow compliance are not designed.
2. Separate salt hopper/funnel and illustrative auger chute dose into vessel, keeping salt out of upstream clean-water/heater path. Salt feed rate, bridging and moisture sealing need testing.
3. Shape/portion dial and screen represent the selection UI. A conceptual load-cell block sits at lift support. No weighing/control implementation.
4. Dry pasta sits in removable wire/perforated basket within stainless sectioned vessel. Tall lift rail/carriage and basket bridge indicate automated lift/drain; no actuator sizing, limit switches, locking or animated mechanism.
5. Orange base plate denotes **direct vessel heating**, a distinct optional heat input. The heated-channel path is not replaced by it.
6. Green loop: screened side suction outside basket -> recirculation pump -> broad tangential return manifold. No pasta through pump intended. Ribbed guard is only a visual placeholder; flow and starch behavior unvalidated.
7. Brown vessel-bottom drain -> actuator/valve concept -> removable waste drawer. No safe drain timing, venting or full-tank sensing implemented.
8. Rear low electrical compartment and separating wall indicate intended wet/dry segregation, not proof of waterproofing or electrical compliance. Steam vents are rear-facing on removable lid.

## Heat strategy comparison — no invented validation
**Channel + vessel heater:** may stage hot fill and vessel recovery, but adds pressure/drop, scale, dry-fire and service issues. Splitting a household circuit's finite power does not create extra energy; two heaters cannot simply be run at unrestricted rated power together. Requires power arbitration, flow/temperature sensing, thermal cutouts, anti-scald design and pressure analysis. No flow rates or heating times have been validated.

**Vessel-only alternative:** bypass/remove channel block and feed cold water via a safe rim inlet; retain direct heater plate. Fewer narrow hot passages, simpler descaling, but must heat full vessel/water mass before or during cooking. Could be equally or more practical on a constrained outlet. No claim that either reaches the target.

Useful lower-bound check, NOT a simulation: heating 1 kg water from 20 to 100 C requires roughly 334 kJ; at an illustrative 1.5 kW that is 223 seconds at impossible 100% system efficiency, before vessel losses and pasta cooking. Actual household supply, portion, shape, water volume, recovery and algorithm must be measured. Neither model is a pressure cooker.

## Safety and cleaning requirements before engineering
- Steam/scald: interlocked lid and basket motion, safe vent direction, cool-touch gripping, splash control, drain temperature controls, obstruction and full-waste detection. No user access during hazardous motion/hot drain.
- Cleanability: tool-free removable tank, basket, vessel, waste drawer and serviceable pump guard; drain low points, eliminate dead legs, accessible descaling and seals. The concept does not prove complete drainability or dishwasher suitability.
- Starch clogging: test foaming, strainer fouling, channel scale, pump cavitation and drain blockage. Prefer clean-water-only upstream heated channels; flush/clean any starch-bearing recirculation path. Broad circulation is a design intent, not an anti-sticking guarantee.
- Water/electrical segregation: secondary containment, leak sensing, strain relief, grounding, rated components, splash ingress and thermal fault testing needed. Depicted wall is packaging intent only.
- No thermal/CFD, structural, food-contact materials, hygiene, certification, tolerance, power-budget or mechanism validation. No BOM, wiring or fabrication instructions.

## Website handoff
GLBs use embedded PBR materials, named nodes and concept metadata. No remote textures or services required. Three static states; no working simulation/animation. PNGs are ready as poster images. Asset work only: target repo/domain not verified here; **not integrated or live**. Website owner should choose model-viewer/Three.js integration, set camera/framing, preserve conceptual disclaimer, and run browser/mobile load checks before publishing.

## Method references
Official Blender scripting/export documentation: https://docs.blender.org/api/current/bpy.ops.export_scene.html and https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html . Bounded public search also checked “Grok Bot Blender” X posts; social posts were not used as engineering or safety evidence.
