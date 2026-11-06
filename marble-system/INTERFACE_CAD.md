# v2 CAD interface notes (0.3-full48)

See `README.md` for the kit-facing description. This file records the geometry
locks used by the generators.

- Tile pitch 304.8 × 228.6 mm, assembled 609.6 × 457.2 mm.
- Wells: global origin 20.0, pitch 40.0, well 22.4 mm square,
  depth 10.0, omitted if they intersect seams at x=304.8 /
  y=228.6, outer edges (keep 14.0 mm) or joiner bands (keep
  12.0 mm). Count 117.
- SOCKET_TO_V = 11.0, SOCKET_TO_RAIL = 35.7487.
- SLIDE = 20.0, SLIDE_45 = 32.0, TONGUE = 10.0,
  TONGUE_CLR = 0.4, WATERFALL = 0.5.
- Classes: {'short': {'Ls': 50.0, 'Lpost': 60.0, 'Omin': 20.0, 'Hmin': 70.0, 'Hmax': 100.0, 'qty': 8}, 'medium': {'Ls': 80.0, 'Lpost': 90.0, 'Omin': 25.0, 'Hmin': 100.0, 'Hmax': 155.0, 'qty': 10}, 'tall': {'Ls': 125.0, 'Lpost': 135.0, 'Omin': 40.0, 'Hmin': 145.0, 'Hmax': 230.0, 'qty': 6}}
- BOM48 sum 48; extras {'switch_gate': 1, 'low_mount': 6, 'lift_mount_plate': 1}.

Sample support XY from CAD 0.2 — (60,60), (140,60), (260,140), (260,180) —
remain valid wells on tile_00 after the tile size reverted from 320×240 to
304.8×228.6.
