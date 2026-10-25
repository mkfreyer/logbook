"""Native before/after pixels and focused groove/belly crops; no paint or retouch."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args();root=a.asset.resolve();out=root/'renders';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);records=[]
def sheet(name,title,items,crop=None):
 images=[Image.open(out/f).convert('RGB')for f,label in items]
 if crop:images=[p.crop(crop)for p in images]
 canvas=Image.new('RGB',(sum(p.width for p in images)+24*(len(images)+1),max(p.height for p in images)+132),(25,27,30));d=ImageDraw.Draw(canvas);d.text((24,16),title,font=font,fill='white');x=24
 for pic,(f,label)in zip(images,items):d.text((x,61),label,font=small,fill=(220,220,220));canvas.paste(pic,(x,108));x+=pic.width+24
 dest=out/(name+'.png');canvas.save(dest);records.append({'file':dest.name,'sha256':sha(dest),'sources':[{'file':f,'sha256':sha(out/f)}for f,label in items],'crop_px':crop,'pixels_resized':False,'pixels_retouched':False})
for view,title in [('reference','Vue de référence — bandes locales uniquement'),('epaule-gauche','Épaule gauche — correction symétrique'),('face','Épaules de face'),('profil','Épaule de profil')]:
 sheet('comparatif-'+view,title,[('avant-'+view+'.png','P4 + tête P5'),('apres-'+view+'.png','Creux localisés')])
pair=[('avant-reference.png','Avant'),('apres-reference.png','Après')]
sheet('creux-1-detail','Premier creux — terminaison',pair,(96,834,339,1152))
sheet('creux-2-detail','Second creux — délimitation',pair,(360,180,774,1125))
sheet('ventre-preserve','Bombé principal — géométrie inchangée',pair,(288,435,522,795))
sheet('deux-epaules','Proposition — les deux épaules',[('apres-reference.png','Droite'),('apres-epaule-gauche.png','Gauche')])
(out/'planches.json').write_text(json.dumps({'composer_sha256':sha(Path(__file__)),'sheets':records},ensure_ascii=False,indent=2)+'\n');print('SHEETS',len(records))
