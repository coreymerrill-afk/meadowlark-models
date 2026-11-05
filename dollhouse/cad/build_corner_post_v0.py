"""Corner post v0 + short walls v0c (1:24, H3C). Units mm. SUPERSEDES corner_bridge_v0 (+ v0b ports) at 90° corners.
Tile coords: outer tile corner (0,0), deck top z=0. Corner socket C=(15.875,15.875).
Rule: the corner post OWNS socket C. Walls never claim a corner socket; at a corner the run starts at 19.875
(= C + plinth half-thickness 4). Short wall length = 127-19.875 = 107.125; posts at 15.875/47.625/79.375 from its
SEAM end (the end on the tile seam / far end). One part works on both ends of a 2-tile side (rotate 180°).
Light: floor riser (5,5) -> z=4 -> along y=5 to x=C -> along x=C to y=C -> vertical up column centre -> at z=HT-3
exits +X and +Y faces straight into the open-ended top race of each butting wall. Top exit at (5,5) for an
exterior corner lamp. Post prints UPRIGHT (footing on bed): the Ø6 peg is a separate dowel_pin_v0 in a bottom socket."""
import os, numpy as np, trimesh as T
from build_v0 import bx, cyl, U, D_, OUT, LC, RACE_IN, SOCK_D, OFF, PITCH
import build_wall_v0 as W0
C=OFF; HALF=W0.PL_T/2; E=C+HALF  # 19.875 wall start
HT=W0.HT; FOOT=12.0; PZ=8.0; SD=5.5; r=RACE_IN; IN=0.5; DOWEL=8.0+SD
def corner_post():
    # footing 19.4 sq x 12 (covers floor riser (5,5)); 8x8 pilaster to HT, faces flush with wall plinth faces
    m=U([bx(IN,IN,0,E,E,FOOT), bx(C-HALF,C-HALF,0,E,E,HT)]); L=LC
    sph=lambda x,y,z: T.creation.icosphere(subdivisions=2,radius=L/2+0.01).apply_translation([x,y,z])
    cuts=[cyl(SOCK_D,SD+0.01,C,C,-0.01),          # bottom socket (5.5 deep) for dowel_pin_v0
          cyl(L,PZ+0.01,r,r,-0.01),               # riser drop from floor corner riser (5,5)
          cyl(L,C-r,r,(r+C)/2,PZ,'y'),            # along Y at x=5 -> y=C
          cyl(L,C-r,(r+C)/2,C,PZ,'x'),            # along X at y=C -> x=C (above socket: 0.9 mm floor)
          cyl(L,HT-3-PZ,C,C,PZ),                  # vertical up pilaster centre
          cyl(L,E-C+1,(C+E+1)/2,C,HT-3,'x'),      # +X exit -> wall top race (open end)
          cyl(L,E-C+1,C,(C+E+1)/2,HT-3,'y'),      # +Y exit
          cyl(L,FOOT-PZ+1,r,r,PZ),                # top exit at (5,5): exterior corner lamp (plug if unused)
          sph(r,r,PZ),sph(r,C,PZ),sph(C,C,PZ),sph(C,C,HT-3)]
    return D_(m,cuts)
def dowel_pin():
    L=DOWEL; p=cyl(6.0,L-0.8,0,0,0.4)
    def tip():
        c=T.creation.cone(radius=3.0,height=3.0,sections=48); return T.boolean.intersection([c,bx(-4,-4,0,4,4,0.4)],engine='manifold')
    t=tip(); t.apply_translation([0,0,L-0.4]); b=tip(); b.apply_transform(T.transformations.rotation_matrix(np.pi,[1,0,0])); b.apply_translation([0,0,0.4])
    m=U([p,t,b]); m.apply_translation(-m.bounds[0]); return m
def short_wall(kind='blank'):
    """Wall 107.125 long, built by trimming a v0-style wall. Wall x=0 is the CORNER end (butts the post),
    x=107.125 is the seam end. Posts at 27.75/59.5/91.25 from corner end. Openings stay on the v0 tile grid
    (centre 43.625 from corner end), vertical bore kept only at seam end (x=102.125)."""
    Ls=127.0-E; full=W0.wall(kind)  # v0 posts at 15.875..111.125; keep x in [E,127]
    m=T.boolean.intersection([full,bx(E,-10,-20,127,10,HT+5)],engine='manifold')
    m.apply_translation([-E,0,0])
    return m
if __name__=='__main__':
    out=[('corner_post_v0',corner_post()),('dowel_pin_v0',dowel_pin())]
    for k in ('blank','window','door'):
        out.append((('wall_panel_short_v0c' if k=='blank' else f'wall_panel_{k}_short_v0c'),W0.to_print(short_wall(k))))
    for n,m in out:
        m.export(os.path.join(OUT,n+'.stl'))
        print(n,'watertight',m.is_watertight,'bodies',len(m.split(only_watertight=False)),'bbox',np.round(m.extents,3),'tris',len(m.faces),'vol cm3',round(m.volume/1000,2))
