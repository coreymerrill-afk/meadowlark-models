"""Wall panel + snap clearance strip v0 (1:24, H3C). Units mm. Reuses build_v0 helpers.
Wall modelled standing: X=width 0..127, Y=thickness, Z=up (Z=0 = floor deck top). Exported in PRINT pose
(inverted: wall top on bed, posts pointing up) -> no supports."""
import os, numpy as np, trimesh as T
from build_v0 import bx, cyl, U, D_, OUT, PITCH, OFF, LC, snap_post
W=127.0; HT=101.6; TH=4.0; PL_T=8.0; PL_H=10.0  # baseboard plinth 8 thick x 10 tall carries Ø6 posts
POST_D=6.0; POST_L=8.0; CH=0.4; RACE_DN=3.0; END_IN=5.0
def post_down(x,y):
    p=cyl(POST_D,POST_L-CH,x,y,-(POST_L-CH))
    c=T.creation.cone(radius=POST_D/2,height=POST_D/2,sections=48)
    tip=T.boolean.intersection([c,bx(-4,-4,0,4,4,CH)],engine='manifold')
    tip.apply_transform(T.transformations.rotation_matrix(np.pi,[1,0,0])); tip.apply_translation([x,y,-(POST_L-CH)])
    return [p,tip]
def wall(kind='blank',port=False):
    yc=0.0  # wall centred on socket line y=0
    s=[bx(0,-TH/2,0,W,TH/2,HT), bx(0,-PL_T/2,0,W,PL_T/2,PL_H-2)]
    # 45° chamfer plinth->wall (2mm step) so inverted print has no flat overhang
    for sgn in (1,-1):
        y0=sgn*TH/2; y1=sgn*(TH/2+2); z=PL_H-2
        pr=T.convex.convex_hull(np.array([[x,y,zz] for x in (0,W) for (y,zz) in ((y0,z),(y1,z),(y0,z+2))]))
        s.append(pr)
    xs=[OFF+i*PITCH for i in range(4)]
    for x in xs: s+=post_down(x,yc)
    m=U(s); cuts=[cyl(LC,W+1,W/2,yc,HT-RACE_DN,'x')]  # open-ended top race
    for x in (END_IN,W-END_IN): cuts.append(cyl(LC,HT-RACE_DN+1,x,yc,-0.5))  # corner vertical bores to race
    if port:  # v0b: Ø3.2 side port through plinth at z=4 into each vertical bore (meets corner_bridge_v0)
        for x in (END_IN,W-END_IN): cuts.append(cyl(LC,PL_T+1,x,yc,4.0,'y'))
    if kind=='window':  # 38x50 centred, sill at 36 (≈34in) + 2mm sill lip
        z0=36.0; cuts.append(bx(W/2-19,-5,z0,W/2+19,5,z0+50))
        m=D_(m,cuts); return U([m,bx(W/2-21,-TH/2-2,z0-2,W/2+21,TH/2,z0)])
    if kind=='door': cuts.append(bx(W/2-18,-5,PL_H,W/2+18,5,PL_H+76))
    return D_(m,cuts)
def to_print(m):  # flip: wall top on bed, posts up
    m=m.copy(); m.apply_transform(T.transformations.rotation_matrix(np.pi,[1,0,0]))
    m.apply_translation(-m.bounds[0]); return m
def clearance_strip():
    L,Wd,H=40.0,12.0,12.0; bar=bx(0,0,0,L,Wd,H); cuts=[]
    for i,d in enumerate((6.2,6.3,6.4)):
        x=8+12*i; cuts.append(cyl(d,8.01,x,Wd/2,H-8))
        for k in range(i+1): cuts.append(cyl(1.2,0.61,x-2+2*k,1.6,H-0.6))  # 1/2/3 dot label = 6.2/6.3/6.4
    parts=[D_(bar,cuts)]
    for i in range(3):
        p=snap_post(); p.apply_translation([8+12*i,Wd+8,0]); parts.append(p)
    return T.util.concatenate(parts)
if __name__=='__main__':
    for n,m in [('wall_panel_v0',to_print(wall())),('wall_panel_window_v0',to_print(wall('window'))),
                ('wall_panel_door_v0',to_print(wall('door'))),('snap_clearance_strip_v0',clearance_strip())]+\
        [(f'wall_panel{k}_v0b',to_print(wall(k.strip('_') or 'blank',port=True))) for k in ('','_window','_door')]:
        m.export(os.path.join(OUT,n+'.stl'))
        print(n,'watertight',m.is_watertight,'bodies',len(m.split(only_watertight=False)),'bbox',np.round(m.extents,2),'tris',len(m.faces),'vol cm3',round(m.volume/1000,1))
