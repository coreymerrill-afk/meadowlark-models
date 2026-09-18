Biomimetics — Flyer-0 (schematic flying-insect robot)
=====================================================

Publish target
  https://models.meadowlarkhomecare.com/insect/

Files
  index.html                 Primary static page (Three.js viewer + prototype path)
  vendor/three.min.js        Local Three.js UMD (same stack as /x1 and /burrito)
  vendor/OrbitControls.js    Local OrbitControls classic UMD
  README.txt                 This file

What this is
  A conceptual schematic — body + four flapping wings — not a photoreal insect
  and not a product claim. Copy is first-principles: nature principles, mimic
  routes (actuation / materials / power), then bench milestones
  (tethered flap → controlled hover attempt → free flight).

Open locally
  1. Keep index.html beside the vendor/ folder.
  2. Serve the site root (preferred) or this folder:
       cd /path/to/meadowlark-models
       python3 -m http.server 8080
       → http://localhost:8080/insect/
  3. If vendor/ is missing, the page falls back to CDN (jsDelivr → unpkg → ESM).

Controls
  Orbit: drag / one-finger
  Zoom: scroll / pinch
  Pan: right-drag / two-finger
  Click a labeled part to highlight
  Flap loop can be paused; prefers-reduced-motion starts paused

Static host (Vercel / any static)
  Deploy the repo root. /insect/ is a folder with index.html — same as /x1
  and /burrito. vercel.json cleanUrls + trailingSlash apply; no extra rewrite
  is required. No build step.
