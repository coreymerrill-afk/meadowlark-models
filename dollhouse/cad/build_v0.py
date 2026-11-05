"""Dollhouse v0 modules (1:24, H3C). Units mm. Z=0 is bed. Requires trimesh+manifold3d."""
import trimesh as T, numpy as np, os
from trimesh.creation import box, cylinder
OUT=os.path.join(os.path.dirname(__file__),'..','stl')
S=127.0; DECK=4.0; RIB_H=6.0; H=DECK+RIB_H; PITCH=31.75; OFF=PITCH/2
SOCK_D=6.3  # Ø6.0 post + 2x0.15 radial clearance (0.4 nozzle); nominal Ø6.1 = 0.05 radial, too tight
SOCK_DEPTH=8.0; LC=3.2; RACE_IN=5.0; RACE_Z=3.0
def bx(x0,y0,z0,x1,y1,z1):
    b=box([x1-x0,y1-y0,z1-z0]); b.apply_translation([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]); return b
def cyl(d,h,x,y,z0,ax='z',sec=48):
    c=cylinder(radius=d/2,height=h,sections=sec)
    if ax=='x': c.apply_transform(T.transformations.rotation_matrix(np.pi/2,[0,1,0]))
    if ax=='y': c.apply_transform(T.transformations.rotation_matrix(np.pi/2,[1,0,0]))
    c.apply_translation([x,y,z0+(h/2 if ax=='z' else 0)]); return c
U=lambda m:T.boolean.union(m,engine='manifold'); D_=lambda a,b:T.boolean.difference([a]+b,engine='manifold')
def floor_tile():
    solids=[bx(0,0,RIB_H,S,S,H)]
    W=6.0  # perimeter rim
    solids+= [bx(0,0,0,S,W,RIB_H),bx(0,S-W,0,S,S,RIB_H),bx(0,0,0,W,S,RIB_H),bx(S-W,0,0,S,S,RIB_H)]
    for k in (1,2,3):  # interior ribs between socket rows
        p=k*PITCH; solids+=[bx(p-1,0,0,p+1,S,RIB_H),bx(0,p-1,0,S,p+1,RIB_H)]
    pts=[OFF+i*PITCH for i in range(4)]
    for x in pts:
        for y in pts: solids.append(cyl(SOCK_D+3.2,RIB_H,x,y,0))  # socket bosses
    m=U(solids); cuts=[]
    for x in pts:
        for y in pts: cuts.append(cyl(SOCK_D,SOCK_DEPTH+0.01,x,y,H-SOCK_DEPTH))
    # light races: Ø3.2 loop inset 5mm in rim, z=3
    r=RACE_IN
    cuts+=[cyl(LC,S-2*r+LC,S/2,r,RACE_Z,'x'),cyl(LC,S-2*r+LC,S/2,S-r,RACE_Z,'x'),
           cyl(LC,S-2*r+LC,r,S/2,RACE_Z,'y'),cyl(LC,S-2*r+LC,S-r,S/2,RACE_Z,'y')]
    for x in (r,S-r):
        for y in (r,S-r): cuts.append(cyl(LC,H+1,x,y,-0.5))  # corner risers
    # room switch stub on +Y edge centre: Ø8x6 recess + 10x6x1 faceplate pocket
    cuts.append(cyl(8.0,12.0,S/2,S,5.0,'y'))  # spans y 121..133 -> 6 deep
    cuts.append(bx(S/2-5,S-1,2,S/2+5,S+0.1,8))
    return D_(m,cuts)
def snap_post():
    p=cyl(6.0,8.0-0.4,0,0,0); ch=cylinder(radius=3.0,height=0.4,sections=48)
    c=T.creation.cone(radius=3.0,height=3.0,sections=48)  # chamfer top via truncated cone
    top=T.boolean.intersection([c,bx(-4,-4,0,4,4,0.4)],engine='manifold'); top.apply_translation([0,0,7.6])
    flange=cyl(9.0,1.0,0,0,-1.0)
    m=U([p,top,flange]); m.apply_translation([0,0,1]); return m
if __name__=='__main__':
    os.makedirs(OUT,exist_ok=True)
    for n,f in [('floor_tile_v0',floor_tile),('snap_post_v0',snap_post)]:
        m=f(); m.export(os.path.join(OUT,n+'.stl'))
        print(n,'watertight',m.is_watertight,'bbox',np.round(m.extents,2),'tris',len(m.faces),'vol cm3',round(m.volume/1000,1))
