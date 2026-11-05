"""Grand kit v3 (1:24, H3C 330x320x325): showpiece ornaments. Same snap system as v0/v2:
Ø5.9 pegs into Ø6.3 sockets on the 31.75 grid, Ø3.2 light bores (LC). Z=0 is the bed.
Stained glass prints as two bodies (lead frame + glass) -> *_lead / *_glass STLs for an H3C tool swap."""
import os, sys, numpy as np, trimesh as T
from trimesh.creation import cone, icosphere
from build_v0 import bx, cyl, U, D_, OUT, LC, SOCK_D, OFF, PITCH, S
from build_grand_v2 import peg, mv, rot, lift, prism, arch_cut, HT
R=T.transformations.rotation_matrix
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
def ext(poly,h,z=0):
    from shapely.validation import make_valid
    poly=make_valid(poly.buffer(0)); geoms=[g for g in getattr(poly,'geoms',[poly]) if g.geom_type=='Polygon' and g.area>0.05]
    ms=[]
    for g in geoms:
        g=g.simplify(0.02)
        if g.is_valid and g.area>0.05: ms.append(T.creation.extrude_polygon(g,h))
    m=T.util.concatenate(ms) if len(ms)>1 else ms[0]
    if len(ms)>1: m=T.boolean.union(ms,engine="manifold")
    m.apply_translation([0,0,z]); return m
def upright(m):  # XY-plane relief -> stand in XZ (face toward -Y), keeps z>=0
    m=m.copy(); m.apply_transform(R(np.pi/2,[1,0,0])); return lift(m)
def arch_poly(w,h,cx=0,y0=0):
    r=w/2; return unary_union([Polygon([(cx-r,y0),(cx+r,y0),(cx+r,y0+h-r),(cx-r,y0+h-r)]),Point(cx,y0+h-r).buffer(r,64)])
def tor(R_,r,z=0,sec=48): m=T.creation.torus(R_,r,major_sections=sec,minor_sections=12); m.apply_translation([0,0,z]); return m
# ---------------------------------------------------------------- stained glass
def sg_pattern(w,h,kind):
    """Lead lines for an arched light: rose / tulip / sunburst. Returns (lead polygon, glass polygon)."""
    outer=arch_poly(w,h); inner=outer.buffer(-1.6)
    lines=[]
    cy_=h-w/2
    if kind=='rose':
        for k in range(8):
            a=k*np.pi/4; lines.append(LineString([(0,cy_),(np.cos(a)*w,cy_+np.sin(a)*w)]).buffer(.45))
        lines+= [Point(0,cy_).buffer(w*.22).boundary.buffer(.5),Point(0,cy_).buffer(w*.4).boundary.buffer(.5)]
        for y in np.arange(4,cy_,h/7): lines.append(Polygon([(-w,y-.5),(w,y-.5),(w,y+.5),(-w,y+.5)]))
        lines.append(Polygon([(-.5,0),(.5,0),(.5,cy_),(-.5,cy_)]))
    elif kind=='tulip':
        lines.append(Polygon([(-.55,0),(.55,0),(.55,h),(-.55,h)]))
        for s in (-1,1):
            for k in range(3): lines.append(Point(s*w*.18,h*.3+k*h*.18).buffer(w*.17).boundary.buffer(.45))
        lines.append(Point(0,cy_).buffer(w*.24).boundary.buffer(.5))
        for y in (h*.15,): lines.append(Polygon([(-w,y-.5),(w,y-.5),(w,y+.5),(-w,y+.5)]))
    else:  # sunburst
        for k in range(1,8):
            a=k*np.pi/8; lines.append(LineString([(0,cy_),(np.cos(a)*w,cy_+np.sin(a)*w)]).buffer(.45))
        lines.append(Point(0,cy_).buffer(w*.18).boundary.buffer(.5))
        for x in (-w/4,w/4): lines.append(Polygon([(x-.5,0),(x+.5,0),(x+.5,cy_),(x-.5,cy_)]))
        for y in np.arange(h*.2,cy_,h*.2): lines.append(Polygon([(-w,y-.5),(w,y-.5),(w,y+.5),(-w,y+.5)]))
    lead=unary_union([outer.difference(inner)]+[l.intersection(outer) for l in lines])
    glass=inner.difference(unary_union(lines)).buffer(-0.05)
    return lead,glass,outer
