"""Comparison layouts only: unretouched Blender pixels at their native size."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np
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
credit='Mat neutre identique, éclairage symétrique. Source : Beatriz Gomez Santamaria — CC BY 4.0.'
for view,label in [('face','Face'),('profil','Profil'),('dos','Dos'),('epaule-droite','Épaule droite anatomique'),('epaule-gauche','Épaule gauche anatomique'),('epaule-profil','Deltoïde, profil'),('epaule-arriere','Deltoïde, postérieur'),('haut-dos','Haut du dos'),('pectoraux','Pectoraux'),('thorax-lateral','Pectoral / thorax latéral')]:
 sheet('comparatif-'+view+'.png','Passe 3 — '+label,[('avant-'+view+'.png','Avant — passe 2'),('apres-'+view+'.png','Après — passe 3')],credit)
sheet('validation-mat-neutre.png','Passe 3 — validation des formes en mat neutre',[('apres-face.png','Face'),('apres-profil.png','Profil'),('apres-dos.png','Dos')],credit)
sheet('deux-epaules.png','Passe 3 — les deux épaules, éclairage équilibré',[('apres-epaule-droite.png','Droite anatomique'),('apres-epaule-gauche.png','Gauche anatomique')],credit)
sheet('deltoide-trois-angles.png','Passe 3 — contrôle des trois portions du deltoïde',[('apres-epaule-droite.png','Antérieur oblique'),('apres-epaule-profil.png','Latéral'),('apres-epaule-arriere.png','Postérieur oblique')],'Trois régions de forme continues. Pas de séparation peinte ni segmentation médicale revendiquée.')
sheet('diagnostic-eclairage.png','Symétrie — même géométrie de passe 2, deux éclairages',[('../../ecorche-beatriz-passe2/renders/apres-face.png','Ancien éclairage dissymétrique'),('avant-face.png','Éclairage symétrique de contrôle')],'La géométrie et le matériau sont identiques. Seul le dispositif lumineux change entre ces deux images.')
(renders/'comparisons.json').write_text(json.dumps({'composer_sha256':sha(Path(__file__)),'method':'Raw PNG pixels pasted at native size; labels and borders only.','sheets':records},ensure_ascii=False,indent=2)+'\n');print('PASSE3_COMPARISONS',len(records))

# Measurement only: no blurred image is written or substituted for a render.
metrics={};metric_inputs=[]
for label,file in [('pass2_old_lights',renders/'../../ecorche-beatriz-passe2/renders/apres-face.png'),('pass2_balanced_lights',renders/'avant-face.png'),('pass3_balanced_lights',renders/'apres-face.png')]:
 rgb=np.asarray(Image.open(file).convert('RGB').filter(ImageFilter.GaussianBlur(2)),float);luma=rgb@np.array([.2126,.7152,.0722]);left=luma[235:350,185:310];right=luma[235:350,410:535][:,::-1];mask=(left>60)&(right>60);metrics[label]=float(np.mean(abs(left-right)[mask])/np.mean((left+right)[mask]/2));metric_inputs.append({'file':str(file.relative_to(renders)),'sha256':sha(file)})
(root/'lighting-audit.json').write_text(json.dumps({'method':'Relative displayed-luminance error on mirrored shoulder ROIs; Gaussian radius 2 px for noise measurement only, images never altered.','left_roi_xyxy':[185,235,310,350],'right_roi_xyxy':[410,235,535,350],'background_threshold_8bit':60,'relative_errors':metrics,'inputs':metric_inputs,'composer_sha256':sha(Path(__file__))},indent=2)+'\n')
