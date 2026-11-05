// Grand dollhouse kit v2 — procedural storybook explorer (Three r149). Units mm, 1:24. x right, z toward viewer, y up.
(function(){
const T=127,H=101.6,F=10,LV=H+F;
const el=document.getElementById('view');
if(!window.THREE){el.insertAdjacentHTML('afterbegin','<p style="padding:1rem" class="muted">3D viewer could not load.</p>');}
const V3=(x,y,z)=>new THREE.Vector3(x,y,z);
const MC={};function mat(c,o={}){const k=c+JSON.stringify(o);if(!MC[k])MC[k]=new THREE.MeshStandardMaterial(Object.assign({color:c,roughness:.75,metalness:0},o));return MC[k];}
const GLOW=[];function glass(c=0xffd58a){const m=new THREE.MeshStandardMaterial({color:0x3a2c1e,emissive:c,emissiveIntensity:.35,roughness:.2,metalness:.1});GLOW.push(m);return m;}
function bx(w,h,d,c,x=0,y=0,z=0,m){const o=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m||mat(c));o.position.set(x,y,z);return o;}
function cy(rt,rb,h,c,x=0,y=0,z=0,seg=20,m){const o=new THREE.Mesh(new THREE.CylinderGeometry(rt,rb,h,seg),m||mat(c));o.position.set(x,y,z);return o;}
function sp(r,c,x=0,y=0,z=0,m){const o=new THREE.Mesh(new THREE.SphereGeometry(r,16,12),m||mat(c));o.position.set(x,y,z);return o;}
function cone(r,h,c,x=0,y=0,z=0,seg=24,m){const o=new THREE.Mesh(new THREE.ConeGeometry(r,h,seg),m||mat(c));o.position.set(x,y,z);return o;}
function tor(R,r,c,x,y,z,arc=Math.PI*2,m){const o=new THREE.Mesh(new THREE.TorusGeometry(R,r,8,24,arc),m||mat(c));o.position.set(x,y,z);return o;}
function G(...ch){const g=new THREE.Group();ch.forEach(c=>c&&g.add(c));return g;}
function at(g,x,y,z,ry=0){g.position.set(x,y,z);g.rotation.y=ry;return g;}
function tubeM(a,b,col,r){const v=V3().subVectors(b,a),len=v.length();const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,len,8),new THREE.MeshBasicMaterial({color:col}));
  m.quaternion.setFromUnitVectors(V3(0,1,0),v.clone().normalize());m.position.copy(a).add(b).multiplyScalar(.5);return m;}
function finial(c,y=0){return G(cy(1.5,1.5,14,c,0,y+7),sp(3.2,c,0,y+16),cone(2,7,c,0,y+22));}
// ---------- components (all return Groups in local frame) ----------
// window on a wall face (local: face plane z=0, outward +z). kind: arch|rect|round|lancet
function windowM(P,w=22,h=40,kind='arch'){const g=G();const gl=glass();
  g.add(bx(w,h-(kind=='rect'?0:w/2),1.5,0,0,0,1,gl));
  if(kind!='rect'){const a=new THREE.Mesh(new THREE.CylinderGeometry(w/2,w/2,1.5,20,1,false,0,Math.PI),gl);a.rotation.x=Math.PI/2;a.rotation.z=Math.PI/2;a.rotation.y=0;a.position.set(0,(h-w/2)/2,1);a.rotation.set(Math.PI/2,0,Math.PI/2);g.add(a);
    const ar=tor(w/2+1.5,1.6,P.trim,0,(h-w/2)/2,2,Math.PI);g.add(ar);g.add(bx(4,5,3,P.trim,0,(h-w/2)/2+w/2+1.5,2.2));}
  g.add(bx(w+3,2.4,3,P.trim,0,-(h-(kind=='rect'?0:w/2))/2-1,2),bx(w+8,3,6,P.trim,0,-(h-(kind=='rect'?0:w/2))/2-3,3));
  g.add(bx(1.6,h-(kind=='rect'?0:w/2),2.2,P.trim,0,0,1.8),bx(w,1.4,2.2,P.trim,0,4,1.8));
  g.add(bx(2,h-(kind=='rect'?0:w/2),2,P.trim,-w/2-1,0,1.6),bx(2,h-(kind=='rect'?0:w/2),2,P.trim,w/2+1,0,1.6));
  if(P.shutter){g.add(bx(w*.45,h*.8,1.5,P.shutter,-w*.8,-h*.06,1.3),bx(w*.45,h*.8,1.5,P.shutter,w*.8,-h*.06,1.3));}
  if(P.flowers){const yb=-(h-(kind=='rect'?0:w/2))/2-8;g.add(bx(w+6,6,7,P.shutter||P.trim,0,yb,4));[0xf472b6,0xfacc15,0xf87171,0xc084fc,0xfb7185].forEach((c,k)=>g.add(sp(2.4,c,-w/2+2+k*(w-4)/4,yb+4,5)));}
  return g;}
function doorM(P,w=34,h=72){const g=G(bx(w,h-w/2,2,P.door||0x5b3a24,0,(h-w/2)/2,1));
  const t=new THREE.Mesh(new THREE.CylinderGeometry(w/2,w/2,2,20,1,false,0,Math.PI),glass(0xffc46b));t.rotation.set(Math.PI/2,0,Math.PI/2);t.position.set(0,h-w/2,1);g.add(t);
  g.add(tor(w/2+2,2,P.trim,0,h-w/2,2.5,Math.PI),bx(3,h-w/2,3,P.trim,-w/2-1.5,(h-w/2)/2,2),bx(3,h-w/2,3,P.trim,w/2+1.5,(h-w/2)/2,2),sp(1.6,0xd4a017,w/3,h*.4,3));
  g.add(bx(w+14,3,14,P.stone||0x9a9086,0,1.5,7),bx(w+8,3,9,P.stone||0x9a9086,0,4.5,5));return g;}
// room box: footprint w×d centred at x,z; openings: {S:[...],N:[..],E:[..],W:[..]} items 'w','d','b'(blank gap), plus opts
function room(P,o){const {w,d,h=H}=o;const g=G();const wc=o.c||P.wall;
  g.add(bx(w+4,F,d+4,P.floor||0xc9b79c,0,F/2,0));
  const sides={S:[w,0,d/2,0],N:[w,0,-d/2,Math.PI],E:[d,w/2,0,Math.PI/2],W:[d,-w/2,0,-Math.PI/2]};
  for(const s in sides){const[L,x,z,r]=sides[s];if(o.open&&o.open.includes(s))continue;const f=G(bx(L,h,6,wc,0,F+h/2,-3));
    // siding courses
    if(P.siding)for(let y=F+8;y<F+h-4;y+=7)f.add(bx(L+.2,1,6.6,P.siding,0,y,-3));
    if(P.brick)for(let y=F+6;y<F+h-4;y+=9)f.add(bx(L+.2,.8,6.5,P.brick,0,y,-3));
    f.add(bx(L+6,6,9,P.trim,0,F+h-2,-3),bx(L+4,8,8,P.base||P.trim,0,F+4,-3));
    const ops=(o.ops&&o.ops[s])||[];const n=ops.length;ops.forEach((t,k)=>{const px=-L/2+L*(k+.5)/n;
      if(t=='w')f.add(at(windowM(P,o.ww||22,o.wh||44,o.wk||'arch'),px,F+h*.55,0));
      if(t=='W')f.add(at(windowM(P,30,58,'arch'),px,F+h*.52,0));
      if(t=='r')f.add(at(windowM(P,26,26,'rect'),px,F+h*.58,0));
      if(t=='d')f.add(at(doorM(P),px,F,0));
      if(t=='D')f.add(at(doorM(P,56,88),px,F,0));});
    at(f,x,0,z,r);g.add(f);}
  // corner quoins
  if(P.quoin)for(const[sx,sz]of[[-1,-1],[1,-1],[-1,1],[1,1]])for(let y=F+4,k=0;y<F+h-8;y+=12,k++)g.add(bx(k%2?10:14,6,k%2?14:10,P.quoin,sx*(w/2+1),y,sz*(d/2+1)));
  return g;}