def stained_insert(w=22,h=44,kind='rose'):
    """Window insert that presses into an arched wall cut: 1.8 lead relief + 1.0 glass (print glass in translucent PETG),
    with a 2 mm friction lip ring. Returns (lead_body, glass_body)."""
    lead,glass,outer=sg_pattern(w,h,kind)
    lip=outer.buffer(1.6).difference(outer.buffer(-0.4))
    L=U([ext(lead,2.4),ext(lip,1.0),ext(outer.difference(outer.buffer(-1.6)),3.2)])
    Gm=ext(glass,1.2,0.4)
    return L,Gm
# ---------------------------------------------------------------- ornaments
def weathervane():
    """Rooster weathervane on a ball-and-spire mast with N/E/S/W letters; pegs into any finial/cupola socket."""
    m=[cyl(10,4,0,0,0),cyl(6,6,0,0,4),mv(icosphere(2,radius=6),0,0,14),cyl(3,70,0,0,18),mv(icosphere(2,radius=4),0,0,56)]
    for a,(L) in zip(range(4),'NESW'):
        arm=rot(bx(0,-1,0,26,1,2),a*np.pi/2); m.append(mv(arm,0,0,44))
        lt={'N':[(0,0),(1.6,0),(1.6,5),(4.4,0),(6,0),(6,8),(4.4,8),(4.4,3),(1.6,8),(0,8)],
            'E':[(0,0),(6,0),(6,1.6),(1.6,1.6),(1.6,3.2),(5,3.2),(5,4.8),(1.6,4.8),(1.6,6.4),(6,6.4),(6,8),(0,8)],
            'S':[(0,0),(6,0),(6,4.8),(1.6,4.8),(1.6,6.4),(6,6.4),(6,8),(0,8),(0,3.2),(4.4,3.2),(4.4,1.6),(0,1.6)],
            'W':[(0,8),(1.4,0),(3,4),(4.6,0),(6,8),(4.6,8),(4.2,4),(3,7),(1.8,4),(1.4,8)]}[L]
        g=upright(ext(Polygon(lt),1.6)); g.apply_translation([-3,0.8,0]); g=rot(g,a*np.pi/2+np.pi/2); c=np.array([np.cos(a*np.pi/2),np.sin(a*np.pi/2)])*26
        m.append(mv(g,c[0],c[1],41))
    rooster=Polygon([(-22,0),(-14,4),(-6,2),(2,4),(8,10),(10,18),(14,20),(16,17),(13,14),(14,8),(18,4),(16,0),(6,-2),(-2,-4),(-10,-2),(-16,4),(-26,14),(-28,8),(-24,2)]).buffer(.3)
    comb=Point(12,21).buffer(2.4); arrow=Polygon([(-36,-6),(30,-6),(30,-4),(36,-5),(30,-7),(30,-6)]).buffer(.9)
    fl=Polygon([(-36,-9),(-30,-5),(-36,-1),(-40,-1),(-35,-5),(-40,-9)])
    body=upright(ext(unary_union([rooster,comb,arrow,fl]),2.0)); body.apply_translation([0,1,0]); m.append(mv(body,0,0,76))
    return lift(D_(U(m+[peg(0,0)]),[cyl(LC,30,0,0,-6)]))
