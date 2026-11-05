// Grand dollhouse kit v3 "Gallery" — storybook explorer (Three r149). Units mm, 1:24. x right, z toward viewer, y up.
(function(){
const T=127,H=101.6,F=10,LV=H+F;
const el=document.getElementById('view');
if(!window.THREE){el.insertAdjacentHTML('afterbegin','<p style="padding:1rem" class="muted">3D viewer could not load.</p>');return;}
THREE.ColorManagement&&(THREE.ColorManagement.legacyMode=false);
const Q=new URLSearchParams(location.search);
const V3=(x,y,z)=>new THREE.Vector3(x,y,z);
let rnd=(()=>{let s=7;return()=>{s=(s*16807)%2147483647;return(s-1)/2147483646;};})();
function seed(n){let s=n||7;rnd=()=>{s=(s*16807)%2147483647;return(s-1)/2147483646;};}
// ---------- procedural canvas textures (grey-scale detail, tinted by material colour) ----------
const TEX={};
function cvs(w,h,fn){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');fn(x,w,h);return c;}
function mkTex(c,rep=1){const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(rep,rep);t.encoding=THREE.sRGBEncoding;t.anisotropy=8;return t;}
function noise(x,w,h,n,a,lo=0,hi=255){for(let k=0;k<n;k++){const v=lo+Math.random()*(hi-lo)|0;x.fillStyle=`rgba(${v},${v},${v},${a})`;x.fillRect(Math.random()*w,Math.random()*h,1+Math.random()*2,1+Math.random()*2);}}
const GEN={
 clap:(x,w,h)=>{x.fillStyle='#f4f4f4';x.fillRect(0,0,w,h);const n=8;for(let k=0;k<n;k++){const y=k*h/n;const g=x.createLinearGradient(0,y,0,y+h/n);g.addColorStop(0,'#c9c9c9');g.addColorStop(.18,'#ffffff');g.addColorStop(1,'#e6e6e6');x.fillStyle=g;x.fillRect(0,y,w,h/n);x.fillStyle='#8f8f8f';x.fillRect(0,y,w,2);}
   for(let k=0;k<60;k++){x.strokeStyle='rgba(120,110,100,.07)';x.beginPath();const y=Math.random()*h;x.moveTo(0,y);x.bezierCurveTo(w/3,y+3,w*2/3,y-3,w,y);x.stroke();}noise(x,w,h,2500,.05);},
 shingle:(x,w,h)=>{x.fillStyle='#bdbdbd';x.fillRect(0,0,w,h);const r=w/8;for(let row=-1;row<h/(r*1.1)+1;row++){for(let k=-1;k<9;k++){const cx=k*r*2/2*2/2*2+(row%2?r:0),cy=row*r*1.1;const v=200+Math.random()*50|0;
   x.fillStyle=`rgb(${v},${v},${v})`;x.strokeStyle='#6b6b6b';x.lineWidth=2;x.beginPath();x.moveTo(cx-r,cy);x.lineTo(cx-r,cy+r*.5);x.arc(cx,cy+r*.5,r,Math.PI,0,true);x.lineTo(cx+r,cy);x.closePath();x.fill();x.stroke();
   const g=x.createRadialGradient(cx,cy+r*.9,1,cx,cy+r*.5,r);g.addColorStop(0,'rgba(255,255,255,.25)');g.addColorStop(1,'rgba(0,0,0,.18)');x.fillStyle=g;x.fill();}}noise(x,w,h,2000,.06);},
 brick:(x,w,h)=>{x.fillStyle='#9a9a9a';x.fillRect(0,0,w,h);const bh=h/10,bw=w/4;for(let r=0;r<10;r++)for(let k=-1;k<5;k++){const v=165+Math.random()*80|0;x.fillStyle=`rgb(${v},${v*.97|0},${v*.95|0})`;x.fillRect(k*bw+(r%2?bw/2:0)+2,r*bh+2,bw-4,bh-4);}noise(x,w,h,3000,.12);},
 stone:(x,w,h)=>{x.fillStyle='#8a8a8a';x.fillRect(0,0,w,h);let y=0;while(y<h){const rh=h/6*(.7+Math.random()*.6);let xx=-Math.random()*40;while(xx<w){const rw=w/4*(.6+Math.random()*.8);const v=170+Math.random()*70|0;x.fillStyle=`rgb(${v},${v},${v})`;
   x.beginPath();x.roundRect?x.roundRect(xx+3,y+3,rw-6,rh-6,8):x.rect(xx+3,y+3,rw-6,rh-6);x.fill();xx+=rw;}y+=rh;}noise(x,w,h,5000,.14);},
 plank:(x,w,h)=>{const n=6;for(let k=0;k<n;k++){const v=190+Math.random()*50|0;x.fillStyle=`rgb(${v},${v},${v})`;x.fillRect(0,k*h/n,w,h/n);x.fillStyle='#6a6a6a';x.fillRect(0,k*h/n,w,2);x.fillRect(((k*137)%w),k*h/n,2,h/n);
   for(let s=0;s<14;s++){x.strokeStyle='rgba(90,80,70,.15)';x.beginPath();const y=k*h/n+Math.random()*h/n;x.moveTo(0,y);x.quadraticCurveTo(w/2,y+(Math.random()-.5)*8,w,y);x.stroke();}}},
 grass:(x,w,h)=>{x.fillStyle='#d8d8d8';x.fillRect(0,0,w,h);for(let k=0;k<9000;k++){const v=150+Math.random()*105|0;x.strokeStyle=`rgba(${v},${v},${v},.55)`;x.beginPath();const px=Math.random()*w,py=Math.random()*h;x.moveTo(px,py);x.lineTo(px+(Math.random()-.5)*4,py-3-Math.random()*5);x.stroke();}},
 stucco:(x,w,h)=>{x.fillStyle='#ededed';x.fillRect(0,0,w,h);noise(x,w,h,9000,.08,120,255);for(let k=0;k<40;k++){const g=x.createRadialGradient(Math.random()*w,Math.random()*h,1,Math.random()*w,Math.random()*h,60);g.addColorStop(0,'rgba(255,255,255,.12)');g.addColorStop(1,'rgba(0,0,0,0)');x.fillStyle=g;x.fillRect(0,0,w,h);}},
 copper:(x,w,h)=>{x.fillStyle='#e0e0e0';x.fillRect(0,0,w,h);for(let k=0;k<120;k++){const g=x.createRadialGradient(Math.random()*w,Math.random()*h,1,Math.random()*w,Math.random()*h,30+Math.random()*40);g.addColorStop(0,'rgba(140,140,140,.25)');g.addColorStop(1,'rgba(255,255,255,0)');x.fillStyle=g;x.fillRect(0,0,w,h);}
   for(let k=0;k<8;k++){x.fillStyle='rgba(90,90,90,.35)';x.fillRect(k*w/8,0,2,h);}},
 wood:(x,w,h)=>{x.fillStyle='#d0d0d0';x.fillRect(0,0,w,h);for(let k=0;k<80;k++){x.strokeStyle=`rgba(80,70,60,${.05+Math.random()*.12})`;x.lineWidth=1+Math.random()*2;x.beginPath();const y=Math.random()*h;x.moveTo(0,y);x.bezierCurveTo(w/3,y+(Math.random()-.5)*20,w*2/3,y+(Math.random()-.5)*20,w,y);x.stroke();}},
};
function tex(kind){if(!TEX[kind])TEX[kind]=mkTex(cvs(512,512,GEN[kind]));return TEX[kind];}
// stained glass: jewel leaded panes. returns texture
const SGC={};
function sgTex(jewels,v){const k=jewels.join()+v;if(SGC[k])return SGC[k];const c=cvs(128,256,(x,w,h)=>{x.fillStyle='#1a1410';x.fillRect(0,0,w,h);
  const J=jewels,cell=(px,py,r,col)=>{const g=x.createRadialGradient(px,py,1,px,py,r*1.3);g.addColorStop(0,'#fff8e0');g.addColorStop(.35,col);g.addColorStop(1,shade(col,.55));x.fillStyle=g;};
  x.lineWidth=5;x.strokeStyle='#1a1410';
  if(v%3==0){// diamond quarries + central rose
    const n=5;for(let i=-1;i<=n;i++)for(let j=-1;j<=n*2;j++){const cx=(i+(j%2)*.5)*w/n,cy=j*h/(n*2)*1.0;cell(cx,cy,22,J[(i+j+9)%J.length]);x.beginPath();x.moveTo(cx,cy-h/(n*2));x.lineTo(cx+w/n/2,cy);x.lineTo(cx,cy+h/(n*2));x.lineTo(cx-w/n/2,cy);x.closePath();x.fill();x.stroke();}
    x.lineWidth=6;for(let r=40;r>0;r-=14){cell(w/2,h*.32,r,J[(r/14|0)%J.length]);x.beginPath();x.arc(w/2,h*.32,r,0,7);x.fill();x.stroke();}
    for(let k=0;k<8;k++){x.beginPath();x.moveTo(w/2,h*.32);x.lineTo(w/2+Math.cos(k*.785)*40,h*.32+Math.sin(k*.785)*40);x.stroke();}}
  else if(v%3==1){// tulip / lily
    for(let j=0;j<8;j++){cell(w/2,j*h/8+16,40,J[j%J.length]);x.fillRect(0,j*h/8,w,h/8);x.strokeRect(0,j*h/8,w,h/8);}
    const pt=(cx,cy,r,col)=>{cell(cx,cy,r,col);x.beginPath();x.ellipse(cx,cy,r*.55,r,0,0,7);x.fill();x.stroke();};
    x.strokeStyle='#1a1410';pt(w/2,h*.3,34,J[0]);pt(w/2-28,h*.42,24,J[1%J.length]);pt(w/2+28,h*.42,24,J[1%J.length]);
    cell(w/2,h*.7,30,'#3f9f5a');x.beginPath();x.moveTo(w/2,h*.36);x.lineTo(w/2,h);x.lineWidth=8;x.stroke();x.lineWidth=5;pt(w/2-20,h*.72,16,'#2f8a4a');pt(w/2+20,h*.66,16,'#2f8a4a');}
  else {// sunburst
    const cx=w/2,cy=h*.28;for(let k=0;k<16;k++){const a0=k/16*Math.PI*2,a1=(k+1)/16*Math.PI*2;cell(cx,cy,140,J[k%J.length]);x.beginPath();x.moveTo(cx,cy);x.arc(cx,cy,300,a0,a1);x.closePath();x.fill();x.stroke();}
    cell(cx,cy,26,'#ffe08a');x.beginPath();x.arc(cx,cy,24,0,7);x.fill();x.stroke();for(let j=1;j<5;j++){x.beginPath();x.moveTo(0,cy+j*h*.17);x.lineTo(w,cy+j*h*.17);x.stroke();}}
  x.lineWidth=10;x.strokeRect(0,0,w,h);});
  const t=mkTex(c);t.wrapS=t.wrapT=THREE.ClampToEdgeWrapping;SGC[k]=t;return t;}
function shade(hex,f){const c=new THREE.Color(hex);c.multiplyScalar(f);return '#'+c.getHexString();}
// ---------- materials ----------
let ROLE={},CUR_P=null;const MC={};
function mat(c,o={}){const k=c+JSON.stringify(o);if(MC[k])return MC[k];
  const r=ROLE[c];const p=Object.assign({color:c,roughness:.72,metalness:0},o);
  if(r&&!o.flat){const t=tex(r.t);p.map=t;p.bumpMap=t;p.bumpScale=r.b??.6;if(r.m!=null)p.metalness=r.m;if(r.r!=null)p.roughness=r.r;}
  return MC[k]=new THREE.MeshStandardMaterial(p);}
const GLOW=[];let SGI=0;
function glass(c=0xffd58a,kind){const P=CUR_P||{};const J=P.jewels||[0xf59e0b,0xdc2626,0x2563eb,0x16a34a,0x9333ea].map(x=>'#'+new THREE.Color(x).getHexString());
  const v=kind!=null?kind:(SGI++%3);const key='g'+c+v+J;if(MC[key])return MC[key];
  const plain=kind==='p'||(P.plainGlass&&kind==null);
  const m=new THREE.MeshStandardMaterial({color:plain?0x2a2620:0x3a3028,emissive:new THREE.Color(c).lerp(new THREE.Color(0xffffff),.35),emissiveIntensity:.5,roughness:.12,metalness:.25,
    map:plain?null:sgTex(J.map(x=>typeof x=='string'?x:'#'+new THREE.Color(x).getHexString()),v),emissiveMap:plain?null:sgTex(J.map(x=>typeof x=='string'?x:'#'+new THREE.Color(x).getHexString()),v),envMapIntensity:1.5});
  m.userData.keepUV=1;GLOW.push(m);return MC[key]=m;}
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
  g.userData.halo=V3(0,0,5);return g;}
function doorM(P,w=34,h=72){const g=G(bx(w,h-w/2,2,P.door||0x5b3a24,0,(h-w/2)/2,1));
  const t=new THREE.Mesh(new THREE.CylinderGeometry(w/2,w/2,2,20,1,false,0,Math.PI),glass(0xffc46b));t.rotation.set(Math.PI/2,0,Math.PI/2);t.position.set(0,h-w/2,1);g.add(t);
  g.add(tor(w/2+2,2,P.trim,0,h-w/2,2.5,Math.PI),bx(3,h-w/2,3,P.trim,-w/2-1.5,(h-w/2)/2,2),bx(3,h-w/2,3,P.trim,w/2+1.5,(h-w/2)/2,2),sp(1.6,0xd4a017,w/3,h*.4,3));
  g.add(bx(w+14,3,14,P.stone||0x9a9086,0,1.5,7),bx(w+8,3,9,P.stone||0x9a9086,0,4.5,5));
  for(const sx of[-1,1]){g.add(bx(5,h-w/2+6,4,P.trim,sx*(w/2+6),(h-w/2)/2+2,2.5),bx(8,4,6,P.trim,sx*(w/2+6),h-w/2+6,3));for(let k=0;k<3;k++)g.add(bx(.8,h-w/2-6,1,P.shutter||P.door||0x5b3a24,sx*(w/2+6)+(k-1)*1.5,(h-w/2)/2,4.6));}
  g.add(bx(w*.34,h*.3,.8,0x3a2a1e,-w*.22,h*.28,2.2),bx(w*.34,h*.3,.8,0x3a2a1e,w*.22,h*.28,2.2),bx(w*.34,h*.18,.8,0x3a2a1e,-w*.22,h*.6,2.2),bx(w*.34,h*.18,.8,0x3a2a1e,w*.22,h*.6,2.2));
  g.add(at(pediment(P,w+24),0,h+6,2.6),sp(3,P.metal||0xd4a017,0,h+3,3.5));return g;}
function pediment(P,w){const sh=new THREE.Shape();sh.moveTo(-w/2,0);sh.lineTo(w/2,0);sh.lineTo(0,w*.28);sh.closePath();const m=new THREE.Mesh(new THREE.ExtrudeGeometry(sh,{depth:4,bevelEnabled:true,bevelSize:.8,bevelThickness:.8,bevelSegments:1}),mat(P.trim));
  const in_=sh.clone?null:null;const g=G(m,bx(w+4,2.4,5.5,P.trim,0,0,2));const t=new THREE.Shape();t.moveTo(-w/2+6,2.5);t.lineTo(w/2-6,2.5);t.lineTo(0,w*.28-4);t.closePath();const tm=new THREE.Mesh(new THREE.ExtrudeGeometry(t,{depth:1,bevelEnabled:false}),mat(P.tympanum||P.wall));tm.position.z=4.4;g.add(tm,sp(2.6,P.metal||0xd4a017,0,w*.12,5.6));return g;}
function medallion(P){const g=G(tor(9,1.6,P.trim,0,0,1.5),sp(4,P.metal||0xd4a017,0,0,1.5),bx(30,36,1.2,P.panel||P.trim,0,0,.6));
  const sw=tor(14,1.8,P.leaf||0x4d7c3a,0,-6,2.5,Math.PI);sw.rotation.z=Math.PI;g.add(sw);for(let k=0;k<5;k++){const a=Math.PI+k/4*Math.PI;g.add(sp(2.2,[0xf472b6,0xfacc15,0xffffff,0xf87171,0xc084fc][k],Math.cos(a)*14,-6+Math.sin(a)*14,3.5));}return g;}
function sconce(P){const g=G(bx(5,8,1.5,P.metal||0xd4a017,0,0,.8),tubeM(V3(0,0,1),V3(0,4,7),P.metal||0xd4a017,.7),cy(3,2.2,7,0,0,7,7,8,glass(0xffc46b,'p')),cone(3.6,3,P.metal||0xd4a017,0,12,7,8));g.userData.halo=V3(0,7,7);return g;}
function ivy(P,h){const g=G();let x=0,y=0;for(let k=0;k<70;k++){x+=(rnd()-.5)*6;y+=rnd()*h/45;const r=2.2+rnd()*2.4;g.add(sp(r,[0x2f5d2a,0x3f7a35,0x4f8f3f,0x2a4f25][k%4],x,y,rnd()*2));if(k%11==0)g.add(sp(1.6,0xf9a8d4,x+2,y+1,3));}
  return g;}
// room box: footprint w×d centred at x,z; openings: {S:[...],N:[..],E:[..],W:[..]} items 'w','d','b'(blank gap), plus opts
function room(P,o){const {w,d,h=H}=o;const g=G();const wc=o.c||P.wall;
  g.add(bx(w+4,F,d+4,P.floor||0xc9b79c,0,F/2,0));
  const sides={S:[w,0,d/2,0],N:[w,0,-d/2,Math.PI],E:[d,w/2,0,Math.PI/2],W:[d,-w/2,0,-Math.PI/2]};
  for(const s in sides){const[L,x,z,r]=sides[s];if(o.open&&o.open.includes(s))continue;const f=G(bx(L,h,6,wc,0,F+h/2,-3));
    // siding courses
    if(P.siding)for(let y=F+8;y<F+h-4;y+=7)f.add(bx(L+.2,1,6.6,P.siding,0,y,-3));
    if(P.brick)for(let y=F+6;y<F+h-4;y+=9)f.add(bx(L+.2,.8,6.5,P.brick,0,y,-3));
    f.add(bx(L+6,6,9,P.trim,0,F+h-2,-3),bx(L+4,8,8,P.base||P.stone||P.trim,0,F+4,-3));
    // v3 facade: frieze + dentils + brackets, corner pilasters, plinth course
    f.add(bx(L+2,9,7.4,P.frieze||P.trim,0,F+h-10,-3),bx(L+3,2,8.4,P.trim,0,F+h-15,-3));
    for(let x=-L/2+3;x<=L/2-3;x+=5)f.add(bx(2.4,2.6,1.6,P.trim,x,F+h-16.6,1.2));
    for(let x=-L/2+8;x<=L/2-8;x+=(L>200?21:18))f.add(bx(3,8,5,P.trim,x,F+h-8,2.6),bx(3,3,7,P.trim,x,F+h-4,3.5));
    for(const sx of[-1,1])f.add(bx(7,h-18,8.6,P.pilaster||P.trim,sx*(L/2-3.5),F+h/2-2,-3),bx(10,5,10,P.trim,sx*(L/2-3.5),F+h-19,-3),bx(10,4,10,P.trim,sx*(L/2-3.5),F+10,-3));
    if(h>70)f.add(bx(L+2,3,7.6,P.trim,0,F+h*.3,-3));
    const ops=(o.ops&&o.ops[s])||[];const n=ops.length;ops.forEach((t,k)=>{const px=-L/2+L*(k+.5)/n;
      if(t=='w'){f.add(at(windowM(P,o.ww||22,o.wh||44,o.wk||'arch'),px,F+h*.55,0));if(P.pediment&&(k%2==0))f.add(at(pediment(P,(o.ww||22)+12),px,F+h*.55+(o.wh||44)/2+6,1));}
      if(t=='b'){f.add(at(medallion(P),px,F+h*.55,0));}
      if(t=='W')f.add(at(windowM(P,30,58,'arch'),px,F+h*.52,0));
      if(t=='r')f.add(at(windowM(P,26,26,'rect'),px,F+h*.58,0));
      if(t=='d'){f.add(at(doorM(P),px,F,0));f.add(at(sconce(P),px-24,F+52,0),at(sconce(P),px+24,F+52,0));}
      if(t=='D'){f.add(at(doorM(P,56,88),px,F,0));f.add(at(sconce(P),px-38,F+60,0),at(sconce(P),px+38,F+60,0));}});
    if(P.ivy&&rnd()<P.ivy)f.add(at(ivy(P,h),(rnd()>.5?1:-1)*(L/2-10),F,2));
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
  for(let x=-w/2-over+4;x<=w/2+over-4;x+=8){g.add(cy(.7,.7,9,P.crest||0x1f1f1f,x,rise+9,0,5),cone(1.6,4,P.crest||0x1f1f1f,x,rise+15,0,5));if(Math.round(x/8)%3==0)g.add(tor(3,.6,P.crest||0x1f1f1f,x,rise+10,0));}
  for(let x=-w/2;x<=w/2;x+=w/4)g.add(sp(2.5,P.metal||0xd4a017,x,rise+6,0));
  g.userData.rise=rise;return g;}
function hip(P,{w,d,h=50,c,over=10}){const g=G();const m=new THREE.Mesh(new THREE.CylinderGeometry(0,Math.SQRT1_2,1,4,1).rotateY(Math.PI/4),mat(c||P.roof));m.scale.set(w+over*2,h,d+over*2);m.position.y=h/2;
  const gg=G(m);gg.add(bx(w+over*2+2,4,d+over*2+2,P.trim,0,1,0));return G(gg);}
function mansard(P,{w,d,h=60,c}){const g=G();const m=new THREE.Mesh(new THREE.CylinderGeometry(Math.SQRT1_2*.72,Math.SQRT1_2,1,4,1).rotateY(Math.PI/4),mat(c||P.roof));m.scale.set(w+16,h,d+16);m.position.y=h/2;g.add(m,bx(w+18,4,d+18,P.trim,0,1,0),bx((w+16)*.72,4,(d+16)*.72,P.trim,0,h,0));
  for(let x=-w/2+12;x<=w/2-10;x+=w/8)g.add(bx(1.5,h,(d+16)*0.86,P.roof2||0x222,x,h/2,0));return g;}
function turret(P,{r=40,h=H*1.6,cap='cone',capH,c,win=4,levels=1,vane:o_vane=false}){const g=G();c=c||P.wall;
  g.add(cy(r,r,h,c,0,h/2,0,36));g.add(cy(r+3,r+3,8,P.base||P.trim,0,4,0,36));
  for(let L=0;L<levels;L++){const y0=L*h/levels;g.add(tor(r+1.5,2,P.trim,0,y0+h/levels-4,0).rotateX(Math.PI/2));
    for(let k=0;k<win;k++){const a=k/win*Math.PI*2+Math.PI/win*(L%2);const wm=windowM(P,16,34,'arch');wm.position.set(Math.sin(a)*r,y0+h/levels*.55,Math.cos(a)*r);wm.rotation.y=a;g.add(wm);}}
  if(P.brick)for(let y=10;y<h;y+=9)g.add(tor(r+.3,.5,P.brick,0,y,0).rotateX(Math.PI/2));
  if(cap=='cone'){capH=capH||r*2.8;g.add(cy(r+8,r+8,4,P.trim,0,h+2,0,36));const cn=cone(r+7,capH,P.capC||P.roof,0,h+4+capH/2,0,36);g.add(cn);
    for(let k=1;k<5;k++)g.add(tor((r+7)*(1-k/5)+.5,1.3,P.roof2||0x222,0,h+4+capH*k/5,0).rotateX(Math.PI/2));
    for(let k=0;k<24;k++){const a=k/24*Math.PI*2;g.add(sp(3.4,P.trim,Math.sin(a)*(r+7),h+3,Math.cos(a)*(r+7)));}
    g.add(at(o_vane?vane(P):finial(P.metal||0xd4a017),0,h+4+capH-2,0));}
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
  const e=sp(3,0,0,h+15,0,new THREE.MeshBasicMaterial({color:0xff7a3d}));g.add(e);const sm=[];for(let k=0;k<7;k++){const s=new THREE.Sprite(new THREE.SpriteMaterial({map:puffTex(),transparent:true,opacity:.0,depthWrite:false,color:0xf1ede6}));s.position.set(-7,h+20,0);s.userData.k=k/7;g.add(s);sm.push(s);}g.userData.smoke={sm,y0:h+18};return g;}
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
function lamppost(P){const g=G(cy(6,8,6,0x222,0,3,0,8),cy(1.6,2,110,0x222,0,58,0,8),bx(16,1.5,1.5,0x222,0,108,0),cy(6,4,14,0,0,118,0,6,new THREE.MeshBasicMaterial({color:0xffd58a})),cone(8,9,0x222,0,129,0,6),sp(2,0x222,0,135,0));g.userData.halo=V3(0,118,0);return g;}
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
// ---------- v3 showpiece components (match build_grand_v3.py STLs) ----------
let _puff,_halo;
function puffTex(){if(!_puff)_puff=mkTex(cvs(64,64,(x,w,h)=>{const g=x.createRadialGradient(32,32,2,32,32,30);g.addColorStop(0,'rgba(255,255,255,.9)');g.addColorStop(.5,'rgba(255,255,255,.35)');g.addColorStop(1,'rgba(255,255,255,0)');x.fillStyle=g;x.fillRect(0,0,64,64);}));return _puff;}
function haloTex(){if(!_halo)_halo=mkTex(cvs(128,128,(x)=>{const g=x.createRadialGradient(64,64,0,64,64,64);g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.12,'rgba(255,240,210,.8)');g.addColorStop(.4,'rgba(255,200,140,.22)');g.addColorStop(1,'rgba(255,180,120,0)');x.fillStyle=g;x.fillRect(0,0,128,128);}));return _halo;}
function vane(P){const c=P.vaneC||0x2b2b2b,gd=P.metal||0xd4a017;const g=G(cy(5,5,4,c,0,2,0,12),sp(4,gd,0,8,0),cy(1.2,1.2,46,c,0,30,0,6),sp(2.6,gd,0,34,0));
  for(let k=0;k<4;k++){const a=k*Math.PI/2;g.add(at(G(bx(24,1,1,c,12,0,0),bx(3.4,4.6,.8,gd,25,0,0)),0,26,0,a));}
  const top=G();const sh=new THREE.Shape();[[-22,0],[-14,4],[-6,2],[2,4],[8,10],[10,18],[14,20],[16,17],[13,14],[14,8],[18,4],[16,0],[6,-2],[-2,-4],[-10,-2],[-16,4],[-26,14],[-28,8],[-24,2]].forEach(([x,y],i)=>i?sh.lineTo(x,y):sh.moveTo(x,y));
  const r=new THREE.Mesh(new THREE.ExtrudeGeometry(sh,{depth:1.4,bevelEnabled:false}),mat(gd,{metalness:.9,roughness:.25,flat:1}));r.scale.setScalar(.55);r.position.set(0,46,-.7);top.add(r,bx(40,1,1,c,0,42,0),cone(2.2,5,gd,21,42,0,4).rotateZ(-Math.PI/2));
  g.add(top);g.userData.spin=top;return g;}
function porteCochere(P,{w=228,d=120,h=92}={}){const g=G();g.add(bx(w,6,d,P.stone||0xb9b2a6,0,3,d/2));
  for(const x of[-w/2+10,w/2-10])for(const z of[10,d-10]){g.add(bx(18,8,18,P.stone||0xb9b2a6,x,6,z));for(const[dx,dz]of[[-3,-3],[3,-3],[-3,3],[3,3]])g.add(cy(2.2,2.2,h-16,P.post||P.trim,x+dx,10+(h-16)/2,z+dz,10));g.add(bx(18,6,18,P.trim,x,h-4,z),cy(7,5,6,P.trim,x,h-10,z,12));
    for(const y of[30,58])g.add(tor(6.5,1,P.metal||0xd4a017,x,y,z).rotateX(Math.PI/2));const L=lantern(P);L.position.set(x+(x<0?-12:12),60,z);g.add(L);}
  const beam=(L,x,z,ry)=>{const b=G(bx(L,14,6,P.trim,0,h,0));const n=Math.round(L/30);for(let k=0;k<n;k++){const a=tor(L/n/2-3,2.2,P.lace||P.trim,-L/2+L/n*(k+.5),h-7,0,Math.PI);b.add(a);b.add(sp(1.8,P.metal||0xd4a017,-L/2+L/n*(k+.5),h-7+L/n/2-2,2));}at(b,x,0,z,ry);g.add(b);};
  beam(w-20,0,10,0);beam(w-20,0,d-10,0);beam(d-20,-w/2+10,d/2,Math.PI/2);beam(d-20,w/2-10,d/2,Math.PI/2);
  g.add(bx(w+8,6,d+8,P.trim,0,h+10,d/2),bx(w,2,d,P.roof,0,h+7,d/2));
  for(let x=-w/2;x<=w/2;x+=9)g.add(cy(1.4,1.4,16,P.trim,x,h+21,-4+0,6),cy(1.4,1.4,16,P.trim,x,h+21,d+4,6));for(let z=0;z<=d;z+=9)g.add(cy(1.4,1.4,16,P.trim,-w/2-4,h+21,z,6),cy(1.4,1.4,16,P.trim,w/2+4,h+21,z,6));
  g.add(bx(w+10,3,4,P.trim,0,h+30,-4),bx(w+10,3,4,P.trim,0,h+30,d+4),bx(4,3,d+10,P.trim,-w/2-4,h+30,d/2),bx(4,3,d+10,P.trim,w/2+4,h+30,d/2));
  for(const x of[-w/2-4,w/2+4])for(const z of[-4,d+4])g.add(cy(5,5,8,P.trim,x,h+34,z,10),sp(5,P.urn||P.metal||0xd4a017,x,h+42,z));
  const ch=chandelier();ch.position.set(0,h-2,d/2);g.add(ch);g.userData.halo=V3(0,h-20,d/2);return g;}
function lantern(P){const g=G(bx(7,1.4,7,0x222,0,0,0),cy(2.8,2.8,10,0,0,6,0,8,glass(0xffc46b,'p')),cone(5,5,0x222,0,13.5,0,4),sp(1.2,P.metal||0xd4a017,0,17,0));g.userData.halo=V3(0,6,0);return g;}
function spiralStair(P,{h=LV}={}){const g=G(cy(4,4,h+10,0x2b2b2b,0,(h+10)/2,0,12),sp(5,P.metal||0xd4a017,0,h+12,0));const n=16,da=Math.PI*2*.85/n,R=34;let prev=null;
  for(let k=0;k<n;k++){const a=k*da;const t=bx(R,2.4,12,P.deck||0x8b6b4a,R/2,0,0);const tg=G(t);tg.rotation.y=-a;tg.position.y=(k+1)*h/n;g.add(tg);
    const p=V3(Math.cos(a)*(R-2),(k+1)*h/n,-Math.sin(a)*(R-2));g.add(tubeM(p,p.clone().add(V3(0,30,0)),0x2b2b2b,.8));const q=p.clone().add(V3(0,30,0));if(prev)g.add(tubeM(prev,q,P.metal||0xd4a017,1.4));prev=q;}return g;}
function gardenGate(P){const g=G(),ir=0x1f1f1f,st=P.stone||0xb9b2a6;for(const x of[-68,68]){g.add(bx(24,96,24,st,x,48,0),bx(30,6,30,P.trim,x,99,0),cy(7,7,10,st,x,107,0,12));const L=lantern(P);L.scale.setScalar(1.4);L.position.set(x,113,0);g.add(L);}
  for(const s of[-1,1]){const gg=G();for(let k=0;k<8;k++){const x=s*(4+k*7.2),top=86+6*Math.sin((k+.5)/8*Math.PI);gg.add(cy(.9,.9,top-6,ir,x,3+(top-6)/2,0,6),cone(1.8,5,P.metal||0xd4a017,x,top,0,4));}
    gg.add(bx(56,2.4,2,ir,s*30,8,0),bx(56,2.4,2,ir,s*30,52,0),bx(56,2.4,2,ir,s*30,78,0));for(const dx of[-9,9])gg.add(tor(7,1,ir,s*30+dx,66,0));gg.add(sp(3,P.metal||0xd4a017,s*30,66,0));g.add(gg);}
  const ar=tor(56,1.6,ir,0,100,0,Math.PI);g.add(ar);for(let k=0;k<9;k++){const a=k/8*Math.PI;g.add(sp(2.6,[0xf472b6,0xffffff,0xfb7185][k%3],Math.cos(a)*56,100+Math.sin(a)*56,0));}
  return g;}
function lampCluster(P){const c=P.lampC||0x1f2937,g=G(bx(26,8,26,P.stone||0xb9b2a6,0,4,0),cy(10,12,14,c,0,15,0,16),cy(3.4,4.2,140,c,0,92,0,12),cy(7,6,6,c,0,90,0,16));
  const hs=[];for(let k=0;k<3;k++){const a=k*Math.PI*2/3;const ex=V3(Math.sin(a)*30,172,Math.cos(a)*30);g.add(tubeM(V3(0,160,0),V3(Math.sin(a)*15,176,Math.cos(a)*15),c,1.4),tubeM(V3(Math.sin(a)*15,176,Math.cos(a)*15),ex,c,1.4));
    g.add(cy(5,4,4,c,ex.x,ex.y+2,ex.z,10),sp(8,0,ex.x,ex.y+11,ex.z,glass(0xfff1c1,'p')),cy(3,4,3,c,ex.x,ex.y+20,ex.z,8));hs.push(V3(ex.x,ex.y+11,ex.z));}
  g.add(sp(9,0,0,186,0,glass(0xfff1c1,'p')),cone(5,10,c,0,199,0,8),sp(2,P.metal||0xd4a017,0,206,0));hs.push(V3(0,186,0));g.userData.halos=hs;return g;}
function flowerBed(P,{L=120,dep=16}){const g=G(bx(L,5,dep,0x4a3424,0,2.5,0));const cols=P.blooms||[0xf472b6,0xfacc15,0xffffff,0xc084fc,0xfb7185,0x60a5fa];
  for(let k=0;k<L/3;k++){const x=(rnd()-.5)*(L-6),z=(rnd()-.5)*(dep-4),y=5+rnd()*8;g.add(cy(.4,.4,y,0x3f7a35,x,y/2,z,4));const b=sp(1.6+rnd()*1.6,cols[k%cols.length],x,y+1,z);g.add(b);}
  for(let x=-L/2;x<=L/2;x+=7)g.add(sp(4,0x3f6b35,x,4,dep/2-2));return g;}
function roseBush(P){const g=G();for(let k=0;k<7;k++)g.add(sp(7+rnd()*3,0x2f5d2a,(rnd()-.5)*14,8+rnd()*10,(rnd()-.5)*14));for(let k=0;k<12;k++){const a=rnd()*6.28,y=6+rnd()*16;g.add(sp(2.2,P.rose||0xe11d48,Math.cos(a)*11,y,Math.sin(a)*11));}return g;}
function mushroom(s=1){const c=[0xdc2626,0xf59e0b,0xa855f7][Math.floor(rnd()*3)];const g=G(cy(2,2.6,8,0xf5f0e6,0,4,0,8));const cap=sp(6,c,0,9,0);cap.scale.y=.55;g.add(cap);for(let k=0;k<5;k++){const a=k*1.25;g.add(sp(.9,0xffffff,Math.cos(a)*3.6,11,Math.sin(a)*3.6));}g.scale.setScalar(s);return g;}
function pond(P,{r=44}={}){const g=G(cy(r+6,r+8,4,P.stone||0xb9b2a6,0,2,0,24));const w=cy(r,r,1,0,0,4.4,0,32,new THREE.MeshStandardMaterial({color:0x2a6f8f,roughness:.05,metalness:.3,emissive:0x0b3550,emissiveIntensity:.4}));g.add(w);
  for(let k=0;k<5;k++){const a=rnd()*6.28,rr=rnd()*r*.7;const pad=cy(5,5,.6,0,Math.cos(a)*rr,5.2,Math.sin(a)*rr,12,mat(0x3f8f3f));g.add(pad);if(k%2==0)g.add(sp(1.8,0xfbcfe8,Math.cos(a)*rr,6.5,Math.sin(a)*rr));}
  for(let k=0;k<14;k++){const a=k/14*6.28;g.add(sp(4+rnd()*3,0x8a8278,Math.cos(a)*(r+6),4,Math.sin(a)*(r+6)));}return g;}
function bench(P){return G(bx(40,2,10,P.deck||0x8b6b4a,0,14,0),bx(40,10,2,P.deck||0x8b6b4a,0,22,-5),bx(2,14,10,0x222,-18,7,0),bx(2,14,10,0x222,18,7,0),tor(4,.6,0x222,-18,8,5.2),tor(4,.6,0x222,18,8,5.2));}
function conservatory(P,{w=200,d=110,h=96}={}){const g=G(bx(w,10,d,P.stone||0x8f8a99,0,5,d/2));const fr=P.metal||0xe8c468,gl=new THREE.MeshStandardMaterial({color:0x9fd8d0,transparent:true,opacity:.28,roughness:.05,metalness:.2,emissive:0x2dd4bf,emissiveIntensity:.12,depthWrite:false});GLOW.push(gl);
  const n=8;for(let k=0;k<=n;k++){const x=-w/2+k*w/n;g.add(bx(2.4,h,2.4,fr,x,10+h/2,d-1),bx(2.4,h,2.4,fr,x,10+h/2,1));}for(let k=0;k<=5;k++){const z=k*d/5;g.add(bx(2.4,h,2.4,fr,-w/2,10+h/2,z),bx(2.4,h,2.4,fr,w/2,10+h/2,z));}
  g.add(bx(w,h,1,0,0,10+h/2,d-1,gl),bx(1,h,d,0,-w/2,10+h/2,d/2,gl),bx(1,h,d,0,w/2,10+h/2,d/2,gl));for(const y of[30,10+h])g.add(bx(w+4,3,d+2,fr,0,y,d/2));
  // barrel-vault glass roof with ribs
  const R=d/2;const vault=new THREE.Mesh(new THREE.CylinderGeometry(R,R,w,24,1,true,0,Math.PI),gl);vault.rotation.z=Math.PI/2;vault.rotation.y=0;vault.position.set(0,10+h,d/2);vault.rotation.set(0,0,Math.PI/2);g.add(vault);
  for(let k=0;k<=n;k++){const x=-w/2+k*w/n;const rib=tor(R,1.4,fr,x,10+h,d/2,Math.PI);rib.rotation.y=Math.PI/2;g.add(rib);}
  g.add(cy(1.6,1.6,w+10,fr,0,10+h+R,d/2,8).rotateZ(Math.PI/2));for(let x=-w/2;x<=w/2;x+=w/4)g.add(at(finial(fr),x,10+h+R,d/2));
  for(let k=0;k<6;k++){const x=-w/2+20+k*(w-40)/5;g.add(at(G(cy(6,4,10,0xb4673d,0,5,0,10),sp(10,0x3f8f3f,0,18,0),sp(2,0xf472b6,4,24,5),sp(2,0xfacc15,-5,22,3)),x,10,d/2+(k%2?20:-20)));}
  const ch=chandelier();ch.scale.setScalar(1.2);ch.position.set(0,10+h+R-4,d/2);g.add(ch);g.userData.halo=V3(0,10+h+R-30,d/2);return g;}
function dynamo(P){const fr=P.metal||0xe8c468;const g=G(bx(70,8,60,P.stone||0x8f8a99,0,4,0),cy(16,16,40,0x334155,0,30,0,16).rotateZ(Math.PI/2),bx(10,30,40,0x1f2937,-28,23,0),bx(10,30,40,0x1f2937,28,23,0));
  const gr=gear(fr,18,0,30,22,0);g.add(gr);g.userData.spin2=gr.userData.spin;
  const dial=G(cy(9,9,2,fr,0,0,0,24),cy(7,7,2.4,0,0,0,0,24,glass(0x86efac,'p')));dial.children.forEach(m=>m.rotation.x=Math.PI/2);dial.position.set(-28,40,21);g.add(dial);
  for(const x of[-20,0,20]){g.add(cy(3,3,8,0xf5f5f4,x,52,-18,8),cy(4.5,4.5,2,0xf5f5f4,x,56,-18,8));}
  g.userData.halo=V3(-28,40,24);return g;}
function plaque(name,sub){const c=cvs(1024,128,(x,w,h)=>{const g=x.createLinearGradient(0,0,0,h);g.addColorStop(0,'#e9c46a');g.addColorStop(.5,'#c99a2e');g.addColorStop(1,'#8a6514');x.fillStyle=g;x.fillRect(0,0,w,h);x.strokeStyle='#5a400c';x.lineWidth=8;x.strokeRect(8,8,w-16,h-16);
  x.fillStyle='#3a2806';x.font='italic 600 54px Georgia,serif';x.textAlign='center';x.fillText(name,w/2,66);x.font='26px Georgia,serif';x.fillText(sub,w/2,104);});const t=mkTex(c);t.wrapS=t.wrapT=THREE.ClampToEdgeWrapping;return new THREE.MeshStandardMaterial({map:t,metalness:.7,roughness:.35});}
// ---------- scene plumbing ----------
let renderer,scene,camera,controls,root,parts=[],spinners=[],target=0,ex=0,night=false,spin=!Q.has('nospin'),lights=[],HALOS=[],WIRES=[],PULSES=[],SMOKES=[],FLIES=null;
const vis={roof:1,wall:1,furn:1,garden:1,light:1,wire:1,panel:1,orn:1,base:1};
const MAXPL=Q.has('lite')?2:7;
function put(obj,grp,layer,lv=0){root.add(obj);parts.push({m:obj,by:obj.position.y,lift:layer*55+lv*120,grp});
  obj.traverse(o=>{if(o.userData){if(o.userData.spin)spinners.push(o.userData.spin);if(o.userData.spin2)spinners.push(o.userData.spin2);if(o.userData.smoke)SMOKES.push(o.userData.smoke);
    if(o.userData.halo)addHalo(o,o.userData.halo,grp=='garden'?46:22);if(o.userData.halos)o.userData.halos.forEach(h=>addHalo(o,h,40));}
    if(o.isMesh){const m=o.material;const lit=m&&(m.transparent||m.isMeshBasicMaterial||(m.emissiveIntensity>0&&m.userData&&m.userData.keepUV));o.castShadow=!lit;o.receiveShadow=!m.transparent;}});return obj;}
function addHalo(o,p,s,c=0xffd9a0){const sp_=new THREE.Sprite(new THREE.SpriteMaterial({map:haloTex(),color:c,transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,opacity:0}));sp_.position.copy(p);sp_.scale.set(s,s,1);sp_.userData.s=s;o.add(sp_);HALOS.push(sp_);return sp_;}
function glowLight(x,y,z,c=0xffb35c,i=.9,d=260){const h=new THREE.Object3D();h.position.set(x,y,z);root.add(h);if(lights.length<MAXPL){const l=new THREE.PointLight(c,0,d,1.6);l.position.set(x,y,z);l.userData.i=i;root.add(l);lights.push(l);}return h;}
function chan(a,b,lv,col=0xfacc15,r=1.4,grp='light',layer=1){put(tubeM(a,b,col,r),grp,layer,lv);}
function roomLights(x,z,w,d,y,lv,wired){const yy=y+F+H-4;const c=[[x-w/2+6,z-d/2+6],[x+w/2-6,z-d/2+6],[x+w/2-6,z+d/2-6],[x-w/2+6,z+d/2-6]];
  for(let k=0;k<4;k++){const a=c[k],b=c[(k+1)%4];chan(V3(a[0],yy,a[1]),V3(b[0],yy,b[1]),lv,wired?0x22d3ee:0xfacc15,wired?2:1.3,wired?'wire':'light');if(wired)WIRES.push([V3(a[0],yy,a[1]),V3(b[0],yy,b[1])]);}
  chan(V3(c[0][0],y+F,c[0][1]),V3(c[0][0],yy,c[0][1]),lv,wired?0x22d3ee:0xfacc15,wired?2.2:1.3,wired?'wire':'light');
  glowLight(x,y+F+H*.7,z,0xffb35c,.8,w+d);}
function jpanel(P,k){const J=P.jewels||['#a855f7'];const col=new THREE.Color(J[k%J.length]);const g=G();
  const m=new THREE.MeshStandardMaterial({color:col.clone().multiplyScalar(.6),emissive:col,emissiveIntensity:.5,roughness:.15,metalness:.3,map:sgTex(J.slice(k%J.length).concat(J.slice(0,k%J.length)),k),emissiveMap:sgTex(J.slice(k%J.length).concat(J.slice(0,k%J.length)),k)});m.userData.keepUV=1;GLOW.push(m);
  g.add(bx(56,76,1.4,0,0,0,0,m),bx(64,84,1.2,P.metal||0xd4a017,0,0,-.8));const fr=P.metal||0xd4a017;g.add(bx(64,4,3,fr,0,40,.6),bx(64,4,3,fr,0,-40,.6),bx(4,84,3,fr,-30,0,.6),bx(4,84,3,fr,30,0,.6),tor(10,1.4,fr,0,40,1.4,Math.PI));
  for(const[x,y]of[[-30,-40],[30,-40],[-30,40],[30,40]])g.add(sp(2.6,0x94a3b8,x,y,2.2));g.add(bx(10,6,2,0x111,0,-30,1.6),sp(1.4,0x22c55e,0,-30,2.8,new THREE.MeshBasicMaterial({color:0x4ade80})));g.userData.halo=V3(0,0,6);return g;}
// house builder sugar
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
   case'lampc':g=lampCluster(P);grp='garden';layer=.4;glowLight(x,180,z,0xffe2a8,1.1,220);break;
   case'gwall':g=gardenWall(P,o);grp='garden';layer=.3;break;
   case'hedge':g=hedge(P,o);grp='garden';layer=.3;break;
   case'box':g=G(bx(o.w,o.h,o.d,o.c||P.trim,0,o.h/2,0));grp=o.grp||'wall';layer=o.layer!=null?o.layer:1+lv;break;
   case'lady':g=lady(o.c);grp='furn';layer=3+lv;break;case'gent':g=gent(o.c);grp='furn';layer=3+lv;break;case'child':g=child(o.c);grp='furn';layer=3+lv;break;case'cat':g=cat();grp='furn';layer=3+lv;break;
   case'bed':g=fourPoster(o.c);grp='furn';layer=3+lv;break;case'chair':g=wingback(o.c);grp='furn';layer=3+lv;break;case'gclock':g=clock();grp='furn';layer=3+lv;break;
   case'chand':g=chandelier();grp='furn';layer=3+lv;break;
   case'airship':g=airship(P);grp='orn';layer=9;spinners.push({air:g,y0:y});break;
   case'string':g=stringLights(o.a,o.b,o.n,o.sag);grp='garden';layer=.6;break;
   case'tesla':g=tesla(P);grp='orn';layer=9;spinners.push({tesla:g.userData.bolt,g});addHalo(g,V3(0,74,0),90,0xc4b5fd);glowLight(x,y+74,z,0xa78bfa,1.4,400);break;
   case'panel':g=jpanel(P,o.k||0);grp='panel';layer=1+lv*1.6;break;
   case'wire':{const pts=o.pts;for(let k=0;k<pts.length-1;k++){put(tubeM(V3(...pts[k]),V3(...pts[k+1]),o.col||0x22d3ee,o.r||2.2),'wire',o.layer||1);WIRES.push([V3(...pts[k]),V3(...pts[k+1])]);}
     for(let k=1;k<pts.length-1;k++)put(G(sp((o.r||2.2)*1.9,0xf5f5f4)).translateX(pts[k][0]).translateY(pts[k][1]).translateZ(pts[k][2]),'wire',o.layer||1);continue;}
   case'glowbox':g=G(bx(o.w,o.h,o.d,0,0,o.h/2,0,glass(o.c||0xffd58a,'p')));grp='orn';layer=o.layer||3;break;
   case'vane':g=vane(P);grp='orn';layer=9;break;
   case'pcochere':g=porteCochere(P,o);layer=2.5;glowLight(x,80,z,0xffd58a,.9,200);break;
   case'spiral':g=spiralStair(P,o);grp='furn';layer=3+lv;break;
   case'gate':g=gardenGate(P);grp='garden';layer=.4;break;
   case'flowers':g=flowerBed(P,o);grp='garden';layer=.25;break;
   case'rose':g=roseBush(P);grp='garden';layer=.25;break;
   case'shroom':g=mushroom(o.s||1);grp='garden';layer=.2;break;
   case'pond':g=pond(P,o);grp='garden';layer=.2;break;
   case'bench':g=bench(P);grp='garden';layer=.3;break;
   case'conserv':g=conservatory(P,o);layer=2.5;glowLight(x+60,90,z,0x99f6e4,.9,220);break;
   case'dynamo':g=dynamo(P);grp='wire';layer=1;glowLight(x,50,z,0x86efac,.9,160);break;
   case'sconce':g=sconce(P);g.scale.setScalar(1.6);grp='orn';layer=3+lv;break;
   default:continue;}
  at(g,x,y+(o.dy||0),z,ry);if(o.s&&t!='tree'&&t!='shroom')g.scale.setScalar(o.s);put(g,grp,layer,0);}}