// gable roof: ridge along x, span d; pitch deg
function gable(P,{w,d,pitch=45,over=10,c,ends=true,lace=true}){const g=G();c=c||P.roof;const a=pitch*Math.PI/180,rise=Math.tan(a)*d/2,sl=(d/2+over)/Math.cos(a);
  for(const s of[1,-1]){const pl=G(bx(w+over*2,4,sl,c,0,0,0));
    for(let k=1;k<sl/8;k++)pl.add(bx(w+over*2,1.4,1.6,P.roof2||0x000000,0,2.6,-sl/2+k*8));
    pl.rotation.x=s*a;pl.position.set(0,rise/2-over*Math.tan(a)/2+2,s*(d/4-over/2+over/2));
    const mid=(d/2+over)/2-over;pl.position.set(0,rise-(d/2+over)/2*Math.tan(a)+2*Math.cos(a),s*((d/2+over)/2-over/1e9)*1-s*over/2+s*over/2);
    pl.position.set(0,rise-((d/2+over)/2)*Math.tan(a)+2,s*((d/2+over)/2));g.add(pl);}
  if(ends){const sh=new THREE.Shape();sh.moveTo(-d/2,0);sh.lineTo(d/2,0);sh.lineTo(0,rise);sh.closePath();
    for(const sx of[-1,1]){const m=new THREE.Mesh(new THREE.ExtrudeGeometry(sh,{depth:5,bevelEnabled:false}),mat(P.gable||P.wall));m.rotation.y=Math.PI/2;m.position.set(sx*w/2-(sx>0?5:0),0,0);g.add(m);
      const ow=at(windowM(P,18,18,'rect'),0,0,0);const rw=G(cy(11,11,2,P.trim),cy(8,8,2.4,0,0,0,0,20,glass()));rw.children.forEach(cc=>cc.rotation.x=Math.PI/2);at(rw,sx*(w/2+1),rise*.42,0,0);rw.rotation.y=Math.PI/2;g.add(rw);
      if(lace)for(let k=1;k<10;k++){const t=k/10;for(const sz of[-1,1])g.add(sp(2.6,P.lace||P.trim,sx*(w/2+over*.6),rise*t-2,sz*(d/2)*(1-t)));}
      g.add(at(finial(P.metal||0xd4a017),sx*(w/2+over*.6),rise,0));}}
  g.add(cy(3,3,w+over*2,P.roof2||0x2b2b2b,0,rise+3,0,8).rotateZ(Math.PI/2));
  for(let x=-w/2;x<=w/2;x+=w/4)g.add(sp(2.5,P.metal||0xd4a017,x,rise+6,0));
  g.userData.rise=rise;return g;}
function hip(P,{w,d,h=50,c,over=10}){const g=G();const m=new THREE.Mesh(new THREE.CylinderGeometry(0,Math.SQRT1_2,1,4,1).rotateY(Math.PI/4),mat(c||P.roof));m.scale.set(w+over*2,h,d+over*2);m.position.y=h/2;
  const gg=G(m);gg.add(bx(w+over*2+2,4,d+over*2+2,P.trim,0,1,0));return G(gg);}
function mansard(P,{w,d,h=60,c}){const g=G();const m=new THREE.Mesh(new THREE.CylinderGeometry(Math.SQRT1_2*.72,Math.SQRT1_2,1,4,1).rotateY(Math.PI/4),mat(c||P.roof));m.scale.set(w+16,h,d+16);m.position.y=h/2;g.add(m,bx(w+18,4,d+18,P.trim,0,1,0),bx((w+16)*.72,4,(d+16)*.72,P.trim,0,h,0));
  for(let x=-w/2+12;x<=w/2-10;x+=w/8)g.add(bx(1.5,h,(d+16)*0.86,P.roof2||0x222,x,h/2,0));return g;}
function turret(P,{r=40,h=H*1.6,cap='cone',capH,c,win=4,levels=1}){const g=G();c=c||P.wall;
  g.add(cy(r,r,h,c,0,h/2,0,36));g.add(cy(r+3,r+3,8,P.base||P.trim,0,4,0,36));
  for(let L=0;L<levels;L++){const y0=L*h/levels;g.add(tor(r+1.5,2,P.trim,0,y0+h/levels-4,0).rotateX(Math.PI/2));
    for(let k=0;k<win;k++){const a=k/win*Math.PI*2+Math.PI/win*(L%2);const wm=windowM(P,16,34,'arch');wm.position.set(Math.sin(a)*r,y0+h/levels*.55,Math.cos(a)*r);wm.rotation.y=a;g.add(wm);}}
  if(P.brick)for(let y=10;y<h;y+=9)g.add(tor(r+.3,.5,P.brick,0,y,0).rotateX(Math.PI/2));
  if(cap=='cone'){capH=capH||r*2.8;g.add(cy(r+8,r+8,4,P.trim,0,h+2,0,36));const cn=cone(r+7,capH,P.roof,0,h+4+capH/2,0,36);g.add(cn);
    for(let k=1;k<5;k++)g.add(tor((r+7)*(1-k/5)+.5,1.3,P.roof2||0x222,0,h+4+capH*k/5,0).rotateX(Math.PI/2));
    g.add(at(finial(P.metal||0xd4a017),0,h+4+capH-2,0));}
  if(cap=='cren'){g.add(cy(r+5,r+5,8,P.trim,0,h+4,0,36));for(let k=0;k<12;k++){const a=k/12*Math.PI*2;g.add(at(G(bx(10,14,6,c,0,0,0)),Math.sin(a)*(r+2),h+15,Math.cos(a)*(r+2),a));}}
  if(cap=='onion'){g.add(cy(r+6,r+6,4,P.trim,0,h+2,0,36));const o=sp(r*.95,P.roof,0,h+r*.75,0);o.scale.y=1.25;g.add(o,cone(r*.35,r*1.1,P.roof,0,h+r*2.2,0),at(finial(P.metal||0xd4a017),0,h+r*2.6,0));}
  if(cap=='cren'||cap=='terrace'){}
  return g;}
function porch(P,{w,d=60,h=88,posts,roof='shed',c}){const g=G();const n=posts||Math.max(2,Math.round(w/45)+1);
  g.add(bx(w,8,d,P.deck||0x8b6b4a,0,4,d/2),bx(w+4,3,d+4,P.trim,0,9,d/2));
  for(let k=0;k<n;k++){const x=-w/2+6+(w-12)*k/(n-1);g.add(cy(3.2,3.2,h,P.post||P.trim,x,8+h/2,d-6,12),cy(5,5,8,P.post||P.trim,x,12,d-6,12),cy(5.5,4,6,P.post||P.trim,x,8+h-3,d-6,12));
    for(const y of[30,60])g.add(tor(3.8,1,P.post||P.trim,x,y,d-6).rotateX(Math.PI/2));
    if(k<n-1){const x2=-w/2+6+(w-12)*(k+1)/(n-1),mx=(x+x2)/2,sp_=x2-x;
      g.add(tor(sp_/2-3,1.6,P.lace||P.trim,mx,8+h-10,d-6,Math.PI));
      for(let s=1;s<7;s++)g.add(sp(1.6,P.lace||P.trim,x+sp_*s/7,8+h-4,d-6));
      if(k!=Math.floor((n-1)/2)){g.add(bx(sp_,3,4,P.trim,mx,8+32,d-6),bx(sp_,2,3,P.trim,mx,8+6,d-6));for(let s=1;s<sp_/7;s++)g.add(cy(1.2,1.2,26,P.trim,x+s*7,8+19,d-6,6));}}}
  if(roof=='shed'){const r=bx(w+14,4,d+12,P.roof,0,8+h+10,d/2);r.rotation.x=.28;g.add(r,bx(w+8,6,4,P.trim,0,8+h+1,d-4));}
  if(roof=='flat'){g.add(bx(w+10,6,d+10,P.trim,0,8+h+3,d/2));for(let x=-w/2;x<=w/2;x+=8)g.add(cy(1.4,1.4,16,P.trim,x,8+h+14,d+2,6));g.add(bx(w+10,3,4,P.trim,0,8+h+22,d+2));}
  if(roof=='gable'){const gr=gable(P,{w:d+10,d:w,pitch:35,over:6});gr.rotation.y=Math.PI/2;gr.position.set(0,8+h,d/2);g.add(gr);}
  return g;}
function dormer(P,{c}={}){const g=G(bx(40,40,36,c||P.wall,0,20,0));g.add(at(windowM(P,18,30,'arch'),0,22,18));const gr=gable(P,{w:36,d:44,pitch:48,over:4,lace:false});gr.rotation.y=Math.PI/2;gr.position.y=40;g.add(gr);return g;}
function chimney(P,{h=120,c}={}){c=c||P.chim||0x9b4a3a;const g=G(bx(30,h,24,c,0,h/2,0));for(let y=6;y<h;y+=7)g.add(bx(30.6,.8,24.6,0x5b2a22,0,y,0));
  g.add(bx(36,5,30,c,0,h-12,0),bx(38,4,32,c,0,h-3,0));for(const x of[-7,7])g.add(cy(5,6,14,0xb4673d,x,h+7,0,12),cy(6.5,6.5,3,0xb4673d,x,h+14,0,12));
  const e=sp(3,0,0,h+15,0,new THREE.MeshBasicMaterial({color:0xff7a3d}));g.add(e);return g;}