def porte_cochere():
    """Carriage porch: 4 clustered columns, segmental arches, balustraded deck, lantern pockets. 230x120 footprint, pegs on grid."""
    W,Dp,Hc=228,120,92; m=[bx(0,0,Hc,W,Dp,Hc+8),bx(-4,-4,Hc+8,W+4,Dp+4,Hc+11)]
    for x in (10,W-10):
        for y in (10,Dp-10):
            m+= [bx(x-8,y-8,0,x+8,y+8,6),cyl(9,4,x,y,6)]
            for dx,dy in ((-3,-3),(3,-3),(-3,3),(3,3)): m.append(cyl(4.2,Hc-16,x+dx,y+dy,10,sec=20))
            m+= [cyl(14,4,x,y,Hc-6),bx(x-9,y-9,Hc-10,x+9,y+9,Hc-6)]
            for z in (30,58): m.append(tor(6.5,1.1,z))
            m[-1].apply_translation([x,y,0]); m[-2].apply_translation([x,y,0])
    for (x0,x1,y0,y1,ax) in ((10,W-10,0,6,'x'),(10,W-10,Dp-6,Dp,'x'),(0,6,10,Dp-10,'y'),(W-6,W,10,Dp-10,'y')):
        span=(x1-x0) if ax=='x' else (y1-y0); r=span/2/0.9
        if ax=='x':
            a=bx(x0,y0,Hc-28,x1,y1,Hc); c=cyl(2*r,10,(x0+x1)/2,(y0+y1)/2,Hc-28-r*0.75,'y',sec=96)
        else:
            a=bx(x0,y0,Hc-28,x1,y1,Hc); c=cyl(2*r,10,(x0+x1)/2,(y0+y1)/2,Hc-28-r*0.75,'x',sec=96); c=mv(c,0,0,0)
        m.append(D_(a,[c]))
    for x in np.arange(12,W-8,9): m+= [cyl(2.6,16,x,4,Hc+11),cyl(2.6,16,x,Dp-4,Hc+11)]
    for y in np.arange(14,Dp-8,9): m+= [cyl(2.6,16,4,y,Hc+11),cyl(2.6,16,W-4,y,Hc+11)]
    m+= [bx(-4,0,Hc+27,W+4,8,Hc+30),bx(-4,Dp-8,Hc+27,W+4,Dp,Hc+30),bx(0,-4,Hc+27,8,Dp+4,Hc+30),bx(W-8,-4,Hc+27,W,Dp+4,Hc+30)]
    for x in (10,W-10):
        for y in (10,Dp-10): m+= [cyl(10,8,x,y,Hc+30),mv(icosphere(2,radius=5.5),x,y,Hc+43)]
    body=U(m+[peg(x,y) for x in (10,W-10) for y in (10,Dp-10)])
    return D_(body,[cyl(LC,Hc+40,10,10,-1),cyl(8,6,W/2,Dp/2,Hc-1)])
def spiral_stair(h=HT+10,steps=16,R_=40):
    """Cast-iron spiral stair: newel + 16 wedge treads + helical handrail on balusters; spans one story, pegs at base."""
    m=[cyl(10,h,0,0,0,sec=32),cyl(22,4,0,0,0,sec=32),mv(icosphere(2,radius=6),0,0,h+4)]
    rise=h/steps; da=2*np.pi*0.85/steps
    for k in range(steps):
        a0=k*da; pts=[(0,0)]+[(np.cos(a0+t)*R_,np.sin(a0+t)*R_) for t in np.linspace(0,da*1.08,6)]
        tr=ext(Polygon(pts).buffer(.2),2.4,rise*(k+1)-2.4); m.append(tr)
        bxp=np.array([np.cos(a0+da/2),np.sin(a0+da/2)])*(R_-2.5); m.append(cyl(2.2,34,bxp[0],bxp[1],rise*(k+1)))
    for k in range(steps*3):
        t0,t1=k/(steps*3),(k+1)/(steps*3); a0,a1=t0*steps*da+da/2,t1*steps*da+da/2
        p0=np.array([np.cos(a0)*(R_-2.5),np.sin(a0)*(R_-2.5),rise+t0*rise*(steps-1)+34]); p1=np.array([np.cos(a1)*(R_-2.5),np.sin(a1)*(R_-2.5),rise+t1*rise*(steps-1)+34])
        seg=T.creation.cylinder(1.8,np.linalg.norm(p1-p0)+1.2,sections=10,segment=[p0,p1]); m.append(seg)
    return lift(U(m+[peg(0,0)]))
