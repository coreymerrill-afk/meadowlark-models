# Queen Anne detail proof

This is one window, one pierced verge board, one curved bracket, one shingle cartridge, and one furnished bay. It is not the whole house, and it is not a render of the approved picture.

The STL files in `models/` are already in assembly coordinates. Open them together and they sit in the same places as `assembly.glb`. `assembly.json` records the translation from each part's design origin. Do not apply that translation again to these STLs.

## Look at it

From this folder:

```
python3 -m http.server 8771
```

Open `http://127.0.0.1:8771/`.

Room, Window, Lace, Bracket, Shingles, and Light move the camera. Neutral draws every solid in one grey. Section cuts the view on Y = 120.2, through the window opening. Drag to orbit. Scroll to zoom.

## What is solid

Every part is one watertight body. Shared volume between parts is zero. The window wall rests on the floor. The sash sits in the opening with 0.6 mm clearance. Furniture rests on the floor. Lace, the bracket, and the shingle cartridge are on the bench beside the room.

`evidence/lace-plan.png` is a cut through the verge board. The white disks are through-holes. `evidence/window-plan.png` is a cut through the clear opening. `evidence/light-section.png` is a cut through the puck: the cavity opens downward and a 2 mm feed leaves the top. `evidence/bracket-section.png` shows the hole in the bracket.

`evidence/report.json` has bounds, volume, body count, and whether each part fits 330 × 320 × 325 mm in the orientation it was exported.

## Not claimed

No slicer was available here, so there is no toolpath. A mesh section is not a slice and not an H3C print. The drawn web between the larger lace holes is 5.4 mm. The bracket records its own rim. Neither has a coupon. The 6 × 3 mm lamp cavity is not a measured LED. Nothing in this folder was printed.
