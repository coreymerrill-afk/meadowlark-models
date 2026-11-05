"""Dollhouse kit v1 (1:24, H3C): multi-story + Wired-5 parts + accessories. Units mm, Z=0 bed.
Reuses build_v0 helpers. Accessories are blocky intentional 1:24 silhouettes with Ø6 snap pegs where they sit on tiles."""
import os, numpy as np, trimesh as T
from build_v0 import bx, cyl, U, D_, OUT, LC, SOCK_D, OFF, PITCH, S, floor_tile
import build_wall_v0 as W0, build_corner_post_v0 as CP
WC=5.0   # Wired-5 main channel Ø (fits 4x 30AWG silicone or 2-pair 28AWG)
MAG_D, MAG_H = 6.2, 2.2  # pocket for Ø6x2 N52 disc magnet (press/CA)
def peg(x,y,z=0): return cyl(5.9,5.0,x,y,z-5.0)  # Ø5.9 peg below base (into Ø6.3 socket)
def lift(m): m.apply_translation([0,0,-m.bounds[0][2]]); return m
# ---------- structure ----------
def upper_floor_tile():
    """Floor tile for story 2: same top grid, plus 4 Ø6.3 underside sockets at corners that take dowels from corner posts/wall tops."""
    t=floor_tile(); cuts=[cyl(SOCK_D,5.5,x,y,-0.01) for x in (OFF,S-OFF) for y in (OFF,S-OFF)]
    return D_(t,cuts)
def stair_module():
    """Straight stair, 12 risers x 9.17 to rise 110 (wall 101.6 + upper tile 10 -> lands on deck); tread 9.5 (≈9 in), width 38 (3 ft)."""
    n=12; rise=(W0.HT+10)/n; run=9.5; w=38.0
    m=U([bx(i*run,0,0,(i+1)*run,w,(i+1)*rise) for i in range(n)]+[peg(OFF-OFF+15.875,15.875)])
    return m
def wired_floor_tile():
    """Floor tile with deeper Ø5 cross channels at z=3 along both centrelines + Ø5 risers at 4 corners; joins v0 Ø3.2 race."""
    t=floor_tile(); c=S/2
    cuts=[cyl(WC,S+1,c,c,3.0,'x'),cyl(WC,S+1,c,c,3.0,'y'),cyl(WC,11,c,c,-0.5)]  # centre ceiling-feed riser
    cuts+=[cyl(WC,11,x,y,-0.5) for x in (5,S-5) for y in (5,S-5)]
    return D_(t,cuts)
def wired_corner_post():
    """Corner post with Ø5 vertical fish bore (replaces Ø3.2) + 5x3 open fish slot on the inside face, capped by panel."""
    p=CP.corner_post(); C=OFF
    cuts=[cyl(WC,W0.HT-4,C,C,6.0), bx(C-1.5,C+2.5,12,C+1.5,C+4.1,W0.HT-6)]
    return D_(p,cuts)
def wired_wall():
    """Short wall v1w: 4 mm wall thickened to 6 on the interior with a 3.5 x 2 vertical+horizontal wire raceway, 60x80 x1.2 service-panel recess, 4 magnet pockets."""
    w=W0.wall('blank'); L=CP.E  # start from full wall then trim to short length
    w=D_(w,[bx(-1,-50,-50,CP.E,50,200)]) if False else W0.wall('blank')
    # standing pose: x along wall, y thickness (centre 0? check bounds), z up
    b=w.bounds; y_in=b[1][1]
    add=bx(b[0][0]+10,y_in-0.01,12,b[1][0]-10,y_in+2.0,W0.HT-2)
    m=U([w,add]); yf=y_in+2.0
    xc=(b[0][0]+b[1][0])/2
    cuts=[bx(xc-30,yf-1.2,20,xc+30,yf+0.1,100),            # panel recess 60x80x1.2
          bx(xc-1.75,yf-3.2,12,xc+1.75,yf-1.19,W0.HT-4),       # vertical raceway 3.5 wide
          bx(b[0][0]+10,yf-3.2,W0.HT-8,b[1][0]-10,yf-1.19,W0.HT-4.5)]  # top horizontal raceway
    for x in (xc-24,xc+24):
        for z in (26,94): cuts.append(cyl(MAG_D,MAG_H+0.01,x,yf-1.2-MAG_H,z,'y'))
    m=D_(m,cuts)
    m=T.boolean.intersection([m,bx(CP.E,-50,-50,200,50,300)],engine='manifold')  # trim corner end -> 107.125 short wall, posts land on 15.875/47.625/79.375 from seam
    m.apply_translation([-CP.E,0,0]); return m
