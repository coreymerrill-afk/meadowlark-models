"""Ball-lift module (paddle wheel in guide channel) — modelled in LIFT-LOCAL coords:
axle along +y through origin, wheel plane XZ, wheel turns CCW seen from +y (front)...
NOTE: angle convention matches lift2d.py: angle measured in XZ from +x toward +z."""
import numpy as np, math
from geom import *
import tracks as T
RB=17.5; RH=70.0; RP=105.0; RG=108.0; RGO=113.0; NPAD=6; PT=8.0; PW=5.0   # paddle half-width (y 0..5 per half)
HUB_HALF=19.0; PLATE_IN=21.0; PLATE_T=5.0
GUIDE_A0=-120.0; GUIDE_A1=98.0
EXIT_A=97.0; EXIT_SLOPE=7.0; CHUTE_END_X=-172.0
H_AXLE=136.0
FLOOR_Z=-H_AXLE          # tile top in lift-local z
QR,QA=116.0,185.0; TIPR=98.0; PAWL_PR=4.0
def P_tan():
    a=math.radians(EXIT_A); r=RH+RB; return np.array([r*math.cos(a),r*math.sin(a)])
def chute_center_z(x):
    P=P_tan(); return P[1]+(x-P[0])*math.tan(math.radians(EXIT_SLOPE))
def xz_extrude(poly,y0,y1):
    m=poly_extrude(poly,y1-y0,0).rotate([90,0,0])   # (x,y_poly->z) ; extrude -> -y
    return m.translate([0,y1,0])
def ycyl(r,y0,y1,x=0,z=0,seg=96):
    return xz_extrude(circle_pts(r,seg,x,z),y0,y1)
