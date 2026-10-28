"""Panel composition only. A mirrored comparison view never mirrors the UVs."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'docs/m4c/meshy-bras-prototype/renders'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def panel(name,items,title,note,width=570):
    images=[]
    for file,label,mirror in items:
        im=Image.open(DEST/file).convert('RGB')
        if mirror:im=ImageOps.mirror(im)
        im=im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS);images.append((im,label))
    w=width*len(images)+24*(len(images)+1);h=max(im.height for im,_ in images)+140
    out=Image.new('RGB',(w,h),'#101820');d=ImageDraw.Draw(out)
    d.text((24,14),title,font=ImageFont.truetype(FONT,25),fill='white')
    for i,(im,label) in enumerate(images):
        x=24+i*(width+24);d.text((x,55),label,font=ImageFont.truetype(FONT,21),fill='#dae2ec');out.paste(im,(x,90))
    d.text((24,h-28),note,font=ImageFont.truetype(FONT,15),fill='#c0cad7');out.save(DEST/name)
panel('comparatif-biceps.png',[('biceps-gauche.png','Biceps gauche',False),('biceps-droit.png','Biceps droit — vue réfléchie',True)],
    'Biceps — comparaison gauche/droite à angles équivalents','Courbes propres à chaque surface. Réflexion de la vue pour comparer ; aucun retournement de pixels UV.')
panel('comparatif-triceps.png',[('triceps-gauche.png','Triceps gauche',False),('triceps-droit.png','Triceps droit — vue réfléchie',True)],
    'Triceps — comparaison gauche/droite à angles équivalents','Groupe postérieur et latéral, sans séparation artificielle des chefs. Huit zones validées intactes.')
panel('comparatif-profils.png',[('profil-bras-gauche.png','Profil du bras gauche',False),('profil-bras-droit.png','Profil droit — vue réfléchie',True)],
    'Profils — biceps et triceps expérimentaux','La bande neutre entre les territoires n’est pas un trou : brachial et zones voisines restent à traiter.')
panel('face-dos.png',[('face-complete.png','Face — quatre nouveaux masques',False),('dos-complet.png','Dos — quatre nouveaux masques',False)],
    'Mannequin complet — silhouette Meshy conservée','Même matériau mat neutre. Tous les territoires hors prototype restent neutres.',width=490)
panel('controle-neutre.png',[('reference-neutre.png','Référence d552e23',False),('neutre-complet.png','Prototype sans sélection',False)],
    'Contrôle neutre — surface et huit masques préservés','PNG avant/après identiques octet pour octet. Seul un jeu UV expérimental est ajouté.',width=410)
items=[('biceps-gauche.png','9 · Biceps gauche'),('biceps-droit.png','10 · Biceps droit'),('triceps-gauche.png','11 · Triceps gauche'),('triceps-droit.png','12 · Triceps droit')]
width,height=480,533;out=Image.new('RGB',(1020,1266),'#101820');d=ImageDraw.Draw(out)
d.text((20,16),'Quatre sélections indépendantes — prototype bras',font=ImageFont.truetype(FONT,26),fill='white')
d.text((20,53),'Un seul masque orange par case · vrais rendus Blender · aucune intégration iPhone',font=ImageFont.truetype(FONT,17),fill='#c0cad7')
for i,(file,label) in enumerate(items):
    im=Image.open(DEST/file).convert('RGB').resize((width,height),Image.Resampling.LANCZOS);x=20+(i%2)*500;y=96+(i//2)*585
    out.paste(im,(x,y));d.text((x+5,y+540),label,font=ImageFont.truetype(FONT,20),fill='white')
out.save(DEST/'planche-quatre-zones.png')
print('ARM_COMPARISON_BOARDS_READY',flush=True)