function base(P,w,d){const g=G(bx(w,8,d,P.lawn||0x5f8f4a,0,-4,0));
  const wd=P.plinth||0x4a2f1e;g.add(bx(w+30,22,d+30,wd,0,-19,0),bx(w+36,4,d+36,P.plinthTrim||0xc9a227,0,-8,0),bx(w+42,8,d+42,wd,0,-34,0),bx(w+46,3,d+46,P.plinthTrim||0xc9a227,0,-39.5,0));
  const pl=new THREE.Mesh(new THREE.BoxGeometry(220,26,1.5),plaque(CUR_H.name,'1:24 · Grand v3 · Meadowlark Models'));pl.position.set(0,-20,d/2+15.8);pl.userData.keepUV=1;g.add(pl);
  for(let k=0;k<Math.round((w+d)/6);k++){const side=k%4,t=rnd()-.5;const px=side<2?t*w*.96:(side==2?-1:1)*(w/2-5),pz=side<2?(side==0?-1:1)*(d/2-5):t*d*.96;g.add(sp(1.8+rnd()*1.6,(P.blooms||[0xf472b6,0xfacc15,0xffffff,0xc084fc])[k%4],px,1.5+rnd()*2,pz));if(k%3==0)g.add(sp(3.4,0x3f6b35,px*.99,2,pz*.99));}
  for(let k=0;k<160;k++){const x=(rnd()-.5)*w*.98,z=(rnd()-.5)*d*.98;g.add(cone(1.2+rnd(),3+rnd()*4,[0x4f7d3a,0x6a9a4a,0x3f6b35][k%3],x,1.5,z,4));}
  put(g,'base',0,0);
  if(!FLIES){}}