def annulus_sector(r0,r1,a0,a1,y0,y1,n=160):
    outer=[(r1*math.cos(math.radians(a0+(a1-a0)*i/n)),r1*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]
    inner=[(r0*math.cos(math.radians(a1-(a1-a0)*i/n)),r0*math.sin(math.radians(a1-(a1-a0)*i/n))) for i in range(n+1)]
    return xz_extrude(outer+inner,y0,y1)
def Qpt(): a=math.radians(QA); return np.array([QR*math.cos(a),QR*math.sin(a)])
def u(a): a=math.radians(a); return np.array([math.cos(a),math.sin(a)])
def stop_pt(): return Qpt()+14*u(QA)+9.3*u(QA+90)
# ---------------- wheel half (print frame: split face on bed, axis z) ----------
def wheel_half():
    hub=cyl(RH,HUB_HALF,0,0,0,seg=180)
    bars=[]
    for k in range(NPAD):
        b=box(RH-5,RP,-PT/2,PT/2,0,PW).rotate([0,0,60*k]); bars.append(b)
    w=union([hub]+bars)
    holes=[cyl(10,HUB_HALF+2,38*math.cos(math.radians(30+60*k)),38*math.sin(math.radians(30+60*k)),-1) for k in range(6)]
    bore=poly_extrude(hexagon(16.4,0),HUB_HALF+2,-1)
    w=w-union(holes)-bore
    # 1 mm chamfer on hub rim (print bottom edge) handled by slicer elephant foot comp; keep simple
    return w
def wheel_assembly_transforms(omega_deg):
    """Return 3x4 transforms (print->lift-local) for the +y and -y halves at wheel angle omega (CCW in XZ)."""
    # print frame: wheel plane XY, axis z.  +half: z->+y.  point at XY angle th -> XZ angle -th ; then rotate by omega
    Rp=np.array([[1,0,0],[0,0,1],[0,-1,0]],float)   # (x,y,z)->(x, z, -y)
    def roty_xz(om):  # CCW in XZ plane (x toward z) by om
        c,s=math.cos(math.radians(om)),math.sin(math.radians(om))
        return np.array([[c,0,-s],[0,1,0],[s,0,c]],float)
    Rplus=roty_xz(omega_deg)@Rp
    flip=np.array([[1,0,0],[0,-1,0],[0,0,-1]],float)  # 180 about x
    Rminus=roty_xz(omega_deg)@Rp@flip
    return [np.hstack([Rplus,np.zeros((3,1))]),np.hstack([Rminus,np.zeros((3,1))])]
# ---------------- axle (lift-local, axis along +y toward the child / front) -----
# Inserted from the BACK (-y), tip-first toward +y. Head stays outside the back plate.
# Order -y -> +y: head, jBack, hexW, jFront, hexC, groove, tip.
AX=dict(head=(-32.5,-26.5,16.0),jB=(-26.5,-20.5,11.0),hexW=(-20.5,21.0,16.0),
        jA=(21.0,29.5,8.75),hexC=(29.5,40.6,13.0),groove=(40.6,45.0,4.75),tip=(45.0,49.0,13.0))
def axle():
    parts=[]
    for k in ('head','jA','jB','groove'):
        y0,y1,r=AX[k]; parts.append(ycyl(r,y0,y1))
    for k in ('hexW','hexC','tip'):
        y0,y1,af=AX[k]; parts.append(xz_extrude(hexagon(af,0),y0,y1))
    return union(parts)
# ---------------- crank -------------------------------------------------------
CRANK_R=55.0
def crank(angle_deg=0.0):
    """Crank in lift-local coords at angle 0 (arm along +x). Thickness along +y, outside the front plate."""
    y0,y1=29.5,39.5
    arm=union([xz_extrude(circle_pts(13,64),y0,y1),xz_extrude(circle_pts(13,64,CRANK_R,0),y0,y1),
               xz_extrude([(0,-11),(CRANK_R,-11),(CRANK_R,11),(0,11)],y0,y1)])
    knob=ycyl(11,y1-0.01,78.5,CRANK_R,0)
    knobend=M.sphere(11,48).translate([CRANK_R,78.5,0])
    c=union([arm,knob,knobend])-xz_extrude(hexagon(14.0,0),y0-1,y1+1)
    c=c-box(CRANK_R-12,CRANK_R+12,78.5-0.5,90,-12,12)  # 0.5 mm flat on knob end (print helper)
    if angle_deg:
        c=c.rotate([0,-angle_deg,0])
    return c
def clip():
    """U-clip in its own flat frame (z=thickness)."""
    outer=[(-15,-12),(15,-12),(15,14),(-15,14)]
    body=poly_extrude(outer,4,0)
    slot=poly_extrude([(-4.95,-13),(4.95,-13),(4.95,4.0),(-4.95,4.0)],6,-1)
    seat=cyl(4.95,6,0,4.0,-1)
    throat=poly_extrude([(-4.45,-13),(4.45,-13),(4.45,0),(-4.45,0)],6,-1)
    relief=[poly_extrude([(s*8,-13),(s*9.5,-13),(s*9.5,8),(s*8,8)],6,-1) for s in (1,-1)]
    c=body-union([seat,throat]+relief)
    # finger tab
    tab=poly_extrude([(-8,14),(8,14),(6,22),(-6,22)],4,0)
    c=union([c,tab])
    # throat narrower than groove (8.9 vs 9.5) => snap; widen inner slot to seat
    return c
# ---------------- pawl ------------------------------------------------------------
def pawl(phi_deg=0.0):
    Q=Qpt(); a=math.radians(QA); T0=np.array([TIPR*math.cos(a),TIPR*math.sin(a)])
    def capsule(p0,p1,r):
        return M.hull(union([ycyl(r,-19.5,19.5,p0[0],p0[1],48),ycyl(r,-19.5,19.5,p1[0],p1[1],48)]))
    hub=ycyl(8.5,-19.5,19.5,Q[0],Q[1])
    tip=capsule(Q,T0,PAWL_PR)
    W=Q+22*u(QA); cw=capsule(Q,W,5.0); blob=ycyl(8,-19.5,19.5,W[0],W[1])
    p=union([hub,tip,cw,blob])-ycyl(5.4,-21,21,Q[0],Q[1])
    # rotate CW by phi about Q (CW in XZ = negative CCW)
    return p.translate([-Q[0],0,-Q[1]]).rotate([0,phi_deg,0]).translate([Q[0],0,Q[1]])
# ---------------- exit chute ----------------------------------------------------
def chute_paths():
    P=P_tan(); xs=np.linspace(P[0],CHUTE_END_X,40)
    def pt(x): return (x,0.0,chute_center_z(x)-T.VH)
    inner=[(pt(x),(-1,0)) for x in xs if x>-122.0]+[(pt(-122.0),(-1,0))]
    outer=[(pt(x),(-1,0)) for x in np.linspace(-122.0,CHUTE_END_X,12)]
    return inner,outer
def exit_chute():
    inner,outer=chute_paths()
    b1=sweep([(p,t,[(-21,-5),(21,-5),(21,21),(-21,21)]) for p,t in inner])
    b2=sweep([(p,t,[(-26,-5),(26,-5),(26,31),(-26,31)]) for p,t in outer])
    c=sweep([(p,t,[(0,0),(21,21),(21,60),(-21,60),(-21,21)]) for p,t in T.extend(inner+outer[1:],1.0)])
    ch=union([b1,b2])-c
    # Nest: wipe bulky walls over the last 12 mm. A low keel (below the ball,
    # inside the V) overlaps 4 mm back into the remaining chute so the housing
    # stays one piece. Clearance fit — keel does not eat the track walls.
    lipx=CHUTE_END_X+12.0
    zl=lambda x: chute_center_z(x)-T.VH
    xs_wipe=list(np.linspace(lipx,CHUTE_END_X,8))
    wipe=sweep([((x,0,zl(x)),(-1,0),[(-40,-8),(40,-8),(40,40),(-40,40)]) for x in xs_wipe])
    xs_keel=list(np.linspace(lipx+4.0,CHUTE_END_X,10))
    keel=sweep([((x,0,zl(x)),(-1,0),[(0,1.3),(4.2,5.8),(2.2,5.8),(0,3.5),(-2.2,5.8),(-4.2,5.8)]) for x in xs_keel])
    # Root the keel into the chute floor on the lift side of J0 (not inside the track).
    xs_root=list(np.linspace(lipx+4.0,lipx+0.4,6))
    root=sweep([((x,0,zl(x)),(-1,0),[(0,-3.2),(5,5.8),(-5,5.8)]) for x in xs_root])
    ch=ch-wipe
    ch=union([ch,keel,root])
    # wheel clearances
    ch=ch-ycyl(RH+1.5,-30,30)-(ycyl(RP+2.5,-7,7))
    return ch
def roof():
    P=P_tan(); x0=-30.0; x1=-122.0
    pts=[]
    zc=lambda x: chute_center_z(x)+RB+3.0
    poly=[(x0,zc(x0)),(x1,zc(x1)),(x1,zc(x1)+4),(x0,zc(x0)+4)]
    r=xz_extrude(poly,-21,21)-ycyl(RG+0.5,-30,30)
    return r
# ---------------- housing ---------------------------------------------------------
PLATE_R=122.0
def plate_outline_parts(front=False):
    Q=Qpt(); parts=[circle_pts(PLATE_R,160),circle_pts(28,64,Q[0],Q[1])]
    base=[(-108,FLOOR_Z),(108,FLOOR_Z),(108,-80),(-108,-80)]
    parts.append(base)
    if not front:
        zc=lambda x: chute_center_z(x)-T.VH
        parts.append([(-60,zc(-60)-5),(-122.5,zc(-122.5)-5),(-122.5,zc(-122.5)+31),(-60,zc(-60)+40)])
    return parts
def plate(y0,y1,front=False):
    p=union([xz_extrude(pp,y0,y1) for pp in plate_outline_parts(front)])
    return p
GUIDE_PIN_A=(-60.0,20.0,80.0)
def housing_back():
    pl=plate(-26,-21)
    guide=annulus_sector(RG,RGO,GUIDE_A0,GUIDE_A1,-21.0,21.0)
    pins=[ycyl(4.0,20.9,25.5,110.5*math.cos(math.radians(a)),110.5*math.sin(math.radians(a)),48) for a in GUIDE_PIN_A]
    foot=box(-105,105,-26,21,FLOOR_Z,-100)-ycyl(RGO-0.01,-30,30)
    foot=foot-box(-98,98,-21,21.5,FLOOR_Z+5,-118)
    Q=Qpt(); S=stop_pt()
    ppin=ycyl(5.0,-21.1,24.5,Q[0],Q[1],48); spin=ycyl(4.0,-21.1,24.5,S[0],S[1],48)
    h=union([pl,guide,foot,ppin,spin,exit_chute(),roof()]+pins)
    # teardrop pegs into tile sockets at x=+-80 (point toward -y = print-bed side)
    for x in (-80.0,80.0):
        td=[(9.7*math.cos(math.radians(a)),9.7*math.sin(math.radians(a))) for a in range(-45,226,5)]+[(0,-9.7*math.sqrt(2))]
        td=[(px,max(py,-9.7)) for px,py in td]
        peg=poly_extrude([(x+px,py) for px,py in td],9.5,FLOOR_Z-9.5)   # in XY plane; extrude along z downward
        h=union([h,peg])
    h=h-ycyl(11.4,-30,-20.5)      # journal B hole (passes hexW, seats jBack)
    return h
def housing_front():
    pl=plate(21,26,front=True)
    holes=[ycyl(9.15,20,27)]
    holes+=[ycyl(4.25,20,27,110.5*math.cos(math.radians(a)),110.5*math.sin(math.radians(a)),48) for a in GUIDE_PIN_A]
    Q=Qpt(); S=stop_pt(); holes+=[ycyl(5.25,20,27,Q[0],Q[1],48),ycyl(4.25,20,27,S[0],S[1],48)]
    # viewing slots (6 mm wide) over the rising ball path
    for r in (82.0,96.0):
        for a0,a1 in ((-62,-25),(-19,18),(24,61),(67,92)):
            holes.append(annulus_sector(r-3,r+3,a0,a1,20,27,40))
    # inlet opening + 45deg cam chamfer on +x edge (inner face) to push half-entered balls inward
    zb=inlet_nose_bottom()-0.3; zt=INLET_CZ+RB+4.0
    holes.append(box(-24.5,24.5,20,27,zb,zt))
    wedge=M.hull(union([box(24.4,24.5,25.99,26.0,zb,zt),box(24.4,29.5,20.99,21.0,zb,zt),box(24.4,29.5,20.0,20.01,zb,zt)]))
    holes.append(wedge)
    return pl-union(holes)
INLET_CZ=-(RG-RB)+2.0
def inlet_nose_bottom():
    return INLET_CZ-T.VH-T.BOT
def ball(flat=0.5):
    b=M.sphere(RB,128)
    return b-box(-30,30,-30,30,-30,-RB+flat)
def lift_test_base():
    """Minimal frame for the first lift test: sockets at lift pegs (x=+-80) and the inlet stand (0,80)."""
    fr=union([box(-110,110,-20,20,-12,0),box(-20,20,0,100,-12,0),cyl(17,12,-80,0,-12),cyl(17,12,80,0,-12),cyl(17,12,0,80,-12)])
    for (x,y) in ((-80,0),(80,0),(0,80)): fr=fr-cyl(10.2,10.01,x,y,-10)
    return fr
