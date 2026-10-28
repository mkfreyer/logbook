"""Control sheets and image verification; only layout, crop and proportional resize."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from glb_io import sha

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-deltoides-residu-local'
REAR=ROOT/'docs/m4c/meshy-validation-arriere'
OUT=ROOT/'docs/m4c/meshy-posterieur-droit-arrondi'
DEST=OUT/'renders'
meta=json.loads((DEST/'render-metadata.json').read_text())
assert len(meta['frames'])==8
assert sha((OUT/'meshy-posterieur-droit-arrondi.blend').read_bytes())==meta['blendSha256']
frames={f['file']:f for f in meta['frames']}
for f in frames.values():assert sha((DEST/f['file']).read_bytes())==f['sha256']
for key in ['cameraMatrix','orthoScale','resolution','referenceCrop']:
    assert frames['avant-angle-annotation.png'][key]==frames['apres-angle-annotation.png'][key]
geometry=json.loads((OUT/'blender-preservation.json').read_text())
assert geometry['before']==geometry['after']==json.loads((BASE/'blender-preservation.json').read_text())['after']
prior=json.loads((REAR/'renders/render-metadata.json').read_text())
oldframes={f['file']:f for f in prior['frames']}
for file in ['apres-trois-quarts-arriere-droit.png','apres-trois-quarts-arriere-gauche.png','apres-epaules-dos.png']:
    assert oldframes[file]['cameraMatrix']==frames[file]['cameraMatrix']
    assert oldframes[file]['resolution']==frames[file]['resolution']
neutral_a=np.array(Image.open(BASE/'renders/neutre-face.png'))
neutral_b=np.array(Image.open(DEST/'neutre-face.png'))
assert np.array_equal(neutral_a,neutral_b)
left_a=np.array(Image.open(REAR/'renders/apres-trois-quarts-arriere-gauche.png'))
left_b=np.array(Image.open(DEST/'apres-trois-quarts-arriere-gauche.png'))

font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
title=ImageFont.truetype(font,25);label=ImageFont.truetype(font,21);small=ImageFont.truetype(font,18)
def board(file,heading,pairs,width,height):
    gap,top,caption,foot=20,94,34,65
    im=Image.new('RGB',(2*width+3*gap,top+len(pairs)*(height+caption+gap)+foot),'#18202a')
    d=ImageDraw.Draw(im)
    d.text((gap,14),heading,font=title,fill='#f1f5fb')
    d.text((gap,49),'Avant : 18e1a44     /     Après : contour postérieur droit arrondi',font=small,fill='#cad4e1')
    d.text((gap,73),'Même caméra, éclairage et surface 3D. Seul le masque ID8 est étendu.',font=small,fill='#cad4e1')
    for row,(text,before,after) in enumerate(pairs):
        for col,path in enumerate([before,after]):
            x=gap+col*(width+gap);y=top+row*(height+caption+gap)
            d.text((x,y),('Avant — ' if col==0 else 'Après — ')+text,font=label,fill='#f1f5fb')
            image=Image.open(path).convert('RGB');image.thumbnail((width,height),Image.Resampling.LANCZOS)
            im.paste(image,(x+(width-image.width)//2,y+caption+(height-image.height)//2))
    d.text((gap,im.height-54),'Ajout de vert dans le gris ; sept autres masques conservés.',font=small,fill='#cad4e1')
    d.text((gap,im.height-29),'Model created with Meshy — CC BY 4.0 — proposition à valider',font=small,fill='#cad4e1')
    im.save(DEST/file)

board('comparatif-angle-annotation.png','Nouvelle courbe — angle de votre annotation',
      [('épaule droite',DEST/'avant-angle-annotation.png',DEST/'apres-angle-annotation.png')],650,620)
board('comparatif-vues-arriere.png','Contrôle de la forme en trois dimensions',
      [('trois quarts arrière droit',REAR/'renders/apres-trois-quarts-arriere-droit.png',DEST/'apres-trois-quarts-arriere-droit.png'),
       ('deux épaules de dos',REAR/'renders/apres-epaules-dos.png',DEST/'apres-epaules-dos.png')],700,700)
report={'rawBlenderFrames':len(frames),'matchedReferenceCameraAndCrop':True,
        'referenceCropIn1000PixelFrame':[90,278,645,805],
        'closeupPixelSize':list(Image.open(DEST/'apres-angle-annotation.png').size),
        'neutralFacePixelIdenticalTo18e1a44':True,
        'leftRearPixelIdentical':bool(np.array_equal(left_a,left_b)),
        'maxLeftRearChannelDifference8bit':int(np.abs(left_a.astype(int)-left_b.astype(int)).max()),
        'imageProcessing':'Captions, layout and proportional reduction only; no surface pixel retouching.'}
(OUT/'render-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
