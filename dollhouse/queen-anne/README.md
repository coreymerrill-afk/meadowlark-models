# Queen Anne Playhouse — v2.0.0

A separate 1:24 house. It is not Bramble Cottage and not one of the other five play-kit manors.

v1.0.0 is in `archive/v1.0.0/`. Its tower roof STL is four bodies. The cone starts about 78 mm above the seat, so that piece touches nothing in the closed view. v2 replaces that.

## Rooms

Not three identical cubes.

| Room | Where | What you see |
| --- | --- | --- |
| Parlor | Tower, ground | Lower ceiling, bay window, window seat |
| Entry | Hall, ground | Door panel and the stair |
| Living and dining | Right wing, ground | Widest room, taller ceiling, sofa, table, dining bay |
| Tower bedroom | Tower, second | Bed |
| Landing | Hall, second | Stair arrives through an opening in the floor |
| Bedroom and bath | Living, second | Bed and a tub |
| Loft | Tower, third | Only the tower continues. A table under the tower roof |

## Roofs

Each roof is one positive solid. Shingle courses are ribs in that mesh. The seat sits 0.35 mm above its own plate. A probe into the top of that plate meets the frame:

| Roof | Bearing probe |
| --- | --- |
| Tower | 1296 mm³ on the tower top frame |
| Hall | 925 mm³ on the hall top frame |
| Living | 1591 mm³ on the living top frame |
| Tower bay | 266 mm³ on the bay |
| Dining bay | 88 mm³ on the bay |

That is a geometric seat, not a strength proof. No PLA modulus and no gravity or uplift case were calculated. Side cheeks on the free ends locate a roof sideways. The roofs are not locked against a straight lift. Open mode parks them up and back so that pose is not the closed house.

Siding courses, window sills, cornice steps, brick courses, and floorboard ribs are mesh, not a texture painted on in the viewer.

## Magnets — nominal 5.0 × 2.8 mm

Round discs, 5.0 mm diameter by 2.8 mm thick. The pocket is that size plus 0.25 mm per side and 0.20 mm on the thickness. Mating skin is 1.2 mm. This is a starting allowance for a 0.4 mm nozzle. It is **not a proven fit**.

No magnet grade is assumed. Holding force is **not** calculated from the diameter.

The sill hook carries the panel. Two pocket heights on each stile, and the matching pockets in the posts, are opposing pairs of the same small disc. If the coupon feels weak, add another pair in the CAD. Do not jump to a larger magnet before that test.

There is **no H3C pause-print profile**. Nothing was sliced.

### Install

1. Check the discs are the nominal 5.0 × 2.8 mm.
2. On `qa2_polarity_fixture_v2`, set two discs in the shallow wells with the faces that should attract pointing across the raised gap. Flip one if they repel. Take them out. The fixture does not enclose them.
3. Set a disc in each open channel, mating face toward the 1.2 mm skin.
4. Slide `qa2_retainer_v2` in until the hook passes the ledge. The bar is the room-side wall. It is dovetailed. It is not glue, and it is not a cap the size of the magnet.
5. Do the frame posts before that storey is set down.
6. Seat the panel on the sill hook.
7. On the coupon (`qa2_coupon_frame_v2` and `qa2_coupon_panel_v2`, same channel cutter as the house), try a straight pull, then lift and pull. Write down the feel. It is not predicted here.

A broken bar can expose a magnet. That is a swallow hazard. This is not a child-safety certification. Retention has not been pull-tested.

## Files

Regenerate with `python3 cad/build_queen_anne_v2.py` from `dollhouse/queen-anne`.
