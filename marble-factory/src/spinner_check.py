import spinner2d as S, math, json, numpy as np
def run_phase(n,H,rh,Rp,phase,t=6.0,R=17.5,dx=0.1):
    axis=np.array([0.0,H]); phi=math.radians(phase); x=-75.0; arm=[]; rot=0
    def gap(x,phi):
        c=np.array([x,0.0]); best=(np.hypot(*(c-axis))-rh-R,None)
        for k in range(n):
            a=phi+2*math.pi*k/n; d=np.array([math.sin(a),-math.cos(a)])
            p0=axis+d*rh; p1=axis+d*Rp; ab=p1-p0; s=np.clip((c-p0)@ab/(ab@ab),0,1); q=p0+ab*s
            g=np.hypot(*(c-q))-R-t/2
            if g<best[0]: best=(g,q)
        return best
    while gap(x,phi)[0]<0: x-=1
    while x<75:
        x+=dx; g,q=gap(x,phi)
        if g<0:
            c=np.array([x,0.0]); nrm=(q-c)/np.hypot(*(q-c)); rr=q-axis; tau=rr[0]*nrm[1]-rr[1]*nrm[0]
            arm.append(abs(tau)); sg=1 if tau>0 else -1; k=0
            if abs(tau)<0.0: return dict(ok=False,phase=phase,x=round(x,1),why='stall: push through axle')
            while g<0 and k<20000: phi+=sg*math.radians(0.02); rot+=0.02; g,q=gap(x,phi); k+=1
            if k>=20000: return dict(ok=False,phase=phase,why='blocked')
    return dict(ok=True,phase=phase,min_arm=round(min(arm),2) if arm else None,rot=round(rot,1))
if __name__=='__main__':
    n,H,rh,Rp=4,36.0,10.0,30.0
    res=[run_phase(n,H,rh,Rp,ph) for ph in range(0,90,1)]
    print(json.dumps(res))
    print('all ok',all(r['ok'] for r in res),'min arm',min(r.get('min_arm') or 99 for r in res))
