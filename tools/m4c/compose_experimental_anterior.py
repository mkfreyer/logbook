"""Layout/crop only of real Blender output; never repaints model pixels."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4c/experience-anterieur-droit/renders'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def board(file,items,title,note,crop=None,width=660):
    panels=[]
    for image,label in items:
        im=Image.open(OUT/image).convert('RGB')
        if crop:im=im.crop(crop)
        im=im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS)
        panels.append((im,label))
    w=width*len(panels)+24*(len(panels)+1);h=max(im.height for im,_ in panels)+145
    canvas=Image.new('RGB',(w,h),'#101820');draw=ImageDraw.Draw(canvas)
    draw.text((24,15),title,font=ImageFont.truetype(FONT,25),fill='white')
    for i,(im,label) in enumerate(panels):
        x=24+i*(width+24);draw.text((x,56),label,font=ImageFont.truetype(FONT,21),fill='#dae2ec');canvas.paste(im,(x,91))
    draw.text((24,h-30),note,font=ImageFont.truetype(FONT,16),fill='#c0cad7');canvas.save(OUT/file)
board('comparatif-reference.png',[('avant-reference.png','Avant — masques 168ac61'),('apres-reference.png','Après — prototype isolé ID 6')],
      'Bord côté pectoral du deltoïde antérieur droit',
      'Tracé de la capture gauche transposé au droit ; même caméra et lumière avant/après.',width=690)
board('comparatif-serre.png',[('avant-reference.png','Avant — bord validé'),('apres-reference.png','Après — bord expérimental')],
      'Comparatif serré, caméra et cadrage identiques',
      'Sept autres masques intacts. Le pectoral existant limite localement l’extension.',crop=(420,220,940,752))
board('comparatif-neutre.png',[('avant-neutre-reference.png','Avant — sans sélection'),('apres-neutre-reference.png','Après — sans sélection')],
      'Contrôle neutre — surfaces et UV inchangés',
      'Les deux PNG sources sont identiques octet pour octet. Aucun sommet déplacé.',width=690)
board('planche-controles.png',[('face.png','Face'),('profil-droit.png','Profil droit'),('trois-quarts-avant-droit.png','Trois quarts avant droit')],
      'Prototype ID 6 — contrôle de la limite en 3D',
      'Vues anatomiques non inversées. Aucun changement dans Logbook ou dans les PR #17 et #18.',width=500)
