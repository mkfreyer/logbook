"""Crop/layout genuine viewer screenshots; never paint or combine model pixels."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('docs/m4d/anterieurs-valides')
audit=json.loads((ROOT/'browser-verification.json').read_text());assert audit['status']=='passed'
assert audit['frontComparisonCameraIdentical']
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
def orange_box(im):
    rgb=np.array(im.convert('RGB')).astype(int);mask=(rgb[:,:,0]-rgb[:,:,1]>20)&(rgb[:,:,1]-rgb[:,:,2]>10)&(rgb[:,:,0]>80)
    y,x=np.where(mask);assert len(y)>10,'Expected visible orange selection'
    return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
def padded(box,size,margin=38):
    return [max(0,box[0]-margin),max(0,box[1]-margin),min(size[0],box[2]+margin),min(size[1],box[3]+margin)]
provenance={'method':'Lossless crops and panel layout only. No mannequin pixel repainted. Source: actual Chromium WebGL, not an iPhone.','crops':[]}
for side in ['right','left']:
    name=f'selection-deltoid.{side}.anterior.png';im=Image.open(ROOT/name);box=padded(orange_box(im),im.size)
    dest='anterieur-'+('droit' if side=='right' else 'gauche')+'-orange.png';im.crop(box).save(ROOT/dest)
    provenance['crops'].append({'file':dest,'source':name,'sourceBox':box})
images=[Image.open(ROOT/f'face-anterieur-{side}.png').convert('RGB') for side in ['droit','gauche']]
boxes=[orange_box(im) for im in images]
union=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
box=padded(union,images[0].size,42);crops=[im.crop(box) for im in images]
w,h=crops[0].size;board=Image.new('RGB',(2*w+60,h+140),'#101c29');draw=ImageDraw.Draw(board)
draw.text((16,12),'Vue de face — deux sélections successives',font=font,fill='white')
for i,(im,label) in enumerate(zip(crops,['Antérieur droit sélectionné','Antérieur gauche sélectionné'])):
    x=20+i*(w+20);draw.text((x,52),label,font=small,fill='white');board.paste(im,(x,82))
draw.text((16,h+104),'Même caméra et cadrage · une zone active à la fois · WebGL de test',font=small,fill='#b8cadb')
board.save(ROOT/'comparaison-face-anterieurs.png')
provenance['faceComparison']={'file':'comparaison-face-anterieurs.png','sources':['face-anterieur-droit.png','face-anterieur-gauche.png'],'sameSourceBox':box,'modelPixelsCombinedBetweenFrames':False}
(ROOT/'capture-provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
print('VIEWER_CAPTURE_CROPS_AND_FRONT_COMPARISON_CREATED',flush=True)
