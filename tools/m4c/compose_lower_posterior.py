"""Verify matched renders and compose boards; never edits mannequin pixels."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from glb_io import sha

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-posterieur-droit-arrondi'
OUT=ROOT/'docs/m4c/meshy-posterieur-droit-bord-inferieur';DEST=OUT/'renders'
meta=json.loads((DEST/'render-metadata.json').read_text())
assert len(meta['frames'])==9
assert sha((OUT/'meshy-posterieur-droit-bord-inferieur.blend').read_bytes())==meta['blendSha256']
frames={f['file']:f for f in meta['frames']}
for f in frames.values():assert sha((DEST/f['file']).read_bytes())==f['sha256']
for key in ['cameraMatrix','orthoScale','resolution','referenceCrop']:
    assert frames['avant-angle-annotation.png'][key]==frames['apres-angle-annotation.png'][key]
oldframes={f['file']:f for f in json.loads((BASE/'renders/render-metadata.json').read_text())['frames']}
for file in ['apres-trois-quarts-arriere-droit.png','apres-trois-quarts-arriere-gauche.png','apres-epaules-dos.png','apres-profil-droit.png']:
    assert oldframes[file]['cameraMatrix']==frames[file]['cameraMatrix']
    assert oldframes[file]['resolution']==frames[file]['resolution']
preservation=json.loads((OUT/'blender-preservation.json').read_text())
assert preservation['before']==preservation['after']==json.loads((BASE/'blender-preservation.json').read_text())['after']
neutral_a=np.array(Image.open(BASE/'renders/neutre-face.png'))
neutral_b=np.array(Image.open(DEST/'neutre-face.png'))
assert np.array_equal(neutral_a,neutral_b)
left_a=np.array(Image.open(BASE/'renders/apres-trois-quarts-arriere-gauche.png'))
left_b=np.array(Image.open(DEST/'apres-trois-quarts-arriere-gauche.png'))

font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
title=ImageFont.truetype(font,25);label=ImageFont.truetype(font,21);small=ImageFont.truetype(font,18)
def board(filename,heading,pairs,width,height):
    gap,top,caption,foot=20,94,34,65
    image=Image.new('RGB',(2*width+3*gap,top+len(pairs)*(height+caption+gap)+foot),'#18202a')
    d=ImageDraw.Draw(image)
    d.text((gap,14),heading,font=title,fill='#f1f5fb')
    d.text((gap,49),'Avant : ad08cef     /     Après : bordure inférieure corrigée',font=small,fill='#cad4e1')
    d.text((gap,73),'Même caméra et lumière ; arrondi supérieur et sept autres masques conservés.',font=small,fill='#cad4e1')
    for row,(text,before,after) in enumerate(pairs):
        for col,path in enumerate([before,after]):
            x=gap+col*(width+gap);y=top+row*(height+caption+gap)
            d.text((x,y),('Avant — ' if col==0 else 'Après — ')+text,font=label,fill='#f1f5fb')
            frame=Image.open(path).convert('RGB');frame.thumbnail((width,height),Image.Resampling.LANCZOS)
            image.paste(frame,(x+(width-frame.width)//2,y+caption+(height-frame.height)//2))
    d.text((gap,image.height-54),'Retrait de vert sous la nouvelle courbe ; aucune sculpture.',font=small,fill='#cad4e1')
    d.text((gap,image.height-29),'Model created with Meshy — CC BY 4.0 — proposition à valider',font=small,fill='#cad4e1')
    image.save(DEST/filename)

board('comparatif-angle-annotation.png','Bordure inférieure — nouvelle annotation',
      [('contour vert/gris',DEST/'avant-angle-annotation.png',DEST/'apres-angle-annotation.png')],650,600)
board('comparatif-vues-arriere.png','Contrôle du raccord dans les vues arrière',
      [('trois quarts arrière droit',BASE/'renders/apres-trois-quarts-arriere-droit.png',DEST/'apres-trois-quarts-arriere-droit.png'),
       ('deux épaules de dos',BASE/'renders/apres-epaules-dos.png',DEST/'apres-epaules-dos.png')],700,700)
report={'rawBlenderFrames':len(frames),'matchedReferenceCameraAndCrop':True,
        'referenceCropIn1000PixelFrame':[160,376,607,786],
        'closeupPixelSize':list(Image.open(DEST/'apres-angle-annotation.png').size),
        'neutralFacePixelIdenticalToAd08cef':True,
        'leftRearPixelIdentical':bool(np.array_equal(left_a,left_b)),
        'maxLeftRearChannelDifference8bit':int(np.abs(left_a.astype(int)-left_b.astype(int)).max()),
        'imageProcessing':'Captions, layout and proportional reduction only. No surface pixel repainting.'}
(OUT/'render-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
