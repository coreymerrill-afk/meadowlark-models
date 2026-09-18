Biomimetics — Flyer-0 v0 (two-wing hover schematic)
===================================================

Publish target
  https://models.meadowlarkhomecare.com/insect/

Locked architecture (Option A) — Lead 2026-09-17
  Two-wing motor + linkage + deliberate elastic return + passive aeroelastic pitch
  LEV-dominated hover is the primary flight story
  Clap-and-fling = curiosity bench; four-wing dragonfly = Phase-2
  Span freeze (public nominals): R = 9 cm · c = 2.3 cm · mass mid 15 g
  Working band ~10–20 g is background context, not the primary chip
  Mission: hover-capable education/research, short endurance, indoor / netted first
  Research/education/environmental flyer — not a weapon
  Copy source: LEAD-ARCHETYPE-LOCK + MODELS-PAGE-CONTENT-LOCK

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
