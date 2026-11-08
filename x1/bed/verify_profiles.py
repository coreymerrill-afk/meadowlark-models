#!/usr/bin/env python3
"""Compare actual browser profile coordinates with generator and exported DXF."""
import json, subprocess
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon, box
import make_egg_crate as bed
root = Path(__file__).resolve().parent
js = r"""
const fs=require('fs'),vm=require('vm');
const s=fs.readFileSync(process.argv[1],'utf8');
const start=s.indexOf('  const BED = (function');
const end=s.indexOf('  function extrudeProfile',start);
const ctx={};vm.createContext(ctx);
vm.runInContext(s.slice(start,end)+'; result={blade:bladeProfile(BED.panel,BED.ribX),rib:ribProfile(BED.panel,BED.bladeY)};',ctx);
console.log(JSON.stringify(ctx.result));
"""
d = json.loads(subprocess.check_output(['node', '-e', js, str(root.parent/'index.html')]))
c = bed.build_cfg()
assert c.db == c.dr == c.RH/2 == 17
assert c.RH == c.Hv == 34 and c.H == 38
assert (root.parent/'index.html').read_bytes() == (root.parent/'X1-Ultra-First-Model-v2.html').read_bytes()
parts = list(ezdxf.readfile(root/'egg_crate_bed.dxf').modelspace().query('LWPOLYLINE[layer=="CUT"]'))
for i, (name, fn, offset) in enumerate([('blade',bed.blade_poly,40),('rib',bed.rib_poly,-40)]):
    model=Polygon([(x*25.4,y*25.4) for x,y in d[name]])
    generated=Polygon(fn(c))
    exported=Polygon([(x,y-offset) for x,y in parts[i].get_points('xy')])
    assert model.is_valid and generated.is_valid and exported.is_valid
    assert model.symmetric_difference(generated).area < 1e-7
    assert model.symmetric_difference(exported).area < 1e-7
    print(name + ': browser = generator = DXF; valid connected outline')
B=Polygon(bed.blade_poly(c));R=Polygon(bed.rib_poly(c))
for x in (0,1175): assert B.intersection(box(x,0,x+25,20)).area == 0
for a,b in zip(c.blade_y,c.blade_y[1:]):
    mid=(a+b)/2
    assert R.intersection(box(mid-15,0,mid+15,12)).area == 0
log=[];bed.verify(c,log)
print(*log,sep='\n')
print('PASS: identical HTML copies, rectangular channels, seam reliefs, half laps, height envelope')
