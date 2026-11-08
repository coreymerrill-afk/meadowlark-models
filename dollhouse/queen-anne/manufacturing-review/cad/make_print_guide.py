from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import pypdfium2 as pdfium
R=Path(__file__).parent;P=R/'print-candidate';O=P/'output/pdf';O.mkdir(parents=True,exist_ok=True)
c=canvas.Canvas(str(O/'Dollhouse-test-print-guide.pdf'),pagesize=(612,792));c.setTitle('Victorian Dollhouse - Fit Test and Assembly Guide')
style=ParagraphStyle('body',fontName='Helvetica',fontSize=10.5,leading=15,textColor=HexColor('#243B39'))
def text(t,x,y,w=516):
 q=Paragraph(t,style);_,h=q.wrap(w,700);q.drawOn(c,x,y-h);return y-h-11
def head(title,sub,page):
 c.setFillColor(HexColor('#235F60'));c.rect(0,715,612,77,fill=1,stroke=0);c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',21);c.drawString(40,754,title);c.setFont('Helvetica',10);c.drawString(40,733,sub);c.setFillColor(HexColor('#566563'));c.setFont('Helvetica',9);c.drawString(40,24,'November 8, 2026  |  Development kit - full-house printing not yet approved');c.drawRightString(572,24,str(page))
head('Victorian dollhouse','The separate demo stays frozen; this is the next manufacturing candidate.',1)
c.drawImage(str(P/'model-preview.jpg'),55,263,width=502,height=433,preserveAspectRatio=True,anchor='c')
y=218
y=text('<b>Preserved:</b> ornate Victorian trim, stairs, rear access, storage drawers and lighting provision. The projecting oriel now has a rose body, ivory trim and copper-toned canopy.',48,y)
y=text('<b>Assembly improvement:</b> the cabinet top is now a separate flat-printing deck. Fit the frame and drawer guides first, then attach the deck. The porch remains an intact subassembly.',48,y)
text('<b>Evidence is bounded:</b> interference checks and representative H3C slices are engineering checks, not proof of physical fit or strength. No printer job has been sent.',48,y)
c.showPage()
head('Print this small set first','H3C / 0.4 mm nozzle / PLA / 0.16 mm layers / 100% scale',2)
c.drawImage(str(P/'slicer/plate_1.png'),374,513,width=190,height=190,mask='auto')
y=691
y=text('<b>11 pieces on one plate</b><br/>Estimated 64m 43s and 22.88 g of PLA, including supports. The numbered STL filenames identify each piece.',48,y,310)
y=text('<b>Before slicing:</b> choose your actual build plate and PLA profile. The supplied project used Generic PLA and the default Cool Plate setting; change that if your plate differs. Select the matching plate and slice locally before printing. The supplied project has no ready-to-send G-code.',48,y,310)
y=490
for title,body in [
 ('01 + 02 + 03: floor joint and 3 mm pin','Insert the pin into both sockets. The two faces should align without forcing or splitting, leaving the designed 0.30 mm adhesive seam. Try dry before gluing.'),
 ('04 + 05: actual drawer guide and runner','Remove any supports carefully. Slide the runner along the guide repeatedly. It should move smoothly without binding or excessive rocking. These use the actual guide/groove shapes.'),
 ('06 + 07: rear panel screw and frame pilot','Use a suitable M2 screw with about 5-6 mm thread engagement. It should retain the panel without cracking the pilot wall. Do not force a tight screw; report the fit first.'),
 ('08 + 09: window ornament and roof relief','Check that the small flower, mouldings and slate joints survive printing and cleanup. The roof sample is laid flat to inspect relief; it does not prove full-roof support removal.'),
 ('10 + 11 + 03: removable test of the deck joint','Reuse the 3 mm pin to align the deck coupon to its bearing. Check flush alignment and easy insertion. These coupons do not establish the finished cabinet load capacity.')]:
 y=text('<b>'+title+'</b><br/>'+body,48,y)
text('<b>Send feedback:</b> photos of the dry-fit pieces, which pairs bind or wobble, and your filament/plate settings. Keep the STLs at 100% scale; adjust local clearances, not the whole house.',48,y)
c.showPage()
head('Assembly order','Dry-fit first. Only rear panels are removable for staging.',3)
y=689
steps=[
 ('1. Build module rows on a flat surface.','For each floor, join the left/middle/right sections along their X seams first. Then bring the front and rear rows together along the Y seam. This avoids trying to insert orthogonal dowels simultaneously.'),
 ('2. Build the open cabinet frame.','Align its sections, check square, then dry-fit drawer guides and drawers. The top deck remains off so the inside is accessible.'),
 ('3. Add the separate cabinet deck.','Use its vertical alignment pins. Check that the deck sits flat. Finish and test drawer-stop hardware before closing access; load and caster stability still require physical testing.'),
 ('4. Install the ground floor and complete porch.','Lower the ground floor onto the cabinet. Fit the porch from the front before installing the upper floor: the porch includes an upstand that the upper floor clears.'),
 ('5. Stack the upper floors.','Lower each storey vertically onto its parallel alignment pins. Dry-fit the stair and rail interfaces. Do not lever on the delicate ornament to seat a joint.'),
 ('6. Install the loft and fixed roof sections.','The fixed roof and walls share coherent module boundaries. Feed low-voltage lighting wires while the channels remain accessible. Select and test lighting components separately.'),
 ('7. Assemble and mount rear panels.','Join each panel on a flat fixture using its horizontal seam pins. Fit it from the rear into the clearance/pilot screw pairs. Remove these panels for staging; leave sides and roof fixed.'),
 ('8. Approve a staged print, not the entire house at once.','After coupons pass, print one decorated wall module and its neighbour to verify supports, detail and the real joint. Adhesive strength, repeated screw use, hardware retention and loaded stability remain physical checks.')]
for title,body in steps:y=text('<b>'+title+'</b><br/>'+body,48,y)
c.save()
doc=pdfium.PdfDocument(str(O/'Dollhouse-test-print-guide.pdf'))
for i,page in enumerate(doc):page.render(scale=1.25).to_pil().save(O/f'guide-page-{i+1}.png')
print('PDF pages',len(doc))