function bay(P,{r=46,h=H*0.86,c,levels=1}){const g=G();for(let L=0;L<levels;L++){const y0=L*LV;const b=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,6,1,false,-Math.PI/2,Math.PI),mat(c||P.wall));b.position.y=y0+F+h/2;g.add(b);
    for(let k=0;k<3;k++){const a=-Math.PI/2+Math.PI/6+k*Math.PI/3;const wm=windowM(P,20,48,'arch');wm.position.set(Math.sin(a)*r*.87,y0+F+h*.55,Math.cos(a)*r*.87);wm.rotation.y=a;g.add(wm);}
    const cap=new THREE.Mesh(new THREE.CylinderGeometry(r*.2,r+6,22,6,1,false,-Math.PI/2,Math.PI),mat(P.metal2||P.roof));cap.position.y=y0+F+h+11;g.add(cap);
    const bs=new THREE.Mesh(new THREE.CylinderGeometry(r+4,r*.6,14,6,1,false,-Math.PI/2,Math.PI),mat(P.trim));bs.position.y=y0+F-7+(L?0:14);if(L)g.add(bs);}
  g.rotation.y=0;return g;}
function cupola(P,{s=1}={}){const g=G(cy(32,32,8,P.trim,0,4,0,8),cy(26,26,46,P.wall,0,31,0,8));for(let k=0;k<8;k++){const a=k*Math.PI/4+Math.PI/8;const w=windowM(P,12,30,'arch');w.position.set(Math.sin(a)*24,32,Math.cos(a)*24);w.rotation.y=a;g.add(w);}
  g.add(cy(32,32,5,P.trim,0,56,0,8));const d=sp(26,P.metal2||P.roof,0,60,0);d.scale.y=1.3;g.add(d,cone(9,30,P.metal2||P.roof,0,104,0,16));
  const v=G(cy(1,1,30,0x333,0,0,0,6),bx(30,1.5,1.5,0x333,0,10,0),cone(3,8,0x333,15,10,0).rotateZ(-Math.PI/2));v.add(at(G(bx(12,8,1,0xd4a017)),-13,10,0));g.add(at(v,0,125,0));
  g.scale.setScalar(s);return g;}
function rail(P,{w,d,h=24,c}){const g=G();c=c||P.trim;const runs=[[w,0,d/2,0],[w,0,-d/2,0],[d,w/2,0,1],[d,-w/2,0,1]];
  for(const[L,x,z,r]of runs){const s=G(bx(L,3,4,c,0,h,0),bx(L,2,3,c,0,3,0));for(let k=0;k<=L/8;k++)s.add(cy(1.2,1.2,h-3,c,-L/2+k*8,h/2,0,6));at(s,x,0,z,r?Math.PI/2:0);g.add(s);}
  for(const[x,z]of[[-w/2,-d/2],[w/2,-d/2],[-w/2,d/2],[w/2,d/2]])g.add(at(G(bx(6,h+6,6,c,0,(h+6)/2,0),sp(3.5,P.metal||0xd4a017,0,h+10,0)),x,0,z));return g;}
function crenels(P,{w,d,c}){const g=G();c=c||P.wall;g.add(bx(w+8,6,d+8,P.trim,0,3,0));for(const[L,x,z,r]of[[w,0,d/2,0],[w,0,-d/2,0],[d,w/2,0,1],[d,-w/2,0,1]]){for(let k=0;k<=L/20;k++)g.add(at(G(bx(11,16,8,c,0,14,0)),r?x:-L/2+k*20,0,r?-L/2+k*20:z,r?Math.PI/2:0));}return g;}
function arcade(P,{w,n=4,h=78,c}){const g=G();const sp_=w/n;g.add(bx(w+6,10,10,P.trim,0,h+5,0),bx(w+6,4,12,P.trim,0,h+12,0));
  for(let k=0;k<=n;k++){const x=-w/2+k*sp_;g.add(cy(3.4,3.4,h-22,P.post||P.trim,x,(h-22)/2+6,0,12),bx(9,6,9,P.trim,x,3,0),bx(10,5,10,P.trim,x,h-17,0));for(let y=12;y<h-24;y+=6)g.add(tor(3.6,.8,P.post||P.trim,x,y,0).rotateX(Math.PI/2));
    if(k<n){g.add(tor(sp_/2-1,3,c||P.wall,x+sp_/2,h-14,0,Math.PI));g.add(bx(sp_,10,8,c||P.wall,x+sp_/2,h-3,0));g.add(bx(5,7,9,P.trim,x+sp_/2,h-14+sp_/2-2,0));}}
  return g;}
function fountain(P){const g=G(cy(54,58,16,P.stone||0xb9b2a6,0,8,0,8),cy(48,48,2,0,0,15,0,8,new THREE.MeshStandardMaterial({color:0x60a5fa,emissive:0x1e64c8,emissiveIntensity:.4,transparent:true,opacity:.85})));
  g.add(cy(8,10,50,P.stone||0xb9b2a6,0,40,0,12),cy(28,10,8,P.stone||0xb9b2a6,0,62,0,24),cy(25,25,1.5,0,0,66,0,24,mat(0x7dd3fc,{emissive:0x2563eb,emissiveIntensity:.4})),cy(5,6,20,P.stone||0xb9b2a6,0,74,0,12),cy(15,6,6,P.stone||0xb9b2a6,0,86,0,24));
  const pc=sp(5,P.metal||0xd4a017,0,96,0);pc.scale.y=1.7;g.add(pc);for(let k=0;k<8;k++){const a=k*Math.PI/4;g.add(tubeM(V3(Math.sin(a)*8,90,Math.cos(a)*8),V3(Math.sin(a)*22,68,Math.cos(a)*22),0xbae6fd,.8));}return g;}
function clocktower(P,{h=260,c}={}){const g=G(bx(64,h,64,c||P.brickWall||P.wall,0,h/2,0));if(P.brick)for(let y=8;y<h;y+=9)g.add(bx(64.6,.8,64.6,P.brick,0,y,0));
  for(const y of[8,h*.45,h-6])g.add(bx(72,7,72,P.trim,0,y,0));
  for(let k=0;k<4;k++){const a=k*Math.PI/2;const f=G(cy(24,24,4,P.trim,0,0,0,32),cy(20,20,4.6,0xfdf6e3,0,0,0,32,new THREE.MeshStandardMaterial({color:0xfdf6e3,emissive:0xffe9a8,emissiveIntensity:.25})),bx(1.6,15,6,0x222,0,6,0),bx(11,1.6,6,0x222,4.5,0,0));f.children.forEach(m=>{if(m.geometry.type=='CylinderGeometry'){m.rotation.x=Math.PI/2;}});
    for(let t=0;t<12;t++){const b=t/12*Math.PI*2;f.add(bx(1.2,3,5.5,0x222,Math.sin(b)*17,Math.cos(b)*17,0));}
    f.children.forEach(m=>{if(m.geometry.type=='BoxGeometry')m.position.z=2.6;});
    g.add(at(f,Math.sin(a)*33,h-56,Math.cos(a)*33,a));const w=windowM(P,18,34,'arch');g.add(at(w,Math.sin(a)*32.5,h-20,Math.cos(a)*32.5,a));
    g.add(at(windowM(P,10,26,'arch'),Math.sin(a)*32.5,h*.3,Math.cos(a)*32.5,a));}
  const s=cone(52,110,P.metal2||P.roof,0,h+55,0,4);s.rotation.y=Math.PI/4;g.add(s,at(finial(P.metal||0xd4a017),0,h+108,0));
  for(const[x,z]of[[-36,-36],[36,-36],[-36,36],[36,36]])g.add(cy(5,5,28,P.trim,x,h+14,z,8),cone(6,22,P.metal2||P.roof,x,h+39,z,8));return g;}
function smokestack(P,{h=280}={}){const g=G(cy(16,20,h,P.chim||0x9b4a3a,0,h/2,0,24),bx(52,18,52,P.stone||0x6b6259,0,9,0));for(let y=30;y<h;y+=50)g.add(tor(19-y/h*4,2.4,P.metal||0xb87333,0,y,0).rotateX(Math.PI/2));
  g.add(cy(22,17,14,P.metal||0xb87333,0,h,0,24),sp(10,0,0,h+10,0,new THREE.MeshBasicMaterial({color:0xff8a3d,transparent:true,opacity:.6})));
  for(let k=0;k<5;k++){const p=sp(10+k*5,0xd6d3d1,8+k*14,h+24+k*20,-k*4,new THREE.MeshStandardMaterial({color:0xe7e5e4,transparent:true,opacity:.45-k*.07}));g.add(p);}return g;}
function gear(c,r=22,x,y,z,ry=0){const g=G(cy(r,r,5,c,0,0,0,24),cy(r*.35,r*.35,6.5,0x3f2e1e,0,0,0,16));for(let k=0;k<12;k++){const a=k/12*Math.PI*2;g.add(at(G(bx(6,5,7,c)),Math.sin(a)*(r+2.5),0,Math.cos(a)*(r+2.5),a));}
  for(let k=0;k<4;k++){const a=k/4*Math.PI*2;g.add(at(G(bx(3,5.4,r*1.4,c)),0,0,0,a));}
  g.rotation.x=Math.PI/2;const o=G(g);at(o,x,y,z,ry);o.userData.spin=g;return o;}
