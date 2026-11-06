# Marble System v2 — Research & Interface Definition (draft, locked for CAD)

**When:** 2026-11-05, America/Denver  
**Workdir:** `/workspace/marble-system-v2` (standalone; v1 at `/workspace/marble-factory` is untouched)  
**Companion:** `interface_v2.json`, `figures/interface_diagram.png`  
**Scope:** engineering interface only. No 48-piece CAD in this pass. Not a certified toy. No service-life claim.

This note locks a coherent joint/grid/height/ball-socket contract so the next CAD phase can build parts against one geometry. Physical rolling, snap durability, and creep are **untested**.

---

## 1. What we inherited, and what we are not repeating

v1 proved a paddle-wheel lift plus V-track geometry around a **35 mm** printed ball (`RB = 17.5`, V-floor 45°, `VH = RB√2 ≈ 24.75`, computational 7.13° slope = 20 mm / 160 mm). Its failure mode as a *reconfigurable* toy was architectural: joints *were* the stands (half-pegs sharing a socket), heights were one-off printed posts, and the default loop could not absorb layout changes.

v2 separates three contracts:

1. **Tile ↔ support** (dense sockets, reusable)
2. **Support height** (indexed, lock above the tile, kid-operable)
3. **Track ↔ track** (alignment + anti-step) and **track ↔ support** (ball socket that aims without unlocking the post)

The v1 lift remains the lifting mechanism. Two of the 48 track pieces are adapters into/out of that lift. Do not silently resize the ball.

---

## 2. Research (authoritative first, then FDM and toy precedent)

### 2.1 Snap-fit manuals (primary)

**Covestro / formerly Bayer, *Snap-Fit Joints for Plastics: A Design Guide***  
https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1557218421.pdf

- After assembly, “the snap-fit features should return to a **stress-free condition**.” Separable vs permanent is set by undercut *shape* (lead angle vs return angle), not by leaving the beam bent.
- Cantilever: taper thickness to **h/2** at the hook (~60% more allowable deflection than a constant section); fillet the root (they warn R/h ≈ 0.6 is optically nice but makes a thick blob; never use a sharp corner; radius not below 0.015 in / 0.38 mm).
- For **frequent** assemble/disassemble, use about **60%** of the single-join allowable strain (their Table 2 examples: unreinforced PC 4% single-join → 2.4% repeated; PC/ABS 2.5% → 1.5%).
- Annular snaps (the right model for a ball/bead in a socket): small undercuts give strong joints; permissible undercut `y ≈ ε · d` if one part is rigid, roughly **2y** if both parts share the strain. Return angle sets extraction force. Manual assembly of a ball is easier than the calculated coaxial mating force because the bead enters at an angle.

