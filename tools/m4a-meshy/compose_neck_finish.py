"""Compose matched 62000ae/local-finish renders; raw images stay untouched."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args();root=a.asset.resolve()
meta=json.loads((root/'assemblage.json').read_text());records={m:json.loads((root/'renders'/m/'metadata.json').read_text()) for m in ['before','after']}
assert all(r['master_sha256']==meta['master_sha256'] for r in records.values())
assert records['before']['lights']==records['after']['lights']
frames={m:{f['file']:f for f in r['frames']} for m,r in records.items()}
common={'tete-face.png','tete-profil.png','tete-trois-quarts.png','raccord-profil.png','raccord-face.png','raccord-trois-quarts.png'}
assert set(frames['before'])==common and set(frames['after'])==common|{'face.png'}
for mode,items in frames.items():
 for file,f in items.items():assert hashlib.sha256((root/'renders'/mode/file).read_bytes()).hexdigest()==f['sha256']
for file in common:
 for field in ['camera_matrix','ortho_scale','resolution','samples']:assert frames['before'][file][field]==frames['after'][file][field]
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';title=ImageFont.truetype(font,26);label=ImageFont.truetype(font,21);small=ImageFont.truetype(font,17)
def pair(path,heading,views):
 width,margin,header,caption,footer=600,20,88,36,70
 im=Image.new('RGB',(2*width+3*margin,header+len(views)*(width+caption+margin)+footer),'#141b24');d=ImageDraw.Draw(im)
 d.text((margin,14),heading,font=title,fill='#f0f4fa');d.text((margin,50),'Avant / après — mêmes caméras, matériau mat et lumières',font=small,fill='#bac7d6')
 for row,(file,text) in enumerate(views):
  for col,mode in enumerate(['before','after']):
   x,y=margin+col*(width+margin),header+row*(width+caption+margin)
   d.text((x,y),('Avant — 62000ae' if mode=='before' else 'Après — finition locale')+' — '+text,font=label,fill='#f0f4fa')
   frame=Image.open(root/'renders'/mode/(file+'.png')).convert('RGB');im.paste(frame.resize((width,width),Image.Resampling.LANCZOS),(x,y+caption))
 d.text((margin,im.height-footer+8),'Visage, menton et cheveux protégés • Déplacements locaux limités à 3 mm',font=small,fill='#bac7d6')
 d.text((margin,im.height-footer+34),'Model created with Meshy — CC BY 4.0 License',font=small,fill='#bac7d6');im.save(root/'renders'/path)
pair('controle-tete.png','Tête conservée — contrôle avant / après',[('tete-face','Face'),('tete-profil','Profil'),('tete-trois-quarts','Trois quarts')])
pair('comparatif-finition-cou.png','Finition locale du cou — avant / après',[('raccord-profil','Profil'),('raccord-face','Face'),('raccord-trois-quarts','Trois quarts')])
image=Image.open(root/'renders/after/face.png').convert('RGB');out=Image.new('RGB',(800,image.height+150),'#141b24');d=ImageDraw.Draw(out)
d.text((25,14),'Mannequin — finition locale du cou',font=title,fill='#f0f4fa');d.text((25,52),'Tête conservée • Corps protégé hors raccords immédiats',font=small,fill='#bac7d6');out.paste(image,(40,88))
d.text((25,out.height-45),'Model created with Meshy — CC BY 4.0 License',font=small,fill='#bac7d6');out.save(root/'renders/mannequin-complet.png')
(root/'renders/verification.json').write_text(json.dumps({'master_sha256':meta['master_sha256'],'matched_before_after_views':6,'raw_render_hashes_verified':13,'camera_scale_resolution_samples_lighting_equal':True,'image_processing':'Captions and uniform resizing only; raw Blender frames untouched.','compositor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
