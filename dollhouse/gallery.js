// v4 Play CAD gallery: loads real STLs (binary) into a small studio viewer.
(function(){
const P=[
['lawn_tile_v4','Lawn / yard tile','127×127 snap tile for yards. Same Ø6.3 sockets + Ø3.2 races as floor_tile_v0.'],
['path_tile_v4','Path / paver tile','127×127 path with paver recesses. Snap outdoor modules onto it.'],
['garden_bed_v4','Garden bed','Raised bed ~100×50, hollow well, 2 pegs on the 31.75 grid.'],
['fence_straight_v4','Fence (straight)','See-through picket fence spanning one tile edge, 2 pegs.'],
['fence_corner_v4','Fence (corner)','90° corner fence, pegs on both legs.'],
['garden_gate_play_v4','Play garden gate','Open frames + piers — clear sight, not ornate-obstructed. 140 wide.'],
['sandbox_v4','Sandbox / play pad','100×100 tray, 4 corner pegs. Drop toys in.'],
['planter_stub_v4','Tree / planter stub','Pot + trunk stub, 1 centre peg. Add foliage or leave bare.'],
['bench_play_v4','Garden bench','Bench with 2 pegs. Free-standing play seat.'],
['shed_shell_v4','Shed / playhouse shell','Open-front shed on one tile; clear side windows. Pegs into lawn/floor.'],
['wall_panel_clear_window_v4','Clear window wall','Short wall 107×102, large open aperture, sill, no muntins.'],
['wall_panel_wide_door_v4','Wide door wall','Short wall with ≥28 mm clear doorway for furniture pass-through.'],
['roof_panel_lift_v4','Lift-off roof panel','Flat-print roof half with underside pegs. Kid lifts to reach rooms.'],
['open_face_rail_v4','Open-face rail','Low furniture rail for open-back edges — full sightline.']
];
const el=document.getElementById('gal'),grid=document.getElementById('galgrid'),info=document.getElementById('galinfo');if(!el||!window.THREE)return;
let R,S,C,O,mesh,inited=false;
function parse(buf){const dv=new DataView(buf),n=dv.getUint32(80,true),pos=new Float32Array(n*9),nor=new Float32Array(n*9);let o=84;
  for(let i=0;i<n;i++){const nx=dv.getFloat32(o,true),ny=dv.getFloat32(o+4,true),nz=dv.getFloat32(o+8,true);o+=12;for(let v=0;v<3;v++){pos[i*9+v*3]=dv.getFloat32(o,true);pos[i*9+v*3+1]=dv.getFloat32(o+4,true);pos[i*9+v*3+2]=dv.getFloat32(o+8,true);nor[i*9+v*3]=nx;nor[i*9+v*3+1]=ny;nor[i*9+v*3+2]=nz;o+=12;}o+=2;}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('normal',new THREE.BufferAttribute(nor,3));g.rotateX(-Math.PI/2);g.computeBoundingBox();return g;}
function init(){if(inited)return;inited=true;R=new THREE.WebGLRenderer({antialias:true});R.setPixelRatio(Math.min(devicePixelRatio,2));R.outputEncoding=THREE.sRGBEncoding;R.toneMapping=THREE.ACESFilmicToneMapping;el.appendChild(R.domElement);
  S=new THREE.Scene();C=new THREE.PerspectiveCamera(32,1,1,5000);O=new (THREE.OrbitControls||window.OrbitControls)(C,R.domElement);O.enableDamping=true;O.autoRotate=true;O.autoRotateSpeed=1.2;
  S.add(new THREE.HemisphereLight(0xfff1dc,0x30283a,.8));const k=new THREE.DirectionalLight(0xffe2b8,1.4);k.position.set(200,300,200);S.add(k);const r=new THREE.DirectionalLight(0x9fc0ff,.7);r.position.set(-300,120,-250);S.add(r);
  const fit=()=>{const w=el.clientWidth,h=el.clientHeight;if(!w)return;R.setSize(w,h,false);R.domElement.style.width='100%';R.domElement.style.height='100%';C.aspect=w/h;C.updateProjectionMatrix();};addEventListener('resize',fit);fit();
  (function L(){requestAnimationFrame(L);if(!el.offsetParent)return;O.update();R.render(S,C);})();}
const M=new THREE.MeshStandardMaterial({color:0x86efac,metalness:.15,roughness:.55});
async function load(i){init();const [id,name,desc]=P[i];[...grid.children].forEach((b,k)=>b.classList.toggle('on',k==i));info.innerHTML=`<b>${name}</b>: ${desc} · <a href="/dollhouse/stl/${id}.stl" download>Download STL</a>`;
  const g=parse(await (await fetch('/dollhouse/stl/'+id+'.stl')).arrayBuffer());if(mesh){S.remove(mesh);mesh.geometry.dispose();}
  const b=g.boundingBox,c=b.getCenter(new THREE.Vector3()),sz=b.getSize(new THREE.Vector3());g.translate(-c.x,-b.min.y,-c.z);mesh=new THREE.Mesh(g,M);S.add(mesh);
  const r=sz.length()/2;O.target.set(0,sz.y/2,0);C.position.set(r*1.6,sz.y/2+r*.9,r*1.9);}
P.forEach((p,i)=>{const b=document.createElement('button');b.textContent=p[1];b.onclick=()=>load(i);grid.appendChild(b);});
window.__gal=()=>{if(!inited)load(0);};
})();
(function(){const k=document.getElementById('kit');if(!k)return;const go=()=>{if(!k.hidden&&window.__gal)window.__gal();};new MutationObserver(go).observe(k,{attributes:true,attributeFilter:['hidden']});go();})();
