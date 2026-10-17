# Furniture v2 index

Seven flat-pack designs for the ACMER X1 Ultra, 18 mm ply, 4x8 sheets. All dollar figures are planning ESTIMATES / ASSUMPTIONS (not quotes). Machine time uses the unverified 100-200 mm/min feed.

| Design | W x D x H mm | Parts | Sheets | Cut path m | Cost / unit (mid) | Price low / mid / high | Gross margin at mid | Net after fees+labor at mid |
|---|---|---|---|---|---|---|---|---|
| [Modular Bookcase / Cube Shelf](bookcase/README.md) | 800 x 300 x 1600 | 11 | 1 | 32.3 | $150 | $180 / $315 / $450 | $165 (52%) | $76 |
| [Dog-Crate End Table](dog-crate/README.md) | 900 x 600 x 700 | 9 | 2 | 61.9 | $247 | $350 / $525 / $700 | $278 (53%) | $138 |
| [Entryway Shoe Bench](shoe-bench/README.md) | 1000 x 400 x 450 | 9 | 1 | 36.0 | $107 | $140 / $220 / $300 | $113 (51%) | $41 |
| [Compact Desk with Drawer](desk/README.md) | 1200 x 600 x 740 | 17 | 1 | 39.2 | $150 | $250 / $425 / $600 | $275 (65%) | $163 |
| [Retail / Market Display Shelving](retail-display/README.md) | 900 x 440 x 1500 | 9 | 2 | 31.1 | $231 | $200 / $500 / $800 | $269 (54%) | $164 |
| [Nightstand](nightstand/README.md) | 560 x 400 x 600 | 15 | 1 | 25.9 | $97 | $120 / $190 / $280 | $93 (49%) | $30 |
| [Rolling Kitchen Cart](kitchen-cart/README.md) | 600 x 450 x 900 | 29 | 1 | 50.1 | $146 | $180 / $280 / $420 | $134 (48%) | $31 |

## Files per design
`model.py` (PARAMS at top), `parts.json`, `plan.json`, `README.md`, `checks.txt`, `assembly.png`, `sheet-N.png`, `*-nest-sheetN-1220x2440.dxf` (layers CUT and LABELS), `nest.json`.

Shared code: `_lib/fp.py`, `run.py`, `gen_readme.py`.

Assumptions: Nightstand and Rolling Kitchen Cart price bands are mine (not in SHORTLIST.md). The five new designs use SHORTLIST.md bands. Dog crate is 700 mm tall rather than ~650 because a 90 mm plinth plus an 18 mm floor tray needs it for a 536 mm interior.
