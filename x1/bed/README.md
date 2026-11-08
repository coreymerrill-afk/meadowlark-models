# Egg-crate bed revision — rectangular channels

Run `python3 make_egg_crate.py` with numpy, ezdxf, shapely>=2, matplotlib and mapbox-earcut installed.

- ONE blade profile × 48 and ONE rib profile × 14. Rib pitch 180 mm = 15 tooth pitches, with symmetric 60 mm end insets. Every blade slot is centered on the same tooth-valley phase (0 mm modulo 12 mm). Parts reverse end-for-end and face-for-face; they are not invertible top-to-bottom: teeth stay up, blade slots down, rib slots up. No indexed placement or left/right variants.
- Two 1200 × 1200 mm panels; each 24 blades and 7 ribs, 3.18 mm steel.
- Blade tips 38 mm above the plate; valleys and rib tops 34 mm. No rib material may exceed 34 mm in assembled mode. Tooth tips alone support stock.
- Opposing slots exactly 17 mm deep (half 34 mm rib height). Finished slot width 3.4 mm, including 0.22 mm clearance. Supplier applies kerf compensation ONCE, to finished-part outlines, not by modifying the nominal width. Test a mating coupon before ordering a full bed.
- Blade vents six rectangles, 120 × 20 mm; 25 × 20 mm relief at each end. Aligned ends give a 50 × 20 mm continuous channel across the middle seam.
- Rib vents 30 × 12 mm between each adjacent blade, providing passage along the blades too. Vents never overlap half-lap slots; rib steel remains connected.
- All four DXFs, PDF and assembly render regenerated from this source. CUT layers only; LABELS and SHEET are references.
- Confirm machine opening and loading before fabrication. This is not a structural certification.

## Diagnosis / limits
The previous browser model rounded all four vent corners while the DXF generator rounded only the two upper corners. Neither had seam reliefs or rib vents. Both used 17.3 mm laps (0.6 mm vertical gap), now exact half-height.

The previous source already specified 34 mm rib tops below 38 mm teeth; an above-tip protrusion was NOT reproduced from the static profiles. This change locks the height envelope and removes lap-depth ambiguity but requires visual review in the assembled and exploded views before claiming the reported rendering artifact resolved. No live deployment performed.
