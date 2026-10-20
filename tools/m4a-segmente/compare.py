"""Compose unretouched Blender renders; each mobile panel is exactly 390 px wide."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4a/segmente';R=OUT/'renders'
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
SMALL=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
BG=(8,19,29);records=[]
def tile(file,label):
    source=Image.open(R/file).convert('RGB');assert source.size==(780,1000)
    im=Image.new('RGB',(390,532),BG);im.paste(source.resize((390,500),Image.Resampling.LANCZOS),(0,32));ImageDraw.Draw(im).text((12,9),label,font=FONT,fill=(220,231,241));return im
for view in ['front','three-quarter','profile','back']:
    out=Image.new('RGB',(780,532),BG)
    out.paste(tile('baseline-'+view+'.png','Meshy source — cadrage haut du corps'),(0,0));out.paste(tile(view+'.png','Pilote — 8 pièces + support'),(390,0));name='comparison-'+view+'-390.png';out.save(R/name);records.append(name)
labels={'pectoralis':'Pectoral','deltoid':'Deltoïde','biceps':'Biceps','triceps':'Triceps'}
parts=[a+'.'+s for s in ['left','right'] for a in labels]
out=Image.new('RGB',(1560,1064),BG)
for i,name in enumerate(parts):
    muscle,side=name.split('.');out.paste(tile('select-'+name+'.png',labels[muscle]+(' gauche' if side=='left' else ' droit')),(i%4*390,i//4*532))
out.save(R/'selections-8-pieces.png');records.append('selections-8-pieces.png')
out=Image.new('RGB',(780,532),BG);out.paste(tile('isolate-pectoralis.left.png','Pectoral gauche — seul objet visible'),(0,0));out.paste(tile('exploded.png','Vue éclatée — géométries séparées'),(390,0));out.save(R/'isolation-et-eclate.png');records.append('isolation-et-eclate.png')
# Standalone mobile image; no scene geometry edits or camera zoom.
Image.open(R/'select-pectoralis.left.png').resize((390,500),Image.Resampling.LANCZOS).save(R/'mobile-selection-390.png')
(OUT/'comparison-metadata.json').write_text(json.dumps(dict(panel_size=[390,500],composition='Pillow LANCZOS resize + titles only; no anatomical image edits',files=records),indent=2)+'\n')
print('COMPARISONS_DONE',len(records))
