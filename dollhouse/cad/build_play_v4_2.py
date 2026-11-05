"""Play kit v4.2 — Structure + Print Fit musts.
 1. roof_panel_lift_v4: pegs on exact grid (x=OFF+n*PITCH, y=10 / 10+2*PITCH); ridge rib carries Ø6.3x5.5 mating sockets
 2. garden_gate_play_v4: pier peg span = 4*PITCH = 127 (W=145); degenerate tris cleaned
 3. corner_post_v0 + wired_corner_post_v1w: top Ø6.3x5.5 socket so upper_floor_tile_v1 stacks via dowel_pin_v0
 4. wall_panel_clear_window_v4 / wall_panel_wide_door_v4 exported via W0.to_print (inverted, no supports)"""
import os, numpy as np, trimesh as T
import build_play_v4_1 as P
from build_v0 import bx, cyl, U, D_, OUT, SOCK_D, OFF, PITCH, S
import build_wall_v0 as W0, build_corner_post_v0 as CP, build_kit_v1 as K
SD=5.5
def roof_panel_lift(L=S*2, depth=80, thick=3.5):
    panel=bx(0,0,0,L,depth,thick); y0=10.0; y1=y0+2*PITCH  # 73.5
    rib=bx(0,depth/2-4,thick,L,depth/2+4,thick+7)
    lip=bx(0,0,thick,L,4,thick+3)
    xs=[OFF+n*PITCH for n in (0,4,7)]  # 15.875, 142.875, 238.125 — all on grid
    pegs=[P.peg(x,y) for x in xs for y in (y0,y1)]
    m=U([panel,rib,lip]+pegs)
    socks=[cyl(SOCK_D,SD+0.01,x,depth/2,thick+7-SD) for x in xs]  # ridge-cap / finial mates
    return P.lift(D_(m,socks))
def garden_gate_play():
    W,pw,h=145.0,18.0,75.0; parts=[]
    for x in (0,W-pw):
        parts+=[bx(x,0,0,x+pw,18,h),bx(x-1,-1,0,x+pw+1,19,6),P.peg(x+pw/2,9),bx(x-2,-2,h,x+pw+2,20,h+6)]
    parts.append(bx(-2,2,h-2,W+2,16,h+8))
    gw=(W-2*pw-4)/2
    for k in range(2):
        x0=pw+2+k*(gw+2)
        parts+=[bx(x0,5,8,x0+gw,13,14),bx(x0,5,h-18,x0+gw,13,h-4),bx(x0,5,8,x0+4,13,h-4),
                bx(x0+gw-4,5,8,x0+gw,13,h-4),bx(x0,5,h/2-2,x0+gw,13,h/2+2)]
    parts.append(bx(W/2-4,3,h/2-3,W/2+4,14,h/2+3))
    m=P.lift(U(parts)); m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices(); return m
def top_sock(p): return D_(p,[cyl(SOCK_D,SD+0.01,OFF,OFF,W0.HT-SD)])
PARTS={'roof_panel_lift_v4':roof_panel_lift,'garden_gate_play_v4':garden_gate_play,
 'corner_post_v0':lambda:top_sock(CP.corner_post()),'wired_corner_post_v1w':lambda:top_sock(K.wired_corner_post()),
 'wall_panel_clear_window_v4':lambda:W0.to_print(P.wall_clear_window()),'wall_panel_wide_door_v4':lambda:W0.to_print(P.wall_wide_door())}
if __name__=='__main__':
    for n,f in PARTS.items():
        m=f(); m.export(os.path.join(OUT,n+'.stl'))
        print(n,'wt',m.is_watertight,'ext',np.round(m.extents,2),'vol',round(m.volume/1000,2),'degen',int((m.area_faces<1e-9).sum()))
