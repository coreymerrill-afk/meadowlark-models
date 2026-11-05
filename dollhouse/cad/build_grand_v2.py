"""Grand kit v2 (1:24, H3C 330x320x325): ornate silhouette parts that ride the 127 mm tile / Ø6 snap / corner-post system.
All parts: Z=0 on bed, Ø5.9 pegs into Ø6.3 sockets (31.75 pitch) or Ø6.3 sockets for dowels. Light race Ø3.2 where noted."""
import os, numpy as np, trimesh as T
from trimesh.creation import cone, icosphere, cylinder, annulus
from build_v0 import bx, cyl, U, D_, OUT, LC, SOCK_D, OFF, PITCH, S
R=T.transformations.rotation_matrix
HT=101.6
def peg(x,y,z=0): return cyl(5.9,5.0,x,y,z-5.0)
def mv(m,x=0,y=0,z=0): m=m.copy(); m.apply_translation([x,y,z]); return m
def rot(m,a,ax=(0,0,1)): m=m.copy(); m.apply_transform(R(a,ax)); return m
def lift(m): m.apply_translation([0,0,-m.bounds[0][2]]); return m
def prism(pts2d,h,ax='y'):  # extrude polygon in XZ plane along Y
    from shapely.geometry import Polygon
    m=T.creation.extrude_polygon(Polygon(pts2d),h); m.apply_transform(R(np.pi/2,[1,0,0])); m.apply_translation([0,h,0]); return m
def arch_cut(w,h,th,x,z0,y0=-1):  # round-top opening, cut along Y
    r=w/2; return U([bx(x-r,y0,z0,x+r,y0+th,z0+h-r), cyl(w,th,x,y0+th/2,z0+h-r,'y')])
# ---------- architecture ----------
def turret_segment(d=96,h=HT,win=True):
    """Hollow round tower drum, 4 mm wall, 4 arched windows, Ø3.2 light drop in wall, 4 pegs + 4 top sockets on 31.75 grid square."""
    o=cyl(d,h,0,0,0,sec=96); i=cyl(d-8,h+2,0,0,-1,sec=96)
    m=D_(o,[i]); band=D_(cyl(d+4,4,0,0,h-8,sec=96),[cyl(d-6,6,0,0,h-9,sec=96)])
    m=U([m,band,D_(cyl(d+3,6,0,0,0,sec=96),[cyl(d-6,8,0,0,-1,sec=96)])])
    cuts=[]
    if win:
        for a in range(4):
            c=arch_cut(18,44,12,0,30,d/2-8); cuts.append(rot(c,a*np.pi/2+np.pi/4))
    cuts.append(cyl(LC,h+2,d/2-2,0,-1))
    for sx in (-1,1):
        for sy in (-1,1): cuts.append(cyl(SOCK_D,6,sx*PITCH/2*1.0+sx*0,sy*PITCH/2,h-5.9))
    ring=[bx(sx*PITCH/2-4,sy*PITCH/2-4,0,sx*PITCH/2+4,sy*PITCH/2+4,6) for sx in (-1,1) for sy in (-1,1)]
    tops=[cyl(10,8,sx*PITCH/2,sy*PITCH/2,h-8) for sx in (-1,1) for sy in (-1,1)]
    # bosses tie to wall via spokes
    sp=[bx(-d/2+4,-2,h-8,d/2-4,2,h),bx(-2,-d/2+4,h-8,2,d/2-4,h),bx(-d/2+4,-2,0,d/2-4,2,6),bx(-2,-d/2+4,0,2,d/2-4,6)]
    m=U([m]+ring+tops+sp+[peg(sx*PITCH/2,sy*PITCH/2) for sx in (-1,1) for sy in (-1,1)])
    return D_(m,cuts)
