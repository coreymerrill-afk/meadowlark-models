from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
D=Path(__file__).parent
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f=ImageFont.truetype(font,24);sm=ImageFont.truetype(font,20);title=ImageFont.truetype(font,40)
for n in ['exterior','cutaway','exploded']:
 im=Image.new('RGB',(2400,1700),'#e8e7df');src=Image.open(D/f'{n}-raw.png').convert('RGB');im.paste(src,(300,100));d=ImageDraw.Draw(im)
 d.rounded_rectangle((20,15,2380,115),14,fill='#122d35');d.text((45,25),'PASTA / 02    '+n.upper()+'    |    PORT-CONNECTED CONCEPT',font=title,fill='#f5efdf');d.text((48,77),'UNBUILT • 15-minute goal unvalidated • Hydraulic geometry retained in the service-exploded view',font=f,fill='#b7d6d1')
 a=list(json.load(open(D/f'{n}-anchors.json')).items());half=(len(a)+1)//2
 for i,(label,(x,y)) in enumerate(a):
  left=i<half;j=i if left else i-half;xx=20 if left else 2100;yy=195+j*235
  x+=300;y+=100;end=(xx+280 if left else xx,yy+35)
  d.line([(x,y),(end[0]+(30 if left else -30),end[1]),end],fill='#496269',width=2);d.ellipse((x-5,y-5,x+5,y+5),fill='#d96229')
  # wrap in narrow sidebars; anchors refer to actual geometry
  words=label.split();lines=['']
  for w in words:
   if d.textlength((lines[-1]+' '+w).strip(),font=f)>252:lines.append(w)
   else:lines[-1]=(lines[-1]+' '+w).strip()
  d.rounded_rectangle((xx,yy,xx+280,yy+max(76,30*len(lines)+16)),8,fill='#faf7ed',outline='#93aaa9')
  for k,line in enumerate(lines):d.text((xx+12,yy+10+k*30),line,font=f,fill='#17343b')
 d.rectangle((0,1605,2400,1700),fill='#122d35');d.text((35,1620),'BLUE = potable feed   |   ORANGE = heated clean fill   |   GREEN = chamber-only recirculation   |   BROWN = gravity waste',font=f,fill='#f5efdf');d.text((35,1660),'Arrows sit on actual pipes. All interfaces have named ports. No thermal, hydraulic, hygiene or safety certification claimed.',font=sm,fill='#b7d6d1')
 im.save(D/f'{n}.png',optimize=True)
# A deliberately separate graph, not a misleading faux-mechanical image.
im=Image.new('RGB',(2000,1420),'#f6f3e9');d=ImageDraw.Draw(im)
d.rectangle((0,0,2000,130),fill='#122d35');d.text((35,25),'V2 / HYDRAULIC CONNECTION GRAPH',font=title,fill='white');d.text((35,82),'Repeated CHAMBER boxes are the same volume. Diagram is NOT a spatial layout. See manifest for XYZ ports.',font=sm,fill='#b7d6d1')
rows=[
 ('POTABLE ONLY — physically left of chamber',220,'#197ca4',[('CLEAN TANK','tank.out'),('ISOLATE / CHECK','in -> out'),('FEED PUMP + METER','feed / meter'),('HEATED CHANNEL','heater.in -> out'),('AIR-GAP NOZZLE','480 -> water max420'),('CHAMBER','open fill')],['F01','F02 / F03','F04','H01 / H02','60mm free fall']),
 ('RECIRCULATION — no connection to potable tank or waste',530,'#21966e',[('SAME CHAMBER','broad screened intake'),('REMOVABLE STRAINER','C00 -> strainer.out'),('RECIRC PUMP','circulation.in / out'),('RETURN WALL PORT','return.wall'),('BROAD TEE / RETURNS','return.a / return.b'),('SAME CHAMBER','gentle return intent')],['C00','C01','C02','C03','C04 / C05']),
 ('DRAIN — entire route descends; valve opens only when commanded',840,'#9a602b',[('CHAMBER LOW POINT','z235 / open floor bore'),('NC DRAIN VALVE','z215 ->185'),('DOWNHILL LINE','z175 ->150'),('REMOVABLE COUPLING','z135'),('WASTE HEADSPACE','stub z120 / maxfill95'),('WASTE VENT','separate V01')],['D01','D02','D02','D03','passive headspace'])]
xs=[30,360,690,1020,1350,1680]
for heading,y,col,nodes,edges in rows:
 d.text((35,y-65),heading,font=f,fill=col)
 for i,((a,b),x) in enumerate(zip(nodes,xs)):
  d.rounded_rectangle((x,y,x+290,y+125),12,fill='white',outline=col,width=3);d.text((x+12,y+20),a,font=sm,fill=col);d.text((x+12,y+66),b,font=ImageFont.truetype(font,17),fill='#263c42')
  if i<5:
   d.line((x+290,y+47,x+325,y+47),fill=col,width=4);d.polygon([(x+325,y+47),(x+314,y+39),(x+314,y+55)],fill=col);d.text((x+277,y+138),edges[i],font=ImageFont.truetype(font,17),fill=col)
d.text((35,1140),'SALT: separate dry system — cartridge -> metering gate -> downhill chute -> chamber annulus (S01).',font=f,fill='#514828')
d.text((35,1200),'STEAM: chamber headspace standpipe -> rear-left steam outlet (ST00 / ST01). Dry electronics bay remains rear-right and segregated.',font=f,fill='#263c42')
d.text((35,1270),'NO clean-feed connection to waste. NO drain pump or uphill drain. NO accidental junctions at line crossings.',font=f,fill='#a44625')
d.text((35,1350),'Concept geometry only. NC = normally closed. Port distance, tangent, gravity and selected clearance checks accompany this graph.',font=sm,fill='#263c42')
im.save(D/'plumbing-graph.png',optimize=True)