function tree(P,{s=1,kind='round'}={}){const g=G(cy(4,6,40,0x6b4a2f,0,20,0,8));if(kind=='round'){[[0,52,0,24],[12,44,6,16],[-12,46,-4,17],[0,68,0,16]].forEach(([x,y,z,r])=>g.add(sp(r,P.leaf||0x4d7c3a,x,y,z)));[[8,60,14],[-10,54,12],[14,48,-6]].forEach(([x,y,z])=>g.add(sp(3,0xf87171,x,y,z)));}
  else{for(let k=0;k<3;k++)g.add(cone(26-k*6,34,P.leaf2||0x2f5d3a,0,40+k*20,0,12));}g.scale.setScalar(s);return g;}
function lamppost(P){return G(cy(6,8,6,0x222,0,3,0,8),cy(1.6,2,110,0x222,0,58,0,8),bx(16,1.5,1.5,0x222,0,108,0),cy(6,4,14,0,0,118,0,6,new THREE.MeshBasicMaterial({color:0xffd58a})),cone(8,9,0x222,0,129,0,6),sp(2,0x222,0,135,0));}
function gardenWall(P,{L}){const g=G(bx(L,24,10,P.stone||0xb9b2a6,0,12,0),bx(L+4,4,13,P.trim,0,26,0));for(const x of[-L/2,L/2])g.add(bx(14,34,14,P.stone||0xb9b2a6,x,17,0),cone(6,8,P.trim,x,38,0,12),sp(6,P.urn||0x6e8b5b,x,46,0));return g;}
function hedge(P,{L}){const g=G();for(let x=-L/2;x<=L/2;x+=12)g.add(sp(9,0x3f6b35,x,8,0));return g;}
// figures + furniture (decorative, scaled 1:24)
function lady(c=0xc084fc){return G(cone(15,38,c,0,19,0,20),cy(5,6,22,c,0,46,0,12),sp(5,0xf2c9a0,0,62,0),cy(12,12,1.4,0xf5e6c8,0,67,0,20),cy(5,5,5,0xf5e6c8,0,70,0,12),sp(5,c,0,30,-8));}
function gent(c=0x334155){return G(cy(2.4,2.4,30,0x222,-3,15,0,8),cy(2.4,2.4,30,0x222,3,15,0,8),cy(6,7,26,c,0,42,0,12),cone(8,14,c,0,30,0,12),sp(5,0xf2c9a0,0,60,0),cy(6,6,1.4,0x111,0,65,0,16),cy(4,4,10,0x111,0,70,0,12));}
function child(c=0xfacc15){const g=gent(c);g.scale.setScalar(.66);return g;}
function cat(){return G(sp(5,0x444,0,6,0).scale.set(1.6,1,1)&&sp(5,0x444,0,6,0),sp(3.6,0x444,8,11,0),cone(1.4,3,0x444,8,15.5,-1.6),cone(1.4,3,0x444,8,15.5,1.6),cy(.8,.8,12,0x444,-8,10,0,6));}
function chandelier(){const g=G(cy(1,1,24,0xd4a017,0,-12,0,6),sp(5,0xd4a017,0,-24,0));for(let k=0;k<6;k++){const a=k*Math.PI/3;g.add(tubeM(V3(0,-24,0),V3(Math.sin(a)*18,-20,Math.cos(a)*18),0xd4a017,.8),sp(2.4,0,Math.sin(a)*18,-16,Math.cos(a)*18,glass(0xffe08a)));}return g;}
function fourPoster(c=0x7c2d12){const g=G(bx(60,12,80,c,0,10,0),bx(56,6,76,0xf5e6c8,0,19,0),bx(24,6,14,0xffffff,-14,24,-28),bx(24,6,14,0xffffff,14,24,-28),bx(56,3,46,0xbe185d,0,23,12));for(const[x,z]of[[-29,-39],[29,-39],[-29,39],[29,39]])g.add(cy(2,2,70,c,x,35,z,8),sp(3,0xd4a017,x,72,z));g.add(bx(60,3,80,0xbe185d,0,70,0));return g;}
function wingback(c=0x166534){return G(bx(30,10,28,c,0,10,0),bx(30,38,6,c,0,30,-12),bx(5,18,26,c,-14,20,0),bx(5,18,26,c,14,20,0),cy(1.5,1.5,6,0x3f2e1e,-12,3,10),cy(1.5,1.5,6,0x3f2e1e,12,3,10));}
function clock(){return G(bx(22,90,14,0x5b3a24,0,45,0),cy(8,8,2,0xfdf6e3,0,76,7.5,20).rotateX(Math.PI/2),cone(13,10,0x5b3a24,0,95,0,4),bx(2,20,2,0xd4a017,0,40,7.5));}
function airship(P){const g=G();const b=sp(30,P.metal2||0xb87333);b.scale.set(2.4,1,1);g.add(b);for(let k=-2;k<=2;k++)g.add(tor(30.5*Math.sqrt(1-(k/2.6)**2),.8,0x5b3a24,k*22,0,0).rotateY(Math.PI/2));
  g.add(bx(40,10,14,0x5b3a24,0,-38,0),tubeM(V3(-14,-33,0),V3(-14,-24,0),0x333,.6),tubeM(V3(14,-33,0),V3(14,-24,0),0x333,.6),cone(10,16,0xbe185d,-76,0,0,4).rotateZ(Math.PI/2),gear(0xd4a017,6,22,-38,8,0));return g;}
function stringLights(a,b,n=14,sag=18){const g=G();let prev=null;for(let k=0;k<=n;k++){const t=k/n;const p=V3(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t-Math.sin(t*Math.PI)*sag,a.z+(b.z-a.z)*t);if(prev)g.add(tubeM(prev,p,0x222,.4));if(k%1==0)g.add(sp(1.8,0,p.x,p.y-2,p.z,glass([0xfde68a,0xf472b6,0x67e8f9,0xa3e635][k%4])));prev=p;}return g;}
function tesla(P){const g=G(cy(6,10,40,0x555,0,20,0,12),cy(3,3,30,0xb87333,0,55,0,12));for(let y=44;y<70;y+=3)g.add(tor(4,.7,0xb87333,0,y,0).rotateX(Math.PI/2));const t=tor(12,4,0xd1d5db,0,74,0);t.rotation.x=Math.PI/2;g.add(t);
  const bolt=new THREE.MeshBasicMaterial({color:0xc4b5fd});for(let k=0;k<5;k++){let p=V3(0,74,0);const a=k*1.3;for(let s=0;s<4;s++){const q=V3(p.x+Math.cos(a)*7+(Math.random()-.5)*6,p.y+5+Math.random()*6,p.z+Math.sin(a)*7+(Math.random()-.5)*6);const m=tubeM(p,q,0xc4b5fd,.6);m.material=bolt;g.add(m);p=q;}}
  g.userData.bolt=bolt;return g;}
// ---------- scene plumbing ----------
let renderer,scene,camera,controls,root,parts=[],spinners=[],target=0,ex=0,night=false,spin=true,lights=[];
const vis={roof:1,wall:1,furn:1,garden:1,light:1,wire:1,panel:1,orn:1,base:1};
function put(obj,grp,layer,lv=0){root.add(obj);parts.push({m:obj,by:obj.position.y,lift:layer*55+lv*120,grp});obj.traverse(o=>{if(o.userData&&o.userData.spin)spinners.push(o.userData.spin);});return obj;}
function glowLight(x,y,z,c=0xffb35c,i=.9,d=260){const l=new THREE.PointLight(c,0,d,1.6);l.position.set(x,y,z);l.userData.i=i;root.add(l);lights.push(l);return l;}
function chan(a,b,lv,col=0xfacc15,r=1.4,grp='light',layer=1){put(tubeM(a,b,col,r),grp,layer,lv);}
function roomLights(x,z,w,d,y,lv,wired){const yy=y+F+H-4;const c=[[x-w/2+6,z-d/2+6],[x+w/2-6,z-d/2+6],[x+w/2-6,z+d/2-6],[x-w/2+6,z+d/2-6]];
  for(let k=0;k<4;k++){const a=c[k],b=c[(k+1)%4];chan(V3(a[0],yy,a[1]),V3(b[0],yy,b[1]),lv,wired?0x22d3ee:0xfacc15,wired?2:1.3,wired?'wire':'light');}
  chan(V3(c[0][0],y+F,c[0][1]),V3(c[0][0],yy,c[0][1]),lv,wired?0x22d3ee:0xfacc15,wired?2.2:1.3,wired?'wire':'light');
  glowLight(x,y+F+H*.7,z,0xffb35c,.8,w+d);}
