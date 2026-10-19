#!/usr/bin/env python3
"""Verify B+ fitness artifacts, honest contact limits and historical preservation."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image
repo=Path(__file__).resolve().parents[2];root=repo/'docs/m4a/bplus-fitness'
baseline='70ceacba5b9e204e6069496c582ea0964b68a558'
scripts=['build_bplus_fitness.py','render_bplus_fitness.py','check_bplus_fitness.py',
         'check_bplus_native_contacts.py','audit_bplus_fitness_review.py','make_bplus_fitness_sheets.py','validate_bplus_fitness_delivery.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=repo).decode().strip()
historical=git('ls-tree','-r','--name-only',baseline,'docs/m4a','tools/m4a').splitlines()
for name in historical:assert git('rev-parse',baseline+':'+name)==git('hash-object',name),name
for name in scripts:ast.parse((repo/'tools/m4a'/name).read_text())
protocols=[];summaries={};input_hashes=set();normalized_hashes=set();displacements=[];views={'front','three-quarter','back','side','selection'}
review=read(root/'review-validation.json');source=repo/'docs/m4a/alternatives/studio-realistic-plus/B-plus.blend'
for v in ['baseline','soft','premium']:
    folder=root/v;c=read(folder/'construction.json');g=read(folder/'geometry-check.json');r=read(folder/'render-metadata.json')
    assert c['generator_sha256']==sha(repo/'tools/m4a/build_bplus_fitness.py')
    assert c['source_blend_sha256']==sha(source);input_hashes.add(c['source_blend_sha256']);normalized_hashes.add(c['source_geometry_normalized_sha256'])
    assert c['L_and_S_geometry_read'] is False and c['separate_muscles_added'] is False
    assert c['counts']['visible_triangles']==112176 and c['counts']['body_triangles']==110000
    assert c['counts']['objects']==3 and c['counts']['demo_surface_zones']==2 and c['counts']['separate_muscle_objects']==0
    assert sum(o['triangles'] for o in g['objects'])==112176 and len(g['objects'])==3
    assert g['source_sha256']==r['source_sha256']==sha(folder/'model.blend')
    assert g['continuous_body'] and g['all_objects_closed_single_component_genus_zero']
    assert all(o['boundary_edges']==o['nonmanifold_edges']==o['nonfinite_coordinates']==o['near_degenerate_triangles']==o['loose_vertices']==0 and o['genus']==0 and o['components']==1 for o in g['objects'])
    body=next(o for o in g['objects'] if o['role']=='body');cross=body['self_crossing_check']
    assert cross['crossings_by_region']['sculptable_body']==0 and cross['crossings_by_region']['hands']==0 and cross['coplanar_candidates']==0
    displacements.append(c['relief']['max_highres_displacement_m'])
    assert c['relief']['minimum_highres_normal_dot']>=.85
    assert r['protocol']['renderer_sha256']==sha(repo/'tools/m4a/render_bplus_fitness.py')
    assert r['protocol']['resolution']==[720,1152] and r['protocol']['samples']==96
    assert r['protocol']['AI_generated_images'] is False and r['protocol']['geometry_changed_by_renderer'] is False
    assert len(r['frames'])==5 and {f['view'] for f in r['frames']}==views
    assert r['selection']['logical_regions']==['pectoralis.left','pectoralis.right'] and r['selection']['separate_muscle_objects']==0
    assert r['selection']['application_interaction'] is False
    for frame in r['frames']:
        file=folder/frame['path'];assert sha(file)==frame['sha256'] and frame['selection_enabled']==(frame['view']=='selection')
        with Image.open(file) as im:assert im.size==(720,1152);im.verify()
    assert sha(folder/'scene-review.blend')==r['review_scene']['sha256'] and r['review_scene']['selection_disabled']
    assert review[v]['source_review_geometry_normals_surface_masks_identical']
    protocols.append(r['protocol']);summaries[v]={'triangles':112176,'objects':3,'demo_surface_zones':2,'max_relief_mm':displacements[-1]*1000,
        'self_crossings_by_region':cross['crossings_by_region'],'all_objects_closed':True,'body_bounds':[body['bounds_min'],body['bounds_max']]}
assert len(input_hashes)==len(normalized_hashes)==1 and protocols[0]==protocols[1]==protocols[2]
assert displacements[0]==0 and 0<displacements[1]<displacements[2]<=.008
assert len({r['geometry_signature_sha256'] for r in review.values()})==3
native=read(root/'native-contact-check.json');assert native['source_sha256']==sha(source)
assert native['crossings']['crossings_by_region']['feet']>0 and native['crossings']['crossings_by_region']['head']>0
sheets=read(root/'sheets-metadata.json');assert len(sheets['sources'])==15 and not sheets['anatomy_repainted']
for item in sheets['sources']:assert sha(root/item['file'])==item['sha256']
assert len(list(root.rglob('*.png')))==22 and len(list(root.glob('*.png')))==7
for p in root.glob('*.png'):
    with Image.open(p) as im:im.verify()
assert not list(root.rglob('*.blend1')) and not list(root.rglob('*.part'))
assert (root/'SOURCE_LICENSE.md').read_bytes()==(repo/'docs/m4a/alternatives/blender-studio/LICENSE.ASSETS.md').read_bytes()
for p in [repo/'docs/M4A_B_PLUS_ECORCHE.md',root/'README.md',root/'PROVENANCE.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if not target.startswith(('http:','https:','#')):
            resolved=(p.parent/target.split('#')[0]).resolve()
            assert resolved.exists() or resolved in {root/'manifest.json',root/'validation.json'},(p,target)
report={'baseline':baseline,'historical_files_verified_unchanged':len(historical),'variants':summaries,
    'same_original_B_plus_source':True,'source_review_geometry_normals_surface_masks_identical':True,
    'common_blender_protocol':True,'blender_pngs_verified':15,'comparison_sheets_verified':7,
    'source_geometry_license':'CC0','application_integration':False,'M4B':False,'mobile_benchmark':False,
    'limitations':['Head/foot self-crossings exist in the original B+ and all proxies; no globally intersection-free claim.',
    'No crossings detected in sculpted proxy regions by this non-coplanar triangle check; no full highres body intersection audit.',
    'Two demonstration surface masks, not a completed anatomical segmentation.',
    'No rig, medical validation, iPhone runtime measurement, bake or app export.']}
(root/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
files=list(root.rglob('*'))+[repo/'docs/M4A_B_PLUS_ECORCHE.md']+[repo/'tools/m4a'/name for name in scripts]
manifest=[{'path':str(p.relative_to(repo)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files) if p.is_file() and p!=root/'manifest.json']
(root/'manifest.json').write_text(json.dumps({'algorithm':'SHA-256','source_geometry_license':'CC0','files':manifest},indent=2)+'\n')
print(json.dumps(report,indent=2))
