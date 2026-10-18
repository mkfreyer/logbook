#!/usr/bin/env python3
"""Verify a single B+ Premium Puissance iteration and reuse of its exact control."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image
repo=Path(__file__).resolve().parents[2];root=repo/'docs/m4a/bplus-power';old=repo/'docs/m4a/bplus-fitness/premium';new=root/'power'
baseline='253ddd7978fbe0289616750cce6abc73b64112a0'
scripts=['build_bplus_power.py','make_bplus_power_sheets.py','audit_bplus_power_review.py','validate_bplus_power_delivery.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=repo).decode().strip()
historical=git('ls-tree','-r','--name-only',baseline,'docs/m4a','tools/m4a').splitlines()
for name in historical:assert git('rev-parse',baseline+':'+name)==git('hash-object',name),name
for name in scripts:ast.parse((repo/'tools/m4a'/name).read_text())
c=read(new/'construction.json');assert c['source_blend_sha256']==sha(old/'model.blend')
assert c['generator_sha256']==sha(repo/'tools/m4a/build_bplus_power.py')
assert not c['topology_changed'] and not c['remesh_or_decimation'] and c['surface_masks_preserved']
assert not c['L_and_S_geometry_read'] and not c['separate_muscles_added']
assert c['counts']['visible_triangles']==112176 and c['counts']['body_triangles']==110000
assert c['counts']['objects']==3 and c['counts']['demo_surface_zones']==2
assert .01<c['relief']['max_displacement_from_parent_m']<.04 and c['relief']['minimum_normal_dot']>=.85
assert c['relief']['target_strength']>c['relief']['parent_strength'] and c['relief']['target_fibre_amplitude_m']>c['relief']['parent_fibre_amplitude_m']
comparison=read(root/'comparison-geometry.json');assert comparison['same_body_topology_and_three_surface_masks']
assert comparison['protected_head_hands_feet_vertices_unchanged']
review=read(root/'review-validation.json');protocols=[];counts={};views={'front','three-quarter','back','side','selection'}
for key,folder in [('../bplus-fitness/premium',old),('power',new)]:
    r=read(folder/'render-metadata.json');g=read(folder/'geometry-check.json')
    assert g['source_sha256']==r['source_sha256']==sha(folder/'model.blend')
    assert g['all_objects_closed_single_component_genus_zero'] and g['continuous_body']
    assert len(g['objects'])==3 and sum(o['triangles'] for o in g['objects'])==112176
    assert all(o['boundary_edges']==o['nonmanifold_edges']==o['loose_vertices']==o['nonfinite_coordinates']==o['near_degenerate_triangles']==0 for o in g['objects'])
    body=next(o for o in g['objects'] if o['role']=='body');cross=body['self_crossing_check']
    assert cross['crossings_by_region']=={'feet':226,'head':78,'hands':0,'sculptable_body':0} and cross['coplanar_candidates']==0
    assert r['protocol']['renderer_sha256']==sha(repo/'tools/m4a/render_bplus_fitness.py')
    assert r['protocol']['resolution']==[720,1152] and r['protocol']['samples']==96 and not r['protocol']['AI_generated_images']
    assert len(r['frames'])==5 and {f['view'] for f in r['frames']}==views
    assert r['selection']['logical_regions']==['pectoralis.left','pectoralis.right'] and not r['selection']['application_interaction']
    for f in r['frames']:
        p=folder/f['path'];assert sha(p)==f['sha256'] and f['selection_enabled']==(f['view']=='selection')
        with Image.open(p) as im:assert im.size==(720,1152);im.verify()
    assert sha(folder/'scene-review.blend')==r['review_scene']['sha256'] and r['review_scene']['selection_disabled']
    assert review[key]['source_review_geometry_normals_surface_masks_identical']
    protocols.append(r['protocol']);counts[key]={'triangles':112176,'objects':3,'demo_surface_zones':2,'self_crossings_by_region':cross['crossings_by_region']}
assert protocols[0]==protocols[1]
sheets=read(root/'sheets-metadata.json');assert len(sheets['sources'])==10 and not sheets['anatomy_repainted']
for f in sheets['sources']:assert sha(root/f['file'])==f['sha256']
assert len(list(root.rglob('*.png')))==12 and len(list(root.glob('*.png')))==7
for p in root.glob('*.png'):
    with Image.open(p) as im:im.verify()
assert not list(root.rglob('*.blend1')) and not list(root.rglob('*.part'))
for p in [repo/'docs/M4A_B_PLUS_PREMIUM_PUISSANCE.md',root/'README.md']:
    for t in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if not t.startswith(('http:','https:','#')):
            target=(p.parent/t.split('#')[0]).resolve()
            assert target.exists() or target in {root/'validation.json',root/'manifest.json'},(p,t)
report={'baseline':baseline,'historical_files_verified_unchanged':len(historical),'one_new_direction':True,
 'comparison':counts,'same_render_protocol':True,'new_blender_renders':5,'preserved_control_renders':5,
 'comparison_sheets':7,'body_topology_and_masks_preserved':True,'protected_vertices_preserved':True,
 'source_geometry_license':'CC0','application_integration':False,'SQLite_changed':False,'M4B':False,'mobile_benchmark':False,
 'limitations':['304 inherited head/foot self-crossings, identical to selected Premium; no globally intersection-free claim.',
 'No crossings detected in sculpted proxy regions by supplied non-coplanar triangle audit.',
 'Two pectoral demo masks only; no final segmentation, rig, medical validation or iPhone runtime benchmark.']}
(root/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
files=list(root.rglob('*'))+[repo/'docs/M4A_B_PLUS_PREMIUM_PUISSANCE.md']+[repo/'tools/m4a'/s for s in scripts]
manifest=[{'path':str(p.relative_to(repo)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files) if p.is_file() and p!=root/'manifest.json']
(root/'manifest.json').write_text(json.dumps({'algorithm':'SHA-256','source_geometry_license':'CC0','files':manifest},indent=2)+'\n')
print(json.dumps(report,indent=2))
