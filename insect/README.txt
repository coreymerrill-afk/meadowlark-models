Biomimetics — Flyer-0 v0 (two-wing hover schematic)
===================================================

Publish target
  https://models.meadowlarkhomecare.com/insect/

Locked architecture (Option A)
  Two-wing motor + linkage + elastic return + passive aeroelastic pitch
  LEV-style hover is the primary flight story
  Clap-and-fling deprioritized; four-wing dragonfly = Phase-2
  Span freeze: semi-span R = 9 cm · mean chord c = 2.3 cm · mass mid ~15 g
  Mission: hover-capable education/research, short endurance, indoor first
  Research/education/environmental flyer — not a weapon

Files
  index.html                 Primary static page (Three.js viewer + locked copy)
  vendor/three.min.js        Local Three.js UMD (same stack as /x1 and /burrito)
  vendor/OrbitControls.js    Local OrbitControls classic UMD
  README.txt                 This file

Open locally
  Serve the repo root:
    python3 -m http.server 8080
    → http://localhost:8080/insect/

Static host
  Vercel cleanUrls + trailingSlash already cover /insect. No build step.