**BASF, *Snap-Fit Design Manual***  
https://productdesignonline.com/wp-content/uploads/2019/08/Snap-Fit-Design-Manual.pdf  
(also circulated as https://www.gapimprove.org/_files/ugd/cd8b34_646f9ecfe9874f9688a50b6967aab3ce.pdf)  
Calculator: https://ultrasimweb.basf.com/snapfit/

Three recurring failure modes: **stress concentration** (fillet `R/t ≥ 0.5`), **creep/relaxation**, **fatigue**. A constantly loaded beam loses pretension; do not design a clamp whose holding force *is* bending strain in plastic.

### 2.2 Additive / FDM specifics

**Klahn, Singer, Meboldt, “Design Guidelines for Additive Manufactured Snap-Fit Joints,” *Procedia CIRP* 50 (2016)**  
https://doi.org/10.1016/j.procir.2016.04.130  
Joined snaps should be “usually load free or have only small displacement… stressed plastics tend to creep and will lose any pretension over time.”

**Protolabs Network / Hubs, “How do you design snap-fit joints for 3D printing?”**  
https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/

- Prefer ductile materials (they list ABS, **PETG**, nylon); PLA and brittle resins are poorer cyclic choices.
- Nominal FDM snap clearance starting point **0.5 mm** (conservative; tune with coupons). Fillet ≥ 0.5 × root thickness, cantilever width ≥ **5 mm**, taper the beam, add locating **lugs** so clips are not also the alignment features.
- Print so the beam bends **in the layer plane**, not across layers.
- “Constant loading causes creep… The snap-fit cantilever is deflected only during assembly, not while components are engaged.”
- They explicitly refuse a universal cycle-life number.

**Bozkurt, “Short-term Creep Behaviour of Different Polymers Used in Additive Manufacturing,” *Strojniški vestnik* (2022)**  
https://doi.org/10.5545/sv-jme.2022.191  
FDM PLA showed **low creep strength** even in short tests; authors conclude PLA is suitable at room temperature and only **very low constant loads**. Nylon deformed more (compliant) but did not rupture under the same protocol.

**ASTM D2990** (tensile / compressive / flexural creep of plastics)  
https://www.astm.org/d2990-17r25.html  
is the recognized measurement method. We have not run it. Do not publish a year-of-play rating.

**Bambu Lab filament TDS V3.0** (printer-relevant, not snap-fit allowables):

- PLA Basic: https://apple-tree.co.jp/wp/wp-content/themes/appletree/uploads/bambulab/datasheet/Bambu_PLA_Basic_TDS_EN.pdf  
  XY / Z tensile 35±4 / 31±3 MPa; breaking elongation 12.2±1.8% / **7.5±1.3%**; HDT 54–57 °C; Tg 60 °C. Specimens were annealed; real toy parts will not be.
- PETG Basic TDS V3.0 (listed values from the published sheet):  
  https://store.bblcdn.com/s1/default/cb94589bf7994fdcbfa833badefae9cd/Bambu_PETG_Basic_Technical_Data_Sheet.pdf  
  XY / Z tensile about 51±1 / 35±6 MPa; breaking elongation about 9.5±0.7% / 5.2±1.4%.  
  Elongation-at-break is **not** allowable snap strain (Covestro uses a fraction of *yield* strain). PLA’s higher break-strain number does not make it the better cyclic clip — it fails more brittlely, especially across layers.

### 2.3 Toy precedents (usability, not proof)

**Ravensburger GraviTrax FAQ** — https://ravensburger-en.mindtouch.us/Product_Information/Ravensburger/GraviTrax%C2%AE/FAQ_for_GraviTrax%C2%AE  

- Aimed at about age 8+ (our 10-year-old niece/nephew fits the same band).
- Height is **discrete stacked tiles** (community: 10 mm standard, 5 mm half-height) and PRO columns equal a fixed number of tiles — not a friction slider.
- Official FAQ: a **Loop** needs enough approach speed; it is not a flat circle that works by hope.
- Marbles are a specified size (community measurement 12.7 mm). Our 35 mm ball is a deliberate scale-up of v1, not a GraviTrax clone.
- Community reports that tall stacked pillars get wobbly — slim height must be reacted at the foot and by the track acting as a frame.

Wooden-train peg track (BRIO-style) and Hot Wheels hook connectors show kids this age understand “push until it clicks / squeeze to release.” They also show friction-only pegs loosen with wear — another reason to use a positive detent plus replaceable clips rather than “print tighter.”

No compatibility with those brands is intended.

---

## 3. The friction / adjustability paradox

A joint that slides freely enough for a 10-year-old will also creep or slip under gravity if holding depends on **friction or bent-plastic preload**. The manuals above say the same thing in two ways: (1) snaps should unload after they click; (2) creep relaxes any leftover clamp force (ASTM D2990 is how one would measure that, later).

So height and track pose are split into different DOF:

| DOF | Must be | How |
|-----|---------|-----|
| Support height | Discrete, positive, unloaded after click | 5 mm rack + replaceable pawl clip |
| Support location XY | Discrete, positive | Square sleeve in a tile socket, flanged foot |
| Track heading / slope | Set by the module geometry + height indices at each end | Module drop is a multiple of 5 mm |
| Track pitch & small yaw | Free enough to hit a nearby socket and match slope | Ø16 mm ball, ±15° cone |
| Track roll (twist) | Locked | Key / keel on the ball cap; track-to-track joints take the rest |
| Track continuity | Positive, no uphill lip | Tongue + lugs + dual hooks, 0.5 mm downhill “waterfall” |
| Release | Tool-free, obvious, not a fingernail pry | Squeeze two large tabs, or lift the height clip |

“Move freely without affecting the structure” is read as: snapping a track onto the ball must **not** unlock height or yank the sleeve out of the tile. Extraction hierarchy (to be coupon-tested, not claimed):  
`F_ball_release < F_height_lock < F_sleeve_extraction`, with a wide gap between them.

---

## 4. Evaluation of the square-channel idea (kept, then strengthened)

The proposed picture — a square outer structure that plants in the base, an inner slider that carries the track, unlocked **above** the tile, snapped shut to hold height — is the right *architecture*. It is kid-legible, keeps the lock where fingers can reach it, and avoids pulling the whole post out of the floor to change height.

What does **not** survive the research as the primary lock is a **friction clamp** (a channel lid squeezed against a smooth slider):

- Holding force is leftover bending strain → creep (Covestro unload rule; BASF / CIRP 2016; Bozkurt PLA creep).
- The clamp sits at the *bottom* of a slim 200 mm post, so kid-bumps and corner momentum are large moments on a small contact.
- Putting a hinged “snap-shut channel” on every dense socket (96 of them) would multiply living hinges. PLA living hinges are a known fatigue item; most sockets are empty anyway.

**Chosen evolution (same mental model, different lock physics):**

1. Empty tile sockets are just keyed square wells plus a seat — no lid per hole.
2. Each of the 24 supports is a short **outer square sleeve** that drops into a well and takes moment through a flange and ≥14 mm embedment.
3. An **inner square post** slides in the sleeve. One face is a 5 mm index rack (radiused slots, not sharp saw-teeth).
4. A **replaceable PETG lock clip** (cantilever pawl, width ≥ 8 mm, tapered, filleted, printed lying down) engages one slot. Operated above the tile. After the click, the pawl sits *in* the slot, nearly unloaded — the slot face, not friction, carries the weight.
5. Optional light closing of the sleeve (a second, larger over-center latch) only takes rattle, and is designed so it can relax without dropping the post.

Wear parts are the clip and the ball cap, not the tile and not a 200 mm post (though a worn post is still a cheap reprint). No tiny magnets. No captive metal screws required; if a later test wants hardware, it would be a large tool-free quarter-turn, not a #2 screw.

---

## 5. Locked interface decisions

### 5.1 Ball — keep 35 mm

No reason to change. v1 lift pockets, V-floor, and computational 7.13° slope are built around `RB = 17.5`. 35 mm is above the common 31.7 mm small-parts cylinder, which is a *gauge* not a certification (ASTM F963 / ISO 8124 are cited only as awareness; this kit is **not** certified). Smaller “real marbles” (~16 mm) would orphan the lift and make parts fiddlier for a 10-year-old.

### 5.2 Base, tiles, grid

- Assembled coverage: **18 × 24 in = 457.2 × 609.6 mm**, 2×2 tiles.
- Tile **pitch:** 228.6 × 304.8 mm (9 × 12 in).
- **Print orientation:** 304.8 mm along the H3C 330 axis (25.2 mm spare before joiners); 228.6 mm along the 320 axis (91.4 mm spare). User’s “narrow 320 margin” is avoided by not placing the 12 in side on the 320 axis. Male dovetails live inside a printable bbox ≤ **328 × 316 × 16 mm** (includes joiners).
- Tile thickness 12 mm (v1).
- Tile joints: males on +X/+Y, females on −X/−Y, plus **two large PETG slide latches per seam** (4 seams → 8 latches). Positive, reusable, no living hinge.
- Socket pitch **50.8 mm (2 in)**. Per tile: 6 along the 12 in side × 4 along the 9 in side = **24 sockets/tile**, **96 sockets** on the assembled base. The 9 in tile seam skips one pitch (76.2 mm alley) so no socket is cut by a joint; the 12 in seam stays on-pitch.
- Socket: 18 mm square well (inner slider is 16 mm square; sleeve occupies the well), keyed so the sleeve can only seat one way; flange sits on the tile to take moment. Opening size is a finger-trap topic for physical review (not certified).

96 sites / 24 posts ≈ 4:1 relocation density. At low post heights a ±15° ball only reaches ~10–15 mm sideways, so low tracks should sit nearly over a socket; mid/high posts can lean toward a neighbor.

### 5.3 Support (24 structures)

Each structure is **4 printed parts**:

| Part | Role | Material (proposed) |
|------|------|---------------------|
| Outer sleeve + flange | Seats in tile, carries moment, houses clip | PLA or PETG |
| Inner post, 16 mm square, rack on one face | Height slider | PLA or PETG |
| Lock clip (wear) | Positive 5 mm index | **PETG**, printed flat |
| Ø16 mm ball cap (wear) | Articulating support, anti-roll key | **PETG** |

- Height law: `H_ball_center = 50 + n·5` mm above tile top, `n = 0…36` (50–230 mm). 37 clicks. Inner travel 180 mm; standing print of the post is inside 325 mm Z.
- Max recommended unsupported track span: **160 mm**. The 240 mm span piece requires a mid-span support. Helix: supports at entry and exit (optional third if a socket lines up).
- Lateral stiffness (order-of-magnitude only, not a test): a 16 mm square PLA post, E ≈ 2.3 GPa from the Bambu XY modulus neighborhood, as a 220 mm cantilever, deflects on the order of 0.5 mm under 2 N and a few mm under a 10 N bump. The track chain must share load. This is why track joints are structural, not decorative.

24 × 4 = **96 support parts**, plus a spare pack of **8 clips + 8 ball caps**.

### 5.4 Ball joint

- Ball on the **replaceable cap** (post side); socket on the track underside. Worn spheres are cheap.
- Diameter **16 mm**. Repeated-use annular undercut budget from Covestro: ε ≈ 1.5–2% → `y ≈ 0.25–0.3 mm` if the socket is the only spring, up to ~0.5–0.6 mm if both sides flex. Lead ~30°, return ~35–40° (separable, intentional pull).
- Articulation: **±15° pitch and yaw**. At H = 150 mm that is ~40 mm of sideslip — enough to favor a neighboring 50.8 mm cell at mid/high settings.
- **Roll locked** by a keel/pin on the cap in an along-track slot (allows pitch; limited yaw; stops dump-the-V twist).
- Long modules (S160, S240, tunnel, helix) get two underside sockets whose spacing is a grid multiple (S160: **152.4 mm** = 3 cells). Short modules and 90° corners get one socket near mid-length; they depend on neighbors + the keel for roll.

### 5.5 Track joints (the actual “snap-in juncture”)

v1 half-pegs go away; tracks join **each other**.

- Male tongue continues the V-floor into a female sleeve.
- Two side lugs take shear (Hubs: do not make the flexure do alignment).
- Two large PETG hooks (width ≥ 8 mm, tapered, filleted, in-layer flex) with accessible squeeze tabs.
- **Anti-step:** downstream floor is **0.5 mm lower** than upstream (“waterfall”) so wear cannot create an uphill lip. Target step after print: 0.0 to −0.8 mm (never uphill).
- Release: squeeze both tabs, pull apart along the tangent. No pry tools.

### 5.6 Slope family (so discrete height can close)

Increment **5 mm** was chosen so v1’s proven **R = 80 mm** 90° corner (arc 125.66 mm) drops **15 mm** (3 clicks) at 6.80°, next to the v1 straight’s **20 mm / 160 mm = 7.13°**. An 8 mm increment cannot hit both.

| Module | Plan geometry | Locked drop | Implied slope |
|--------|---------------|------------:|---------------|
| S160 | 160 mm straight | 20 mm (4) | 7.13° |
| S80 | 80 mm straight | 10 mm (2) | 7.13° |
| S40 | 40 mm straight | 5 mm (1) | 7.13° |
| CR90 / CL90 | 90°, Rc = 80 mm | 15 mm (3) | 6.80° |
| CR45 / CL45 | 45°, Rc = 80 mm | 10 mm (2) | 9.04° (steeper; 5 mm / 4.55° is a pending stall test, not default) |
| SPAN240 | 240 mm straight | 30 mm (6) | 7.13° (needs mid support) |
| TUN160 | covered S160 | 20 mm (4) | 7.13° |
| HX360 | descending helix, Rc = 90 mm, path 565.5 mm | 80 mm (16) | 7.26° |
| SPLIT_Y outlet A | through path ~160 mm | 20 mm | ~7.1° |
| SPLIT_Y outlet B | same run + cascade | 35 mm (7) | extra 15 mm well |
| MERGE_Y | accepts Δh ≤ 5 mm | 15 mm out | inlets may use a funnel if off by more |
| FUNNEL | collector | 20 mm | energy + height dump |
| DROP40 | open fall into catch | 40 mm | not a rolling slope |
| SWITCH | gated split | same as SPLIT_Y | |
| ADAPT_OUT / ADAPT_IN | v1 lift interfaces | documented in JSON; match v1 7° chute / ~8° inlet |

A **horizontal loop cannot be a flat frictionless circle**. HX360 is a descending helix with an 80 mm pitch. A 70 mm-deep v1-style skirt would self-intersect at that pitch, so the helix uses a **slim open V** (section height ≤ 40 mm) giving ~40 mm vertical clearance. Footprint ≈ 256 mm dia (Rc 90 + ~38 mm half-width) — printable on the H3C 320 axis.

Branching arithmetic: one SPLIT consumes one stream and emits two. A single lift can reabsorb one stream. Practical simultaneous circuit: **at most one live split–merge pair** (or a split into a catch-basin plus a main return). Two supplied splits do not mean two independent loops back to one lift.

---

## 6. 48-piece track BOM (supplied inventory)

These 48 are **kit contents**, not a single sculpture that places every piece at once.

| ID | Qty | Role |
|----|----:|------|
| S160 | 8 | main run |
| S80 | 6 | length trim |
| S40 | 4 | fine trim |
| CR90 | 5 | right 90 |
| CL90 | 5 | left 90 |
| CR45 | 2 | grid aiming |
| CL45 | 2 | grid aiming |
| SPLIT_Y | 2 | branch (needs downstream inventory) |
| MERGE_Y | 2 | rejoin |
| FUNNEL | 2 | collect / after a drop |
| HX360 | 2 | descending “horizontal loop” |
| DROP40 | 2 | cascade |
| SPAN240 | 2 | long run + mid support |
| TUN160 | 1 | covered S160 |
| SWITCH | 1 | gated split |
| ADAPT_OUT | 1 | v1 lift chute → new male/female |
| ADAPT_IN | 1 | new joint → v1-style inlet |

**48 total.**

### Example routes that close on paper (not physically rolled)

**Route A — simple lift return** (11 track pieces + adapters):  
`ADAPT_OUT + S160 + CR90 + S160 + CR90 + S160 + S80 + CR90 + S160 + ADAPT_IN`  
Drops: 20+15+20+15+20+10+15+20 = **135 mm** plus the two adapters (~15–25 mm combined, v1-like). Inside the v1 lift’s ~150–180 mm raise budget.

**Route B — one split and merge** (adds SPLIT_Y, extra S80/corners on each leg, MERGE_Y, FUNNEL). The longer-plan leg must pick a smaller drop-per-length or the shorter leg must take DROP40 / the B-cascade so both inlets hit the merge within **5 mm**.

**Route C — helix feature:** HX360 spends **80 mm** of the ~160–200 mm budget. Remaining approach + return must still be downhill; you cannot add a second helix and still climb back into the same lift without going negative on budget.

Do not claim that an arbitrary 48-piece layout closes.

---

## 7. Other printed parts (not in the 48)

- Base: 4 tiles + 8 seam latches.
- Supports: 24 × (sleeve, post, clip, ball cap) = 96, plus 8 spare clips and 8 spare ball caps.
- Optional later: extra junction repair clips (not required to start CAD).
- v1 lift parts stay in the v1 kit; v2 only adds the two adapters among the 48.

---

## 8. Materials, print, tolerances (starting matrix — tune on coupons)

| Class | First print | Why |
|-------|-------------|-----|
| Tiles, inner posts, track *bodies* | PLA OK | Stiff, colorful, easy on H3C; low constant load if height is indexed |
| Lock clips, ball caps, tile latches, track hooks if separate | **PETG** | Cyclic flex / impact; Hubs recommendation vs PLA |
| Nylon | Not default | Best fatigue in literature, moisture + dimensional hassle for a kid-color kit |

Starting clearances (one-sided unless noted), from Hubs 0.5 mm FDM snap starting point plus tighter sliding fits to be couponed:

| Pair | Start | Intent |
|------|------:|--------|
| Sleeve in tile well | 0.25 mm/side | Firm plant, removable |
| Inner post in sleeve | 0.20 mm/side | Sliding, not sloppy |
| Rack slot vs pawl | 0.15–0.25 mm vertical backlash target | Positive seat |
| Ball vs socket diametral | 0.3–0.5 mm + 0.4–0.6 mm lip undercut | Click, intentional pull-off |
| Track tongue | 0.20 mm/side | Alignment from lugs, not from hooks |
| Waterfall | 0.50 mm downstream down | Anti-step |

Build rules from the manuals: taper snaps, fillet ≥ 0.5 t, width ≥ 5 mm (we use ≥ 8 mm), bend in-layer, locate with lugs.

---

## 9. Coupons the next phase should print *before* the full 48

1. **Snap strain ladder** — PETG vs PLA cantilevers, undercuts 0.4 / 0.6 / 0.8 mm, widths 8 and 12 mm, print flat vs upright (expect upright to die early).
2. **Height lock** — 20 cycle engage/disengage, then 5 N downward for 24–72 h; compare to a friction-clamp control. Pass = no dropped index.
3. **Ball socket** — insertion / extraction force, ±15° sweep, 50 cycles, then pull-off vs a locked post (hierarchy check).
4. **Track joint step** — paint or feeler-gauge the V floor; reject any uphill lip.
5. **Post bump** — full-height post, 2 N and 10 N lateral at the ball; measure tip deflection and whether the sleeve stays seated.
6. **Tolerance ladder** — pins/holes 0.15–0.50 mm on the actual H3C profile (generic slicer numbers are not H3C numbers).
7. **Slope rolling** (physical, currently **untested**): 35 mm printed ball on S160 at 15 mm (5.36°), 20 mm (7.13°), and the 6.80° corner. This is the gate for keeping 5 mm clicks.
8. **Helix clearance** — section + 80 mm pitch does not collide; ball stays in the slim V.

No cycle count from these coupons will be marketed as a lifetime.

---

## 10. Safety (awareness only)

Not certified to ASTM F963 or ISO 8124. Pinch remains at the v1 lift wheel. 16–18 mm square wells may admit fingers. Ball caps and clips must be large enough not to be mouth-sized. Adult supervision, age ~10, no claim otherwise.

---

## 11. Explicit tradeoffs

- Discrete 5 mm height vs continuously sliding: we gave up infinitely fine posing to get a lock that does not rely on creep-prone friction. Small gradations are still “one click.”
- 50.8 mm grid vs 38.1 mm: denser grid would help low-height aiming but opens ~33% of each tile as holes and weakens the plate. 96 sockets is the compromise.
- Free ball vs keyed ball: a fully free ball would let the V twist and dump the marble, and would sag under load. Keyed ±15° matches “snap in and aim” without “collapse the route.”
- Helix pitch 80 mm vs a tighter visual loop: a 60 mm pitch at v1’s 70 mm section would self-intersect. Slim section + 80 mm drop is the physical constraint.
- Integral large track hooks vs fully separate clips: integral is easier for a 10-year-old; wear then asks for a reprint or a later repair-clip overlay. Lock clip and ball cap *are* separate because they will be the first to wear.
- PETG for flexures, PLA allowed for stiff geometry: matches bureau guidance and the Bambu machine the family already has. Nylon is reserved if coupons show PETG clips dying early.
- 45° corners at 9.04°: slightly faster than the 7.13° family so the drop stays on the 5 mm lattice with R = 80. Slow 4.55° alternative is not default until a ball actually rolls it.

---

## 12. Unresolved items (physical tests only — interface can proceed)

1. Real rolling friction of a printed 35 mm ball in a printed V at 6.8–7.3° (and whether 5.36° ever works).
2. Insertion / extraction force window that a ~10-year-old can operate but gravity and a rolling ball cannot.
3. Clip fatigue life in PETG (and whether PLA clips survive even 50 cycles). No number until couponed.
4. 24–72 h creep of the chosen detent vs a friction-clamp control under a representative track + ball load.
5. Tile warp on a 304.8 × 228.6 mm plate with 24 wells, printed on the official H3C profile (v1 used a generic slicer).
6. Finger-trap and pinch review of the wells, ball, and lift — qualitative, not a lab cert.
7. Whether 45° / 10 mm (9.04°) throws balls out of an unbanked V.
8. Helix entry speed: descending helix should not need a “loop-the-loop” boost, but that is an assumption.
9. Exact `socket_to_rail_z` offset (JSON uses a 22 mm placeholder) once the track underside is modeled.
10. ADAPT_OUT / ADAPT_IN solid mating to the *existing* v1 chute keel and inlet — measure v1 parts, do not restyle the lift.

The parent CAD phase can start against `interface_v2.json` now.