function path(P,x,z,w,d){const g=G();for(let zz=-d/2;zz<d/2;zz+=12)g.add(bx(w*(.8+rnd()*.2),2,10,P.stone||0xb9b2a6,(rnd()-.5)*4,1,zz));put(at(g,x,0,z),'garden',.2,0);}
function worldUV(mesh,S=48){const g=mesh.geometry;const p=g.attributes.position,n=g.attributes.normal;if(!p||!n)return;const sc=mesh.scale;const uv=new Float32Array(p.count*2);
  for(let i=0;i<p.count;i++){const x=p.getX(i)*sc.x,y=p.getY(i)*sc.y,z=p.getZ(i)*sc.z,ax=Math.abs(n.getX(i)),ay=Math.abs(n.getY(i)),az=Math.abs(n.getZ(i));let u,v;
    if(ax>=ay&&ax>=az){u=z;v=y;}else if(ay>=az){u=x;v=z;}else{u=x;v=y;}uv[i*2]=u/S;uv[i*2+1]=v/S;}g.setAttribute('uv',new THREE.BufferAttribute(uv,2));}
// ---------- palettes (v3 colour stories) ----------
const PAL={
 cottage:{wall:0xf1e4c8,wallTex:'stucco',trim:0xfffaf0,roof:0x6b8f4e,roof2:0x40602f,shutter:0x2a8f86,flowers:1,lace:0xfffaf0,chim:0x9a8a7c,stone:0xc2ae8f,quoin:0xd6c6a6,siding:0xe9dcbc,door:0xb83a4b,leaf:0x6a9a4a,gable:0xf4cdb3,metal:0xc9a227,metal2:0x5f9e8f,capC:0x5f9e8f,deck:0x9c7a55,ivy:.5,frieze:0xf4cdb3,
   jewels:['#e11d48','#f59e0b','#22c55e','#38bdf8','#a855f7'],blooms:[0xf472b6,0xfacc15,0xffffff,0xc084fc,0xfb7185],lawn:0x6f9a4f,plinth:0x5a3a24,sky:['#7fb2d6','#f7d9b5'],skyN:['#0b1230','#3b2a4a']},
 ranch:{wall:0xf3cf6a,wallTex:'clap',trim:0xfffbeb,roof:0x4a6a86,roof2:0x2f4a63,shutter:0x274b73,siding:0xe6c25e,lace:0xfffbeb,chim:0xa24936,stone:0xc9bfa8,door:0x274b73,metal:0xd4a017,metal2:0x5b9c8f,capC:0x5b9c8f,deck:0x8b6b4a,post:0xffffff,pediment:1,frieze:0xfef3c7,pilaster:0xffffff,
   jewels:['#2563eb','#f59e0b','#fef3c7','#7c3aed','#0ea5e9'],lawn:0x7aa55a,plinth:0x3d2a1c,sky:['#8ec5e8','#fbe7c6'],skyN:['#081028','#2a2050']},
 town:{wall:0xd9466f,wallTex:'brick',trim:0xfdf2f8,roof:0x34303a,roof2:0x18161b,shutter:0x0f766e,flowers:1,lace:0xfdf2f8,brick:0xc93d6a,chim:0x7a3b52,stone:0xbab2a6,door:0x0f766e,metal:0xd4a017,metal2:0x3f9e8e,capC:0x3f9e8e,gable:0xf9a8d4,pediment:1,frieze:0xf9a8d4,ivy:.2,
   jewels:['#ec4899','#14b8a6','#fbbf24','#8b5cf6','#f43f5e'],lawn:0x6a9a52,plinth:0x2e1f2a,sky:['#c4a7e7','#ffd6e0'],skyN:['#120a24','#3a1838']},
 court:{wall:0xe8c49a,wallTex:'stucco',trim:0xf7ecd9,roof:0xb8552f,roofTex:'tile',roof2:0x8a3a1f,shutter:0x2f5f8a,stone:0xd8c8aa,quoin:0xd3b88c,door:0x6b3e1f,metal:0xd4a017,metal2:0x5b8f8a,post:0xf7ecd9,lawn:0x7aa05a,leaf2:0x2f5d3a,ivy:.35,frieze:0xe0b07a,
   jewels:['#1d4ed8','#f59e0b','#b91c1c','#0d9488','#fde68a'],blooms:[0xd946ef,0xf472b6,0xfb923c,0xffffff],rose:0xd946ef,plinth:0x4a3020,sky:['#f3b27a','#fde7c8'],skyN:['#14102a','#4a2a2a']},
 shop:{wall:0x8a4a36,wallTex:'brick',trim:0xe0bf82,roof:0x5a9a88,roofTex:'copper',roofMetal:.5,roof2:0x2f6156,brick:0x5c3428,chim:0x7a3b2a,stone:0x6b6259,door:0x2f2015,metal:0xc68a3c,metal2:0x4f9a86,capC:0x4f9a86,shutter:0x2f6156,deck:0x5b4334,quoin:0xa36a4f,frieze:0x5c3428,
   jewels:['#f59e0b','#84cc16','#fde68a','#ea580c','#0891b2'],lawn:0x6b8f4a,plinth:0x2b1d14,sky:['#d9b48a','#f3e2c4'],skyN:['#0d0c18','#33200f']},
 wired:{wall:0x4a2558,wallTex:'clap',trim:0xe8c468,roof:0x2c6e63,roof2:0x1d453f,shutter:0x1d453f,lace:0xe8c468,brick:0x3a1f46,chim:0x3a1f46,stone:0x8f8a99,door:0x1d453f,metal:0xe8c468,metal2:0x3f9f8a,capC:0x3f9f8a,quoin:0x6b4580,flowers:1,deck:0x3f2e2a,post:0xe8c468,wired:1,gable:0x5e3570,pediment:1,frieze:0x2c1736,pilaster:0x6b4580,tympanum:0x2c1736,siding:0x40204d,
   jewels:['#a855f7','#10b981','#3b82f6','#e11d48','#facc15'],blooms:[0xa855f7,0xe879f9,0xfacc15,0x22d3ee],lawn:0x4f7a45,plinth:0x1c1024,plinthTrim:0xe8c468,crest:0xe8c468,sky:['#3b2a66','#e9a5c8'],skyN:['#05040f','#1e0f3a']}
};
GEN.tile=(x,w,h)=>{x.fillStyle='#8a8a8a';x.fillRect(0,0,w,h);const cw=w/6,rh=h/6;for(let r=0;r<7;r++)for(let k=0;k<6;k++){const g=x.createLinearGradient(k*cw,0,k*cw+cw,0);const v=180+Math.random()*60|0;g.addColorStop(0,`rgb(${v*.7|0},${v*.7|0},${v*.7|0})`);g.addColorStop(.5,`rgb(${v},${v},${v})`);g.addColorStop(1,`rgb(${v*.6|0},${v*.6|0},${v*.6|0})`);x.fillStyle=g;x.beginPath();x.ellipse(k*cw+cw/2,r*rh,cw/2,rh*.62,0,0,Math.PI*2);x.fill();}noise(x,w,h,3000,.1);};
function roles(P){for(const k in ROLE)delete ROLE[k];const S=(c,r)=>{if(c!=null)ROLE[c]=r;};
  S(P.trim,{t:'stucco',b:.12,r:.55});S(P.siding,{t:P.wallTex||'clap',b:.4});S(P.gable,{t:P.wallTex=='brick'?'stucco':(P.wallTex||'clap'),b:.4});S(P.wall,{t:P.wallTex||'clap',b:.55});S(P.brick,{t:'brick',b:.6});
  S(P.stone,{t:'stone',b:.9});S(P.quoin,{t:'stone',b:.7});S(P.chim,{t:'brick',b:.8});S(P.deck,{t:'plank',b:.5});S(P.door,{t:'wood',b:.4,r:.5});S(P.lawn,{t:'grass',b:.5,r:.95});S(P.plinth,{t:'wood',b:.3,r:.35});
  S(P.roof,{t:P.roofTex||'shingle',b:.9,m:P.roofMetal,r:P.roofMetal?.45:.8});S(P.metal2,{t:'copper',b:.3,m:.55,r:.4});S(P.metal,{t:'copper',b:.05,m:.92,r:.26});S(P.plinthTrim||0xc9a227,{t:'copper',b:.05,m:.95,r:.25});}
