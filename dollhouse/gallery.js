// v4 Play CAD gallery: loads real STLs (binary) into a small studio viewer.
(function(){
const P=[
['floor_tile_v0','Floor tile (core)','127×127 snap floor. Ø6.3 sockets on 31.75 grid + Ø3.2 light races. Required for every manor.'],
['upper_floor_tile_v1','Upper floor tile','Same grid as floor_tile_v0 for stacked stories (town / shop / wired).'],
['corner_post_v0','Corner post (core)','v4.2: top Ø6.3×5.5 socket — dowel up into upper_floor_tile_v1. Owns corner socket.'],
['snap_post_v0','Snap post','Ø6 post for mid-span / porch bearing ≤127 mm.'],
['dowel_pin_v0','Dowel pin','Ø6 peg seating posts into floor sockets.'],
['snap_clearance_strip_v0','Clearance strip','Print first — pick the Ø socket that pushes firm and pulls by hand.'],
['wall_panel_short_v0c','Short wall (blank)','107×102 blank short wall between corner posts.'],
['lawn_tile_v4','Lawn / yard tile','127×127 snap tile for yards. Same Ø6.3 sockets + Ø3.2 races as floor_tile_v0.'],
['path_tile_v4','Path / paver tile','127×127 path with paver recesses. Snap outdoor modules onto it.'],
['garden_bed_v4','Garden bed','Raised bed ~100×50, hollow well, 2 pegs on the 31.75 grid.'],
['fence_straight_v4','Fence (straight)','See-through picket fence spanning one tile edge, 2 pegs.'],
['fence_corner_v4','Fence (corner)','90° corner fence, pegs on both legs.'],
['garden_gate_play_v4','Play garden gate','v4.2 pegs 127 apart; v4.3 export scrubbed (no zero-area tris). 145 wide.'],
['sandbox_v4','Sandbox / play pad','100×100 tray, 4 corner pegs. Drop toys in.'],
['planter_stub_v4','Tree / planter stub','Pot + trunk stub, 1 centre peg. Add foliage or leave bare.'],
['bench_play_v4','Garden bench','Bench with 2 pegs. Free-standing play seat.'],
['shed_shell_v4','Shed / playhouse shell','v4.1: front posts + lintel under roof edge. Open-front play kept.'],
['wall_panel_clear_window_v4','Clear window wall','v4.1: taller sill, mid rail, jambs ≥12 mm. Clear opening kept.'],
['wall_panel_wide_door_v4','Wide door wall','Short wall with ≥28 mm clear doorway for furniture pass-through.'],
['roof_panel_lift_v4','Lift-off roof panel','Lip seats on wall tops; ridge Ø6.3 socks are for finial/chimney/cupola/dormer mates (not wall pegs).'],
['open_face_rail_v4','Open-face rail','Low furniture rail for open-back edges — full sightline.'],
['tower_stub_v43','Tower stub','v4.3 vertical accent. Peg → corner-post top / floor; top sock for finial.'],
['chimney_ridge_v43','Ridge chimney','v4.3. Peg → roof_panel_lift ridge Ø6.3. Lift-compatible.'],
['finial_ridge_v43','Ridge finial','v4.3. Peg → ridge / tower / gable top sock.'],
['clock_shaft_v43','Clock shaft','v4.3 Cogsworth vertical. Peg → corner-post top; top sock for finial.'],
['porch_post_v43','Porch post','v4.3 façade. Peg → floor/lawn/path Ø6.3 (same as outdoor); top sock for beam.'],
['porch_beam_v43','Porch beam','v4.3. Pegs at 0 & 127 → porch_post tops.'],
['porch_roof_slice_v43','Porch roof slice','v4.3 shed porch roof. Pegs → porch_post tops. Does not cover windows.'],
['gable_end_v43','Gable end','v4.3 roofs-on silhouette. Pegs at 0 & 127; apex sock for finial.'],
['dormer_play_v43','Play dormer','v4.3. Peg → ridge; clear window opening; lift-compatible.'],
['mansard_break_v43','Mansard break','v4.3 silhouette panel. Pegs at 0 & 127 → ridge.'],
['cupola_play_v43','Play cupola','v4.3. Pegs at ±31.75 → ridge; top sock for finial.']
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
