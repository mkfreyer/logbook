#!/usr/bin/env python3
"""Publish two mobile-size comparisons and verify this single material PoC."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
repo=Path(__file__).resolve().parents[2];root=repo/'docs/m4a/material-poc';baseline=repo/'docs/m4a/bplus-power/power';revision='cf7f7061daf6c758636aca892dc3995b4c9b1d74'
scripts=['make_material_poc_textures.py','prepare_material_poc.py','render_material_poc.py','audit_material_poc.py','finish_material_poc.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=repo).decode().strip()
historical=git('ls-tree','-r','--name-only',revision,'docs/m4a','tools/m4a').splitlines()
for name in historical:assert git('rev-parse',revision+':'+name)==git('hash-object',name),name
for name in scripts:ast.parse((repo/'tools/m4a'/name).read_text())
c=read(root/'experiment/construction.json');audit=read(root/'audit.json');r=read(root/'renders/render-metadata.json');old=read(baseline/'render-metadata.json');textures=read(root/'experiment/textures/textures.json')
assert c['preparer_sha256']==sha(repo/'tools/m4a/prepare_material_poc.py') and c['source_sha256']==sha(baseline/'model.blend')
assert textures['generator_sha256']==sha(repo/'tools/m4a/make_material_poc_textures.py') and len(textures['files'])==4
for f in textures['files']:
 file=root/'experiment/textures'/f['path'];assert sha(file)==f['sha256']
 with Image.open(file) as im:assert im.size==(1024,1024);im.verify()
assert audit['source_prepared_geometry_normals_original_UV_identical'] and audit['added_triangles']==0
assert r['source_sha256']==sha(root/'experiment/model.blend') and r['protocol']['renderer_sha256']==sha(repo/'tools/m4a/render_material_poc.py')
assert r['protocol']['samples']==old['protocol']['samples']==96 and r['protocol']['lights']==old['protocol']['lights'] and r['protocol']['seed']==old['protocol']['seed']==0
assert r['protocol']['material']['color']==old['protocol']['material']['base_color_linear'] and r['protocol']['material']['roughness']==old['protocol']['material']['roughness'] and r['protocol']['material']['metallic']==old['protocol']['material']['metallic']
assert not r['protocol']['AI_generated_images'] and not r['protocol']['anatomy_repainted']
assert len(r['frames'])==4 and {f['view'] for f in r['frames']}=={'front','three-quarter','detail','selection'}
sources=[]
for f in r['frames']:
 file=root/'renders'/f['path'];assert sha(file)==f['sha256']
 with Image.open(file) as im:assert list(im.size)==f['resolution'];im.verify()
 assert f['orange_zones']==(['pectoralis.left'] if f['view']=='selection' else [])
 sources.append({'file':str(file.relative_to(repo)),'sha256':sha(file)})
assert sha(root/'renders/scene-review.blend')==r['review_scene']['sha256'] and r['review_scene']['neutral_selection_restored']
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fontpath,20);small=ImageFont.truetype(fontpath,14)
for view,label in [('front','Face'),('three-quarter','Trois quarts')]:
 new_frame=next(f for f in r['frames'] if f['view']==view);old_frame=next(f for f in old['frames'] if f['view']==view)
 assert sha(baseline/old_frame['path'])==old_frame['sha256'] and new_frame['yaw']==old_frame['yaw'] and abs(new_frame['ortho_scale']-old['protocol']['ortho_scale'])<1e-6 and new_frame['target']==old['protocol']['camera_target']
 image=Image.new('RGB',(780,736),'#0a1621');d=ImageDraw.Draw(image);d.text((14,9),'M4A · Matériaux / normales · '+label,font=font,fill='#e6edf7')
 for col,(file,title) in enumerate([(baseline/(view+'.png'),'Avant · B+ Puissance'),(root/'renders'/(view+'.png'),'Après · POC visuel')]):
  x=390*col;d.text((x+14,42),title,font=small,fill='#c4d1df')
  with Image.open(file) as im:assert im.size==(720,1152);image.paste(im.convert('RGB').resize((390,624),Image.Resampling.LANCZOS),(x,70))
  sources.append({'file':str(file.relative_to(repo)),'sha256':sha(file)})
 d.text((14,701),'Chaque mannequin : 390 px · Géométrie identique · Éclairage identique',font=small,fill='#c4d1df')
 d.text((14,720),'Verdict : approche insuffisante · Base Dan Ulrich / Blender Studio · CC0',font=small,fill='#c4d1df');image.save(root/('comparaison-'+view+'.png'))
for p in [repo/'docs/M4A_POC_MATERIAUX_ECORCHE.md',root/'README.md']:
 for t in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if not t.startswith(('http:','https:','#')):
   q=(p.parent/t.split('#')[0]).resolve();assert q.exists() or q in {root/'manifest.json',root/'validation.json'},(p,t)
assert len(list(root.rglob('*.png')))==10 and not list(root.rglob('*.blend1'))
validation={'verdict':'approche insuffisante','historical_files_verified_unchanged':len(historical),'new_blender_frames':4,'reused_reference_frames':2,'comparison_sheets':2,'comparison_column_px':390,
 'visible_triangles':112176,'added_triangles':0,'source_geometry_exactly_preserved':True,'textures':4,'texture_resolution':[1024,1024],'commercial_cost_eur':0,'one_material_attempt_only':True,
 'application_integration':False,'M4B':False,'mobile_runtime_measured':False,'sources':sources}
(root/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
files=list(root.rglob('*'))+[repo/'docs/M4A_POC_MATERIAUX_ECORCHE.md']+[repo/'tools/m4a'/n for n in scripts]
manifest=[{'path':str(p.relative_to(repo)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files) if p.is_file() and p!=root/'manifest.json']
(root/'manifest.json').write_text(json.dumps({'algorithm':'SHA-256','files':manifest},indent=2)+'\n');print(json.dumps(validation,ensure_ascii=False))