const HOUSES=[
{id:'cottage0',name:'Bramble Cottage',old:'Cottage-0',size:'2 × 2 + porch',pal:'cottage',stories:'1½',blurb:'A storybook cottage straight out of a fairy tale: steep mossy roof with two dormers, a witch-hat turret on the corner, a lacy front porch, a fieldstone chimney, and flower boxes under every window.',
 story:'Built by a retired hedge-witch who wanted a cottage that looked like it grew there. The turret holds her reading nook, the dormers are the guest attic, and the chimney never quite stops glowing.',
 bom:{'floor_tile_v0':4,'corner_post_v0':4,'wall_panels (v0c short/full mix)':8,'roof_panel_v2':2,'gable_end_v2':2,'dormer_v2':2,'turret_segment_v2':2,'turret_cap_v2':1,'porch_post_v2':5,'railing_v2':3,'gingerbread_trim_v2':4,'bay_window_v2':1,'chimney_v2':1,'garden_wall_v2':2,'fix_victorian_lamppost_v2':1},
 build(P){base(P,560,520);mk(P,[['room',{w:254,d:254,ops:{S:['w','d','w'],N:['w','w'],E:['w','w'],W:['b','b']},wk:'arch'}],
  ['gable',{y:LV,w:254,d:254,pitch:52,over:14}],['dormer',{x:-60,y:LV+6,z:100}],['dormer',{x:60,y:LV+6,z:100}],
  ['turret',{x:-132,z:132,r:42,h:LV*1.55,capH:140,vane:true}],['porch',{x:20,z:127,w:170,d:64,roof:'gable'}],['bay',{x:-127,z:0,r:44,r_:0,r:-Math.PI/2+0}],
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
  ['pcochere',{x:317,z:-20,r:Math.PI/2}],['bay',{x:-190,z:-127,r:44,r:Math.PI}],
  ['chimney',{x:-250,z:-60,y:LV-10,h:110}],['chimney',{x:250,z:-60,y:LV-10,h:110}],
  ['lady',{x:-60,z:160,y:8,c:0x60a5fa}],['gent',{x:-30,z:165,y:8}],['chair',{x:120,z:150,y:8}],['chair',{x:160,z:150,y:8,c:0x9a3412}],['child',{x:80,z:240}],
  ['lampc',{x:-160,z:250}],['lampc',{x:160,z:250}],['tree',{x:-380,z:-220,s:1.3}],['tree',{x:380,z:-200,s:1.5,kind:'pine'}],['tree',{x:-390,z:230,s:1}],['gwall',{x:-260,z:268,L:240}],['gwall',{x:260,z:268,L:240}],['chand',{y:F+H*1.5-2}]]);
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
  ['fountain',{x:0,z:40}],['turret',{x:-254,z:-254,r:50,h:LV*2.1,cap:'cren'}],['turret',{x:254,z:-254,r:50,h:LV*2.1,cap:'cone',capH:150,vane:true}],
  ['room',{z:254,w:200,d:80,h:H*1.3,ops:{S:['b','D','b'],N:['b','D','b']},open:[]}],['gable',{z:254,y:F+H*1.3,w:200,d:80,pitch:40,over:8}],['turret',{x:-118,z:254,r:28,h:H*1.8,capH:90}],['turret',{x:118,z:254,r:28,h:H*1.8,capH:90}],
  ['room',{x:-254,z:254,w:80,d:80,h:H*.6,ops:{S:['r']}}],['room',{x:254,z:254,w:80,d:80,h:H*.6,ops:{S:['r']}}],
  ['tree',{x:-60,z:120,s:.7,kind:'pine'}],['tree',{x:60,z:120,s:.7,kind:'pine'}],['tree',{x:-60,z:-40,s:.6,kind:'pine'}],['tree',{x:60,z:-40,s:.6,kind:'pine'}],
  ['lady',{x:-30,z:80,c:0xb91c1c}],['gent',{x:30,z:90,c:0x1e3a8a}],['cat',{x:0,z:100,y:16}],['lampc',{x:-150,z:300}],['lampc',{x:150,z:300}],['gwall',{x:-220,z:330,L:180}],['gwall',{x:220,z:330,L:180}],['bed',{x:-190,z:150}],['chair',{x:190,z:100}],['gclock',{x:-200,z:-190}]]);path(P,0,320,50,60);}},
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
  ['lampc',{x:20,z:240}],['tree',{x:-380,z:-220,s:1.2,kind:'pine'}],['tree',{x:-380,z:220,s:1}],['hedge',{x:-210,z:255,L:200}]]);
  for(let k=0;k<3;k++){const gr=G();const xx=180-127+k*127;const s=bx(127,4,140,P.roof,0,0,0);s.rotation.x=-.55;s.position.set(0,38,-4);const gl=bx(125,64,3,0,0,30,64,glass(0xbfe3ff));gl.rotation.x=0;gr.add(s,gl,bx(129,4,6,P.trim,0,64,66));at(gr,xx,F+H*1.25+8,-60);put(gr,'roof',5,0);}
  path(P,180,230,120,50);}},
{id:'wired5',name:'The Electrified Manor',old:'Wired-5',size:'3 × 2 × 3 stories, wired',pal:'wired',stories:3,wired:true,blurb:'The showpiece. A plum-and-gold Second Empire manor with a three-story round tower, a wraparound porch dripping with gingerbread, a mansard roof full of dormers, and a crackling Tesla coil on the tower cap — wired like a real house, with glowing wire runs you can see, magnetic gold-framed service panels, and every fixture lit.',
 story:'A lighting inventor built this to show off her electric miracles. Every room has a switch, every lamp is real, and she left the wiring visible on purpose — wire theater. The Tesla coil is just for drama.',
 bom:{'wired_floor_tile_v1w':6,'upper_floor_tile_v1':10,'wired_corner_post_v1w':18,'wired_wall_short_v1w':8,'wall_panels':28,'wire_theater_panel_v2w':6,'power_module_v1w':1,'turret_segment_v2':6,'turret_cap_v2':1,'dormer_v2':4,'porch_post_v2':12,'railing_v2':9,'gingerbread_trim_v2':10,'bay_window_v2':1,'chimney_v2':2,'edison_sconce_v2w':6,'fix_chandelier_v2':3,'fix_victorian_lamppost_v2':2},
 build(P){base(P,760,600);mk(P,[['room',{w:381,d:254,ops:{S:['W','D','W'],N:['w','w','w'],E:['w','w'],W:['w','w']}}],['room',{lv:1,w:381,d:254,ops:{S:['w','w','w'],N:['w','w','w'],E:['w','w'],W:['w','w']}}],
  ['mansard',{y:LV*2,w:381,d:254,h:H}],['dormer',{x:-100,y:LV*2+34,z:120}],['dormer',{x:0,y:LV*2+34,z:120}],['dormer',{x:100,y:LV*2+34,z:120}],['dormer',{x:0,y:LV*2+34,z:-120,r:Math.PI}],
  ['rail',{y:LV*2+H+2,w:250,d:150}],['turret',{x:-190,z:127,r:52,h:LV*3,levels:3,capH:170}],['tesla',{x:-190,y:LV*3+168,z:127}],
  ['porch',{x:40,z:127,w:300,d:66,posts:8,roof:'shed'}],['conserv',{x:190,z:0,w:220,d:120,r:Math.PI/2}],['bay',{x:-190,z:-30,r:44,r:-Math.PI/2,levels:2}],
  ['chimney',{x:150,z:-90,y:LV*2,h:150}],['chimney',{x:-120,z:-90,y:LV*2,h:150}],
  ['panel',{x:-60,y:F+60,z:-131,r:Math.PI}],['panel',{x:60,y:F+60,z:-131,r:Math.PI}],['panel',{x:-60,y:LV+F+60,z:-131,r:Math.PI}],['panel',{x:60,y:LV+F+60,z:-131,r:Math.PI}],['panel',{x:194,y:LV+F+60,z:-50,r:Math.PI/2}],['panel',{x:-194,y:LV+F+60,z:60,r:-Math.PI/2}],
  ['wire',{pts:[[150,F+30,-130],[150,LV*2+H,-130],[-150,LV*2+H,-130],[-150,F+30,-130],[150,F+30,-130]],r:2.4,layer:1}],
  ['wire',{pts:[[-60,F+20,-130],[-60,LV*2+60,-130]],layer:1}],['wire',{pts:[[60,F+20,-130],[60,LV*2+60,-130]],layer:1}],['wire',{pts:[[-190,F,-80],[-190,LV*3,-80]],layer:2}],
  ['box',{x:0,y:0,z:-150,w:60,h:30,d:24,c:0x334155,grp:'wire',layer:1}],['glowbox',{x:0,y:20,z:-163,w:10,h:4,d:2,c:0x22c55e,layer:1}],
  ['string',{a:V3(-330,120,250),b:V3(-50,F+H+20,150),n:14,sag:20}],['string',{a:V3(330,120,250),b:V3(180,F+H+20,150),n:12,sag:20}],['lampc',{x:-330,z:250}],['lampc',{x:330,z:250}],
  ['chand',{x:0,y:F+H-2}],['chand',{x:-100,y:LV+F+H-2}],['chand',{x:100,y:LV+F+H-2}],['lady',{x:-40,z:170,y:8,c:0xe8c468}],['gent',{x:0,z:175,y:8,c:0x1d453f}],['child',{x:40,z:180,y:8,c:0xa78bfa}],['cat',{x:80,z:170,y:8}],
  ['chair',{x:-80,z:-30}],['bed',{x:90,y:LV,z:-40}],['gclock',{x:140,z:-90}],['tree',{x:330,z:-220,s:1.3,kind:'pine'}],['tree',{x:-350,z:-220,s:1.2}],['gwall',{x:-200,z:290,L:220}],['gwall',{x:200,z:290,L:220}]]);
  parts.filter(p=>p.m.position.x==-190&&p.m.position.z==-30).forEach(p=>p.m.rotation.y=-Math.PI/2);
  path(P,0,240,56,60);}}
];
// fix bay rotation via r key duplicates: handled by mk ry (last r wins in object literal)
// ---------- v3 extra dressing per house ----------
const EXTRA={
 cottage0:[['gate',{x:20,z:248,s:.95}],['lampc',{x:-205,z:195,s:.85}],['pond',{x:-60,z:-205,r:40}],['bench',{x:-140,z:-200,r:.3}],['rose',{x:-110,z:150}],['rose',{x:120,z:150}],['rose',{x:150,z:-150}],
   ['flowers',{x:145,z:0,L:200,dep:16,r:Math.PI/2}],['flowers',{x:0,z:-145,L:200,dep:14}],['shroom',{x:225,z:110,s:1.6}],['shroom',{x:235,z:128,s:1.1}],['shroom',{x:200,z:120,s:.9}],['shroom',{x:-210,z:-120,s:1.3}],['shroom',{x:-245,z:-170,s:1}],
   ['string',{a:V3(-132,150,170),b:V3(100,F+H+30,191),n:14,sag:16}]],
 ranch1:[['gate',{x:0,z:268}],['flowers',{x:-200,z:212,L:170}],['flowers',{x:200,z:212,L:170}],['rose',{x:-340,z:120}],['rose',{x:-340,z:60}],['bench',{x:-300,z:200}],['pond',{x:-300,z:-200,r:44}],['shroom',{x:-380,z:-120,s:1.4}],['shroom',{x:-370,z:-140}],
   ['string',{a:V3(-317,105,150),b:V3(-60,108,200),n:14,sag:14}],['string',{a:V3(60,108,200),b:V3(260,108,150),n:12,sag:14}],['vane',{x:0,y:F*2+H*2.2+28+125*.9+4}]],
 town2:[['gate',{x:30,z:228,s:.75}],['lampc',{x:-185,z:200,s:.9}],['spiral',{x:80,z:-60}],['flowers',{x:-150,z:128,L:40,dep:14}],['rose',{x:-190,z:120}],['rose',{x:190,z:40}],['bench',{x:-120,z:200}],
   ['vane',{x:127,y:LV+LV*2-6+30*2.6+8,z:127}],['shroom',{x:200,z:-120,s:1.3}],['shroom',{x:-200,z:-160}]],
 court3:[['gate',{x:0,z:332,s:1.4}],['flowers',{x:-60,z:-110,L:90,dep:12}],['flowers',{x:60,z:-110,L:90,dep:12}],['rose',{x:-90,z:150}],['rose',{x:90,z:150}],['rose',{x:-320,z:100}],['rose',{x:320,z:100}],
   ['bench',{x:-70,z:150,r:.4}],['bench',{x:70,z:150,r:-.4}],['string',{a:V3(-120,96,-110),b:V3(120,96,180),n:18,sag:20}],['string',{a:V3(120,96,-110),b:V3(-120,96,180),n:18,sag:20}]],
 shop4:[['vane',{x:-50,y:300+112,z:-60}],['flowers',{x:-210,z:200,L:160,dep:14}],['bench',{x:-120,z:210}],['rose',{x:-330,z:140}],['box',{x:340,z:60,w:22,h:22,d:22,c:0x7a5534,grp:'garden',layer:.3}],['box',{x:345,z:90,w:18,h:18,d:18,c:0x8b6b4a,grp:'garden',layer:.3}],
   ['string',{a:V3(-80,180,40),b:V3(330,250,-60),n:16,sag:30}],['lampc',{x:340,z:220,s:.9}]],
 wired5:[['gate',{x:0,z:292,s:1.05}],['dynamo',{x:-255,z:-235}],['flowers',{x:-150,z:205,L:90}],['flowers',{x:150,z:205,L:90}],['rose',{x:-300,z:120}],['bench',{x:-290,z:180}],
   ['wire',{pts:[[-255,6,-205],[-255,6,-150],[0,6,-150]],col:0x22d3ee,r:2.4,layer:1}],
   ['wire',{pts:[[0,6,-150],[300,6,-150],[300,6,250],[330,6,250],[330,170,250]],col:0xf472b6,r:1.8,layer:1}],
   ['wire',{pts:[[0,6,-150],[-300,6,-150],[-300,6,250],[-330,6,250],[-330,170,250]],col:0xf472b6,r:1.8,layer:1}],
   ['wire',{pts:[[190,F+20,-110],[300,F+20,-110],[300,F+20,60]],col:0xfacc15,r:1.8,layer:1}],
   ['wire',{pts:[[-190,LV*3,-80],[-190,LV*3+150,127-60]],col:0xa78bfa,r:1.8,layer:2}],
   ['wire',{pts:[[-150,LV*2+H,-130],[-150,LV*2+H+20,-160],[150,LV*2+H+20,-160],[150,LV*2+H,-130]],col:0xfacc15,r:1.6,layer:2}],
   ['sconce',{x:-40,y:F+52,z:134}],['sconce',{x:40,y:F+52,z:134}],['sconce',{x:-130,y:LV+F+52,z:134}],['sconce',{x:130,y:LV+F+52,z:134}],
   ['panel',{x:-130,y:LV+F+60,z:-131,r:Math.PI,k:2}],['panel',{x:130,y:LV+F+60,z:-131,r:Math.PI,k:3}],['panel',{x:-130,y:F+60,z:-131,r:Math.PI,k:4}],['panel',{x:130,y:F+60,z:-131,r:Math.PI,k:1}],
   ['string',{a:V3(-190,LV*3-10,180),b:V3(0,LV*2+H+10,127),n:16,sag:18}]]
};
const CAM={cottage0:[34,20,.7],ranch1:[28,22,.64],town2:[38,14,.72],court3:[30,28,.68],shop4:[24,18,.66],wired5:[32,16,.68]};
let CUR_H=null;
// ---------- UI ----------
let cur=0;const pills=document.getElementById('pills');
HOUSES.forEach((h,n)=>{const b=document.createElement('button');b.textContent=h.name;b.onclick=()=>{location.hash=h.id;select(n);};pills.appendChild(b);});
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected',x===b));document.querySelectorAll('section').forEach(s=>s.hidden=s.id!==b.dataset.tab);if(b.dataset.tab==='explore')resize();if(b.dataset.tab==='kit'&&window.__gal)window.__gal();});
const WIRE=`<h3>Wiring the Electrified Manor</h3><p><strong>Low voltage only (3–5 V DC, USB or batteries). Never mains.</strong></p><ul>
<li><strong>Trunk:</strong> Ø5 bores up every <code>wired_corner_post_v1w</code> carry 30 AWG silicone pairs between stories. The tower has its own riser to the Tesla-coil LED.</li>
<li><strong>Floors:</strong> <code>wired_floor_tile_v1w</code> centre channels feed the chandelier of the room below.</li>
<li><strong>Wire theater:</strong> the back-wall runs stay visible behind jewel-glass <code>wire_theater_panel_v2w</code> covers (gold arched frames, 4 × Ø6×2 N52 magnets), so you can watch the wiring. The animated sparks in the viewer show current flowing from the dynamo kiosk. Wall magnets face north-out and panel magnets south-out, so any panel fits any wall.</li>
<li><strong>Garden circuit:</strong> pink runs go under the lawn tiles to the two lamppost clusters (<code>lamppost_cluster_v3</code>, 4 LEDs each). Gold runs feed the conservatory chandelier and the roof cresting.</li>
<li><strong>Power:</strong> <code>power_module_v1w</code> (USB-C 5 V trigger or 3×AAA) sits in the dynamo kiosk behind the house, with a green pilot LED and a JST-PH plug per story.</li></ul>
<table><thead><tr><th>Kit</th><th>Qty</th></tr></thead><tbody><tr><td>30 AWG silicone wire red + black</td><td>2 × 10 m</td></tr><tr><td>Warm-white 3 mm LEDs w/ resistor, 5 V</td><td>24</td></tr><tr><td>Micro LEDs 1.8 mm (chandelier cups, globes)</td><td>30</td></tr><tr><td>Purple flicker LED (Tesla coil) + 2 amber flicker (chimneys)</td><td>3</td></tr><tr><td>Green pilot LED (dynamo dial)</td><td>1</td></tr><tr><td>Micro slide switches</td><td>9 (one per room + garden + exterior)</td></tr><tr><td>JST-PH 2-pin pigtails</td><td>12 pairs</td></tr><tr><td>N52 magnets Ø6×2 / Ø6×1</td><td>40 / 40</td></tr><tr><td>Warm fairy-light string, 2 m</td><td>2</td></tr></tbody></table>`;
const V3BOM={cottage0:{'weathervane_v3':1,'garden_gate_v3':1,'lamppost_cluster_v3':1,'door_surround_v3':1,'stained_bay_v3':1,'roof_cresting_v3':1,'stained_insert_*_v3 (lead+glass)':14,'finial_spire_v3':2},
 ranch1:{'porte_cochere_v3':1,'garden_gate_v3':1,'lamppost_cluster_v3':2,'door_surround_v3':2,'stained_bay_v3':1,'roof_cresting_v3':2,'weathervane_v3':1,'stained_insert_*_v3 (lead+glass)':24},
 town2:{'spiral_stair_v3':1,'weathervane_v3':1,'garden_gate_v3':1,'lamppost_cluster_v3':1,'door_surround_v3':1,'mansard_panel_v3':4,'stained_bay_v3':2,'stained_insert_*_v3 (lead+glass)':30},
 court3:{'garden_gate_v3':1,'lamppost_cluster_v3':2,'weathervane_v3':1,'door_surround_v3':4,'stained_insert_*_v3 (lead+glass)':28,'finial_spire_v3':4},
 shop4:{'weathervane_v3':1,'lamppost_cluster_v3':2,'door_surround_v3':1,'roof_cresting_v3':1,'stained_insert_*_v3 (lead+glass)':22},
 wired5:{'mansard_panel_v3':6,'garden_gate_v3':1,'lamppost_cluster_v3':2,'door_surround_v3':1,'stained_bay_v3':2,'spiral_stair_v3':1,'stained_insert_*_v3 (lead+glass)':36,'finial_spire_v3':5}};
