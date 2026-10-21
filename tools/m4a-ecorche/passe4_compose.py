"""Captioned layouts only: raw Blender pixels copied at native size, no image cleanup."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args();root=a.asset.resolve();out=root/'renders';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
def sheet(name,title,items):
 images=[Image.open(out/file).convert('RGB')for file,label in items];height=max(i.height for i in images);width=sum(i.width for i in images)+24*(len(images)+1);canvas=Image.new('RGB',(width,height+132),(25,27,30));d=ImageDraw.Draw(canvas);d.text((24,16),title,font=font,fill='white');x=24
 for img,(file,label)in zip(images,items):
  d.text((x,61),label,font=small,fill=(220,220,220));canvas.paste(img,(x,108));x+=img.width+24
 dest=out/(name+'.png');canvas.save(dest);records.append({'file':dest.name,'sha256':sha(dest),'sources':[{'file':f,'sha256':sha(out/f)}for f,label in items],'raw_pixels_resized':False,'raw_pixels_retouched':False})
labels={'face':'Face','profil':'Profil','dos':'Dos','epaule-droite':'Épaule droite — trois quarts','epaule-gauche':'Épaule gauche — trois quarts','epaule-profil':'Deltoïde — profil','gorge':'Gorge — face','gorge-trois-quarts':'Gorge — trois quarts','tete':'Visage — face','tete-profil':'Tête — profil','tete-trois-quarts':'Visage — trois quarts'}
for view,label in labels.items():sheet('comparatif-'+view,label,[('avant-'+view+'.png','Passe 3 — avant'),('apres-'+view+'.png','Passe 4 — proposition')])
sheet('validation-mat-neutre','Quatrième passe — même matériau mat neutre',[('apres-face.png','Face'),('apres-profil.png','Profil'),('apres-dos.png','Dos')])
sheet('deux-epaules','Épaules — finition antérieure à volume conservé',[('apres-epaule-droite.png','Droite'),('apres-epaule-gauche.png','Gauche')])
sheet('tete-trois-vues','Tête simplifiée — proposition à valider',[('apres-tete.png','Face'),('apres-tete-trois-quarts.png','Trois quarts'),('apres-tete-profil.png','Profil')])
sheet('gorge-deux-vues','Gorge / cou — enveloppe continue',[('apres-gorge.png','Face'),('apres-gorge-trois-quarts.png','Trois quarts')])
(out/'planches.json').write_text(json.dumps({'composer_sha256':sha(Path(__file__)),'sheets':records},ensure_ascii=False,indent=2)+'\n');print('PASSE4_SHEETS',len(records))
