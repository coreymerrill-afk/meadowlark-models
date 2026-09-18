Biomimetics — Flyer catalog (Flyer-0 / Flyer-1 / Flyer-2)
=======================================================

Publish target
  https://models.meadowlarkhomecare.com/insect/
  https://models.meadowlarkhomecare.com/insect/flyer-1/
  https://models.meadowlarkhomecare.com/insect/flyer-2/

Three first-principles starts (not leftovers of each other)
  Flyer-0  /insect/           Two-wing rotary motor + deliberate spring/elastic return
                              Locked envelope: R = 9 cm · c = 2.3 cm · mass mid 15 g
                              Option A kept. Thorax spring = resonator; pitch flexure separate.
  Flyer-1  /insect/flyer-1/   Four-wing / dual-pair (independent fore + hind)
                              Distinct boom + two drives. Not decorative plates on Flyer-0.
  Flyer-2  /insect/flyer-2/   Piezo stack + resonant flexure amplifier — no rotary crank
                              Honest micro / HV / resonant story. Not a free win over crank.

Shared chrome
  Magenta/violet biomimetics accent
  Catalog switcher on every flyer page
  Same static Three.js / OrbitControls vendor stack as /x1 and /burrito

Files
  index.html                 Flyer-0 page
  flyer-1/index.html         Flyer-1 page
  flyer-2/index.html         Flyer-2 page
  shared.css                 Catalog, tabs, mobile framing
  three-stack.js             Local UMD + CDN fallback loader
  page-chrome.js             Tabs + hotspot list + Three boot
  vendor/three.min.js        Local Three.js UMD
  vendor/OrbitControls.js    Local OrbitControls classic UMD
  README.txt                 This file

Open locally
  Serve the repo root:
    python3 -m http.server 8080
    → http://localhost:8080/insect/
    → http://localhost:8080/insect/flyer-1/
    → http://localhost:8080/insect/flyer-2/

Static host
  Vercel cleanUrls + trailingSlash already cover these folders. No build step.