// house builder sugar: R(room at tile coords) etc.
function mk(P,list){for(const it of list){const[t,o]=it;const lv=o.lv||0,y=(o.y!=null?o.y:lv*LV),x=o.x||0,z=o.z||0,ry=o.r||0;let g,grp='wall',layer=1+lv*1.6;
  switch(t){
   case'room':g=room(P,o);roomLights(x,z,o.w,o.d,y,lv,P.wired);break;
   case'gable':g=gable(P,o);grp='roof';layer=5+lv;break;
   case'hip':g=hip(P,o);grp='roof';layer=5+lv;break;
   case'mansard':g=mansard(P,o);grp='roof';layer=5+lv;break;
   case'turret':g=turret(P,o);layer=2+lv;glowLight(x,y+(o.h||H*1.6)*.6,z,0xffb35c,.7,200);break;
   case'porch':g=porch(P,o);layer=2.5;break;
   case'dormer':g=dormer(P,o);grp='roof';layer=6+lv;break;
   case'chimney':g=chimney(P,o);grp='orn';layer=7+lv;break;
   case'bay':g=bay(P,o);layer=2.5+lv;break;
   case'cupola':g=cupola(P,o);grp='orn';layer=8+lv;break;
   case'rail':g=rail(P,o);grp='orn';layer=6+lv;break;
   case'crenels':g=crenels(P,o);grp='orn';layer=6+lv;break;
   case'arcade':g=arcade(P,o);layer=2.5;break;
   case'fountain':g=fountain(P);grp='garden';layer=.5;glowLight(x,30,z,0x60a5fa,.8,200);break;
   case'clock':g=clocktower(P,o);layer=4;break;
   case'stack':g=smokestack(P,o);grp='orn';layer=7;break;
   case'gear':g=gear(o.c||P.metal||0xb87333,o.rad||22,0,0,0);grp='orn';layer=3+lv;break;
   case'tree':g=tree(P,o);grp='garden';layer=.3;break;
   case'lamp':g=lamppost(P);grp='garden';layer=.4;glowLight(x,118,z,0xffd58a,.9,180);break;
   case'gwall':g=gardenWall(P,o);grp='garden';layer=.3;break;
   case'hedge':g=hedge(P,o);grp='garden';layer=.3;break;
   case'box':g=G(bx(o.w,o.h,o.d,o.c||P.trim,0,o.h/2,0));grp=o.grp||'wall';layer=o.layer!=null?o.layer:1+lv;break;
   case'lady':g=lady(o.c);grp='furn';layer=3+lv;break;case'gent':g=gent(o.c);grp='furn';layer=3+lv;break;case'child':g=child(o.c);grp='furn';layer=3+lv;break;case'cat':g=cat();grp='furn';layer=3+lv;break;
   case'bed':g=fourPoster(o.c);grp='furn';layer=3+lv;break;case'chair':g=wingback(o.c);grp='furn';layer=3+lv;break;case'gclock':g=clock();grp='furn';layer=3+lv;break;
   case'chand':g=chandelier();grp='furn';layer=3+lv;break;
   case'airship':g=airship(P);grp='orn';layer=9;spinners.push({air:g});break;
   case'string':g=stringLights(o.a,o.b,o.n,o.sag);grp='garden';layer=.6;break;
   case'tesla':g=tesla(P);grp='orn';layer=9;spinners.push({tesla:g.userData.bolt});break;
   case'panel':g=G(bx(60,80,1.6,0xa78bfa),bx(64,84,1,0xd4a017,0,0,-.4),sp(3,0xfacc15,0,32,1.2));grp='panel';layer=1+lv*1.6;break;
   case'wire':{const pts=o.pts;for(let k=0;k<pts.length-1;k++)put(tubeM(V3(...pts[k]),V3(...pts[k+1]),0x22d3ee,o.r||2.2),'wire',o.layer||1);continue;}
   case'glowbox':g=G(bx(o.w,o.h,o.d,0,0,o.h/2,0,glass(o.c||0xffd58a)));grp='orn';layer=o.layer||3;break;
   default:continue;}
  at(g,x,y+(o.dy||0),z,ry);if(o.s)g.scale.setScalar(o.s);put(g,grp,layer,0);}}
