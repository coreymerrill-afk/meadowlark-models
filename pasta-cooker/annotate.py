from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
D=Path(__file__).parent
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f=ImageFont.truetype(font,22);title=ImageFont.truetype(font,37);small=ImageFont.truetype(font,19)
for name in ['exterior','cutaway','exploded']:
 im=Image.open(D/f'{name}-raw.png').convert('RGB');d=ImageDraw.Draw(im)
 d.rounded_rectangle((30,22,1570,138),16,fill='#10262e');d.text((52,35),'PASTA / 01     '+name.upper(),font=title,fill='#f1e9d3');d.text((53,89),'CONCEPT / UNBUILT   |   ~15 min target is unvalidated',font=f,fill='#b1dcd7')
 anchors=json.load(open(D/f'{name}-anchors.json'));
 if name=='exterior':anchors['Clean water tank']=[305,620]
 if name=='cutaway':anchors['10 Electrics (rear)']=anchors.pop('10 Electrical isolation')
 items=list(anchors.items());half=(len(items)+1)//2
 # labels arranged outside model; leader lines show functional anchors
 for i,(label,(x,y)) in enumerate(items):
  left=i<half;j=i if left else i-half; yy=190+j*135;xx=30 if left else 1260
  width=310;end=(xx+width if left else xx,yy+23)
  d.line([(x,y),((end[0]+x)//2,end[1]),end],fill='#36585e',width=2);d.ellipse((x-5,y-5,x+5,y+5),fill='#ed7946')
  d.rounded_rectangle((xx,yy,xx+width,yy+48),8,fill='#f3f0e7',outline='#9db6b6',width=1);d.text((xx+10,yy+11),label,font=small,fill='#15333b')
 d.rectangle((0,1134,1600,1200),fill='#10262e');d.text((35,1145),'Blue: clean feed   /   Orange: heat   /   Green: circulation   /   Brown: drain',font=f,fill='#eee6d4');d.text((35,1174),'Illustrative paths and packaging only. Not a build-ready or safety-certified design.',font=small,fill='#b1dcd7')
 im.save(D/f'{name}.png')
