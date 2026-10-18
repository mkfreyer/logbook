#!/usr/bin/env python3
"""Assemble only two mobile-size comparisons and verify the failed PoC delivery."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
repo=Path(__file__).resolve().parents[2];root=repo/'docs/m4a/pectoral-poc';baseline='43ac3c1ddd4a5cb37afd62ad0feded96afb0d290'
scripts=['build_pectoral_poc.py','render_pectoral_poc.py','audit_pectoral_poc.py','finish_pectoral_poc.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=repo).decode().strip()
historical=git('ls-tree','-r','--name-only',baseline,'docs/m4a','tools/m4a').splitlines()
for name in historical:assert git('rev-parse',baseline+':'+name)==git('hash-object',name),name
for name in scripts:ast.parse((repo/'tools/m4a'/name).read_text())
c=read(root/'experiment/construction.json');g=read(root/'experiment/geometry-check.json');audit=read(root/'audit.json')
assert c['generator_sha256']==sha(repo/'tools/m4a/build_pectoral_poc.py')
assert c['source_sha256']==sha(repo/'docs/m4a/bplus-power/power/model.blend')
assert not c['third_party_anatomy_loaded'] and c['outside_scope_unchanged'] and c['counts']['demo_surface_zones']==3
assert g['source_sha256']==sha(root/'experiment/model.blend') and g['all_objects_closed_single_component_genus_zero']
assert audit['verdict']=='méthode insuffisante' and audit['source_review_geometry_normals_surface_attributes_identical']
assert c['zone_triangles']==audit['zone_triangles'] and audit['two_eyes_unchanged']
protocols=[];sources=[]
for kind in ['before','after']:
    r=read(root/kind/'render-metadata.json');protocols.append(r['protocol'])
    assert r['protocol']['samples']==96 and r['protocol']['renderer_sha256']==sha(repo/'tools/m4a/render_pectoral_poc.py')
    assert not r['protocol']['AI_generated_images'] and not r['protocol']['anatomy_repainted']
    assert len(r['frames'])==(2 if kind=='before' else 4)
    assert r['source_sha256']==sha(repo/'docs/m4a/bplus-power/power/model.blend' if kind=='before' else root/'experiment/model.blend')
    for f in r['frames']:
        p=root/kind/f['path'];assert sha(p)==f['sha256']
        with Image.open(p) as im:assert list(im.size)==f['resolution'];im.verify()
        assert f['orange_zones']==(['pectoralis.left'] if f['view']=='selection' else [])
        sources.append({'file':str(p.relative_to(root)),'sha256':sha(p)})
    if kind=='after':assert sha(root/'after/scene-review.blend')==r['review_scene']['sha256'] and r['review_scene']['neutral_selection_restored']
assert protocols[0]==protocols[1]
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';title=ImageFont.truetype(fontpath,20);small=ImageFont.truetype(fontpath,14)
meta=PngImagePlugin.PngInfo();meta.add_text('Verdict','Methode insuffisante; no 2D anatomy repainting')
for view,label in [('front','Face'),('three-quarter','Trois quarts')]:
    out=Image.new('RGB',(780,736),'#0a1621');d=ImageDraw.Draw(out)
    d.text((14,9),'M4A · PoC local · '+label,font=title,fill='#e6edf7')
    for col,(kind,name) in enumerate([('before','Avant · B+ Puissance'),('after','Après · Essai insuffisant')]):
        x=col*390;d.text((x+14,42),name,font=small,fill='#c4d1df')
        with Image.open(root/kind/(view+'.png')) as im:out.paste(im.convert('RGB').resize((390,624),Image.Resampling.LANCZOS),(x,70))
    d.text((14,701),'Chaque mannequin : 390 px · Même studio et matériau · Rendus Blender',font=small,fill='#c4d1df')
    d.text((14,720),'Base Dan Ulrich / Blender Studio · CC0 · Modélisation arrêtée après cet essai',font=small,fill='#c4d1df')
    out.save(root/('comparaison-'+view+'.png'),pnginfo=meta)
for p in [repo/'docs/M4A_POC_ECORCHE_PECTORAUX.md',root/'README.md']:
    for t in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if not t.startswith(('http:','https:','#')):
            q=(p.parent/t.split('#')[0]).resolve();assert q.exists() or q in {root/'manifest.json',root/'validation.json'},(p,t)
assert len(list(root.rglob('*.png')))==8 and not list(root.rglob('*.blend1'))
validation={'verdict':'méthode insuffisante','historical_files_verified_unchanged':len(historical),'new_blender_frames':6,'comparison_sheets':2,
 'comparison_column_width_px':390,'source_geometry_license':'CC0','body_triangles':c['counts']['body_triangles'],'visible_triangles':c['counts']['visible_triangles'],
 'objects':3,'selectable_demo_zones':3,'one_visual_attempt_only':True,'no_automatic_followup_variant':True,'application_integration':False,'M4B':False,'mobile_runtime_measured':False,'sources':sources}
(root/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
files=list(root.rglob('*'))+[repo/'docs/M4A_POC_ECORCHE_PECTORAUX.md']+[repo/'tools/m4a'/n for n in scripts]
manifest=[{'path':str(p.relative_to(repo)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files) if p.is_file() and p!=root/'manifest.json']
(root/'manifest.json').write_text(json.dumps({'algorithm':'SHA-256','files':manifest},indent=2)+'\n');print(json.dumps(validation,ensure_ascii=False))
