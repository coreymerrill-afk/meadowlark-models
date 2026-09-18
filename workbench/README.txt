Workbench Gen-0 — modular shop tiles (schematic)
================================================

Publish target
  https://models.meadowlarkhomecare.com/workbench/

Status
  DRAFT schematic so the program is visible. Not a finished product,
  not a cut list, not a buy package. Living catalog — not frozen forever.

IA
  /workbench/              Landing + DRAFT + trio cards
  /workbench/flat/         Primary schematic (3D)
  /workbench/extension/    Sibling schematic
  /workbench/miter/        DWS716XPS-aware (not “generic”)

Locked Gen-0 (do not invent past this)
  Module OA          36" × 36" OUTER (post / latch face)
  A-clear            ≈29" × 29"
  Posts              nominal 4×4 (~3½" × 3½" dressed)
  Top height         38" AFF (not 36; footprint OA is not height)
  Latch              magnets dock/align → mechanical for shear
                     identical faces, all 4 sides
                     primary latch 12" below finished top (≈26 AFF) — not ~18 AFF
  Ply                ½" X1-cut / non-structural · ¾" load tops/shelves
  First miter        DeWalt DWS716XPS
                     base ~27.2×22.4 fits 29 clear — tight depth
                     removable inserts for later SKUs
  Mobility           locking casters (3" class = design default, SKU OPEN)

OPEN / DRAFT — do not invent numbers
  Magnet grade/Ø · latch brand SKU · caster brand SKU
  Dual-latch count · DWS716XPS bevel swing tape · shopping/buy lists

Vision
  Mobile kit that docks around a semi-permanent X1. Distinct from the
  X1 stand itself (no X1-red) and from /insect (no magenta).

Files
  index.html                 Landing
  flat/index.html            Primary 3D
  extension/index.html       Sibling 3D
  miter/index.html           DWS716XPS 3D
  wb.css                     Shared styles
  wb-viewer.js               Shared Three.js boot
  vendor/three.min.js        Local Three.js UMD (same stack as /x1 /insect)
  vendor/OrbitControls.js    Local OrbitControls classic UMD
  README.txt                 This file

Open locally
  Serve the repo root:
    python3 -m http.server 8080
    → http://localhost:8080/workbench/

Static host
  Vercel cleanUrls + trailingSlash already cover these folders. No build step.