function select(n){cur=n;const h=HOUSES[n];CUR_H=h;[...pills.children].forEach((b,k)=>b.classList.toggle('on',k==n));
  document.getElementById('rev').textContent='Grand v3 · Gallery — '+h.name;document.getElementById('blurb').textContent=h.blurb;
  const bom=Object.assign({},h.bom,V3BOM[h.id]||{});const tot=Object.values(bom).reduce((a,b)=>a+b,0);
  document.getElementById('facts').innerHTML=[[h.size,'Footprint (tiles)'],[h.stories,'Stories'],[tot+' parts','Structure + ornament'],[h.old,'Was (v1)']].map(([a,b])=>`<div class="fact"><b>${a}</b><span>${b}</span></div>`).join('');
  document.getElementById('bom').innerHTML=`<h3>${h.name} — print list</h3><table><thead><tr><th>Part (STL)</th><th>Qty</th></tr></thead><tbody>${Object.entries(bom).map(([k,v])=>`<tr><td><code>${k}</code>${/_v3/.test(k)?' <span class="new">v3</span>':''}</td><td>${v}</td></tr>`).join('')}</tbody></table>
  <p class="muted">Roof panels, gables, mansard panels and arcades print flat. Turret drums, caps, the spiral stair and lamppost clusters print upright. Stained-glass inserts print as two bodies (lead + translucent glass) in one H3C tool-swap plate: <a href="/dollhouse/stl/stained_inserts_plate_v3.3mf">stained_inserts_plate_v3.3mf</a>. Every part fits the H3C bed; the largest is porte_cochere_v3 at 236 × 128 × 146.</p>`;
  document.getElementById('notes-house').innerHTML=`<h3>${h.name}</h3><p>${h.story}</p>`+(h.wired?WIRE:`<p class="muted">Lights: Ø3.2 channels run around each wall top and down a corner post. Turret, chimney, lamppost globes and fountain each hide an LED pocket. Press <b>Night lights</b> to see it lit.</p>`);
  ['btn-wire','btn-panel','lg-w','lg-p'].forEach(id=>document.getElementById(id).hidden=!h.wired);build(h);}
