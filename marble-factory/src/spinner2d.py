"""2D passability check: ball (R=17.5) rolling along z=0 (ball-centre frame) pushes an overhead
paddle rotor (axis at (0,H)). Rotor turns only as pushed (worst case: no coasting).
Reports the minimum lever arm of the contact normal about the axle (stall risk if small)."""
import numpy as np, math
def run(n=4,H=32.0,rh=11.0,Rp=27.0,t=6.0,R=17.5,dx=0.1):
    phi=math.radians(180.0/n)/2   # start: a paddle hanging partially down ahead
    # set a paddle exactly pointing down-ish behind/ahead: phi measured from straight down, CW positive = forward (+x at bottom)
    x=-70.0; armmin=1e9; rot=0.0; contacts=0; maxpen=0
    axis=np.array([0.0,H])
    def gap(x,phi):
        c=np.array([x,0.0]); best=(1e9,None)
        # hub
        g=np.hypot(*(c-axis))-rh-R
        best=(g,None)
        for k in range(n):
            a=phi+2*math.pi*k/n; d=np.array([math.sin(a),-math.cos(a)])
            p0=axis+d*rh; p1=axis+d*Rp
            ab=p1-p0; s=np.clip((c-p0)@ab/(ab@ab),0,1); q=p0+ab*s
            gg=np.hypot(*(c-q))-R-t/2
            if gg<best[0]: best=(gg,q)
        return best
    if gap(x,phi)[0]<0: return None
    hub_clear=H-rh-R
    while x<70:
        x+=dx; g,q=gap(x,phi)
        if g<0:
            if q is None: return dict(ok=False,why='hub hit')
            contacts+=1
            c=np.array([x,0.0]); nrm=(q-c)/np.hypot(*(q-c))   # push direction on paddle
            rr=q-axis; tau=rr[0]*nrm[1]-rr[1]*nrm[0]          # CCW positive
            # forward rotation at bottom moving +x is CCW about axis when viewed with x right z up
            arm=abs(tau)
            if tau<=0: return dict(ok=False,why='push gives reverse torque',x=x)
            armmin=min(armmin,arm)
            k=0
            while g<0 and k<20000: phi+=math.radians(0.02); rot+=0.02; g,q=gap(x,phi); k+=1
            if k>=20000: return dict(ok=False,why='cannot resolve',x=x)
    return dict(ok=True,min_lever_mm=round(armmin,2),rotor_turn_deg=round(rot,1),hub_clear=hub_clear,contact_steps=contacts)
if __name__=='__main__':
    best=[]
    for n in (3,4,5,6):
        for H in (30,32,34,36):
            for Rp in (24,27,30,33):
                for rh in (8,10):
                    r=run(n,H,rh,Rp)
                    if r and r.get('ok') and H-rh-17.5>=1.5:
                        dip=17.5-(H-Rp); best.append((r['min_lever_mm'],n,H,Rp,rh,round(dip,1),r['rotor_turn_deg']))
    best.sort(reverse=True)
    for b in best[:15]: print(b)