def turret_cap(d=104,h=110):
    """Witch-hat cone roof with flared eave, scalloped shingle bands and finial; hollow, pegs into turret sockets."""
    c=cone(d/2,h,sections=96); c=U([c,D_(cyl(d+8,4,0,0,0,sec=96),[cyl(d-12,6,0,0,-1,sec=96)])])
    inner=mv(cone(d/2-4,h-8,sections=96),0,0,-0.01)
    m=D_(c,[inner])
    bands=[]
    for k,f in enumerate((0.25,0.45,0.65)):
        r=d/2*(1-f)+1.2; bands.append(D_(cyl(2*r,2.2,0,0,h*f,sec=96),[cyl(2*r-6,3,0,0,h*f-0.5,sec=96)]))
    fin=U([cyl(3,22,0,0,h-4),mv(icosphere(2,radius=4),0,0,h+10),mv(cone(3,8),0,0,h+14)])
    pl=[cyl(10,4,sx*PITCH/2,sy*PITCH/2,0) for sx in (-1,1) for sy in (-1,1)]
    sp=[bx(-PITCH/2,-2,0,PITCH/2,2,4),bx(-2,-PITCH/2,0,2,PITCH/2,4)]
    m=U([m,fin]+bands+pl+sp+[peg(sx*PITCH/2,sy*PITCH/2) for sx in (-1,1) for sy in (-1,1)])
    return lift(D_(m,[cyl(LC,h,0,0,-1)]))  # light bore up the finial for a tip LED
def roof_panel(span=S*2,run=S/2+12,pitch=45,th=4):
    """One half of a gable roof (prints flat, shingle texture up): 254 x ~100, rows of fish-scale bumps, ridge dowel holes."""
    L=run/np.cos(np.radians(pitch)); m=bx(0,0,0,span,L,th); tiles=[]
    for r,y in enumerate(np.arange(6,L-4,9)):
        off=0 if r%2==0 else 6
        for x in np.arange(6+off,span-4,12): tiles.append(cyl(11,1.4,x,y,th-0.01,sec=16))
    m=U([m]+tiles); cuts=[cyl(SOCK_D,8,x,L-4,th/2,'y') for x in (OFF,span/2,span-OFF)]
    cuts+= [cyl(SOCK_D,th+2,x,8,-1) for x in (OFF,span-OFF)]
    return D_(m,cuts)
def gable_end(w=S,rise=None,pitch=45):
    """Triangular gable with gingerbread bargeboard scallops, round attic window + pegs on base."""
    rise=rise or w/2*np.tan(np.radians(pitch)); m=prism([(0,0),(w,0),(w/2,rise)],4)
    barge=[]
    for s in (1,-1):
        for k in np.linspace(0.08,0.92,9):
            x=w/2-s*(w/2)*(1-k); z=rise*k
            barge.append(cyl(6,6,x,2,z-4.5,'y',sec=16))
    m=U([m]+barge+[mv(cyl(4,30,w/2,2,rise-6),0,0,0)])
    m=D_(m,[cyl(22,10,w/2,2,rise*0.45,'y'),bx(w/2-0.8,-1,rise*0.45-11,w/2+0.8,6,rise*0.45+11)])
    m=U([m,D_(cyl(26,5,w/2,2,rise*0.45,'y'),[cyl(21,7,w/2,2,rise*0.45,'y')])])
    m=U([m]+[peg(x,2) for x in (OFF,w-OFF)]); return m
def dormer():
    """Pop-out dormer: 50 wide box, arched window, tiny gable roof + finial; base cut to sit on a 45° roof panel (2 pegs)."""
    w,d,h=50,46,48
    body=bx(0,0,0,w,d,h); body=D_(body,[bx(4,4,-1,w-4,d+1,h-4),arch_cut(24,34,8,w/2,8,-1)])
    roof=prism([(-5,h),(w+5,h),(w/2,h+30)],d+6); roof=mv(roof,0,-3,0)
    roof=D_(roof,[mv(prism([(0,h-0.1),(w,h-0.1),(w/2,h+25)],d+8),0,-4,0)])
    sill=bx(w/2-16,-3,6,w/2+16,2,9)
    cut=prism([(-20,-1),(w+20,-1),(w+20,d*1.0+1)],w+40); cut=rot(cut,0)
    m=U([body,roof,sill,cyl(3,14,w/2,-3,h+28),mv(icosphere(1,radius=3),w/2,-3,h+43)])
    m=D_(m,[bx(-10,d-0.01,-60,w+10,d+60,0.01)])
    return lift(U([m,peg(OFF,d/2),peg(w-OFF+8,d/2)]))