function mergeParts(){const keep=new Set();spinners.forEach(s=>{const o=s.isObject3D?s:(s.air||s.g);if(o)o.traverse(c=>keep.add(c));});SMOKES.forEach(S=>S.sm.forEach(x=>keep.add(x)));
  const inv=new THREE.Matrix4(),rel=new THREE.Matrix4();let before=0,after=0;
  parts.forEach(pt=>{const obj=pt.m;obj.updateMatrixWorld(true);inv.copy(obj.matrixWorld).invert();const groups=new Map();
    obj.traverse(m=>{if(!m.isMesh||keep.has(m)||m===obj)return;const mt=m.material;if(!mt||Array.isArray(mt)||mt.transparent)return;const g=m.geometry;if(!g.attributes.normal)return;before++;
      if(!groups.has(mt))groups.set(mt,[]);groups.get(mt).push(m);});
    groups.forEach((ms,mt)=>{if(ms.length<2){after+=ms.length;return;}let n=0;const geos=ms.map(m=>{rel.multiplyMatrices(inv,m.matrixWorld);let g=m.geometry.index?m.geometry.toNonIndexed():m.geometry.clone();g.applyMatrix4(rel);n+=g.attributes.position.count;return g;});
      const P=new Float32Array(n*3),N=new Float32Array(n*3),U=new Float32Array(n*2);let o=0;geos.forEach(g=>{P.set(g.attributes.position.array,o*3);N.set(g.attributes.normal.array,o*3);if(g.attributes.uv)U.set(g.attributes.uv.array,o*2);o+=g.attributes.position.count;g.dispose();});
      const bg=new THREE.BufferGeometry();bg.setAttribute('position',new THREE.BufferAttribute(P,3));bg.setAttribute('normal',new THREE.BufferAttribute(N,3));bg.setAttribute('uv',new THREE.BufferAttribute(U,2));
      const mm=new THREE.Mesh(bg,mt);const lit=mt.isMeshBasicMaterial||(mt.userData&&mt.userData.keepUV);mm.castShadow=!lit;mm.receiveShadow=true;
      ms.forEach(m=>{m.parent.remove(m);});obj.add(mm);after++;});});
  window.__dh_stats={before,after};}
