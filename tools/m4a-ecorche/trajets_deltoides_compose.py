"""Lay out original before/after pixels, without color annotations or retouching."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args();root=a.asset.resolve();out=root/'renders'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
def sheet(name,title,items,crop=None):
    images=[Image.open(out/file).convert('RGB')for file,label in items]
    if crop:images=[img.crop(crop)for img in images]
    canvas=Image.new('RGB',(sum(i.width for i in images)+24*(len(images)+1),max(i.height for i in images)+132),(25,27,30));d=ImageDraw.Draw(canvas);d.text((24,16),title,font=font,fill='white');x=24
    for img,(file,label)in zip(images,items):d.text((x,61),label,font=small,fill=(220,220,220));canvas.paste(img,(x,108));x+=img.width+24
    path=out/(name+'.png');canvas.save(path);records.append({'file':path.name,'sha256':sha(path),'sources':[{'file':f,'sha256':sha(out/f)}for f,label in items],'crop_px':crop,'raw_pixels_resized':False,'raw_pixels_retouched':False})
labels={'reference':'Épaule droite — caméra de référence','epaule-gauche':'Épaule gauche','epaules-face':'Les deux épaules — face','epaules-dos':'Les deux épaules — dos','epaule-profil':'Deltoïde — profil','epaule-arriere':'Deltoïde — trois quarts arrière','face':'Corps — face','profil':'Corps — profil','trois-quarts':'Corps — trois quarts','dos':'Corps — dos'}
for view,label in labels.items():sheet('comparatif-'+view,label,[('avant-'+view+'.png','Avant — P4 + tête P5'),('apres-'+view+'.png','Après — creux déplacés')])
sheet('comparatif-reference-detail','Détail des deux trajets — sans annotations',[('avant-reference.png','Avant'),('apres-reference.png','Après')],(238,170,638,650))
sheet('deux-deltoides-apres','Proposition — les deux épaules symétriques',[('apres-reference.png','Droite'),('apres-epaule-gauche.png','Gauche')])
(out/'planches.json').write_text(json.dumps({'composer_sha256':sha(Path(__file__)),'sheets':records},ensure_ascii=False,indent=2)+'\n');print('TRAJETS_SHEETS',len(records))
