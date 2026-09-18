Workbench Gen-0 — modular shop tiles (schematic)
================================================

Publish target
  https://models.meadowlarkhomecare.com/workbench/

Status
  DRAFT schematic so the program is visible. Not a finished product,
  not a cut list, not a buy package.

Locked Gen-0 (do not invent past this)
  Module OA          36" × 36" (outer post / latch face)
  Posts              nominal 4×4 (3½" × 3½" dressed)
  Clear between      ≈29"
  Top height         38" AFF
  Latch              magnets dock/align → mechanical for shear
                     identical faces, all 4 sides
                     12" below top (≈26 AFF)
  Ply                ½" default plates / ¾" load tops (note only)
  First trio         Flat (primary) · Extension · Miter (DWS716XPS)
  Mobility           locking casters (3" class = design default, SKU open)

Vision
  Mobile kit that docks around a semi-permanent X1. Distinct from the
  X1 stand itself (no X1-red) and from /insect (no magenta).

Files
  index.html                 Primary static page (Three.js viewer + copy)
  vendor/three.min.js        Local Three.js UMD (same stack as /x1 /insect)
  vendor/OrbitControls.js    Local OrbitControls classic UMD
  README.txt                 This file

Open locally
  Serve the repo root:
    python3 -m http.server 8080
    → http://localhost:8080/workbench/

Static host
  Vercel cleanUrls + trailingSlash already cover /workbench. No build step.