function clearMats(){for(const k in MC)delete MC[k];}
function build(h){if(root){scene.remove(root);root.traverse(o=>{if(o.geometry)o.geometry.dispose();});}root=new THREE.Group();scene.add(root);parts=[];spinners=[];lights=[];HALOS=[];WIRES=[];PULSES=[];SMOKES=[];GLOW.length=0;SGI=0;seed(h.id.length*977+13);clearMats();
  const P=PAL[h.pal];CUR_P=P;roles(P);h.build(P);mk(P,EXTRA[h.id]||[]);
  root.traverse(o=>{if(o.isMesh&&o.material&&o.material.map&&!o.material.userData.keepUV&&!o.userData.keepUV)worldUV(o);});
  mergeParts();
  // fireflies
  const bb0=new THREE.Box3().setFromObject(root);const fg=new THREE.BufferGeometry(),N=140,pos=new Float32Array(N*3);for(let k=0;k<N;k++){pos[k*3]=bb0.min.x+rnd()*(bb0.max.x-bb0.min.x);pos[k*3+1]=10+rnd()*160;pos[k*3+2]=bb0.min.z+rnd()*(bb0.max.z-bb0.min.z);}
  fg.setAttribute('position',new THREE.BufferAttribute(pos,3));FLIES=new THREE.Points(fg,new THREE.PointsMaterial({map:haloTex(),size:9,color:P.wired?0x67e8f9:0xfde68a,transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,opacity:0}));FLIES.userData.p0=pos.slice();root.add(FLIES);
  // current pulses along wire runs
  if(P.wired){const pm=new THREE.MeshBasicMaterial({color:0xecfeff});WIRES.forEach((w,i)=>{const L=w[0].distanceTo(w[1]);const n=Math.max(1,Math.round(L/90));for(let k=0;k<n;k++){const m=new THREE.Mesh(new THREE.SphereGeometry(2.6,8,6),pm);root.add(m);const hl=addHalo(m,V3(0,0,0),26,0x67e8f9);hl.userData.always=1;PULSES.push({m,a:w[0],b:w[1],t:k/n,sp:.004+((i*37)%10)/2500});}});}
  // sky + framing
  setSky(P);const bb=new THREE.Box3().setFromObject(root),sph=bb.getBoundingSphere(new THREE.Sphere());const c=sph.center,R=sph.radius;
  const [az,el,k]=CAM[h.id]||[35,22,.8];const fov=camera.fov*Math.PI/180;const dist=R/Math.sin(fov/2)*k;const A=az*Math.PI/180,E=el*Math.PI/180;
  camera.position.set(c.x+Math.sin(A)*Math.cos(E)*dist,c.y+Math.sin(E)*dist,c.z+Math.cos(A)*Math.cos(E)*dist);controls.target.set(c.x,c.y*.8,c.z);camera.near=Math.max(1,dist/200);camera.far=dist*8;camera.updateProjectionMatrix();
  const s=key.shadow.camera;s.left=-R;s.right=R;s.top=R;s.bottom=-R;s.near=1;s.far=R*6;s.updateProjectionMatrix();key.position.set(c.x+R*1.1,c.y+R*1.8,c.z+R*.9);key.target.position.copy(c);
  floor.position.y=-44;scene.fog.near=dist*1.3;scene.fog.far=dist*3.2;applyVis();setNight(night);}
