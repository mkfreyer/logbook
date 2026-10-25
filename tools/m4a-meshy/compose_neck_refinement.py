"""Compose unchanged matched Blender frames of the local neck refinement."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

p=argparse.ArgumentParser()
p.add_argument('--asset',type=Path,required=True)
a=p.parse_args()
root=a.asset.resolve()
meta=json.loads((root/'assemblage.json').read_text())
records={m:json.loads((root/'renders'/m/'metadata.json').read_text()) for m in ['before','after']}
frames={m:{x['file']:x for x in r['frames']} for m,r in records.items()}
assert records['after']['master_sha256']==meta['master_sha256']
reused=records['before']['master_sha256']!=meta['master_sha256']
if reused:
    reuse=json.loads((root/'renders/before/reuse.json').read_text())
    assert reuse['rendered_master_sha256']==records['before']['master_sha256']
    assert reuse['current_master_sha256']==meta['master_sha256']
    assert reuse['before_scene_geometry_normals_transform_material_lights_world_exact']
    assert reuse['raw_render_hashes_verified']==5
assert records['before']['lights']==records['after']['lights']
expected={'face.png','trois-quarts.png','raccord-face.png','raccord-profil.png','raccord-trois-quarts.png'}
assert frames['before'].keys()==frames['after'].keys()==expected
for file,before in frames['before'].items():
    for field in ['camera_matrix','ortho_scale','resolution','samples']:
        assert before[field]==frames['after'][file][field]
    for mode in frames:
        assert hashlib.sha256((root/'renders'/mode/file).read_bytes()).hexdigest()==frames[mode][file]['sha256']
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
title=ImageFont.truetype(font,27)
label=ImageFont.truetype(font,22)
small=ImageFont.truetype(font,17)

width,margin,header,caption,footer=600,20,90,36,66
canvas=Image.new('RGB',(2*width+3*margin,header+3*(width+caption+margin)+footer),'#141b24')
d=ImageDraw.Draw(canvas)
d.text((margin,14),'Raccord tête / cou — correction locale',font=title,fill='#f0f4fa')
d.text((margin,52),'Même matériau mat, caméras et lumières — Blender / Cycles',font=small,fill='#bac7d6')
for row,(view,text) in enumerate([('raccord-profil','Profil'),('raccord-face','Face'),('raccord-trois-quarts','Trois quarts')]):
    for col,mode in enumerate(['before','after']):
        x,y=margin+col*(width+margin),header+row*(width+caption+margin)
        d.text((x,y),('Avant — dbba75e' if mode=='before' else 'Après — raccord fondu')+' / '+text,font=label,fill='#f0f4fa')
        im=Image.open(root/'renders'/mode/(view+'.png')).convert('RGB')
        canvas.paste(im.resize((width,width),Image.Resampling.LANCZOS),(x,y+caption))
d.text((margin,canvas.height-footer+8),'Corps, visage supérieur et cheveux conservés • Raccord seul reconstruit',font=small,fill='#bac7d6')
d.text((margin,canvas.height-footer+33),'Model created with Meshy — CC BY 4.0 License',font=small,fill='#bac7d6')
canvas.save(root/'renders/comparatif-raccord.png')

width=460
height=round(1152*width/720)
canvas=Image.new('RGB',(3*width+4*margin,header+caption+height+footer),'#141b24')
d=ImageDraw.Draw(canvas)
d.text((margin,14),'Contrôle général — corps et proportions conservés',font=title,fill='#f0f4fa')
d.text((margin,52),'Correction limitée à la base de la tête et au raccord cervical',font=small,fill='#bac7d6')
for col,(mode,view,text) in enumerate([('before','face','Avant / Face'),('after','face','Après / Face'),('after','trois-quarts','Après / Trois quarts')]):
    x=margin+col*(width+margin)
    d.text((x,header),text,font=label,fill='#f0f4fa')
    im=Image.open(root/'renders'/mode/(view+'.png')).convert('RGB')
    canvas.paste(im.resize((width,height),Image.Resampling.LANCZOS),(x,header+caption))
d.text((margin,canvas.height-footer+8),'Proposition pour validation visuelle • Aucune intégration applicative',font=small,fill='#bac7d6')
d.text((margin,canvas.height-footer+33),'Model created with Meshy — CC BY 4.0 License',font=small,fill='#bac7d6')
canvas.save(root/'renders/controle-general.png')
(root/'renders/verification.json').write_text(json.dumps({
    'matched_before_after_views':5,'raw_render_hashes_verified':10,
    'camera_scale_resolution_samples_lighting_equal':True,
    'master_sha256':meta['master_sha256'],
    'before_views_reused_after_exact_scene_equivalence_check':reused,
    'image_processing':'Captions and uniform resizing only. Raw Blender frames untouched.',
    'compositor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
},indent=2)+'\n')
