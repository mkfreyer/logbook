"""Layout/crop actual Blender pixels only; no guide painting or image retouch."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

p = argparse.ArgumentParser()
p.add_argument('--asset',type=Path,required=True)
a = p.parse_args()
root = a.asset/'renders'
fontpath = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = lambda n:ImageFont.truetype(fontpath,n)
sha = lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
records = []


def sheet(name,title,items,columns=2,size=(640,768),notes=()):
    gap,top,bottom = 20,94,54+len(notes)*28
    width = columns*size[0]+(columns+1)*gap
    rows = (len(items)+columns-1)//columns
    height = top+rows*(size[1]+54+gap)+bottom
    canvas = Image.new('RGB',(width,height),'#16191d')
    draw = ImageDraw.Draw(canvas)
    draw.text((gap,18),title,font=font(27),fill='#f5f5f4')
    draw.text((gap,56),'0ab3d83 intact • P4 + tête P5 • guides 3D uniquement • aucune sculpture',font=font(18),fill='#c8cbd0')
    source = []
    for i,(filename,label,crop) in enumerate(items):
        image = Image.open(root/filename).convert('RGB')
        if crop:
            image = image.crop(tuple(int(x*3)for x in crop))
        scale = min(size[0]/image.width,size[1]/image.height)
        image = image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
        x = gap+(i%columns)*(size[0]+gap)
        y = top+(i//columns)*(size[1]+54+gap)
        draw.text((x,y),label,font=font(21),fill='#f5f5f4')
        canvas.paste(image,(x+(size[0]-image.width)//2,y+38))
        source.append({'file':filename,'sha256':sha(root/filename),'crop_reference_px':crop})
    y = height-bottom+12
    for note in notes:
        draw.text((gap,y),note,font=font(17),fill='#c8cbd0')
        y += 28
    path = root/(name+'.png')
    canvas.save(path)
    records.append({'file':path.name,'sha256':sha(path),'sources':source,
                    'operation':'layout, labels, uniform resize and stated crops only'})


sheet('controle-trajets','Validation des trajets — même caméra, même lumière, même géométrie',[
    ('reference-sans-guides.png','A — Géométrie P4 intacte',None),
    ('reference-anciens-rouges.png','B — Anciens trajets annotés en rouge',None),
    ('reference-nouveaux-bleus.png','C — Trajets souhaités en bleu',None),
    ('reference-superposition.png','D — Superposition ancien / demandé',None)],
    notes=('Rouge : ancien. Bleu : demandé. Dans D, le haut commun du premier trajet reste rouge.',
           'Pointillés orange : repères des portions de courbe masquées par le bras ; à arbitrer.',
           'Cadrage recalé manuellement sur la référence ; validation des guides encore requise.'))
sheet('detail-terminaisons','Terminaisons — les positions demandées sont conservées, sans sculpture',[
    ('reference-sans-guides.png','Premier trajet — P4 intact',(30,270,115,384)),
    ('reference-superposition.png','Premier trajet — guides',(30,270,115,384)),
    ('reference-sans-guides.png','Second trajet — P4 intact',(120,240,220,384)),
    ('reference-superposition.png','Second trajet — guides',(120,240,220,384))],
    size=(510,690),notes=('Les extraits proviennent des mêmes pixels Blender ; aucun trait ajouté après rendu.',
                         'Les guides restent sur le deltoïde ; les repères orange signalent les recouvrements du bras.'))
sheet('controle-surface-3d','Guides sur le volume réel — autres vues de contrôle',[
    ('profil-guides.png','Profil — mêmes courbes 3D',None),
    ('face-guides.png','Face — guides préparés en miroir',None)],
    size=(640,576),notes=('Les masquages changent avec l’angle : ce sont des courbes sur la surface, pas des traits écran.',))
sheet('controle-deux-epaules','Deux épaules — préparation symétrique sans aucune déformation',[
    ('reference-superposition.png','Épaule droite',None),
    ('reference-epaule-gauche.png','Épaule gauche — caméra miroir',None)],
    notes=('Les deux maillages P4 sont intégralement conservés ; seuls des objets CURVE ont été ajoutés.',))
(root/'planches.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print('COMPOSED',len(records))