def stained_bay():
    """Two-story-capable canted bay (one story here) with three tall rose-glass lights + transoms, corbel brackets, copper-domed cap.
    Body prints in wall colour; the glass inserts are stained_insert parts."""
    w,d,h=S-24,40,86; a=d
    pts=[(0,0),(a,d),(w-a,d),(w,0)]; pl=Polygon(pts)
    body=D_(ext(pl,h),[ext(Polygon([(4,-3),(a+1,d-4),(w-a-1,d-4),(w-4,-3)]),h+2,6)])
    cuts=[]
    for x0,y0,ang,wid in ((w/2,d,0,26),(a/2,d/2,-np.arctan2(d,a),20),(w-a/2,d/2,np.arctan2(d,a),20)):
        c=arch_cut(wid,52,10,0,0,-5); c=rot(c,ang); cuts.append(mv(c,x0,y0,12))
        t=bx(-wid/2,-5,0,wid/2,5,10); t=rot(t,ang); cuts.append(mv(t,x0,y0,68))
    body=D_(body,cuts)
    frame=[]
    for z in (10,66,80): frame.append(ext(pl.buffer(2,join_style=2).difference(pl.buffer(-3,join_style=2)),2.2,z))
    for x,y in pts[1:3]: frame.append(cyl(4,h,x,y,0,sec=16))
    cap=ext(pl.buffer(6,join_style=2),4,h)
    dome=T.boolean.intersection([mv(icosphere(4,radius=w/2*0.62),w/2,d/2-14,h+4),ext(pl.buffer(4,join_style=2),40,h+4)],engine='manifold')
    cor=[]
    for x in np.linspace(8,w-8,7):
        cor.append(bx(x-3,0,-0.01,x+3,8,8))
    m=U([body,cap,dome]+frame+cor+[peg(x,8) for x in (PITCH/2+8,w-PITCH/2-8)])
    return lift(D_(m,[cyl(LC,h+20,w/2,d-8,0)]))
def door_surround():
    """Ornate entry surround for the 34x72 door: fluted pilasters, sidelights, fanlight sunburst, broken pediment with urn, keystone. Wall-face relief, 8 mm deep."""
    W,Hh=78,118; o=[]
    o.append(Polygon([(0,0),(12,0),(12,84),(0,84)])); o.append(Polygon([(W-12,0),(W,0),(W,84),(W-12,84)]))
    o.append(Polygon([(-4,84),(W+4,84),(W+4,92),(-4,92)]))
    arc=Point(W/2,74).buffer(W/2-6,64).difference(Point(W/2,74).buffer(W/2-12,64)); arc=arc.intersection(Polygon([(-9,74),(W+9,74),(W+9,200),(-9,200)]))
    o.append(arc)
    for k in range(1,10):
        a=k*np.pi/10; o.append(LineString([(W/2,74),(W/2+np.cos(a)*(W/2-8),74+np.sin(a)*(W/2-8))]).buffer(.8))
    o.append(Point(W/2,74).buffer(5))
    for s in (-1,1):
        base=W/2+s*W/2
        o.append(Polygon([(W/2+s*8,108),(base+s*6,96),(base+s*6,92),(W/2+s*8,102)]))
    o.append(Polygon([(W/2-5,104),(W/2+5,104),(W/2+7,112),(W/2+3,116),(W/2-3,116),(W/2-7,112)])); o.append(Point(W/2,119).buffer(3.4))
    o.append(Polygon([(W/2-4,108-34),(W/2+4,108-34),(W/2+3,108-24),(W/2-3,108-24)]))
    rel=ext(unary_union(o),6)
    flutes=[bx(x-0.8,8,6,x+0.8,80,7.8) for x0 in (0,W-12) for x in (x0+3,x0+6,x0+9)]
    caps=[bx(-2,80,0,14,85,9),bx(W-14,80,0,W+2,85,9),bx(-2,0,0,14,6,9),bx(W-14,0,0,W+2,6,9)]
    m=U([rel]+flutes+caps); m=upright(m)
    m=U([m]+[peg(6,-4,0)]); return lift(D_(m,[cyl(LC,40,W/2,-4,70,'y')]))
