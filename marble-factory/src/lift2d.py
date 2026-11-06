"""Quasi-static 2D simulation of the paddle-wheel ball lift in the wheel plane.
Ball is a disk (R=17.5) whose centre must satisfy all contact constraints; at each
wheel step it settles to the lowest reachable position (gravity) via projected descent.
Returns pickup/retention/release evidence. Axle at origin, wheel turns CCW (angle increasing)."""
import numpy as np, json, math, sys
P = dict(RB=17.5, RH=70.0, RP=105.0, RG=108.0, NPAD=6, PT=8.0,  # paddle tangential thickness
         GUIDE_A0=-120.0, GUIDE_A1=None, EXIT_A=97.0, EXIT_SLOPE=7.0, CHUTE_X_END=-175.0)
def setup(p):
    p=dict(p)
    a=math.radians(p['EXIT_A']); rc=p['RH']+p['RB']
    p['XP']=rc*math.cos(a); p['ZP']=rc*math.sin(a)
    if p['GUIDE_A1'] is None: p['GUIDE_A1']=p['EXIT_A']+1.0
    return p
def chute_z(p,x):  # ball-centre line of exit chute (descending to -x)
    return p['ZP']+(x-p['XP'])*math.tan(math.radians(p['EXIT_SLOPE']))
def project(p,c,w):
    RB=p['RB']; viol=0.0
    for _ in range(60):
        moved=False
        r=np.hypot(*c); ang=math.degrees(math.atan2(c[1],c[0]))
        # hub
        if r<p['RH']+RB: c=c/r*(p['RH']+RB); moved=True; viol=max(viol,p['RH']+RB-r)
        # guide (outer wall) on rising side and over top up to exit
        if p['GUIDE_A0']<=ang<=p['GUIDE_A1'] and r>p['RG']-RB:
            c=c/r*(p['RG']-RB); moved=True
        # chute floor (left of tangent point)
        if c[0]<=p['XP'] and c[1]<chute_z(p,c[0]):
            c=np.array([c[0],chute_z(p,c[0])]); moved=True
        # paddles (capsules)
        for k in range(p['NPAD']):
            th=math.radians(w+360.0/p['NPAD']*k); d=np.array([math.cos(th),math.sin(th)])
            t=np.clip(c@d,p['RH'],p['RP']); q=d*t; v=c-q; dist=np.hypot(*v); need=RB+p['PT']/2
            if dist<need-1e-9:
                if dist<1e-9: v=np.array([-d[1],d[0]]); dist=1
                c=q+v/dist*need; moved=True
        if not moved: break
    return c
def settle(p,c,w,iters=400,step=0.4):
    for _ in range(iters):
        n=project(p,c+np.array([0,-step]),w)
        # allow sliding: try descent along small tangent options
        best=n
        if best[1]>c[1]-1e-4:
            for dx in (-step,step):
                m=project(p,c+np.array([dx,-step*0.2]),w)
                if m[1]<best[1]-1e-4: best=m
        if best[1]>=c[1]-1e-5: break
        c=best
    return c
def run(p,w0=None,dw=0.5,turns=1.2):
    p=setup(p)
    # start: ball dropped into sump at bottom, between paddles (paddle trailing just left)
    c=np.array([0.0,-(p['RG']-p['RB'])])
    w=-90-25 if w0 is None else w0   # paddle 25 deg behind ball
    c=settle(p,project(p,c,w),w)
    log=[]; released=None; minpad=1e9
    for i in range(int(360*turns/dw)):
        w+=dw; c=project(p,c,w); c=settle(p,c,w)
        ang=math.degrees(math.atan2(c[1],c[0])); r=float(np.hypot(*c))
        log.append([round(w,2),round(c[0],2),round(c[1],2),round(ang,1),round(r,2)])
        if released is None and c[0]<p['XP']-40 : released=w
        if c[0]<p['CHUTE_X_END']: break
    return p,log,released
if __name__=='__main__':
    p,log,rel=run(P)
    print('released at wheel angle',rel,'final',log[-1], 'n',len(log))
    zs=[l[2] for l in log]; print('min z',min(zs),'max z',max(zs))
    for l in log[::20]: print(l)

def full_eval(p0, iters=5000, dw=0.5):
    """Return per-step log with contacts and pinch margin (gap to second-nearest obstacle)."""
    p=setup(p0); c=np.array([0.0,-(p['RG']-p['RB'])]); w=-115.0
    c=settle(p,project(p,c,w),w,iters); out=[]; rel=None
    for i in range(int(400/dw)):
        w+=dw; c=project(p,c,w); c=settle(p,c,w,iters)
        gaps=[]
        for k in range(p['NPAD']):
            th=math.radians(w+360.0/p['NPAD']*k); d=np.array([math.cos(th),math.sin(th)])
            t=np.clip(c@d,p['RH'],p['RP']); gaps.append(float(np.hypot(*(c-d*t))-p['RB']-p['PT']/2))
        gaps.sort()
        r=float(np.hypot(*c))
        out.append(dict(w=round(w,2),x=round(float(c[0]),2),z=round(float(c[1]),2),r=round(r,2),
                        g1=round(gaps[0],2),g2=round(gaps[1],2)))
        if rel is None and r>p['RP']+p['RB']+p['PT']/2+1: rel=w
        if c[0]<p['CHUTE_X_END']: break
    return p,out,rel