def service_panel():
    """1.2 mm panel 59.6x79.6 with 4 magnet bosses (pockets Ø6.2x... panel side takes Ø6x1 disc) + 2 mm finger notch."""
    p=bx(0,0,0,59.6,79.6,1.2); cuts=[bx(27.3,-0.1,0.6,32.3,2,1.3)]
    for x in (5.8,53.8):
        for y in (5.8,73.8): cuts.append(cyl(MAG_D,1.0,x,y,0.21))  # Ø6x1 magnets, 0.2 skin face
    return D_(p,cuts)
# ---------- furniture (sizes in real ft*12.7) ----------
def bed():
    return U([bx(0,0,0,50,80,8),bx(0,0,8,50,78,14),bx(0,76,0,50,80,30),bx(4,4,14,46,18,17),peg(15.875,15.875),peg(15.875+PITCH,15.875)])
def table():
    t=[bx(0,0,28,48,30,31)]+[bx(x,y,0,x+3,y+3,28) for x in (2,43) for y in (2,25)]; return U(t)
def chair():
    return U([bx(0,0,15,16,16,18),bx(0,13,18,16,16,38)]+[bx(x,y,0,x+2.5,y+2.5,15) for x in (1,12.5) for y in (1,12.5)])
def sofa():
    return U([bx(0,0,0,76,34,14),bx(0,26,14,76,34,34),bx(0,0,14,8,34,24),bx(68,0,14,76,34,24),peg(15.875,15.875),peg(15.875+2*PITCH,15.875)])
def bookshelf():
    m=bx(0,0,0,38,12,76); cuts=[bx(2,-0.1,2+i*18.5,36,10,2+i*18.5+16.5) for i in range(4)]
    return U([D_(m,cuts),peg(15.875,6)]) if False else D_(m,cuts)
def counter():
    m=U([bx(0,0,0,76,25,36),bx(-1,-1,36,77,26,38)]); return D_(m,[bx(40,4,34,66,20,38.5),bx(2,-0.1,4,74,0.8,32)])  # sink well + door reveal
def toilet():
    return U([bx(3,6,0,13,22,12),bx(0,4,12,16,26,16),bx(0,22,12,16,30,32)])
def sink():
    m=U([bx(5,6,0,13,14,28),bx(0,0,28,18,20,33)]); return D_(m,[bx(3,3,30,15,17,33.5)])
# ---------- figures (73 mm adult, 1:24) ----------
def _figure(h,sit=False):
    k=h/73.0; p=[]
    head=T.creation.icosphere(2,radius=5*k); head.apply_translation([0,0,h-5*k]); p.append(head)
    p.append(cyl(4*k,4*k,0,0,h-13*k))                       # neck
    if sit:
        p+= [bx(-8*k,-5*k,30*k,8*k,5*k,h-12*k),            # torso
             bx(-8*k,-5*k,24*k,8*k,22*k,31*k),             # thighs forward
             bx(-7*k,15*k,0,-1*k,22*k,24*k),bx(1*k,15*k,0,7*k,22*k,24*k)]  # shins
    else:
        p+= [bx(-8*k,-4.5*k,36*k,8*k,4.5*k,h-12*k),bx(-7*k,-4*k,0,-0.8*k,4*k,37*k),bx(0.8*k,-4*k,0,7*k,4*k,37*k)]
    p+= [bx(-11*k,-2.5*k,(28 if not sit else 34)*k,-8*k,2.5*k,h-13*k),bx(8*k,-2.5*k,(28 if not sit else 34)*k,11*k,2.5*k,h-13*k)]
    if not sit: p.append(cyl(16*k,1.2,0,0,-1.2))            # stand base
    return lift(U(p))
# ---------- fixtures: LED recess Ø5.2 (5 mm LED) or 3.6 (3 mm LED / 0805 on wire), wire exit Ø2 ----------
def ceiling_puck():
    m=cyl(16,4,0,0,0); return D_(m,[cyl(10,2.2,0,0,-0.01),cyl(2.2,5,0,0,-0.5),cyl(6.3,0,0,0,0) if False else cyl(5.9,0.01,99,99,99)])