function applyVis(){parts.forEach(p=>{p.m.visible=!!(vis[p.grp]??1);});}
let skyD,skyN;
function grad(a,b){return mkTex(cvs(16,512,(x,w,h)=>{const g=x.createLinearGradient(0,0,0,h);g.addColorStop(0,a);g.addColorStop(.75,b);g.addColorStop(1,b);x.fillStyle=g;x.fillRect(0,0,w,h);}));}
function setSky(P){skyD=grad(...(P.sky||['#7fb2d6','#f7d9b5']));skyN=grad(...(P.skyN||['#05060f','#1d1838']));}
function setNight(on){night=on;if(!scene)return;scene.background=on?skyN:skyD;const P=CUR_P||{};
  scene.fog.color.set(on?(P.skyN||['','#1d1838'])[1]:(P.sky||['','#f7d9b5'])[1]);
  hemi.intensity=on?.12:.7;hemi.color.set(on?0x7d8cff:0xfff1dc);key.intensity=on?.12:1.55;key.color.set(on?0x8aa2ff:0xffe2b8);rim.intensity=on?.35:.55;fill.intensity=on?.05:.3;
  renderer.toneMappingExposure=on?1.15:1.0;root&&root.traverse(o=>{if(o.isMesh&&o.material&&o.material.isMeshStandardMaterial)o.material.envMapIntensity=on?.12:(o.material.userData.keepUV?1.5:1);});
  floor.material.color.set(on?0x2a2540:0xffffff);floor.material.envMapIntensity=on?.1:1;
  GLOW.forEach(m=>m.emissiveIntensity=on?2.8:(P.wired?.9:.55));lights.forEach(l=>l.intensity=on?l.userData.i*1.3:0);
  HALOS.forEach(s=>s.material.opacity=on?.95:(s.userData.always?.7:(P.wired?.28:0)));if(FLIES)FLIES.material.opacity=on?1:0;}
let hemi,key,rim,fill,floor,resize=()=>{};
renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:Q.has('shot')});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputEncoding=THREE.sRGBEncoding;renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;el.prepend(renderer.domElement);
scene=new THREE.Scene();scene.fog=new THREE.Fog(0xf7d9b5,2500,7000);camera=new THREE.PerspectiveCamera(34,1,1,9000);const OC=THREE.OrbitControls||window.OrbitControls;controls=new OC(camera,renderer.domElement);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*.49;
controls.addEventListener('start',()=>{if(spin){spin=false;document.getElementById('btn-spin').classList.remove('on');}});
// soft studio environment for metals + glass
(function(){const es=new THREE.Scene();const sg=new THREE.SphereGeometry(100,32,16);const cols=[];const col=new THREE.Color();for(let i=0;i<sg.attributes.position.count;i++){const y=sg.attributes.position.getY(i)/100;col.set(y>0?0xfff1dc:0x4a3a30).lerp(new THREE.Color(0x8fb4d8),Math.max(0,y)*.6);cols.push(col.r,col.g,col.b);}
  sg.setAttribute('color',new THREE.Float32BufferAttribute(cols,3));es.add(new THREE.Mesh(sg,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.BackSide})));
  for(const[x,y,z,s]of[[60,60,40,40],[-70,40,-30,30],[0,90,0,50]]){const m=new THREE.Mesh(new THREE.PlaneGeometry(s,s),new THREE.MeshBasicMaterial({color:0xffffff,side:THREE.DoubleSide}));m.position.set(x,y,z);m.lookAt(0,0,0);es.add(m);}
  const pm=new THREE.PMREMGenerator(renderer);scene.environment=pm.fromScene(es,.04).texture;})();
hemi=new THREE.HemisphereLight(0xfff1dc,0x4a3a42,.7);scene.add(hemi);
key=new THREE.DirectionalLight(0xffe2b8,1.55);key.castShadow=true;key.shadow.mapSize.set(2048,2048);key.shadow.bias=-.0004;key.shadow.normalBias=.6;key.shadow.radius=4;scene.add(key,key.target);
rim=new THREE.DirectionalLight(0x9fc0ff,.55);rim.position.set(-600,350,-700);scene.add(rim);fill=new THREE.DirectionalLight(0xffc9a0,.3);fill.position.set(-500,120,500);scene.add(fill);
floor=new THREE.Mesh(new THREE.CircleGeometry(2400,64),new THREE.MeshStandardMaterial({color:0x3a2e2a,roughness:.9,map:mkTex(cvs(256,256,(x,w,h)=>{const g=x.createRadialGradient(128,128,10,128,128,128);g.addColorStop(0,'#c9b8a6');g.addColorStop(.5,'#8a7868');g.addColorStop(1,'#3a3030');x.fillStyle=g;x.fillRect(0,0,w,h);}))}));
floor.material.map.wrapS=floor.material.map.wrapT=THREE.ClampToEdgeWrapping;floor.material.map.repeat.set(1,1);floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;scene.add(floor);
resize=()=>{const w=el.clientWidth,hh=el.clientHeight;if(!w)return;renderer.setSize(w,hh,false);renderer.domElement.style.width='100%';renderer.domElement.style.height='100%';camera.aspect=w/hh;camera.updateProjectionMatrix();};
addEventListener('resize',resize);resize();const tv=V3();
(function loop(t){requestAnimationFrame(loop);ex+=(target-ex)*.07;parts.forEach(p=>p.m.position.y=p.by+p.lift*ex);
  if(spin&&root)root.rotation.y+=.0014;const ts=t/1000;
  spinners.forEach(s=>{if(s.isObject3D)s.rotation.y+=.006;else if(s.air){s.air.position.y=s.y0+Math.sin(t/900)*10;s.air.rotation.y=Math.sin(t/4000)*.3;}else if(s.tesla){s.tesla.color.setHSL(.72+Math.random()*.08,1,.6+Math.random()*.35);s.g.children.forEach(c=>{if(c.material===s.tesla)c.visible=Math.random()>.25;});}});
  SMOKES.forEach(S=>S.sm.forEach(p=>{const k=(p.userData.k+ts*.12)%1;p.position.y=S.y0+k*90;p.position.x=-7+Math.sin(k*6+ts)*6+k*20;const sc=8+k*34;p.scale.set(sc,sc,1);p.material.opacity=(night?.25:.55)*Math.sin(k*Math.PI);}));
  PULSES.forEach(p=>{p.t=(p.t+p.sp)%1;p.m.position.lerpVectors(p.a,p.b,p.t);p.m.position.y+=0;p.m.visible=vis.wire&&true;});
  if(FLIES&&night){const a=FLIES.geometry.attributes.position,p0=FLIES.userData.p0;for(let k=0;k<a.count;k++){a.setXYZ(k,p0[k*3]+Math.sin(ts*.7+k)*14,p0[k*3+1]+Math.sin(ts*1.1+k*1.7)*10,p0[k*3+2]+Math.cos(ts*.6+k*.9)*14);}a.needsUpdate=true;FLIES.material.size=7+Math.sin(ts*3)*2;}
  if(night)lights.forEach((l,i)=>{l.intensity=l.userData.i*1.3*(.92+.08*Math.sin(ts*9+i*2.1));});
  controls.update();renderer.render(scene,camera);})(0);
const tog=(id,fn)=>{const b=document.getElementById(id);b.onclick=()=>{b.classList.toggle('on');fn(b.classList.contains('on'));};};
tog('btn-explode',on=>target=on?1:0);tog('btn-night',setNight);tog('btn-spin',on=>spin=on);
[['btn-roof',['roof','orn']],['btn-wall',['wall']],['btn-furn',['furn']],['btn-garden',['garden']],['btn-light',['light']],['btn-wire',['wire']],['btn-panel',['panel']]].forEach(([id,ks])=>tog(id,on=>{ks.forEach(k=>vis[k]=on?1:0);applyVis();}));
addEventListener('hashchange',()=>{const i=HOUSES.findIndex(h=>h.id==location.hash.slice(1));if(i>=0&&i!=cur)select(i);});
if(!spin)document.getElementById('btn-spin').classList.remove('on');
select(Math.max(0,HOUSES.findIndex(h=>h.id==location.hash.slice(1))));
if(Q.has('explode')){document.getElementById('btn-explode').classList.add('on');target=1;ex=1;}
if(Q.has('night')){document.getElementById('btn-night').classList.add('on');setNight(true);}
window.__dh={ready:true};
})();
