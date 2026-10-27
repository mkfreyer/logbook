"""Matched color boards and mirrored silhouette diagnostics, no asset painting."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from glb_io import sha
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-posterieur-droit-bord-inferieur'
OUT=ROOT/'docs/m4c/meshy-posterieurs-harmonises';DEST=OUT/'renders'
meta=json.loads((DEST/'render-metadata.json').read_text());assert len(meta['frames'])==9
assert sha((OUT/'meshy-posterieurs-harmonises.blend').read_bytes())==meta['blendSha256']
frames={f['file']:f for f in meta['frames']}
for f in frames.values():assert sha((DEST/f['file']).read_bytes())==f['sha256']
for key in ['cameraMatrix','orthoScale','resolution']:
    assert frames['avant-dos-grand.png'][key]==frames['apres-dos-grand.png'][key]
prior={f['file']:f for f in json.loads((BASE/'renders/render-metadata.json').read_text())['frames']}
for name in ['apres-trois-quarts-arriere-gauche.png','apres-trois-quarts-arriere-droit.png']:
    assert frames[name]['cameraMatrix']==prior[name]['cameraMatrix']
    assert frames[name]['resolution']==prior[name]['resolution']
neutral_a=np.array(Image.open(BASE/'renders/neutre-face.png'));neutral_b=np.array(Image.open(DEST/'neutre-face.png'));assert np.array_equal(neutral_a,neutral_b)
right_a=np.array(Image.open(DEST/'avant-silhouette-droit.png'));right_b=np.array(Image.open(DEST/'apres-silhouette-droit.png'));assert np.array_equal(right_a,right_b)
colored_a=np.array(Image.open(BASE/'renders/apres-trois-quarts-arriere-droit.png'));colored_b=np.array(Image.open(DEST/'apres-trois-quarts-arriere-droit.png'))
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';title=ImageFont.truetype(font,25);label=ImageFont.truetype(font,21);small=ImageFont.truetype(font,18)

def pair_board(name,heading,left,right,labels,width=700,height=700,mirror_left=False):
    gap,top,foot=20,124,75
    board=Image.new('RGB',(2*width+3*gap,top+height+foot),'#18202a');d=ImageDraw.Draw(board)
    d.text((gap,14),heading,font=title,fill='#f1f5fb')
    d.text((gap,49),'ID5 gauche adapté sur sa surface 3D ; ID8 droit et six autres masques inchangés.',font=small,fill='#cad4e1')
    for col,path in enumerate([left,right]):
        x=gap+col*(width+gap);d.text((x,84),labels[col],font=label,fill='#f1f5fb')
        im=Image.open(path).convert('RGB')
        if col==0 and mirror_left:im=ImageOps.mirror(im)
        im.thumbnail((width,height),Image.Resampling.LANCZOS)
        board.paste(im,(x+(width-im.width)//2,top+(height-im.height)//2))
    d.text((gap,board.height-61),'Miroir éventuel : présentation uniquement, jamais copie des pixels UV.',font=small,fill='#cad4e1')
    d.text((gap,board.height-34),'Model created with Meshy — CC BY 4.0 — proposition à valider',font=small,fill='#cad4e1')
    board.save(DEST/name)

pair_board('comparatif-gauche.png','Épaule gauche — avant / après',BASE/'renders/apres-trois-quarts-arriere-gauche.png',DEST/'apres-trois-quarts-arriere-gauche.png',['Avant — 977f68a','Après — adaptation gauche'])
pair_board('comparatif-dos.png','Deux épaules de dos — avant / après',DEST/'avant-dos-grand.png',DEST/'apres-dos-grand.png',['Avant — 977f68a','Après — adaptation gauche'],1000,640)
pair_board('comparaison-miroir-couleur.png','Comparaison en miroir des deux épaules',DEST/'apres-trois-quarts-arriere-gauche.png',DEST/'apres-trois-quarts-arriere-droit.png',['Gauche — image inversée pour comparer','Droite — référence conservée'],mirror_left=True)

reference=right_a[:,:,0]>=128
stats=[];panels=[]
for state in ['avant','apres']:
    left=np.array(ImageOps.mirror(Image.open(DEST/(state+'-silhouette-gauche.png'))))[:,:,0]>=128
    common=left&reference;union=left|reference;iou=float(common.sum()/union.sum())
    stats.append({'state':state,'leftProjectedPixels':int(left.sum()),'rightProjectedPixels':int(reference.sum()),'areaRatioLeftOverRight':float(left.sum()/reference.sum()),'IoU':iou})
    rgb=np.zeros((*left.shape,3),np.uint8);rgb[left&~reference]=[62,204,235];rgb[reference&~left]=[234,91,178];rgb[common]=[235,239,246]
    panels.append(Image.fromarray(rgb))
assert stats[1]['IoU']>stats[0]['IoU'],'Visual silhouette agreement must improve'
width,height,gap=700,700,20
board=Image.new('RGB',(1460,900),'#18202a');d=ImageDraw.Draw(board)
d.text((gap,14),'Silhouettes vertes — comparaison géométrique en miroir',font=title,fill='#f1f5fb')
d.text((gap,51),'Diagnostic de masques rendu sans éclairage ; aucune mise à l’échelle relative.',font=small,fill='#cad4e1')
for col,(im,stat) in enumerate(zip(panels,stats)):
    x=gap+col*(width+gap);im=im.resize((width,height),Image.Resampling.NEAREST);board.paste(im,(x,116))
    d.text((x,85),('Avant' if col==0 else 'Après')+f" — recouvrement {100*stat['IoU']:.1f} %",font=label,fill='#f1f5fb')
d.text((gap,837),'Cyan : gauche miroir seule   |   Rose : droite seule   |   Blanc : superposition',font=small,fill='#cad4e1')
d.text((gap,866),'Mesure sur ces vues uniquement ; les asymétries réelles du Meshy restent présentes.',font=small,fill='#cad4e1')
board.save(DEST/'comparaison-silhouettes-miroir.png')
report={'referenceCommit':'977f68a','rawBlenderFrames':len(frames),
    'matchedBeforeAfterBackCameraAndLighting':True,'rightUnlitSilhouettePixelIdentical':True,
    'neutralFacePixelIdentical':True,'maxColoredRightChannelDifference8bit':int(np.abs(colored_a.astype(int)-colored_b.astype(int)).max()),
    'silhouetteComparison':stats,'silhouetteMethod':'Actual unlit material masks, left image reflected for visual comparison only, threshold 128/255, equal cameras and scale.',
    'imageProcessing':'Layout, captions, proportional reduction, explicitly labelled presentation mirror and numerical silhouette overlay only. Raw model renders unchanged.'}
(OUT/'render-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
