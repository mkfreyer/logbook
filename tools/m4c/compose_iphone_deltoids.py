"""Compose genuine Blender frames; labels and crops only, never repaint masks."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from glb_io import sha
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4c/meshy-deltoides-reperes-iphone';D=OUT/'renders'
meta=json.loads((D/'render-metadata.json').read_text());frames={p['file']:p for p in meta['frames']}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for k,label in [('posterior','Deltoïde postérieur droit'),('lateral','Deltoïde moyen droit'),('anterior','Deltoïde antérieur droit')]:
 a,b=frames['avant-reference-'+k+'.png'],frames['apres-reference-'+k+'.png'];assert a['cameraMatrix']==b['cameraMatrix'] and a['resolution']==b['resolution'] and a['lens']==b['lens']
 before=Image.open(D/a['file']).convert('RGB');after=Image.open(D/b['file']).convert('RGB');w,h=before.size
 board=Image.new('RGB',(w*2+36,h+102),'#11202c');d=ImageDraw.Draw(board);d.text((14,10),label+' • vue iPhone reconstituée',font=font,fill='white');d.text((14,48),'Avant — 06fa665 / 268ea3e',font=small,fill='white');d.text((w+24,48),'Proposition — mêmes caméra et éclairage',font=small,fill='white');board.paste(before,(12,86));board.paste(after,(w+24,86));board.save(D/('comparatif-'+k+'.png'))
board=Image.new('RGB',(1840,1300),'#11202c');d=ImageDraw.Draw(board);d.text((18,12),'Six faisceaux indépendants — sélection orange de contrôle',font=font,fill='white');d.text((18,48),'Gauche / droite anatomiques • géométrie, normales et UV inchangés',font=small,fill='#bcd0df')
for row,side in enumerate(['left','right']):
 for col,(part,name) in enumerate([('anterior','Antérieur'),('lateral','Moyen'),('posterior','Postérieur')]):
  im=Image.open(D/f'controle-{side}-{part}.png').convert('RGB').resize((550,550));x,y=18+col*608,88+row*604;board.paste(im,(x,y));d.text((x,y+560),name+' '+('gauche' if side=='left' else 'droit'),font=small,fill='white')
board.save(D/'planche-six-faisceaux.png')
board=Image.new('RGB',(1836,1140),'#11202c');d=ImageDraw.Draw(board);d.text((18,12),'Répartition rouge / bleu / vert — contrôle 3D des deux épaules',font=font,fill='white')
for k,(name,title) in enumerate([('face','Face'),('dos','Dos'),('trois-quarts-avant-gauche','Avant gauche'),('trois-quarts-avant-droit','Avant droit'),('trois-quarts-arriere-gauche','Arrière gauche'),('trois-quarts-arriere-droit','Arrière droit')]):
 im=Image.open(D/('apres-'+name+'.png')).convert('RGB').resize((588,438));x,y=18+(k%3)*606,76+(k//3)*520;board.paste(im,(x,y));d.text((x,y+448),title,font=small,fill='white')
board.save(D/'planche-vues-anatomiques.png')
a=np.array(Image.open(D/'avant-neutre.png'));b=np.array(Image.open(D/'apres-neutre.png'));assert np.array_equal(a,b)
record={'status':'passed','matchedReferenceComparisons':3,'neutralPixelsIdentical':True,'frames':len(frames),'allFrameHashesExact':all(sha((D/f).read_bytes())==r['sha256'] for f,r in frames.items())}
assert record['allFrameHashesExact'];(OUT/'render-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
