"""Panels from genuine Blender renders. Mirror display only, never atlas pixels."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4c/experience-anterieurs-bilateraux';DEST=OUT/'renders'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def board(name,items,title,note,width=650):
    panels=[]
    for file,label,mirror in items:
        im=Image.open(DEST/file).convert('RGB')
        if mirror:im=ImageOps.mirror(im)
        im=im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS);panels.append((im,label))
    w=width*len(panels)+24*(len(panels)+1);h=max(im.height for im,_ in panels)+140
    canvas=Image.new('RGB',(w,h),'#101820');draw=ImageDraw.Draw(canvas)
    draw.text((24,14),title,font=ImageFont.truetype(FONT,25),fill='white')
    for i,(im,label) in enumerate(panels):
        x=24+i*(width+24);draw.text((x,55),label,font=ImageFont.truetype(FONT,21),fill='#dae2ec');canvas.paste(im,(x,90))
    draw.text((24,h-27),note,font=ImageFont.truetype(FONT,16),fill='#c0cad7');canvas.save(DEST/name)
board('comparatif-gauche.png',[('gauche-avant.png','Gauche avant — 7b69e3d',False),('epaule-gauche-nouvelle.png','Gauche après — transposition 3D',False)],
    'Deltoïde antérieur gauche — caméra et lumière identiques','Seul le bord côté pectoral du masque gauche change. Aucune déformation du mannequin.')
board('comparaison-bilaterale.png',[('epaule-droite-validee.png','Droite validée — reflet pour comparer',True),('epaule-gauche-nouvelle.png','Gauche — adaptation sur sa surface',False)],
    'Comparaison des deux épaules à angles anatomiques équivalents','Caméras ±45°, mêmes cadrage et échelle. Reflet de la vue droite uniquement, jamais des UV.')
board('comparaison-contours.png',[('silhouette-droite-validee.png','Référence droite — vue réfléchie',True),('silhouette-gauche-avant.png','Gauche avant',False),('silhouette-gauche-apres.png','Gauche après',False)],
    'Contrôle des silhouettes colorables — rendu 3D sans ombrage','Les différences restantes reflètent les surfaces réelles et les frontières voisines préservées.',width=500)
board('planche-bilaterale.png',[('face-bilaterale.png','Face — deux antérieurs',False),('trois-quarts-avant-droit.png','Trois quarts avant droit',False),('trois-quarts-avant-gauche.png','Trois quarts avant gauche',False)],
    'Proposition bilatérale — masque droit validé inchangé','Deux zones orange pour contrôle. Les six autres zones restent neutres sur ces rendus.',width=520)
board('comparatif-neutre.png',[('neutre-avant.png','Avant — géométrie validée',False),('neutre-complet.png','Après — géométrie identique',False)],
    'Contrôle neutre — zéro changement géométrique','Les PNG sources avant/après sont identiques octet pour octet.',width=400)
right=np.fliplr(np.array(Image.open(DEST/'silhouette-droite-validee.png').convert('L'))>127)
metrics={}
for label,file in [('before','silhouette-gauche-avant.png'),('after','silhouette-gauche-apres.png')]:
    left=np.array(Image.open(DEST/file).convert('L'))>127
    metrics[label]={'intersectionOverUnion':float((left&right).sum()/(left|right).sum()),'leftPixels':int(left.sum()),'rightPixels':int(right.sum())}
(OUT/'silhouette-comparison.json').write_text(json.dumps({'method':'Threshold actual emissive mask renders at 0.5, anatomically mirrored cameras ±45deg. Reflect only the rendered right image, no registration/translation or UV pixel reflection. Finite raster comparison, not exact geometric symmetry.','results':metrics},indent=2)+'\n')
print('SILHOUETTE_COMPARISON',metrics,flush=True)
