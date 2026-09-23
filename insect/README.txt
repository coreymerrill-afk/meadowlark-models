Biomimetics — Flyer catalog (CONTENT LOCK v1.3 + alternates v0)
==============================================================

Publish target
  https://models.meadowlarkhomecare.com/insect/
  https://models.meadowlarkhomecare.com/insect/flyer-1/
  https://models.meadowlarkhomecare.com/insect/flyer-2/

Copy source
  MODELS-PAGE-CONTENT-LOCK v1.3
  CRITIC-TWEAK-FLYER-0
  FLYER-ALTERNATES-LOCK-v0
  LEAD-ARCHETYPE-LOCK (Option A KEEP)
  MOBILE-NOTES.md (insect column from MOBILE-NOTES-INSECT-DRAFT)

Flyer-0  /insect/           LIVE — two-wing rotary motor + linkage + deliberate thorax spring
                            R = 9 cm · c = 2.3 cm · mass mid 15 g
                            Scale chip: hawkmoth-class / odonate Re band
                            Thorax spring/flexure = resonator; pitch living-hinge separate
                            Schematic motion only; Φ ~110–120° intent (no fake Hz)

Flyer-1  /insect/flyer-1/   LIVE — Dual-pair (four-wing / phaseable pairs)
                            Schematic only. Must not be Flyer-0 + decorative plates.
                            No frozen lab path; no lift number on the page.

Flyer-2  /insect/flyer-2/   LIVE — Resonant piezo (no rotary crank)
                            Schematic only. Honest HV / micro. Must not hide a crank.
                            No frozen lab path; no invented Hz.

Catalog chrome
  Flyer-0 live · Flyer-1 Dual-pair live · Flyer-2 Resonant piezo live
  Flyer-0 stays the primary /insect/ start. Alternates are live starts, not Phase-2 footnotes.

Files
  index.html                 Flyer-0
  flyer-1/index.html         Flyer-1 Dual-pair
  flyer-2/index.html         Flyer-2 Resonant piezo
  shared.css                 Catalog, tabs, mobile chrome diet
  three-stack.js             Local UMD + CDN fallback (loads /vendor)
  page-chrome.js             Tabs + hotspots + portrait FOV / touch
  ../vendor/                 Shared Three.js UMD + OrbitControls (repo root)
  README.txt                 This file

Repo
  MOBILE-NOTES.md            Insect success-criteria + chrome diet

Open locally
  python3 -m http.server 8080
  → http://localhost:8080/insect/

Static host
  Vercel cleanUrls already cover these folders. No build step.