def porch_post(h=HT):
    """Turned porch column Ø10 with capital, base, and corbel brackets; peg bottom, Ø6.3 socket top for porch roof/rail."""
    prof=[(0,0),(8,0),(8,5),(6,7),(5,10),(5,h-14),(6.5,h-10),(5,h-8),(8,h-4),(8,h),(0,h)]
    m=T.creation.revolve(np.array(prof),sections=48)
    beads=[mv(T.creation.torus(5.4,1.4,major_sections=48,minor_sections=12),0,0,z) for z in (18,h*0.5,h-20)]
    cor=[rot(prism([(5,h-26),(5,h),(26,h),(26,h-4)],4),a) for a in (0,np.pi)]
    cor=[mv(c,0,-2,0) for c in cor]
    m=U([m]+beads+cor+[peg(0,0)])
    return D_(m,[cyl(SOCK_D,8,0,0,h-7.9),cyl(LC,h-12,4.2,0,4)])
def railing(L=S-2*OFF+PITCH,h=36):
    """Spindle railing: top+bottom rail, 13 turned balusters; pegs/sockets on 31.75 pitch so it clips between posts."""
    m=[bx(0,-3,h-5,L,3,h),bx(0,-2.5,4,L,2.5,8)]
    n=int(L//8)
    for k in range(1,n):
        x=k*L/n; m+= [cyl(3.4,h-12,x,0,8),mv(icosphere(1,radius=2.4),x,0,h*0.5)]
    return U(m+[peg(x,0) for x in (PITCH/2,L-PITCH/2)])
def gingerbread_trim(L=S,h=22):
    """Lace fascia: scalloped bracket strip with cut trefoils; clips under eaves (2 Ø6.3 sockets on 63.5 pitch)."""
    m=bx(0,0,0,L,3,h); cuts=[]
    for x in np.arange(8,L-4,15.875):
        cuts+= [cyl(9,6,x,1.5,6,'y',sec=24),cyl(4,6,x-4,1.5,13,'y',sec=16),cyl(4,6,x+4,1.5,13,'y',sec=16)]
        cuts.append(bx(x-2,-1,-1,x+2,5,3))
    m=D_(m,cuts); drops=[U([cyl(2.6,6,x,1.5,-5),mv(icosphere(1,radius=2.4),x,1.5,-6)]) for x in np.arange(16,L-4,15.875)]
    return lift(U([m]+drops))
def bay_window():
    """Three-sided canted bay (127 face, 40 deep), 3 arched lights, corbelled base, copper-style hip cap. Pegs into floor sockets."""
    w,d,h=S-2*12,40,82; a=d
    pts=[(0,0),(a,d),(w-a,d),(w,0)]
    from shapely.geometry import Polygon
    pl=Polygon(pts); body=T.creation.extrude_polygon(pl,h); inner=mv(T.creation.extrude_polygon(Polygon([(4,-3),(a+1,d-4),(w-a-1,d-4),(w-4,-3)]),h+2),0,0,0)
    body=D_(body,[mv(inner,0,0,6)])
    cuts=[mv(rot(arch_cut(20,50,10,0,0,-5),0),w/2,d,14)]
    for sx,x0,ang in ((1,a/2,np.arctan2(d,a)),(1,w-a/2,-np.arctan2(d,a))):
        c=rot(arch_cut(16,46,10,0,0,-5),-ang); cuts.append(mv(c,x0,d/2,16))
    body=D_(body,cuts)
    cap=T.creation.extrude_polygon(pl.buffer(5,join_style=2),5); cap=mv(cap,0,0,h)
    hip=T.creation.extrude_polygon(pl.buffer(3,join_style=2),12,); hip=mv(hip,0,0,h+5)
    hip=T.boolean.intersection([hip,mv(prism([(-10,h+5),(w+10,h+5),(w/2,h+40)],80),0,-20,0)],engine='manifold')
    cor=T.creation.extrude_polygon(pl.buffer(2,join_style=2),6)
    m=U([body,cap,hip,cor]+[peg(x,8) for x in (PITCH/2+8,w-PITCH/2-8)])
    return lift(D_(m,[cyl(LC,h,w/2,d-6,0)]))
def chimney():
    """Brick stack 30x24x120 with corbel bands and two chimney pots; LED flicker cavity Ø8 with Ø3.2 wire feed."""
    m=[bx(0,0,0,30,24,120),bx(-3,-3,96,33,27,102),bx(-4,-4,108,34,28,112)]
    for z in np.arange(6,94,6):
        m.append(bx(-0.6,-0.6,z,30.6,24.6,z+1.0))
    m+= [cyl(9,14,9,12,112),cyl(9,14,21,12,112),cyl(11,3,9,12,124),cyl(11,3,21,12,124)]
    m=U(m+[peg(OFF/2+7,12)]); return D_(m,[cyl(6,20,9,12,110),cyl(6,20,21,12,110),cyl(8,30,15,12,88),cyl(LC,100,15,12,-1)])
def cupola():
    """Octagonal lantern cupola with arched openings and onion dome + weathervane; widow's-walk / ridge topper."""
    o=cyl(56,46,0,0,0,sec=8); m=D_(o,[cyl(48,48,0,0,4,sec=8)]+[rot(arch_cut(12,30,10,0,10,22),k*np.pi/4+np.pi/8) for k in range(8)])
    base=cyl(64,6,0,0,-6,sec=8); cap=cyl(64,4,0,0,46,sec=8)
    dome=icosphere(3,radius=26); dome.apply_scale([1,1,1.2]); dome=T.boolean.intersection([dome,bx(-40,-40,0,40,40,40)],engine='manifold'); dome=mv(dome,0,0,50)
    tip=U([cone(10,26,sections=32)]); tip=mv(tip,0,0,78)
    vane=U([cyl(2,26,0,0,100),bx(-14,-0.8,116,14,0.8,120),prism([(14,112),(22,118),(14,124)],1.6)])
    vane=mv(vane,0,0,0)
    m=U([m,base,cap,dome,tip,vane]+[peg(sx*PITCH/2,sy*PITCH/2,-6) for sx in (-1,1) for sy in (-1,1)])
    return lift(D_(m,[cyl(LC,90,0,0,-12)]))
def crenel_parapet(L=S):
    """Battlement strip 127 long for tower tops / rooftop terrace: merlons with arrow slits, pegs below."""
    m=[bx(0,0,0,L,8,14)]
    for x in np.arange(0,L-4,21.2): m.append(D_(bx(x,0,14,x+12,8,30),[bx(x+5,-1,18,x+7,9,27)]))
    return U(m+[peg(x,4) for x in (OFF,L-OFF)])
def arcade_panel(L=S,h=HT):
    """Cloister arcade: 3 round arches on twisted-look columns, keystones, light race in the frieze. Same pegs as a wall."""
    m=bx(0,0,0,L,8,h); cuts=[]; n=3; w=(L-8*4)/n
    for k in range(n):
        x=8+w/2+k*(w+8); cuts.append(arch_cut(w,h-26,10,x,10,-1))
    m=D_(m,cuts); add=[]
    for k in range(n+1):
        x=4+k*(w+8)
        for z in np.arange(12,h-30,7): add.append(mv(T.creation.torus(4.2,1.2,major_sections=24,minor_sections=8),x,4,z))
    for k in range(n):
        x=8+w/2+k*(w+8); add.append(prism([(x-4,h-18),(x+4,h-18),(x+3,h-10),(x-3,h-10)],12)); add[-1]=mv(add[-1],0,-2,0)
    add.append(bx(-2,-2,h-8,L+2,10,h))
    m=U([m]+add+[peg(x,4) for x in (OFF,L-OFF)])
    return D_(m,[cyl(LC,L+6,L/2,4,h-4,'x')])
def fountain():
    """Tiered courtyard fountain on a 127 tile plinth: octagon basin, two bowls, pinecone finial, LED well + Ø3.2 feed."""
    b=D_(cyl(110,18,0,0,0,sec=8),[cyl(100,20,0,0,4,sec=8)])
    st=cyl(16,56,0,0,0,sec=24); bowl1=D_(cyl(60,8,0,0,40,sec=48),[cyl(54,8,0,0,43,sec=48)])
    bowl2=D_(cyl(32,6,0,0,66,sec=48),[cyl(27,6,0,0,68,sec=48)]); st2=cyl(8,30,0,0,50)
    pine=icosphere(2,radius=5); pine.apply_scale([1,1,1.8]); pine=mv(pine,0,0,82)
    m=U([b,st,bowl1,bowl2,st2,pine]+[peg(sx*PITCH,sy*PITCH) for sx in (-1,1) for sy in (-1,1)])
    return lift(D_(m,[cyl(LC,80,0,0,-6),cyl(10,6,0,0,62)]))
def clock_tower(h=200):
    """Workshop clocktower: square 64 shaft (prints in 2 halves on H3C height-wise fine at 200), four Ø44 clock faces, belfry arches, spire."""
    m=D_(bx(-32,-32,0,32,32,h),[bx(-28,-28,-1,28,28,h+1)])
    faces=[]
    for a in range(4):
        f=U([cyl(46,4,0,33,h-50,'y'),D_(cyl(40,2,0,35.5,h-50,'y'),[cyl(36,3,0,35.5,h-50,'y')])])
        for k in range(12): f=U([f,mv(bx(-0.8,34,17,0.8,37,20),0,0,0) if False else rot(mv(bx(-0.8,34,-20,0.8,37.5,-16),0,0,h-50),0)]) if k==0 else f
        faces.append(rot(f,a*np.pi/2))
    hands=[rot(U([bx(-1,35,h-50,1,37.5,h-34),bx(0,35,h-51,12,37.5,h-49)]),a*np.pi/2) for a in range(4)]
    bel=[rot(arch_cut(20,34,10,0,h-24,26),a*np.pi/2) for a in range(4)]
    m=D_(m,bel)
    cor=[bx(-36,-36,h-4,36,36,h),bx(-36,-36,h-82,36,36,h-78),bx(-35,-35,0,35,35,8)]
    m=U([m]+faces+hands+cor+[peg(sx*PITCH/2,sy*PITCH/2) for sx in (-1,1) for sy in (-1,1)])
    return D_(m,[cyl(LC,h,24,24,-1)])
def clock_spire():
    sp=U([mv(T.creation.cone(40,90,sections=4),0,0,0),cyl(3,30,0,0,84),mv(icosphere(1,radius=4),0,0,112)])
    sp=rot(sp,np.pi/4); base=bx(-38,-38,0,38,38,4)
    return lift(U([sp,base]+[peg(sx*PITCH/2,sy*PITCH/2) for sx in (-1,1) for sy in (-1,1)]))
def smokestack():
    """Riveted brick smokestack Ø36x220 with banded cap and gear ornament; houses a cold-smoke-look LED glow."""
    m=D_(cyl(36,220,0,0,0,sec=48),[cyl(28,222,0,0,6,sec=48)])
    bands=[D_(cyl(42,5,0,0,z,sec=48),[cyl(34,6,0,0,z-.5,sec=48)]) for z in (0,60,140,205)]
    cap=D_(cyl(46,10,0,0,214,sec=48),[cyl(30,12,0,0,213,sec=48)])
    g=cyl(28,6,0,21,110,'y',sec=16); teeth=[rot(bx(-2,18,108,2,24,126),0)]
    gear=D_(U([g]+[rot(mv(bx(-2,18,-2,2,24,2),0,0,0),0)]),[cyl(8,8,0,21,110,'y')])
    base=bx(-26,-26,0,26,26,16)
    return U([m,cap,gear,base]+bands+[peg(sx*PITCH/2,sy*PITCH/2) for sx in (-1,1) for sy in (-1,1)])
def balcony():
    """Juliet balcony: half-round deck Ø70 on S-curve corbels with spindle rail; 2 pegs into wall plinth sockets."""
    deck=T.boolean.intersection([cyl(76,4,0,0,0,sec=64),bx(-40,0,-1,40,40,6)],engine='manifold')
    rail=[]
    for k in range(13):
        a=np.pi*k/12; rail.append(cyl(2.6,26,36*np.cos(a),36*np.sin(a),4))
    top=T.boolean.intersection([D_(cyl(78,3,0,0,30,sec=64),[cyl(70,5,0,0,29,sec=64)]),bx(-42,0,28,42,42,34)],engine='manifold')
    cor=[mv(prism([(0,0),(14,0),(4,-24),(0,-24)],4),x,0,0) for x in (-24,20)]
    cor=[rot(rot(c,np.pi/2,(0,0,1)),0) for c in cor]
    m=U([deck,top]+rail+[bx(-30,-4,-24,-26,0,0),bx(26,-4,-24,30,0,0)]+[mv(cyl(5.9,6,x,-2,-24,'y'),0,0,0) for x in ()])
    return lift(U([m,bx(-40,-6,-2,40,0,4)]))
def widows_walk(L=S*2,W=S):
    """Rooftop widow's walk frame: perimeter rail with finial posts at each 63.5, pegs into ridge sockets."""
    m=[]
    for (x0,y0,x1,y1) in ((0,0,L,4),(0,W-4,L,W),(0,0,4,W),(L-4,0,L,W)): m+= [bx(x0,y0,24,x1,y1,28),bx(x0,y0,0,x1,y1,4)]
    for x in np.arange(0,L+1,63.5):
        for y in (2,W-2): m+= [cyl(5,30,min(max(x,2.5),L-2.5),y,0),mv(icosphere(1,radius=3.5),min(max(x,2.5),L-2.5),y,32)]
    for x in np.arange(8,L-4,9): m+= [cyl(2.4,20,x,2,4),cyl(2.4,20,x,W-2,4)]
    return U(m)
# ---------- wired showpiece ----------
def wire_theater_panel():
    """Electrified Manor glass-front service panel: 60x80x1.6 arched frame, clear-PETG window, 4 Ø6x2 magnet pockets, brass 'gauge' bosses."""
    m=bx(0,0,0,60,80,1.6); m=U([m,bx(-2,-2,0,62,82,1.0)])
    m=D_(m,[arch_cut(40,58,4,30,10,-1) if False else bx(10,10,-1,50,56,3),cyl(40,4,30,56,-1)])
    add=[cyl(9,2.2,30,70,1.5),cyl(6,2,14,70,1.5),cyl(6,2,46,70,1.5)]
    cuts=[cyl(6.2,2.2,x,y,-0.01) for x in (6,54) for y in (6,74)]
    return D_(U([m]+add),cuts)
def edison_sconce():
    """Ornate gooseneck sconce: back plate with filigree, curled arm, cage shade over a 3 mm LED; Ø3.2 wire bore through plate."""
    plate=U([cyl(22,3,0,0,0,'y',sec=8),cyl(14,2,0,-2,0,'y',sec=8)])
    arm=T.creation.torus(10,1.6,major_sections=48,minor_sections=12); arm=T.boolean.intersection([arm,bx(-12,-12,-3,0,12,3)],engine='manifold'); arm=rot(arm,np.pi/2,(1,0,0)); arm=mv(arm,0,10,0)
    cage=D_(cyl(12,14,0,22,-12,sec=8),[cyl(9,16,0,22,-13,sec=8)]+[mv(bx(-8,-1,-10,8,1,-4),0,22,0)])
    cage=U([cage,cone(7,6,sections=24).apply_translation([0,22,1]) or cage])
    return lift(D_(U([plate,arm,cage]),[cyl(LC,40,0,10,0,'y')]))
# ---------- accessories ----------
def four_poster_bed():
    m=[bx(0,0,8,60,80,16),bx(2,2,16,58,78,22),bx(4,62,22,56,76,28)]
    for x,y in ((2,2),(58,2),(2,78),(58,78)): m+= [cyl(4,70 if y>40 else 60,x,y,0),mv(icosphere(1,radius=3.2),x,y,72 if y>40 else 62)]
    m+= [bx(0,76,16,60,80,52),bx(0,0,58,4,80,61),bx(56,0,58,60,80,61)]
    hb=[cyl(14,4,30,78,52,'y')]
    return lift(U(m+hb))
def wingback_chair():
    m=[bx(0,0,8,30,28,16),bx(0,24,16,30,30,52),bx(-2,0,16,4,28,32),bx(26,0,16,32,28,32),bx(-4,20,36,2,30,50),bx(28,20,36,34,30,50)]
    m+= [cyl(3,8,x,y,0) for x in (3,27) for y in (3,26)]
    m+= [cyl(8,28,1,0,30,'y',sec=24),cyl(8,28,29,0,30,'y',sec=24)]
    return lift(U(m))
def grandfather_clock():
    m=[bx(0,0,0,22,14,10),bx(2,1,10,20,13,60),bx(0,0,60,22,14,84),bx(1,-1,84,21,14,92),cyl(16,2,11,-0.5,72,'y'),mv(prism([(0,92),(22,92),(11,100)],14),0,0,0),cyl(3,6,11,7,99)]
    return U(m+[cyl(8,1.6,11,0.2,30,'y'),bx(10.5,-0.5,30,11.5,1,52)])
def chandelier():
    """6-arm candle chandelier, ceiling rose with Ø3.2 feed; 6 cups for 1.8 mm LEDs."""
    m=[cyl(18,3,0,0,40),cyl(3,22,0,0,18),mv(icosphere(2,radius=7),0,0,14),cyl(10,6,0,0,4)]
    for k in range(6):
        a=k*np.pi/3; x,y=22*np.cos(a),22*np.sin(a)
        arm=bx(0,-1.2,10,22,1.2,12.4); m.append(rot(arm,a)); m+= [cyl(6,4,x,y,10),cyl(3,6,x,y,14)]
    return lift(D_(U(m),[cyl(LC,48,0,0,0)]+[cyl(2,5,22*np.cos(k*np.pi/3),22*np.sin(k*np.pi/3),16) for k in range(6)]))
def victorian_lamppost():
    m=[cyl(18,4,0,0,0,sec=8),cyl(10,10,0,0,4,sec=8),cyl(4,110,0,0,12),cyl(8,4,0,0,40),cyl(20,3,0,0,120,sec=6),
       D_(cyl(18,22,0,0,123,sec=6),[cyl(14,22,0,0,124,sec=6)]),mv(cone(12,12,sections=6),0,0,145),mv(icosphere(1,radius=3),0,0,158),bx(-8,-1,112,8,1,114)]
    return D_(U(m+[peg(0,0)]),[cyl(LC,150,0,0,-6)])
def figure(kind='lady'):
    """1:24 (~70 mm) storybook figures: lady in bustle gown, gentleman in top hat, child, inventor w/ goggles, cat."""
    if kind=='cat':
        b=icosphere(2,radius=6); b.apply_scale([1.6,1,1]); return lift(U([mv(b,0,0,6),mv(icosphere(2,radius=4),9,0,12),mv(cone(1.6,3),7.5,-2,15),mv(cone(1.6,3),7.5,2,15),cyl(1.6,14,-9,0,6)]))
    sc={'lady':1,'gent':1.04,'child':0.66,'inventor':0.98}[kind]; parts=[]
    head=mv(icosphere(2,radius=5*sc),0,0,62*sc)
    if kind=='lady':
        skirt=mv(cone(15,36,sections=48),0,0,0); bust=mv(icosphere(2,radius=6),0,-6,26); torso=cyl(10,22,0,0,32)
        parts=[skirt,bust,torso,mv(icosphere(2,radius=4),0,0,68),cyl(24,1.4,0,0,66.5)]  # bun + parasol-brim hat
    else:
        legs=[cyl(4.4*sc,30*sc,x*sc,0,0) for x in (-2.6,2.6)]; torso=cyl(12*sc,26*sc,0,0,30*sc)
        coat=mv(cone(8*sc,20*sc,sections=32),0,0,22*sc); arms=[cyl(3.4*sc,24*sc,x*sc,0,32*sc) for x in (-7.2,7.2)]
        parts=legs+[torso,coat]+arms
        if kind=='gent': parts+= [cyl(10,1.4,0,0,66.5),cyl(7,10,0,0,67)]
        if kind=='inventor': parts+= [cyl(3,12*sc,0,0,62*sc,'x'),cyl(4,2,-2.6,-4.5,62*sc,'y'),cyl(4,2,2.6,-4.5,62*sc,'y'),bx(-6,-6,24,6,-5,46)]
    base=cyl(18*sc+4,2,0,0,-2)
    return lift(U(parts+[head,base]))
def garden_wall(L=S):
    """Low stone garden wall with coping and urn finial posts; pegs on the tile grid."""
    m=[bx(0,0,0,L,10,28),bx(-2,-2,28,L+2,12,32)]
    for x in (0,L-12): m+= [bx(x,-2,0,x+12,12,38),mv(cone(5,8,sections=24),x+6,5,38),mv(icosphere(2,radius=5),x+6,5,48)]
    for x in np.arange(6,L,12): m.append(bx(x,-0.5,9,x+0.8,10.5,10)) 
    return U(m+[peg(x,5) for x in (OFF,L-OFF)])
def grand_stair():
    """Sweeping stair: 12 risers, newel post with ball finial, spindle rail; rises 111.6 (story)."""
    n=12; rise=(HT+10)/n; run=9.5; w=40
    m=[bx(i*run,0,0,(i+1)*run,w,(i+1)*rise) for i in range(n)]+[bx(i*run-1,-1,(i+1)*rise-1.4,(i+1)*run+0.6,w+1,(i+1)*rise) for i in range(n)]
    for i in range(n): m.append(cyl(2.2,34,i*run+run/2,2,(i+1)*rise))
    m.append(cyl(8,50,run/2,2,rise)); m.append(mv(icosphere(2,radius=6),run/2,2,rise+54))
    hand=bx(0,0,0,np.hypot(n*run,n*rise),4,4); hand.apply_transform(R(-np.arctan2(rise,run),[0,1,0])); hand=mv(hand,0,0,rise+34)
    return lift(U(m+[hand,peg(15.875,15.875)]))
PARTS={
 'turret_segment_v2':turret_segment,'turret_cap_v2':turret_cap,'roof_panel_v2':roof_panel,'gable_end_v2':gable_end,'dormer_v2':dormer,
 'porch_post_v2':porch_post,'railing_v2':railing,'gingerbread_trim_v2':gingerbread_trim,'bay_window_v2':bay_window,'chimney_v2':chimney,
 'cupola_v2':cupola,'crenel_parapet_v2':crenel_parapet,'arcade_panel_v2':arcade_panel,'fountain_v2':fountain,'clock_tower_v2':clock_tower,
 'clock_spire_v2':clock_spire,'smokestack_v2':smokestack,'balcony_v2':balcony,'widows_walk_v2':widows_walk,'garden_wall_v2':garden_wall,
 'grand_stair_v2':grand_stair,'wire_theater_panel_v2w':wire_theater_panel,'edison_sconce_v2w':edison_sconce,
 'furn_four_poster_v2':four_poster_bed,'furn_wingback_v2':wingback_chair,'furn_grandfather_clock_v2':grandfather_clock,'fix_chandelier_v2':chandelier,
 'fix_victorian_lamppost_v2':victorian_lamppost,
 'fig_lady_v2':lambda:figure('lady'),'fig_gent_v2':lambda:figure('gent'),'fig_child_v2':lambda:figure('child'),'fig_inventor_v2':lambda:figure('inventor'),'fig_cat_v2':lambda:figure('cat'),
}
if __name__=='__main__':
    import sys; os.makedirs(OUT,exist_ok=True); bad=[]
    for n,f in PARTS.items():
        if len(sys.argv)>1 and n not in sys.argv[1:]: continue
        try:
            m=f(); m=lift(m); ext=m.extents
            ok=m.is_watertight and ext[0]<=330 and ext[1]<=320 and ext[2]<=325
            m.export(os.path.join(OUT,n+'.stl')); print(f"{n:32s} {ext[0]:6.1f}x{ext[1]:6.1f}x{ext[2]:6.1f} wt={m.is_watertight} {'OK' if ok else 'CHECK'}")
            if not ok: bad.append(n)
        except Exception as e: print(n,'ERR',repr(e)[:200]); bad.append(n)
    print('bad:',bad)
