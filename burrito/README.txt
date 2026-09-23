Automated Burrito Maker — Pass-3 Concept B (interactive 3D viewer)
==================================================================

Publish target
  https://models.meadowlarkhomecare.com/burrito/

Files
  index.html                 Primary static page (Three.js viewer)
  README.txt                 This file
  ../vendor/                 Shared Three.js UMD + OrbitControls (repo root)

Open locally
  1. Serve the repo root so /vendor and /burrito resolve together:
       python3 -m http.server 8080
       → http://localhost:8080/burrito/
  2. Opening index.html from disk falls back to ../vendor/, then CDN (jsDelivr → unpkg → ESM).

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
  Deploy the repo. /burrito/ serves index.html. Three.js lives in /vendor/.
  No build step required.