function base(P,w,d){const g=G(bx(w,8,d,P.lawn||0x5f8f4a,0,-4,0),bx(w+6,10,d+6,P.plinth||0x6b4f3a,0,-13,0));for(let k=0;k<26;k++){const a=Math.random()*Math.PI*2;g.add(sp(2.2,[0xf472b6,0xfacc15,0xffffff,0xc084fc][k%4],(Math.random()-.5)*w*.95,1,(d/2-8)*(Math.random()>.5?1:-1)));}put(g,'base',0,0);}
function path(P,x,z,w,d){const g=G();for(let zz=-d/2;zz<d/2;zz+=12)g.add(bx(w*(.8+Math.random()*.2),2,10,P.stone||0xb9b2a6,(Math.random()-.5)*4,1,zz));put(at(g,x,0,z),'garden',.2,0);}
// ---------- palettes ----------
const PAL={
 cottage:{wall:0xf3e9d2,trim:0xffffff,roof:0x5c7f4b,roof2:0x3d5a30,shutter:0x2a9d8f,flowers:1,lace:0xffffff,chim:0x8a817c,stone:0xb8aa96,quoin:0xd6ccb8,siding:0xe6dbc0,door:0xbe3d3d,leaf:0x6a9a4a,gable:0xf7d9c4,metal:0xd4a017,deck:0x9c7a55},
 ranch:{wall:0xf6d77b,trim:0xfffbeb,roof:0x3e5c76,roof2:0x2b4257,shutter:0x1e3a5f,siding:0xe9c766,lace:0xfffbeb,chim:0xa24936,stone:0xc2b8a3,door:0x1e3a5f,metal:0xd4a017,metal2:0x5b8f8a,deck:0x8b6b4a,post:0xffffff},
 town:{wall:0xe75480,trim:0xfdf2f8,roof:0x2d2a32,roof2:0x18161b,shutter:0x0f766e,flowers:1,lace:0xfdf2f8,brick:0xc93d6a,chim:0x7a3b52,stone:0xbab2a6,door:0x0f766e,metal:0xd4a017,metal2:0x4a9a8f,gable:0xf9a8d4},
 court:{wall:0xe9c9a0,trim:0xf5ebdc,roof:0xb5532f,roof2:0x8a3a1f,shutter:0x3f6b8f,stone:0xd2c3a8,quoin:0xcdb48c,door:0x6b3e1f,metal:0xd4a017,metal2:0x5b8f8a,post:0xf5ebdc,lawn:0x7aa05a,leaf2:0x2f5d3a},
 shop:{wall:0x7a4b3a,trim:0xd9b779,roof:0x4f8f80,roof2:0x2f6156,brick:0x5c3428,chim:0x7a3b2a,stone:0x6b6259,door:0x2f2015,metal:0xb87333,metal2:0x4f8f80,shutter:0x2f6156,deck:0x5b4334,quoin:0xa36a4f},
 wired:{wall:0x4c2a5a,trim:0xe8c468,roof:0x2f6b62,roof2:0x1d453f,shutter:0x1d453f,lace:0xe8c468,brick:0x3a1f46,chim:0x3a1f46,stone:0x8f8a99,door:0x1d453f,metal:0xe8c468,metal2:0x3f8f80,quoin:0x6b4580,flowers:1,deck:0x3f2e2a,post:0xe8c468,wired:1,gable:0x5e3570}
};
// ---------- the six houses ----------
const HOUSES=[
{id:'cottage0',name:'Bramble Cottage',old:'Cottage-0',size:'2 × 2 + porch',pal:'cottage',stories:'1½',blurb:'A storybook cottage straight out of a fairy tale: steep mossy roof with two dormers, a witch-hat turret on the corner, a lacy front porch, a fieldstone chimney, and flower boxes under every window.',
 story:'Built by a retired hedge-witch who wanted a cottage that looked like it grew there. The turret holds her reading nook, the dormers are the guest attic, and the chimney never quite stops glowing.',
 bom:{'floor_tile_v0':4,'corner_post_v0':4,'wall_panels (v0c short/full mix)':8,'roof_panel_v2':2,'gable_end_v2':2,'dormer_v2':2,'turret_segment_v2':2,'turret_cap_v2':1,'porch_post_v2':5,'railing_v2':3,'gingerbread_trim_v2':4,'bay_window_v2':1,'chimney_v2':1,'garden_wall_v2':2,'fix_victorian_lamppost_v2':1},
 build(P){base(P,560,520);mk(P,[['room',{w:254,d:254,ops:{S:['w','d','w'],N:['w','w'],E:['w','w'],W:['b','b']},wk:'arch'}],
  ['gable',{y:LV,w:254,d:254,pitch:52,over:14}],['dormer',{x:-60,y:LV+6,z:100}],['dormer',{x:60,y:LV+6,z:100}],
  ['turret',{x:-132,z:132,r:42,h:LV*1.55,capH:140}],['porch',{x:20,z:127,w:170,d:64,roof:'gable'}],['bay',{x:-127,z:0,r:44,r_:0,r:-Math.PI/2+0}],
  ['chimney',{x:128,z:-40,y:0,h:LV+150}],['lady',{x:-10,z:210,c:0xc084fc}],['child',{x:20,z:220}],['cat',{x:50,z:180,y:8}],
  ['tree',{x:210,z:150,s:1.2}],['tree',{x:-230,z:-150,s:1.4,kind:'pine'}],['tree',{x:200,z:-170,s:1.1}],['lamp',{x:90,z:240}],['gwall',{x:-140,z:245,L:190}],['gwall',{x:190,z:245,L:120}],['hedge',{x:-245,z:40,L:180,r:Math.PI/2}],
  ['bed',{x:60,z:-60,y:0}],['chair',{x:-60,z:-40}],['chand',{x:0,y:F+H-2,z:0}]]);
  parts.filter(p=>p.m.position.x==-127&&p.m.position.z==0).forEach(p=>p.m.rotation.y=-Math.PI/2);
  path(P,20,230,50,80);}},
{id:'ranch1',name:'Larkspur Grand Ranch',old:'Ranch-1',size:'4 × 2 + porte-cochère',pal:'ranch',stories:'1 + tower',blurb:'A long butter-yellow ranch with a wraparound porch the full width of the front, a cross-gabled centre hall that rises into a widow\'s walk and copper cupola, and a porte-cochère on the east for the carriage.',
 story:'A horse-country summer house. Everyone lives on the porch. The centre hall has a ballroom-height ceiling; climb to the widow\'s walk to watch for guests coming up the lane.',
 bom:{'floor_tile_v0':10,'corner_post_v0':10,'wall_panels':18,'roof_panel_v2':6,'gable_end_v2':4,'porch_post_v2':14,'railing_v2':10,'gingerbread_trim_v2':10,'widows_walk_v2':1,'cupola_v2':1,'chimney_v2':2,'bay_window_v2':2,'garden_wall_v2':2},
 build(P){base(P,820,560);mk(P,[['room',{x:-190,w:254,d:254,ops:{S:['w','w'],N:['w','w'],W:['w','w']}}],['room',{x:190,w:254,d:254,ops:{S:['w','w'],N:['w','w'],E:['d']}}],
  ['room',{w:127,d:254,h:H*1.5,ops:{S:['D'],N:['W']},c:0xfbe7a1}],['room',{y:F+H*1.5,w:127,d:127,h:H*.7,ops:{S:['r'],N:['r'],E:['r'],W:['r']},c:0xfbe7a1}],
  ['hip',{x:-190,y:LV,w:254,d:254,h:56}],['hip',{x:190,y:LV,w:254,d:254,h:56}],['gable',{y:F*2+H*2.2,w:127,d:127,pitch:30,over:8}],
  ['rail',{y:F*2+H*2.2+20,w:90,d:90}],['cupola',{y:F*2+H*2.2+28,s:.9}],
  ['porch',{z:127,w:640,d:70,posts:13,roof:'shed'}],['porch',{x:-317,z:0,w:254,d:60,posts:6,r:-Math.PI/2}],
  ['porch',{x:317,z:-20,w:180,d:120,posts:4,roof:'flat',r:Math.PI/2}],['bay',{x:-190,z:-127,r:44,r:Math.PI}],
  ['chimney',{x:-250,z:-60,y:LV-10,h:110}],['chimney',{x:250,z:-60,y:LV-10,h:110}],
  ['lady',{x:-60,z:160,y:8,c:0x60a5fa}],['gent',{x:-30,z:165,y:8}],['chair',{x:120,z:150,y:8}],['chair',{x:160,z:150,y:8,c:0x9a3412}],['child',{x:80,z:240}],
  ['lamp',{x:-140,z:255}],['lamp',{x:140,z:255}],['tree',{x:-380,z:-220,s:1.3}],['tree',{x:380,z:-200,s:1.5,kind:'pine'}],['tree',{x:-390,z:230,s:1}],['gwall',{x:-260,z:268,L:240}],['gwall',{x:260,z:268,L:240}],['chand',{y:F+H*1.5-2}]]);
  parts.filter(p=>p.m.position.x==-190&&p.m.position.z==-127).forEach(p=>p.m.rotation.y=Math.PI);
  path(P,0,240,60,60);}},
{id:'town2',name:'Pennywhistle Row House',old:'Townhouse-2',size:'2 × 2 × 3 stories',pal:'town',stories:3,blurb:'A tall raspberry townhouse stacked three stories high: a two-story bay window, a lace-railed Juliet balcony, a corner oriel turret with an onion dome, a mansard roof with dormers, and a rooftop terrace strung with fairy lights.',
 story:'A confectioner lives over her sweet shop. Ground floor is the shop, the bay is her parlour, the balcony is for waving at the parade, and the rooftop terrace is where the cocoa gets served at midnight.',
 bom:{'floor_tile_v0':4,'upper_floor_tile_v1':8,'corner_post_v0':12,'wall_panels':24,'bay_window_v2':2,'balcony_v2':1,'turret_segment_v2':3,'turret_cap_v2 (onion variant)':1,'dormer_v2':3,'crenel_parapet_v2':4,'grand_stair_v2':2,'chimney_v2':2,'gingerbread_trim_v2':4},
 build(P){base(P,480,480);mk(P,[['room',{w:254,d:254,ops:{S:['W','D'],N:['w','w'],E:['w','w'],W:['w','w']},ww:20}],['room',{lv:1,w:254,d:254,ops:{S:['b','w'],N:['w','w'],E:['w','w'],W:['w','w']}}],['room',{lv:2,w:254,d:254,h:H*.9,ops:{N:['w','w'],E:['w'],W:['w']}}],
  ['mansard',{y:LV*2,w:254,d:254,h:H*.9+F}],['dormer',{x:-60,y:LV*2+30,z:118}],['dormer',{x:60,y:LV*2+30,z:118}],['dormer',{x:0,y:LV*2+30,z:-118,r:Math.PI}],
  ['crenels',{y:LV*2+H*.9+F+2,w:190,d:190,c:0xe75480}],['string',{a:V3(-90,LV*3+40,-90),b:V3(90,LV*3+40,90),n:16,sag:16}],['string',{a:V3(90,LV*3+40,-90),b:V3(-90,LV*3+40,90),n:16,sag:16}],
  ['bay',{x:-64,z:127,r:48,levels:2}],['box',{x:64,y:LV+F+20,z:140,w:90,h:4,d:28,c:0xfdf2f8,layer:3}],['rail',{x:64,y:LV+F+20,z:142,w:90,d:24,h:22}],
  ['turret',{x:127,z:127,y:LV,r:30,h:LV*2-6,cap:'onion',levels:2}],['chimney',{x:-110,z:-80,y:LV*2,h:150}],['chimney',{x:100,z:-100,y:LV*2,h:130}],
  ['box',{x:0,z:132,y:F+H+F-4,w:260,h:10,d:14,c:0xfdf2f8,layer:2}],['glowbox',{x:60,z:131,y:F+H-12,w:60,h:12,d:4,c:0xf9a8d4,layer:2}],
  ['lady',{x:64,y:LV+F+22,z:140,c:0x0f766e}],['gent',{x:30,z:190,c:0x581c87}],['child',{x:-10,z:200,c:0xf472b6}],['cat',{x:-80,y:LV*3+12,z:0}],
  ['chair',{x:-60,y:LV,z:20}],['bed',{x:50,y:LV*2,z:-50}],['chand',{x:0,y:LV+F+H-2}],['lamp',{x:-180,z:200}],['tree',{x:180,z:-170,s:1}],['hedge',{x:-180,z:-200,L:120}]]);path(P,30,200,46,60);}},
{id:'court3',name:'Cloisterwick Manor',old:'Courtyard-3',size:'4 × 4 cloister',pal:'court',stories:'1–2 + towers',blurb:'A sun-baked cloister manor wrapped around a secret courtyard: an arcade of twisted columns on every side, a tiered fountain in the middle, crenellated towers at the back corners, a gatehouse with twin turrets, and red tile roofs.',
 story:'Once a mountain abbey, now a family manor. The gatehouse is the welcome hall, the back towers hold the library and the bell, and the fountain sings all night with a blue LED in its well.',
 bom:{'floor_tile_v0':12,'corner_post_v0':16,'wall_panels':30,'arcade_panel_v2':10,'fountain_v2':1,'turret_segment_v2':8,'turret_cap_v2':2,'crenel_parapet_v2':10,'roof_panel_v2':8,'gable_end_v2':2,'garden_wall_v2':2},
 build(P){base(P,700,700);const s=127;mk(P,[['room',{z:-190,w:508,d:127,ops:{N:['w','w','w','w'],S:['d','b','b','d']}}],['room',{x:-190,z:63,w:127,d:380,ops:{W:['w','w','w'],E:['b','d','b']}}],['room',{x:190,z:63,w:127,d:380,ops:{E:['w','w','w'],W:['b','d','b']}}],
  ['hip',{z:-190,y:LV,w:508,d:127,h:46}],['hip',{x:-190,z:63,y:LV,w:127,d:380,h:46}],['hip',{x:190,z:63,y:LV,w:127,d:380,h:46}],
  ['arcade',{z:-120,w:250,n:4}],['arcade',{x:-120,z:63,w:250,n:4,r:Math.PI/2}],['arcade',{x:120,z:63,w:250,n:4,r:-Math.PI/2}],
  ['fountain',{x:0,z:40}],['turret',{x:-254,z:-254,r:50,h:LV*2.1,cap:'cren'}],['turret',{x:254,z:-254,r:50,h:LV*2.1,cap:'cone',capH:150}],
  ['room',{z:254,w:200,d:80,h:H*1.3,ops:{S:['b','D','b'],N:['b','D','b']},open:[]}],['gable',{z:254,y:F+H*1.3,w:200,d:80,pitch:40,over:8}],['turret',{x:-118,z:254,r:28,h:H*1.8,capH:90}],['turret',{x:118,z:254,r:28,h:H*1.8,capH:90}],
  ['room',{x:-254,z:254,w:80,d:80,h:H*.6,ops:{S:['r']}}],['room',{x:254,z:254,w:80,d:80,h:H*.6,ops:{S:['r']}}],
  ['tree',{x:-60,z:120,s:.7,kind:'pine'}],['tree',{x:60,z:120,s:.7,kind:'pine'}],['tree',{x:-60,z:-40,s:.6,kind:'pine'}],['tree',{x:60,z:-40,s:.6,kind:'pine'}],
  ['lady',{x:-30,z:80,c:0xb91c1c}],['gent',{x:30,z:90,c:0x1e3a8a}],['cat',{x:0,z:100,y:16}],['lamp',{x:-60,z:330}],['lamp',{x:60,z:330}],['gwall',{x:-220,z:330,L:180}],['gwall',{x:220,z:330,L:180}],['bed',{x:-190,z:150}],['chair',{x:190,z:100}],['gclock',{x:-200,z:-190}]]);path(P,0,320,50,60);}},
{id:'shop4',name:'Cogsworth Works',old:'Workshop-4',size:'2 × 2 home + 2 × 3 works',pal:'shop',stories:'2 + clocktower',blurb:'An inventor\'s compound: a cosy two-story brick home on one side, a sawtooth-roofed workshop with great arched doors on the other, a clocktower between them, a copper-banded smokestack puffing away, brass gears on the walls, and a little airship tethered overhead.',
 story:'Professor Cogsworth builds clocks, kettles and, recently, a small airship. The clocktower keeps the whole street on time (badly). Light the smokestack LED and the workshop looks like it\'s working late.',
 bom:{'floor_tile_v0':10,'upper_floor_tile_v1':4,'corner_post_v0':14,'wall_panels':28,'clock_tower_v2':1,'clock_spire_v2':1,'smokestack_v2':1,'roof_panel_v2':8,'gable_end_v2':2,'dormer_v2':2,'chimney_v2':1,'balcony_v2':1,'porch_post_v2':4},
 build(P){base(P,820,560);mk(P,[['room',{x:-210,w:254,d:254,ops:{S:['w','d'],W:['w','w'],N:['w','w']},wk:'arch'}],['room',{x:-210,lv:1,w:254,d:254,ops:{S:['w','w'],W:['w','w'],N:['w','w']}}],
  ['gable',{x:-210,y:LV*2,w:254,d:254,pitch:50,over:12}],['dormer',{x:-260,y:LV*2+8,z:98}],['dormer',{x:-160,y:LV*2+8,z:98}],['chimney',{x:-330,z:-60,y:0,h:LV*2+140}],
  ['room',{x:180,w:381,d:254,h:H*1.25,ops:{S:['D','D','D'],E:['W','W'],N:['W','W','W']}}],
  ['box',{x:180,y:F+H*1.25,w:395,h:8,d:268,c:0xd9b779,grp:'roof',layer:5}],
  ['tesla_',{}],
  ['clock',{x:-50,z:-60,h:300}],['stack',{x:330,z:-90,y:0,h:330}],
  ['gear',{x:180,y:F+90,z:129,rad:24}],['gear',{x:226,y:F+70,z:129,rad:14}],['gear',{x:-210,y:LV+F+75,z:129,rad:16}],['gear',{x:-337,y:LV+40,z:0,rad:20,r:Math.PI/2}],
  ['porch',{x:-210,z:127,w:200,d:50,posts:4,roof:'shed'}],['airship',{x:60,y:560,z:40}],
  ['gent',{x:120,z:170,c:0x78350f}],['child',{x:160,z:175,c:0x0e7490}],['cat',{x:-150,z:170,y:8}],['lady',{x:-240,z:190,c:0x7c2d12}],['gclock',{x:-300,z:-80}],['bed',{x:-200,y:LV,z:-40}],['chand',{x:180,y:F+H*1.25-2}],
  ['lamp',{x:20,z:240}],['tree',{x:-380,z:-220,s:1.2,kind:'pine'}],['tree',{x:-380,z:220,s:1}],['hedge',{x:-210,z:255,L:200}]]);
  for(let k=0;k<3;k++){const gr=G();const xx=180-127+k*127;const s=bx(127,4,140,P.roof,0,0,0);s.rotation.x=-.55;s.position.set(0,38,-4);const gl=bx(125,64,3,0,0,30,64,glass(0xbfe3ff));gl.rotation.x=0;gr.add(s,gl,bx(129,4,6,P.trim,0,64,66));at(gr,xx,F+H*1.25+8,-60);put(gr,'roof',5,0);}
  path(P,180,230,120,50);}},
{id:'wired5',name:'The Electrified Manor',old:'Wired-5',size:'3 × 2 × 3 stories, wired',pal:'wired',stories:3,wired:true,blurb:'The showpiece. A plum-and-gold Second Empire manor with a three-story round tower, a wraparound porch dripping with gingerbread, a mansard roof full of dormers, and a crackling Tesla coil on the tower cap — wired like a real house, with glowing wire runs you can see, magnetic gold-framed service panels, and every fixture lit.',
 story:'A lighting inventor built this to show off her electric miracles. Every room has a switch, every lamp is real, and she left the wiring visible on purpose — wire theater. The Tesla coil is just for drama.',
 bom:{'wired_floor_tile_v1w':6,'upper_floor_tile_v1':10,'wired_corner_post_v1w':18,'wired_wall_short_v1w':8,'wall_panels':28,'wire_theater_panel_v2w':6,'power_module_v1w':1,'turret_segment_v2':6,'turret_cap_v2':1,'dormer_v2':4,'porch_post_v2':12,'railing_v2':9,'gingerbread_trim_v2':10,'bay_window_v2':1,'chimney_v2':2,'edison_sconce_v2w':6,'fix_chandelier_v2':3,'fix_victorian_lamppost_v2':2},
 build(P){base(P,760,600);mk(P,[['room',{w:381,d:254,ops:{S:['W','D','W'],N:['w','w','w'],E:['w','w'],W:['w','w']}}],['room',{lv:1,w:381,d:254,ops:{S:['w','w','w'],N:['w','w','w'],E:['w','w'],W:['w','w']}}],
  ['mansard',{y:LV*2,w:381,d:254,h:H}],['dormer',{x:-100,y:LV*2+34,z:120}],['dormer',{x:0,y:LV*2+34,z:120}],['dormer',{x:100,y:LV*2+34,z:120}],['dormer',{x:0,y:LV*2+34,z:-120,r:Math.PI}],
  ['rail',{y:LV*2+H+2,w:250,d:150}],['turret',{x:-190,z:127,r:52,h:LV*3,levels:3,capH:170}],['tesla',{x:-190,y:LV*3+168,z:127}],
  ['porch',{x:40,z:127,w:300,d:66,posts:8,roof:'shed'}],['porch',{x:190,z:0,w:254,d:60,posts:6,r:Math.PI/2}],['bay',{x:-190,z:-30,r:44,r:-Math.PI/2,levels:2}],
  ['chimney',{x:150,z:-90,y:LV*2,h:150}],['chimney',{x:-120,z:-90,y:LV*2,h:150}],
  ['panel',{x:-60,y:F+60,z:-131,r:Math.PI}],['panel',{x:60,y:F+60,z:-131,r:Math.PI}],['panel',{x:-60,y:LV+F+60,z:-131,r:Math.PI}],['panel',{x:60,y:LV+F+60,z:-131,r:Math.PI}],['panel',{x:194,y:LV+F+60,z:-50,r:Math.PI/2}],['panel',{x:-194,y:LV+F+60,z:60,r:-Math.PI/2}],
  ['wire',{pts:[[150,F+30,-130],[150,LV*2+H,-130],[-150,LV*2+H,-130],[-150,F+30,-130],[150,F+30,-130]],r:2.4,layer:1}],
  ['wire',{pts:[[-60,F+20,-130],[-60,LV*2+60,-130]],layer:1}],['wire',{pts:[[60,F+20,-130],[60,LV*2+60,-130]],layer:1}],['wire',{pts:[[-190,F,-80],[-190,LV*3,-80]],layer:2}],
  ['box',{x:0,y:0,z:-150,w:60,h:30,d:24,c:0x334155,grp:'wire',layer:1}],['glowbox',{x:0,y:20,z:-163,w:10,h:4,d:2,c:0x22c55e,layer:1}],
  ['string',{a:V3(-330,120,250),b:V3(-50,F+H+20,150),n:14,sag:20}],['string',{a:V3(330,120,250),b:V3(180,F+H+20,150),n:12,sag:20}],['lamp',{x:-330,z:250}],['lamp',{x:330,z:250}],
  ['chand',{x:0,y:F+H-2}],['chand',{x:-100,y:LV+F+H-2}],['chand',{x:100,y:LV+F+H-2}],['lady',{x:-40,z:170,y:8,c:0xe8c468}],['gent',{x:0,z:175,y:8,c:0x1d453f}],['child',{x:40,z:180,y:8,c:0xa78bfa}],['cat',{x:80,z:170,y:8}],
  ['chair',{x:-80,z:-30}],['bed',{x:90,y:LV,z:-40}],['gclock',{x:140,z:-90}],['tree',{x:330,z:-220,s:1.3,kind:'pine'}],['tree',{x:-350,z:-220,s:1.2}],['gwall',{x:-200,z:290,L:220}],['gwall',{x:200,z:290,L:220}]]);
  parts.filter(p=>p.m.position.x==-190&&p.m.position.z==-30).forEach(p=>p.m.rotation.y=-Math.PI/2);
  path(P,0,240,56,60);}}
];
// fix bay rotation via r key duplicates: handled by mk ry (last r wins in object literal)
// ---------- UI ----------
let cur=0;const pills=document.getElementById('pills');
HOUSES.forEach((h,n)=>{const b=document.createElement('button');b.textContent=h.name;b.onclick=()=>{location.hash=h.id;select(n);};pills.appendChild(b);});
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected',x===b));document.querySelectorAll('section').forEach(s=>s.hidden=s.id!==b.dataset.tab);if(b.dataset.tab==='explore')resize();});
const WIRE=`<h3>Wiring the Electrified Manor</h3><p><strong>Low voltage only (3–5 V DC, USB or batteries). Never mains.</strong></p><ul>
<li><strong>Trunk:</strong> Ø5 bores up every <code>wired_corner_post_v1w</code> carry 30 AWG silicone pairs between stories; the tower has its own riser to the Tesla-coil LED.</li>
<li><strong>Floors:</strong> <code>wired_floor_tile_v1w</code> centre channels feed the chandelier of the room below.</li>
<li><strong>Wire theater:</strong> the back wall runs are left visible behind clear-window <code>wire_theater_panel_v2w</code> covers (gold arched frames, 4 × Ø6×2 N52 magnets) so you can watch the wiring. Wall magnets north-out, panel magnets south-out, so any panel fits any wall.</li>
<li><strong>Power:</strong> <code>power_module_v1w</code> (USB-C 5 V trigger or 3×AAA) behind the house, green pilot LED, JST-PH plugs per story.</li></ul>
<table><thead><tr><th>Kit</th><th>Qty</th></tr></thead><tbody><tr><td>30 AWG silicone wire red + black</td><td>2 × 8 m</td></tr><tr><td>Warm-white 3 mm LEDs w/ resistor, 5 V</td><td>20</td></tr><tr><td>Micro LEDs 1.8 mm (chandelier cups)</td><td>18</td></tr><tr><td>Purple flicker LED (Tesla coil) + 2 amber flicker (chimneys)</td><td>3</td></tr><tr><td>Micro slide switches</td><td>8 (one per room + exterior)</td></tr><tr><td>JST-PH 2-pin pigtails</td><td>10 pairs</td></tr><tr><td>N52 magnets Ø6×2 / Ø6×1</td><td>24 / 24</td></tr><tr><td>Warm fairy-light string, 2 m</td><td>1</td></tr></tbody></table>`;
function select(n){cur=n;const h=HOUSES[n];[...pills.children].forEach((b,k)=>b.classList.toggle('on',k==n));
  document.getElementById('rev').textContent='Grand v2 — '+h.name;document.getElementById('blurb').textContent=h.blurb;
  const tot=Object.values(h.bom).reduce((a,b)=>a+b,0);
  document.getElementById('facts').innerHTML=[[h.size,'Footprint (tiles)'],[h.stories,'Stories'],[tot+' parts','Structure + ornament'],[h.old,'Was (v1)']].map(([a,b])=>`<div class="fact"><b>${a}</b><span>${b}</span></div>`).join('');
  document.getElementById('bom').innerHTML=`<h3>${h.name} — print list</h3><table><thead><tr><th>Part (STL)</th><th>Qty</th></tr></thead><tbody>${Object.entries(h.bom).map(([k,v])=>`<tr><td><code>${k}</code></td><td>${v}</td></tr>`).join('')}</tbody></table>
  <p class="muted">Roof panels, gables and arcades print flat; turret drums and caps print upright. Every v2 ornament fits the H3C bed (largest: roof panel 254 × 107, smokestack 229 tall). Bambu Studio 3MF plates come after the clearance-strip fit test.</p>`;
  document.getElementById('notes-house').innerHTML=`<h3>${h.name}</h3><p>${h.story}</p>`+(h.wired?WIRE:`<p class="muted">Lights: Ø3.2 channels run around each wall top and down a corner post; turret, chimney and fountain each hide an LED pocket. Press <b>Night lights</b> to see it lit.</p>`);
  ['btn-wire','btn-panel','lg-w','lg-p'].forEach(id=>document.getElementById(id).hidden=!h.wired);build(h);}
