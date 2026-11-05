"""Corner light-bridge v0 (1:24, H3C). Units mm. Tile coords: corner at (0,0), deck top = z0.
Block sits in the outer corner zone (0..11.6 sq) clear of both wall plinths (plinth outer face at 11.875).
Wire path: floor riser (5,5) -> up into block -> 90° turn at z=4 -> horizontal Ø3.2 exits on +Y face (x=5)
and +X face (y=5), aimed at the plinth side-port of wall_panel_*_v0b (x=5 / z=4). Optional Ø3.2 top exit
for an exterior corner lamp. 2 mm skirt hooks the tile's outer edges = foolproof index.
Exported in PRINT pose: inverted (top on bed, skirt up) -> no supports."""
import os, numpy as np, trimesh as T
from build_v0 import bx, cyl, U, D_, OUT, LC, RACE_IN
A=11.6; HB=12.0; SK=2.0; SKD=4.0; PZ=4.0; r=RACE_IN
def corner_bridge():
    s=[bx(0,0,0,A,A,HB), bx(-SK,-SK,-SKD,A,0,HB), bx(-SK,-SK,-SKD,0,A,HB)]  # block + L skirt over tile edges
    m=U(s)
    cuts=[cyl(LC,PZ+0.01,r,r,-0.01),                    # drop from floor riser
          cyl(LC,A-r+1,r,(r+A+1)/2,PZ,'y'),             # -> wall along tile X edge
          cyl(LC,A-r+1,(r+A+1)/2,r,PZ,'x'),             # -> wall along tile Y edge
          cyl(LC+0.01,LC+0.01,r,r,PZ-LC/2),             # rounded junction volume
          cyl(LC,HB-PZ+1,r,r,PZ)]                       # top exit: exterior corner lamp
    return D_(m,cuts)
def to_print(m):
    m=m.copy(); m.apply_transform(T.transformations.rotation_matrix(np.pi,[1,0,0])); m.apply_translation(-m.bounds[0]); return m
if __name__=='__main__':
    m=to_print(corner_bridge()); m.export(os.path.join(OUT,'corner_bridge_v0.stl'))
    print('corner_bridge_v0 watertight',m.is_watertight,'bbox',np.round(m.extents,2),'tris',len(m.faces),'vol cm3',round(m.volume/1000,2))