def table_lamp():
    m=U([cyl(12,2,0,0,0),cyl(2.6,20,0,0,2),T.creation.cone(9,14,sections=40).apply_translation([0,0,18]) ])
    return D_(m,[cyl(3.6,6,0,0,18),cyl(1.4,26,0,0,-0.5),bx(-0.7,-7,-0.01,0.7,0,1.2)])  # LED pocket, wire bore, base slot
def wall_sconce():
    m=U([bx(-6,0,0,6,2,16),bx(-4,0,10,4,9,13),cyl(8,6,0,7,13)])
    return D_(m,[cyl(3.6,6.5,0,7,12.9),cyl(2,4,0,0,3,'y'),bx(-0.8,-0.1,3,0.8,1.2,13)])
def porch_light():
    m=U([bx(-5,0,0,5,2,22),bx(-4,2,16,4,10,18),bx(-5,5,4,5,12,16)])
    return D_(m,[cyl(3.6,9,0,8.5,5),cyl(2,4,0,1,10,'y')])
def post_lamp():
    m=U([cyl(14,2,0,0,0),peg(0,0) if False else cyl(5.9,0.01,0,0,0),cyl(4,72,0,0,2),bx(-6,-6,74,6,6,88),T.creation.cone(9,6,sections=4).apply_translation([0,0,88])])
    return D_(m,[cyl(5.2,10,0,0,77),cyl(1.6,80,0,0,-0.5)])
def power_module():
    """USB-C / 3xAAA box 60x30x20 that snaps on 2 sockets; Ø5 wire exit down into floor centre riser."""
    m=U([bx(0,0,0,60,30,20),peg(15.875,15),peg(15.875+PITCH,15)]); return D_(m,[bx(3,3,3,57,27,20.1),bx(-0.1,10,6,3.1,20,11),cyl(WC,4,30,15,-0.1)])
# Published exporters (STLs exist under dollhouse/stl/). Stair + fix_* lamps are CAD-only — see UNPUBLISHED.
PARTS=dict(upper_floor_tile_v1=upper_floor_tile,
  wired_floor_tile_v1w=wired_floor_tile,wired_corner_post_v1w=wired_corner_post,wired_wall_short_v1w=wired_wall,service_panel_v1w=service_panel,power_module_v1w=power_module,
  furn_bed_v1=bed,furn_table_v1=table,furn_chair_v1=chair,furn_sofa_v1=sofa,furn_bookshelf_v1=bookshelf,furn_counter_v1=counter,furn_toilet_v1=toilet,furn_sink_v1=sink,
  fig_adult_standing_v1=lambda:_figure(73),fig_adult_sitting_v1=lambda:_figure(56,True),fig_child_v1=lambda:_figure(46))
UNPUBLISHED=dict(stair_module_v1=stair_module,
  fix_ceiling_puck_v1=ceiling_puck,fix_table_lamp_v1=table_lamp,fix_wall_sconce_v1=wall_sconce,fix_porch_light_v1=porch_light,fix_post_lamp_v1=post_lamp)
if __name__=='__main__':
    for n,f in PARTS.items():
        m=f(); m.export(os.path.join(OUT,n+'.stl'))
        print(f"| `stl/{n}.stl` | {'%.1f × %.1f × %.1f'%tuple(m.extents)} | wt={m.is_watertight} | {len(m.faces)} tris | {m.volume/1000:.1f} cm³ |")
# ---- mini wall: a 1-tile side with corner posts at BOTH ends (Courtyard-3 inner court) = 127-2*19.875 = 87.25
def mini_wall(kind='blank'):
    w=W0.wall(kind) if kind=='blank' else W0.wall(kind)
    m=T.boolean.intersection([w,bx(CP.E,-50,-50,S-CP.E,50,300)],engine='manifold'); m.apply_translation([-CP.E,0,0]); return m
if __name__=='__main__':
    for n,k in (('wall_panel_mini_v1','blank'),('wall_panel_window_mini_v1','window'),('wall_panel_door_mini_v1','door')):
        m=mini_wall(k); m.export(os.path.join(OUT,n+'.stl')); print(n,m.is_watertight,m.extents.round(1),round(m.volume/1000,1))