def garden_gate():
    """Wrought-iron double garden gate with scroll hearts, spear finials, and two stone piers with lantern caps (Ø3.2 bores). 160 wide."""
    W=160; pier=[]
    for x in (0,W-24):
        pier+= [bx(x,0,0,x+24,24,96),bx(x-3,-3,0,x+27,27,10),bx(x-3,-3,96,x+27,27,102),cyl(14,10,x+12,12,102),bx(x+5,5,112,x+19,19,128),cyl(18,4,x+12,12,128),cone(10,16).apply_translation([x+12,12,132]) or None]
    pier=[p for p in pier if p is not None]
    lantern=[mv(cone(10,16),x+12,12,132) for x in (0,W-24)]
    g=[]
    gw=(W-48)/2
    for k in range(2):
        x0=24+k*gw
        g+= [bx(x0,10,6,x0+gw,14,10),bx(x0,10,52,x0+gw,14,56),bx(x0,10,80,x0+gw,14,83)]
        for x in np.arange(x0+5,x0+gw-2,7.4):
            g.append(bx(x-1,10.5,6,x+1,13.5,92+6*np.sin((x-x0)/gw*np.pi)))
            g.append(upright(ext(Polygon([(-2.6,0),(2.6,0),(0,7)]),2)).apply_translation([x,13.5,92+6*np.sin((x-x0)/gw*np.pi)]) or None)
        cx=x0+gw/2
        for s in (-1,1):
            sc=Point(cx+s*8,66).buffer(8,32).boundary.buffer(1.0)
            sc=upright(ext(sc,3)); sc.apply_translation([0,13.5,0]); sc=mv(sc,0,0,58)
            g.append(sc)
    g=[x for x in g if x is not None]
    m=U(pier+lantern+g+[peg(12,12),peg(W-12,12)])
    return D_(m,[cyl(LC,140,12,12,-1),cyl(LC,140,W-12,12,-1)])
def lamppost_cluster():
    """Three-globe Victorian lamppost cluster: fluted post on a plinth, scrolled crossarm, three globes on Ø3.2 bores, peg base. 205 tall."""
    m=[bx(-14,-14,0,14,14,8),cyl(22,10,0,0,8,sec=32),cyl(14,14,0,0,18,sec=32),cyl(8,140,0,0,32,sec=32),cyl(14,6,0,0,90,sec=32),cyl(12,6,0,0,168,sec=32)]
    for k in range(8):
        a=k*np.pi/4; m.append(cyl(1.4,120,np.cos(a)*4,np.sin(a)*4,36,sec=8))
    for a in (0,2*np.pi/3,4*np.pi/3):
        c,s_=np.cos(a),np.sin(a)
        for t in np.linspace(0,1,14)[:-1]:
            p0=np.array([c*t*34,s_*t*34,172+np.sin(t*np.pi)*12]); t2=t+1/13; p1=np.array([c*t2*34,s_*t2*34,172+np.sin(t2*np.pi)*12])
            m.append(T.creation.cylinder(1.8,np.linalg.norm(p1-p0)+1,sections=10,segment=[p0,p1]))
        m+= [cyl(8,4,c*34,s_*34,170),mv(icosphere(3,radius=9),c*34,s_*34,184),cyl(6,4,c*34,s_*34,192),cyl(2.2,6,c*34,s_*34,196)]
    m+= [mv(icosphere(3,radius=10),0,0,196),cyl(6,8,0,0,205),mv(cone(4,10),0,0,213)]
    body=U(m+[peg(0,0)])
    cuts=[cyl(LC,210,0,0,-1)]
    for a in (0,2*np.pi/3,4*np.pi/3): cuts.append(cyl(5,10,np.cos(a)*34,np.sin(a)*34,178))
    return D_(body,cuts+[cyl(6,10,0,0,192)])
