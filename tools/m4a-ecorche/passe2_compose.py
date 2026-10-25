"""Comparison layouts only: unretouched Blender pixels at their native size."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args();root=a.asset.resolve();renders=root/'renders'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23);title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',30);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
def sheet(name,heading,columns,footer):
 images=[Image.open(renders/f).convert('RGB')for f,_ in columns];w=max(x.width for x in images);h=max(x.height for x in images);page=Image.new('RGB',(len(images)*w,h+164),'#292929');draw=ImageDraw.Draw(page);draw.text((24,16),heading,font=title,fill='#f3f0eb')
 for i,((file,label),im)in enumerate(zip(columns,images)):
  draw.text((i*w+24,66),label,font=font,fill='#ddd8ce');page.paste(im,(i*w+(w-im.width)//2,108));im.close()
 draw.text((24,h+125),footer,font=small,fill='#ddd8ce');file=renders/name;page.save(file)
 records.append({'file':name,'sha256':sha(file),'inputs':[{'file':f,'sha256':sha(renders/f)}for f,_ in columns],'render_pixels_retouch':False})
credit='Mat neutre identique avant/après. Source : Beatriz Gomez Santamaria — CC BY 4.0. Adaptation Logbook.'
for view,label in [('face','Face'),('profil','Profil'),('dos','Dos'),('epaule-avant','Deltoïde, vue antérieure'),('epaule-profil','Deltoïde, vue latérale'),('epaule-arriere','Deltoïde, vue postérieure'),('haut-dos','Haut du dos')]:
 sheet('comparatif-'+view+'.png','Passe 2 — '+label,[('avant-'+view+'.png','Avant — passe 1 validée'),('apres-'+view+'.png','Après — passe 2 ciblée')],credit)
sheet('validation-mat-neutre.png','Passe 2 — silhouette conservée, matériau mat neutre',[('apres-face.png','Face'),('apres-profil.png','Profil'),('apres-dos.png','Dos')],'Rendus Blender réels. Source : Beatriz Gomez Santamaria — CC BY 4.0. Aucune intégration applicative.')
sheet('deltoides-mat-neutre.png','Passe 2 — contrôle des formes de l’épaule',[('apres-epaule-avant.png','Antérieur oblique'),('apres-epaule-profil.png','Latéral'),('apres-epaule-arriere.png','Postérieur oblique')],'Un muscle continu, trois régions de forme. Aucun trait de séparation peint ; différenciation à valider visuellement.')
(renders/'comparisons.json').write_text(json.dumps({'composer_sha256':sha(Path(__file__)),'method':'Raw PNG pixels pasted at native size; labels and borders only.','sheets':records},ensure_ascii=False,indent=2)+'\n');print('PASSE2_COMPARISONS',len(records))
