# Furniture v2 index

Seven flat-pack designs for the ACMER X1 Ultra, 18 mm ply, 4x8 sheets. All dollar figures are planning ESTIMATES / ASSUMPTIONS (not quotes). Machine time is an ESTIMATE from a sourced range for a 120 W diode on 18 mm ply (typical 300 mm/min effective after passes, range 120-600; see CUT-SPEED-RESEARCH.md), not measured on the machine.

| Design | W x D x H mm | Parts | Sheets | Cut path m | Machine time, diode best / typical / slow case (h) | Commercial CO2 (h) | Cost / unit (mid) | Price low / mid / high | Gross margin at mid | Net after fees+labor at mid | Gross margin per machine hour (typical) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Modular Bookcase / Cube Shelf](bookcase/README.md) | 800 x 300 x 1600 | 11 | 1 | 32.3 | 1.2 / 2.2 / 4.9 | 1.0 | $148 | $180 / $315 / $450 | $167 (53%) | $78 | $77 |
| [Dog-Crate End Table](dog-crate/README.md) | 900 x 600 x 700 | 9 | 2 | 61.9 | 2.3 / 4.1 / 9.3 | 1.9 | $242 | $350 / $525 / $700 | $283 (54%) | $143 | $69 |
| [Entryway Shoe Bench](shoe-bench/README.md) | 1000 x 400 x 450 | 9 | 1 | 36.0 | 1.3 / 2.4 / 5.4 | 1.1 | $104 | $140 / $220 / $300 | $116 (53%) | $44 | $49 |
| [Compact Desk with Drawer](desk/README.md) | 1200 x 600 x 740 | 17 | 1 | 39.2 | 1.4 / 2.5 / 5.8 | 1.2 | $147 | $250 / $425 / $600 | $278 (66%) | $166 | $109 |
| [Retail / Market Display Shelving](retail-display/README.md) | 900 x 440 x 1500 | 9 | 2 | 31.1 | 1.4 / 2.3 / 4.9 | 1.0 | $229 | $200 / $500 / $800 | $271 (54%) | $166 | $117 |
| [Nightstand](nightstand/README.md) | 560 x 400 x 600 | 15 | 1 | 25.9 | 1.0 / 1.8 / 4.0 | 0.8 | $95 | $120 / $190 / $280 | $95 (50%) | $32 | $53 |
| [Rolling Kitchen Cart](kitchen-cart/README.md) | 600 x 450 x 900 | 29 | 1 | 50.1 | 1.7 / 3.2 / 7.5 | 1.5 | $142 | $180 / $280 / $420 | $138 (49%) | $35 | $43 |

## Files per design
`model.py` (PARAMS at top), `parts.json`, `plan.json`, `README.md`, `checks.txt`, `assembly.png`, `sheet-N.png`, `*-nest-sheetN-1220x2440.dxf` (layers CUT and LABELS), `nest.json`.

`parts.json` carries outlines AND hole rings (see PARTS-SCHEMA.md). `check_parts_json.py` re-checks tab/slot consistency from parts.json alone. Cut-time research and sourced rates: CUT-SPEED-RESEARCH.md.

Shared code: `_lib/fp.py`, `run.py`, `gen_readme.py`, `check_parts_json.py`.

Assumptions: Nightstand and Rolling Kitchen Cart price bands are mine (not in SHORTLIST.md). The five new designs use SHORTLIST.md bands. Dog crate is 700 mm tall rather than ~650 because a 90 mm plinth plus an 18 mm floor tray needs it for a 536 mm interior.