def roof_cresting(L=S*2):
    """Ridge cresting: fleur-de-lis + spear iron cresting strip that clips over a Ø6 ridge roll. Prints flat-on-edge."""
    o=[Polygon([(0,0),(L,0),(L,3),(0,3)])]
    for x in np.arange(8,L-4,16):
        o.append(Polygon([(x-.8,3),(x+.8,3),(x+.8,14),(x-.8,14)])); o.append(Polygon([(x-2.4,13),(x+2.4,13),(x,19)]))
    for x in np.arange(16,L-8,32):
        o.append(Point(x,9).buffer(4).boundary.buffer(.7)); o+= [Point(x-3.5,13).buffer(2.2),Point(x+3.5,13).buffer(2.2),Polygon([(x-1.2,9),(x+1.2,9),(x,22)])]
    m=ext(unary_union(o),2.2); m=upright(m)
    clip=[D_(cyl(10,8,x,0,-0.01,'y'),[cyl(6.3,10,x,0,-1.0,'y')]) for x in (OFF,L/2,L-OFF)]
    return lift(U([m]+[mv(c,0,1,-2) for c in clip]))
def mansard_panel(L=S*2,h=96):
    """Mansard slope panel (prints flat): scalloped fish-scale shingles in bands, dormer cut-out option, top/bottom dowel holes. Closes the v2 viewer-only gap."""
    m=bx(0,0,0,L,h,4); tiles=[]
    for r,y in enumerate(np.arange(5,h-6,8)):
        off=0 if r%2 else 5
        for x in np.arange(5+off,L-4,10): tiles.append(cyl(9.4,1.2,x,y,3.99,sec=16))
    band=[bx(0,h-6,3.9,L,h,6),bx(0,0,3.9,L,5,6)]
    m=U([m]+tiles+band); return D_(m,[cyl(SOCK_D,8,x,h-3,3,'y') for x in (OFF,L/2,L-OFF)]+[cyl(SOCK_D,8,x,3,3,'y') for x in (OFF,L-OFF)])
def finial_spire():
    """Tall copper-look spire finial (ball, collar, lancet) for turret caps and gables; LED tip bore."""
    m=[cyl(10,4,0,0,0),cyl(7,8,0,0,4),mv(icosphere(3,radius=7),0,0,18),cyl(9,3,0,0,25),cyl(4,20,0,0,27),mv(icosphere(2,radius=4.5),0,0,48),mv(cone(2.8,22),0,0,52)]
    return lift(D_(U(m+[peg(0,0)]),[cyl(LC,40,0,0,-6)]))
PARTS={'weathervane_v3':weathervane,'porte_cochere_v3':porte_cochere,'spiral_stair_v3':spiral_stair,'stained_bay_v3':stained_bay,
 'door_surround_v3':door_surround,'garden_gate_v3':garden_gate,'lamppost_cluster_v3':lamppost_cluster,'roof_cresting_v3':roof_cresting,
 'mansard_panel_v3':mansard_panel,'finial_spire_v3':finial_spire}
for k in ('rose','tulip','sunburst'):
    PARTS[f'stained_insert_{k}_v3_lead']=(lambda k=k:stained_insert(22,44,k)[0]); PARTS[f'stained_insert_{k}_v3_glass']=(lambda k=k:stained_insert(22,44,k)[1])
PARTS['stained_insert_tall_rose_v3_lead']=lambda:stained_insert(26,52,'rose')[0]; PARTS['stained_insert_tall_rose_v3_glass']=lambda:stained_insert(26,52,'rose')[1]
if __name__=='__main__':
    os.makedirs(OUT,exist_ok=True); bad=[]
    for n,f in PARTS.items():
        if len(sys.argv)>1 and n not in sys.argv[1:]: continue
        try:
            m=f(); m=lift(m); e=m.extents
            ok=m.is_watertight and e[0]<=330 and e[1]<=320 and e[2]<=325 and m.volume>0
            m.export(os.path.join(OUT,n+'.stl')); print(f"{n:34s} {e[0]:6.1f}x{e[1]:6.1f}x{e[2]:6.1f} wt={m.is_watertight} vol={m.volume:8.0f} {'OK' if ok else 'CHECK'}",flush=True)
            if not ok: bad.append(n)
        except Exception as ex: import traceback; print(n,'ERR',repr(ex)[:300],flush=True); bad.append(n)
    print('bad:',bad)