function build(h){if(!window.THREE)return;if(root)scene.remove(root);root=new THREE.Group();scene.add(root);parts=[];spinners=[];lights=[];GLOW.length=0;
  const P=PAL[h.pal];h.build(P);
  // centre + frame
  const bb=new THREE.Box3().setFromObject(root),sz=bb.getSize(V3()),c=bb.getCenter(V3());const R=Math.max(sz.x,sz.y,sz.z);
  camera.position.set(c.x+R*.95,c.y+R*.55,c.z+R*1.05);controls.target.set(c.x,c.y*.7,c.z);applyVis();setNight(night);}
function applyVis(){parts.forEach(p=>{p.m.visible=!!(vis[p.grp]??1);});}
function setNight(on){night=on;if(!scene)return;scene.background=new THREE.Color(on?0x0b1020:0x1a1f27);hemi.intensity=on?.18:.85;sun.intensity=on?.08:.9;
  GLOW.forEach(m=>m.emissiveIntensity=on?1.6:.35);lights.forEach(l=>l.intensity=on?l.userData.i:0);}
let hemi,sun,resize=()=>{};
if(window.THREE){renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=false;el.prepend(renderer.domElement);
  scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(38,1,1,8000);const OC=THREE.OrbitControls||window.OrbitControls;controls=new OC(camera,renderer.domElement);controls.enableDamping=true;
  controls.addEventListener('start',()=>{if(spin){spin=false;document.getElementById('btn-spin').classList.remove('on');}});
  hemi=new THREE.HemisphereLight(0xfff4e0,0x3a3550,.85);scene.add(hemi);sun=new THREE.DirectionalLight(0xffe7c2,.9);sun.position.set(400,700,300);scene.add(sun);const fill=new THREE.DirectionalLight(0x9ab8ff,.25);fill.position.set(-400,200,-300);scene.add(fill);
  resize=()=>{const w=el.clientWidth,hh=el.clientHeight;if(!w)return;renderer.setSize(w,hh,false);renderer.domElement.style.width='100%';renderer.domElement.style.height='100%';camera.aspect=w/hh;camera.updateProjectionMatrix();};
  addEventListener('resize',resize);resize();let t0=0;
  (function loop(t){requestAnimationFrame(loop);ex+=(target-ex)*.08;parts.forEach(p=>p.m.position.y=p.by+p.lift*ex);
    if(spin&&root)root.rotation.y+=.0025;
    spinners.forEach(s=>{if(s.isObject3D)s.rotation.y+=.01;else if(s.air){s.air.position.y=560+Math.sin(t/900)*10;}else if(s.tesla){s.tesla.color.setHSL(.72,1,.6+Math.random()*.35);}});
    controls.update();renderer.render(scene,camera);})(0);}
const tog=(id,fn)=>{const b=document.getElementById(id);b.onclick=()=>{b.classList.toggle('on');fn(b.classList.contains('on'));};};
tog('btn-explode',on=>target=on?1:0);tog('btn-night',setNight);tog('btn-spin',on=>spin=on);
[['btn-roof',['roof','orn']],['btn-wall',['wall']],['btn-furn',['furn']],['btn-garden',['garden']],['btn-light',['light']],['btn-wire',['wire']],['btn-panel',['panel']]].forEach(([id,ks])=>tog(id,on=>{ks.forEach(k=>vis[k]=on?1:0);applyVis();}));
addEventListener('hashchange',()=>{const i=HOUSES.findIndex(h=>h.id==location.hash.slice(1));if(i>=0&&i!=cur)select(i);});
select(Math.max(0,HOUSES.findIndex(h=>h.id==location.hash.slice(1))));
})();
