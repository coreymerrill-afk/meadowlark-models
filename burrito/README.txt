Automated Burrito Maker — Pass-3 Concept B (interactive 3D viewer)
==================================================================

Publish target
  https://models.meadowlarkhomecare.com/burrito/

Files
  index.html                 Primary static page (Three.js viewer)
  Burrito-Line-Pass3.html    Same content (named alias)
  vendor/three.min.js        Local Three.js UMD (r149-class)
  vendor/OrbitControls.js    Local OrbitControls classic UMD
  README.txt                 This file

Open locally
  1. Keep index.html (or Burrito-Line-Pass3.html) beside the vendor/ folder.
  2. Double-open the HTML in a current browser (Chrome / Edge / Firefox / Safari),
     or serve the folder:
       cd /path/to/burrito-blueprints/web
       python3 -m http.server 8080
       → http://localhost:8080/
  3. If vendor/ is missing, the page falls back to CDN (jsDelivr → unpkg → ESM).
     Local vendor/ is preferred for file:// and offline use.

Controls
  Orbit: drag / one-finger
  Zoom: scroll / pinch
  Pan: right-drag / two-finger
  Click a station mesh, chip, or sidebar card to highlight & focus
  Play cycle: nest advances L→R; Station 6 lifts +2 in and jaws close/open

Locked Pass-3 geometry (Concept B)
  Module 144 in L × 34 in D · Deck 42 in AFF · Walking-beam pitch 18.0 in
  7 stations L→R: Warm/Press · P1 Griddle · P2 Egg · Rice+Beans · Cold C1–C3
                  · Soft-fold jaws · Foil+pack / heat-hold exit
  Nest boats 13×13 in solid bottom, Ø12.5 pocket
  Soft-fold HOME outside Ø13.5 keep-out; nest elevates +2.0 in at Sta.6
  RAW catch under Sta.2–3 · Trough dam Sta.3|4 · Baffle skirts at cook bays
  Operator aisle at front (−Z)

Design note
  Throughput shown in UI is a design target (~55/hr @ 1 operator) — not a
  marketing claim.

Static host (Vercel / any static)
  Deploy the contents of this web/ folder (HTML + vendor/). Root should serve
  index.html. No build step required.
