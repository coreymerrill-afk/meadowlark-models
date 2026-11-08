# V1 → V2: exact repairs

| V1 fault (geometry, not labeling) | V2 replacement |
|---|---|
| Blue feed centerline traverses waste solid for at least 88.5 mm | Clean tank/check/pump/meter/heater entirely left; no clean/waste spatial intersection in scoped checks |
| Brown drain climbs 65 mm, no drain pump | Open low point z235 → valve inlet215/out185 → coupling135 → internal stub120; monotonically descending |
| Drain begins inside unbored solid floor | Sloped annular floor terminates at an actual open 24 mm low-point bore |
| Blue feed joins second heater vertex, leaving dead leg | Feed meets first declared heater inlet, axially, with actual collar; no unintended branch |
| Pumps, tank and strainer have implicit/floating connections | Named physical ports, matching pipe axes, bored chamber interfaces, broad strainer hood and service union |
| Salt line climbs 65 mm without an auger | Salt outlet540 →515 →490 →480, gravity chute into chamber annulus |
| Exploded tanks/heater move away from stationary pipes | Plumbing remains fully assembled; only basket/carriage and removable lid move. Steam pickup is chamber-supported, not attached to moving lid |
| Basket clearance not demonstrated | Raised basket bottom470 > rim455; remains centered over chamber; fixed fill/salt/steam interfaces outside radial lift sweep |

38 endpoints pass (<0.01 mm), 31 bore tangents pass, 134 separate-circuit segment checks pass; zero sampled unrelated clean tank/waste/dry-bay collisions. Every saved view also rechecks actual endpoints against actual collar positions. Scoped geometry checks only, not a safety/manufacturing validation.

See `AUDIT-V1.md` for original coordinates; `connection-manifest.json`, `topology-checks.json`, `view-topology-checks.json`, and `CHECK-SUMMARY.json` for reproducible evidence. No v1 files overwritten; no website deployment performed.
