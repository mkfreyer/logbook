"""Lay out unretouched Blender renders; only labels and borders are added."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args();root=a.asset.resolve();renders=root/'renders'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
title=ImageFont.truetype(bold,30);label=ImageFont.truetype(font,23);small=ImageFont.truetype(font,19)
records=[]
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def sheet(name,heading,columns,note):
 images=[Image.open(renders/file).convert('RGB')for file,text in columns];w=max(im.width for im in images);h=max(im.height for im in images)
 page=Image.new('RGB',(len(images)*w,h+164),'#0a1522');d=ImageDraw.Draw(page);d.text((24,16),heading,font=title,fill='#edf3ff')
 for i,((file,text),im)in enumerate(zip(columns,images)):
  d.text((i*w+24,65),text,font=label,fill='#c4d2e5');page.paste(im,(i*w+(w-im.width)//2,108));im.close()
 d.text((24,h+123),note,font=small,fill='#c4d2e5');file=renders/name;page.save(file)
 records.append({'file':name,'sha256':sha(file),'inputs':[{'file':f,'sha256':sha(renders/f)}for f,_ in columns],'render_pixels_retouch':False})
for view,title_fr in [('face','Face'),('profil','Profil'),('dos','Dos'),('trois-quarts','Trois quarts')]:
 sheet('comparatif-'+view+'.png','Logbook — '+title_fr,[('avant-'+view+'.png','Original asymétrique'),('apres-'+view+'.png','Reconstruction symétrique + volumes')],'Même cadrage, matériau et éclairage. Original : Beatriz Gomez Santamaria — CC BY 4.0.')
sheet('planche-validation.png','Écorché athlétique — proposition à valider',[('apres-face.png','Face'),('apres-profil.png','Profil'),('apres-dos.png','Dos')],'Rendus Blender réels. Aucun changement applicatif. Source : Beatriz Gomez Santamaria — CC BY 4.0.')
sheet('comparatif-volumes.png','Volumes — reconstruction seule / retouche athlétique',[('base-symetrique-trois-quarts.png','Symétrie seule'),('apres-trois-quarts.png','Symétrie + retouche des volumes')],'Les deux corps sont reconstruits. Le gain visible ici vient uniquement de la retouche des volumes.')
sheet('controle-deltoide.png','Épaule — contrôle rapproché, trois faisceaux encore à valider',[('deltoide-avant.png','Vue antérieure oblique'),('deltoide-arriere.png','Vue postérieure oblique')],'Le deltoïde reste un objet par côté. Aucune segmentation indépendante de ses trois faisceaux n’est revendiquée.')
sheet('selection-comparatif.png','Démonstration de coloration indépendante',[('apres-trois-quarts.png','Matériau neutre'),('selection-pectorale.png','Pectoral gauche orange')],'Démonstration de matériau Blender ; aucune interactivité applicative développée.')
(renders/'comparisons.json').write_text(json.dumps({'composer_sha256':sha(Path(__file__)),'method':'Unretouched input PNG pixels pasted at native size; labels and borders only.','sheets':records},ensure_ascii=False,indent=2)+'\n')
print('COMPARISONS_CREATED',len(records))
