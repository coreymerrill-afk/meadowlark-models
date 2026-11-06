"""2D check of the gravity anti-reverse pawl against the 6 paddle bars.
Pawl: full-width lever pivoting on pin Q; tip arm (capsule Q->T, radius PR) points inward toward
wheel; counterweight arm points outward. Stop post prevents rotation of the tip arm past rest (CCW).
Forward (CCW wheel) must push pawl CW out of the way every paddle; reverse must drive pawl into stop."""
import numpy as np, math
W=dict(RH=70.0,RP=105.0,PT=8.0,NPAD=6)
PW=dict(QR=116.0,QA=185.0,TIPR=98.0,PR=4.0,CW_LEN=22.0)
def segdist(a,b,c,d):
    # min distance between segments ab and cd (sampled exact enough)
    def pt(p,a,b):
        ab=b-a; t=np.clip((p-a)@ab/(ab@ab),0,1); return a+ab*t
    best=1e9; pair=None
    for s in np.linspace(0,1,41):
        p=a+(b-a)*s; q=pt(p,c,d); dd=np.hypot(*(p-q))
        if dd<best: best=dd; pair=(p,q)
    for s in np.linspace(0,1,41):
        p=c+(d-c)*s; q=pt(p,a,b); dd=np.hypot(*(p-q))
        if dd<best: best=dd; pair=(q,p)
    return best,pair
def geom(pw):
    a=math.radians(pw['QA']); Q=np.array([pw['QR']*math.cos(a),pw['QR']*math.sin(a)])
    T0=np.array([pw['TIPR']*math.cos(a),pw['TIPR']*math.sin(a)])
    return Q,T0
def rot(v,ang):
    c,s=math.cos(ang),math.sin(ang); return np.array([c*v[0]-s*v[1],s*v[0]+c*v[1]])
def pawl_tip(pw,phi):  # phi = CW rotation from rest (>=0), radians
    Q,T0=geom(pw); return Q, Q+rot(T0-Q,-phi)
def clear(w,pw,phi,wp=W):
    Q,T=pawl_tip(pw,phi); best=(1e9,None,None)
    for k in range(wp['NPAD']):
        th=math.radians(w+360.0/wp['NPAD']*k); d=np.array([math.cos(th),math.sin(th)])
        dd,pair=segdist(Q,T,d*wp['RH'],d*wp['RP'])
        g=dd-pw['PR']-wp['PT']/2
        if g<best[0]: best=(g,k,pair)
    return best
def simulate(direction=+1,dw=0.25,span=200,pw=PW,wp=W):
    phi=0.0; w=0.0; maxphi=0; log=[]; locked=None
    for i in range(int(span/dw)):
        w+=direction*dw
        g,k,pair=clear(w,pw,phi,wp)
        if g<0:
            # contact: torque direction from paddle push (paddle velocity at contact)
            p,q=pair; th=math.atan2(q[1],q[0]); v=np.array([-math.sin(th),math.cos(th)])*direction
            Q,_=pawl_tip(pw,phi); r=p-Q; tau=r[0]*v[1]-r[1]*v[0]   # + = CCW (into stop)
            if tau>0 and phi<=1e-6: locked=w; break
            # pushed CW: rotate until clear
            n=0
            while g<0 and n<4000: phi+=math.radians(0.05); g,k,pair=clear(w,pw,phi,wp); n+=1
            if n>=4000: locked=w; break
        else:
            # gravity returns toward rest (CCW) as far as clear
            while phi>0:
                nphi=max(0,phi-math.radians(0.5)); g2,_,_=clear(w,pw,nphi,wp)
                if g2<0: break
                phi=nphi
        maxphi=max(maxphi,phi); log.append((round(w,2),round(math.degrees(phi),2)))
    return dict(locked_at=locked,max_rot_deg=round(math.degrees(maxphi),1),steps=len(log),log=log)
if __name__=='__main__':
    f=simulate(+1); r=simulate(-1)
    print('forward locked:',f['locked_at'],'max pawl rotation',f['max_rot_deg'])
    print('reverse locked at wheel angle',r['locked_at'])
    Q,T=geom(PW); print('Q',Q,'T',T)
