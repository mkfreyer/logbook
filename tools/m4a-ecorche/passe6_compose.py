"""Triple comparison layouts; native raw render pixels, no resize or cleanup."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args();root=a.asset.resolve();out=root/'renders';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
def sheet(name,title,items):
 images=[Image.open(out/file).convert('RGB')for file,label in items];height=max(i.height for i in images);width=sum(i.width for i in images)+24*(len(images)+1);canvas=Image.new('RGB',(width,height+132),(25,27,30));d=ImageDraw.Draw(canvas);d.text((24,16),title,font=font,fill='white');x=24
 for img,(file,label)in zip(images,items):d.text((x,61),label,font=small,fill=(220,220,220));canvas.paste(img,(x,108));x+=img.width+24
 dest=out/(name+'.png');canvas.save(dest);records.append({'file':dest.name,'sha256':sha(dest),'sources':[{'file':f,'sha256':sha(out/f)}for f,label in items],'raw_pixels_resized':False,'raw_pixels_retouched':False})
labels={'epaules-face':'Épaules — face','epaules-dos':'Épaules — arrière','epaule-droite':'Épaule droite — trois quarts','epaule-gauche':'Épaule gauche — trois quarts','epaule-profil':'Deltoïde — profil','epaule-arriere':'Deltoïde — trois quarts arrière'}
for view,label in labels.items():sheet('comparatif-'+view,label,[('p4-'+view+'.png','Passe 4'),('p5-'+view+'.png','Passe 5 — deltoïdes refusés'),('p6-'+view+'.png','Passe 6 — proposition')])
sheet('validation-corps','Passe 6 — tête, cou et corps P5 conservés',[('p6-face.png','Face'),('p6-profil.png','Profil'),('p6-dos.png','Dos')])
sheet('deux-deltoides','Passe 6 — les deux deltoïdes',[('p6-epaule-droite.png','Droite'),('p6-epaule-gauche.png','Gauche')])
sheet('profil-arriere','Passe 6 — changements de courbure',[('p6-epaule-profil.png','Profil'),('p6-epaule-arriere.png','Trois quarts arrière')])
(out/'planches.json').write_text(json.dumps({'composer_sha256':sha(Path(__file__)),'sheets':records},ensure_ascii=False,indent=2)+'\n');print('PASSE6_SHEETS',len(records))
